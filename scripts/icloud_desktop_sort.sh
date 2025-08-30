#!/bin/bash
set -euo pipefail

DESKTOP="$HOME/Desktop"
ICLOUD_ROOT="$HOME/Library/Mobile Documents/com~apple~CloudDocs"
DATE_DIR="$(date +%Y-%m-%d)"
BASE_DIR="$ICLOUD_ROOT/Sorted/$DATE_DIR"

# 作成先ディレクトリ
mkdir -p "$BASE_DIR/Images/Screenshots" "$BASE_DIR/Images/Photos" \
         "$BASE_DIR/Audio" "$BASE_DIR/Video" \
         "$BASE_DIR/Docs/PDF" "$BASE_DIR/Docs/Word" "$BASE_DIR/Docs/Excel" "$BASE_DIR/Docs/PPT" "$BASE_DIR/Docs/Text" \
         "$BASE_DIR/Archives" "$BASE_DIR/Others"

safe_move() {
  src="$1"; dest_dir="$2"
  mkdir -p "$dest_dir"
  bn="$(basename "$src")"
  target="$dest_dir/$bn"
  if [ ! -e "$target" ]; then
    mv "$src" "$target"
    return 0
  fi
  i=1
  ext="${bn##*.}"
  name="${bn%.*}"
  while :; do
    candidate="$dest_dir/${name}_$i.${ext}"
    if [ ! -e "$candidate" ]; then
      mv "$src" "$candidate"
      return 0
    fi
    i=$((i+1))
  done
}

moved_total=0
failed_total=0
report() { printf "%s\n" "$1"; }

# find helper
move_by_find() {
  label="$1"; dest="$2"; shift 2
  report "=== $label ==="
  # 受け取った条件をそのまま渡す（クォート保持）
  find "$DESKTOP" -maxdepth 1 -type f \( "$@" \) -print0 | while IFS= read -r -d '' f; do
    if safe_move "$f" "$dest"; then moved_total=$((moved_total+1)); else failed_total=$((failed_total+1)); fi
  done
}

# スクリーンショット（名称キーワード）
move_by_find "Screenshots" "$BASE_DIR/Images/Screenshots" \
  -iname '*スクリーンショット*' -o -iname 'Screen Shot*' -o -iname 'Screenshot*'

# 画像
move_by_find "Images" "$BASE_DIR/Images/Photos" \
  -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.heic' -o -iname '*.gif' -o -iname '*.webp'

# 音声
move_by_find "Audio" "$BASE_DIR/Audio" \
  -iname '*.m4a' -o -iname '*.mp3' -o -iname '*.wav' -o -iname '*.flac' -o -iname '*.aac'

# 動画
move_by_find "Video" "$BASE_DIR/Video" \
  -iname '*.mov' -o -iname '*.mp4' -o -iname '*.m4v' -o -iname '*.mkv' -o -iname '*.avi' -o -iname '*.webm'

# 文書
move_by_find "PDF" "$BASE_DIR/Docs/PDF" -iname '*.pdf'
move_by_find "Word" "$BASE_DIR/Docs/Word" -iname '*.doc' -o -iname '*.docx'
move_by_find "Excel" "$BASE_DIR/Docs/Excel" -iname '*.xls' -o -iname '*.xlsx' -o -iname '*.csv'
move_by_find "PPT" "$BASE_DIR/Docs/PPT" -iname '*.ppt' -o -iname '*.pptx' -o -iname '*.key'
move_by_find "Text" "$BASE_DIR/Docs/Text" -iname '*.txt' -o -iname '*.rtf' -o -iname '*.md'

# アーカイブ
move_by_find "Archives" "$BASE_DIR/Archives" -iname '*.zip' -o -iname '*.rar' -o -iname '*.7z' -o -iname '*.tar' -o -iname '*.gz'

# 残りの単体ファイル
report "=== Others ==="
find "$DESKTOP" -maxdepth 1 -type f -print0 | while IFS= read -r -d '' f; do
  bn="$(basename "$f")"
  bnlc="$(printf '%s' "$bn" | tr '[:upper:]' '[:lower:]')"
  # 既に処理済み拡張子/名称はスキップ
  case "$bnlc" in
    *スクリーンショット*|screen\ shot*|screenshot*|*.png|*.jpg|*.jpeg|*.heic|*.gif|*.webp|*.m4a|*.mp3|*.wav|*.flac|*.aac|*.mov|*.mp4|*.m4v|*.mkv|*.avi|*.webm|*.pdf|*.doc|*.docx|*.xls|*.xlsx|*.csv|*.ppt|*.pptx|*.key|*.txt|*.rtf|*.md|*.zip|*.rar|*.7z|*.tar|*.gz)
      continue;;
  esac
  if safe_move "$f" "$BASE_DIR/Others"; then moved_total=$((moved_total+1)); else failed_total=$((failed_total+1)); fi
done

remaining=$(find "$DESKTOP" -maxdepth 1 -type f | wc -l | tr -d ' ')

echo "\n=== Summary ==="
echo "Moved: $moved_total files"
echo "Failed: $failed_total files"
echo "Remaining on Desktop: $remaining files"
echo "Destination root: $BASE_DIR"
