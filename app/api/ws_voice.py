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
    partial_task: Optional[asyncio.Task] = None
    ended: bool = False
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

        async def run_partial_loop():
            nonlocal audio_chunks, ended
            last_len = 0
            while not ended:
                await asyncio.sleep(0.4)
                try:
                    cur_len = sum(len(c) for c in audio_chunks)
                    if cur_len == 0 or cur_len == last_len:
                        continue
                    last_len = cur_len
                    # Use current aggregate buffer (limit size to avoid huge decode)
                    buf = b"".join(audio_chunks[-20:])  # last ~20 chunks
                    speech = get_speech_service(model_size="small", language="ja")
                    asr = await speech.transcribe_audio(buf, language="ja", enable_diarization=False)
                    ptxt = (asr.get("text") or "").strip()
                    if ptxt:
                        await websocket.send_json({"event": "asr_partial", "text": ptxt})
                except Exception:
                    # ignore partial errors
                    continue

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
                if partial_task is None or partial_task.done():
                    partial_task = asyncio.create_task(run_partial_loop())
            elif typ == "cancel_tts":
                # Cooperative cancel: set a flag consumed by streaming loop
                cancel = True
                await websocket.send_json({"event": "cancel_ack"})
            elif typ == "end":
                ended = True
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
                # best-effort cancel partial loop
                try:
                    if partial_task and not partial_task.done():
                        partial_task.cancel()
                except Exception:
                    pass
                await websocket.send_json({"event": "text", "text": text})

                # Generate reply + TTS (sentence-chunk streaming with cancel)
                try:
                    convo = get_conversation_service()
                    ai = await convo.groq_service.sales_analysis(text or "")
                    reply_text = ai.get("response") or "ありがとうございます。もう少し詳しく教えていただけますか？"
                    voice_service = await convo._get_or_init_voice_service()
                    # Prewarm to reduce first audio
                    try:
                        await voice_service.prewarm(speaker_id)
                    except Exception:
                        pass
                    # Sentence-level chunking for early playback
                    parts = []
                    for ch in ['。', '！', '？', '!','?']:
                        reply_text = reply_text.replace(ch, ch+'|')
                    parts = [p.strip().strip('|') for p in reply_text.split('|') if p and len(p.strip()) > 0]
                    if not parts:
                        parts = [reply_text]
                    cancel = False
                    for idx, seg in enumerate(parts):
                        if cancel:
                            break
                        try:
                            wav = await voice_service.synthesize_voice(text=seg, speaker_id=speaker_id)
                            await websocket.send_json({
                                "event": "tts",
                                "text": seg,
                                "index": idx,
                                "audio_b64": base64.b64encode(wav).decode("utf-8") if wav else "",
                            })
                        except Exception:
                            continue
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

