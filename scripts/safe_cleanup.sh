#!/usr/bin/env bash
set -Eeuo pipefail

# Safe cleanup utility
# - Targets only caches/temp artifacts
# - Explicitly excludes critical dirs
# - Supports dry-run and apply modes
# - Optional log rotation (compress + retention)

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

DRY_RUN=1
ROTATE_LOGS=0
KEEP_LOGS_DAYS=30
COMPRESS_OLDER_THAN_DAYS=1

print_usage() {
  cat <<USAGE
Usage: scripts/safe_cleanup.sh [--apply] [--rotate-logs] [--keep-logs-days N] [--compress-older-than-days N]

Default is dry-run (preview only). Use --apply to actually delete.
Excludes: .git/, venv/, .venv/, backups/, test_backups/, memory/, uploads/, logs/, frontend/*/node_modules/
Targets (delete): __pycache__, .pytest_cache, .mypy_cache, .ruff_cache, .ipynb_checkpoints, .cache, htmlcov,
                  *.pyc, *.pyo, .DS_Store, *.swp, *.swo, *~, *.orig, *.rej, .coverage,
                  npm-debug.log*, yarn-error.log*, pnpm-debug.log*
Log rotation (if --rotate-logs):
  - compress *.log older than COMPRESS_OLDER_THAN_DAYS (gzip)
  - delete *.log.gz older than KEEP_LOGS_DAYS
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) DRY_RUN=0; shift ;;
    --rotate-logs) ROTATE_LOGS=1; shift ;;
    --keep-logs-days) KEEP_LOGS_DAYS="${2:-30}"; shift 2 ;;
    --compress-older-than-days) COMPRESS_OLDER_THAN_DAYS="${2:-1}"; shift 2 ;;
    -h|--help) print_usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; print_usage; exit 2 ;;
  esac
done

echo "Root: $ROOT_DIR"
if [[ $DRY_RUN -eq 1 ]]; then echo "Mode: DRY-RUN (no changes)"; else echo "Mode: APPLY (modifies files)"; fi

# Build prune expression for excluded directories
PRUNE=(
  -path "./.git" -o
  -path "./venv" -o
  -path "./.venv" -o
  -path "./backups" -o
  -path "./test_backups" -o
  -path "./memory" -o
  -path "./uploads" -o
  -path "./logs" -o
  -path "./frontend/voice-roleplay-frontend/node_modules"
)

deleted_dirs=0
deleted_files=0

delete_path() {
  local p="$1"
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY] rm -rf $p"
  else
    rm -rf "$p"
  fi
}

delete_file() {
  local p="$1"
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY] rm -f $p"
  else
    rm -f "$p"
  fi
}

echo "\n== Delete cache directories =="
while IFS= read -r -d '' d; do
  echo "$d"
  delete_path "$d" || true
  deleted_dirs=$((deleted_dirs+1))
done < <(find . \
  \( "${PRUNE[@]}" \) -prune -o \
  -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache -o -name .ipynb_checkpoints -o -name .cache -o -name htmlcov \) \
  -print0)

echo "\n== Delete junk files =="
while IFS= read -r -d '' f; do
  echo "$f"
  delete_file "$f" || true
  deleted_files=$((deleted_files+1))
done < <(find . \
  \( "${PRUNE[@]}" \) -prune -o \
  -type f \( -name "*.pyc" -o -name "*.pyo" -o -name ".DS_Store" -o -name "*.swp" -o -name "*.swo" -o -name "*~" -o -name "*.orig" -o -name "*.rej" -o -name ".coverage" -o -name "npm-debug.log*" -o -name "yarn-error.log*" -o -name "pnpm-debug.log*" \) \
  -print0)

echo "\n== Summary =="
echo "Deleted dirs (or would delete): $deleted_dirs"
echo "Deleted files (or would delete): $deleted_files"

rotate_logs() {
  local compress_days="$1" keep_days="$2"
  echo "\n== Log rotation =="
  # Compress *.log older than compress_days (not already .gz)
  while IFS= read -r -d '' f; do
    echo "Compress: $f"
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "[DRY] gzip -n $f"
    else
      gzip -n "$f" || true
    fi
  done < <(find ./logs -type f -name "*.log" -mtime +"$compress_days" -print0 2>/dev/null || true)

  # Delete compressed logs older than keep_days
  while IFS= read -r -d '' gz; do
    echo "Remove old: $gz"
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "[DRY] rm -f $gz"
    else
      rm -f "$gz" || true
    fi
  done < <(find ./logs -type f -name "*.log.gz" -mtime +"$keep_days" -print0 2>/dev/null || true)
}

if [[ $ROTATE_LOGS -eq 1 ]]; then
  rotate_logs "$COMPRESS_OLDER_THAN_DAYS" "$KEEP_LOGS_DAYS"
  echo "\nLog rotation done (mode: $([[ $DRY_RUN -eq 1 ]] && echo DRY-RUN || echo APPLY))"
fi

echo "\nDone."


