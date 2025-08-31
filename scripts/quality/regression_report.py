#!/usr/bin/env python3
"""
Failure clustering & slice KPI summary (lightweight)
"""

import json
from pathlib import Path
from collections import Counter, defaultdict


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def main():
    out = Path("out")
    new_fails = load_json(out / "new_fails.json") or {}
    shadow = load_json(out / "enhanced_golden_test_model_optimization.json") or {}

    # Simple clustering by tag or case_id
    cases = new_fails.get("cases", [])
    by_tag = Counter(c.get("tag", "unknown") for c in cases)
    by_file = Counter(c.get("file", "unknown") for c in cases)

    print("📌 Regression Clustering (Top)\n===============================")
    for k, v in by_tag.most_common(5):
        print(f"  tag={k}: {v}")
    for k, v in by_file.most_common(5):
        print(f"  file={k}: {v}")

    # Slice KPI (critical vs docs)
    baseline = shadow.get("baseline", {}).get("cases", [])
    enh = shadow.get("enhanced", {}).get("cases", [])
    def pass_rate(cases):
        if not cases:
            return 0.0
        return 100.0 * sum(1 for c in cases if c.get("baseline_pass") or c.get("enhanced_pass")) / len(cases)

    print("\n📊 Slice KPI\n===========")
    print(f"  baseline_pass_rate: {pass_rate(baseline):.1f}%")
    print(f"  enhanced_pass_rate: {pass_rate(enh):.1f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


