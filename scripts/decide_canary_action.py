#!/usr/bin/env python3
"""
Canary Action Decision
カナリア週の自動判定・アクション実行
"""

import json
import argparse
import subprocess
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

def load_canary_window(window_file: str) -> Dict[str, Any]:
    """カナリーウィンドウ評価結果を読み込み"""
    
    window_path = Path(window_file)
    if not window_path.exists():
        raise FileNotFoundError(f"ウィンドウファイルが見つかりません: {window_file}")
    
    with open(window_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def approve_and_merge_pr(pr_url: str, dry_run: bool = False) -> bool:
    """PRの承認とマージ"""
    
    try:
        # PR番号を抽出
        pr_number = pr_url.split('/')[-1]
        
        print(f"🔄 PR #{pr_number} の自動承認・マージ開始")
        
        if dry_run:
            print("🧪 Dry Run: 実際のPR操作はスキップ")
            return True
        
        # PR承認
        approve_cmd = ["gh", "pr", "review", pr_number, "--approve", "--body", "🤖 カナリア週7日ウィンドウ評価により自動承認\n\n✅ 全条件達成:\n- 平均合格率 ≥ 85%\n- Flaky率 < 5%\n- 新規失敗率 ≤ 60%\n\n🚀 Phase 3本採用へ自動移行"]
        
        result = subprocess.run(approve_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ PR承認失敗: {result.stderr}")
            return False
        
        print(f"✅ PR #{pr_number} 承認完了")
        
        # PR自動マージ（squash）
        merge_cmd = ["gh", "pr", "merge", pr_number, "--squash", "--auto", "--delete-branch"]
        
        result = subprocess.run(merge_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ PR自動マージ失敗: {result.stderr}")
            return False
        
        print(f"✅ PR #{pr_number} 自動マージ完了（squash）")
        return True
        
    except Exception as e:
        print(f"❌ PR操作エラー: {e}")
        return False

def create_improvement_issue(window_data: Dict[str, Any], dry_run: bool = False) -> bool:
    """改善Issue自動作成"""
    
    try:
        metrics = window_data["metrics"]
        conditions = window_data["conditions"]
        root_cause_top3 = window_data.get("root_cause_top3", [])
        
        # Issue本文生成
        issue_body = f"""## 🐤 カナリア週継続 - 改善が必要

### 📊 7日ウィンドウ評価結果
- **判定**: カナリア週継続
- **評価期間**: {window_data['evaluation_period']['days']}日間
- **観測データ数**: {window_data['evaluation_period']['observations_count']}件

### ❌ 未達成条件
"""
        
        # 未達成条件の詳細
        if not conditions["pass_rate_ok"]:
            issue_body += f"- **合格率**: {metrics['avg_pass_rate']}% < 85% (基準未達)\n"
        if not conditions["flaky_rate_ok"]:
            issue_body += f"- **Flaky率**: {metrics['avg_flaky_rate']}% ≥ 5% (基準超過)\n"
        if not conditions["new_fail_ratio_ok"]:
            issue_body += f"- **新規失敗率**: {metrics['avg_new_fail_ratio']}% > 60% (基準超過)\n"
        if not conditions["min_pass_rate_ok"]:
            issue_body += f"- **最低合格率**: {metrics['min_pass_rate']}% < 80% (最低基準未達)\n"
        
        # Root Cause Top3
        if root_cause_top3:
            issue_body += f"\n### 🔍 Root Cause Top3\n"
            for i, (cause, count) in enumerate(root_cause_top3[:3], 1):
                issue_body += f"{i}. **{cause}**: {count}件\n"
        
        # 提案アクション
        issue_body += f"""
### 🎯 提案アクション

#### 合格率改善
- [ ] 正規化ルール強化（`tests/golden/evaluator.py`）
- [ ] プロンプト最適化（`tests/golden/run_golden.py`）
- [ ] 参照データ品質向上（`tests/golden/cases/`）

#### Flaky率削減
- [ ] モデル温度設定見直し（temperature=0.0確認）
- [ ] リトライロジック強化
- [ ] 環境依存要因の排除

#### 新規失敗率削減
- [ ] 失敗履歴シミュレーション実行
- [ ] 同義語辞書拡充
- [ ] 複合語分割ルール追加

### 📈 監視継続
- **次回評価**: 明日 09:10 JST
- **目標**: 全条件7日連続達成
- **エスカレーション**: 連続2日未達成で優先度HIGH

### 🔗 関連リンク
- [Golden KPI Dashboard](http://localhost:8501)
- [Canary PR](https://github.com/{os.getenv('GITHUB_REPOSITORY', 'repo')}/pull/29)
- [実行ログ]({os.getenv('GITHUB_SERVER_URL', 'https://github.com')}/{os.getenv('GITHUB_REPOSITORY', 'repo')}/actions/runs/{os.getenv('GITHUB_RUN_ID', '0')})

---
🤖 このIssueは自動生成されました
"""
        
        if dry_run:
            print("🧪 Dry Run: Issue作成内容")
            print(issue_body)
            return True
        
        # Issue作成
        create_cmd = [
            "gh", "issue", "create",
            "--title", f"🐤 カナリア週改善要求 - {datetime.now().strftime('%Y-%m-%d')}",
            "--body", issue_body,
            "--label", "canary,improvement,auto-generated"
        ]
        
        result = subprocess.run(create_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Issue作成失敗: {result.stderr}")
            return False
        
        issue_url = result.stdout.strip()
        print(f"✅ 改善Issue作成完了: {issue_url}")
        return True
        
    except Exception as e:
        print(f"❌ Issue作成エラー: {e}")
        return False

def create_release_tag(dry_run: bool = False) -> bool:
    """リリースタグ作成"""
    
    try:
        tag_name = f"v3.0-threshold-0.7"
        release_title = "🚀 Phase 3 Golden Test (Threshold 0.7) - Production Ready"
        
        release_body = f"""## 🎉 Phase 3 本採用完了

### 📊 カナリア週評価結果
- **評価期間**: 7日間
- **最終合格率**: 85%以上達成
- **Flaky率**: 5%未満維持
- **新規失敗率**: 60%以下達成

### 🔧 主要改善
- **正規化強化**: NFKC・同義語・複合語分割
- **プロンプト最適化**: 複合語保持ルール追加
- **評価器改善**: 類似度ゲート・数値近似マッチング
- **監視自動化**: 週次通知・自動昇格・ロールバック

### 📈 品質向上
- **しきい値**: 0.5 → 0.7 (40%向上)
- **Predicted@0.7**: 60-70%安定
- **new_fail_ratio**: 100% → 50% (50%改善)

### 🚀 次のマイルストーン
- Phase 4準備: しきい値0.85への段階昇格
- Shadow評価継続: 品質予測精度向上
- 完全自動化: 人手介入なしの品質管理

---
🤖 自動生成リリース - Golden Test System v3.0
"""
        
        if dry_run:
            print("🧪 Dry Run: リリースタグ作成内容")
            print(f"Tag: {tag_name}")
            print(f"Title: {release_title}")
            print(release_body)
            return True
        
        # リリース作成
        release_cmd = [
            "gh", "release", "create", tag_name,
            "--title", release_title,
            "--notes", release_body,
            "--latest"
        ]
        
        result = subprocess.run(release_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ リリース作成失敗: {result.stderr}")
            return False
        
        print(f"✅ リリースタグ作成完了: {tag_name}")
        return True
        
    except Exception as e:
        print(f"❌ リリース作成エラー: {e}")
        return False

def notify_slack_decision(decision: str, window_data: Dict[str, Any], action_url: str) -> bool:
    """Slack判定結果通知"""
    
    try:
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            print("⚠️ SLACK_WEBHOOK_URL が設定されていません")
            return False
        
        metrics = window_data["metrics"]
        
        if decision == "promote":
            message = {
                "text": "🚀 カナリア週自動昇格完了！",
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
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*平均合格率*: {metrics['avg_pass_rate']}% ✅"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Flaky率*: {metrics['avg_flaky_rate']}% ✅"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*新規失敗率*: {metrics['avg_new_fail_ratio']}% ✅"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*状態*: 本採用完了 🎉"
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
                                "url": "http://localhost:8501"
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "🔗 実行ログ"
                                },
                                "url": action_url
                            }
                        ]
                    }
                ]
            }
        else:
            message = {
                "text": "🐤 カナリア週継続",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🐤 カナリア週継続 - 改善要求"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*理由*: {window_data['decision_reason']}"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*平均合格率*: {metrics['avg_pass_rate']}%"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Flaky率*: {metrics['avg_flaky_rate']}%"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*新規失敗率*: {metrics['avg_new_fail_ratio']}%"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*次回評価*: 明日 09:10"
                            }
                        ]
                    }
                ]
            }
        
        # Slack送信（簡易実装）
        import requests
        response = requests.post(webhook_url, json=message, timeout=10)
        
        if response.status_code == 200:
            print("✅ Slack通知送信完了")
            return True
        else:
            print(f"❌ Slack通知送信失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Slack通知エラー: {e}")
        return False

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Canary Action Decision")
    parser.add_argument("--window", type=str, required=True, help="ウィンドウ評価結果ファイル")
    parser.add_argument("--pr-url", type=str, help="カナリーPR URL")
    parser.add_argument("--auto-merge", action="store_true", help="自動マージ有効")
    parser.add_argument("--create-issue-on-fail", action="store_true", help="失敗時Issue作成")
    parser.add_argument("--dry-run", action="store_true", help="Dry runモード")
    
    args = parser.parse_args()
    
    try:
        # ウィンドウ評価結果読み込み
        window_data = load_canary_window(args.window)
        decision = window_data["decision"]
        
        print(f"🤖 カナリア自動判定: {decision}")
        print(f"理由: {window_data['decision_reason']}")
        
        success = True
        
        if decision == "promote":
            print("🚀 本採用条件達成 - 自動昇格開始")
            
            # PR承認・マージ
            if args.auto_merge and args.pr_url:
                success &= approve_and_merge_pr(args.pr_url, args.dry_run)
            
            # リリースタグ作成
            success &= create_release_tag(args.dry_run)
            
            # 成功通知
            action_url = os.getenv("GITHUB_SERVER_URL", "") + "/" + os.getenv("GITHUB_REPOSITORY", "") + "/actions/runs/" + os.getenv("GITHUB_RUN_ID", "")
            notify_slack_decision("promote", window_data, action_url)
            
        elif decision == "continue_canary":
            print("🐤 カナリア週継続 - 改善Issue作成")
            
            # 改善Issue作成
            if args.create_issue_on_fail:
                success &= create_improvement_issue(window_data, args.dry_run)
            
            # 継続通知
            action_url = os.getenv("GITHUB_SERVER_URL", "") + "/" + os.getenv("GITHUB_REPOSITORY", "") + "/actions/runs/" + os.getenv("GITHUB_RUN_ID", "")
            notify_slack_decision("continue", window_data, action_url)
            
        else:
            print("❌ データ不足 - 手動確認が必要")
            success = False
        
        if success:
            print("✅ カナリア自動判定完了")
            exit(0)
        else:
            print("❌ カナリア自動判定で問題発生")
            exit(1)
            
    except Exception as e:
        print(f"❌ カナリア判定エラー: {e}")
        exit(2)

if __name__ == "__main__":
    main()
