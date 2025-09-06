#!/bin/bash
# 自動監視開始
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
"$DIR"/monitor-services.sh &
MONITOR_PID=$!
echo "📡 バックグラウンド監視開始 (PID: $MONITOR_PID)"
echo $MONITOR_PID > "$DIR"/.monitor.pid

