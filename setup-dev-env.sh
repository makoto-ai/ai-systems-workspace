#!/bin/bash
# 音声ロールプレイシステム v2.0.0 - 開発環境セットアップスクリプト

set -e

echo "🚀 音声ロールプレイシステム開発環境セットアップ開始"
echo "=================================================="

# 色付きログ関数
log_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

log_warn() {
    echo -e "\033[33m[WARN]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

# 1. 前提条件チェック
log_info "前提条件をチェック中..."
if ! command -v docker &> /dev/null; then
    log_error "Docker がインストールされていません"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose がインストールされていません"
    exit 1
fi

# 2. 既存コンテナ停止・削除
log_info "既存のコンテナを停止・削除中..."
docker-compose down -v 2>/dev/null || true

# 3. 環境変数設定
log_info "環境変数を設定中..."
if [ ! -f .env.local ]; then
    log_warn ".env.local が存在しません。.env.docker をコピーします"
    cp .env.docker .env.local
fi

# 4. Docker イメージ取得・ビルド
log_info "Docker イメージを取得中..."
docker-compose pull

# 5. データベース初期化
log_info "データベースを初期化中..."
docker-compose up -d roleplay-db analytics-db

# データベース起動を待機
log_info "データベースの起動を待機中..."
sleep 20

# 6. Redis起動
log_info "Redis キャッシュを起動中..."
docker-compose up -d redis-cache

# 7. VOICEVOX Engine起動
log_info "VOICEVOX Engine を起動中..."
docker-compose up -d voicevox-engine

# 8. 監視システム起動
log_info "監視システムを起動中..."
docker-compose up -d prometheus grafana

# 9. 管理ツール起動
log_info "管理ツールを起動中..."
docker-compose up -d pgadmin redis-commander

# 10. ヘルスチェック
log_info "サービスのヘルスチェック中..."
sleep 30

# データベース接続テスト
if docker exec voice-roleplay-db pg_isready -U voice_user -d voice_roleplay_db > /dev/null 2>&1; then
    log_info "✅ PostgreSQL (ロールプレイDB) 接続OK"
else
    log_error "❌ PostgreSQL (ロールプレイDB) 接続失敗"
fi

if docker exec voice-analytics-db pg_isready -U analytics_user -d voice_analytics_db > /dev/null 2>&1; then
    log_info "✅ TimescaleDB (分析DB) 接続OK"
else
    log_error "❌ TimescaleDB (分析DB) 接続失敗"
fi

# Redis接続テスト
if docker exec voice-redis-cache redis-cli ping > /dev/null 2>&1; then
    log_info "✅ Redis キャッシュ 接続OK"
else
    log_error "❌ Redis キャッシュ 接続失敗"
fi

# VOICEVOX接続テスト
if curl -s http://localhost:50021/docs > /dev/null 2>&1; then
    log_info "✅ VOICEVOX Engine 接続OK"
else
    log_warn "⚠️  VOICEVOX Engine まだ起動中... (初回は時間がかかります)"
fi

# 11. Python依存関係インストール
log_info "Python依存関係をインストール中..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pip install asyncpg timescaledb-python redis psycopg2-binary sqlalchemy alembic
    log_info "✅ Python依存関係のインストール完了"
else
    log_warn "⚠️  .venv が見つかりません。手動でPython環境を設定してください"
fi

# 12. 完了報告
echo ""
echo "🎉 開発環境セットアップ完了！"
echo "=================================================="
echo ""
echo "📊 アクセス情報:"
echo "  🖥️  FastAPI (アプリ): http://localhost:8000"
echo "  ��️  pgAdmin: http://localhost:8080"
echo "  📊  Grafana: http://localhost:3000"
echo "  📈  Prometheus: http://localhost:9090"
echo "  🔧  Redis Commander: http://localhost:8081"
echo "  🎵  VOICEVOX Engine: http://localhost:50021"
echo ""
echo "🔐 ログイン情報:"
echo "  pgAdmin: admin@voice-roleplay.local / pgadmin_2024"
echo "  Grafana: admin / voice_admin_2024"
echo ""
echo "▶️  アプリケーション起動コマンド:"
echo "  source .venv/bin/activate"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "🛑 環境停止コマンド:"
echo "  docker-compose down"
echo ""
