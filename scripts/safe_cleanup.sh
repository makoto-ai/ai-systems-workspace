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
# out/ retention settings (safe defaults)
CLEAN_OUT=0
OUT_KEEP_DAYS=7
OUT_MAX_TOTAL_MB=100

print_usage() {
  cat <<USAGE
Usage: scripts/safe_cleanup.sh [--apply] [--rotate-logs] [--keep-logs-days N] [--compress-older-than-days N] [--clean-out] [--out-keep-days N] [--out-max-total-mb N]

Default is dry-run (preview only). Use --apply to actually delete.
Excludes: .git/, venv/, .venv/, backups/, test_backups/, memory/, uploads/, logs/, frontend/*/node_modules/
Targets (delete): __pycache__, .pytest_cache, .mypy_cache, .ruff_cache, .ipynb_checkpoints, .cache, htmlcov,
                  *.pyc, *.pyo, .DS_Store, *.swp, *.swo, *~, *.orig, *.rej, .coverage,
                  npm-debug.log*, yarn-error.log*, pnpm-debug.log*
Log rotation (if --rotate-logs):
  - compress *.log older than COMPRESS_OLDER_THAN_DAYS (gzip)
  - delete *.log.gz older than KEEP_LOGS_DAYS

Out directory cleanup (if --clean-out):
  - delete files in out/ older than OUT_KEEP_DAYS (jsonl/json/md default)
  - if total out/ size exceeds OUT_MAX_TOTAL_MB, delete oldest overflow files
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) DRY_RUN=0; shift ;;
    --rotate-logs) ROTATE_LOGS=1; shift ;;
    --keep-logs-days) KEEP_LOGS_DAYS="${2:-30}"; shift 2 ;;
    --compress-older-than-days) COMPRESS_OLDER_THAN_DAYS="${2:-1}"; shift 2 ;;
    --clean-out) CLEAN_OUT=1; shift ;;
    --out-keep-days) OUT_KEEP_DAYS="${2:-7}"; shift 2 ;;
    --out-max-total-mb) OUT_MAX_TOTAL_MB="${2:-100}"; shift 2 ;;
    -h|--help) print_usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; print_usage; exit 2 ;;
  esac
done

echo "Root: $ROOT_DIR"
if [[ $DRY_RUN -eq 1 ]]; then echo "Mode: DRY-RUN (no changes)"; else echo "Mode: APPLY (modifies files)"; fi

# Ensure logs directory exists (harmless if already present)
mkdir -p logs || true

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

cleanup_out() {
  local keep_days="$1" max_total_mb="$2"
  echo "\n== Clean up out/ directory =="
  mkdir -p out || true

  # Delete by age (conservative patterns)
  while IFS= read -r -d '' f; do
    echo "Remove old: $f"
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "[DRY] rm -f $f"
    else
      rm -f "$f" || true
    fi
  done < <(find ./out -type f \
           \( -name "*.jsonl" -o -name "*.json" -o -name "*.md" -o -name "*.log" \) \
           -mtime +"$keep_days" -print0 2>/dev/null || true)

  # Enforce total size cap (oldest first)
  # Compute total size in KB
  local total_kb
  total_kb=$(du -sk ./out 2>/dev/null | awk '{print $1}')
  total_kb=${total_kb:-0}
  local cap_kb=$(( max_total_mb * 1024 ))
  if [[ "$total_kb" -gt "$cap_kb" ]]; then
    echo "Total out/ size ${total_kb}KB exceeds cap ${cap_kb}KB. Pruning oldest files..."
    # List files by mtime ascending (oldest first)
    mapfile -t files < <(find ./out -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | awk '{ $1=""; sub(/^ /,""); print }')
    for fp in "${files[@]}"; do
      # Recompute size periodically
      total_kb=$(du -sk ./out 2>/dev/null | awk '{print $1}')
      if [[ "$total_kb" -le "$cap_kb" ]]; then break; fi
      echo "Prune: $fp"
      if [[ $DRY_RUN -eq 1 ]]; then
        echo "[DRY] rm -f $fp"
      else
        rm -f "$fp" || true
      fi
    done
  else
    echo "out/ size within cap (${total_kb}KB <= ${cap_kb}KB)"
  fi
}

if [[ $CLEAN_OUT -eq 1 ]]; then
  cleanup_out "$OUT_KEEP_DAYS" "$OUT_MAX_TOTAL_MB"
  echo "\nout/ cleanup done (mode: $([[ $DRY_RUN -eq 1 ]] && echo DRY-RUN || echo APPLY))"
fi

echo "\nDone."


