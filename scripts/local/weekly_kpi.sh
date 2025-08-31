#!/bin/bash
set -euo pipefail

# Weekly KPI local runner
export TZ=Asia/Tokyo
BASE="/Users/araimakoto/ai-driven/ai-systems-workspace"
cd "$BASE"

mkdir -p "$BASE/logs/kpi" "$BASE/logs/cron" "$BASE/out"

# Activate venv if available
if [ -f "$BASE/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$BASE/.venv/bin/activate"
fi

TS=$(date '+%Y%m%d-%H%M%S')

echo "[KPI] Run started at $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

# 1) Golden coverage (appends to out/kpi_history.jsonl)
python3 scripts/quality/golden_coverage_report.py | tee "logs/kpi/${TS}_golden_report.txt"

# 2) Dynamic gates summary
python3 scripts/quality/dynamic_gates.py --summary | tee "logs/kpi/${TS}_gate_summary.txt"

# 3) Regression clustering & slice KPI (non-fatal)
python3 scripts/quality/regression_report.py | tee "logs/kpi/${TS}_regression_report.txt" || true

echo "[KPI] Run finished at $(date -u +"%Y-%m-%dT%H:%M:%SZ")"


