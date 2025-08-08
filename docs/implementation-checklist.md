# Dify ワークフロー実装チェックリスト

## 📋 実装手順

### ✅ Phase 1: 基本設定
- [ ] Dify管理画面にアクセス (http://localhost:3000)
- [ ] 新しいワークフローを作成
- [ ] 名前: "Sales Roleplay Workflow"
- [ ] 説明: "販売ロールプレイ用の音声対話システム"

### ✅ Phase 2: 入力ノード設定
- [ ] Start Nodeを配置
- [ ] 入力フィールドを追加:
  - [ ] `customer_message` (Text, Required)
  - [ ] `product_name` (Select, Options: ["サービスA", "サービスB", "サービスC"])
  - [ ] `customer_type` (Select, Options: ["新規顧客", "既存顧客", "見込み顧客"])
  - [ ] `salesperson_style` (Select, Options: ["新人営業", "ベテラン営業", "コンサルタント"])

### ✅ Phase 3: 分析ノード設定
- [ ] LLM Nodeを追加 (名前: input_analysis)
- [ ] プロンプトを設定:
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

### ✅ Phase 4: 応答生成ノード設定
- [ ] LLM Nodeを追加 (名前: response_generation)
- [ ] プロンプトを設定:
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

### ✅ Phase 5: 話者選択ノード設定
- [ ] Code Nodeを追加 (名前: speaker_selection)
- [ ] コードを設定:
```python
def main(salesperson_style: str, emotional_state: str) -> dict:
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
    
    selected_speaker = speaker_mapping.get(salesperson_style, {}).get(emotional_state, "13")
    
    return {
        "selected_speaker": selected_speaker,
        "speaker_info": f"{salesperson_style} - {emotional_state}"
    }
```

### ✅ Phase 6: TTS生成ノード設定
- [ ] HTTP Request Nodeを追加 (名前: tts_generation)
- [ ] 設定:
  - [ ] URL: `http://host.docker.internal:8080/v1/audio/speech`
  - [ ] Method: POST
  - [ ] Headers: `Content-Type: application/json`
  - [ ] Body:
```json
{
  "model": "tts-1",
  "input": "{{response_generation.text}}",
  "voice": "{{speaker_selection.selected_speaker}}",
  "response_format": "mp3"
}
```

### ✅ Phase 7: 出力ノード設定
- [ ] End Nodeを配置 (名前: final_output)
- [ ] 出力フィールドを設定:
  - [ ] `response_text`: {{response_generation.text}}
  - [ ] `audio_data`: {{tts_generation.body}}
  - [ ] `speaker_info`: {{speaker_selection.speaker_info}}
  - [ ] `analysis_result`: {{input_analysis.text}}

### ✅ Phase 8: ノード接続
- [ ] user_input → input_analysis
- [ ] input_analysis → response_generation
- [ ] response_generation → speaker_selection
- [ ] speaker_selection → tts_generation
- [ ] tts_generation → final_output

### ✅ Phase 9: テスト実行
- [ ] ワークフローを保存
- [ ] テストデータで実行:
  - [ ] customer_message: "御社のサービスについて詳しく教えてください"
  - [ ] product_name: "サービスA"
  - [ ] customer_type: "新規顧客"
  - [ ] salesperson_style: "新人営業"

### ✅ Phase 10: 動作確認
- [ ] 分析結果が適切に生成される
- [ ] 営業応答が自然で適切
- [ ] 話者選択が正しく動作
- [ ] TTS音声が生成される
- [ ] 出力データが完全

## 🔧 トラブルシューティング

### TTS API接続エラー
- [ ] FastAPIサーバーが起動しているか確認
- [ ] URLが正しいか確認 (host.docker.internal:8080)
- [ ] VOICEVOXコンテナが動作しているか確認

### LLMノードエラー
- [ ] プロンプトの変数名が正しいか確認
- [ ] 前のノードの出力名が正しいか確認
- [ ] LLMモデルが設定されているか確認

### Code Nodeエラー
- [ ] Python構文が正しいか確認
- [ ] 入力変数が正しく渡されているか確認
- [ ] 戻り値の形式が正しいか確認

## 📊 テストシナリオ

### シナリオ1: 基本動作確認
```
customer_message: "こんにちは、サービスについて教えてください"
product_name: "サービスA"
customer_type: "新規顧客"
salesperson_style: "新人営業"
```

### シナリオ2: 価格相談
```
customer_message: "価格はどのくらいですか？"
product_name: "サービスB"
customer_type: "見込み顧客"
salesperson_style: "ベテラン営業"
```

### シナリオ3: 技術的質問
```
customer_message: "技術的な詳細を知りたいです"
product_name: "サービスC"
customer_type: "既存顧客"
salesperson_style: "コンサルタント"
``` 