# �� APIDOG クイックスタートガイド - app フォルダ完全解消

## 現実的ワークフロー
[[memory:4333578]] の通り、**Cursor + Apidogワークフローは手動入力で十分実用的**です。

### ✅ **推奨手順**: Cursor → 手動入力 → Apidog

1. **Cursor で相談**
   - AIアシスタントで実装方針を相談
   - API仕様やエラー対応を検討

2. **手動入力**
   - Apidogに必要なパラメータを手入力
   - 過度な自動化は不要

3. **Apidogテスト**
   - 設定済みエンドポイントでテスト実行
   - レスポンス確認とデバッグ

## 📋 利用可能エンドポイント（全て解消済み）

### **基本機能**
- `GET /api/health/basic` - 軽量ヘルスチェック（0.01秒）
- `GET /api/health` - 詳細ヘルスチェック
- `GET /api/health/detailed` - AI状態チェック

### **AI チャット機能** ⭐ **メインエンドポイント**
- `POST /api/chat` - Regular AI Chat（666ms）

### **音声機能** ✅ **修正完了**
- `POST /api/audio/speech` - OpenAI互換TTS（要model パラメータ）
- `POST /api/audio/speech-json` - Dify互換TTS
- `POST /api/voice/custom-voice-synthesis` - カスタム音声合成
- `POST /api/voice/upload-custom-voice` - 音声ファイルアップロード

### **テキスト分析**
- `GET /api/text/supported-formats` - サポート形式
- `POST /api/text/text/analyze` - テキスト分析
- `GET /api/text/model-status` - モデル状態
- `GET /api/text/health` - テキストAPIヘルス

### **リマインダー機能** ✅ **修正完了**
- `POST /api/reminder/session/record` - セッション記録（フォーム形式）
- `GET /api/reminder/settings/{user_id}` - 設定取得
- `POST /api/reminder/settings/update` - 設定更新
- `GET /api/reminder/stats/{user_id}` - 活動統計

## 🔧 **完全動作テスト設定**

### **1. 基本接続確認**
```bash
GET http://localhost:8000/api/health/basic
Response: {"status":"ok"}
```

### **2. AI チャット（メイン機能）**
```bash
POST http://localhost:8000/api/chat
Content-Type: application/json
{
  "message": "こんにちは、営業について相談したいです",
  "max_tokens": 200,
  "temperature": 0.7
}
```

### **3. 音声合成（修正済み）**
```bash
POST http://localhost:8000/api/audio/speech
Content-Type: application/json
{
  "model": "tts-1",
  "input": "営業スキルを向上させましょう",
  "voice": "alloy",
  "speed": 1.0
}
```

### **4. リマインダー記録（修正済み）**
```bash
POST http://localhost:8000/api/reminder/session/record
Content-Type: multipart/form-data
Form Data:
- user_id: test_user
- scenario_type: sales_practice
- duration_minutes: 15
- performance_score: 0.85
```

### **5. テキスト分析**
```bash
GET http://localhost:8000/api/text/supported-formats
Response: 200MB・50ファイル対応の詳細情報

POST http://localhost:8000/api/text/text/analyze
Content-Type: application/json
{
  "text": "お客様の課題を解決するために、弊社では...",
  "document_type": "sales_document",
  "analysis_type": "comprehensive"
}
```

## 🔧 **トラブルシューティング**

### フロントエンド接続エラー
```bash
# 環境変数確認
echo $NEXT_PUBLIC_API_URL

# サーバー再起動
npm run dev
```

### バックエンドエラー
```bash
# ヘルスチェック
curl http://localhost:8000/api/health/basic

# サーバー再起動
python -m app.main
```

## 📊 **現在の状況**
- ✅ バックエンド: `http://localhost:8000` で動作中
- ✅ フロントエンド: `http://localhost:3000` で動作中
- ✅ Apidog: 全エンドポイント設定済み・動作確認済み
- ✅ 軽量ヘルスチェック: 0.01秒で応答

## 💡 **最優先テスト項目（全て解消済み）**
1. ✅ `/api/health/basic` - 基本接続
2. ✅ `/api/chat` - AI会話機能 
3. ✅ `/api/audio/speech` - 音声合成（modelパラメータ追加済み）
4. ✅ `/api/reminder/session/record` - セッション記録（フォーム形式修正済み）
5. ✅ `/api/text/supported-formats` - テキスト分析

## 🎯 **Apidog活用成功パターン**

### **手動入力ベスト プラクティス**
1. **基本テスト**: ヘルスチェックから開始
2. **メイン機能**: AI chatで動作確認
3. **音声機能**: model パラメータ必須
4. **フォーム送信**: multipart/form-data使用
5. **エラー時**: Cursorで相談・パラメータ調整

app フォルダの全てのエラーが解消され、Apidogで完全テスト可能になりました！🎉 