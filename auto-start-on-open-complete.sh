#!/bin/bash
# PC再起動後の完全自動復旧スクリプト（4大自動化システム統合版）
set -euo pipefail

echo "🚀 完全自動復旧システム開始..."

# ルート決定・遷移
ROOT="/Users/araimakoto/ai-driven/ai-systems-workspace"
cd "$ROOT"
mkdir -p logs

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
./quick-status.sh || true

echo "🚀 基本サービス自動起動中..."
./start-services.sh || true

# ハイブリッド（8000）死活確認→未稼働なら起動
if pgrep -f "main_hybrid:app" >/dev/null; then
  echo "ℹ️  hybrid(8000) 稼働中"
else
  echo "▶️ hybrid(8000) 起動中..."
  nohup python3 -u main_hybrid.py > logs/hybrid_restart.log 2>&1 &
  sleep 2
  echo "✅ hybrid 起動トリガ送信済み"
fi

# 4大自動化システム復旧
echo "🤖 4大自動化システム復旧中..."
./auto-restore-automation.sh || true

# 4大自動化システム動作確認
echo "🔍 4大自動化システム動作確認中..."
./check-automation-systems.sh || true

# 監視開始

# Obsidianバックアップ
echo "🗂️ Obsidianバックアップ実行中..."
./scripts/obsidian-backup.sh > logs/obsidian_backup.log 2>&1 &
echo "✅ Obsidianバックアップ: 実行開始（バックグラウンド）"

echo "👀 バックグラウンド監視開始..."
./start-monitor.sh || true

echo "🎉 完全自動復旧完了！"
echo "📊 アクセスURL:"
echo " - Hybrid API: http://localhost:8000 (docs: /docs)"
echo " - 補助Backend(app.main): http://localhost:8010 (必要時)"
echo " - フロントエンド: http://localhost:3000 (存在時)"
