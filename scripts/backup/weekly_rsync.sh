#!/bin/bash

# 🗂️ 週次フルバックアップスクリプト（rsync）
# 使用方法: ./scripts/backup/weekly_rsync.sh
# cron登録: 0 2 * * 0 bash ~/ai-driven/ai-systems-workspace/scripts/backup/weekly_rsync.sh

set -e

# ログ設定
LOG_FILE="logs/rsync_backup_$(date +%Y-%m-%d).log"
mkdir -p logs

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🚀 週次フルバックアップ開始"

# バックアップ先の確認
BACKUP_DRIVE="/Volumes/BACKUP_DRIVE"
if [ ! -d "$BACKUP_DRIVE" ]; then
    log "❌ バックアップドライブが見つかりません: $BACKUP_DRIVE"
    log "💡 外部ドライブを接続するか、パスを変更してください"
    exit 1
fi

# バックアップ先ディレクトリ作成
MIRROR_DIR="$BACKUP_DRIVE/ai-system-mirror"
mkdir -p "$MIRROR_DIR"

log "📁 バックアップ先: $MIRROR_DIR"

# 1. AIシステム全体のミラーリング
log "📦 AIシステム全体をミラーリング中..."
if [ -d ~/ai-driven/ai-systems-workspace ]; then
    rsync -avh --delete \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='.venv' \
        --exclude='node_modules' \
        --exclude='*.log' \
        --exclude='.DS_Store' \
        ~/ai-driven/ai-systems-workspace/ "$MIRROR_DIR/ai-systems-workspace/"
    log "✅ AIシステムミラーリング完了"
else
    log "⚠️ AIシステムディレクトリが見つかりません"
fi

# 2. Obsidian Vault のミラーリング
log "📚 Obsidian Vault をミラーリング中..."
OBSIDIAN_PATH="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Obsidian"
if [ -d "$OBSIDIAN_PATH" ]; then
    rsync -avh --delete \
        --exclude='.DS_Store' \
        --exclude='workspace.json' \
        --exclude='.trash' \
        "$OBSIDIAN_PATH/" "$MIRROR_DIR/obsidian-vault/"
    log "✅ Obsidian Vault ミラーリング完了"
else
    log "⚠️ Obsidian Vault が見つかりません: $OBSIDIAN_PATH"
fi

# 3. WhisperX出力のミラーリング
log "🎙️ WhisperX出力をミラーリング中..."
WHISPERX_OUTPUTS="$HOME/whisperx_outputs"
if [ -d "$WHISPERX_OUTPUTS" ]; then
    rsync -avh --delete "$WHISPERX_OUTPUTS/" "$MIRROR_DIR/whisperx-outputs/"
    log "✅ WhisperX出力ミラーリング完了"
else
    log "ℹ️ WhisperX出力ディレクトリが見つかりません: $WHISPERX_OUTPUTS"
fi

# 4. 設定ファイルのミラーリング
log "⚙️ 設定ファイルをミラーリング中..."
mkdir -p "$MIRROR_DIR/configs"

# シェル設定
if [ -f ~/.zshrc ]; then
    cp ~/.zshrc "$MIRROR_DIR/configs/"
fi
if [ -f ~/.bash_profile ]; then
    cp ~/.bash_profile "$MIRROR_DIR/configs/"
fi

# Docker設定
if [ -f ~/.docker/config.json ]; then
    cp ~/.docker/config.json "$MIRROR_DIR/configs/"
fi

# SSH設定
if [ -d ~/.ssh ]; then
    rsync -avh ~/.ssh/ "$MIRROR_DIR/configs/ssh/"
fi

log "✅ 設定ファイルミラーリング完了"

# 5. バックアップ情報の記録
BACKUP_INFO="$MIRROR_DIR/backup_info.txt"
cat > "$BACKUP_INFO" << EOF
週次フルバックアップ情報
========================
日時: $(date)
バックアップ先: $MIRROR_DIR
サイズ: $(du -sh "$MIRROR_DIR" | cut -f1)

含まれる内容:
- AIシステム全体（ミラーリング）
- Obsidian Vault（ミラーリング）
- WhisperX出力（ミラーリング）
- 設定ファイル

システム情報:
- OS: $(uname -s)
- ホスト名: $(hostname)
- ユーザー: $(whoami)
- ディスク使用量: $(df -h "$BACKUP_DRIVE" | tail -1)
EOF

log "📝 バックアップ情報記録完了"

# 6. バックアップ完了通知
BACKUP_SIZE=$(du -sh "$MIRROR_DIR" | cut -f1)
log "🎉 週次フルバックアップ完了！"
log "📊 バックアップサイズ: $BACKUP_SIZE"
log "📁 保存先: $MIRROR_DIR"

# 7. 成功通知（オプション）
if command -v osascript &> /dev/null; then
    osascript -e "display notification \"週次バックアップ完了: $BACKUP_SIZE\" with title \"AIシステム週次バックアップ\""
fi

log "✅ 週次フルバックアップ完了"
