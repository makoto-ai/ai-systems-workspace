# 販売ロールプレイワークフロー設計書

## 🎯 ワークフロー概要

### 目的
Dify v1.5.1のワークフロー機能を使用して、販売シナリオに特化したロールプレイシステムを構築する。

### システム構成
```
入力 → 分析 → LLM処理 → 話者選択 → TTS生成 → 出力
```

## 📋 ワークフロー詳細設計

### 1. 入力ノード (Input Node)
**ノード名**: `user_input`
**タイプ**: Start Node
**パラメータ**:
- `customer_message`: テキスト入力（顧客の発言）
- `product_name`: 商品名（選択式）
- `customer_type`: 顧客タイプ（選択式）
- `salesperson_style`: 営業スタイル（選択式）

### 2. 分析ノード (Analysis Node)
**ノード名**: `input_analysis`
**タイプ**: LLM Node
**プロンプト**:
```
あなたは販売分析の専門家です。以下の情報を分析してください：

顧客の発言: {{customer_message}}
商品名: {{product_name}}
顧客タイプ: {{customer_type}}
営業スタイル: {{salesperson_style}}

以下の形式で分析結果を返してください：
- 顧客の関心度: (高/中/低)
- 主要な懸念点: (具体的な懸念)
- 推奨アプローチ: (アプローチ戦略)
- 感情の状態: (positive/neutral/negative)
```

### 3. 応答生成ノード (Response Generation Node)
**ノード名**: `response_generation`
**タイプ**: LLM Node
**プロンプト**:
```
あなたは経験豊富な{{salesperson_style}}の営業担当者です。

顧客情報:
- 発言: {{customer_message}}
- タイプ: {{customer_type}}
- 関心度: {{input_analysis.customer_interest}}
- 懸念点: {{input_analysis.main_concerns}}
- 感情状態: {{input_analysis.emotional_state}}

商品情報:
- 商品名: {{product_name}}

推奨アプローチ: {{input_analysis.recommended_approach}}

上記の情報を基に、適切な営業応答を生成してください。
応答は自然で親しみやすく、顧客の懸念に対処する内容にしてください。
```

### 4. 話者選択ノード (Speaker Selection Node)
**ノード名**: `speaker_selection`
**タイプ**: Code Node
**ロジック**:
```python
def select_speaker(salesperson_style, emotional_state):
    speaker_mapping = {
        "新人営業": {
            "positive": "13",  # 青山龍星（爽やか）
            "neutral": "13",
            "negative": "8"    # 春日部つむぎ（丁寧）
        },
        "ベテラン営業": {
            "positive": "11",  # 玄野武宏（落ち着き）
            "neutral": "11",
            "negative": "11"
        },
        "コンサルタント": {
            "positive": "52",  # 雀松朱司（コンサル）
            "neutral": "52",
            "negative": "52"
        }
    }
    
    return speaker_mapping.get(salesperson_style, {}).get(emotional_state, "13")
```

### 5. TTS生成ノード (TTS Generation Node)
**ノード名**: `tts_generation`
**タイプ**: HTTP Request Node
**設定**:
- **URL**: `http://host.docker.internal:8080/v1/audio/speech`
- **Method**: POST
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "model": "tts-1",
  "input": "{{response_generation.output}}",
  "voice": "{{speaker_selection.selected_speaker}}",
  "response_format": "mp3"
}
```

### 6. 出力ノード (Output Node)
**ノード名**: `final_output`
**タイプ**: End Node
**出力**:
- `response_text`: 生成された応答テキスト
- `audio_data`: 音声データ（Base64）
- `speaker_info`: 使用した話者情報
- `analysis_result`: 分析結果

## 🎨 Dify UI での実装手順

### Step 1: 新しいワークフローの作成
1. Dify管理画面で「ワークフロー」→「新規作成」
2. 名前: "Sales Roleplay Workflow"
3. 説明: "販売ロールプレイ用の音声対話システム"

### Step 2: 入力ノードの設定
1. Start Nodeを配置
2. 入力フィールドを追加:
   - `customer_message` (Text, Required)
   - `product_name` (Select, Options: ["サービスA", "サービスB", "サービスC"])
   - `customer_type` (Select, Options: ["新規顧客", "既存顧客", "見込み顧客"])
   - `salesperson_style` (Select, Options: ["新人営業", "ベテラン営業", "コンサルタント"])

### Step 3: LLMノードの設定
1. 分析ノード用のLLMノードを追加
2. 応答生成ノード用のLLMノードを追加
3. 各ノードにプロンプトを設定

### Step 4: HTTPノードの設定
1. HTTP Requestノードを追加
2. TTS APIの設定を入力
3. レスポンス処理の設定

### Step 5: 出力ノードの設定
1. End Nodeを配置
2. 出力フィールドを設定

## 🔧 技術的な設定

### 環境変数
```env
DIFY_API_KEY=your_api_key
VOICEVOX_API_URL=http://host.docker.internal:8080
```

### HTTPツール設定
- **Name**: VOICEVOX TTS
- **URL**: http://host.docker.internal:8080/v1/audio/speech
- **Authentication**: None
- **Timeout**: 30s

## 📊 テストシナリオ

### シナリオ1: 新規顧客への初回提案
- **顧客メッセージ**: "御社のサービスについて詳しく教えてください"
- **商品名**: "サービスA"
- **顧客タイプ**: "新規顧客"
- **営業スタイル**: "新人営業"

### シナリオ2: 既存顧客からの価格相談
- **顧客メッセージ**: "価格についてもう少し相談したいのですが..."
- **商品名**: "サービスB"
- **顧客タイプ**: "既存顧客"
- **営業スタイル**: "ベテラン営業"

### シナリオ3: 見込み顧客への技術説明
- **顧客メッセージ**: "技術的な詳細を知りたいです"
- **商品名**: "サービスC"
- **顧客タイプ**: "見込み顧客"
- **営業スタイル**: "コンサルタント"

## 🎯 期待される効果

1. **個別最適化**: 顧客タイプと営業スタイルに応じた最適な応答
2. **音声品質**: 適切な話者による自然な音声生成
3. **学習効果**: 様々なシナリオでの営業スキル向上
4. **分析機能**: 顧客の反応と営業効果の分析

## 📈 将来の拡張計画

1. **WhisperX統合**: 音声入力機能の追加
2. **感情分析**: より詳細な感情分析機能
3. **業界特化**: 業界別のプロンプト最適化
4. **パフォーマンス分析**: 営業成果の追跡と分析 