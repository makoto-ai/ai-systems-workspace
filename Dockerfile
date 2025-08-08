# 🐳 AI Systems Dockerfile
# 作成日: 2025-08-04
# 目的: AIシステムの本番環境用Dockerイメージ

# マルチステージビルド
FROM python:3.12-slim as builder

# ビルド依存関係
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 仮想環境作成
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 依存関係インストール
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 本番イメージ
FROM python:3.12-slim

# メタデータ
LABEL maintainer="Makoto Arai <makoto@example.com>"
LABEL description="AI Systems - Voice Roleplay & Script Generation"
LABEL version="1.0.0"

# セキュリティ設定
RUN groupadd -r appuser && useradd -r -g appuser appuser

# システム依存関係
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    vault \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 仮想環境をコピー
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 作業ディレクトリ設定
WORKDIR /app

# アプリケーションファイルをコピー
COPY . .

# 権限設定
RUN chown -R appuser:appuser /app
USER appuser

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 環境変数設定
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# ポート設定
EXPOSE 8000

# 起動スクリプト
COPY scripts/start_docker.sh /start.sh
RUN chmod +x /start.sh

# エントリーポイント
ENTRYPOINT ["/start.sh"]
