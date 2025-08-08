#!/bin/bash
# PC再起動後の自動復旧スクリプト

echo "🔄 PC再起動後の自動復旧開始..."

# Python仮想環境の確認・起動
if [ -d ".venv" ]; then
    echo "🐍 Python仮想環境起動中..."
    source .venv/bin/activate
    echo "✅ Python仮想環境: アクティブ"
else
    echo "⚠️  Python仮想環境が見つかりません"
fi

# サービス状況確認
echo "📊 サービス状況確認中..."
./quick-status.sh

# 必要に応じてサービス起動
echo "🚀 サービス自動起動中..."
./start-services.sh

# 監視開始
echo "👀 バックグラウンド監視開始..."
./start-monitor.sh

echo "🎉 PC再起動後の復旧完了！"
