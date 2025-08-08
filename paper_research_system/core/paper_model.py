"""
Paper data models for Academic Paper Research Assistant
論文データモデル
"""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Author:
    """著者情報"""
    name: str
    name_japanese: Optional[str] = None  # カタカナ併記用
    institution: Optional[str] = None
    orcid: Optional[str] = None


@dataclass
class Institution:
    """所属機関情報"""
    name: str
    name_japanese: Optional[str] = None  # カタカナ併記用
    country: Optional[str] = None
    type: Optional[str] = None  # university, research_institute, etc.


@dataclass
class Paper:
    """論文情報"""
    title: str
    title_japanese: Optional[str] = None  # 日本語タイトル（翻訳用）
    authors: List[Author] = None
    institutions: List[Institution] = None
    publication_year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    citation_count: Optional[int] = None
    abstract: Optional[str] = None
    abstract_japanese: Optional[str] = None  # 日本語要約
    journal: Optional[str] = None
    venue: Optional[str] = None
    keywords: List[str] = None

    # メタデータ
    source_api: Optional[str] = None  # openalex, crossref, semantic_scholar
    confidence_score: Optional[float] = None  # 信頼性スコア
    relevance_score: Optional[float] = None  # 関連性スコア
    total_score: Optional[float] = None  # 統合検索用総合スコア

    def __post_init__(self):
        if self.authors is None:
            self.authors = []
        if self.institutions is None:
            self.institutions = []
        if self.keywords is None:
            self.keywords = []

    def to_chatgpt_format(self) -> str:
        """ChatGPT/Claude投入用のフォーマット"""
        result = f"""
## 📄 {self.title}

**著者**: {', '.join([author.name for author in self.authors])}
**発表年**: {self.publication_year}
**引用数**: {self.citation_count if self.citation_count else 'N/A'}
**DOI**: {self.doi if self.doi else 'N/A'}
**URL**: {self.url if self.url else 'N/A'}

**概要**:
{self.abstract if self.abstract else '概要なし'}

**所属機関**: {', '.join([inst.name for inst in self.institutions]) if self.institutions else 'N/A'}
**ジャーナル**: {self.journal if self.journal else 'N/A'}
        """
        return result.strip()

    def to_japanese_summary(self) -> str:
        """日本語での要約"""
        return f"""
【論文情報】
タイトル: {self.title}
著者: {', '.join([author.name for author in self.authors])}
発表年: {self.publication_year}
引用数: {self.citation_count if self.citation_count else '不明'}
信頼性: {self.source_api} API経由で取得（ハルシネーションなし）

【用途】
この情報をChatGPTやClaudeに投げて要約・原稿化に使用できます。
        """.strip()
