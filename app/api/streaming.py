"""
WebSocket endpoint for low-latency streaming ASR.

Events (JSON lines):
- {"type":"ready"}
- {"type":"partial","text":str,"confidence":float,"start_ms":int,"end_ms":int}
- {"type":"final","text":str,"confidence":float,"start_ms":int,"end_ms":int}
- {"type":"error","message":str}

Client sends raw binary PCM16 mono at 16kHz frames. Optionally, first message can be
JSON to configure {language?:"ja", sample_rate?:16000}.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

try:
    from services.streaming_asr_service import StreamingASRService
except ImportError:  # pragma: no cover
    from app.services.streaming_asr_service import StreamingASRService  # type: ignore

try:
    from services.metrics import append_jsonl, now_iso
except ImportError:  # pragma: no cover
    from app.services.metrics import append_jsonl, now_iso  # type: ignore


router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/voice")
async def ws_voice(websocket: WebSocket):
    await websocket.accept()
    service = StreamingASRService(language="ja", sample_rate=16000)
    session_started = now_iso()

    async def send_json(payload):
        await websocket.send_text(json.dumps(payload, ensure_ascii=False))

    await send_json({"type": "ready"})
    # Send default config ack so clients don't have to send an initial config
    await send_json({"type": "config_ack", "ok": True, "defaults": {"language": service.language, "sample_rate": service.sample_rate}})

    try:
        configured = False
        while True:
            message = await websocket.receive()

            # Disconnection
            if message.get("type") == "websocket.disconnect":
                break

            # Text message (potential config)
            if message.get("text") is not None:
                logger.info("ws/voice: received text message for config")
                if not configured:
                    try:
                        raw = message.get("text") or "{}"
                        config = json.loads(raw)
                        language = config.get("language")
                        sample_rate = config.get("sample_rate")
                        service.configure(language=language, sample_rate=sample_rate)
                        configured = True
                        logger.info("ws/voice: config applied, sending config_ack")
                        await send_json({"type": "config_ack", "ok": True})
                    except Exception as e:
                        logger.warning(f"ws/voice: invalid config: {e}")
                        await send_json({"type": "error", "message": f"invalid config: {e}"})
                else:
                    # Ignore subsequent text messages for now
                    pass
                continue

            # Binary audio chunk
            data = message.get("bytes")
            if data is not None and len(data) > 0:
                try:
                    partials = await service.feed_chunk(data)
                    for p in partials:
                        await send_json({
                            "type": "final" if p.is_final else "partial",
                            "text": p.text,
                            "confidence": p.confidence,
                            "start_ms": p.start_ms,
                            "end_ms": p.end_ms,
                        })
                        try:
                            append_jsonl({
                                "ts": now_iso(),
                                "kind": "ws_asr",
                                "event": "partial" if not p.is_final else "final",
                                "latency_ms": p.end_ms - p.start_ms,
                                "text_len": len(p.text),
                                "confidence": p.confidence,
                                "session_started": session_started,
                            })
                        except Exception:
                            pass
                except Exception as e:
                    await send_json({"type": "error", "message": str(e)})
                continue

            # Otherwise ignore
            continue

    except WebSocketDisconnect:
        logger.info("ws/voice disconnected")
    except Exception as e:
        logger.error(f"ws/voice error: {e}")
        try:
            await send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            final = await service.flush_final()
            if final and final.text:
                await send_json({
                    "type": "final",
                    "text": final.text,
                    "confidence": final.confidence,
                    "start_ms": final.start_ms,
                    "end_ms": final.end_ms,
                })
        except Exception:
            pass
        try:
            await websocket.close()
        except Exception:
            pass


