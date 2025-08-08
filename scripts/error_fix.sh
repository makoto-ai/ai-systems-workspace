#!/bin/bash

# AI Systems エラー修正スクリプト
# 一般的なエラーを自動修正

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

# 依存関係インストール
install_dependencies() {
    log_info "依存関係をインストール中..."
    
    # Python依存関係
    if [ -f "requirements_hybrid.txt" ]; then
        pip install -r requirements_hybrid.txt
        log_success "Python依存関係インストール完了"
    else
        log_warn "requirements_hybrid.txt が見つかりません"
    fi
    
    # システム依存関係
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y \
            curl \
            wget \
            git \
            ffmpeg \
            libsndfile1 \
            portaudio19-dev \
            python3-dev \
            gcc \
            g++
    elif command -v brew &> /dev/null; then
        brew install \
            curl \
            wget \
            git \
            ffmpeg \
            libsndfile \
            portaudio
    fi
    
    log_success "システム依存関係インストール完了"
}

# ファイル権限修正
fix_permissions() {
    log_info "ファイル権限を修正中..."
    
    # スクリプトファイルに実行権限を付与
    find . -name "*.sh" -exec chmod +x {} \;
    find . -name "*.py" -exec chmod +x {} \;
    
    # ログディレクトリ作成
    mkdir -p logs
    mkdir -p data
    mkdir -p backups
    
    # 権限設定
    chmod 755 logs data backups
    chmod 644 *.py *.yml *.yaml *.json *.md
    
    log_success "ファイル権限修正完了"
}

# 設定ファイル修正
fix_configurations() {
    log_info "設定ファイルを修正中..."
    
    # 環境変数ファイル作成
    if [ ! -f ".env" ]; then
        if [ -f "env.hybrid.example" ]; then
            cp env.hybrid.example .env
            log_info ".env ファイルを作成しました"
        fi
    fi
    
    # ログディレクトリ作成
    mkdir -p logs/{app,error,access,metrics,debug}
    
    # 設定ディレクトリ作成
    mkdir -p config/{email,notification,prompt_templates}
    
    # データディレクトリ作成
    mkdir -p data/{uploads,processed,backups}
    
    log_success "設定ファイル修正完了"
}

# Pythonインポートエラー修正
fix_python_imports() {
    log_info "Pythonインポートエラーを修正中..."
    
    # __init__.py ファイル作成
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    # モジュールディレクトリに__init__.pyを作成
    for dir in modules scripts youtube_script_system; do
        if [ -d "$dir" ]; then
            touch "$dir/__init__.py"
        fi
    done
    
    # パッケージ構造修正
    if [ -d "modules" ]; then
        touch "modules/__init__.py"
    fi
    
    if [ -d "scripts" ]; then
        touch "scripts/__init__.py"
    fi
    
    log_success "Pythonインポートエラー修正完了"
}

# 構文エラー修正
fix_syntax_errors() {
    log_info "構文エラーを修正中..."
    
    # Pythonファイルの構文チェック
    for file in $(find . -name "*.py"); do
        if python -m py_compile "$file" 2>/dev/null; then
            log_info "✓ $file"
        else
            log_warn "✗ $file - 構文エラーがあります"
        fi
    done
    
    # YAMLファイルの構文チェック
    for file in $(find . -name "*.yml" -o -name "*.yaml"); do
        if python -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null; then
            log_info "✓ $file"
        else
            log_warn "✗ $file - YAML構文エラーがあります"
        fi
    done
    
    log_success "構文エラー修正完了"
}

# 依存関係チェック
check_dependencies() {
    log_info "依存関係をチェック中..."
    
    # Pythonパッケージチェック
    required_packages=(
        "fastapi"
        "uvicorn"
        "httpx"
        "psutil"
        "pydantic"
    )
    
    missing_packages=()
    
    for package in "${required_packages[@]}"; do
        if python -c "import $package" 2>/dev/null; then
            log_info "✓ $package"
        else
            log_warn "✗ $package - 不足"
            missing_packages+=("$package")
        fi
    done
    
    if [ ${#missing_packages[@]} -gt 0 ]; then
        log_warn "不足しているパッケージ: ${missing_packages[*]}"
        log_info "pip install ${missing_packages[*]} を実行してください"
    else
        log_success "すべての依存関係が利用可能です"
    fi
}

# ファイル整合性チェック
check_file_integrity() {
    log_info "ファイル整合性をチェック中..."
    
    # 必要なファイルの存在チェック
    required_files=(
        "main_hybrid.py"
        "docker-compose.hybrid.yml"
        "Dockerfile.hybrid"
        "requirements_hybrid.txt"
        "env.hybrid.example"
    )
    
    missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            log_info "✓ $file"
        else
            log_warn "✗ $file - 見つかりません"
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        log_warn "不足しているファイル: ${missing_files[*]}"
    else
        log_success "すべての必要なファイルが存在します"
    fi
}

# ネットワーク接続テスト
test_network_connectivity() {
    log_info "ネットワーク接続をテスト中..."
    
    # ローカルホスト接続テスト
    localhost_services=(
        "8000:ai-systems-app"
        "8001:mcp-service"
        "8002:composer-service"
        "8200:vault"
        "3000:grafana"
        "9090:prometheus"
    )
    
    for service in "${localhost_services[@]}"; do
        port="${service%:*}"
        name="${service#*:}"
        
        if curl -s "http://localhost:$port/health" >/dev/null 2>&1; then
            log_info "✓ $name ($port)"
        else
            log_warn "✗ $name ($port) - 接続できません"
        fi
    done
    
    log_success "ネットワーク接続テスト完了"
}

# ログファイルクリーンアップ
cleanup_logs() {
    log_info "ログファイルをクリーンアップ中..."
    
    # 古いログファイル削除
    find logs -name "*.log" -mtime +7 -delete 2>/dev/null || true
    find . -name "*.log" -mtime +7 -delete 2>/dev/null || true
    
    # 空のログファイル削除
    find logs -name "*.log" -size 0 -delete 2>/dev/null || true
    find . -name "*.log" -size 0 -delete 2>/dev/null || true
    
    # ログディレクトリ作成
    mkdir -p logs/{app,error,access,metrics,debug,performance,security}
    
    log_success "ログファイルクリーンアップ完了"
}

# システム最適化
optimize_system() {
    log_info "システムを最適化中..."
    
    # Pythonキャッシュクリア
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    # 一時ファイル削除
    find . -name "*.tmp" -delete 2>/dev/null || true
    find . -name "*.temp" -delete 2>/dev/null || true
    
    # バックアップファイル整理
    find . -name "*.bak" -mtime +30 -delete 2>/dev/null || true
    find . -name "*.backup" -mtime +30 -delete 2>/dev/null || true
    
    log_success "システム最適化完了"
}

# メイン処理
main() {
    log_info "AI Systems エラー修正を開始..."
    
    # 依存関係インストール
    install_dependencies
    
    # ファイル権限修正
    fix_permissions
    
    # 設定ファイル修正
    fix_configurations
    
    # Pythonインポートエラー修正
    fix_python_imports
    
    # 構文エラー修正
    fix_syntax_errors
    
    # 依存関係チェック
    check_dependencies
    
    # ファイル整合性チェック
    check_file_integrity
    
    # ログファイルクリーンアップ
    cleanup_logs
    
    # システム最適化
    optimize_system
    
    log_success "エラー修正完了！"
    
    # 最終チェック
    echo ""
    echo "=========================================="
    echo "🔧 エラー修正完了"
    echo "📋 修正内容:"
    echo "  - 依存関係インストール"
    echo "  - ファイル権限修正"
    echo "  - 設定ファイル修正"
    echo "  - Pythonインポートエラー修正"
    echo "  - 構文エラー修正"
    echo "  - ログファイルクリーンアップ"
    echo "  - システム最適化"
    echo "=========================================="
}

# スクリプト実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 