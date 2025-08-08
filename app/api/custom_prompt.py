"""
カスタムプロンプト管理API
営業ロールプレイの返答品質向上のためのプロンプト最適化機能
"""

import logging
import json
import os
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/custom-prompt", tags=["custom-prompt"])

# プロンプトテンプレート保存ディレクトリ
PROMPT_TEMPLATES_DIR = Path("config/prompt_templates")
PROMPT_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


class PromptTemplate(BaseModel):
    """プロンプトテンプレートモデル"""

    name: str
    description: str
    category: str  # sales, analysis, customer_service, training
    language: str = "ja"
    system_prompt: str
    user_prompt_template: str
    parameters: Dict[str, Any] = {}
    quality_settings: Dict[str, Any] = {}
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PromptOptimizationRequest(BaseModel):
    """プロンプト最適化リクエスト"""

    current_prompt: str
    target_scenario: str  # sales, customer_service, technical_support
    quality_goals: List[str]  # ["accuracy", "empathy", "professionalism", "efficiency"]
    customer_type: str = "general"
    industry: str = "general"


# デフォルトプロンプトテンプレート
DEFAULT_TEMPLATES = {
    "premium_sales_expert": {
        "name": "プレミアム営業エキスパート",
        "description": "最高品質の営業対応に特化したプロンプト",
        "category": "sales",
        "system_prompt": """
あなたは20年以上の経験を持つトップセールスです。以下の特徴を必ず守ってください：

🎯 **営業哲学**
- 顧客の成功が最優先
- 信頼関係の構築を重視
- ソリューション思考で課題解決
- 誠実で透明性のあるコミュニケーション

🎪 **コミュニケーションスタイル**
- 温かみがありながらプロフェッショナル
- 相手の立場に立った共感的対応
- 具体的で分かりやすい説明
- 適切なタイミングでの質問

📊 **対応品質基準**
- 60-100文字の自然な長さ
- 敬語を正しく使用
- 業界専門用語を適切に活用
- 次のアクションを明確に示す
""",
        "user_prompt_template": """
【顧客情報】
- 発言: "{customer_input}"
- 業界: {industry}
- 顧客タイプ: {customer_type}
- 営業ステージ: {sales_stage}
- 会話履歴: {conversation_history}

【対応要求】
上記情報を踏まえ、最高品質の営業応答を生成してください。顧客の真のニーズを理解し、価値ある提案につなげる応答をお願いします。
""",
        "quality_settings": {
            "max_tokens": 150,
            "temperature": 0.6,
            "top_p": 0.9,
            "frequency_penalty": 0.3,
            "presence_penalty": 0.2,
        },
    },
    "consultative_advisor": {
        "name": "コンサルタティブアドバイザー",
        "description": "コンサルティング型営業に特化したプロンプト",
        "category": "sales",
        "system_prompt": """
あなたは戦略コンサルタントとしての視点を持つ営業アドバイザーです：

🔍 **分析的アプローチ**
- データドリブンな提案
- ROI・効果測定を重視
- リスク分析と対策提示
- 長期的視点での価値創造

💡 **提案スタイル**
- 課題の根本原因を特定
- 複数の解決策を比較検討
- 実装計画の具体的提示
- 成功指標の明確化

🤝 **関係構築**
- 対等なパートナーとしての姿勢
- 専門知識の積極的共有
- 顧客の成長支援にコミット
- 継続的な改善提案
""",
        "user_prompt_template": """
【分析対象】
顧客発言: "{customer_input}"
企業規模: {company_size}
業界: {industry}
現在の課題: {current_challenges}

【コンサルティング要求】
戦略的視点から最適な提案を行ってください。データに基づく具体的な改善案と、実装ロードマップを含む応答をお願いします。
""",
        "quality_settings": {"max_tokens": 200, "temperature": 0.4, "top_p": 0.85},
    },
    "empathetic_supporter": {
        "name": "共感型サポーター",
        "description": "感情的サポートと信頼関係構築に特化",
        "category": "customer_service",
        "system_prompt": """
あなたは卓越した感情知能を持つカスタマーサクセス担当者です：

❤️ **感情面での配慮**
- 顧客の感情状態を敏感に察知
- 不安や懸念に対する共感的対応
- ポジティブな感情の増幅
- ストレス軽減を常に意識

🛡️ **信頼関係構築**
- 誠実で透明性のあるコミュニケーション
- 約束は必ず守る姿勢
- 顧客の立場に立った思考
- 長期的関係性を重視

🌟 **サポート品質**
- 迅速で的確な問題解決
- 予防的なアドバイス提供
- 継続的なフォローアップ
- 顧客成功への積極的関与
""",
        "user_prompt_template": """
【顧客状況】
発言内容: "{customer_input}"
感情状態: {emotional_state}
問題の緊急度: {urgency_level}
過去のやり取り: {interaction_history}

【サポート要求】
顧客の感情に寄り添いながら、実際的な解決策を提供してください。安心感と信頼感を与える応答をお願いします。
""",
    },
}


@router.get("/templates")
async def get_prompt_templates() -> Dict[str, Any]:
    """利用可能なプロンプトテンプレート一覧を取得"""
    templates = {}

    # デフォルトテンプレートを追加
    templates.update(DEFAULT_TEMPLATES)

    # カスタムテンプレートを読み込み
    for template_file in PROMPT_TEMPLATES_DIR.glob("*.json"):
        try:
            with open(template_file, "r", encoding="utf-8") as f:
                custom_template = json.load(f)
                templates[template_file.stem] = custom_template
        except Exception as e:
            logger.warning(f"カスタムテンプレート読み込みエラー: {template_file}: {e}")

    return {
        "total_templates": len(templates),
        "categories": list(
            set(t.get("category", "general") for t in templates.values())
        ),
        "templates": templates,
    }


@router.post("/templates")
async def create_prompt_template(template: PromptTemplate) -> Dict[str, Any]:
    """新しいプロンプトテンプレートを作成"""
    try:
        # タイムスタンプを追加
        template.created_at = datetime.now().isoformat()
        template.updated_at = template.created_at

        # ファイルに保存
        template_file = (
            PROMPT_TEMPLATES_DIR / f"{template.name.replace(' ', '_').lower()}.json"
        )
        with open(template_file, "w", encoding="utf-8") as f:
            json.dump(template.dict(), f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "template_id": template.name,
            "file_path": str(template_file),
            "message": "プロンプトテンプレートが正常に作成されました",
        }

    except Exception as e:
        logger.error(f"プロンプトテンプレート作成エラー: {e}")
        raise HTTPException(
            status_code=500, detail=f"テンプレート作成に失敗しました: {e}"
        )


@router.get("/templates/{template_id}")
async def get_prompt_template(template_id: str) -> Dict[str, Any]:
    """特定のプロンプトテンプレートを取得"""

    # デフォルトテンプレートから検索
    if template_id in DEFAULT_TEMPLATES:
        return DEFAULT_TEMPLATES[template_id]

    # カスタムテンプレートから検索
    template_file = PROMPT_TEMPLATES_DIR / f"{template_id}.json"
    if template_file.exists():
        try:
            with open(template_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"テンプレート読み込みエラー: {e}"
            )

    raise HTTPException(status_code=404, detail="テンプレートが見つかりません")


@router.post("/optimize")
async def optimize_prompt(request: PromptOptimizationRequest) -> Dict[str, Any]:
    """プロンプトを自動最適化"""

    optimization_strategies = {
        "sales": {
            "accuracy": "具体的な数値と事例を含める",
            "empathy": "顧客の感情に共感する表現を追加",
            "professionalism": "敬語と業界用語を適切に使用",
            "efficiency": "簡潔で要点を絞った表現に調整",
        },
        "customer_service": {
            "accuracy": "正確な情報提供を最優先",
            "empathy": "顧客の困り事に寄り添う表現",
            "professionalism": "丁寧で親しみやすい敬語",
            "efficiency": "迅速な問題解決を重視",
        },
    }

    try:
        # 最適化戦略を選択
        strategies = optimization_strategies.get(
            request.target_scenario, optimization_strategies["sales"]
        )

        # 最適化されたプロンプトを生成
        optimized_sections = []

        for goal in request.quality_goals:
            if goal in strategies:
                optimized_sections.append(f"【{goal.upper()}】{strategies[goal]}")

        optimized_prompt = f"""
{request.current_prompt}

【最適化指針】
{chr(10).join(optimized_sections)}

【顧客タイプ特化】{request.customer_type}
【業界特化】{request.industry}

上記の指針に従って、より効果的な応答を生成してください。
"""

        return {
            "success": True,
            "original_prompt": request.current_prompt,
            "optimized_prompt": optimized_prompt,
            "optimization_applied": request.quality_goals,
            "target_scenario": request.target_scenario,
            "improvements": [
                strategies[goal] for goal in request.quality_goals if goal in strategies
            ],
        }

    except Exception as e:
        logger.error(f"プロンプト最適化エラー: {e}")
        raise HTTPException(status_code=500, detail=f"最適化に失敗しました: {e}")


@router.post("/test")
async def test_prompt_quality(
    template_id: str = Form(...),
    test_input: str = Form(...),
    customer_type: str = Form(default="general"),
    industry: str = Form(default="general"),
) -> Dict[str, Any]:
    """プロンプトの品質をテスト"""

    try:
        # テンプレートを取得
        template = await get_prompt_template(template_id)

        # テストパラメータを設定
        test_params = {
            "customer_input": test_input,
            "customer_type": customer_type,
            "industry": industry,
            "sales_stage": "needs_assessment",
            "conversation_history": "初回コンタクト",
        }

        # プロンプトを構築
        formatted_prompt = template["user_prompt_template"].format(**test_params)
        full_prompt = f"{template['system_prompt']}\n\n{formatted_prompt}"

        # Groq APIでテスト実行
        try:
            from services.groq_service import GroqService
        except ImportError:
            from app.services.groq_service import GroqService
        groq_service = GroqService()

        result = await groq_service.chat_completion(
            full_prompt,
            max_tokens=template.get("quality_settings", {}).get("max_tokens", 150),
            temperature=template.get("quality_settings", {}).get("temperature", 0.7),
        )

        # 品質評価
        response_text = result["response"]
        quality_score = _evaluate_response_quality(
            response_text, customer_type, industry
        )

        return {
            "success": True,
            "template_used": template_id,
            "test_input": test_input,
            "generated_response": response_text,
            "quality_score": quality_score,
            "prompt_length": len(full_prompt),
            "response_length": len(response_text),
            "quality_metrics": {
                "length_appropriate": 60 <= len(response_text) <= 150,
                "politeness_detected": any(
                    word in response_text
                    for word in ["ございます", "いただき", "申し上げ"]
                ),
                "question_included": "？" in response_text
                or "でしょうか" in response_text,
                "industry_relevant": (
                    industry.lower() in response_text.lower()
                    if industry != "general"
                    else True
                ),
            },
        }

    except Exception as e:
        logger.error(f"プロンプトテストエラー: {e}")
        raise HTTPException(status_code=500, detail=f"テストに失敗しました: {e}")


def _evaluate_response_quality(
    response: str, customer_type: str, industry: str
) -> float:
    """応答品質を評価（0-1のスコア）"""
    score = 0.0

    # 長さの適切性 (0.2)
    if 60 <= len(response) <= 150:
        score += 0.2
    elif 30 <= len(response) <= 200:
        score += 0.1

    # 丁寧語の使用 (0.3)
    politeness_words = ["ございます", "いただき", "申し上げ", "恐れ入り", "失礼いたし"]
    if any(word in response for word in politeness_words):
        score += 0.3

    # 質問・確認の含有 (0.2)
    if "？" in response or any(
        word in response for word in ["でしょうか", "いかがでしょう", "お聞かせ"]
    ):
        score += 0.2

    # 具体性 (0.2)
    concrete_words = ["具体的", "詳しく", "例えば", "実際に", "どのような"]
    if any(word in response for word in concrete_words):
        score += 0.2

    # 業界関連性 (0.1)
    if industry != "general" and industry.lower() in response.lower():
        score += 0.1

    return min(1.0, score)


@router.get("/analytics")
async def get_prompt_analytics() -> Dict[str, Any]:
    """プロンプト使用状況と効果の分析"""

    # 実際の実装では、使用ログから分析データを取得
    return {
        "total_templates": len(DEFAULT_TEMPLATES)
        + len(list(PROMPT_TEMPLATES_DIR.glob("*.json"))),
        "most_used_template": "premium_sales_expert",
        "average_quality_score": 0.847,
        "usage_by_category": {"sales": 65, "customer_service": 25, "training": 10},
        "quality_trends": {
            "last_week": 0.823,
            "this_week": 0.847,
            "improvement": "+2.9%",
        },
        "top_performing_templates": [
            {"name": "premium_sales_expert", "avg_score": 0.912},
            {"name": "consultative_advisor", "avg_score": 0.889},
            {"name": "empathetic_supporter", "avg_score": 0.867},
        ],
    }
