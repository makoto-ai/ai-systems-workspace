# 📦 AI Voice Roleplay System - User Setup Guide

## 🎯 概要
AIを活用した音声ロールプレイシステム。WhisperXによる音声認識、Claude/GPTによる対話生成、Voicevoxによる音声合成を統合し、自然な音声対話を実現します。

---

## 📋 必要なもの

### 🖥️ システム要件
- **OS**: macOS 12.0+ / Ubuntu 20.04+ / Windows 11+
- **Python**: 3.12+
- **メモリ**: 8GB以上推奨
- **ストレージ**: 10GB以上の空き容量
- **ネットワーク**: 安定したインターネット接続

### 🔑 APIキー
- **Anthropic Claude**: APIキー（必須）
- **OpenAI GPT-4**: APIキー（推奨）
- **その他**: 必要に応じて追加

### 🎤 音声関連
- **マイク**: 高品質なマイク推奨
- **スピーカー**: 音声出力用
- **WhisperX**: 音声認識エンジン
- **Voicevox**: 音声合成エンジン

---

## 🚀 クイックスタート

### 1. リポジトリのクローン
```bash
git clone https://github.com/your-username/ai-voice-roleplay-system.git
cd ai-voice-roleplay-system
```

### 2. 環境設定
```bash
# 仮想環境作成
python3 -m venv .venv

# 仮想環境アクティベート
source .venv/bin/activate  # macOS/Linux
# または
.venv\Scripts\activate     # Windows

# 依存関係インストール
pip install -r requirements.txt
```

### 3. 設定ファイル作成
```bash
# 環境変数ファイル作成
cp env.example .env

# APIキーを設定
nano .env
```

### 4. システム起動
```bash
# 簡単起動
./scripts/start_roleplay.sh

# または詳細オプション
./scripts/start_roleplay.sh --help
```

---

## ⚙️ 詳細設定

### 🔧 環境変数設定
`.env`ファイルに以下を設定：

```bash
# Anthropic Claude API
ANTHROPIC_API_KEY=your_claude_api_key_here

# OpenAI GPT-4 API
OPENAI_API_KEY=your_openai_api_key_here

# 音声設定
AUDIO_INPUT_DEVICE=default
AUDIO_OUTPUT_DEVICE=default
SAMPLE_RATE=16000

# システム設定
LOG_LEVEL=INFO
BACKUP_ENABLED=true
MONITORING_ENABLED=true
```

### 🎤 音声設定
`config/voice_settings.json`で音声パラメータを調整：

```json
{
  "whisperx": {
    "model_size": "large-v3",
    "language": "ja",
    "compute_type": "float16"
  },
  "voicevox": {
    "speaker_id": 1,
    "speed": 1.0,
    "pitch": 0.0
  }
}
```

### 📝 プロンプト設定
`config/prompt_templates/`ディレクトリでプロンプトをカスタマイズ：

- `conversation_template.md`: 対話テンプレート
- `feedback_template.md`: フィードバックテンプレート
- `roleplay_template.md`: ロールプレイテンプレート

---

## 🎮 使用方法

### 基本的な音声対話
1. システム起動
2. マイクに向かって話す
3. AIが応答を生成
4. 音声で応答を受信

### ロールプレイモード
1. ロール設定を選択
2. シナリオを開始
3. キャラクターになりきって対話
4. セッション終了時に記録保存

### バッチ処理モード
1. 音声ファイルを指定
2. 一括処理を実行
3. 結果をObsidianに保存

---

## 📊 監視・ログ

### 📈 システム監視
- **Grafanaダッシュボード**: http://localhost:3000
- **Prometheusメトリクス**: http://localhost:9090
- **ログファイル**: `logs/`ディレクトリ

### 🔍 ログ確認
```bash
# リアルタイムログ
tail -f logs/system.log

# エラーログ
grep ERROR logs/system.log

# パフォーマンスログ
grep PERFORMANCE logs/system.log
```

---

## 🔧 トラブルシューティング

### よくある問題

#### 1. 音声認識が動作しない
```bash
# WhisperXの確認
python -c "import whisperx; print('WhisperX OK')"

# マイク権限の確認
ls -la /dev/audio*
```

#### 2. APIキーエラー
```bash
# 環境変数の確認
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# .envファイルの確認
cat .env
```

#### 3. 依存関係エラー
```bash
# 仮想環境の再作成
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 🆘 サポート
- **GitHub Issues**: バグ報告・機能要望
- **ドキュメント**: `/docs/`ディレクトリ
- **ログ分析**: `/logs/`ディレクトリ

---

## 🔄 アップデート

### システムアップデート
```bash
# 最新版の取得
git pull origin main

# 依存関係の更新
pip install -r requirements.txt --upgrade

# 設定ファイルの更新確認
diff env.example .env
```

### バックアップ
```bash
# 手動バックアップ
./scripts/backup/weekly_backup.sh

# 自動バックアップ（cron設定）
crontab -e
# 0 3 * * 1 /path/to/backup/script.sh
```

---

## 📚 参考資料

### 📖 ドキュメント
- [システム構成図](docs/ai-roleplay-system-architecture.md)
- [API仕様書](docs/api-specification.md)
- [ユーザーガイド](docs/user-guide.md)

### 🎥 チュートリアル
- [基本セットアップ動画](https://youtube.com/watch?v=...)
- [高度な設定動画](https://youtube.com/watch?v=...)
- [トラブルシューティング動画](https://youtube.com/watch?v=...)

### 💬 コミュニティ
- [Discord](https://discord.gg/...)
- [GitHub Discussions](https://github.com/.../discussions)
- [Twitter](https://twitter.com/...)

---

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。
詳細は[LICENSE](LICENSE)ファイルを参照してください。

---

*最終更新: 2025-08-04*
*バージョン: 1.0.0* 