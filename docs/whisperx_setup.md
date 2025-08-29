# WhisperX 構築・運用手順

このドキュメントは、WhisperX をローカル環境で構築し、FastAPI 経由で提供し、GitHub Actions から `WHISPERX_ENDPOINT` として利用するまでの最短手順をまとめたものです。

## 1. 既存インストール確認

```bash
# venv がある場合: import 確認
source .venv/bin/activate 2>/dev/null || true
python - <<'PY'
try:
    import whisperx
    print('whisperx: ok')
except Exception as e:
    print('whisperx: missing', e)
PY
```

## 2. pyenv で専用環境を作る（必要な場合）

```bash
pyenv virtualenv 3.12.8 whisperx-312
pyenv local whisperx-312
python -m pip install -U pip
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
python -m pip install whisperx fastapi uvicorn[standard]
# macOS推奨
brew install ffmpeg
```

## 3. API サーバーを用意

`whisperx_api.py` がリポジトリに含まれています。以下で起動できます。

```bash
uvicorn whisperx_api:app --host 0.0.0.0 --port 5000
```

ヘルスチェック:

```bash
curl -s http://localhost:5000/health | jq
```

サンプル呼び出し:

```bash
curl -s -X POST http://localhost:5000/transcribe \
  -F "audio=@/path/to/input.wav" \
  -F "language=ja" | jq
```

## 4. 外部公開（任意: Cloudflare Tunnel 例）

```bash
cloudflared tunnel --url http://localhost:5000
```

表示された URL を `WHISPERX_ENDPOINT` として利用します。

## 5. GitHub Actions 連携

リポジトリ → Settings → Secrets and variables → Actions に登録:

- `WHISPERX_ENDPOINT`: 例 `https://your-tunnel.trycloudflare.com`

ワークフローは `deploy.yml` が `WHISPERX_ENDPOINT` を `$GITHUB_ENV` へ注入するよう設定済みです。

## 6. 運用メモ

- WhisperX モデル/デバイスは環境変数で変更可能:
  - `WHISPERX_MODEL` (default: `large-v2`)
  - `WHISPERX_DEVICE` (default: `cpu`)
  - `WHISPERX_COMPUTE_TYPE` (default: `int8`)
- 音質や速度に応じて `ctranslate2` の `compute_type` を変更してください。
- 大規模モデルで GPU を用いる場合は CUDA 環境と対応 wheel を利用してください。

### Groqメイン運用・WhisperXフォールバック

- STT呼び出しは `stt.py` の `transcribe(path)` を使用
- 優先順序: Groq(環境変数 `GROQ_API_KEY`) → WhisperX(環境変数 `WHISPERX_ENDPOINT`)
- `.env` を使う場合は `python-dotenv` が読み込み（ローカルのみ）

---

再構築が必要になった場合は本ドキュメントの 1→5 を順に実行してください。
