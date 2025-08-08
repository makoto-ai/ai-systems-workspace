#!/usr/bin/env python3
"""
品質メトリクスサービス
BLEU/ROUGE スコア計算システム

Author: AI Assistant
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import Counter
import statistics

@dataclass
class QualityScores:
    """品質スコア結果"""
    bleu_score: float
    rouge_1: float
    rouge_2: float
    rouge_l: float
    readability_score: float
    coherence_score: float
    overall_score: float

class QualityMetricsService:
    """品質メトリクスサービス"""
    
    def __init__(self):
        self.service_name = "品質メトリクスサービス"
        self.version = "1.0.0"
    
    def calculate_quality_scores(
        self, 
        reference_text: str, 
        generated_text: str
    ) -> QualityScores:
        """品質スコア計算（メイン）"""
        
        # 基本的な前処理
        ref_clean = self._preprocess_text(reference_text)
        gen_clean = self._preprocess_text(generated_text)
        
        # 各メトリクス計算
        bleu = self._calculate_bleu(ref_clean, gen_clean)
        rouge_1 = self._calculate_rouge_1(ref_clean, gen_clean)
        rouge_2 = self._calculate_rouge_2(ref_clean, gen_clean)
        rouge_l = self._calculate_rouge_l(ref_clean, gen_clean)
        readability = self._calculate_readability(gen_clean)
        coherence = self._calculate_coherence(gen_clean)
        
        # 総合スコア計算
        overall = self._calculate_overall_score(
            bleu, rouge_1, rouge_2, rouge_l, readability, coherence
        )
        
        return QualityScores(
            bleu_score=bleu,
            rouge_1=rouge_1,
            rouge_2=rouge_2,
            rouge_l=rouge_l,
            readability_score=readability,
            coherence_score=coherence,
            overall_score=overall
        )
    
    def _preprocess_text(self, text: str) -> List[str]:
        """テキスト前処理"""
        # 小文字化、句読点除去、トークン化
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        return [token for token in tokens if token.strip()]
    
    def _calculate_bleu(self, reference: List[str], generated: List[str]) -> float:
        """BLEU スコア計算（簡易版）"""
        if not reference or not generated:
            return 0.0
        
        # 1-gramマッチング
        ref_counter = Counter(reference)
        gen_counter = Counter(generated)
        
        matches = sum((ref_counter & gen_counter).values())
        total = len(generated)
        
        if total == 0:
            return 0.0
        
        precision = matches / total
        
        # 長さペナルティ（簡易版）
        bp = min(1.0, len(generated) / len(reference)) if reference else 0.0
        
        return bp * precision
    
    def _calculate_rouge_1(self, reference: List[str], generated: List[str]) -> float:
        """ROUGE-1 スコア計算"""
        if not reference or not generated:
            return 0.0
        
        ref_set = set(reference)
        gen_set = set(generated)
        
        overlap = len(ref_set & gen_set)
        
        if len(ref_set) == 0:
            return 0.0
        
        return overlap / len(ref_set)
    
    def _calculate_rouge_2(self, reference: List[str], generated: List[str]) -> float:
        """ROUGE-2 スコア計算（バイグラム）"""
        if len(reference) < 2 or len(generated) < 2:
            return 0.0
        
        # バイグラム生成
        ref_bigrams = set(zip(reference[:-1], reference[1:]))
        gen_bigrams = set(zip(generated[:-1], generated[1:]))
        
        overlap = len(ref_bigrams & gen_bigrams)
        
        if len(ref_bigrams) == 0:
            return 0.0
        
        return overlap / len(ref_bigrams)
    
    def _calculate_rouge_l(self, reference: List[str], generated: List[str]) -> float:
        """ROUGE-L スコア計算（最長共通部分列）"""
        if not reference or not generated:
            return 0.0
        
        # LCS計算（簡易版）
        lcs_length = self._lcs_length(reference, generated)
        
        if len(reference) == 0:
            return 0.0
        
        return lcs_length / len(reference)
    
    def _lcs_length(self, seq1: List[str], seq2: List[str]) -> int:
        """最長共通部分列の長さ計算"""
        m, n = len(seq1), len(seq2)
        
        # DP テーブル
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    def _calculate_readability(self, tokens: List[str]) -> float:
        """読みやすさスコア計算"""
        if not tokens:
            return 0.0
        
        # 平均単語長
        avg_word_length = statistics.mean(len(word) for word in tokens)
        
        # 短い単語ほど読みやすい（簡易版）
        readability = max(0.0, 1.0 - (avg_word_length - 3.0) / 10.0)
        
        return min(1.0, readability)
    
    def _calculate_coherence(self, tokens: List[str]) -> float:
        """一貫性スコア計算"""
        if len(tokens) < 2:
            return 0.0
        
        # 隣接する単語の類似性（簡易版）
        coherence_scores = []
        
        for i in range(len(tokens) - 1):
            word1, word2 = tokens[i], tokens[i + 1]
            # 簡易的な類似性計算（文字の一致率）
            similarity = self._word_similarity(word1, word2)
            coherence_scores.append(similarity)
        
        return statistics.mean(coherence_scores) if coherence_scores else 0.0
    
    def _word_similarity(self, word1: str, word2: str) -> float:
        """単語間類似性計算（簡易版）"""
        if not word1 or not word2:
            return 0.0
        
        # 文字レベルの一致率
        common_chars = len(set(word1) & set(word2))
        total_chars = len(set(word1) | set(word2))
        
        return common_chars / total_chars if total_chars > 0 else 0.0
    
    def _calculate_overall_score(
        self, 
        bleu: float, 
        rouge_1: float, 
        rouge_2: float, 
        rouge_l: float, 
        readability: float, 
        coherence: float
    ) -> float:
        """総合スコア計算"""
        # 重み付き平均
        weights = {
            'bleu': 0.2,
            'rouge_1': 0.2,
            'rouge_2': 0.15,
            'rouge_l': 0.15,
            'readability': 0.15,
            'coherence': 0.15
        }
        
        total_score = (
            bleu * weights['bleu'] +
            rouge_1 * weights['rouge_1'] +
            rouge_2 * weights['rouge_2'] +
            rouge_l * weights['rouge_l'] +
            readability * weights['readability'] +
            coherence * weights['coherence']
        )
        
        return min(1.0, total_score)

# サービス取得関数
def get_quality_metrics_service() -> QualityMetricsService:
    """品質メトリクスサービス取得"""
    return QualityMetricsService()