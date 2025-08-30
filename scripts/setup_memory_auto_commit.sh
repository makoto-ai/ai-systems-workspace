#!/bin/bash
# Memory Auto-Commit Setup Script
# cron設定とlaunchdエージェント設定を行う

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT_PATH="${PROJECT_DIR}/scripts/memory_auto_commit.sh"

echo "🚀 Memory自動コミット設定開始..."
echo "プロジェクト: ${PROJECT_DIR}"

# 1. cron設定
echo "1️⃣ cron設定の追加..."
CRON_JOB="*/5 * * * * cd ${PROJECT_DIR} && ${SCRIPT_PATH} >> ${PROJECT_DIR}/logs/memory_auto_commit.log 2>&1"

# 既存のcronをバックアップ
crontab -l > /tmp/crontab.backup 2>/dev/null || echo "# New crontab" > /tmp/crontab.backup

# 重複チェック
if ! grep -q "memory_auto_commit.sh" /tmp/crontab.backup; then
    echo "${CRON_JOB}" >> /tmp/crontab.backup
    crontab /tmp/crontab.backup
    echo "✅ cron設定完了（5分間隔）"
else
    echo "ℹ️  cron設定は既に存在しています"
fi

# 2. ログディレクトリ作成
mkdir -p "${PROJECT_DIR}/logs"

# 3. launchdエージェントファイル作成（macOS推奨）
LAUNCHD_PATH="${HOME}/Library/LaunchAgents/com.ai-systems.memory-auto-commit.plist"
echo "2️⃣ launchdエージェント設定..."

cat > "${LAUNCHD_PATH}" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ai-systems.memory-auto-commit</string>
    <key>ProgramArguments</key>
    <array>
        <string>${SCRIPT_PATH}</string>
    </array>
    <key>StartInterval</key>
    <integer>300</integer>
    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>
    <key>StandardOutPath</key>
    <string>${PROJECT_DIR}/logs/memory_auto_commit.log</string>
    <key>StandardErrorPath</key>
    <string>${PROJECT_DIR}/logs/memory_auto_commit.log</string>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF

# launchdエージェントをロード
launchctl unload "${LAUNCHD_PATH}" 2>/dev/null || true
launchctl load "${LAUNCHD_PATH}"
echo "✅ launchdエージェント設定完了"

echo ""
echo "🎉 Memory自動コミット設定完了！"
echo "📊 設定内容:"
echo "• 実行間隔: 5分"
echo "• ログ出力: ${PROJECT_DIR}/logs/memory_auto_commit.log"
echo "• cron設定: 有効"
echo "• launchdエージェント: 有効"
echo ""
echo "🔍 動作確認:"
echo "tail -f ${PROJECT_DIR}/logs/memory_auto_commit.log"
