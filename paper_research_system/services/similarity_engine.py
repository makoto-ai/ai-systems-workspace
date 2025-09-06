"""
Similarity Engine for Academic Paper Recommendation
論文推薦システム用類似度計算エンジン
"""

from ..core.paper_model import Paper
import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
import math
import sys
from pathlib import Path

# Package-relative imports are used; no sys.path modification


logger = logging.getLogger(__name__)


class SimilarityEngine:
    """論文類似度計算エンジン"""

    def __init__(self):
        """初期化"""
        self.stop_words = self._load_stop_words()
        self.author_weight = 0.25
        self.keyword_weight = 0.35
        self.content_weight = 0.40

    def _load_stop_words(self) -> set:
        """英語ストップワードをロード"""
        # 基本的な英語ストップワード
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "this",
            "that",
            "these",
            "those",
            "it",
            "its",
            "they",
            "them",
            "their",
            "we",
            "us",
            "our",
            "you",
            "your",
            "he",
            "him",
            "his",
            "she",
            "her",
            "from",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "not",
            "no",
            "very",
            "more",
            "most",
            "other",
            "some",
            "any",
            "may",
            "can",
        }
        return stop_words

    def calculate_similarity(self, paper1: Paper, paper2: Paper) -> float:
        """
        2つの論文間の総合類似度を計算

        Args:
            paper1: 比較対象論文1
            paper2: 比較対象論文2

        Returns:
            類似度スコア (0.0 - 1.0)
        """
        try:
            # 各要素の類似度計算
            content_sim = self._calculate_content_similarity(paper1, paper2)
            author_sim = self._calculate_author_similarity(paper1, paper2)
            keyword_sim = self._calculate_keyword_similarity(paper1, paper2)

            # 重み付き総合類似度
            total_similarity = (
                content_sim * self.content_weight
                + author_sim * self.author_weight
                + keyword_sim * self.keyword_weight
            )

            logger.debug(
                f"類似度計算: content={
                    content_sim:.3f}, author={
                    author_sim:.3f}, keyword={
                    keyword_sim:.3f}, total={
                    total_similarity:.3f}"
            )

            return min(total_similarity, 1.0)

        except Exception as e:
            logger.error(f"類似度計算エラー: {e}")
            return 0.0

    def _calculate_content_similarity(self, paper1: Paper, paper2: Paper) -> float:
        """コンテンツ類似度計算（タイトル + 概要）"""
        # テキスト結合
        text1 = self._combine_text(paper1)
        text2 = self._combine_text(paper2)

        if not text1 or not text2:
            return 0.0

        # TF-IDF ベクトル化
        vocab, tf_idf1, tf_idf2 = self._calculate_tf_idf(text1, text2)

        if not vocab:
            return 0.0

        # コサイン類似度計算
        return self._cosine_similarity(tf_idf1, tf_idf2)

    def _calculate_author_similarity(self, paper1: Paper, paper2: Paper) -> float:
        """著者類似度計算"""
        if not paper1.authors or not paper2.authors:
            return 0.0

        authors1 = {
            author.name.lower().strip() for author in paper1.authors if author.name
        }
        authors2 = {
            author.name.lower().strip() for author in paper2.authors if author.name
        }

        if not authors1 or not authors2:
            return 0.0

        # Jaccard係数による類似度
        intersection = len(authors1.intersection(authors2))
        union = len(authors1.union(authors2))

        return intersection / union if union > 0 else 0.0

    def _calculate_keyword_similarity(self, paper1: Paper, paper2: Paper) -> float:
        """キーワード類似度計算"""
        keywords1 = self._extract_keywords(paper1)
        keywords2 = self._extract_keywords(paper2)

        if not keywords1 or not keywords2:
            return 0.0

        # 重み付きJaccard係数
        all_keywords = keywords1.keys() | keywords2.keys()
        dot_product = 0.0
        norm1 = sum(keywords1[k] ** 2 for k in keywords1)
        norm2 = sum(keywords2[k] ** 2 for k in keywords2)

        for keyword in all_keywords:
            dot_product += keywords1.get(keyword, 0) * keywords2.get(keyword, 0)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (math.sqrt(norm1) * math.sqrt(norm2))

    def _combine_text(self, paper: Paper) -> str:
        """論文のテキストを結合"""
        parts = []

        if paper.title:
            # タイトルを重視（3回繰り返し）
            parts.extend([paper.title] * 3)

        if paper.abstract:
            parts.append(paper.abstract)

        if paper.keywords:
            # キーワードを重視（2回繰り返し）
            keyword_text = " ".join(paper.keywords)
            parts.extend([keyword_text] * 2)

        return " ".join(parts)

    def _extract_keywords(self, paper: Paper) -> Dict[str, float]:
        """論文からキーワードを抽出（重み付き）"""
        text = self._combine_text(paper)
        if not text:
            return {}

        # テキスト正規化
        text = re.sub(r"[^\w\s]", " ", text.lower())
        words = text.split()

        # ストップワード除去
        words = [
            word for word in words if word not in self.stop_words and len(word) > 2
        ]

        # 頻度計算
        word_counts = Counter(words)
        total_words = len(words)

        # TF-IDF風の重み計算
        keyword_weights = {}
        for word, count in word_counts.items():
            tf = count / total_words
            # 長い単語により高い重みを付与
            length_bonus = min(len(word) / 10, 1.5)
            keyword_weights[word] = tf * length_bonus

        return keyword_weights

    def _calculate_tf_idf(
        self, text1: str, text2: str
    ) -> Tuple[List[str], List[float], List[float]]:
        """TF-IDF計算"""

        # テキスト正規化
        def normalize_text(text):
            text = re.sub(r"[^\w\s]", " ", text.lower())
            words = text.split()
            return [
                word for word in words if word not in self.stop_words and len(word) > 2
            ]

        words1 = normalize_text(text1)
        words2 = normalize_text(text2)

        if not words1 or not words2:
            return [], [], []

        # 語彙構築
        vocab = list(set(words1 + words2))
        vocab.sort()  # 一貫性のため

        # TF計算
        def calculate_tf(words, vocab):
            word_counts = Counter(words)
            total_words = len(words)
            return [word_counts[word] / total_words for word in vocab]

        tf1 = calculate_tf(words1, vocab)
        tf2 = calculate_tf(words2, vocab)

        # IDF計算（2文書の簡易版）
        idf = []
        for word in vocab:
            doc_freq = (1 if word in words1 else 0) + (1 if word in words2 else 0)
            idf.append(math.log(2 / doc_freq) if doc_freq > 0 else 0)

        # TF-IDF計算
        tf_idf1 = [tf1[i] * idf[i] for i in range(len(vocab))]
        tf_idf2 = [tf2[i] * idf[i] for i in range(len(vocab))]

        return vocab, tf_idf1, tf_idf2

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """コサイン類似度計算"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def find_most_similar(
        self, target_paper: Paper, candidate_papers: List[Paper], top_k: int = 5
    ) -> List[Tuple[Paper, float]]:
        """
        最も類似した論文を見つける

        Args:
            target_paper: 基準となる論文
            candidate_papers: 候補論文リスト
            top_k: 返す論文数

        Returns:
            (論文, 類似度)のタプルリスト（類似度降順）
        """
        similarities = []

        for candidate in candidate_papers:
            # 同じ論文はスキップ
            if self._is_same_paper(target_paper, candidate):
                continue

            similarity = self.calculate_similarity(target_paper, candidate)
            if similarity > 0.1:  # 最低閾値
                similarities.append((candidate, similarity))

        # 類似度でソート
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    def _is_same_paper(self, paper1: Paper, paper2: Paper) -> bool:
        """同じ論文かどうか判定"""
        # DOIが同じ
        if paper1.doi and paper2.doi and paper1.doi == paper2.doi:
            return True

        # タイトルが90%以上類似
        if paper1.title and paper2.title:
            title_sim = self._calculate_content_similarity_simple(
                paper1.title, paper2.title
            )
            if title_sim > 0.9:
                return True

        return False

    def _calculate_content_similarity_simple(self, text1: str, text2: str) -> float:
        """シンプルなコンテンツ類似度（タイトル比較用）"""
        if not text1 or not text2:
            return 0.0

        words1 = set(re.findall(r"\w+", text1.lower()))
        words2 = set(re.findall(r"\w+", text2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0


# シングルトンインスタンス
_similarity_engine = None


def get_similarity_engine() -> SimilarityEngine:
    """SimilarityEngineのシングルトンインスタンスを取得"""
    global _similarity_engine
    if _similarity_engine is None:
        _similarity_engine = SimilarityEngine()
    return _similarity_engine
