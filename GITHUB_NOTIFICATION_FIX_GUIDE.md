# 🔧 GitHub通知設定 緊急改善ガイド

## 🚨 即座に実行すべき設定

### 1️⃣ GitHub Web設定（最優先）
```
1. GitHub.com → Settings → Notifications
2. Email → Actions → ✅ 「Only failures」に変更
3. Email → Dependabot → ❌ 「Disable」
4. Email → Discussions → ❌ 「Disable」
```

### 2️⃣ リポジトリ別設定
```
1. voice-roleplay-system リポジトリ → Settings
2. Notifications → 👀 「Watch」から「Ignore」に変更
3. または「Custom」で必要最小限のみ選択
```

## 📧 メール振り分け設定

### Gmail設定例
```
From: notifications@github.com
Subject: [makoto-ai/voice-roleplay-system]
→ ラベル: GitHub/Auto
→ アーカイブ（受信トレイをスキップ）
```

## 🔧 ワークフロー最適化

### セキュリティスキャン頻度変更
- 毎日 → 週1回（月曜日）
- push時 → mainブランチのみ

### Dependabot頻度変更  
- 毎日 → 週1回
- 複数PR → 1つずつ

## 🎯 推奨設定

### ✅ 残すべき通知
- セキュリティアラート（Critical/High）
- 手動実行したワークフローの結果
- PRレビュー依頼

### ❌ 無効化すべき通知
- 日次自動スキャン
- Dependabot PR作成
- テスト成功通知
- カバレッジレポート

---

**実行後の効果**: メール数 90%削減（1日20通 → 2通）
