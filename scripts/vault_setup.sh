#!/bin/bash

# Vault統合スクリプト
# シークレット管理とセキュリティ設定

set -e

# 色付きログ関数
log_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

log_warn() {
    echo -e "\033[33m[WARN]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

log_success() {
    echo -e "\033[36m[SUCCESS]\033[0m $1"
}

# Vault初期化
init_vault() {
    log_info "Vaultを初期化中..."
    
    # Vaultが起動するまで待機
    until curl -f http://localhost:8200/v1/sys/health > /dev/null 2>&1; do
        log_warn "Vaultの起動を待機中..."
        sleep 5
    done
    
    # Vault初期化（初回のみ）
    if ! curl -f http://localhost:8200/v1/sys/init > /dev/null 2>&1; then
        log_info "Vault初期化を実行中..."
        curl -X POST http://localhost:8200/v1/sys/init \
            -H "Content-Type: application/json" \
            -d '{
                "secret_shares": 5,
                "secret_threshold": 3
            }' > vault_init.json
        
        # 初期化結果を保存
        if [ -f vault_init.json ]; then
            log_success "Vault初期化完了"
            cat vault_init.json
        else
            log_error "Vault初期化失敗"
            return 1
        fi
    else
        log_info "Vaultは既に初期化済みです"
    fi
}

# シークレットエンジン設定
setup_secret_engines() {
    log_info "シークレットエンジンを設定中..."
    
    # KVエンジン有効化
    curl -X POST http://localhost:8200/v1/sys/mounts/ai-systems \
        -H "X-Vault-Token: dev-token" \
        -H "Content-Type: application/json" \
        -d '{
            "type": "kv",
            "options": {
                "version": "2"
            }
        }' > /dev/null 2>&1 || log_warn "KVエンジン設定に失敗"
    
    log_success "シークレットエンジン設定完了"
}

# シークレット設定
setup_secrets() {
    log_info "シークレットを設定中..."
    
    # API Keys
    curl -X POST http://localhost:8200/v1/ai-systems/data/api-keys \
        -H "X-Vault-Token: dev-token" \
        -H "Content-Type: application/json" \
        -d "{
            \"data\": {
                \"claude_api_key\": \"$CLAUDE_API_KEY\",
                \"openai_api_key\": \"$OPENAI_API_KEY\",
                \"groq_api_key\": \"$GROQ_API_KEY\"
            }
        }" > /dev/null 2>&1 || log_warn "API Keys設定に失敗"
    
    # データベース認証情報
    curl -X POST http://localhost:8200/v1/ai-systems/data/database \
        -H "X-Vault-Token: dev-token" \
        -H "Content-Type: application/json" \
        -d "{
            \"data\": {
                \"postgres_password\": \"$POSTGRES_PASSWORD\",
                \"postgres_user\": \"ai_user\",
                \"postgres_db\": \"ai_systems\"
            }
        }" > /dev/null 2>&1 || log_warn "データベース認証情報設定に失敗"
    
    # Grafana認証情報
    curl -X POST http://localhost:8200/v1/ai-systems/data/grafana \
        -H "X-Vault-Token: dev-token" \
        -H "Content-Type: application/json" \
        -d "{
            \"data\": {
                \"admin_password\": \"$GRAFANA_PASSWORD\"
            }
        }" > /dev/null 2>&1 || log_warn "Grafana認証情報設定に失敗"
    
    # アプリケーション設定
    curl -X POST http://localhost:8200/v1/ai-systems/data/app-config \
        -H "X-Vault-Token: dev-token" \
        -H "Content-Type: application/json" \
        -d '{
            "data": {
                "environment": "production",
                "log_level": "INFO",
                "max_workers": 4,
                "request_timeout": 60
            }
        }' > /dev/null 2>&1 || log_warn "アプリケーション設定に失敗"
    
    log_success "シークレット設定完了"
}

# ポリシー設定
setup_policies() {
    log_info "Vaultポリシーを設定中..."
    
    # AI Systems ポリシー
    curl -X POST http://localhost:8200/v1/sys/policies/acl/ai-systems-policy \
        -H "X-Vault-Token: dev-token" \
        -H "Content-Type: application/json" \
        -d '{
            "policy": "path \"ai-systems/data/*\" { capabilities = [\"read\", \"update\"] }"
        }' > /dev/null 2>&1 || log_warn "AI Systems ポリシー設定に失敗"
    
    # 監視ポリシー
    curl -X POST http://localhost:8200/v1/sys/policies/acl/monitoring-policy \
        -H "X-Vault-Token: dev-token" \
        -H "Content-Type: application/json" \
        -d '{
            "policy": "path \"ai-systems/data/monitoring/*\" { capabilities = [\"read\"] }"
        }' > /dev/null 2>&1 || log_warn "監視ポリシー設定に失敗"
    
    log_success "Vaultポリシー設定完了"
}

# 認証方法設定
setup_auth_methods() {
    log_info "認証方法を設定中..."
    
    # AppRole認証有効化
    curl -X POST http://localhost:8200/v1/sys/auth/approle \
        -H "X-Vault-Token: dev-token" \
        -H "Content-Type: application/json" \
        -d '{
            "type": "approle"
        }' > /dev/null 2>&1 || log_warn "AppRole認証設定に失敗"
    
    # AI Systems AppRole作成
    curl -X POST http://localhost:8200/v1/auth/approle/role/ai-systems \
        -H "X-Vault-Token: dev-token" \
        -H "Content-Type: application/json" \
        -d '{
            "policies": ["ai-systems-policy"],
            "token_ttl": "1h",
            "token_max_ttl": "24h"
        }' > /dev/null 2>&1 || log_warn "AI Systems AppRole作成に失敗"
    
    log_success "認証方法設定完了"
}

# シークレット取得テスト
test_secrets() {
    log_info "シークレット取得をテスト中..."
    
    # API Keys取得テスト
    if curl -f http://localhost:8200/v1/ai-systems/data/api-keys \
        -H "X-Vault-Token: dev-token" > /dev/null 2>&1; then
        log_success "API Keys取得テスト成功"
    else
        log_error "API Keys取得テスト失敗"
        return 1
    fi
    
    # データベース認証情報取得テスト
    if curl -f http://localhost:8200/v1/ai-systems/data/database \
        -H "X-Vault-Token: dev-token" > /dev/null 2>&1; then
        log_success "データベース認証情報取得テスト成功"
    else
        log_error "データベース認証情報取得テスト失敗"
        return 1
    fi
    
    log_success "シークレット取得テスト完了"
}

# バックアップ設定
setup_backup() {
    log_info "Vaultバックアップを設定中..."
    
    # バックアップディレクトリ作成
    mkdir -p /app/backups/vault
    
    # バックアップスクリプト作成
    cat > /app/scripts/vault_backup.sh << 'EOF'
#!/bin/bash
# Vaultバックアップスクリプト

BACKUP_DIR="/app/backups/vault"
DATE=$(date +%Y%m%d_%H%M%S)

# Vault設定バックアップ
curl -X GET http://localhost:8200/v1/sys/config/state \
    -H "X-Vault-Token: dev-token" \
    > "$BACKUP_DIR/vault_config_$DATE.json"

# シークレットバックアップ
curl -X GET http://localhost:8200/v1/ai-systems/data/api-keys \
    -H "X-Vault-Token: dev-token" \
    > "$BACKUP_DIR/api_keys_$DATE.json"

curl -X GET http://localhost:8200/v1/ai-systems/data/database \
    -H "X-Vault-Token: dev-token" \
    > "$BACKUP_DIR/database_$DATE.json"

echo "Vaultバックアップ完了: $DATE"
EOF
    
    chmod +x /app/scripts/vault_backup.sh
    
    # 定期バックアップ設定（cron）
    echo "0 2 * * * /app/scripts/vault_backup.sh" >> /tmp/crontab
    crontab /tmp/crontab
    
    log_success "Vaultバックアップ設定完了"
}

# メイン処理
main() {
    log_info "Vault統合設定を開始..."
    
    # 環境変数チェック
    if [ -z "$CLAUDE_API_KEY" ] || [ -z "$OPENAI_API_KEY" ] || [ -z "$GROQ_API_KEY" ]; then
        log_error "必要な環境変数が設定されていません"
        exit 1
    fi
    
    # Vault初期化
    init_vault
    
    # シークレットエンジン設定
    setup_secret_engines
    
    # シークレット設定
    setup_secrets
    
    # ポリシー設定
    setup_policies
    
    # 認証方法設定
    setup_auth_methods
    
    # シークレット取得テスト
    test_secrets
    
    # バックアップ設定
    setup_backup
    
    log_success "Vault統合設定完了！"
    
    # 設定情報表示
    echo "=========================================="
    echo "🔐 Vault設定完了"
    echo "📍 アドレス: http://localhost:8200"
    echo "🔑 トークン: dev-token"
    echo "📁 バックアップ: /app/backups/vault"
    echo "🔄 定期バックアップ: 毎日2:00"
    echo "=========================================="
}

# スクリプト実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 