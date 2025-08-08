"""
Reminder API for Voice Roleplay System
営業ロールプレイリマインダーAPI
"""

from fastapi import APIRouter, HTTPException, Depends, Form, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional, List
import logging
import uuid
from datetime import datetime

try:
    from services.usage_limit_service import get_usage_limit_service, UsageLimitService
    from services.email_service import get_email_service, EmailService
    from services.reminder_scheduler_service import get_reminder_scheduler_service, ReminderSchedulerService
    from services.notification_service import get_notification_service, MultiChannelNotificationService, NotificationMessage
except ImportError:
    from app.services.usage_limit_service import get_usage_limit_service, UsageLimitService
    from app.services.email_service import get_email_service, EmailService
    from app.services.reminder_scheduler_service import get_reminder_scheduler_service, ReminderSchedulerService
    from app.services.notification_service import get_notification_service, MultiChannelNotificationService, NotificationMessage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reminder", tags=["Reminder"])

# Pydantic models for request/response
class ReminderSettingsRequest(BaseModel):
    """リマインダー設定リクエスト"""
    email_address: EmailStr
    user_name: str
    email_enabled: bool = True
    reminder_days: List[int] = [3, 1, 0]
    timezone: str = "Asia/Tokyo"
    enable_shame_system: bool = False  # サボり検知・突きつけ機能のオンオフ

class RoleplaySessionRequest(BaseModel):
    """ロールプレイセッション記録リクエスト"""
    scenario_type: str
    duration_minutes: int
    improvement_points: List[str] = []
    performance_score: Optional[float] = None

class EmailConfigRequest(BaseModel):
    """メール設定リクエスト"""
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    from_email: EmailStr
    from_name: str = "営業ロールプレイシステム"
    use_tls: bool = True

class NotificationChannelRequest(BaseModel):
    """通知チャンネル設定リクエスト"""
    channel: str
    enabled: bool = True
    webhook_url: Optional[str] = None
    api_token: Optional[str] = None
    bot_token: Optional[str] = None
    channel_id: Optional[str] = None
    additional_config: Dict[str, Any] = {}

class MultiChannelTestRequest(BaseModel):
    """マルチチャンネルテストリクエスト"""
    channels: List[str]
    test_message: str = "テストメッセージです"

@router.post("/settings/update")
async def update_reminder_settings(
    user_id: str = Form(...),
    settings: ReminderSettingsRequest = Form(...),
    usage_service: UsageLimitService = Depends(get_usage_limit_service)
) -> Dict[str, Any]:
    """
    ユーザーのリマインダー設定を更新
    
    Args:
        user_id: ユーザーID
        settings: リマインダー設定
        usage_service: 利用制限サービス
        
    Returns:
        更新結果
    """
    try:
        logger.info(f"Updating reminder settings for user: {user_id}")
        
        result = await usage_service.update_reminder_settings(
            user_id=user_id,
            email_address=settings.email_address,
            user_name=settings.user_name,
            email_enabled=settings.email_enabled,
            reminder_days=settings.reminder_days,
            timezone=settings.timezone,
            enable_shame_system=settings.enable_shame_system
        )
        
        if result.get("success"):
            logger.info(f"Reminder settings updated for user: {user_id}")
            return {
                "success": True,
                "message": "リマインダー設定が更新されました",
                "settings": result.get("settings")
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "設定更新に失敗しました"))
            
    except Exception as e:
        logger.error(f"Error updating reminder settings for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"設定更新エラー: {str(e)}")

@router.get("/settings/{user_id}")
async def get_reminder_settings(
    user_id: str,
    usage_service: UsageLimitService = Depends(get_usage_limit_service)
) -> Dict[str, Any]:
    """
    ユーザーのリマインダー設定を取得
    
    Args:
        user_id: ユーザーID
        usage_service: 利用制限サービス
        
    Returns:
        リマインダー設定
    """
    try:
        stats = await usage_service.get_user_roleplay_stats(user_id)
        
        if "error" in stats:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
        return {
            "success": True,
            "user_id": user_id,
            "reminder_settings": stats.get("reminder_settings"),
            "activity_stats": {
                "last_roleplay_date": stats.get("last_roleplay_date"),
                "consecutive_days": stats.get("consecutive_days"),
                "total_sessions": stats.get("total_roleplay_sessions"),
                "days_since_last": stats.get("days_since_last"),
                "needs_reminder": stats.get("needs_reminder")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting reminder settings for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"設定取得エラー: {str(e)}")

@router.post("/session/record")
async def record_roleplay_session(
    user_id: str = Form(...),
    scenario_type: str = Form(...),
    duration_minutes: int = Form(...),
    improvement_points: List[str] = Form(default=[]),
    performance_score: Optional[float] = Form(None),
    usage_service: UsageLimitService = Depends(get_usage_limit_service)
) -> Dict[str, Any]:
    """
    ロールプレイセッションを記録
    
    Args:
        user_id: ユーザーID
        session_data: セッションデータ
        usage_service: 利用制限サービス
        
    Returns:
        記録結果
    """
    try:
        session_id = str(uuid.uuid4())
        
        logger.info(f"Recording roleplay session for user: {user_id}")
        
        result = await usage_service.record_roleplay_session(
            user_id=user_id,
            session_id=session_id,
            scenario_type=scenario_type,
            duration_minutes=duration_minutes,
            improvement_points=improvement_points,
            performance_score=performance_score
        )
        
        if result.get("success"):
            logger.info(f"Roleplay session recorded: {session_id}")
            return {
                "success": True,
                "message": "ロールプレイセッションが記録されました",
                "session_id": session_id,
                "user_stats": result.get("user_stats")
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "セッション記録に失敗しました"))
            
    except Exception as e:
        logger.error(f"Error recording roleplay session for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"セッション記録エラー: {str(e)}")

@router.get("/stats/{user_id}")
async def get_user_activity_stats(
    user_id: str,
    usage_service: UsageLimitService = Depends(get_usage_limit_service)
) -> Dict[str, Any]:
    """
    ユーザーの活動統計を取得
    
    Args:
        user_id: ユーザーID
        usage_service: 利用制限サービス
        
    Returns:
        活動統計
    """
    try:
        stats = await usage_service.get_user_roleplay_stats(user_id)
        
        if "error" in stats:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
        return {
            "success": True,
            "user_id": user_id,
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting activity stats for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"統計取得エラー: {str(e)}")

@router.post("/shame-system/{user_id}/enable")
async def enable_shame_system(
    user_id: str,
    usage_service: UsageLimitService = Depends(get_usage_limit_service)
) -> Dict[str, Any]:
    """
    ユーザーのサボり検知機能を有効化（本気の人向け）
    
    Args:
        user_id: ユーザーID
        usage_service: 利用制限サービス
        
    Returns:
        有効化結果
    """
    try:
        # 現在の設定を取得
        stats = await usage_service.get_user_roleplay_stats(user_id)
        
        if "error" in stats:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
        current_settings = stats.get("reminder_settings", {})
        
        # サボり機能を有効化
        result = await usage_service.update_reminder_settings(
            user_id=user_id,
            email_address=current_settings.get("email_address", ""),
            user_name=current_settings.get("user_name", user_id),
            email_enabled=current_settings.get("email_enabled", True),
            reminder_days=current_settings.get("reminder_days", [3, 1, 0]),
            timezone=current_settings.get("timezone", "Asia/Tokyo"),
            enable_shame_system=True  # 有効化
        )
        
        if result.get("success"):
            logger.info(f"Shame system enabled for user: {user_id}")
            return {
                "success": True,
                "message": "🔥 サボり検知機能が有効になりました！本気モードでスキル向上に取り組みましょう。",
                "user_id": user_id,
                "shame_system_enabled": True,
                "warning": "この機能により、サボった場合は厳しく指摘されます。覚悟はよろしいですか？"
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "設定更新に失敗しました"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling shame system for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"サボり機能有効化エラー: {str(e)}")

@router.post("/shame-system/{user_id}/disable")
async def disable_shame_system(
    user_id: str,
    usage_service: UsageLimitService = Depends(get_usage_limit_service)
) -> Dict[str, Any]:
    """
    ユーザーのサボり検知機能を無効化（プレッシャー軽減）
    
    Args:
        user_id: ユーザーID
        usage_service: 利用制限サービス
        
    Returns:
        無効化結果
    """
    try:
        # 現在の設定を取得
        stats = await usage_service.get_user_roleplay_stats(user_id)
        
        if "error" in stats:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
        current_settings = stats.get("reminder_settings", {})
        
        # サボり機能を無効化
        result = await usage_service.update_reminder_settings(
            user_id=user_id,
            email_address=current_settings.get("email_address", ""),
            user_name=current_settings.get("user_name", user_id),
            email_enabled=current_settings.get("email_enabled", True),
            reminder_days=current_settings.get("reminder_days", [3, 1, 0]),
            timezone=current_settings.get("timezone", "Asia/Tokyo"),
            enable_shame_system=False  # 無効化
        )
        
        if result.get("success"):
            logger.info(f"Shame system disabled for user: {user_id}")
            return {
                "success": True,
                "message": "😌 サボり検知機能が無効になりました。基本的なレポート機能のみ利用できます。",
                "user_id": user_id,
                "shame_system_enabled": False,
                "note": "いつでも再度有効化できます。本気でスキル向上に取り組む時はお知らせください。"
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "設定更新に失敗しました"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling shame system for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"サボり機能無効化エラー: {str(e)}")

@router.get("/shame-system/{user_id}/status")
async def get_shame_system_status(
    user_id: str,
    usage_service: UsageLimitService = Depends(get_usage_limit_service)
) -> Dict[str, Any]:
    """
    ユーザーのサボり検知機能の状態を確認
    
    Args:
        user_id: ユーザーID
        usage_service: 利用制限サービス
        
    Returns:
        機能の状態
    """
    try:
        stats = await usage_service.get_user_roleplay_stats(user_id)
        
        if "error" in stats:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
        confrontation_data = stats.get("confrontation_data", {})
        shame_enabled = confrontation_data.get("shame_system_enabled", False)
        
        return {
            "success": True,
            "user_id": user_id,
            "shame_system_enabled": shame_enabled,
            "status": "有効" if shame_enabled else "無効",
            "description": "本気モード：サボりを厳しく指摘します" if shame_enabled else "優しいモード：基本レポートのみ",
            "can_enable": not shame_enabled,
            "can_disable": shame_enabled
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting shame system status for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"状態確認エラー: {str(e)}")

@router.get("/confrontation/{user_id}")
async def get_user_confrontation_report(
    user_id: str,
    usage_service: UsageLimitService = Depends(get_usage_limit_service)
) -> Dict[str, Any]:
    """
    ユーザーのサボり突きつけレポート（面談用）
    
    Args:
        user_id: ユーザーID
        usage_service: 利用制限サービス
        
    Returns:
        詳細な突きつけレポート
    """
    try:
        stats = await usage_service.get_user_roleplay_stats(user_id)
        
        if "error" in stats:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
        confrontation_data = stats.get("confrontation_data", {})
        
        # 面談用の追加情報
        meeting_notes = {
            "suggested_actions": [],
            "intervention_urgency": "低",
            "recommended_frequency": "週1回"
        }
        
        days_since_last = confrontation_data.get("days_since_last", 0)
        
        if days_since_last > 14:
            meeting_notes["intervention_urgency"] = "緊急"
            meeting_notes["recommended_frequency"] = "毎日"
            meeting_notes["suggested_actions"] = [
                "即座にロールプレイスケジュールを再設定",
                "毎日の実行確認を実施",
                "成果目標の再設定と短期目標の設定",
                "上司への報告とサポート体制の強化"
            ]
        elif days_since_last > 7:
            meeting_notes["intervention_urgency"] = "高"
            meeting_notes["recommended_frequency"] = "週3回"
            meeting_notes["suggested_actions"] = [
                "週次スケジュールの見直し",
                "習慣化のための仕組み作り",
                "短期的な成果目標の設定",
                "進捗の定期確認"
            ]
        elif days_since_last > 3:
            meeting_notes["intervention_urgency"] = "中"
            meeting_notes["recommended_frequency"] = "週2回"
            meeting_notes["suggested_actions"] = [
                "スケジュール調整のサポート",
                "モチベーション向上施策",
                "習慣継続のためのリマインダー強化"
            ]
        
        return {
            "success": True,
            "user_id": user_id,
            "user_name": stats.get("reminder_settings", {}).get("user_name", user_id),
            "confrontation_data": confrontation_data,
            "meeting_notes": meeting_notes,
            "report_generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting confrontation report for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"突きつけレポート取得エラー: {str(e)}")

@router.get("/admin/all-users-report")
async def get_all_users_activity_report(
    usage_service: UsageLimitService = Depends(get_usage_limit_service)
) -> Dict[str, Any]:
    """
    全ユーザーの活動レポート（管理者用）
    サボっているユーザーを特定するためのダッシュボード
    
    Args:
        usage_service: 利用制限サービス
        
    Returns:
        全ユーザーの活動状況とサボり度
    """
    try:
        report = await usage_service.get_all_users_activity_report()
        
        if not report.get("success"):
            raise HTTPException(status_code=500, detail=report.get("error", "レポート生成に失敗しました"))
        
        return {
            "success": True,
            "message": "全ユーザー活動レポート取得完了",
            "report": report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting all users activity report: {e}")
        raise HTTPException(status_code=500, detail=f"全ユーザーレポート取得エラー: {str(e)}")

@router.post("/shame-notification/{user_id}")
async def send_shame_notification(
    user_id: str,
    channels: List[str] = Form(default=["email"]),
    usage_service: UsageLimitService = Depends(get_usage_limit_service),
    notification_service: MultiChannelNotificationService = Depends(get_notification_service)
) -> Dict[str, Any]:
    """
    サボっているユーザーに恥辱通知を送信
    
    Args:
        user_id: ユーザーID
        channels: 送信チャンネル (email, slack, discord等)
        usage_service: 利用制限サービス
        notification_service: 通知サービス
        
    Returns:
        送信結果
    """
    try:
        # ユーザーの突きつけデータ取得
        stats = await usage_service.get_user_roleplay_stats(user_id)
        
        if "error" in stats:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
        confrontation_data = stats.get("confrontation_data", {})
        days_since_last = confrontation_data.get("days_since_last", 0)
        
        # サボり機能が無効の場合は送信しない
        if not confrontation_data.get("shame_system_enabled", False):
            return {
                "success": False,
                "message": "このユーザーはサボり検知機能を無効にしているため、恥辱通知は送信されませんでした",
                "shame_system_enabled": False
            }
        
        # サボり度が低い場合は送信しない
        if days_since_last <= 2:
            return {
                "success": False,
                "message": "ユーザーは十分に活動しているため、恥辱通知は送信されませんでした",
                "days_since_last": days_since_last
            }
        
        # 恥辱メッセージ作成
        user_name = stats.get("reminder_settings", {}).get("user_name", user_id)
        harsh_messages = confrontation_data.get("harsh_messages", [])
        
        shame_message = f"""
🚨 【緊急】営業スキル向上の停滞について 🚨

{user_name}さん、

あなたの最近の活動状況について深刻な懸念があります：

{chr(10).join(f"• {msg}" for msg in harsh_messages)}

現在の状況：
• 最後のロールプレイから {days_since_last} 日経過
• スキル劣化リスク: {confrontation_data.get('shame_metrics', {}).get('skill_deterioration_risk', '不明')}
• 競合優位性の損失: {confrontation_data.get('shame_metrics', {}).get('competitive_disadvantage', '不明')}

今すぐロールプレイシステムにアクセスして、スキル向上を再開してください。
あなたの営業成績と将来のキャリアがかかっています。

営業ロールプレイシステム
"""
        
        # 複数チャンネルに送信
        notification_message = NotificationMessage(
            title="【緊急】営業スキル向上の停滞について",
            content=shame_message,
            urgency="high",
            user_id=user_id,
            notification_type="shame_alert"
        )
        
        send_results = await notification_service.send_multi_channel(
            message=notification_message,
            channels=channels
        )
        
        logger.info(f"Shame notification sent to user {user_id} via channels: {channels}")
        
        return {
            "success": True,
            "message": f"恥辱通知を {len(channels)} チャンネルに送信しました",
            "user_id": user_id,
            "days_since_last": days_since_last,
            "channels_used": channels,
            "send_results": send_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending shame notification to user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"恥辱通知送信エラー: {str(e)}")

# Scheduler management endpoints (admin only)
@router.post("/scheduler/start")
async def start_reminder_scheduler(
    usage_service: UsageLimitService = Depends(get_usage_limit_service),
    email_service: EmailService = Depends(get_email_service)
) -> Dict[str, Any]:
    """
    リマインダースケジューラーを開始（管理者専用）
    
    Args:
        usage_service: 利用制限サービス
        email_service: メールサービス
        
    Returns:
        開始結果
    """
    try:
        scheduler = get_reminder_scheduler_service(usage_service, email_service)
        result = await scheduler.start_scheduler()
        
        if result.get("success"):
            logger.info("Reminder scheduler started via API")
            return {
                "success": True,
                "message": "リマインダースケジューラーが開始されました",
                "config": result.get("config")
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("message", "スケジューラー開始に失敗しました"))
            
    except Exception as e:
        logger.error(f"Error starting reminder scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"スケジューラー開始エラー: {str(e)}")

@router.post("/scheduler/stop")
async def stop_reminder_scheduler(
    usage_service: UsageLimitService = Depends(get_usage_limit_service),
    email_service: EmailService = Depends(get_email_service)
) -> Dict[str, Any]:
    """
    リマインダースケジューラーを停止（管理者専用）
    
    Returns:
        停止結果
    """
    try:
        scheduler = get_reminder_scheduler_service(usage_service, email_service)
        result = await scheduler.stop_scheduler()
        
        logger.info("Reminder scheduler stopped via API")
        return {
            "success": True,
            "message": "リマインダースケジューラーが停止されました"
        }
        
    except Exception as e:
        logger.error(f"Error stopping reminder scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"スケジューラー停止エラー: {str(e)}")

@router.get("/scheduler/status")
async def get_scheduler_status(
    usage_service: UsageLimitService = Depends(get_usage_limit_service),
    email_service: EmailService = Depends(get_email_service)
) -> Dict[str, Any]:
    """
    スケジューラーの状態を取得
    
    Returns:
        スケジューラー状態
    """
    try:
        scheduler = get_reminder_scheduler_service(usage_service, email_service)
        status = await scheduler.get_scheduler_status()
        
        return {
            "success": True,
            "scheduler_status": status
        }
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=f"状態取得エラー: {str(e)}")

@router.post("/scheduler/send")
async def manual_send_reminders(
    reminder_type: Optional[str] = Form(None),
    usage_service: UsageLimitService = Depends(get_usage_limit_service),
    email_service: EmailService = Depends(get_email_service)
) -> Dict[str, Any]:
    """
    手動でリマインダーを送信（管理者専用）
    
    Args:
        reminder_type: リマインダータイプ（3days, 1day, same_day）
        usage_service: 利用制限サービス
        email_service: メールサービス
        
    Returns:
        送信結果
    """
    try:
        scheduler = get_reminder_scheduler_service(usage_service, email_service)
        result = await scheduler.manual_send_reminders(reminder_type)
        
        if result.get("success"):
            logger.info(f"Manual reminders sent: {result.get('results')}")
            return {
                "success": True,
                "message": "リマインダーを手動送信しました",
                "results": result.get("results")
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "リマインダー送信に失敗しました"))
            
    except Exception as e:
        logger.error(f"Error sending manual reminders: {e}")
        raise HTTPException(status_code=500, detail=f"手動送信エラー: {str(e)}")

# Email configuration endpoints (admin only)
@router.post("/email/test")
async def test_email_connection(
    email_service: EmailService = Depends(get_email_service)
) -> Dict[str, Any]:
    """
    メール接続をテスト（管理者専用）
    
    Args:
        email_service: メールサービス
        
    Returns:
        テスト結果
    """
    try:
        result = await email_service.test_email_connection()
        
        if result.get("success"):
            return {
                "success": True,
                "message": "メール接続テストが成功しました",
                "details": result.get("message")
            }
        else:
            return {
                "success": False,
                "message": "メール接続テストが失敗しました",
                "error": result.get("error")
            }
            
    except Exception as e:
        logger.error(f"Error testing email connection: {e}")
        raise HTTPException(status_code=500, detail=f"メール接続テストエラー: {str(e)}")

@router.get("/users/due")
async def get_users_due_for_reminder(
    reminder_type: str,
    usage_service: UsageLimitService = Depends(get_usage_limit_service)
) -> Dict[str, Any]:
    """
    リマインダーが必要なユーザーを取得（管理者専用）
    
    Args:
        reminder_type: リマインダータイプ（3days, 1day, same_day）
        usage_service: 利用制限サービス
        
    Returns:
        対象ユーザー一覧
    """
    try:
        if reminder_type not in ["3days", "1day", "same_day"]:
            raise HTTPException(status_code=400, detail="Invalid reminder type")
        
        users = await usage_service.get_users_for_reminder(reminder_type)
        
        return {
            "success": True,
            "reminder_type": reminder_type,
            "user_count": len(users),
            "users": users
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting users due for reminder: {e}")
        raise HTTPException(status_code=500, detail=f"ユーザー取得エラー: {str(e)}")

@router.get("/dashboard")
async def get_reminder_dashboard(
    usage_service: UsageLimitService = Depends(get_usage_limit_service),
    email_service: EmailService = Depends(get_email_service)
) -> Dict[str, Any]:
    """
    リマインダーシステムのダッシュボード情報を取得
    
    Returns:
        ダッシュボードデータ
    """
    try:
        # スケジューラー状態
        scheduler = get_reminder_scheduler_service(usage_service, email_service)
        scheduler_status = await scheduler.get_scheduler_status()
        
        # 各タイプのリマインダー対象ユーザー数
        reminder_counts = {}
        for reminder_type in ["3days", "1day", "same_day"]:
            users = await usage_service.get_users_for_reminder(reminder_type)
            reminder_counts[reminder_type] = len(users)
        
        # メール接続状態
        email_status = await email_service.test_email_connection()
        
        return {
            "success": True,
            "dashboard": {
                "scheduler_status": scheduler_status,
                "reminder_counts": reminder_counts,
                "email_status": email_status,
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting reminder dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"ダッシュボード取得エラー: {str(e)}")

# Background task for automatic scheduler startup
async def startup_reminder_scheduler():
    """アプリケーション起動時にスケジューラーを自動開始"""
    try:
        try:
            from services.usage_limit_service import get_usage_limit_service
            from services.email_service import get_email_service
        except ImportError:
            from app.services.usage_limit_service import get_usage_limit_service
            from app.services.email_service import get_email_service
        
        usage_service = get_usage_limit_service()
        email_service = get_email_service()
        scheduler = get_reminder_scheduler_service(usage_service, email_service)
        
        result = await scheduler.start_scheduler()
        if result.get("success"):
            logger.info("Reminder scheduler auto-started on application startup")
        else:
            logger.warning(f"Failed to auto-start reminder scheduler: {result.get('message')}")
            
    except Exception as e:
        logger.error(f"Error auto-starting reminder scheduler: {e}")

# Multi-channel notification endpoints
@router.post("/channels/test")
async def test_notification_channel(
    channel: str = Form(...),
    notification_service: MultiChannelNotificationService = Depends(get_notification_service)
) -> Dict[str, Any]:
    """
    通知チャンネルをテスト
    
    Args:
        channel: テストするチャンネル (slack, discord, telegram, teams, line, sms)
        notification_service: 通知サービス
        
    Returns:
        テスト結果
    """
    try:
        result = await notification_service.test_channel(channel)
        
        return {
            "success": True,
            "message": f"{channel}チャンネルのテストが完了しました",
            "test_result": result
        }
        
    except Exception as e:
        logger.error(f"Error testing notification channel {channel}: {e}")
        raise HTTPException(status_code=500, detail=f"チャンネルテストエラー: {str(e)}")

@router.post("/channels/test-multi")
async def test_multiple_channels(
    test_request: MultiChannelTestRequest,
    notification_service: MultiChannelNotificationService = Depends(get_notification_service)
) -> Dict[str, Any]:
    """
    複数チャンネルを同時テスト
    
    Args:
        test_request: テストリクエスト
        notification_service: 通知サービス
        
    Returns:
        テスト結果
    """
    try:
        # テストメッセージを作成
        test_message = NotificationMessage(
            title="🧪 マルチチャンネルテスト",
            content=test_request.test_message,
            user_id="test_user",
            reminder_type="test",
            channel="multi"
        )
        
        # 複数チャンネルに送信
        result = await notification_service.send_multi_channel(test_message, test_request.channels)
        
        return {
            "success": result.get("success", False),
            "message": f"{result.get('successful_channels', 0)}/{result.get('total_channels', 0)} チャンネルでテスト成功",
            "detailed_results": result.get("results", {}),
            "summary": {
                "total_channels": result.get("total_channels", 0),
                "successful": result.get("successful_channels", 0),
                "failed": result.get("total_channels", 0) - result.get("successful_channels", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error testing multiple channels: {e}")
        raise HTTPException(status_code=500, detail=f"マルチチャンネルテストエラー: {str(e)}")

@router.get("/channels/available")
async def get_available_channels() -> Dict[str, Any]:
    """
    利用可能な通知チャンネル一覧を取得
    
    Returns:
        チャンネル情報
    """
    channels = {
        "slack": {
            "name": "Slack",
            "cost": "無料",
            "setup": "Webhook URL が必要",
            "use_case": "企業・チーム利用",
            "popularity": "⭐⭐⭐⭐⭐"
        },
        "discord": {
            "name": "Discord", 
            "cost": "無料",
            "setup": "Webhook URL が必要",
            "use_case": "コミュニティ・個人利用",
            "popularity": "⭐⭐⭐⭐"
        },
        "telegram": {
            "name": "Telegram",
            "cost": "無料",
            "setup": "Bot Token + Channel ID が必要",
            "use_case": "個人利用・海外展開",
            "popularity": "⭐⭐⭐"
        },
        "teams": {
            "name": "Microsoft Teams",
            "cost": "無料",
            "setup": "Webhook URL が必要",
            "use_case": "企業利用（Office365環境）",
            "popularity": "⭐⭐⭐⭐"
        },
        "line": {
            "name": "LINE",
            "cost": "月1000通まで無料、以降従量課金",
            "setup": "API Token が必要",
            "use_case": "日本の個人ユーザー",
            "popularity": "⭐⭐⭐⭐⭐（日本）",
            "warning": "⚠️ コストがかかる可能性があります"
        },
        "sms": {
            "name": "SMS",
            "cost": "約5-10円/通",
            "setup": "SMS プロバイダー（Twilio等）の設定が必要",
            "use_case": "緊急リマインダー",
            "popularity": "⭐⭐",
            "warning": "⚠️ 送信ごとにコストがかかります"
        }
    }
    
    return {
        "success": True,
        "channels": channels,
        "recommendations": {
            "企業利用": ["slack", "teams"],
            "個人利用": ["discord", "telegram"],
            "日本特化": ["line"],
            "無料重視": ["slack", "discord", "telegram", "teams"],
            "確実な到達": ["sms", "line"]
        }
    }

@router.get("/channels/cost-comparison")
async def get_cost_comparison() -> Dict[str, Any]:
    """
    通知方法のコスト比較を取得
    
    Returns:
        コスト比較情報
    """
    cost_data = {
        "free_options": {
            "slack": "完全無料（Webhook利用）",
            "discord": "完全無料（Webhook利用）",
            "telegram": "完全無料（Bot API利用）",
            "teams": "完全無料（Webhook利用）"
        },
        "paid_options": {
            "line": {
                "free_tier": "月1000通まで無料",
                "paid_tier": "1000通以降 従量課金",
                "estimated_cost": "月5000通なら約2000円程度"
            },
            "sms": {
                "cost_per_message": "約5-10円/通",
                "monthly_estimate_100_users": "約1500-3000円（週2回×100ユーザー）",
                "provider_options": ["Twilio", "AWS SNS", "SendGrid"]
            }
        },
        "recommendations": {
            "startup_phase": "Slack + Discord（完全無料）",
            "growth_phase": "Slack + Discord + Telegram（完全無料）",
            "enterprise": "Teams + Slack（企業環境に最適）",
            "japan_market": "LINE（コスト許容時）+ Slack",
            "high_priority": "SMS（緊急時のみ）+ メール"
        }
    }
    
    return {
        "success": True,
        "cost_comparison": cost_data,
        "user_preference_note": "LINEは月1000通まで無料なので、小規模運用なら問題なし"
    }

@router.post("/send-custom-notification")
async def send_custom_notification(
    title: str = Form(...),
    content: str = Form(...),
    user_id: str = Form(...),
    channels: List[str] = Form(...),
    action_url: Optional[str] = Form(None),
    notification_service: MultiChannelNotificationService = Depends(get_notification_service)
) -> Dict[str, Any]:
    """
    カスタム通知を複数チャンネルに送信（管理者専用）
    
    Args:
        title: 通知タイトル
        content: 通知内容
        user_id: ユーザーID
        channels: 送信チャンネルリスト
        action_url: アクションURL（オプション）
        notification_service: 通知サービス
        
    Returns:
        送信結果
    """
    try:
        # カスタム通知メッセージを作成
        message = NotificationMessage(
            title=title,
            content=content,
            user_id=user_id,
            reminder_type="custom",
            channel="multi",
            action_url=action_url
        )
        
        # 複数チャンネルに送信
        result = await notification_service.send_multi_channel(message, channels)
        
        if result.get("success"):
            logger.info(f"Custom notification sent to {result.get('successful_channels')} channels for user {user_id}")
            return {
                "success": True,
                "message": f"カスタム通知を {result.get('successful_channels')}/{result.get('total_channels')} チャンネルに送信しました",
                "detailed_results": result.get("results"),
                "summary": {
                    "total_channels": result.get("total_channels"),
                    "successful": result.get("successful_channels"),
                    "failed": result.get("total_channels", 0) - result.get("successful_channels", 0)
                }
            }
        else:
            return {
                "success": False,
                "message": "カスタム通知の送信に失敗しました",
                "error": result.get("results")
            }
            
    except Exception as e:
        logger.error(f"Error sending custom notification: {e}")
        raise HTTPException(status_code=500, detail=f"カスタム通知送信エラー: {str(e)}")

# Utility function to be called from main.py
def include_startup_event(app):
    """アプリケーション起動イベントを追加"""
    @app.on_event("startup")
    async def startup_event():
        await startup_reminder_scheduler() 