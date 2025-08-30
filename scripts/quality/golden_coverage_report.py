#!/usr/bin/env python3
"""
Golden被覆と改善率の簡易レポート出力
"""

import json
from pathlib import Path
from typing import Dict


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
        "improvement_pp": 0.0,
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
        metrics["improvement_pp"] = enh_rate - base_rate
    return metrics


def main():
    cov = compute_golden_coverage()
    print("📊 Golden Coverage Summary")
    print("cases_total:", cov["cases_total"]) 
    print("baseline_pass:", cov["baseline_pass"]) 
    print("enhanced_pass:", cov["enhanced_pass"]) 
    print("improvement_pp:", f"{cov['improvement_pp']:.1f}pp")


if __name__ == "__main__":
    main()


