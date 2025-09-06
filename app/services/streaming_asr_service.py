"""
Streaming ASR Service

Goal: Low-latency partial results with optional VAD and final high-quality stabilization.

Design:
- Try to use faster-whisper for low-latency partial recognition if available.
- Try to use webrtcvad for robust voice-activity detection if available.
- Fall back to existing SpeechService (WhisperX wrapper) for non-streaming finalize if dependencies
  are unavailable. Partial results will be produced by periodically running the offline transcriber
  on the current buffer (acceptable for an MVP without extra deps).

Assumptions:
- Client sends PCM16LE mono audio frames at a consistent sample rate (default 16000 Hz) over WebSocket.
- Language defaults to Japanese ("ja").

This module avoids hard dependencies: it runs even if optional libs are missing.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
import struct

try:
    # Optional low-latency ASR
    from faster_whisper import WhisperModel  # type: ignore

    FASTER_WHISPER_AVAILABLE = True
except Exception:
    WhisperModel = None  # type: ignore
    FASTER_WHISPER_AVAILABLE = False

try:
    import webrtcvad  # type: ignore

    WEBRTC_VAD_AVAILABLE = True
except Exception:
    webrtcvad = None  # type: ignore
    WEBRTC_VAD_AVAILABLE = False

try:
    # Local speech service for fallback finalize
    from services.speech_service import get_speech_service
except ImportError:  # pragma: no cover
    from app.services.speech_service import get_speech_service  # type: ignore


logger = logging.getLogger(__name__)


@dataclass
class PartialResult:
    text: str
    confidence: float
    is_final: bool
    start_ms: int
    end_ms: int


def _bytes_per_frame(sample_rate: int, frame_ms: int) -> int:
    # PCM16 mono: 2 bytes per sample
    return int(sample_rate * (frame_ms / 1000.0) * 2)


class StreamingASRService:
    """
    Manage streaming audio ingestion, optional VAD segmentation, and partial/final ASR.

    Public methods:
    - configure(language, sample_rate)
    - feed_chunk(pcm_bytes) → Optional[List[PartialResult]] (zero or more updates)
    - flush_final() → Optional[PartialResult] (final stabilization)
    """

    def __init__(
        self,
        language: str = "ja",
        sample_rate: int = 16000,
        vad_aggressiveness: int = 2,
        partial_interval_ms: int = 700,
    ) -> None:
        self.language = language
        self.sample_rate = sample_rate
        self.vad_aggressiveness = max(0, min(3, vad_aggressiveness))
        self.partial_interval_ms = max(200, partial_interval_ms)

        self._buffer = bytearray()
        self._segment_buffer = bytearray()
        self._last_partial_at_ms = 0
        self._stream_start_ms = int(time.time() * 1000)
        self._closed = False

        # Optional components
        self._vad = None
        if WEBRTC_VAD_AVAILABLE:
            try:
                self._vad = webrtcvad.Vad(self.vad_aggressiveness)
                logger.info("StreamingASR: WebRTC VAD enabled")
            except Exception as e:
                logger.warning(f"StreamingASR: VAD init failed, continue without VAD: {e}")
                self._vad = None

        self._fw_model = None
        if FASTER_WHISPER_AVAILABLE:
            try:
                # small-int8 is a good latency/quality tradeoff; allow CPU by default
                self._fw_model = WhisperModel(
                    "small",
                    device="cpu",
                    compute_type="int8",
                )
                logger.info("StreamingASR: faster-whisper model loaded (small/int8/cpu)")
            except Exception as e:
                logger.warning(f"StreamingASR: faster-whisper load failed, fallback mode: {e}")
                self._fw_model = None

        self._speech_service = get_speech_service()

        # Derived
        self._frame_ms = 20  # 20ms frames for VAD
        self._frame_bytes = _bytes_per_frame(self.sample_rate, self._frame_ms)

    def configure(self, language: Optional[str] = None, sample_rate: Optional[int] = None) -> None:
        if language:
            self.language = language
        if sample_rate and sample_rate != self.sample_rate:
            # Reset buffers if sample rate changes to avoid alignment issues
            self.sample_rate = sample_rate
            self._frame_bytes = _bytes_per_frame(self.sample_rate, self._frame_ms)
            self._buffer.clear()
            self._segment_buffer.clear()

    async def feed_chunk(self, pcm_bytes: bytes) -> List[PartialResult]:
        """
        Feed a chunk of PCM16 mono audio. Return zero or more partial results.
        """
        if self._closed:
            return []

        self._buffer.extend(pcm_bytes)
        self._segment_buffer.extend(pcm_bytes)

        now_ms = int(time.time() * 1000)
        results: List[PartialResult] = []

        # VAD-based segmentation if available
        if self._vad is not None:
            # Process in frame-sized steps for VAD decisions
            while len(self._segment_buffer) >= self._frame_bytes:
                frame = bytes(self._segment_buffer[: self._frame_bytes])
                del self._segment_buffer[: self._frame_bytes]

                try:
                    is_speech = self._vad.is_speech(frame, self.sample_rate)
                except Exception:
                    is_speech = True

                # Simple heuristic: if non-speech frame encountered and we have
                # accumulated buffer, attempt a finalization of the segment.
                if not is_speech and len(self._buffer) > 0:
                    final = await self._transcribe_bytes(bytes(self._buffer), is_final=True)
                    self._buffer.clear()
                    if final:
                        results.append(final)

        # Time-based partial update (no more often than partial_interval_ms)
        if now_ms - self._last_partial_at_ms >= self.partial_interval_ms and len(self._buffer) > 0:
            partial = await self._transcribe_bytes(bytes(self._buffer), is_final=False)
            self._last_partial_at_ms = now_ms
            if partial:
                results.append(partial)

        return results

    async def flush_final(self) -> Optional[PartialResult]:
        """
        Flush any remaining audio and produce a final stabilized transcript.
        """
        if self._closed:
            return None
        self._closed = True

        if len(self._buffer) == 0:
            return None

        final = await self._transcribe_bytes(bytes(self._buffer), is_final=True)
        self._buffer.clear()
        return final

    async def _transcribe_bytes(self, pcm_bytes: bytes, is_final: bool) -> Optional[PartialResult]:
        """
        Run ASR on the provided bytes. Prefer faster-whisper for partials; use SpeechService as
        universal fallback. Returns a PartialResult or None if recognition fails.
        """
        try:
            start_ms = int(time.time() * 1000) - self._stream_start_ms

            if self._fw_model is not None:
                # faster-whisper expects float32 audio or file path; the wrapper also supports raw pcm with
                # parameters, but to keep it simple, we will let faster-whisper accept numpy array if available.
                # To avoid hard dependency on numpy here, we rely on the model's transcribe on bytes via
                # a temporary minimal WAV wrapper is out of scope; thus we will fall back to SpeechService for now
                # when we cannot easily feed raw bytes. Implementing true streaming decode is deferred.
                pass

            # Fallback or general path: use existing SpeechService.
            # Wrap raw PCM16 mono into a minimal WAV container for compatibility.
            wav_bytes = self._pcm16_to_wav(pcm_bytes, self.sample_rate)
            result = await self._speech_service.transcribe_audio(wav_bytes, self.language)

            text = result.get("text", "").strip()
            confidence = float(result.get("confidence", 0.0))
            end_ms = int(time.time() * 1000) - self._stream_start_ms
            return PartialResult(text=text, confidence=confidence, is_final=is_final, start_ms=start_ms, end_ms=end_ms)

        except Exception as e:
            logger.warning(f"StreamingASR: transcription failed: {e}")
            return None

    def _pcm16_to_wav(self, pcm: bytes, sample_rate: int) -> bytes:
        """Create a minimal WAV header for PCM16 mono and prepend to bytes."""
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        subchunk2_size = len(pcm)
        chunk_size = 36 + subchunk2_size

        header = b"RIFF" + struct.pack("<I", chunk_size) + b"WAVE"
        fmt = (
            b"fmt "
            + struct.pack("<I", 16)  # Subchunk1Size for PCM
            + struct.pack("<H", 1)  # AudioFormat PCM
            + struct.pack("<H", num_channels)
            + struct.pack("<I", sample_rate)
            + struct.pack("<I", byte_rate)
            + struct.pack("<H", block_align)
            + struct.pack("<H", bits_per_sample)
        )
        data = b"data" + struct.pack("<I", subchunk2_size)
        return header + fmt + data + pcm


