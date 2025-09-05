#!/bin/zsh
set -eo pipefail

# 引数: 監視対象で追加されたファイルパス（KMの%TriggerValue%）
SRC_PATH=${1:-}
if [[ -z "$SRC_PATH" || ! -e "$SRC_PATH" ]]; then
  echo "[route_downloads_v3] invalid path: $SRC_PATH" >&2
  exit 1
fi

# ログ
LOG_DIR="$HOME/Documents/Logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/file_router.log"

# サイズが安定するまで待機（最大20秒）
stable_wait() {
  local p="$1"; local last=-1; local i=0
  while (( i < 20 )); do
    local sz=$(stat -f %z "$p" 2>/dev/null || echo 0)
    if [[ "$sz" = "$last" ]]; then break; fi
    last=$sz; i=$((i+1)); sleep 1
  done
}

# 拡張子小文字
ext_lc() { local f="$1"; local e="${f##*.}"; echo "${e:l}"; }

# スクショ判定（ファイル名）
is_screenshot() {
  local b; b=$(basename "$1")
  [[ "$b" == *"Screen Shot"* || "$b" == *"スクリーンショット"* || "$b" == *"スクリーンショット"* ]]
}

# 日本語日付タイトル
now_title() { date '+%Y年%m月%d日_%H時%M分%S秒'; }

# 重複回避の移動
safe_move() {
  local src="$1" dst_dir="$2" new_base="$3" ext="${1##*.}"
  mkdir -p "$dst_dir" || true
  local dst
  if [[ "$ext" != "$src" && -n "$ext" ]]; then
    dst="$dst_dir/$new_base.$ext"
  else
    dst="$dst_dir/$new_base"
  fi
  local n=1
  while [[ -e "$dst" ]]; do
    dst="$dst_dir/${new_base}_$n.${ext}"; n=$((n+1))
  done
  mkdir -p "$(dirname "$dst")" || true
  if ! mv "$src" "$dst" 2>/dev/null; then
    cp -p "$src" "$dst" 2>/dev/null && rm -f "$src"
  fi
  echo "$dst"
}

# カテゴリ判定
categorize() {
  local p="$1"; local e; e=$(ext_lc "$p")
  if is_screenshot "$p"; then echo "スクリーンショット"; return 0; fi
  case "$e" in
    jpg|jpeg|png|gif|webp|heic|tiff) echo "写真" ;;
    mp4|mov|mkv|avi) echo "動画" ;;
    mp3|wav|m4a|aac|flac|aiff) echo "音声" ;;
    doc|docx) echo "Word" ;;
    ppt|pptx|key) echo "PowerPoint" ;;
    xls|xlsx|csv|numbers) echo "Excel" ;;
    txt|md|rtf) echo "テキスト" ;;
    pdf) echo "PDF" ;;
    zip|tar|tgz|gz|7z|rar) echo "アーカイブ" ;;
    *) echo "その他" ;;
  esac
}

# 配置先ルート
DEST_ROOT_DOCS="$HOME/Documents/_Inbox"
DEST_ROOT_PICS="$HOME/Pictures/受信"
DEST_ROOT_MOVS="$HOME/Movies/受信"
DEST_ROOT_MUSIC="$HOME/Music/受信"

# 旧メモのログ系は既存ロジックを尊重（SSD接続時はSSDへ保存） [[memory:7146105]]

stable_wait "$SRC_PATH"

BASE_ORIG=$(basename "$SRC_PATH")
CATEGORY=$(categorize "$SRC_PATH")
STAMP=$(now_title)
TITLE_PREFIX="${STAMP}_${CATEGORY}"
NAME_BASE_NOEXT="${BASE_ORIG%.*}"
SAFE_NAME=$(echo "$NAME_BASE_NOEXT" | tr '/' '_' )
NEW_BASE="${TITLE_PREFIX}_${SAFE_NAME}"

case "$CATEGORY" in
  写真|スクリーンショット)
    DEST_DIR="$DEST_ROOT_PICS/$CATEGORY" ;;
  動画)
    DEST_DIR="$DEST_ROOT_MOVS/$CATEGORY" ;;
  音声)
    DEST_DIR="$DEST_ROOT_MUSIC/$CATEGORY" ;;
  Word|PowerPoint|Excel|テキスト|PDF)
    DEST_DIR="$DEST_ROOT_DOCS/Docs/$CATEGORY" ;;
  アーカイブ)
    DEST_DIR="$DEST_ROOT_DOCS/Archives" ;;
  *)
    DEST_DIR="$DEST_ROOT_DOCS/Misc" ;;
esac

FINAL=$(safe_move "$SRC_PATH" "$DEST_DIR" "$NEW_BASE")
echo "[$(date '+%F %T')] $SRC_PATH -> $FINAL ($CATEGORY)" >> "$LOG_FILE"
exit 0


