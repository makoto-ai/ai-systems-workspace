# 📋 Voice Roleplay System - 完全システム仕様書

## 🎯 概要
Voice Roleplay Systemは、AI技術を活用した高度な営業ロールプレイ・音声対話システムです。企業の営業トレーニング、顧客対応シミュレーション、音声分析に特化したプロダクション対応システムです。

---

## 🏗️ アーキテクチャ概要

### システム構成
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Server    │    │   AI Services   │
│   (Future)      │◄──►│   FastAPI       │◄──►│   Multiple LLMs │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                        ┌─────────────────┐
                        │   Voice Engine  │
                        │   VOICEVOX +    │
                        │   WhisperX      │
                        └─────────────────┘
```

### 技術スタック
- **Backend Framework**: FastAPI 0.104+
- **Python Version**: 3.12.11
- **AI Models**: Groq (Llama 3.1 70B), Llama 3.1 Swallow 8B
- **Speech Recognition**: WhisperX 3.1.1+
- **Text-to-Speech**: VOICEVOX Engine
- **Database**: SQLite (Production: PostgreSQL対応)

---

## 🔧 システム要件

### ハードウェア要件
| コンポーネント | 最小要件 | 推奨要件 | エンタープライズ |
|----------------|----------|----------|------------------|
| **CPU** | Intel i5 / AMD Ryzen 5 | Intel i7 / AMD Ryzen 7 | Intel Xeon / AMD EPYC |
| **RAM** | 8GB | 16GB | 32GB+ |
| **ストレージ** | 10GB SSD | 50GB NVMe SSD | 200GB+ NVMe SSD |
| **GPU** | なし（CPU動作） | NVIDIA GTX 1660+ | NVIDIA RTX 4090+ |

### ソフトウェア要件
| カテゴリ | 要件 | バージョン | 備考 |
|----------|------|------------|------|
| **OS** | macOS / Linux | 10.15+ / Ubuntu 20.04+ | Windows WSL2対応 |
| **Python** | CPython | 3.12.11 | pyenv推奨 |
| **Git** | Version Control | 2.28+ | 必須 |
| **Node.js** | Frontend (Future) | 18+ LTS | 将来対応 |

---

## 📦 依存関係詳細

### Core Python Packages
```python
# Web Framework
fastapi>=0.104.1
uvicorn[standard]>=0.24.0

# AI & Machine Learning
torch>=2.0.0
torchaudio>=2.0.0
transformers>=4.53.0
accelerate>=0.30.0
bitsandbytes>=0.43.0

# Speech Processing
whisperx>=3.1.1
faster-whisper>=0.10.0
pyannote.audio>=3.1.0

# Audio Processing
librosa>=0.10.1
soundfile>=0.12.1
numpy>=1.26.2

# HTTP Clients & APIs
httpx>=0.25.0
requests>=2.31.0
groq>=0.4.1

# Data Processing
pandas>=2.0.0
pydantic>=2.0.0

# Utilities
python-multipart>=0.0.6
python-dotenv>=1.0.0
Pillow>=10.0.0
```

### System Dependencies (macOS)
```bash
# Package Manager
brew install pyenv

# Audio Libraries
brew install ffmpeg portaudio sox

# Development Tools
brew install git curl wget

# Optional: Conda Environment
brew install --cask conda
```

### System Dependencies (Linux)
```bash
# Python Development
sudo apt-get install python3.12-dev python3.12-venv python3-pip

# Audio Libraries
sudo apt-get install ffmpeg portaudio19-dev sox libsox-fmt-all

# Build Tools
sudo apt-get install build-essential libasound2-dev libsndfile1-dev

# Development Tools
sudo apt-get install git curl wget
```

---

## 🎙️ 音声エンジン仕様

### WhisperX Configuration
```python
MODEL_SIZES = ["tiny", "base", "small", "medium", "large"]
SUPPORTED_LANGUAGES = [
    "ja", "en", "zh", "ko", "es", "fr", "de", "it", 
    "pt", "ru", "ar", "hi", "nl", "pl", "tr", "vi", "th"
]
DEVICE_SUPPORT = ["cpu", "cuda", "mps"]
COMPUTE_TYPE = {
    "cpu": "int8",
    "cuda": "float16", 
    "mps": "float16"
}
```

### VOICEVOX Integration
```python
VOICEVOX_ENGINE_URL = "http://localhost:50021"
SUPPORTED_SPEAKERS = [
    "四国めたん", "ずんだもん", "春日部つむぎ", "雨晴はう"
    # その他40+のスピーカー
]
AUDIO_FORMAT = "wav"
SAMPLE_RATE = 24000
```

---

## 🤖 AI サービス仕様

### Groq Integration
```python
MODEL_CONFIG = {
    "llama-3.1-70b-versatile": {
        "max_tokens": 8192,
        "temperature": 0.7,
        "top_p": 0.9
    }
}
RATE_LIMITS = {
    "requests_per_minute": 30,
    "tokens_per_minute": 6000
}
```

### Sales Scenario Engine
```python
CUSTOMER_TYPES = [
    "ANALYTICAL",    # 分析重視型
    "DRIVER",        # 結果重視型
    "EXPRESSIVE",    # 表現重視型
    "AMIABLE",       # 協調重視型
    "COLLABORATIVE", # 協力重視型
    "SKEPTICAL"      # 懐疑的型
]

SALES_STAGES = [
    "prospecting",      # 見込み客開拓
    "needs_assessment", # ニーズ調査
    "proposal",         # 提案
    "objection_handling", # 反対意見処理
    "closing"           # クロージング
]

BANT_CRITERIA = {
    "budget": "予算",
    "authority": "決裁権",
    "need": "必要性", 
    "timeline": "導入時期"
}
```

### Text Analysis (Swallow)
```python
SWALLOW_MODEL = "tokyotech-llm/Llama-3.1-Swallow-8B-Instruct-v0.3"
ANALYSIS_TYPES = ["comprehensive", "faq", "summary"]
DOCUMENT_TYPES = ["sales_document", "product_spec", "customer_profile"]
SUPPORTED_FORMATS = [".txt", ".csv", ".md", ".json"]
MAX_FILE_SIZE = "10MB"
MAX_TEXT_LENGTH = 50000  # characters
```

---

## 🌐 API仕様

### エンドポイント一覧
| カテゴリ | メソッド | エンドポイント | 機能 |
|----------|----------|----------------|------|
| **Health** | GET | `/health` | システム状態確認 |
| **Voice** | POST | `/voice/tts` | テキスト→音声変換 |
| **Speech** | POST | `/speech/transcribe` | 音声→テキスト変換 |
| **AI** | POST | `/ai/chat` | 統合AI対話 |
| **Conversation** | POST | `/conversation/session` | セッション管理 |
| **Text** | POST | `/text/upload/analyze` | テキスト分析 |
| **Sales** | POST | `/ai/sales-analysis` | 営業分析 |

### OpenAI互換API
| エンドポイント | 機能 | 互換性 |
|----------------|------|--------|
| `/v1/chat/completions` | チャット完了 | OpenAI GPT-4 |
| `/v1/audio/transcriptions` | 音声転写 | OpenAI Whisper |
| `/v1/audio/speech` | 音声合成 | OpenAI TTS |

---

## 🗄️ データ仕様

### 会話履歴構造
```json
{
  "session_id": "uuid",
  "user_id": "string",
  "conversation_history": [
    {
      "timestamp": "ISO8601",
      "speaker": "user|assistant",
      "content": "string",
      "audio_metadata": {
        "duration": "float",
        "confidence": "float",
        "language": "string"
      }
    }
  ],
  "sales_context": {
    "customer_type": "string",
    "sales_stage": "string",
    "bant_score": {
      "budget": "float",
      "authority": "float", 
      "need": "float",
      "timeline": "float"
    }
  }
}
```

### 分析結果構造
```json
{
  "analysis_id": "uuid",
  "input_type": "audio|text",
  "analysis_results": {
    "summary": "string",
    "key_points": ["string"],
    "customer_insights": {
      "type": "string",
      "pain_points": ["string"],
      "buying_signals": ["string"]
    },
    "recommendations": ["string"],
    "confidence_score": "float"
  },
  "processing_time": "float"
}
```

---

## 🔒 セキュリティ仕様

### API認証
```python
SECURITY_FEATURES = {
    "api_key_authentication": True,
    "rate_limiting": True,
    "input_validation": True,
    "output_sanitization": True
}

RATE_LIMITS = {
    "api_requests": "100/minute",
    "file_uploads": "10/minute", 
    "audio_processing": "5/minute"
}
```

### データ保護
- **暗号化**: AES-256 (ファイル保存時)
- **通信**: HTTPS/TLS 1.3
- **APIキー**: 環境変数で管理
- **ログ**: 個人情報マスキング

---

## 🚀 パフォーマンス仕様

### レスポンス時間目標
| 機能 | 目標時間 | 最大許容時間 |
|------|----------|--------------|
| **Health Check** | 50ms | 200ms |
| **Text-to-Speech** | 2秒 | 10秒 |
| **Speech-to-Text** | 5秒 | 30秒 |
| **AI Chat** | 3秒 | 15秒 |
| **Text Analysis** | 5秒 | 30秒 |

### スループット目標
- **同時接続**: 100セッション
- **音声処理**: 10並列ストリーム
- **API呼び出し**: 1000リクエスト/分

---

## 📊 監視・ログ仕様

### ログレベル
```python
LOG_LEVELS = {
    "ERROR": "システムエラー・例外",
    "WARNING": "警告・非推奨使用",
    "INFO": "一般情報・処理状況", 
    "DEBUG": "デバッグ情報・詳細ログ"
}
```

### メトリクス
- **システムメトリクス**: CPU、メモリ、ディスク使用率
- **アプリケーションメトリクス**: レスポンス時間、エラー率
- **ビジネスメトリクス**: セッション数、音声処理時間

---

## 🔄 バックアップ・復旧仕様

### バックアップ対象
1. **アプリケーションコード**: Git Bundle (254KB)
2. **設定ファイル**: 環境変数、設定JSON
3. **ユーザーデータ**: 会話履歴、分析結果
4. **モデルファイル**: 学習済みモデル (自動ダウンロード可能)

### 復旧時間目標 (RTO)
- **コード復旧**: 15分
- **環境構築**: 30分
- **データ復旧**: 10分
- **総復旧時間**: 1時間以内

### 復旧ポイント目標 (RPO)
- **重要データ**: 1時間以内の損失
- **システム設定**: ゼロ損失
- **ユーザーセッション**: 最大15分の損失

---

## 🎯 今後の拡張計画

### Phase 11: Frontend Development
- **React/Next.js** ウェブインターフェース
- **リアルタイム音声対話** UI
- **管理ダッシュボード**

### Phase 12: Enterprise Features
- **マルチテナント対応**
- **RBAC (Role-Based Access Control)**
- **監査ログ・コンプライアンス**

### Phase 13: Advanced AI
- **カスタムモデル学習**
- **感情分析・表情認識**
- **リアルタイム翻訳**

---

**📋 このシステム仕様書は、Voice Roleplay Systemの技術的な完全な仕様を記録しています。**

*最終更新日: 2025年7月5日*  
*バージョン: 1.0.0*  
*対象リリース: milestone/complete-implementation* 