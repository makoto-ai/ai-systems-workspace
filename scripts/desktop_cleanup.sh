#!/bin/bash
# デスクトップ一括振り分けスクリプト（緊急版）
set -euo pipefail

DESKTOP="$HOME/Desktop"
MOVED=0
TOTAL=0

# カウント
echo "📊 デスクトップファイル分析中..."
TOTAL=$(find "$DESKTOP" -type f | wc -l)
echo "対象ファイル数: $TOTAL"

# フォルダ作成
mkdir -p "$HOME/Music/Audio"
mkdir -p "$HOME/Pictures/Photos" 
mkdir -p "$HOME/Documents/_Inbox/Docs"
mkdir -p "$HOME/Downloads/_Misc"

echo ""
echo "🎵 音声ファイル移動中..."
find "$DESKTOP" -name "*.m4a" -o -name "*.mp3" -o -name "*.wav" | while read -r file; do
    if [ -f "$file" ]; then
        mv "$file" "$HOME/Music/Audio/"
        echo "♪ $(basename "$file")"
        MOVED=$((MOVED + 1))
    fi
done

echo ""
echo "📷 画像ファイル移動中..."
find "$DESKTOP" -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.gif" | while read -r file; do
    if [ -f "$file" ]; then
        mv "$file" "$HOME/Pictures/Photos/"
        echo "📷 $(basename "$file")"
        MOVED=$((MOVED + 1))
    fi
done

echo ""
echo "📄 文書ファイル移動中..."
find "$DESKTOP" -name "*.pdf" -o -name "*.doc" -o -name "*.docx" -o -name "*.txt" -o -name "*.pages" | while read -r file; do
    if [ -f "$file" ]; then
        mv "$file" "$HOME/Documents/_Inbox/Docs/"
        echo "📄 $(basename "$file")"
        MOVED=$((MOVED + 1))
    fi
done

echo ""
echo "📦 その他ファイル移動中..."
find "$DESKTOP" -name "*.zip" -o -name "*.rar" -o -name "*.tar" -o -name "*.gz" | while read -r file; do
    if [ -f "$file" ]; then
        mv "$file" "$HOME/Downloads/_Misc/"
        echo "📦 $(basename "$file")"
        MOVED=$((MOVED + 1))
    fi
done

echo ""
REMAINING=$(find "$DESKTOP" -type f | wc -l)
echo "✅ 振り分け完了"
echo "📊 結果:"
echo "• 処理前: $TOTAL ファイル"
echo "• 処理後: $REMAINING ファイル"
echo "• 移動完了: $((TOTAL - REMAINING)) ファイル"
