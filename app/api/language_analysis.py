from fastapi import APIRouter, HTTPException, Form
from typing import Dict, Any, Optional, List
import logging
try:
    from services.language_analysis_service import language_analysis_service, PolitenessLevel, LanguageIssueType
    from services.friendliness_analyzer import friendliness_analyzer, FriendlinessLevel
except ImportError:
    from app.services.language_analysis_service import language_analysis_service, PolitenessLevel, LanguageIssueType
    from app.services.friendliness_analyzer import friendliness_analyzer, FriendlinessLevel

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/language/analyze")
async def analyze_language_quality(
    text: str = Form(...),
    context: str = Form(default="sales"),
    customer_level: str = Form(default="business")
):
    """
    言葉遣いの総合分析
    
    Args:
        text: 分析対象のテキスト
        context: 文脈 (sales, meeting, presentation)
        customer_level: 顧客レベル (executive, business, casual)
    
    Returns:
        言葉遣い分析結果
    """
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="分析対象のテキストが空です")
        
        # 言語分析実行
        result = await language_analysis_service.analyze_language_quality(
            text=text,
            context=context,
            customer_level=customer_level
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "analysis_result": result,
            "input": {
                "text": text,
                "context": context,
                "customer_level": customer_level
            },
            "summary": {
                "overall_score": result["overall_score"],
                "politeness_level": result["politeness_analysis"]["level"],
                "issues_count": len(result["detected_issues"]),
                "business_appropriateness": result["business_appropriateness"]["appropriateness_score"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Language analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"言語分析でエラーが発生しました: {str(e)}")

@router.post("/language/check-politeness")
async def check_politeness_level(
    text: str = Form(...)
):
    """
    丁寧度レベルのクイックチェック
    
    Args:
        text: チェック対象のテキスト
    
    Returns:
        丁寧度レベルと基本的な評価
    """
    try:
        result = await language_analysis_service.analyze_language_quality(text, "sales", "business")
        
        politeness = result["politeness_analysis"]
        
        return {
            "success": True,
            "politeness_level": politeness["level"],
            "score": politeness["score"],
            "keigo_usage": politeness["keigo_usage"],
            "missing_elements": politeness["missing_elements"],
            "quick_feedback": _generate_quick_feedback(politeness)
        }
        
    except Exception as e:
        logger.error(f"Politeness check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/language/fix-issues")
async def get_language_fixes(
    text: str = Form(...),
    priority: str = Form(default="high")
):
    """
    言葉遣いの修正提案を取得
    
    Args:
        text: 修正対象のテキスト
        priority: 優先度 (high, medium, low, all)
    
    Returns:
        修正提案とその説明
    """
    try:
        result = await language_analysis_service.analyze_language_quality(text, "sales", "business")
        
        improvements = result["improvement_suggestions"]
        
        if priority == "all":
            selected_improvements = {
                "high": improvements["high_priority"],
                "medium": improvements["medium_priority"], 
                "low": improvements["low_priority"]
            }
        else:
            selected_improvements = improvements.get(f"{priority}_priority", [])
        
        return {
            "success": True,
            "original_text": text,
            "improvements": selected_improvements,
            "overall_suggestions": improvements["overall_suggestions"],
            "fixed_text": _apply_basic_fixes(text, improvements),
            "improvement_count": len(selected_improvements) if isinstance(selected_improvements, list) else sum(len(v) for v in selected_improvements.values())
        }
        
    except Exception as e:
        logger.error(f"Language fix error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/language/business-check")
async def check_business_appropriateness(
    text: str = Form(...),
    customer_level: str = Form(default="business"),
    industry: str = Form(default="general")
):
    """
    ビジネス適切性のチェック
    
    Args:
        text: チェック対象のテキスト
        customer_level: 顧客レベル (executive, business, casual)
        industry: 業界 (IT, finance, manufacturing, general)
    
    Returns:
        ビジネス適切性の評価
    """
    try:
        result = await language_analysis_service.analyze_language_quality(text, "sales", customer_level)
        
        business_analysis = result["business_appropriateness"]
        tone_analysis = result["tone_assessment"]
        
        # 業界特化の追加チェック
        industry_specific = _check_industry_specific_language(text, industry)
        
        return {
            "success": True,
            "business_appropriateness": business_analysis,
            "tone_analysis": tone_analysis,
            "industry_specific": industry_specific,
            "recommendations": _generate_business_recommendations(
                business_analysis, tone_analysis, customer_level, industry
            ),
            "overall_business_score": (
                business_analysis["appropriateness_score"] + 
                tone_analysis["tone_appropriateness"]
            ) / 2
        }
        
    except Exception as e:
        logger.error(f"Business check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/language/keigo-check")
async def check_keigo_usage(
    text: str = Form(...)
):
    """
    敬語使用状況のチェック
    
    Args:
        text: チェック対象のテキスト
    
    Returns:
        敬語使用状況の詳細分析
    """
    try:
        result = await language_analysis_service.analyze_language_quality(text, "sales", "business")
        
        keigo_analysis = result["keigo_analysis"]
        issues = [issue for issue in result["detected_issues"] 
                 if issue["issue_type"] == "incorrect_keigo"]
        
        return {
            "success": True,
            "keigo_analysis": keigo_analysis,
            "keigo_issues": issues,
            "keigo_suggestions": _generate_keigo_suggestions(keigo_analysis),
            "keigo_score": keigo_analysis["balance_score"],
            "improvement_tips": _get_keigo_improvement_tips(keigo_analysis)
        }
        
    except Exception as e:
        logger.error(f"Keigo check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/language/tone-analysis")
async def analyze_communication_tone(
    text: str = Form(...),
    target_tone: str = Form(default="professional_friendly")
):
    """
    コミュニケーショントーンの分析
    
    Args:
        text: 分析対象のテキスト
        target_tone: 目標とするトーン
    
    Returns:
        トーン分析結果と調整提案
    """
    try:
        result = await language_analysis_service.analyze_language_quality(text, "sales", "business")
        
        tone_analysis = result["tone_assessment"]
        
        # 目標トーンとの比較
        tone_adjustment = _calculate_tone_adjustment(tone_analysis, target_tone)
        
        return {
            "success": True,
            "current_tone": tone_analysis,
            "target_tone": target_tone,
            "tone_adjustment": tone_adjustment,
            "adjustment_suggestions": _generate_tone_adjustment_suggestions(
                tone_analysis, target_tone
            )
        }
        
    except Exception as e:
        logger.error(f"Tone analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/language/patterns")
async def get_language_patterns():
    """
    言語パターンと基準の取得
    
    Returns:
        システムで使用している言語パターンと評価基準
    """
    try:
        return {
            "success": True,
            "patterns": {
                "keigo_patterns": language_analysis_service.keigo_patterns,
                "business_expressions": language_analysis_service.business_expressions,
                "inappropriate_expressions": language_analysis_service.inappropriate_expressions
            },
            "evaluation_criteria": {
                "politeness_levels": [level.value for level in PolitenessLevel],
                "issue_types": [issue_type.value for issue_type in LanguageIssueType]
            },
            "improvement_suggestions": language_analysis_service.improvement_suggestions
        }
        
    except Exception as e:
        logger.error(f"Pattern retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ヘルパー関数
def _generate_quick_feedback(politeness) -> str:
    """クイックフィードバックの生成"""
    level = politeness["level"]
    score = politeness["score"]
    
    if level == "very_formal":
        return "非常に丁寧な言葉遣いです。素晴らしい！"
    elif level == "formal":
        return "適切な丁寧さです。営業にふさわしい言葉遣いです。"
    elif level == "business":
        return "ビジネス標準の言葉遣いです。さらに丁寧さを加えると良いでしょう。"
    elif level == "casual":
        return "やや カジュアルです。もう少し丁寧な表現を心がけましょう。"
    else:
        return "営業には不適切な言葉遣いです。大幅な改善が必要です。"

def _apply_basic_fixes(text: str, improvements: Dict[str, Any]) -> str:
    """基本的な修正の適用"""
    fixed_text = text
    
    # 高優先度の問題を自動修正
    for improvement in improvements.get("high_priority", []):
        original = improvement["original"]
        suggested = improvement["suggested"]
        fixed_text = fixed_text.replace(original, suggested)
    
    return fixed_text

def _check_industry_specific_language(text: str, industry: str) -> Dict[str, Any]:
    """業界特化の言語チェック"""
    industry_patterns = {
        "IT": {
            "preferred": ["効率化", "デジタル", "システム", "ソリューション"],
            "technical": ["クラウド", "AI", "DX", "セキュリティ"]
        },
        "finance": {
            "preferred": ["信頼性", "実績", "安全性", "コンプライアンス"],
            "technical": ["リスク管理", "投資対効果", "監査"]
        },
        "manufacturing": {
            "preferred": ["品質", "効率", "安全", "生産性"],
            "technical": ["QCD", "カイゼン", "トレーサビリティ"]
        }
    }
    
    patterns = industry_patterns.get(industry, {"preferred": [], "technical": []})
    
    preferred_count = sum(1 for word in patterns["preferred"] if word in text)
    technical_count = sum(1 for word in patterns["technical"] if word in text)
    
    return {
        "industry": industry,
        "preferred_usage": preferred_count,
        "technical_usage": technical_count,
        "industry_fit_score": (preferred_count + technical_count) / max(len(patterns["preferred"]) + len(patterns["technical"]), 1)
    }

def _generate_business_recommendations(
    business_analysis: Dict[str, Any],
    tone_analysis: Dict[str, Any],
    customer_level: str,
    industry: str
) -> List[str]:
    """ビジネス推奨事項の生成"""
    recommendations = []
    
    if business_analysis["appropriateness_score"] < 0.7:
        recommendations.append(f"{customer_level}レベルの顧客により適した表現を使用してください")
    
    if tone_analysis["tone_appropriateness"] < 0.6:
        recommendations.append("より営業に適したトーンに調整してください")
    
    if industry != "general":
        recommendations.append(f"{industry}業界特有の表現を取り入れることを検討してください")
    
    return recommendations

def _generate_keigo_suggestions(keigo_analysis: Dict[str, Any]) -> List[str]:
    """敬語使用提案の生成"""
    suggestions = []
    
    usage = keigo_analysis["usage_details"]
    
    if usage["teineigo"]["count"] == 0:
        suggestions.append("基本的な丁寧語（です・ます）を使用してください")
    
    if usage["sonkeigo"]["count"] == 0:
        suggestions.append("相手を敬う尊敬語を適度に使用してください")
    
    if usage["kenjougo"]["count"] == 0:
        suggestions.append("謙譲語で自分をへりくだる表現を使用してください")
    
    return suggestions

@router.post("/language/friendliness-analysis")
async def analyze_friendliness(
    text: str = Form(...),
    context: str = Form(default="sales"),
    customer_relationship: str = Form(default="new")
):
    """
    親しみやすさの詳細分析
    
    Args:
        text: 分析対象のテキスト
        context: 文脈 (sales, meeting, negotiation)
        customer_relationship: 顧客との関係性 (new, existing, long_term)
    
    Returns:
        親しみやすさ分析結果
    """
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="分析対象のテキストが空です")
        
        # 親しみやすさ分析実行
        result = friendliness_analyzer.analyze_friendliness(
            text=text,
            context=context,
            customer_relationship=customer_relationship
        )
        
        return {
            "success": True,
            "friendliness_analysis": {
                "level": result.level.value,
                "score": result.score,
                "balance_score": result.balance_score,
                "warmth_indicators": result.warmth_indicators,
                "distance_indicators": result.distance_indicators,
                "issues": [
                    {
                        "type": issue.issue_type.value,
                        "severity": issue.severity,
                        "description": issue.description,
                        "suggestion": issue.suggestion,
                        "examples": issue.examples
                    } for issue in result.issues
                ],
                "recommendations": result.recommendations
            },
            "input": {
                "text": text,
                "context": context,
                "customer_relationship": customer_relationship
            },
            "improvement_tips": friendliness_analyzer.get_friendliness_tips(result.level)
        }
        
    except Exception as e:
        logger.error(f"Friendliness analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"親しみやすさ分析でエラーが発生しました: {str(e)}")

@router.post("/language/distance-check")
async def check_distance_balance(
    text: str = Form(...),
    target_relationship: str = Form(default="friendly_professional")
):
    """
    距離感のバランスチェック
    
    Args:
        text: チェック対象のテキスト
        target_relationship: 目標の関係性 (formal, friendly_professional, casual)
    
    Returns:
        距離感バランスの評価
    """
    try:
        # 親しみやすさ分析
        friendliness_result = friendliness_analyzer.analyze_friendliness(text)
        
        # 言語分析（丁寧度）
        language_result = await language_analysis_service.analyze_language_quality(text)
        
        # バランス評価
        balance_assessment = _assess_distance_balance(
            friendliness_result, language_result, target_relationship
        )
        
        return {
            "success": True,
            "distance_balance": {
                "current_level": friendliness_result.level.value,
                "politeness_level": language_result["politeness_analysis"]["level"],
                "balance_score": balance_assessment["balance_score"],
                "distance_issues": balance_assessment["issues"],
                "recommendations": balance_assessment["recommendations"]
            },
            "detailed_analysis": {
                "warmth_score": friendliness_result.score,
                "politeness_score": language_result["politeness_analysis"]["score"],
                "target_relationship": target_relationship
            }
        }
        
    except Exception as e:
        logger.error(f"Distance balance check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/language/warmth-suggestions")
async def get_warmth_suggestions(
    text: str = Form(...),
    current_issues: List[str] = Form(default=[])
):
    """
    温かみ向上の具体的提案
    
    Args:
        text: 改善対象のテキスト
        current_issues: 現在の問題点
    
    Returns:
        温かみ向上のための具体的提案
    """
    try:
        # 親しみやすさ分析
        result = friendliness_analyzer.analyze_friendliness(text)
        
        # 温かみ向上提案生成
        warmth_suggestions = _generate_warmth_improvement_suggestions(
            text, result, current_issues
        )
        
        return {
            "success": True,
            "original_text": text,
            "warmth_suggestions": warmth_suggestions,
            "before_after_examples": _generate_before_after_examples(text, result),
            "practice_phrases": _get_warmth_practice_phrases(result.level)
        }
        
    except Exception as e:
        logger.error(f"Warmth suggestions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ヘルパー関数の追加

def _assess_distance_balance(
    friendliness_result,
    language_result,
    target_relationship: str
) -> Dict[str, Any]:
    """距離感バランスの評価"""
    
    # 目標関係性の定義
    target_configs = {
        "formal": {
            "target_politeness": "formal",
            "target_friendliness": "formal_distant",
            "balance_weight": {"politeness": 0.7, "friendliness": 0.3}
        },
        "friendly_professional": {
            "target_politeness": "business", 
            "target_friendliness": "balanced",
            "balance_weight": {"politeness": 0.5, "friendliness": 0.5}
        },
        "casual": {
            "target_politeness": "casual",
            "target_friendliness": "friendly",
            "balance_weight": {"politeness": 0.3, "friendliness": 0.7}
        }
    }
    
    config = target_configs.get(target_relationship, target_configs["friendly_professional"])
    
    # バランススコア計算
    politeness_match = 1.0 if language_result["politeness_analysis"]["level"] == config["target_politeness"] else 0.5
    friendliness_match = 1.0 if friendliness_result.level.value == config["target_friendliness"] else 0.5
    
    balance_score = (
        politeness_match * config["balance_weight"]["politeness"] +
        friendliness_match * config["balance_weight"]["friendliness"]
    )
    
    # 問題と推奨事項
    issues = []
    recommendations = []
    
    if balance_score < 0.6:
        issues.append("目標とする関係性とのバランスが取れていません")
        recommendations.append(f"{target_relationship}に適したバランスに調整してください")
    
    return {
        "balance_score": balance_score,
        "issues": issues,
        "recommendations": recommendations
    }

def _generate_warmth_improvement_suggestions(
    text: str,
    friendliness_result,
    current_issues: List[str]
) -> Dict[str, List[str]]:
    """温かみ向上提案の生成"""
    
    suggestions = {
        "immediate_improvements": [],
        "phrase_additions": [],
        "tone_adjustments": [],
        "structure_changes": []
    }
    
    # 現在の問題に基づく提案
    if friendliness_result.score < 0.3:
        suggestions["immediate_improvements"].extend([
            "相槌（「そうですね」「なるほど」）を追加",
            "共感表現（「お気持ちお察しします」）を使用",
            "協力姿勢（「一緒に考えましょう」）を示す"
        ])
    
    if len(friendliness_result.distance_indicators) > 0:
        suggestions["tone_adjustments"].extend([
            "過度に堅い表現を柔らかく変更",
            "個人的な温かみを加える",
            "お役所的な表現を避ける"
        ])
    
    return suggestions

def _generate_before_after_examples(text: str, friendliness_result) -> List[Dict[str, str]]:
    """改善前後の例文生成"""
    
    examples = []
    
    # 距離感のある表現の改善例
    for indicator in friendliness_result.distance_indicators:
        if indicator in text:
            if indicator == "弊社では":
                examples.append({
                    "before": "弊社では対応いたしかねます",
                    "after": "申し訳ございませんが、私どもでは少し難しいかもしれません"
                })
            elif indicator == "規定により":
                examples.append({
                    "before": "規定によりお受けできません",
                    "after": "大変恐縮ですが、こちらの件は対応が困難です"
                })
    
    return examples

def _get_warmth_practice_phrases(level: FriendlinessLevel) -> List[str]:
    """レベル別練習フレーズ"""
    
    phrases = {
        FriendlinessLevel.TOO_DISTANT: [
            "お気持ちお察しします",
            "そうですね、確かに",
            "なるほど、よくわかります",
            "一緒に考えさせてください",
            "安心してお任せください"
        ],
        FriendlinessLevel.FORMAL_DISTANT: [
            "実は私も同じように思います",
            "正直に申し上げると",
            "お気軽にご相談ください",
            "喜んでお手伝いします",
            "楽しみにしております"
        ],
        FriendlinessLevel.BALANCED: [
            "いつでもお声がけください",
            "何でもお聞かせください",
            "心強いお言葉です",
            "ワクワクしてきますね"
        ]
    }
    
    return phrases.get(level, phrases[FriendlinessLevel.FORMAL_DISTANT])

def _get_keigo_improvement_tips(keigo_analysis: Dict[str, Any]) -> List[str]:
    """敬語改善のヒント"""
    tips = [
        "「いらっしゃる」「おっしゃる」などの尊敬語で相手を立てる",
        "「申し上げる」「させていただく」などの謙譲語で謙遜する",
        "「です」「ます」「ございます」で丁寧さを表現する"
    ]
    
    return tips

def _calculate_tone_adjustment(
    current_tone: Dict[str, Any],
    target_tone: str
) -> Dict[str, float]:
    """トーン調整の計算"""
    target_mapping = {
        "professional_friendly": {
            "professional": 0.6,
            "friendly": 0.4,
            "confident": 0.3,
            "humble": 0.2,
            "enthusiastic": 0.1
        },
        "formal_respectful": {
            "professional": 0.8,
            "humble": 0.6,
            "friendly": 0.2,
            "confident": 0.4,
            "enthusiastic": 0.1
        }
    }
    
    target_scores = target_mapping.get(target_tone, target_mapping["professional_friendly"])
    current_scores = current_tone["tone_scores"]
    
    adjustments = {}
    for tone, target_score in target_scores.items():
        current_score = current_scores.get(tone, 0.0)
        adjustments[tone] = target_score - current_score
    
    return adjustments

def _generate_tone_adjustment_suggestions(
    current_tone: Dict[str, Any],
    target_tone: str
) -> List[str]:
    """トーン調整提案の生成"""
    suggestions = []
    
    if target_tone == "professional_friendly":
        suggestions.extend([
            "親しみやすさを保ちながら、プロフェッショナルな表現を使用してください",
            "適度な感謝の表現で好印象を与えてください"
        ])
    elif target_tone == "formal_respectful":
        suggestions.extend([
            "より formal で respectful な表現を心がけてください",
            "謙譲語を積極的に使用してください"
        ])
    
    return suggestions 