# 音声分析機能 実装ロードマップ

## 現在実装済み (Phase 6-7)

### ✅ 基本音声分析
- **話者分離**: WhisperX Speaker Diarization
- **音声認識信頼度**: 0-1スケールの信頼度スコア
- **言語検出**: 17言語の自動検出
- **音声品質**: 音声時間、セグメント分析

### ✅ 出力データ例
```json
{
  "text": "こんにちは、料金について教えてください",
  "language": "ja",
  "confidence": 0.95,
  "duration": 3.2,
  "speaker_count": 1,
  "speakers": ["SPEAKER_00"],
  "segments": [
    {
      "start": 0.0,
      "end": 1.5,
      "text": "こんにちは",
      "confidence": 0.98,
      "speaker": "SPEAKER_00"
    }
  ]
}
```

## Phase 8: 営業分析機能 (高優先度)

### 1. 感情分析 (Emotion Analysis)
```python
# 実装すべき機能
emotion_analysis = {
    "overall_sentiment": "positive",  # positive/neutral/negative
    "emotion_scores": {
        "interest": 0.8,      # 興味度
        "confidence": 0.6,    # 自信度
        "urgency": 0.3,       # 緊急度
        "skepticism": 0.2     # 懐疑度
    },
    "voice_characteristics": {
        "speaking_rate": "normal",    # slow/normal/fast
        "volume_level": "medium",     # low/medium/high
        "pitch_variation": "moderate" # monotone/moderate/expressive
    }
}
```

### 2. 営業パフォーマンス分析
```python
sales_analysis = {
    "communication_quality": {
        "clarity": 0.9,           # 発話の明瞭度
        "fluency": 0.8,           # 流暢さ
        "pace": "appropriate",    # 話すスピード
        "filler_words": 0.1       # 「えー」「あの」の頻度
    },
    "sales_skills": {
        "active_listening": 0.7,  # 相手の話を聞いているか
        "question_quality": 0.8,  # 質問の質
        "objection_handling": 0.6 # 異議処理
    },
    "customer_engagement": {
        "interest_level": 0.8,    # 顧客の興味度
        "buying_signals": 0.4,    # 購買シグナル
        "resistance_level": 0.2   # 抵抗度
    }
}
```

### 3. 声紋分析 (Voice Biometrics)
```python
voice_biometrics = {
    "speaker_verification": {
        "identity_confidence": 0.95,  # 話者同一性
        "voice_consistency": 0.92     # 声の一貫性
    },
    "vocal_characteristics": {
        "fundamental_frequency": 150,  # 基本周波数 (Hz)
        "formant_frequencies": [800, 1200, 2400],  # フォルマント
        "spectral_centroid": 1500,     # スペクトル重心
        "zero_crossing_rate": 0.1      # ゼロ交差率
    },
    "speaking_patterns": {
        "pause_frequency": 0.15,       # ポーズの頻度
        "speech_rhythm": "regular",    # 話すリズム
        "intonation_pattern": "varied" # イントネーション
    }
}
```

## Phase 8: 実装計画

### 8.1 感情分析エンジン統合
- **ライブラリ**: `librosa` + `transformers` (感情認識モデル)
- **リアルタイム処理**: 音声セグメント毎の感情分析
- **営業特化**: 興味・懐疑・購買意欲の検出

### 8.2 声紋分析システム
- **音響特徴抽出**: MFCC、メルスペクトログラム
- **話者認証**: 同一人物の継続確認
- **ストレス検出**: 声の緊張度測定

### 8.3 営業スキル評価
- **会話分析**: 質問の質、聞く姿勢
- **説得力測定**: 論理性、説得技法
- **顧客反応分析**: 興味度、抵抗度

## Phase 9: 高度な分析 (中優先度)

### 9.1 マルチモーダル分析
- **音声 + テキスト**: 内容と音声特徴の統合分析
- **時系列分析**: 会話の流れに沿った変化追跡
- **パターン認識**: 成功する営業パターンの学習

### 9.2 予測分析
- **成約確度予測**: 会話内容から成約可能性を予測
- **最適応答提案**: 次に言うべき最適な言葉を提案
- **リスク検出**: 失注リスクの早期発見

## Phase 10: AI コーチング (低優先度)

### 10.1 リアルタイムフィードバック
- **即座の改善提案**: 「もう少しゆっくり話してください」
- **感情調整**: 「相手が不安そうです。安心させる言葉を」
- **戦略提案**: 「価格の話題に移るタイミングです」

### 10.2 パーソナライズド分析
- **個人特性分析**: 営業スタイルの強み・弱み
- **成長追跡**: スキル向上の可視化
- **ベンチマーク**: 他の営業との比較

## 技術実装詳細

### 感情分析実装
```python
import librosa
import numpy as np
from transformers import pipeline

class EmotionAnalyzer:
    def __init__(self):
        self.emotion_classifier = pipeline(
            "audio-classification",
            model="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
        )
    
    async def analyze_emotion(self, audio_data: bytes) -> Dict[str, Any]:
        # 音響特徴抽出
        y, sr = librosa.load(io.BytesIO(audio_data))
        
        # 感情分析
        emotions = self.emotion_classifier(audio_data)
        
        # 音響特徴
        mfcc = librosa.feature.mfcc(y=y, sr=sr)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        
        return {
            "emotions": emotions,
            "acoustic_features": {
                "mfcc_mean": np.mean(mfcc, axis=1).tolist(),
                "spectral_centroid": np.mean(spectral_centroid)
            }
        }
```

### 営業分析実装
```python
class SalesAnalyzer:
    def __init__(self):
        self.conversation_analyzer = ConversationAnalyzer()
        
    async def analyze_sales_performance(
        self, 
        conversation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        
        # 会話内容分析
        content_analysis = await self._analyze_content(
            conversation_data["text"]
        )
        
        # 音声特徴分析
        voice_analysis = await self._analyze_voice_features(
            conversation_data["audio_features"]
        )
        
        # 営業スキル評価
        skills_evaluation = await self._evaluate_sales_skills(
            content_analysis, voice_analysis
        )
        
        return {
            "overall_score": skills_evaluation["overall"],
            "detailed_analysis": {
                "content": content_analysis,
                "voice": voice_analysis,
                "skills": skills_evaluation
            },
            "recommendations": self._generate_recommendations(
                skills_evaluation
            )
        }
```

## 実装スケジュール

### Week 1-2: 感情分析
- 音響特徴抽出エンジン
- 感情認識モデル統合
- リアルタイム感情分析

### Week 3-4: 声紋分析
- 声紋特徴抽出
- 話者認証システム
- 音声品質評価

### Week 5-6: 営業分析
- 会話分析エンジン
- 営業スキル評価
- パフォーマンス指標

### Week 7-8: 統合とテスト
- 全分析機能の統合
- UI/UX改善
- 総合テスト

## 結論

音声分析・声紋分析は**Phase 8で実装すべき重要機能**です。
これらがあることで：

1. **営業スキルの客観的評価**が可能
2. **リアルタイムフィードバック**で即座の改善
3. **データドリブンな営業研修**を実現

最後に実装するのではなく、**営業ロールプレイの核心機能**として早期実装が重要です。 