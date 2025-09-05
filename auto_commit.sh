#!/bin/bash
# Obsidian自動コミットスクリプト（未追跡含む）
set -e
cd "$(dirname "$0")"
# 変更があるか（未追跡含む）
if [ -z "$(git status --porcelain)" ]; then
  echo "変更なし - コミットをスキップ"
  exit 0
fi
# 全変更をステージングしてコミット
git add -A
GIT_COMMITTER_DATE="$(date '+%Y-%m-%d %H:%M:%S %z')" git commit -m "Auto commit: $(date '+%Y-%m-%d %H:%M:%S')"
echo "自動コミット完了: $(date)"
