#!/bin/bash

# ⏰ cron自動バックアップ設定スクリプト
# 使用方法: ./scripts/backup/setup_cron_backup.sh

set -e

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "⏰ cron自動バックアップ設定開始"

# スクリプトパスの取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log "📁 プロジェクトルート: $PROJECT_ROOT"

# 1. 毎日バックアップ（毎朝3時）
DAILY_BACKUP_JOB="0 3 * * * bash '$PROJECT_ROOT/scripts/backup/daily_backup.sh' >> '$PROJECT_ROOT/logs/cron_daily_backup.log' 2>&1"

# 1b. restic オフサイトバックアップ（毎朝4時）
RESTIC_BACKUP_JOB="0 4 * * * bash '$PROJECT_ROOT/scripts/backup/restic_backup.sh' >> '$PROJECT_ROOT/logs/cron_restic_backup.log' 2>&1"

# 2. 週次フルバックアップ（毎週日曜日午前2時）
WEEKLY_BACKUP_JOB="0 2 * * 0 bash '$PROJECT_ROOT/scripts/backup/weekly_rsync.sh' >> '$PROJECT_ROOT/logs/cron_weekly_backup.log' 2>&1"

# 2b. 週次リストア検証（毎週日曜日午前3時）
RESTORE_VERIFY_JOB="0 3 * * 0 bash '$PROJECT_ROOT/scripts/backup/restic_restore_verify.sh' >> '$PROJECT_ROOT/logs/cron_restore_verify.log' 2>&1"

# 3. 現在のcronジョブを取得
CURRENT_CRON=$(crontab -l 2>/dev/null || echo "")

# 4. 既存のバックアップジョブを削除
log "🧹 既存のバックアップジョブを削除中..."
CURRENT_CRON=$(echo "$CURRENT_CRON" | grep -v "daily_backup.sh" | grep -v "weekly_rsync.sh" | grep -v "restic_backup.sh" | grep -v "restic_restore_verify.sh" || true)

# 5. 新しいバックアップジョブを追加
log "📝 新しいバックアップジョブを追加中..."
NEW_CRON="$CURRENT_CRON
# AIシステム自動バックアップ
$DAILY_BACKUP_JOB
$RESTIC_BACKUP_JOB
$WEEKLY_BACKUP_JOB
$RESTORE_VERIFY_JOB"

# 6. cronテーブルを更新
echo "$NEW_CRON" | crontab -

log "✅ cron設定完了"

# 7. ログディレクトリ作成
mkdir -p "$PROJECT_ROOT/logs"

# 8. 設定確認
log "📋 設定されたcronジョブ:"
crontab -l | grep -E "(daily_backup|weekly_rsync)"

# 9. テスト実行（オプション）
read -p "バックアップスクリプトをテスト実行しますか？ (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "🧪 テスト実行開始..."
    
    # 毎日バックアップのテスト
    log "📦 毎日バックアップテスト..."
    bash "$PROJECT_ROOT/scripts/backup/daily_backup.sh"
    
    log "✅ テスト実行完了"
fi

# 10. 設定完了情報
log "🎉 cron自動バックアップ設定完了！"
log ""
log "📋 設定内容:"
log "  - 毎日バックアップ: 毎朝3時実行"
log "  - 週次フルバックアップ: 毎週日曜日午前2時実行"
log "  - ログファイル: $PROJECT_ROOT/logs/cron_*.log"
log ""
log "💡 管理コマンド:"
log "  - cron確認: crontab -l"
log "  - cron編集: crontab -e"
log "  - ログ確認: tail -f $PROJECT_ROOT/logs/cron_*.log"
log "  - 手動実行: bash $PROJECT_ROOT/scripts/backup/daily_backup.sh"
log ""
log "⚠️ 注意事項:"
log "  - 外部ドライブの接続を確認してください"
log "  - 十分なディスク容量を確保してください"
log "  - 初回実行時は時間がかかる場合があります"
