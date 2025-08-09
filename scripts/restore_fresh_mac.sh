#!/bin/bash

# 🧰 新規Mac復元スクリプト（idempotent）
# 目的:
#  - Homebrew/基本ツール/開発環境を自動セットアップ
#  - Python仮想環境と依存をインストール
#  - 既存のバックアップ・監視系スクリプトを有効化
#  - （任意）restic で最新スナップショットの検証復元
#
# 使い方:
#   bash scripts/restore_fresh_mac.sh
#
# オプション環境変数:
#   RESTIC_REPOSITORY, RESTIC_PASSWORD  … 設定されている場合のみ検証復元を実行
#   RESTIC_RESTORE_INCLUDE               … includeパス(複数は--includeを追加して編集)
#   PYTHON_VERSION                       … brewのpythonパッケージ指定 (例: 3.12) 既定: 3.12
#
set -euo pipefail

if [[ "${DEBUG:-}" != "" ]]; then set -x; fi

echo "🔁 Starting fresh Mac restore..."

# --- 変数とパス ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$WORKSPACE_ROOT/logs"
mkdir -p "$LOG_DIR"

PY_VER="${PYTHON_VERSION:-3.12}"
BREW_BIN="/opt/homebrew/bin/brew"
PYTHON_BIN="/opt/homebrew/bin/python${PY_VER%.*}"  # 例: /opt/homebrew/bin/python3.12

# --- ユーティリティ ---
log(){ echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_DIR/restore_fresh_mac.log"; }
exists(){ command -v "$1" >/dev/null 2>&1; }

# --- Xcode Command Line Tools ---
if ! xcode-select -p >/dev/null 2>&1; then
  log "🛠️ Installing Xcode Command Line Tools..."
  xcode-select --install || true
  log "ℹ️ インストール確認後、必要なら再実行してください"
fi

# --- Homebrew ---
if ! exists brew; then
  log "🍺 Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  echo 'eval "$('/opt/homebrew/bin/brew' shellenv)"' >> "$HOME/.zprofile"
  eval "$('/opt/homebrew/bin/brew' shellenv)"
else
  eval "$('$BREW_BIN' shellenv)"
fi

log "🍺 Updating Homebrew..."
brew update

# --- 必要ツール ---
log "📦 Installing base packages..."
brew install git jq curl wget coreutils gnupg openssl readline zlib || true
brew install python@${PY_VER} || true
brew install ffmpeg || true
brew install restic || true
brew install cloudflared || true

# --- Python 仮想環境 ---
log "🐍 Setting up Python virtual environment..."
PY_CMD="$PYTHON_BIN"
if [[ ! -x "$PY_CMD" ]]; then
  # フォールバック: システムpython
  PY_CMD="$(command -v python3 || true)"
fi

if [[ -z "${PY_CMD}" ]]; then
  log "❌ Python3 が見つかりません。Homebrewのpython@${PY_VER}を確認してください。"; exit 1
fi

cd "$WORKSPACE_ROOT"

if [[ ! -d .venv ]]; then
  log "🔧 Creating venv at .venv"
  "$PY_CMD" -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel

if [[ -f requirements.txt ]]; then
  log "📚 Installing Python dependencies from requirements.txt"
  pip install -r requirements.txt
fi

# --- WhisperX API（任意） ---
if [[ -f whisperx_api.py ]]; then
  log "🎙️ WhisperX API available (manual start): uvicorn whisperx_api:app --host 0.0.0.0 --port 5000"
fi

# --- バックアップのcron設定 ---
if [[ -f scripts/backup/setup_cron_backup.sh ]]; then
  log "⏰ Configuring cron jobs for backups..."
  bash scripts/backup/setup_cron_backup.sh || true
fi

# --- restic 検証復元（任意） ---
if exists restic && [[ -n "${RESTIC_REPOSITORY:-}" && -n "${RESTIC_PASSWORD:-}" ]]; then
  log "🧪 Running restic test restore..."
  RESTORE_DIR="$HOME/Backups/restore_test_$(date +%Y%m%d_%H%M%S)"
  mkdir -p "$RESTORE_DIR"
  INCLUDE_OPT=""
  if [[ -n "${RESTIC_RESTORE_INCLUDE:-}" ]]; then
    INCLUDE_OPT="--include \"$RESTIC_RESTORE_INCLUDE\""
  fi
  # shellcheck disable=SC2086
  bash -lc "restic snapshots && restic restore latest --target '$RESTORE_DIR' $INCLUDE_OPT"
  log "✅ Restore test completed: $RESTORE_DIR"
else
  log "ℹ️ restic 環境変数が未設定のため、検証復元はスキップしました。"
fi

# --- GitHub Secrets/環境変数のヒント ---
if [[ ! -f .env ]]; then
  cat > .env <<EOF
# ローカルのみ: CIではGitHub Secrets/Actions で注入
GROQ_API_KEY=
WHISPERX_ENDPOINT=
EOF
  log "📝 .env を作成しました（ローカル開発用）。必要に応じて値を設定してください。"
fi

log "🎉 Fresh Mac restore completed."
log "📍 Workspace: $WORKSPACE_ROOT"
log "💡 次の手順:"
log "  - source .venv/bin/activate"
log "  - uvicorn whisperx_api:app --host 0.0.0.0 --port 5000  (任意)"
log "  - GitHub Secrets に GROQ_API_KEY / WHISPERX_ENDPOINT を登録 (CI用)"


