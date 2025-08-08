"""
メタ情報統合処理を行うcomposerモジュール
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from .prompt_generator import PaperMetadata, create_prompt_from_metadata


class ScriptComposer:
    """論文メタデータと要約を統合してYouTube原稿を生成するクラス"""
    
    def __init__(self):
        self.prompt_generator = None  # 遅延初期化
    
    def compose_script(self, metadata: PaperMetadata, abstract: str, style: str = "popular") -> str:
        """
        論文メタデータと要約からYouTube原稿を生成
        
        Args:
            metadata: 論文メタデータ
            abstract: 論文要約
            style: 原稿スタイル
        
        Returns:
            生成されたYouTube原稿
        """
        # プロンプトを生成
        system_prompt = create_prompt_from_metadata(metadata, style)
        
        # 統合された原稿を生成
        composed_script = f"{system_prompt}\n\n{abstract}"
        
        return composed_script
    
    def compose_from_json(self, metadata_file: str, abstract: str, style: str = "popular") -> str:
        """
        JSONファイルからメタデータを読み込んで原稿を生成
        
        Args:
            metadata_file: メタデータJSONファイルのパス
            abstract: 論文要約
            style: 原稿スタイル
        
        Returns:
            生成されたYouTube原稿
        """
        metadata = self._load_metadata_from_json(metadata_file)
        return self.compose_script(metadata, abstract, style)
    
    def _load_metadata_from_json(self, file_path: str) -> PaperMetadata:
        """JSONファイルからメタデータを読み込み"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return PaperMetadata(
            title=data.get('title', ''),
            authors=data.get('authors', []),
            abstract=data.get('abstract', ''),
            doi=data.get('doi'),
            publication_year=data.get('publication_year'),
            journal=data.get('journal'),
            citation_count=data.get('citation_count'),
            institutions=data.get('institutions'),
            keywords=data.get('keywords')
        )
    
    def validate_metadata(self, metadata: PaperMetadata) -> Dict[str, Any]:
        """
        メタデータの妥当性を検証
        
        Returns:
            検証結果の辞書
        """
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": []
        }
        
        # 必須フィールドのチェック
        if not metadata.title:
            validation_result["errors"].append("タイトルが空です")
            validation_result["is_valid"] = False
        
        if not metadata.authors:
            validation_result["warnings"].append("著者情報がありません")
        
        if not metadata.abstract:
            validation_result["warnings"].append("要約が空です")
        
        # 年号の妥当性チェック
        if metadata.publication_year:
            if metadata.publication_year < 1900 or metadata.publication_year > 2030:
                validation_result["warnings"].append("発表年が妥当な範囲外です")
        
        # 引用数の妥当性チェック
        if metadata.citation_count and metadata.citation_count < 0:
            validation_result["errors"].append("引用数が負の値です")
            validation_result["is_valid"] = False
        
        return validation_result


def compose_script(metadata: PaperMetadata, abstract: str, style: str = "popular") -> str:
    """
    論文メタデータと要約からYouTube原稿を生成する便利関数
    
    Args:
        metadata: 論文メタデータ
        abstract: 論文要約
        style: 原稿スタイル
    
    Returns:
        生成されたYouTube原稿
    """
    composer = ScriptComposer()
    return composer.compose_script(metadata, abstract, style)


def compose_from_json(metadata_file: str, abstract: str, style: str = "popular") -> str:
    """
    JSONファイルからメタデータを読み込んで原稿を生成する便利関数
    
    Args:
        metadata_file: メタデータJSONファイルのパス
        abstract: 論文要約
        style: 原稿スタイル
    
    Returns:
        生成されたYouTube原稿
    """
    composer = ScriptComposer()
    return composer.compose_from_json(metadata_file, abstract, style)


if __name__ == "__main__":
    # テスト用のサンプルデータ
    sample_metadata = PaperMetadata(
        title="AI技術を用いた営業効率化の研究",
        authors=["田中太郎", "佐藤花子"],
        abstract="本研究では、AI技術を用いて営業活動の効率化を図る手法を提案する。",
        publication_year=2023,
        journal="営業科学ジャーナル",
        citation_count=45,
        institutions=["東京大学"],
        keywords=["AI", "営業効率化"]
    )
    
    sample_abstract = """
    本研究では、機械学習技術を用いて営業活動の効率化を図る手法を提案する。
    顧客データの分析により、成約率を30%向上させることに成功した。
    特に、顧客の購買行動パターンを分析することで、最適なアプローチタイミングを
    特定できることが明らかになった。
    """
    
    composer = ScriptComposer()
    script = composer.compose_script(sample_metadata, sample_abstract, "popular")
    print("生成された原稿:")
    print(script)
    
    # 検証テスト
    validation = composer.validate_metadata(sample_metadata)
    print(f"\n検証結果: {validation}") 