"""
OpenAlex API client for Academic Paper Research Assistant
OpenAlex API クライアント（無料・APIキー不要）
"""

from services.query_translator import get_query_translator
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


class OpenAlexClient:
    """OpenAlex API クライアント"""

    def __init__(self):
        self.base_url = settings.openalex_base_url
        self.timeout = settings.request_timeout
        self.query_translator = get_query_translator()

    async def search_papers(self, query: str,
                            max_results: int = None) -> List[Paper]:
        """
        論文検索（改良版）

        Args:
            query: 検索クエリ（日本語対応）
            max_results: 最大結果数

        Returns:
            論文リスト
        """
        if max_results is None:
            max_results = settings.max_results_per_api

        # 1. 日本語クエリの場合は英語に変換
        search_queries = self._prepare_search_queries(query)

        all_papers = []

        try:
            # User-Agentヘッダーを設定（403エラー回避）
            headers = {
                "User-Agent": "Academic-Paper-Research-Assistant/1.0 (https://github.com/research-assistant)",
                "Accept": "application/json"
            }
            async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
                # 複数クエリで検索して結果をマージ
                for search_query in search_queries[:3]:  # 上位3クエリのみ
                    logger.info(f"検索実行中: '{search_query}'")
                    # per-pageが0にならないよう最小値を保証
                    per_query_results = max(
                        1, max_results // len(search_queries[:3]))
                    papers = await self._search_single_query(client, search_query, per_query_results)
                    logger.info(f"'{search_query}' → {len(papers)}件取得")
                    all_papers.extend(papers)

                # 重複除去（DOIベース）
                seen_dois = set()
                unique_papers = []
                for paper in all_papers:
                    paper_id = paper.doi if paper.doi else paper.title
                    if paper_id not in seen_dois:
                        seen_dois.add(paper_id)
                        unique_papers.append(paper)

                # 引用数順でソート
                unique_papers.sort(
                    key=lambda p: p.citation_count or 0, reverse=True)

                # 最大結果数に制限
                result_papers = unique_papers[:max_results]

                logger.info(
                    f"OpenAlex: {len(result_papers)}件の論文を取得 (検索クエリ数: {len(search_queries[:3])})")
                return result_papers

        except Exception as e:
            logger.error(f"OpenAlex検索エラー: {e}")
            return []

    def _prepare_search_queries(self, original_query: str) -> List[str]:
        """検索クエリを準備"""
        # 日本語が含まれているかチェック
        if self._contains_japanese(original_query):
            # 日本語→英語変換
            translated_queries = self.query_translator.translate_japanese_query(
                original_query)
            logger.info(
                f"日本語クエリを変換: '{original_query}' → {translated_queries[:3]}")
            return translated_queries
        else:
            # 英語クエリの場合は拡張
            enhanced_query = self.query_translator.enhance_query_for_sales_psychology(
                original_query)
            return [enhanced_query, original_query]

    def _contains_japanese(self, text: str) -> bool:
        """日本語が含まれているかチェック"""
        import re
        return bool(re.search(r'[ぁ-んァ-ヶ一-龯]', text))

    async def _search_single_query(
            self, client: httpx.AsyncClient, query: str, max_results: int) -> List[Paper]:
        """単一クエリでの検索"""
        url = f"{self.base_url}/works"

        # 営業・心理学分野に特化したフィルタ（改良版）
        filters = [
            "type:article",  # 論文のみ
            "publication_year:>1990"  # 1990年以降の研究
        ]

        # 営業・心理学に特化した概念フィルタ
        sales_psychology_concepts = [
            "C138885662",   # Psychology
            "C2522767166",  # Social psychology
            "C144024400",   # Organizational behavior
            "C41008148",    # Marketing
            "C15744967",    # Consumer behaviour
            "C162324750",   # Economics (behavioral economics)
            "C74844659",    # Business administration
            "C192562407",   # Management
            "C141071460",   # Communication
            "C86803240"     # Personality psychology
        ]

        # より柔軟な概念フィルタ（OR条件）
        concept_filter = f"concepts.id:{'|'.join(sales_psychology_concepts)}"
        filters.append(concept_filter)

        params = {
            "search": query,
            "per-page": max_results,
            "sort": "cited_by_count:desc",
            "filter": ",".join(filters),
            "select": "id,title,display_name,publication_year,doi,cited_by_count,authorships,primary_location,abstract_inverted_index,concepts"
        }

        logger.info(f"OpenAlex詳細検索: {query}")
        logger.info(f"検索パラメータ: {params}")

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logger.error(f"OpenAlex 403エラー: {e.response.text}")
                # 簡単なフォールバック検索
                fallback_params = {"search": query, "per-page": max_results}
                response = await client.get(url, params=fallback_params)
                response.raise_for_status()
            else:
                raise

        data = response.json()
        papers = []

        for work in data.get("results", []):
            paper = self._parse_work_enhanced(work, query)
            if paper:
                papers.append(paper)

        return papers

    def _parse_work_enhanced(
            self, work: Dict[str, Any], query: str) -> Optional[Paper]:
        """OpenAlexのwork情報をPaperオブジェクトに変換（改良版）"""
        try:
            # 基本情報
            title = work.get("title", "")
            publication_year = work.get("publication_year")
            doi = work.get("doi")
            citation_count = work.get("cited_by_count", 0)

            # URL生成
            url = work.get("doi") if work.get("doi") else work.get("id")

            # 著者情報
            authors = []
            for authorship in work.get("authorships", []):
                author_info = authorship.get("author", {})
                author_name = author_info.get("display_name", "")

                # 所属機関
                institution_name = None
                for institution in authorship.get("institutions", []):
                    if institution.get("display_name"):
                        institution_name = institution.get("display_name")
                        break

                authors.append(Author(
                    name=author_name,
                    institution=institution_name,
                    orcid=author_info.get("orcid")
                ))

            # 所属機関リスト
            institutions = []
            for authorship in work.get("authorships", []):
                for institution in authorship.get("institutions", []):
                    inst_name = institution.get("display_name")
                    if inst_name:
                        institutions.append(Institution(
                            name=inst_name,
                            country=institution.get("country_code"),
                            type=institution.get("type")
                        ))

            # 重複除去
            institutions = list(
                {inst.name: inst for inst in institutions}.values())

            # ジャーナル情報
            journal = None
            venue = work.get("primary_location", {})
            if venue and venue.get("source"):
                journal = venue["source"].get("display_name")

            # 概要（inverted indexから復元）
            abstract = self._reconstruct_abstract(
                work.get("abstract_inverted_index"))

            # 関連性スコア計算
            relevance_score = self._calculate_relevance_score(work, query)

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
                source_api="openalex",
                confidence_score=0.9,
                relevance_score=relevance_score
            )

        except Exception as e:
            logger.error(f"OpenAlex論文パース失敗: {e}")
            return None

    def _reconstruct_abstract(
            self, inverted_index: Optional[Dict]) -> Optional[str]:
        """inverted indexから概要を復元"""
        if not inverted_index:
            return None

        try:
            # 位置とキーワードのマッピング
            position_word_map = {}
            for word, positions in inverted_index.items():
                for pos in positions:
                    position_word_map[pos] = word

            # 位置順にソートして文章を復元
            sorted_positions = sorted(position_word_map.keys())
            abstract_words = [position_word_map[pos]
                              for pos in sorted_positions]

            return " ".join(abstract_words)
        except Exception:
            return None

    def _calculate_relevance_score(
            self, work: Dict[str, Any], query: str) -> float:
        """論文の関連性スコアを計算"""
        score = 0.0

        # タイトルマッチング
        title = work.get("title", "").lower()
        query_words = query.lower().split()

        for word in query_words:
            if word in title:
                score += 2.0

        # 概念マッチング
        concepts = work.get("concepts", [])
        sales_psychology_concepts = [
            "psychology", "social psychology", "marketing",
            "organizational behavior", "consumer behavior",
            "business", "economics", "decision making"
        ]

        for concept in concepts:
            concept_name = concept.get("display_name", "").lower()
            if any(target in concept_name for target in sales_psychology_concepts):
                score += concept.get("score", 0) * 1.5

        # 引用数による重み付け
        citation_count = work.get("cited_by_count", 0)
        if citation_count > 1000:
            score += 1.0
        elif citation_count > 100:
            score += 0.5

        return min(score, 10.0)  # 最大10点

    def _parse_work(self, work: Dict[str, Any]) -> Optional[Paper]:
        """OpenAlexのwork情報をPaperオブジェクトに変換"""
        try:
            # 基本情報
            title = work.get("title", "")
            publication_year = work.get("publication_year")
            doi = work.get("doi")
            citation_count = work.get("cited_by_count", 0)

            # URL生成
            url = work.get("doi") if work.get("doi") else work.get("id")

            # 著者情報
            authors = []
            for authorship in work.get("authorships", []):
                author_info = authorship.get("author", {})
                author_name = author_info.get("display_name", "")

                # 所属機関
                institution_name = None
                for institution in authorship.get("institutions", []):
                    if institution.get("display_name"):
                        institution_name = institution.get("display_name")
                        break

                authors.append(Author(
                    name=author_name,
                    institution=institution_name,
                    orcid=author_info.get("orcid")
                ))

            # 所属機関リスト
            institutions = []
            for authorship in work.get("authorships", []):
                for institution in authorship.get("institutions", []):
                    inst_name = institution.get("display_name")
                    if inst_name:
                        institutions.append(Institution(
                            name=inst_name,
                            country=institution.get("country_code"),
                            type=institution.get("type")
                        ))

            # 重複除去
            institutions = list(
                {inst.name: inst for inst in institutions}.values())

            # ジャーナル情報
            journal = None
            venue = work.get("primary_location", {})
            if venue and venue.get("source"):
                journal = venue["source"].get("display_name")

            # 概要（OpenAlexにはabstractがない場合が多い）
            abstract = work.get("abstract")

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
                source_api="openalex",
                confidence_score=0.9,  # OpenAlexは信頼性が高い
                relevance_score=None  # 後で計算
            )

        except Exception as e:
            logger.error(f"OpenAlex論文パース失敗: {e}")
            return None

# 同期版の関数も提供


def search_papers_sync(query: str, max_results: int = None) -> List[Paper]:
    """同期版の論文検索"""
    client = OpenAlexClient()
    return asyncio.run(client.search_papers(query, max_results))
