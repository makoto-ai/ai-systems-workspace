"""
Recommendation Engine for Academic Papers
学術論文推薦エンジン
"""

from services.safe_rate_limited_search_service import (
    get_safe_rate_limited_search_service,
)
from services.similarity_engine import get_similarity_engine
from core.paper_model import Paper
import asyncio
import logging
import re
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import Counter, defaultdict
import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


logger = logging.getLogger(__name__)


class RecommendationEngine:
    """学術論文推薦エンジン"""

    def __init__(self):
        """初期化"""
        self.similarity_engine = get_similarity_engine()
        self.search_service = get_safe_rate_limited_search_service()
        self.min_similarity_threshold = 0.15
        self.diversity_weight = 0.3
        self.max_papers_per_author = 2  # 同一著者からの最大推薦数

    async def generate_recommendations(
        self,
        source_papers: List[Paper],
        max_recommendations: int = 10,
        expand_search: bool = True,
    ) -> List[Tuple[Paper, float, str]]:
        """
        検索結果に基づいて関連論文を推薦

        Args:
            source_papers: 基となる論文リスト
            max_recommendations: 最大推薦数
            expand_search: 拡張検索を行うかどうか

        Returns:
            (推薦論文, 類似度スコア, 推薦理由)のタプルリスト
        """
        try:
            if not source_papers:
                logger.warning("推薦の基となる論文がありません")
                return []

            logger.info(
                f"推薦生成開始: 基論文数={
                    len(source_papers)}, 拡張検索={
                    '有効' if expand_search else '無効'}"
            )

            # 候補論文収集
            candidate_papers = []

            if expand_search:
                # 拡張検索による候補収集
                expanded_papers = await self._expand_search_candidates(source_papers)
                candidate_papers.extend(expanded_papers)
                logger.info(f"拡張検索で{len(expanded_papers)}件の候補を収集")

            # 類似度ベース推薦
            similarity_recommendations = self._calculate_similarity_recommendations(
                source_papers, candidate_papers
            )

            # 多様性の確保
            diverse_recommendations = self._ensure_diversity(similarity_recommendations)

            # 最終スコアリングとランキング
            final_recommendations = self._final_ranking(
                diverse_recommendations, max_recommendations
            )

            logger.info(f"推薦生成完了: 最終推薦数={len(final_recommendations)}")
            return final_recommendations

        except Exception as e:
            logger.error(f"推薦生成エラー: {e}")
            return []

    async def _expand_search_candidates(
        self, source_papers: List[Paper]
    ) -> List[Paper]:
        """拡張検索による候補論文収集"""
        candidate_papers = []

        # キーワード拡張検索
        keyword_candidates = await self._keyword_expansion_search(source_papers)
        candidate_papers.extend(keyword_candidates)

        # 著者ベース検索
        author_candidates = await self._author_based_search(source_papers)
        candidate_papers.extend(author_candidates)

        # 重複除去
        unique_candidates = self._remove_duplicates(candidate_papers, source_papers)

        return unique_candidates

    async def _keyword_expansion_search(
        self, source_papers: List[Paper]
    ) -> List[Paper]:
        """キーワード拡張検索"""
        # 重要キーワードを抽出
        important_keywords = self._extract_important_keywords(source_papers)

        if not important_keywords:
            return []

        # 上位キーワードで検索
        search_queries = []
        for keyword, score in important_keywords[:5]:  # 上位5キーワード
            if len(keyword) > 3:  # 短すぎるキーワードを除外
                search_queries.append(keyword)

        # 並列検索実行
        all_results = []
        for query in search_queries[:3]:  # API制限を考慮して3つまで
            try:
                results = await self.search_service.search_papers(query, max_results=5)
                all_results.extend(results)
                logger.debug(f"キーワード '{query}' で {len(results)} 件取得")
            except Exception as e:
                logger.error(f"キーワード検索エラー '{query}': {e}")

        return all_results

    async def _author_based_search(self, source_papers: List[Paper]) -> List[Paper]:
        """著者ベース検索"""
        # 著者別の重要度計算
        author_importance = self._calculate_author_importance(source_papers)

        if not author_importance:
            return []

        all_results = []
        for author_name, importance in author_importance[:3]:  # 上位3著者
            try:
                # 著者名で検索
                query = f'author:"{author_name}"'
                results = await self.search_service.search_papers(query, max_results=3)
                all_results.extend(results)
                logger.debug(f"著者 '{author_name}' で {len(results)} 件取得")
            except Exception as e:
                logger.error(f"著者検索エラー '{author_name}': {e}")

        return all_results

    def _extract_important_keywords(
        self, papers: List[Paper]
    ) -> List[Tuple[str, float]]:
        """重要キーワードの抽出"""
        keyword_scores = defaultdict(float)

        for paper in papers:
            # タイトルからキーワード抽出（高重み）
            title_keywords = self._extract_keywords_from_text(
                paper.title or "", weight=3.0
            )
            for keyword, score in title_keywords.items():
                keyword_scores[keyword] += score

            # 概要からキーワード抽出（中重み）
            abstract_keywords = self._extract_keywords_from_text(
                paper.abstract or "", weight=2.0
            )
            for keyword, score in abstract_keywords.items():
                keyword_scores[keyword] += score

            # 既存キーワード（高重み）
            if paper.keywords:
                for keyword in paper.keywords:
                    keyword_scores[keyword.lower()] += 2.5

        # スコア順でソート
        sorted_keywords = sorted(
            keyword_scores.items(), key=lambda x: x[1], reverse=True
        )

        # フィルタリング（一般的すぎるキーワードを除外）
        filtered_keywords = []
        common_words = {
            "research",
            "study",
            "analysis",
            "method",
            "approach",
            "paper",
            "article",
            "review",
        }

        for keyword, score in sorted_keywords:
            if len(keyword) > 3 and keyword not in common_words and score > 1.0:
                filtered_keywords.append((keyword, score))

        return filtered_keywords[:20]  # 上位20キーワード

    def _extract_keywords_from_text(
        self, text: str, weight: float = 1.0
    ) -> Dict[str, float]:
        """テキストからキーワードを抽出"""
        if not text:
            return {}

        # テキスト正規化
        text = re.sub(r"[^\w\s]", " ", text.lower())
        words = text.split()

        # ストップワード除去
        stop_words = self.similarity_engine.stop_words
        words = [word for word in words if word not in stop_words and len(word) > 2]

        # N-gram生成（1-gram, 2-gram）
        keywords = {}

        # 1-gram
        for word in words:
            keywords[word] = keywords.get(word, 0) + weight

        # 2-gram (重要な専門用語をキャッチ)
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i + 1]}"
            keywords[bigram] = keywords.get(bigram, 0) + weight * 1.5

        return keywords

    def _calculate_author_importance(
        self, papers: List[Paper]
    ) -> List[Tuple[str, float]]:
        """著者の重要度計算"""
        author_scores = defaultdict(float)

        for paper in papers:
            if not paper.authors:
                continue

            # 引用数による重み
            citation_weight = 1.0 + (paper.citation_count or 0) / 1000.0

            for author in paper.authors:
                if author.name:
                    author_scores[author.name] += citation_weight

        # スコア順でソート
        sorted_authors = sorted(author_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_authors[:10]  # 上位10著者

    def _calculate_similarity_recommendations(
        self, source_papers: List[Paper], candidate_papers: List[Paper]
    ) -> List[Tuple[Paper, float, str]]:
        """類似度ベース推薦計算"""
        recommendations = []

        for candidate in candidate_papers:
            best_similarity = 0.0
            best_source = None

            # 各基論文との最大類似度を計算
            for source in source_papers:
                similarity = self.similarity_engine.calculate_similarity(
                    source, candidate
                )
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_source = source

            # 閾値以上の類似度の場合、推薦候補に追加
            if best_similarity >= self.min_similarity_threshold:
                reason = self._generate_recommendation_reason(
                    candidate, best_source, best_similarity
                )
                recommendations.append((candidate, best_similarity, reason))

        return recommendations

    def _generate_recommendation_reason(
        self, paper: Paper, source_paper: Paper, similarity: float
    ) -> str:
        """推薦理由の生成"""
        reasons = []

        # 類似度レベル
        if similarity > 0.7:
            reasons.append("高い内容関連性")
        elif similarity > 0.4:
            reasons.append("内容関連性")
        else:
            reasons.append("テーマ関連性")

        # 著者関連性
        if source_paper.authors and paper.authors:
            source_authors = {a.name.lower() for a in source_paper.authors if a.name}
            paper_authors = {a.name.lower() for a in paper.authors if a.name}
            if source_authors.intersection(paper_authors):
                reasons.append("共通著者")

        # 引用数による信頼性
        if paper.citation_count and paper.citation_count > 50:
            reasons.append("高被引用")
        elif paper.citation_count and paper.citation_count > 10:
            reasons.append("被引用")

        # 新しさ
        if paper.publication_year and paper.publication_year >= 2020:
            reasons.append("最新研究")

        return " | ".join(reasons)

    def _ensure_diversity(
        self, recommendations: List[Tuple[Paper, float, str]]
    ) -> List[Tuple[Paper, float, str]]:
        """推薦の多様性を確保"""
        if not recommendations:
            return []

        # 著者別グルーピング
        author_groups = defaultdict(list)
        no_author_papers = []

        for paper, similarity, reason in recommendations:
            if paper.authors:
                # 最初の著者で分類
                first_author = (
                    paper.authors[0].name if paper.authors[0].name else "unknown"
                )
                author_groups[first_author].append((paper, similarity, reason))
            else:
                no_author_papers.append((paper, similarity, reason))

        # 各著者グループから最大数を選択
        diverse_recommendations = []

        for author, papers in author_groups.items():
            # 類似度でソート
            papers.sort(key=lambda x: x[1], reverse=True)
            # 最大制限数まで選択
            diverse_recommendations.extend(papers[: self.max_papers_per_author])

        # 著者なし論文も追加
        diverse_recommendations.extend(no_author_papers)

        return diverse_recommendations

    def _final_ranking(
        self, recommendations: List[Tuple[Paper, float, str]], max_count: int
    ) -> List[Tuple[Paper, float, str]]:
        """最終ランキング"""
        if not recommendations:
            return []

        # 論文品質スコア計算
        scored_recommendations = []

        for paper, similarity, reason in recommendations:
            quality_score = self._calculate_quality_score(paper)
            final_score = similarity * 0.7 + quality_score * 0.3
            scored_recommendations.append((paper, final_score, reason))

        # 最終スコアでソート
        scored_recommendations.sort(key=lambda x: x[1], reverse=True)

        return scored_recommendations[:max_count]

    def _calculate_quality_score(self, paper: Paper) -> float:
        """論文品質スコア計算"""
        score = 0.0

        # 引用数による評価
        if paper.citation_count:
            # 対数スケールで正規化
            import math

            score += min(math.log(paper.citation_count + 1) / 10, 0.5)

        # 年度による評価（新しい方が良い）
        if paper.publication_year:
            current_year = 2025
            year_score = max(0, (paper.publication_year - 1990) / (current_year - 1990))
            score += year_score * 0.3

        # 概要の有無
        if paper.abstract and len(paper.abstract) > 100:
            score += 0.1

        # DOIの有無（信頼性指標）
        if paper.doi:
            score += 0.1

        return min(score, 1.0)

    def _remove_duplicates(
        self, candidates: List[Paper], source_papers: List[Paper]
    ) -> List[Paper]:
        """重複除去"""
        seen_titles = set()
        seen_dois = set()
        unique_papers = []

        # 既存論文のタイトルとDOIを記録
        for paper in source_papers:
            if paper.title:
                seen_titles.add(paper.title.lower().strip())
            if paper.doi:
                seen_dois.add(paper.doi.lower().strip())

        for paper in candidates:
            is_duplicate = False

            # DOIチェック
            if paper.doi and paper.doi.lower().strip() in seen_dois:
                is_duplicate = True

            # タイトルチェック
            if paper.title:
                title_norm = paper.title.lower().strip()
                if title_norm in seen_titles:
                    is_duplicate = True

                # 非常に似たタイトルもチェック
                for seen_title in seen_titles:
                    if self._titles_very_similar(title_norm, seen_title):
                        is_duplicate = True
                        break

            if not is_duplicate:
                unique_papers.append(paper)
                if paper.title:
                    seen_titles.add(paper.title.lower().strip())
                if paper.doi:
                    seen_dois.add(paper.doi.lower().strip())

        return unique_papers

    def _titles_very_similar(self, title1: str, title2: str) -> bool:
        """タイトルが非常に似ているかチェック"""
        if not title1 or not title2:
            return False

        # 単語レベルでの類似度チェック
        words1 = set(re.findall(r"\w+", title1))
        words2 = set(re.findall(r"\w+", title2))

        if not words1 or not words2:
            return False

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        # 80%以上の重複で類似と判定
        return (intersection / union) > 0.8 if union > 0 else False


# シングルトンインスタンス
_recommendation_engine = None


def get_recommendation_engine() -> RecommendationEngine:
    """RecommendationEngineのシングルトンインスタンスを取得"""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = RecommendationEngine()
    return _recommendation_engine
