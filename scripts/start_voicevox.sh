#!/bin/bash
set -euo pipefail

echo "[voicevox] 起動チェック..."

if ! command -v docker >/dev/null 2>&1; then
  echo "[voicevox] Dockerが見つかりません" >&2
  exit 1
fi

# Docker起動待ち（最大60秒）
i=0
until docker info >/dev/null 2>&1 || [ $i -ge 60 ]; do i=$((i+1)); sleep 1; done

CONTAINER_NAME=voicevox
# 安定タグ（CPU版）
IMAGE=ghcr.io/voicevox/voicevox_engine:cpu-ubuntu22.04-0.15.4
PORT=50021

if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "[voicevox] 稼働中: http://localhost:${PORT}"
  exit 0
fi

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "[voicevox] 既存コンテナを起動します..."
  docker start ${CONTAINER_NAME} >/dev/null
else
  echo "[voicevox] コンテナを新規作成して起動します..."
  docker pull ${IMAGE} >/dev/null 2>&1 || true
  docker run -d --name ${CONTAINER_NAME} -p ${PORT}:50021 \
    -e VV_ENABLE_CORS=1 \
    ${IMAGE} >/dev/null
fi

# 起動確認
for _ in $(seq 1 30); do
  if curl -sSf http://localhost:${PORT}/version >/dev/null 2>&1; then
    echo "[voicevox] 起動完了: http://localhost:${PORT}"
    exit 0
  fi
  sleep 1
done

echo "[voicevox] 起動確認タイムアウト" >&2
exit 1


