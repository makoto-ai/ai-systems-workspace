#!/usr/bin/env python3
"""
Consecutive Failures Safety Check
連続失敗セーフティネット
"""

import json
import argparse
import subprocess
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

def get_recent_canary_results(days: int = 3) -> List[Dict[str, Any]]:
    """直近のカナリー評価結果を取得"""
    
    results = []
    
    # GitHub Actions Artifactsから取得（簡易実装）
    # 実際の実装では GitHub API を使用
    
    # ローカルファイルから取得（フォールバック）
    canary_file = Path("out/canary_window.json")
    if canary_file.exists():
        try:
            with open(canary_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "decision": data.get("decision", "unknown"),
                "pass_rate": data.get("metrics", {}).get("avg_pass_rate", 0),
                "conditions_met": data.get("decision") == "promote"
            })
        except Exception as e:
            print(f"⚠️ カナリー結果読み込みエラー: {e}")
    
    return results

def check_consecutive_failures(threshold: int = 2) -> Dict[str, Any]:
    """連続失敗チェック"""
    
    recent_results = get_recent_canary_results()
    
    if len(recent_results) < threshold:
        return {
            "consecutive_failures": 0,
            "threshold_exceeded": False,
            "status": "insufficient_data",
            "message": f"データ不足（{len(recent_results)}件 < {threshold}件）"
        }
    
    # 連続失敗カウント
    consecutive_count = 0
    for result in recent_results:
        if not result["conditions_met"]:
            consecutive_count += 1
        else:
            break  # 成功があれば連続失敗リセット
    
    threshold_exceeded = consecutive_count >= threshold
    
    return {
        "consecutive_failures": consecutive_count,
        "threshold_exceeded": threshold_exceeded,
        "threshold": threshold,
        "recent_results": recent_results,
        "status": "escalation_required" if threshold_exceeded else "normal",
        "message": f"連続失敗{consecutive_count}回（しきい値{threshold}回）"
    }

def create_escalation_issue(check_result: Dict[str, Any]) -> bool:
    """エスカレーションIssue作成"""
    
    try:
        consecutive_count = check_result["consecutive_failures"]
        recent_results = check_result["recent_results"]
        
        # Issue本文生成
        issue_body = f"""## 🚨 カナリー週連続失敗エスカレーション

### ⚠️ 緊急対応が必要
- **連続失敗回数**: {consecutive_count}回
- **しきい値**: {check_result["threshold"]}回
- **状態**: 自動エスカレーション発動

### 📊 直近の評価結果
"""
        
        for i, result in enumerate(recent_results[:3], 1):
            status_icon = "✅" if result["conditions_met"] else "❌"
            issue_body += f"{i}. **{result['date']}**: {status_icon} {result['decision']} (合格率: {result['pass_rate']:.1f}%)\n"
        
        issue_body += f"""
### 🎯 緊急対応アクション

#### 即座対応（24時間以内）
- [ ] **ロールバック検討**: `scripts/rollback_threshold.sh --from 0.7 --to 0.5`
- [ ] **根本原因分析**: 連続失敗の共通要因特定
- [ ] **緊急改善**: 最優先で修正可能な問題の対処

#### 中期対応（1週間以内）
- [ ] **しきい値見直し**: 0.7が適切か再評価
- [ ] **評価基準調整**: 85%基準の妥当性検証
- [ ] **プロセス改善**: 自動昇格条件の見直し

#### 長期対応（2週間以内）
- [ ] **品質向上**: 正規化・プロンプト・データ品質の抜本改善
- [ ] **監視強化**: より早期の問題検知体制構築
- [ ] **運用改善**: 人手介入タイミングの最適化

### 🔍 調査ポイント
- **環境変化**: モデルAPI・インフラ・データの変更有無
- **季節要因**: 時期特有の問題（祝日・メンテナンス等）
- **累積劣化**: 小さな問題の蓄積による品質低下

### 📈 成功条件
- **即座改善**: 次回評価で条件達成
- **安定化**: 3日連続で条件達成
- **再発防止**: 同様問題の予防策実装

### 🔗 関連リンク
- [Golden KPI Dashboard](http://localhost:8501)
- [ロールバックスクリプト](./scripts/rollback_threshold.sh)
- [実行ログ]({os.getenv('GITHUB_SERVER_URL', 'https://github.com')}/{os.getenv('GITHUB_REPOSITORY', 'repo')}/actions/runs/{os.getenv('GITHUB_RUN_ID', '0')})

---
🚨 このIssueは連続失敗により自動生成されました（優先度: HIGH）
"""
        
        # Issue作成
        create_cmd = [
            "gh", "issue", "create",
            "--title", f"🚨 カナリー週連続失敗エスカレーション ({consecutive_count}回連続)",
            "--body", issue_body,
            "--label", "priority:high,canary,escalation,auto-generated"
        ]
        
        result = subprocess.run(create_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ エスカレーションIssue作成失敗: {result.stderr}")
            return False
        
        issue_url = result.stdout.strip()
        print(f"✅ エスカレーションIssue作成完了: {issue_url}")
        return True
        
    except Exception as e:
        print(f"❌ エスカレーションIssue作成エラー: {e}")
        return False

def send_escalation_slack(check_result: Dict[str, Any]) -> bool:
    """エスカレーションSlack通知"""
    
    try:
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            print("⚠️ SLACK_WEBHOOK_URL が設定されていません")
            return False
        
        consecutive_count = check_result["consecutive_failures"]
        
        message = {
            "text": f"🚨 カナリー週連続失敗エスカレーション ({consecutive_count}回連続)",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 緊急: カナリー週連続失敗 ({consecutive_count}回)"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*状態*: 🚨 エスカレーション発動\n*連続失敗*: {consecutive_count}回\n*対応*: 24時間以内の緊急対応が必要"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*緊急アクション*:\n• ロールバック検討\n• 根本原因分析\n• 緊急改善実施"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*エスカレーション先*:\n• 開発チーム\n• 品質管理責任者\n• プロダクトオーナー"
                        }
                    ]
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
                            "style": "danger"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🔄 ロールバック"
                            },
                            "url": f"{os.getenv('GITHUB_SERVER_URL', 'https://github.com')}/{os.getenv('GITHUB_REPOSITORY', 'repo')}/blob/master/scripts/rollback_threshold.sh"
                        }
                    ]
                }
            ]
        }
        
        # Slack送信
        import requests
        response = requests.post(webhook_url, json=message, timeout=10)
        
        if response.status_code == 200:
            print("✅ エスカレーションSlack通知送信完了")
            return True
        else:
            print(f"❌ エスカレーションSlack通知送信失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ エスカレーションSlack通知エラー: {e}")
        return False

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Consecutive Failures Safety Check")
    parser.add_argument("--threshold", type=int, default=2, help="連続失敗しきい値")
    parser.add_argument("--escalate-on-exceed", action="store_true", help="しきい値超過時エスカレーション")
    
    args = parser.parse_args()
    
    try:
        # 連続失敗チェック
        check_result = check_consecutive_failures(args.threshold)
        
        print(f"🛡️ セーフティネットチェック結果:")
        print(f"  連続失敗: {check_result['consecutive_failures']}回")
        print(f"  しきい値: {check_result.get('threshold', args.threshold)}回")
        print(f"  状態: {check_result['status']}")
        print(f"  メッセージ: {check_result['message']}")
        
        if check_result["threshold_exceeded"]:
            print("🚨 エスカレーション発動")
            
            if args.escalate_on_exceed:
                # エスカレーションIssue作成
                create_escalation_issue(check_result)
                
                # エスカレーションSlack通知
                send_escalation_slack(check_result)
                
                print("✅ エスカレーション処理完了")
            else:
                print("⚠️ エスカレーション処理はスキップ（--escalate-on-exceed未指定）")
            
            exit(1)  # エスカレーション状態
        else:
            print("✅ 正常範囲内")
            exit(0)
            
    except Exception as e:
        print(f"❌ セーフティネットチェックエラー: {e}")
        exit(2)

if __name__ == "__main__":
    main()
