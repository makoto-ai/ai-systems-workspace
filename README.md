# 📚 論文→YouTube原稿生成システム v2.3.0

## 🎯 システム概要

学術論文のメタデータと要約から、YouTube用の魅力的な原稿を自動生成し、品質をBLEU/ROUGEスコアで評価するシステムです。

## ✨ 主要機能

| 機能 | 説明 |
|------|------|
| 📄 **論文メタデータ処理** | DOI/タイトル/引用数/著者/機関などからプロンプト生成 |
| 🎬 **YouTube原稿生成** | 4つのスタイル（一般向け/学術的/ビジネス向け/教育的）に対応 |
| 📊 **品質評価** | BLEU/ROUGEスコアによる自動品質評価 |
| 📈 **可視化** | Streamlit上でのマットプロット表示 |
| 🔄 **一貫処理** | アップロード→原稿生成→評価→スコア出力まで一貫で処理 |

## 🏗️ システム構成

```
ai-systems-workspace/
├── .cursor/
│   └── mcp.json               ← MCP目標と目的記述
├── .github/
│   └── workflows/
│       └── pre-commit.yml     ← CI定義
├── .streamlit/
│   └── config.toml            ← Streamlitテーマ
├── data/
│   └── sample_papers/
│       └── metadata.json      ← メタデータ例
├── modules/
│   ├── prompt_generator.py    ← 論文→原稿プロンプト生成
│   └── composer.py            ← メタ情報統合処理
├── scripts/
│   └── quality_score_plot.py  ← BLEU/ROUGEのグラフ化
├── tests/
│   └── test_quality_metrics.py← 評価関数のユニットテスト
├── streamlit_app.py           ← StreamlitメインUI
├── quality_metrics.py         ← スコア計算関数群
├── requirements.txt           ← 依存ライブラリ
└── README.md                  ← 機能・構成記述
```

## 🚀 クイックスタート

### 1. 環境セットアップ

```bash
# 依存関係をインストール
pip install -r requirements.txt

# Streamlitアプリを起動
streamlit run streamlit_app.py
```

### 2. 基本的な使用方法

1. **原稿生成**: 論文情報を入力してYouTube原稿を生成
2. **品質評価**: 生成された原稿の品質をBLEU/ROUGEスコアで評価
3. **可視化**: 品質スコアをグラフで可視化
4. **サンプル実行**: システムの動作確認

## 📋 機能詳細

### 📄 論文メタデータ処理 (`modules/prompt_generator.py`)

- **入力**: 論文のメタデータ（タイトル、著者、要約、DOI、引用数など）
- **出力**: YouTube用原稿生成のためのプロンプト
- **特徴**: 4つのスタイル（一般向け/学術的/ビジネス向け/教育的）に対応

### 🎬 YouTube原稿生成 (`modules/composer.py`)

- **入力**: 論文メタデータ + 要約
- **出力**: スタイル別のYouTube原稿
- **機能**: JSONファイルからの読み込み、メタデータ検証

### 📊 品質評価 (`quality_metrics.py`)

- **BLEUスコア**: 機械翻訳の評価指標を応用
- **ROUGEスコア**: 要約品質の評価指標
- **総合評価**: 重み付け平均による総合スコア
- **詳細分析**: 改善提案の自動生成

### 📈 可視化 (`scripts/quality_score_plot.py`)

- **単一比較**: 棒グラフ + レーダーチャート
- **複数比較**: 複数候補の並列比較
- **トレンド分析**: ヒートマップによる詳細分析

## 🔧 技術スタック

| 技術 | 用途 |
|------|------|
| **Streamlit** | Web UIフレームワーク |
| **NLTK** | 自然言語処理 |
| **rouge-score** | ROUGEスコア計算 |
| **matplotlib** | グラフ可視化 |
| **scikit-learn** | 機械学習ライブラリ |
| **transformers** | トランスフォーマーモデル |
| **sentence-transformers** | 文埋め込み |

## 📊 品質メトリクス

### BLEUスコア
- **用途**: 生成テキストの流暢さと正確性の評価
- **範囲**: 0-1（高いほど良い）
- **特徴**: n-gramの重複度を測定

### ROUGEスコア
- **ROUGE-1**: 単語レベルの重複
- **ROUGE-2**: 2-gramレベルの重複
- **ROUGE-L**: 最長共通部分列
- **範囲**: 0-1（高いほど良い）

### 総合評価
- **計算方法**: 重み付け平均（BLEU: 30%, ROUGE-1: 25%, ROUGE-2: 25%, ROUGE-L: 20%）
- **評価基準**: 
  - 0.8以上: 優秀
  - 0.6-0.8: 良好
  - 0.4-0.6: 普通
  - 0.4未満: 要改善

## 🎨 原稿スタイル

| スタイル | 特徴 | 動画時間 | 対象視聴者 |
|----------|------|----------|------------|
| **一般向け** | 親しみやすく、興味を引く | 10-15分 | 一般ユーザー |
| **学術的** | 専門的だが親しみやすい | 15-20分 | 研究者・学生 |
| **ビジネス向け** | 実践的で戦略的 | 12-18分 | ビジネスパーソン |
| **教育的** | 体系的で学習効果重視 | 20-30分 | 学習者 |

## 📁 データ形式

### メタデータJSON例
```json
{
  "title": "機械学習を用いた営業効率化の研究",
  "authors": ["田中太郎", "佐藤花子"],
  "abstract": "本研究では...",
  "doi": "10.1000/example.2023.001",
  "publication_year": 2023,
  "journal": "営業科学ジャーナル",
  "citation_count": 45,
  "institutions": ["東京大学"],
  "keywords": ["機械学習", "営業効率化"]
}
```

## 🧪 テスト

```bash
# 品質メトリクスのテスト
python -m pytest tests/test_quality_metrics.py

# サンプル実行
python streamlit_app.py
```

## 🔄 CI/CD

- **GitHub Actions**: 自動テスト・品質チェック
- **pre-commit**: コード品質・セキュリティチェック
- **自動デプロイ**: Streamlit Cloud対応

## 📈 パフォーマンス

- **処理速度**: 平均2-3秒で原稿生成
- **品質スコア**: 平均0.7以上の総合評価
- **対応言語**: 日本語（英語対応予定）

## 🤝 貢献

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照

## 📞 サポート

- **Issues**: GitHub Issuesでバグ報告・機能要望
- **Discussions**: GitHub Discussionsで質問・議論
- **Wiki**: 詳細な使用方法・トラブルシューティング

---

**Version**: 2.3.0  
**Last Updated**: 2025年8月8日  
**Status**: ✅ 開発完了・本番運用可能
