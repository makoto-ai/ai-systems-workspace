"""
営業ロールプレイ特化API
選定された10名のスピーカーと5つのシナリオを使用した営業練習システム
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator

try:
    from core.sales_speakers import (
        SALES_SPEAKERS,
        SALES_SCENARIOS,
        get_sales_speaker_list,
        get_speaker_by_scenario,
        get_all_scenarios,
    )
    from services.voice_service import VoiceService, VoiceServiceError
    from core.voicevox import VoicevoxConnectionError
except ImportError:
    from app.core.sales_speakers import (
        SALES_SPEAKERS,
        SALES_SCENARIOS,
        get_sales_speaker_list,
        get_speaker_by_scenario,
        get_all_scenarios,
    )
    from app.services.voice_service import VoiceService, VoiceServiceError
    from app.core.voicevox import VoicevoxConnectionError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sales", tags=["sales-roleplay"])


# リクエストモデル
class SalesTextToSpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, description="変換するテキスト")
    scenario: str = Field(
        ..., description="営業シナリオ（new_business, existing_customer, etc.）"
    )
    gender: Optional[str] = Field(
        "random", description="スピーカーの性別（male, female, random）"
    )
    emotion_level: Optional[str] = Field(
        "normal", description="感情レベル（normal, intense, gentle）"
    )

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("テキストは空にできません")
        return v.strip()

    @field_validator("scenario")
    @classmethod
    def scenario_must_be_valid(cls, v: str) -> str:
        if v not in SALES_SCENARIOS:
            valid_scenarios = list(SALES_SCENARIOS.keys())
            raise ValueError(
                f'無効なシナリオです。次の中から選択: {", ".join(valid_scenarios)}'
            )
        return v

    @field_validator("gender")
    @classmethod
    def gender_must_be_valid(cls, v: str) -> str:
        if v not in ["male", "female", "random"]:
            raise ValueError("性別は male, female, random のいずれかを指定してください")
        return v


class SalesScenarioRequest(BaseModel):
    scenario: str = Field(..., description="営業シナリオ名")
    customer_type: Optional[str] = Field(None, description="顧客タイプ（optional）")


# レスポンスモデル
class SpeakerInfo(BaseModel):
    id: int
    name: str
    character: str
    scenario: str
    best_use: str


class ScenarioInfo(BaseModel):
    name: str
    difficulty: str
    focus: str
    male_speaker: str
    female_speaker: str


# API エンドポイント
@router.get("/speakers", summary="営業特化スピーカー一覧")
async def get_sales_speakers() -> Dict[str, Any]:
    """営業ロールプレイに特化した10名のスピーカー一覧を取得"""
    try:
        speakers = get_sales_speaker_list()

        return {
            "status": "success",
            "total_speakers": len(speakers),
            "speakers": speakers,
            "categories": {
                "male_count": 5,
                "female_count": 5,
                "scenarios_supported": len(SALES_SCENARIOS),
            },
        }
    except Exception as e:
        logger.error(f"スピーカー一覧取得エラー: {e}")
        raise HTTPException(
            status_code=500, detail="スピーカー一覧の取得に失敗しました"
        )


@router.get("/scenarios", summary="営業シナリオ一覧")
async def get_sales_scenarios() -> Dict[str, Any]:
    """利用可能な営業シナリオ一覧を取得"""
    try:
        scenarios = get_all_scenarios()

        scenario_list = []
        for key, scenario in scenarios.items():
            scenario_list.append(
                {
                    "id": key,
                    "name": scenario["name"],
                    "difficulty": scenario["difficulty"],
                    "focus": scenario["focus"],
                    "male_speaker": scenario["male_speaker"],
                    "female_speaker": scenario["female_speaker"],
                }
            )

        return {
            "status": "success",
            "total_scenarios": len(scenario_list),
            "scenarios": scenario_list,
        }
    except Exception as e:
        logger.error(f"シナリオ一覧取得エラー: {e}")
        raise HTTPException(status_code=500, detail="シナリオ一覧の取得に失敗しました")


@router.get("/scenarios/{scenario_id}/speaker", summary="シナリオ別推奨スピーカー")
async def get_recommended_speaker(
    scenario_id: str, gender: str = "random"
) -> Dict[str, Any]:
    """指定されたシナリオに最適なスピーカーを取得"""
    try:
        if scenario_id not in SALES_SCENARIOS:
            raise HTTPException(
                status_code=404, detail="指定されたシナリオが見つかりません"
            )

        speaker = get_speaker_by_scenario(scenario_id, gender)
        scenario_info = SALES_SCENARIOS[scenario_id]

        return {
            "status": "success",
            "scenario": {
                "id": scenario_id,
                "name": scenario_info["name"],
                "difficulty": scenario_info["difficulty"],
                "focus": scenario_info["focus"],
            },
            "recommended_speaker": {
                "id": speaker["id"],
                "name": speaker["name"],
                "character": speaker["character"],
                "scenario": speaker["scenario"],
                "best_use": speaker["best_use"],
            },
        }
    except Exception as e:
        logger.error(f"推奨スピーカー取得エラー: {e}")
        raise HTTPException(
            status_code=500, detail="推奨スピーカーの取得に失敗しました"
        )


@router.post("/text-to-speech", summary="営業特化音声合成")
async def sales_text_to_speech(
    request: Request, req: SalesTextToSpeechRequest
) -> StreamingResponse:
    """営業シナリオに基づいた音声合成"""
    try:
        # シナリオに基づいてスピーカーを選択
        speaker = get_speaker_by_scenario(req.scenario, req.gender)
        if not speaker:
            raise HTTPException(
                status_code=404,
                detail="指定されたシナリオに対応するスピーカーが見つかりません",
            )

        speaker_id = speaker["id"]

        # Voice serviceの可用性確認（既存APIと同じ方式）
        if (
            not hasattr(request.app.state, "voice_service")
            or request.app.state.voice_service is None
        ):
            raise HTTPException(
                status_code=503,
                detail="Voice service not available. Please check VOICEVOX server connection.",
            )

        # 感情レベルに基づいて音声パラメータを調整
        emotion_params = _get_emotion_params(req.emotion_level)

        # 営業特化音声合成実行（既存APIと同じ方式）
        import io

        wav_data = await request.app.state.voice_service.synthesize_voice(
            text=req.text,
            speaker_id=speaker_id,
            emotion=emotion_params,
        )

        if not wav_data:
            raise HTTPException(status_code=500, detail="Failed to generate audio")

        # バイナリデータをストリーム形式に変換
        audio_stream = io.BytesIO(wav_data)

        logger.info(
            f"営業音声合成成功: scenario={req.scenario}, speaker={speaker['name']}, text_length={len(req.text)}"
        )

        # HTTPヘッダーは日本語をサポートしないため、Base64エンコード
        import base64

        speaker_name_b64 = base64.b64encode(speaker["name"].encode("utf-8")).decode(
            "ascii"
        )
        speaker_character_b64 = base64.b64encode(
            speaker["character"].encode("utf-8")
        ).decode("ascii")

        return StreamingResponse(
            audio_stream,
            media_type="audio/wav",
            headers={
                "X-Speaker-Name-B64": speaker_name_b64,
                "X-Speaker-Character-B64": speaker_character_b64,
                "X-Scenario": req.scenario,
                "X-Speaker-ID": str(speaker_id),
            },
        )

    except VoiceServiceError as e:
        logger.error(f"音声合成エラー: {e}")
        raise HTTPException(status_code=500, detail=f"音声合成に失敗しました: {str(e)}")
    except VoicevoxConnectionError as e:
        logger.error(f"VOICEVOX接続エラー: {e}")
        raise HTTPException(status_code=503, detail="音声エンジンに接続できません")
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        raise HTTPException(
            status_code=500, detail="音声合成処理中にエラーが発生しました"
        )


@router.post("/roleplay/start", summary="ロールプレイセッション開始")
async def start_roleplay_session(request: SalesScenarioRequest) -> Dict[str, Any]:
    """営業ロールプレイセッションを開始"""
    try:
        if request.scenario not in SALES_SCENARIOS:
            raise HTTPException(
                status_code=404, detail="指定されたシナリオが見つかりません"
            )

        scenario_info = SALES_SCENARIOS[request.scenario]

        # ランダムに男女のスピーカーを選択
        import random

        gender = random.choice(["male", "female"])
        speaker = get_speaker_by_scenario(request.scenario, gender)

        session_data = {
            "session_id": f"sales_{request.scenario}_{random.randint(1000, 9999)}",
            "scenario": {
                "id": request.scenario,
                "name": scenario_info["name"],
                "difficulty": scenario_info["difficulty"],
                "focus": scenario_info["focus"],
            },
            "ai_partner": {
                "speaker_id": speaker["id"],
                "name": speaker["name"],
                "character": speaker["character"],
                "role": "顧客役",
            },
            "tips": _get_scenario_tips(request.scenario),
            "started_at": "2024-07-31T09:00:00Z",  # 実際はdatetimeを使用
        }

        return {
            "status": "success",
            "message": "ロールプレイセッションを開始しました",
            "session": session_data,
        }

    except Exception as e:
        logger.error(f"セッション開始エラー: {e}")
        raise HTTPException(status_code=500, detail="セッションの開始に失敗しました")


# ヘルパー関数
def _get_emotion_params(emotion_level: str) -> Dict[str, float]:
    """感情レベルに基づいて音声パラメータを取得"""
    if emotion_level == "intense":
        return {"speed": 1.1, "pitch": 0.05, "intonation": 1.3, "volume": 1.1}
    elif emotion_level == "gentle":
        return {"speed": 0.9, "pitch": -0.02, "intonation": 0.8, "volume": 0.9}
    else:  # normal
        return {"speed": 1.0, "pitch": 0.0, "intonation": 1.0, "volume": 1.0}


def _get_scenario_tips(scenario: str) -> List[str]:
    """シナリオ別のアドバイスを取得"""
    tips_map = {
        "new_business": [
            "まずは信頼関係の構築から始めましょう",
            "相手のニーズを丁寧にヒアリングしてください",
            "押し売りではなく、価値提案を心がけてください",
        ],
        "existing_customer": [
            "既存の関係性を活かした提案をしてください",
            "過去の実績や成果を具体的に示しましょう",
            "アップセルの機会を見極めてください",
        ],
        "difficult_negotiation": [
            "冷静さを保ち、感情的にならないでください",
            "相手の懸念に真摯に向き合いましょう",
            "代替案や妥協点を準備してください",
        ],
        "closing": [
            "決断を促すタイミングを見極めてください",
            "最後の懸念事項をクリアにしましょう",
            "次のステップを明確に提示してください",
        ],
        "consultation": [
            "相手の不安に寄り添ってください",
            "十分な情報提供で安心感を与えましょう",
            "急かすことなく、じっくりと対話してください",
        ],
    }

    return tips_map.get(scenario, ["頑張ってください！"])


@router.get("/health", summary="営業API健康状態")
async def health_check():
    """営業特化APIの健康状態をチェック"""
    try:
        # 基本的な設定確認
        speakers_count = len(get_sales_speaker_list())
        scenarios_count = len(get_all_scenarios())

        return {
            "status": "healthy",
            "speakers_loaded": speakers_count,
            "scenarios_loaded": scenarios_count,
            "timestamp": "2024-07-31T09:00:00Z",
        }
    except Exception as e:
        logger.error(f"健康状態チェックエラー: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-07-31T09:00:00Z",
        }
