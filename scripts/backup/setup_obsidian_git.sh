#!/bin/bash

# 🧾 Obsidian Gitバージョン管理セットアップスクリプト
# 使用方法: ./scripts/backup/setup_obsidian_git.sh

set -e

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "🧾 Obsidian Gitバージョン管理セットアップ開始"

# Obsidian Vault パス
OBSIDIAN_PATH="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Obsidian"

if [ ! -d "$OBSIDIAN_PATH" ]; then
    log "❌ Obsidian Vault が見つかりません: $OBSIDIAN_PATH"
    log "💡 ObsidianのiCloud同期が有効になっているか確認してください"
    exit 1
fi

log "📁 Obsidian Vault パス: $OBSIDIAN_PATH"

# 1. .gitignore ファイル作成
log "📝 .gitignore ファイルを作成中..."
cat > "$OBSIDIAN_PATH/.gitignore" << 'EOF'
# macOS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Obsidian
workspace.json
workspace-mobile.json
.hotkeys.json
.hotkeys-mobile.json
.graphviewrc
.graphviewrc-mobile
.trash/

# プラグイン設定（必要に応じて除外）
# .obsidian/plugins/*/

# 一時ファイル
*.tmp
*.temp
*.swp
*.swo

# ログファイル
*.log

# バックアップファイル
*.bak
*.backup
EOF

log "✅ .gitignore ファイル作成完了"

# 2. Git初期化
log "🔧 Gitリポジトリを初期化中..."
cd "$OBSIDIAN_PATH"

if [ ! -d ".git" ]; then
    git init
    log "✅ Gitリポジトリ初期化完了"
else
    log "ℹ️ Gitリポジトリは既に存在します"
fi

# 3. 初期コミット
log "📝 初期コミットを作成中..."
git add .
git commit -m "Initial commit: Obsidian Vault versioning started - $(date)"

log "✅ 初期コミット完了"

# 4. 自動コミットスクリプト作成
AUTO_COMMIT_SCRIPT="$OBSIDIAN_PATH/auto_commit.sh"
cat > "$AUTO_COMMIT_SCRIPT" << 'EOF'
#!/bin/bash
# Obsidian自動コミットスクリプト

cd "$(dirname "$0")"

# 変更があるかチェック
if git diff --quiet && git diff --cached --quiet; then
    echo "変更なし - コミットをスキップ"
    exit 0
fi

# 変更をコミット
git add .
git commit -m "Auto commit: $(date '+%Y-%m-%d %H:%M:%S')"

echo "自動コミット完了: $(date)"
EOF

chmod +x "$AUTO_COMMIT_SCRIPT"
log "✅ 自動コミットスクリプト作成完了"

# 5. cron登録（毎時自動コミット）
log "⏰ cronに自動コミットを登録中..."
CRON_JOB="0 * * * * cd '$OBSIDIAN_PATH' && ./auto_commit.sh >> logs/auto_commit.log 2>&1"

# 既存のcronジョブを確認
if crontab -l 2>/dev/null | grep -q "auto_commit.sh"; then
    log "ℹ️ 自動コミットは既にcronに登録されています"
else
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    log "✅ 自動コミットをcronに登録しました"
fi

# 6. ログディレクトリ作成
mkdir -p "$OBSIDIAN_PATH/logs"

# 7. GitHub連携（オプション）
read -p "GitHubリモートリポジトリを設定しますか？ (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "GitHubリポジトリURLを入力してください: " GITHUB_URL
    if [ ! -z "$GITHUB_URL" ]; then
        git remote add origin "$GITHUB_URL"
        git branch -M main
        git push -u origin main
        log "✅ GitHubリモート設定完了"
    fi
fi

# 8. セットアップ完了情報
log "🎉 Obsidian Gitバージョン管理セットアップ完了！"
log ""
log "📋 設定内容:"
log "  - Gitリポジトリ: $OBSIDIAN_PATH"
log "  - .gitignore: 不要ファイル除外設定済み"
log "  - 自動コミット: 毎時実行（cron登録済み）"
log "  - ログファイル: $OBSIDIAN_PATH/logs/auto_commit.log"
log ""
log "💡 使用方法:"
log "  - 手動コミット: cd '$OBSIDIAN_PATH' && git add . && git commit -m 'メッセージ'"
log "  - 自動コミット: 毎時自動実行"
log "  - ログ確認: tail -f '$OBSIDIAN_PATH/logs/auto_commit.log'"
