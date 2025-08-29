#!/bin/zsh
set -euo pipefail
# プロジェクトルート
ROOT="/Users/araimakoto/ai-driven/ai-systems-workspace"
cd "$ROOT"
# Python 実行パス（pyenvのものを利用）
PYTHON="/Users/araimakoto/.pyenv/versions/3.12.8/bin/python"
# リモート同期先（iCloud既定フォルダ）
export REMOTE_BACKUP_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/AI-Backups"
# 自動バックアップ開始
exec "$PYTHON" scripts/auto_backup_system.py --auto
