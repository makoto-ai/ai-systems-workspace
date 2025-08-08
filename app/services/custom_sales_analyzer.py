from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class CustomSalesAnalyzer:
    """
    カスタマイズ可能な営業分析サービス
    ユーザー独自の視点と評価基準を実装可能
    """
    
    def __init__(self, custom_config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            custom_config: ユーザー独自の設定
        """
        self.config = custom_config or {}
        self.initialize_default_criteria()
        
    def initialize_default_criteria(self):
        """デフォルトの評価基準を初期化"""
        self.default_criteria = {
            "rapport_building": {
                "description": "信頼関係構築力",
                "keywords": ["お忙しい", "お時間", "ありがとう", "恐れ入ります"],
                "tone_indicators": ["丁寧", "親しみやすい", "配慮"],
                "weight": 0.25,
                "min_score": 0.6,
                "excellent_threshold": 0.8
            },
            "needs_discovery": {
                "description": "ニーズ発見力",
                "question_patterns": ["現在", "課題", "お困り", "どのような", "いかがですか"],
                "follow_up_depth": 2,
                "weight": 0.3,
                "min_score": 0.7,
                "excellent_threshold": 0.85
            },
            "value_proposition": {
                "description": "価値提案力",
                "benefit_keywords": ["効率", "削減", "向上", "改善", "最適化"],
                "concrete_examples": True,
                "roi_mention": True,
                "weight": 0.25,
                "min_score": 0.65,
                "excellent_threshold": 0.8
            },
            "objection_handling": {
                "description": "異議処理力",
                "acknowledgment_patterns": ["おっしゃる通り", "確かに", "理解できます"],
                "solution_focus": True,
                "weight": 0.2,
                "min_score": 0.6,
                "excellent_threshold": 0.85
            }
        }
        
    def load_custom_criteria(self, criteria_file: str):
        """
        カスタム評価基準をファイルから読み込み
        
        Args:
            criteria_file: 評価基準ファイルのパス
        """
        try:
            with open(criteria_file, 'r', encoding='utf-8') as f:
                custom_criteria = json.load(f)
            
            # デフォルト基準とマージ
            for key, value in custom_criteria.items():
                if key in self.default_criteria:
                    self.default_criteria[key].update(value)
                else:
                    self.default_criteria[key] = value
                    
            logger.info(f"Custom criteria loaded from {criteria_file}")
            
        except Exception as e:
            logger.error(f"Failed to load custom criteria: {e}")
            
    async def analyze_with_custom_perspective(
        self,
        conversation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        独自視点での営業分析
        
        Args:
            conversation_data: 会話データ
            
        Returns:
            カスタム分析結果
        """
        try:
            # 基本分析
            basic_analysis = await self._perform_basic_analysis(conversation_data)
            
            # 独自視点分析
            custom_analysis = await self._perform_custom_analysis(conversation_data)
            
            # 総合評価
            overall_assessment = self._calculate_overall_assessment(
                basic_analysis, custom_analysis
            )
            
            # 改善提案
            improvement_suggestions = self._generate_improvement_suggestions(
                basic_analysis, custom_analysis
            )
            
            return {
                "timestamp": datetime.now().isoformat(),
                "basic_analysis": basic_analysis,
                "custom_analysis": custom_analysis,
                "overall_assessment": overall_assessment,
                "improvement_suggestions": improvement_suggestions,
                "next_focus_areas": self._identify_next_focus_areas(custom_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error in custom analysis: {e}")
            return {"error": str(e)}
    
    async def _perform_basic_analysis(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """基本的な営業分析"""
        text = conversation_data.get("text", "")
        
        # 信頼関係構築の評価
        rapport_score = self._evaluate_rapport_building(text)
        
        # ニーズ発見の評価
        needs_discovery_score = self._evaluate_needs_discovery(text, conversation_data)
        
        # 価値提案の評価
        value_prop_score = self._evaluate_value_proposition(text)
        
        # 異議処理の評価
        objection_score = self._evaluate_objection_handling(text, conversation_data)
        
        return {
            "rapport_building": rapport_score,
            "needs_discovery": needs_discovery_score,
            "value_proposition": value_prop_score,
            "objection_handling": objection_score
        }
    
    async def _perform_custom_analysis(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """ユーザー独自の分析ロジック"""
        # ここに独自の分析ロジックを実装
        # 例：業界特化の分析
        industry_analysis = self._analyze_industry_specific_aspects(conversation_data)
        
        # 例：個人のコーチング方針に基づく分析
        coaching_analysis = self._analyze_coaching_perspective(conversation_data)
        
        # 例：感情的知性（EQ）の分析
        emotional_intelligence = self._analyze_emotional_intelligence(conversation_data)
        
        return {
            "industry_specific": industry_analysis,
            "coaching_perspective": coaching_analysis,
            "emotional_intelligence": emotional_intelligence
        }
    
    def _evaluate_rapport_building(self, text: str) -> Dict[str, Any]:
        """信頼関係構築力の評価"""
        criteria = self.default_criteria["rapport_building"]
        
        # キーワードの出現頻度
        keyword_count = sum(1 for keyword in criteria["keywords"] if keyword in text)
        keyword_score = min(keyword_count / len(criteria["keywords"]), 1.0)
        
        # 丁寧語の使用
        polite_expressions = ["です", "ます", "ございます", "いただき"]
        polite_score = sum(1 for expr in polite_expressions if expr in text) / len(polite_expressions)
        
        # 総合スコア
        total_score = (keyword_score * 0.6 + polite_score * 0.4)
        
        return {
            "score": total_score,
            "breakdown": {
                "keyword_usage": keyword_score,
                "politeness": polite_score
            },
            "rating": self._convert_to_rating(total_score, criteria),
            "suggestions": self._generate_rapport_suggestions(total_score)
        }
    
    def _evaluate_needs_discovery(self, text: str, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """ニーズ発見力の評価"""
        criteria = self.default_criteria["needs_discovery"]
        
        # 質問の数と質
        question_count = text.count("？") + text.count("?")
        question_patterns = criteria["question_patterns"]
        quality_questions = sum(1 for pattern in question_patterns if pattern in text)
        
        # 深掘り質問の評価
        follow_up_score = self._evaluate_follow_up_questions(conversation_data)
        
        # 総合スコア
        question_score = min(question_count / 5, 1.0)  # 5つの質問で満点
        quality_score = min(quality_questions / len(question_patterns), 1.0)
        
        total_score = (question_score * 0.3 + quality_score * 0.4 + follow_up_score * 0.3)
        
        return {
            "score": total_score,
            "breakdown": {
                "question_quantity": question_score,
                "question_quality": quality_score,
                "follow_up_depth": follow_up_score
            },
            "rating": self._convert_to_rating(total_score, criteria),
            "suggestions": self._generate_needs_discovery_suggestions(total_score)
        }
    
    def _evaluate_value_proposition(self, text: str) -> Dict[str, Any]:
        """価値提案力の評価"""
        criteria = self.default_criteria["value_proposition"]
        
        # 利益に関するキーワード
        benefit_keywords = criteria["benefit_keywords"]
        benefit_score = sum(1 for keyword in benefit_keywords if keyword in text) / len(benefit_keywords)
        
        # 具体例の提示
        concrete_indicators = ["例えば", "具体的には", "実際に", "事例として"]
        concrete_score = min(sum(1 for indicator in concrete_indicators if indicator in text) / 2, 1.0)
        
        # ROI言及
        roi_indicators = ["投資", "リターン", "効果", "削減", "節約"]
        roi_score = min(sum(1 for indicator in roi_indicators if indicator in text) / 3, 1.0)
        
        total_score = (benefit_score * 0.4 + concrete_score * 0.3 + roi_score * 0.3)
        
        return {
            "score": total_score,
            "breakdown": {
                "benefit_focus": benefit_score,
                "concrete_examples": concrete_score,
                "roi_mention": roi_score
            },
            "rating": self._convert_to_rating(total_score, criteria),
            "suggestions": self._generate_value_prop_suggestions(total_score)
        }
    
    def _evaluate_objection_handling(self, text: str, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """異議処理力の評価"""
        criteria = self.default_criteria["objection_handling"]
        
        # 異議の存在確認
        objection_indicators = ["しかし", "ただ", "でも", "難しい", "心配"]
        has_objections = any(indicator in text for indicator in objection_indicators)
        
        if not has_objections:
            return {
                "score": 0.0,
                "rating": "N/A",
                "message": "異議処理の機会がありませんでした"
            }
        
        # 受容表現
        acknowledgment_patterns = criteria["acknowledgment_patterns"]
        acknowledgment_score = sum(1 for pattern in acknowledgment_patterns if pattern in text) / len(acknowledgment_patterns)
        
        # 解決策提示
        solution_indicators = ["提案", "解決", "対応", "方法", "できます"]
        solution_score = min(sum(1 for indicator in solution_indicators if indicator in text) / 3, 1.0)
        
        total_score = (acknowledgment_score * 0.5 + solution_score * 0.5)
        
        return {
            "score": total_score,
            "breakdown": {
                "acknowledgment": acknowledgment_score,
                "solution_focus": solution_score
            },
            "rating": self._convert_to_rating(total_score, criteria),
            "suggestions": self._generate_objection_handling_suggestions(total_score)
        }
    
    def _analyze_industry_specific_aspects(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """業界特化の分析"""
        # 業界固有の要素を分析
        # 例：IT業界なら技術用語の適切な使用
        # 例：製造業なら品質・コスト・納期の言及
        
        industry = conversation_data.get("industry", "general")
        
        if industry == "IT":
            return self._analyze_it_industry_aspects(conversation_data)
        elif industry == "manufacturing":
            return self._analyze_manufacturing_aspects(conversation_data)
        else:
            return self._analyze_general_industry_aspects(conversation_data)
    
    def _analyze_coaching_perspective(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """コーチング視点での分析"""
        # 個人のコーチング方針に基づく分析
        text = conversation_data.get("text", "")
        
        # 例：積極性の評価
        assertiveness = self._evaluate_assertiveness(text)
        
        # 例：共感力の評価
        empathy = self._evaluate_empathy(text)
        
        # 例：論理性の評価
        logical_thinking = self._evaluate_logical_thinking(text)
        
        return {
            "assertiveness": assertiveness,
            "empathy": empathy,
            "logical_thinking": logical_thinking
        }
    
    def _analyze_emotional_intelligence(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """感情的知性の分析"""
        text = conversation_data.get("text", "")
        
        # 感情認識
        emotion_recognition = self._evaluate_emotion_recognition(text)
        
        # 感情調整
        emotion_regulation = self._evaluate_emotion_regulation(text)
        
        # 社会的認識
        social_awareness = self._evaluate_social_awareness(text)
        
        return {
            "emotion_recognition": emotion_recognition,
            "emotion_regulation": emotion_regulation,
            "social_awareness": social_awareness,
            "overall_eq": (emotion_recognition + emotion_regulation + social_awareness) / 3
        }
    
    def _convert_to_rating(self, score: float, criteria: Dict[str, Any]) -> str:
        """スコアを評価レベルに変換"""
        if score >= criteria.get("excellent_threshold", 0.8):
            return "Excellent"
        elif score >= criteria.get("min_score", 0.6):
            return "Good"
        elif score >= 0.4:
            return "Needs Improvement"
        else:
            return "Poor"
    
    def _calculate_overall_assessment(self, basic_analysis: Dict[str, Any], custom_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """総合評価の計算"""
        # 基本スコアの重み付け平均
        basic_scores = [
            basic_analysis["rapport_building"]["score"] * self.default_criteria["rapport_building"]["weight"],
            basic_analysis["needs_discovery"]["score"] * self.default_criteria["needs_discovery"]["weight"],
            basic_analysis["value_proposition"]["score"] * self.default_criteria["value_proposition"]["weight"],
            basic_analysis["objection_handling"]["score"] * self.default_criteria["objection_handling"]["weight"]
        ]
        
        basic_weighted_score = sum(basic_scores)
        
        # カスタム分析の統合
        custom_score = 0.0
        if "emotional_intelligence" in custom_analysis:
            custom_score = custom_analysis["emotional_intelligence"]["overall_eq"]
        
        # 総合スコア
        overall_score = (basic_weighted_score * 0.8 + custom_score * 0.2)
        
        return {
            "overall_score": overall_score,
            "performance_level": self._get_performance_level(overall_score),
            "strengths": self._identify_strengths(basic_analysis),
            "areas_for_improvement": self._identify_improvement_areas(basic_analysis),
            "custom_insights": custom_analysis
        }
    
    def _generate_improvement_suggestions(self, basic_analysis: Dict[str, Any], custom_analysis: Dict[str, Any]) -> List[str]:
        """改善提案の生成"""
        suggestions = []
        
        # 基本スキルの改善提案
        for skill, analysis in basic_analysis.items():
            if analysis["score"] < self.default_criteria[skill]["min_score"]:
                suggestions.extend(analysis.get("suggestions", []))
        
        # カスタム分析に基づく提案
        if "emotional_intelligence" in custom_analysis:
            eq_score = custom_analysis["emotional_intelligence"]["overall_eq"]
            if eq_score < 0.7:
                suggestions.append("感情的知性の向上：相手の感情をより敏感に察知し、適切に対応する練習をしましょう")
        
        return suggestions
    
    def _identify_next_focus_areas(self, custom_analysis: Dict[str, Any]) -> List[str]:
        """次回の重点領域の特定"""
        focus_areas = []
        
        # 業界特化の提案
        if "industry_specific" in custom_analysis:
            focus_areas.append("業界固有の課題により深く対応する")
        
        # コーチング視点の提案
        if "coaching_perspective" in custom_analysis:
            coaching = custom_analysis["coaching_perspective"]
            if coaching.get("assertiveness", 0) < 0.6:
                focus_areas.append("より積極的な提案とクロージング")
            if coaching.get("empathy", 0) < 0.6:
                focus_areas.append("顧客との共感構築")
        
        return focus_areas
    
    # 以下、各種評価メソッドの実装
    def _evaluate_follow_up_questions(self, conversation_data: Dict[str, Any]) -> float:
        """深掘り質問の評価"""
        # 簡単な実装例
        return 0.7
    
    def _evaluate_assertiveness(self, text: str) -> float:
        """積極性の評価"""
        assertive_indicators = ["提案", "おすすめ", "ぜひ", "いかがでしょうか"]
        score = sum(1 for indicator in assertive_indicators if indicator in text) / len(assertive_indicators)
        return min(score, 1.0)
    
    def _evaluate_empathy(self, text: str) -> float:
        """共感力の評価"""
        empathy_indicators = ["理解", "わかります", "大変", "お困り"]
        score = sum(1 for indicator in empathy_indicators if indicator in text) / len(empathy_indicators)
        return min(score, 1.0)
    
    def _evaluate_logical_thinking(self, text: str) -> float:
        """論理性の評価"""
        logical_indicators = ["理由", "根拠", "データ", "実績", "結果"]
        score = sum(1 for indicator in logical_indicators if indicator in text) / len(logical_indicators)
        return min(score, 1.0)
    
    def _evaluate_emotion_recognition(self, text: str) -> float:
        """感情認識の評価"""
        return 0.6  # 実装例
    
    def _evaluate_emotion_regulation(self, text: str) -> float:
        """感情調整の評価"""
        return 0.7  # 実装例
    
    def _evaluate_social_awareness(self, text: str) -> float:
        """社会的認識の評価"""
        return 0.6  # 実装例
    
    def _analyze_it_industry_aspects(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """IT業界特化分析"""
        return {"industry_focus": "IT", "technical_appropriateness": 0.8}
    
    def _analyze_manufacturing_aspects(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """製造業特化分析"""
        return {"industry_focus": "Manufacturing", "qcd_focus": 0.7}
    
    def _analyze_general_industry_aspects(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """一般業界分析"""
        return {"industry_focus": "General", "general_effectiveness": 0.6}
    
    def _get_performance_level(self, score: float) -> str:
        """パフォーマンスレベルの判定"""
        if score >= 0.8:
            return "優秀"
        elif score >= 0.6:
            return "良好"
        elif score >= 0.4:
            return "要改善"
        else:
            return "要大幅改善"
    
    def _identify_strengths(self, basic_analysis: Dict[str, Any]) -> List[str]:
        """強みの特定"""
        strengths = []
        for skill, analysis in basic_analysis.items():
            if analysis["score"] >= 0.8:
                strengths.append(f"{skill}が優秀")
        return strengths
    
    def _identify_improvement_areas(self, basic_analysis: Dict[str, Any]) -> List[str]:
        """改善領域の特定"""
        areas = []
        for skill, analysis in basic_analysis.items():
            if analysis["score"] < 0.6:
                areas.append(f"{skill}の強化が必要")
        return areas
    
    def _generate_rapport_suggestions(self, score: float) -> List[str]:
        """信頼関係構築の提案"""
        if score < 0.6:
            return [
                "より丁寧な言葉遣いを心がけましょう",
                "相手の時間を気遣う表現を増やしましょう",
                "感謝の気持ちをより表現しましょう"
            ]
        return []
    
    def _generate_needs_discovery_suggestions(self, score: float) -> List[str]:
        """ニーズ発見の提案"""
        if score < 0.7:
            return [
                "より多くの質問で顧客の状況を把握しましょう",
                "オープンクエスチョンを増やしましょう",
                "答えに対してさらに深掘りしましょう"
            ]
        return []
    
    def _generate_value_prop_suggestions(self, score: float) -> List[str]:
        """価値提案の提案"""
        if score < 0.65:
            return [
                "具体的な利益を明示しましょう",
                "事例や実績を交えて説明しましょう",
                "ROIを数値で示しましょう"
            ]
        return []
    
    def _generate_objection_handling_suggestions(self, score: float) -> List[str]:
        """異議処理の提案"""
        if score < 0.6:
            return [
                "相手の懸念をまず受け止めましょう",
                "解決策を具体的に提示しましょう",
                "相手の立場に立って考えましょう"
            ]
        return [] 