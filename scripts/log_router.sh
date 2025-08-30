#!/bin/bash
set -euo pipefail
CHANNEL="${1:-dev}"
MESSAGE="${2:-}"
SSD_ROOT="/Volumes/CrucialSSD/Documents/Logs"
LOCAL_ROOT="$HOME/Documents/Logs"
case "$CHANNEL" in
  dev|Dev|DEV) GROUP="DevLogs" ;;
  prod|Prod|PROD) GROUP="ProdLogs" ;;
  *) GROUP="DevLogs" ;;
 esac
DATE_DIR="$(date +%Y-%m-%d)"
LOCAL_DIR="$LOCAL_ROOT/$GROUP/$DATE_DIR"
SSD_DIR="$SSD_ROOT/$GROUP/$DATE_DIR"
mkdir -p "$LOCAL_DIR"
logline="[$(date '+%Y-%m-%d %H:%M:%S')] $(hostname -s) $CHANNEL: $MESSAGE"
printf "%s
" "$logline" >> "$LOCAL_DIR/activity.log"
if [ -d "/Volumes/CrucialSSD" ] && [ -w "/Volumes/CrucialSSD" ]; then
  mkdir -p "$SSD_DIR"
  printf "%s
" "$logline" >> "$SSD_DIR/activity.log"
fi
