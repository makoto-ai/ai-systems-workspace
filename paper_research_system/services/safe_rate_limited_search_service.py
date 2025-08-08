"""
Safe Rate-Limited Integrated Search Service
安全なレート制限対応統合検索サービス
"""

from core.paper_model import Paper
from api.ultra_safe_semantic_scholar_client import UltraSafeSemanticScholarClient
from api.crossref_client import CrossRefClient
from api.openalex_client import OpenAlexClient
import asyncio
from typing import List, Dict, Optional
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


logger = logging.getLogger(__name__)


class SafeRateLimitedSearchService:
    """安全なレート制限対応統合検索サービス"""

    def __init__(self):
        self.openalex = OpenAlexClient()
        self.crossref = CrossRefClient()
        self.semantic_scholar = UltraSafeSemanticScholarClient()

    async def search_papers(self, query: str, max_results: int = 10) -> List[Paper]:
        """
        安全な統合検索（レート制限対応）

        Args:
            query: 検索クエリ
            max_results: 最大結果数

        Returns:
            統合された論文リスト
        """
        logger.info(
            f"安全な統合検索開始 (レート制限対応): '{query}' (最大{max_results}件)"
        )

        # 各APIに割り当てる結果数
        per_api_results = max(max_results // 3, 2)

        try:
            # 1. 並列実行可能なAPI（OpenAlex + CrossRef）
            parallel_tasks = [
                self.openalex.search_papers(query, per_api_results),
                self.crossref.search_papers(query, per_api_results),
            ]

            parallel_results = await asyncio.gather(
                *parallel_tasks, return_exceptions=True
            )

            # 2. Semantic Scholar（順次実行、レート制限対応）
            semantic_result = await self.semantic_scholar.search_papers(
                query, per_api_results
            )

            # 結果をマージ
            all_papers = []
            api_names = ["OpenAlex", "CrossRef", "Semantic Scholar"]
            api_results = [*parallel_results, semantic_result]

            for i, result in enumerate(api_results):
                if isinstance(result, Exception):
                    logger.error(f"{api_names[i]}検索エラー: {result}")
                    continue

                papers = result if isinstance(result, list) else []
                logger.info(f"{api_names[i]}: {len(papers)}件取得")
                all_papers.extend(papers)

            # 重複除去とランキング
            merged_papers = self._merge_and_rank_papers(all_papers, query)

            # 結果数を制限
            final_papers = merged_papers[:max_results]

            logger.info(
                f"安全な統合検索完了: 計{
                    len(all_papers)}件 → 重複除去後{
                    len(merged_papers)}件 → 最終{
                    len(final_papers)}件"
            )

            return final_papers

        except Exception as e:
            logger.error(f"安全な統合検索エラー: {e}")
            return []

    def _merge_and_rank_papers(self, papers: List[Paper], query: str) -> List[Paper]:
        """論文リストをマージ・重複除去・ランキング"""

        # 1. DOIベースでの重複除去
        doi_groups = {}
        no_doi_papers = []

        for paper in papers:
            if paper.doi:
                doi_key = paper.doi.lower().strip()
                if doi_key not in doi_groups:
                    doi_groups[doi_key] = []
                doi_groups[doi_key].append(paper)
            else:
                no_doi_papers.append(paper)

        # 2. 同じDOIの論文から最良のものを選択
        merged_papers = []

        for doi, paper_group in doi_groups.items():
            best_paper = self._select_best_paper(paper_group)
            merged_papers.append(best_paper)

        # 3. DOIのない論文はタイトルベースで重複チェック
        title_groups = {}
        for paper in no_doi_papers:
            title_key = self._normalize_title(paper.title)
            if title_key not in title_groups:
                title_groups[title_key] = []
            title_groups[title_key].append(paper)

        for title, paper_group in title_groups.items():
            if len(title) > 10:  # 短すぎるタイトルは除外
                best_paper = self._select_best_paper(paper_group)
                merged_papers.append(best_paper)

        # 4. 総合スコアでランキング
        for paper in merged_papers:
            paper.total_score = self._calculate_total_score(paper, query)

        # スコア順でソート
        merged_papers.sort(key=lambda p: p.total_score, reverse=True)

        return merged_papers

    def _select_best_paper(self, papers: List[Paper]) -> Paper:
        """同じ論文の複数バージョンから最良のものを選択"""
        # 1. 概要がある論文を優先
        papers_with_abstract = [p for p in papers if p.abstract]
        if papers_with_abstract:
            papers = papers_with_abstract

        # 2. 引用数が多い論文を優先
        papers.sort(key=lambda p: p.citation_count or 0, reverse=True)

        # 3. 信頼度が高いAPIソースを優先
        api_priority = {"semantic_scholar": 3, "openalex": 2, "crossref": 1}
        papers.sort(key=lambda p: api_priority.get(p.source_api, 0), reverse=True)

        return papers[0]

    def _normalize_title(self, title: str) -> str:
        """タイトルを正規化"""
        import re

        # 大文字小文字統一、記号除去、複数空白を単一空白に
        normalized = re.sub(r"[^\w\s]", "", title.lower())
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _calculate_total_score(self, paper: Paper, query: str) -> float:
        """総合スコアを計算"""
        score = 0.0

        # 1. 各APIの関連性スコア
        if paper.relevance_score:
            score += paper.relevance_score * 2

        # 2. 引用数スコア（対数スケール）
        if paper.citation_count:
            import math

            citation_score = math.log10(paper.citation_count + 1) * 2
            score += min(citation_score, 8.0)  # 最大8点

        # 3. 概要の有無
        if paper.abstract:
            score += 3.0

        # 4. 発表年（新しさ）
        if paper.publication_year:
            if paper.publication_year >= 2015:
                score += 2.0
            elif paper.publication_year >= 2005:
                score += 1.0
            elif paper.publication_year >= 1995:
                score += 0.5

        # 5. APIソースの信頼度
        api_bonus = {
            "semantic_scholar": 1.5,  # 高品質なメタデータ
            "openalex": 1.2,  # 幅広いカバレッジ
            "crossref": 1.0,  # 基本的なメタデータ
        }
        score += api_bonus.get(paper.source_api, 0)

        return score


# サービスインスタンス作成用関数


def get_safe_rate_limited_search_service() -> SafeRateLimitedSearchService:
    """SafeRateLimitedSearchService インスタンスを取得"""
    return SafeRateLimitedSearchService()
