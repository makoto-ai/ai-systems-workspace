# 🐳 Docker CI/CD & Vault連携 完全ガイド

## 📋 概要

このガイドでは、AIシステムのDocker CI/CD & Vault連携の設定と使用方法を説明します。

## 🚀 セットアップ手順

### 1. Vaultシークレット登録

```bash
# Vault CLIインストール（未インストールの場合）
brew install vault

# ローカルVault起動
vault server -dev

# シークレット登録
vault kv put secret/ai-systems \
  CLAUDE_API_KEY="sk-xxxxxxxxx" \
  OPENAI_API_KEY="sk-yyyyyyyyy" \
  GROQ_API_KEY="gsk-xxxxxxxxx" \
  WHISPERX_ENDPOINT="http://localhost:8000" \
  DATABASE_URL="postgresql://ai_user:ai_password@postgres:5432/ai_systems" \
  REDIS_URL="redis://redis:6379" \
  JWT_SECRET="your-jwt-secret-key" \
  ENCRYPTION_KEY="your-encryption-key"
```

### 2. シークレット管理

```bash
# シークレット読み込み
./scripts/load_secrets.sh load

# シークレット更新
./scripts/load_secrets.sh update CLAUDE_API_KEY "sk-new-key"

# シークレット一覧表示
./scripts/load_secrets.sh list

# シークレット削除
./scripts/load_secrets.sh delete OLD_API_KEY
```

### 3. Docker環境起動

```bash
# 完全環境起動
docker-compose up -d

# ログ確認
docker-compose logs -f ai-systems

# 特定サービス起動
docker-compose up -d ai-systems postgres redis
```

### 4. GitHub Actions設定

```bash
# GitHub Secrets設定
# リポジトリ設定 > Secrets and variables > Actions で以下を設定：

VAULT_ADDR=http://your-vault-server:8200
VAULT_TOKEN=your-vault-token
DOCKER_REGISTRY=ghcr.io
DOCKER_USERNAME=your-username
DOCKER_PASSWORD=your-token
```

## 🔐 Vault連携の詳細

### シークレット構造

```json
{
  "secret/ai-systems": {
    "CLAUDE_API_KEY": "sk-xxxxxxxxx",
    "OPENAI_API_KEY": "sk-yyyyyyyyy",
    "GROQ_API_KEY": "gsk-xxxxxxxxx",
    "WHISPERX_ENDPOINT": "http://localhost:8000",
    "DATABASE_URL": "postgresql://user:pass@localhost:5432/ai_systems",
    "REDIS_URL": "redis://localhost:6379",
    "JWT_SECRET": "your-jwt-secret-key",
    "ENCRYPTION_KEY": "your-encryption-key"
  }
}
```

### 環境変数マッピング

| 環境変数 | 説明 | デフォルト値 |
|----------|------|--------------|
| `CLAUDE_API_KEY` | Claude API キー | - |
| `OPENAI_API_KEY` | OpenAI API キー | - |
| `GROQ_API_KEY` | Groq API キー | - |
| `WHISPERX_ENDPOINT` | WhisperX エンドポイント | `http://localhost:8000` |
| `DATABASE_URL` | PostgreSQL 接続URL | - |
| `REDIS_URL` | Redis 接続URL | - |
| `JWT_SECRET` | JWT 署名キー | - |
| `ENCRYPTION_KEY` | 暗号化キー | - |

## 🐳 Docker サービス構成

### メインサービス

- **ai-systems**: AIシステムメインアプリケーション
- **postgres**: PostgreSQL データベース
- **redis**: Redis キャッシュ
- **vault**: HashiCorp Vault シークレット管理
- **nginx**: Nginx リバースプロキシ

### 監視サービス

- **prometheus**: メトリクス収集
- **grafana**: ダッシュボード表示

## 🔄 CI/CD ワークフロー

### 自動デプロイフロー

1. **GitHub Push** → GitHub Actions起動
2. **テスト実行** → pytest による自動テスト
3. **Docker ビルド** → マルチステージビルド
4. **セキュリティスキャン** → Trivy による脆弱性チェック
5. **コンテナレジストリプッシュ** → GitHub Container Registry
6. **本番デプロイ** → 自動デプロイ実行

### デプロイメント設定

```yaml
# .github/workflows/deploy.yml
name: 🚀 Auto Deploy via Docker

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: ✅ Checkout repository
        uses: actions/checkout@v4
      - name: 🧪 Run tests
        run: python -m pytest tests/ -v

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: 🐳 Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
```

## 📊 監視とログ

### アクセスURL

- **メインアプリケーション**: http://localhost:8000
- **API ドキュメント**: http://localhost:8000/docs
- **Grafana ダッシュボード**: http://localhost:3000
- **Prometheus メトリクス**: http://localhost:9090
- **Vault UI**: http://localhost:8200

### ログ確認

```bash
# 全サービスのログ
docker-compose logs -f

# 特定サービスのログ
docker-compose logs -f ai-systems

# リアルタイムログ
docker-compose logs -f --tail=100
```

## 🔧 トラブルシューティング

### よくある問題

1. **Vault接続エラー**
   ```bash
   # Vaultサーバー起動確認
   vault status
   
   # ローカルVault起動
   vault server -dev
   ```

2. **Docker ビルドエラー**
   ```bash
   # キャッシュクリア
   docker-compose build --no-cache
   
   # イメージ削除
   docker-compose down --rmi all
   ```

3. **データベース接続エラー**
   ```bash
   # PostgreSQL起動確認
   docker-compose logs postgres
   
   # データベース初期化
   docker-compose exec postgres psql -U ai_user -d ai_systems
   ```

### デバッグコマンド

```bash
# コンテナ内でシェル実行
docker-compose exec ai-systems bash

# 環境変数確認
docker-compose exec ai-systems env

# プロセス確認
docker-compose exec ai-systems ps aux

# ネットワーク確認
docker network ls
docker network inspect ai-systems-network
```

## 🚀 本番環境デプロイ

### 1. 環境変数設定

```bash
# 本番環境変数
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export DEBUG=false
```

### 2. セキュリティ設定

```bash
# SSL証明書設定
cp ssl/cert.pem nginx/ssl/
cp ssl/key.pem nginx/ssl/

# 認証設定
htpasswd -c nginx/.htpasswd admin
```

### 3. デプロイ実行

```bash
# 本番デプロイ
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# ヘルスチェック
curl -f http://localhost/health
```

## 📈 パフォーマンス最適化

### リソース制限

```yaml
# docker-compose.yml
services:
  ai-systems:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### キャッシュ設定

```yaml
# Redis キャッシュ設定
redis:
  command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
```

## 🔒 セキュリティベストプラクティス

1. **シークレット管理**: Vaultを使用して機密情報を管理
2. **ネットワーク分離**: 各サービスを適切に分離
3. **アクセス制御**: Nginxによる認証とレート制限
4. **監査ログ**: すべてのアクセスをログ記録
5. **定期的な更新**: セキュリティパッチの適用

## 📚 参考資料

- [Docker Compose 公式ドキュメント](https://docs.docker.com/compose/)
- [HashiCorp Vault 公式ドキュメント](https://www.vaultproject.io/docs)
- [GitHub Actions 公式ドキュメント](https://docs.github.com/en/actions)
- [Nginx 公式ドキュメント](https://nginx.org/en/docs/)

---

**🎉 これで、Docker CI/CD & Vault連携の設定が完了しました！** 