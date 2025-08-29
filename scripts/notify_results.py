#!/usr/bin/env python3
"""
Golden Test Results Notification System
Slack/Discord統合通知システム
"""

import json
import os
import requests
from datetime import datetime
from pathlib import Path
import argparse

def load_latest_metrics():
    """最新のメトリクスを読み込み"""
    # 週次データから最新情報を取得
    log_file = Path("tests/golden/observation_log.md")
    if not log_file.exists():
        return None
    
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 最新の週次観測を抽出
    import re
    pattern = r'## (\d{4}-\d{2}-\d{2}) - 週次観測.*?合格率.*?(\d+)/(\d+) \((\d+)%\)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    if not matches:
        return None
    
    latest_match = matches[-1]
    date_str, passed, total, percentage = latest_match
    
    # Root Cause Top3とfreshness情報を抽出
    section_pattern = rf'## {re.escape(date_str)} - 週次観測(.*?)(?=## |\Z)'
    section_match = re.search(section_pattern, content, re.DOTALL)
    
    root_causes = {}
    new_failures = 0
    total_failures = 0
    
    if section_match:
        section_content = section_match.group(1)
        failure_matches = re.findall(r'- \*\*([^*]+)\*\*: `root_cause:([^`]+)`(?:\s*\|\s*`freshness:([^`]+)`)?', section_content)
        for case_id, root_cause, freshness in failure_matches:
            total_failures += 1
            root_causes[root_cause] = root_causes.get(root_cause, 0) + 1
            if freshness == "NEW":
                new_failures += 1
    
    # Shadow evaluation結果
    shadow_pass_rate = 0.0
    shadow_file = Path("out/shadow_0_7.json")
    if shadow_file.exists():
        try:
            with open(shadow_file, 'r', encoding='utf-8') as f:
                shadow_data = json.load(f)
            shadow_pass_rate = shadow_data["shadow_evaluation"]["shadow_pass_rate"]
        except:
            pass
    
    return {
        "date": date_str,
        "pass_rate": int(percentage),
        "passed": int(passed),
        "total": int(total),
        "total_failures": total_failures,
        "new_failures": new_failures,
        "new_fail_ratio": (new_failures / max(total_failures, 1)) if total_failures > 0 else 0.0,
        "flaky_rate": 0.0,  # 簡易計算（実際はログから算出）
        "root_cause_top3": sorted(root_causes.items(), key=lambda x: x[1], reverse=True)[:3],
        "shadow_pass_rate": shadow_pass_rate
    }

def create_slack_message(metrics, action_url=None, dashboard_url="http://localhost:8501"):
    """Slack用メッセージ作成"""
    if not metrics:
        return None
    
    # ステータス絵文字
    if metrics["pass_rate"] >= 90:
        status_emoji = "✅"
        status_text = "良好"
    elif metrics["pass_rate"] >= 80:
        status_emoji = "⚠️"
        status_text = "注意"
    else:
        status_emoji = "🚨"
        status_text = "緊急"
    
    # Root Cause Top3
    root_cause_text = ""
    for i, (cause, count) in enumerate(metrics["root_cause_top3"]):
        root_cause_text += f"{i+1}. {cause}: {count}件\n"
    
    message = {
        "text": f"{status_emoji} Golden Test 週次結果 ({metrics['date']})",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{status_emoji} Golden Test 週次結果"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*日付:* {metrics['date']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*状態:* {status_text}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*合格率:* {metrics['pass_rate']}% ({metrics['passed']}/{metrics['total']})"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*新規失敗率:* {metrics['new_fail_ratio']:.1%}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Flaky率:* {metrics['flaky_rate']:.1%}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Predicted@0.7:* {metrics['shadow_pass_rate']:.1f}%"
                    }
                ]
            }
        ]
    }
    
    # Root Cause Top3セクション
    if root_cause_text:
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Root Cause Top3:*\n{root_cause_text}"
            }
        })
    
    # リンクセクション
    links_text = f"• <{dashboard_url}|📊 Golden KPI Dashboard>"
    if action_url:
        links_text += f"\n• <{action_url}|🔗 実行ログ>"
    
    message["blocks"].append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": links_text
        }
    })
    
    return message

def create_discord_message(metrics, action_url=None, dashboard_url="http://localhost:8501"):
    """Discord用メッセージ作成"""
    if not metrics:
        return None
    
    # ステータス色
    if metrics["pass_rate"] >= 90:
        color = 0x00ff00  # 緑
    elif metrics["pass_rate"] >= 80:
        color = 0xffaa00  # オレンジ
    else:
        color = 0xff0000  # 赤
    
    # Root Cause Top3
    root_cause_text = ""
    for i, (cause, count) in enumerate(metrics["root_cause_top3"]):
        root_cause_text += f"{i+1}. **{cause}**: {count}件\n"
    
    embed = {
        "title": f"📊 Golden Test 週次結果 ({metrics['date']})",
        "color": color,
        "fields": [
            {
                "name": "合格率",
                "value": f"{metrics['pass_rate']}% ({metrics['passed']}/{metrics['total']})",
                "inline": True
            },
            {
                "name": "新規失敗率",
                "value": f"{metrics['new_fail_ratio']:.1%}",
                "inline": True
            },
            {
                "name": "Flaky率",
                "value": f"{metrics['flaky_rate']:.1%}",
                "inline": True
            },
            {
                "name": "Predicted@0.7",
                "value": f"{metrics['shadow_pass_rate']:.1f}%",
                "inline": True
            }
        ],
        "timestamp": datetime.now().isoformat()
    }
    
    # Root Cause Top3
    if root_cause_text:
        embed["fields"].append({
            "name": "Root Cause Top3",
            "value": root_cause_text,
            "inline": False
        })
    
    # リンク
    links_text = f"[📊 Dashboard]({dashboard_url})"
    if action_url:
        links_text += f" | [🔗 実行ログ]({action_url})"
    
    embed["fields"].append({
        "name": "リンク",
        "value": links_text,
        "inline": False
    })
    
    return {"embeds": [embed]}

def send_slack_notification(webhook_url, message):
    """Slack通知送信"""
    try:
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        print("✅ Slack通知送信完了")
        return True
    except Exception as e:
        print(f"❌ Slack通知送信失敗: {e}")
        return False

def send_discord_notification(webhook_url, message):
    """Discord通知送信"""
    try:
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        print("✅ Discord通知送信完了")
        return True
    except Exception as e:
        print(f"❌ Discord通知送信失敗: {e}")
        return False

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Golden Test Results Notification")
    parser.add_argument("--action-url", type=str, help="GitHub Actions実行URL")
    parser.add_argument("--dashboard-url", type=str, default="http://localhost:8501",
                       help="ダッシュボードURL")
    
    args = parser.parse_args()
    
    # メトリクス読み込み
    print("📊 最新メトリクス読み込み中...")
    metrics = load_latest_metrics()
    
    if not metrics:
        print("❌ メトリクスが見つかりません")
        return False
    
    print(f"📈 合格率: {metrics['pass_rate']}%")
    print(f"📊 新規失敗率: {metrics['new_fail_ratio']:.1%}")
    
    # Webhook URL取得
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
    
    success = True
    
    # Slack通知
    if slack_webhook:
        print("📤 Slack通知送信中...")
        slack_message = create_slack_message(metrics, args.action_url, args.dashboard_url)
        if slack_message:
            success &= send_slack_notification(slack_webhook, slack_message)
    else:
        print("⚠️ SLACK_WEBHOOK_URL が設定されていません")
    
    # Discord通知
    if discord_webhook:
        print("📤 Discord通知送信中...")
        discord_message = create_discord_message(metrics, args.action_url, args.dashboard_url)
        if discord_message:
            success &= send_discord_notification(discord_webhook, discord_message)
    else:
        print("⚠️ DISCORD_WEBHOOK_URL が設定されていません")
    
    if not slack_webhook and not discord_webhook:
        print("⚠️ 通知先が設定されていません（SLACK_WEBHOOK_URL または DISCORD_WEBHOOK_URL を設定してください）")
        return False
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
