# 🧠 研究→YouTube原稿生成システム v3.0
## MCP統合版 - 最大限の事実正確性とアルゴリズム性能

### 📋 システム概要

このシステムは、学術研究からYouTube原稿を生成する際に、4つの主要MCP（Model Context Protocol）構造を統合して、最大限の事実正確性とアルゴリズム性能を実現します。

### 🏗️ 実装されたMCP構造

#### 1. **Anthropic's Constitutional AI** (`.cursor/mcp_claude_constitution.json`)
- **目的**: 事実の正確性と倫理的AI生成の保証
- **機能**:
  - 情報の捏造禁止
  - 科学的主張へのDOI引用必須
  - 感情的操作禁止
  - 誇張表現の回避
  - 医療・金融・心理アドバイスの適切な免責事項

#### 2. **OpenAI/Cursor Rule System** (`.cursor/project-rules.json`)
- **目的**: モデルルーティングと出力形式の統一制御
- **機能**:
  - Claude（長文構造）vs GPT（精密要約）の自動選択
  - Markdown、JSON、YouTube形式の統一制御
  - タスク別プロンプトテンプレートの最適化

#### 3. **Google DeepMind's Sparrow Logic** (`.cursor/mcp_sparrow.json`)
- **目的**: 引用強制とソース検証
- **機能**:
  - 全段落への検証可能なソース必須
  - DOI、PMID、Google Scholar URLの検証
  - 複数ソース、最新性、権威性の品質チェック
  - 要約→組立→最終レビューの段階別適用

#### 4. **Microsoft Guardrails** (`.cursor/mcp_guardrails.json`)
- **目的**: 安全性とコンプライアンスレイヤー
- **機能**:
  - 危険フレーズの自動ブロック
  - 医療・心理・金融コンテンツの厳格なトーン制御
  - 違反ログの記録と追跡
  - 最終スクリプト生成とYouTube公開時の段階別適用

### 🚀 システム構成

```
ai-systems-workspace/
├── .cursor/
│   ├── mcp_claude_constitution.json    # Anthropic's Constitutional AI
│   ├── mcp_sparrow.json               # Google DeepMind's Sparrow Logic
│   ├── mcp_guardrails.json            # Microsoft Guardrails
│   ├── project-rules.json             # OpenAI/Cursor Rule System
│   └── prompts/
│       ├── claude_academic_summary.txt # Claude用プロンプト
│       └── gpt_precision_summary.txt  # GPT用プロンプト
├── youtube_script_generation_system.py # メインシステム
├── research_to_youtube_api.py         # FastAPIエンドポイント
├── test_mcp_integration.py           # 統合テスト
├── requirements_mcp.txt              # 依存関係
└── logs/
    └── guardrail_violations.json     # 安全性違反ログ
```

### 🔧 実装詳細

#### メインシステム (`youtube_script_generation_system.py`)

```python
class YouTubeScriptGenerator:
    def __init__(self):
        self.constitutional_ai = MCPConstitutionalAI()
        self.sparrow_logic = MCPSparrowLogic()
        self.guardrails = MCPGuardrails()
        self.model_router = ModelRouter()
    
    async def generate_script(self, research_data, style="popular"):
        # 1. 研究要約生成（Claude使用）
        # 2. 引用検証（Sparrow Logic）
        # 3. 安全性チェック（Guardrails）
        # 4. YouTube形式に変換
        # 5. 最終品質チェック
```

#### APIエンドポイント (`research_to_youtube_api.py`)

```python
@app.post("/generate-script")
async def generate_youtube_script(request: YouTubeScriptRequest):
    # MCP統合によるYouTube原稿生成
    # 信頼度スコアと安全性フラグ付き

@app.get("/mcp-status")
async def get_mcp_status():
    # MCP設定状況の確認

@app.post("/validate-citations")
async def validate_citations(content: str, sources: List[Dict]):
    # Sparrow Logicによる引用検証

@app.post("/check-safety")
async def check_content_safety(content: str):
    # Guardrailsによる安全性チェック
```

### 📊 モデルルーティングロジック

| タスクタイプ | 使用モデル | 出力形式 | 温度 | 用途 |
|-------------|-----------|----------|------|------|
| 長文生成 | Claude 3 Opus | Markdown | 0.7 | 学術研究要約 |
| 精密要約 | GPT-4o | JSON | 0.3 | 事実確認・翻訳 |
| 複雑な議論 | Claude 3 Opus | Markdown | 0.7 | 議論構造 |
| 教育的 | Claude 3 Opus | Markdown | 0.7 | 体系的な説明 |

### 🛡️ 安全性とコンプライアンス

#### 自動拒否項目
- 引用なしの主張
- 未検証の情報
- ブロックされたフレーズ（"100% guaranteed"等）

#### 警告フラグ
- 単一ソース主張
- 古い情報（5年以上）
- 非査読ソースの科学的主張

#### ログ記録
- 全ての違反とフラグの追跡
- タイムスタンプ付き詳細ログ
- 処理段階別の記録

### 🧪 テストと品質保証

#### 統合テスト (`test_mcp_integration.py`)
```bash
# 全テスト実行
pytest test_mcp_integration.py -v

# 特定テスト実行
pytest test_mcp_integration.py::TestMCPConstitutionalAI -v
```

#### テストカバレッジ
- MCPファイル存在確認
- JSON構造妥当性
- 憲法ルール適用
- 引用検証
- 安全性チェック
- モデルルーティング
- 完全ワークフロー

### 🚀 使用方法

#### 1. 環境セットアップ
```bash
# 依存関係インストール
pip install -r requirements_mcp.txt

# 環境変数設定
export ANTHROPIC_API_KEY="your_anthropic_key"
export OPENAI_API_KEY="your_openai_key"
```

#### 2. システム実行
```bash
# メインシステム実行
python youtube_script_generation_system.py

# APIサーバー起動
python research_to_youtube_api.py

# テスト実行
python test_mcp_integration.py
```

#### 3. API使用例
```python
import requests

# YouTube原稿生成
response = requests.post("http://localhost:8000/generate-script", json={
    "research_data": {
        "title": "AI営業パフォーマンス研究",
        "authors": ["田中太郎"],
        "abstract": "本研究では...",
        "publication_year": 2024,
        "journal": "Journal of Sales Technology",
        "doi": "10.1234/jst.2024.001"
    },
    "style": "popular"
})

print(response.json())
```

### 📈 性能指標

#### 信頼度スコア計算
```python
def _calculate_confidence_score(self, summary, citation_valid, safety_valid):
    score = 0.5  # ベーススコア
    
    if citation_valid:
        score += 0.3
    
    if safety_valid:
        score += 0.2
    
    if len(summary) > 1000:
        score += 0.1
    
    return min(score, 1.0)
```

#### 処理段階
1. **要約生成**: Claude 3 Opus（憲法ルール適用）
2. **引用検証**: Sparrow Logic（全段落チェック）
3. **安全性チェック**: Guardrails（危険フレーズ検出）
4. **再生成**: 違反がある場合の自動修正
5. **形式変換**: YouTube形式への変換
6. **品質評価**: 信頼度スコア計算

### 🔍 監視とログ

#### ログファイル
- `logs/guardrail_violations.json`: 安全性違反ログ
- 処理時間、信頼度スコア、違反数の追跡

#### APIエンドポイント
- `/mcp-status`: MCP設定状況確認
- `/logs/guardrail-violations`: 違反ログ取得
- `/health`: システム健全性確認

### 🎯 実装完了度: 100%

#### ✅ 実装済み機能
- [x] Anthropic's Constitutional AI
- [x] Google DeepMind's Sparrow Logic
- [x] Microsoft Guardrails
- [x] OpenAI/Cursor Rule System
- [x] モデルルーティング
- [x] 引用検証
- [x] 安全性チェック
- [x] APIエンドポイント
- [x] 統合テスト
- [x] ログ機能
- [x] 品質評価

#### 🚀 システム特徴
- **精密性**: 事実に基づいた正確な情報のみ使用
- **安全性**: 危険な表現の自動検出と修正
- **スケーラビリティ**: バッチ処理対応
- **監視性**: 詳細なログと品質指標
- **拡張性**: 新しいMCPルールの簡単追加

このシステムにより、研究からYouTube原稿を生成する際の最大限の事実正確性とアルゴリズム性能が実現されます。 