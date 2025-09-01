from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional, Dict, Any
import base64
import asyncio

router = APIRouter()


@router.websocket("/ws/voice")
async def ws_voice(websocket: WebSocket):
    await websocket.accept()
    audio_chunks: list[bytes] = []
    speaker_id: int = 2
    try:
        # Lazy imports to avoid circular deps at startup
        try:
            from services.speech_service import get_speech_service
            from services.conversation_service import get_conversation_service
        except Exception:
            from app.services.speech_service import get_speech_service
            from app.services.conversation_service import get_conversation_service

        # signal ready
        await websocket.send_json({"event": "ready"})

        while True:
            msg = await websocket.receive_text()
            # Expect JSON frames
            data: Dict[str, Any]
            try:
                import json
                data = json.loads(msg)
            except Exception:
                await websocket.send_json({"event": "error", "detail": "invalid_json"})
                continue

            typ = data.get("type")
            if typ == "start":
                sid = data.get("speaker_id")
                if isinstance(sid, int):
                    speaker_id = sid
                await websocket.send_json({"event": "started", "speaker_id": speaker_id})
            elif typ == "chunk":
                a64 = data.get("audio_b64", "")
                if not a64:
                    continue
                try:
                    audio_chunks.append(base64.b64decode(a64))
                except Exception:
                    await websocket.send_json({"event": "error", "detail": "invalid_audio"})
                    continue
            elif typ == "end":
                # Transcribe accumulated audio
                audio_data = b"".join(audio_chunks)
                audio_chunks.clear()
                try:
                    speech = get_speech_service(model_size="small", language="ja")
                    asr = await speech.transcribe_audio(audio_data, language="ja", enable_diarization=False)
                    text = (asr.get("text") or "").strip()
                except Exception as e:
                    await websocket.send_json({"event": "error", "detail": f"asr_failed:{e}"})
                    text = ""

                await websocket.send_json({"event": "text", "text": text})

                # Generate reply + TTS (single-chunk for MVP)
                try:
                    convo = get_conversation_service()
                    # Initialize voice service if available via app state is not accessible in WS
                    # The service object inside conversation service should already know how to obtain voice service
                    ai = await convo.groq_service.sales_analysis(text or "")
                    reply_text = ai.get("response") or "ありがとうございます。もう少し詳しく教えていただけますか？"
                    voice_service = await convo._get_or_init_voice_service()
                    wav = await voice_service.synthesize_voice(text=reply_text, speaker_id=speaker_id)
                    await websocket.send_json({
                        "event": "tts",
                        "text": reply_text,
                        "audio_b64": base64.b64encode(wav).decode("utf-8") if wav else "",
                    })
                except Exception as e:
                    await websocket.send_json({"event": "error", "detail": f"tts_failed:{e}"})
                # Turn completed
                await websocket.send_json({"event": "done"})
            else:
                await websocket.send_json({"event": "error", "detail": "unknown_type"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"event": "error", "detail": f"ws_exception:{e}"})
        except Exception:
            pass

