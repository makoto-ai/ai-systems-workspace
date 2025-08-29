#!/bin/bash
# AIロールプレイシステム起動スクリプト

set -e

# ログ設定
LOG_FILE="logs/roleplay_start.log"
mkdir -p logs

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 環境チェック
check_environment() {
    log "🔍 環境チェック開始"
    
    # Python仮想環境確認
    if [ ! -d ".venv" ]; then
        log "❌ Python仮想環境が見つかりません"
        log "📥 作成方法: python3 -m venv .venv"
        return 1
    fi
    
    # 依存関係確認
    if ! source .venv/bin/activate && python -c "import fastapi, psutil, requests" 2>/dev/null; then
        log "❌ 依存関係が不足しています"
        log "📥 インストール方法: pip install -r requirements.txt"
        return 1
    fi
    
    # 環境変数確認
    if [ -z "$CLAUDE_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
        log "⚠️  APIキーが設定されていません"
        log "📝 設定方法: .envファイルにAPIキーを追加"
    fi
    
    log "✅ 環境チェック完了"
}

# サービス起動
start_services() {
    log "🚀 サービス起動開始"
    
    # 1. データベース起動
    if command -v docker &> /dev/null; then
        log "🐳 Docker Compose起動中..."
        docker-compose up -d postgres redis 2>/dev/null || log "⚠️  Docker Compose起動失敗"
    else
        log "⚠️  Dockerがインストールされていません"
    fi
    
    # 2. 監視サービス起動
    if [ -d "monitoring" ]; then
        log "📊 監視サービス起動中..."
        docker-compose up -d prometheus grafana 2>/dev/null || log "⚠️  監視サービス起動失敗"
    fi
    
    log "✅ サービス起動完了"
}

# メインアプリケーション起動
start_main_app() {
    log "🎤 AIロールプレイシステム起動中..."
    
    # 仮想環境アクティベート
    source .venv/bin/activate
    
    # 環境変数読み込み
    if [ -f ".env" ]; then
        export $(cat .env | grep -v '^#' | xargs)
        log "✅ 環境変数読み込み完了"
    fi
    
    # メインアプリケーション起動
    log "🌐 FastAPIサーバー起動中..."
    uvicorn main_hybrid:app --host 0.0.0.0 --port 8000 --reload &
    APP_PID=$!
    
    # 起動待機
    sleep 5
    
    # ヘルスチェック
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log "✅ アプリケーション起動完了"
        log "🌐 ダッシュボード: http://localhost:8000"
        log "📊 メトリクス: http://localhost:8000/metrics"
        log "🔍 ヘルスチェック: http://localhost:8000/health"
    else
        log "❌ アプリケーション起動失敗"
        return 1
    fi
}

# 音声処理サービス起動
start_voice_services() {
    log "🎵 音声処理サービス起動中..."
    
    # WhisperX起動（オプション）
    if command -v whisperx &> /dev/null; then
        log "🎤 WhisperX起動中..."
        # WhisperX起動コマンド（環境に応じて調整）
    else
        log "⚠️  WhisperXがインストールされていません"
    fi
    
    # Voicevox起動（オプション）
    if [ -d "voicevox" ] || command -v voicevox &> /dev/null; then
        log "🔊 Voicevox起動中..."
        # Voicevox起動コマンド（環境に応じて調整）
    else
        log "⚠️  Voicevoxがインストールされていません"
    fi
}

# 使用方法表示
show_usage() {
    log "📖 使用方法"
    echo ""
    echo "🎤 AIロールプレイシステム"
    echo "=========================="
    echo ""
    echo "🌐 Webインターフェース:"
    echo "   http://localhost:8000"
    echo ""
    echo "📊 監視ダッシュボード:"
    echo "   http://localhost:3000 (Grafana)"
    echo "   http://localhost:9090 (Prometheus)"
    echo ""
    echo "🔧 管理コマンド:"
    echo "   ./scripts/backup/weekly_backup.sh  # バックアップ"
    echo "   ./scripts/run_ai_pipeline.sh       # AIパイプライン"
    echo "   ./scripts/setup_vault.sh           # Vault設定"
    echo ""
    echo "🛑 停止方法:"
    echo "   Ctrl+C または docker-compose down"
    echo ""
}

# メイン実行
main() {
    log "🎯 AIロールプレイシステム起動開始"
    
    # 1. 環境チェック
    check_environment || exit 1
    
    # 2. サービス起動
    start_services
    
    # 3. 音声処理サービス起動
    start_voice_services
    
    # 4. メインアプリケーション起動
    start_main_app || exit 1
    
    # 5. 使用方法表示
    show_usage
    
    # 6. プロセス監視
    log "🔄 システム稼働中... (Ctrl+Cで停止)"
    wait $APP_PID
}

# スクリプト実行
main "$@" 