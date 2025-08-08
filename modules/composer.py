"""
メタ情報統合処理を行うcomposerモジュール
"""

import json
import sys
import os
import logging
import traceback
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.prompt_generator import PaperMetadata, create_prompt_from_metadata

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComposerError(Exception):
    """Composer関連のエラー"""
    pass


class SystemDiagnostics:
    """システム診断機能"""
    
    @staticmethod
    def check_system_health() -> Dict[str, Any]:
        """システムの健全性をチェック"""
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "issues": [],
            "warnings": []
        }
        
        try:
            # 必要なファイルの存在確認
            required_files = [
                "modules/prompt_generator.py",
                ".cursor/composer.json",
                ".cursor/mcp.json"
            ]
            
            for file_path in required_files:
                if not os.path.exists(file_path):
                    diagnostics["issues"].append(f"必要なファイルが見つかりません: {file_path}")
                    diagnostics["status"] = "unhealthy"
            
            # モジュールのインポート確認
            try:
                from modules.prompt_generator import PaperMetadata, create_prompt_from_metadata
                diagnostics["warnings"].append("モジュールインポート: 正常")
            except ImportError as e:
                diagnostics["issues"].append(f"モジュールインポートエラー: {e}")
                diagnostics["status"] = "unhealthy"
            
            # 設定ファイルの妥当性確認
            try:
                with open(".cursor/composer.json", 'r', encoding='utf-8') as f:
                    json.load(f)
                diagnostics["warnings"].append("composer.json: 正常")
            except Exception as e:
                diagnostics["issues"].append(f"composer.jsonエラー: {e}")
                diagnostics["status"] = "unhealthy"
            
            return diagnostics
            
        except Exception as e:
            diagnostics["issues"].append(f"診断エラー: {e}")
            diagnostics["status"] = "error"
            return diagnostics
    
    @staticmethod
    def generate_error_report(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """エラーレポートを生成"""
        return {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {},
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "working_directory": os.getcwd()
            }
        }


class ScriptComposer:
    """論文メタデータと要約を統合してYouTube原稿を生成するクラス"""
    
    def __init__(self):
        self.prompt_generator = None  # 遅延初期化
        self.diagnostics = SystemDiagnostics()
        logger.info("ScriptComposerを初期化しました")
        
        # システム診断を実行
        health_check = self.diagnostics.check_system_health()
        if health_check["status"] != "healthy":
            logger.warning(f"システム診断で問題が見つかりました: {health_check['issues']}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """システムの現在の状態を取得"""
        return self.diagnostics.check_system_health()
    
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
        try:
            # メタデータの検証
            validation = self.validate_metadata(metadata)
            if not validation["is_valid"]:
                logger.warning(f"メタデータに問題があります: {validation['errors']}")
            
            # プロンプトを生成
            system_prompt = create_prompt_from_metadata(metadata, style)
            
            # 統合された原稿を生成
            composed_script = f"{system_prompt}\n\n{abstract}"
            
            logger.info(f"原稿生成完了: {len(composed_script)}文字")
            return composed_script
            
        except Exception as e:
            # エラーレポートを生成
            error_report = self.diagnostics.generate_error_report(e, {
                "operation": "compose_script",
                "metadata_title": metadata.title if metadata else "unknown",
                "style": style
            })
            logger.error(f"原稿生成中にエラーが発生しました: {error_report}")
            raise ComposerError(f"原稿生成に失敗しました: {e}")
    
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
        try:
            metadata = self._load_metadata_from_json(metadata_file)
            return self.compose_script(metadata, abstract, style)
        except ComposerError:
            # ComposerErrorはそのまま再送出
            raise
        except Exception as e:
            # エラーレポートを生成
            error_report = self.diagnostics.generate_error_report(e, {
                "operation": "compose_from_json",
                "metadata_file": metadata_file,
                "style": style
            })
            error_msg = f"JSONファイルからの原稿生成に失敗しました: {e}"
            logger.error(f"{error_msg} - {error_report}")
            raise ComposerError(error_msg)
    
    def _load_metadata_from_json(self, file_path: str) -> PaperMetadata:
        """JSONファイルからメタデータを読み込み"""
        # ファイルの存在確認
        if not os.path.exists(file_path):
            error_msg = f"ファイルが見つかりません: {file_path}"
            logger.error(error_msg)
            raise ComposerError(error_msg)
        
        try:
            # ファイルの読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"JSONファイルを読み込みました: {file_path}")
            
            # データの検証
            if not isinstance(data, dict):
                error_msg = f"JSONファイルの形式が不正です: {file_path}"
                logger.error(error_msg)
                raise ComposerError(error_msg)
            
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
            
        except json.JSONDecodeError as e:
            error_msg = f"JSONファイルの形式が不正です: {file_path} - {e}"
            logger.error(error_msg)
            raise ComposerError(error_msg)
        except Exception as e:
            error_msg = f"メタデータの読み込みに失敗しました: {file_path} - {e}"
            logger.error(error_msg)
            raise ComposerError(error_msg)
    
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
        
        try:
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
            
            logger.info(f"メタデータ検証完了: {len(validation_result['errors'])}個のエラー, {len(validation_result['warnings'])}個の警告")
            return validation_result
            
        except Exception as e:
            logger.error(f"メタデータ検証中にエラーが発生しました: {e}")
            validation_result["errors"].append(f"検証エラー: {e}")
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
    try:
        composer = ScriptComposer()
        return composer.compose_script(metadata, abstract, style)
    except ComposerError:
        # ComposerErrorはそのまま再送出
        raise
    except Exception as e:
        error_msg = f"原稿生成に失敗しました: {e}"
        logger.error(error_msg)
        raise ComposerError(error_msg)


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
    try:
        composer = ScriptComposer()
        return composer.compose_from_json(metadata_file, abstract, style)
    except ComposerError:
        # ComposerErrorはそのまま再送出
        raise
    except Exception as e:
        error_msg = f"JSONファイルからの原稿生成に失敗しました: {e}"
        logger.error(error_msg)
        raise ComposerError(error_msg)


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
    
    try:
        composer = ScriptComposer()
        script = composer.compose_script(sample_metadata, sample_abstract, "popular")
        print("生成された原稿:")
        print(script)
        
        # 検証テスト
        validation = composer.validate_metadata(sample_metadata)
        print(f"\n検証結果: {validation}")
        
    except ComposerError as e:
        print(f"エラーが発生しました: {e}")
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}") 