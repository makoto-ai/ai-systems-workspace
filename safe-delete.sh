#!/bin/bash
# 🛡️ 安全削除スクリプト
# 重要ファイルを絶対に削除させない保護システム

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROTECTION_SCRIPT="$SCRIPT_DIR/CRITICAL_FILE_PROTECTION.py"

# 色設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛡️ 安全削除システム${NC}"
echo "==============================="

# 保護システムの存在確認
if [ ! -f "$PROTECTION_SCRIPT" ]; then
    echo -e "${RED}❌ 保護システムが見つかりません: $PROTECTION_SCRIPT${NC}"
    exit 1
fi

# 引数チェック
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}⚠️ 使用法: $0 <削除対象ファイル/ディレクトリ...>${NC}"
    echo ""
    echo "例:"
    echo "  $0 __pycache__/"
    echo "  $0 *.pyc"
    echo "  $0 temp.log cache/"
    exit 1
fi

# 保護システム状態確認
echo -e "${BLUE}📊 保護システム状態:${NC}"
python3 "$PROTECTION_SCRIPT" status | grep -E "(保護有効|操作前バックアップ|確認要求)"
echo ""

# 削除対象表示
echo -e "${YELLOW}🎯 削除対象:${NC}"
for target in "$@"; do
    if [ -e "$target" ]; then
        echo -e "  ✅ ${target}"
    else
        echo -e "  ❌ ${target} (存在しません)"
    fi
done
echo ""

# 安全削除実行
echo -e "${GREEN}🔒 安全削除を実行中...${NC}"
python3 "$PROTECTION_SCRIPT" safe-rm "$@"

# 結果確認
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 削除完了${NC}"
    
    # 削除後の状況確認
    echo ""
    echo -e "${BLUE}📁 削除後の状況:${NC}"
    for target in "$@"; do
        if [ ! -e "$target" ]; then
            echo -e "  ✅ ${target} (削除済み)"
        else
            echo -e "  ⚠️ ${target} (残存)"
        fi
    done
else
    echo -e "${RED}❌ 削除に失敗または保護されました${NC}"
    echo ""
    echo -e "${YELLOW}💡 ヒント:${NC}"
    echo "  - 重要ファイルは保護されています"
    echo "  - 緊急復旧: $0 restore <ファイル名>"
    echo "  - 設定確認: $0 status"
fi