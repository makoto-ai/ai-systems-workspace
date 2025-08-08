# 監視停止
if [ -f .monitor.pid ]; then
    MONITOR_PID=$(cat .monitor.pid)
    kill $MONITOR_PID 2>/dev/null && echo "🛑 監視停止完了 (PID: $MONITOR_PID)"
    rm .monitor.pid
else
    echo "ℹ️  監視プロセスは動作していません"
fi

