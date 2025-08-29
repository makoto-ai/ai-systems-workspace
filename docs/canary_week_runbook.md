# 🐤 Canary Week 運用手順書

## 概要
Golden Test Phase 3（しきい値0.7）のカナリア週運用手順とロールバック対応

## カナリア週の定義
- **期間**: しきい値昇格後の最初の1週間
- **監視強化**: 通常80%基準 → 85%基準に厳格化
- **即時対応**: 基準未達で24時間以内の対応

## 監視基準

### 🟢 正常（継続）
```
合格率 >= 85% AND
flaky_rate < 5% AND  
new_fail_ratio <= 60%
```

### 🟡 注意（監視強化）
```
合格率 80-84% OR
flaky_rate 3-4.9% OR
new_fail_ratio 50-60%
```

### 🔴 緊急（ロールバック検討）
```
合格率 < 80% OR
flaky_rate >= 5% OR
new_fail_ratio > 60% OR
連続失敗 >= 2回
```

## 手動実行コマンド

### カナリア週開始
```bash
gh workflow run weekly-golden.yml --field canary=true
```

### 緊急ロールバック
```bash
scripts/rollback_threshold.sh --from 0.7 --to 0.5
```

### 実験レーン（MODEL改善）
```bash
python experiments/model_swap.py --cases MODEL --out out/model_exp.json --models groq
python experiments/prompt_optimization.py
```

### 影響測定
```bash
python tests/golden/runner.py --threshold-shadow 0.7 --report out/shadow_0_7.json
python tests/golden/root_cause_analyzer.py --update-freshness
```

## 通知設定

### Slack通知例
```json
{
  "text": "🐤 Canary Week Alert",
  "blocks": [
    {
      "type": "section", 
      "fields": [
        {"type": "mrkdwn", "text": "*合格率:* 82% < 85%"},
        {"type": "mrkdwn", "text": "*状態:* 🟡 注意"}
      ]
    }
  ]
}
```

### 必要なSecrets
- `SLACK_WEBHOOK_URL`: Slack通知用
- `DISCORD_WEBHOOK_URL`: Discord通知用

## ロールバック手順

### 1. 自動検知
- GitHub Actions週次チェックで基準未達検出
- 自動Issue起票・関係者通知

### 2. 緊急判断
```bash
# 現在の状況確認
python tests/golden/runner.py --threshold-shadow 0.7 --report out/current_status.json

# ダッシュボード確認
open http://localhost:8501
```

### 3. ロールバック実行
```bash
# 即時ロールバック
scripts/rollback_threshold.sh --from 0.7 --to 0.5

# 検証実行
python tests/golden/run_golden.py
```

### 4. 事後対応
- Issue更新（原因・影響・対策）
- 改善計画策定
- 再昇格条件の明確化

## 本採用移行条件

### 1週間連続で以下を満たす
```
✅ 合格率 >= 85%
✅ flaky_rate < 5%  
✅ new_fail_ratio <= 60%
✅ 重大インシデント 0件
✅ ロールバック実行 0回
```

### 本採用手順
1. カナリアフラグ無効化: `canary: false`
2. PR本採用マージ
3. 通常運用移行
4. 昇格履歴記録

## トラブルシューティング

### Q: 合格率が急落した
```bash
# Root Cause分析
python tests/golden/root_cause_analyzer.py --export-new-fails out/emergency_fails.json

# 失敗パターン確認
python tests/golden/tools/suggest_norm_rules.py --in out/emergency_fails.json --out out/emergency_rules.yaml
```

### Q: MODEL起因失敗が増加
```bash
# プロンプト実験
python experiments/prompt_optimization.py

# モデル比較実験
python experiments/model_swap.py --cases MODEL --models groq openai --out out/model_comparison.json
```

### Q: 新規失敗率が上昇
```bash
# 履歴分析
python tests/golden/root_cause_analyzer.py --update-freshness

# 正規化ルール強化
# tests/golden/evaluator.py の _NORM_MAP 更新
```

## 関連リンク
- [Golden KPI Dashboard](http://localhost:8501)
- [GitHub Actions](https://github.com/makoto-ai/ai-systems-workspace/actions)
- [Canary PR #29](https://github.com/makoto-ai/ai-systems-workspace/pull/29)

## 更新履歴
- 2025-08-29: Phase 3カナリア週運用開始
- プロンプト最適化実装（複合語保持）
- 二重ゲート通過（new_fail_ratio 50%達成）
