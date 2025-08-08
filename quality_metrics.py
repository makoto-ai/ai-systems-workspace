"""
BLEU/ROUGEスコア算出機能
nltk, rouge-score を使い、文書類似度を算出
"""

import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
from typing import Dict, Any, List, Optional
import numpy as np


class QualityMetrics:
    """BLEU/ROUGEスコアを計算するクラス"""
    
    def __init__(self):
        # NLTKデータのダウンロード
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        # ROUGEスコアラーを初期化
        self.rouge_scorer = rouge_scorer.RougeScorer(
            ['rouge1', 'rouge2', 'rougeL'], 
            use_stemmer=True
        )
        
        # BLEUスコアの平滑化関数
        self.smoothing_function = SmoothingFunction().method4
    
    def calculate_bleu_score(self, reference: str, candidate: str) -> float:
        """
        BLEUスコアを計算
        
        Args:
            reference: 参照テキスト
            candidate: 候補テキスト
        
        Returns:
            BLEUスコア (0-1)
        """
        # トークン化
        reference_tokens = [nltk.word_tokenize(reference.lower())]
        candidate_tokens = nltk.word_tokenize(candidate.lower())
        
        # BLEUスコア計算
        score = sentence_bleu(
            reference_tokens, 
            candidate_tokens, 
            smoothing_function=self.smoothing_function
        )
        
        return score
    
    def calculate_rouge_scores(self, reference: str, candidate: str) -> Dict[str, float]:
        """
        ROUGEスコアを計算
        
        Args:
            reference: 参照テキスト
            candidate: 候補テキスト
        
        Returns:
            ROUGEスコアの辞書
        """
        scores = self.rouge_scorer.score(reference, candidate)
        
        return {
            'rouge1': scores['rouge1'].fmeasure,
            'rouge2': scores['rouge2'].fmeasure,
            'rougeL': scores['rougeL'].fmeasure
        }
    
    def calculate_all_metrics(self, reference: str, candidate: str) -> Dict[str, Any]:
        """
        全ての品質メトリクスを計算
        
        Args:
            reference: 参照テキスト
            candidate: 候補テキスト
        
        Returns:
            全メトリクスの辞書
        """
        bleu_score = self.calculate_bleu_score(reference, candidate)
        rouge_scores = self.calculate_rouge_scores(reference, candidate)
        
        # 総合評価スコアを計算
        overall_score = self._calculate_overall_score(bleu_score, rouge_scores)
        
        return {
            'bleu_score': round(bleu_score, 4),
            'rouge_scores': {k: round(v, 4) for k, v in rouge_scores.items()},
            'overall_score': round(overall_score, 4),
            'assessment': self._get_assessment(overall_score)
        }
    
    def _calculate_overall_score(self, bleu_score: float, rouge_scores: Dict[str, float]) -> float:
        """
        総合評価スコアを計算
        
        Args:
            bleu_score: BLEUスコア
            rouge_scores: ROUGEスコア
        
        Returns:
            総合スコア (0-1)
        """
        # 重み付け平均を計算
        weights = {
            'bleu': 0.3,
            'rouge1': 0.25,
            'rouge2': 0.25,
            'rougeL': 0.2
        }
        
        overall = (
            bleu_score * weights['bleu'] +
            rouge_scores['rouge1'] * weights['rouge1'] +
            rouge_scores['rouge2'] * weights['rouge2'] +
            rouge_scores['rougeL'] * weights['rougeL']
        )
        
        return overall
    
    def _get_assessment(self, overall_score: float) -> str:
        """
        総合スコアから評価を判定
        
        Args:
            overall_score: 総合スコア
        
        Returns:
            評価文字列
        """
        if overall_score >= 0.8:
            return "優秀"
        elif overall_score >= 0.6:
            return "良好"
        elif overall_score >= 0.4:
            return "普通"
        else:
            return "要改善"
    
    def compare_multiple_candidates(self, reference: str, candidates: List[str]) -> List[Dict[str, Any]]:
        """
        複数の候補テキストを比較
        
        Args:
            reference: 参照テキスト
            candidates: 候補テキストのリスト
        
        Returns:
            各候補の評価結果のリスト
        """
        results = []
        
        for i, candidate in enumerate(candidates):
            metrics = self.calculate_all_metrics(reference, candidate)
            metrics['candidate_index'] = i
            results.append(metrics)
        
        # 総合スコアでソート
        results.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return results
    
    def get_detailed_analysis(self, reference: str, candidate: str) -> Dict[str, Any]:
        """
        詳細な分析を提供
        
        Args:
            reference: 参照テキスト
            candidate: 候補テキスト
        
        Returns:
            詳細分析結果
        """
        metrics = self.calculate_all_metrics(reference, candidate)
        
        # テキスト統計
        ref_words = len(reference.split())
        cand_words = len(candidate.split())
        
        # 詳細分析
        analysis = {
            'metrics': metrics,
            'text_statistics': {
                'reference_length': ref_words,
                'candidate_length': cand_words,
                'length_ratio': round(cand_words / ref_words, 2) if ref_words > 0 else 0
            },
            'recommendations': self._get_recommendations(metrics, ref_words, cand_words)
        }
        
        return analysis
    
    def _get_recommendations(self, metrics: Dict[str, Any], ref_length: int, cand_length: int) -> List[str]:
        """
        改善提案を生成
        
        Args:
            metrics: 計算されたメトリクス
            ref_length: 参照テキストの長さ
            cand_length: 候補テキストの長さ
        
        Returns:
            改善提案のリスト
        """
        recommendations = []
        
        # BLEUスコアに基づく提案
        if metrics['bleu_score'] < 0.3:
            recommendations.append("BLEUスコアが低いため、より正確な翻訳/生成が必要です")
        
        # ROUGEスコアに基づく提案
        if metrics['rouge_scores']['rougeL'] < 0.3:
            recommendations.append("内容の重複度が低いため、より関連性の高い内容を含めてください")
        
        # 長さに基づく提案
        length_ratio = cand_length / ref_length if ref_length > 0 else 0
        if length_ratio < 0.5:
            recommendations.append("テキストが短すぎるため、より詳細な説明を追加してください")
        elif length_ratio > 2.0:
            recommendations.append("テキストが長すぎるため、簡潔にまとめてください")
        
        # 総合評価に基づく提案
        if metrics['overall_score'] < 0.4:
            recommendations.append("全体的な品質が低いため、大幅な改善が必要です")
        
        return recommendations


# シングルトンインスタンス
_quality_metrics_instance = None


def get_quality_metrics() -> QualityMetrics:
    """QualityMetricsのシングルトンインスタンスを取得"""
    global _quality_metrics_instance
    if _quality_metrics_instance is None:
        _quality_metrics_instance = QualityMetrics()
    return _quality_metrics_instance


if __name__ == "__main__":
    # テスト用のサンプルデータ
    reference_text = """
    本研究では、機械学習技術を用いて営業活動の効率化を図る手法を提案する。
    顧客データの分析により、成約率を30%向上させることに成功した。
    特に、顧客の購買行動パターンを分析することで、最適なアプローチタイミングを
    特定できることが明らかになった。
    """
    
    candidate_text = """
    機械学習を使った営業効率化の研究について説明します。
    顧客データを分析して、成約率を30%上げることに成功しました。
    顧客の購買パターンを分析して、最適なアプローチのタイミングを
    見つけることができるようになりました。
    """
    
    # 品質メトリクスを計算
    metrics = get_quality_metrics()
    results = metrics.calculate_all_metrics(reference_text, candidate_text)
    
    print("品質メトリクス結果:")
    print(f"BLEUスコア: {results['bleu_score']}")
    print(f"ROUGEスコア: {results['rouge_scores']}")
    print(f"総合スコア: {results['overall_score']}")
    print(f"評価: {results['assessment']}")
    
    # 詳細分析
    detailed_analysis = metrics.get_detailed_analysis(reference_text, candidate_text)
    print(f"\n詳細分析:")
    print(f"テキスト統計: {detailed_analysis['text_statistics']}")
    print(f"改善提案: {detailed_analysis['recommendations']}") 