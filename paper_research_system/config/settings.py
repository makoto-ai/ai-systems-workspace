"""
Settings configuration for Academic Paper Research Assistant
論文リサーチ支援システム設定
"""

import os
from dotenv import load_dotenv
from typing import List
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

load_dotenv()


class Settings(BaseSettings):
    """アプリケーション設定"""

    # OpenAlex API設定 (無料・APIキー不要)
    openalex_base_url: str = "https://api.openalex.org"

    # Crossref API設定 (無料)
    crossref_base_url: str = "https://api.crossref.org/works"

    # Semantic Scholar API設定 (承認済み - レート制限: 1req/sec)
    semantic_scholar_api_key: str = os.getenv(
        "SEMANTIC_SCHOLAR_API_KEY",
        "Bz4kPPH4YB6KbEpplfkj42ZyBPOIVDyD7dAXIIQn")
    semantic_scholar_base_url: str = "https://api.semanticscholar.org/graph/v1"

    # 検索設定
    max_results_per_api: int = 5
    default_fields: List[str] = ["営業", "マネジメント", "心理学", "組織行動", "リーダーシップ"]

    # 出力設定
    output_language: str = "ja"
    include_abstracts: bool = True
    include_citation_count: bool = True

    # リクエスト設定
    request_timeout: int = 30
    retry_attempts: int = 3

    model_config = ConfigDict(env_file=".env")


# グローバル設定インスタンス
settings = Settings()
