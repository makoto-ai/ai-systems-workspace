#!/bin/bash
set -euo pipefail
DST="/Volumes/CrucialSSD/AI-Backups/backups_migrated"
LOG="$HOME/ai-ssd-rotation.log"
DRY=${DRY_RUN:-0}
now() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(now)] $1" | tee -a "$LOG"; }
[ -d "$DST" ] || { log "dst missing: $DST"; exit 0; }
# 7日未更新の.log/.pyc/.tmpを削除
find "$DST" -type f \( -name '*.log' -o -name '*.pyc' -o -name '*.tmp' \) -mtime +7 -print | while IFS= read -r f; do [ "$DRY" = 1 ] && echo "DRY rm $f" || rm -f "$f"; done
# 30日超の一時・中間生成物を削除（*.tar.gz除外）
find "$DST" -type f ! -name '*.tar.gz' -mtime +30 -print | while IFS= read -r f; do [ "$DRY" = 1 ] && echo "DRY rm $f" || rm -f "$f"; done
# 90日超の古いアーカイブを削除（最新7個は常に保護）
keep=7
idx=0
ls -1t "$DST"/*.tar.gz 2>/dev/null | while IFS= read -r f; do
  idx=$((idx+1))
  [ $idx -le $keep ] && continue
  # 90日より古いもののみ
  ts_file=$(date -r "$f" +%s 2>/dev/null || stat -f %m "$f")
  ts_cut=$(date -v-90d +%s 2>/dev/null || python3 - <<PY
import time; print(int(time.time()-90*24*3600))
PY
)
  if [ "$ts_file" -lt "$ts_cut" ]; then
    [ "$DRY" = 1 ] && echo "DRY rm $f" || rm -f "$f"
  fi
done
log "rotation done"
