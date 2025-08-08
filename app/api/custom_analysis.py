from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from typing import Dict, Any, Optional, List
import json
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

router = APIRouter()

class CustomAnalysisService:
    """独自分析サービス"""
    
    def __init__(self):
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        config_path = "config/custom_analysis_config.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定"""
        return {
            "custom_analysis_config": {
                "evaluation_criteria": {
                    "empathy_score": {"weight": 0.3, "keywords": ["わかります", "理解"]},
                    "specificity_score": {"weight": 0.25, "keywords": ["具体的に", "例えば"]},
                    "closing_power": {"weight": 0.25, "keywords": ["いかがでしょうか"]},
                    "industry_knowledge": {"weight": 0.2, "keywords": ["業界", "専門"]}
                }
            }
        }
    
    async def analyze_with_custom_perspective(
        self,
        conversation_text: str,
        industry: str = "general",
        skill_level: str = "intermediate",
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """独自視点での分析"""
        
        config = self.config["custom_analysis_config"]
        criteria = config["evaluation_criteria"]
        
        # 各評価項目の分析
        analysis_results = {}
        
        for criterion_name, criterion_config in criteria.items():
            score = self._evaluate_criterion(
                conversation_text, 
                criterion_config, 
                industry
            )
            analysis_results[criterion_name] = {
                "score": score,
                "weight": criterion_config["weight"],
                "description": criterion_config.get("description", criterion_name)
            }
        
        # 総合スコア計算
        weighted_score = sum(
            result["score"] * result["weight"] 
            for result in analysis_results.values()
        )
        
        # 個別フィードバック生成
        feedback = self._generate_personalized_feedback(
            analysis_results, 
            weighted_score, 
            skill_level
        )
        
        # 次回の推奨事項
        recommendations = self._generate_next_session_recommendations(
            analysis_results, 
            focus_areas
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_score": weighted_score,
            "performance_level": self._get_performance_level(weighted_score),
            "detailed_analysis": analysis_results,
            "personalized_feedback": feedback,
            "industry_insights": self._get_industry_insights(industry, conversation_text),
            "next_session_recommendations": recommendations,
            "custom_config_used": config.get("analyzer_name", "カスタム分析")
        }
    
    def _evaluate_criterion(
        self, 
        text: str, 
        criterion_config: Dict[str, Any], 
        industry: str
    ) -> float:
        """評価基準に基づくスコア計算"""
        
        # キーワードベースの基本評価
        keywords = criterion_config.get("keywords", [])
        negative_keywords = criterion_config.get("negative_keywords", [])
        
        positive_count = sum(1 for keyword in keywords if keyword in text)
        negative_count = sum(1 for keyword in negative_keywords if keyword in text)
        
        # 基本スコア
        base_score = min(positive_count / max(len(keywords), 1), 1.0)
        
        # ネガティブキーワードのペナルティ
        penalty = min(negative_count * 0.1, 0.3)
        
        # 業界特化の調整
        industry_bonus = self._calculate_industry_bonus(text, industry, criterion_config)
        
        final_score = max(0, min(1.0, base_score - penalty + industry_bonus))
        
        return final_score
    
    def _calculate_industry_bonus(
        self, 
        text: str, 
        industry: str, 
        criterion_config: Dict[str, Any]
    ) -> float:
        """業界特化ボーナス"""
        
        industry_keywords_key = f"{industry.lower()}_keywords"
        if industry_keywords_key in criterion_config:
            industry_keywords = criterion_config[industry_keywords_key]
            industry_mentions = sum(1 for keyword in industry_keywords if keyword in text)
            return min(industry_mentions * 0.1, 0.2)
        
        return 0.0
    
    def _generate_personalized_feedback(
        self,
        analysis_results: Dict[str, Any],
        overall_score: float,
        skill_level: str
    ) -> Dict[str, Any]:
        """個人化されたフィードバック生成"""
        
        # 強みと弱みの特定
        strengths = []
        weaknesses = []
        
        for criterion, result in analysis_results.items():
            if result["score"] >= 0.8:
                strengths.append(criterion)
            elif result["score"] < 0.6:
                weaknesses.append(criterion)
        
        # パフォーマンスレベルに基づくフィードバック
        config = self.config["custom_analysis_config"]
        templates = config.get("personalized_feedback_templates", {})
        
        if overall_score >= 0.8:
            template = templates.get("excellent_performance", "素晴らしい対応でした！")
            main_feedback = template.format(
                strength_area=strengths[0] if strengths else "全体的な対応"
            )
        elif overall_score >= 0.6:
            template = templates.get("good_performance", "良い対応でした。")
            main_feedback = template.format(
                improvement_area=weaknesses[0] if weaknesses else "さらなる向上"
            )
        elif overall_score >= 0.4:
            template = templates.get("needs_improvement", "改善が必要です。")
            main_feedback = template.format(
                specific_issue=weaknesses[0] if weaknesses else "基本スキル",
                actionable_advice="継続的な練習"
            )
        else:
            template = templates.get("poor_performance", "基本から見直しましょう。")
            main_feedback = template.format(
                basic_skill="基本的な営業スキル",
                detailed_guidance="段階的な練習"
            )
        
        return {
            "main_feedback": main_feedback,
            "strengths": strengths,
            "areas_for_improvement": weaknesses,
            "specific_suggestions": self._generate_specific_suggestions(weaknesses),
            "encouragement": self._generate_encouragement(overall_score, skill_level)
        }
    
    def _generate_specific_suggestions(self, weaknesses: List[str]) -> List[str]:
        """具体的な改善提案"""
        suggestions = []
        
        suggestion_map = {
            "empathy_score": "相手の立場に立って考え、共感の言葉を増やしましょう",
            "specificity_score": "具体的な数字や事例を交えて説明しましょう",
            "closing_power": "次のステップを明確に提示し、決断を促しましょう",
            "industry_knowledge": "業界特有の課題と解決策を学習しましょう"
        }
        
        for weakness in weaknesses:
            if weakness in suggestion_map:
                suggestions.append(suggestion_map[weakness])
        
        return suggestions
    
    def _generate_encouragement(self, score: float, skill_level: str) -> str:
        """励ましのメッセージ"""
        if skill_level == "beginner":
            return "基本を身につけることが最も重要です。継続して練習しましょう！"
        elif skill_level == "intermediate":
            return "スキルが向上してきています。より高度な技術にチャレンジしましょう！"
        else:
            return "高いレベルに達しています。細かな調整で完璧を目指しましょう！"
    
    def _get_industry_insights(self, industry: str, text: str) -> Dict[str, Any]:
        """業界特化の洞察"""
        config = self.config["custom_analysis_config"]
        industry_config = config.get("industry_specific_analysis", {})
        
        if industry in industry_config.get("industry_mappings", {}):
            industry_info = industry_config["industry_mappings"][industry]
            
            # 業界特有の懸念事項の言及チェック
            concerns_mentioned = [
                concern for concern in industry_info["key_concerns"]
                if concern in text
            ]
            
            # 成功要因の言及チェック
            success_factors_mentioned = [
                factor for factor in industry_info["success_factors"]
                if factor in text
            ]
            
            return {
                "industry": industry,
                "concerns_addressed": concerns_mentioned,
                "success_factors_mentioned": success_factors_mentioned,
                "industry_fit_score": (
                    len(concerns_mentioned) + len(success_factors_mentioned)
                ) / (len(industry_info["key_concerns"]) + len(industry_info["success_factors"])),
                "recommendations": self._get_industry_recommendations(industry, industry_info)
            }
        
        return {"industry": industry, "industry_fit_score": 0.0}
    
    def _get_industry_recommendations(self, industry: str, industry_info: Dict[str, Any]) -> List[str]:
        """業界特化の推奨事項"""
        recommendations = []
        
        recommendations.append(f"{industry}業界では以下の点に注意しましょう：")
        for concern in industry_info["key_concerns"]:
            recommendations.append(f"・{concern}に関する解決策を明確に提示する")
        
        return recommendations
    
    def _generate_next_session_recommendations(
        self,
        analysis_results: Dict[str, Any],
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """次回セッションの推奨事項"""
        
        # 最も低いスコアの分野を特定
        lowest_score_area = min(
            analysis_results.keys(), 
            key=lambda x: analysis_results[x]["score"]
        )
        
        # 推奨シナリオ
        scenario_recommendations = {
            "empathy_score": "感情的な顧客との対話シナリオ",
            "specificity_score": "詳細な提案書作成シナリオ",
            "closing_power": "決断を迫るクロージングシナリオ",
            "industry_knowledge": "業界特化の専門的なシナリオ"
        }
        
        recommended_scenario = scenario_recommendations.get(
            lowest_score_area, 
            "総合的な営業シナリオ"
        )
        
        return {
            "primary_focus": lowest_score_area,
            "recommended_scenario": recommended_scenario,
            "difficulty_level": self._recommend_difficulty_level(analysis_results),
            "session_goals": self._generate_session_goals(lowest_score_area),
            "practice_exercises": self._recommend_practice_exercises(lowest_score_area)
        }
    
    def _recommend_difficulty_level(self, analysis_results: Dict[str, Any]) -> str:
        """難易度レベルの推奨"""
        avg_score = sum(result["score"] for result in analysis_results.values()) / len(analysis_results)
        
        if avg_score >= 0.8:
            return "上級"
        elif avg_score >= 0.6:
            return "中級"
        else:
            return "初級"
    
    def _generate_session_goals(self, focus_area: str) -> List[str]:
        """セッション目標の生成"""
        goals_map = {
            "empathy_score": [
                "相手の感情を理解し、適切に共感する",
                "顧客の立場に立った発言を3回以上行う"
            ],
            "specificity_score": [
                "具体的な数字や事例を3つ以上提示する",
                "曖昧な表現を避け、明確な説明を心がける"
            ],
            "closing_power": [
                "次のステップを明確に提示する",
                "決断を促すクロージングを実践する"
            ],
            "industry_knowledge": [
                "業界特有の課題を3つ以上特定する",
                "業界に適した解決策を提案する"
            ]
        }
        
        return goals_map.get(focus_area, ["総合的な営業スキルの向上"])
    
    def _recommend_practice_exercises(self, focus_area: str) -> List[str]:
        """練習課題の推奨"""
        exercises_map = {
            "empathy_score": [
                "顧客の不安を察知し、共感する練習",
                "相手の立場で考える視点転換練習"
            ],
            "specificity_score": [
                "数字を使った説明練習",
                "具体例を交えた事例紹介練習"
            ],
            "closing_power": [
                "決断を促す表現の練習",
                "次のステップ提示の練習"
            ],
            "industry_knowledge": [
                "業界トレンドの学習",
                "競合他社の分析練習"
            ]
        }
        
        return exercises_map.get(focus_area, ["基本的な営業スキル練習"])
    
    def _get_performance_level(self, score: float) -> str:
        """パフォーマンスレベル判定"""
        if score >= 0.9:
            return "卓越"
        elif score >= 0.8:
            return "優秀"
        elif score >= 0.6:
            return "良好"
        elif score >= 0.4:
            return "要改善"
        else:
            return "要大幅改善"

# サービスインスタンス
custom_analysis_service = CustomAnalysisService()

@router.post("/custom-analysis/analyze")
async def analyze_conversation_with_custom_perspective(
    conversation_text: str = Form(...),
    industry: str = Form(default="general"),
    skill_level: str = Form(default="intermediate"),
    focus_areas: Optional[str] = Form(default=None)
):
    """
    独自視点での会話分析
    
    Args:
        conversation_text: 分析対象の会話テキスト
        industry: 業界 (IT, manufacturing, finance, general)
        skill_level: スキルレベル (beginner, intermediate, advanced)
        focus_areas: 重点分野 (カンマ区切り)
    """
    try:
        # focus_areasの処理
        focus_areas_list = None
        if focus_areas:
            focus_areas_list = [area.strip() for area in focus_areas.split(",")]
        
        # 独自分析実行
        result = await custom_analysis_service.analyze_with_custom_perspective(
            conversation_text=conversation_text,
            industry=industry,
            skill_level=skill_level,
            focus_areas=focus_areas_list
        )
        
        return {
            "success": True,
            "analysis_result": result,
            "message": "独自視点での分析が完了しました"
        }
        
    except Exception as e:
        logger.error(f"Custom analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/custom-analysis/update-config")
async def update_custom_config(
    config_file: UploadFile = File(...),
):
    """
    カスタム分析設定の更新
    
    Args:
        config_file: 新しい設定ファイル (JSON)
    """
    try:
        # アップロードされたファイルを読み込み
        content = await config_file.read()
        config_data = json.loads(content.decode('utf-8'))
        
        # 設定ファイルを保存
        config_path = "config/custom_analysis_config.json"
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        # サービスの設定を再読み込み
        custom_analysis_service.config = custom_analysis_service._load_config()
        
        return {
            "success": True,
            "message": "カスタム分析設定が更新されました",
            "config_name": config_data.get("custom_analysis_config", {}).get("analyzer_name", "カスタム分析")
        }
        
    except Exception as e:
        logger.error(f"Config update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/custom-analysis/config")
async def get_current_config():
    """
    現在のカスタム分析設定を取得
    """
    try:
        return {
            "success": True,
            "config": custom_analysis_service.config,
            "message": "現在の設定を取得しました"
        }
        
    except Exception as e:
        logger.error(f"Config retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/custom-analysis/bulk-analyze")
async def bulk_analyze_conversations(
    conversations: List[str] = Form(...),
    industry: str = Form(default="general"),
    skill_level: str = Form(default="intermediate")
):
    """
    複数の会話を一括分析
    
    Args:
        conversations: 分析対象の会話リスト
        industry: 業界
        skill_level: スキルレベル
    """
    try:
        results = []
        
        for i, conversation in enumerate(conversations):
            result = await custom_analysis_service.analyze_with_custom_perspective(
                conversation_text=conversation,
                industry=industry,
                skill_level=skill_level
            )
            
            results.append({
                "conversation_id": i + 1,
                "analysis": result
            })
        
        # 全体の統計情報
        overall_stats = {
            "total_conversations": len(conversations),
            "average_score": sum(r["analysis"]["overall_score"] for r in results) / len(results),
            "performance_distribution": _calculate_performance_distribution(results)
        }
        
        return {
            "success": True,
            "bulk_analysis_results": results,
            "overall_statistics": overall_stats,
            "message": f"{len(conversations)}件の会話分析が完了しました"
        }
        
    except Exception as e:
        logger.error(f"Bulk analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _calculate_performance_distribution(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """パフォーマンス分布の計算"""
    distribution = {"卓越": 0, "優秀": 0, "良好": 0, "要改善": 0, "要大幅改善": 0}
    
    for result in results:
        level = result["analysis"]["performance_level"]
        if level in distribution:
            distribution[level] += 1
    
    return distribution 