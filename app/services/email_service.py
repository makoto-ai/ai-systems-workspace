"""
Email Service for Roleplay Reminder System
営業ロールプレイリマインダーメール配信サービス
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path
import jinja2
from jinja2 import Template

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """メール設定"""

    smtp_server: str
    smtp_port: int
    username: str
    password: str
    from_email: str
    from_name: str = "営業ロールプレイシステム"
    use_tls: bool = True


@dataclass
class ReminderEmail:
    """リマインダーメール情報"""

    user_email: str
    user_name: str
    reminder_type: str  # "3days", "1day", "same_day"
    last_roleplay_date: Optional[str]
    streak_count: int
    improvement_points: List[str]
    personalized_message: str


class EmailService:
    """メール配信サービス"""

    def __init__(self, config_path: str = "config/email_config.json"):
        """
        Initialize email service

        Args:
            config_path: Path to email configuration file
        """
        self.config_path = Path(config_path)
        self.config: Optional[EmailConfig] = None
        self.templates_path = Path("app/templates/email")

        # Create directories
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.templates_path.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_path)),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
        )

        self._load_config()
        self._initialize_templates()

        logger.info("Email service initialized")

    def _load_config(self) -> None:
        """設定ファイルを読み込み"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                self.config = EmailConfig(**config_data)
                logger.info("Email configuration loaded")
            else:
                self._create_default_config()
        except Exception as e:
            logger.error(f"Failed to load email config: {e}")
            self._create_default_config()

    def _create_default_config(self) -> None:
        """デフォルト設定を作成"""
        default_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "",  # 設定が必要
            "password": "",  # 設定が必要
            "from_email": "",
            "from_name": "営業ロールプレイシステム",
            "use_tls": True,
        }

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            logger.info(f"Default email config created at {self.config_path}")
            logger.warning(
                "Please configure email settings in config/email_config.json"
            )
        except Exception as e:
            logger.error(f"Failed to create default config: {e}")

    def _initialize_templates(self) -> None:
        """メールテンプレートを初期化"""
        templates = {
            "3days_reminder.html": self._get_3days_template(),
            "1day_reminder.html": self._get_1day_template(),
            "same_day_reminder.html": self._get_same_day_template(),
            "base.html": self._get_base_template(),
        }

        for template_name, content in templates.items():
            template_path = self.templates_path / template_name
            if not template_path.exists():
                try:
                    with open(template_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    logger.debug(f"Created template: {template_name}")
                except Exception as e:
                    logger.error(f"Failed to create template {template_name}: {e}")

    def _get_base_template(self) -> str:
        """ベーステンプレート"""
        return """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}営業ロールプレイシステム{% endblock %}</title>
    <style>
        body { font-family: 'Hiragino Kaku Gothic Pro', 'ヒラギノ角ゴ Pro W3', Meiryo, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: white; padding: 30px; border: 1px solid #ddd; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; color: #666; }
        .btn { display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }
        .stats { background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .highlight { color: #667eea; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{% block header %}🎯 営業ロールプレイシステム{% endblock %}</h1>
        </div>
        <div class="content">
            {% block content %}{% endblock %}
        </div>
        <div class="footer">
            <p>このメールは営業ロールプレイシステムから自動送信されています。</p>
            <p>継続は力なり - あなたの営業スキル向上を応援します！</p>
        </div>
    </div>
</body>
</html>"""

    def _get_3days_template(self) -> str:
        """3日前リマインダーテンプレート"""
        return """{% extends "base.html" %}

{% block title %}今週のロールプレイ予定について{% endblock %}

{% block header %}📅 今週のロールプレイはいかがですか？{% endblock %}

{% block content %}
<h2>{{ user_name }}さん、お疲れ様です！</h2>

<p>今週も3日が経過しました。営業スキル向上のためのロールプレイの進捗はいかがでしょうか？</p>

{% if last_roleplay_date %}
<div class="stats">
    <h3>📊 あなたの実績</h3>
    <p><strong>最後のロールプレイ：</strong> {{ last_roleplay_date }}</p>
    <p><strong>連続実行記録：</strong> {{ streak_count }}回</p>
</div>
{% endif %}

{% if improvement_points %}
<div class="stats">
    <h3>🎯 前回の改善ポイント</h3>
    <ul>
    {% for point in improvement_points %}
        <li>{{ point }}</li>
    {% endfor %}
    </ul>
</div>
{% endif %}

<p class="highlight">{{ personalized_message }}</p>

<p>継続的な練習が営業成果につながります。今週もぜひロールプレイを活用してください！</p>

<a href="#" class="btn">🚀 今すぐロールプレイを開始</a>

<h3>💡 今週のおすすめ練習シーン</h3>
<ul>
    <li>新規開拓のアポイント獲得</li>
    <li>価格交渉での説得力向上</li>
    <li>競合他社との差別化説明</li>
</ul>
{% endblock %}"""

    def _get_1day_template(self) -> str:
        """前日リマインダーテンプレート"""
        return """{% extends "base.html" %}

{% block title %}明日がロールプレイ期限です！{% endblock %}

{% block header %}⏰ 明日でロールプレイ期限です！{% endblock %}

{% block content %}
<h2>{{ user_name }}さん、明日が期限です！</h2>

<p><strong>重要：</strong>明日でロールプレイの実行期限となります。営業スキル向上の機会を逃さないようにしましょう！</p>

{% if last_roleplay_date %}
<div class="stats">
    <h3>📊 現在の状況</h3>
    <p><strong>最後のロールプレイ：</strong> {{ last_roleplay_date }}</p>
    <p><strong>連続実行記録：</strong> {{ streak_count }}回</p>
</div>
{% endif %}

<p class="highlight">{{ personalized_message }}</p>

<div class="stats">
    <h3>⚡ 15分で完了する効率的な練習法</h3>
    <ol>
        <li><strong>5分：</strong> 状況設定とゴール確認</li>
        <li><strong>7分：</strong> ロールプレイ実行</li>
        <li><strong>3分：</strong> フィードバック確認と改善点記録</li>
    </ol>
</div>

<a href="#" class="btn">🎯 今すぐ15分練習を開始</a>

<p><small>※ 短時間でも継続することで、確実にスキルは向上します！</small></p>
{% endblock %}"""

    def _get_same_day_template(self) -> str:
        """当日リマインダーテンプレート"""
        return """{% extends "base.html" %}

{% block title %}本日中にロールプレイを完了しましょう{% endblock %}

{% block header %}🔥 本日が最終日です！{% endblock %}

{% block content %}
<h2>{{ user_name }}さん、今日が最後のチャンスです！</h2>

<p><strong>緊急：</strong>本日中にロールプレイを完了してください。継続的な成長のために、今すぐ行動しましょう！</p>

{% if last_roleplay_date %}
<div class="stats">
    <h3>📊 あなたの記録</h3>
    <p><strong>最後のロールプレイ：</strong> {{ last_roleplay_date }}</p>
    <p><strong>連続実行記録：</strong> {{ streak_count }}回 <span style="color: #e74c3c;">（途切れる危険！）</span></p>
</div>
{% endif %}

<p class="highlight">{{ personalized_message }}</p>

<div class="stats" style="border-left: 4px solid #e74c3c;">
    <h3>🚨 今すぐできる最短練習（10分）</h3>
    <p><strong>クイック練習モード：</strong></p>
    <ul>
        <li>既存顧客への追加提案（3分設定 + 5分実行 + 2分振り返り）</li>
        <li>電話アポイントメント獲得練習</li>
        <li>クロージング場面の練習</li>
    </ul>
</div>

<a href="#" class="btn" style="background: #e74c3c; font-size: 18px; padding: 15px 30px;">🔥 緊急練習スタート</a>

<p style="color: #e74c3c;"><strong>注意：</strong>今日を逃すと連続記録がリセットされます。たった10分で継続できます！</p>
{% endblock %}"""

    async def send_reminder_email(self, reminder: ReminderEmail) -> bool:
        """リマインダーメールを送信"""
        if not self.config or not self.config.username or not self.config.password:
            logger.warning("Email configuration not complete. Cannot send emails.")
            return False

        try:
            # テンプレート選択
            template_name = f"{reminder.reminder_type}_reminder.html"
            template = self.jinja_env.get_template(template_name)

            # HTML コンテンツ生成
            html_content = template.render(
                user_name=reminder.user_name,
                last_roleplay_date=reminder.last_roleplay_date,
                streak_count=reminder.streak_count,
                improvement_points=reminder.improvement_points,
                personalized_message=reminder.personalized_message,
            )

            # メッセージ作成
            message = MIMEMultipart("alternative")
            message["Subject"] = self._get_subject(reminder.reminder_type)
            message["From"] = f"{self.config.from_name} <{self.config.from_email}>"
            message["To"] = reminder.user_email

            # HTML パート追加
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)

            # SMTP送信
            return await self._send_email(message, reminder.user_email)

        except Exception as e:
            logger.error(f"Failed to send reminder email to {reminder.user_email}: {e}")
            return False

    def _get_subject(self, reminder_type: str) -> str:
        """件名を取得"""
        subjects = {
            "3days": "📅 今週のロールプレイはいかがですか？",
            "1day": "⏰ 明日がロールプレイ期限です！",
            "same_day": "🔥 本日中にロールプレイを完了しましょう",
        }
        return subjects.get(reminder_type, "営業ロールプレイリマインダー")

    async def _send_email(self, message: MIMEMultipart, to_email: str) -> bool:
        """実際のメール送信"""
        try:
            # SMTP接続
            context = ssl.create_default_context()

            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls(context=context)

                server.login(self.config.username, self.config.password)

                # メール送信
                text = message.as_string()
                server.sendmail(self.config.from_email, to_email, text)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"SMTP send error to {to_email}: {e}")
            return False

    async def test_email_connection(self) -> Dict[str, Any]:
        """メール接続をテスト"""
        if not self.config:
            return {"success": False, "error": "Email configuration not loaded"}

        if not self.config.username or not self.config.password:
            return {"success": False, "error": "Email credentials not configured"}

        try:
            context = ssl.create_default_context()

            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls(context=context)

                server.login(self.config.username, self.config.password)

            return {"success": True, "message": "Email connection successful"}

        except Exception as e:
            return {"success": False, "error": str(e)}


# Dependency injection
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
