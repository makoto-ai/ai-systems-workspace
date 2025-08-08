#!/bin/bash

# ハイブリッドAIシステムデプロイスクリプト
# MCPとComposerの統合デプロイ

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

# 環境変数チェック
check_environment() {
    log_info "環境変数をチェック中..."
    
    required_vars=(
        "CLAUDE_API_KEY"
        "OPENAI_API_KEY"
        "GROQ_API_KEY"
        "POSTGRES_PASSWORD"
        "GRAFANA_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "環境変数 $var が設定されていません"
            exit 1
        fi
    done
    
    log_success "環境変数チェック完了"
}

# Vault初期化
init_vault() {
    log_info "Vaultを初期化中..."
    
    # Vaultが起動するまで待機
    until curl -f http://localhost:8200/v1/sys/health > /dev/null 2>&1; do
        log_warn "Vaultの起動を待機中..."
        sleep 5
    done
    
    # Vaultにシークレットを設定
    curl -X POST http://localhost:8200/v1/secret/data/ai-systems \
        -H "X-Vault-Token: dev-token" \
        -H "Content-Type: application/json" \
        -d "{
            \"data\": {
                \"claude_api_key\": \"$CLAUDE_API_KEY\",
                \"openai_api_key\": \"$OPENAI_API_KEY\",
                \"groq_api_key\": \"$GROQ_API_KEY\",
                \"postgres_password\": \"$POSTGRES_PASSWORD\",
                \"grafana_password\": \"$GRAFANA_PASSWORD\"
            }
        }" > /dev/null 2>&1 || log_warn "Vaultシークレット設定に失敗"
    
    log_success "Vault初期化完了"
}

# Docker Compose デプロイ
deploy_services() {
    log_info "Docker Composeでサービスをデプロイ中..."
    
    # 既存のコンテナを停止
    docker-compose -f docker-compose.hybrid.yml down || true
    
    # イメージをプル
    docker-compose -f docker-compose.hybrid.yml pull
    
    # サービスを起動
    docker-compose -f docker-compose.hybrid.yml up -d
    
    log_success "Docker Composeデプロイ完了"
}

# ヘルスチェック
health_check() {
    log_info "ヘルスチェックを実行中..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "ヘルスチェック試行 $attempt/$max_attempts"
        
        # メインアプリケーション
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log_success "メインアプリケーション: 正常"
        else
            log_warn "メインアプリケーション: 異常"
        fi
        
        # MCPサービス
        if curl -f http://localhost:8001/health > /dev/null 2>&1; then
            log_success "MCPサービス: 正常"
        else
            log_warn "MCPサービス: 異常"
        fi
        
        # Composerサービス
        if curl -f http://localhost:8002/health > /dev/null 2>&1; then
            log_success "Composerサービス: 正常"
        else
            log_warn "Composerサービス: 異常"
        fi
        
        # Grafana
        if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
            log_success "Grafana: 正常"
        else
            log_warn "Grafana: 異常"
        fi
        
        # Prometheus
        if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
            log_success "Prometheus: 正常"
        else
            log_warn "Prometheus: 異常"
        fi
        
        # Vault
        if curl -f http://localhost:8200/v1/sys/health > /dev/null 2>&1; then
            log_success "Vault: 正常"
        else
            log_warn "Vault: 異常"
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "ヘルスチェックが失敗しました"
            return 1
        fi
        
        sleep 10
        ((attempt++))
    done
    
    log_success "ヘルスチェック完了"
}

# パフォーマンステスト
performance_test() {
    log_info "パフォーマンステストを実行中..."
    
    # Composer API テスト
    log_info "Composer API テスト..."
    curl -X POST http://localhost:8000/composer/generate \
        -H "Content-Type: application/json" \
        -d '{
            "metadata": {
                "title": "AI技術の最新動向",
                "authors": ["田中太郎", "佐藤花子"],
                "abstract": "本研究では、最新のAI技術について調査を行った。",
                "publication_year": 2024
            },
            "abstract": "AI技術の最新動向について詳しく解説します。",
            "style": "popular"
        }' > /dev/null 2>&1 && log_success "Composer API: 成功" || log_error "Composer API: 失敗"
    
    # MCP API テスト
    log_info "MCP API テスト..."
    curl -X POST http://localhost:8000/mcp/generate \
        -H "Content-Type: application/json" \
        -d '{
            "title": "AI技術の最新動向",
            "content": "AI技術について詳しく解説します。",
            "style": "educational"
        }' > /dev/null 2>&1 && log_success "MCP API: 成功" || log_error "MCP API: 失敗"
    
    # ハイブリッド API テスト
    log_info "ハイブリッド API テスト..."
    curl -X POST http://localhost:8000/hybrid/generate \
        -H "Content-Type: application/json" \
        -d '{
            "metadata": {
                "title": "AI技術の最新動向",
                "authors": ["田中太郎", "佐藤花子"],
                "abstract": "本研究では、最新のAI技術について調査を行った。",
                "publication_year": 2024
            },
            "abstract": "AI技術の最新動向について詳しく解説します。",
            "style": "popular"
        }' > /dev/null 2>&1 && log_success "ハイブリッド API: 成功" || log_error "ハイブリッド API: 失敗"
    
    log_success "パフォーマンステスト完了"
}

# メトリクス収集開始
start_metrics_collection() {
    log_info "メトリクス収集を開始中..."
    
    # システムメトリクス収集
    nohup python scripts/collect_metrics.py > logs/metrics.log 2>&1 &
    
    # ログ収集
    nohup python scripts/collect_logs.py > logs/log_collector.log 2>&1 &
    
    log_success "メトリクス収集開始完了"
}

# サービス情報表示
show_service_info() {
    log_info "サービス情報:"
    echo "=========================================="
    echo "🌐 メインアプリケーション: http://localhost:8000"
    echo "🤖 MCPサービス: http://localhost:8001"
    echo "📝 Composerサービス: http://localhost:8002"
    echo "📊 Grafana: http://localhost:3000 (admin/admin)"
    echo "📈 Prometheus: http://localhost:9090"
    echo "🔐 Vault: http://localhost:8200"
    echo "🗄️  PostgreSQL: localhost:5432"
    echo "🔴 Redis: localhost:6379"
    echo "🎤 VOICEVOX: http://localhost:50021"
    echo "🤖 Ollama: http://localhost:11434"
    echo "=========================================="
}

# メイン処理
main() {
    log_info "ハイブリッドAIシステムデプロイを開始..."
    
    # 環境変数チェック
    check_environment
    
    # Docker Compose デプロイ
    deploy_services
    
    # Vault初期化
    init_vault
    
    # ヘルスチェック
    health_check
    
    # パフォーマンステスト
    performance_test
    
    # メトリクス収集開始
    start_metrics_collection
    
    # サービス情報表示
    show_service_info
    
    log_success "ハイブリッドAIシステムデプロイ完了！"
}

# スクリプト実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 