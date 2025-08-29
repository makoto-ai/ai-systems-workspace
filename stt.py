"""
Speech-to-Text provider abstraction.

Primary: Groq (whisper-large-v3)
Fallback: WhisperX HTTP API (if WHISPERX_ENDPOINT is set)

Usage:
    from stt import transcribe
    text = transcribe("/path/to/audio.mp3")
"""
from __future__ import annotations

import os
import requests
from typing import Optional

try:
    # ローカルのみ: .env があれば読み込む（CIではSecretsで注入される想定）
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass


GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
WHISPERX_ENDPOINT: Optional[str] = os.getenv("WHISPERX_ENDPOINT")


def _post_groq(audio_path: str) -> Optional[str]:
    if not GROQ_API_KEY:
        return None
    try:
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, "application/octet-stream")}
            data = {"model": "whisper-large-v3"}
            resp = requests.post(
                url,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                files=files,
                data=data,
                timeout=120,
            )
        resp.raise_for_status()
        body = resp.json()
        return body.get("text")
    except Exception:
        return None


def _normalize_whisperx_url(endpoint: str) -> str:
    # ユーザーがベースURLを渡している場合は /transcribe を付与
    if endpoint.rstrip("/").endswith("/transcribe"):
        return endpoint
    return endpoint.rstrip("/") + "/transcribe"


def _post_whisperx(audio_path: str) -> Optional[str]:
    if not WHISPERX_ENDPOINT:
        return None
    try:
        url = _normalize_whisperx_url(WHISPERX_ENDPOINT)
        with open(audio_path, "rb") as f:
            # whisperx_api.py は 'audio' フィールドを期待
            files = {"audio": (os.path.basename(audio_path), f, "application/octet-stream")}
            resp = requests.post(url, files=files, timeout=180)
        resp.raise_for_status()
        body = resp.json()
        return body.get("text") or body.get("result") or ""
    except Exception:
        return None


def transcribe(audio_path: str) -> str:
    """Transcribe audio file to text.

    - Tries Groq first when GROQ_API_KEY is available
    - Falls back to WhisperX HTTP endpoint if configured
    """
    text = _post_groq(audio_path)
    if text:
        return text

    text = _post_whisperx(audio_path)
    if text:
        return text

    raise RuntimeError(
        "No STT available: set GROQ_API_KEY or WHISPERX_ENDPOINT"
    )


__all__ = ["transcribe"]


