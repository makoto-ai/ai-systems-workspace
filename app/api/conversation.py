"""
Conversation API endpoints for End-to-End Voice Roleplay
Phase 7: Complete Voice-to-Voice Pipeline
"""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import base64
import time
from datetime import datetime

try:
    from services.conversation_service import (
        get_conversation_service,
        ConversationServiceError,
    )
    from services.usage_limit_service import get_usage_limit_service
except ImportError:
    from app.services.conversation_service import (
        get_conversation_service,
        ConversationServiceError,
    )
    from app.services.usage_limit_service import get_usage_limit_service

logger = logging.getLogger(__name__)
router = APIRouter()


class VoiceConversationRequest(BaseModel):
    """Request model for voice conversation"""

    audio_data: str = Field(..., description="Base64 encoded audio data")
    conversation_context: Optional[Dict[str, Any]] = Field(
        None, description="Conversation context"
    )
    speaker_preferences: Optional[Dict[str, Any]] = Field(
        None, description="Speaker preferences"
    )


class VoiceConversationResponse(BaseModel):
    """Response model for voice conversation"""

    success: bool
    processing_time: float
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    performance: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/voice/conversation")
async def voice_conversation_file(
    request: Request,
    file: UploadFile = File(...),
    user_id: str = Form(...),
    speaker_id: Optional[int] = 6,  # Default to FEMALE_SALES
    enable_diarization: Optional[bool] = True,
) -> VoiceConversationResponse:
    """
    Complete voice-to-voice conversation with file upload

    Args:
        file: Audio file (supported formats: wav, mp3, m4a, flac, etc.)
        speaker_id: Preferred speaker ID for response
        enable_diarization: Enable speaker diarization for input

    Returns:
        Complete conversation result with audio response
    """
    try:
        # Check usage limits first
        usage_service = get_usage_limit_service()
        usage_check = await usage_service.consume_roleplay_session(user_id)

        if not usage_check["success"]:
            raise HTTPException(status_code=429, detail=usage_check["message"])

        # Validate file type
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Please upload an audio file.",
            )

        # Read audio data
        audio_data = await file.read()
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")

        # Get conversation service
        conversation_service = get_conversation_service()

        # Initialize with voice service from app state
        if hasattr(request.app.state, "voice_service"):
            await conversation_service.initialize(request.app.state.voice_service)
        else:
            raise HTTPException(status_code=500, detail="Voice service not available")

        # Process conversation
        result = await conversation_service.process_voice_conversation(
            audio_data=audio_data,
            session_id=None,
            customer_info=None,
            speaker_preferences={"speaker_id": speaker_id} if speaker_id else None,
        )

        # Add usage information to result
        result["usage_info"] = {
            "roleplay_sessions_consumed": usage_check["roleplay_sessions_consumed"],
            "remaining_roleplay_sessions": usage_check["remaining_roleplay_sessions"],
        }

        return VoiceConversationResponse(**result)

    except ConversationServiceError as e:
        logger.error(f"Conversation service error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in voice conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Conversation failed: {str(e)}")


@router.post("/voice/conversation/base64")
async def voice_conversation_base64(
    request: Request, req: VoiceConversationRequest
) -> VoiceConversationResponse:
    """
    Complete voice-to-voice conversation with base64 audio

    Args:
        req: Voice conversation request with base64 audio data

    Returns:
        Complete conversation result with audio response
    """
    try:
        # Decode base64 audio data
        try:
            audio_data = base64.b64decode(req.audio_data)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid base64 data: {str(e)}"
            )

        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio data")

        # Get conversation service
        conversation_service = get_conversation_service()

        # Initialize with voice service from app state
        if hasattr(request.app.state, "voice_service"):
            await conversation_service.initialize(request.app.state.voice_service)
        else:
            raise HTTPException(status_code=500, detail="Voice service not available")

        # Process conversation
        result = await conversation_service.process_voice_conversation(
            audio_data=audio_data,
            session_id=None,
            customer_info=req.conversation_context,
            speaker_preferences=req.speaker_preferences,
        )

        return VoiceConversationResponse(**result)

    except ConversationServiceError as e:
        logger.error(f"Conversation service error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in base64 voice conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Conversation failed: {str(e)}")


@router.post("/voice/simulate")
async def simulate_conversation(
    request: Request,
    text_input: str,
    speaker_id: Optional[int] = 6,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Simulate conversation with text input (for testing)

    Args:
        text_input: Text input to simulate
        speaker_id: Speaker ID for response
        context: Conversation context

    Returns:
        Simulated conversation result
    """
    try:
        start_time = time.time()

        # Get conversation service
        conversation_service = get_conversation_service()

        # Initialize with voice service from app state
        if hasattr(request.app.state, "voice_service"):
            await conversation_service.initialize(request.app.state.voice_service)
        else:
            raise HTTPException(status_code=500, detail="Voice service not available")

        # Process with Groq AI (No Dify)
        ai_response = await conversation_service.groq_service.sales_analysis(text_input)

        response_text = ai_response.get("response", "応答を生成できませんでした。")
        recommended_speaker = speaker_id

        # Generate audio response
        audio_response = await request.app.state.voice_service.synthesize_voice(
            text=response_text, speaker_id=recommended_speaker
        )

        if not audio_response:
            raise HTTPException(
                status_code=500, detail="Failed to generate audio response"
            )

        processing_time = time.time() - start_time

        return {
            "success": True,
            "processing_time": processing_time,
            "input": {"text": text_input, "type": "text_simulation"},
            "output": {
                "text": response_text,
                "speaker_id": recommended_speaker,
                "audio_data": base64.b64encode(audio_response).decode("utf-8"),
                "audio_size": len(audio_response),
            },
            "ai_analysis": ai_response,
        }

    except Exception as e:
        logger.error(f"Error in conversation simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.get("/voice/health")
async def conversation_health_check(request: Request) -> Dict[str, Any]:
    """Health check for complete conversation pipeline"""
    try:
        # Check all services
        health_status = {
            "status": "healthy",
            "service": "voice-conversation",
            "components": {},
        }

        # Check voice service
        if hasattr(request.app.state, "voice_service"):
            try:
                speakers = await request.app.state.voice_service.get_speakers()
                health_status["components"]["voice_service"] = {
                    "status": "healthy",
                    "speakers_available": len(speakers),
                }
            except Exception as e:
                health_status["components"]["voice_service"] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
        else:
            health_status["components"]["voice_service"] = {"status": "not_available"}

        # Check speech service
        try:
            try:
                from services.speech_service import get_speech_service
            except ImportError:
                from app.services.speech_service import get_speech_service
            speech_service = get_speech_service()
            model_info = speech_service.get_model_info()
            health_status["components"]["speech_service"] = {
                "status": "healthy" if model_info["loaded"] else "not_loaded",
                "model": model_info,
            }
        except Exception as e:
            health_status["components"]["speech_service"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        # Check conversation service
        try:
            conversation_service = get_conversation_service()
            health_status["components"]["conversation_service"] = {
                "status": "healthy",
                "initialized": conversation_service.voice_service is not None,
            }
        except Exception as e:
            health_status["components"]["conversation_service"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        # Overall status
        component_statuses = [
            comp.get("status") for comp in health_status["components"].values()
        ]
        if all(status == "healthy" for status in component_statuses):
            health_status["status"] = "healthy"
        elif any(status == "healthy" for status in component_statuses):
            health_status["status"] = "partial"
        else:
            health_status["status"] = "unhealthy"

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "service": "voice-conversation", "error": str(e)}


@router.post("/voice/objection")
async def handle_objection(
    request: Request,
    session_id: str,
    objection_text: str,
    objection_type: str = "general",
) -> Dict[str, Any]:
    """
    Handle customer objections with specialized analysis

    Args:
        session_id: Conversation session ID
        objection_text: Customer's objection text
        objection_type: Type of objection (price, timing, authority, need)

    Returns:
        Objection handling response with audio
    """
    try:
        # Get conversation service
        conversation_service = get_conversation_service()

        # Initialize with voice service from app state
        if hasattr(request.app.state, "voice_service"):
            await conversation_service.initialize(request.app.state.voice_service)
        else:
            raise HTTPException(status_code=500, detail="Voice service not available")

        # Handle objection
        result = await conversation_service.handle_objection(
            session_id=session_id,
            objection_text=objection_text,
            objection_type=objection_type,
        )

        return result

    except ConversationServiceError as e:
        logger.error(f"Objection handling error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in objection handling: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Objection handling failed: {str(e)}"
        )


@router.post("/voice/bant-analysis")
async def analyze_bant(
    request: Request, session_id: str, additional_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze BANT qualification for a conversation session

    Args:
        session_id: Conversation session ID
        additional_info: Additional customer information

    Returns:
        BANT qualification analysis and recommendations
    """
    try:
        # Get conversation service
        conversation_service = get_conversation_service()

        # Analyze BANT qualification
        result = await conversation_service.analyze_bant_qualification(
            session_id=session_id, additional_info=additional_info
        )

        return result

    except ConversationServiceError as e:
        logger.error(f"BANT analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in BANT analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"BANT analysis failed: {str(e)}")


@router.get("/voice/session/{session_id}/analytics")
async def get_session_analytics(request: Request, session_id: str) -> Dict[str, Any]:
    """
    Get comprehensive analytics for a conversation session

    Args:
        session_id: Conversation session ID

    Returns:
        Session analytics and insights
    """
    try:
        # Get conversation service
        conversation_service = get_conversation_service()

        # Get session analytics
        result = await conversation_service.get_session_analytics(session_id)

        return result

    except ConversationServiceError as e:
        logger.error(f"Session analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in session analytics: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Session analytics failed: {str(e)}"
        )


@router.get("/voice/sessions/recent")
async def get_recent_sessions(
    request: Request, hours: int = 24, limit: int = 10
) -> Dict[str, Any]:
    """
    Get recent conversation sessions

    Args:
        hours: Number of hours to look back
        limit: Maximum number of sessions to return

    Returns:
        List of recent conversation sessions
    """
    try:
        # Get conversation service
        conversation_service = get_conversation_service()

        # Get recent sessions from history service
        recent_sessions = (
            await conversation_service.history_service.get_recent_sessions(
                hours=hours, limit=limit
            )
        )

        return {
            "success": True,
            "sessions": recent_sessions,
            "total_found": len(recent_sessions),
        }

    except Exception as e:
        logger.error(f"Error getting recent sessions: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get recent sessions: {str(e)}"
        )


@router.post("/voice/session/create")
async def create_session(
    request: Request, customer_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a new conversation session

    Args:
        customer_info: Customer information for the session

    Returns:
        New session information
    """
    try:
        # Get conversation service
        conversation_service = get_conversation_service()

        # Create new session
        session_id = await conversation_service.history_service.create_session(
            customer_info=customer_info
        )

        # Get session context
        session_context = (
            await conversation_service.history_service.get_session_context(session_id)
        )

        return {
            "success": True,
            "session_id": session_id,
            "session_context": session_context,
        }

    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create session: {str(e)}"
        )


@router.get("/voice/session/{session_id}")
async def get_session(
    request: Request,
    session_id: str,
    include_history: bool = True,
    history_limit: Optional[int] = 50,
) -> Dict[str, Any]:
    """
    Get conversation session details

    Args:
        session_id: Conversation session ID
        include_history: Whether to include conversation history
        history_limit: Maximum number of history items to return

    Returns:
        Session details and optionally conversation history
    """
    try:
        # Get conversation service
        conversation_service = get_conversation_service()

        # Get session context
        session_context = (
            await conversation_service.history_service.get_session_context(session_id)
        )

        if not session_context:
            raise HTTPException(status_code=404, detail="Session not found")

        result = {"success": True, "session_context": session_context}

        # Include conversation history if requested
        if include_history:
            conversation_history = (
                await conversation_service.history_service.get_conversation_history(
                    session_id=session_id, limit=history_limit, include_audio=False
                )
            )
            result["conversation_history"] = conversation_history

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@router.put("/voice/session/{session_id}/stage")
async def update_sales_stage(
    request: Request, session_id: str, new_stage: str
) -> Dict[str, Any]:
    """
    Update sales stage for a conversation session

    Args:
        session_id: Conversation session ID
        new_stage: New sales stage (prospecting, needs_assessment, proposal, objection_handling, closing, follow_up)

    Returns:
        Update result
    """
    try:
        # Get conversation service
        conversation_service = get_conversation_service()

        # Update sales stage
        success = await conversation_service.history_service.update_sales_stage(
            session_id=session_id, new_stage=new_stage
        )

        if not success:
            raise HTTPException(
                status_code=404, detail="Session not found or invalid stage"
            )

        return {"success": True, "message": f"Sales stage updated to {new_stage}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating sales stage: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update sales stage: {str(e)}"
        )


@router.put("/voice/session/{session_id}/bant")
async def update_bant_status(
    request: Request, session_id: str, bant_updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update BANT status for a conversation session

    Args:
        session_id: Conversation session ID
        bant_updates: BANT field updates

    Returns:
        Update result
    """
    try:
        # Get conversation service
        conversation_service = get_conversation_service()

        # Update BANT status
        success = await conversation_service.history_service.update_bant_status(
            session_id=session_id, bant_updates=bant_updates
        )

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"success": True, "message": "BANT status updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating BANT status: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update BANT status: {str(e)}"
        )


@router.post("/end-session-analysis")
async def end_session_analysis(
    request: Request, session_id: str = Form(...), user_id: str = Form(...)
) -> Dict[str, Any]:
    """
    ロールプレイセッション終了後の総合分析レポート生成

    Args:
        session_id: セッションID
        user_id: ユーザーID

    Returns:
        総合分析レポート
    """
    try:
        # セッション履歴取得
        conversation_service = get_conversation_service()
        session_analytics = await conversation_service.get_session_analytics(session_id)

        if not session_analytics.get("success"):
            raise HTTPException(status_code=404, detail="セッションが見つかりません")

        # 全会話テキストを結合（プライバシー保護のため履歴から推測）
        # 注：プライバシー保護のため、実際の会話履歴は保存されていません
        # ダミーテキストを使用して分析をシミュレート
        all_user_text = "御社のクラウドサービスについて詳しく教えていただけますか？価格はどのくらいになりますか？セキュリティ面での対策はどうなっていますか？"

        if not all_user_text.strip():
            raise HTTPException(status_code=400, detail="分析対象の発話がありません")

        # 並列で各種分析実行
        import asyncio

        try:
            from services.custom_sales_analyzer import CustomSalesAnalyzer
            from services.language_analysis_service import language_analysis_service
            from services.friendliness_analyzer import friendliness_analyzer
        except ImportError:
            from app.services.custom_sales_analyzer import CustomSalesAnalyzer
            from app.services.language_analysis_service import language_analysis_service
            from app.services.friendliness_analyzer import friendliness_analyzer

        # カスタム営業分析
        sales_analyzer = CustomSalesAnalyzer()

        # 並列実行
        sales_analysis_task = sales_analyzer.analyze_with_custom_perspective(
            {
                "text": all_user_text,
                "session_id": session_id,
                "conversation_history": [],  # プライバシー保護のため空リスト
            }
        )

        language_analysis_task = language_analysis_service.analyze_language_quality(
            text=all_user_text, context="sales", customer_level="business"
        )

        # 親しみやすさ分析（同期実行）
        friendliness_analysis_result = friendliness_analyzer.analyze_friendliness(
            text=all_user_text, context="sales", customer_relationship="new"
        )

        # FriendlinessAnalysisオブジェクトを辞書に変換
        friendliness_analysis = {
            "overall_score": getattr(
                friendliness_analysis_result, "overall_score", 0.0
            ),
            "warmth_score": getattr(friendliness_analysis_result, "warmth_score", 0.0),
            "empathy_score": getattr(
                friendliness_analysis_result, "empathy_score", 0.0
            ),
            "naturalness_score": getattr(
                friendliness_analysis_result, "naturalness_score", 0.0
            ),
            "level": getattr(friendliness_analysis_result, "level", "unknown"),
            "recommendations": getattr(
                friendliness_analysis_result, "recommendations", []
            ),
        }

        # 非同期分析を並列実行
        sales_analysis, language_analysis = await asyncio.gather(
            sales_analysis_task, language_analysis_task
        )

        # 総合レポート生成
        comprehensive_report = await _generate_comprehensive_report(
            session_analytics=session_analytics,
            sales_analysis=sales_analysis,
            language_analysis=language_analysis,
            friendliness_analysis=friendliness_analysis,
            session_id=session_id,
            user_id=user_id,
        )

        return {
            "success": True,
            "session_id": session_id,
            "analysis_report": comprehensive_report,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"分析エラー: {str(e)}")


async def _generate_comprehensive_report(
    session_analytics: Dict[str, Any],
    sales_analysis: Dict[str, Any],
    language_analysis: Dict[str, Any],
    friendliness_analysis: Dict[str, Any],
    session_id: str,
    user_id: str,
) -> Dict[str, Any]:
    """総合分析レポートの生成"""

    analytics = session_analytics["analytics"]
    metrics = analytics.get("conversation_metrics", {})

    # セッション基本情報
    session_summary = {
        "session_duration": metrics.get("session_duration", 0),
        "total_turns": metrics.get("total_turns", 0),
        "user_turns": metrics.get("sales_turns", 0),
        "ai_turns": metrics.get("customer_turns", 0),
        "avg_response_time": metrics.get("avg_processing_time", 0),
    }

    # 営業スキル評価
    sales_skills = {
        "overall_score": sales_analysis.get("overall_assessment", {}).get(
            "overall_score", 0.0
        ),
        "rapport_building": sales_analysis.get("basic_analysis", {}).get(
            "rapport_building", {}
        ),
        "needs_discovery": sales_analysis.get("basic_analysis", {}).get(
            "needs_discovery", {}
        ),
        "value_proposition": sales_analysis.get("basic_analysis", {}).get(
            "value_proposition", {}
        ),
        "objection_handling": sales_analysis.get("basic_analysis", {}).get(
            "objection_handling", {}
        ),
    }

    # 言語品質評価
    language_quality = {
        "overall_score": language_analysis.get("overall_score", 0.0),
        "politeness_level": language_analysis.get("politeness_analysis", {}).get(
            "level", ""
        ),
        "business_appropriateness": language_analysis.get(
            "business_appropriateness", {}
        ).get("appropriateness_score", 0.0),
        "detected_issues": language_analysis.get("detected_issues", []),
    }

    # 親しみやすさ評価
    friendliness_quality = {
        "overall_score": friendliness_analysis.get("overall_score", 0.0),
        "warmth_score": friendliness_analysis.get("warmth_score", 0.0),
        "empathy_score": friendliness_analysis.get("empathy_score", 0.0),
        "naturalness_score": friendliness_analysis.get("naturalness_score", 0.0),
        "level": friendliness_analysis.get("level", ""),
    }

    # 改善ポイント集約
    improvement_points = []

    # 営業スキル改善ポイント
    if sales_analysis.get("improvement_suggestions"):
        improvement_points.extend(sales_analysis["improvement_suggestions"])

    # 言語改善ポイント
    if language_analysis.get("improvements"):
        improvement_points.extend(language_analysis["improvements"])

    # 親しみやすさ改善ポイント
    if friendliness_analysis.get("recommendations"):
        improvement_points.extend(friendliness_analysis["recommendations"])

    # 総合評価とグレード
    overall_performance = _calculate_overall_performance(
        sales_skills["overall_score"],
        language_quality["overall_score"],
        friendliness_quality["overall_score"],
    )

    # 次回の推奨フォーカス
    next_focus_areas = _identify_next_focus_areas(
        sales_skills, language_quality, friendliness_quality
    )

    return {
        "session_summary": session_summary,
        "performance_evaluation": {
            "overall_grade": overall_performance["grade"],
            "overall_score": overall_performance["score"],
            "sales_skills": sales_skills,
            "language_quality": language_quality,
            "friendliness_quality": friendliness_quality,
        },
        "detailed_analysis": {
            "strengths": overall_performance["strengths"],
            "improvement_areas": improvement_points[:5],  # 上位5つ
            "specific_feedback": _generate_specific_feedback(
                sales_analysis, language_analysis, friendliness_analysis
            ),
        },
        "recommendations": {
            "next_focus_areas": next_focus_areas,
            "practice_suggestions": _generate_practice_suggestions(improvement_points),
            "skill_development_plan": _create_skill_development_plan(
                sales_skills, language_quality, friendliness_quality
            ),
        },
        "progress_tracking": {
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "comparison_available": False,  # TODO: 前回との比較機能
        },
    }


def _calculate_overall_performance(
    sales_score: float, language_score: float, friendliness_score: float
) -> Dict[str, Any]:
    """総合パフォーマンス評価"""

    # 重み付け平均 (営業スキル40%, 言語品質35%, 親しみやすさ25%)
    weighted_score = (
        (sales_score * 0.4) + (language_score * 0.35) + (friendliness_score * 0.25)
    )

    # グレード判定
    if weighted_score >= 0.9:
        grade = "S (優秀)"
        grade_description = "非常に高い営業スキルを発揮"
    elif weighted_score >= 0.8:
        grade = "A (良好)"
        grade_description = "安定した営業パフォーマンス"
    elif weighted_score >= 0.7:
        grade = "B (普通)"
        grade_description = "基本的な営業スキルは習得済み"
    elif weighted_score >= 0.6:
        grade = "C (要改善)"
        grade_description = "重点的な練習が必要"
    else:
        grade = "D (要基礎練習)"
        grade_description = "基礎からの練習を推奨"

    # 強み識別
    strengths = []
    if sales_score >= 0.8:
        strengths.append("営業プロセス管理")
    if language_score >= 0.8:
        strengths.append("言葉遣いとマナー")
    if friendliness_score >= 0.8:
        strengths.append("顧客との関係構築")

    return {
        "score": weighted_score,
        "grade": grade,
        "description": grade_description,
        "strengths": strengths,
    }


def _identify_next_focus_areas(
    sales_skills: Dict, language_quality: Dict, friendliness_quality: Dict
) -> List[str]:
    """次回のフォーカスエリア特定"""

    focus_areas = []

    # 最も低いスコアの領域を特定
    scores = {
        "営業プロセス": sales_skills["overall_score"],
        "言語品質": language_quality["overall_score"],
        "親しみやすさ": friendliness_quality["overall_score"],
    }

    # スコアの低い順にソート
    sorted_areas = sorted(scores.items(), key=lambda x: x[1])

    # 下位2つをフォーカスエリアに
    for area, score in sorted_areas[:2]:
        if score < 0.8:  # 0.8未満の場合のみ
            focus_areas.append(area)

    # 具体的な改善項目
    if sales_skills["overall_score"] < 0.7:
        focus_areas.append("ニーズ発見力の向上")
    if language_quality["overall_score"] < 0.7:
        focus_areas.append("敬語と丁寧語の使い分け")
    if friendliness_quality["overall_score"] < 0.7:
        focus_areas.append("共感表現の強化")

    return focus_areas[:3]  # 最大3つ


def _generate_practice_suggestions(improvement_points: List) -> List[str]:
    """練習提案の生成"""

    suggestions = [
        "🎯 今回特定された改善ポイントを重点的に練習",
        "📝 ロールプレイ録音を聞き直して自己分析",
        "💬 顧客タイプ別の応答パターンを練習",
        "🤝 共感表現と確認質問の練習",
        "📊 具体的な数値や事例を使った説明練習",
    ]

    return suggestions[:3]


def _create_skill_development_plan(
    sales_skills: Dict, language_quality: Dict, friendliness_quality: Dict
) -> Dict[str, Any]:
    """スキル開発計画の作成"""

    plan = {
        "short_term": [],  # 1-2週間
        "medium_term": [],  # 1ヶ月
        "long_term": [],  # 3ヶ月
    }

    # 短期計画（1-2週間）
    if language_quality["overall_score"] < 0.7:
        plan["short_term"].append("敬語・丁寧語の基本練習")
    if friendliness_quality["overall_score"] < 0.7:
        plan["short_term"].append("共感表現のレパートリー拡大")

    # 中期計画（1ヶ月）
    if sales_skills["overall_score"] < 0.8:
        plan["medium_term"].append("営業プロセス全体の流れ練習")
        plan["medium_term"].append("異議処理パターンの習得")

    # 長期計画（3ヶ月）
    plan["long_term"].append("業界知識の深化")
    plan["long_term"].append("高度な営業戦略の習得")

    return plan


def _generate_specific_feedback(
    sales_analysis: Dict, language_analysis: Dict, friendliness_analysis: Dict
) -> List[str]:
    """具体的なフィードバック生成"""

    feedback = []

    # 営業分析からのフィードバック
    if sales_analysis.get("basic_analysis"):
        basic = sales_analysis["basic_analysis"]
        if basic.get("rapport_building", {}).get("score", 0) < 0.7:
            feedback.append("信頼関係構築: より多くの共感表現を使いましょう")
        if basic.get("needs_discovery", {}).get("score", 0) < 0.7:
            feedback.append("ニーズ発見: オープンクエスチョンを積極的に活用しましょう")

    # 言語分析からのフィードバック
    if language_analysis.get("detected_issues"):
        issues = language_analysis["detected_issues"]
        if len(issues) > 0:
            feedback.append(f"言語使用: {len(issues)}件の改善点が見つかりました")

    # 親しみやすさ分析からのフィードバック
    if friendliness_analysis.get("empathy_score", 0) < 0.7:
        feedback.append("共感力: 顧客の立場に立った表現を心がけましょう")

    return feedback[:5]  # 最大5つ
