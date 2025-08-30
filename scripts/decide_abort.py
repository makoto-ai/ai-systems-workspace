#!/usr/bin/env python3
"""
早期Abort判定スクリプト
データ収集専用PRの初回計測結果を評価し、基準を満たさない場合は自動クローズ
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Tuple


class EarlyAbortDecider:
    def __init__(self):
        self.hard_min_pass = 0.65  # Pass Rate最低基準（65%）
        self.hard_max_new = 0.70   # New Fail Ratio最大基準（70%）
    
    def load_shadow_results(self, shadow_path: str) -> Dict[str, Any]:
        """Shadow評価結果を読み込み"""
        shadow_file = Path(shadow_path)
        if not shadow_file.exists():
            raise FileNotFoundError(f"Shadow report not found: {shadow_file}")
        
        with open(shadow_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def evaluate_abort_criteria(self, shadow_data: Dict[str, Any], target_threshold: float) -> Tuple[bool, str]:
        """早期Abort基準を評価"""
        # マルチシャドー評価結果から該当しきい値を取得
        multi_eval = shadow_data.get("multi_shadow_evaluation", {})
        thresholds = multi_eval.get("thresholds", {})
        
        target_str = str(target_threshold)
        if target_str not in thresholds:
            return True, f"Target threshold {target_threshold} not found in evaluation"
        
        target_data = thresholds[target_str]
        
        # KPI取得
        pass_rate = target_data.get("weighted_pass_rate", target_data.get("shadow_pass_rate", 0))
        new_fail_ratio = target_data.get("new_fail_ratio", 1.0) * 100
        flaky_rate = target_data.get("flaky_rate", 1.0) * 100
        
        print(f"📊 {target_threshold}のKPI:")
        print(f"  Pass Rate: {pass_rate:.1f}%")
        print(f"  New Fail Ratio: {new_fail_ratio:.1f}%")
        print(f"  Flaky Rate: {flaky_rate:.1f}%")
        
        # Abort条件チェック
        abort_reasons = []
        
        if pass_rate < self.hard_min_pass * 100:
            abort_reasons.append(f"Pass Rate {pass_rate:.1f}% < {self.hard_min_pass * 100:.0f}%")
        
        if new_fail_ratio > self.hard_max_new * 100:
            abort_reasons.append(f"New Fail Ratio {new_fail_ratio:.1f}% > {self.hard_max_new * 100:.0f}%")
        
        should_abort = len(abort_reasons) > 0
        
        if should_abort:
            reason = "早期Abort条件に該当: " + ", ".join(abort_reasons)
        else:
            reason = "Abort条件に該当せず - データ収集継続"
        
        return should_abort, reason
    
    def set_github_env(self, abort: bool, reason: str):
        """GitHub Actions環境変数を設定"""
        github_env = os.environ.get('GITHUB_ENV')
        
        if github_env:
            with open(github_env, 'a') as f:
                f.write(f"ABORT={'true' if abort else 'false'}\n")
                f.write(f"ABORT_REASON={reason}\n")
            print(f"✅ GitHub環境変数設定: ABORT={'true' if abort else 'false'}")
        else:
            print("⚠️ GITHUB_ENV not found - ローカル実行モード")
            print(f"ABORT={'true' if abort else 'false'}")
            print(f"ABORT_REASON={reason}")
    
    def decide_abort(self, shadow_path: str, target_threshold: float, 
                    hard_min_pass: float = None, hard_max_new: float = None) -> Dict[str, Any]:
        """早期Abort判定を実行"""
        print("🔍 早期Abort判定開始")
        
        # カスタム基準の設定
        if hard_min_pass is not None:
            self.hard_min_pass = hard_min_pass
        if hard_max_new is not None:
            self.hard_max_new = hard_max_new
        
        print(f"📏 Abort基準:")
        print(f"  最低Pass Rate: {self.hard_min_pass * 100:.0f}%")
        print(f"  最大New Fail Ratio: {self.hard_max_new * 100:.0f}%")
        
        # Shadow評価結果読み込み
        shadow_data = self.load_shadow_results(shadow_path)
        
        # Abort判定
        should_abort, reason = self.evaluate_abort_criteria(shadow_data, target_threshold)
        
        # 結果表示
        print(f"\n{'🛑' if should_abort else '✅'} 判定結果: {'ABORT' if should_abort else 'CONTINUE'}")
        print(f"理由: {reason}")
        
        # GitHub環境変数設定
        self.set_github_env(should_abort, reason)
        
        return {
            "abort": should_abort,
            "reason": reason,
            "target_threshold": target_threshold,
            "criteria": {
                "hard_min_pass": self.hard_min_pass,
                "hard_max_new": self.hard_max_new
            }
        }


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="早期Abort判定")
    parser.add_argument("--shadow", required=True, help="Shadow評価結果ファイルパス")
    parser.add_argument("--threshold", type=float, required=True, help="ターゲットしきい値")
    parser.add_argument("--hard-min-pass", type=float, help="最低Pass Rate（0-1）")
    parser.add_argument("--hard-max-new", type=float, help="最大New Fail Ratio（0-1）")
    args = parser.parse_args()
    
    decider = EarlyAbortDecider()
    
    try:
        result = decider.decide_abort(
            shadow_path=args.shadow,
            target_threshold=args.threshold,
            hard_min_pass=args.hard_min_pass,
            hard_max_new=args.hard_max_new
        )
        
        # Abort判定の場合は終了コード1
        return 1 if result["abort"] else 0
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())




