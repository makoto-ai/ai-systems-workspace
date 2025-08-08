#!/bin/bash
# 4大自動化システム動作確認スクリプト

echo "🔍 4大自動化システム動作確認開始..."

# 1. GitHub Actions ワークフロー確認
echo "📊 【システム1】リアルタイム監視システム"
if [ -f ".github/workflows/monitoring.yml" ]; then
    echo "✅ monitoring.yml: 存在"
    grep -q "cron.*\*/5" .github/workflows/monitoring.yml && echo "✅ 5分毎実行設定: OK" || echo "⚠️  Cronスケジュール要確認"
else
    echo "❌ monitoring.yml: 不在"
fi

# 2. セキュリティシステム確認
echo "🛡️  【システム2】セキュリティ自動化システム"
if [ -f ".github/workflows/security-scan.yml" ]; then
    echo "✅ security-scan.yml: 存在"
    grep -q "cron.*18.*\*.*\*" .github/workflows/security-scan.yml && echo "✅ 毎日18:00 UTC実行設定: OK" || echo "⚠️  セキュリティスケジュール要確認"
else
    echo "❌ security-scan.yml: 不在"
fi

if [ -f ".github/dependabot.yml" ]; then
    echo "✅ dependabot.yml: 存在"
else
    echo "❌ dependabot.yml: 不在"
fi

# 3. データ完全性システム確認
echo "💾 【システム3】データ完全性検証システム"
if [ -f "scripts/data-integrity-check.py" ]; then
    echo "✅ data-integrity-check.py: 存在"
    python scripts/data-integrity-check.py --version 2>/dev/null && echo "✅ Python実行: OK" || echo "⚠️  実行権限要確認"
else
    echo "❌ data-integrity-check.py: 不在"
fi

# 4. GitHub Actions統合確認
echo "🔄 【システム4】GitHub Actions統合自動化システム"
WORKFLOW_COUNT=$(ls .github/workflows/*.yml 2>/dev/null | wc -l)
echo "✅ ワークフロー数: $WORKFLOW_COUNT個"

if [ $WORKFLOW_COUNT -ge 4 ]; then
    echo "✅ 統合ワークフロー: 十分"
else
    echo "⚠️  ワークフロー数不足"
fi

# Git remote確認
if git remote -v | grep -q "github.com"; then
    echo "✅ GitHub連携: OK"
else
    echo "⚠️  GitHub連携要確認"
fi

echo "🎯 4大自動化システム確認完了"
