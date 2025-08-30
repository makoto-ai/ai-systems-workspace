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
.PHONY: run-log tag pareto pareto-comment learn-loop auto-improve quality-cycle regression-check learning-report
run-log:
	gh run view $$(gh run list --limit 1 --json databaseId --jq '.[0].databaseId') --log > out/latest.log
tag:
	python scripts/quality/tag_failures.py out/latest.log
pareto:
	@tail -n +2 out/pareto.csv | column -t -s, | head -n 10
pareto-comment:
	scripts/quality/comment_pareto.sh 10
learn-loop: run-log tag pareto pareto-comment

# 高品質自動改善システム
auto-improve: learn-loop
	@echo "🚀 自動品質改善システム開始"
	python scripts/quality/regression_detector.py baseline before_fix
	python scripts/quality/auto_fix_generator.py
	python scripts/quality/regression_detector.py detect after_fix

# 完全品質サイクル（分析→修正→検証→学習）
quality-cycle:
	@echo "🔄 完全品質改善サイクル実行"
	$(MAKE) auto-improve
	python scripts/quality/continuous_learner.py
	@echo "✅ 品質改善サイクル完了"

# 回帰チェックのみ
regression-check:
	python scripts/quality/regression_detector.py detect

# 学習レポート表示
learning-report:
	python scripts/quality/continuous_learner.py

# === Phase 1: Dashboard & Monitoring ===
dashboard: ## 🎯 学習効果ダッシュボード表示
	@echo "🎯 Learning Insights Dashboard Starting..."
	@python scripts/dashboard/learning_insights.py

health: ## 💚 システム健康度チェック
	@echo "💚 System Health Check Starting..."
	@python scripts/quality/health_monitor.py

insights: dashboard health ## 🚀 総合分析（ダッシュボード + 健康度）
	@echo ""
	@echo "🚀 Complete System Analysis Completed!"
	@echo "📄 詳細レポート: out/learning_insights.json, out/system_health.json"

quick-check: ## ⚡ クイックシステム確認（要点のみ）
	@echo "⚡ Quick System Status Check"
	@python scripts/quality/health_monitor.py | head -15
	@echo ""
	@python scripts/dashboard/learning_insights.py | tail -8
