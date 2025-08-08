"""
共通検証ユーティリティ
Autoモードの出力品質担保・再現性向上・AI信頼性確保の中核機能
"""

import json
import logging
import re
import requests
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import difflib
from sentence_transformers import SentenceTransformer
import numpy as np

# ログ設定
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """検証結果データクラス"""
    is_valid: bool
    score: float
    details: List[str]
    warnings: List[str]
    errors: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "is_valid": self.is_valid,
            "score": self.score,
            "details": self.details,
            "warnings": self.warnings,
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat()
        }

class DOIValidator:
    """DOI存在性確認クラス"""
    
    def __init__(self):
        self.crossref_api_url = "https://api.crossref.org/works/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'YouTubeScriptGenerator/1.0 (mailto:test@example.com)'
        })
    
    def extract_dois(self, text: str) -> List[str]:
        """テキストからDOIを抽出"""
        doi_pattern = r'\b(10\.\d{4,}(?:\.\d+)*\/\S+(?:(?!["&\'<>])\S)*)\b'
        return re.findall(doi_pattern, text)
    
    def verify_doi(self, doi: str) -> Tuple[bool, Dict[str, Any]]:
        """DOIの存在性を確認"""
        try:
            url = f"{self.crossref_api_url}{doi}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                work = data.get('message', {})
                
                return True, {
                    "title": work.get('title', [''])[0] if work.get('title') else '',
                    "authors": [author.get('given', '') + ' ' + author.get('family', '') 
                              for author in work.get('author', [])],
                    "published": work.get('published-print', {}).get('date-parts', [[]])[0][0] if work.get('published-print') else '',
                    "journal": work.get('container-title', [''])[0] if work.get('container-title') else '',
                    "doi": doi
                }
            else:
                return False, {"error": f"HTTP {response.status_code}", "doi": doi}
                
        except Exception as e:
            logger.error(f"DOI検証エラー: {doi} - {str(e)}")
            return False, {"error": str(e), "doi": doi}
    
    def validate_dois_in_text(self, text: str) -> ValidationResult:
        """テキスト内の全てのDOIを検証"""
        dois = self.extract_dois(text)
        valid_count = 0
        details = []
        warnings = []
        errors = []
        
        if not dois:
            warnings.append("テキスト内にDOIが検出されませんでした")
            return ValidationResult(
                is_valid=False,
                score=0.0,
                details=details,
                warnings=warnings,
                errors=errors,
                timestamp=datetime.now()
            )
        
        for doi in dois:
            is_valid, info = self.verify_doi(doi)
            if is_valid:
                valid_count += 1
                details.append(f"✅ DOI有効: {doi} - {info.get('title', 'N/A')}")
            else:
                errors.append(f"❌ DOI無効: {doi} - {info.get('error', 'Unknown error')}")
        
        score = valid_count / len(dois) if dois else 0.0
        is_valid = score >= 0.8  # 80%以上が有効
        
        return ValidationResult(
            is_valid=is_valid,
            score=score,
            details=details,
            warnings=warnings,
            errors=errors,
            timestamp=datetime.now()
        )

class HallucinationDetector:
    """ハルシネーション検出クラス"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        try:
            self.model = SentenceTransformer(model_name)
            self.similarity_threshold = 0.8
        except Exception as e:
            logger.warning(f"SentenceTransformerの初期化に失敗: {e}")
            self.model = None
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """2つのテキスト間の類似度を計算"""
        if not self.model:
            return 0.0
        
        try:
            embeddings = self.model.encode([text1, text2])
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            return float(similarity)
        except Exception as e:
            logger.error(f"類似度計算エラー: {e}")
            return 0.0
    
    def extract_claims(self, text: str) -> List[str]:
        """テキストから主張を抽出"""
        # 主張を示す表現パターン
        claim_patterns = [
            r'研究によると[^。]*。',
            r'結果として[^。]*。',
            r'分析では[^。]*。',
            r'調査結果[^。]*。',
            r'実験により[^。]*。',
            r'データから[^。]*。'
        ]
        
        claims = []
        for pattern in claim_patterns:
            matches = re.findall(pattern, text)
            claims.extend(matches)
        
        return claims
    
    def detect_hallucination(self, output_text: str, source_text: str) -> ValidationResult:
        """ハルシネーションを検出"""
        details = []
        warnings = []
        errors = []
        
        # 主張の抽出
        output_claims = self.extract_claims(output_text)
        source_claims = self.extract_claims(source_text)
        
        if not output_claims:
            warnings.append("出力テキストに主張が検出されませんでした")
            return ValidationResult(
                is_valid=True,
                score=1.0,
                details=details,
                warnings=warnings,
                errors=errors,
                timestamp=datetime.now()
            )
        
        # 各主張の類似度を計算
        total_similarity = 0.0
        claim_count = 0
        
        for output_claim in output_claims:
            best_similarity = 0.0
            best_match = ""
            
            for source_claim in source_claims:
                similarity = self.calculate_similarity(output_claim, source_claim)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = source_claim
            
            total_similarity += best_similarity
            claim_count += 1
            
            if best_similarity >= self.similarity_threshold:
                details.append(f"✅ 主張一致: {output_claim[:50]}... (類似度: {best_similarity:.2f})")
            else:
                warnings.append(f"⚠️ 主張不一致: {output_claim[:50]}... (類似度: {best_similarity:.2f})")
        
        if claim_count > 0:
            average_similarity = total_similarity / claim_count
        else:
            average_similarity = 1.0
        
        is_valid = average_similarity >= self.similarity_threshold
        
        return ValidationResult(
            is_valid=is_valid,
            score=average_similarity,
            details=details,
            warnings=warnings,
            errors=errors,
            timestamp=datetime.now()
        )

class StructureValidator:
    """構造整合性検証クラス"""
    
    def __init__(self):
        self.templates = {
            "thesis_antithesis_synthesis": {
                "required_sections": ["テーゼ", "アンチテーゼ", "ジンテーゼ"],
                "section_patterns": {
                    "テーゼ": [r"まず", r"最初に", r"基本的に"],
                    "アンチテーゼ": [r"しかし", r"一方で", r"反対に"],
                    "ジンテーゼ": [r"まとめると", r"結論として", r"最終的に"]
                }
            },
            "youtube_script": {
                "required_sections": ["フック", "導入", "メインコンテンツ", "結論", "アクション呼びかけ"],
                "section_patterns": {
                    "フック": [r"興味深い", r"驚くべき", r"重要な"],
                    "導入": [r"この研究", r"今回の", r"について"],
                    "メインコンテンツ": [r"詳細に", r"具体的に", r"分析すると"],
                    "結論": [r"まとめ", r"結論", r"最終的に"],
                    "アクション呼びかけ": [r"チャンネル登録", r"いいね", r"コメント"]
                }
            }
        }
    
    def detect_sections(self, text: str, template_name: str = "youtube_script") -> Dict[str, List[str]]:
        """テキストからセクションを検出"""
        template = self.templates.get(template_name, self.templates["youtube_script"])
        sections = {}
        
        for section_name, patterns in template["section_patterns"].items():
            section_matches = []
            for pattern in patterns:
                matches = re.findall(pattern, text)
                section_matches.extend(matches)
            sections[section_name] = section_matches
        
        return sections
    
    def validate_structure(self, text: str, template_name: str = "youtube_script") -> ValidationResult:
        """構造の整合性を検証"""
        template = self.templates.get(template_name, self.templates["youtube_script"])
        sections = self.detect_sections(text, template_name)
        
        details = []
        warnings = []
        errors = []
        
        # 必須セクションの存在確認
        missing_sections = []
        present_sections = []
        
        for required_section in template["required_sections"]:
            if required_section in sections and sections[required_section]:
                present_sections.append(required_section)
                details.append(f"✅ セクション存在: {required_section}")
            else:
                missing_sections.append(required_section)
                warnings.append(f"⚠️ セクション不足: {required_section}")
        
        # セクションの順序確認
        section_order_score = self._check_section_order(text, template["required_sections"])
        
        # 文量バランスの確認
        balance_score = self._check_content_balance(sections)
        
        # 総合スコア計算
        presence_score = len(present_sections) / len(template["required_sections"])
        total_score = (presence_score + section_order_score + balance_score) / 3
        
        is_valid = total_score >= 0.7 and len(missing_sections) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            score=total_score,
            details=details,
            warnings=warnings,
            errors=errors,
            timestamp=datetime.now()
        )
    
    def _check_section_order(self, text: str, required_sections: List[str]) -> float:
        """セクションの順序をチェック"""
        # 簡易的な順序チェック（実際の実装ではより詳細な分析が必要）
        text_lower = text.lower()
        order_score = 0.0
        
        for i, section in enumerate(required_sections):
            if section.lower() in text_lower:
                order_score += 1.0
        
        return order_score / len(required_sections)
    
    def _check_content_balance(self, sections: Dict[str, List[str]]) -> float:
        """コンテンツのバランスをチェック"""
        if not sections:
            return 0.0
        
        section_counts = [len(matches) for matches in sections.values()]
        if not section_counts:
            return 0.0
        
        # 標準偏差が小さいほどバランスが良い
        mean_count = np.mean(section_counts)
        std_count = np.std(section_counts)
        
        if mean_count == 0:
            return 0.0
        
        # バランススコア（0-1）
        balance_score = max(0, 1 - (std_count / mean_count))
        return balance_score

class ValidationLogger:
    """検証ログ管理クラス"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def log_validation_result(self, test_name: str, result: ValidationResult) -> None:
        """検証結果をログに記録"""
        log_data = {
            "test_name": test_name,
            "timestamp": result.timestamp.isoformat(),
            "result": result.to_dict()
        }
        
        log_file = f"{self.log_dir}/validation_{test_name}_{self.timestamp}.json"
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            logger.info(f"検証結果を記録: {log_file}")
        except Exception as e:
            logger.error(f"検証結果の記録に失敗: {e}")
    
    def get_validation_summary(self, results: List[Tuple[str, ValidationResult]]) -> Dict[str, Any]:
        """検証結果のサマリーを取得"""
        summary = {
            "total_tests": len(results),
            "passed_tests": sum(1 for _, result in results if result.is_valid),
            "average_score": np.mean([result.score for _, result in results]) if results else 0.0,
            "details": {}
        }
        
        for test_name, result in results:
            summary["details"][test_name] = result.to_dict()
        
        return summary 