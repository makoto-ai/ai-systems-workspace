THRESHOLD?=0.72
RUN_ID?=
.PHONY: shadow canary-pr pr-url run-log metrics comment abort

shadow:
	python tests/golden/runner.py --threshold-shadow "0.70,0.72,0.75,0.80,0.85" --weights tests/golden/weights_phase4.yaml --report out/shadow_grid.json

canary-pr:
	git checkout -B canary/threshold-$(THRESHOLD)
	git add -A
	SKIP=pre-commit-check git commit -m "Data-Collection Canary: 0.70→$(THRESHOLD) threshold change"
	git push -u origin canary/threshold-$(THRESHOLD)
	gh pr create --draft --title "🔬 Data-Collection Canary: 0.70→$(THRESHOLD) threshold change" --body "Draftでデータ収集。早期Abort=Pass<65 or New>70。" --label canary --label staged-promotion --label data-collection

pr-url:
	gh pr view --json url --jq .url

run-log:
	gh run view $$(gh run list --limit 1 --json databaseId --jq '.[0].databaseId') --log > out/latest.log

metrics:
	python scripts/quality/parse_metrics.py out/latest.log > out/metrics.env
	@echo "metrics -> out/metrics.env"

comment:
	. out/metrics.env && scripts/quality/comment_summary.sh "$$PASS" "$$NEW" "$$FLAKY"

abort:
	. out/metrics.env && PASS=$$PASS NEW=$$NEW FLAKY=$$FLAKY python scripts/quality/abort_if_needed.py
