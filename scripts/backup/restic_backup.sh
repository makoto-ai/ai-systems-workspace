#!/bin/bash

# 🔐 restic オフサイト暗号化バックアップ（日次想定）
# 使用: ./scripts/backup/restic_backup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

log(){ echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_DIR/restic_backup.log"; }

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

# 環境変数チェック
if [[ -z "${RESTIC_REPOSITORY:-}" || -z "${RESTIC_PASSWORD:-}" ]]; then
  log "❌ RESTIC_REPOSITORY または RESTIC_PASSWORD が未設定です"
  exit 1
fi

# バックアップ実行
log "🚀 restic backup start"

EX_ARGS=()
for e in "${EXCLUDES[@]:-}"; do
  EX_ARGS+=("--exclude" "$e")
done

restic backup "${BACKUP_PATHS[@]}" "${EX_ARGS[@]}"

# 保持ポリシー
restic forget \
  --keep-daily "${RESTIC_KEEP_DAILY:-14}" \
  --keep-weekly "${RESTIC_KEEP_WEEKLY:-8}" \
  --keep-monthly "${RESTIC_KEEP_MONTHLY:-6}" \
  --prune

log "✅ restic backup completed"


