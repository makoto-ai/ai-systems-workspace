from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Literal
from pathlib import Path
try:
    from services.voice_service import VoiceService, VoiceServiceError, SpeakerNotFoundError
    from core.speakers import MALE_SALES
    from core.voicevox import EmotionParams, Speaker, VoicevoxConnectionError
except ImportError:
    from app.services.voice_service import VoiceService, VoiceServiceError, SpeakerNotFoundError
    from app.core.speakers import MALE_SALES
    from app.core.voicevox import EmotionParams, Speaker, VoicevoxConnectionError
import base64
import io

router = APIRouter()

class EmotionRequest(BaseModel):
    preset: Optional[str] = Field(None, description="感情プリセット（happy, sad, angry, surprised）")
    pitch: Optional[float] = Field(None, ge=-0.15, le=0.15, description="ピッチの変化（-0.15 ~ 0.15）")
    speed: Optional[float] = Field(None, ge=0.5, le=2.0, description="話速（0.5 ~ 2.0）")
    intonation: Optional[float] = Field(None, ge=0.0, le=2.0, description="イントネーションの強さ（0.0 ~ 2.0）")
    volume: Optional[float] = Field(None, ge=0.0, le=2.0, description="音量（0.0 ~ 2.0）")
    pre_phoneme: Optional[float] = Field(None, ge=0.0, le=1.5, description="開始無音（0.0 ~ 1.5）")
    post_phoneme: Optional[float] = Field(None, ge=0.0, le=1.5, description="終了無音（0.0 ~ 1.5）")

class TextToSpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, description="変換するテキスト（空文字不可）")
    speaker_id: int = Field(..., description="話者ID")
    emotion: Optional[str] = Field(None, description="感情（happy, sad, angry, surprised）")
    
    @field_validator('text')
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Text must not be empty')
        return v
    
    @field_validator('emotion')
    @classmethod
    def emotion_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_emotions = ['happy', 'sad', 'angry', 'surprised']
            if v.lower() not in valid_emotions:
                raise ValueError(f'Invalid emotion. Must be one of: {", ".join(valid_emotions)}')
        return v

# OpenAI互換のTTSリクエストモデル
class OpenAITTSRequest(BaseModel):
    model: str
    input: str
    voice: str = "2"  # デフォルトは四国めたん
    response_format: Literal["mp3", "opus", "aac", "flac"] = "mp3"
    speed: Optional[float] = 1.0

@router.get("/speakers")
async def get_speakers(request: Request) -> Dict[str, Any]:
    """利用可能な話者の一覧を取得する"""
    try:
        # Check if voice service is available
        if not hasattr(request.app.state, 'voice_service') or request.app.state.voice_service is None:
            return {
                "speakers": [],
                "total_speakers": 0,
                "message": "Voice service not available. VOICEVOX server may not be running.",
                "status": "unavailable"
            }
        return await request.app.state.voice_service.get_speakers()
    except VoiceServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except VoicevoxConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
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
                "surprised": EmotionParams.surprised()
            }
            emotion_params = emotion_map.get(req.emotion.lower())

        # Check if voice service is available
        if not hasattr(request.app.state, 'voice_service') or request.app.state.voice_service is None:
            raise HTTPException(
                status_code=503, 
                detail="Voice service not available. Please check VOICEVOX server connection."
            )

        # 音声合成を実行
        wav_data = await request.app.state.voice_service.synthesize_voice(
            text=req.text,
            speaker_id=req.speaker_id,
            emotion=emotion_params
        )

        if not wav_data:
            raise HTTPException(status_code=500, detail="Failed to generate audio")

        # WAVファイルとして返す
        return Response(
            content=wav_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f'attachment; filename="voice_{req.speaker_id}_{hash(req.text)}.wav"'
            }
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
            "shimmer": 1  # デフォルトは1
        }
        
        # 数値文字列の場合は直接変換、それ以外はマッピングを使用
        try:
            speaker_id = int(req.voice)
        except ValueError:
            speaker_id = voice_mapping.get(req.voice.lower(), 1)

        # 音声合成を実行
        wav_data = await request.app.state.voice_service.synthesize_voice(
            text=req.input,
            speaker_id=speaker_id
        )

        if not wav_data:
            raise HTTPException(status_code=500, detail="Failed to generate audio")

        # レスポンスフォーマットに応じたContent-Typeを設定
        content_type_map = {
            "mp3": "audio/mpeg",
            "opus": "audio/opus",
            "aac": "audio/aac",
            "flac": "audio/flac"
        }
        content_type = content_type_map.get(req.response_format, "audio/mpeg")

        # 現在はWAVフォーマットのみサポート
        # TODO: 他のフォーマットへの変換サポートを追加
        return Response(
            content=wav_data,
            media_type="audio/wav",  # 実際はWAVを返す
            headers={
                "Content-Disposition": f'attachment; filename="voice_{speaker_id}.wav"'
            }
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
async def dify_compatible_tts(request: Request, req: OpenAITTSRequest) -> Dict[str, Any]:
    """Dify互換のTTSエンドポイント（Base64エンコードされたJSONレスポンス）"""
    try:
        # 話者IDを取得（デフォルトは2：四国めたん）
        speaker_id = int(req.voice)

        # 音声合成を実行
        wav_data = await request.app.state.voice_service.synthesize_voice(
            text=req.input,
            speaker_id=speaker_id
        )

        if not wav_data:
            raise HTTPException(status_code=500, detail="Failed to generate audio")

        # Base64エンコード
        audio_base64 = base64.b64encode(wav_data).decode('utf-8')

        # JSONレスポンスを返す
        return {
            "audio_data": audio_base64,
            "speaker_id": speaker_id,
            "text": req.input,
            "format": "wav",
            "size": len(wav_data)
        }

    except SpeakerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except VoiceServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except VoicevoxConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")