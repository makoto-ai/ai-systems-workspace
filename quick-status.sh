#!/bin/bash
# システム状況確認スクリプト

echo "📊 システム状況確認..."
echo "================================"

# プロセス確認（hybrid優先）
if pgrep -f "main_hybrid:app" > /dev/null; then
    echo "✅ バックエンド: 稼働中 (hybrid)"
elif pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo "✅ バックエンド: 稼働中 (uvicorn)"
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
# backend health: try /health then fallback to /api/health/basic
if curl -sS -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null | grep -q "^200$"; then
  echo " - バックエンドAPI: OK"
else
  if curl -sS -o /dev/null -w "%{http_code}" http://localhost:8000/api/health/basic 2>/dev/null | grep -q "^200$"; then
    echo " - バックエンドAPI: OK"
  else
    echo " - バックエンドAPI: NG"
  fi
fi

curl -s http://localhost:3000 > /dev/null 2>&1 && echo " - フロントエンド: OK" || echo " - フロントエンド: NG"

echo ""
echo "🎯 アクセスURL:"
echo " - バックエンド: http://localhost:8000"
echo " - フロントエンド: http://localhost:3000"
echo " - API仕様: http://localhost:8000/docs"
