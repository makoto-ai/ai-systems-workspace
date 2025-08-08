#!/bin/bash
# MCP-Composer連携パイプライン実行スクリプト

set -e

# ログ設定
LOG_FILE="logs/pipeline_execution.log"
mkdir -p logs

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 引数チェック
if [ $# -eq 0 ]; then
    log "❌ 使用方法: $0 <task_name> [parameters...]"
    log "利用可能なタスク:"
    log "  - doi_verification <doi>"
    log "  - hallucination_check <text>"
    log "  - structure_validation <file>"
    log "  - quality_analysis"
    log "  - security_scan"
    log "  - performance_test"
    exit 1
fi

TASK_NAME="$1"
shift

log "🚀 パイプライン実行開始: $TASK_NAME"

case $TASK_NAME in
    "doi_verification")
        if [ -z "$1" ]; then
            log "❌ DOIが指定されていません"
            log "使用例: ./scripts/run_pipeline.sh doi_verification 10.1038/s41586-020-2649-2"
            exit 1
        fi
        
        # DOI形式の基本的な検証
        if [[ ! "$1" =~ ^10\.[0-9]+ ]]; then
            log "❌ 無効なDOI形式: $1"
            log "DOIは10.で始まる必要があります"
            exit 1
        fi
        
        log "📚 DOI検証実行: $1"
        
        # タイムアウト設定付きで実行（timeoutコマンドが利用できない場合は通常実行）
        if command -v timeout >/dev/null 2>&1; then
            timeout 60 python3 scripts/verify_doi.py "$1" 2>&1
            exit_code=$?
            
            if [ $exit_code -eq 0 ]; then
                log "✅ DOI検証成功"
            elif [ $exit_code -eq 124 ]; then
                log "❌ DOI検証タイムアウト（60秒）"
                exit 1
            else
                log "❌ DOI検証失敗（終了コード: $exit_code）"
                exit $exit_code
            fi
        else
            # timeoutコマンドが利用できない場合は通常実行
            python3 scripts/verify_doi.py "$1" 2>&1
            exit_code=$?
            
            if [ $exit_code -eq 0 ]; then
                log "✅ DOI検証成功"
            else
                log "❌ DOI検証失敗（終了コード: $exit_code）"
                exit $exit_code
            fi
        fi
        ;;
    
    "hallucination_check")
        if [ -z "$1" ]; then
            log "❌ テキストが指定されていません"
            log "使用例: ./scripts/run_pipeline.sh hallucination_check 'テキスト内容'"
            exit 1
        fi
        log "🧠 幻覚チェック実行"
        result=$(python3 scripts/check_hallucination.py "$1" 2>&1)
        exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            log "✅ 幻覚チェック成功"
            echo "$result"
        else
            log "❌ 幻覚チェック失敗: $result"
            exit $exit_code
        fi
        ;;
    
    "structure_validation")
        if [ -z "$1" ]; then
            log "❌ ファイルが指定されていません"
            log "使用例: ./scripts/run_pipeline.sh structure_validation data/sample.json"
            exit 1
        fi
        log "📋 構造検証実行: $1"
        result=$(python3 scripts/validate_structure.py "$1" 2>&1)
        exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            log "✅ 構造検証成功"
            echo "$result"
        else
            log "❌ 構造検証失敗: $result"
            exit $exit_code
        fi
        ;;
    
    "quality_analysis")
        log "📊 品質分析実行"
        result=$(python3 scripts/quality_score_plot.py 2>&1)
        exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            log "✅ 品質分析成功"
            echo "$result"
        else
            log "❌ 品質分析失敗: $result"
            exit $exit_code
        fi
        ;;
    
    "security_scan")
        log "🔒 セキュリティスキャン実行"
        result=$(python3 scripts/security_scan.py 2>&1)
        exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            log "✅ セキュリティスキャン成功"
            echo "$result"
        else
            log "❌ セキュリティスキャン失敗: $result"
            exit $exit_code
        fi
        ;;
    
    "performance_test")
        log "⚡ パフォーマンステスト実行"
        result=$(python3 scripts/performance_test.py 2>&1)
        exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            log "✅ パフォーマンステスト成功"
            echo "$result"
        else
            log "❌ パフォーマンステスト失敗: $result"
            exit $exit_code
        fi
        ;;
    
    *)
        log "❌ 未知のタスク: $TASK_NAME"
        log "利用可能なタスク: doi_verification, hallucination_check, structure_validation, quality_analysis, security_scan, performance_test"
        exit 1
        ;;
esac

log "✅ パイプライン実行完了: $TASK_NAME" 