# 🚀 Vercel クラウドデプロイガイド

## 📋 デプロイ手順

### 1. Vercelアカウント作成・ログイン
```bash
# Vercel CLIインストール
npm install -g vercel

# Vercelにログイン
vercel login
```

### 2. プロジェクトリンク
```bash
# プロジェクトルートで実行
vercel

# 質問への回答:
# ? Set up and deploy "voice-roleplay-system"? [Y/n] y
# ? Which scope do you want to deploy to? [あなたのアカウント]
# ? Link to existing project? [N/y] n
# ? What's your project's name? voice-roleplay-system
# ? In which directory is your code located? ./frontend/voice-roleplay-frontend
```

### 3. 環境変数設定（重要）

Vercelダッシュボードで以下の環境変数を設定：

```bash
# AIサービスAPIキー
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# アプリケーション設定
NEXT_PUBLIC_APP_URL=https://your-app.vercel.app
NEXT_PUBLIC_API_URL=https://your-app.vercel.app/api
NODE_ENV=production
```

### 4. 本番デプロイ
```bash
# 本番環境にデプロイ
vercel --prod
```

## 🔑 APIキー取得方法

### Groq API Key
1. https://console.groq.com/ にアクセス
2. アカウント作成・ログイン
3. API Keys → Create API Key
4. **無料枠**: 大容量利用可能

### OpenAI API Key  
1. https://platform.openai.com/ にアクセス
2. API Keys → Create new secret key
3. **注意**: 使用量に応じて課金

### Anthropic API Key
1. https://console.anthropic.com/ にアクセス
2. アカウント作成後APIキー生成
3. **無料クレジット**: 初回$5提供

### Google Generative AI
1. https://makersuite.google.com/ にアクセス
2. Get API Key → Create API Key
3. **無料枠**: 月60リクエスト

## 🌍 デプロイ後の確認

### アクセスURL
```
メインサイト: https://your-app.vercel.app
ファイル連携: https://your-app.vercel.app/file-upload
ロールプレイ: https://your-app.vercel.app/roleplay
API健康状態: https://your-app.vercel.app/api/health
```

### モバイル対応確認
- スマートフォンから上記URLにアクセス
- 音声録音機能のテスト
- ファイルアップロード機能のテスト

## 🔧 トラブルシューティング

### よくある問題

1. **APIキーエラー**
   - Vercelダッシュボードで環境変数を再確認
   - APIキーの有効性をチェック

2. **ファイルアップロードエラー**
   - Vercel Functions の25MBサイズ制限を確認
   - APIキーの使用量制限をチェック

3. **音声処理エラー**
   - Groq API キーの設定を確認
   - 対応音声形式（wav, mp3, m4a, webm）をチェック

## 📱 お客さんへの案内

デプロイ完了後、お客さんに以下を案内：

```
🌐 URL: https://your-app.vercel.app

✅ どこからでもアクセス可能
✅ スマートフォン完全対応  
✅ 音声録音・AI分析
✅ ファイルアップロード機能
✅ 高速・安定動作

📱 モバイルブラウザからアクセスして、
ホーム画面に追加すればアプリのように利用可能！
```
