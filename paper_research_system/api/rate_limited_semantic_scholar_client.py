"""
Rate-Limited Semantic Scholar API client for Academic Paper Research Assistant
レート制限対応 Semantic Scholar API クライアント（1リクエスト/秒）
"""

from ..config.settings import settings
from ..core.paper_model import Paper, Author
import httpx
import asyncio
import time
from typing import List, Optional, Dict, Any
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


logger = logging.getLogger(__name__)


class RateLimitedSemanticScholarClient:
    """レート制限対応 Semantic Scholar API クライアント"""

    def __init__(self):
        self.base_url = settings.semantic_scholar_base_url
        self.api_key = settings.semantic_scholar_api_key
        self.timeout = settings.request_timeout
        self.last_request_time = 0.0
        self.rate_limit_delay = 2.0  # 2秒 - 絶対安全な間隔

    async def _rate_limit_wait(self):
        """レート制限のための待機"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - elapsed
            logger.info(f"Semantic Scholar レート制限待機: {wait_time:.2f}秒")
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()

    async def search_papers(self, query: str, max_results: int = None) -> List[Paper]:
        """
        論文検索（レート制限対応）

        Args:
            query: 検索クエリ
            max_results: 最大結果数

        Returns:
            論文リスト
        """
        if max_results is None:
            max_results = min(
                settings.max_results_per_api, 2
            )  # レート制限考慮でさらに少なめ

        try:
            # レート制限待機
            await self._rate_limit_wait()

            # ヘッダー設定
            headers = {
                "User-Agent": "Academic-Paper-Research-Assistant/1.0",
            }
            if self.api_key:
                headers["x-api-key"] = self.api_key

            async with httpx.AsyncClient(
                timeout=self.timeout, headers=headers
            ) as client:
                # Semantic Scholarの検索エンドポイント
                url = f"{self.base_url}/paper/search"
                params = {
                    "query": query,
                    "limit": max_results,
                    "sort": "citationCount:desc",  # 引用数順
                    "fields": "paperId,title,abstract,authors,venue,year,citationCount,openAccessPdf,externalIds",
                }

                logger.info(f"Semantic Scholar検索実行 (安全モード): {query}")
                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()
                papers = []

                for paper_data in data.get("data", []):
                    paper = self._parse_work_safe(paper_data, query)
                    if paper:
                        papers.append(paper)

                logger.info(f"Semantic Scholar (安全): {len(papers)}件の論文を取得")
                return papers

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(
                    f"Semantic Scholar レート制限: {e} - 緊急停止（設定に問題あり）"
                )
                return []
            else:
                logger.error(f"Semantic Scholar HTTPエラー: {e}")
                return []
        except Exception as e:
            logger.error(f"Semantic Scholar検索エラー: {e}")
            return []

    def _parse_work_safe(
        self, paper_data: Dict[str, Any], query: str
    ) -> Optional[Paper]:
        """Semantic Scholarのpaper情報をPaperオブジェクトに変換（安全版）"""
        try:
            # 基本情報（None チェック強化）
            title = paper_data.get("title") or ""
            if not title:
                return None  # タイトルなしは除外

            publication_year = paper_data.get("year")
            citation_count = paper_data.get("citationCount", 0)

            # DOI
            external_ids = paper_data.get("externalIds", {}) or {}
            doi = external_ids.get("DOI")
            if doi:
                doi = f"https://doi.org/{doi}"

            # URL
            url = doi
            open_access = paper_data.get("openAccessPdf")
            if open_access and open_access.get("url"):
                url = open_access["url"]

            # 著者情報（None チェック強化）
            authors = []
            authors_data = paper_data.get("authors", []) or []
            for author_info in authors_data:
                if not author_info:
                    continue
                author_name = author_info.get("name") or "Unknown Author"
                authors.append(
                    Author(
                        name=author_name,
                        institution=None,  # 基本検索では取得困難
                        orcid=None,
                    )
                )

            # 所属機関リスト（基本検索では取得困難）
            institutions = []

            # ジャーナル情報
            journal = paper_data.get("venue")

            # 概要（None チェック）
            abstract = paper_data.get("abstract")

            # 関連性スコア計算
            relevance_score = self._calculate_relevance_score_safe(paper_data, query)

            return Paper(
                title=title,
                authors=authors,
                institutions=institutions,
                publication_year=publication_year,
                doi=doi,
                url=url,
                citation_count=citation_count,
                abstract=abstract,
                journal=journal,
                source_api="semantic_scholar",
                confidence_score=0.85,  # Semantic Scholarは高品質
                relevance_score=relevance_score,
            )

        except Exception as e:
            logger.error(f"Semantic Scholar論文パース失敗 (安全版): {e}")
            return None

    def _calculate_relevance_score_safe(
        self, paper_data: Dict[str, Any], query: str
    ) -> float:
        """論文の関連性スコアを計算（安全版）"""
        score = 0.0

        try:
            # タイトルマッチング
            title = (paper_data.get("title") or "").lower()
            query_words = query.lower().split()

            for word in query_words:
                if word in title:
                    score += 2.0

            # 概要マッチング
            abstract = (paper_data.get("abstract") or "").lower()
            abstract_matches = sum(1 for word in query_words if word in abstract)
            score += min(abstract_matches * 0.5, 2.0)  # 最大2点

            # 引用数による重み付け
            citation_count = paper_data.get("citationCount", 0) or 0
            if citation_count > 1000:
                score += 2.0
            elif citation_count > 100:
                score += 1.0
            elif citation_count > 10:
                score += 0.5

            # 発表年による重み付け（新しい論文に加点）
            year = paper_data.get("year")
            if year:
                if year >= 2015:
                    score += 1.0
                elif year >= 2005:
                    score += 0.5
        except Exception:
            # エラーが起きても最低限のスコアを返す
            pass

        return min(score, 10.0)  # 最大10点


# 同期版の関数も提供


def search_papers_sync(query: str, max_results: int = None) -> List[Paper]:
    """同期版の論文検索"""
    client = RateLimitedSemanticScholarClient()
    return asyncio.run(client.search_papers(query, max_results))
