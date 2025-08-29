# Golden Test Framework

## 概要
AIモデル出力の品質を継続的に監視・改善するためのゴールデンテストフレームワーク。

## 運用フロー

### 週次観測サイクル
```bash
# 週次チェック実行（毎週金曜日推奨）
./scripts/weekly_golden_check.sh
```

### 段階的品質向上
1. **Phase 1: データ蓄積期** (現在)
   - しきい値: 0.3 固定
   - 目標: 辞書チューニングで合格率90%以上
   - 期間: 2-3週間

2. **Phase 2: 精度向上期**
   - しきい値: 0.3 → 0.5 引き上げ
   - 目標: 合格率80%以上維持
   - 期間: 1-2週間

3. **Phase 3: 本格運用期**
   - しきい値: 0.5 → 0.7 引き上げ
   - 目標: 合格率70%以上で安定運用

## ファイル構成

```
tests/golden/
├── README.md              # このファイル
├── run_golden.py          # テスト実行スクリプト
├── evaluator.py           # 評価ロジック（正規化辞書含む）
├── observation_log.md     # 観測ログ
├── cases/                 # テストケース
│   ├── sample_001.json
│   ├── sample_002.json
│   └── ...
└── logs/                  # 実行ログ（JSONL形式）
    ├── 20250829_210950.jsonl
    └── ...
```

## 手動実行

### 基本実行
```bash
cd /Users/araimakoto/ai-driven/ai-systems-workspace
PYTHONPATH=/Users/araimakoto/ai-driven/ai-systems-workspace python3 tests/golden/run_golden.py
```

### しきい値指定
```bash
python3 tests/golden/run_golden.py --threshold 0.5
```

## 辞書チューニング

不合格ケースが発生した場合は `tests/golden/evaluator.py` の `_NORM_MAP` を更新：

```python
_NORM_MAP = {
    # 新しい正規化ルール追加
    "新しい語": "正規化後の語",
    # ...
}
```

## ログ分析

実行ログは `tests/golden/logs/` に JSONL 形式で保存：
- `id`: テストケースID
- `score`: 評価スコア (0.0-1.0)
- `passed`: 合格判定
- `reference`: 期待値
- `prediction`: モデル出力
- `threshold`: 使用したしきい値

## 自動化

週次チェックスクリプト (`scripts/weekly_golden_check.sh`) により：
- 自動実行・結果判定
- 観測ログ更新
- 改善アクション提案
- しきい値引き上げタイミング通知

## 運用ルール

### 合格率に応じた対応

#### 90%以上 ✅
- **状態**: 良好
- **アクション**: 現状維持
- **条件**: 連続週数達成で `scripts/bump_threshold_enhanced.sh` によるしきい値引き上げ
- **二重ゲート**: Phase 3では flaky_rate < 5%, new_fail_ratio ≤ 60% も必要

#### 80-89% ⚠️
- **状態**: 要改善
- **アクション**: 辞書追加のみ
- **対象**: `tests/golden/evaluator.py` の `_NORM_MAP` を更新
- **方針**: 不合格ケースの正規化ルール追加

#### 80%未満 🔥
- **状態**: 緊急対応
- **アクション**: system強化またはモデル切替
- **カナリア週**: 85%未満で自動ロールバック検討

### 昇格ゲート条件（数式）

#### Phase 1 → Phase 2 (0.3 → 0.5)
```
consecutive_weeks >= 3 AND
avg(pass_rate[-3:]) >= 90%
```

#### Phase 2 → Phase 3 (0.5 → 0.7) 【二重ゲート】
```
consecutive_weeks >= 2 AND
avg(pass_rate[-2:]) >= 90% AND
flaky_rate < 0.05 AND
new_fail_ratio <= 0.60
```

#### Phase 3 → Phase 4 (0.7 → 0.85)
```
consecutive_weeks >= 2 AND
avg(pass_rate[-2:]) >= 85% AND
new_failure_resolution_rate >= 0.70
```

#### Phase 4 → Phase 5 (0.85 → 0.9)
```
consecutive_weeks >= 3 AND
avg(pass_rate[-3:]) >= 90%
```

### カナリア運用（通知・ロールバック条件と手順）

#### カナリア週の定義
- **期間**: しきい値昇格後の最初の1週間
- **監視強化**: 通常の80%基準から85%基準に厳格化
- **即時対応**: 基準未満で24時間以内の対応

#### 通知強化
- **Slack/Discord**: 即時通知（合格率・flaky_rate・new_fail_ratio・root_cause Top3）
- **GitHub Issue**: 緊急Issue自動起票
- **ダッシュボード**: リアルタイム監視

#### ロールバック条件
```
canary_week = true AND
(pass_rate < 85% OR consecutive_failures >= 2)
```

#### ロールバック手順
1. **自動検知**: GitHub Actions週次チェック
2. **緊急Issue**: 自動起票・関係者通知
3. **ロールバック実行**: `scripts/rollback_threshold.sh`
4. **検証**: 前段階しきい値での再テスト
5. **報告**: 結果をIssueに更新

### 実験レーンの使い方

#### 起動コマンド
```bash
# MODEL起因失敗の実験
python experiments/model_swap.py --cases MODEL --out out/model_exp.json

# 複数モデル比較
python experiments/model_swap.py --cases MODEL --models groq openai --out out/model_comparison.json

# 特定Root Cause対象
python experiments/model_swap.py --cases TOKENIZE --out out/tokenize_exp.json
```

#### 評価指標
- **Pass@1**: 1回目で合格する確率
- **平均スコア**: 全ケースの平均評価スコア
- **実行時間**: API応答時間の合計
- **APIコスト見積**: 概算コスト（USD）

#### GitHub Actions手動実行
```yaml
# .github/workflows/model-experiment.yml で手動起動
workflow_dispatch:
  inputs:
    run_experiment:
      type: boolean
      default: false
```

### ダッシュボード指標一覧

#### メトリクスカード
- **pass_rate**: 現在の合格率（%）
- **flaky_rate**: Flaky失敗率（%）
- **new_fail_ratio**: 新規失敗率（%）
- **Predicted@0.7**: シャドー評価での0.7しきい値予測合格率（%）

#### チャート
- **週次合格率トレンド**: 時系列ラインチャート（目標・警告ライン付き）
- **新規失敗率トレンド**: 赤色ラインチャート
- **Root Cause Top3**: 失敗理由上位3つの分布
- **不足キーワード上位10**: 棒グラフ

#### 実験結果
- **モデル比較**: Pass@1・平均スコア・実行時間・コスト
- **Shadow Evaluation**: 次段階しきい値での予測結果

### 自動昇格/降格プロセス

#### 🎯 最終目標: しきい値0.9（完成度0.9）

#### 階層別昇格ルール

##### 0.3 → 0.5（基本安定性確認）
- **条件**: 3週連続で合格率90%以上
- **目的**: データ蓄積期から精度向上期への移行

##### 0.5 → 0.7（辞書完成度確認）
- **条件**: 2週連続で合格率90%以上 + 不合格原因が辞書/正規化で説明可能
- **目的**: 正規化ルールの成熟度確認

##### 0.7 → 0.85（高精度期移行）
- **条件**: 2週連続で合格率85%以上 + 新規不合格の70%以上を次週までに解決可能
- **目的**: 継続的改善能力の確認

##### 0.85 → 0.9（完成ライン到達）
- **条件**: 3週連続で合格率90%以上
- **目的**: 実質完成品質の達成

#### 降格ルール
- **条件**: 2週連続でしきい値の80%を下回る合格率
- **動作**: 一段階前のしきい値に自動降格
- **目的**: 品質劣化の早期検知・回復

#### 実行
```bash
./scripts/bump_threshold_if_stable.sh
```

#### 結果
- 設定ファイル (`tests/golden/config.yml`) の更新
- 自動ブランチ作成・PR作成
- 観測ログへの記録

#### 昇格週の運用ルール
- **辞書追加凍結**: 昇格判定週は辞書チューニングを行わない
- **純粋観測**: モデル+後処理の実力のみを評価
- **客観判定**: 人為的な調整を排除した品質測定

### CI/CD統合

#### 週次自動チェック
- **スケジュール**: 毎週金曜日 09:00 JST
- **ワークフロー**: `.github/workflows/weekly-golden.yml`
- **失敗時**: GitHub Issue自動起票

#### 品質ゲート
- 合格率80%未満でCI失敗
- ログのArtifacts保存
- 緊急対応の自動通知

## KPI可視化

### Streamlitダッシュボード
```bash
streamlit run dashboard/golden_kpi.py
```

#### 表示指標
1. **週次合格率**: ラインチャート（目標・警告ライン付き）
2. **失敗理由**: 不足キーワード上位10（棒グラフ）
3. **モデル効率性**: 合格1件あたり試行回数（表形式）

#### データソース
- `tests/golden/logs/*.jsonl`: 詳細実行ログ
- `tests/golden/observation_log.md`: 週次観測データ

### 本格運用時の拡張
- **Superset**: PostgreSQL/MySQL連携
- **アラート**: Slack/Email通知
- **自動レポート**: 週次/月次品質レポート