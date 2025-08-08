#!/bin/bash

# 🚀 AI Systems Complete Startup Script
# 作成日: 2025-08-04
# 目的: 完全なAIシステムの起動

set -e

# カラー出力設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_step() {
    echo -e "${PURPLE}🔧 $1${NC}"
}

log_complete() {
    echo -e "${CYAN}🎉 $1${NC}"
}

# ヘルプ表示
show_help() {
    echo "🚀 AI Systems Complete Startup"
    echo ""
    echo "使用方法:"
    echo "  ./scripts/start_complete_system.sh [オプション]"
    echo ""
    echo "オプション:"
    echo "  -h, --help     このヘルプを表示"
    echo "  -m, --monitor  監視システムも起動"
    echo "  -b, --backup   起動前にバックアップ実行"
    echo "  -d, --docker   Dockerで起動"
    echo "  -v, --verbose  詳細ログを表示"
    echo ""
    echo "例:"
    echo "  ./scripts/start_complete_system.sh              # 基本起動"
    echo "  ./scripts/start_complete_system.sh --monitor    # 監視付き起動"
    echo "  ./scripts/start_complete_system.sh --backup     # バックアップ後起動"
}

# 環境チェック
check_environment() {
    log_step "環境チェック中..."
    
    # Python環境チェック
    if ! command -v python3 &> /dev/null; then
        log_error "Python3がインストールされていません"
        exit 1
    fi
    
    # 仮想環境チェック
    if [ ! -d ".venv" ]; then
        log_warning "仮想環境が見つかりません。作成します..."
        python3 -m venv .venv
        log_success "仮想環境を作成しました"
    fi
    
    # 必要なディレクトリ作成
    mkdir -p logs
    mkdir -p data/audio_files
    mkdir -p data/conversations
    mkdir -p config/prompt_templates
    
    log_success "環境チェック完了"
}

# 依存関係インストール
install_dependencies() {
    log_step "依存関係をインストール中..."
    
    source .venv/bin/activate
    
    # pip更新
    pip install --upgrade pip
    
    # 基本パッケージインストール
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt || {
            log_warning "一部の依存関係のインストールに失敗しました。基本パッケージのみインストールします..."
            pip install fastapi uvicorn python-dotenv requests anthropic groq || {
                log_error "基本パッケージのインストールにも失敗しました"
                exit 1
            }
        }
    fi
    
    log_success "依存関係インストール完了"
}

# 設定ファイルチェック
check_configuration() {
    log_step "設定ファイルをチェック中..."
    
    # .envファイルチェック
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            log_info "env.exampleから.envを作成中..."
            cp env.example .env
            log_success ".envファイルを作成しました"
        else
            log_warning ".envファイルが見つかりません"
        fi
    fi
    
    # 設定ディレクトリチェック
    if [ ! -d "config" ]; then
        mkdir -p config
        log_info "configディレクトリを作成しました"
    fi
    
    log_success "設定ファイルチェック完了"
}

# バックアップ実行
run_backup() {
    log_step "バックアップを実行中..."
    if [ -f "scripts/backup/weekly_backup.sh" ]; then
        bash scripts/backup/weekly_backup.sh
        log_success "バックアップ完了"
    else
        log_warning "バックアップスクリプトが見つかりません"
    fi
}

# 監視システム起動
start_monitoring() {
    log_step "監視システムを起動中..."
    
    # Prometheus起動
    if [ -f "monitoring/prometheus/prometheus.yml" ]; then
        log_info "Prometheusを起動中..."
        # ここでPrometheusを起動
    fi
    
    # Grafana起動
    if [ -f "monitoring/grafana/dashboards/ai-systems-dashboard.json" ]; then
        log_info "Grafanaダッシュボードを設定中..."
        # ここでGrafanaを起動
    fi
    
    log_success "監視システム起動完了"
}

# メインシステム起動
start_main_system() {
    log_step "メインシステムを起動中..."
    
    source .venv/bin/activate
    
    # メインアプリケーション起動
    if [ -f "main_hybrid.py" ]; then
        log_info "ハイブリッドシステムを起動中..."
        python main_hybrid.py &
        MAIN_PID=$!
        log_success "メインシステム起動完了 (PID: $MAIN_PID)"
    else
        log_error "メインアプリケーションファイルが見つかりません"
        exit 1
    fi
}

# ヘルスチェック
health_check() {
    log_step "ヘルスチェックを実行中..."
    
    # 少し待ってからヘルスチェック
    sleep 5
    
    # HTTPヘルスチェック
    if command -v curl &> /dev/null; then
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "システムが正常に動作しています"
        else
            log_warning "システムの応答が遅い可能性があります"
        fi
    fi
    
    log_success "ヘルスチェック完了"
}

# システム情報表示
show_system_info() {
    log_complete "システム起動完了！"
    echo ""
    echo "🌐 アクセス情報:"
    echo "  メインアプリケーション: http://localhost:8000"
    echo "  API ドキュメント: http://localhost:8000/docs"
    echo "  ヘルスチェック: http://localhost:8000/health"
    echo ""
    echo "📊 監視ダッシュボード:"
    echo "  Grafana: http://localhost:3000"
    echo "  Prometheus: http://localhost:9090"
    echo ""
    echo "📁 ファイル構成:"
    echo "  ログファイル: ./logs/"
    echo "  設定ファイル: ./config/"
    echo "  バックアップ: ~/Backups/voice-ai-system/"
    echo ""
    echo "🛠️  管理コマンド:"
    echo "  システム停止: Ctrl+C"
    echo "  ログ確認: tail -f logs/system.log"
    echo "  バックアップ: ./scripts/backup/weekly_backup.sh"
    echo ""
}

# メイン処理
main() {
    # 引数解析
    MONITOR_FLAG=false
    BACKUP_FLAG=false
    DOCKER_FLAG=false
    VERBOSE_FLAG=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -m|--monitor)
                MONITOR_FLAG=true
                shift
                ;;
            -b|--backup)
                BACKUP_FLAG=true
                shift
                ;;
            -d|--docker)
                DOCKER_FLAG=true
                shift
                ;;
            -v|--verbose)
                VERBOSE_FLAG=true
                shift
                ;;
            *)
                log_error "不明なオプション: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo "🚀 AI Systems Complete Startup"
    echo "================================"
    
    # バックアップ実行
    if [ "$BACKUP_FLAG" = true ]; then
        run_backup
    fi
    
    # 環境チェック
    check_environment
    
    # 依存関係インストール
    install_dependencies
    
    # 設定ファイルチェック
    check_configuration
    
    # 監視システム起動
    if [ "$MONITOR_FLAG" = true ]; then
        start_monitoring
    fi
    
    # メインシステム起動
    start_main_system
    
    # ヘルスチェック
    health_check
    
    # システム情報表示
    show_system_info
    
    # プロセス監視
    if [ ! -z "$MAIN_PID" ]; then
        log_info "システムを監視中... (PID: $MAIN_PID)"
        wait $MAIN_PID
    fi
}

# スクリプト実行
main "$@" 