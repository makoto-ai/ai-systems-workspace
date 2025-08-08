"""
Multi-Channel Notification Service for Voice Roleplay System
マルチチャンネル通知サービス（メール以外の通知方法）
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import aiohttp
import requests
from enum import Enum

logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    """通知チャンネル種別"""
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    TEAMS = "teams"
    WEB_PUSH = "web_push"
    LINE = "line"
    SMS = "sms"

@dataclass
class NotificationConfig:
    """通知設定"""
    channel: str
    enabled: bool = True
    webhook_url: Optional[str] = None
    api_token: Optional[str] = None
    bot_token: Optional[str] = None
    channel_id: Optional[str] = None
    phone_number: Optional[str] = None
    user_id: Optional[str] = None
    additional_config: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_config is None:
            self.additional_config = {}

@dataclass
class NotificationMessage:
    """通知メッセージ"""
    title: str
    content: str
    user_id: str
    reminder_type: str
    channel: str
    priority: str = "normal"  # low, normal, high, urgent
    action_url: Optional[str] = None
    image_url: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class MultiChannelNotificationService:
    """マルチチャンネル通知サービス"""
    
    def __init__(self, config_path: str = "config/notification_config.json"):
        """
        Initialize multi-channel notification service
        
        Args:
            config_path: Path to notification configuration
        """
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.channels_config = self._load_config()
        
        # Initialize HTTP session
        self.session = None
        
        logger.info("Multi-channel notification service initialized")
    
    def _load_config(self) -> Dict[str, NotificationConfig]:
        """設定を読み込み"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                channels = {}
                for channel_name, data in config_data.items():
                    channels[channel_name] = NotificationConfig(**data)
                return channels
            else:
                return self._create_default_config()
        except Exception as e:
            logger.error(f"Failed to load notification config: {e}")
            return {}
    
    def _create_default_config(self) -> Dict[str, NotificationConfig]:
        """デフォルト設定を作成"""
        default_configs = {
            "slack": NotificationConfig(
                channel="slack",
                enabled=False,
                webhook_url="",
                additional_config={
                    "username": "営業ロールプレイBot",
                    "emoji": ":speech_balloon:",
                    "mention_channel": False
                }
            ),
            "discord": NotificationConfig(
                channel="discord", 
                enabled=False,
                webhook_url="",
                additional_config={
                    "username": "営業ロールプレイBot",
                    "avatar_url": "",
                    "mention_everyone": False
                }
            ),
            "telegram": NotificationConfig(
                channel="telegram",
                enabled=False,
                bot_token="",
                channel_id="",
                additional_config={
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                }
            ),
            "teams": NotificationConfig(
                channel="teams",
                enabled=False,
                webhook_url="",
                additional_config={
                    "theme_color": "0076D7",
                    "summary": "営業ロールプレイリマインダー"
                }
            ),
            "line": NotificationConfig(
                channel="line",
                enabled=False,
                api_token="",
                additional_config={
                    "channel_access_token": "",
                    "cost_warning": "LINE API は従量課金です。月1000通まで無料、以降は課金されます。"
                }
            ),
            "sms": NotificationConfig(
                channel="sms",
                enabled=False,
                api_token="",
                additional_config={
                    "provider": "twilio",  # twilio, aws_sns, etc.
                    "from_number": "",
                    "cost_per_message": "約5-10円/通"
                }
            )
        }
        
        try:
            # 設定ファイルに保存
            config_data = {}
            for channel, config in default_configs.items():
                config_data[channel] = asdict(config)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Default notification config created at {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to create default config: {e}")
        
        return default_configs
    
    async def _ensure_session(self):
        """HTTP セッションを確保"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def send_notification(self, message: NotificationMessage) -> Dict[str, Any]:
        """
        通知を送信
        
        Args:
            message: 通知メッセージ
            
        Returns:
            送信結果
        """
        channel_config = self.channels_config.get(message.channel)
        if not channel_config or not channel_config.enabled:
            return {
                "success": False,
                "error": f"Channel {message.channel} is not enabled"
            }
        
        try:
            await self._ensure_session()
            
            # チャンネル別の送信処理
            if message.channel == "slack":
                return await self._send_slack(message, channel_config)
            elif message.channel == "discord":
                return await self._send_discord(message, channel_config)
            elif message.channel == "telegram":
                return await self._send_telegram(message, channel_config)
            elif message.channel == "teams":
                return await self._send_teams(message, channel_config)
            elif message.channel == "line":
                return await self._send_line(message, channel_config)
            elif message.channel == "sms":
                return await self._send_sms(message, channel_config)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported channel: {message.channel}"
                }
                
        except Exception as e:
            logger.error(f"Failed to send notification via {message.channel}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_slack(self, message: NotificationMessage, config: NotificationConfig) -> Dict[str, Any]:
        """Slack通知送信"""
        if not config.webhook_url:
            return {"success": False, "error": "Slack webhook URL not configured"}
        
        # 絵文字マッピング
        emoji_map = {
            "3days": ":calendar:",
            "1day": ":warning:",
            "same_day": ":rotating_light:"
        }
        
        # Slack メッセージフォーマット
        slack_message = {
            "username": config.additional_config.get("username", "営業ロールプレイBot"),
            "icon_emoji": config.additional_config.get("emoji", ":speech_balloon:"),
            "attachments": [
                {
                    "color": self._get_color_for_reminder(message.reminder_type),
                    "title": message.title,
                    "text": message.content,
                    "footer": "営業ロールプレイシステム",
                    "ts": int(datetime.now().timestamp()),
                    "fields": [
                        {
                            "title": "ユーザー",
                            "value": message.user_id,
                            "short": True
                        },
                        {
                            "title": "リマインダータイプ",
                            "value": message.reminder_type,
                            "short": True
                        }
                    ]
                }
            ]
        }
        
        if message.action_url:
            slack_message["attachments"][0]["actions"] = [
                {
                    "type": "button",
                    "text": "ロールプレイ開始",
                    "url": message.action_url,
                    "style": "primary"
                }
            ]
        
        try:
            async with self.session.post(config.webhook_url, json=slack_message) as response:
                if response.status == 200:
                    return {"success": True, "channel": "slack"}
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"Slack API error: {error_text}"}
        except Exception as e:
            return {"success": False, "error": f"Slack send error: {str(e)}"}
    
    async def _send_discord(self, message: NotificationMessage, config: NotificationConfig) -> Dict[str, Any]:
        """Discord通知送信"""
        if not config.webhook_url:
            return {"success": False, "error": "Discord webhook URL not configured"}
        
        # Discord Embed フォーマット
        discord_message = {
            "username": config.additional_config.get("username", "営業ロールプレイBot"),
            "embeds": [
                {
                    "title": message.title,
                    "description": message.content,
                    "color": int(self._get_color_for_reminder(message.reminder_type, format="int")),
                    "timestamp": datetime.now().isoformat(),
                    "footer": {
                        "text": "営業ロールプレイシステム"
                    },
                    "fields": [
                        {
                            "name": "ユーザー",
                            "value": message.user_id,
                            "inline": True
                        },
                        {
                            "name": "タイプ",
                            "value": message.reminder_type,
                            "inline": True
                        }
                    ]
                }
            ]
        }
        
        if message.action_url:
            discord_message["embeds"][0]["url"] = message.action_url
        
        if config.additional_config.get("avatar_url"):
            discord_message["avatar_url"] = config.additional_config["avatar_url"]
        
        try:
            async with self.session.post(config.webhook_url, json=discord_message) as response:
                if response.status == 204:  # Discord returns 204 on success
                    return {"success": True, "channel": "discord"}
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"Discord API error: {error_text}"}
        except Exception as e:
            return {"success": False, "error": f"Discord send error: {str(e)}"}
    
    async def _send_telegram(self, message: NotificationMessage, config: NotificationConfig) -> Dict[str, Any]:
        """Telegram通知送信"""
        if not config.bot_token or not config.channel_id:
            return {"success": False, "error": "Telegram bot token or channel ID not configured"}
        
        # Telegramメッセージフォーマット（HTML）
        telegram_message = f"""
<b>{message.title}</b>

{message.content}

👤 ユーザー: {message.user_id}
📋 タイプ: {message.reminder_type}
        """.strip()
        
        # Telegram Bot API URL
        url = f"https://api.telegram.org/bot{config.bot_token}/sendMessage"
        
        payload = {
            "chat_id": config.channel_id,
            "text": telegram_message,
            "parse_mode": config.additional_config.get("parse_mode", "HTML"),
            "disable_web_page_preview": config.additional_config.get("disable_web_page_preview", True)
        }
        
        # インラインキーボード（アクションボタン）
        if message.action_url:
            payload["reply_markup"] = {
                "inline_keyboard": [[
                    {
                        "text": "🚀 ロールプレイ開始",
                        "url": message.action_url
                    }
                ]]
            }
        
        try:
            async with self.session.post(url, json=payload) as response:
                result = await response.json()
                if result.get("ok"):
                    return {"success": True, "channel": "telegram", "message_id": result["result"]["message_id"]}
                else:
                    return {"success": False, "error": f"Telegram API error: {result.get('description')}"}
        except Exception as e:
            return {"success": False, "error": f"Telegram send error: {str(e)}"}
    
    async def _send_teams(self, message: NotificationMessage, config: NotificationConfig) -> Dict[str, Any]:
        """Microsoft Teams通知送信"""
        if not config.webhook_url:
            return {"success": False, "error": "Teams webhook URL not configured"}
        
        # Teams Adaptive Card フォーマット
        teams_message = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": config.additional_config.get("theme_color", "0076D7"),
            "summary": config.additional_config.get("summary", "営業ロールプレイリマインダー"),
            "sections": [
                {
                    "activityTitle": message.title,
                    "activitySubtitle": f"ユーザー: {message.user_id}",
                    "activityImage": "https://raw.githubusercontent.com/adaptive-cards/adaptivecards.io/master/content/icons/teams.png",
                    "text": message.content,
                    "facts": [
                        {
                            "name": "リマインダータイプ",
                            "value": message.reminder_type
                        },
                        {
                            "name": "送信時刻",
                            "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                    ]
                }
            ]
        }
        
        if message.action_url:
            teams_message["potentialAction"] = [
                {
                    "@type": "OpenUri",
                    "name": "ロールプレイ開始",
                    "targets": [
                        {
                            "os": "default",
                            "uri": message.action_url
                        }
                    ]
                }
            ]
        
        try:
            async with self.session.post(config.webhook_url, json=teams_message) as response:
                if response.status == 200:
                    return {"success": True, "channel": "teams"}
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"Teams API error: {error_text}"}
        except Exception as e:
            return {"success": False, "error": f"Teams send error: {str(e)}"}
    
    async def _send_line(self, message: NotificationMessage, config: NotificationConfig) -> Dict[str, Any]:
        """LINE通知送信（有料）"""
        if not config.api_token:
            return {"success": False, "error": "LINE API token not configured"}
        
        # コスト警告ログ
        logger.warning("LINE API は従量課金です。月1000通まで無料、以降は課金されます。")
        
        # LINE Messaging API フォーマット
        url = "https://api.line.me/v2/bot/message/broadcast"
        headers = {
            "Authorization": f"Bearer {config.api_token}",
            "Content-Type": "application/json"
        }
        
        line_message = {
            "messages": [
                {
                    "type": "text",
                    "text": f"{message.title}\n\n{message.content}\n\n👤 {message.user_id}"
                }
            ]
        }
        
        # フレックスメッセージ（リッチな表示）
        if message.action_url:
            line_message["messages"] = [
                {
                    "type": "flex",
                    "altText": message.title,
                    "contents": {
                        "type": "bubble",
                        "hero": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": message.title,
                                    "weight": "bold",
                                    "size": "xl",
                                    "color": "#0076D7"
                                }
                            ]
                        },
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": message.content,
                                    "wrap": True
                                }
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "uri",
                                        "label": "ロールプレイ開始",
                                        "uri": message.action_url
                                    },
                                    "style": "primary"
                                }
                            ]
                        }
                    }
                }
            ]
        
        try:
            async with self.session.post(url, json=line_message, headers=headers) as response:
                if response.status == 200:
                    return {"success": True, "channel": "line", "cost_incurred": True}
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"LINE API error: {error_text}"}
        except Exception as e:
            return {"success": False, "error": f"LINE send error: {str(e)}"}
    
    async def _send_sms(self, message: NotificationMessage, config: NotificationConfig) -> Dict[str, Any]:
        """SMS通知送信（有料）"""
        if not config.api_token or not config.phone_number:
            return {"success": False, "error": "SMS API token or phone number not configured"}
        
        # コスト警告ログ
        logger.warning(f"SMS API は従量課金です。{config.additional_config.get('cost_per_message', '約5-10円/通')}")
        
        # SMS用の短縮メッセージ
        sms_content = f"{message.title}\n\n{message.content[:100]}{'...' if len(message.content) > 100 else ''}"
        
        # プロバイダー別の実装（例：Twilio）
        if config.additional_config.get("provider") == "twilio":
            return await self._send_twilio_sms(sms_content, config)
        else:
            return {"success": False, "error": "SMS provider not configured"}
    
    async def _send_twilio_sms(self, content: str, config: NotificationConfig) -> Dict[str, Any]:
        """Twilio SMS送信"""
        # この実装は例です。実際のTwilio API設定が必要
        logger.info(f"SMS would be sent: {content[:50]}...")
        return {"success": False, "error": "Twilio SMS not implemented yet"}
    
    def _get_color_for_reminder(self, reminder_type: str, format: str = "hex") -> str:
        """リマインダータイプに応じた色を取得"""
        colors = {
            "3days": {"hex": "#36a64f", "int": 3581007},   # Green
            "1day": {"hex": "#ff9500", "int": 16749824},   # Orange  
            "same_day": {"hex": "#ff0000", "int": 16711680} # Red
        }
        
        return colors.get(reminder_type, colors["3days"])[format]
    
    async def send_multi_channel(self, message: NotificationMessage, channels: List[str]) -> Dict[str, Any]:
        """
        複数チャンネルに同時送信
        
        Args:
            message: 通知メッセージ
            channels: 送信チャンネルリスト
            
        Returns:
            チャンネル別送信結果
        """
        results = {}
        
        # 並列送信
        tasks = []
        for channel in channels:
            if channel in self.channels_config and self.channels_config[channel].enabled:
                channel_message = NotificationMessage(
                    title=message.title,
                    content=message.content,
                    user_id=message.user_id,
                    reminder_type=message.reminder_type,
                    channel=channel,
                    priority=message.priority,
                    action_url=message.action_url,
                    metadata=message.metadata
                )
                tasks.append(self._send_with_channel(channel_message))
        
        if tasks:
            send_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(send_results):
                channel = channels[i] if i < len(channels) else f"unknown_{i}"
                if isinstance(result, Exception):
                    results[channel] = {"success": False, "error": str(result)}
                else:
                    results[channel] = result
        
        return {
            "success": any(r.get("success", False) for r in results.values()),
            "results": results,
            "total_channels": len(channels),
            "successful_channels": sum(1 for r in results.values() if r.get("success", False))
        }
    
    async def _send_with_channel(self, message: NotificationMessage) -> Dict[str, Any]:
        """チャンネル付きメッセージ送信"""
        return await self.send_notification(message)
    
    async def test_channel(self, channel: str) -> Dict[str, Any]:
        """
        チャンネル接続テスト
        
        Args:
            channel: テストするチャンネル
            
        Returns:
            テスト結果
        """
        test_message = NotificationMessage(
            title="🧪 通知テスト",
            content="営業ロールプレイシステムからのテスト通知です。この通知が届けば設定成功です！",
            user_id="test_user",
            reminder_type="test",
            channel=channel
        )
        
        result = await self.send_notification(test_message)
        return {
            "channel": channel,
            "test_result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    async def close(self):
        """リソースクリーンアップ"""
        if self.session:
            await self.session.close()

# Dependency injection
_notification_service: Optional[MultiChannelNotificationService] = None

def get_notification_service() -> MultiChannelNotificationService:
    """Get notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = MultiChannelNotificationService()
    return _notification_service 