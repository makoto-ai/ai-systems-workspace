"""
Speech-to-Text Service using WhisperX with Speaker Diarization
Phase 6: WhisperX Speech-to-Text Integration
"""

# Import WhisperX with fallback for compatibility
try:
    import whisperx  # type: ignore
    import whisperx.diarize  # type: ignore

    WHISPERX_AVAILABLE = True
except ImportError:
    WHISPERX_AVAILABLE = False

import tempfile
import os
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

# torch dependency removed for simplification
import gc
import numpy as np

logger = logging.getLogger(__name__)


class SpeechServiceError(Exception):
    """Speech service related errors"""

    pass


class SpeechService:
    """Service for handling speech-to-text conversion using WhisperX with speaker diarization"""

    def __init__(
        self,
        model_size: str = "base",
        language: str = "ja",
        device: str = "auto",
        hf_token: Optional[str] = None,
    ):
        """
        Initialize the Speech Service with WhisperX model (EXTREME SPEED MODE)

        Args:
            model_size: WhisperX model size (FORCED to "tiny" for maximum speed)
            language: Default language code ("ja", "en", etc.)
            device: Device to use (FORCED to "cpu" for maximum stability)
            hf_token: HuggingFace token for speaker diarization (DISABLED for speed)
        """
        # Configurable model with safe defaults
        self.model_size = model_size or "base"
        self.language = language
        self.device = self._get_device(device)
        self.hf_token = None  # diarization disabled by default for speed
        self.model = None
        self.align_model = None
        self.diarize_model = None

        # Performance settings
        self.extreme_speed = True
        self.minimal_processing = True
        self.skip_all_extras = True

        self._load_models()

    def _get_device(self, device: str) -> str:
        """Determine the best device to use"""
        if device == "auto":
            return "cpu"  # Simplified: always use CPU
        return device

    def _load_models(self):
        """Load only the essential model for maximum speed"""
        try:
            if not WHISPERX_AVAILABLE:
                logger.warning("WhisperX is not available. Using fallback mode.")
                # Set up fallback mode
                self.model = "fallback"
                self.align_model = None
                self.align_metadata = None
                self.diarize_model = None
                logger.info("Fallback speech service initialized (no WhisperX)")
                return

            logger.info(f"Loading WhisperX model size={self.model_size} device={self.device}")

            # Load core WhisperX model with selected size
            self.model = whisperx.load_model(
                self.model_size,
                device=self.device,
                compute_type="int8",  # CPU-friendly; upgrade if GPU available
            )
            logger.info("WhisperX model loaded")

            # Skip ALL other models for maximum speed
            self.align_model = None
            self.align_metadata = None
            self.diarize_model = None

            logger.info("Skipped alignment and diarization models for extreme speed")

        except Exception as e:
            logger.error(f"Failed to load WhisperX models: {str(e)}")
            logger.warning("Falling back to dummy implementation")
            # Fallback to dummy implementation
            self.model = "fallback"
            self.align_model = None
            self.align_metadata = None
            self.diarize_model = None

    def _load_diarization_model_on_demand(self) -> bool:
        """Load diarization model on demand if not already loaded"""
        if self.diarize_model is not None:
            return True

        if not self.hf_token:
            logger.warning(
                "Cannot load diarization model: HuggingFace token not provided"
            )
            return False

        try:
            logger.info("Loading speaker diarization model on demand...")
            self.diarize_model = whisperx.diarize.DiarizationPipeline(
                use_auth_token=self.hf_token, device=self.device
            )
            logger.info("Speaker diarization model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load diarization model on demand: {str(e)}")
            return False

    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        enable_diarization: bool = True,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe audio data to text using WhisperX with optional speaker diarization
        EXTREME SPEED MODE: 0.2-0.4 seconds target
        """
        if not self.model:
            raise SpeechServiceError("Speech model not loaded")

        use_language = language or self.language

        # Fallback mode when WhisperX is not available
        if self.model == "fallback" or not WHISPERX_AVAILABLE:
            logger.info("Using fallback speech recognition")
            return self._fallback_transcribe(audio_data, use_language)

        # Create temporary file and ensure WAV/PCM16/16kHz mono for stable VAD
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as temp_file:
            temp_file.write(audio_data)
            raw_path = temp_file.name
        temp_file_path = raw_path
        try:
            import subprocess, shutil
            wav_fd, wav_tmp = tempfile.mkstemp(suffix=".wav")
            os.close(wav_fd)
            ffmpeg_bin = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
            env = os.environ.copy()
            env["PATH"] = env.get("PATH", "") + ":/opt/homebrew/bin:/usr/local/bin:/usr/bin"
            # Try decoding input (webm/ogg/whatever) to wav pcm_s16le 16k mono
            cmd = [
                ffmpeg_bin, "-y", "-i", raw_path,
                "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
                wav_tmp,
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
            temp_file_path = wav_tmp
        except Exception:
            # fallback: assume input already wav
            temp_file_path = raw_path

        try:
            logger.info(f"EXTREME SPEED: Transcribing audio")

            # Load audio with WhisperX
            audio = whisperx.load_audio(temp_file_path)

            # EXTREME SPEED: Skip duration checks for maximum speed
            # Only pad if absolutely necessary
            if len(audio) < 8000:  # Less than 0.5 seconds at 16kHz
                padding = 8000 - len(audio)
                audio = np.pad(audio, (0, padding), "constant")

            # 1. Transcribe with WhisperX (EXTREME SPEED MODE)
            # Absolute minimum settings for sub-second processing
            result = self.model.transcribe(
                audio,
                batch_size=1,  # Minimum batch for maximum speed
                language=use_language,
            )

            # 2. EXTREME SPEED: Skip ALL extra processing
            diarization_successful = False
            logger.info("EXTREME SPEED: Minimal processing only")

            # Process and format results with minimal overhead
            transcription_result = self._format_result_fast(result, use_language)

            # EXTREME SPEED: Skip GPU cleanup for speed
            logger.info(f"EXTREME SPEED: Transcription completed")
            return transcription_result

        except Exception as e:
            logger.error(f"Failed to transcribe audio: {str(e)}")
            raise SpeechServiceError(f"Failed to transcribe audio: {str(e)}")

        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            except OSError:
                pass

    def _fallback_transcribe(self, audio_data: bytes, language: str) -> Dict[str, Any]:
        """
        Fallback transcription when WhisperX is not available
        """
        logger.info("Using fallback transcription (WhisperX not available)")

        # Return a placeholder result for development/testing
        return {
            "text": "[音声認識: WhisperXが利用できません。代替実装を使用中]",
            "language": language,
            "segments": [
                {
                    "start": 0.0,
                    "end": 1.0,
                    "text": "[音声認識: WhisperXが利用できません]",
                    "confidence": 0.5,
                }
            ],
            "confidence": 0.5,
            "duration": 1.0,
            "speaker_count": 1,
            "speakers": ["SPEAKER_00"],
            "has_diarization": False,
            "processing_time": 0.1,
            "fallback_mode": True,
        }

    def _format_result_fast(
        self, result: Dict[str, Any], language: str
    ) -> Dict[str, Any]:
        """
        EXTREME SPEED: Format WhisperX result with minimal processing

        Args:
            result: WhisperX transcription result
            language: Language used for transcription

        Returns:
            Minimal formatted transcription result
        """
        segments = result.get("segments", [])

        # Extract full text with minimal processing
        full_text = " ".join([segment.get("text", "").strip() for segment in segments])

        # EXTREME SPEED: Minimal segment processing
        processed_segments = []
        for segment in segments:
            if isinstance(segment, dict):
                processed_segments.append(
                    {
                        "start": segment.get("start", 0.0),
                        "end": segment.get("end", 0.0),
                        "text": str(segment.get("text", "")).strip(),
                        "confidence": segment.get("avg_logprob", 0.0),
                    }
                )

        # EXTREME SPEED: Minimal statistics
        total_duration = processed_segments[-1]["end"] if processed_segments else 0.0

        return {
            "text": full_text.strip(),
            "language": language,
            "segments": processed_segments,
            "confidence": sum(s.get("confidence", 0) for s in processed_segments)
            / max(len(processed_segments), 1),
            "duration": total_duration,
            "speaker_count": 1,  # Fixed for speed
            "speakers": ["SPEAKER_00"],  # Fixed for speed
            "has_diarization": False,
            "processing_time": 0.0,  # Will be set by caller
        }

    def _format_result(
        self, result: Dict[str, Any], language: str, has_diarization: bool
    ) -> Dict[str, Any]:
        """
        Format WhisperX result into standardized format

        Args:
            result: WhisperX transcription result
            language: Language used for transcription
            has_diarization: Whether diarization was performed

        Returns:
            Formatted transcription result
        """
        segments = result.get("segments", [])

        # Extract full text
        full_text = " ".join([segment.get("text", "").strip() for segment in segments])

        # Process segments with speaker information
        processed_segments = []
        speakers = set()

        for segment in segments:
            if isinstance(segment, dict):
                speaker = segment.get("speaker", "UNKNOWN") if has_diarization else None
                if speaker and speaker != "UNKNOWN":
                    speakers.add(speaker)

                processed_segment = {
                    "start": segment.get("start", 0.0),
                    "end": segment.get("end", 0.0),
                    "text": str(segment.get("text", "")).strip(),
                    "confidence": segment.get("avg_logprob", 0.0),
                    "speaker": speaker,
                }
                processed_segments.append(processed_segment)

        # Calculate statistics
        total_duration = processed_segments[-1]["end"] if processed_segments else 0.0
        avg_confidence = (
            sum(seg.get("confidence", 0.0) for seg in processed_segments)
            / len(processed_segments)
            if processed_segments
            else 0.0
        )

        return {
            "text": full_text.strip(),
            "language": language,
            "segments": processed_segments,
            "confidence": max(
                0.0, min(1.0, (avg_confidence + 10) / 10)
            ),  # Convert log prob to 0-1 scale
            "duration": total_duration,
            "speaker_count": len(speakers),
            "speakers": sorted(list(speakers)) if speakers else [],
            "has_diarization": has_diarization,
        }

    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get list of supported languages

        Returns:
            Dictionary of language codes and names
        """
        return {
            "ja": "Japanese",
            "en": "English",
            "zh": "Chinese",
            "ko": "Korean",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ar": "Arabic",
            "hi": "Hindi",
            "nl": "Dutch",
            "pl": "Polish",
            "tr": "Turkish",
            "vi": "Vietnamese",
            "th": "Thai",
        }

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded models

        Returns:
            Model information dictionary
        """
        return {
            "model_size": self.model_size,
            "device": self.device,
            "compute_type": "int8",  # CPU-compatible mode for stability
            "language": self.language,
            "hf_token_available": self.hf_token is not None,
            "supported_languages": len(self.get_supported_languages()),
            "loaded": self.model is not None,
            "alignment_available": self.align_model is not None,
            "diarization_available": self.diarize_model is not None,
            "features": {
                "transcription": True,
                "alignment": self.align_model is not None,
                "speaker_diarization": self.diarize_model is not None,
            },
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current service status"""
        is_fallback = self.model == "fallback" or not WHISPERX_AVAILABLE
        return {
            "model_loaded": self.model is not None,
            "model_size": "tiny" if not is_fallback else "fallback",
            "device": "cpu",
            "compute_type": "int8",
            "extreme_speed_mode": True,
            "language": self.language,
            "alignment_model": False,
            "diarization_model": False,
            "whisperx_available": WHISPERX_AVAILABLE,
            "fallback_mode": is_fallback,
            "warning": "WhisperXが利用できません" if is_fallback else None,
        }


# Global speech service instance
_speech_service_instance: Optional[SpeechService] = None


def get_speech_service(
    model_size: str = "base", language: str = "ja", hf_token: Optional[str] = None
) -> SpeechService:
    """
    Get or create a global speech service instance

    Args:
        model_size: WhisperX model size
        language: Default language
        hf_token: HuggingFace token for speaker diarization

    Returns:
        SpeechService instance
    """
    global _speech_service_instance

    if _speech_service_instance is None:
        _speech_service_instance = SpeechService(
            model_size=model_size, language=language, hf_token=hf_token
        )

    return _speech_service_instance
