#!/bin/bash
# 🎯 Quick Backup - 任意のプロジェクトから実行可能
# 使用法: ./quick-backup.sh "メッセージ" または ../quick-backup.sh "メッセージ"

MESSAGE="${1:-⚡ Quick backup: $(date '+%Y-%m-%d %H:%M:%S')}"

# カラー設定
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}⚡ Quick Backup実行中...${NC}"

# ai-systems-workspaceディレクトリを検索
WORKSPACE_DIR=""

# 現在のディレクトリがworkspaceかチェック
if [ -f "./master-backup.sh" ]; then
    WORKSPACE_DIR="."
# 一つ上のディレクトリがworkspaceかチェック
elif [ -f "../master-backup.sh" ]; then
    WORKSPACE_DIR=".."
# 二つ上のディレクトリがworkspaceかチェック  
elif [ -f "../../master-backup.sh" ]; then
    WORKSPACE_DIR="../.."
else
    echo "❌ master-backup.shが見つかりません"
    echo "ai-systems-workspaceディレクトリから実行してください"
    exit 1
fi

echo -e "${GREEN}✅ Workspace発見: $WORKSPACE_DIR${NC}"

# マスターバックアップ実行
cd "$WORKSPACE_DIR"
chmod +x master-backup.sh
./master-backup.sh "$MESSAGE"