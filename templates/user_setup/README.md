# 📦 User Template Setup Guide

## 🎯 概要

AIロールプレイシステムの商用展開用テンプレートです。他ユーザーが簡単にセットアップできるよう、必要な手順とファイルを整理しています。

## 📋 必要なもの

### システム要件
- **OS**: macOS 12+ / Ubuntu 20.04+ / Windows 11+
- **Python**: 3.12+
- **Docker**: 20.10+ (オプション)
- **Git**: 2.30+

### 必須ソフトウェア
- **WhisperX**: 音声認識・話者分離
- **Voicevox**: 音声合成（日本語対応）
- **Claude API**: 構成・要約生成
- **GPT-4 API**: 構文チェック・検証

## 🚀 クイックスタート

### 1. リポジトリクローン
```bash
git clone https://github.com/your-username/ai-systems-workspace.git
cd ai-systems-workspace
```

### 2. 環境設定
```bash
# 仮想環境作成
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# 依存関係インストール
pip install -r requirements.txt
```

### 3. 環境変数設定
```bash
# 環境変数ファイル作成
cp env.example .env

# APIキー設定
echo "CLAUDE_API_KEY=your_claude_key" >> .env
echo "OPENAI_API_KEY=your_openai_key" >> .env
echo "GROQ_API_KEY=your_groq_key" >> .env
```

### 4. 起動
```bash
# 1行で起動
./scripts/start_roleplay.sh
```

## 📁 ファイル構成

```
templates/user_setup/
├── README.md                    # このファイル
├── env.example                  # 環境変数テンプレート
├── project_status_template.md   # プロジェクト状況テンプレート
└── setup_guide.md              # 詳細セットアップガイド
```

## 🔧 設定項目

### 基本設定
- **APIキー**: Claude、OpenAI、Groq
- **データベース**: PostgreSQL、Redis
- **監視**: Prometheus、Grafana

### 音声処理設定
- **WhisperX**: 音声認識エンドポイント
- **Voicevox**: 音声合成エンドポイント
- **音声品質**: サンプリングレート、ビットレート

### AI設定
- **モデル選択**: Claude-3-Opus、GPT-4
- **温度設定**: 0.1-0.9（創造性調整）
- **トークン制限**: 最大出力文字数

## 📊 監視・ログ

### ダッシュボード
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **アプリケーション**: http://localhost:8000

### ログファイル
- **アプリケーション**: `logs/app.log`
- **音声処理**: `logs/voice.log`
- **バックアップ**: `logs/backup.log`

## 🔄 自動化機能

### バックアップ
```bash
# 週次バックアップ実行
./scripts/backup/weekly_backup.sh

# crontab設定（毎週月曜朝3時）
0 3 * * 1 bash ~/ai-systems-workspace/scripts/backup/weekly_backup.sh
```

### CI/CD
- **GitHub Actions**: 自動テスト・デプロイ
- **Docker**: コンテナ化・環境統一
- **Vault**: シークレット管理

## 🛠 トラブルシューティング

### よくある問題

#### 1. APIキーエラー
```bash
# 環境変数確認
echo $CLAUDE_API_KEY
echo $OPENAI_API_KEY

# .envファイル確認
cat .env
```

#### 2. 依存関係エラー
```bash
# 仮想環境確認
which python
pip list

# 依存関係再インストール
pip install -r requirements.txt --force-reinstall
```

#### 3. ポート競合
```bash
# 使用中ポート確認
lsof -i :8000
lsof -i :3000
lsof -i :9090

# プロセス終了
kill -9 <PID>
```

## 📞 サポート

### ドキュメント
- **システム構成**: `docs/system_architecture.md`
- **API仕様**: `docs/api_specification.md`
- **トラブルシューティング**: `docs/troubleshooting.md`

### コミュニティ
- **GitHub Issues**: バグ報告・機能要望
- **Discord**: リアルタイムサポート
- **Email**: support@your-domain.com

## 📄 ライセンス

MIT License - 詳細は `LICENSE` ファイルを参照してください。

---

*このテンプレートは商用展開を想定して作成されています。* 