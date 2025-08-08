# ✅ 【完全復旧用まとめ】CI/CD・セキュリティ・MCP設定フル構築ログ

---

## 🗂️ 1. GitHubリポジトリ構成・初期化

| 項目         | 内容                                                                                    |
| ---------- | ------------------------------------------------------------------------------------- |
| リポジトリ名     | `ai-systems-workspace`                                                                |
| GitHub URL | `https://github.com/makoto-ai/ai-systems-workspace`                                   |
| 初期化コマンド    | `git init` → `gh repo create` → `git remote add origin` → `git push -u origin master` |
| MCP構成ファイル  | `.cursor/mcp.json`（後述）                                                                |

---

## ⚙️ 2. GitHub Actions（CI/CD）構成

### 📄 `.github/workflows/pre-commit.yml`

```yaml
name: Run Pre-Commit Checks
on: [push, pull_request]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install pre-commit
          pre-commit install-hooks
      - name: Run pre-commit checks
        run: pre-commit run --all-files
```

---

## 🔒 3. pre-commit によるセキュリティ・品質チェック構成

### 📄 `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: check-yaml
      - id: check-json
      - id: detect-aws-credentials
      - id: detect-private-key
      - id: check-added-large-files
      - id: end-of-file-fixer
      - id: trailing-whitespace

  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
      - id: black

  - repo: https://gitlab.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit

  - repo: https://github.com/pypa/pip-audit
    rev: v2.7.2
    hooks:
      - id: pip-audit
```

---

## 🧠 4. MCPファイル（Cursor用）`.cursor/mcp.json`

```json
{
  "name": "ai-systems-workspace",
  "goals": [
    "Set up CI/CD using GitHub Actions",
    "Implement pre-commit hooks for quality and security",
    "Deploy with GitHub Pages or FastAPI"
  ],
  "tools": ["git", "gh", "pre-commit", "black", "flake8", "bandit", "pip-audit"],
  "language": "Python",
  "pythonVersion": "3.12",
  "framework": "FastAPI"
}
```

---

## 🐳 5. `docker-compose.yml`（FastAPIで開発していた場合）

```yaml
version: '3.9'

services:
  app:
    build: .
    container_name: ai-systems-app
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📜 6. README.md への追記（CIバッジなど）

```md
## ✅ CI/CD Status

![CI](https://github.com/makoto-ai/ai-systems-workspace/actions/workflows/pre-commit.yml/badge.svg)

This project includes:
- GitHub Actions-based CI
- Pre-commit hooks for quality & security
- Static analysis via Bandit, pip-audit
```

---

## ✅ 7. ターミナルでの主要操作履歴（再現用）

```bash
# pyenvでPython 3.12.8の設定
pyenv shell 3.12.8

# GitHub認証
gh auth login --web

# プロジェクト初期化
git init
git add .
git commit --no-verify -m "first commit"
gh repo create ai-systems-workspace --public --confirm
git remote add origin https://github.com/makoto-ai/ai-systems-workspace.git
git push -u origin master

# pre-commit有効化
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

---

## 🔄 再構築方法（カーソルに貼り付ける指示）

```bash
# MCP再作成
mkdir -p .cursor
echo '{
  "name": "ai-systems-workspace",
  "goals": [
    "Set up CI/CD using GitHub Actions",
    "Implement pre-commit hooks for quality and security",
    "Deploy with GitHub Pages or FastAPI"
  ],
  "tools": ["git", "gh", "pre-commit", "black", "flake8", "bandit", "pip-audit"],
  "language": "Python",
  "pythonVersion": "3.12",
  "framework": "FastAPI"
}' > .cursor/mcp.json
```

---

## 🎯 補足（カーソル再構築のポイント）

* `.cursor/mcp.json` があれば、Cursorは「プロジェクト目標」を理解し、必要なステップを自動で提案します。
* `.pre-commit-config.yaml` は復旧後に「再インストールコマンド（`pre-commit install`）」を再実行してください。
* `.github/workflows` 以下が消された場合は、GitHub Actionsが動作しなくなるため、再作成が必要です。

---

## ✅ 結論：このまとめをカーソルに貼り付ければ全復旧できます

Makotoさんがこのページで構築した内容は、**カーソルが一時的に削除してしまっても、上記まとめをそのまま指示すれば完全復元が可能です。**
特に `.cursor/mcp.json` + `.pre-commit-config.yaml` + `.github/workflows/pre-commit.yml` の3点セットが重要です。

---

## 🚀 現在のシステム統合状況

### ✅ 復旧済みシステム
- **動作確認済みYouTube原稿システム**: `working_youtube_script_system.py`
- **Streamlit UI**: `ui/streamlit_app.py`
- **品質メトリクス**: `services/quality_metrics.py`
- **信頼性エンフォーサー**: `system_reliability_enforcer.py`

### 🔄 次回復旧時の優先順位
1. **CI/CD設定**: `.github/workflows/`, `.pre-commit-config.yaml`
2. **MCP設定**: `.cursor/mcp.json`
3. **基本システム**: `working_youtube_script_system.py`
4. **UIシステム**: `ui/streamlit_app.py`
5. **品質システム**: `services/quality_metrics.py`

---

**作成日**: 2025年8月8日  
**作成者**: AI Assistant + Makoto  
**用途**: 完全システム復旧マニュアル 