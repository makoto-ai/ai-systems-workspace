#!/bin/bash
set -euo pipefail
PROJECT_ROOT="/Users/araimakoto/ai-driven/ai-systems-workspace"
SSD_MOUNT="/Volumes/CrucialSSD"
LOCK_FILE="/tmp/ssd_prepare.lock"
DEBOUNCE_SEC=60
now=$(date +%s)
if [ -f "$LOCK_FILE" ]; then
  last=$(cat "$LOCK_FILE" 2>/dev/null || echo 0)
  if [ "$((now - last))" -lt "$DEBOUNCE_SEC" ]; then exit 0; fi
fi
echo "$now" > "$LOCK_FILE"
if [ ! -d "$SSD_MOUNT" ] || [ ! -w "$SSD_MOUNT" ]; then
  cd "$PROJECT_ROOT"; ./scripts/log_router.sh dev "SSD prepare: SSD not ready" || true; exit 0; fi
mkdir -p "$SSD_MOUNT/Documents/Logs/DevLogs" "$SSD_MOUNT/Documents/Logs/ProdLogs"
cd "$PROJECT_ROOT"; ./scripts/sync_logs_to_ssd.sh || true
./scripts/log_router.sh dev "SSD attached: prepared logging directories and synced"
