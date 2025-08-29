"""
Advanced Filter Engine for Academic Paper Search
学術論文検索用高度フィルタエンジン
"""

from core.paper_model import Paper
import logging
from typing import List, Optional, Set
from datetime import datetime
from dataclasses import dataclass
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


logger = logging.getLogger(__name__)


@dataclass
class SearchFilters:
    """検索フィルタ設定"""

    # 年代フィルタ
    year_from: Optional[int] = None
    year_to: Optional[int] = None

    # 引用数フィルタ
    min_citations: Optional[int] = None
    max_citations: Optional[int] = None

    # 著者フィルタ
    authors: Optional[List[str]] = None
    exclude_authors: Optional[List[str]] = None

    # ジャーナル/会議フィルタ
    journals: Optional[List[str]] = None
    exclude_journals: Optional[List[str]] = None

    # DOI有無フィルタ
    require_doi: Optional[bool] = None

    # 概要有無フィルタ
    require_abstract: Optional[bool] = None

    # APIソースフィルタ
    allowed_sources: Optional[List[str]] = None

    # キーワードフィルタ
    required_keywords: Optional[List[str]] = None
    excluded_keywords: Optional[List[str]] = None

    # 論文種別フィルタ
    # ['journal', 'conference', 'preprint', 'book']
    paper_types: Optional[List[str]] = None


class AdvancedFilterEngine:
    """高度検索フィルタエンジン"""

    def __init__(self):
        """初期化"""
        self.current_year = datetime.now().year

    def apply_filters(self, papers: List[Paper], filters: SearchFilters) -> List[Paper]:
        """
        論文リストにフィルタを適用

        Args:
            papers: フィルタ対象の論文リスト
            filters: 適用するフィルタ設定

        Returns:
            フィルタ適用後の論文リスト
        """
        if not papers or not filters:
            return papers

        filtered_papers = papers.copy()
        original_count = len(filtered_papers)

        # 各フィルタを順次適用
        filtered_papers = self._apply_year_filter(filtered_papers, filters)
        filtered_papers = self._apply_citation_filter(filtered_papers, filters)
        filtered_papers = self._apply_author_filter(filtered_papers, filters)
        filtered_papers = self._apply_journal_filter(filtered_papers, filters)
        filtered_papers = self._apply_content_filter(filtered_papers, filters)
        filtered_papers = self._apply_source_filter(filtered_papers, filters)
        filtered_papers = self._apply_keyword_filter(filtered_papers, filters)
        filtered_papers = self._apply_type_filter(filtered_papers, filters)

        final_count = len(filtered_papers)
        logger.info(
            f"フィルタ適用: {original_count}件 → {final_count}件 ({
                original_count -
                final_count}件除外)"
        )

        return filtered_papers

    def _apply_year_filter(
        self, papers: List[Paper], filters: SearchFilters
    ) -> List[Paper]:
        """年代フィルタ適用"""
        if filters.year_from is None and filters.year_to is None:
            return papers

        filtered = []
        for paper in papers:
            year = paper.publication_year
            if year is None:
                continue  # 年度不明は除外

            # 年度範囲チェック
            if filters.year_from and year < filters.year_from:
                continue
            if filters.year_to and year > filters.year_to:
                continue

            filtered.append(paper)

        logger.debug(f"年代フィルタ適用: {len(papers)} → {len(filtered)}件")
        return filtered

    def _apply_citation_filter(
        self, papers: List[Paper], filters: SearchFilters
    ) -> List[Paper]:
        """引用数フィルタ適用"""
        if filters.min_citations is None and filters.max_citations is None:
            return papers

        filtered = []
        for paper in papers:
            citations = paper.citation_count or 0

            # 引用数範囲チェック
            if filters.min_citations and citations < filters.min_citations:
                continue
            if filters.max_citations and citations > filters.max_citations:
                continue

            filtered.append(paper)

        logger.debug(f"引用数フィルタ適用: {len(papers)} → {len(filtered)}件")
        return filtered

    def _apply_author_filter(
        self, papers: List[Paper], filters: SearchFilters
    ) -> List[Paper]:
        """著者フィルタ適用"""
        if not filters.authors and not filters.exclude_authors:
            return papers

        filtered = []
        for paper in papers:
            if not paper.authors:
                # 著者情報なし
                if filters.authors:
                    continue  # 指定著者必須なら除外
                filtered.append(paper)
                continue

            author_names = {
                author.name.lower().strip() for author in paper.authors if author.name
            }

            # 指定著者チェック
            if filters.authors:
                required_authors = {name.lower().strip() for name in filters.authors}
                if not any(
                    self._author_matches(req_author, author_names)
                    for req_author in required_authors
                ):
                    continue

            # 除外著者チェック
            if filters.exclude_authors:
                excluded_authors = {
                    name.lower().strip() for name in filters.exclude_authors
                }
                if any(
                    self._author_matches(exc_author, author_names)
                    for exc_author in excluded_authors
                ):
                    continue

            filtered.append(paper)

        logger.debug(f"著者フィルタ適用: {len(papers)} → {len(filtered)}件")
        return filtered

    def _author_matches(self, filter_author: str, paper_authors: Set[str]) -> bool:
        """著者名マッチング（部分一致も対応）"""
        filter_author = filter_author.lower().strip()

        for paper_author in paper_authors:
            # 完全一致
            if filter_author == paper_author:
                return True

            # 部分一致（姓名の一部でもOK）
            if filter_author in paper_author or paper_author in filter_author:
                return True

            # 姓のみの一致
            filter_parts = filter_author.split()
            paper_parts = paper_author.split()
            if filter_parts and paper_parts:
                if filter_parts[-1] == paper_parts[-1]:  # 姓が一致
                    return True

        return False

    def _apply_journal_filter(
        self, papers: List[Paper], filters: SearchFilters
    ) -> List[Paper]:
        """ジャーナル/会議フィルタ適用"""
        if not filters.journals and not filters.exclude_journals:
            return papers

        filtered = []
        for paper in papers:
            journal = (paper.journal or "").lower().strip()

            # 指定ジャーナルチェック
            if filters.journals:
                required_journals = {j.lower().strip() for j in filters.journals}
                if not any(
                    self._journal_matches(req_journal, journal)
                    for req_journal in required_journals
                ):
                    continue

            # 除外ジャーナルチェック
            if filters.exclude_journals:
                excluded_journals = {
                    j.lower().strip() for j in filters.exclude_journals
                }
                if any(
                    self._journal_matches(exc_journal, journal)
                    for exc_journal in excluded_journals
                ):
                    continue

            filtered.append(paper)

        logger.debug(f"ジャーナルフィルタ適用: {len(papers)} → {len(filtered)}件")
        return filtered

    def _journal_matches(self, filter_journal: str, paper_journal: str) -> bool:
        """ジャーナル名マッチング"""
        if not filter_journal or not paper_journal:
            return False

        # 部分一致
        return filter_journal in paper_journal or paper_journal in filter_journal

    def _apply_content_filter(
        self, papers: List[Paper], filters: SearchFilters
    ) -> List[Paper]:
        """コンテンツフィルタ適用（DOI・概要有無）"""
        filtered = []
        for paper in papers:
            # DOI必須チェック
            if filters.require_doi and not paper.doi:
                continue

            # 概要必須チェック
            if filters.require_abstract and not paper.abstract:
                continue

            filtered.append(paper)

        logger.debug(f"コンテンツフィルタ適用: {len(papers)} → {len(filtered)}件")
        return filtered

    def _apply_source_filter(
        self, papers: List[Paper], filters: SearchFilters
    ) -> List[Paper]:
        """APIソースフィルタ適用"""
        if not filters.allowed_sources:
            return papers

        allowed_sources = {source.lower() for source in filters.allowed_sources}

        filtered = []
        for paper in papers:
            if paper.source_api and paper.source_api.lower() in allowed_sources:
                filtered.append(paper)

        logger.debug(f"ソースフィルタ適用: {len(papers)} → {len(filtered)}件")
        return filtered

    def _apply_keyword_filter(
        self, papers: List[Paper], filters: SearchFilters
    ) -> List[Paper]:
        """キーワードフィルタ適用"""
        if not filters.required_keywords and not filters.excluded_keywords:
            return papers

        filtered = []
        for paper in papers:
            text_content = self._extract_searchable_text(paper)

            # 必須キーワードチェック
            if filters.required_keywords:
                if not all(
                    self._keyword_in_text(keyword, text_content)
                    for keyword in filters.required_keywords
                ):
                    continue

            # 除外キーワードチェック
            if filters.excluded_keywords:
                if any(
                    self._keyword_in_text(keyword, text_content)
                    for keyword in filters.excluded_keywords
                ):
                    continue

            filtered.append(paper)

        logger.debug(f"キーワードフィルタ適用: {len(papers)} → {len(filtered)}件")
        return filtered

    def _extract_searchable_text(self, paper: Paper) -> str:
        """論文から検索可能テキストを抽出"""
        parts = []

        if paper.title:
            parts.append(paper.title)
        if paper.abstract:
            parts.append(paper.abstract)
        if paper.keywords:
            parts.extend(paper.keywords)

        return " ".join(parts).lower()

    def _keyword_in_text(self, keyword: str, text: str) -> bool:
        """キーワードがテキスト内に存在するかチェック"""
        keyword = keyword.lower().strip()
        return keyword in text

    def _apply_type_filter(
        self, papers: List[Paper], filters: SearchFilters
    ) -> List[Paper]:
        """論文種別フィルタ適用"""
        if not filters.paper_types:
            return papers

        filtered = []
        for paper in papers:
            paper_type = self._classify_paper_type(paper)
            if paper_type in filters.paper_types:
                filtered.append(paper)

        logger.debug(f"論文種別フィルタ適用: {len(papers)} → {len(filtered)}件")
        return filtered

    def _classify_paper_type(self, paper: Paper) -> str:
        """論文種別を分類"""
        journal = (paper.journal or "").lower()

        # プレプリント判定
        if any(preprint in journal for preprint in ["arxiv", "biorxiv", "preprint"]):
            return "preprint"

        # 会議判定
        if any(
            conf in journal
            for conf in ["conference", "proceedings", "workshop", "symposium"]
        ):
            return "conference"

        # 書籍判定
        if any(book in journal for book in ["book", "chapter", "handbook"]):
            return "book"

        # デフォルトはジャーナル
        return "journal"

    def create_filter_summary(self, filters: SearchFilters) -> str:
        """フィルタ設定の要約を生成"""
        summary_parts = []

        # 年代
        if filters.year_from or filters.year_to:
            year_range = f"{filters.year_from or '~'}-{filters.year_to or '~'}"
            summary_parts.append(f"📅 年代: {year_range}")

        # 引用数
        if filters.min_citations or filters.max_citations:
            citation_range = f"{
                filters.min_citations or 0}~{
                filters.max_citations or '∞'}"
            summary_parts.append(f"📊 引用数: {citation_range}")

        # 著者
        if filters.authors:
            summary_parts.append(f"👥 著者: {', '.join(filters.authors[:2])}")
            if len(filters.authors) > 2:
                summary_parts[-1] += f", 他{len(filters.authors) - 2}名"

        # ジャーナル
        if filters.journals:
            summary_parts.append(f"📚 ジャーナル: {', '.join(filters.journals[:2])}")
            if len(filters.journals) > 2:
                summary_parts[-1] += f", 他{len(filters.journals) - 2}誌"

        # コンテンツ要件
        requirements = []
        if filters.require_doi:
            requirements.append("DOI必須")
        if filters.require_abstract:
            requirements.append("概要必須")
        if requirements:
            summary_parts.append(f"📋 要件: {', '.join(requirements)}")

        # キーワード
        if filters.required_keywords:
            summary_parts.append(
                f"🔍 必須KW: {', '.join(filters.required_keywords[:2])}"
            )
            if len(filters.required_keywords) > 2:
                summary_parts[-1] += f", 他{len(filters.required_keywords) - 2}個"

        if not summary_parts:
            return "フィルタなし"

        return " | ".join(summary_parts)


# シングルトンインスタンス
_filter_engine = None


def get_filter_engine() -> AdvancedFilterEngine:
    """AdvancedFilterEngineのシングルトンインスタンスを取得"""
    global _filter_engine
    if _filter_engine is None:
        _filter_engine = AdvancedFilterEngine()
    return _filter_engine
