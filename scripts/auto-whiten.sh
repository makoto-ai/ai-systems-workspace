#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

# --- PID lock (single instance) ---
lock_dir="/tmp/auto_whiten.lock"
if mkdir "$lock_dir" 2>/dev/null; then
  echo $$ > "$lock_dir/pid"
  trap 'rm -rf "$lock_dir"' EXIT INT TERM
else
  echo "ℹ️ auto-whiten: another instance running (lock). Skipping."
  exit 0
fi

# 変更が無ければ終了
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  exit 0
fi

# 危険そうなファイルがステージに乗っていたら中止（必要に応じて拡張）
if git status --porcelain | cut -c4- | grep -E '\.env$|\.pem$|\.key$|secrets?/|credentials?' >/dev/null 2>&1; then
  echo "❌ 秘密ファイルの変更を検知。自動コミット中止。"
  exit 1
fi

# --- Backoff when index.lock exists or pre-commit is operating ---
max_tries=5
delay=2
try=1
while [ -f .git/index.lock ] && [ $try -le $max_tries ]; do
  echo "⏳ waiting for .git/index.lock (attempt $try/$max_tries)"
  sleep $delay
  try=$((try+1))
  delay=$((delay*2))
done

if [ -f .git/index.lock ]; then
  echo "⚠️ index.lock persists. Skipping this cycle to avoid conflicts."
  exit 0
fi

# すべて追加してコミット
msg="auto: sync $(date +'%Y-%m-%d %H:%M:%S')"
git add -A
git commit -m "$msg" || exit 0

# （任意）main/masterに積みたくない場合は下記を有効化
# branch="$(git rev-parse --abbrev-ref HEAD)"
# if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
#   git switch -c auto-sync 2>/dev/null || git switch auto-sync
# fi

echo "✅ 自動コミット：$msg"


