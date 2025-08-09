#!/bin/bash

# 🔐 Vault初期セットアップスクリプト
# 使用方法: ./scripts/setup_vault.sh

set -e

echo "🔐 Vault初期セットアップ開始..."

# Vault CLI インストール確認
if ! command -v vault &> /dev/null; then
    echo "📥 Vault CLI インストール中..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install vault
    else
        # Linux
        curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
        sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
        sudo apt-get update && sudo apt-get install vault
    fi
fi

echo "✅ Vault CLI インストール完了"

# Vaultサーバー起動確認
if ! curl -f http://localhost:8200/v1/sys/health > /dev/null 2>&1; then
    echo "🚀 Vaultサーバー起動中..."
    vault server -dev &
    sleep 5
fi

echo "✅ Vaultサーバー稼働確認"

# シークレット登録
echo "📝 シークレット登録中..."
vault kv put secret/ai-systems \
    CLAUDE_API_KEY="${CLAUDE_API_KEY:-your_claude_key}" \
    OPENAI_API_KEY="${OPENAI_API_KEY:-your_openai_key}" \
    GROQ_API_KEY="${GROQ_API_KEY:-your_groq_key}" \
    WHISPERX_ENDPOINT="${WHISPERX_ENDPOINT:-http://localhost:8000}" \
    DATABASE_PASSWORD="${DATABASE_PASSWORD:-ai_password}" \
    JWT_SECRET="${JWT_SECRET:-default_jwt_secret}" \
    ENCRYPTION_KEY="${ENCRYPTION_KEY:-default_encryption_key}"

echo "✅ シークレット登録完了"

# 読み込みテスト
echo "🧪 シークレット読み込みテスト..."
source scripts/load_secrets.sh

echo "🎉 Vault初期セットアップ完了！"
echo "📋 使用方法:"
echo "   source scripts/load_secrets.sh  # シークレット読み込み"
echo "   docker-compose up -d            # アプリケーション起動"
