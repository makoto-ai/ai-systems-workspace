# 📧 ロールプレイリマインダーシステム セットアップガイド

## 概要

このリマインダーシステムは、営業ロールプレイの継続的実施を促進するために、ユーザーに自動的にメールリマインダーを送信します。

### 🎯 機能

- **3段階リマインダー**: 3日前、前日、当日にパーソナライズされたメールを送信
- **活動追跡**: ロールプレイセッションの記録と連続実行日数の管理
- **パーソナライズ**: ユーザーの実績に基づいたカスタマイズメッセージ
- **自動スケジューリング**: バックグラウンドで自動実行

## 📋 セットアップ手順

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. メール設定

#### A. 設定ファイルの作成

```bash
# サンプルをコピー
cp config/email_config.example.json config/email_config.json

# 設定を編集
vi config/email_config.json
```

#### B. Gmail使用時の設定例

```json
{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "username": "your-business-email@gmail.com",
  "password": "your-app-password",
  "from_email": "your-business-email@gmail.com",
  "from_name": "営業ロールプレイシステム",
  "use_tls": true
}
```

**⚠️ Gmailの場合の重要な設定:**

1. **2段階認証を有効化**
   - Googleアカウント設定 → セキュリティ → 2段階認証プロセス

2. **アプリパスワードを生成**
   - Googleアカウント設定 → セキュリティ → アプリパスワード
   - 「メール」を選択してパスワードを生成

3. **生成されたアプリパスワードを使用**
   - 通常のGmailパスワードではなく、生成されたアプリパスワードを使用

### 3. システム起動

```bash
# 開発環境
python -m uvicorn app.main:app --reload

# 本番環境
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🔧 API使用方法

### ユーザーのリマインダー設定

```bash
curl -X POST "http://localhost:8000/api/reminder/settings/update" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "email_address": "user@example.com",
    "user_name": "山田太郎",
    "email_enabled": true,
    "reminder_days": [3, 1, 0],
    "timezone": "Asia/Tokyo"
  }'
```

### ロールプレイセッション記録

```bash
curl -X POST "http://localhost:8000/api/reminder/session/record" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "scenario_type": "新規開拓",
    "duration_minutes": 15,
    "improvement_points": ["声のトーンを上げる", "商品説明を簡潔に"],
    "performance_score": 0.85
  }'
```

### 管理者機能

#### スケジューラー開始
```bash
curl -X POST "http://localhost:8000/api/reminder/scheduler/start"
```

#### 手動リマインダー送信
```bash
curl -X POST "http://localhost:8000/api/reminder/scheduler/send" \
  -d "reminder_type=1day"
```

#### ダッシュボード確認
```bash
curl "http://localhost:8000/api/reminder/dashboard"
```

## 📊 モニタリング

### ダッシュボードアクセス

- **Swagger UI**: `http://localhost:8000/docs`
- **リマインダーダッシュボード**: `GET /api/reminder/dashboard`

### ログ確認

```bash
# アプリケーションログ
tail -f data/app.log

# リマインダーログ
cat data/reminder_logs.json | jq '.[-10:]'
```

## 🎨 メールテンプレートカスタマイズ

テンプレートファイルの場所:
- `app/templates/email/3days_reminder.html`
- `app/templates/email/1day_reminder.html`
- `app/templates/email/same_day_reminder.html`
- `app/templates/email/base.html`

### カスタマイズ例

```html
{% extends "base.html" %}

{% block content %}
<h2>{{ user_name }}さん、こんにちは！</h2>

<p>{{ personalized_message }}</p>

<!-- カスタムコンテンツを追加 -->
<div class="custom-section">
    <h3>今週の特別オファー</h3>
    <p>ロールプレイ完了で特典プレゼント！</p>
</div>
{% endblock %}
```

## ⚙️ 設定オプション

### スケジューラー設定 (`config/reminder_scheduler.json`)

```json
{
  "enabled": true,
  "check_interval_minutes": 60,
  "daily_check_hour": 9,
  "timezone": "Asia/Tokyo",
  "max_emails_per_batch": 50
}
```

### リマインダーのタイミング

- **3days**: ロールプレイから3日経過でリマインダー
- **1day**: ロールプレイから1日経過でリマインダー
- **same_day**: 当日限りのリマインダー

## 🔍 トラブルシューティング

### よくある問題

#### 1. メールが送信されない

**原因**: SMTP設定が不正
**解決策**:
```bash
# メール接続テスト
curl -X POST "http://localhost:8000/api/reminder/email/test"
```

#### 2. スケジューラーが動作しない

**原因**: スケジューラーが停止している
**解決策**:
```bash
# ステータス確認
curl "http://localhost:8000/api/reminder/scheduler/status"

# 手動開始
curl -X POST "http://localhost:8000/api/reminder/scheduler/start"
```

#### 3. リマインダーが送信されすぎる

**原因**: 重複送信チェックの問題
**解決策**:
- データベースの `reminder_logs.json` を確認
- スケジューラーを一旦停止して再起動

### デバッグモード

```bash
# デバッグログ有効化
export LOG_LEVEL=DEBUG
python -m uvicorn app.main:app --reload
```

## 📈 運用のベストプラクティス

### 1. メール配信制限

- Gmail: 1日500通まで
- 商用SMTP: プロバイダーの制限を確認

### 2. ユーザーエクスペリエンス

- 配信停止機能の実装検討
- A/Bテストでメッセージ効果測定
- ユーザーフィードバックの収集

### 3. セキュリティ

- SMTP認証情報の安全な管理
- メールアドレスの暗号化検討
- ログのローテーション設定

## 🚀 次のステップ

1. **フロントエンド統合**: React/Vue.jsでの設定画面作成
2. **高度な分析**: メール開封率・クリック率の追跡
3. **マルチチャネル**: SMS、Slack、Teamsとの連携
4. **AI強化**: パーソナライズメッセージのAI生成

---

## 📞 サポート

質問やバグ報告は以下まで:
- GitHub Issues
- Discord サポートチャンネル
- メール: support@roleplay-system.com 