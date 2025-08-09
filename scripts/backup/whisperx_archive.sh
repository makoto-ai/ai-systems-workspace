#!/bin/bash

# 🎙️ WhisperX出力日付付きアーカイブスクリプト
# 使用方法: ./scripts/backup/whisperx_archive.sh [input_file] [output_dir]
# 例: ./scripts/backup/whisperx_archive.sh input.wav whisperx_outputs/

set -e

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 引数チェック
if [ $# -lt 1 ]; then
    echo "使用方法: $0 <input_file> [output_dir]"
    echo "例: $0 input.wav whisperx_outputs/"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_DIR="${2:-whisperx_outputs}"

# 入力ファイル存在確認
if [ ! -f "$INPUT_FILE" ]; then
    log "❌ 入力ファイルが見つかりません: $INPUT_FILE"
    exit 1
fi

log "🎙️ WhisperX出力アーカイブ開始"

# 日付付き出力ディレクトリ作成
DATE=$(date +%Y-%m-%d_%H-%M-%S)
ARCHIVE_DIR="$OUTPUT_DIR/output_$DATE"
mkdir -p "$ARCHIVE_DIR"

log "📁 アーカイブ先: $ARCHIVE_DIR"

# 1. 入力ファイルをコピー
log "📋 入力ファイルをコピー中..."
cp "$INPUT_FILE" "$ARCHIVE_DIR/input_$(basename "$INPUT_FILE")"

# 2. WhisperX実行
log "🎤 WhisperX処理中..."
cd "$ARCHIVE_DIR"

# WhisperXコマンド実行（環境に応じて調整）
if command -v whisperx &> /dev/null; then
    whisperx --input "input_$(basename "$INPUT_FILE")" \
             --output_dir . \
             --language ja \
             --model large-v2
    log "✅ WhisperX処理完了"
elif command -v python &> /dev/null; then
    # Python経由でWhisperX実行
    python -m whisperx --input "input_$(basename "$INPUT_FILE")" \
                       --output_dir . \
                       --language ja \
                       --model large-v2
    log "✅ WhisperX処理完了"
else
    log "❌ WhisperXが見つかりません"
    log "💡 インストール方法: pip install whisperx"
    exit 1
fi

# 3. 処理情報の記録
PROCESS_INFO="$ARCHIVE_DIR/process_info.txt"
cat > "$PROCESS_INFO" << EOF
WhisperX処理情報
=================
処理日時: $(date)
入力ファイル: $INPUT_FILE
出力ディレクトリ: $ARCHIVE_DIR
ファイルサイズ: $(du -sh "$INPUT_FILE" | cut -f1)

処理設定:
- 言語: 日本語 (ja)
- モデル: large-v2
- 出力形式: 標準WhisperX形式

システム情報:
- OS: $(uname -s)
- ホスト名: $(hostname)
- ユーザー: $(whoami)
EOF

log "📝 処理情報記録完了"

# 4. 結果ファイル一覧
log "📋 生成されたファイル:"
ls -la "$ARCHIVE_DIR/"

# 5. アーカイブ完了通知
ARCHIVE_SIZE=$(du -sh "$ARCHIVE_DIR" | cut -f1)
log "🎉 WhisperXアーカイブ完了！"
log "📊 アーカイブサイズ: $ARCHIVE_SIZE"
log "📁 保存先: $ARCHIVE_DIR"

# 6. 成功通知（オプション）
if command -v osascript &> /dev/null; then
    osascript -e "display notification \"WhisperXアーカイブ完了: $ARCHIVE_SIZE\" with title \"WhisperX処理完了\""
fi

# 7. 古いアーカイブの削除（30日以上前）
log "🧹 古いアーカイブを削除中..."
find "$OUTPUT_DIR" -type d -name "output_*" -mtime +30 -exec rm -rf {} \; 2>/dev/null || true

log "✅ WhisperX出力アーカイブ完了"
