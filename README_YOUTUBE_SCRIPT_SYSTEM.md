# YouTube Script Generation System

## 概要

研究論文からYouTube原稿を自動生成する高度なAIシステムです。Groq APIを活用し、高速で高品質なYouTube原稿を生成します。

## 🚀 主な機能

### 1. 多様なスタイル対応
- **Popular**: 一般視聴者向け（15分）
- **Academic**: 研究者・学生向け（20分）
- **Business**: ビジネスパーソン向け（18分）
- **Educational**: 学習者向け（30分）

### 2. 品質保証システム
- **引用検証**: 科学的根拠の確認
- **安全性チェック**: 有害コンテンツの検出
- **品質メトリクス**: 可読性、エンゲージメント、構造スコアの自動計算

### 3. 高速処理
- Groq APIによる高速レスポンス
- 自動リトライ機能
- 詳細なログ出力

## 📁 システム構成

```
youtube_script_generation_system.py  # メインシステム
config/
  └── youtube_script_config.json     # 設定ファイル
test_youtube_script_system.py        # テストファイル
logs/                                # ログディレクトリ
```

## 🛠️ セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 設定ファイルの準備

`config/youtube_script_config.json` が自動的に作成されます。

### 3. 環境変数の設定

```bash
export GROQ_API_KEY="your_groq_api_key"
```

## 🎯 使用方法

### 基本的な使用例

```python
import asyncio
from youtube_script_generation_system import YouTubeScriptGenerator, ResearchMetadata

async def main():
    # 研究データの準備
    research_data = ResearchMetadata(
        title="AIによる営業パフォーマンス向上の研究",
        authors=["田中太郎", "佐藤花子"],
        abstract="本研究では、AI技術を活用した営業手法の効果を検証しました。",
        publication_year=2024,
        journal="Journal of Sales Technology",
        doi="10.1234/jst.2024.001",
        citation_count=15,
        keywords=["AI", "営業", "パフォーマンス"],
        institutions=["東京大学"]
    )
    
    # YouTube原稿生成
    generator = YouTubeScriptGenerator()
    script = await generator.generate_script(research_data, style="popular")
    
    # 結果の確認
    print(f"タイトル: {script.title}")
    print(f"信頼度スコア: {script.confidence_score:.2f}")
    print(f"動画時間: {script.total_duration}秒")

# 実行
asyncio.run(main())
```

### コマンドライン実行

```bash
python youtube_script_generation_system.py
```

## 📊 出力形式

### YouTubeScript オブジェクト

```python
@dataclass
class YouTubeScript:
    title: str                    # 動画タイトル
    hook: str                     # 導入部分
    introduction: str             # 導入
    main_content: str            # メインコンテンツ
    conclusion: str              # 結論
    call_to_action: str          # アクション呼びかけ
    total_duration: int          # 動画時間（秒）
    sources: List[Dict[str, str]] # 参考文献
    confidence_score: float      # 信頼度スコア
    safety_flags: List[Dict[str, str]] # 安全性フラグ
    processing_time: float       # 処理時間
    quality_metrics: Dict[str, float] # 品質メトリクス
```

## 🔧 設定カスタマイズ

### スタイル設定の変更

`config/youtube_script_config.json` で各スタイルの設定を変更できます：

```json
{
  "styles": {
    "popular": {
      "duration": 900,
      "tone": "親しみやすく、分かりやすい",
      "target_audience": "一般視聴者"
    }
  }
}
```

### 品質閾値の調整

```json
{
  "quality_thresholds": {
    "readability_score": 0.7,
    "engagement_score": 0.6,
    "structure_score": 0.8,
    "confidence_score": 0.7
  }
}
```

## 🧪 テスト

### テストの実行

```bash
python test_youtube_script_system.py
```

### テスト内容

- 設定管理クラスのテスト
- 品質メトリクスのテスト
- エラーハンドラーのテスト
- 原稿生成の基本テスト
- 異なるスタイルでのテスト
- 統合テスト

## 📈 品質メトリクス

### 1. 可読性スコア
- 文章の複雑さを評価
- 0.0（非常に複雑）〜 1.0（非常に読みやすい）

### 2. エンゲージメントスコア
- 視聴者の興味を引く要素を評価
- 質問、具体例、ストーリー要素を考慮

### 3. 構造スコア
- 原稿の構成の適切性を評価
- フック、導入、本文、結論のバランス

## 🔒 安全性機能

### 自動検出項目
- 医療関連コンテンツ
- 金融関連コンテンツ
- 心理関連コンテンツ

### 自動修正機能
- 安全性問題の自動修正
- 適切な免責事項の追加

## 📝 ログ機能

### ログファイル
- 場所: `logs/youtube_script_generation_YYYYMMDD_HHMMSS.log`
- 詳細な処理ログ
- エラー情報の記録

### ログレベル
- INFO: 通常の処理情報
- WARNING: 警告情報
- ERROR: エラー情報

## 🚨 トラブルシューティング

### よくある問題

1. **Groq APIキーエラー**
   ```
   解決方法: GROQ_API_KEY環境変数の設定を確認
   ```

2. **設定ファイルエラー**
   ```
   解決方法: config/youtube_script_config.json の形式を確認
   ```

3. **メモリ不足**
   ```
   解決方法: 大きな研究データは分割して処理
   ```

## 🔄 更新履歴

### v2.0.0 (2024-01-XX)
- MCP統合の実装
- 設定ファイルの外部化
- ログ機能の強化
- テスト機能の追加

### v1.0.0 (2024-01-XX)
- 基本的な原稿生成機能
- 品質評価システム
- 安全性チェック機能

## 📞 サポート

問題が発生した場合は、以下を確認してください：

1. ログファイルの確認
2. 設定ファイルの確認
3. 環境変数の設定確認
4. 依存関係のインストール確認

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。 