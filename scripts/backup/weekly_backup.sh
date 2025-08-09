#!/bin/bash
# WhisperX / Obsidian / VoiceAIシステムの定期バックアップ

set -e

# ログ設定
LOG_FILE="logs/weekly_backup.log"
mkdir -p logs

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# バックアップ実行
main() {
    log "🚀 週次バックアップ開始"
    
    # 日時設定
    DATE=$(date +%Y-%m-%d_%H-%M-%S)
    BACKUP_DIR=~/Backups/voice-ai-system/$DATE
    mkdir -p "$BACKUP_DIR"
    
    log "📁 バックアップ先: $BACKUP_DIR"
    
    # 1. AI Systems Workspace バックアップ
    if [ -d ~/ai-driven/ai-systems-workspace ]; then
        log "📦 AI Systems Workspace バックアップ中..."
        cp -r ~/ai-driven/ai-systems-workspace "$BACKUP_DIR/"
        log "✅ AI Systems Workspace バックアップ完了"
    else
        log "⚠️  AI Systems Workspace が見つかりません"
    fi
    
    # 2. Obsidian Vault バックアップ
    if [ -d ~/Library/Mobile\ Documents/com~apple~CloudDocs/Obsidian ]; then
        log "📝 Obsidian Vault バックアップ中..."
        cp -r ~/Library/Mobile\ Documents/com~apple~CloudDocs/Obsidian "$BACKUP_DIR/"
        log "✅ Obsidian Vault バックアップ完了"
    else
        log "⚠️  Obsidian Vault が見つかりません"
    fi
    
    # 3. Voice Roleplay System バックアップ
    if [ -d ~/ai-driven/voice-roleplay-system ]; then
        log "🎤 Voice Roleplay System バックアップ中..."
        cp -r ~/ai-driven/voice-roleplay-system "$BACKUP_DIR/"
        log "✅ Voice Roleplay System バックアップ完了"
    else
        log "⚠️  Voice Roleplay System が見つかりません"
    fi
    
    # 4. 設定ファイル バックアップ
    log "⚙️  設定ファイル バックアップ中..."
    cp ~/.cursor/config "$BACKUP_DIR/" 2>/dev/null || log "⚠️  .cursor/config が見つかりません"
    cp ~/.env* "$BACKUP_DIR/" 2>/dev/null || log "⚠️  .env ファイルが見つかりません"
    log "✅ 設定ファイル バックアップ完了"
    
    # 5. バックアップ情報記録
    BACKUP_INFO="$BACKUP_DIR/backup_info.txt"
    cat > "$BACKUP_INFO" << EOF
バックアップ情報
================
日時: $DATE
バックアップ先: $BACKUP_DIR
内容:
- AI Systems Workspace
- Obsidian Vault  
- Voice Roleplay System
- 設定ファイル

システム情報:
- OS: $(uname -s)
- ホスト名: $(hostname)
- ユーザー: $(whoami)
EOF
    
    # 6. バックアップサイズ確認
    BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
    log "📊 バックアップサイズ: $BACKUP_SIZE"
    
    # 7. 古いバックアップ削除（30日以上）
    find ~/Backups/voice-ai-system -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null || true
    log "🧹 30日以上古いバックアップを削除しました"
    
    log "🎉 週次バックアップ完了: $DATE"
    log "📁 バックアップ先: $BACKUP_DIR"
    log "📊 バックアップサイズ: $BACKUP_SIZE"
}

# スクリプト実行
main "$@" 