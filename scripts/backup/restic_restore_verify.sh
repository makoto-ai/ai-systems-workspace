#!/bin/bash

# 🧪 restic 週次リストア検証 + 通知（Slack/Webhook or メール）
# 使用: ./scripts/backup/restic_restore_verify.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

log(){ echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_DIR/restic_restore_verify.log"; }

# 設定読込
if [[ -f "$SCRIPT_DIR/restic.env" ]]; then
  # shellcheck disable=SC1091
  source "$SCRIPT_DIR/restic.env"
else
  log "❌ 設定ファイルがありません: $SCRIPT_DIR/restic.env (restic.env.example をコピーして作成)"
  exit 1
fi

if ! command -v restic >/dev/null 2>&1; then
  log "❌ restic が見つかりません。brew install restic でインストールしてください"
  exit 1
fi

RESTORE_DIR="$HOME/Backups/restore_verify_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESTORE_DIR"

TARGET_REL="ai-systems-workspace/docs/whisperx_setup.md"

log "🔁 Restoring sample file for verification..."
set +e
restic restore latest --target "$RESTORE_DIR" --include "$TARGET_REL"
STATUS=$?
set -e

MESSAGE=""
if [[ $STATUS -eq 0 && -f "$RESTORE_DIR/$TARGET_REL" ]]; then
  SUM=$(shasum -a 256 "$RESTORE_DIR/$TARGET_REL" | awk '{print $1}')
  MESSAGE="✅ Restic restore verify OK: $TARGET_REL (sha256=$SUM)"
  log "$MESSAGE"
else
  MESSAGE="❌ Restic restore verify FAILED"
  log "$MESSAGE"
fi

# 通知（Slack Webhook）
if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
  curl -s -X POST -H 'Content-type: application/json' \
    --data "{\"text\": \"$MESSAGE\"}" "$SLACK_WEBHOOK_URL" >/dev/null || true
fi

# メール通知（macOSのmailコマンドが設定済みなら）
if command -v mail >/dev/null 2>&1 && [[ -n "${ALERT_EMAIL:-}" ]]; then
  echo "$MESSAGE" | mail -s "Restic Restore Verify" "$ALERT_EMAIL" || true
fi

log "🧪 Verification finished: $MESSAGE"


