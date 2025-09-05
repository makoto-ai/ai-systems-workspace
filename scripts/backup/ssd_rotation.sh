#!/bin/bash
# SSD backup rotation with hard caps
# - Time-based cleanup: 7/30/90 days
# - Hard caps: keep newest N, ensure free >= MIN_FREE_GI and total <= MAX_TOTAL_GI
# Env overrides: MIN_FREE_GI(50), MAX_TOTAL_GI(900), KEEP_MIN(7), DRY_RUN(0/1)
set -euo pipefail
DST="/Volumes/CrucialSSD/AI-Backups/backups_migrated"
LOG="$HOME/ai-ssd-rotation.log"
DRY=${DRY_RUN:-0}
MIN_FREE_GI=${MIN_FREE_GI:-50}
MAX_TOTAL_GI=${MAX_TOTAL_GI:-900}
KEEP_MIN=${KEEP_MIN:-7}
now() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(now)] $1" | tee -a "$LOG"; }
[ -d "$DST" ] || { log "dst missing: $DST"; exit 0; }
# Helpers
get_free_gi() {
  # avail GiB for DST mount
  df -g "$DST" | tail -1 | awk '{print $4+0}' || echo 0
}
get_total_gi() {
  # total size used by DST folder in GiB (approx)
  local mib
  mib=$(du -sm "$DST" 2>/dev/null | awk '{print $1+0}')
  awk -v m="$mib" 'BEGIN{printf "%.0f", m/1024}'
}
remove_file() {
  local f="$1"
  if [ "$DRY" = 1 ]; then
    echo "DRY rm $f"
  else
    rm -f -- "$f" || true
  fi
}
# 1) 7/30/90日規則
find "$DST" -type f \( -name '*.log' -o -name '*.pyc' -o -name '*.tmp' \) -mtime +7 -print | while IFS= read -r f; do remove_file "$f"; done
find "$DST" -type f ! -name '*.tar.gz' -mtime +30 -print | while IFS= read -r f; do remove_file "$f"; done
# 90日超の.tar.gz（最新KEEP_MINは常に保護）
idx=0
ls -1t "$DST"/*.tar.gz 2>/dev/null | while IFS= read -r f; do
  idx=$((idx+1))
  [ $idx -le $KEEP_MIN ] && continue
  # file mtime vs 90 days ago
  ts_file=$(date -r "$f" +%s 2>/dev/null || stat -f %m "$f")
  ts_cut=$(date -v-90d +%s 2>/dev/null || python3 - <<PY
import time; print(int(time.time()-90*24*3600))
PY
)
  if [ "$ts_file" -lt "$ts_cut" ]; then remove_file "$f"; fi
done
# 2) ハードキャップ: free >= MIN_FREE_GI & total <= MAX_TOTAL_GI になるまで古い順で削除（最新KEEP_MIN保護）
free_gi=$(get_free_gi)
used_gi=$(get_total_gi)
log "pre-check: free=${free_gi}Gi, used=${used_gi}Gi"
if [ "$free_gi" -lt "$MIN_FREE_GI" ] || [ "$used_gi" -gt "$MAX_TOTAL_GI" ]; then
  log "hard-cap engaged (min_free=${MIN_FREE_GI}Gi, max_total=${MAX_TOTAL_GI}Gi, keep_min=${KEEP_MIN})"
  # build list oldest-first, skipping newest KEEP_MIN
  list=$(ls -1t "$DST"/*.tar.gz 2>/dev/null | tail -r 2>/dev/null || tac <(ls -1t "$DST"/*.tar.gz 2>/dev/null) 2>/dev/null || true)
  # skip newest KEEP_MIN by dropping first KEEP_MIN from newest list
  newest=$(ls -1t "$DST"/*.tar.gz 2>/dev/null || true)
  keep_set=" $(echo "$newest" | awk 'NR<=k{print}' k=${KEEP_MIN} | tr '\n' ' ') "
  for f in $list; do
    # skip if in keep_set
    case "$keep_set" in *" $f "*) continue;; esac
    remove_file "$f"
    free_gi=$(get_free_gi)
    used_gi=$(get_total_gi)
    log "deleted: $(basename "$f") => free=${free_gi}Gi, used=${used_gi}Gi"
    if [ "$free_gi" -ge "$MIN_FREE_GI" ] && [ "$used_gi" -le "$MAX_TOTAL_GI" ]; then
      log "hard-cap satisfied"; break
    fi
  done
fi
log "rotation done"
