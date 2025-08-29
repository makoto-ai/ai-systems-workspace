#!/bin/bash
# 論文検索システム - 実行スクリプト
# 仮想環境を自動でアクティベートして実行

# カラー設定
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎯 Academic Paper Research Assistant${NC}"
echo -e "${GREEN}📚 論文検索システム起動中...${NC}"

# 仮想環境の確認とアクティベート
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  仮想環境が見つかりません。作成中...${NC}"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

echo -e "${GREEN}✅ 仮想環境アクティブ: $(python --version)${NC}"
echo -e "${GREEN}✅ NumPy: $(python -c 'import numpy; print(numpy.__version__)')${NC}"
echo ""

# 使用可能なコマンド表示
echo -e "${BLUE}📋 利用可能なコマンド:${NC}"
echo ""
echo -e "${YELLOW}1. 統合検索（メイン）:${NC}"
echo "   python main_integrated.py 'sales psychology' --save-obsidian"
echo ""
echo -e "${YELLOW}2. 引用ネットワーク分析:${NC}"
echo "   python main_citation_network.py build 'sales psychology'"
echo "   python main_citation_network.py visualize -a [分析名]"
echo ""
echo -e "${YELLOW}3. 専門検索（営業心理学）:${NC}"
echo "   python main_specialized.py 'negotiation techniques'"
echo ""
echo -e "${YELLOW}4. 高度フィルター検索:${NC}"
echo "   python main_filter.py 'machine learning' --interactive"
echo ""
echo -e "${YELLOW}5. 検索履歴管理:${NC}"
echo "   python main_history.py list"
echo ""

# 引数がある場合は直接実行
if [ $# -gt 0 ]; then
    echo -e "${GREEN}🚀 実行中: $@${NC}"
    "$@"
fi