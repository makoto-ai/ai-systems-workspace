# Voice Roleplay System - Phase 8 環境変数設定ガイド

## 🚀 Phase 8: 必須APIキー設定

### 1. Groq API Key (必須)
```bash
export GROQ_API_KEY="your_groq_api_key_here"
```

**取得方法:**
1. https://console.groq.com/keys にアクセス
2. アカウント作成・ログイン
3. API Keys → Create API Key
4. 生成されたキーを上記に設定

### 2. HuggingFace Token (音声分離用)
```bash
export HF_TOKEN="your_huggingface_token_here"
```

**取得方法:**
1. https://huggingface.co/settings/tokens にアクセス
2. アカウント作成・ログイン
3. Settings → Access Tokens → New Token (Read権限)
4. 以下のモデルに同意が必要:
   - https://huggingface.co/pyannote/segmentation-3.0
   - https://huggingface.co/pyannote/speaker-diarization-3.1

### 3. Dify API Key (オプション・フォールバック用)
```bash
export DIFY_API_KEY="your_dify_api_key_here"
export DIFY_BASE_URL="https://api.dify.ai/v1"
```

**取得方法:**
1. https://dify.ai/ にアクセス
2. アカウント作成・ログイン
3. Settings → API Keys → Create API Key

### 4. 追加AIプロバイダー（オプション・Phase 8拡張）
```bash
export OPENAI_API_KEY="your_openai_api_key_here"
export CLAUDE_API_KEY="your_claude_api_key_here"
export GEMINI_API_KEY="your_gemini_api_key_here"
```

**取得方法:**
- **OpenAI**: https://platform.openai.com/api-keys
- **Claude**: https://console.anthropic.com/
- **Gemini**: https://makersuite.google.com/app/apikey

## 🔧 設定方法

### 一時的な設定（現在のセッションのみ）
```bash
export GROQ_API_KEY="your_actual_key_here"
export HF_TOKEN="your_actual_token_here"
```

### 永続的な設定（推奨）
```bash
# ~/.zshrc に追加
echo 'export GROQ_API_KEY="your_actual_key_here"' >> ~/.zshrc
echo 'export HF_TOKEN="your_actual_token_here"' >> ~/.zshrc
source ~/.zshrc
```

### .envファイルでの設定
```bash
# プロジェクトルートに .env ファイルを作成
cat > .env << 'EOF'
GROQ_API_KEY=your_actual_key_here
HF_TOKEN=your_actual_token_here
DIFY_API_KEY=your_actual_key_here
DIFY_BASE_URL=https://api.dify.ai/v1
DEBUG=true
LOG_LEVEL=INFO
EOF
```

## ✅ 設定確認

### 環境変数の確認
```bash
echo $GROQ_API_KEY
echo $HF_TOKEN
echo $DIFY_API_KEY
```

### テスト実行
```bash
# Groq接続テスト
python test_groq_integration.py

# 音声機能テスト
python test_whisper.py

# 統合テスト
python test_phase8_integration.py

# 統一AIサービステスト（新機能）
python test_unified_ai.py
```

## 🔄 統一AIサービス（Phase 8拡張）

### 複数AIプロバイダー対応
```bash
# 利用可能なプロバイダー確認
curl http://localhost:8000/ai/providers

# プロバイダー切り替え
curl -X POST http://localhost:8000/ai/providers/switch \
  -H "Content-Type: application/json" \
  -d '{"provider": "openai"}'

# 特定プロバイダーでチャット
curl -X POST http://localhost:8000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "provider": "groq"}'
```

### 自動フォールバック機能
- **Primary**: Groq（高速・低コスト）
- **Fallback 1**: OpenAI（高品質）
- **Fallback 2**: Claude（高品質）
- **Fallback 3**: Dify（ワークフロー）
- **Fallback 4**: Simulation（常に利用可能）

## 🎯 優先度

1. **GROQ_API_KEY** - 最優先（Phase 8の核心機能）
2. **HF_TOKEN** - 重要（音声分離機能）
3. **DIFY_API_KEY** - オプション（フォールバック用）

## 💡 費用目安

- **Groq**: 月額 ¥500-2000（使用量に応じて）
- **HuggingFace**: 無料
- **Dify**: 月額 ¥2000-8000（使用量に応じて） 