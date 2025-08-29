#!/bin/bash
# 週次ゴールデンテスト観測スクリプト

set -euo pipefail

echo "🔍 週次ゴールデンテスト観測"
echo "=========================="

# 作業ディレクトリ設定
cd /Users/araimakoto/ai-driven/ai-systems-workspace
export PYTHONPATH=/Users/araimakoto/ai-driven/ai-systems-workspace

# 現在の日時
WEEK_DATE=$(date +"%Y-%m-%d")
echo "📅 観測日: $WEEK_DATE"

# ゴールデンテスト実行
echo "🧪 ゴールデンテスト実行中..."
RESULT=$(python3 tests/golden/run_golden.py --threshold 0.3)
echo "$RESULT"

# 結果をパース
PASSED=$(echo "$RESULT" | grep "passed" | cut -d' ' -f2)
RATE=$(echo "$PASSED" | cut -d'/' -f1)
TOTAL=$(echo "$PASSED" | cut -d'/' -f2)
PERCENTAGE=$((RATE * 100 / TOTAL))

echo ""
echo "📊 今週の結果"
echo "=============="
echo "合格率: $RATE/$TOTAL ($PERCENTAGE%)"

# 観測ログに追記
LOG_FILE="tests/golden/observation_log.md"
echo "" >> "$LOG_FILE"
echo "## $WEEK_DATE - 週次観測" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
echo "### 結果" >> "$LOG_FILE"
echo "- **合格率**: $RATE/$TOTAL ($PERCENTAGE%)" >> "$LOG_FILE"
echo "- **しきい値**: 0.3" >> "$LOG_FILE"

# 判定とアクション提案
if [ "$PERCENTAGE" -ge 90 ]; then
    echo "✅ 合格率90%以上 - 良好な状態を維持"
    echo "- **状態**: 良好 ✅" >> "$LOG_FILE"
    
    # 3週連続90%以上なら0.5への引き上げ提案
    RECENT_GOOD=$(tail -n 20 "$LOG_FILE" | grep -c "良好 ✅" || true)
    if [ "$RECENT_GOOD" -ge 3 ]; then
        echo "🎯 3週連続90%以上達成 - しきい値0.5への引き上げを検討"
        echo "- **提案**: しきい値0.5への引き上げ検討 🎯" >> "$LOG_FILE"
    fi
    
elif [ "$PERCENTAGE" -ge 80 ]; then
    echo "⚠️ 合格率80-89% - 辞書チューニングが必要"
    echo "- **状態**: 要改善 ⚠️" >> "$LOG_FILE"
    echo "- **アクション**: 不合格ケースの辞書追加" >> "$LOG_FILE"
    
else
    echo "🔥 合格率80%未満 - 緊急対応が必要"
    echo "- **状態**: 緊急 🔥" >> "$LOG_FILE"
    echo "- **アクション**: 辞書の大幅見直し" >> "$LOG_FILE"
fi

echo ""
echo "📝 最新ログを確認: $LOG_FILE"
echo "🔄 次回観測: $(date -v+7d +%Y-%m-%d)"
