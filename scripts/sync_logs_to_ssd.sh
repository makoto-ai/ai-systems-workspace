#!/bin/bash
set -euo pipefail
SSD_ROOT="/Volumes/CrucialSSD/Documents/Logs"
LOCAL_ROOT="$HOME/Documents/Logs"
if [ ! -d "/Volumes/CrucialSSD" ] || [ ! -w "/Volumes/CrucialSSD" ]; then echo "SSD not available; skip"; exit 0; fi
mkdir -p "$SSD_ROOT"
rsync -a --exclude ".DS_Store" "$LOCAL_ROOT/" "$SSD_ROOT/"
find "$LOCAL_ROOT" -type f -mtime +30 -delete || true
find "$LOCAL_ROOT" -type d -empty -delete || true
