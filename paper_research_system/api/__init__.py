"""
API module for Academic Paper Research Assistant
API連携モジュール
"""

from .openalex_client import OpenAlexClient
from .crossref_client import CrossRefClient
from .semantic_scholar_client import SemanticScholarClient

__all__ = ["OpenAlexClient", "CrossRefClient", "SemanticScholarClient"]
