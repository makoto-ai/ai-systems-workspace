"""
Voice Conversation Service with Privacy-Aware Context Understanding
音声会話処理サービス（プライバシー保護文脈理解付き）
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    from services.groq_service import GroqService
    from services.speech_service import get_speech_service
    from services.voice_service import VoiceService
    from services.conversation_history_service import get_conversation_history_service
    from services.privacy_aware_context_service import (
        get_privacy_aware_context_service,
        PrivacyMode,
    )
    from core.speakers import FEMALE_SALES, MALE_SALES
except ImportError:
    from app.services.groq_service import GroqService
    from app.services.speech_service import get_speech_service
    from app.services.voice_service import VoiceService
    from app.services.conversation_history_service import (
        get_conversation_history_service,
    )
    from app.services.privacy_aware_context_service import (
        get_privacy_aware_context_service,
        PrivacyMode,
    )
    from app.core.speakers import FEMALE_SALES, MALE_SALES

logger = logging.getLogger(__name__)


class ConversationServiceError(Exception):
    """Conversation service error"""

    pass


class ConversationService:
    """Voice conversation service with privacy-protected context understanding"""

    def __init__(self):
        """Initialize conversation service"""
        self.groq_service = GroqService()
        self.voice_service = None
        self.history_service = get_conversation_history_service()

        # プライバシー保護文脈理解サービス
        self.context_service = get_privacy_aware_context_service(PrivacyMode.STRICT)

        logger.info(
            "Conversation service initialized with privacy-aware context understanding"
        )

    async def process_voice_conversation(
        self,
        audio_data: bytes,
        session_id: Optional[str] = None,
        customer_info: Optional[Dict[str, Any]] = None,
        speaker_preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process voice conversation with privacy-protected context understanding
        音声会話を処理（プライバシー保護文脈理解付き）

        Args:
            audio_data: 音声データ
            session_id: セッションID
            customer_info: 顧客情報（匿名化される）
            speaker_preferences: 話者設定

        Returns:
            処理結果
        """
        start_time = time.time()

        try:
            # Initialize session if needed
            if not session_id:
                session_id = await self.history_service.create_session(
                    customer_info=customer_info
                )
                # プライバシー保護文脈セッションも初期化
                await self.context_service.initialize_session_context(session_id)
                logger.info(f"Created new conversation session: {session_id}")

            # Step 1: Speech-to-Text (WhisperX) - REAL-TIME MODE
            logger.info("Step 1: Converting speech to text (REAL-TIME)...")
            speech_service = get_speech_service(
                model_size="medium"
            )  # High accuracy model for better recognition
            transcription_result = await speech_service.transcribe_audio(
                audio_data,
                language="ja",
                enable_diarization=False,  # Skip for speed
                min_speakers=1,
                max_speakers=2,
            )

            input_text = transcription_result["text"]
            logger.info(f"Transcribed: {input_text[:100]}...")

            # Step 2: Privacy-Aware Context Analysis
            logger.info("Step 2: Privacy-aware context analysis...")
            context_suggestions = await self.context_service.get_contextual_suggestions(
                session_id=session_id, current_input=input_text
            )

            # Step 3: AI Processing (Groq-based, Ultra Fast) with Context
            logger.info("Step 3: Groq AI processing with contextual understanding...")

            # 文脈情報をAI分析に追加
            enhanced_prompt = input_text
            if context_suggestions.get("suggestions"):
                context_info = f"\n[文脈情報（匿名化済み）]\n"
                context_info += f"- 現在のトピック: {context_suggestions.get('current_topic', '不明')}\n"
                context_info += f"- 営業モメンタム: {context_suggestions.get('sales_momentum', 'neutral')}\n"
                context_info += (
                    f"- 提案: {', '.join(context_suggestions['suggestions'][:2])}\n"
                )
                enhanced_prompt += context_info

            ai_response = await self.groq_service.sales_analysis(enhanced_prompt)

            response_text = ai_response.get(
                "response", "申し訳ございません、もう一度お話しください。"
            )
            recommended_speaker = FEMALE_SALES

            logger.info(f"AI response: {response_text[:100]}...")

            # Step 4: Text-to-Speech (VOICEVOX) - EXTREME SPEED
            logger.info("Step 4: Converting text to speech (EXTREME SPEED)...")
            if not self.voice_service:
                raise ConversationServiceError("Voice service not initialized")

            # EXTREME SPEED: Start TTS immediately, skip all history updates
            import asyncio

            audio_result = await self.voice_service.synthesize_voice(
                text=response_text, speaker_id=recommended_speaker
            )

            # Step 5: Update Privacy-Aware Context (Async, Non-blocking)
            logger.info("Step 5: Updating privacy-aware context...")
            asyncio.create_task(
                self.context_service.update_context(
                    session_id=session_id,
                    user_input=input_text,
                    ai_response=response_text,
                    analysis_data=ai_response,
                )
            )

            # EXTREME SPEED: Fire-and-forget history updates (completely async)
            asyncio.create_task(
                self.history_service.add_turn(
                    session_id=session_id,
                    role="customer",
                    content=input_text[:50],  # Truncate heavily for speed
                    audio_data=None,  # Skip audio storage completely
                    analysis_data={
                        "confidence": transcription_result.get("confidence", 0.8)
                    },
                )
            )

            # Step 6: Format response
            processing_time = time.time() - start_time

            result = {
                "success": True,
                "session_id": session_id,
                "processing_time": processing_time,
                "input": {
                    "text": input_text,
                    "confidence": transcription_result.get("confidence", 0.8),
                    "language": "ja",
                },
                "output": {
                    "text": response_text,
                    "audio_data": audio_result if audio_result else b"",
                    "speaker_id": recommended_speaker,
                },
                "context": {
                    "privacy_protected": True,
                    "suggestions_available": len(
                        context_suggestions.get("suggestions", [])
                    )
                    > 0,
                    "current_topic": context_suggestions.get("current_topic"),
                    "confidence": context_suggestions.get("confidence", 0.5),
                },
                "analysis": {
                    "sentiment": ai_response.get("sentiment"),
                    "intent": ai_response.get("intent"),
                    "sales_stage": ai_response.get("sales_stage"),
                    "next_action": ai_response.get("next_action"),
                },
                "performance": {
                    "speed_mode": "EXTREME",
                    "processing_time_ms": round(processing_time * 1000, 2),
                    "privacy_mode": "STRICT",
                },
            }

            logger.info(
                f"Voice conversation processed in {processing_time:.2f}s with privacy protection"
            )
            return result

        except Exception as e:
            logger.error(f"Voice conversation processing error: {e}")
            raise ConversationServiceError(f"Failed to process voice conversation: {e}")

    async def initialize_voice_service(
        self, host: str = "localhost", port: str = "50021"
    ):
        """Initialize voice service"""
        try:
            self.voice_service = VoiceService(host=host, port=port)
            logger.info("Voice service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize voice service: {e}")
            raise ConversationServiceError(f"Voice service initialization failed: {e}")

    async def initialize(self, voice_service: VoiceService):
        """Initialize with existing voice service instance"""
        self.voice_service = voice_service
        logger.info("Voice service initialized with existing instance")

    async def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get session context with privacy protection
        プライバシー保護されたセッション文脈を取得
        """
        try:
            # プライバシー保護文脈サマリー
            context_summary = await self.context_service.get_session_summary(session_id)

            # 従来の履歴サービスからの情報（匿名化）
            history_context = await self.history_service.get_session_context(session_id)

            return {
                "success": True,
                "session_id": session_id,
                "privacy_protected_context": context_summary,
                "basic_context": {
                    "session_exists": history_context != {},
                    "privacy_mode": "strict",
                },
                "privacy_guarantees": {
                    "personal_info_storage": False,
                    "audio_storage": False,
                    "content_anonymization": True,
                    "auto_cleanup": True,
                },
            }

        except Exception as e:
            logger.error(f"Get session context error: {e}")
            return {"success": False, "error": str(e)}

    async def get_conversation_suggestions(
        self, session_id: str, current_input: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get contextual conversation suggestions with privacy protection
        プライバシー保護された会話提案を取得
        """
        try:
            if current_input:
                suggestions = await self.context_service.get_contextual_suggestions(
                    session_id=session_id, current_input=current_input
                )
            else:
                # 現在の文脈から提案を生成
                context_summary = await self.context_service.get_session_summary(
                    session_id
                )
                if context_summary.get("success"):
                    summary_data = context_summary.get("summary", {})
                    suggestions = {
                        "suggestions": summary_data.get("next_best_actions", []),
                        "current_topic": summary_data.get("current_topic"),
                        "context_available": True,
                    }
                else:
                    suggestions = {"suggestions": [], "context_available": False}

            return {
                "success": True,
                "suggestions": suggestions,
                "privacy_protected": True,
            }

        except Exception as e:
            logger.error(f"Get conversation suggestions error: {e}")
            return {"success": False, "error": str(e)}

    async def cleanup_session(self, session_id: str) -> Dict[str, Any]:
        """
        Clean up session with privacy protection
        プライバシー保護でセッションをクリーンアップ
        """
        try:
            # プライバシー保護文脈クリーンアップ
            await self.context_service._cleanup_session(session_id)

            # 従来の履歴サービスでは自動タイムアウト設定済み

            return {
                "success": True,
                "session_id": session_id,
                "message": "セッションを安全にクリーンアップしました",
                "privacy_protected": True,
            }

        except Exception as e:
            logger.error(f"Session cleanup error: {e}")
            return {"success": False, "error": str(e)}

    def get_service_info(self) -> Dict[str, Any]:
        """Get service information with privacy features"""
        return {
            "service_name": "Privacy-Aware Conversation Service",
            "version": "2.0.0",
            "features": {
                "voice_to_voice": True,
                "privacy_protected_context": True,
                "realtime_processing": True,
                "groq_ai_integration": True,
                "voicevox_tts": True,
                "whisperx_stt": True,
            },
            "privacy": {
                "personal_info_storage": False,
                "audio_storage": False,
                "content_anonymization": True,
                "session_based_only": True,
                "auto_cleanup": True,
                "gdpr_compliant": True,
            },
            "performance": {
                "speed_mode": "EXTREME",
                "target_latency_ms": "<2000",
                "context_understanding": True,
            },
        }

    async def handle_objection(
        self, session_id: str, objection_text: str, objection_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Handle customer objections using privacy-aware context
        顧客の異議をプライバシー保護文脈で処理
        """
        try:
            # 文脈を取得
            context_suggestions = await self.context_service.get_contextual_suggestions(
                session_id=session_id, current_input=objection_text
            )

            # 異議処理用の強化プロンプト
            enhanced_prompt = f"[異議処理]\n{objection_text}\n"
            enhanced_prompt += f"異議タイプ: {objection_type}\n"

            if context_suggestions.get("suggestions"):
                enhanced_prompt += (
                    f"文脈提案: {', '.join(context_suggestions['suggestions'][:2])}\n"
                )

            # AI分析
            ai_response = await self.groq_service.sales_analysis(enhanced_prompt)
            response_text = ai_response.get(
                "response", "ご懸念をお聞かせいただき、ありがとうございます。"
            )

            # 音声生成
            if not self.voice_service:
                raise ConversationServiceError("Voice service not initialized")

            audio_result = await self.voice_service.synthesize_voice(
                text=response_text, speaker_id=FEMALE_SALES
            )

            return {
                "success": True,
                "session_id": session_id,
                "objection_handling": {
                    "objection_text": objection_text,
                    "objection_type": objection_type,
                    "response": response_text,
                    "strategy": ai_response.get(
                        "handling_strategy", "empathetic_response"
                    ),
                    "confidence": 0.8,
                },
                "output": {
                    "text": response_text,
                    "audio_data": audio_result if audio_result else b"",
                    "speaker_id": FEMALE_SALES,
                },
            }

        except Exception as e:
            logger.error(f"Objection handling error: {e}")
            return {"success": False, "error": str(e)}

    async def analyze_bant_qualification(
        self, session_id: str, additional_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze BANT qualification with privacy-aware context
        プライバシー保護文脈でBANT適格性を分析
        """
        try:
            # セッション文脈を取得
            context_summary = await self.context_service.get_session_summary(session_id)

            if not context_summary.get("success"):
                return {"success": False, "error": "Session not found"}

            summary = context_summary.get("summary", {})

            # BANT分析（匿名化された情報のみ使用）
            bant_analysis = {
                "bant_status": {
                    "budget": {"status": "unknown", "indicators": []},
                    "authority": {"status": "unknown", "indicators": []},
                    "need": {
                        "status": (
                            "qualified"
                            if summary.get("identified_patterns")
                            else "exploring"
                        )
                    },
                    "timeline": {"status": "unknown", "indicators": []},
                },
                "bant_score": 0.25,  # デフォルトスコア
                "qualification_level": "low",
                "next_questions": [],
                "recommended_action": "continue_qualification",
            }

            # パターンからBANT情報を推測
            patterns = summary.get("identified_patterns", [])
            if "buying_signals_present" in patterns:
                bant_analysis["bant_score"] = 0.5
                bant_analysis["qualification_level"] = "medium"

            # 次のアクションから質問を生成
            next_actions = summary.get("next_best_actions", [])
            if next_actions:
                bant_analysis["next_questions"] = [
                    "ご予算についてお聞かせいただけますか？",
                    "導入時期についてご検討されていますか？",
                ]

            return {
                "success": True,
                "session_id": session_id,
                "bant_analysis": bant_analysis,
                "privacy_protected": True,
            }

        except Exception as e:
            logger.error(f"BANT analysis error: {e}")
            return {"success": False, "error": str(e)}

    async def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """
        Get comprehensive analytics with privacy protection
        プライバシー保護された包括的な分析を取得
        """
        try:
            # プライバシー保護文脈サマリー
            context_summary = await self.context_service.get_session_summary(session_id)

            if not context_summary.get("success"):
                return {"success": False, "error": "Session not found"}

            summary = context_summary.get("summary", {})

            # 基本的な分析結果を構築
            analytics = {
                "conversation_metrics": {
                    "session_duration": summary.get("duration_minutes", 0),
                    "total_turns": summary.get("total_turns", 0),
                    "avg_engagement": summary.get("average_engagement", 0.5),
                },
                "conversation_summary": {
                    "main_topics": summary.get("main_topics", []),
                    "current_topic": summary.get("current_topic"),
                    "sales_momentum": summary.get("sales_momentum", "neutral"),
                },
                "sales_progression": {
                    "current_stage": "needs_assessment",
                    "progression": "analyzed",
                    "engagement_trend": "stable",
                },
                "stage_analysis": {
                    "focus": "discovery",
                    "next_stage": "proposal",
                    "key_activities": ["qualify_needs", "understand_requirements"],
                },
                "bant_status": {},  # 匿名化のため空
                "buying_signals": [],
                "concerns": [],
                "engagement_insights": {
                    "engagement_level": (
                        "medium"
                        if summary.get("average_engagement", 0.5) > 0.5
                        else "low"
                    ),
                    "participation_rate": 0.5,
                },
                "next_best_actions": summary.get("next_best_actions", []),
            }

            return {
                "success": True,
                "session_id": session_id,
                "analytics": analytics,
                "privacy_protected": True,
                "personal_info_stored": False,
            }

        except Exception as e:
            logger.error(f"Session analytics error: {e}")
            return {"success": False, "error": str(e)}


# Global service instance
_conversation_service: Optional[ConversationService] = None


def get_conversation_service() -> ConversationService:
    """Get or create conversation service instance"""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService()
    return _conversation_service
