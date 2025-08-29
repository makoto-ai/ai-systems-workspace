# scripts/quality/comment_pareto.sh
#!/usr/bin/env bash
set -euo pipefail
PR_NUM=$(gh pr view --json number --jq .number)
TOP=${1:-10}
echo "## 📊 Failure Pareto (top $TOP)" > out/pareto.md
echo "" >> out/pareto.md
echo "| Tag | Count | Share |" >> out/pareto.md
echo "|---:|---:|---:|" >> out/pareto.md
tail -n +2 out/pareto.csv | head -n "$TOP" | awk -F, '{printf("| %s | %s | %s%% |\n",$1,$2,$3)}' >> out/pareto.md
echo "" >> out/pareto.md
echo "- Total unique failures: $(jq '.total' out/tags.json)" >> out/pareto.md
echo "- 次の一手: 上位2タグに絞って小PR（最小正規化/局所±3%・ms↔秒/点パッチ）。" >> out/pareto.md
gh pr comment "$PR_NUM" --body-file out/pareto.md
