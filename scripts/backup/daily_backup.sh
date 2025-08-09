#!/bin/bash

# 📦 毎日自動バックアップスクリプト
# 使用方法: ./scripts/backup/daily_backup.sh
# cron登録: 0 3 * * * bash ~/ai-driven/ai-systems-workspace/scripts/backup/daily_backup.sh

set -e

# ログ設定
LOG_FILE="logs/backup_$(date +%Y-%m-%d).log"
mkdir -p logs

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🚀 自動バックアップ開始"

# 日付フォルダ作成
DATE=$(date +%Y-%m-%d_%H-%M)
BACKUP_ROOT=~/Backups/ai-dev-backup
DEST="$BACKUP_ROOT/$DATE"
mkdir -p "$DEST"

log "📁 バックアップ先: $DEST"

# 1. AIシステム全体のバックアップ
log "📦 AIシステム全体をバックアップ中..."
if [ -d ~/ai-driven/ai-systems-workspace ]; then
    rsync -avh --exclude='.git' --exclude='__pycache__' --exclude='.venv' \
        ~/ai-driven/ai-systems-workspace/ "$DEST/ai-systems-workspace/"
    log "✅ AIシステムバックアップ完了"
else
    log "⚠️ AIシステムディレクトリが見つかりません"
fi

# 2. Obsidian Vault バックアップ
log "📚 Obsidian Vault をバックアップ中..."
OBSIDIAN_PATH="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Obsidian"
if [ -d "$OBSIDIAN_PATH" ]; then
    rsync -avh --exclude='.DS_Store' --exclude='workspace.json' \
        "$OBSIDIAN_PATH/" "$DEST/obsidian-vault/"
    log "✅ Obsidian Vault バックアップ完了"
else
    log "⚠️ Obsidian Vault が見つかりません: $OBSIDIAN_PATH"
fi

# 3. WhisperX出力のバックアップ
log "🎙️ WhisperX出力をバックアップ中..."
WHISPERX_OUTPUTS="$HOME/whisperx_outputs"
if [ -d "$WHISPERX_OUTPUTS" ]; then
    rsync -avh "$WHISPERX_OUTPUTS/" "$DEST/whisperx-outputs/"
    log "✅ WhisperX出力バックアップ完了"
else
    log "ℹ️ WhisperX出力ディレクトリが見つかりません: $WHISPERX_OUTPUTS"
fi

# 4. 設定ファイルのバックアップ
log "⚙️ 設定ファイルをバックアップ中..."
mkdir -p "$DEST/configs"

# .zshrc, .bash_profile など
if [ -f ~/.zshrc ]; then
    cp ~/.zshrc "$DEST/configs/"
fi
if [ -f ~/.bash_profile ]; then
    cp ~/.bash_profile "$DEST/configs/"
fi

# Docker設定
if [ -f ~/.docker/config.json ]; then
    cp ~/.docker/config.json "$DEST/configs/"
fi

log "✅ 設定ファイルバックアップ完了"

# 5. バックアップ情報の記録
BACKUP_INFO="$DEST/backup_info.txt"
cat > "$BACKUP_INFO" << EOF
バックアップ情報
================
日時: $(date)
バックアップ先: $DEST
サイズ: $(du -sh "$DEST" | cut -f1)

含まれる内容:
- AIシステム全体
- Obsidian Vault
- WhisperX出力
- 設定ファイル

システム情報:
- OS: $(uname -s)
- ホスト名: $(hostname)
- ユーザー: $(whoami)
EOF

log "📝 バックアップ情報記録完了"

# 6. 古いバックアップの削除（30日以上前）
log "🧹 古いバックアップを削除中..."
find "$BACKUP_ROOT" -type d -name "*" -mtime +30 -exec rm -rf {} \; 2>/dev/null || true

# 7. バックアップ完了通知
BACKUP_SIZE=$(du -sh "$DEST" | cut -f1)
log "🎉 バックアップ完了！"
log "📊 バックアップサイズ: $BACKUP_SIZE"
log "📁 保存先: $DEST"

# 8. 成功通知（オプション）
if command -v osascript &> /dev/null; then
    osascript -e "display notification \"バックアップ完了: $BACKUP_SIZE\" with title \"AIシステム自動バックアップ\""
fi

log "✅ 自動バックアップ完了"
