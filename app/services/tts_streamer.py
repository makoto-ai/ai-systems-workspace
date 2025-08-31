"""
TTS Streamer Service

Streams synthesized audio in small parts as NDJSON events for low-latency playback on the client.
Each event:
  {"index": int, "text": str, "bytes": int, "audio_b64": str}

This avoids building a single WAV during generation and lets the client start playback earlier.
"""

from __future__ import annotations

import asyncio
import base64
import logging
from dataclasses import dataclass
from typing import AsyncGenerator, List, Optional

try:
    from services.voice_service import VoiceService
except ImportError:  # pragma: no cover
    from app.services.voice_service import VoiceService  # type: ignore


logger = logging.getLogger(__name__)


def _split_into_sentences(text: str) -> List[str]:
    # Simple sentence splitter for Japanese/English punctuation
    import re

    text = text.strip()
    if not text:
        return []
    # Split on common punctuation while keeping content
    parts = re.split(r"([。！？.!?])", text)
    merged: List[str] = []
    for i in range(0, len(parts), 2):
        seg = parts[i].strip()
        punct = parts[i + 1] if i + 1 < len(parts) else ""
        combined = (seg + punct).strip()
        if combined:
            merged.append(combined)
    # Fallback: if splitter produced nothing, return all
    return merged or [text]


async def stream_tts_ndjson(
    voice_service: VoiceService,
    text: str,
    speaker_id: int,
    max_concurrency: int = 2,
) -> AsyncGenerator[str, None]:
    """Generate NDJSON lines with base64-encoded audio for each sentence chunk."""

    sentences = _split_into_sentences(text)
    if not sentences:
        return

    semaphore = asyncio.Semaphore(max_concurrency)

    async def synthesize(idx: int, sentence: str) -> str:
        async with semaphore:
            try:
                wav = await voice_service.synthesize_voice(sentence, speaker_id)
                if not wav:
                    payload = {
                        "index": idx,
                        "text": sentence,
                        "bytes": 0,
                        "audio_b64": "",
                    }
                else:
                    payload = {
                        "index": idx,
                        "text": sentence,
                        "bytes": len(wav),
                        "audio_b64": base64.b64encode(wav).decode("ascii"),
                    }
                import json

                return json.dumps(payload, ensure_ascii=False) + "\n"
            except Exception as e:
                logger.error(f"TTS synth failed idx={idx}: {e}")
                import json

                return (
                    json.dumps(
                        {
                            "index": idx,
                            "text": sentence,
                            "bytes": 0,
                            "error": str(e),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

    tasks = [asyncio.create_task(synthesize(i, s)) for i, s in enumerate(sentences)]

    # Yield in completion order for lowest latency
    for coro in asyncio.as_completed(tasks):
        line = await coro
        yield line


