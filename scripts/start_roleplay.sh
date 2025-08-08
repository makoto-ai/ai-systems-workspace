#!/bin/bash

# 🎤 AI Voice Roleplay System - Quick Start Script
# 作成日: 2025-08-04
# 目的: 1行でロールプレイシステムを起動

set -e  # エラー時に停止

# カラー出力設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# ヘルプ表示
show_help() {
    echo "🎤 AI Voice Roleplay System - Quick Start"
    echo ""
    echo "使用方法:"
    echo "  ./scripts/start_roleplay.sh [オプション]"
    echo ""
    echo "オプション:"
    echo "  -h, --help     このヘルプを表示"
    echo "  -d, --docker   Dockerで起動"
    echo "  -v, --verbose  詳細ログを表示"
    echo "  --backup       起動前にバックアップ実行"
    echo ""
    echo "例:"
    echo "  ./scripts/start_roleplay.sh              # 通常起動"
    echo "  ./scripts/start_roleplay.sh --docker     # Docker起動"
    echo "  ./scripts/start_roleplay.sh --backup     # バックアップ後起動"
}

# 環境チェック
check_environment() {
    log_info "🔍 環境チェック中..."
    
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
    
    # 依存関係チェック
    if [ ! -f "requirements.txt" ]; then
        log_warning "requirements.txtが見つかりません"
    fi
    
    log_success "環境チェック完了"
}

# バックアップ実行
run_backup() {
    log_info "💾 バックアップ実行中..."
    if [ -f "scripts/backup/weekly_backup.sh" ]; then
        bash scripts/backup/weekly_backup.sh
        log_success "バックアップ完了"
    else
        log_warning "バックアップスクリプトが見つかりません"
    fi
}

# 通常起動
start_normal() {
    log_info "🚀 通常モードで起動中..."
    
    # 仮想環境アクティベート
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        log_info "✅ 仮想環境をアクティベートしました"
    else
        log_error "仮想環境が見つかりません"
        exit 1
    fi
    
    # 依存関係インストール
    if [ -f "requirements.txt" ]; then
        log_info "📦 依存関係をインストール中..."
        pip install --upgrade pip
        pip install -r requirements.txt || {
            log_warning "一部の依存関係のインストールに失敗しました。基本パッケージのみインストールします..."
            pip install fastapi uvicorn python-dotenv requests || {
                log_error "基本パッケージのインストールにも失敗しました"
                exit 1
            }
        }
    fi
    
    # 環境変数チェック
    if [ ! -f ".env" ]; then
        log_warning ".envファイルが見つかりません"
        if [ -f "env.example" ]; then
            log_info "env.exampleから.envを作成中..."
            cp env.example .env
            log_success ".envファイルを作成しました"
        fi
    fi
    
    # メインスクリプト実行
    if [ -f "scripts/run_voice_loop.py" ]; then
        log_info "🎤 音声ループ開始..."
        python scripts/run_voice_loop.py
    elif [ -f "main_hybrid.py" ]; then
        log_info "🤖 ハイブリッドシステム開始..."
        python main_hybrid.py
    elif [ -f "youtube_script_generation_system.py" ]; then
        log_info "📝 YouTubeスクリプト生成システム開始..."
        python youtube_script_generation_system.py
    else
        log_warning "起動可能なメインスクリプトが見つかりません"
        log_info "利用可能なスクリプト:"
        ls -la *.py 2>/dev/null || log_info "  - メインディレクトリにPythonファイルが見つかりません"
        ls -la scripts/*.py 2>/dev/null || log_info "  - scriptsディレクトリにPythonファイルが見つかりません"
        log_info "システムを手動で起動してください"
        exit 0
    fi
}

# Docker起動
start_docker() {
    log_info "🐳 Dockerモードで起動中..."
    
    if [ ! -f "docker-compose.yml" ]; then
        log_error "docker-compose.ymlが見つかりません"
        exit 1
    fi
    
    # Docker Compose起動
    docker-compose up -d
    
    log_success "Dockerコンテナを起動しました"
    log_info "📊 監視ダッシュボード: http://localhost:3000"
    log_info "🎤 音声API: http://localhost:50021"
}

# メイン処理
main() {
    # 引数解析
    BACKUP_FLAG=false
    DOCKER_FLAG=false
    VERBOSE_FLAG=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -d|--docker)
                DOCKER_FLAG=true
                shift
                ;;
            -v|--verbose)
                VERBOSE_FLAG=true
                shift
                ;;
            --backup)
                BACKUP_FLAG=true
                shift
                ;;
            *)
                log_error "不明なオプション: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # バックアップ実行
    if [ "$BACKUP_FLAG" = true ]; then
        run_backup
    fi
    
    # 環境チェック
    check_environment
    
    # 起動モード選択
    if [ "$DOCKER_FLAG" = true ]; then
        start_docker
    else
        start_normal
    fi
}

# スクリプト実行
main "$@" 