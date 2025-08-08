from typing import Dict, Any, List, Optional, Tuple
import re
import logging
from dataclasses import dataclass
from enum import Enum
try:
    from services.friendliness_analyzer import friendliness_analyzer, FriendlinessLevel
except ImportError:
    from app.services.friendliness_analyzer import friendliness_analyzer, FriendlinessLevel

logger = logging.getLogger(__name__)

class PolitenessLevel(Enum):
    """丁寧度レベル"""
    VERY_FORMAL = "very_formal"      # 非常に丁寧（尊敬語・謙譲語多用）
    FORMAL = "formal"                # 丁寧（基本的な敬語使用）
    BUSINESS = "business"            # ビジネス標準
    CASUAL = "casual"                # カジュアル
    TOO_CASUAL = "too_casual"        # 営業には不適切

class LanguageIssueType(Enum):
    """言葉遣いの問題タイプ"""
    INCORRECT_KEIGO = "incorrect_keigo"           # 敬語の誤用
    TOO_CASUAL = "too_casual"                    # カジュアルすぎる
    UNCLEAR_EXPRESSION = "unclear_expression"     # 曖昧な表現
    INAPPROPRIATE_WORD = "inappropriate_word"     # 不適切な語彙
    MISSING_POLITENESS = "missing_politeness"    # 丁寧語不足
    EXCESSIVE_FORMALITY = "excessive_formality"  # 過度に堅い

@dataclass
class LanguageIssue:
    """言葉遣いの問題"""
    issue_type: LanguageIssueType
    position: int
    original_text: str
    suggested_fix: str
    severity: float  # 0.0-1.0
    explanation: str

@dataclass
class PolitenessAnalysis:
    """丁寧語分析結果"""
    level: PolitenessLevel
    score: float
    keigo_usage: Dict[str, Any]
    politeness_indicators: List[str]
    missing_elements: List[str]

class LanguageAnalysisService:
    """言葉遣い分析サービス"""
    
    def __init__(self):
        self.initialize_language_patterns()
        
    def initialize_language_patterns(self):
        """言語パターンの初期化"""
        
        # 敬語パターン
        self.keigo_patterns = {
            "sonkeigo": {  # 尊敬語
                "patterns": [
                    r"いらっしゃる", r"おっしゃる", r"なさる", r"お.*になる",
                    r"ご.*になる", r".*れる", r".*られる"
                ],
                "examples": ["いらっしゃいます", "おっしゃる通り", "お考えになる"]
            },
            "kenjougo": {  # 謙譲語
                "patterns": [
                    r"申し上げる", r"お.*する", r"ご.*する", r"させていただく",
                    r"伺う", r"拝見", r"頂戴", r"恐れ入り"
                ],
                "examples": ["申し上げます", "お伺いします", "ご提案いたします"]
            },
            "teineigo": {  # 丁寧語
                "patterns": [
                    r"です", r"ます", r"ございます", r"であります"
                ],
                "examples": ["です", "ます", "ございます"]
            }
        }
        
        # ビジネス適切表現
        self.business_expressions = {
            "opening": [
                "お忙しい中", "貴重なお時間", "恐れ入ります", "失礼いたします"
            ],
            "consideration": [
                "ご検討", "ご相談", "ご質問", "ご不明な点", "いかがでしょうか"
            ],
            "gratitude": [
                "ありがとうございます", "感謝申し上げます", "恐縮です"
            ],
            "apology": [
                "申し訳ございません", "恐れ入ります", "失礼いたしました"
            ]
        }
        
        # 不適切表現（営業で避けるべき）
        self.inappropriate_expressions = {
            "too_casual": [
                "やばい", "すげー", "マジで", "ぶっちゃけ", "てか", "っす"
            ],
            "unclear": [
                "なんか", "とか", "みたいな", "かも", "多分", "たぶん"
            ],
            "negative": [
                "無理", "できません", "ダメ", "困ります", "面倒"
            ],
            "pushy": [
                "絶対", "必ず", "間違いなく", "確実に", "100%"
            ]
        }
        
        # 改善提案マップ
        self.improvement_suggestions = {
            "やばい": "すばらしい/大変",
            "すげー": "非常に/とても",
            "マジで": "本当に/実際に",
            "ぶっちゃけ": "率直に申し上げると",
            "てか": "ところで",
            "っす": "です",
            "なんか": "何かしら/いささか",
            "とか": "など/等",
            "みたいな": "のような",
            "かも": "可能性があります",
            "多分": "おそらく",
            "無理": "困難です/厳しいです",
            "できません": "対応が困難です",
            "ダメ": "適切ではありません"
        }
    
    async def analyze_language_quality(
        self,
        text: str,
        context: str = "sales",
        customer_level: str = "business"
    ) -> Dict[str, Any]:
        """
        言葉遣いの総合分析
        
        Args:
            text: 分析対象テキスト
            context: 文脈（sales, meeting, presentation）
            customer_level: 顧客レベル（executive, business, casual）
        """
        
        try:
            # 1. 丁寧度分析
            politeness_analysis = self._analyze_politeness(text)
            
            # 2. 敬語使用状況
            keigo_analysis = self._analyze_keigo_usage(text)
            
            # 3. 不適切表現の検出
            issues = self._detect_language_issues(text)
            
            # 4. ビジネス適切性評価
            business_appropriateness = self._evaluate_business_appropriateness(
                text, customer_level
            )
            
            # 5. 改善提案
            improvements = self._generate_language_improvements(text, issues)
            
            # 6. 総合スコア計算
            overall_score = self._calculate_language_score(
                politeness_analysis, keigo_analysis, issues, business_appropriateness
            )
            
            # 7. 親しみやすさ分析
            friendliness_analysis = friendliness_analyzer.analyze_friendliness(
                text=text,
                context=context,
                customer_relationship=customer_level  # customer_levelを関係性として使用
            )
            
            return {
                "overall_score": overall_score,
                "politeness_analysis": {
                    "level": politeness_analysis.level.value,
                    "score": politeness_analysis.score,
                    "keigo_usage": politeness_analysis.keigo_usage,
                    "politeness_indicators": politeness_analysis.politeness_indicators,
                    "missing_elements": politeness_analysis.missing_elements
                },
                "keigo_analysis": keigo_analysis,
                "detected_issues": [
                    {
                        "issue_type": issue.issue_type.value,
                        "position": issue.position,
                        "original_text": issue.original_text,
                        "suggested_fix": issue.suggested_fix,
                        "severity": issue.severity,
                        "explanation": issue.explanation
                    } for issue in issues
                ],
                "business_appropriateness": business_appropriateness,
                "improvement_suggestions": improvements,
                "context_analysis": self._analyze_context_appropriateness(text, context),
                "tone_assessment": self._assess_communication_tone(text),
                "friendliness_analysis": {
                    "level": friendliness_analysis.level.value,
                    "score": friendliness_analysis.score,
                    "balance_score": friendliness_analysis.balance_score,
                    "warmth_indicators": friendliness_analysis.warmth_indicators,
                    "distance_indicators": friendliness_analysis.distance_indicators,
                    "issues": [
                        {
                            "type": issue.issue_type.value,
                            "severity": issue.severity,
                            "description": issue.description,
                            "suggestion": issue.suggestion,
                            "examples": issue.examples
                        } for issue in friendliness_analysis.issues
                    ],
                    "recommendations": friendliness_analysis.recommendations
                }
            }
            
        except Exception as e:
            logger.error(f"Language analysis failed: {e}")
            return {"error": str(e)}
    
    def _analyze_politeness(self, text: str) -> PolitenessAnalysis:
        """丁寧度の分析"""
        
        # 丁寧語の出現回数
        teineigo_count = 0
        keigo_indicators = []
        
        for category, patterns in self.keigo_patterns.items():
            for pattern in patterns["patterns"]:
                matches = re.findall(pattern, text)
                count = len(matches)
                if count > 0:
                    teineigo_count += count
                    keigo_indicators.extend(matches)
        
        # 配慮表現の確認
        consideration_count = 0
        for category, expressions in self.business_expressions.items():
            for expr in expressions:
                if expr in text:
                    consideration_count += 1
                    keigo_indicators.append(expr)
        
        # テキスト長に対する丁寧語の比率
        text_length = len(text.replace(" ", ""))
        politeness_ratio = teineigo_count / max(text_length / 10, 1)  # 10文字あたりの丁寧語
        
        # 丁寧度レベルの判定
        if politeness_ratio >= 0.8 and consideration_count >= 2:
            level = PolitenessLevel.VERY_FORMAL
            score = 0.95
        elif politeness_ratio >= 0.5 and consideration_count >= 1:
            level = PolitenessLevel.FORMAL
            score = 0.85
        elif politeness_ratio >= 0.3:
            level = PolitenessLevel.BUSINESS
            score = 0.75
        elif politeness_ratio >= 0.1:
            level = PolitenessLevel.CASUAL
            score = 0.6
        else:
            level = PolitenessLevel.TOO_CASUAL
            score = 0.3
        
        # 不足要素の特定
        missing_elements = []
        if "です" not in text and "ます" not in text:
            missing_elements.append("基本的な丁寧語（です・ます）")
        if consideration_count == 0:
            missing_elements.append("配慮表現（お忙しい中等）")
        if "ありがとう" not in text and len(text) > 50:
            missing_elements.append("感謝の表現")
        
        return PolitenessAnalysis(
            level=level,
            score=score,
            keigo_usage={
                "teineigo_count": teineigo_count,
                "consideration_count": consideration_count,
                "politeness_ratio": politeness_ratio
            },
            politeness_indicators=keigo_indicators,
            missing_elements=missing_elements
        )
    
    def _analyze_keigo_usage(self, text: str) -> Dict[str, Any]:
        """敬語使用状況の分析"""
        
        keigo_usage = {}
        total_keigo = 0
        
        for keigo_type, data in self.keigo_patterns.items():
            count = 0
            found_patterns = []
            
            for pattern in data["patterns"]:
                matches = re.findall(pattern, text)
                count += len(matches)
                found_patterns.extend(matches)
            
            keigo_usage[keigo_type] = {
                "count": count,
                "patterns": found_patterns,
                "examples_used": [p for p in found_patterns if p in data["examples"]]
            }
            total_keigo += count
        
        # 敬語バランスの評価
        balance_score = 1.0
        if total_keigo > 0:
            ratios = [data["count"] / total_keigo for data in keigo_usage.values()]
            # バランスが取れている（一つの敬語に偏りすぎない）かチェック
            if max(ratios) > 0.8:  # 80%以上が一つの敬語タイプ
                balance_score = 0.7
        
        return {
            "usage_details": keigo_usage,
            "total_keigo_count": total_keigo,
            "balance_score": balance_score,
            "appropriate_usage": self._check_keigo_appropriateness(keigo_usage)
        }
    
    def _detect_language_issues(self, text: str) -> List[LanguageIssue]:
        """言葉遣いの問題を検出"""
        
        issues = []
        
        # 不適切表現の検出
        for category, expressions in self.inappropriate_expressions.items():
            for expr in expressions:
                pattern = re.compile(rf'\b{re.escape(expr)}\b')
                for match in pattern.finditer(text):
                    severity = self._get_issue_severity(category, expr)
                    issue_type = self._map_category_to_issue_type(category)
                    
                    suggested_fix = self.improvement_suggestions.get(
                        expr, f"より適切な表現に変更"
                    )
                    
                    issues.append(LanguageIssue(
                        issue_type=issue_type,
                        position=match.start(),
                        original_text=expr,
                        suggested_fix=suggested_fix,
                        severity=severity,
                        explanation=self._get_issue_explanation(category, expr)
                    ))
        
        # 敬語の誤用チェック
        keigo_issues = self._check_keigo_errors(text)
        issues.extend(keigo_issues)
        
        return sorted(issues, key=lambda x: x.severity, reverse=True)
    
    def _evaluate_business_appropriateness(
        self, 
        text: str, 
        customer_level: str
    ) -> Dict[str, Any]:
        """ビジネス適切性の評価"""
        
        # 顧客レベルに応じた期待値
        expected_formality = {
            "executive": 0.9,    # 経営層：非常に丁寧
            "business": 0.7,     # ビジネス：標準的な丁寧さ
            "casual": 0.5        # カジュアル：基本的な丁寧さ
        }
        
        expected_score = expected_formality.get(customer_level, 0.7)
        
        # ビジネス表現の使用度チェック
        business_score = 0.0
        used_expressions = []
        
        for category, expressions in self.business_expressions.items():
            category_score = 0.0
            for expr in expressions:
                if expr in text:
                    category_score += 1
                    used_expressions.append(expr)
            
            # カテゴリごとの重み付け
            weights = {
                "opening": 0.3,
                "consideration": 0.3,
                "gratitude": 0.2,
                "apology": 0.2
            }
            
            business_score += (category_score / len(expressions)) * weights.get(category, 0.25)
        
        # 適切性スコア
        appropriateness_score = min(business_score / expected_score, 1.0)
        
        return {
            "customer_level": customer_level,
            "expected_formality": expected_score,
            "business_score": business_score,
            "appropriateness_score": appropriateness_score,
            "used_expressions": used_expressions,
            "recommendations": self._get_customer_level_recommendations(customer_level, business_score)
        }
    
    def _generate_language_improvements(
        self, 
        text: str, 
        issues: List[LanguageIssue]
    ) -> Dict[str, Any]:
        """言語改善提案の生成"""
        
        improvements = {
            "high_priority": [],
            "medium_priority": [],
            "low_priority": [],
            "overall_suggestions": []
        }
        
        # 問題の重要度別分類
        for issue in issues:
            improvement = {
                "original": issue.original_text,
                "suggested": issue.suggested_fix,
                "explanation": issue.explanation,
                "position": issue.position
            }
            
            if issue.severity >= 0.8:
                improvements["high_priority"].append(improvement)
            elif issue.severity >= 0.5:
                improvements["medium_priority"].append(improvement)
            else:
                improvements["low_priority"].append(improvement)
        
        # 全体的な改善提案
        overall_suggestions = self._generate_overall_suggestions(text, issues)
        improvements["overall_suggestions"] = overall_suggestions
        
        return improvements
    
    def _calculate_language_score(
        self,
        politeness: PolitenessAnalysis,
        keigo: Dict[str, Any],
        issues: List[LanguageIssue],
        business: Dict[str, Any]
    ) -> float:
        """言語総合スコアの計算"""
        
        # 基本スコア（丁寧度）
        base_score = politeness.score
        
        # 敬語使用ボーナス
        keigo_bonus = min(keigo["balance_score"] * 0.1, 0.1)
        
        # 問題による減点
        issue_penalty = 0.0
        for issue in issues:
            issue_penalty += issue.severity * 0.1
        
        # ビジネス適切性ボーナス
        business_bonus = business["appropriateness_score"] * 0.1
        
        # 総合スコア計算
        total_score = base_score + keigo_bonus + business_bonus - issue_penalty
        
        return max(0.0, min(1.0, total_score))
    
    def _analyze_context_appropriateness(self, text: str, context: str) -> Dict[str, Any]:
        """文脈適切性の分析"""
        
        context_requirements = {
            "sales": {
                "required_elements": ["感謝", "配慮", "提案"],
                "avoided_elements": ["断定", "押し付け"],
                "tone": "professional_friendly"
            },
            "meeting": {
                "required_elements": ["尊敬", "謙譲", "議論"],
                "avoided_elements": ["カジュアル", "独断"],
                "tone": "formal_collaborative"
            },
            "presentation": {
                "required_elements": ["明確性", "論理性", "丁寧"],
                "avoided_elements": ["曖昧", "口語"],
                "tone": "authoritative_polite"
            }
        }
        
        requirements = context_requirements.get(context, context_requirements["sales"])
        
        # 必要要素のチェック
        required_score = self._check_required_elements(text, requirements["required_elements"])
        
        # 避けるべき要素のチェック
        avoided_score = self._check_avoided_elements(text, requirements["avoided_elements"])
        
        return {
            "context": context,
            "required_elements_score": required_score,
            "avoided_elements_score": avoided_score,
            "context_appropriateness": (required_score + avoided_score) / 2,
            "recommendations": self._get_context_recommendations(context, required_score, avoided_score)
        }
    
    def _assess_communication_tone(self, text: str) -> Dict[str, Any]:
        """コミュニケーショントーンの評価"""
        
        tone_indicators = {
            "friendly": ["ありがとう", "お疲れ", "よろしく", "嬉しい"],
            "professional": ["ご提案", "ご検討", "申し上げ", "いたします"],
            "confident": ["確信", "実績", "成功", "効果"],
            "humble": ["恐れ入り", "申し訳", "未熟", "勉強"],
            "enthusiastic": ["ぜひ", "素晴らしい", "期待", "楽しみ"]
        }
        
        tone_scores = {}
        for tone, indicators in tone_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text)
            tone_scores[tone] = score / len(indicators)
        
        # 主要トーンの特定
        primary_tone = max(tone_scores.keys(), key=lambda k: tone_scores[k])
        
        return {
            "tone_scores": tone_scores,
            "primary_tone": primary_tone,
            "tone_balance": self._evaluate_tone_balance(tone_scores),
            "tone_appropriateness": self._evaluate_tone_appropriateness(tone_scores)
        }
    
    # 以下、ヘルパーメソッド
    def _get_issue_severity(self, category: str, expression: str) -> float:
        """問題の重要度を取得"""
        severity_map = {
            "too_casual": 0.9,
            "unclear": 0.6,
            "negative": 0.8,
            "pushy": 0.7
        }
        return severity_map.get(category, 0.5)
    
    def _map_category_to_issue_type(self, category: str) -> LanguageIssueType:
        """カテゴリを問題タイプにマッピング"""
        mapping = {
            "too_casual": LanguageIssueType.TOO_CASUAL,
            "unclear": LanguageIssueType.UNCLEAR_EXPRESSION,
            "negative": LanguageIssueType.INAPPROPRIATE_WORD,
            "pushy": LanguageIssueType.INAPPROPRIATE_WORD
        }
        return mapping.get(category, LanguageIssueType.INAPPROPRIATE_WORD)
    
    def _get_issue_explanation(self, category: str, expression: str) -> str:
        """問題の説明を取得"""
        explanations = {
            "too_casual": f"'{expression}'は営業シーンには適さないカジュアルな表現です",
            "unclear": f"'{expression}'は曖昧な表現で、顧客に不安を与える可能性があります",
            "negative": f"'{expression}'はネガティブな印象を与える可能性があります",
            "pushy": f"'{expression}'は押し付けがましい印象を与える可能性があります"
        }
        return explanations.get(category, "より適切な表現への変更をお勧めします")
    
    def _check_keigo_errors(self, text: str) -> List[LanguageIssue]:
        """敬語の誤用をチェック"""
        # 簡略化された実装例
        issues = []
        
        # よくある敬語の誤用パターン
        common_errors = {
            "お疲れ様でした": "お疲れ様です（現在進行形が適切）",
            "ご苦労様": "お疲れ様です（目上の人には使わない）",
            "すいません": "申し訳ございません（より丁寧な表現）"
        }
        
        for error, correction in common_errors.items():
            if error in text:
                position = text.find(error)
                issues.append(LanguageIssue(
                    issue_type=LanguageIssueType.INCORRECT_KEIGO,
                    position=position,
                    original_text=error,
                    suggested_fix=correction,
                    severity=0.7,
                    explanation=f"敬語の使い方：{correction}"
                ))
        
        return issues
    
    def _check_keigo_appropriateness(self, keigo_usage: Dict[str, Any]) -> Dict[str, str]:
        """敬語の適切性をチェック"""
        appropriateness = {}
        
        for keigo_type, data in keigo_usage.items():
            if data["count"] == 0:
                appropriateness[keigo_type] = "使用なし"
            elif data["count"] < 3:
                appropriateness[keigo_type] = "適度な使用"
            else:
                appropriateness[keigo_type] = "多用気味"
        
        return appropriateness
    
    def _get_customer_level_recommendations(self, level: str, score: float) -> List[str]:
        """顧客レベル別の推奨事項"""
        recommendations = {
            "executive": [
                "より丁寧な尊敬語を使用してください",
                "謙譲語を積極的に使用してください",
                "配慮表現を必ず含めてください"
            ],
            "business": [
                "基本的な敬語を確実に使用してください",
                "ビジネス標準の表現を心がけてください"
            ],
            "casual": [
                "親しみやすさを保ちつつ、基本的な丁寧さを守ってください"
            ]
        }
        
        return recommendations.get(level, recommendations["business"])
    
    def _generate_overall_suggestions(self, text: str, issues: List[LanguageIssue]) -> List[str]:
        """全体的な改善提案"""
        suggestions = []
        
        if len(issues) > 3:
            suggestions.append("全体的に言葉遣いを見直しましょう")
        
        if not ("です" in text or "ます" in text):
            suggestions.append("基本的な丁寧語（です・ます調）を使用しましょう")
        
        if "ありがとう" not in text and len(text) > 30:
            suggestions.append("感謝の気持ちを表現しましょう")
        
        return suggestions
    
    def _check_required_elements(self, text: str, elements: List[str]) -> float:
        """必要要素のチェック"""
        found = sum(1 for element in elements if element in text)
        return found / len(elements) if elements else 1.0
    
    def _check_avoided_elements(self, text: str, elements: List[str]) -> float:
        """避けるべき要素のチェック"""
        found = sum(1 for element in elements if element in text)
        return 1.0 - (found / len(elements)) if elements else 1.0
    
    def _get_context_recommendations(self, context: str, required: float, avoided: float) -> List[str]:
        """文脈別推奨事項"""
        recommendations = []
        
        if required < 0.5:
            recommendations.append(f"{context}に適した表現をより多く使用してください")
        
        if avoided < 0.5:
            recommendations.append(f"{context}では避けるべき表現が含まれています")
        
        return recommendations
    
    def _evaluate_tone_balance(self, tone_scores: Dict[str, float]) -> str:
        """トーンバランスの評価"""
        scores = list(tone_scores.values())
        max_score = max(scores)
        min_score = min(scores)
        
        if max_score - min_score < 0.3:
            return "バランス良好"
        elif max_score > 0.7:
            return "特定のトーンが強い"
        else:
            return "トーンが不明確"
    
    def _evaluate_tone_appropriateness(self, tone_scores: Dict[str, float]) -> float:
        """トーン適切性の評価"""
        # 営業に適したトーンの重み
        weights = {
            "friendly": 0.3,
            "professional": 0.4,
            "confident": 0.2,
            "humble": 0.1,
            "enthusiastic": 0.1
        }
        
        weighted_score = sum(
            tone_scores[tone] * weight 
            for tone, weight in weights.items()
        )
        
        return min(1.0, weighted_score)

# サービスインスタンス
language_analysis_service = LanguageAnalysisService() 