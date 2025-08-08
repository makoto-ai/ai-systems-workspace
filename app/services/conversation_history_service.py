"""
Conversation History Management Service
Phase 8: Advanced Sales Roleplay - Conversation Context Management
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class SalesStage(Enum):
    """Sales process stages"""

    PROSPECTING = "prospecting"
    NEEDS_ASSESSMENT = "needs_assessment"
    PROPOSAL = "proposal"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING = "closing"
    FOLLOW_UP = "follow_up"


@dataclass
class ConversationTurn:
    """Single conversation turn"""

    id: str
    timestamp: datetime
    role: str  # 'customer' or 'sales'
    content: str
    audio_data: Optional[bytes] = None
    speaker_id: Optional[int] = None
    intent: Optional[str] = None
    sentiment: Optional[str] = None
    confidence: Optional[float] = None
    processing_time: Optional[float] = None


@dataclass
class CustomerProfile:
    """Customer profile information"""

    customer_id: str
    name: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    role: Optional[str] = None
    contact_info: Optional[Dict[str, str]] = None
    preferences: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class BANTStatus:
    """BANT (Budget, Authority, Need, Timeline) qualification status"""

    budget: Dict[str, Any]
    authority: Dict[str, Any]
    need: Dict[str, Any]
    timeline: Dict[str, Any]
    score: float = 0.0
    last_updated: Optional[datetime] = None


@dataclass
class ConversationSession:
    """Complete conversation session"""

    session_id: str
    customer_profile: CustomerProfile
    turns: List[ConversationTurn]
    sales_stage: SalesStage
    bant_status: BANTStatus
    topics_discussed: List[str]
    buying_signals: List[Dict[str, Any]]
    concerns: List[Dict[str, Any]]
    next_actions: List[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


class ConversationHistoryService:
    """Service for managing conversation history and context"""

    def __init__(self, storage_backend: str = "memory"):
        """
        Initialize conversation history service

        Args:
            storage_backend: Storage backend ('memory', 'file', 'database')
        """
        self.storage_backend = storage_backend
        self.sessions: Dict[str, ConversationSession] = {}
        self.customer_profiles: Dict[str, CustomerProfile] = {}

        logger.info(
            f"Conversation history service initialized with {storage_backend} backend"
        )

    async def create_session(
        self,
        customer_id: Optional[str] = None,
        customer_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create new conversation session

        Args:
            customer_id: Existing customer ID
            customer_info: Customer information for new customer

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())

        # Get or create customer profile
        if customer_id and customer_id in self.customer_profiles:
            customer_profile = self.customer_profiles[customer_id]
        else:
            customer_profile = self._create_customer_profile(customer_id, customer_info)
            self.customer_profiles[customer_profile.customer_id] = customer_profile

        # Initialize BANT status
        bant_status = BANTStatus(
            budget={"status": "unknown", "range": None},
            authority={"status": "unknown", "level": None},
            need={"status": "unknown", "urgency": None},
            timeline={"status": "unknown", "urgency": None},
        )

        # Create session
        session = ConversationSession(
            session_id=session_id,
            customer_profile=customer_profile,
            turns=[],
            sales_stage=SalesStage.PROSPECTING,
            bant_status=bant_status,
            topics_discussed=[],
            buying_signals=[],
            concerns=[],
            next_actions=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={},
        )

        self.sessions[session_id] = session
        logger.info(
            f"Created conversation session {session_id} for customer {customer_profile.customer_id}"
        )

        return session_id

    async def add_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        audio_data: Optional[bytes] = None,
        speaker_id: Optional[int] = None,
        analysis_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add conversation turn to session

        Args:
            session_id: Session ID
            role: Speaker role ('customer' or 'sales')
            content: Text content
            audio_data: Audio data if available
            speaker_id: Speaker ID for TTS
            analysis_data: Analysis results (intent, sentiment, etc.)

        Returns:
            Turn ID
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        turn_id = str(uuid.uuid4())

        # Create turn
        turn = ConversationTurn(
            id=turn_id,
            timestamp=datetime.now(),
            role=role,
            content=content,
            audio_data=audio_data,
            speaker_id=speaker_id,
            intent=analysis_data.get("intent") if analysis_data else None,
            sentiment=analysis_data.get("sentiment") if analysis_data else None,
            confidence=analysis_data.get("confidence") if analysis_data else None,
            processing_time=(
                analysis_data.get("processing_time") if analysis_data else None
            ),
        )

        session.turns.append(turn)
        session.updated_at = datetime.now()

        # Update session context based on analysis
        if analysis_data:
            await self._update_session_context(session, analysis_data)

        logger.info(f"Added {role} turn to session {session_id}")
        return turn_id

    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get conversation session by ID"""
        return self.sessions.get(session_id)

    async def get_conversation_history(
        self, session_id: str, limit: Optional[int] = None, include_audio: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for session

        Args:
            session_id: Session ID
            limit: Maximum number of turns to return
            include_audio: Whether to include audio data

        Returns:
            List of conversation turns
        """
        if session_id not in self.sessions:
            return []

        session = self.sessions[session_id]
        turns = session.turns

        if limit:
            turns = turns[-limit:]

        history = []
        for turn in turns:
            turn_data = {
                "id": turn.id,
                "timestamp": turn.timestamp.isoformat(),
                "role": turn.role,
                "content": turn.content,
                "speaker_id": turn.speaker_id,
                "intent": turn.intent,
                "sentiment": turn.sentiment,
                "confidence": turn.confidence,
                "processing_time": turn.processing_time,
            }

            if include_audio and turn.audio_data:
                turn_data["audio_data"] = turn.audio_data

            history.append(turn_data)

        return history

    async def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get comprehensive session context

        Args:
            session_id: Session ID

        Returns:
            Session context including customer profile, BANT status, etc.
        """
        if session_id not in self.sessions:
            return {}

        session = self.sessions[session_id]

        return {
            "session_id": session.session_id,
            "customer_profile": asdict(session.customer_profile),
            "sales_stage": session.sales_stage.value,
            "bant_status": asdict(session.bant_status),
            "topics_discussed": session.topics_discussed,
            "buying_signals": session.buying_signals,
            "concerns": session.concerns,
            "next_actions": session.next_actions,
            "conversation_summary": self._generate_conversation_summary(session),
            "session_metrics": self._calculate_session_metrics(session),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }

    async def update_sales_stage(self, session_id: str, new_stage: str) -> bool:
        """Update sales stage for session"""
        if session_id not in self.sessions:
            return False

        try:
            stage = SalesStage(new_stage)
            self.sessions[session_id].sales_stage = stage
            self.sessions[session_id].updated_at = datetime.now()

            logger.info(f"Updated sales stage to {new_stage} for session {session_id}")
            return True
        except ValueError:
            logger.error(f"Invalid sales stage: {new_stage}")
            return False

    async def update_bant_status(
        self, session_id: str, bant_updates: Dict[str, Any]
    ) -> bool:
        """Update BANT status for session"""
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]

        # Update BANT fields
        for field, value in bant_updates.items():
            if field in ["budget", "authority", "need", "timeline"]:
                setattr(session.bant_status, field, value)

        # Recalculate BANT score
        session.bant_status.score = self._calculate_bant_score(session.bant_status)
        session.bant_status.last_updated = datetime.now()
        session.updated_at = datetime.now()

        logger.info(
            f"Updated BANT status for session {session_id}, score: {session.bant_status.score}"
        )
        return True

    async def get_customer_sessions(self, customer_id: str) -> List[str]:
        """Get all session IDs for a customer"""
        session_ids = []
        for session_id, session in self.sessions.items():
            if session.customer_profile.customer_id == customer_id:
                session_ids.append(session_id)
        return session_ids

    async def get_recent_sessions(
        self, hours: int = 24, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent conversation sessions"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_sessions = []
        for session in self.sessions.values():
            if session.updated_at >= cutoff_time:
                recent_sessions.append(
                    {
                        "session_id": session.session_id,
                        "customer_id": session.customer_profile.customer_id,
                        "customer_name": session.customer_profile.name,
                        "sales_stage": session.sales_stage.value,
                        "bant_score": session.bant_status.score,
                        "turn_count": len(session.turns),
                        "created_at": session.created_at.isoformat(),
                        "updated_at": session.updated_at.isoformat(),
                    }
                )

        # Sort by updated_at descending
        recent_sessions.sort(key=lambda x: x["updated_at"], reverse=True)

        return recent_sessions[:limit]

    def _create_customer_profile(
        self, customer_id: Optional[str], customer_info: Optional[Dict[str, Any]]
    ) -> CustomerProfile:
        """Create customer profile"""
        if not customer_id:
            customer_id = str(uuid.uuid4())

        profile = CustomerProfile(
            customer_id=customer_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        if customer_info:
            profile.name = customer_info.get("name")
            profile.company = customer_info.get("company")
            profile.industry = customer_info.get("industry")
            profile.role = customer_info.get("role")
            profile.contact_info = customer_info.get("contact_info")
            profile.preferences = customer_info.get("preferences")

        return profile

    async def _update_session_context(
        self, session: ConversationSession, analysis_data: Dict[str, Any]
    ) -> None:
        """Update session context based on analysis data"""
        # Update sales stage if recommended
        if "sales_stage" in analysis_data:
            try:
                new_stage = SalesStage(analysis_data["sales_stage"])
                session.sales_stage = new_stage
            except ValueError:
                pass

        # Update topics discussed
        if "topics_to_explore" in analysis_data:
            for topic in analysis_data["topics_to_explore"]:
                if topic not in session.topics_discussed:
                    session.topics_discussed.append(topic)

        # Update buying signals
        if "buying_signals" in analysis_data:
            for signal in analysis_data["buying_signals"]:
                session.buying_signals.append(
                    {
                        "signal": signal,
                        "timestamp": datetime.now().isoformat(),
                        "confidence": analysis_data.get("confidence", 0.5),
                    }
                )

        # Update concerns
        if "concerns" in analysis_data:
            for concern in analysis_data["concerns"]:
                session.concerns.append(
                    {
                        "concern": concern,
                        "timestamp": datetime.now().isoformat(),
                        "addressed": False,
                    }
                )

        # Update next actions
        if "next_action" in analysis_data:
            if analysis_data["next_action"] not in session.next_actions:
                session.next_actions.append(analysis_data["next_action"])

    def _generate_conversation_summary(
        self, session: ConversationSession
    ) -> Dict[str, Any]:
        """Generate conversation summary"""
        if not session.turns:
            return {"summary": "No conversation yet", "key_points": []}

        # Basic summary statistics
        customer_turns = [t for t in session.turns if t.role == "customer"]
        sales_turns = [t for t in session.turns if t.role == "sales"]

        # Key topics mentioned
        all_content = " ".join([t.content for t in session.turns])
        key_topics = []

        topic_keywords = {
            "pricing": ["料金", "価格", "費用", "コスト"],
            "features": ["機能", "特徴", "性能", "できること"],
            "implementation": ["導入", "実装", "開始", "スタート"],
            "timeline": ["いつ", "時期", "スケジュール", "予定"],
            "decision": ["決定", "検討", "判断", "承認"],
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in all_content for keyword in keywords):
                key_topics.append(topic)

        return {
            "summary": f"顧客との会話 {len(customer_turns)}回、営業側発言 {len(sales_turns)}回",
            "key_points": key_topics,
            "duration_minutes": self._calculate_conversation_duration(session),
            "engagement_level": self._assess_engagement_level(session),
        }

    def _calculate_session_metrics(
        self, session: ConversationSession
    ) -> Dict[str, Any]:
        """Calculate session metrics"""
        if not session.turns:
            return {}

        # Calculate various metrics
        total_turns = len(session.turns)
        customer_turns = len([t for t in session.turns if t.role == "customer"])
        sales_turns = len([t for t in session.turns if t.role == "sales"])

        # Average response time (if available)
        processing_times = [
            t.processing_time for t in session.turns if t.processing_time
        ]
        avg_processing_time = (
            sum(processing_times) / len(processing_times) if processing_times else 0
        )

        # Sentiment analysis
        sentiments = [t.sentiment for t in session.turns if t.sentiment]
        positive_sentiments = len([s for s in sentiments if s == "positive"])
        sentiment_ratio = positive_sentiments / len(sentiments) if sentiments else 0

        return {
            "total_turns": total_turns,
            "customer_turns": customer_turns,
            "sales_turns": sales_turns,
            "avg_processing_time": avg_processing_time,
            "sentiment_ratio": sentiment_ratio,
            "conversation_balance": customer_turns / max(sales_turns, 1),
        }

    def _calculate_bant_score(self, bant_status: BANTStatus) -> float:
        """Calculate BANT qualification score"""
        qualified_count = 0
        total_count = 4

        for field in ["budget", "authority", "need", "timeline"]:
            field_data = getattr(bant_status, field)
            if field_data.get("status") == "qualified":
                qualified_count += 1

        return qualified_count / total_count

    def _calculate_conversation_duration(self, session: ConversationSession) -> int:
        """Calculate conversation duration in minutes"""
        if len(session.turns) < 2:
            return 0

        start_time = session.turns[0].timestamp
        end_time = session.turns[-1].timestamp
        duration = end_time - start_time

        return int(duration.total_seconds() / 60)

    def _assess_engagement_level(self, session: ConversationSession) -> str:
        """Assess customer engagement level"""
        if not session.turns:
            return "unknown"

        customer_turns = [t for t in session.turns if t.role == "customer"]

        if len(customer_turns) == 0:
            return "low"

        # Check for positive indicators
        positive_indicators = 0
        for turn in customer_turns:
            content = turn.content.lower()
            if any(
                word in content
                for word in ["はい", "そうですね", "いいですね", "興味", "検討"]
            ):
                positive_indicators += 1

        engagement_ratio = positive_indicators / len(customer_turns)

        if engagement_ratio >= 0.6:
            return "high"
        elif engagement_ratio >= 0.3:
            return "medium"
        else:
            return "low"


# Global service instance
_conversation_history_service: Optional[ConversationHistoryService] = None


def get_conversation_history_service(
    storage_backend: str = "memory",
) -> ConversationHistoryService:
    """Get or create conversation history service instance"""
    global _conversation_history_service
    if _conversation_history_service is None:
        _conversation_history_service = ConversationHistoryService(
            storage_backend=storage_backend
        )
    return _conversation_history_service
