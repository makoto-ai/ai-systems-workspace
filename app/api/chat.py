from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Optional, Literal
import asyncio
import base64
import time

router = APIRouter()


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: Optional[bool] = False
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None


class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict]
    usage: Dict[str, int]


@router.post("/chat/completions")
async def chat_completion(request: Request, req: ChatRequest):
    """OpenAI互換のチャット完了エンドポイント（音声合成統合）"""
    try:
        # 最後のユーザーメッセージを取得
        user_input = req.messages[-1].content

        # 音声合成を実行
        if (
            not hasattr(request.app.state, "voice_service")
            or request.app.state.voice_service is None
        ):
            raise HTTPException(status_code=503, detail="Voice service not available")

        wav_data = await request.app.state.voice_service.synthesize_voice(
            text=user_input, speaker_id=2  # 四国めたん
        )

        if not wav_data:
            raise HTTPException(status_code=500, detail="Failed to generate audio")

        # 音声データをBase64エンコード
        audio_base64 = base64.b64encode(wav_data).decode("utf-8")

        return ChatResponse(
            id=f"voicevox-{hash(user_input)}",
            created=int(time.time()),
            model=req.model,
            choices=[
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": user_input,
                        "function_call": {
                            "name": "play_audio",
                            "arguments": {"audio_data": audio_base64, "format": "wav"},
                        },
                    },
                    "finish_reason": "stop",
                }
            ],
            usage={
                "prompt_tokens": len(user_input),
                "completion_tokens": len(user_input),
                "total_tokens": len(user_input) * 2,
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
