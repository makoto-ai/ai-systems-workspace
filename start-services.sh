#!/bin/bash
# 音声システム自動起動・監視スクリプト
set -euo pipefail

echo "🚀 音声ロールプレイシステム起動中..."

# FastAPI Backend
echo "📡 バックエンド起動中..."
mkdir -p logs
if pgrep -f "main_hybrid:app" > /dev/null; then
    echo "ℹ️  ハイブリッドが8000で稼働中のため、app.mainは起動しません"
elif ! pgrep -f "uvicorn app.main:app" > /dev/null; then
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8010 > logs/backend8010.log 2>&1 &
    echo "✅ バックエンド(app.main)起動: http://localhost:8010"
else
    echo "ℹ️  バックエンド(app.main)は既に起動中"
fi

# Next.js Frontend  
echo "🖥️  フロントエンド起動中..."
if ! pgrep -f "next dev" > /dev/null; then
    cd frontend/voice-roleplay-frontend
    npm run dev > ../../logs/frontend.log 2>&1 &
    cd ../../
    echo "✅ フロントエンド起動: http://localhost:3000"
else
    echo "ℹ️  フロントエンドは既に起動中"
fi

echo "🎉 システム起動完了！"
