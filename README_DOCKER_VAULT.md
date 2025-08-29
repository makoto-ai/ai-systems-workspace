# 🐳 Docker CI/CD & Vault連携 完全実装ガイド

MakotoさんのAIシステム開発環境における**自動デプロイ**と**安全なシークレット管理**の完全実装テンプレートです。

---

## ✅ 実装完了項目

### 1. **Docker CI/CD 自動デプロイ**
- ✅ GitHub Actions ワークフロー (`.github/workflows/deploy.yml`)
- ✅ 自動ビルド・再起動
- ✅ 事前テスト実行
- ✅ ヘルスチェック

### 2. **Vault シークレット管理**
- ✅ Vault初期セットアップ (`scripts/setup_vault.sh`)
- ✅ シークレット読み込み (`scripts/load_secrets.sh`)
- ✅ Docker Compose統合 (`docker-compose.yml`)

---

## 🚀 使用方法

### Step 1: Vault初期セットアップ

```bash
# Vault CLI インストール & 初期設定
./scripts/setup_vault.sh
```

### Step 2: シークレット読み込み

```bash
# 環境変数としてシークレット読み込み
source scripts/load_secrets.sh
```

### Step 3: アプリケーション起動

```bash
# Docker Composeで起動
docker-compose up -d
```

---

## 🔐 Vault シークレット管理

### 登録済みシークレット

| 項目 | 説明 | デフォルト値 |
|------|------|-------------|
| `CLAUDE_API_KEY` | Claude API キー | `your_claude_key` |
| `OPENAI_API_KEY` | OpenAI API キー | `your_openai_key` |
| `GROQ_API_KEY` | Groq API キー | `your_groq_key` |
| `WHISPERX_ENDPOINT` | WhisperX エンドポイント | `http://localhost:8000` |
| `DATABASE_PASSWORD` | データベースパスワード | `ai_password` |
| `JWT_SECRET` | JWT署名キー | `default_jwt_secret` |
| `ENCRYPTION_KEY` | 暗号化キー | `default_encryption_key` |

### シークレット更新

```bash
# 個別更新
vault kv put secret/ai-systems CLAUDE_API_KEY="sk-new-key"

# 一括更新
vault kv put secret/ai-systems \
  CLAUDE_API_KEY="sk-xxxxxxxxx" \
  OPENAI_API_KEY="sk-yyyyyyyyy" \
  GROQ_API_KEY="sk-zzzzzzzzz"
```

---

## 🔄 GitHub Actions CI/CD

### 自動デプロイフロー

1. **Push to main** → GitHub Actions 起動
2. **Vault認証** → シークレット読み込み
3. **事前テスト** → pytest実行
4. **Docker再ビルド** → 最新コードでビルド
5. **コンテナ再起動** → 新しい環境で起動
6. **ヘルスチェック** → 動作確認

### GitHub Secrets設定

Repository Settings → Secrets and variables → Actions で以下を設定：

```
VAULT_TOKEN=your_vault_token
```

---

## 🐳 Docker Compose 構成

### サービス一覧

| サービス | ポート | 説明 |
|----------|--------|------|
| `app` | 8000 | メインAIアプリケーション |
| `postgres` | 5432 | PostgreSQL データベース |
| `redis` | 6379 | Redis キャッシュ |
| `vault` | 8200 | Vault シークレット管理 |

### 環境変数注入

```yaml
environment:
  - CLAUDE_API_KEY=${CLAUDE_API_KEY}
  - OPENAI_API_KEY=${OPENAI_API_KEY}
  - WHISPERX_ENDPOINT=${WHISPERX_ENDPOINT}
  # ... その他のシークレット
```

---

## 📊 監視・ログ

### ログ確認

```bash
# 全サービスログ
docker-compose logs

# 特定サービスログ
docker-compose logs app
docker-compose logs postgres
docker-compose logs vault
```

### システム状態確認

```bash
# コンテナ状態
docker-compose ps

# リソース使用量
docker stats
```

---

## 🔧 トラブルシューティング

### よくある問題

#### 1. Vault接続エラー
```bash
# Vaultサーバー起動確認
curl http://localhost:8200/v1/sys/health

# 手動起動
vault server -dev
```

#### 2. シークレット読み込みエラー
```bash
# シークレット存在確認
vault kv get secret/ai-systems

# 再登録
./scripts/setup_vault.sh
```

#### 3. Docker起動エラー
```bash
# ログ確認
docker-compose logs

# 強制再起動
docker-compose down
docker-compose up -d --force-recreate
```

---

## 🎯 セキュリティベストプラクティス

### ✅ 実装済み

- [x] シークレットの環境変数化
- [x] Vaultによる集中管理
- [x] Docker Compose統合
- [x] GitHub Actions連携

### 🔄 推奨追加設定

- [ ] Vault認証ポリシー設定
- [ ] シークレットローテーション
- [ ] 監査ログ設定
- [ ] バックアップ自動化

---

## 📈 パフォーマンス最適化

### 現在の構成

```yaml
# メモリ制限
services:
  app:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

### 推奨設定

```yaml
# 本番環境向け
services:
  app:
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

---

## 🎉 完了！

これで以下の機能が利用可能になりました：

1. **自動デプロイ**: GitHub Push → 自動ビルド・再起動
2. **安全なシークレット管理**: Vaultによる集中管理
3. **環境分離**: 開発・本番環境の完全分離
4. **監視・ログ**: 統合ログ・ヘルスチェック

### 次のステップ

1. 実際のAPIキーをVaultに登録
2. GitHub Secrets設定
3. 本番環境でのテスト実行

---

**🎯 これでMakotoさんのAIシステム開発環境が完全に自動化されました！**
