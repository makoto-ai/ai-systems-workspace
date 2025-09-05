# 自動監視開始
./monitor-services.sh &
MONITOR_PID=$!
echo "📡 バックグラウンド監視開始 (PID: $MONITOR_PID)"
echo $MONITOR_PID > .monitor.pid

