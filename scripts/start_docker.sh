#!/bin/bash

# 🐳 Docker Startup Script
# 作成日: 2025-08-04
# 目的: Dockerコンテナ内でのアプリケーション起動

set -e

# カラー出力設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# ログ関数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_secret() {
    echo -e "${PURPLE}🔐 $1${NC}"
}

# Vault接続設定
setup_vault() {
    log_info "Vault接続を設定中..."
    
    # Vaultアドレス設定
    export VAULT_ADDR="${VAULT_ADDR:-http://vault:8200}"
    export VAULT_TOKEN="${VAULT_TOKEN:-dev-token}"
    
    # Vault接続待機
    log_info "Vaultサーバーの起動を待機中..."
    until vault status &> /dev/null; do
        sleep 2
    done
    
    log_success "Vault接続完了"
}

# シークレット読み込み
load_secrets_from_vault() {
    log_info "Vaultからシークレットを読み込み中..."
    
    # シークレットパス
    SECRET_PATH="secret/ai-systems"
    
    # Vaultからシークレットを取得
    if vault kv get "$SECRET_PATH" &> /dev/null; then
        log_success "シークレットを取得しました: $SECRET_PATH"
        
        # 環境変数として設定
        export $(vault kv get -format=json "$SECRET_PATH" | jq -r '.data.data | to_entries | map("\(.key)=\(.value)") | .[]')
        
        # 設定された環境変数を表示（値は隠す）
        log_secret "設定された環境変数:"
        vault kv get -format=json "$SECRET_PATH" | jq -r '.data.data | keys[]' | while read key; do
            echo "  - $key=***"
        done
        
    else
        log_warning "シークレットが見つかりません: $SECRET_PATH"
        log_info "デフォルト環境変数を使用します"
    fi
}

# データベース接続確認
check_database() {
    log_info "データベース接続を確認中..."
    
    # PostgreSQL接続確認
    if [ -n "$DATABASE_URL" ]; then
        until python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.close()
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" 2>/dev/null; do
            log_warning "データベース接続を待機中..."
            sleep 5
        done
        log_success "データベース接続完了"
    fi
}

# Redis接続確認
check_redis() {
    log_info "Redis接続を確認中..."
    
    # Redis接続確認
    if [ -n "$REDIS_URL" ]; then
        until python -c "
import redis
import os
try:
    r = redis.from_url(os.environ['REDIS_URL'])
    r.ping()
    print('Redis connection successful')
except Exception as e:
    print(f'Redis connection failed: {e}')
    exit(1)
" 2>/dev/null; do
            log_warning "Redis接続を待機中..."
            sleep 5
        done
        log_success "Redis接続完了"
    fi
}

# アプリケーション起動
start_application() {
    log_info "アプリケーションを起動中..."
    
    # メインアプリケーション起動
    if [ -f "main_hybrid.py" ]; then
        log_info "ハイブリッドシステムを起動中..."
        exec python main_hybrid.py
    elif [ -f "youtube_script_generation_system.py" ]; then
        log_info "YouTubeスクリプト生成システムを起動中..."
        exec python youtube_script_generation_system.py
    else
        log_error "起動可能なアプリケーションが見つかりません"
        exit 1
    fi
}

# メイン処理
main() {
    echo "🐳 AI Systems Docker Startup"
    echo "============================"
    
    # Vault設定
    setup_vault
    
    # シークレット読み込み
    load_secrets_from_vault
    
    # データベース接続確認
    check_database
    
    # Redis接続確認
    check_redis
    
    # アプリケーション起動
    start_application
}

# スクリプト実行
main "$@" 