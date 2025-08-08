#!/bin/bash
# 🚀 AI Systems Workspace - マスターバックアップシステム
# 全プロジェクトの完全性検証付き自動バックアップ

# カラー設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
MESSAGE="${1:-🚀 Master Backup: $TIMESTAMP}"

echo -e "${BLUE}🚀 AI Systems Workspace - マスターバックアップ開始${NC}"
echo -e "${PURPLE}📅 実行時刻: $TIMESTAMP${NC}"

# プロジェクト検出
PROJECTS=()
FAILED_PROJECTS=()
SUCCESS_PROJECTS=()

# Git リポジトリを自動検出
for dir in */; do
    if [ -d "$dir/.git" ]; then
        PROJECTS+=("${dir%/}")
    fi
done

echo -e "\n${YELLOW}📂 検出されたプロジェクト: ${#PROJECTS[@]}個${NC}"
for project in "${PROJECTS[@]}"; do
    echo -e "${BLUE}  📁 $project${NC}"
done

# 各プロジェクトをバックアップ
echo -e "\n${YELLOW}🔄 プロジェクト別バックアップ開始${NC}"

for project in "${PROJECTS[@]}"; do
    echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📦 処理中: $project${NC}"
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    cd "$project" || continue
    
    # プロジェクト固有の検証実行
    VERIFICATION_PASSED=true
    
    # 1. voice-roleplay-system専用検証
    if [ "$project" == "voice-roleplay-system" ]; then
        echo -e "${YELLOW}🔍 Voice System専用検証実行${NC}"
        if [ -f "./backup-verify.sh" ]; then
            if ./backup-verify.sh > /dev/null 2>&1; then
                echo -e "${GREEN}✅ Voice System検証: 合格${NC}"
            else
                echo -e "${RED}❌ Voice System検証: 失敗${NC}"
                VERIFICATION_PASSED=false
            fi
        else
            echo -e "${YELLOW}⚠️  Voice System検証スクリプトなし${NC}"
        fi
    fi
    
    # 2. paper_research_system専用検証
    if [ "$project" == "paper_research_system" ]; then
        echo -e "${YELLOW}🔍 Paper Research専用検証実行${NC}"
        
        # 重要ファイル確認
        PAPER_CRITICAL=(
            "main_integrated.py"
            "main_citation_network.py"
            "requirements.txt"
            "database/citation_graph.db"
        )
        
        PAPER_ERRORS=0
        for file in "${PAPER_CRITICAL[@]}"; do
            if [ -f "$file" ]; then
                echo -e "${GREEN}✅ $file${NC}"
            else
                echo -e "${RED}❌ $file 欠損${NC}"
                PAPER_ERRORS=$((PAPER_ERRORS + 1))
            fi
        done
        
        if [ $PAPER_ERRORS -eq 0 ]; then
            echo -e "${GREEN}✅ Paper Research検証: 合格${NC}"
        else
            echo -e "${RED}❌ Paper Research検証: 失敗 ($PAPER_ERRORS errors)${NC}"
            VERIFICATION_PASSED=false
        fi
    fi
    
    # 3. monitoring_system専用検証
    if [ "$project" == "monitoring_system" ]; then
        echo -e "${YELLOW}🔍 Monitoring System専用検証実行${NC}"
        
        MONITOR_CRITICAL=(
            "capacity_monitor.py"
            "config/thresholds.json"
        )
        
        MONITOR_ERRORS=0
        for file in "${MONITOR_CRITICAL[@]}"; do
            if [ -f "$file" ]; then
                echo -e "${GREEN}✅ $file${NC}"
            else
                echo -e "${RED}❌ $file 欠損${NC}"
                MONITOR_ERRORS=$((MONITOR_ERRORS + 1))
            fi
        done
        
        if [ $MONITOR_ERRORS -eq 0 ]; then
            echo -e "${GREEN}✅ Monitoring System検証: 合格${NC}"
        else
            echo -e "${RED}❌ Monitoring System検証: 失敗 ($MONITOR_ERRORS errors)${NC}"
            VERIFICATION_PASSED=false
        fi
    fi
    
    # Git変更確認とコミット
    if [ "$VERIFICATION_PASSED" = true ]; then
        if [ -n "$(git status --porcelain)" ]; then
            echo -e "${YELLOW}📝 変更検出 - コミット実行${NC}"
            
            # プロジェクトサイズ情報
            PROJECT_SIZE=$(du -sh . | cut -f1)
            PROJECT_MESSAGE="$MESSAGE [$project: $PROJECT_SIZE]"
            
            git add -A
            if git commit -m "$PROJECT_MESSAGE"; then
                echo -e "${GREEN}✅ $project: コミット完了${NC}"
                
                # リモートプッシュ試行
                if git remote | grep -q "origin"; then
                    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
                    if git push origin "$CURRENT_BRANCH" 2>/dev/null; then
                        echo -e "${GREEN}✅ $project: GitHubプッシュ完了${NC}"
                    else
                        echo -e "${YELLOW}⚠️  $project: プッシュ失敗（ネットワーク問題）${NC}"
                    fi
                fi
                
                SUCCESS_PROJECTS+=("$project")
            else
                echo -e "${RED}❌ $project: コミット失敗${NC}"
                FAILED_PROJECTS+=("$project")
            fi
        else
            echo -e "${BLUE}ℹ️  $project: 変更なし${NC}"
            SUCCESS_PROJECTS+=("$project")
        fi
    else
        echo -e "${RED}🚨 $project: 検証失敗のためバックアップスキップ${NC}"
        FAILED_PROJECTS+=("$project")
    fi
    
    cd ..
done

# 最終結果レポート
echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 マスターバックアップ完了レポート${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${GREEN}✅ 成功プロジェクト: ${#SUCCESS_PROJECTS[@]}個${NC}"
for project in "${SUCCESS_PROJECTS[@]}"; do
    echo -e "${GREEN}  ✓ $project${NC}"
done

if [ ${#FAILED_PROJECTS[@]} -gt 0 ]; then
    echo -e "${RED}❌ 失敗プロジェクト: ${#FAILED_PROJECTS[@]}個${NC}"
    for project in "${FAILED_PROJECTS[@]}"; do
        echo -e "${RED}  ✗ $project${NC}"
    done
fi

# ログ記録
echo "[$TIMESTAMP] MASTER BACKUP - Success: ${#SUCCESS_PROJECTS[@]}, Failed: ${#FAILED_PROJECTS[@]} - $MESSAGE" >> master-backup.log

if [ ${#FAILED_PROJECTS[@]} -eq 0 ]; then
    echo -e "\n${GREEN}🎉 全プロジェクトバックアップ完了！${NC}"
    exit 0
else
    echo -e "\n${YELLOW}⚠️  一部プロジェクトでエラーが発生しました${NC}"
    exit 1
fi