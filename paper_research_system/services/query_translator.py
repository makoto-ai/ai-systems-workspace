"""
Query Translation Service for Academic Paper Research
検索クエリ翻訳・改善サービス
"""

import re
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class QueryTranslator:
    """検索クエリの翻訳・改善サービス"""

    def __init__(self):
        # 営業・心理学分野の日本語→英語辞書
        self.sales_psychology_terms = {
            # 営業関連
            "営業": ["sales", "selling", "salesperson"],
            "営業効果": ["sales effectiveness", "sales performance"],
            "営業成果": ["sales results", "sales outcomes"],
            "営業戦略": ["sales strategy", "sales tactics"],
            "営業プロセス": ["sales process", "selling process"],
            "営業管理": ["sales management", "sales administration"],
            "営業スキル": ["sales skills", "selling skills"],
            "営業力": ["sales capability", "sales competency"],
            "顧客": ["customer", "client", "buyer"],
            "顧客満足": ["customer satisfaction", "client satisfaction"],
            "顧客関係": ["customer relationship", "client relationship"],
            "購買": ["purchasing", "buying behavior"],
            "購買意思決定": ["buying decision", "purchase decision"],
            "消費者行動": ["consumer behavior", "buyer behavior"],
            # 心理学関連
            "心理学": ["psychology", "psychological"],
            "心理": ["psychology", "psychological", "mental"],
            "行動": ["behavior", "behaviour", "behavioral"],
            "認知": ["cognition", "cognitive"],
            "動機": ["motivation", "motivational"],
            "態度": ["attitude", "attitudinal"],
            "説得": ["persuasion", "persuasive"],
            "影響": ["influence", "influential"],
            "意思決定": ["decision making", "decision-making"],
            "信頼": ["trust", "credibility"],
            "コミュニケーション": ["communication", "interpersonal"],
            "対人関係": ["interpersonal relationship", "social relationship"],
            "社会心理学": ["social psychology", "social psychological"],
            "組織心理学": ["organizational psychology", "industrial psychology"],
            "消費者心理": ["consumer psychology", "buyer psychology"],
            # ビジネス心理学
            "ビジネス心理学": ["business psychology", "organizational psychology"],
            "組織行動": ["organizational behavior", "organizational behaviour"],
            "リーダーシップ": ["leadership", "leadership behavior"],
            "チームワーク": ["teamwork", "team collaboration"],
            "コーチング": ["coaching", "business coaching"],
            "交渉": ["negotiation", "bargaining"],
            "プレゼンテーション": ["presentation", "presentation skills"],
            # 効果測定
            "効果": ["effectiveness", "effect", "impact"],
            "成果": ["performance", "results", "outcomes"],
            "改善": ["improvement", "enhancement"],
            "向上": ["improvement", "enhancement", "development"],
            "測定": ["measurement", "evaluation", "assessment"],
            "分析": ["analysis", "analytical"],
            "評価": ["evaluation", "assessment"],
        }

        # 学術分野フィルタ
        self.academic_concepts = [
            "concept",
            "theory",
            "model",
            "framework",
            "approach",
            "study",
            "research",
            "analysis",
            "investigation",
            "empirical",
            "experimental",
            "quantitative",
            "qualitative",
        ]

    def translate_japanese_query(self, query: str) -> List[str]:
        """日本語クエリを英語クエリリストに変換"""
        # 1. 基本的な単語分割
        words = re.findall(r"[ぁ-んァ-ヶ一-龯]+|[a-zA-Z]+", query)

        # 2. 各単語を英語変換
        english_terms = []
        for word in words:
            if word in self.sales_psychology_terms:
                english_terms.extend(self.sales_psychology_terms[word])
            else:
                # 部分マッチも試す
                for jp_term, en_terms in self.sales_psychology_terms.items():
                    if jp_term in word or word in jp_term:
                        english_terms.extend(en_terms)
                        break

        # 3. 重複除去
        english_terms = list(set(english_terms))

        # 4. クエリパターン生成
        queries = []

        if len(english_terms) >= 2:
            # 複合クエリ（AND検索）
            for i, term1 in enumerate(english_terms[:3]):
                for term2 in english_terms[i + 1 : 4]:
                    queries.append(f"{term1} AND {term2}")

        # 5. 個別キーワード
        queries.extend(english_terms[:5])

        # 6. 学術的表現を追加
        if english_terms:
            primary_term = english_terms[0]
            for concept in self.academic_concepts[:3]:
                queries.append(f"{primary_term} {concept}")

        return queries[:8]  # 最大8クエリ

    def enhance_query_for_sales_psychology(self, base_query: str) -> str:
        """営業・心理学分野に特化したクエリ拡張"""
        enhanced_terms = []

        # ベースクエリを分析
        base_lower = base_query.lower()

        # 営業関連の場合
        if any(term in base_lower for term in ["sales", "selling", "salesperson"]):
            enhanced_terms.extend(
                [
                    "sales effectiveness",
                    "sales performance",
                    "sales psychology",
                    "buyer behavior",
                    "customer relationship",
                    "persuasion",
                ]
            )

        # 心理学関連の場合
        if any(
            term in base_lower for term in ["psychology", "psychological", "behavior"]
        ):
            enhanced_terms.extend(
                [
                    "consumer psychology",
                    "social psychology",
                    "decision making",
                    "motivation",
                    "attitude",
                    "influence",
                ]
            )

        # ビジネス関連の場合
        if any(
            term in base_lower for term in ["business", "organization", "management"]
        ):
            enhanced_terms.extend(
                [
                    "organizational behavior",
                    "business psychology",
                    "leadership",
                    "communication",
                    "negotiation",
                ]
            )

        # 拡張クエリ生成
        if enhanced_terms:
            # 最も関連性の高い2-3語を追加
            return f"{base_query} ({' OR '.join(enhanced_terms[:3])})"

        return base_query

    def get_domain_filters(self) -> Dict[str, List[str]]:
        """営業・心理学分野のフィルタ条件を取得"""
        return {
            "concepts": [
                # OpenAlex concept IDs for relevant fields
                "psychology",
                "social psychology",
                "cognitive psychology",
                "organizational behavior",
                "business",
                "marketing",
                "management",
                "economics",
                "decision making",
                "consumer behavior",
            ],
            "keywords": [
                "sales",
                "selling",
                "psychology",
                "behavior",
                "motivation",
                "persuasion",
                "influence",
                "decision",
                "consumer",
                "buyer",
                "customer",
                "relationship",
                "communication",
                "negotiation",
                "leadership",
                "organizational",
                "business",
            ],
        }


# サービスインスタンス作成用関数


def get_query_translator() -> QueryTranslator:
    """QueryTranslator インスタンスを取得"""
    return QueryTranslator()
