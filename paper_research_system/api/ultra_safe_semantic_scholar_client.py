"""
Ultra-Safe Semantic Scholar API client for Academic Paper Research Assistant
絶対安全 Semantic Scholar API クライアント（3秒間隔 + リトライ機能）
"""

from config.settings import settings
from core.paper_model import Paper, Author
import httpx
import asyncio
import time
from typing import List, Optional, Dict, Any
import logging
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))


logger = logging.getLogger(__name__)


class UltraSafeSemanticScholarClient:
    """絶対安全 Semantic Scholar API クライアント"""

    def __init__(self):
        self.base_url = settings.semantic_scholar_base_url
        self.api_key = settings.semantic_scholar_api_key
        self.timeout = settings.request_timeout
        self.last_request_time = 0.0
        self.rate_limit_delay = 3.0  # 3秒 - 絶対に安全
        self.max_retries = 2

    async def _ultra_safe_wait(self):
        """絶対安全な待機"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - elapsed
            logger.info(f"Semantic Scholar 絶対安全待機: {wait_time:.2f}秒")
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()

    async def search_papers(self, query: str,
                            max_results: int = None) -> List[Paper]:
        """
        論文検索（絶対安全版）

        Args:
            query: 検索クエリ
            max_results: 最大結果数

        Returns:
            論文リスト
        """
        if max_results is None:
            max_results = 2  # 最小限に制限

        # リトライ付きで実行
        for attempt in range(self.max_retries + 1):
            try:
                return await self._single_search_attempt(query, max_results, attempt)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    if attempt < self.max_retries:
                        wait_time = (attempt + 1) * 5.0  # 5秒、10秒と増加
                        logger.warning(
                            f"レート制限検出 - {wait_time}秒待機後リトライ ({attempt + 1}/{self.max_retries})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error("レート制限: 全リトライ失敗 - Semantic Scholar スキップ")
                        return []
                else:
                    logger.error(f"Semantic Scholar HTTPエラー: {e}")
                    return []
            except Exception as e:
                logger.error(f"Semantic Scholar 予期しないエラー: {e}")
                return []

        return []

    async def _single_search_attempt(
            self, query: str, max_results: int, attempt: int) -> List[Paper]:
        """単一検索試行"""
        # 絶対安全な待機
        await self._ultra_safe_wait()

        # ヘッダー設定
        headers = {
            "User-Agent": "Academic-Paper-Research-Assistant/1.0 (Safe-Mode)",
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key

        async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
            # Semantic Scholarの検索エンドポイント
            url = f"{self.base_url}/paper/search"
            params = {
                "query": query,
                "limit": max_results,
                "sort": "citationCount:desc",  # 引用数順
                "fields": "paperId,title,abstract,authors,venue,year,citationCount,openAccessPdf,externalIds"
            }

            logger.info(
                f"Semantic Scholar検索実行 (絶対安全モード - 試行{attempt + 1}): {query}")
            response = await client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            papers = []

            for paper_data in data.get("data", []):
                paper = self._parse_work_ultra_safe(paper_data, query)
                if paper:
                    papers.append(paper)

            logger.info(f"Semantic Scholar (絶対安全): {len(papers)}件の論文を取得")
            return papers

    def _parse_work_ultra_safe(
            self, paper_data: Dict[str, Any], query: str) -> Optional[Paper]:
        """Semantic Scholarのpaper情報をPaperオブジェクトに変換（絶対安全版）"""
        try:
            # 基本情報（厳重なNone チェック）
            if not paper_data or not isinstance(paper_data, dict):
                return None

            title = paper_data.get("title")
            if not title or not isinstance(
                    title, str) or len(title.strip()) == 0:
                return None  # タイトルなしは除外

            publication_year = paper_data.get("year")
            if publication_year and not isinstance(publication_year, int):
                publication_year = None

            citation_count = paper_data.get("citationCount", 0)
            if not isinstance(citation_count, int):
                citation_count = 0

            # DOI
            external_ids = paper_data.get("externalIds")
            doi = None
            if external_ids and isinstance(external_ids, dict):
                doi_value = external_ids.get("DOI")
                if doi_value and isinstance(doi_value, str):
                    doi = f"https://doi.org/{doi_value}"

            # URL
            url = doi
            open_access = paper_data.get("openAccessPdf")
            if open_access and isinstance(open_access, dict):
                oa_url = open_access.get("url")
                if oa_url and isinstance(oa_url, str):
                    url = oa_url

            # 著者情報（厳重なチェック）
            authors = []
            authors_data = paper_data.get("authors", [])
            if authors_data and isinstance(authors_data, list):
                for author_info in authors_data:
                    if not author_info or not isinstance(author_info, dict):
                        continue
                    author_name = author_info.get("name")
                    if author_name and isinstance(author_name, str):
                        authors.append(Author(
                            name=author_name,
                            institution=None,
                            orcid=None
                        ))

            # 所属機関リスト（基本検索では取得困難）
            institutions = []

            # ジャーナル情報
            journal = paper_data.get("venue")
            if journal and not isinstance(journal, str):
                journal = None

            # 概要（厳重なチェック）
            abstract = paper_data.get("abstract")
            if abstract and not isinstance(abstract, str):
                abstract = None

            # 関連性スコア計算
            relevance_score = self._calculate_relevance_score_ultra_safe(
                paper_data, query)

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
                confidence_score=0.85,
                relevance_score=relevance_score
            )

        except Exception as e:
            logger.error(f"Semantic Scholar論文パース失敗 (絶対安全版): {e}")
            return None

    def _calculate_relevance_score_ultra_safe(
            self, paper_data: Dict[str, Any], query: str) -> float:
        """論文の関連性スコアを計算（絶対安全版）"""
        try:
            score = 0.0

            # タイトルマッチング
            title = paper_data.get("title") or ""
            if isinstance(title, str):
                title_lower = title.lower()
                query_words = query.lower().split()

                for word in query_words:
                    if word in title_lower:
                        score += 2.0

            # 概要マッチング
            abstract = paper_data.get("abstract") or ""
            if isinstance(abstract, str):
                abstract_lower = abstract.lower()
                query_words = query.lower().split()
                abstract_matches = sum(
                    1 for word in query_words if word in abstract_lower)
                score += min(abstract_matches * 0.5, 2.0)  # 最大2点

            # 引用数による重み付け
            citation_count = paper_data.get("citationCount", 0)
            if isinstance(citation_count, int) and citation_count > 0:
                if citation_count > 1000:
                    score += 2.0
                elif citation_count > 100:
                    score += 1.0
                elif citation_count > 10:
                    score += 0.5

            # 発表年による重み付け
            year = paper_data.get("year")
            if isinstance(year, int):
                if year >= 2015:
                    score += 1.0
                elif year >= 2005:
                    score += 0.5

            return min(score, 10.0)  # 最大10点

        except Exception:
            # エラーが起きても最低限のスコアを返す
            return 1.0

# 同期版の関数も提供


def search_papers_sync(query: str, max_results: int = None) -> List[Paper]:
    """同期版の論文検索"""
    client = UltraSafeSemanticScholarClient()
    return asyncio.run(client.search_papers(query, max_results))
