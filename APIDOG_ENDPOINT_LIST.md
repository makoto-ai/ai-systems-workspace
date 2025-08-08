# 🔧 APIDOG エンドポイント一覧 - app フォルダ解消結果

## ✅ 動作確認済み（Apidog テスト推奨）

### **基本機能**
```bash
# 基本ヘルスチェック（0.01秒）
GET http://localhost:8000/api/health/basic
Response: {"status":"ok"}

# 詳細ヘルスチェック
GET http://localhost:8000/api/health
Response: AI状態詳細情報
```

### **AI チャット機能** [[memory:4333578]]
```bash
# Regular AI Chat（メインエンドポイント、666ms）
POST http://localhost:8000/api/chat
Content-Type: application/json
{
  "message": "こんにちは、テストです",
  "max_tokens": 100
}
Response: AI応答 + モデル情報
```

### **音声合成機能**
```bash
# OpenAI互換TTS（修正済み）
POST http://localhost:8000/api/audio/speech
Content-Type: application/json
{
  "model": "tts-1",
  "input": "こんにちは、テストです",
  "voice": "alloy"
}
Response: WAVファイル（バイナリ）

# Dify互換TTS
POST http://localhost:8000/api/audio/speech-json
Content-Type: application/json
{
  "model": "tts-1",
  "input": "こんにちは、テストです",
  "voice": "alloy"
}
Response: Base64エンコードJSON
```

### **テキスト分析機能**
```bash
# サポート形式一覧
GET http://localhost:8000/api/text/supported-formats
Response: 対応ファイル形式一覧（200MB、50ファイル対応）

# モデル状態確認
GET http://localhost:8000/api/text/model-status
Response: テキスト分析モデル状態
```

## ⚠️ パラメータ修正が必要

### **リマインダー機能**
```bash
# セッション記録（要パラメータ修正）
POST http://localhost:8000/api/reminder/session/record
Content-Type: application/json
# 修正前（エラー）:
{
  "user_id": "test_user",
  "session_duration": 10,
  "scenario_type": "test"
}
# エラー: Field required: session_data

# 修正後（推奨）:
{
  "user_id": "test_user",
  "session_data": {
    "session_duration": 10,
    "scenario_type": "test",
    "performance_score": 0.8
  }
}
```

## 🚀 Apidog 設定手順

### **手動入力ワークフロー**（推奨）
1. **Cursor で相談** - API仕様確認・エラー対応検討
2. **手動入力** - 上記テスト済みパラメータをApidogに入力
3. **テスト実行** - レスポンス確認・デバッグ

### **優先テスト順序**
1. `GET /api/health/basic` - 接続確認
2. `POST /api/chat` - メイン機能
3. `POST /api/audio/speech` - 音声合成
4. `GET /api/text/supported-formats` - テキスト分析
5. `POST /api/reminder/session/record` - リマインダー（パラメータ修正後）

## 📊 解消状況

- ✅ **音声API** - modelパラメータ追加で解決
- ✅ **チャットAPI** - 正常動作確認
- ✅ **テキストAPI** - 正常動作確認  
- ⚠️ **リマインダーAPI** - session_dataパラメータ要修正
- ✅ **ヘルスAPI** - 全機能正常

## 💡 Apidog活用のポイント

- **手動入力が最も実用的** - 過度な自動化は不要
- **テスト済みパラメータ使用** - 上記の動作確認済み設定をコピー
- **段階的テスト** - 基本→チャット→音声→分析の順序
- **エラー時はCursorで相談** - パラメータ調整とデバッグ支援 