"""
Reminder Scheduler Service for Voice Roleplay System
営業ロールプレイリマインダー自動配信スケジューラー
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
from pathlib import Path
from dataclasses import dataclass, asdict

try:
    from services.usage_limit_service import UsageLimitService
    from services.email_service import EmailService, ReminderEmail
    from services.notification_service import (
        MultiChannelNotificationService,
        NotificationMessage,
    )
except ImportError:
    from app.services.usage_limit_service import UsageLimitService
    from app.services.email_service import EmailService, ReminderEmail
    from app.services.notification_service import (
        MultiChannelNotificationService,
        NotificationMessage,
    )

logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    """スケジューラー設定"""

    enabled: bool = True
    check_interval_minutes: int = 60  # 1時間ごとにチェック
    daily_check_hour: int = 9  # 毎日9時にチェック
    timezone: str = "Asia/Tokyo"
    max_emails_per_batch: int = 50  # バッチあたりの最大メール数


@dataclass
class ReminderLog:
    """リマインダー送信ログ"""

    user_id: str
    reminder_type: str
    sent_at: str
    email_address: str
    success: bool
    error_message: Optional[str] = None


class ReminderSchedulerService:
    """リマインダースケジューラーサービス"""

    def __init__(
        self,
        usage_service: Optional[UsageLimitService] = None,
        email_service: Optional[EmailService] = None,
        config_path: str = "config/reminder_scheduler.json",
    ):
        """
        Initialize reminder scheduler service

        Args:
            usage_service: Usage limit service instance
            email_service: Email service instance
            config_path: Path to scheduler configuration
        """
        self.usage_service = usage_service
        self.email_service = email_service
        self.config_path = Path(config_path)
        self.logs_path = Path("data/reminder_logs.json")

        # Create directories
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.logs_path.parent.mkdir(parents=True, exist_ok=True)

        # Load configuration
        self.config = self._load_config()

        # In-memory logs (keep last 1000 entries)
        self.recent_logs: List[ReminderLog] = []
        self._load_logs()

        # Scheduler state
        self.is_running = False
        self.last_check_date = None

        logger.info("Reminder scheduler service initialized")

    def _load_config(self) -> SchedulerConfig:
        """設定を読み込み"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                return SchedulerConfig(**config_data)
            else:
                return self._create_default_config()
        except Exception as e:
            logger.error(f"Failed to load scheduler config: {e}")
            return SchedulerConfig()

    def _create_default_config(self) -> SchedulerConfig:
        """デフォルト設定を作成"""
        config = SchedulerConfig()
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(asdict(config), f, ensure_ascii=False, indent=2)
            logger.info(f"Default scheduler config created at {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to create default config: {e}")
        return config

    def _load_logs(self) -> None:
        """ログを読み込み"""
        try:
            if self.logs_path.exists():
                with open(self.logs_path, "r", encoding="utf-8") as f:
                    logs_data = json.load(f)
                self.recent_logs = [ReminderLog(**log) for log in logs_data[-1000:]]
                logger.info(f"Loaded {len(self.recent_logs)} reminder logs")
        except Exception as e:
            logger.error(f"Failed to load reminder logs: {e}")
            self.recent_logs = []

    def _save_logs(self) -> None:
        """ログを保存"""
        try:
            logs_data = [asdict(log) for log in self.recent_logs[-1000:]]
            with open(self.logs_path, "w", encoding="utf-8") as f:
                json.dump(logs_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save reminder logs: {e}")

    async def start_scheduler(self) -> Dict[str, Any]:
        """スケジューラーを開始"""
        if self.is_running:
            return {"success": False, "message": "Scheduler is already running"}

        if not self.config.enabled:
            return {
                "success": False,
                "message": "Scheduler is disabled in configuration",
            }

        try:
            self.is_running = True
            logger.info("Starting reminder scheduler...")

            # バックグラウンドタスクとして実行
            asyncio.create_task(self._scheduler_loop())

            return {
                "success": True,
                "message": "Reminder scheduler started",
                "config": asdict(self.config),
            }

        except Exception as e:
            self.is_running = False
            logger.error(f"Failed to start scheduler: {e}")
            return {"success": False, "error": str(e)}

    async def stop_scheduler(self) -> Dict[str, Any]:
        """スケジューラーを停止"""
        self.is_running = False
        logger.info("Reminder scheduler stopped")
        return {"success": True, "message": "Reminder scheduler stopped"}

    async def _scheduler_loop(self) -> None:
        """メインスケジューラーループ"""
        logger.info("Reminder scheduler loop started")

        while self.is_running:
            try:
                await self._process_reminders()

                # 次のチェックまで待機
                await asyncio.sleep(self.config.check_interval_minutes * 60)

            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(300)  # エラー時は5分待機

    async def _process_reminders(self) -> Dict[str, Any]:
        """
        リマインダーの処理とエスカレーション
        """
        try:
            now = datetime.now()
            results = {
                "processed_reminders": 0,
                "escalation_notifications": 0,
                "errors": [],
            }

            # 通常のリマインダー処理
            for reminder_type in ["3days", "1day", "same_day"]:
                users = await self.usage_service.get_users_for_reminder(reminder_type)

                if users:
                    batch_result = await self._send_reminder_batch(users, reminder_type)
                    results["processed_reminders"] += len(users)

                    if batch_result.get("errors"):
                        results["errors"].extend(batch_result["errors"])

            # エスカレーション通知処理（週に1回実行）
            if now.weekday() == 0:  # 月曜日
                escalation_result = await self._process_escalation_notifications()
                results["escalation_notifications"] = escalation_result.get(
                    "sent_count", 0
                )

                if escalation_result.get("errors"):
                    results["errors"].extend(escalation_result["errors"])

            return {"success": True, "timestamp": now.isoformat(), "results": results}

        except Exception as e:
            logger.error(f"Error processing reminders: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _process_escalation_notifications(self) -> Dict[str, Any]:
        """
        エスカレーション通知の処理
        長期間サボっているユーザーに強化された通知を送信
        """
        try:
            # 全ユーザーレポート取得
            all_users_report = await self.usage_service.get_all_users_activity_report()

            if not all_users_report.get("success"):
                return {"success": False, "error": "Failed to get users report"}

            escalation_users = []
            sent_count = 0
            errors = []

            # エスカレーション対象ユーザーを特定（7日以上サボっている）
            for user in all_users_report["users"]:
                if user["days_since_last"] > 7:  # 1週間以上サボっている
                    escalation_users.append(user)

            logger.info(
                f"Found {len(escalation_users)} users for escalation notifications"
            )

            # エスカレーション通知を送信
            for user in escalation_users:
                try:
                    user_id = user["user_id"]
                    days_since_last = user["days_since_last"]

                    # ユーザーの詳細統計取得
                    user_stats = await self.usage_service.get_user_roleplay_stats(
                        user_id
                    )
                    confrontation_data = user_stats.get("confrontation_data", {})

                    # エスカレーションメッセージ作成
                    escalation_message = self._create_escalation_message(
                        user, confrontation_data
                    )

                    # エスカレーションメール送信
                    email_result = await self.email_service.send_reminder_email(
                        email_address=user_stats.get("reminder_settings", {}).get(
                            "email_address", ""
                        ),
                        user_name=user.get("user_name", user_id),
                        reminder_type="escalation",
                        personalized_message=escalation_message,
                        user_stats={
                            "days_since_last": days_since_last,
                            "consecutive_days": user.get("consecutive_days", 0),
                            "total_sessions": user.get("total_sessions", 0),
                        },
                    )

                    if email_result.get("success"):
                        sent_count += 1
                        logger.info(f"Escalation notification sent to user {user_id}")
                    else:
                        errors.append(
                            f"Failed to send escalation to {user_id}: {email_result.get('error')}"
                        )

                except Exception as e:
                    errors.append(
                        f"Error sending escalation to {user.get('user_id', 'unknown')}: {str(e)}"
                    )
                    logger.error(f"Error sending escalation notification: {e}")

            return {
                "success": True,
                "sent_count": sent_count,
                "target_users": len(escalation_users),
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"Error processing escalation notifications: {e}")
            return {"success": False, "error": str(e)}

    def _create_escalation_message(
        self, user: Dict[str, Any], confrontation_data: Dict[str, Any]
    ) -> str:
        """
        エスカレーション用のメッセージを作成
        """
        user_name = user.get("user_name", user.get("user_id"))
        days_since_last = user.get("days_since_last", 0)
        harsh_messages = confrontation_data.get("harsh_messages", [])

        escalation_message = f"""
🚨🚨🚨 最終警告：営業スキル向上の完全停滞 🚨🚨🚨

{user_name}さん、

これは最終警告です。あなたの営業スキル向上活動が {days_since_last} 日間完全に停止しています。

【深刻な問題】:
{chr(10).join(f"⚠️ {msg}" for msg in harsh_messages)}

【このままの状況が続くと】:
💥 営業成績の著しい低下
💥 顧客からの信頼失失
💥 競合他社への顧客流出
💥 キャリア上の重大な損失

【即座に必要なアクション】:
1. 今日中にロールプレイシステムにログイン
2. 最低でも週3回のロールプレイ実行を再開
3. 進捗報告とフィードバックセッションの予約

これ以上の遅延は許されません。
あなたの営業キャリアと会社の業績が危機に瀕しています。

即座に行動を開始してください。

営業ロールプレイシステム管理者
"""

        return escalation_message

    async def _send_reminder_batch(
        self, users: List[Dict[str, Any]], reminder_type: str
    ) -> Dict[str, Any]:
        """リマインダーメールのバッチ送信"""
        errors = []
        for user_data in users:
            try:
                # パーソナライズされたメッセージを生成
                personalized_message = self._generate_personalized_message(
                    user_data, reminder_type
                )

                # リマインダーメールオブジェクトを作成
                reminder_email = ReminderEmail(
                    user_email=user_data["email"],
                    user_name=user_data["name"],
                    reminder_type=reminder_type,
                    last_roleplay_date=user_data["last_roleplay_date"],
                    streak_count=user_data["consecutive_days"],
                    improvement_points=user_data["improvement_points"][:3],  # 最大3個
                    personalized_message=personalized_message,
                )

                # メール送信
                success = await self.email_service.send_reminder_email(reminder_email)

                # ログ記録
                log_entry = ReminderLog(
                    user_id=user_data["user_id"],
                    reminder_type=reminder_type,
                    sent_at=datetime.now().isoformat(),
                    email_address=user_data["email"],
                    success=success,
                    error_message=None if success else "Failed to send email",
                )

                self.recent_logs.append(log_entry)

                if success:
                    logger.info(
                        f"Sent {reminder_type} reminder to {user_data['email']}"
                    )
                else:
                    logger.error(
                        f"Failed to send {reminder_type} reminder to {user_data['email']}"
                    )

                # メール送信間隔
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(
                    f"Error sending reminder to {user_data.get('email', 'unknown')}: {e}"
                )

                # エラーログ記録
                error_log = ReminderLog(
                    user_id=user_data.get("user_id", "unknown"),
                    reminder_type=reminder_type,
                    sent_at=datetime.now().isoformat(),
                    email_address=user_data.get("email", "unknown"),
                    success=False,
                    error_message=str(e),
                )
                self.recent_logs.append(error_log)
                errors.append(
                    f"Failed to send {reminder_type} reminder to {user_data.get('email', 'unknown')}: {str(e)}"
                )

        # ログ保存
        self._save_logs()
        return {"success": True, "sent_count": len(users), "errors": errors}

    def _generate_personalized_message(
        self, user_data: Dict[str, Any], reminder_type: str
    ) -> str:
        """パーソナライズされたメッセージを生成"""
        try:
            name = user_data.get("name", "お客様")
            consecutive_days = user_data.get("consecutive_days", 0)
            total_sessions = user_data.get("total_sessions", 0)

            # 基本メッセージテンプレート
            base_messages = {
                "3days": [
                    f"{name}さんの営業スキル向上を応援しています！",
                    f"これまで{total_sessions}回のロールプレイを実行されていますね。",
                    f"継続的な練習が営業成果につながります。",
                ],
                "1day": [
                    f"{name}さん、明日が期限です！",
                    f"これまで{consecutive_days}日連続で頑張っていますね。",
                    f"せっかくの連続記録を途切れさせないようにしましょう。",
                ],
                "same_day": [
                    f"{name}さん、今日が最後のチャンスです！",
                    f"今日で連続記録が{consecutive_days}日から途切れてしまいます。",
                    f"10分だけでも練習すれば、記録を継続できます。",
                ],
            }

            # パフォーマンスに基づく追加メッセージ
            performance_messages = []

            if consecutive_days >= 7:
                performance_messages.append("1週間以上の継続、素晴らしいですね！")
            elif consecutive_days >= 3:
                performance_messages.append("3日以上の継続、とても良いペースです！")

            if total_sessions >= 20:
                performance_messages.append(
                    "20回以上のセッション、かなりの経験を積まれています。"
                )
            elif total_sessions >= 10:
                performance_messages.append(
                    "10回以上のセッション、着実にスキルが向上していますね。"
                )

            # 改善ポイントに基づくメッセージ
            improvement_points = user_data.get("improvement_points", [])
            if improvement_points:
                recent_point = improvement_points[-1]
                performance_messages.append(
                    f"前回は「{recent_point}」の改善を目指していましたね。"
                )

            # メッセージ組み立て
            messages = base_messages.get(reminder_type, ["頑張ってください！"])
            if performance_messages:
                messages.extend(performance_messages[:2])  # 最大2個追加

            return " ".join(messages)

        except Exception as e:
            logger.error(f"Error generating personalized message: {e}")
            return "営業スキル向上のために、ぜひロールプレイを継続してください！"

    async def manual_send_reminders(self, reminder_type: str = None) -> Dict[str, Any]:
        """手動でリマインダーを送信"""
        if not self.usage_service or not self.email_service:
            return {"success": False, "error": "Required services not available"}

        try:
            reminder_types = (
                [reminder_type] if reminder_type else ["3days", "1day", "same_day"]
            )
            results = {}

            for rtype in reminder_types:
                users = await self.usage_service.get_users_for_reminder(rtype)
                await self._send_reminder_batch(users, rtype)
                results[rtype] = len(users)

            return {
                "success": True,
                "message": "Manual reminders sent",
                "results": results,
            }

        except Exception as e:
            logger.error(f"Error in manual reminder send: {e}")
            return {"success": False, "error": str(e)}

    async def get_scheduler_status(self) -> Dict[str, Any]:
        """スケジューラーの状態を取得"""
        return {
            "is_running": self.is_running,
            "config": asdict(self.config),
            "last_check_date": (
                self.last_check_date.isoformat() if self.last_check_date else None
            ),
            "recent_logs_count": len(self.recent_logs),
            "last_10_logs": [asdict(log) for log in self.recent_logs[-10:]],
        }

    async def update_config(self, **kwargs) -> Dict[str, Any]:
        """設定を更新"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

            # 設定保存
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(asdict(self.config), f, ensure_ascii=False, indent=2)

            return {
                "success": True,
                "message": "Configuration updated",
                "config": asdict(self.config),
            }

        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return {"success": False, "error": str(e)}


# Dependency injection
_reminder_scheduler: Optional[ReminderSchedulerService] = None


def get_reminder_scheduler_service(
    usage_service: UsageLimitService = None, email_service: EmailService = None
) -> ReminderSchedulerService:
    """Get reminder scheduler service instance"""
    global _reminder_scheduler
    if _reminder_scheduler is None:
        _reminder_scheduler = ReminderSchedulerService(usage_service, email_service)
    return _reminder_scheduler
