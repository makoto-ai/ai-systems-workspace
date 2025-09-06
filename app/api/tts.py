"""
Streaming TTS API (NDJSON)

POST /api/tts/stream
body: { text: string, speaker_id: number }

returns: NDJSON lines with fields {index, text, bytes, audio_b64}
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Any, Dict
import asyncio

try:
    from services.tts_streamer import stream_tts_ndjson
except ImportError:  # pragma: no cover
    from app.services.tts_streamer import stream_tts_ndjson  # type: ignore

try:
    from services.metrics import append_jsonl, now_iso
except ImportError:  # pragma: no cover
    from app.services.metrics import append_jsonl, now_iso  # type: ignore


router = APIRouter()


class StreamTTSRequest(BaseModel):
    text: str = Field(..., min_length=1)
    speaker_id: int = Field(...)


@router.post("/tts/stream")
async def tts_stream(request: Request, body: StreamTTSRequest):
    if not hasattr(request.app.state, "voice_service") or request.app.state.voice_service is None:
        raise HTTPException(status_code=503, detail="Voice service not available")

    voice_service = request.app.state.voice_service

    async def generator():
        started = now_iso()
        idx = 0
        async for line in stream_tts_ndjson(voice_service, body.text, body.speaker_id):
            try:
                append_jsonl({
                    "ts": now_iso(),
                    "kind": "http_tts",
                    "event": "chunk",
                    "index": idx,
                    "text_len": len(body.text),
                    "speaker_id": body.speaker_id,
                    "started": started,
                })
            except Exception:
                pass
            idx += 1
            yield line

    headers = {"Content-Type": "application/x-ndjson; charset=utf-8"}
    return StreamingResponse(generator(), headers=headers, media_type="application/x-ndjson")


