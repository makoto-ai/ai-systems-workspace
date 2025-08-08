"""
Specialized Search Service for Sales, Management & Psychology Research
営業・マネジメント・心理学特化検索サービス
"""

from core.paper_model import Paper
from services.safe_rate_limited_search_service import SafeRateLimitedSearchService
from typing import List, Dict, Optional, Tuple
import logging
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))


logger = logging.getLogger(__name__)


class SpecializedSearchService:
    """営業・マネジメント・心理学特化検索サービス"""

    def __init__(self):
        self.base_search = SafeRateLimitedSearchService()
        self.domain_taxonomy = self._build_domain_taxonomy()
        self.critical_thinking_modes = self._build_critical_thinking_modes()

    def _build_domain_taxonomy(self) -> Dict[str, Dict]:
        """専門分野の詳細分類体系"""
        return {
            "sales_psychology": {
                "name": "営業心理学",
                "core_concepts": [
                    "sales psychology", "selling behavior", "buyer psychology",
                    "customer persuasion", "sales techniques", "prospecting",
                    "closing techniques", "objection handling", "relationship selling",
                    "consultative selling", "value-based selling", "trust building"
                ],
                "behavioral_economics": [
                    "behavioral economics", "loss aversion", "anchoring bias",
                    "framing effects", "social proof", "scarcity principle",
                    "commitment consistency", "reciprocity", "authority influence"
                ],
                "neuroscience": [
                    "neuromarketing", "consumer neuroscience", "decision neuroscience",
                    "emotional decision making", "cognitive bias", "mental models"
                ],
                "filters": ["sales", "selling", "buyer", "customer", "prospect", "persuasion"]
            },

            "management_psychology": {
                "name": "マネジメント心理学",
                "leadership": [
                    "leadership psychology", "transformational leadership",
                    "authentic leadership", "servant leadership", "charismatic leadership",
                    "emotional intelligence", "leader effectiveness", "leadership styles"
                ],
                "team_dynamics": [
                    "team psychology", "group dynamics", "team effectiveness",
                    "psychological safety", "team cohesion", "conflict resolution",
                    "team communication", "collaborative behavior"
                ],
                "motivation": [
                    "motivation psychology", "intrinsic motivation", "goal setting theory",
                    "self-determination theory", "achievement motivation",
                    "performance motivation", "employee engagement"
                ],
                "filters": ["management", "leadership", "team", "motivation", "organization"]
            },

            "behavioral_economics": {
                "name": "行動経済学",
                "decision_making": [
                    "behavioral economics", "decision theory", "prospect theory",
                    "bounded rationality", "cognitive biases", "heuristics",
                    "mental accounting", "temporal discounting"
                ],
                "social_psychology": [
                    "social influence", "conformity", "social norms",
                    "social identity", "in-group bias", "social comparison",
                    "social learning", "observational learning"
                ],
                "market_behavior": [
                    "market psychology", "investor behavior", "consumer choice",
                    "price psychology", "brand psychology", "purchasing decisions"
                ],
                "filters": ["behavioral", "decision", "bias", "psychology", "economics"]
            },

            "universal_psychology": {
                "name": "汎用心理学",
                "cognitive_psychology": [
                    "cognitive psychology", "information processing", "memory",
                    "attention", "perception", "learning", "problem solving"
                ],
                "personality": [
                    "personality psychology", "big five", "personality traits",
                    "individual differences", "temperament", "character"
                ],
                "social_psychology": [
                    "social psychology", "interpersonal relations", "communication",
                    "attitude change", "group behavior", "social cognition"
                ],
                "filters": ["psychology", "behavior", "cognitive", "personality", "social"]
            }
        }

    def _build_critical_thinking_modes(self) -> Dict[str, Dict]:
        """クリティカルシンキング検索モード"""
        return {
            "thesis": {
                "name": "テーゼ（主流理論）",
                "search_focus": [
                    "meta-analysis",
                    "systematic review",
                    "established theory",
                    "consensus",
                    "empirical evidence",
                    "validated model"],
                "sort_criteria": "citation_count_desc",
                "description": "確立された理論・実証された効果を重視"},
            "antithesis": {
                "name": "アンチテーゼ（反対・批判研究）",
                "search_focus": [
                    "criticism",
                    "limitations",
                    "contradictory findings",
                    "alternative explanation",
                    "replication failure",
                    "debate"],
                "sort_criteria": "relevance_score_desc",
                "description": "主流理論への批判・反証・限界を重視"},
            "synthesis": {
                "name": "ジンテーゼ（統合・発展）",
                        "search_focus": [
                            "integrative model",
                            "framework",
                            "reconciliation",
                            "boundary conditions",
                            "moderating factors",
                            "contingency"],
                "sort_criteria": "total_score_desc",
                "description": "理論の統合・発展・応用条件を重視"},
            "meta_analysis": {
                "name": "メタ分析重視",
                "search_focus": [
                    "meta-analysis",
                    "systematic review",
                    "review",
                    "analysis of analyses",
                    "quantitative review"],
                "sort_criteria": "citation_count_desc",
                "description": "複数研究を統合したメタ分析を優先"}}

    async def specialized_search(self,
                                 query: str,
                                 domain: str = "sales_psychology",
                                 thinking_mode: str = "thesis",
                                 max_results: int = 10) -> Tuple[List[Paper],
                                                                 Dict[str,
                                                                      any]]:
        """
        特化検索の実行

        Args:
            query: 基本検索クエリ
            domain: 専門分野 (sales_psychology, management_psychology, etc.)
            thinking_mode: 思考モード (thesis, antithesis, synthesis, meta_analysis)
            max_results: 最大結果数

        Returns:
            (論文リスト, メタデータ)
        """
        logger.info(f"特化検索開始: '{query}' | 分野:{domain} | モード:{thinking_mode}")

        # 1. ドメイン特化クエリ生成
        enhanced_queries = self._generate_domain_queries(query, domain)

        # 2. クリティカルシンキングモード適用
        critical_queries = self._apply_critical_thinking_mode(
            enhanced_queries, thinking_mode)

        # 3. 並列検索実行
        all_papers = []
        search_metadata = {
            "original_query": query,
            "domain": domain,
            "thinking_mode": thinking_mode,
            "generated_queries": critical_queries,
            "search_stats": {}
        }

        for enhanced_query in critical_queries[:5]:  # 上位5クエリ
            papers = await self.base_search.search_papers(enhanced_query, max(1, max_results // len(critical_queries[:5])))
            all_papers.extend(papers)
            search_metadata["search_stats"][enhanced_query] = len(papers)

        # 4. 特化フィルタリング・ランキング
        filtered_papers = self._apply_domain_filtering(
            all_papers, domain, thinking_mode)

        # 5. 最終ランキング
        final_papers = self._rank_papers_by_mode(
            filtered_papers, thinking_mode, max_results)

        search_metadata["final_count"] = len(final_papers)
        search_metadata["filtering_stats"] = {
            "total_found": len(all_papers),
            "after_filtering": len(filtered_papers),
            "final_results": len(final_papers)
        }

        logger.info(
            f"特化検索完了: {
                len(all_papers)}件 → {
                len(filtered_papers)}件 → {
                len(final_papers)}件")

        return final_papers, search_metadata

    def _generate_domain_queries(
            self,
            base_query: str,
            domain: str) -> List[str]:
        """ドメイン特化クエリ生成"""
        domain_config = self.domain_taxonomy.get(domain, {})
        queries = [base_query]  # 元クエリも含める

        # ドメイン概念との組み合わせ
        for concept_category, concepts in domain_config.items():
            if concept_category == "name" or concept_category == "filters":
                continue

            if isinstance(concepts, list):
                # 主要概念との組み合わせ
                for concept in concepts[:3]:  # 上位3概念
                    queries.append(f"{base_query} {concept}")
                    queries.append(f"{concept} {base_query}")

        # フィルタキーワードとの組み合わせ
        filters = domain_config.get("filters", [])
        for filter_word in filters[:2]:
            queries.append(f"{base_query} {filter_word}")

        return list(set(queries))  # 重複除去

    def _apply_critical_thinking_mode(
            self,
            queries: List[str],
            mode: str) -> List[str]:
        """クリティカルシンキングモード適用"""
        mode_config = self.critical_thinking_modes.get(mode, {})
        focus_terms = mode_config.get("search_focus", [])

        enhanced_queries = queries.copy()

        # モード特化の追加クエリ
        for query in queries[:3]:  # 主要クエリのみ
            for focus_term in focus_terms[:2]:  # 上位2フォーカス
                enhanced_queries.append(f"{query} {focus_term}")

        return enhanced_queries

    def _apply_domain_filtering(
            self,
            papers: List[Paper],
            domain: str,
            mode: str) -> List[Paper]:
        """ドメイン特化フィルタリング"""
        domain_config = self.domain_taxonomy.get(domain, {})
        mode_config = self.critical_thinking_modes.get(mode, {})

        filtered_papers = []

        for paper in papers:
            # ドメイン関連性スコア計算
            domain_score = self._calculate_domain_relevance(
                paper, domain_config)

            # クリティカルシンキングモード関連性
            mode_score = self._calculate_mode_relevance(paper, mode_config)

            # 総合判定（適切なフィルタリング）
            if domain_score >= 0.1 or mode_score >= 0.1 or (
                    domain_score + mode_score) >= 0.2:
                paper.domain_score = domain_score
                paper.mode_score = mode_score
                filtered_papers.append(paper)

        return filtered_papers

    def _calculate_domain_relevance(
            self,
            paper: Paper,
            domain_config: Dict) -> float:
        """ドメイン関連性スコア計算"""
        score = 0.0
        text_to_check = f"{paper.title} {paper.abstract or ''}".lower()

        # 各概念カテゴリでの一致度チェック
        for category, concepts in domain_config.items():
            if category in [
                    "name",
                    "filters"] or not isinstance(
                    concepts,
                    list):
                continue

            category_matches = sum(
                1 for concept in concepts if concept.lower() in text_to_check)
            category_score = min(category_matches * 0.5, 2.0)  # カテゴリあたり最大2点
            score += category_score

        return score

    def _calculate_mode_relevance(
            self,
            paper: Paper,
            mode_config: Dict) -> float:
        """クリティカルシンキングモード関連性"""
        score = 0.0
        text_to_check = f"{paper.title} {paper.abstract or ''}".lower()
        focus_terms = mode_config.get("search_focus", [])

        # フォーカス用語での一致度
        matches = sum(
            1 for term in focus_terms if term.lower() in text_to_check)
        score = min(matches * 1.0, 3.0)  # 最大3点

        # メタ分析モードの場合は特別扱い
        if mode_config.get("name") == "メタ分析重視":
            meta_terms = ["meta-analysis", "systematic review", "review"]
            if any(term in text_to_check for term in meta_terms):
                score += 5.0  # メタ分析ボーナス

        return score

    def _rank_papers_by_mode(
            self,
            papers: List[Paper],
            mode: str,
            max_results: int) -> List[Paper]:
        """モード別ランキング"""
        mode_config = self.critical_thinking_modes.get(mode, {})
        sort_criteria = mode_config.get("sort_criteria", "total_score_desc")

        # カスタムスコア計算
        for paper in papers:
            paper.specialized_score = self._calculate_specialized_score(
                paper, mode)

        # ソート
        if sort_criteria == "citation_count_desc":
            papers.sort(key=lambda p: (p.citation_count or 0), reverse=True)
        elif sort_criteria == "relevance_score_desc":
            papers.sort(key=lambda p: (p.relevance_score or 0), reverse=True)
        else:  # total_score_desc
            papers.sort(key=lambda p: (p.specialized_score or 0), reverse=True)

        return papers[:max_results]

    def _calculate_specialized_score(self, paper: Paper, mode: str) -> float:
        """特化スコア計算"""
        base_score = paper.total_score or 0
        domain_bonus = getattr(paper, 'domain_score', 0) * 2
        mode_bonus = getattr(paper, 'mode_score', 0) * 1.5

        # メタ分析特別ボーナス
        if "meta-analysis" in (paper.title + (paper.abstract or "")).lower():
            meta_bonus = 5.0
        else:
            meta_bonus = 0.0

        return base_score + domain_bonus + mode_bonus + meta_bonus

# インスタンス取得関数


def get_specialized_search_service() -> SpecializedSearchService:
    """SpecializedSearchService インスタンスを取得"""
    return SpecializedSearchService()
