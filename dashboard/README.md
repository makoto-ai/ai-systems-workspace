# Golden Test KPI Dashboard

## 概要
Golden Testの結果を可視化するStreamlitベースのダッシュボード。

## 表示指標

### 1. 週次合格率（ラインチャート）
- 時系列での合格率推移
- 目標ライン（90%）と警告ライン（80%）
- トレンド分析

### 2. 失敗理由分析（棒グラフ）
- 不足キーワードの頻度分析
- 上位10位までの表示
- 辞書チューニングの優先度判定

### 3. モデル効率性（表形式）
- 合格1件あたりの推定試行回数
- 日別・モデル別の効率性比較
- パフォーマンス監視

## 起動方法

### 依存関係インストール
```bash
pip install -r dashboard/requirements.txt
```

### ダッシュボード起動
```bash
cd /Users/araimakoto/ai-driven/ai-systems-workspace
streamlit run dashboard/golden_kpi.py
```

### アクセス
ブラウザで `http://localhost:8501` にアクセス

## データソース

### Golden Test ログ
- `tests/golden/logs/*.jsonl`: 詳細実行ログ
- `tests/golden/observation_log.md`: 週次観測データ

### 更新頻度
- リアルタイム: ページリロード時に最新データを読み込み
- 自動更新: 週次Golden Testの実行により更新

## カスタマイズ

### 新しい指標の追加
`dashboard/golden_kpi.py` を編集して新しい分析ロジックを追加

### 表示期間の変更
サイドバーの期間選択フィルターを使用

### エクスポート
Streamlitの標準機能でグラフをPNG/SVGでダウンロード可能

## 本格運用時の拡張

### Superset連携
- PostgreSQL/MySQLにログデータを蓄積
- Supersetで高度なダッシュボード構築
- アラート機能の追加

### 自動レポート
- 週次/月次レポートの自動生成
- Slack/Email通知
- 品質トレンドの自動分析
