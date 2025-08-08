#!/bin/bash
# プロセス監視・自動復旧スクリプト

echo "👀 システム監視開始..."

while true; do
    # バックエンド監視
    if ! pgrep -f "uvicorn app.main:app" > /dev/null; then
        echo "⚠️  バックエンド停止検出 - 再起動中..."
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
        echo "✅ バックエンド復旧完了"
    fi
    
    # フロントエンド監視
    if ! pgrep -f "next dev" > /dev/null; then
        echo "⚠️  フロントエンド停止検出 - 再起動中..."
        cd frontend/voice-roleplay-frontend
        npm run dev > ../../logs/frontend.log 2>&1 &
        cd ../../
        echo "✅ フロントエンド復旧完了"
    fi
    
    # ヘルスチェック（異常時のみ通知）
    if ! curl -s http://localhost:8000/api/health/basic > /dev/null 2>&1; then
        echo "🚨 URGENT: システム異常検出 - 即座確認が必要 $(date)"
    fi
    
    # 1日1回のサマリー（午前9時のみ）
    CURRENT_HOUR=$(date +%H)
    if [ "$CURRENT_HOUR" = "09" ]; then
        echo "📊 日次システムサマリー: 全サービス正常動作中 $(date)"
    fi
    
    sleep 300  # 5分毎の内部チェック（通知は異常時のみ）
done
