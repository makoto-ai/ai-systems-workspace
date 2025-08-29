#!/usr/bin/env python3
"""
Canary Decision Notification
カナリー判定結果通知
"""

import json
import argparse
import os
import requests
from pathlib import Path
from datetime import datetime

def create_decision_slack_message(decision: str, window_data: dict, action_url: str) -> dict:
    """判定結果Slack メッセージ作成"""
    
    metrics = window_data.get("metrics", {})
    
    if decision == "promote":
        return {
            "text": "🚀 カナリー週自動昇格完了！",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚀 Phase 3 本採用自動昇格完了！"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*7日ウィンドウ評価*: 全条件達成 ✅\n*自動アクション*: PR承認・マージ・リリースタグ作成"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*平均合格率*: {metrics.get('avg_pass_rate', 0):.1f}% ≥ 85% ✅"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Flaky率*: {metrics.get('avg_flaky_rate', 0):.1f}% < 5% ✅"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*新規失敗率*: {metrics.get('avg_new_fail_ratio', 0):.1f}% ≤ 60% ✅"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*リリース*: v3.0-threshold-0.7 🎉"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*🎯 次のマイルストーン*:\n• Phase 4準備 (しきい値0.85)\n• Shadow評価継続\n• 完全自動化運用"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📊 Dashboard"
                            },
                            "url": "http://localhost:8501",
                            "style": "primary"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🔗 実行ログ"
                            },
                            "url": action_url
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🏷️ リリース"
                            },
                            "url": f"https://github.com/{os.getenv('GITHUB_REPOSITORY', 'repo')}/releases/tag/v3.0-threshold-0.7"
                        }
                    ]
                }
            ]
        }
    else:
        return {
            "text": "🐤 カナリー週継続 - 改善要求",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🐤 カナリー週継続 - 改善要求"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*7日ウィンドウ評価*: 条件未達成\n*理由*: {window_data.get('decision_reason', '不明')}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*平均合格率*: {metrics.get('avg_pass_rate', 0):.1f}%"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Flaky率*: {metrics.get('avg_flaky_rate', 0):.1f}%"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*新規失敗率*: {metrics.get('avg_new_fail_ratio', 0):.1f}%"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*次回評価*: 明日 09:10 JST"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*🎯 改善アクション*:\n• 正規化ルール強化\n• プロンプト最適化\n• 参照データ品質向上"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📊 Dashboard"
                            },
                            "url": "http://localhost:8501"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🔗 実行ログ"
                            },
                            "url": action_url
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📋 改善Issue"
                            },
                            "url": f"https://github.com/{os.getenv('GITHUB_REPOSITORY', 'repo')}/issues"
                        }
                    ]
                }
            ]
        }

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Canary Decision Notification")
    parser.add_argument("--decision", type=str, required=True, help="判定結果 (promote/continue)")
    parser.add_argument("--window", type=str, required=True, help="ウィンドウ評価結果ファイル")
    parser.add_argument("--action-url", type=str, help="GitHub Actions実行URL")
    
    args = parser.parse_args()
    
    try:
        # ウィンドウデータ読み込み
        with open(args.window, 'r', encoding='utf-8') as f:
            window_data = json.load(f)
        
        # Slack通知
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            print("⚠️ SLACK_WEBHOOK_URL が設定されていません")
            return False
        
        message = create_decision_slack_message(args.decision, window_data, args.action_url or "")
        
        response = requests.post(webhook_url, json=message, timeout=10)
        
        if response.status_code == 200:
            print("✅ カナリー判定結果Slack通知送信完了")
            
            # 通知ペイロード保存
            payload_file = Path("out/notify_payload.json")
            payload_file.parent.mkdir(parents=True, exist_ok=True)
            with open(payload_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "decision": args.decision,
                    "slack_payload": message
                }, f, ensure_ascii=False, indent=2)
            
            return True
        else:
            print(f"❌ Slack通知送信失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ カナリー判定通知エラー: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
