#!/usr/bin/env python3
"""
🔒 セキュリティ自動化システム - メール通知機能
GitHub Actions統合・日本語対応・完全自動化
"""

import os
import json
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
import socket


class SecurityEmailNotifier:
    def __init__(self, config_path: str = "config/security_email_config.json"):
        self.config_path = config_path
        self.email_config = self.load_or_create_config()

    def load_or_create_config(self) -> Dict:
        """設定ファイル読み込み（なければ安全なデフォルトを作成）"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ 設定ファイル読み込みエラー: {e}")

        # デフォルト設定作成
        default_config = {
            "enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "",
            "sender_password": "",
            "recipient_email": "",
            "daily_summary": True,
            "emergency_only": False,
            "test_mode": True,
            "note": "実際のメール設定に変更してから enabled を true にしてください",
        }

        # 設定ファイル作成
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)

        print(f"📧 セキュリティメール設定作成: {self.config_path}")
        return default_config

    def create_daily_summary_email(self, results: Dict) -> tuple:
        """日次セキュリティサマリーメール作成"""
        timestamp = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        hostname = socket.gethostname()

        # 総合状況判定
        total_issues = sum(
            [
                len(results.get("security_issues", [])),
                len(results.get("data_integrity_issues", [])),
                len(results.get("api_failures", [])),
                len(results.get("github_actions_failures", [])),
            ]
        )

        status_emoji = "✅" if total_issues == 0 else "⚠️" if total_issues < 5 else "🚨"
        status_text = "正常" if total_issues == 0 else f"{total_issues}件の問題"

        subject = (
            f"{status_emoji} セキュリティ自動化システム - 日次レポート ({status_text})"
        )

        body = f"""
🔒 セキュリティ自動化システム - 日次レポート
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 実行日時: {timestamp}
🖥️ システム: {hostname}
📊 総合ステータス: {status_emoji} {status_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 実行結果サマリー
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ データ整合性チェック: {results.get('data_integrity_status', 'UNKNOWN')}
   問題数: {len(results.get('data_integrity_issues', []))}件

🔌 API動作確認: {results.get('api_test_status', 'UNKNOWN')}
   失敗数: {len(results.get('api_failures', []))}件

🔒 セキュリティスキャン: {results.get('security_scan_status', 'UNKNOWN')}
   検出数: {len(results.get('security_issues', []))}件

⚙️ GitHub Actions: {results.get('github_actions_status', 'UNKNOWN')}
   エラー数: {len(results.get('github_actions_failures', []))}件

"""

        # 詳細情報追加
        if results.get("data_integrity_issues"):
            body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ データ整合性の問題
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
            for issue in results["data_integrity_issues"][:5]:  # 最大5件
                body += f"• {issue}\n"

        if results.get("api_failures"):
            body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ API動作の問題
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
            for failure in results["api_failures"][:5]:  # 最大5件
                body += f"• {failure}\n"

        if results.get("security_issues"):
            body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 セキュリティの問題
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
            for issue in results["security_issues"][:5]:  # 最大5件
                body += f"• {issue}\n"

        body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 推奨アクション
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

        if total_issues == 0:
            body += "🎉 現在、システムは正常に動作しています。"
        elif total_issues < 5:
            body += """🔧 軽微な問題が検出されました:
1. ログを確認してください
2. 必要に応じて修正を実施してください
3. 次回の自動チェックで確認されます"""
        else:
            body += """🚨 重大な問題が検出されました:
1. 至急システムを確認してください
2. セキュリティリスクの可能性があります
3. 必要に応じてシステムを停止してください"""

        body += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📧 このメールはセキュリティ自動化システムにより送信されました
⏰ 次回実行: 明日同時刻
🔧 設定変更: {self.config_path}

システム詳細: voice-roleplay-system/
GitHub Actions: .github/workflows/monitoring.yml
"""

        return subject, body

    def create_emergency_alert_email(self, alert_type: str, details: str) -> tuple:
        """緊急アラートメール作成"""
        timestamp = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        hostname = socket.gethostname()

        subject = f"🚨 緊急セキュリティアラート - {alert_type}"

        body = f"""
🚨 緊急セキュリティアラート
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 検知時刻: {timestamp}
🖥️ システム: {hostname}
⚠️ アラート種別: {alert_type}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 詳細情報
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{details}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 即座の対応が必要です
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. システムの状況を即座に確認してください
2. 必要に応じてシステムを停止してください
3. セキュリティ侵害の可能性を調査してください
4. 問題解決まで監視を強化してください

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📧 このメールは緊急アラートシステムにより送信されました
🔧 システム詳細: voice-roleplay-system/
"""

        return subject, body

    def send_email(self, subject: str, body: str) -> bool:
        """メール送信実行"""
        if not self.email_config.get("enabled", False):
            if self.email_config.get("test_mode", True):
                print(f"📧 [テストモード] メール送信: {subject}")
                print(f"📄 本文（抜粋）: {body[:200]}...")
                return True
            else:
                print("📧 メール機能は無効です")
                return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_config["sender_email"]
            msg["To"] = self.email_config["recipient_email"]
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(
                self.email_config["smtp_server"], self.email_config["smtp_port"]
            ) as server:
                server.starttls()
                server.login(
                    self.email_config["sender_email"],
                    self.email_config["sender_password"],
                )
                server.send_message(msg)

            print(f"📧 メール送信完了: {subject}")
            return True

        except Exception as e:
            print(f"❌ メール送信エラー: {e}")
            return False

    def send_daily_summary(self, results: Dict) -> bool:
        """日次サマリー送信"""
        if not self.email_config.get("daily_summary", True):
            print("📧 日次サマリーは無効です")
            return False

        subject, body = self.create_daily_summary_email(results)
        return self.send_email(subject, body)

    def send_emergency_alert(self, alert_type: str, details: str) -> bool:
        """緊急アラート送信"""
        subject, body = self.create_emergency_alert_email(alert_type, details)
        return self.send_email(subject, body)

    def test_email_system(self) -> bool:
        """メールシステムテスト"""
        test_results = {
            "data_integrity_status": "OK",
            "api_test_status": "OK",
            "security_scan_status": "OK",
            "github_actions_status": "OK",
            "data_integrity_issues": [],
            "api_failures": [],
            "security_issues": [],
            "github_actions_failures": [],
        }

        print("🧪 メールシステムテスト開始...")
        success = self.send_daily_summary(test_results)

        if success:
            print("✅ メールシステムテスト成功")
        else:
            print("❌ メールシステムテスト失敗")

        return success


def main():
    """メイン実行（テスト用）"""
    notifier = SecurityEmailNotifier()
    notifier.test_email_system()


if __name__ == "__main__":
    main()
