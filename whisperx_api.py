#!/usr/bin/env python3
"""
WhisperX simple inference API (FastAPI)

Endpoints:
- GET /health: returns status and model readiness
- POST /transcribe: multipart/form-data with 'audio' (UploadFile), optional 'language'

Environment variables (optional):
- WHISPERX_MODEL: whisper/whisperx model name (default: large-v2)
- WHISPERX_DEVICE: cpu | cuda (default: cpu)
- WHISPERX_COMPUTE_TYPE: int8 | int8_float16 | float16 | float32 (default: int8)
"""
from __future__ import annotations

import os
import tempfile
from typing import Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse

import whisperx  # type: ignore


app = FastAPI(title="WhisperX API", version="1.0.0")


class WhisperXService:
    """Lazy-initialized WhisperX ASR service."""

    def __init__(self) -> None:
        self.model_name: str = os.getenv("WHISPERX_MODEL", "large-v2")
        self.device: str = os.getenv("WHISPERX_DEVICE", "cpu")
        self.compute_type: str = os.getenv("WHISPERX_COMPUTE_TYPE", "int8")
        self._asr_model = None
        self._align_model = None
        self._align_metadata = None

    @property
    def ready(self) -> bool:
        return self._asr_model is not None

    def ensure_loaded(self) -> None:
        if self._asr_model is None:
            self._asr_model = whisperx.load_model(
                self.model_name, device=self.device, compute_type=self.compute_type
            )

    def _ensure_align_loaded(self, language_code: str) -> None:
        if self._align_model is None or self._align_metadata is None:
            self._align_model, self._align_metadata = whisperx.load_align_model(
                language_code=language_code, device=self.device
            )

    def transcribe(self, input_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        self.ensure_loaded()

        audio = whisperx.load_audio(input_path)
        result = self._asr_model.transcribe(
            audio,
            batch_size=16,
            language=language,
        )

        lang_code = result.get("language", language) or "ja"
        self._ensure_align_loaded(lang_code)

        result_aligned = whisperx.align(
            result["segments"],
            self._align_model,
            self._align_metadata,
            audio,
            self.device,
            return_char_alignments=False,
        )

        return {
            "language": lang_code,
            "text": result.get("text", ""),
            "segments": result_aligned.get("segments", result.get("segments", [])),
        }


service = WhisperXService()


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "model": service.model_name,
            "device": service.device,
            "compute_type": service.compute_type,
            "ready": service.ready,
        }
    )


@app.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
) -> JSONResponse:
    suffix = os.path.splitext(audio.filename or "audio.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp.flush()

        try:
            result = service.transcribe(tmp.name, language=language)
            return JSONResponse({"ok": True, **result})
        except Exception as e:  # noqa: BLE001
            return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "5000")))


