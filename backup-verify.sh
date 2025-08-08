#!/bin/bash
# 📋 完全バックアップ検証システム
# 不完全なバックアップを防止する事前チェック機能

# カラー設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 バックアップ完全性検証開始...${NC}"

# 検証結果
ERRORS=0
WARNINGS=0

# 1. 論文検索システムの検証
echo -e "\n${YELLOW}📚 論文検索システム検証:${NC}"

if [ -d "paper_research_system" ]; then
    PAPER_SIZE=$(du -sm paper_research_system 2>/dev/null | cut -f1)
    if [ "$PAPER_SIZE" -lt 50 ]; then
        echo -e "${RED}❌ 論文システムサイズ異常: ${PAPER_SIZE}MB (最小50MB必要)${NC}"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✅ 論文システムサイズ: ${PAPER_SIZE}MB${NC}"
    fi
    
    # 重要ファイルの確認
    CRITICAL_FILES=(
        "paper_research_system/main_integrated.py"
        "paper_research_system/main_citation_network.py"
        "paper_research_system/requirements.txt"
        "paper_research_system/.venv/bin/activate"
        "paper_research_system/database/citation_graph.db"
        "paper_research_system/run.sh"
    )
    
    for file in "${CRITICAL_FILES[@]}"; do
        if [ -f "$file" ]; then
            SIZE=$(ls -lah "$file" 2>/dev/null | awk '{print $5}')
            echo -e "${GREEN}✅ $file (${SIZE})${NC}"
        else
            echo -e "${RED}❌ 重要ファイル欠損: $file${NC}"
            ERRORS=$((ERRORS + 1))
        fi
    done
    
    # 仮想環境の検証
    if [ -f "paper_research_system/.venv/bin/activate" ]; then
        cd paper_research_system
        source .venv/bin/activate 2>/dev/null
        if python -c "import numpy, scipy, networkx" 2>/dev/null; then
            echo -e "${GREEN}✅ 仮想環境: NumPy/SciPy/NetworkX正常${NC}"
        else
            echo -e "${RED}❌ 仮想環境: 必要ライブラリ欠損${NC}"
            ERRORS=$((ERRORS + 1))
        fi
        cd ..
    else
        echo -e "${RED}❌ 仮想環境ディレクトリ欠損${NC}"
        ERRORS=$((ERRORS + 1))
    fi
    
else
    echo -e "${RED}❌ 論文検索システムディレクトリ欠損${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 2. 音声システムの検証
echo -e "\n${YELLOW}🎤 音声ロールプレイシステム検証:${NC}"

VOICE_CRITICAL=(
    "app/main.py"
    "docker-compose.yml"
    "requirements.txt"
    "DATABASE_SCHEMA.sql"
)

for file in "${VOICE_CRITICAL[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${YELLOW}⚠️  音声システムファイル: $file${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# 3. Obsidianデータの検証
echo -e "\n${YELLOW}🧠 Obsidianナレッジ検証:${NC}"

if [ -d "docs/obsidian-knowledge" ]; then
    OBSIDIAN_SIZE=$(du -sm docs/obsidian-knowledge 2>/dev/null | cut -f1)
    OBSIDIAN_FILES=$(find docs/obsidian-knowledge -name "*.md" | wc -l)
    echo -e "${GREEN}✅ Obsidianデータ: ${OBSIDIAN_SIZE}MB, ${OBSIDIAN_FILES}ファイル${NC}"
else
    echo -e "${YELLOW}⚠️  Obsidianディレクトリなし${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# 4. 総合結果
echo -e "\n${BLUE}📊 検証結果サマリー:${NC}"
echo -e "エラー: ${ERRORS}"
echo -e "警告: ${WARNINGS}"

if [ $ERRORS -eq 0 ]; then
    echo -e "\n${GREEN}🎉 バックアップ完全性検証: 合格${NC}"
    echo -e "${GREEN}✅ 全ての重要データが正常に含まれています${NC}"
    exit 0
else
    echo -e "\n${RED}🚨 バックアップ完全性検証: 失敗${NC}"
    echo -e "${RED}❌ ${ERRORS}件の重大な問題があります${NC}"
    echo -e "${RED}⚠️  このままバックアップすると不完全なデータが保存されます${NC}"
    exit 1
fi