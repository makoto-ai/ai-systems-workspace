#!/bin/bash

# 📊 AI Systems Status Report Generator
# 作成日: 2025-08-04
# 目的: システムの完全な状態レポートを生成

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

log_header() {
    echo -e "${PURPLE}📊 $1${NC}"
}

# システム情報収集
collect_system_info() {
    log_header "システム情報を収集中..."
    
    echo "=== システム情報 ===" > system_report.txt
    echo "日時: $(date)" >> system_report.txt
    echo "ホスト名: $(hostname)" >> system_report.txt
    echo "OS: $(uname -s) $(uname -r)" >> system_report.txt
    echo "CPU: $(sysctl -n hw.ncpu) コア" >> system_report.txt
    echo "メモリ: $(sysctl -n hw.memsize | awk '{print $0/1024/1024/1024 " GB"}')" >> system_report.txt
    echo "ディスク使用量: $(df -h . | tail -1 | awk '{print $5}')" >> system_report.txt
    echo "" >> system_report.txt
}

# Python環境情報
collect_python_info() {
    log_header "Python環境情報を収集中..."
    
    echo "=== Python環境 ===" >> system_report.txt
    if command -v python3 &> /dev/null; then
        echo "Python3: $(python3 --version)" >> system_report.txt
    else
        echo "Python3: 未インストール" >> system_report.txt
    fi
    
    if [ -d ".venv" ]; then
        echo "仮想環境: 存在" >> system_report.txt
        source .venv/bin/activate
        echo "仮想環境Python: $(python --version)" >> system_report.txt
    else
        echo "仮想環境: 未作成" >> system_report.txt
    fi
    echo "" >> system_report.txt
}

# 依存関係情報
collect_dependencies_info() {
    log_header "依存関係情報を収集中..."
    
    echo "=== 依存関係 ===" >> system_report.txt
    if [ -f "requirements.txt" ]; then
        echo "requirements.txt: 存在" >> system_report.txt
        echo "パッケージ数: $(wc -l < requirements.txt)" >> system_report.txt
    else
        echo "requirements.txt: 未作成" >> system_report.txt
    fi
    
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        echo "インストール済みパッケージ数: $(pip list | wc -l)" >> system_report.txt
    fi
    echo "" >> system_report.txt
}

# ファイル構成情報
collect_file_structure_info() {
    log_header "ファイル構成情報を収集中..."
    
    echo "=== ファイル構成 ===" >> system_report.txt
    echo "プロジェクトサイズ: $(du -sh . | awk '{print $1}')" >> system_report.txt
    
    # 主要ディレクトリの存在確認
    directories=("scripts" "config" "data" "logs" "docs" "monitoring")
    for dir in "${directories[@]}"; do
        if [ -d "$dir" ]; then
            echo "$dir/: 存在 ($(find $dir -type f | wc -l) ファイル)" >> system_report.txt
        else
            echo "$dir/: 未作成" >> system_report.txt
        fi
    done
    echo "" >> system_report.txt
}

# スクリプト情報
collect_scripts_info() {
    log_header "スクリプト情報を収集中..."
    
    echo "=== スクリプト ===" >> system_report.txt
    if [ -d "scripts" ]; then
        echo "スクリプト数: $(find scripts -name "*.sh" -o -name "*.py" | wc -l)" >> system_report.txt
        echo "実行可能スクリプト:" >> system_report.txt
        find scripts -executable -type f | while read script; do
            echo "  - $script" >> system_report.txt
        done
    else
        echo "scriptsディレクトリ: 未作成" >> system_report.txt
    fi
    echo "" >> system_report.txt
}

# 設定情報
collect_config_info() {
    log_header "設定情報を収集中..."
    
    echo "=== 設定 ===" >> system_report.txt
    if [ -f ".env" ]; then
        echo ".env: 存在" >> system_report.txt
        echo "設定項目数: $(grep -c "=" .env)" >> system_report.txt
    else
        echo ".env: 未作成" >> system_report.txt
    fi
    
    if [ -d "config" ]; then
        echo "configディレクトリ: 存在" >> system_report.txt
        echo "設定ファイル数: $(find config -type f | wc -l)" >> system_report.txt
    else
        echo "configディレクトリ: 未作成" >> system_report.txt
    fi
    echo "" >> system_report.txt
}

# バックアップ情報
collect_backup_info() {
    log_header "バックアップ情報を収集中..."
    
    echo "=== バックアップ ===" >> system_report.txt
    backup_dir="$HOME/Backups/voice-ai-system"
    if [ -d "$backup_dir" ]; then
        echo "バックアップディレクトリ: 存在" >> system_report.txt
        echo "バックアップ数: $(find "$backup_dir" -maxdepth 1 -type d | wc -l)" >> system_report.txt
        echo "最新バックアップ: $(ls -t "$backup_dir" | head -1)" >> system_report.txt
        echo "バックアップサイズ: $(du -sh "$backup_dir" | awk '{print $1}')" >> system_report.txt
    else
        echo "バックアップディレクトリ: 未作成" >> system_report.txt
    fi
    echo "" >> system_report.txt
}

# システム状態チェック
check_system_status() {
    log_header "システム状態をチェック中..."
    
    echo "=== システム状態 ===" >> system_report.txt
    
    # プロセスチェック
    if pgrep -f "main_hybrid.py" > /dev/null; then
        echo "メインシステム: 実行中" >> system_report.txt
    else
        echo "メインシステム: 停止中" >> system_report.txt
    fi
    
    # ポートチェック
    if lsof -i :8000 > /dev/null 2>&1; then
        echo "Webサーバー: 実行中 (ポート8000)" >> system_report.txt
    else
        echo "Webサーバー: 停止中" >> system_report.txt
    fi
    
    # cronジョブチェック
    if crontab -l 2>/dev/null | grep -q "weekly_backup.sh"; then
        echo "定期バックアップ: 設定済み" >> system_report.txt
    else
        echo "定期バックアップ: 未設定" >> system_report.txt
    fi
    echo "" >> system_report.txt
}

# パフォーマンス情報
collect_performance_info() {
    log_header "パフォーマンス情報を収集中..."
    
    echo "=== パフォーマンス ===" >> system_report.txt
    echo "CPU使用率: $(top -l 1 | grep "CPU usage" | awk '{print $3}')" >> system_report.txt
    echo "メモリ使用率: $(memory_pressure | grep "System-wide memory free percentage" | awk '{print $5}')" >> system_report.txt
    echo "ディスク使用率: $(df -h . | tail -1 | awk '{print $5}')" >> system_report.txt
    echo "" >> system_report.txt
}

# 推奨事項
generate_recommendations() {
    log_header "推奨事項を生成中..."
    
    echo "=== 推奨事項 ===" >> system_report.txt
    
    # 仮想環境チェック
    if [ ! -d ".venv" ]; then
        echo "⚠️  仮想環境を作成することを推奨します" >> system_report.txt
    fi
    
    # .envファイルチェック
    if [ ! -f ".env" ]; then
        echo "⚠️  .envファイルを作成することを推奨します" >> system_report.txt
    fi
    
    # バックアップチェック
    if [ ! -d "$HOME/Backups/voice-ai-system" ]; then
        echo "⚠️  定期バックアップを設定することを推奨します" >> system_report.txt
    fi
    
    # システム起動チェック
    if ! pgrep -f "main_hybrid.py" > /dev/null; then
        echo "⚠️  システムを起動することを推奨します" >> system_report.txt
    fi
    
    echo "" >> system_report.txt
}

# レポート表示
display_report() {
    log_success "システムレポートが生成されました: system_report.txt"
    echo ""
    echo "📊 システムレポート概要:"
    echo "================================"
    cat system_report.txt
    echo ""
    echo "📁 詳細レポート: system_report.txt"
}

# メイン処理
main() {
    echo "📊 AI Systems Status Report Generator"
    echo "===================================="
    
    # レポートファイル初期化
    > system_report.txt
    
    # 各種情報収集
    collect_system_info
    collect_python_info
    collect_dependencies_info
    collect_file_structure_info
    collect_scripts_info
    collect_config_info
    collect_backup_info
    check_system_status
    collect_performance_info
    generate_recommendations
    
    # レポート表示
    display_report
}

# スクリプト実行
main "$@" 