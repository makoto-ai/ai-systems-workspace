#!/usr/bin/env python3
"""
Golden被覆と改善率の簡易レポート出力 + 履歴保存/差分
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def compute_golden_coverage() -> Dict[str, float]:
    out = Path("out")
    metrics = {
        "cases_total": 0,
        "baseline_pass": 0,
        "enhanced_pass": 0,
        "baseline_rate": 0.0,
        "enhanced_rate": 0.0,
        "improvement_pp": 0.0,
        "timestamp": datetime.now().isoformat(),
    }
    f = out / "enhanced_golden_test_model_optimization.json"
    data = load_json(f)
    if not data:
        return metrics
    b = data.get("baseline", {})
    e = data.get("enhanced", {})
    metrics["cases_total"] = b.get("total", 0)
    metrics["baseline_pass"] = b.get("passed", 0)
    metrics["enhanced_pass"] = e.get("passed", 0)
    if metrics["cases_total"] > 0:
        base_rate = metrics["baseline_pass"] / metrics["cases_total"] * 100
        enh_rate = metrics["enhanced_pass"] / metrics["cases_total"] * 100
        metrics["baseline_rate"] = base_rate
        metrics["enhanced_rate"] = enh_rate
        metrics["improvement_pp"] = enh_rate - base_rate
    return metrics


def load_last_history(history_path: Path) -> Optional[Dict]:
    try:
        if not history_path.exists():
            return None
        lines = history_path.read_text(encoding="utf-8").strip().splitlines()
        return json.loads(lines[-1]) if lines else None
    except Exception:
        return None


def append_history(history_path: Path, entry: Dict) -> None:
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main():
    cov = compute_golden_coverage()
    hist_path = Path("out/kpi_history.jsonl")
    prev = load_last_history(hist_path)
    append_history(hist_path, cov)

    print("📊 Golden Coverage Summary")
    print("cases_total:", cov["cases_total"]) 
    print("baseline_pass:", cov["baseline_pass"]) 
    print("enhanced_pass:", cov["enhanced_pass"]) 
    print("baseline_rate:", f"{cov['baseline_rate']:.1f}%")
    print("enhanced_rate:", f"{cov['enhanced_rate']:.1f}%")
    print("improvement_pp:", f"{cov['improvement_pp']:.1f}pp")

    if prev and prev.get("cases_total"):
        diff = cov["enhanced_rate"] - prev.get("enhanced_rate", 0.0)
        print("diff_vs_prev:", f"{diff:+.1f}pp")
    else:
        print("diff_vs_prev:", "n/a")


if __name__ == "__main__":
    main()


