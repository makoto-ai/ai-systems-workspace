#!/usr/bin/env python3
"""
Acceptance Gate for PRs

Criteria (Target threshold = 0.72):
- Pass improvement: weighted_pass_rate@0.72 increases by >= +1.0pp OR
- New failures reduction: new_fail_ratio@0.72 decreases by >= 1.0pp
- And no regressions vs previous commit (weighted_pass_rate not down, new_fail_ratio not up)

Inputs:
- out/shadow_grid.json (current PR run via runner)
- out/prev_shadow_grid.json (baseline from main/history) [optional]
- out/kpi_history.jsonl (fallback for previous metrics)

Exit codes:
- 0: Accepted
- 2: Warning only (data-collection label suggested)
- 1: Rejected (criteria not met)
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, Optional

TARGET = "0.72"
IMPROVE_PP = 1.0


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def extract_metrics_from_shadow(report: Dict[str, Any], threshold: str) -> Optional[Dict[str, float]]:
    m = report.get("multi_shadow_evaluation", {}).get("thresholds", {})
    t = m.get(threshold)
    if not t:
        return None
    return {
        "pass_rate": float(t.get("weighted_pass_rate", t.get("shadow_pass_rate", 0.0))),
        "new_fail": float(t.get("new_fail_ratio", 1.0)) * 100.0,
    }


def load_previous_metrics() -> Optional[Dict[str, float]]:
    # Prefer explicit previous shadow grid snapshot
    prev = load_json(Path("out/prev_shadow_grid.json"))
    if prev:
        m = extract_metrics_from_shadow(prev, TARGET)
        if m:
            return m

    # Fallback: use last entry from KPI history if present (approximation)
    hist = Path("out/kpi_history.jsonl")
    if hist.exists():
        try:
            lines = hist.read_text(encoding="utf-8").strip().splitlines()
            if lines:
                last = json.loads(lines[-1])
                return {
                    "pass_rate": float(last.get("enhanced_rate", last.get("baseline_rate", 0.0))),
                    "new_fail": 100.0,  # unknown -> neutral worst; forces relying on shadow prev if available
                }
        except Exception:
            pass
    return None


def decide(current: Dict[str, float], previous: Optional[Dict[str, float]]) -> Dict[str, Any]:
    cur_pass = current["pass_rate"]
    cur_new = current["new_fail"]

    prev_pass = previous["pass_rate"] if previous else None
    prev_new = previous["new_fail"] if previous else None

    improvements = []
    regressions = []

    if prev_pass is not None:
        delta_pass = cur_pass - prev_pass
        if delta_pass >= IMPROVE_PP:
            improvements.append(f"Pass +{delta_pass:.1f}pp")
        elif delta_pass < 0:
            regressions.append(f"Pass -{abs(delta_pass):.1f}pp")

    if prev_new is not None and prev_new < 100.0:  # only if known
        delta_new = prev_new - cur_new
        if delta_new >= IMPROVE_PP:
            improvements.append(f"New -{delta_new:.1f}pp")
        elif delta_new < 0:
            regressions.append(f"New +{abs(delta_new):.1f}pp")

    accepted = False
    reason = ""
    if improvements and not regressions:
        # any improvement path qualifies
        accepted = True
        reason = ", ".join(improvements)
    else:
        reason = ("; ".join(regressions) or "No measurable improvement")

    return {
        "accepted": accepted,
        "improvements": improvements,
        "regressions": regressions,
        "reason": reason,
        "current": current,
        "previous": previous,
    }


def main() -> int:
    cur = load_json(Path("out/shadow_grid.json"))
    if not cur:
        print("❌ acceptance_gate: out/shadow_grid.json missing")
        return 2

    cur_metrics = extract_metrics_from_shadow(cur, TARGET)
    if not cur_metrics:
        print(f"❌ acceptance_gate: threshold {TARGET} missing in report")
        return 2

    prev_metrics = load_previous_metrics()
    decision = decide(cur_metrics, prev_metrics)

    print("📌 Acceptance Gate @0.72")
    print(f"  current pass={decision['current']['pass_rate']:.1f}% new={decision['current']['new_fail']:.1f}%")
    if decision["previous"]:
        print(f"  previous pass={decision['previous']['pass_rate']:.1f}% new={decision['previous']['new_fail']:.1f}%")
    if decision["improvements"]:
        print("  improvements:", ", ".join(decision["improvements"]))
    if decision["regressions"]:
        print("  regressions:", ", ".join(decision["regressions"]))

    if decision["accepted"]:
        print("✅ Acceptance criteria met:", decision["reason"])
        return 0
    else:
        print("🛑 Acceptance criteria not met:", decision["reason"])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


