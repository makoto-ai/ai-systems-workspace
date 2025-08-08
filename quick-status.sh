#!/bin/bash
# システム状況確認スクリプト

echo "📊 システム状況確認..."
echo "================================"

# プロセス確認
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo "✅ バックエンド: 稼働中"
else
    echo "❌ バックエンド: 停止中"
fi

if pgrep -f "next dev" > /dev/null; then
    echo "✅ フロントエンド: 稼働中"
else
    echo "❌ フロントエンド: 停止中"
fi

# ヘルスチェック
echo ""
echo "🔍 ヘルスチェック:"
curl -s http://localhost:8000/api/health/basic 2>/dev/null && echo " - バックエンドAPI: OK" || echo " - バックエンドAPI: NG"
curl -s http://localhost:3000 > /dev/null 2>&1 && echo " - フロントエンド: OK" || echo " - フロントエンド: NG"

echo ""
echo "🎯 アクセスURL:"
echo " - バックエンド: http://localhost:8000"
echo " - フロントエンド: http://localhost:3000"
echo " - API仕様: http://localhost:8000/docs"
