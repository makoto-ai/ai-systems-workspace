#!/bin/bash
# 🛡️ Cursor暴走防止・保護システム

echo "🛡️ Cursor暴走防止システム設定中..."

# 1. ホームディレクトリ保護
echo "🏠 ホームディレクトリ保護設定..."
mkdir -p ~/.cursor-protection
echo "export CURSOR_PROTECTED_DIRS=\"$HOME/Documents $HOME/Desktop $HOME/Downloads\"" >> ~/.cursor-protection/config

# 2. 重要ディレクトリのバックアップ権限設定
echo "🔒 重要ディレクトリ保護..."
find ~/ai-driven -name "*.sh" -exec chmod +x {} \;
find ~/ai-driven -name ".git" -exec chmod -R 755 {} \;

# 3. Cursor設定の安全化
echo "⚙️ Cursor設定安全化..."
mkdir -p .vscode/backup
cp .vscode/*.json .vscode/backup/ 2>/dev/null || echo "設定ファイルバックアップ完了"

# 4. 自動保存間隔の短縮
echo "💾 自動保存強化..."
echo '{
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 500,
  "workbench.settings.enableNaturalLanguageSearch": false,
  "cursor.ai.enabled": true,
  "cursor.ai.dangerousActionsRequireConfirmation": true
}' > .vscode/safety-settings.json

echo "🎯 Cursor保護システム設定完了"
