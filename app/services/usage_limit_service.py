"""
Usage Limit Service for Voice Roleplay System
Manages video processing limits and roleplay session consumption
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class RoleplaySession:
    """Individual roleplay session record"""

    session_id: str
    start_time: str
    end_time: str
    duration_minutes: int
    scenario_type: str
    performance_score: Optional[float] = None
    improvement_points: List[str] = None


@dataclass
class ReminderSettings:
    """User reminder email settings"""

    email_enabled: bool = True
    email_address: str = ""
    user_name: str = ""
    reminder_days: List[int] = None  # [3, 1, 0] for 3 days, 1 day, same day
    timezone: str = "Asia/Tokyo"
    enable_shame_system: bool = False  # サボり検知・突きつけ機能のオンオフ

    def __post_init__(self):
        if self.reminder_days is None:
            self.reminder_days = [3, 1, 0]


@dataclass
class UsageStats:
    """User usage statistics"""

    user_id: str
    video_processing_minutes_used: int  # 動画処理で使用した分数
    roleplay_sessions_remaining: int  # 残りロープレセッション数
    last_reset_date: str  # 最後のリセット日
    created_at: str
    updated_at: str

    # Roleplay activity tracking
    last_roleplay_date: Optional[str] = None  # 最後のロールプレイ実行日
    consecutive_days: int = 0  # 連続実行日数
    total_roleplay_sessions: int = 0  # 総セッション数
    recent_sessions: List[RoleplaySession] = None  # 最近のセッション（最大10件）
    recent_improvement_points: List[str] = None  # 最近の改善ポイント

    # Email reminder settings
    reminder_settings: ReminderSettings = None

    def __post_init__(self):
        if self.recent_sessions is None:
            self.recent_sessions = []
        elif isinstance(self.recent_sessions, list) and self.recent_sessions:
            # 辞書のリストをRoleplaySessionオブジェクトのリストに変換
            if isinstance(self.recent_sessions[0], dict):
                self.recent_sessions = [
                    RoleplaySession(**session) for session in self.recent_sessions
                ]

        if self.recent_improvement_points is None:
            self.recent_improvement_points = []

        if self.reminder_settings is None:
            self.reminder_settings = ReminderSettings()
        elif isinstance(self.reminder_settings, dict):
            # 辞書からReminderSettingsオブジェクトに変換
            self.reminder_settings = ReminderSettings(**self.reminder_settings)


class UsageLimitService:
    """Service for managing usage limits and session consumption"""

    def __init__(self, storage_path: str = "data/usage_limits.json"):
        """
        Initialize usage limit service

        Args:
            storage_path: Path to store usage data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Configuration
        self.max_video_processing_minutes = 60  # 1時間まで
        self.initial_roleplay_sessions = 60  # 初期ロープレセッション数
        self.reset_period_days = 30  # 30日でリセット

        # In-memory storage
        self.usage_stats: Dict[str, UsageStats] = {}

        # Load existing data
        self._load_usage_data()

        logger.info(
            f"Usage limit service initialized with storage: {self.storage_path}"
        )

    def _load_usage_data(self) -> None:
        """Load usage data from storage"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for user_id, stats_data in data.items():
                    self.usage_stats[user_id] = UsageStats(**stats_data)

                logger.info(f"Loaded usage data for {len(self.usage_stats)} users")
            else:
                logger.info("No existing usage data found")

        except Exception as e:
            logger.error(f"Failed to load usage data: {e}")
            self.usage_stats = {}

    def _save_usage_data(self) -> None:
        """Save usage data to storage"""
        try:
            data = {}
            for user_id, stats in self.usage_stats.items():
                data[user_id] = asdict(stats)

            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug("Usage data saved successfully")

        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")

    def _get_or_create_user_stats(self, user_id: str) -> UsageStats:
        """Get or create user usage statistics"""
        if user_id not in self.usage_stats:
            now = datetime.now().isoformat()
            self.usage_stats[user_id] = UsageStats(
                user_id=user_id,
                video_processing_minutes_used=0,
                roleplay_sessions_remaining=self.initial_roleplay_sessions,
                last_reset_date=now,
                created_at=now,
                updated_at=now,
            )
            self._save_usage_data()
            logger.info(f"Created new user stats for {user_id}")

        return self.usage_stats[user_id]

    def _check_reset_needed(self, user_stats: UsageStats) -> bool:
        """Check if user stats need to be reset"""
        try:
            last_reset = datetime.fromisoformat(user_stats.last_reset_date)
            now = datetime.now()

            return (now - last_reset).days >= self.reset_period_days

        except Exception as e:
            logger.error(f"Error checking reset date: {e}")
            return False

    def _reset_user_stats(self, user_id: str) -> None:
        """Reset user statistics for new period"""
        if user_id in self.usage_stats:
            stats = self.usage_stats[user_id]
            now = datetime.now().isoformat()

            stats.video_processing_minutes_used = 0
            stats.roleplay_sessions_remaining = self.initial_roleplay_sessions
            stats.last_reset_date = now
            stats.updated_at = now

            self._save_usage_data()
            logger.info(f"Reset usage stats for user {user_id}")

    async def can_process_video(
        self, user_id: str, video_duration_minutes: int
    ) -> Dict[str, Any]:
        """
        Check if user can process video of given duration

        Args:
            user_id: User identifier
            video_duration_minutes: Video duration in minutes

        Returns:
            Dict with can_process flag and details
        """
        user_stats = self._get_or_create_user_stats(user_id)

        # Check if reset is needed
        if self._check_reset_needed(user_stats):
            self._reset_user_stats(user_id)
            user_stats = self.usage_stats[user_id]

        # Check if video exceeds max duration
        if video_duration_minutes > self.max_video_processing_minutes:
            return {
                "can_process": False,
                "reason": "video_too_long",
                "message": f"動画は最大{self.max_video_processing_minutes}分まで処理可能です",
                "max_duration": self.max_video_processing_minutes,
                "requested_duration": video_duration_minutes,
            }

        # Check remaining capacity
        remaining_minutes = (
            self.max_video_processing_minutes - user_stats.video_processing_minutes_used
        )

        if video_duration_minutes > remaining_minutes:
            return {
                "can_process": False,
                "reason": "insufficient_quota",
                "message": f"動画処理の残り時間が不足しています（残り{remaining_minutes}分）",
                "remaining_minutes": remaining_minutes,
                "requested_duration": video_duration_minutes,
            }

        return {
            "can_process": True,
            "remaining_minutes": remaining_minutes,
            "requested_duration": video_duration_minutes,
        }

    async def consume_video_processing(
        self, user_id: str, video_duration_minutes: int
    ) -> Dict[str, Any]:
        """
        Consume video processing quota and roleplay session

        Args:
            user_id: User identifier
            video_duration_minutes: Video duration in minutes

        Returns:
            Dict with consumption result
        """
        user_stats = self._get_or_create_user_stats(user_id)

        # Check if reset is needed
        if self._check_reset_needed(user_stats):
            self._reset_user_stats(user_id)
            user_stats = self.usage_stats[user_id]

        # Check if processing is allowed
        can_process_result = await self.can_process_video(
            user_id, video_duration_minutes
        )
        if not can_process_result["can_process"]:
            return {"success": False, "consumed": False, **can_process_result}

        # Check if user has roleplay sessions remaining
        if user_stats.roleplay_sessions_remaining <= 0:
            return {
                "success": False,
                "consumed": False,
                "reason": "no_sessions_remaining",
                "message": "ロープレセッションが残っていません",
                "sessions_remaining": 0,
            }

        # Consume video processing quota and roleplay session
        user_stats.video_processing_minutes_used += video_duration_minutes
        user_stats.roleplay_sessions_remaining -= 1  # 1セッション消費
        user_stats.updated_at = datetime.now().isoformat()

        self._save_usage_data()

        logger.info(
            f"User {user_id} consumed {video_duration_minutes}min video processing + 1 roleplay session"
        )

        return {
            "success": True,
            "consumed": True,
            "video_minutes_consumed": video_duration_minutes,
            "roleplay_sessions_consumed": 1,
            "remaining_video_minutes": self.max_video_processing_minutes
            - user_stats.video_processing_minutes_used,
            "remaining_roleplay_sessions": user_stats.roleplay_sessions_remaining,
        }

    async def consume_roleplay_session(self, user_id: str) -> Dict[str, Any]:
        """
        Consume a roleplay session (for direct roleplay without video)

        Args:
            user_id: User identifier

        Returns:
            Dict with consumption result
        """
        user_stats = self._get_or_create_user_stats(user_id)

        # Check if reset is needed
        if self._check_reset_needed(user_stats):
            self._reset_user_stats(user_id)
            user_stats = self.usage_stats[user_id]

        # Check if user has roleplay sessions remaining
        if user_stats.roleplay_sessions_remaining <= 0:
            return {
                "success": False,
                "consumed": False,
                "reason": "no_sessions_remaining",
                "message": "ロープレセッションが残っていません",
                "sessions_remaining": 0,
            }

        # Consume roleplay session
        user_stats.roleplay_sessions_remaining -= 1
        user_stats.updated_at = datetime.now().isoformat()

        self._save_usage_data()

        logger.info(f"User {user_id} consumed 1 roleplay session")

        return {
            "success": True,
            "consumed": True,
            "roleplay_sessions_consumed": 1,
            "remaining_roleplay_sessions": user_stats.roleplay_sessions_remaining,
        }

    async def get_user_usage(self, user_id: str) -> Dict[str, Any]:
        """
        Get user usage statistics

        Args:
            user_id: User identifier

        Returns:
            Dict with user usage information
        """
        user_stats = self._get_or_create_user_stats(user_id)

        # Check if reset is needed
        if self._check_reset_needed(user_stats):
            self._reset_user_stats(user_id)
            user_stats = self.usage_stats[user_id]

        return {
            "user_id": user_id,
            "video_processing": {
                "minutes_used": user_stats.video_processing_minutes_used,
                "minutes_remaining": self.max_video_processing_minutes
                - user_stats.video_processing_minutes_used,
                "max_minutes": self.max_video_processing_minutes,
            },
            "roleplay_sessions": {
                "remaining": user_stats.roleplay_sessions_remaining,
                "initial": self.initial_roleplay_sessions,
                "used": self.initial_roleplay_sessions
                - user_stats.roleplay_sessions_remaining,
            },
            "period_info": {
                "last_reset": user_stats.last_reset_date,
                "reset_period_days": self.reset_period_days,
                "next_reset": self._calculate_next_reset_date(
                    user_stats.last_reset_date
                ),
            },
            "created_at": user_stats.created_at,
            "updated_at": user_stats.updated_at,
        }

    def _calculate_next_reset_date(self, last_reset_date: str) -> str:
        """Calculate next reset date"""
        try:
            last_reset = datetime.fromisoformat(last_reset_date)
            next_reset = last_reset + timedelta(days=self.reset_period_days)
            return next_reset.isoformat()
        except Exception as e:
            logger.error(f"Error calculating next reset date: {e}")
            return datetime.now().isoformat()

    async def get_all_users_usage(self) -> Dict[str, Any]:
        """Get usage statistics for all users"""
        all_usage = {}

        for user_id in self.usage_stats.keys():
            all_usage[user_id] = await self.get_user_usage(user_id)

        return {"total_users": len(all_usage), "users": all_usage}

    async def record_roleplay_session(
        self,
        user_id: str,
        session_id: str,
        scenario_type: str,
        duration_minutes: int,
        improvement_points: List[str] = None,
        performance_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Record a roleplay session for reminder tracking

        Args:
            user_id: User identifier
            session_id: Session identifier
            scenario_type: Type of roleplay scenario
            duration_minutes: Session duration in minutes
            improvement_points: List of improvement points from the session
            performance_score: Optional performance score (0-1)

        Returns:
            Updated user stats summary
        """
        try:
            user_stats = self._get_or_create_user_stats(user_id)
            now = datetime.now()

            # Create session record
            session = RoleplaySession(
                session_id=session_id,
                start_time=now.isoformat(),
                end_time=(now + timedelta(minutes=duration_minutes)).isoformat(),
                duration_minutes=duration_minutes,
                scenario_type=scenario_type,
                performance_score=performance_score,
                improvement_points=improvement_points or [],
            )

            # Update user stats
            user_stats.last_roleplay_date = now.isoformat()
            user_stats.total_roleplay_sessions += 1
            user_stats.updated_at = now.isoformat()

            # Add to recent sessions (keep only last 10)
            user_stats.recent_sessions.append(session)
            if len(user_stats.recent_sessions) > 10:
                user_stats.recent_sessions = user_stats.recent_sessions[-10:]

            # Update recent improvement points
            if improvement_points:
                user_stats.recent_improvement_points.extend(improvement_points)
                user_stats.recent_improvement_points = (
                    user_stats.recent_improvement_points[-5:]
                )  # Keep last 5

            # Calculate consecutive days
            user_stats.consecutive_days = await self._calculate_consecutive_days(
                user_id
            )

            # Save changes
            self._save_usage_data()

            logger.info(f"Recorded roleplay session for user {user_id}: {session_id}")

            return {
                "success": True,
                "session_recorded": True,
                "user_stats": {
                    "total_sessions": user_stats.total_roleplay_sessions,
                    "consecutive_days": user_stats.consecutive_days,
                    "last_session": user_stats.last_roleplay_date,
                },
            }

        except Exception as e:
            logger.error(f"Failed to record roleplay session for user {user_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _calculate_consecutive_days(self, user_id: str) -> int:
        """Calculate consecutive days of roleplay activity"""
        try:
            user_stats = self.usage_stats.get(user_id)
            if not user_stats or not user_stats.recent_sessions:
                return 0

            # Sort sessions by date
            sessions_by_date = {}
            for session in user_stats.recent_sessions:
                session_date = datetime.fromisoformat(session.start_time).date()
                if session_date not in sessions_by_date:
                    sessions_by_date[session_date] = []
                sessions_by_date[session_date].append(session)

            # Calculate consecutive days
            dates = sorted(sessions_by_date.keys(), reverse=True)
            consecutive_days = 0
            today = datetime.now().date()

            for i, date in enumerate(dates):
                expected_date = today - timedelta(days=i)
                if date == expected_date:
                    consecutive_days += 1
                else:
                    break

            return consecutive_days

        except Exception as e:
            logger.error(f"Error calculating consecutive days for user {user_id}: {e}")
            return 0

    async def update_reminder_settings(
        self,
        user_id: str,
        email_address: str,
        user_name: str,
        email_enabled: bool = True,
        reminder_days: List[int] = None,
        timezone: str = "Asia/Tokyo",
        enable_shame_system: bool = False,
    ) -> Dict[str, Any]:
        """
        Update user's reminder email settings

        Args:
            user_id: User identifier
            email_address: User's email address
            user_name: User's display name
            email_enabled: Whether to send reminder emails
            reminder_days: Days before deadline to send reminders
            timezone: User's timezone

        Returns:
            Update result
        """
        try:
            user_stats = self._get_or_create_user_stats(user_id)

            # Update reminder settings
            user_stats.reminder_settings = ReminderSettings(
                email_enabled=email_enabled,
                email_address=email_address,
                user_name=user_name,
                reminder_days=reminder_days or [3, 1, 0],
                timezone=timezone,
                enable_shame_system=enable_shame_system,
            )

            user_stats.updated_at = datetime.now().isoformat()

            # Save changes
            self._save_usage_data()

            logger.info(f"Updated reminder settings for user {user_id}")

            return {
                "success": True,
                "message": "Reminder settings updated successfully",
                "settings": asdict(user_stats.reminder_settings),
            }

        except Exception as e:
            logger.error(f"Failed to update reminder settings for user {user_id}: {e}")
            return {"success": False, "error": str(e)}

    async def get_users_for_reminder(self, reminder_type: str) -> List[Dict[str, Any]]:
        """
        Get users who need reminder emails

        Args:
            reminder_type: Type of reminder ("3days", "1day", "same_day")

        Returns:
            List of users who need reminders
        """
        reminder_users = []
        now = datetime.now()

        # Map reminder types to days
        reminder_day_map = {"3days": 3, "1day": 1, "same_day": 0}

        target_days = reminder_day_map.get(reminder_type)
        if target_days is None:
            logger.error(f"Invalid reminder type: {reminder_type}")
            return []

        try:
            for user_id, user_stats in self.usage_stats.items():
                # Check if user has email reminders enabled
                if not user_stats.reminder_settings.email_enabled:
                    continue

                if not user_stats.reminder_settings.email_address:
                    continue

                # Check if this reminder day is enabled for user
                if target_days not in user_stats.reminder_settings.reminder_days:
                    continue

                # Calculate days since last roleplay
                days_since_last = self._get_days_since_last_roleplay(user_stats)

                # Send reminder if it's been the target number of days
                if days_since_last == target_days:
                    # Include shame system status
                    shame_enabled = user_stats.reminder_settings.enable_shame_system

                    reminder_users.append(
                        {
                            "user_id": user_id,
                            "email": user_stats.reminder_settings.email_address,
                            "name": user_stats.reminder_settings.user_name,
                            "last_roleplay_date": user_stats.last_roleplay_date,
                            "consecutive_days": user_stats.consecutive_days,
                            "improvement_points": user_stats.recent_improvement_points,
                            "total_sessions": user_stats.total_roleplay_sessions,
                            "shame_system_enabled": shame_enabled,
                        }
                    )

            logger.info(
                f"Found {len(reminder_users)} users for {reminder_type} reminder"
            )
            return reminder_users

        except Exception as e:
            logger.error(f"Error getting users for reminder: {e}")
            return []

    def _get_days_since_last_roleplay(self, user_stats: UsageStats) -> int:
        """Calculate days since last roleplay session"""
        if not user_stats.last_roleplay_date:
            return 999  # No sessions yet

        try:
            last_date = datetime.fromisoformat(user_stats.last_roleplay_date).date()
            today = datetime.now().date()
            return (today - last_date).days
        except Exception as e:
            logger.error(f"Error calculating days since last roleplay: {e}")
            return 999

    async def get_user_roleplay_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get detailed roleplay statistics for a user

        Args:
            user_id: User identifier

        Returns:
            Detailed roleplay statistics
        """
        try:
            user_stats = self._get_or_create_user_stats(user_id)
            days_since_last = self._get_days_since_last_roleplay(user_stats)

            return {
                "user_id": user_id,
                "last_roleplay_date": user_stats.last_roleplay_date,
                "consecutive_days": user_stats.consecutive_days,
                "total_roleplay_sessions": user_stats.total_roleplay_sessions,
                "recent_sessions": [
                    asdict(session) for session in user_stats.recent_sessions
                ],
                "recent_improvement_points": user_stats.recent_improvement_points,
                "reminder_settings": asdict(user_stats.reminder_settings),
                "days_since_last": days_since_last,
                "needs_reminder": days_since_last >= 1,
                # 突きつけ用の詳細データ
                "confrontation_data": self._generate_confrontation_data(
                    user_stats, days_since_last
                ),
            }

        except Exception as e:
            logger.error(f"Error getting roleplay stats for user {user_id}: {e}")
            return {"error": str(e)}

    def _generate_confrontation_data(
        self, user_stats: UsageStats, days_since_last: int
    ) -> Dict[str, Any]:
        """
        サボり突きつけ用のデータ生成

        Args:
            user_stats: ユーザー統計
            days_since_last: 最後からの経過日数

        Returns:
            突きつけ用データ
        """
        now = datetime.now()

        # サボり機能が無効の場合は基本情報のみ
        shame_enabled = (
            user_stats.reminder_settings.enable_shame_system
            if user_stats.reminder_settings
            else False
        )

        if not shame_enabled:
            return {
                "shame_system_enabled": False,
                "days_since_last": days_since_last,
                "slacking_level": "disabled",
                "slacking_message": f"最後のロールプレイから{days_since_last}日経過しています。",
                "message": "サボり検知機能は無効になっています。レポート機能のみ利用可能です。",
                "basic_stats": {
                    "total_sessions": user_stats.total_roleplay_sessions,
                    "consecutive_days": user_stats.consecutive_days,
                    "days_since_last": days_since_last,
                },
            }

        # サボり度判定
        if days_since_last == 0:
            slacking_level = "excellent"  # 優秀
            slacking_message = (
                "今日もロールプレイを実行しています！素晴らしい継続力です。"
            )
        elif days_since_last <= 2:
            slacking_level = "good"  # 良好
            slacking_message = f"最後のロールプレイから{days_since_last}日経過。まだ習慣は維持できています。"
        elif days_since_last <= 7:
            slacking_level = "warning"  # 警告
            slacking_message = f"⚠️ 最後のロールプレイから{days_since_last}日経過。習慣が崩れかけています。"
        elif days_since_last <= 14:
            slacking_level = "danger"  # 危険
            slacking_message = f"🚨 最後のロールプレイから{days_since_last}日経過。完全にサボっています！"
        else:
            slacking_level = "critical"  # 重大
            slacking_message = f"💥 最後のロールプレイから{days_since_last}日経過。もはや習慣は完全に消失しています！"

        # 過去の実績
        total_sessions = user_stats.total_roleplay_sessions
        best_streak = (
            user_stats.consecutive_days if user_stats.consecutive_days > 0 else 0
        )

        # 損失計算
        potential_sessions_lost = max(
            0, days_since_last - 1
        )  # 本来できたはずのセッション数
        investment_wasted = potential_sessions_lost * 30  # 1セッション30分として

        # 改善ポイントの停滞
        improvement_stagnation = len(user_stats.recent_improvement_points) == 0

        # 厳しいメッセージ生成
        harsh_messages = []

        if days_since_last > 3:
            harsh_messages.append(
                f"あなたは{days_since_last}日間、営業スキル向上を放置しています。"
            )

        if potential_sessions_lost > 0:
            harsh_messages.append(
                f"この期間に{potential_sessions_lost}回のロールプレイができたはずです。"
            )
            harsh_messages.append(
                f"約{investment_wasted}分の成長機会を無駄にしました。"
            )

        if total_sessions > 0 and days_since_last > 7:
            harsh_messages.append(
                f"これまで{total_sessions}回のセッションを積み重ねたのに、その努力を台無しにしています。"
            )

        if best_streak > 0 and days_since_last > 3:
            harsh_messages.append(
                f"過去の最大連続記録{best_streak}日を裏切る行為です。"
            )

        if improvement_stagnation:
            harsh_messages.append(
                "改善ポイントも記録されておらず、成長への意欲が見られません。"
            )

        # 競合他社に負ける警告
        if days_since_last > 7:
            harsh_messages.append(
                "競合他社の営業担当は毎日スキルを磨いています。あなたは確実に遅れをとっています。"
            )

        return {
            "shame_system_enabled": True,
            "slacking_level": slacking_level,
            "days_since_last": days_since_last,
            "slacking_message": slacking_message,
            "harsh_messages": harsh_messages,
            "statistics": {
                "total_sessions": total_sessions,
                "best_streak": best_streak,
                "potential_sessions_lost": potential_sessions_lost,
                "investment_wasted_minutes": investment_wasted,
                "improvement_stagnation": improvement_stagnation,
            },
            "shame_metrics": {
                "days_wasted": days_since_last,
                "productivity_loss_percentage": min(
                    100, (days_since_last / 30) * 100
                ),  # 30日で100%とする
                "skill_deterioration_risk": (
                    "高"
                    if days_since_last > 7
                    else "中" if days_since_last > 3 else "低"
                ),
                "competitive_disadvantage": (
                    "深刻"
                    if days_since_last > 14
                    else "危険" if days_since_last > 7 else "軽微"
                ),
            },
        }

    async def get_all_users_activity_report(self) -> Dict[str, Any]:
        """
        全ユーザーの活動レポート（管理者・面談用）

        Returns:
            全ユーザーの活動状況
        """
        try:
            now = datetime.now()
            all_users_report = []

            for user_id, user_stats in self.usage_stats.items():
                days_since_last = self._get_days_since_last_roleplay(user_stats)
                confrontation_data = self._generate_confrontation_data(
                    user_stats, days_since_last
                )

                user_report = {
                    "user_id": user_id,
                    "user_name": (
                        user_stats.reminder_settings.user_name
                        if user_stats.reminder_settings
                        else user_id
                    ),
                    "last_roleplay_date": user_stats.last_roleplay_date,
                    "days_since_last": days_since_last,
                    "total_sessions": user_stats.total_roleplay_sessions,
                    "consecutive_days": user_stats.consecutive_days,
                    "slacking_level": confrontation_data["slacking_level"],
                    "confrontation_summary": confrontation_data["slacking_message"],
                    "needs_intervention": days_since_last > 7,  # 1週間以上は介入が必要
                    "risk_level": confrontation_data["shame_metrics"][
                        "competitive_disadvantage"
                    ],
                }

                all_users_report.append(user_report)

            # サボり度でソート（ひどい順）
            all_users_report.sort(key=lambda x: x["days_since_last"], reverse=True)

            # 統計情報
            total_users = len(all_users_report)
            slacking_users = len(
                [u for u in all_users_report if u["days_since_last"] > 3]
            )
            critical_users = len(
                [u for u in all_users_report if u["days_since_last"] > 14]
            )

            # エスカレーション対象ユーザーを特定（7日以上サボっている）
            escalation_users = []
            for user in all_users_report["users"]:
                if user["days_since_last"] > 7:  # 1週間以上サボっている
                    # サボり機能が有効なユーザーのみ対象
                    user_stats = self.usage_stats.get(user["user_id"])
                    if (
                        user_stats
                        and user_stats.reminder_settings
                        and user_stats.reminder_settings.enable_shame_system
                    ):
                        escalation_users.append(user)

            return {
                "success": True,
                "report_date": now.isoformat(),
                "summary": {
                    "total_users": total_users,
                    "slacking_users": slacking_users,
                    "critical_users": critical_users,
                    "slacking_rate": (
                        round((slacking_users / total_users * 100), 1)
                        if total_users > 0
                        else 0
                    ),
                },
                "users": all_users_report,
                "escalation_users": escalation_users,
            }

        except Exception as e:
            logger.error(f"Error generating all users activity report: {e}")
            return {"success": False, "error": str(e)}

    async def admin_reset_user(self, user_id: str) -> Dict[str, Any]:
        """Admin function to reset user usage"""
        if user_id not in self.usage_stats:
            return {"success": False, "message": f"User {user_id} not found"}

        self._reset_user_stats(user_id)

        return {
            "success": True,
            "message": f"Usage stats reset for user {user_id}",
            "new_stats": await self.get_user_usage(user_id),
        }

    async def admin_add_sessions(
        self, user_id: str, additional_sessions: int
    ) -> Dict[str, Any]:
        """Admin function to add roleplay sessions"""
        user_stats = self._get_or_create_user_stats(user_id)

        user_stats.roleplay_sessions_remaining += additional_sessions
        user_stats.updated_at = datetime.now().isoformat()

        self._save_usage_data()

        return {
            "success": True,
            "message": f"Added {additional_sessions} sessions for user {user_id}",
            "new_sessions_remaining": user_stats.roleplay_sessions_remaining,
        }


# Global service instance
_usage_limit_service: Optional[UsageLimitService] = None


def get_usage_limit_service() -> UsageLimitService:
    """Get global usage limit service instance"""
    global _usage_limit_service
    if _usage_limit_service is None:
        _usage_limit_service = UsageLimitService()
    return _usage_limit_service
