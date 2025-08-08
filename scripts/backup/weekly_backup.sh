#!/bin/bash

# 🧠 AI Voice Roleplay System - Weekly Backup Script
# 作成日: 2025-08-04
# 目的: WhisperX/Obsidian/VoiceAIシステムの定期バックアップ

set -e  # エラー時に停止

# 設定
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_ROOT="$HOME/Backups/voice-ai-system"
BACKUP_DIR="$BACKUP_ROOT/$DATE"
LOG_FILE="$BACKUP_ROOT/backup.log"

# バックアップディレクトリ作成
mkdir -p "$BACKUP_ROOT"
mkdir -p "$BACKUP_DIR"

# ログ関数
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# バックアップ開始
log_message "🚀 Starting weekly backup for Voice AI System..."

log_message "📁 Created backup directory: $BACKUP_DIR"

# 1. AIシステムのバックアップ
if [ -d "$HOME/ai-driven/ai-systems-workspace" ]; then
    log_message "📦 Backing up AI Systems Workspace..."
    cp -r "$HOME/ai-driven/ai-systems-workspace" "$BACKUP_DIR/"
    log_message "✅ AI Systems backup completed"
else
    log_message "⚠️  AI Systems Workspace not found at $HOME/ai-driven/ai-systems-workspace"
fi

# 2. Obsidian Vaultのバックアップ
OBSIDIAN_VAULT="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Obsidian"
OBSIDIAN_VAULT_ALT="$HOME/Documents/Obsidian"
if [ -d "$OBSIDIAN_VAULT" ]; then
    log_message "📝 Backing up Obsidian Vault..."
    cp -r "$OBSIDIAN_VAULT" "$BACKUP_DIR/"
    log_message "✅ Obsidian backup completed"
elif [ -d "$OBSIDIAN_VAULT_ALT" ]; then
    log_message "📝 Backing up Obsidian Vault (alternative location)..."
    cp -r "$OBSIDIAN_VAULT_ALT" "$BACKUP_DIR/"
    log_message "✅ Obsidian backup completed"
else
    log_message "⚠️  Obsidian Vault not found at $OBSIDIAN_VAULT or $OBSIDIAN_VAULT_ALT"
fi

# 3. WhisperX関連ファイルのバックアップ
WHISPERX_DIR="$HOME/whisperx"
if [ -d "$WHISPERX_DIR" ]; then
    log_message "🎤 Backing up WhisperX files..."
    cp -r "$WHISPERX_DIR" "$BACKUP_DIR/"
    log_message "✅ WhisperX backup completed"
else
    log_message "⚠️  WhisperX directory not found at $WHISPERX_DIR"
fi

# 4. 音声ファイルのバックアップ
VOICE_FILES="$HOME/Downloads/voice_files"
VOICE_FILES_ALT="$HOME/Downloads/audio"
VOICE_FILES_ALT2="./data/audio_files"
if [ -d "$VOICE_FILES" ]; then
    log_message "🎵 Backing up voice files..."
    cp -r "$VOICE_FILES" "$BACKUP_DIR/"
    log_message "✅ Voice files backup completed"
elif [ -d "$VOICE_FILES_ALT" ]; then
    log_message "🎵 Backing up voice files (alternative location)..."
    cp -r "$VOICE_FILES_ALT" "$BACKUP_DIR/"
    log_message "✅ Voice files backup completed"
elif [ -d "$VOICE_FILES_ALT2" ]; then
    log_message "🎵 Backing up voice files (project location)..."
    cp -r "$VOICE_FILES_ALT2" "$BACKUP_DIR/"
    log_message "✅ Voice files backup completed"
else
    log_message "⚠️  Voice files directory not found at common locations"
fi

# 5. 環境設定ファイルのバックアップ
log_message "⚙️  Backing up configuration files..."
if [ -f "$HOME/.env" ]; then
    cp "$HOME/.env" "$BACKUP_DIR/"
    log_message "✅ .env backup completed"
fi

# 6. バックアップサイズと統計
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log_message "📊 Backup size: $BACKUP_SIZE"

# 7. 古いバックアップの削除（30日以上古いもの）
log_message "🧹 Cleaning old backups (older than 30 days)..."
find "$BACKUP_ROOT" -type d -name "2025-*" -mtime +30 -exec rm -rf {} \; 2>/dev/null || true

# 8. バックアップ完了通知
log_message "🎉 Weekly backup completed successfully!"
log_message "📁 Backup location: $BACKUP_DIR"
log_message "📏 Total size: $BACKUP_SIZE"

# 9. 成功通知（オプション）
if command -v osascript &> /dev/null; then
    osascript -e 'display notification "Voice AI System backup completed successfully!" with title "Backup Complete"'
fi

echo "✅ Backup completed at $DATE"
echo "📁 Location: $BACKUP_DIR"
echo "📏 Size: $BACKUP_SIZE" 