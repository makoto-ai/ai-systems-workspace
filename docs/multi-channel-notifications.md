# 📢 マルチチャンネル通知システム

## 概要

営業ロールプレイリマインダーを、メール以外の様々なチャンネルで受信できます。

### 🎯 利用可能なチャンネル

| チャンネル | コスト | 適用場面 | 設定難易度 |
|------------|--------|----------|------------|
| 📧 **メール** | 無料 | 基本通知 | ⭐ |
| 💬 **Slack** | 無料 | 企業・チーム | ⭐⭐ |
| 🎮 **Discord** | 無料 | コミュニティ・個人 | ⭐⭐ |
| 📱 **Telegram** | 無料 | 個人・海外 | ⭐⭐⭐ |
| 🏢 **Teams** | 無料 | 企業（Office365） | ⭐⭐ |
| 💚 **LINE** | 月1000通まで無料* | 日本の個人 | ⭐⭐⭐⭐ |
| 📞 **SMS** | 有料（5-10円/通）* | 緊急時 | ⭐⭐⭐⭐⭐ |

**\*コストが発生する可能性があります**

## 🚀 クイックスタート

### 1. 無料で始める推奨セット

**個人利用**
```bash
# 設定ファイルをコピー
cp config/notification_config.example.json config/notification_config.json

# Slack + Discord の組み合わせがおすすめ
```

**企業利用**
```bash
# Teams + Slack の組み合わせがおすすめ
```

### 2. API で利用可能チャンネル確認

```bash
curl "http://localhost:8000/api/reminder/channels/available"
```

### 3. コスト比較

```bash
curl "http://localhost:8000/api/reminder/channels/cost-comparison"
```

## 📋 チャンネル別セットアップ

### 💬 Slack（推奨・無料）

**1. Incoming Webhooks アプリを追加**
1. Slackワークスペースで App Directory を開く
2. "Incoming Webhooks" を検索してインストール
3. 通知を送信したいチャンネルを選択
4. Webhook URL をコピー

**2. 設定ファイル更新**
```json
{
  "slack": {
    "channel": "slack",
    "enabled": true,
    "webhook_url": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
    "additional_config": {
      "username": "営業ロールプレイBot",
      "emoji": ":speech_balloon:"
    }
  }
}
```

**3. テスト**
```bash
curl -X POST "http://localhost:8000/api/reminder/channels/test" \
  -d "channel=slack"
```

### 🎮 Discord（無料）

**1. Webhook設定**
1. Discordサーバーのテキストチャンネル設定を開く
2. 連携タブ → Webhooks → "新しいWebhook"
3. 名前とアイコンを設定
4. Webhook URLをコピー

**2. 設定ファイル更新**
```json
{
  "discord": {
    "channel": "discord",
    "enabled": true,
    "webhook_url": "https://discord.com/api/webhooks/000000000000000000/XXXXXXXXXXXXXXXXXXXXXXXX",
    "additional_config": {
      "username": "営業ロールプレイBot"
    }
  }
}
```

### 📱 Telegram（無料）

**1. ボット作成**
1. Telegramで @BotFather とチャット
2. `/newbot` コマンドでボット作成
3. ボット名とユーザー名を設定
4. Bot Token を取得

**2. チャンネル作成とボット追加**
1. 通知用チャンネル（グループ）を作成
2. 作成したボットをチャンネルに追加
3. ボットに管理者権限を付与

**3. チャンネルID取得**
```bash
# ボットをチャンネルに追加後、以下でチャンネルIDを確認
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
```

**4. 設定ファイル更新**
```json
{
  "telegram": {
    "channel": "telegram",
    "enabled": true,
    "bot_token": "123456789:ABCDEFghijklmnopQRSTuvwxyz",
    "channel_id": "-1001234567890"
  }
}
```

### 🏢 Microsoft Teams（無料）

**1. Incoming Webhook設定**
1. Teams チャンネルで "..." → コネクタ
2. "Incoming Webhook" を検索
3. 設定（名前、画像）
4. Webhook URL を取得

**2. 設定ファイル更新**
```json
{
  "teams": {
    "channel": "teams",
    "enabled": true,
    "webhook_url": "https://outlook.office.com/webhook/a1b2c3d4.../IncomingWebhook/..."
  }
}
```

### 💚 LINE（月1000通まで無料）

⚠️ **注意**: LINE APIは従量課金制です

**1. LINE Developers 設定**
1. [LINE Developers Console](https://developers.line.biz/) でアカウント作成
2. プロバイダーを作成
3. Messaging API チャンネルを作成
4. チャンネルアクセストークンを取得

**2. 設定ファイル更新**
```json
{
  "line": {
    "channel": "line",
    "enabled": true,
    "api_token": "YOUR_CHANNEL_ACCESS_TOKEN"
  }
}
```

**3. コスト管理**
- 月1000通まで無料
- 以降は 1通あたり約0.4円
- 月間使用量を監視推奨

### 📞 SMS（有料）

⚠️ **注意**: SMSは送信ごとにコストがかかります

現在Twilio連携の準備中です。緊急リマインダー用途での利用を想定しています。

## 🔧 API使用方法

### マルチチャンネルテスト

```bash
curl -X POST "http://localhost:8000/api/reminder/channels/test-multi" \
  -H "Content-Type: application/json" \
  -d '{
    "channels": ["slack", "discord"],
    "test_message": "マルチチャンネルテストです！"
  }'
```

### カスタム通知送信

```bash
curl -X POST "http://localhost:8000/api/reminder/send-custom-notification" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "重要なお知らせ",
    "content": "新しい営業研修が開始されます！",
    "user_id": "user123",
    "channels": ["slack", "discord", "telegram"],
    "action_url": "https://roleplay.example.com/training"
  }'
```

## 💡 利用シーン別推奨設定

### 🏃‍♂️ スタートアップ・個人

**推奨**: Slack + Discord（完全無料）
- 低コストで信頼性の高い通知
- 設定が簡単
- どちらか一方が失敗してもバックアップあり

### 🏢 企業・チーム

**推奨**: Teams + Slack
- 既存のOffice365環境との統合
- 営業チーム内での情報共有
- 企業セキュリティポリシーに適合

### 🇯🇵 日本市場特化

**推奨**: LINE（小規模） + Slack（バックアップ）
- 日本での高い普及率
- 月1000通まで無料（小規模なら十分）
- Slackをバックアップとして設定

### 🌍 海外展開

**推奨**: Telegram + Discord + Slack
- Telegramは海外で人気
- 多様な地域をカバー
- 言語対応しやすい

### 🚨 高優先度・緊急時

**推奨**: メール + Slack + SMS（緊急時のみ）
- 確実な到達を重視
- SMSは最後の手段として
- 段階的エスカレーション

## 📊 効果測定

### 到達率監視

```bash
# ダッシュボードで送信結果確認
curl "http://localhost:8000/api/reminder/dashboard"
```

### チャンネル別パフォーマンス

- Slack: 企業内での即座な確認 ⚡
- Discord: コミュニティでの自然な通知 🎮  
- Telegram: 個人利用での確実な到達 📱
- Teams: ビジネス環境での公式通知 🏢
- LINE: 日本での個人通知 💚
- SMS: 緊急時の確実な通知 📞

## 🔧 トラブルシューティング

### よくある問題

**1. Webhook URLが無効**
```bash
# テスト実行で確認
curl -X POST "http://localhost:8000/api/reminder/channels/test" -d "channel=slack"
```

**2. 権限エラー（Telegram/LINE）**
- ボットが適切なチャンネルに追加されているか確認
- 管理者権限が付与されているか確認

**3. 通知が届かない**
- 設定ファイルの enabled フラグを確認
- APIキーやトークンの有効期限を確認
- ログでエラーメッセージを確認

### デバッグモード

```bash
export LOG_LEVEL=DEBUG
python -m uvicorn app.main:app --reload
```

## 💰 コスト最適化

### 無料プランでの運用

**月間想定通知数**: 
- ユーザー100人 × 週2回リマインダー = 月800通
- LINE無料枠（1000通）内で運用可能

**コスト削減のコツ**:
1. メインは無料チャンネル（Slack/Discord）
2. LINEは日本ユーザーのみに限定
3. SMSは本当の緊急時のみ
4. 複数チャンネル設定でリダンダンシー確保

### スケールアップ時の戦略

**月5000通 の場合**:
- LINE: 約1600円/月（4000通 × 0.4円）
- SMS: 約20,000円/月（4000通 × 5円）
- Slack/Discord/Telegram: 無料

**→ 無料チャンネルをメインに、LINEを補完として使用**

---

## 🚀 次のステップ

1. **段階的導入**: まずSlackから開始
2. **ユーザーフィードバック**: どのチャンネルが効果的かモニタリング  
3. **A/Bテスト**: チャンネル別の効果測定
4. **自動最適化**: 成功率の高いチャンネルを優先

**効果的なマルチチャンネル戦略で、営業スキル向上の継続率を最大化しましょう！** 🎯 