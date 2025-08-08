#!/bin/bash

# APIキー設定スクリプト v2.0
# 改善版 - より詳細なエラーメッセージと設定ガイド

echo "🔧 APIキー設定スクリプト v2.0"
echo "=================================="

# 環境変数ファイルの確認
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "📝 .envファイルを作成します..."
    cp env.example .env
    echo "✅ .envファイルが作成されました"
else
    echo "✅ .envファイルが既に存在します"
fi

# Groq APIキーの設定
echo ""
echo "🤖 Groq APIキーの設定"
echo "----------------------"
echo "Groq APIキーを取得するには:"
echo "1. https://console.groq.com/ にアクセス"
echo "2. アカウントを作成またはログイン"
echo "3. API Keys セクションで新しいキーを作成"
echo ""

read -p "Groq APIキーを入力してください (または Enter でスキップ): " GROQ_API_KEY

if [ ! -z "$GROQ_API_KEY" ]; then
    # .envファイルに追加
    if grep -q "GROQ_API_KEY" .env; then
        # 既存の行を更新
        sed -i.bak "s/^GROQ_API_KEY=.*/GROQ_API_KEY=$GROQ_API_KEY/" .env
        echo "✅ Groq APIキーが更新されました"
    else
        # 新しい行を追加
        echo "GROQ_API_KEY=$GROQ_API_KEY" >> .env
        echo "✅ Groq APIキーが追加されました"
    fi
else
    echo "⚠️  Groq APIキーが設定されませんでした"
    echo "   モックモードで動作します"
fi

# OpenAI APIキーの設定（オプション）
echo ""
echo "🧠 OpenAI APIキーの設定（オプション）"
echo "------------------------------------"
echo "OpenAI APIキーを取得するには:"
echo "1. https://platform.openai.com/api-keys にアクセス"
echo "2. アカウントを作成またはログイン"
echo "3. Create new secret key で新しいキーを作成"
echo ""

read -p "OpenAI APIキーを入力してください (または Enter でスキップ): " OPENAI_API_KEY

if [ ! -z "$OPENAI_API_KEY" ]; then
    # .envファイルに追加
    if grep -q "OPENAI_API_KEY" .env; then
        # 既存の行を更新
        sed -i.bak "s/^OPENAI_API_KEY=.*/OPENAI_API_KEY=$OPENAI_API_KEY/" .env
        echo "✅ OpenAI APIキーが更新されました"
    else
        # 新しい行を追加
        echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> .env
        echo "✅ OpenAI APIキーが追加されました"
    fi
else
    echo "⚠️  OpenAI APIキーが設定されませんでした"
fi

# 環境変数の読み込み確認
echo ""
echo "🔍 設定の確認"
echo "-------------"

# .envファイルから環境変数を読み込み
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 設定状況の確認
echo "📊 現在の設定状況:"
if [ ! -z "$GROQ_API_KEY" ]; then
    echo "✅ Groq APIキー: 設定済み (${GROQ_API_KEY:0:8}...)"
else
    echo "❌ Groq APIキー: 未設定"
fi

if [ ! -z "$OPENAI_API_KEY" ]; then
    echo "✅ OpenAI APIキー: 設定済み (${OPENAI_API_KEY:0:8}...)"
else
    echo "❌ OpenAI APIキー: 未設定"
fi

# システムテスト
echo ""
echo "🧪 システムテスト"
echo "----------------"

# Python環境の確認
if command -v python3 &> /dev/null; then
    echo "✅ Python3: 利用可能"
    
    # 依存関係の確認
    if [ -f "requirements.txt" ]; then
        echo "📦 依存関係を確認中..."
        python3 -c "import openai; print('✅ OpenAIライブラリ: 利用可能')" 2>/dev/null || echo "❌ OpenAIライブラリ: 未インストール"
    fi
else
    echo "❌ Python3: 利用できません"
fi

# 設定完了メッセージ
echo ""
echo "🎉 設定完了!"
echo "============="
echo ""
echo "📝 次のステップ:"
echo "1. システムをテスト: python3 test_youtube_script_system.py"
echo "2. Streamlitアプリを起動: streamlit run streamlit_app.py"
echo "3. 自動テストを実行: python3 auto_test_system.py"
echo ""
echo "⚠️  注意事項:"
echo "- APIキーは安全に保管してください"
echo "- .envファイルをGitにコミットしないでください"
echo "- モックモードでも基本的な機能は動作します"
echo ""
echo "🔗 参考リンク:"
echo "- Groq API: https://console.groq.com/"
echo "- OpenAI API: https://platform.openai.com/api-keys"
echo "- プロジェクトドキュメント: README.md" 