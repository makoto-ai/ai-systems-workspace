#!/usr/bin/env python3
"""
Golden Test Runner with Shadow Evaluation
しきい値影響予測・シャドー評価システム
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    # 相対インポートを試行
    from .run_golden import predict, load_config
    from .evaluator import score
    from .root_cause_analyzer import analyze_failure_root_cause, Freshness
except ImportError:
    try:
        # 絶対インポートを試行
        from run_golden import predict, load_config
        from evaluator import score
        from root_cause_analyzer import analyze_failure_root_cause, Freshness
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please run from tests/golden directory or ensure modules are accessible")
        sys.exit(1)

def run_shadow_evaluation(shadow_threshold: float, report_path: str = None) -> Dict[str, Any]:
    """シャドー評価実行（本番しきい値は変更せず、予測評価のみ）"""
    
    # 現在の設定を読み込み
    config = load_config()
    current_threshold = config.get("threshold", 0.5)
    
    print(f"🔍 Shadow Evaluation: threshold {current_threshold} → {shadow_threshold}")
    print(f"📊 本番しきい値は {current_threshold} のまま、{shadow_threshold} での予測評価を実行")
    
    # テストケースを読み込み
    cases_dir = Path("tests/golden/cases")
    if not cases_dir.exists():
        raise FileNotFoundError(f"Test cases directory not found: {cases_dir}")
    
    results = []
    shadow_passed = 0
    shadow_total = 0
    new_failures = 0
    total_failures = 0
    flaky_failures = 0
    root_cause_counts = {}
    
    # 失敗履歴を構築（new_fail_ratio計算用）
    failure_history = build_failure_history()
    current_date = datetime.now().strftime("%Y%m%d")
    
    for case_file in sorted(cases_dir.glob("*.json")):
        try:
            with open(case_file, 'r', encoding='utf-8') as f:
                case_data = json.load(f)
            
            case_id = case_data.get("id", case_file.stem)
            reference = case_data.get("reference", "")
            input_text = case_data.get("input", "")
            
            # 予測実行
            prediction = predict(input_text)
            test_score = score(reference, prediction)
            
            # 現在のしきい値での結果
            current_passed = test_score >= current_threshold
            
            # シャドーしきい値での結果
            shadow_passed_case = test_score >= shadow_threshold
            shadow_total += 1
            if shadow_passed_case:
                shadow_passed += 1
            
            # 失敗分析（シャドーしきい値基準）
            if not shadow_passed_case:
                total_failures += 1
                
                # Root Cause分析
                root_cause = analyze_failure_root_cause(case_id, reference, prediction, test_score)
                root_cause_str = root_cause.value
                root_cause_counts[root_cause_str] = root_cause_counts.get(root_cause_str, 0) + 1
                
                # Freshness判定
                freshness = infer_freshness(case_id, current_date, failure_history)
                if freshness == Freshness.NEW:
                    new_failures += 1
                
                # Flaky判定
                if test_score >= 0.7:
                    flaky_failures += 1
            
            results.append({
                "case_id": case_id,
                "score": test_score,
                "current_passed": current_passed,
                "shadow_passed": shadow_passed_case,
                "reference": reference,
                "prediction": prediction,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"❌ Error processing {case_file}: {e}")
            continue
    
    # 統計計算
    shadow_pass_rate = (shadow_passed / shadow_total * 100) if shadow_total > 0 else 0
    flaky_rate = (flaky_failures / max(total_failures, 1) * 100) if total_failures > 0 else 0
    new_fail_ratio = (new_failures / max(total_failures, 1)) if total_failures > 0 else 0
    
    # Root Cause Top3
    root_cause_top3 = sorted(root_cause_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    # レポート生成
    report = {
        "shadow_evaluation": {
            "current_threshold": current_threshold,
            "shadow_threshold": shadow_threshold,
            "timestamp": datetime.now().isoformat(),
            "total_cases": shadow_total,
            "shadow_passed": shadow_passed,
            "shadow_pass_rate": shadow_pass_rate,
            "total_failures": total_failures,
            "new_failures": new_failures,
            "new_fail_ratio": new_fail_ratio,
            "flaky_failures": flaky_failures,
            "flaky_rate": flaky_rate,
            "root_cause_top3": root_cause_top3,
            "root_cause_distribution": root_cause_counts
        },
        "detailed_results": results
    }
    
    # レポート保存
    if report_path:
        report_file = Path(report_path)
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"📄 Shadow evaluation report saved: {report_file}")
    
    # 結果表示
    print(f"\n📊 Shadow Evaluation Results (threshold={shadow_threshold}):")
    print(f"  合格率: {shadow_passed}/{shadow_total} ({shadow_pass_rate:.1f}%)")
    print(f"  Flaky率: {flaky_rate:.1f}%")
    print(f"  新規失敗率: {new_fail_ratio:.1%}")
    print(f"  Root Cause Top3: {root_cause_top3}")
    
    return report

def build_failure_history() -> Dict[str, set]:
    """過去の失敗履歴を構築"""
    logs_dir = Path("tests/golden/logs")
    failure_history = {}
    
    if not logs_dir.exists():
        return failure_history
    
    for log_file in sorted(logs_dir.glob("*.jsonl")):
        date_str = log_file.stem.split('_')[0]  # YYYYMMDD部分
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if not data.get('passed', True):  # 失敗ケース
                            case_id = data.get('id', '')
                            if case_id:
                                if case_id not in failure_history:
                                    failure_history[case_id] = set()
                                failure_history[case_id].add(date_str)
                    except json.JSONDecodeError:
                        continue
    
    return failure_history

def infer_freshness(case_id: str, current_date: str, history: Dict[str, set]) -> Freshness:
    """失敗の新規性を判定"""
    if case_id not in history:
        return Freshness.NEW
    
    past_failures = history[case_id]
    for past_date in past_failures:
        if past_date < current_date:
            return Freshness.REPEAT
    
    return Freshness.NEW

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Golden Test Runner with Shadow Evaluation")
    parser.add_argument("--threshold-shadow", type=float, 
                       help="シャドー評価用しきい値（本番は変更されません）")
    parser.add_argument("--report", type=str, 
                       help="レポート出力パス（例: out/shadow_0_7.json）")
    
    args = parser.parse_args()
    
    if args.threshold_shadow:
        try:
            report = run_shadow_evaluation(args.threshold_shadow, args.report)
            return report["shadow_evaluation"]["shadow_pass_rate"] >= 80  # 成功判定
        except Exception as e:
            print(f"❌ Shadow evaluation failed: {e}")
            return False
    else:
        parser.print_help()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
