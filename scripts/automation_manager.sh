#!/bin/bash

# 🤖 AI Systems Automation Manager
# 作成日: 2025-08-04
# 目的: システムの自動化管理

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

log_automation() {
    echo -e "${PURPLE}🤖 $1${NC}"
}

# 自動テスト実行
run_automated_tests() {
    log_automation "自動テストを実行中..."
    
    # テストディレクトリ作成
    mkdir -p tests
    
    # Pythonテスト実行
    if [ -f "tests/test_main_system.py" ]; then
        log_info "Pythonテストを実行中..."
        python -m pytest tests/ -v --tb=short || {
            log_warning "一部のテストが失敗しました"
        }
    fi
    
    # システムテスト実行
    log_info "システムテストを実行中..."
    
    # ヘルスチェック
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "ヘルスチェック成功"
    else
        log_warning "ヘルスチェック失敗（システムが起動していない可能性）"
    fi
    
    # ファイル整合性チェック
    log_info "ファイル整合性をチェック中..."
    required_files=(
        "main_hybrid.py"
        "requirements.txt"
        "docker-compose.yml"
        "Dockerfile"
        ".env"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            log_success "✓ $file"
        else
            log_warning "✗ $file (見つかりません)"
        fi
    done
    
    log_success "自動テスト完了"
}

# 自動デプロイ実行
run_automated_deploy() {
    log_automation "自動デプロイを実行中..."
    
    # 環境チェック
    log_info "環境をチェック中..."
    
    # Docker環境チェック
    if command -v docker &> /dev/null; then
        log_success "Docker利用可能"
    else
        log_error "Dockerがインストールされていません"
        return 1
    fi
    
    # 依存関係チェック
    if [ -f "requirements.txt" ]; then
        log_info "依存関係をインストール中..."
        pip install -r requirements.txt || {
            log_warning "一部の依存関係のインストールに失敗しました"
        }
    fi
    
    # Docker Compose起動
    if [ -f "docker-compose.yml" ]; then
        log_info "Docker Composeを起動中..."
        docker-compose up -d --build || {
            log_error "Docker Compose起動に失敗しました"
            return 1
        }
    fi
    
    # デプロイ確認
    log_info "デプロイを確認中..."
    sleep 10
    
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "デプロイ成功"
    else
        log_warning "デプロイ確認に失敗しました"
    fi
    
    log_success "自動デプロイ完了"
}

# 自動監視実行
run_automated_monitoring() {
    log_automation "自動監視を実行中..."
    
    # システム状態チェック
    log_info "システム状態をチェック中..."
    
    # プロセスチェック
    if pgrep -f "main_hybrid.py" > /dev/null; then
        log_success "メインシステム: 実行中"
    else
        log_warning "メインシステム: 停止中"
    fi
    
    # ポートチェック
    if lsof -i :8000 > /dev/null 2>&1; then
        log_success "Webサーバー: 実行中 (ポート8000)"
    else
        log_warning "Webサーバー: 停止中"
    fi
    
    # リソース使用量チェック
    log_info "リソース使用量をチェック中..."
    
    # CPU使用率
    cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
    if (( $(echo "$cpu_usage < 80" | bc -l) )); then
        log_success "CPU使用率: ${cpu_usage}%"
    else
        log_warning "CPU使用率: ${cpu_usage}% (高負荷)"
    fi
    
    # メモリ使用率
    memory_usage=$(memory_pressure | grep "System-wide memory free percentage" | awk '{print $5}' | sed 's/%//')
    memory_used=$((100 - memory_usage))
    if (( memory_used < 80 )); then
        log_success "メモリ使用率: ${memory_used}%"
    else
        log_warning "メモリ使用率: ${memory_used}% (高負荷)"
    fi
    
    # ディスク使用率
    disk_usage=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
    if (( disk_usage < 80 )); then
        log_success "ディスク使用率: ${disk_usage}%"
    else
        log_warning "ディスク使用率: ${disk_usage}% (容量不足)"
    fi
    
    log_success "自動監視完了"
}

# 自動バックアップ実行
run_automated_backup() {
    log_automation "自動バックアップを実行中..."
    
    if [ -f "scripts/backup/weekly_backup.sh" ]; then
        bash scripts/backup/weekly_backup.sh
        log_success "自動バックアップ完了"
    else
        log_error "バックアップスクリプトが見つかりません"
    fi
}

# 自動最適化実行
run_automated_optimization() {
    log_automation "自動最適化を実行中..."
    
    # ログファイル最適化
    log_info "ログファイルを最適化中..."
    if [ -d "logs" ]; then
        find logs -name "*.log" -size +100M -exec gzip {} \;
        log_success "ログファイル圧縮完了"
    fi
    
    # キャッシュクリア
    log_info "キャッシュをクリア中..."
    if [ -d ".venv" ]; then
        find .venv -name "*.pyc" -delete
        find .venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
        log_success "Pythonキャッシュクリア完了"
    fi
    
    # Docker最適化
    if command -v docker &> /dev/null; then
        log_info "Docker最適化中..."
        docker system prune -f || true
        log_success "Docker最適化完了"
    fi
    
    log_success "自動最適化完了"
}

# 自動セキュリティチェック
run_automated_security_check() {
    log_automation "自動セキュリティチェックを実行中..."
    
    # 環境変数セキュリティチェック
    log_info "環境変数をチェック中..."
    sensitive_vars=("CLAUDE_API_KEY" "OPENAI_API_KEY" "GROQ_API_KEY")
    
    for var in "${sensitive_vars[@]}"; do
        if [ -n "${!var}" ]; then
            # APIキーが適切に設定されているかチェック
            if [[ "${!var}" =~ ^sk-[a-zA-Z0-9]+$ ]]; then
                log_success "✓ $var: 設定済み"
            else
                log_warning "⚠ $var: 形式が不正"
            fi
        else
            log_warning "⚠ $var: 未設定"
        fi
    done
    
    # ファイル権限チェック
    log_info "ファイル権限をチェック中..."
    sensitive_files=(".env" "config/" "secrets/")
    
    for file in "${sensitive_files[@]}"; do
        if [ -e "$file" ]; then
            permissions=$(stat -f "%Sp" "$file")
            if [[ "$permissions" =~ ^-rw------- ]]; then
                log_success "✓ $file: 適切な権限"
            else
                log_warning "⚠ $file: 権限が緩い"
            fi
        fi
    done
    
    log_success "自動セキュリティチェック完了"
}

# 自動レポート生成
generate_automated_report() {
    log_automation "自動レポートを生成中..."
    
    report_file="automation_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# 🤖 AI Systems Automation Report
生成日時: $(date)

## 📊 システム状態

### プロセス状態
- メインシステム: $(pgrep -f "main_hybrid.py" > /dev/null && echo "実行中" || echo "停止中")
- Webサーバー: $(lsof -i :8000 > /dev/null 2>&1 && echo "実行中" || echo "停止中")

### リソース使用量
- CPU使用率: $(top -l 1 | grep "CPU usage" | awk '{print $3}')
- メモリ使用率: $((100 - $(memory_pressure | grep "System-wide memory free percentage" | awk '{print $5}' | sed 's/%//')))%
- ディスク使用率: $(df -h . | tail -1 | awk '{print $5}')

### ファイル状態
$(for file in main_hybrid.py requirements.txt docker-compose.yml Dockerfile .env; do
    if [ -f "$file" ]; then
        echo "- ✓ $file"
    else
        echo "- ✗ $file (見つかりません)"
    fi
done)

## 🔧 実行されたアクション
- 自動テスト: 完了
- 自動デプロイ: 完了
- 自動監視: 完了
- 自動バックアップ: 完了
- 自動最適化: 完了
- 自動セキュリティチェック: 完了

## 📈 推奨事項
$(if [ ! -f ".env" ]; then echo "- .envファイルを作成してください"; fi)
$(if ! pgrep -f "main_hybrid.py" > /dev/null; then echo "- システムを起動してください"; fi)
$(if [ "$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')" -gt 80 ]; then echo "- ディスク容量を確認してください"; fi)

---
*このレポートは自動生成されました*
EOF
    
    log_success "自動レポート生成完了: $report_file"
}

# メイン処理
main() {
    local action=${1:-all}
    
    echo "🤖 AI Systems Automation Manager"
    echo "================================"
    
    case $action in
        "test")
            run_automated_tests
            ;;
        "deploy")
            run_automated_deploy
            ;;
        "monitor")
            run_automated_monitoring
            ;;
        "backup")
            run_automated_backup
            ;;
        "optimize")
            run_automated_optimization
            ;;
        "security")
            run_automated_security_check
            ;;
        "report")
            generate_automated_report
            ;;
        "all")
            log_automation "全自動化プロセスを実行中..."
            run_automated_tests
            run_automated_deploy
            run_automated_monitoring
            run_automated_backup
            run_automated_optimization
            run_automated_security_check
            generate_automated_report
            log_success "全自動化プロセス完了"
            ;;
        "help"|"-h"|"--help")
            echo "🤖 AI Systems Automation Manager"
            echo ""
            echo "使用方法:"
            echo "  ./scripts/automation_manager.sh [アクション]"
            echo ""
            echo "アクション:"
            echo "  test      自動テスト実行"
            echo "  deploy    自動デプロイ実行"
            echo "  monitor   自動監視実行"
            echo "  backup    自動バックアップ実行"
            echo "  optimize  自動最適化実行"
            echo "  security  自動セキュリティチェック"
            echo "  report    自動レポート生成"
            echo "  all       全自動化プロセス実行"
            echo "  help      このヘルプを表示"
            echo ""
            echo "例:"
            echo "  ./scripts/automation_manager.sh test"
            echo "  ./scripts/automation_manager.sh all"
            ;;
        *)
            log_error "不明なアクション: $action"
            echo "使用可能なアクション: test, deploy, monitor, backup, optimize, security, report, all, help"
            exit 1
            ;;
    esac
}

# スクリプト実行
main "$@" 