# scripts/quality/comment_summary.sh
#!/usr/bin/env bash
set -euo pipefail
PR_NUM=$(gh pr view --json number --jq .number)
PASS="${1:-unknown}"; NEW="${2:-unknown}"; FLAKY="${3:-unknown}"
gh pr comment "$PR_NUM" --body "$(cat <<MD
### 📊 Canary Metrics (auto)
- **Pass**: $PASS%
- **New**: $NEW%
- **Flaky**: $FLAKY%

判定基準:
- 昇格(0.72): Pass≥80 / New≤60 / Flaky<5
- 早期Abort(Data-Collection): Pass<65 or New>70

📝 自動解析: 最新Runログから抽出。値が'unknown'の場合はログ形式差異のため手動確認してください。
MD
)"
