#!/bin/zsh
set -euo pipefail

KEEP=3
DRY_RUN=0

usage() {
  echo "Usage: $0 [--keep N] [--dry-run]" >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep)
      KEEP=${2:-3}; shift 2 ;;
    --dry-run)
      DRY_RUN=1; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

pause_watcher() {
  pkill -f 'chokidar' 2>/dev/null || true
  pkill -f 'auto-whiten.sh' 2>/dev/null || true
  rm -f .git/index.lock || true
}

resume_watcher() {
  nohup npm run auto:white --silent >/dev/null 2>&1 &
}

prune_pattern() {
  local pattern="$1"
  local keep="$2"
  # 取得（存在しない場合は空）
  local list
  list=$(ls -1t $pattern 2>/dev/null || true)
  [[ -z "$list" ]] && { echo "keep: none $pattern"; return 0; }
  local idx=1
  echo "$list" | while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    if (( idx > keep )); then
      if [[ $DRY_RUN -eq 1 ]]; then
        echo "DRY: rm -f $f"
      else
        rm -f "$f" || true
      fi
    fi
    idx=$((idx+1))
  done
}

git_untrack_pattern() {
  local pattern="$1"
  set +e
  for f in $pattern; do
    [[ -e "$f" ]] || continue
    git ls-files --error-unmatch "$f" >/dev/null 2>&1
    if [[ $? -eq 0 ]]; then
      if [[ $DRY_RUN -eq 1 ]]; then
        echo "DRY: git rm --cached -f $f"
      else
        git rm --cached -f "$f" 2>/dev/null || true
      fi
    fi
  done
  set -e
}

pause_watcher

prune_pattern "public/*.wav" "$KEEP"
prune_pattern "memory/snapshots/*.json" "$KEEP"

git_untrack_pattern "public/*.wav"
git_untrack_pattern "memory/snapshots/*.json"

if [[ $DRY_RUN -eq 0 ]]; then
  git add -A || true
  git commit -m "chore: prune artifacts (keep latest $KEEP)" || true
fi

resume_watcher

rem_wav=$(ls -1 public/*.wav 2>/dev/null | wc -l | tr -d ' ' || true)
rem_snap=$(ls -1 memory/snapshots/*.json 2>/dev/null | wc -l | tr -d ' ' || true)
echo "Remaining WAVs: ${rem_wav:-0}"
echo "Remaining snapshots: ${rem_snap:-0}"


