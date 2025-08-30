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

# === Phase 2: Predictive & Preventive System ===
predict: ## 🔮 問題予測分析実行
	@echo "🔮 Issue Prediction Analysis Starting..."
	@python scripts/quality/issue_predictor.py

prevent: predict ## 🛡️ 予防的修正適用
	@echo "🛡️ Applying Preventive Fixes..."
	@python scripts/quality/preventive_fixer.py

predict-test: ## 🧪 予測システムテスト（7日間予測）
	@echo "🧪 Testing Prediction System (7-day horizon)"
	@python scripts/quality/issue_predictor.py
	@echo ""
	@echo "📊 Prediction Results:"
	@test -f out/issue_predictions.json && jq '.risk_assessment' out/issue_predictions.json || echo "No predictions generated"

future-safe: predict prevent ## 🚀 完全予防実行（予測→修正→検証）
	@echo ""
	@echo "🚀 Complete Preventive Cycle Executed!"
	@echo "📊 Summary:"
	@test -f out/issue_predictions.json && echo "  Predictions: Generated" || echo "  Predictions: Failed"
	@test -f out/preventive_fixes.json && echo "  Preventive Fixes: Applied" || echo "  Preventive Fixes: No fixes needed"
	@echo "📄 Reports: out/issue_predictions.json, out/preventive_fixes.json"

phase2-status: ## 📊 Phase 2システム状態確認
	@echo "📊 Phase 2: Predictive & Preventive System Status"
	@echo "============================================="
	@echo ""
	@echo "🔮 Prediction Engine:"
	@test -f scripts/quality/issue_predictor.py && echo "  ✅ Active" || echo "  ❌ Missing"
	@echo ""
	@echo "🛡️ Preventive Fixer:"
	@test -f scripts/quality/preventive_fixer.py && echo "  ✅ Active" || echo "  ❌ Missing" 
	@echo ""
	@echo "⚡ GitHub Actions Integration:"
	@test -f .github/workflows/predictive-quality.yml && echo "  ✅ Configured" || echo "  ❌ Missing"
	@echo ""
	@echo "📄 Recent Predictions:"
	@test -f out/issue_predictions.json && echo "  ✅ Available ($(stat -f%Sm -t%Y-%m-%d out/issue_predictions.json 2>/dev/null || echo 'unknown date'))" || echo "  ℹ️ Run 'make predict' to generate"

# === Phase 3: Realtime Quality Guard System ===
realtime-monitor: ## 📊 リアルタイム品質監視開始
	@echo "📊 Starting Realtime Quality Monitor..."
	@echo "⚠️ Press Ctrl+C to stop monitoring"
	@python scripts/quality/realtime_monitor.py

realtime-test: ## 🧪 リアルタイム監視テスト実行
	@echo "🧪 Realtime Monitor Test Mode"
	@python scripts/quality/realtime_monitor.py --test

auto-guard: ## 🛡️ 自動品質ガード実行
	@echo "🛡️ Auto Guard System Starting..."
	@python scripts/quality/auto_guard.py --test

instant-feedback: ## ⚡ 即座フィードバックシステムテスト
	@echo "⚡ Instant Feedback System Test"
	@python scripts/quality/instant_feedback.py --test

feedback-summary: ## 📊 フィードバック統計表示
	@echo "📊 Feedback Statistics Summary"
	@python scripts/quality/instant_feedback.py --summary

dynamic-gates: ## 🎛️ 動的品質ゲートテスト
	@echo "🎛️ Dynamic Quality Gates Test"
	@python scripts/quality/dynamic_gates.py --test

gates-summary: ## 📋 品質ゲート状態確認
	@echo "📋 Quality Gates Summary"
	@python scripts/quality/dynamic_gates.py --summary

# Phase 3 統合コマンド
phase3-full: realtime-test auto-guard instant-feedback dynamic-gates ## 🚀 Phase 3 全システムテスト
	@echo ""
	@echo "🚀 Phase 3: Realtime Quality Guard - All Systems Test Completed!"
	@echo "============================================================="
	@echo "✅ Realtime Monitor: Active"
	@echo "✅ Auto Guard: Active"  
	@echo "✅ Instant Feedback: Active"
	@echo "✅ Dynamic Gates: Active"
	@echo ""
	@echo "📄 Reports generated in out/ directory"
	@echo "🔧 Use 'make realtime-monitor' to start live monitoring"

phase3-status: ## 📊 Phase 3システム状態確認
	@echo "📊 Phase 3: Realtime Quality Guard System Status"
	@echo "================================================"
	@echo ""
	@echo "📊 Realtime Monitor:"
	@test -f scripts/quality/realtime_monitor.py && echo "  ✅ Active" || echo "  ❌ Missing"
	@echo ""
	@echo "🛡️ Auto Guard:"
	@test -f scripts/quality/auto_guard.py && echo "  ✅ Active" || echo "  ❌ Missing"
	@echo ""
	@echo "⚡ Instant Feedback:"
	@test -f scripts/quality/instant_feedback.py && echo "  ✅ Active" || echo "  ❌ Missing"
	@echo ""
	@echo "🎛️ Dynamic Gates:"
	@test -f scripts/quality/dynamic_gates.py && echo "  ✅ Active" || echo "  ❌ Missing"
	@echo ""
	@echo "⚡ GitHub Actions Integration:"
	@test -f .github/workflows/realtime-quality-guard.yml && echo "  ✅ Configured" || echo "  ❌ Missing"
	@echo ""
	@echo "📄 Quality Data:"
	@test -f out/realtime_quality.json && echo "  ✅ Monitor Data Available" || echo "  ℹ️ Run 'make realtime-test' to generate"
	@test -f out/feedback_history.json && echo "  ✅ Feedback History Available" || echo "  ℹ️ Run 'make instant-feedback' to generate"
	@test -f out/gate_learning.json && echo "  ✅ Gate Learning Data Available" || echo "  ℹ️ Run 'make dynamic-gates' to generate"

# 究極統合コマンド - 全フェーズ実行
ultimate-system: insights future-safe phase3-full ## 🌟 究極システム - Phase 1+2+3 統合実行
	@echo ""
	@echo "🌟 ULTIMATE AI-DRIVEN SYSTEM EXECUTION COMPLETE!"
	@echo "=================================================="
	@echo ""
	@echo "🎯 Phase 1: 可視化・監視 ✅"
	@echo "🔮 Phase 2: 予測・予防 ✅"  
	@echo "🚀 Phase 3: リアルタイム品質ガード ✅"
	@echo ""
	@echo "📊 System Capabilities:"
	@echo "  • Real-time quality monitoring"
	@echo "  • Predictive issue analysis"
	@echo "  • Automatic quality protection"
	@echo "  • Instant developer feedback"
	@echo "  • Dynamic adaptive thresholds"
	@echo "  • Continuous learning & improvement"
	@echo ""
	@echo "🎊 The most advanced AI-driven quality system is now active!"
