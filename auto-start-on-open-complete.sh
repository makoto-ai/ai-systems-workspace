#!/bin/bash
# PC再起動後の完全自動復旧スクリプト（4大自動化システム統合版）

echo "🚀 完全自動復旧システム開始..."

# Python仮想環境の確認・起動
if [ -d ".venv" ]; then
    echo "🐍 Python仮想環境起動中..."
    # shellcheck source=/dev/null
    source .venv/bin/activate
    echo "✅ Python仮想環境: アクティブ"
else
    echo "⚠️  Python仮想環境が見つかりません"
fi

# 基本サービス復旧
echo "📊 基本サービス状況確認中..."
./quick-status.sh

echo "🚀 基本サービス自動起動中..."
./start-services.sh

# 4大自動化システム復旧
echo "🤖 4大自動化システム復旧中..."
./auto-restore-automation.sh

# 4大自動化システム動作確認
echo "🔍 4大自動化システム動作確認中..."
./check-automation-systems.sh

# 監視開始

# Obsidianバックアップ
echo "🗂️ Obsidianバックアップ実行中..."
./scripts/obsidian-backup.sh > /dev/null 2>&1 &
echo "✅ Obsidianバックアップ: 完了（バックグラウンド実行）"

echo "👀 バックグラウンド監視開始..."
./start-monitor.sh

echo "🎉 完全自動復旧完了！"
echo "📊 アクセスURL:"
echo " - バックエンド: http://localhost:8000"
echo " - フロントエンド: http://localhost:3000"
echo " - API仕様: http://localhost:8000/docs"
