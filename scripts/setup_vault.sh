#!/bin/bash
# Vault連携セットアップ - セキュリティ強化

set -e

# ログ設定
LOG_FILE="logs/vault_setup.log"
mkdir -p logs

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Vault CLI インストール確認
check_vault() {
    if command -v vault &> /dev/null; then
        log "✅ Vault CLI インストール済み"
        return 0
    else
        log "❌ Vault CLI がインストールされていません"
        log "📥 インストール方法:"
        log "   brew install vault"
        return 1
    fi
}

# Vault サーバー起動
start_vault() {
    log "🚀 Vault サーバー起動開始"
    
    # Vault設定ファイル作成
    cat > vault_config.json << EOF
{
  "storage": {
    "file": {
      "path": "./vault/data"
    }
  },
  "listener": {
    "tcp": {
      "address": "0.0.0.0:8200",
      "tls_disable": true
    }
  },
  "ui": true,
  "disable_mlock": true
}
EOF
    
    # データディレクトリ作成
    mkdir -p vault/data
    
    # Vault起動
    vault server -config=vault_config.json &
    VAULT_PID=$!
    
    # 起動待機
    sleep 5
    
    # 初期化
    vault operator init -key-shares=1 -key-threshold=1 -format=json > vault_init.json
    
    # ルートトークン取得
    ROOT_TOKEN=$(jq -r '.root_token' vault_init.json)
    UNSEAL_KEY=$(jq -r '.keys[0]' vault_init.json)
    
    # アンシール
    vault operator unseal $UNSEAL_KEY
    
    # 環境変数設定
    export VAULT_ADDR='http://localhost:8200'
    export VAULT_TOKEN=$ROOT_TOKEN
    
    log "✅ Vault サーバー起動完了"
    log "🔑 ルートトークン: $ROOT_TOKEN"
    log "🔐 アンシールキー: $UNSEAL_KEY"
}

# シークレット登録
setup_secrets() {
    log "🔐 シークレット登録開始"
    
    # API キー登録
    vault kv put secret/ai-systems \
        claude_api_key="${CLAUDE_API_KEY:-}" \
        openai_api_key="${OPENAI_API_KEY:-}" \
        groq_api_key="${GROQ_API_KEY:-}" \
        database_password="${DATABASE_PASSWORD:-ai_password}" \
        jwt_secret="${JWT_SECRET:-default_jwt_secret}" \
        encryption_key="${ENCRYPTION_KEY:-default_encryption_key}"
    
    # データベース設定
    vault kv put secret/database \
        postgres_user="ai_user" \
        postgres_password="${DATABASE_PASSWORD:-ai_password}" \
        postgres_db="ai_systems" \
        redis_password="${REDIS_PASSWORD:-}"
    
    # 監視設定
    vault kv put secret/monitoring \
        prometheus_admin_password="admin123" \
        grafana_admin_password="admin123" \
        alertmanager_password="alert123"
    
    log "✅ シークレット登録完了"
}

# ポリシー設定
setup_policies() {
    log "📋 ポリシー設定開始"
    
    # AI Systems ポリシー
    vault policy write ai-systems-policy - << EOF
path "secret/data/ai-systems" {
  capabilities = ["read"]
}

path "secret/data/database" {
  capabilities = ["read"]
}

path "secret/data/monitoring" {
  capabilities = ["read"]
}
EOF
    
    # トークン作成
    vault token create -policy=ai-systems-policy -format=json > ai-systems-token.json
    
    AI_TOKEN=$(jq -r '.auth.client_token' ai-systems-token.json)
    
    log "✅ ポリシー設定完了"
    log "🎫 AI Systems トークン: $AI_TOKEN"
}

# Docker Compose 統合
update_docker_compose() {
    log "🐳 Docker Compose 統合開始"
    
    # vault_config.json 作成
    cat > vault_config.json << EOF
{
  "vault": {
    "address": "http://vault:8200",
    "token": "${AI_TOKEN:-}",
    "secrets": {
      "ai-systems": "secret/data/ai-systems",
      "database": "secret/data/database",
      "monitoring": "secret/data/monitoring"
    }
  }
}
EOF
    
    log "✅ Docker Compose 統合完了"
}

# メイン実行
main() {
    log "🎯 Vault セットアップ開始"
    
    # 1. Vault CLI 確認
    check_vault || exit 1
    
    # 2. Vault サーバー起動
    start_vault
    
    # 3. シークレット登録
    setup_secrets
    
    # 4. ポリシー設定
    setup_policies
    
    # 5. Docker Compose 統合
    update_docker_compose
    
    log "🎉 Vault セットアップ完了"
    log "📊 ダッシュボード: http://localhost:8200"
    log "🔑 ルートトークン: $(jq -r '.root_token' vault_init.json)"
}

# スクリプト実行
main "$@"
