#!/bin/bash

# 🗄️ DBダンプ（日次想定）PostgreSQL/Redis 対応
# 使用: ./scripts/backup/db_dump.sh

set -euo pipefail

BACKUP_BASE="$HOME/Backups/db"
mkdir -p "$BACKUP_BASE"

DATE=$(date +%Y-%m-%d_%H%M)

# --- PostgreSQL ---
# 環境変数（必要に応じて設定）: PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
if command -v pg_dump >/dev/null 2>&1 && [[ -n "${PGDATABASE:-}" ]]; then
  OUT="$BACKUP_BASE/pg_${PGDATABASE}_${DATE}.dump"
  echo "📦 pg_dump -> $OUT"
  pg_dump -Fc -f "$OUT" || echo "⚠️ pg_dump failed"
fi

# --- Redis ---
if command -v redis-cli >/dev/null 2>&1; then
  OUT="$BACKUP_BASE/redis_${DATE}.rdb"
  echo "📦 redis save -> $OUT"
  # ローカル実行前提の簡易取得（環境に合わせて調整）
  redis-cli SAVE || true
  # 既定のRDBパスからコピー（linux/osxで異なるため候補検索）
  CANDIDATES=(/var/lib/redis/dump.rdb /usr/local/var/db/redis/dump.rdb $HOME/Library/Containers/com.redis.Redis/Data/dump.rdb)
  for p in "${CANDIDATES[@]}"; do
    if [[ -f "$p" ]]; then cp "$p" "$OUT" && break; fi
  done
fi

echo "✅ DB dump finished"


