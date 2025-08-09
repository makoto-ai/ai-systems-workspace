#!/bin/bash
# AI Systems Pipeline - CI/CD + Docker + Composer自動連携

set -e

# ログ設定
LOG_FILE="logs/ai_pipeline.log"
mkdir -p logs

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 環境変数読み込み
if [ -f .env.docker ]; then
    source .env.docker
    log "✅ 環境変数読み込み完了"
else
    log "⚠️  .env.docker が見つかりません"
fi

# ヘルスチェック関数
check_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    log "🔍 $service ヘルスチェック開始: $url"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null; then
            log "✅ $service 準備完了"
            return 0
        fi
        
        log "⏳ $service 待機中... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    log "❌ $service 起動失敗"
    return 1
}

# Docker Compose 起動
start_services() {
    log "🚀 Docker Compose 起動開始"
    
    # 既存コンテナ停止
    docker-compose down || true
    
    # 新規起動
    docker-compose up -d
    
    # ヘルスチェック
    check_service "PostgreSQL" "http://localhost:5432" || return 1
    check_service "Redis" "http://localhost:6379" || return 1
    check_service "AI Systems App" "http://localhost:8000/health" || return 1
    check_service "Prometheus" "http://localhost:9090/-/healthy" || return 1
    check_service "Grafana" "http://localhost:3000/api/health" || return 1
    
    log "✅ 全サービス起動完了"
}

# Composer + MCP 統合実行
run_ai_generation() {
    log "🤖 AI生成パイプライン開始"
    
    # 環境変数設定
    export CLAUDE_API_KEY="${CLAUDE_API_KEY}"
    export OPENAI_API_KEY="${OPENAI_API_KEY}"
    export GROQ_API_KEY="${GROQ_API_KEY}"
    
    # Composer実行
    log "📝 Composer実行開始"
    python3 -c "
from modules.composer import ScriptComposer
composer = ScriptComposer()
result = composer.generate_script('営業シナリオ', '音声AI営業システム')
print(f'Composer結果: {result}')
" || log "⚠️  Composer実行エラー"
    
    # MCP実行
    log "🔍 MCP実行開始"
    python3 -c "
from youtube_script_generation_system import YouTubeScriptGenerator
mcp = YouTubeScriptGenerator()
result = mcp.generate_script('論文検索', '音声AI営業')
print(f'MCP結果: {result}')
" || log "⚠️  MCP実行エラー"
    
    log "✅ AI生成パイプライン完了"
}

# メトリクス収集
collect_metrics() {
    log "📊 メトリクス収集開始"
    
    # Prometheusメトリクス取得
    curl -s http://localhost:8000/metrics > logs/prometheus_metrics.txt 2>/dev/null || true
    
    # システム監視データ取得
    curl -s http://localhost:8000/system/health > logs/system_health.json 2>/dev/null || true
    
    # ログファイルサイズ確認
    find logs/ -name "*.log" -exec ls -lh {} \; | head -5 > logs/file_sizes.txt
    
    log "✅ メトリクス収集完了"
}

# クリーンアップ
cleanup() {
    log "🧹 クリーンアップ開始"
    
    # 古いログファイル削除（7日以上）
    find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true
    
    # 一時ファイル削除
    rm -f logs/temp_*.txt 2>/dev/null || true
    
    log "✅ クリーンアップ完了"
}

# メイン実行
main() {
    log "🎯 AI Systems Pipeline 開始"
    
    # 1. サービス起動
    start_services || {
        log "❌ サービス起動失敗"
        exit 1
    }
    
    # 2. AI生成実行
    run_ai_generation
    
    # 3. メトリクス収集
    collect_metrics
    
    # 4. クリーンアップ
    cleanup
    
    log "🎉 AI Systems Pipeline 完了"
}

# スクリプト実行
main "$@"
