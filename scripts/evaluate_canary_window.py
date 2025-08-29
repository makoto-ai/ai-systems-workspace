#!/usr/bin/env python3
"""
Canary Window Evaluation
カナリア週7日ウィンドウの評価・集計
"""

import json
import argparse
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

def parse_observation_log() -> List[Dict[str, Any]]:
    """observation_log.mdから週次結果を解析"""
    
    log_file = Path("tests/golden/observation_log.md")
    if not log_file.exists():
        print(f"❌ 観測ログが見つかりません: {log_file}")
        return []
    
    observations = []
    current_entry = None
    
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 日付セクションを抽出
    date_sections = re.findall(r'## (\d{4}-\d{2}-\d{2}) - 週次観測(.*?)(?=## \d{4}-\d{2}-\d{2}|$)', content, re.DOTALL)
    
    for date_str, section_content in date_sections:
        try:
            # 合格率抽出
            pass_rate_match = re.search(r'合格率\*\*:\s*(\d+)/(\d+)\s*\((\d+)%\)', section_content)
            if pass_rate_match:
                passed = int(pass_rate_match.group(1))
                total = int(pass_rate_match.group(2))
                pass_rate = int(pass_rate_match.group(3))
            else:
                continue
            
            # しきい値抽出
            threshold_match = re.search(r'しきい値\*\*:\s*([\d.]+)', section_content)
            threshold = float(threshold_match.group(1)) if threshold_match else 0.5
            
            # 状態抽出
            status_match = re.search(r'状態\*\*:\s*([^✅❌\n]+)', section_content)
            status = status_match.group(1).strip() if status_match else "不明"
            
            observations.append({
                "date": date_str,
                "pass_rate": pass_rate,
                "passed": passed,
                "total": total,
                "threshold": threshold,
                "status": status,
                "raw_section": section_content
            })
            
        except Exception as e:
            print(f"⚠️ 日付 {date_str} の解析エラー: {e}")
            continue
    
    return observations

def load_shadow_evaluations() -> Dict[str, Any]:
    """Shadow評価結果を読み込み"""
    
    shadow_files = list(Path("out").glob("shadow_0_7*.json"))
    if not shadow_files:
        print("⚠️ Shadow評価ファイルが見つかりません")
        return {}
    
    # 最新のファイルを使用
    latest_file = max(shadow_files, key=lambda x: x.stat().st_mtime)
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            shadow_data = json.load(f)
        
        shadow_eval = shadow_data.get("shadow_evaluation", {})
        return {
            "shadow_pass_rate": shadow_eval.get("shadow_pass_rate", 0),
            "flaky_rate": shadow_eval.get("flaky_rate", 0),
            "new_fail_ratio": shadow_eval.get("new_fail_ratio", 0),
            "root_cause_top3": shadow_eval.get("root_cause_top3", []),
            "file": str(latest_file)
        }
        
    except Exception as e:
        print(f"❌ Shadow評価読み込みエラー: {e}")
        return {}

def evaluate_canary_window(days: int) -> Dict[str, Any]:
    """カナリア週ウィンドウの評価"""
    
    print(f"📊 カナリア週{days}日ウィンドウ評価開始")
    
    # 観測ログ解析
    observations = parse_observation_log()
    if not observations:
        return {
            "error": "観測データが見つかりません",
            "decision": "insufficient_data"
        }
    
    # 指定期間内のデータをフィルタ
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_observations = []
    
    for obs in observations:
        obs_date = datetime.strptime(obs["date"], "%Y-%m-%d")
        if obs_date >= cutoff_date:
            recent_observations.append(obs)
    
    if not recent_observations:
        return {
            "error": f"過去{days}日間のデータが見つかりません",
            "decision": "insufficient_data"
        }
    
    print(f"📈 評価対象: {len(recent_observations)}件の観測データ")
    
    # メトリクス集計
    pass_rates = [obs["pass_rate"] for obs in recent_observations]
    avg_pass_rate = sum(pass_rates) / len(pass_rates)
    min_pass_rate = min(pass_rates)
    
    # Shadow評価データ
    shadow_data = load_shadow_evaluations()
    avg_flaky_rate = shadow_data.get("flaky_rate", 0) * 100  # パーセント変換
    avg_new_fail_ratio = shadow_data.get("new_fail_ratio", 0) * 100
    
    # 判定条件
    conditions = {
        "pass_rate_ok": avg_pass_rate >= 85,
        "flaky_rate_ok": avg_flaky_rate < 5.0,
        "new_fail_ratio_ok": avg_new_fail_ratio <= 60.0,
        "min_pass_rate_ok": min_pass_rate >= 80  # 最低基準
    }
    
    all_conditions_met = all(conditions.values())
    decision = "promote" if all_conditions_met else "continue_canary"
    
    # 結果サマリー
    result = {
        "timestamp": datetime.now().isoformat(),
        "evaluation_period": {
            "days": days,
            "start_date": cutoff_date.strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d"),
            "observations_count": len(recent_observations)
        },
        "metrics": {
            "avg_pass_rate": round(avg_pass_rate, 1),
            "min_pass_rate": min_pass_rate,
            "avg_flaky_rate": round(avg_flaky_rate, 2),
            "avg_new_fail_ratio": round(avg_new_fail_ratio, 1),
            "shadow_pass_rate": shadow_data.get("shadow_pass_rate", 0)
        },
        "conditions": conditions,
        "decision": decision,
        "decision_reason": generate_decision_reason(conditions, avg_pass_rate, avg_flaky_rate, avg_new_fail_ratio),
        "observations": recent_observations,
        "shadow_data": shadow_data,
        "root_cause_top3": shadow_data.get("root_cause_top3", [])
    }
    
    return result

def generate_decision_reason(conditions: Dict[str, bool], pass_rate: float, flaky_rate: float, new_fail_ratio: float) -> str:
    """判定理由の生成"""
    
    if all(conditions.values()):
        return f"✅ 全条件達成: 合格率{pass_rate:.1f}%≥85%, Flaky率{flaky_rate:.1f}%<5%, 新規失敗率{new_fail_ratio:.1f}%≤60%"
    
    failed_conditions = []
    if not conditions["pass_rate_ok"]:
        failed_conditions.append(f"合格率{pass_rate:.1f}%<85%")
    if not conditions["flaky_rate_ok"]:
        failed_conditions.append(f"Flaky率{flaky_rate:.1f}%≥5%")
    if not conditions["new_fail_ratio_ok"]:
        failed_conditions.append(f"新規失敗率{new_fail_ratio:.1f}%>60%")
    if not conditions["min_pass_rate_ok"]:
        failed_conditions.append("最低合格率<80%")
    
    return f"❌ 未達成条件: {', '.join(failed_conditions)}"

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Canary Window Evaluation")
    parser.add_argument("--days", type=int, default=7, help="評価期間（日数）")
    parser.add_argument("--out", type=str, default="out/canary_window.json", help="出力ファイル")
    
    args = parser.parse_args()
    
    # 評価実行
    result = evaluate_canary_window(args.days)
    
    # 結果出力
    output_file = Path(args.out)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # サマリー表示
    print(f"\n📊 カナリア週{args.days}日ウィンドウ評価結果:")
    print(f"  判定: {result['decision']}")
    print(f"  理由: {result['decision_reason']}")
    print(f"  平均合格率: {result['metrics']['avg_pass_rate']}%")
    print(f"  平均Flaky率: {result['metrics']['avg_flaky_rate']}%")
    print(f"  平均新規失敗率: {result['metrics']['avg_new_fail_ratio']}%")
    print(f"  観測データ数: {result['evaluation_period']['observations_count']}件")
    print(f"\n✅ 評価結果保存: {output_file}")
    
    # 判定結果で終了コード設定
    if result["decision"] == "promote":
        print("🚀 本採用条件達成！")
        exit(0)
    elif result["decision"] == "continue_canary":
        print("🐤 カナリア週継続")
        exit(1)
    else:
        print("❌ データ不足")
        exit(2)

if __name__ == "__main__":
    main()
