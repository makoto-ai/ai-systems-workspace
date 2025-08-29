#!/usr/bin/env python3
"""
Canary PR作成スクリプト
段階昇格のCanary PRを安全に作成
"""

import json
import yaml
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class CanaryPRCreator:
    def __init__(self):
        self.config_path = "tests/golden/config.yml"
        self.shadow_report_path = "out/shadow_grid.json"
        self.decision_path = "out/staged_decision.json"
    
    def load_promotion_decision(self) -> Dict[str, Any]:
        """段階昇格決定結果を読み込み"""
        decision_file = Path(self.decision_path)
        if not decision_file.exists():
            raise FileNotFoundError(f"Decision file not found: {decision_file}")
        
        with open(decision_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_shadow_evaluation(self) -> Dict[str, Any]:
        """シャドー評価結果を読み込み"""
        shadow_file = Path(self.shadow_report_path)
        if not shadow_file.exists():
            raise FileNotFoundError(f"Shadow report not found: {shadow_file}")
        
        with open(shadow_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def validate_promotion_readiness(self, decision: Dict[str, Any], shadow_data: Dict[str, Any]) -> Dict[str, Any]:
        """昇格準備状況を検証"""
        promotion = decision["promotion"]
        target_threshold = promotion["target_threshold"]
        
        # シャドー評価からターゲットしきい値のKPIを取得
        thresholds = shadow_data["multi_shadow_evaluation"]["thresholds"]
        target_str = str(target_threshold)
        
        if target_str not in thresholds:
            return {
                "ready": False,
                "reason": f"Target threshold {target_threshold} not found in shadow evaluation",
                "kpi": {}
            }
        
        target_kpi = thresholds[target_str]
        pass_rate = target_kpi.get("weighted_pass_rate", target_kpi.get("shadow_pass_rate", 0))
        new_fail_ratio = target_kpi.get("new_fail_ratio", 1.0) * 100
        flaky_rate = target_kpi.get("flaky_rate", 1.0) * 100
        
        # 昇格基準チェック
        meets_pass_rate = pass_rate >= 80
        meets_new_fail_ratio = new_fail_ratio <= 60
        meets_flaky_rate = flaky_rate < 5
        
        all_criteria_met = meets_pass_rate and meets_new_fail_ratio and meets_flaky_rate
        
        validation = {
            "ready": all_criteria_met,
            "target_threshold": target_threshold,
            "kpi": {
                "pass_rate": {"value": pass_rate, "threshold": 80, "meets": meets_pass_rate},
                "new_fail_ratio": {"value": new_fail_ratio, "threshold": 60, "meets": meets_new_fail_ratio},
                "flaky_rate": {"value": flaky_rate, "threshold": 5, "meets": meets_flaky_rate}
            }
        }
        
        if not all_criteria_met:
            failed_criteria = []
            if not meets_pass_rate:
                failed_criteria.append(f"Pass Rate {pass_rate:.1f}% < 80%")
            if not meets_new_fail_ratio:
                failed_criteria.append(f"New Fail Ratio {new_fail_ratio:.1f}% > 60%")
            if not meets_flaky_rate:
                failed_criteria.append(f"Flaky Rate {flaky_rate:.1f}% >= 5%")
            
            validation["reason"] = f"基準未達成: {', '.join(failed_criteria)}"
        
        return validation
    
    def generate_pr_content(self, decision: Dict[str, Any], validation: Dict[str, Any], force_create: bool = False, draft: bool = False, data_collection: bool = False) -> Dict[str, str]:
        """PR内容を生成"""
        current = decision["current_threshold"]["actual_used"]
        target = decision["promotion"]["target_threshold"]
        step = decision["promotion"]["step"]
        
        # タイトル調整
        title_prefix = "🐤 (Data-Collection) " if data_collection else "🐤 "
        title = f"{title_prefix}Canary: Golden Test threshold {current:.2f} → {target:.2f}"
        
        # ステータスバッジ
        if validation["ready"]:
            status_badge = "✅ 基準達成"
            risk_level = "🟢 LOW"
        elif force_create:
            status_badge = "⚠️ 強制作成"
            risk_level = "🟡 MEDIUM"
        else:
            status_badge = "❌ 基準未達"
            risk_level = "🔴 HIGH"
        
        # KPI詳細
        kpi_section = ""
        if "kpi" in validation and validation["kpi"]:
            kpi_table = "| Metric | Current | Threshold | Status |\n|--------|---------|-----------|--------|\n"
            for metric, data in validation["kpi"].items():
                status_icon = "✅" if data["meets"] else "❌"
                kpi_table += f"| {metric.replace('_', ' ').title()} | {data['value']:.1f}% | {data['threshold']}% | {status_icon} |\n"
            kpi_section = f"\n### 📊 昇格基準KPI\n\n{kpi_table}"
        
        # PR本文
        data_collection_notice = """
### ⚠️ データ収集専用PR

**このPRは基準未達成のため、データ収集専用のDraft PRです。**
- 自動マージ: ❌ 無効
- 早期Abort: ✅ 有効（Pass<65% or New>70%で自動クローズ）
- 目的: 実運用相当データでの効果測定

---
""" if data_collection else ""
        
        body = f"""## 🚀 段階昇格: Golden Test Threshold {current:.2f} → {target:.2f}

{data_collection_notice}

### 📋 昇格情報
- **Current Threshold**: {current:.2f}
- **Target Threshold**: {target:.2f}  
- **Promotion Step**: +{step:.2f}
- **Status**: {status_badge}
- **Risk Level**: {risk_level}

{kpi_section}

### 🔍 根拠データ
- **決定タイムスタンプ**: {decision.get('timestamp', 'N/A')}
- **妥当性**: {'✅ VALID' if decision['promotion']['valid'] else '❌ INVALID'}
- **決定理由**: {decision['promotion']['validation_message']}

### ⚙️ 安全制約
- **最小ステップ**: {decision['safety_constraints']['min_step']:.2f}
- **最大ステップ**: {decision['safety_constraints']['max_step']:.2f}
- **クランプ適用**: {'✅ YES' if decision['safety_constraints']['clamping_applied'] else '❌ NO'}

### 🐤 カナリア監視項目
- [ ] 合格率の安定性（7日間）
- [ ] Flaky率の変動監視
- [ ] New fail ratioの推移確認
- [ ] 回帰テストの実行

### 🔄 自動処理フロー
1. **マージ後**: カナリアフラグ有効化
2. **7日間**: 自動監視・メトリクス収集  
3. **監視完了**: 自動本採用またはロールバック判定

### 📊 実験データ
```json
{json.dumps(validation.get("kpi", {}), indent=2, ensure_ascii=False)}
```

---
**⚠️ このPRは段階昇格システムにより自動生成されました**
- 実行ID: `{datetime.now().strftime('%Y%m%d-%H%M%S')}`
- システム: `staged-promotion-v1.0`
"""
        
        return {"title": title, "body": body}
    
    def create_canary_branch_and_commit(self, current: float, target: float) -> str:
        """Canaryブランチを作成してコミット"""
        branch_name = f"canary/threshold-{target:.2f}"
        
        try:
            # ブランチ作成
            subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True)
            print(f"✅ ブランチ作成: {branch_name}")
            
            # config.yml更新
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            config['threshold'] = target
            
            # カナリア設定追加
            config['canary'] = {
                'enabled': True,
                'started_at': datetime.now().isoformat(),
                'previous_threshold': current,
                'monitoring_duration_days': 7
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            # コミット
            subprocess.run(["git", "add", self.config_path], check=True)
            subprocess.run([
                "git", "commit", "-m", 
                f"🐤 Canary: threshold {current:.2f} → {target:.2f}\n\n自動段階昇格システムによるCanary PR"
            ], check=True)
            
            print(f"✅ コミット完了: threshold {current:.2f} → {target:.2f}")
            return branch_name
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git操作エラー: {e}")
            raise
    
    def create_github_pr(self, pr_content: Dict[str, str], branch_name: str, force_create: bool = False, draft: bool = False, extra_labels: str = "") -> Optional[str]:
        """GitHub PRを作成"""
        try:
            # gh CLI を使用してPR作成
            labels = ["canary", "staged-promotion", "golden-test", "threshold"]
            
            # 追加ラベル処理
            if extra_labels:
                extra_list = [l.strip() for l in extra_labels.split(",") if l.strip()]
                labels.extend(extra_list)
            
            cmd = [
                "gh", "pr", "create",
                "--title", pr_content["title"],
                "--body", pr_content["body"],
                "--label", ",".join(labels),
                "--head", branch_name,
                "--base", "main"
            ]
            
            # Draft指定
            if draft:
                cmd.append("--draft")
            
            if not force_create:
                # デモモードでは実際にPRを作成しない
                print("🧪 デモモード: 実際のPR作成はスキップ")
                print(f"実行予定コマンド: {' '.join(cmd)}")
                return f"https://github.com/example/repo/pull/demo-{branch_name}"
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            pr_url = result.stdout.strip()
            
            print(f"✅ PR作成完了: {pr_url}")
            return pr_url
            
        except subprocess.CalledProcessError as e:
            print(f"❌ PR作成エラー: {e}")
            if hasattr(e, 'stderr') and e.stderr:
                print(f"Error details: {e.stderr}")
            raise
    
    def create_canary_pr(self, force_create: bool = False, demo_mode: bool = True, draft: bool = False, extra_labels: str = "", target_threshold: float = None) -> Dict[str, Any]:
        """Canary PRを作成"""
        print("🐤 Canary PR作成プロセス開始")
        
        # データ収集モード判定
        data_collection = draft and "data-collection" in extra_labels
        
        # 1. 決定結果読み込み
        decision = self.load_promotion_decision()
        
        # ターゲットしきい値の上書き（指定がある場合）
        if target_threshold is not None:
            print(f"🎯 ターゲットしきい値を上書き: {decision['promotion']['target_threshold']:.2f} → {target_threshold:.2f}")
            decision['promotion']['target_threshold'] = target_threshold
            decision['promotion']['step'] = target_threshold - decision['current_threshold']['actual_used']
            
        print(f"📋 昇格決定読み込み: {decision['promotion']['target_threshold']:.2f}")
        
        # 2. シャドー評価読み込み
        shadow_data = self.load_shadow_evaluation()
        print("📊 シャドー評価読み込み完了")
        
        # 3. 昇格準備状況検証
        validation = self.validate_promotion_readiness(decision, shadow_data)
        print(f"🔍 準備状況: {'✅ READY' if validation['ready'] else '❌ NOT READY'}")
        
        if not validation["ready"] and not force_create and not data_collection:
            print(f"🛑 昇格基準未達成のためPR作成中止")
            print(f"理由: {validation.get('reason', 'N/A')}")
            return {
                "success": False,
                "reason": validation.get("reason", "基準未達成"),
                "validation": validation
            }
        
        # 4. PR内容生成
        pr_content = self.generate_pr_content(decision, validation, force_create, draft, data_collection)
        print("📝 PR内容生成完了")
        
        if demo_mode:
            # デモモード: 実際の操作なしで内容表示
            print("\n" + "="*60)
            print("🧪 DEMO MODE: Canary PR Preview")
            print("="*60)
            print(f"Title: {pr_content['title']}")
            print(f"\nBody:\n{pr_content['body'][:500]}...")
            print("="*60)
            
            return {
                "success": True,
                "demo_mode": True,
                "pr_content": pr_content,
                "validation": validation
            }
        
        # 5. 実際のPR作成（非デモモード）
        try:
            current = decision["current_threshold"]["actual_used"]
            target = decision["promotion"]["target_threshold"]
            
            # ブランチ作成＆コミット
            branch_name = self.create_canary_branch_and_commit(current, target)
            
            # GitHub PR作成
            pr_url = self.create_github_pr(pr_content, branch_name, force_create, draft, extra_labels)
            
            result = {
                "success": True,
                "pr_url": pr_url,
                "branch_name": branch_name,
                "validation": validation,
                "current_threshold": current,
                "target_threshold": target
            }
            
            print(f"🎉 Canary PR作成完了!")
            return result
            
        except Exception as e:
            print(f"❌ PR作成失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "validation": validation
            }


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Canary PR作成")
    parser.add_argument("--force", action="store_true", help="基準未達成でも強制作成")
    parser.add_argument("--no-demo", action="store_true", help="実際のPRを作成（デモモード無効）")
    parser.add_argument("--draft", action="store_true", help="Draft PRとして作成")
    parser.add_argument("--labels", type=str, help="追加ラベル（カンマ区切り）", default="")
    parser.add_argument("--target", type=float, help="ターゲットしきい値を指定", default=None)
    args = parser.parse_args()
    
    creator = CanaryPRCreator()
    
    try:
        result = creator.create_canary_pr(
            force_create=args.force,
            demo_mode=not args.no_demo,
            draft=args.draft,
            extra_labels=args.labels,
            target_threshold=args.target
        )
        
        # 結果表示
        if result["success"]:
            if result.get("demo_mode"):
                print("\n✅ デモモード完了: 実際のPRは作成されていません")
                print("実際に作成するには --no-demo フラグを使用してください")
            else:
                print(f"\n✅ Canary PR作成成功: {result.get('pr_url', 'N/A')}")
                
            return 0
        else:
            print(f"\n❌ Canary PR作成失敗: {result.get('reason', result.get('error', 'Unknown'))}")
            return 1
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return 2


if __name__ == "__main__":
    import sys
    sys.exit(main())
