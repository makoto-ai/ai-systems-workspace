#!/bin/bash

# 🔐 Vaultからシークレットを読み込むスクリプト
# 使用方法: source scripts/load_secrets.sh

echo "🔐 Loading secrets from Vault..."

# Vaultからシークレットを取得して環境変数に設定
export $(vault kv get -format=json secret/ai-systems | jq -r '.data.data | to_entries | map("\(.key)=\(.value)") | .[]')

# 読み込み確認
echo "✅ Secrets loaded successfully"
echo "📋 Available environment variables:"
echo "  - CLAUDE_API_KEY: ${CLAUDE_API_KEY:0:10}..."
echo "  - OPENAI_API_KEY: ${OPENAI_API_KEY:0:10}..."
echo "  - WHISPERX_ENDPOINT: ${WHISPERX_ENDPOINT}" 