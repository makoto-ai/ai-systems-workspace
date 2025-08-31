#!/bin/bash
set -euo pipefail

# Guard wrapper: keep new Downloads/AirDrop files in place for >=24h, then route
# Usage: downloads_guard_wrapper.sh <absolute_file_path>

LOG_DIR="$HOME/ai-driven/ai-systems-workspace/logs/downloads"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/guard_$(date -u +%Y%m%d).log"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

if [ $# -lt 1 ]; then
  echo "$(ts) ERR: missing file path" | tee -a "$LOG" >&2
  exit 2
fi

FILE="$1"
if [ ! -e "$FILE" ]; then
  echo "$(ts) ERR: not found: $FILE" | tee -a "$LOG" >&2
  exit 1
fi

# Skip temp/incomplete downloads
case "${FILE,,}" in
  *.crdownload|*.download|*.part|*.partial)
    echo "$(ts) SKIP temp file: $FILE" | tee -a "$LOG"
    exit 0
  ;;
esac

# Age check (seconds since epoch)
NOW=$(date -u +%s)
MTIME=$(stat -f %m "$FILE" 2>/dev/null || stat -t %s -f %m "$FILE" 2>/dev/null || echo "$NOW")
AGE=$(( NOW - MTIME ))

# Keep in place for <24h
if [ "$AGE" -lt 86400 ]; then
  echo "$(ts) HOLD (<24h): $FILE (age=${AGE}s)" | tee -a "$LOG"
  exit 0
fi

# Route if >=24h
ROUTER="$HOME/bin/route_downloads_v2.sh"
if [ -x "$ROUTER" ]; then
  echo "$(ts) ROUTE via $ROUTER: $FILE" | tee -a "$LOG"
  "$ROUTER" "$FILE" | tee -a "$LOG"
  exit 0
fi

# Fallback: simple type-based move (no copies)
EXT_LOWER=$(echo "${FILE##*.}" | tr 'A-Z' 'a-z')
DEST_BASE="$HOME/Documents/_Inbox"
mkdir -p "$DEST_BASE"

is_image=false
case "$EXT_LOWER" in
  jpg|jpeg|png|heic|heif|gif|webp|tiff|bmp)
    is_image=true
  ;;
esac

if $is_image; then
  DEST="$DEST_BASE/Photos/$(date -u +%Y)/$(date -u +%m-%d)"
else
  DEST="$DEST_BASE/Docs/$(date -u +%Y)/$(date -u +%m-%d)"
fi
mkdir -p "$DEST"

echo "$(ts) ROUTE fallback mv -> $DEST: $FILE" | tee -a "$LOG"
mv -n "$FILE" "$DEST/" 2>>"$LOG" || {
  echo "$(ts) ERR move failed: $FILE" | tee -a "$LOG" >&2
  exit 1
}
echo "$(ts) DONE: $DEST/$(basename "$FILE")" | tee -a "$LOG"


