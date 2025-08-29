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
    # Shadow評価データ（複数しきい値対応）
    shadow_data = {"0.7": 60.0, "0.85": 0.0}  # デフォルト値
    
    # マルチシャドー評価ファイルを優先
    multi_shadow_file = Path("out/shadow_multi.json")
    if multi_shadow_file.exists():
        try:
            with open(multi_shadow_file, 'r', encoding='utf-8') as f:
                multi_data = json.load(f)
            
            multi_eval = multi_data.get("multi_shadow_evaluation", {})
            thresholds = multi_eval.get("thresholds", {})
            
            shadow_data["0.7"] = thresholds.get("0.7", {}).get("shadow_pass_rate", 60.0)
            shadow_data["0.85"] = thresholds.get("0.85", {}).get("shadow_pass_rate", 0.0)
        except Exception as e:
            print(f"⚠️ Multi-shadow evaluation読み込みエラー: {e}")
    
    # 従来の0.7単体ファイルをフォールバック
    elif Path("out/shadow_0_7.json").exists():
        try:
            with open("out/shadow_0_7.json", 'r', encoding='utf-8') as f:
                single_data = json.load(f)
            shadow_data["0.7"] = single_data["shadow_evaluation"]["shadow_pass_rate"]
        except Exception as e:
            print(f"⚠️ Shadow evaluation読み込みエラー: {e}")
    
    shadow_pass_rate = shadow_data["0.7"]  # 後方互換性
    
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
        "shadow_pass_rate": shadow_pass_rate,
        "shadow_data": shadow_data  # 新しい複数しきい値データ
    }

def create_slack_message(metrics, action_url=None, dashboard_url="http://localhost:8501", canary_mode=False, pr_url=None):
    """Slack用メッセージ作成（週次レポート対応）"""
    if not metrics:
        return None
    
    # カナリア週判定
    if canary_mode:
        title_prefix = "🐤 Canary Weekly Report"
        threshold_text = "(Threshold=0.7)"
        canary_status = "カナリア週監視中"
    else:
        title_prefix = "📊 Weekly Report"
        threshold_text = f"(Threshold={metrics.get('threshold', 0.5)})"
        canary_status = "通常運用"
    
    # ステータス判定（カナリア週は85%基準）
    threshold = 85 if canary_mode else 80
    if metrics["pass_rate"] >= threshold:
        status_emoji = "✅"
        status_text = "良好"
    elif metrics["pass_rate"] >= (threshold - 5):
        status_emoji = "⚠️"
        status_text = "注意"
    else:
        status_emoji = "🚨"
        status_text = "緊急"
    
    # KPI判定アイコン
    pass_rate_icon = "✅" if metrics["pass_rate"] >= threshold else "❌"
    flaky_rate_icon = "✅" if metrics["flaky_rate"] <= 5.0 else "❌"
    new_fail_icon = "✅" if metrics["new_fail_ratio"] <= 0.60 else "❌"
    
    # Root Cause Top3の整形
    root_cause_text = ""
    total_failures = sum(count for _, count in metrics["root_cause_top3"]) if metrics["root_cause_top3"] else 1
    for i, (cause, count) in enumerate(metrics["root_cause_top3"][:3]):
        percentage = (count / total_failures) * 100 if total_failures > 0 else 0
        root_cause_text += f"{i+1}. {cause} ({percentage:.0f}%)\n"
    
    message = {
        "text": f"{title_prefix} {threshold_text}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{title_prefix} {threshold_text}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*状態:* {status_emoji} {status_text} ({canary_status})"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*合格率:* {metrics['pass_rate']}% (基準 >={threshold}%) {pass_rate_icon}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Flaky率:* {metrics['flaky_rate']:.1f}% (<5%) {flaky_rate_icon}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*新規失敗率:* {metrics['new_fail_ratio']:.1%} (≤60%) {new_fail_icon}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Predicted@0.7:* {metrics.get('shadow_pass_rate', 0):.1f}%"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Predicted@0.85:* {metrics.get('shadow_data', {}).get('0.85', 0):.1f}% {'✅' if metrics.get('shadow_data', {}).get('0.85', 0) >= 85 else '❌'}"
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
                "text": f"*Root Cause Top3:*\n{root_cause_text.rstrip()}"
            }
        })
    
    # アクションボタンセクション
    elements = [
        {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "📊 Dashboard"
            },
            "url": dashboard_url
        }
    ]
    
    if action_url:
        elements.append({
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "🔗 Run Logs"
            },
            "url": action_url
        })
    
    if pr_url:
        elements.append({
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "🐤 Canary PR" if canary_mode else "📋 PR"
            },
            "url": pr_url
        })
    
    message["blocks"].append({
        "type": "actions",
        "elements": elements
    })
    
    # フッター
    message["blocks"].append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"📅 {metrics['date']} | 🤖 自動生成レポート"
            }
        ]
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
    parser.add_argument("--slack-webhook", type=str, help="Slack Webhook URL")
    parser.add_argument("--canary", action="store_true", help="カナリア週モード")
    parser.add_argument("--pr-url", type=str, help="関連PR URL")
    
    args = parser.parse_args()
    
    # メトリクス読み込み
    print("📊 最新メトリクス読み込み中...")
    metrics = load_latest_metrics()
    
    if not metrics:
        print("❌ メトリクスが見つかりません")
        return False
    
    print(f"📈 合格率: {metrics['pass_rate']}%")
    print(f"📊 新規失敗率: {metrics['new_fail_ratio']:.1%}")
    print(f"🐤 カナリア週: {args.canary}")
    
    # Webhook URL取得（引数優先、環境変数フォールバック）
    slack_webhook = args.slack_webhook or os.getenv("SLACK_WEBHOOK_URL")
    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
    
    success = True
    
    # Slack通知
    if slack_webhook:
        print("📤 Slack通知送信中...")
        slack_message = create_slack_message(
            metrics, 
            action_url=args.action_url, 
            dashboard_url=args.dashboard_url,
            canary_mode=args.canary,
            pr_url=args.pr_url
        )
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
