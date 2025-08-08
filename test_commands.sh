#!/bin/bash
# Voice Roleplay System - 推奨テストコマンド集

# 環境の準備
source venv/bin/activate

# 基本コマンド
alias test-quick="python -m pytest tests/ -q"
alias test-voice="python -m pytest tests/api/test_voice.py -v"
alias test-ai="python -m pytest tests/test_language_analysis.py -v"
alias test-health="python -m pytest tests/api/test_health.py -v"
alias test-fail-fast="python -m pytest tests/ -x --tb=short"
alias test-coverage="python -m pytest tests/ --cov=app --cov-report=term-missing"
alias test-performance="python -m pytest tests/ --durations=5"

echo "🎯 Voice Roleplay System テストコマンド"
echo "=================================="
echo "test-quick      : 高速全体チェック"
echo "test-voice      : 音声機能テスト"
echo "test-ai         : AI・言語分析テスト"
echo "test-health     : ヘルスチェック"
echo "test-fail-fast  : 問題発見モード"
echo "test-coverage   : カバレッジ確認"
echo "test-performance: パフォーマンス確認"
echo "==================================" 