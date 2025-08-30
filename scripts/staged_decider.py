#!/usr/bin/env python3
"""
段階昇格の決定ロジック
現在値の実測 → 安全ステップ計算 → 昇格可否判定
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple, Optional


class StagedPromotionDecider:
    def __init__(self):
        self.min_step = 0.02
        self.max_step = 0.05
        self.config_path = "tests/golden/config.yml"
        self.shadow_report_path = "out/shadow_grid.json"
    
    def get_current_threshold_reality(self) -> float:
        """config.ymlから実際の現在しきい値を取得"""
        config_path = Path(self.config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return float(config.get('threshold', 0.5))
    
    def detect_threshold_divergence(self) -> Tuple[float, float, bool]:
        """しきい値の乖離を検出"""
        config_current = self.get_current_threshold_reality()
        
        # Shadow reportから推定値を取得
        report_path = Path(self.shadow_report_path)
        if not report_path.exists():
            print(f"⚠️ Shadow report not found: {report_path}")
            return config_current, 0.0, True
        
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        staged_promotion = report.get('multi_shadow_evaluation', {}).get('staged_promotion', {})
        report_assumed = float(staged_promotion.get('current_threshold', 0.0))
        
        # 乖離チェック（0.01を超えたら乖離とみなす）
        divergence_detected = abs(config_current - report_assumed) > 0.01
        
        print(f"📊 しきい値乖離チェック:")
        print(f"  Config実値: {config_current:.2f}")
        print(f"  Report推定: {report_assumed:.2f}")
        print(f"  乖離: {config_current - report_assumed:+.3f}")
        print(f"  乖離検出: {'❌ YES' if divergence_detected else '✅ NO'}")
        
        return config_current, report_assumed, divergence_detected
    
    def calculate_safe_next_target(self, current: float) -> float:
        """安全な次のターゲットを計算（危険幅クランプ適用）"""
        # 基本ステップは0.02
        proposed_step = self.min_step
        proposed_target = current + proposed_step
        
        # ステップのクランプ（0.02-0.05の範囲内）
        clamped_step = max(self.min_step, min(proposed_step, self.max_step))
        
        if clamped_step != proposed_step:
            print(f"⚠️ ステップクランプ適用: {proposed_step:.2f} → {clamped_step:.2f}")
        
        # 0.02刻みに丸める
        safe_target = current + clamped_step
        rounded_target = round(safe_target / 0.02) * 0.02
        
        print(f"🎯 安全ターゲット計算:")
        print(f"  Current: {current:.2f}")
        print(f"  Step: +{clamped_step:.2f}")
        print(f"  Target: {rounded_target:.2f}")
        
        # 期待値チェック（0.70 → 0.72を期待）
        if current == 0.70:
            expected_target = 0.72
            if abs(rounded_target - expected_target) < 0.001:
                print(f"✅ 期待ターゲット一致: {expected_target:.2f}")
            else:
                print(f"⚠️ 期待ターゲット不一致: expected={expected_target:.2f}, actual={rounded_target:.2f}")
        
        return rounded_target
    
    def validate_promotion_step(self, current: float, target: float) -> Tuple[bool, str]:
        """昇格ステップの妥当性を検証"""
        step = target - current
        
        # 危険幅チェック
        if step > self.max_step:
            return False, f"overshoot: ステップ{step:.2f}が上限{self.max_step:.2f}を超過"
        
        if step < self.min_step:
            return False, f"understep: ステップ{step:.2f}が下限{self.min_step:.2f}未満"
        
        # 期待範囲チェック
        if target not in [0.72, 0.75]:
            return False, f"unexpected_target: {target:.2f}は期待範囲外（0.72 or 0.75）"
        
        # 0.72を優先
        if current == 0.70 and target != 0.72:
            return False, f"priority_violation: 0.70からは0.72を優先すべき（actual: {target:.2f}）"
        
        return True, f"valid: {current:.2f} → {target:.2f} (+{step:.2f})"
    
    def decide_staged_promotion(self) -> Dict[str, Any]:
        """段階昇格を決定"""
        print("🚀 段階昇格決定プロセス開始")
        
        # 1. 現在値の実測と乖離チェック
        config_current, report_assumed, has_divergence = self.detect_threshold_divergence()
        
        # 2. 乖離時は実値を採用
        if has_divergence:
            print(f"🔧 乖離修正: report推定値を無視、config実値({config_current:.2f})を採用")
            actual_current = config_current
        else:
            actual_current = config_current
        
        # 3. 安全な次のターゲット計算
        next_target = self.calculate_safe_next_target(actual_current)
        
        # 4. 昇格ステップの妥当性検証
        is_valid, validation_message = self.validate_promotion_step(actual_current, next_target)
        
        # 5. 決定結果
        decision = {
            "timestamp": json.loads(json.dumps({"ts": "now"}, default=str))["ts"],
            "current_threshold": {
                "config_value": config_current,
                "report_assumed": report_assumed,
                "actual_used": actual_current,
                "divergence_detected": has_divergence
            },
            "promotion": {
                "target_threshold": next_target,
                "step": next_target - actual_current,
                "valid": is_valid,
                "validation_message": validation_message
            },
            "safety_constraints": {
                "min_step": self.min_step,
                "max_step": self.max_step,
                "clamping_applied": abs(next_target - actual_current) != self.min_step
            },
            "next_action": "create_canary_pr" if is_valid else "block_promotion"
        }
        
        print(f"\n📋 段階昇格決定結果:")
        print(f"  実際の現在値: {actual_current:.2f}")
        print(f"  次のターゲット: {next_target:.2f}")
        print(f"  昇格ステップ: +{next_target - actual_current:.2f}")
        print(f"  妥当性: {'✅ VALID' if is_valid else '❌ INVALID'}")
        print(f"  理由: {validation_message}")
        print(f"  次のアクション: {decision['next_action']}")
        
        return decision
    
    def save_decision(self, decision: Dict[str, Any], output_path: str = "out/staged_decision.json"):
        """決定結果を保存"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(decision, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"💾 決定結果保存: {output_file}")
        return output_file


def main():
    """メイン実行"""
    decider = StagedPromotionDecider()
    
    try:
        # 段階昇格決定
        decision = decider.decide_staged_promotion()
        
        # 結果保存
        decider.save_decision(decision)
        
        # 成功/失敗の終了コード
        exit_code = 0 if decision["promotion"]["valid"] else 1
        print(f"\n🎯 終了コード: {exit_code}")
        return exit_code
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return 2


if __name__ == "__main__":
    import sys
    sys.exit(main())



