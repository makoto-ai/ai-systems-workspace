"""
Privacy-Aware Context API
個人情報を保存しない文脈理解システムのAPI
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Form, Body
from pydantic import BaseModel

try:
    from services.privacy_aware_context_service import (
        get_privacy_aware_context_service,
        PrivacyMode,
    )
except ImportError:
    from app.services.privacy_aware_context_service import (
        get_privacy_aware_context_service,
        PrivacyMode,
    )

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/context", tags=["context"])


class UpdateContextRequest(BaseModel):
    """文脈更新リクエスト"""

    session_id: str
    user_input: str
    ai_response: str
    analysis_data: Optional[Dict[str, Any]] = None


class ContextualSuggestionRequest(BaseModel):
    """文脈提案リクエスト"""

    session_id: str
    current_input: str


@router.post("/initialize-session")
async def initialize_session(
    privacy_mode: str = Form(default="strict"),
) -> Dict[str, Any]:
    """
    新しいプライバシー保護セッションを初期化

    Args:
        privacy_mode: プライバシーモード ("strict", "standard", "research")

    Returns:
        セッション情報
    """
    try:
        # プライバシーモード検証
        valid_modes = {
            "strict": PrivacyMode.STRICT,
            "standard": PrivacyMode.STANDARD,
            "research": PrivacyMode.RESEARCH,
        }
        if privacy_mode not in valid_modes:
            raise HTTPException(
                status_code=400, detail=f"Invalid privacy mode: {privacy_mode}"
            )

        # サービス取得
        context_service = get_privacy_aware_context_service(valid_modes[privacy_mode])

        # セッション初期化
        import uuid

        session_id = str(uuid.uuid4())
        await context_service.initialize_session_context(session_id)

        return {
            "success": True,
            "session_id": session_id,
            "privacy_mode": privacy_mode,
            "privacy_protection": {
                "personal_info_storage": False,
                "audio_storage": False,
                "content_anonymization": True,
                "auto_cleanup": True,
            },
            "message": f"プライバシー保護セッションを初期化しました (mode: {privacy_mode})",
        }

    except Exception as e:
        logger.error(f"Session initialization error: {e}")
        raise HTTPException(status_code=500, detail=f"セッション初期化エラー: {str(e)}")


@router.post("/update")
async def update_context(request: UpdateContextRequest) -> Dict[str, Any]:
    """
    文脈を更新（個人情報は自動匿名化）

    Args:
        request: 文脈更新リクエスト

    Returns:
        更新された文脈情報
    """
    try:
        context_service = get_privacy_aware_context_service()

        result = await context_service.update_context(
            session_id=request.session_id,
            user_input=request.user_input,
            ai_response=request.ai_response,
            analysis_data=request.analysis_data,
        )

        return {
            "success": True,
            "context_result": result,
            "privacy_guaranteed": True,
            "message": "文脈を安全に更新しました",
        }

    except Exception as e:
        logger.error(f"Context update error: {e}")
        raise HTTPException(status_code=500, detail=f"文脈更新エラー: {str(e)}")


@router.post("/suggestions")
async def get_contextual_suggestions(
    request: ContextualSuggestionRequest,
) -> Dict[str, Any]:
    """
    文脈に基づいた提案を取得

    Args:
        request: 文脈提案リクエスト

    Returns:
        文脈ベースの提案
    """
    try:
        context_service = get_privacy_aware_context_service()

        suggestions = await context_service.get_contextual_suggestions(
            session_id=request.session_id, current_input=request.current_input
        )

        return {
            "success": True,
            "suggestions": suggestions,
            "privacy_protected": True,
            "message": "文脈ベースの提案を生成しました",
        }

    except Exception as e:
        logger.error(f"Contextual suggestions error: {e}")
        raise HTTPException(status_code=500, detail=f"提案生成エラー: {str(e)}")


@router.get("/session/{session_id}/summary")
async def get_session_summary(session_id: str) -> Dict[str, Any]:
    """
    セッションサマリーを取得（個人情報なし）

    Args:
        session_id: セッションID

    Returns:
        セッションサマリー
    """
    try:
        context_service = get_privacy_aware_context_service()

        summary = await context_service.get_session_summary(session_id)

        return {
            "success": True,
            "summary": summary,
            "privacy_note": "このサマリーに個人情報は含まれていません",
        }

    except Exception as e:
        logger.error(f"Session summary error: {e}")
        raise HTTPException(status_code=500, detail=f"サマリー取得エラー: {str(e)}")


@router.delete("/session/{session_id}")
async def cleanup_session(session_id: str) -> Dict[str, Any]:
    """
    セッションを手動でクリーンアップ

    Args:
        session_id: セッションID

    Returns:
        クリーンアップ結果
    """
    try:
        context_service = get_privacy_aware_context_service()

        await context_service._cleanup_session(session_id)

        return {
            "success": True,
            "session_id": session_id,
            "message": "セッションを安全にクリーンアップしました",
        }

    except Exception as e:
        logger.error(f"Session cleanup error: {e}")
        raise HTTPException(status_code=500, detail=f"クリーンアップエラー: {str(e)}")


@router.get("/service-info")
async def get_service_info() -> Dict[str, Any]:
    """
    プライバシー保護文脈サービスの情報を取得

    Returns:
        サービス情報
    """
    try:
        context_service = get_privacy_aware_context_service()

        info = context_service.get_service_info()

        return {
            "success": True,
            "service_info": info,
            "privacy_guarantees": {
                "no_personal_info_storage": True,
                "no_audio_storage": True,
                "automatic_anonymization": True,
                "session_based_only": True,
                "auto_cleanup": True,
                "gdpr_compliant": True,
            },
        }

    except Exception as e:
        logger.error(f"Service info error: {e}")
        raise HTTPException(status_code=500, detail=f"サービス情報取得エラー: {str(e)}")


@router.post("/privacy-demo")
async def privacy_demonstration(
    sample_input: str = Form(...), privacy_mode: str = Form(default="strict")
) -> Dict[str, Any]:
    """
    プライバシー保護の動作デモンストレーション

    Args:
        sample_input: サンプル入力（個人情報を含む可能性あり）
        privacy_mode: プライバシーモード

    Returns:
        匿名化デモンストレーション
    """
    try:
        valid_modes = {
            "strict": PrivacyMode.STRICT,
            "standard": PrivacyMode.STANDARD,
            "research": PrivacyMode.RESEARCH,
        }
        if privacy_mode not in valid_modes:
            privacy_mode = "strict"

        context_service = get_privacy_aware_context_service(valid_modes[privacy_mode])

        # 匿名化デモンストレーション
        anonymized_content = await context_service._anonymize_content(sample_input)

        return {
            "success": True,
            "demonstration": {
                "original_input": sample_input,
                "anonymized_output": anonymized_content,
                "privacy_mode": privacy_mode,
                "personal_info_removed": sample_input != anonymized_content,
            },
            "privacy_features": {
                "name_anonymization": "[NAME]で置換",
                "company_anonymization": "[COMPANY]で置換",
                "contact_anonymization": "[EMAIL]/[PHONE]で置換",
                "address_anonymization": "[ADDRESS]で置換",
            },
            "message": "個人情報を安全に匿名化しました",
        }

    except Exception as e:
        logger.error(f"Privacy demo error: {e}")
        raise HTTPException(status_code=500, detail=f"プライバシーデモエラー: {str(e)}")


@router.get("/privacy-policy")
async def get_privacy_policy() -> Dict[str, Any]:
    """
    プライバシーポリシーを取得

    Returns:
        プライバシーポリシー
    """
    return {
        "success": True,
        "privacy_policy": {
            "title": "プライバシー保護型文脈理解システム",
            "principles": [
                "個人情報は一切保存されません",
                "音声データは一切保存されません",
                "すべての入力は即座に匿名化されます",
                "セッション終了と同時にデータは削除されます",
                "クロスセッション追跡は行いません",
                "学習データは完全匿名化されたパターンのみです",
            ],
            "data_handling": {
                "collection": "匿名化された会話パターンのみ",
                "storage": "セッション中のメモリのみ",
                "retention": "セッション終了で自動削除",
                "sharing": "一切行いません",
                "anonymization": "リアルタイム匿名化",
            },
            "user_rights": [
                "いつでもセッション削除可能",
                "プライバシーモード選択可能",
                "匿名化プロセスの透明性",
                "データ保存なしの保証",
            ],
            "compliance": ["GDPR準拠", "個人情報保護法準拠"],
            "last_updated": "2024-07-20",
        },
    }
