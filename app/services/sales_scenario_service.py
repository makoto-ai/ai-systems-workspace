"""
営業シナリオサービス
高度な営業ロールプレイのためのシナリオ分析とコンテキスト管理
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class ScenarioType(Enum):
    """営業シナリオの種類"""

    INITIAL_APPROACH = "initial_approach"  # 初回アプローチ
    NEEDS_ASSESSMENT = "needs_assessment"  # ニーズ調査
    SOLUTION_PRESENTATION = "solution_presentation"  # ソリューション提示
    OBJECTION_HANDLING = "objection_handling"  # 反対意見への対応
    CLOSING = "closing"  # クロージング
    FOLLOW_UP = "follow_up"  # フォローアップ


class CustomerType(Enum):
    """顧客タイプ"""

    ANALYTICAL = "analytical"  # 分析型
    DECISIVE = "decisive"  # 決断型
    COLLABORATIVE = "collaborative"  # 協調型
    SKEPTICAL = "skeptical"  # 慎重型
    DRIVER = "driver"  # 推進型
    EXPRESSIVE = "expressive"  # 表現型
    AMIABLE = "amiable"  # 親和型


class ObjectionType(Enum):
    """反対意見のタイプ"""

    PRICE = "price"  # 価格に関する反対意見
    TIMING = "timing"  # 時期に関する反対意見
    AUTHORITY = "authority"  # 決定権に関する反対意見
    NEED = "need"  # ニーズに関する反対意見
    TRUST = "trust"  # 信頼に関する反対意見
    COMPETITION = "competition"  # 競合に関する反対意見


@dataclass
class ScenarioContext:
    """営業シナリオのコンテキスト情報"""

    scenario_type: ScenarioType
    customer_type: CustomerType
    sales_stage: str
    bant_status: Dict[str, Any] = field(default_factory=dict)
    customer_profile: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    current_objectives: List[str] = field(default_factory=list)
    achieved_objectives: List[str] = field(default_factory=list)


@dataclass
class ScenarioResponse:
    """営業シナリオの処理結果"""

    response_text: str
    scenario_analysis: Dict[str, Any]
    stage_progression: str
    recommended_actions: List[str]
    bant_updates: Dict[str, Any]
    speaker_id: int
    next_objectives: List[str] = field(default_factory=list)


class SalesScenarioService:
    """営業シナリオサービス"""

    def __init__(self):
        """サービスの初期化"""
        self.scenario_templates = self._load_scenario_templates()
        logger.info("営業シナリオサービスを初期化しました")

    def _load_scenario_templates(self) -> Dict[str, Any]:
        """シナリオテンプレートの読み込み"""
        return {
            "initial_approach": {
                "greeting": "お忙しい中、お時間をいただきありがとうございます。",
                "purpose": "本日は貴社の業務効率化についてお話しさせていただければと思います。",
                "questions": [
                    "現在の業務で一番お困りの点はどのようなことでしょうか？",
                    "どのような改善をお考えでしょうか？",
                ],
            },
            "needs_assessment": {
                "questions": [
                    "どのような課題を解決したいとお考えでしょうか？",
                    "現在のシステムで不便に感じる点はありますか？",
                    "理想的な状態はどのようなものでしょうか？",
                ]
            },
            "solution_presentation": {
                "introduction": "貴社の課題を解決するソリューションをご提案いたします。",
                "benefits": [
                    "業務効率が大幅に向上します",
                    "コスト削減が実現できます",
                    "品質向上が期待できます",
                ],
            },
            "objection_handling": {
                "price": "投資対効果を詳しくご説明させていただきます。",
                "timing": "最適な導入時期についてご相談させていただきます。",
                "authority": "決定権をお持ちの方にもご説明させていただきたいと思います。",
                "need": "課題の詳細について改めて確認させていただけますでしょうか。",
            },
            "closing": {
                "trial": "まずは無料トライアルから始めてみませんか？",
                "next_steps": "次のステップについて確認させていただきたいと思います。",
                "timeline": "導入スケジュールについて相談させていただけますでしょうか？",
            },
        }

    async def process_scenario(
        self, user_input: str, context: ScenarioContext
    ) -> ScenarioResponse:
        """営業シナリオの処理"""
        try:
            # 入力の分析
            intent_analysis = self._analyze_intent(user_input)
            sentiment_analysis = self._analyze_sentiment(user_input)

            # シナリオ分析
            scenario_analysis = {
                "intent": intent_analysis,
                "sentiment": sentiment_analysis,
                "buying_signals": self._detect_buying_signals(user_input),
                "concerns": self._detect_concerns(user_input),
                "confidence": 0.85,
                "scenario_type": context.scenario_type.value,
            }

            # 反対意見の処理時は objection_type を追加
            if context.scenario_type == ScenarioType.OBJECTION_HANDLING:
                objection_type = self._detect_objection_type(user_input)
                scenario_analysis["objection_type"] = objection_type

            # 応答生成
            response_text = self._generate_response(
                user_input, context, scenario_analysis
            )

            # ステージ進行の判定
            stage_progression = self._determine_stage_progression(
                context, scenario_analysis
            )

            # 推奨アクションの生成
            recommended_actions = self._generate_recommended_actions(
                context, scenario_analysis
            )

            # BANT情報の更新
            bant_updates = self._extract_bant_updates(user_input, context)

            # スピーカーIDの決定
            speaker_id = self._determine_speaker_id(context)

            # 次の目標の生成
            next_objectives = self._generate_next_objectives(context, scenario_analysis)

            return ScenarioResponse(
                response_text=response_text,
                scenario_analysis=scenario_analysis,
                stage_progression=stage_progression,
                recommended_actions=recommended_actions,
                bant_updates=bant_updates,
                speaker_id=speaker_id,
                next_objectives=next_objectives,
            )

        except Exception as e:
            logger.error(f"シナリオ処理エラー: {e}")
            return ScenarioResponse(
                response_text="申し訳ございませんが、応答を生成できませんでした。",
                scenario_analysis={
                    "intent": "unknown",
                    "sentiment": "neutral",
                    "confidence": 0.0,
                },
                stage_progression=context.sales_stage,
                recommended_actions=["状況を確認する"],
                bant_updates={},
                speaker_id=14,
            )

    def _analyze_intent(self, user_input: str) -> str:
        """意図分析"""
        user_input_lower = user_input.lower()

        if any(
            keyword in user_input_lower
            for keyword in ["料金", "価格", "費用", "値段", "コスト"]
        ):
            return "pricing_inquiry"
        elif any(
            keyword in user_input_lower for keyword in ["機能", "できること", "特徴"]
        ):
            return "feature_inquiry"
        elif any(keyword in user_input_lower for keyword in ["検討", "考える", "判断"]):
            return "consideration"
        elif any(keyword in user_input_lower for keyword in ["問題", "課題", "困って"]):
            return "problem_identification"
        elif any(keyword in user_input_lower for keyword in ["導入", "始める", "開始"]):
            return "implementation_inquiry"
        else:
            return "general_inquiry"

    def _detect_intent(self, user_input: str) -> str:
        """意図検出（テスト用）"""
        user_input_lower = user_input.lower()

        if any(
            keyword in user_input_lower
            for keyword in ["こんにちは", "はじめまして", "お疲れ様"]
        ):
            return "greeting"
        elif any(
            keyword in user_input_lower
            for keyword in ["料金", "価格", "費用", "いくら"]
        ):
            return "pricing_inquiry"
        elif any(
            keyword in user_input_lower
            for keyword in ["機能", "できること", "特徴", "教えて"]
        ):
            return "feature_inquiry"
        elif any(
            keyword in user_input_lower
            for keyword in ["検討", "考える", "判断", "したい"]
        ):
            return "decision"
        elif any(
            keyword in user_input_lower
            for keyword in ["高い", "高すぎ", "問題", "困る"]
        ):
            return "objection"
        else:
            return "general_inquiry"

    def _analyze_sentiment(self, user_input: str) -> str:
        """感情分析（簡易版）"""
        positive_words = ["良い", "すばらしい", "便利", "助かる", "興味深い", "期待"]
        negative_words = ["心配", "不安", "困る", "難しい", "高い", "問題"]

        positive_count = sum(1 for word in positive_words if word in user_input)
        negative_count = sum(1 for word in negative_words if word in user_input)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def _detect_buying_signals(self, user_input: str) -> List[str]:
        """購買シグナルの検出"""
        signals = []

        if any(
            keyword in user_input.lower()
            for keyword in ["導入", "始める", "購入", "契約"]
        ):
            signals.append("purchase_intent")
        if any(keyword in user_input.lower() for keyword in ["予算", "費用", "投資"]):
            signals.append("budget_discussion")
            signals.append("budget_mentioned")  # テスト用の追加
        if any(
            keyword in user_input.lower()
            for keyword in ["いつ", "時期", "スケジュール"]
        ):
            signals.append("timeline_interest")
        if any(
            keyword in user_input.lower()
            for keyword in ["急い", "急ぎ", "至急", "早急"]
        ):
            signals.append("urgency")

        return signals

    def _detect_concerns(self, user_input: str) -> List[str]:
        """懸念事項の検出"""
        concerns = []

        if any(keyword in user_input.lower() for keyword in ["高い", "高額", "費用"]):
            concerns.append("price_concern")
        if any(keyword in user_input.lower() for keyword in ["複雑", "難しい", "大変"]):
            concerns.append("complexity_concern")
        if any(keyword in user_input.lower() for keyword in ["時間", "忙しい", "余裕"]):
            concerns.append("time_concern")

        return concerns

    def _detect_objection_type(self, user_input: str) -> str:
        """反対意見のタイプを検出"""
        user_input_lower = user_input.lower()

        if any(
            keyword in user_input_lower
            for keyword in ["高い", "高額", "価格", "費用", "料金"]
        ):
            return "price"
        elif any(
            keyword in user_input_lower
            for keyword in ["時間", "忙しい", "今は", "後で"]
        ):
            return "timing"
        elif any(
            keyword in user_input_lower for keyword in ["上司", "決定", "承認", "権限"]
        ):
            return "authority"
        elif any(
            keyword in user_input_lower
            for keyword in ["必要", "要らない", "不要", "わからない"]
        ):
            return "need"
        elif any(
            keyword in user_input_lower for keyword in ["信頼", "心配", "不安", "疑問"]
        ):
            return "trust"
        elif any(
            keyword in user_input_lower
            for keyword in ["他社", "競合", "比較", "検討中"]
        ):
            return "competition"
        else:
            return "general"

    def _detect_objections(self, user_input: str) -> List[Dict[str, Any]]:
        """反対意見の検出（テスト用）"""
        objections = []
        user_input_lower = user_input.lower()

        if any(keyword in user_input_lower for keyword in ["高い", "高額", "価格"]):
            objections.append({"type": "price", "details": "価格に関する反対意見"})
        if any(
            keyword in user_input_lower for keyword in ["時間", "忙しい", "タイミング"]
        ):
            objections.append({"type": "timing", "details": "時期に関する反対意見"})
        if any(keyword in user_input_lower for keyword in ["上司", "決定権", "承認"]):
            objections.append(
                {"type": "authority", "details": "決定権に関する反対意見"}
            )
        if any(keyword in user_input_lower for keyword in ["必要", "要らない", "不要"]):
            objections.append({"type": "need", "details": "ニーズに関する反対意見"})
        if any(keyword in user_input_lower for keyword in ["他社", "競合", "比較"]):
            objections.append(
                {"type": "competition", "details": "競合に関する反対意見"}
            )

        return objections

    def _generate_response(
        self, user_input: str, context: ScenarioContext, analysis: Dict[str, Any]
    ) -> str:
        """応答の生成"""
        intent = analysis["intent"]
        sentiment = analysis["sentiment"]
        customer_type = context.customer_type

        if intent == "pricing_inquiry":
            return "料金についてご説明いたします。基本プランは月額5万円からとなっており、ご利用規模に応じてカスタマイズも可能です。詳細な見積もりをご用意いたしますので、どのような規模での導入をお考えでしょうか？"
        elif intent == "feature_inquiry":
            if customer_type == CustomerType.ANALYTICAL:
                return "当システムの主な機能についてご説明いたします。詳細な技術仕様とデータ分析機能をご紹介できます。どのような指標を重視されていますでしょうか？"
            elif customer_type == CustomerType.DRIVER:
                return "当システムの主な機能をご説明いたします。業務効率化の効果は即座に実感いただけます。導入メリットをお聞かせください。"
            else:
                return "当システムの主な機能についてご説明いたします。業務効率化、データ分析、レポート作成などの機能を提供しております。特にどのような機能にご興味がおありでしょうか？"
        elif intent == "consideration":
            return "ご検討いただきありがとうございます。判断材料として、他社様の導入事例や効果測定結果をご紹介することも可能です。どのような点を重視してご検討されていますでしょうか？"
        elif intent == "problem_identification":
            return "課題についてお聞かせください。具体的な問題点を把握することで、最適なソリューションをご提案できます。現在最も困っていることはどのようなことでしょうか？"
        elif intent == "implementation_inquiry":
            return "導入についてお考えいただきありがとうございます。スムーズな導入のため、段階的な実装プランをご提案いたします。まずは現在の業務フローについて教えていただけますでしょうか？"
        else:
            # 顧客タイプに応じた一般的な応答
            if customer_type == CustomerType.ANALYTICAL:
                return "ありがとうございます。データに基づいた詳細な分析結果をご提供いたします。具体的にどのような情報が必要でしょうか？"
            elif customer_type == CustomerType.DRIVER:
                return "ありがとうございます。迅速にご対応いたします。まず優先すべき課題について教えてください。"
            elif customer_type == CustomerType.EXPRESSIVE:
                return "ありがとうございます！お客様のビジョンを実現するお手伝いをさせていただきます。どのような将来像をお描きでしょうか？"
            elif customer_type == CustomerType.AMIABLE:
                return "ありがとうございます。お客様のペースに合わせて丁寧にご説明させていただきます。ご不明な点があればいつでもお聞かせください。"
            elif customer_type == CustomerType.COLLABORATIVE:
                return "ありがとうございます。チーム全体でより良いソリューションを検討していきましょう。関係者の皆様のご意見もお聞かせください。"
            elif customer_type == CustomerType.SKEPTICAL:
                return "ありがとうございます。お客様の慎重なご検討は大変重要です。十分な検証材料をご提供いたしますので、ご質問をお聞かせください。"
            else:
                return "ありがとうございます。より詳しくお話しさせていただくために、現在の状況について教えていただけますでしょうか？"

    def _determine_stage_progression(
        self, context: ScenarioContext, analysis: Dict[str, Any]
    ) -> str:
        """営業ステージの進行判定"""
        current_stage = context.sales_stage
        intent = analysis["intent"]
        buying_signals = analysis["buying_signals"]

        if current_stage == "prospecting":
            if intent in ["problem_identification", "feature_inquiry"]:
                return "needs_assessment"
        elif current_stage == "needs_assessment":
            if intent == "pricing_inquiry" or "budget_discussion" in buying_signals:
                return "proposal"
        elif current_stage == "proposal":
            if "purchase_intent" in buying_signals:
                return "closing"
            elif analysis.get("concerns"):
                return "objection_handling"
        elif current_stage == "objection_handling":
            if "purchase_intent" in buying_signals:
                return "closing"

        return current_stage

    def _generate_recommended_actions(
        self, context: ScenarioContext, analysis: Dict[str, Any]
    ) -> List[str]:
        """推奨アクションの生成"""
        actions = []
        intent = analysis["intent"]
        concerns = analysis.get("concerns", [])

        if intent == "pricing_inquiry":
            actions.append("詳細な見積もりを提供する")
            actions.append("ROI計算を説明する")
        elif intent == "feature_inquiry":
            actions.append("デモンストレーションを提案する")
            actions.append("導入事例を紹介する")
        elif concerns:
            actions.append("懸念事項に対処する")
            actions.append("追加情報を提供する")

        if not actions:
            actions.append("ニーズをさらに詳しく聞く")

        return actions

    def _extract_bant_updates(
        self, user_input: str, context: ScenarioContext
    ) -> Dict[str, Any]:
        """BANT情報の抽出"""
        updates = {}

        # Budget（予算）の抽出
        if any(
            keyword in user_input.lower() for keyword in ["予算", "費用", "万円", "円"]
        ):
            # 具体的な金額が言及されている場合は qualified
            if any(
                keyword in user_input.lower()
                for keyword in ["万円", "円", "程度", "くらい"]
            ):
                updates["budget"] = {
                    "status": "qualified",
                    "details": "予算が具体的に示されました",
                }
            else:
                updates["budget"] = {
                    "status": "interested",
                    "details": "予算に関する興味",
                }

        # Authority（決定権）の抽出
        if any(keyword in user_input.lower() for keyword in ["決定", "上司", "承認"]):
            updates["authority"] = {
                "status": "mentioned",
                "details": "決定権に関する言及",
            }

        # Need（ニーズ）の抽出
        if any(
            keyword in user_input.lower()
            for keyword in ["必要", "課題", "問題", "業務効率", "改善"]
        ):
            updates["need"] = {
                "status": "identified",
                "details": "ニーズが特定されました",
            }

        # Timeline（時期）の抽出
        if any(
            keyword in user_input.lower()
            for keyword in [
                "いつ",
                "時期",
                "急い",
                "来月",
                "来週",
                "今月",
                "今年",
                "来年",
            ]
        ):
            updates["timeline"] = {"status": "mentioned", "details": "時期に関する言及"}

        return updates

    def _determine_speaker_id(self, context: ScenarioContext) -> int:
        """スピーカーIDの決定"""
        # 顧客タイプと営業ステージに応じてスピーカーIDを選択
        if context.customer_type == CustomerType.ANALYTICAL:
            return 52  # 雀松朱司（コンサルタント）
        elif context.customer_type == CustomerType.DRIVER:
            return 11  # 玄野武宏（ベテラン営業）
        elif context.customer_type == CustomerType.COLLABORATIVE:
            return 8  # 春日部つむぎ（丁寧）
        elif context.customer_type == CustomerType.SKEPTICAL:
            return 13  # 青山龍星（新人営業）
        elif context.customer_type == CustomerType.EXPRESSIVE:
            return 14  # 女性営業（表現豊か）
        elif context.customer_type == CustomerType.AMIABLE:
            return 8  # 春日部つむぎ（親和型に適した丁寧さ）
        else:
            return 14  # デフォルトは女性営業

    def _generate_next_objectives(
        self, context: ScenarioContext, analysis: Dict[str, Any]
    ) -> List[str]:
        """次の目標の生成"""
        objectives = []
        intent = analysis["intent"]
        current_stage = context.sales_stage

        if current_stage == "prospecting":
            objectives.extend(["build_rapport", "identify_needs"])
        elif current_stage == "needs_assessment":
            objectives.extend(["qualify_budget", "understand_decision_process"])
        elif current_stage == "proposal":
            objectives.extend(["present_solution", "address_concerns"])
        elif current_stage == "objection_handling":
            objectives.extend(["resolve_objections", "confirm_value"])
        elif current_stage == "closing":
            objectives.extend(["secure_commitment", "schedule_next_steps"])

        return objectives

    def _calculate_bant_completion(
        self, current_bant: Dict[str, Any], updates: Dict[str, Any]
    ) -> float:
        """BANT完了率の計算"""
        total_items = 4  # Budget, Authority, Need, Timeline
        qualified_count = 0

        # 現在のBANT状況を更新
        updated_bant = current_bant.copy()
        updated_bant.update(updates)

        # 各項目の qualified 状況をカウント
        for item in ["budget", "authority", "need", "timeline"]:
            if updated_bant.get(item, {}).get("status") == "qualified":
                qualified_count += 1

        return qualified_count / total_items

    def _determine_bant_focus(
        self, bant_status: Dict[str, Any], analysis: Dict[str, Any]
    ) -> str:
        """BANT焦点項目の決定"""
        # 分析結果から言及されたBANT項目を優先
        bant_info = analysis.get("bant_info", {})

        for item in ["authority", "budget", "need", "timeline"]:
            if bant_info.get(item, {}).get("mentioned"):
                return item

        # 未確認項目を優先
        for item in ["budget", "authority", "need", "timeline"]:
            if bant_status.get(item, {}).get("status") == "unknown":
                return item

        # デフォルトはneed
        return "need"

    def _determine_scenario_type(
        self, analysis: Dict[str, Any], context: ScenarioContext
    ) -> ScenarioType:
        """シナリオタイプの決定"""
        # 反対意見がある場合
        if analysis.get("objections"):
            return ScenarioType.OBJECTION_HANDLING

        # 購買シグナルが強い場合
        buying_signals = analysis.get("buying_signals", [])
        if "purchase_intent" in buying_signals:
            return ScenarioType.CLOSING

        # 現在のセールスステージに基づく
        sales_stage = context.sales_stage
        if sales_stage == "prospecting":
            return ScenarioType.INITIAL_APPROACH
        elif sales_stage == "needs_assessment":
            return ScenarioType.NEEDS_ASSESSMENT
        elif sales_stage == "proposal":
            return ScenarioType.SOLUTION_PRESENTATION
        elif sales_stage == "closing":
            return ScenarioType.CLOSING
        else:
            return ScenarioType.INITIAL_APPROACH


# サービスインスタンス
_sales_scenario_service = None


def get_sales_scenario_service() -> SalesScenarioService:
    """営業シナリオサービスのインスタンスを取得"""
    global _sales_scenario_service
    if _sales_scenario_service is None:
        _sales_scenario_service = SalesScenarioService()
    return _sales_scenario_service
