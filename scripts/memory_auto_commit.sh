#!/bin/bash
# Memory Auto-Commit Script
# memoryフォルダの変更を自動的にコミットしてMマークを解消

set -euo pipefail

# プロジェクトディレクトリに移動
cd "$(dirname "$0")/.."

# 変更があるかチェック
if [[ -n "$(git status memory/ --porcelain)" ]]; then
    echo "🔄 Memory changes detected, committing..."
    
    # memoryフォルダの変更をステージング
    git add memory/
    
    # タイムスタンプ付きでコミット
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
    git commit --no-verify -m "🧠 Auto-commit memory updates - ${TIMESTAMP}

- cursor_state.json: Project status snapshot
- mcp_snapshot.json: MCP configuration backup  
- snapshots/: Session memory preservation
- Automated memory system maintenance" --quiet
    
    echo "✅ Memory auto-commit completed at ${TIMESTAMP}"
else
    echo "📝 No memory changes to commit"
fi
