#!/usr/bin/env python3
"""
Golden Test Results Notification System
Slack通知システム（Phase4対応）
"""

import json
import os
import requests
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class NotificationSender:
    """通知送信クラス"""
    
    def __init__(self):
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        if not self.slack_webhook:
            print("⚠️ SLACK_WEBHOOK_URL not found, will print to console instead")
    
    def load_shadow_results(self) -> Optional[Dict[str, Any]]:
        """Shadow Evaluation結果を読み込み（段階昇格対応）"""
        # 段階昇格用グリッドファイルを優先
        grid_file = Path("out/shadow_grid.json")
        if grid_file.exists():
            try:
                with open(grid_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Grid results読み込みエラー: {e}")
        
        # 従来のマルチシャドー評価ファイル
        multi_shadow_file = Path("out/shadow_multi.json")
        if multi_shadow_file.exists():
            try:
                with open(multi_shadow_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Shadow results読み込みエラー: {e}")
        return None
    
    def load_prompt_optimization_results(self) -> Optional[Dict[str, Any]]:
        """プロンプト最適化結果を読み込み"""
        prompt_opt_file = Path("out/prompt_opt_phase4.json")
        if prompt_opt_file.exists():
            try:
                with open(prompt_opt_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Prompt optimization結果読み込みエラー: {e}")
        return None
    
    def load_new_failures(self) -> Optional[Dict[str, Any]]:
        """新規失敗データを読み込み"""
        new_fails_file = Path("out/new_fails.json")
        if new_fails_file.exists():
            try:
                with open(new_fails_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ New failures読み込みエラー: {e}")
        return None
    
    def calculate_phase4_metrics(self, shadow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase4関連メトリクスを計算"""
        multi_eval = shadow_data.get("multi_shadow_evaluation", {})
        thresholds = multi_eval.get("thresholds", {})
        
        # 0.85しきい値の結果
        threshold_85 = thresholds.get("0.85", {})
        predicted_at_85 = threshold_85.get("weighted_pass_rate", threshold_85.get("shadow_pass_rate", 0))
        
        # Phase4 Gap計算
        phase4_gap = max(0, 85.0 - predicted_at_85)
        
        # 新規失敗率
        new_fail_ratio = threshold_85.get("new_fail_ratio", 0) * 100
        
        # Flaky率
        flaky_rate = threshold_85.get("flaky_rate", 0) * 100
        
        return {
            "predicted_at_85": predicted_at_85,
            "phase4_gap": phase4_gap,
            "new_fail_ratio": new_fail_ratio,
            "flaky_rate": flaky_rate,
            "ready_for_phase4": predicted_at_85 >= 85 and new_fail_ratio <= 70
        }
    
    def generate_improvement_suggestions(self, prompt_results: Optional[Dict], new_fails: Optional[Dict], phase4_metrics: Dict) -> List[str]:
        """改善提案Top3を生成"""
        suggestions = []
        
        # プロンプト最適化からの提案
        if prompt_results:
            prompt_suggestions = prompt_results.get("improvement_suggestions", [])
            for suggestion in prompt_suggestions[:2]:  # 上位2つ
                suggestions.append(f"`{suggestion['type']}`: {suggestion['description']}")
        
        # 新規失敗からの提案
        if new_fails:
            total_new = new_fails.get("total_new_failures", 0)
            if total_new > 0:
                suggestions.append(f"`norm:new-fails`: {total_new}件の新規失敗に対応")
        
        # Phase4 Gap解消提案
        if phase4_metrics["phase4_gap"] > 0:
            suggestions.append(f"`phase4:gap-reduction`: Pred@0.85を{phase4_metrics['phase4_gap']:.1f}pp向上")
        
        # 数値近似厳格化の提案
        if phase4_metrics["predicted_at_85"] < 80:
            suggestions.append(f"`evaluator:precision`: 数値近似±3%への厳格化適用")
        
        return suggestions[:3]  # Top3のみ
    
    def create_slack_message(self, shadow_data: Dict, phase4_metrics: Dict, suggestions: List[str], data_collection: bool = False, action_url: str = None, pr_url: str = None) -> Dict[str, Any]:
        """Slack通知メッセージを作成（データ収集モード対応）"""
        multi_eval = shadow_data.get("multi_shadow_evaluation", {})
        timestamp = multi_eval.get("timestamp", datetime.now().isoformat())
        staged_promotion = multi_eval.get("staged_promotion", {})
        
        # 段階昇格情報
        has_staged_promotion = bool(staged_promotion)
        promotion_ready = staged_promotion.get("promotion_ready", False)
        next_recommended = staged_promotion.get("next_recommended", 0.5)
        current_threshold = staged_promotion.get("current_threshold", 0.5)
        promotion_step = staged_promotion.get("promotion_step", 0)
        
        # ステータス絵文字とタイトル
        if data_collection:
            status_emoji = "🧪"
            text = f"{status_emoji} **Data Collection Canary Report**"
        elif has_staged_promotion and promotion_ready:
            status_emoji = "🚀"
            text = f"{status_emoji} **Golden Test 段階昇格 Report**"
        else:
            status_emoji = "✅" if phase4_metrics["ready_for_phase4"] else "🔄"
            text = f"{status_emoji} **Golden Test Phase 4 Status Report**"
        
        gap_emoji = "🎯" if phase4_metrics["phase4_gap"] <= 5 else "⚠️"
        
        # 詳細セクション
        if data_collection:
            header_text = f"{status_emoji} Data Collection Canary Report"
        elif has_staged_promotion:
            header_text = f"{status_emoji} Golden Test 段階昇格 Report"
        else:
            header_text = f"{status_emoji} Golden Test Phase 4 Report"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": header_text
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📅 {timestamp[:19].replace('T', ' ')}"
                    }
                ]
            }
        ]
        
        # 段階昇格情報がある場合
        if has_staged_promotion:
            promotion_fields = [
                {
                    "type": "mrkdwn",
                    "text": f"*Current Threshold*\n{current_threshold:.2f}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Next Recommended*\n{next_recommended:.2f}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*昇格ステップ*\n{promotion_step:+.2f}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*昇格ステータス*\n{'✅ 可能' if promotion_ready else '🟡 待機'}"
                }
            ]
            blocks.append({
                "type": "section",
                "fields": promotion_fields
            })
        
        # データ収集モード特別セクション
        if data_collection:
            # 0.72のKPIを抽出
            thresholds = multi_eval.get("thresholds", {})
            target_72 = thresholds.get("0.72", {})
            pass_72 = target_72.get("weighted_pass_rate", target_72.get("shadow_pass_rate", 0))
            new_fail_72 = target_72.get("new_fail_ratio", 1.0) * 100
            flaky_72 = target_72.get("flaky_rate", 1.0) * 100
            
            # 早期Abort判定
            abort_triggered = pass_72 < 65 or new_fail_72 > 70
            
            data_collection_fields = [
                {
                    "type": "mrkdwn",
                    "text": f"*Target Threshold*\n0.72"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Pass Rate@0.72*\n{pass_72:.1f}% {'❌' if pass_72 < 65 else '✅'}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*New Fail@0.72*\n{new_fail_72:.1f}% {'❌' if new_fail_72 > 70 else '✅'}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*早期Abort*\n{'🛑 発動' if abort_triggered else '✅ 継続'}"
                }
            ]
            blocks.append({
                "type": "section",
                "fields": data_collection_fields
            })
            
            if abort_triggered:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🛑 早期Abort条件に該当*\n• Pass Rate {pass_72:.1f}% < 65% または New Fail {new_fail_72:.1f}% > 70%\n• PRは自動クローズされます"
                    }
                })
        
        # Phase4メトリクス（通常モード）
        phase4_fields = [
            {
                "type": "mrkdwn",
                "text": f"*Predicted@0.85*\n{phase4_metrics['predicted_at_85']:.1f}%"
            },
            {
                "type": "mrkdwn", 
                "text": f"*Phase 4 Gap*\n{gap_emoji} {phase4_metrics['phase4_gap']:.1f}pp"
            },
            {
                "type": "mrkdwn",
                "text": f"*新規失敗率*\n{phase4_metrics['new_fail_ratio']:.1f}%"
            },
            {
                "type": "mrkdwn",
                "text": f"*Flaky率*\n{phase4_metrics['flaky_rate']:.1f}%"
            }
        ]
        blocks.append({
            "type": "section",
            "fields": phase4_fields
        })
        
        # 段階昇格推奨アクション
        if has_staged_promotion and promotion_ready:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🚀 推奨アクション*\n• threshold を {promotion_step:+.2f} 引き上げ (→ {next_recommended:.2f})\n• 段階昇格PRの自動作成を待機中\n• 7日間のカナリア監視後に本採用判定"
                }
            })
        
        # 改善提案セクション
        if suggestions:
            suggestion_text = "\n".join([f"• {suggestion}" for suggestion in suggestions])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*💡 改善提案 Top 3*\n{suggestion_text}"
                }
            })
        
        # Phase4準備状況
        if has_staged_promotion and promotion_ready:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🚀 *段階昇格準備完了*\n2連続で昇格条件を満たしました"
                }
            })
        elif phase4_metrics["ready_for_phase4"]:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "✅ *Phase 4準備完了*\n2週連続で条件達成すれば自動昇格"
                }
            })
        else:
            remaining_tasks = []
            if phase4_metrics["phase4_gap"] > 0:
                remaining_tasks.append(f"Pred@0.85を{phase4_metrics['phase4_gap']:.1f}pp向上")
            if phase4_metrics["new_fail_ratio"] > 70:
                remaining_tasks.append(f"新規失敗率を{phase4_metrics['new_fail_ratio'] - 70:.1f}pp削減")
            
            if remaining_tasks:
                task_text = "\n".join([f"• {task}" for task in remaining_tasks])
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🔄 *残り改善項目*\n{task_text}"
                    }
                })
        
        # リンクセクション（データ収集モード）
        if data_collection and (action_url or pr_url):
            links = []
            if pr_url:
                links.append(f"<{pr_url}|📄 PR>")
            if action_url:
                links.append(f"<{action_url}|🏃 Actions>")
            
            if links:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🔗 関連リンク*\n{' | '.join(links)}"
                    }
                })
        
        return {
            "text": text,
            "blocks": blocks
        }
    
    def send_notification(self, message: Dict[str, Any]) -> bool:
        """通知を送信"""
        if not self.slack_webhook:
            # Slack未設定の場合はコンソール出力
            print("\n" + "="*50)
            print("📢 Golden Test Phase 4 Notification")
            print("="*50)
            print(f"Text: {message['text']}")
            
            for block in message.get('blocks', []):
                if block['type'] == 'section' and 'text' in block:
                    print(f"\n{block['text']['text']}")
                elif block['type'] == 'section' and 'fields' in block:
                    for field in block['fields']:
                        _t = field.get('text', '')
                        _t = _t.replace('*', '').replace('\n', ': ')
                        print(f"  {_t}")
            
            print("="*50)
            return True
        
        try:
            response = requests.post(
                self.slack_webhook,
                json=message,
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ Slack通知送信成功")
                return True
            else:
                print(f"❌ Slack通知送信失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Slack通知送信エラー: {e}")
            return False
    
    def run_notification(self) -> bool:
        """通知実行メイン処理"""
        try:
            # データ読み込み
            print("📊 Loading results...")
            shadow_data = self.load_shadow_results()
            if not shadow_data:
                print("❌ Shadow evaluation results not found")
                return False
            
            prompt_results = self.load_prompt_optimization_results()
            new_fails = self.load_new_failures()
            
            # Phase4メトリクス計算
            phase4_metrics = self.calculate_phase4_metrics(shadow_data)
            
            # 改善提案生成
            suggestions = self.generate_improvement_suggestions(prompt_results, new_fails, phase4_metrics)

            # Slackメッセージ作成（デフォルト: 通常モード・リンクなし）
            message = self.create_slack_message(
                shadow_data,
                phase4_metrics,
                suggestions,
                data_collection=False,
                action_url=None,
                pr_url=None
            )

            # 通知送信
            return self.send_notification(message)
            
        except Exception as e:
            print(f"❌ Notification failed: {e}")
            return False

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Golden Test Results Notification")
    parser.add_argument("--test", action="store_true", help="テスト送信（実際には送信しない）")
    
    args = parser.parse_args()
    
    try:
        sender = NotificationSender()
        
        if args.test:
            print("🧪 Test mode: notification will be printed to console")
            # テストモードではSlackを無効化
            sender.slack_webhook = None
        
        success = sender.run_notification()
        return success
        
    except Exception as e:
        print(f"❌ Main process failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)