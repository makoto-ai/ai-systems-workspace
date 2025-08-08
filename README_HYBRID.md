# ハイブリッドAIシステム構成

MCPとComposerの統合システムで、Claude API、Whisper、Voicevox、Ollamaを自動制御する包括的なAIシステムです。

## 🏗️ アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                   ハイブリッドAIシステム                    │
├─────────────────────────────────────────────────────────────┤
│  🌐 FastAPI (main_hybrid.py)                              │
│  ├── 📝 Composer API (/composer/generate)                 │
│  ├── 🤖 MCP API (/mcp/generate)                          │
│  └── 🔄 Hybrid API (/hybrid/generate)                    │
├─────────────────────────────────────────────────────────────┤
│  🗄️  PostgreSQL  |  🔴 Redis  |  🔐 Vault               │
├─────────────────────────────────────────────────────────────┤
│  🎤 VOICEVOX  |  🤖 Ollama  |  📊 Prometheus            │
├─────────────────────────────────────────────────────────────┤
│  📈 Grafana  |  🔍 OpenTelemetry  |  📋 GitHub Actions   │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 クイックスタート

### 1. 環境変数の設定

```bash
# 環境変数ファイルをコピー
cp env.hybrid.example .env.hybrid

# 必要な環境変数を設定
export CLAUDE_API_KEY="your_claude_api_key"
export OPENAI_API_KEY="your_openai_api_key"
export GROQ_API_KEY="your_groq_api_key"
export POSTGRES_PASSWORD="your_secure_password"
export GRAFANA_PASSWORD="your_secure_password"
```

### 2. Docker Composeで起動

```bash
# ハイブリッド構成で起動
docker-compose -f docker-compose.hybrid.yml up -d

# または、デプロイスクリプトを使用
chmod +x scripts/hybrid-deploy.sh
./scripts/hybrid-deploy.sh
```

### 3. サービス確認

```bash
# ヘルスチェック
curl http://localhost:8000/health

# サービス情報
curl http://localhost:8000/system/status
```

## 📋 サービス一覧

| サービス | URL | 説明 |
|---------|-----|------|
| メインアプリケーション | http://localhost:8000 | FastAPI統合アプリ |
| MCPサービス | http://localhost:8001 | MCP専用API |
| Composerサービス | http://localhost:8002 | Composer専用API |
| Grafana | http://localhost:3000 | 監視ダッシュボード |
| Prometheus | http://localhost:9090 | メトリクス収集 |
| Vault | http://localhost:8200 | シークレット管理 |
| PostgreSQL | localhost:5432 | データベース |
| Redis | localhost:6379 | キャッシュ |
| VOICEVOX | http://localhost:50021 | 音声合成 |
| Ollama | http://localhost:11434 | ローカルLLM |

## 🔧 API エンドポイント

### Composer API

```bash
# スクリプト生成
curl -X POST http://localhost:8000/composer/generate \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "title": "AI技術の最新動向",
      "authors": ["田中太郎", "佐藤花子"],
      "abstract": "本研究では、最新のAI技術について調査を行った。",
      "publication_year": 2024
    },
    "abstract": "AI技術の最新動向について詳しく解説します。",
    "style": "popular"
  }'
```

### MCP API

```bash
# MCPスクリプト生成
curl -X POST http://localhost:8000/mcp/generate \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI技術の最新動向",
    "content": "AI技術について詳しく解説します。",
    "style": "educational"
  }'
```

### ハイブリッド API

```bash
# Composer + MCP統合生成
curl -X POST http://localhost:8000/hybrid/generate \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "title": "AI技術の最新動向",
      "authors": ["田中太郎", "佐藤花子"],
      "abstract": "本研究では、最新のAI技術について調査を行った。",
      "publication_year": 2024
    },
    "abstract": "AI技術の最新動向について詳しく解説します。",
    "style": "popular"
  }'
```

## 📊 監視とメトリクス

### OpenTelemetry統合

- **トレース**: 分散トレーシング
- **メトリクス**: Prometheus形式
- **ログ**: 構造化ログ

### Prometheusメトリクス

```bash
# メトリクスエンドポイント
curl http://localhost:8000/metrics

# 主要メトリクス
- ai_systems_requests_total
- ai_systems_errors_total
- ai_systems_response_time_seconds
- ai_systems_cpu_usage_percent
- ai_systems_memory_usage_percent
```

### Grafanaダッシュボード

- システム全体の監視
- AI API パフォーマンス
- データベース監視
- アラート設定

## 🔐 セキュリティ

### Vault統合

```bash
# Vaultシークレット管理
curl -X POST http://localhost:8200/v1/secret/data/ai-systems \
  -H "X-Vault-Token: dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "claude_api_key": "your_key",
      "openai_api_key": "your_key"
    }
  }'
```

### 環境変数管理

- 本番環境ではVaultを使用
- 開発環境では`.env.hybrid`
- GitHub SecretsでCI/CD統合

## 🤖 AI統合

### Claude API

```python
# Claude API統合
from youtube_script_generation_system import YouTubeScriptGenerator

generator = YouTubeScriptGenerator()
result = await generator.generate_script({
    "title": "AI技術解説",
    "content": "最新のAI技術について",
    "style": "educational"
})
```

### VOICEVOX統合

```python
# VOICEVOX音声合成
import requests

response = requests.post(
    "http://voicevox-engine:50021/audio_query",
    params={"text": "こんにちは", "speaker": 1}
)
```

### Ollama統合

```python
# OllamaローカルLLM
import requests

response = requests.post(
    "http://ollama:11434/api/generate",
    json={
        "model": "llama2",
        "prompt": "AI技術について説明してください"
    }
)
```

## 🔄 GitHub Actions自動化

### デプロイパイプライン

1. **セキュリティスキャン**: Bandit + Trivy
2. **テスト実行**: ユニットテスト + 統合テスト
3. **Dockerビルド**: マルチプラットフォーム
4. **Vault設定**: シークレット管理
5. **デプロイ**: Docker Compose
6. **監視設定**: Prometheus + Grafana
7. **パフォーマンステスト**: API負荷テスト
8. **自動化スクリプト**: メトリクス収集

### ワークフロー設定

```yaml
# .github/workflows/hybrid-deploy.yml
name: Hybrid AI Systems Deployment
on:
  push:
    branches: [main, develop]
    tags: ['v*']
```

## 📈 パフォーマンス最適化

### メトリクス収集

```bash
# メトリクス収集スクリプト
python scripts/collect_metrics.py

# ログ収集
python scripts/collect_logs.py
```

### キャッシュ戦略

- Redis: セッション管理
- PostgreSQL: 永続データ
- メモリキャッシュ: 高速アクセス

### スケーリング

```bash
# 水平スケーリング
docker-compose -f docker-compose.hybrid.yml up -d --scale ai-systems-app=3

# 負荷分散
docker-compose -f docker-compose.hybrid.yml up -d --scale mcp-service=2
```

## 🛠️ トラブルシューティング

### よくある問題

1. **Vault接続エラー**
   ```bash
   # Vault初期化
   curl -X POST http://localhost:8200/v1/sys/init
   ```

2. **OpenTelemetry接続エラー**
   ```bash
   # Collector再起動
   docker-compose -f docker-compose.hybrid.yml restart otel-collector
   ```

3. **メトリクス収集エラー**
   ```bash
   # メトリクススクリプト再起動
   pkill -f collect_metrics.py
   python scripts/collect_metrics.py &
   ```

### ログ確認

```bash
# アプリケーションログ
docker-compose -f docker-compose.hybrid.yml logs ai-systems-app

# メトリクスログ
tail -f logs/metrics.log

# システムログ
docker-compose -f docker-compose.hybrid.yml logs
```

## 🔧 開発環境

### ローカル開発

```bash
# 開発用環境変数
cp env.hybrid.example .env.hybrid.dev

# 開発モード起動
docker-compose -f docker-compose.hybrid.yml -f docker-compose.dev.yml up -d
```

### テスト実行

```bash
# ユニットテスト
python -m pytest tests/ -v

# 統合テスト
python -m pytest tests/integration/ -v

# パフォーマンステスト
python scripts/performance_test.py
```

## 📚 参考資料

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [OpenTelemetry公式ドキュメント](https://opentelemetry.io/)
- [Prometheus公式ドキュメント](https://prometheus.io/)
- [Vault公式ドキュメント](https://www.vaultproject.io/)
- [Docker Compose公式ドキュメント](https://docs.docker.com/compose/)

## 🤝 コントリビューション

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 ライセンス

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 