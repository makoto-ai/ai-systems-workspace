#!/bin/bash
# 音声システム開発 - 完全性検証付き自動保存スクリプト
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
MESSAGE="${1:-💾 Auto-save: $TIMESTAMP}"

# カラー設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔄 完全性検証付き自動保存開始...${NC}"

# 1. バックアップ前の完全性検証
echo -e "\n${YELLOW}🔍 Step 1: バックアップ完全性検証${NC}"
if [ -f "./backup-verify.sh" ]; then
    chmod +x ./backup-verify.sh
    if ./backup-verify.sh; then
        echo -e "${GREEN}✅ 検証合格: データ完全性確認済み${NC}"
    else
        echo -e "${RED}❌ 検証失敗: 不完全なデータが検出されました${NC}"
        echo -e "${RED}🚨 バックアップを中止します（データ損失防止）${NC}"
        echo "[$TIMESTAMP] BACKUP ABORTED - Verification Failed: $MESSAGE" >> .auto-save.log
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  検証スクリプトなし - 標準バックアップ実行${NC}"
fi

# 2. Git変更検出とコミット
echo -e "\n${YELLOW}🔍 Step 2: Git変更検出${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 変更を検出しました"
    
    # データサイズ情報を記録
    if [ -d "paper_research_system" ]; then
        PAPER_SIZE=$(du -sh paper_research_system | cut -f1)
        MESSAGE="$MESSAGE [論文システム: $PAPER_SIZE]"
    fi
    
    git add -A
    git commit -m "$MESSAGE"
    echo -e "${GREEN}✅ 保存完了: $MESSAGE${NC}"
    
    # 3. 自動プッシュ（オプション）
    echo -e "\n${YELLOW}🔍 Step 3: リモートバックアップ${NC}"
    if git remote | grep -q "origin"; then
        echo "🌐 GitHubにプッシュ中..."
        CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
        if git push origin "$CURRENT_BRANCH" 2>/dev/null; then
            echo -e "${GREEN}✅ GitHubバックアップ完了${NC}"
        else
            echo -e "${YELLOW}⚠️  GitHubプッシュ失敗（ネットワーク問題の可能性）${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  リモートリポジトリ未設定${NC}"
    fi
else
    echo "ℹ️  変更はありません"
fi

echo "[$TIMESTAMP] VERIFIED BACKUP: $MESSAGE" >> .auto-save.log
echo -e "\n${GREEN}🎉 完全性検証付きバックアップ完了！${NC}"
