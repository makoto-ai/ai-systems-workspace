## 分離アーキテクチャ + 共通イベントレイヤ

### 目的
- 機能を独立サービスとして分離し、疎結合で進化可能にする
- 統合は **append-only の共通イベントレイヤ** で実現

### サービス分割
- 音声I/O: ASR/TTS, 録音/再生UI
- 会話ロジック: プロンプト/履歴
- 採点・評価: NG語/沈黙/反論成功率
- シナリオ・シミュレーション: 分岐探索
- ダッシュボード: 可視化/レポート（他DBへ直参照しない）

### 共通イベントレイヤ
- `events` テーブル（Postgres, append-only）
  - JSON形式: `{type, tenant, session, ts, payload}`
  - 各サービスは結果を events に書き込む
  - ダッシュボード/バッチは events から集計
  - 改ざん不可の監査台帳として利用

### 集計と分析
- 夜間Cron/Temporalでマテビュー更新（KPI: 合格率/反論成功率/沈黙率/学習曲線）
- `mv_kpi_overview` を参照

### DB/セキュリティ
- Postgres + RLS (Row Level Security) でテナント分離
- 基本スキーマ: `users, sessions, turns, scores, scenarios, sim_runs, events`

### 拡張性
- イベント量増 → Kafka/NATS/SQSへ置換可能なイベント抽象
- LLM抽象: 通常 GPT-5 / 長文 Claude Sonnet 4 / 難所 Opus 4.1 を切替可能

### API雛形
- `/api/ingest/turn` 取り込み
- `/api/score` 採点記録
- `/api/sim/run` シミュレーション実行
- `/api/metrics/overview` KPI概要

### バッチ
- `scripts/nightly_aggregate.py` で夜間集計（雛形）。実装時は `REFRESH MATERIALIZED VIEW CONCURRENTLY` を使用

### Frontend雛形
- Next.js ダッシュボードで events 由来のKPI可視化（NG率 / 反論成功率ヒートマップ など）


