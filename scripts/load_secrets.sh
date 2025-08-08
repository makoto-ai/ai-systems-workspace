#!/bin/bash

# 🔐 Vault Secrets Loader
# 作成日: 2025-08-04
# 目的: Vaultからシークレットを読み込み、環境変数として設定

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

# Vault接続チェック
check_vault_connection() {
    log_info "Vault接続をチェック中..."
    
    if ! command -v vault &> /dev/null; then
        log_error "Vault CLIがインストールされていません"
        log_info "インストール方法: https://developer.hashicorp.com/vault/docs/install"
        exit 1
    fi
    
    # Vaultサーバー接続チェック
    if ! vault status &> /dev/null; then
        log_warning "Vaultサーバーに接続できません"
        log_info "ローカルVaultを起動中..."
        vault server -dev &
        sleep 5
    fi
    
    log_success "Vault接続確認完了"
}

# シークレット読み込み
load_secrets() {
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
        log_error "シークレットが見つかりません: $SECRET_PATH"
        log_info "シークレットを登録してください:"
        echo "vault kv put $SECRET_PATH \\"
        echo "  CLAUDE_API_KEY=\"sk-xxxxxxxxx\" \\"
        echo "  OPENAI_API_KEY=\"sk-yyyyyyyyy\" \\"
        echo "  GROQ_API_KEY=\"gsk-xxxxxxxxx\" \\"
        echo "  WHISPERX_ENDPOINT=\"http://localhost:8000\""
        exit 1
    fi
}

# シークレット登録
register_secrets() {
    log_info "シークレットを登録中..."
    
    # デフォルトシークレット（実際の値に置き換えてください）
    vault kv put secret/ai-systems \
        CLAUDE_API_KEY="sk-xxxxxxxxx" \
        OPENAI_API_KEY="sk-yyyyyyyyy" \
        GROQ_API_KEY="gsk-xxxxxxxxx" \
        WHISPERX_ENDPOINT="http://localhost:8000" \
        DATABASE_URL="postgresql://user:pass@localhost:5432/ai_systems" \
        REDIS_URL="redis://localhost:6379" \
        JWT_SECRET="your-jwt-secret-key" \
        ENCRYPTION_KEY="your-encryption-key"
    
    log_success "シークレットを登録しました"
}

# シークレット更新
update_secret() {
    local key=$1
    local value=$2
    
    log_info "シークレットを更新中: $key"
    
    # 現在のシークレットを取得
    current_secrets=$(vault kv get -format=json secret/ai-systems | jq -r '.data.data')
    
    # 新しい値を追加/更新
    updated_secrets=$(echo "$current_secrets" | jq --arg key "$key" --arg value "$value" '. + {($key): $value}')
    
    # Vaultに保存
    echo "$updated_secrets" | vault kv put secret/ai-systems -
    
    log_success "シークレットを更新しました: $key"
}

# シークレット削除
delete_secret() {
    local key=$1
    
    log_info "シークレットを削除中: $key"
    
    # 現在のシークレットを取得
    current_secrets=$(vault kv get -format=json secret/ai-systems | jq -r '.data.data')
    
    # 指定されたキーを削除
    updated_secrets=$(echo "$current_secrets" | jq --arg key "$key" 'del(.[$key])')
    
    # Vaultに保存
    echo "$updated_secrets" | vault kv put secret/ai-systems -
    
    log_success "シークレットを削除しました: $key"
}

# シークレット一覧表示
list_secrets() {
    log_info "シークレット一覧を表示中..."
    
    if vault kv get secret/ai-systems &> /dev/null; then
        vault kv get -format=json secret/ai-systems | jq -r '.data.data | keys[]' | while read key; do
            echo "  - $key"
        done
    else
        log_warning "シークレットが見つかりません"
    fi
}

# ヘルプ表示
show_help() {
    echo "🔐 Vault Secrets Loader"
    echo ""
    echo "使用方法:"
    echo "  ./scripts/load_secrets.sh [コマンド]"
    echo ""
    echo "コマンド:"
    echo "  load        シークレットを読み込み（デフォルト）"
    echo "  register    デフォルトシークレットを登録"
    echo "  update KEY VALUE  シークレットを更新"
    echo "  delete KEY  シークレットを削除"
    echo "  list        シークレット一覧を表示"
    echo "  help        このヘルプを表示"
    echo ""
    echo "例:"
    echo "  ./scripts/load_secrets.sh load"
    echo "  ./scripts/load_secrets.sh update CLAUDE_API_KEY sk-new-key"
    echo "  ./scripts/load_secrets.sh list"
}

# メイン処理
main() {
    local command=${1:-load}
    
    case $command in
        "load")
            check_vault_connection
            load_secrets
            log_success "シークレット読み込み完了"
            ;;
        "register")
            check_vault_connection
            register_secrets
            ;;
        "update")
            if [ -z "$2" ] || [ -z "$3" ]; then
                log_error "使用方法: update KEY VALUE"
                exit 1
            fi
            check_vault_connection
            update_secret "$2" "$3"
            ;;
        "delete")
            if [ -z "$2" ]; then
                log_error "使用方法: delete KEY"
                exit 1
            fi
            check_vault_connection
            delete_secret "$2"
            ;;
        "list")
            check_vault_connection
            list_secrets
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "不明なコマンド: $command"
            show_help
            exit 1
            ;;
    esac
}

# スクリプト実行
main "$@" 