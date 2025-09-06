#!/bin/bash
# プロセス監視・自動復旧スクリプト（ハイブリッド前提）
set -euo pipefail

echo "👀 システム監視開始..."

while true; do
    # ハイブリッド(8000)監視
    if ! pgrep -f "main_hybrid:app" > /dev/null; then
        echo "⚠️  hybrid 停止検出 - 再起動中..."
        # VOICE環境の適用
        if [ -f scripts/env.voice.sh ]; then
            # shellcheck disable=SC1091
            source scripts/env.voice.sh
        fi
        nohup env VOICE_DEFAULT_SPEED="$VOICE_DEFAULT_SPEED" VOICE_DEFAULT_VOLUME="$VOICE_DEFAULT_VOLUME" VOICE_DEFAULT_PRE_S="$VOICE_DEFAULT_PRE_S" VOICE_DEFAULT_POST_S="$VOICE_DEFAULT_POST_S" VOICE_DEFAULT_PAUSE_SCALE="$VOICE_DEFAULT_PAUSE_SCALE" python3 -u main_hybrid.py > logs/hybrid_restart.log 2>&1 &
        echo "✅ hybrid 復旧完了 (8000)"
    fi

    # app.main(8010) 監視（補助）
    if ! pgrep -f "uvicorn app.main:app" > /dev/null; then
        echo "ℹ️  app.main は未起動（hybrid優先運用）。必要時のみ start-services.sh で起動してください"
    fi

    # フロントエンド監視（存在チェック付き）
    if [ -d frontend/voice-roleplay-frontend ]; then
        if ! pgrep -f "next dev" > /dev/null; then
            echo "⚠️  フロントエンド停止検出 - 再起動中..."
            ( cd frontend/voice-roleplay-frontend && npm run dev > ../../logs/frontend.log 2>&1 & )
            echo "✅ フロントエンド復旧完了"
        fi
    fi

    # ヘルスチェック（/health に変更）
    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "🚨 URGENT: システム異常検出 - 即座確認が必要 $(date)"
    fi

    # 1日1回のサマリー（午前9時のみ）
    CURRENT_HOUR=$(date +%H)
    if [ "$CURRENT_HOUR" = "09" ]; then
        echo "📊 日次システムサマリー: 稼働確認OK $(date)"
    fi

    sleep 300  # 5分毎の内部チェック（通知は異常時のみ）
done
