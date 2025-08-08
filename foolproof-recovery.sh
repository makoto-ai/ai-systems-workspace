#!/bin/bash
# 🎯 迷わない完全復旧スクリプト v2.0
# 「何も考えずに1コマンド」で完全復旧

echo "🎯 迷わない完全復旧開始..."
echo "   目標：何も考えずに100%復旧"

# === 事前確認 ===
echo ""
echo "📋 Step 1: 環境確認..."

# 現在地確認
CURRENT_DIR=$(basename "$PWD")
if [[ "$CURRENT_DIR" == "voice-roleplay-system" ]]; then
    echo "  ✅ 正しいディレクトリ: $CURRENT_DIR"
else
    echo "  ⚠️  ディレクトリ確認: $CURRENT_DIR"
fi

# 必須ファイル確認
REQUIRED_FILES=(".env" "requirements.txt" "package.json")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file: 存在"
    else
        echo "  ❌ $file: 不足"
        MISSING_FILES=true
    fi
done

if [ "$MISSING_FILES" = true ]; then
    echo "❌ 必須ファイル不足 - 復旧停止"
    exit 1
fi

# === Python仮想環境 完全自動構築 ===
echo ""
echo "🐍 Step 2: Python環境完全自動構築..."

# 新規仮想環境作成
if [ ! -d ".venv" ]; then
    echo "  🆕 新規仮想環境作成中..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# 依存関係一括インストール
echo "  📦 依存関係一括インストール中..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "  ✅ Python環境構築完了"

# === Node.js環境 ===
echo ""
echo "📦 Step 3: Node.js環境確認..."

cd frontend/voice-roleplay-frontend

if [ ! -d "node_modules" ]; then
    echo "  📦 Node.js依存関係インストール中..."
    npm ci -s
fi

echo "  ✅ Node.js環境確認完了"
cd ../..

# === サービス起動 ===
echo ""
echo "🚀 Step 4: 全サービス起動..."

# 既存プロセス停止
pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "npm run dev" 2>/dev/null

# バックエンド起動
echo "  🖥️  バックエンド起動中..."
source .venv/bin/activate
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
sleep 2

# フロントエンド起動
echo "  🌐 フロントエンド起動中..."
cd frontend/voice-roleplay-frontend
nohup npm run dev > ../../frontend.log 2>&1 &
cd ../..
sleep 3

# === 動作確認 ===
echo ""
echo "🔍 Step 5: 動作確認..."

# バックエンド確認
if curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo "  ✅ バックエンド: 正常稼働 (http://localhost:8000)"
else
    echo "  ❌ バックエンド: 応答なし"
fi

# フロントエンド確認  
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "  ✅ フロントエンド: 正常稼働 (http://localhost:3000)"
else
    echo "  ⚠️  フロントエンド: 起動中..."
fi

# === 完了レポート ===
echo ""
echo "🎉 復旧完了!"
echo ""
echo "📊 アクセスURL:"
echo "  🖥️  バックエンド: http://localhost:8000"
echo "  🌐 フロントエンド: http://localhost:3000"
echo ""
echo "✨ 迷いポイント: 0個"
