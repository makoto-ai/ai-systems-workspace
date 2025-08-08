# 🐳 Voice Roleplay System - Docker完全固定環境
FROM python:3.11-slim

# 作業ディレクトリ設定
WORKDIR /app

# システム依存関係インストール
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Node.js インストール (LTS版)
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs

# Python依存関係をコピーしてインストール
COPY requirements-frozen.txt .
RUN pip install --no-cache-dir -r requirements-frozen.txt

# アプリケーションファイルをコピー
COPY . .

# フロントエンド依存関係インストール
WORKDIR /app/frontend/voice-roleplay-frontend
RUN npm ci

# 作業ディレクトリを戻す
WORKDIR /app

# ポート公開
EXPOSE 8000 3000

# 起動スクリプト
CMD ["./docker-recovery.sh"]
