from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Literal
from pathlib import Path
from datetime import datetime
import re
import os

try:
    from services.voice_service import (
        VoiceService,
        VoiceServiceError,
        SpeakerNotFoundError,
    )
    from core.speakers import MALE_SALES
    from core.voicevox import EmotionParams, Speaker, VoicevoxConnectionError
except ImportError:
    from app.services.voice_service import (
        VoiceService,
        VoiceServiceError,
        SpeakerNotFoundError,
    )
    from app.core.speakers import MALE_SALES
    from app.core.voicevox import EmotionParams, Speaker, VoicevoxConnectionError
import base64
import io

router = APIRouter()


class EmotionRequest(BaseModel):
    preset: Optional[str] = Field(
        None, description="感情プリセット（happy, sad, angry, surprised）"
    )
    pitch: Optional[float] = Field(
        None, ge=-0.15, le=0.15, description="ピッチの変化（-0.15 ~ 0.15）"
    )
    speed: Optional[float] = Field(
        None, ge=0.5, le=2.0, description="話速（0.5 ~ 2.0）"
    )
    intonation: Optional[float] = Field(
        None, ge=0.0, le=2.0, description="イントネーションの強さ（0.0 ~ 2.0）"
    )
    volume: Optional[float] = Field(
        None, ge=0.0, le=2.0, description="音量（0.0 ~ 2.0）"
    )
    pre_phoneme: Optional[float] = Field(
        None, ge=0.0, le=1.5, description="開始無音（0.0 ~ 1.5）"
    )
    post_phoneme: Optional[float] = Field(
        None, ge=0.0, le=1.5, description="終了無音（0.0 ~ 1.5）"
    )


class TextToSpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, description="変換するテキスト（空文字不可）")
    speaker_id: int = Field(..., description="話者ID")
    emotion: Optional[str] = Field(
        None, description="感情（happy, sad, angry, surprised）"
    )

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Text must not be empty")
        return v

    @field_validator("emotion")
    @classmethod
    def emotion_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_emotions = ["happy", "sad", "angry", "surprised"]
            if v.lower() not in valid_emotions:
                raise ValueError(
                    f'Invalid emotion. Must be one of: {", ".join(valid_emotions)}'
                )
        return v


# OpenAI互換のTTSリクエストモデル
class OpenAITTSRequest(BaseModel):
    model: str
    input: str
    voice: str = "2"  # デフォルトは四国めたん
    response_format: Literal["mp3", "opus", "aac", "flac"] = "mp3"
    speed: Optional[float] = 1.0


@router.post("/reply_text")
async def reply_text(request: Request, text_input: str) -> Dict[str, Any]:
    try:
        base = (text_input or "").strip().replace("\n", " ")
        if not base:
            base = "承知しました。続けてどうぞ。"
        reply = f"承知しました。『{base[:80]}』への回答です。"
        return {"output": {"text": reply}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate")
async def simulate_tts(request: Request, text_input: str, speaker_id: int = 2) -> Dict[str, Any]:
    try:
        if (
            not hasattr(request.app.state, "voice_service")
            or request.app.state.voice_service is None
        ):
            raise HTTPException(status_code=503, detail="Voice service not available")
        wav = await request.app.state.voice_service.synthesize_voice(
            text=text_input or "承知しました。続けてどうぞ。", speaker_id=speaker_id
        )
        if not wav:
            raise HTTPException(status_code=500, detail="Failed to generate audio")
        b64 = base64.b64encode(wav).decode("utf-8")
        return {"output": {"audio_data": b64, "text": text_input}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/speakers")
async def get_speakers(request: Request) -> Dict[str, Any]:
    """利用可能な話者の一覧を取得する"""
    try:
        # Check if voice service is available
        if (
            not hasattr(request.app.state, "voice_service")
            or request.app.state.voice_service is None
        ):
            return {
                "speakers": [],
                "total_speakers": 0,
                "message": "Voice service not available. VOICEVOX server may not be running.",
                "status": "unavailable",
            }
        return await request.app.state.voice_service.get_speakers()
    except VoiceServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except VoicevoxConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


class ConversationLiteRequest(BaseModel):
    input: str = Field(..., min_length=1, description="ユーザーの発話（テキスト）")
    speaker_id: int = Field(..., description="話者ID")
    system_prompt: Optional[str] = Field(None, description="応答方針（任意）")


@router.post("/conversation-lite")
async def conversation_lite(request: Request, req: ConversationLiteRequest) -> Response:
    """最小1往復: text->LLM->TTS（高速フォールバック内蔵）"""
    try:
        # 応答テキスト生成（MCPがあれば利用、なければ軽量テンプレート）
        reply_text = None
        try:
            if hasattr(request.app.state, "mcp_generator") and request.app.state.mcp_generator:
                mcp = request.app.state.mcp_generator
                payload = {"title": "conversation-lite", "content": req.input, "style": "concise"}
                gen = await mcp.generate_script(payload)
                # 生成結果から短く要約（先頭200文字）
                reply_text = (gen or "").strip()[:200] or None
        except Exception:
            reply_text = None
        if not reply_text:
            # フォールバック（丁寧+簡潔）
            base = req.input.strip().replace("\n", " ")[:80]
            reply_text = f"承知しました。『{base}』について要点をまとめて対応します。"

        # 音声合成
        wav_data = await request.app.state.voice_service.synthesize_voice(
            text=reply_text, speaker_id=req.speaker_id
        )
        if not wav_data:
            raise HTTPException(status_code=500, detail="Failed to generate audio")

        # 保存（public）
        try:
            project_root = Path(__file__).resolve().parents[2]
            public_dir = project_root / "public"
            public_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y年%m月%d日_%H時%M分%S秒")
            head = reply_text.strip()[:12]
            head = re.sub(r"[\\/:*?\"<>|\n\r]", "_", head)
            fname = f"{ts}_会話応答_話者{req.speaker_id}_{head or '音声'}.wav"
            (public_dir / fname).write_bytes(wav_data)
        except Exception:
            pass

        return Response(content=wav_data, media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/text-to-speech")
async def text_to_speech(request: Request, req: TextToSpeechRequest) -> Response:
    """テキストを音声に変換する"""
    try:
        # 感情パラメータの設定
        emotion_params = None
        if req.emotion:
            emotion_map = {
                "happy": EmotionParams.happy(),
                "sad": EmotionParams.sad(),
                "angry": EmotionParams.angry(),
                "surprised": EmotionParams.surprised(),
            }
            emotion_params = emotion_map.get(req.emotion.lower())

        # Check if voice service is available
        if (
            not hasattr(request.app.state, "voice_service")
            or request.app.state.voice_service is None
        ):
            raise HTTPException(
                status_code=503,
                detail="Voice service not available. Please check VOICEVOX server connection.",
            )

        # 音声合成を実行
        wav_data = await request.app.state.voice_service.synthesize_voice(
            text=req.text, speaker_id=req.speaker_id, emotion=emotion_params
        )

        if not wav_data:
            raise HTTPException(status_code=500, detail="Failed to generate audio")

        # 生成音声を public/ に保存（日本語名）
        try:
            project_root = Path(__file__).resolve().parents[2]
            public_dir = project_root / "public"
            public_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y年%m月%d日_%H時%M分%S秒")
            # テキスト先頭を短く取り、ファイル名に不適切な記号を除去
            head = req.text.strip()[:12]
            head = re.sub(r"[\\/:*?\"<>|\n\r]", "_", head)
            fname = f"{ts}_話者{req.speaker_id}_{head or '音声'}.wav"
            out_path = public_dir / fname
            with open(out_path, "wb") as f:
                f.write(wav_data)
        except Exception:
            # 保存失敗は応答に影響させない
            pass

        # WAVファイルとして返す
        return Response(
            content=wav_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f'attachment; filename="voice_{req.speaker_id}_{hash(req.text)}.wav"'
            },
        )

    except SpeakerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except VoiceServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except VoicevoxConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/audio/speech")
async def openai_compatible_tts(request: Request, req: OpenAITTSRequest) -> Response:
    """OpenAI互換のTTSエンドポイント"""
    try:
        # 話者IDを取得
        # OpenAI互換のため、文字列の場合はマッピングを使用
        voice_mapping = {
            "alloy": 1,
            "echo": 2,
            "fable": 3,
            "onyx": 4,
            "nova": 5,
            "shimmer": 1,  # デフォルトは1
        }

        # 数値文字列の場合は直接変換、それ以外はマッピングを使用
        try:
            speaker_id = int(req.voice)
        except ValueError:
            speaker_id = voice_mapping.get(req.voice.lower(), 1)

        # 音声合成を実行
        wav_data = await request.app.state.voice_service.synthesize_voice(
            text=req.input, speaker_id=speaker_id
        )

        if not wav_data:
            raise HTTPException(status_code=500, detail="Failed to generate audio")

        # 生成音声を public/ に保存（日本語名）
        try:
            project_root = Path(__file__).resolve().parents[2]
            public_dir = project_root / "public"
            public_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y年%m月%d日_%H時%M分%S秒")
            head = req.input.strip()[:12]
            head = re.sub(r"[\\/:*?\"<>|\n\r]", "_", head)
            fname = f"{ts}_話者{speaker_id}_{head or '音声'}.wav"
            out_path = public_dir / fname
            with open(out_path, "wb") as f:
                f.write(wav_data)
        except Exception:
            pass

        # レスポンスフォーマットに応じたContent-Typeを設定
        content_type_map = {
            "mp3": "audio/mpeg",
            "opus": "audio/opus",
            "aac": "audio/aac",
            "flac": "audio/flac",
        }
        content_type = content_type_map.get(req.response_format, "audio/mpeg")

        # 現在はWAVフォーマットのみサポート
        # TODO: 他のフォーマットへの変換サポートを追加
        return Response(
            content=wav_data,
            media_type="audio/wav",  # 実際はWAVを返す
            headers={
                "Content-Disposition": f'attachment; filename="voice_{speaker_id}.wav"'
            },
        )

    except SpeakerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except VoiceServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except VoicevoxConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/audio/speech-json")
async def dify_compatible_tts(
    request: Request, req: OpenAITTSRequest
) -> Dict[str, Any]:
    """Dify互換のTTSエンドポイント（Base64エンコードされたJSONレスポンス）"""
    try:
        # 話者IDを取得（デフォルトは2：四国めたん）
        speaker_id = int(req.voice)

        # 音声合成を実行
        wav_data = await request.app.state.voice_service.synthesize_voice(
            text=req.input, speaker_id=speaker_id
        )

        if not wav_data:
            raise HTTPException(status_code=500, detail="Failed to generate audio")

        # Base64エンコード
        audio_base64 = base64.b64encode(wav_data).decode("utf-8")

        # JSONレスポンスを返す
        return {
            "audio_data": audio_base64,
            "speaker_id": speaker_id,
            "text": req.input,
            "format": "wav",
            "size": len(wav_data),
        }

    except SpeakerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except VoiceServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except VoicevoxConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
