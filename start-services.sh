#!/bin/bash
# 音声システム自動起動・監視スクリプト

echo "🚀 音声ロールプレイシステム起動中..."

# FastAPI Backend
echo "📡 バックエンド起動中..."
if ! pgrep -f "uvicorn app.main:app" > /dev/null; then
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
    echo "✅ バックエンド起動: http://localhost:8000"
else
    echo "ℹ️  バックエンドは既に起動中"
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
