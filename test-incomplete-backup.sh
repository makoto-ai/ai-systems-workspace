#!/bin/bash
# 🧪 不完全バックアップ防止機能のテスト

echo "🧪 不完全バックアップ検証テスト開始..."

# 1. 重要ファイルを一時的に移動（破損をシミュレート）
echo "📋 Step 1: 重要ファイル破損をシミュレート"
if [ -f "paper_research_system/main_integrated.py" ]; then
    mv paper_research_system/main_integrated.py paper_research_system/main_integrated.py.backup
    echo "✅ main_integrated.py を一時移動"
fi

# 2. バックアップ実行（失敗するはず）
echo -e "\n📋 Step 2: バックアップ実行テスト（失敗予定）"
./auto-save.sh "🧪 テスト: 不完全バックアップ検出テスト"
BACKUP_RESULT=$?

# 3. ファイルを復元
echo -e "\n📋 Step 3: ファイル復元"
if [ -f "paper_research_system/main_integrated.py.backup" ]; then
    mv paper_research_system/main_integrated.py.backup paper_research_system/main_integrated.py
    echo "✅ main_integrated.py を復元"
fi

# 4. 結果評価
echo -e "\n📊 テスト結果:"
if [ $BACKUP_RESULT -ne 0 ]; then
    echo "✅ SUCCESS: 不完全バックアップが正しく阻止されました"
    echo "✅ 検証システム正常動作"
else
    echo "❌ FAIL: 不完全バックアップが通ってしまいました"
    echo "❌ 検証システム不具合"
fi

echo -e "\n🧪 テスト完了"