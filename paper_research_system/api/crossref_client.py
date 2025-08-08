"""
CrossRef API client for Academic Paper Research Assistant
CrossRef API クライアント（無料・APIキー不要）
"""

from config.settings import settings
from core.paper_model import Paper, Author, Institution
import httpx
import asyncio
from typing import List, Optional, Dict, Any
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


logger = logging.getLogger(__name__)


class CrossRefClient:
    """CrossRef API クライアント"""

    def __init__(self):
        self.base_url = settings.crossref_base_url
        self.timeout = settings.request_timeout

    async def search_papers(self, query: str, max_results: int = None) -> List[Paper]:
        """
        論文検索

        Args:
            query: 検索クエリ
            max_results: 最大結果数

        Returns:
            論文リスト
        """
        if max_results is None:
            max_results = settings.max_results_per_api

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # CrossRefの検索エンドポイント
                params = {
                    "query": query,
                    "rows": max_results,
                    "sort": "score",  # 関連性順
                    "filter": "type:journal-article,from-pub-date:1990",  # 学術論文、1990年以降
                }

                logger.info(f"CrossRef検索実行: {query}")
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()

                data = response.json()
                papers = []

                for item in data.get("message", {}).get("items", []):
                    paper = self._parse_work(item, query)
                    if paper:
                        papers.append(paper)

                logger.info(f"CrossRef: {len(papers)}件の論文を取得")
                return papers

        except Exception as e:
            logger.error(f"CrossRef検索エラー: {e}")
            return []

    def _parse_work(self, item: Dict[str, Any], query: str) -> Optional[Paper]:
        """CrossRefのitem情報をPaperオブジェクトに変換"""
        try:
            # 基本情報
            title_parts = item.get("title", [])
            title = title_parts[0] if title_parts else ""

            # 発表年
            published = item.get("published-print") or item.get("published-online", {})
            publication_year = None
            if published.get("date-parts"):
                publication_year = published["date-parts"][0][0]

            # DOI
            doi = item.get("DOI")
            if doi:
                doi = f"https://doi.org/{doi}"

            # 引用数（CrossRefには直接引用数情報がない）
            citation_count = 0

            # URL
            url = doi or item.get("URL")

            # 著者情報
            authors = []
            for author_info in item.get("author", []):
                first_name = author_info.get("given", "")
                last_name = author_info.get("family", "")
                full_name = f"{first_name} {last_name}".strip()

                # 所属機関
                affiliation = None
                affiliations = author_info.get("affiliation", [])
                if affiliations:
                    affiliation = affiliations[0].get("name")

                authors.append(
                    Author(
                        name=full_name,
                        institution=affiliation,
                        orcid=author_info.get("ORCID"),
                    )
                )

            # 所属機関リスト（著者の所属から抽出）
            institutions = []
            for author_info in item.get("author", []):
                for affiliation in author_info.get("affiliation", []):
                    inst_name = affiliation.get("name")
                    if inst_name:
                        institutions.append(
                            Institution(
                                name=inst_name,
                                country=None,  # CrossRefには国情報がない場合が多い
                                type=None,
                            )
                        )

            # 重複除去
            institutions = list({inst.name: inst for inst in institutions}.values())

            # ジャーナル情報
            journal = None
            container_titles = item.get("container-title", [])
            if container_titles:
                journal = container_titles[0]

            # 概要（CrossRefには通常abstractがない）
            abstract = item.get("abstract")

            # 関連性スコア計算
            relevance_score = self._calculate_relevance_score(item, query)

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
                source_api="crossref",
                confidence_score=0.8,  # CrossRefは信頼性が高い
                relevance_score=relevance_score,
            )

        except Exception as e:
            logger.error(f"CrossRef論文パース失敗: {e}")
            return None

    def _calculate_relevance_score(self, item: Dict[str, Any], query: str) -> float:
        """論文の関連性スコアを計算"""
        score = 0.0

        # タイトルマッチング
        title_parts = item.get("title", [])
        title = title_parts[0].lower() if title_parts else ""
        query_words = query.lower().split()

        for word in query_words:
            if word in title:
                score += 2.0

        # CrossRefのスコア（関連性）
        crossref_score = item.get("score", 0)
        score += min(crossref_score / 100, 3.0)  # 最大3点に正規化

        # 発表年による重み付け（新しい論文に加点）
        published = item.get("published-print") or item.get("published-online", {})
        if published.get("date-parts"):
            year = published["date-parts"][0][0]
            if year >= 2010:
                score += 1.0
            elif year >= 2000:
                score += 0.5

        return min(score, 10.0)  # 最大10点


# 同期版の関数も提供


def search_papers_sync(query: str, max_results: int = None) -> List[Paper]:
    """同期版の論文検索"""
    client = CrossRefClient()
    return asyncio.run(client.search_papers(query, max_results))
