#!/bin/bash
set -euo pipefail
REPO_DIR="/Users/araimakoto/ai-driven/ai-systems-workspace"
cd "$REPO_DIR"
TARGETS=("logs" "memory" "out" "data_integrity_report.json")
# 変更がなければ終了
if git diff --quiet -- "${TARGETS[@]}"; then
  echo "no changes"
  exit 0
fi
HOST=$(hostname -s || echo host)
TS=$(date +"%Y-%m-%d %H:%M:%S")
COUNT=$(git diff --name-only -- "${TARGETS[@]}" | wc -l | tr -d " \t")
BR=$(git rev-parse --abbrev-ref HEAD || echo main)
# ステージングとコミット
git add -A -- "${TARGETS[@]}"
MSG="chore(memory): auto-commit ${COUNT} files @ ${TS} (${HOST})"
GIT_COMMITTER_DATE="$TS" GIT_AUTHOR_DATE="$TS" git commit -m "$MSG" || true
# オプション: push（失敗しても続行）
if [ "${MEMORY_AUTO_PUSH:-0}" = "1" ]; then
  git push origin "$BR" || true
fi
