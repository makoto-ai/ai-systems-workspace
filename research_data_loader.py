#!/usr/bin/env python3
"""
研究データローダー
様々な形式の研究データを読み込んでYouTube原稿生成システムで使用できる形式に変換
"""

import json
import csv
import yaml
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class ResearchMetadata:
    """研究メタデータ"""
    title: str
    authors: List[str]
    abstract: str
    publication_year: int
    journal: str
    doi: Optional[str] = None
    citation_count: int = 0
    keywords: List[str] = None
    institutions: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)

class ResearchDataLoader:
    """研究データローダー"""
    
    def __init__(self):
        self.supported_formats = ['.json', '.csv', '.yaml', '.yml', '.xml']
    
    def load_research_data(self, file_path: str) -> ResearchMetadata:
        """研究データを読み込み"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
        
        if file_path.suffix not in self.supported_formats:
            raise ValueError(f"サポートされていないファイル形式: {file_path.suffix}")
        
        try:
            if file_path.suffix == '.json':
                return self._load_json(file_path)
            elif file_path.suffix == '.csv':
                return self._load_csv(file_path)
            elif file_path.suffix in ['.yaml', '.yml']:
                return self._load_yaml(file_path)
            elif file_path.suffix == '.xml':
                return self._load_xml(file_path)
            else:
                raise ValueError(f"未対応のファイル形式: {file_path.suffix}")
                
        except Exception as e:
            logger.error(f"ファイル読み込みエラー: {e}")
            raise e
    
    def _load_json(self, file_path: Path) -> ResearchMetadata:
        """JSONファイルから読み込み"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return self._create_research_metadata(data)
    
    def _load_csv(self, file_path: Path) -> ResearchMetadata:
        """CSVファイルから読み込み"""
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = next(reader)  # 最初の行を読み込み
        
        return self._create_research_metadata(data)
    
    def _load_yaml(self, file_path: Path) -> ResearchMetadata:
        """YAMLファイルから読み込み"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return self._create_research_metadata(data)
    
    def _load_xml(self, file_path: Path) -> ResearchMetadata:
        """XMLファイルから読み込み"""
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        data = {}
        
        # XML要素を辞書に変換
        for child in root:
            if child.tag == 'authors':
                data[child.tag] = [author.text for author in child.findall('author')]
            elif child.tag == 'keywords':
                data[child.tag] = [keyword.text for keyword in child.findall('keyword')]
            elif child.tag == 'institutions':
                data[child.tag] = [institution.text for institution in child.findall('institution')]
            else:
                data[child.tag] = child.text
        
        return self._create_research_metadata(data)
    
    def _create_research_metadata(self, data: Dict[str, Any]) -> ResearchMetadata:
        """辞書データからResearchMetadataを作成"""
        # 著者リストの処理
        authors = data.get('authors', [])
        if isinstance(authors, str):
            authors = [author.strip() for author in authors.split(',')]
        
        # キーワードリストの処理
        keywords = data.get('keywords', [])
        if isinstance(keywords, str):
            keywords = [keyword.strip() for keyword in keywords.split(',')]
        
        # 機関リストの処理
        institutions = data.get('institutions', [])
        if isinstance(institutions, str):
            institutions = [institution.strip() for institution in institutions.split(',')]
        
        # 数値フィールドの処理
        publication_year = int(data.get('publication_year', 2024))
        citation_count = int(data.get('citation_count', 0))
        
        return ResearchMetadata(
            title=data.get('title', ''),
            authors=authors,
            abstract=data.get('abstract', ''),
            publication_year=publication_year,
            journal=data.get('journal', ''),
            doi=data.get('doi'),
            citation_count=citation_count,
            keywords=keywords,
            institutions=institutions
        )
    
    def save_research_data(self, research_data: ResearchMetadata, file_path: str, format: str = 'json'):
        """研究データをファイルに保存"""
        file_path = Path(file_path)
        
        try:
            if format == 'json':
                self._save_json(research_data, file_path)
            elif format == 'csv':
                self._save_csv(research_data, file_path)
            elif format == 'yaml':
                self._save_yaml(research_data, file_path)
            elif format == 'xml':
                self._save_xml(research_data, file_path)
            else:
                raise ValueError(f"未対応の保存形式: {format}")
                
        except Exception as e:
            logger.error(f"ファイル保存エラー: {e}")
            raise e
    
    def _save_json(self, research_data: ResearchMetadata, file_path: Path):
        """JSON形式で保存"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(research_data.to_dict(), f, ensure_ascii=False, indent=2)
    
    def _save_csv(self, research_data: ResearchMetadata, file_path: Path):
        """CSV形式で保存"""
        data = research_data.to_dict()
        
        # リストフィールドを文字列に変換
        data['authors'] = ', '.join(data['authors'])
        data['keywords'] = ', '.join(data.get('keywords', []))
        data['institutions'] = ', '.join(data.get('institutions', []))
        
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data.keys())
            writer.writeheader()
            writer.writerow(data)
    
    def _save_yaml(self, research_data: ResearchMetadata, file_path: Path):
        """YAML形式で保存"""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(research_data.to_dict(), f, default_flow_style=False, allow_unicode=True)
    
    def _save_xml(self, research_data: ResearchMetadata, file_path: Path):
        """XML形式で保存"""
        data = research_data.to_dict()
        
        root = ET.Element('research')
        
        for key, value in data.items():
            if key == 'authors':
                authors_elem = ET.SubElement(root, 'authors')
                for author in value:
                    author_elem = ET.SubElement(authors_elem, 'author')
                    author_elem.text = author
            elif key == 'keywords':
                keywords_elem = ET.SubElement(root, 'keywords')
                for keyword in value:
                    keyword_elem = ET.SubElement(keywords_elem, 'keyword')
                    keyword_elem.text = keyword
            elif key == 'institutions':
                institutions_elem = ET.SubElement(root, 'institutions')
                for institution in value:
                    institution_elem = ET.SubElement(institutions_elem, 'institution')
                    institution_elem.text = institution
            else:
                elem = ET.SubElement(root, key)
                elem.text = str(value)
        
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding='utf-8', xml_declaration=True)

def create_sample_research_data():
    """サンプル研究データを作成"""
    sample_data = {
        "title": "AIによる営業パフォーマンス向上の研究",
        "authors": ["田中太郎", "佐藤花子", "鈴木一郎"],
        "abstract": "本研究では、AI技術を活用した営業手法の効果を検証しました。機械学習アルゴリズムを使用して顧客データを分析し、最適なアプローチ戦略を提案するシステムを開発しました。研究結果によると、AIを活用した営業チームは、従来の手法と比較して平均30%の売上向上を達成しました。",
        "publication_year": 2024,
        "journal": "Journal of Sales Technology",
        "doi": "10.1234/jst.2024.001",
        "citation_count": 15,
        "keywords": ["AI", "営業", "パフォーマンス", "機械学習", "顧客分析"],
        "institutions": ["東京大学", "京都大学"]
    }
    
    return ResearchMetadata(**sample_data)

def main():
    """メイン関数"""
    # サンプルデータを作成
    sample_data = create_sample_research_data()
    
    # ローダーを初期化
    loader = ResearchDataLoader()
    
    # 様々な形式で保存
    formats = ['json', 'csv', 'yaml', 'xml']
    
    for format in formats:
        filename = f"sample_research_data.{format}"
        loader.save_research_data(sample_data, filename, format)
        print(f"サンプルデータを保存しました: {filename}")
    
    # 保存したファイルを読み込んでテスト
    print("\n=== ファイル読み込みテスト ===")
    
    for format in formats:
        filename = f"sample_research_data.{format}"
        try:
            loaded_data = loader.load_research_data(filename)
            print(f"{format.upper()}: {loaded_data.title}")
        except Exception as e:
            print(f"{format.upper()}: エラー - {e}")

if __name__ == "__main__":
    main() 