# Voice Roleplay System 🎤

**次世代音声対話システム** - 完全な音声から音声への会話パイプライン、高度な営業ロールプレイ機能、声のクローニング、音声バイオメトリクス認証を備えた包括的なAIシステム

## 🚀 **最新機能 (v2.0.0)**

### 🎯 **Phase 1: 声のクローニング機能**
- **RVC技術**: 最先端のRetrieval-based Voice Conversionによるリアルタイム声質変換
- **音声学習**: 5-10分の音声サンプルから個人の声をモデル化
- **高品質合成**: So-vits-svcによる自然な音声生成
- **感情制御**: 音声の感情パラメータ調整（happy, sad, angry, excited）

### 🔍 **Phase 2: 高度な声紋分析**
- **話者認証**: 99.5%以上の精度を目標とした音声による本人確認
- **バイオメトリクス**: 基本周波数、フォルマント、スペクトル特性の詳細分析
- **感情分析**: リアルタイム感情状態検出（興奮、悲しみ、幸せ、怒り、中立）
- **人口統計**: 音声からの年齢・性別推定
- **セキュリティ**: アンチスプーフィング技術による音声真正性検証

### 🌐 **Phase 3: Cloudflare統合（計画中）**
- **エッジコンピューティング**: Cloudflare Workersによる低遅延処理
- **CDN配信**: 音声データの最適化配信
- **リアルタイムストリーミング**: WebRTCによるP2P音声通信

## 📋 **システム概要**

### **コア機能**
- ✅ **音声認識**: WhisperXによる高精度音声→テキスト変換 + 話者分離
- ✅ **AI統合**: マルチプロバイダー対応（Groq, OpenAI, Claude, Gemini）
- ✅ **音声合成**: VOICEVOXによる自然な音声生成
- ✅ **声のクローニング**: ユーザーの声で応答生成
- ✅ **ドキュメント処理**: 30以上のファイル形式対応
- ✅ **営業分析**: 高度な会話分析とロールプレイ機能

### **新機能ハイライト**
- 🎤 **個人化された音声応答**: あなたの声でAIが応答
- 🔐 **音声認証**: 声による本人確認システム
- 😊 **感情理解**: 音声から感情状態をリアルタイム分析
- 👤 **話者プロファイリング**: 年齢・性別・特徴の自動推定
- 🛡️ **セキュリティ強化**: 音声なりすまし検出機能

## 🏗️ **アーキテクチャ**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI Services   │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Voice UI    │ │    │ │ Voice Clone │ │    │ │ Groq/OpenAI │ │
│ │ Recording   │ │◄──►│ │ Service     │ │◄──►│ │ Claude/Gem. │ │
│ │ Playback    │ │    │ │ RVC Models  │ │    │ │ Multi-AI    │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Real-time   │ │    │ │ Advanced    │ │    │ │ WhisperX    │ │
│ │ Analysis    │ │    │ │ Voice       │ │    │ │ VOICEVOX    │ │
│ │ Dashboard   │ │    │ │ Analytics   │ │    │ │ Speech Proc │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ **技術スタック**

### **Backend**
- **FastAPI**: 高性能Web API フレームワーク
- **WhisperX**: 話者分離機能付き音声認識
- **VOICEVOX**: 自然な日本語音声合成
- **RVC-Python**: リアルタイム声質変換
- **SpeechBrain**: 話者認識・分析
- **Resemblyzer**: 話者埋め込み抽出

### **Frontend**
- **Next.js 14**: モダンReactフレームワーク
- **TypeScript**: 型安全な開発環境
- **Tailwind CSS**: ユーティリティファーストCSS

### **AI/ML**
- **多様なAIプロバイダー**: Groq, OpenAI, Claude, Gemini
- **音声処理**: Librosa, PyWorld, Praat
- **機械学習**: PyTorch, Scikit-learn, NumPy

## 🟢 **運用・起動まとめ（最短手順）**

- 一発起動（ハブ）
```bash
/Users/araimakoto/ai-driven/ai-systems-workspace/auto-start-on-open-complete.sh
```

- 動作確認
  - API: http://localhost:8000/health /docs
  - TTS: http://localhost:8000/api/voice/speakers, /api/voice/text-to-speech
  - 公開: http://localhost:8000/public/

- 迅速テスト（TTS）
```bash
curl -sS -H "Content-Type: application/json" \
  -d '{"text":"テスト","speaker_id":2}' \
  -o out/quick.wav http://localhost:8000/api/voice/text-to-speech
```

- 常駐/定期ジョブ
  - 監視: 常駐（PIDは `cat /Users/araimakoto/ai-driven/ai-systems-workspace/.monitor.pid`）
  - 自動コミット: 5分毎（launchd: local.memory_auto_commit）
  - デイリーバックアップ: 毎日3時（launchd: local.daily_backup）

- 主要ログ
  - `logs/hybrid_restart.log`（API）
  - `logs/monitor_start.log`（監視）
  - `logs/cron_daily_backup.*.log`（バックアップ）
  - `logs/audit.jsonl`（監査）

- 停止
```bash
pkill -f "main_hybrid:app" || true
pkill -f monitor-services.sh || true
```

## 🚀 **クイックスタート**
### 自動コミットで常に白にする（モードA）
- 一度だけ実行: `npm run auto:white:once`
- 監視して常駐: `npm run auto:white`
- 停止: 監視プロセス（ターミナル）を Ctrl+C
- 注意: `.gitignore` に入っていないファイルは自動コミット対象。秘密は pre-commit でブロック。

### **E2E/CI（自動会話検証）**

1) 依存準備

```bash
npm i -D @playwright/test
npx playwright install --with-deps
```

2) 変数

- E2E_BASE_URL: フロントのURL（既定: http://localhost:5173）
- API_BASE_URL: APIのURL（既定: http://localhost:8000）

3) ローカル実行

```bash
npx playwright test
pytest -q tests/api/test_roundtrip.py
```

4) 音声フィクスチャ

- `tests/fixtures/input.wav` を差し替えると実録音で検証可能

失敗時: `playwright-report/` を参照（Actionsではアーティファクトに保存）


### **1. 環境セットアップ**
```bash
# リポジトリクローン
git clone https://github.com/your-repo/voice-roleplay-dify.git
cd voice-roleplay-dify

# Python仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# フロントエンド依存関係
cd frontend/voice-roleplay-frontend
npm install
cd ../..
```

### **2. 環境変数設定**
```bash
# .envファイル作成
cp .env.example .env

# API キー設定
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
HF_TOKEN=your_huggingface_token  # 話者分離用
```

### **3. システム起動**

#### **統合起動（推奨）**
```bash
# バックエンドとフロントエンドを同時起動
npm run dev:full
```

#### **個別起動**
```bash
# バックエンド起動
python -m app.main

# フロントエンド起動（別ターミナル）
npm run frontend
```

### **4. アクセス**
- **API ドキュメント**: http://localhost:8000/docs
- **フロントエンド**: http://localhost:3000
- **システム情報**: http://localhost:8000

## 🎤 **使用方法**

### **基本的な音声会話**
1. フロントエンドにアクセス
2. 「音声録音開始」をクリック
3. 話しかける
4. AIが音声で応答

### **声のクローニング**
```bash
# 1. 音声サンプルをアップロード
curl -X POST "http://localhost:8000/api/voice-clone/profiles" \
  -F "user_id=your_user_id" \
  -F "files=@sample1.wav" \
  -F "files=@sample2.wav" \
  -F "files=@sample3.wav"

# 2. クローン音声生成
curl -X POST "http://localhost:8000/api/voice-clone/synthesize" \
  -F "profile_id=your_profile_id" \
  -F "text=こんにちは、私の声でお話しします"
```

### **話者認証**
```bash
# 1. 話者登録
curl -X POST "http://localhost:8000/api/voice-analysis/register-speaker" \
  -F "speaker_id=john_doe" \
  -F "files=@voice1.wav" \
  -F "files=@voice2.wav" \
  -F "files=@voice3.wav"

# 2. 認証テスト
curl -X POST "http://localhost:8000/api/voice-analysis/authenticate" \
  -F "file=@test_voice.wav" \
  -F "expected_speaker_id=john_doe"
```

## 📊 **API エンドポイント**

### **音声会話**
- `POST /api/voice/conversation` - 完全な音声対話
- `POST /api/speech/transcribe` - 音声認識
- `POST /api/speech/synthesize` - 音声合成

### **声のクローニング**
- `POST /api/voice-clone/profiles` - 音声プロファイル作成
- `POST /api/voice-clone/synthesize` - クローン音声生成
- `GET /api/voice-clone/profiles` - プロファイル一覧
- `GET /api/voice-clone/service-info` - サービス情報

### **高度な音声分析**
- `POST /api/voice-analysis/analyze` - 包括的音声分析
- `POST /api/voice-analysis/register-speaker` - 話者登録
- `POST /api/voice-analysis/authenticate` - 話者認証
- `POST /api/voice-analysis/emotion` - 感情分析
- `POST /api/voice-analysis/demographics` - 年齢・性別分析

### **ドキュメント処理**
- `POST /api/text/process` - ファイル処理とナレッジ抽出

## 🧪 **テスト**

### **機能テスト**
```bash
# 基本機能テスト
python test_knowledge_files.py

# 声のクローニングテスト
python test_voice_cloning.py

# 高度な音声機能統合テスト
python test_advanced_voice_features.py

# ヘルスチェック
curl http://localhost:8000/api/health
```

## 📁 **プロジェクト構造**

```
voice-roleplay-dify/
├── app/                           # バックエンドアプリケーション
│   ├── api/                       # API エンドポイント
│   │   ├── voice_cloning.py       # 声のクローニング API
│   │   ├── advanced_voice_analysis.py # 高度な音声分析 API
│   │   ├── conversation.py        # 音声会話 API
│   │   ├── speech.py              # 音声処理 API
│   │   └── ...
│   ├── services/                  # ビジネスロジック
│   │   ├── voice_cloning_service.py
│   │   ├── advanced_voice_analysis_service.py
│   │   ├── conversation_service.py
│   │   ├── speech_service.py
│   │   └── ...
│   └── main.py                    # アプリケーションエントリーポイント
├── frontend/voice-roleplay-frontend/ # Next.js フロントエンド
│   ├── src/
│   │   ├── app/                   # App Router
│   │   ├── components/            # React コンポーネント
│   │   ├── hooks/                 # カスタムフック
│   │   └── types/                 # TypeScript 型定義
│   └── package.json
├── docs/                          # ドキュメント
│   ├── next-gen-voice-features.md
│   ├── sales-roleplay-roadmap.md
│   └── ...
├── data/                          # データファイル
│   ├── voice_models/              # 声のクローニングモデル
│   ├── speaker_models/            # 話者認識モデル
│   └── voicevox/                  # VOICEVOX データ
├── tests/                         # テストファイル
├── requirements.txt               # Python 依存関係
├── package.json                   # 統合 npm スクリプト
└── README.md                      # このファイル
```

## ⚙️ **システム要件**

### **最小要件**
- **OS**: Windows 10+, macOS 10.15+, Ubuntu 20.04+
- **Python**: 3.8+
- **Node.js**: 18+
- **RAM**: 8GB（基本機能）
- **ストレージ**: 10GB

### **推奨要件（全機能）**
- **GPU**: NVIDIA RTX 3060+ （声のクローニング用）
- **RAM**: 16GB+
- **ストレージ**: 50GB+ （モデルファイル用）
- **CPU**: マルチコア（リアルタイム処理用）

## 🔧 **開発**

### **開発用スクリプト**
```bash
# 開発環境セットアップ
npm run setup

# バックエンド開発
npm run backend

# フロントエンド開発
npm run frontend

# 全体開発
npm run dev:full

# ビルド
npm run build

# テスト
npm run test
```

### **コントリビューション**
1. フォーク作成
2. フィーチャーブランチ作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエスト作成

## 🛡️ **セキュリティとプライバシー**

### **データ保護**
- 音声データの暗号化保存
- 学習モデルのローカル保存
- GDPR準拠のデータ処理

### **認証・認可**
- 話者認証による本人確認
- 音声データアクセス制御
- 学習データの匿名化

## 📈 **パフォーマンス**

### **処理時間目標**
- **音声認識**: <2秒
- **AI応答生成**: <3秒
- **音声合成**: <2秒
- **声のクローニング**: <5秒
- **話者認証**: <1秒

### **品質指標**
- **音声認識精度**: >95%
- **話者認証精度**: >99.5%
- **感情分析精度**: >85%
- **音声合成品質**: 高品質（MOS > 4.0）

## 🗺️ **ロードマップ**

### **Phase 3: Cloudflare統合** （進行中）
- [ ] Cloudflare Workers実装
- [ ] CDN音声配信最適化
- [ ] エッジコンピューティング
- [ ] WebRTCリアルタイム通信

### **将来の拡張**
- [ ] 多言語音声クローニング
- [ ] 高度な感情制御
- [ ] ビデオ通話対応
- [ ] モバイルアプリ
- [ ] 企業向けエンタープライズ機能

## 📝 **ライセンス**

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 🙏 **謝辞**

- [WhisperX](https://github.com/m-bain/whisperX) - 高精度音声認識
- [VOICEVOX](https://voicevox.hiroshiba.jp/) - 自然な日本語音声合成
- [RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI) - 声質変換技術
- [SpeechBrain](https://speechbrain.github.io/) - 話者認識ツールキット

## 📞 **サポート**

- **ドキュメント**: [docs/](docs/)
- **Issue報告**: GitHub Issues
- **ディスカッション**: GitHub Discussions

---

**Voice Roleplay System v2.0.0** - 次世代音声AI技術で、より自然で個人化された対話体験を提供します 🚀
