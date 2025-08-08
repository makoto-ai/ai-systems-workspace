"""
Privacy-Aware Context Service
プライバシーを保護しながら会話文脈を理解・強化するサービス

設計方針:
- 個人情報は保存しない
- 音声データは一切保存しない
- セッション終了で自動削除
- 匿名化された特徴量のみ抽出
- 文脈パターンの学習のみ実行
"""

import logging
import hashlib
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import asyncio
import re

logger = logging.getLogger(__name__)


class ContextLevel(Enum):
    """文脈理解レベル"""

    IMMEDIATE = "immediate"  # 直前の発言のみ
    SESSION = "session"  # セッション内全体
    PATTERN = "pattern"  # 匿名化されたパターン学習


class PrivacyMode(Enum):
    """プライバシー保護モード"""

    STRICT = "strict"  # 個人情報完全除外
    STANDARD = "standard"  # 匿名化処理
    RESEARCH = "research"  # 明示的同意による学習


@dataclass
class AnonymizedContext:
    """匿名化された文脈情報"""

    context_id: str
    session_hash: str  # セッションの匿名ハッシュ
    topic_categories: List[str]
    sentiment_pattern: str
    engagement_level: str
    sales_stage_progression: List[str]
    concern_categories: List[str]
    interest_signals: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None


@dataclass
class ContextPattern:
    """学習された文脈パターン（完全匿名）"""

    pattern_id: str
    pattern_type: str  # "topic_flow", "objection_handling", etc.
    success_indicators: List[str]
    common_transitions: Dict[str, str]
    effectiveness_score: float
    usage_count: int
    last_updated: datetime


@dataclass
class SessionContext:
    """セッション内文脈（一時的、個人情報なし）"""

    session_id: str
    context_history: List[Dict[str, Any]]
    current_topic: Optional[str]
    engagement_trend: List[float]
    sales_momentum: str
    identified_patterns: List[str]
    next_best_actions: List[str]
    created_at: datetime


class PrivacyAwareContextService:
    """プライバシー保護型文脈理解サービス"""

    def __init__(self, privacy_mode: PrivacyMode = PrivacyMode.STRICT):
        """
        Initialize Privacy-Aware Context Service

        Args:
            privacy_mode: プライバシー保護レベル
        """
        self.privacy_mode = privacy_mode

        # セッション内文脈（メモリのみ、一時的）
        self.session_contexts: Dict[str, SessionContext] = {}

        # 匿名化されたパターン学習データ
        self.context_patterns: Dict[str, ContextPattern] = {}

        # プライバシー設定
        self.privacy_config = self._get_privacy_config(privacy_mode)

        # 文脈分析設定
        self.max_context_length = 10  # 直近10ターンまで
        self.session_timeout_minutes = 60

        # 定期クリーンアップタスク開始（イベントループがある場合のみ）
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self._periodic_cleanup())
        except RuntimeError:
            # イベントループがない場合は後で開始
            pass

        logger.info(
            f"Privacy-Aware Context Service initialized (mode: {privacy_mode.value})"
        )

    def _get_privacy_config(self, mode: PrivacyMode) -> Dict[str, Any]:
        """プライバシー設定を取得"""
        configs = {
            PrivacyMode.STRICT: {
                "store_content": False,  # 発言内容は保存しない
                "store_audio": False,  # 音声は絶対保存しない
                "store_personal_info": False,  # 個人情報は保存しない
                "anonymize_immediately": True,  # 即座に匿名化
                "session_timeout_minutes": 60,  # 1時間でタイムアウト
                "auto_delete_on_timeout": True,  # タイムアウト時自動削除
                "pattern_learning": True,  # 匿名パターン学習のみ
                "cross_session_context": False,  # セッション跨ぎ禁止
            },
            PrivacyMode.STANDARD: {
                "store_content": False,  # 発言内容は保存しない
                "store_audio": False,  # 音声は絶対保存しない
                "store_personal_info": False,  # 個人情報は保存しない
                "anonymize_immediately": True,  # 即座に匿名化
                "session_timeout_minutes": 120,  # 2時間でタイムアウト
                "auto_delete_on_timeout": True,  # タイムアウト時自動削除
                "pattern_learning": True,  # 匿名パターン学習
                "cross_session_context": False,  # セッション跨ぎ禁止
            },
            PrivacyMode.RESEARCH: {
                "store_content": False,  # 発言内容は保存しない（研究でも）
                "store_audio": False,  # 音声は絶対保存しない
                "store_personal_info": False,  # 個人情報は保存しない
                "anonymize_immediately": True,  # 即座に匿名化
                "session_timeout_minutes": 240,  # 4時間でタイムアウト
                "auto_delete_on_timeout": True,  # タイムアウト時自動削除
                "pattern_learning": True,  # 高度なパターン学習
                "cross_session_context": False,  # セッション跨ぎ禁止（安全性優先）
            },
        }
        return configs[mode]

    async def initialize_session_context(self, session_id: str) -> str:
        """セッション文脈を初期化"""
        try:
            # 既存セッションがある場合はクリーンアップ
            if session_id in self.session_contexts:
                await self._cleanup_session(session_id)

            # 新しいセッション文脈を作成
            context = SessionContext(
                session_id=session_id,
                context_history=[],
                current_topic=None,
                engagement_trend=[],
                sales_momentum="neutral",
                identified_patterns=[],
                next_best_actions=[],
                created_at=datetime.now(),
            )

            self.session_contexts[session_id] = context

            logger.info(f"Initialized privacy-aware context for session: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to initialize session context: {e}")
            raise

    async def update_context(
        self,
        session_id: str,
        user_input: str,
        ai_response: str,
        analysis_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """文脈を更新（個人情報を除外して）"""
        try:
            if session_id not in self.session_contexts:
                await self.initialize_session_context(session_id)

            context = self.session_contexts[session_id]

            # 個人情報を除外した匿名化処理
            anonymized_input = await self._anonymize_content(user_input)
            anonymized_response = await self._anonymize_content(ai_response)

            # 文脈情報を抽出（個人情報なし）
            context_info = await self._extract_context_features(
                anonymized_input, anonymized_response, analysis_data or {}
            )

            # セッション文脈を更新
            context.context_history.append(
                {
                    "turn_id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                    "topic_category": context_info.get("topic_category"),
                    "sentiment": context_info.get("sentiment"),
                    "engagement_level": context_info.get("engagement_level"),
                    "sales_stage": context_info.get("sales_stage"),
                    "buying_signals": context_info.get("buying_signals", []),
                    "concerns": context_info.get("concerns", []),
                }
            )

            # 履歴長制限（プライバシー保護）
            if len(context.context_history) > self.max_context_length:
                context.context_history = context.context_history[
                    -self.max_context_length :
                ]

            # 現在のトピックを更新
            context.current_topic = context_info.get("topic_category")

            # エンゲージメント傾向を更新
            engagement_score = context_info.get("engagement_level", 0.5)
            context.engagement_trend.append(engagement_score)
            if len(context.engagement_trend) > 5:  # 直近5ターンのみ
                context.engagement_trend = context.engagement_trend[-5:]

            # 営業モメンタムを計算
            context.sales_momentum = await self._calculate_sales_momentum(context)

            # パターン識別
            context.identified_patterns = await self._identify_conversation_patterns(
                context
            )

            # 次のベストアクションを提案
            context.next_best_actions = await self._suggest_next_actions(context)

            # 匿名化されたパターンを学習データに追加
            if self.privacy_config["pattern_learning"]:
                await self._learn_anonymized_patterns(context_info)

            return {
                "success": True,
                "context_updated": True,
                "current_topic": context.current_topic,
                "sales_momentum": context.sales_momentum,
                "engagement_trend": (
                    context.engagement_trend[-1] if context.engagement_trend else 0.5
                ),
                "identified_patterns": context.identified_patterns,
                "next_best_actions": context.next_best_actions,
                "privacy_mode": self.privacy_mode.value,
            }

        except Exception as e:
            logger.error(f"Failed to update context: {e}")
            return {"success": False, "error": str(e)}

    async def get_contextual_suggestions(
        self, session_id: str, current_input: str
    ) -> Dict[str, Any]:
        """文脈に基づいた提案を生成"""
        try:
            if session_id not in self.session_contexts:
                return {"suggestions": [], "context_available": False}

            context = self.session_contexts[session_id]

            # 現在の入力を匿名化
            anonymized_input = await self._anonymize_content(current_input)

            # 文脈に基づいた提案を生成
            suggestions = []

            # 1. トピック継続性の提案
            if context.current_topic:
                topic_suggestions = await self._get_topic_continuity_suggestions(
                    context.current_topic, anonymized_input
                )
                suggestions.extend(topic_suggestions)

            # 2. エンゲージメント向上の提案
            if context.engagement_trend:
                engagement_suggestions = await self._get_engagement_suggestions(
                    context.engagement_trend
                )
                suggestions.extend(engagement_suggestions)

            # 3. 営業ステージ適応の提案
            stage_suggestions = await self._get_sales_stage_suggestions(
                context.sales_momentum, context.identified_patterns
            )
            suggestions.extend(stage_suggestions)

            # 4. パターンマッチングによる提案
            pattern_suggestions = await self._get_pattern_based_suggestions(
                context.identified_patterns
            )
            suggestions.extend(pattern_suggestions)

            return {
                "success": True,
                "suggestions": suggestions[:5],  # 上位5つに制限
                "context_available": True,
                "current_topic": context.current_topic,
                "sales_momentum": context.sales_momentum,
                "confidence": self._calculate_suggestion_confidence(context),
            }

        except Exception as e:
            logger.error(f"Failed to get contextual suggestions: {e}")
            return {"success": False, "error": str(e)}

    async def _anonymize_content(self, content: str) -> str:
        """コンテンツを匿名化"""
        try:
            # 個人情報パターンを除去
            anonymized = content

            # 名前のパターンを除去
            anonymized = re.sub(r"[一-龯]{2,4}(さん|様|氏|君)", "[NAME]", anonymized)

            # 会社名のパターンを除去
            anonymized = re.sub(
                r"(株式会社|有限会社|合同会社|[A-Za-z]+(?:株式会社|Corp|Inc|Ltd))",
                "[COMPANY]",
                anonymized,
            )

            # 電話番号を除去
            anonymized = re.sub(r"\d{2,4}-\d{2,4}-\d{4}", "[PHONE]", anonymized)

            # メールアドレスを除去
            anonymized = re.sub(
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL]", anonymized
            )

            # 住所情報を除去
            anonymized = re.sub(
                r"[都道府県市区町村]{2,}[0-9一-九十百千万-]+", "[ADDRESS]", anonymized
            )

            return anonymized

        except Exception as e:
            logger.error(f"Anonymization failed: {e}")
            return "[ANONYMIZED]"

    async def _extract_context_features(
        self, user_input: str, ai_response: str, analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """文脈特徴量を抽出（個人情報なし）"""
        try:
            features = {}

            # トピックカテゴリ抽出
            features["topic_category"] = await self._categorize_topic(user_input)

            # 感情分析（匿名）
            features["sentiment"] = analysis_data.get("sentiment", "neutral")

            # エンゲージメントレベル
            features["engagement_level"] = await self._calculate_engagement_level(
                user_input
            )

            # 営業ステージ推定
            features["sales_stage"] = await self._estimate_sales_stage(
                user_input, ai_response
            )

            # 購買シグナル検出（匿名化）
            features["buying_signals"] = await self._detect_buying_signals(user_input)

            # 懸念事項検出（匿名化）
            features["concerns"] = await self._detect_concerns(user_input)

            return features

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return {}

    async def _categorize_topic(self, content: str) -> str:
        """トピックをカテゴリ化"""
        try:
            content_lower = content.lower()

            # 営業関連トピック
            if any(
                word in content_lower for word in ["価格", "料金", "費用", "コスト"]
            ):
                return "pricing"
            elif any(
                word in content_lower for word in ["機能", "特徴", "仕様", "スペック"]
            ):
                return "features"
            elif any(
                word in content_lower for word in ["セキュリティ", "安全", "保護"]
            ):
                return "security"
            elif any(
                word in content_lower
                for word in ["導入", "実装", "開始", "スケジュール"]
            ):
                return "implementation"
            elif any(
                word in content_lower for word in ["サポート", "支援", "メンテナンス"]
            ):
                return "support"
            elif any(word in content_lower for word in ["競合", "比較", "他社"]):
                return "competition"
            elif any(word in content_lower for word in ["予算", "投資", "ROI", "効果"]):
                return "budget"
            else:
                return "general"

        except Exception as e:
            logger.error(f"Topic categorization failed: {e}")
            return "unknown"

    async def _calculate_engagement_level(self, content: str) -> float:
        """エンゲージメントレベルを計算"""
        try:
            score = 0.5  # ベースライン

            # ポジティブな指標
            positive_indicators = [
                "はい",
                "そうですね",
                "いいですね",
                "興味",
                "検討",
                "教えて",
            ]
            negative_indicators = ["いえ", "ちょっと", "厳しい", "難しい", "考えます"]

            for indicator in positive_indicators:
                if indicator in content:
                    score += 0.1

            for indicator in negative_indicators:
                if indicator in content:
                    score -= 0.1

            # 質問の存在
            if "？" in content or "ですか" in content:
                score += 0.1

            return max(0.0, min(1.0, score))

        except Exception as e:
            logger.error(f"Engagement calculation failed: {e}")
            return 0.5

    async def _estimate_sales_stage(self, user_input: str, ai_response: str) -> str:
        """営業ステージを推定"""
        try:
            combined_content = user_input + " " + ai_response
            content_lower = combined_content.lower()

            if any(
                word in content_lower for word in ["初めて", "紹介", "概要", "どんな"]
            ):
                return "prospecting"
            elif any(
                word in content_lower for word in ["課題", "問題", "困って", "必要"]
            ):
                return "needs_assessment"
            elif any(
                word in content_lower for word in ["提案", "プラン", "見積", "価格"]
            ):
                return "proposal"
            elif any(
                word in content_lower for word in ["心配", "不安", "懸念", "でも"]
            ):
                return "objection_handling"
            elif any(
                word in content_lower
                for word in ["決めたい", "進めたい", "契約", "導入"]
            ):
                return "closing"
            else:
                return "needs_assessment"  # デフォルト

        except Exception as e:
            logger.error(f"Sales stage estimation failed: {e}")
            return "unknown"

    async def _detect_buying_signals(self, content: str) -> List[str]:
        """購買シグナルを検出"""
        try:
            signals = []
            content_lower = content.lower()

            signal_patterns = {
                "budget_confirmed": ["予算は確保", "費用は大丈夫", "予算内で"],
                "timeline_defined": ["来月から", "年内に", "急いで"],
                "decision_authority": ["決裁権", "決定権", "承認を得て"],
                "specific_interest": ["詳しく教えて", "資料をください", "デモを"],
                "comparison_done": ["他社と比べて", "検討した結果"],
                "positive_reaction": ["いいですね", "素晴らしい", "期待できる"],
            }

            for signal_type, patterns in signal_patterns.items():
                if any(pattern in content_lower for pattern in patterns):
                    signals.append(signal_type)

            return signals

        except Exception as e:
            logger.error(f"Buying signals detection failed: {e}")
            return []

    async def _detect_concerns(self, content: str) -> List[str]:
        """懸念事項を検出"""
        try:
            concerns = []
            content_lower = content.lower()

            concern_patterns = {
                "cost_concern": ["高い", "費用が", "予算が", "コストが"],
                "security_concern": ["セキュリティが心配", "安全性は", "データ保護"],
                "implementation_concern": ["導入が大変", "複雑", "時間がかかる"],
                "reliability_concern": ["信頼できる", "実績は", "トラブルは"],
                "support_concern": ["サポートは", "困った時", "対応してくれる"],
                "compatibility_concern": ["既存システムと", "連携できる", "互換性"],
            }

            for concern_type, patterns in concern_patterns.items():
                if any(pattern in content_lower for pattern in patterns):
                    concerns.append(concern_type)

            return concerns

        except Exception as e:
            logger.error(f"Concerns detection failed: {e}")
            return []

    async def _calculate_sales_momentum(self, context: SessionContext) -> str:
        """営業モメンタムを計算"""
        try:
            if not context.engagement_trend:
                return "neutral"

            # 直近の傾向を分析
            recent_engagement = (
                context.engagement_trend[-3:]
                if len(context.engagement_trend) >= 3
                else context.engagement_trend
            )

            if not recent_engagement:
                return "neutral"

            avg_engagement = sum(recent_engagement) / len(recent_engagement)
            trend = (
                recent_engagement[-1] - recent_engagement[0]
                if len(recent_engagement) > 1
                else 0
            )

            if avg_engagement > 0.7 and trend >= 0:
                return "accelerating"
            elif avg_engagement > 0.6:
                return "positive"
            elif avg_engagement < 0.4 and trend < 0:
                return "declining"
            elif avg_engagement < 0.5:
                return "challenging"
            else:
                return "neutral"

        except Exception as e:
            logger.error(f"Sales momentum calculation failed: {e}")
            return "unknown"

    async def _identify_conversation_patterns(
        self, context: SessionContext
    ) -> List[str]:
        """会話パターンを識別"""
        try:
            patterns = []

            if len(context.context_history) < 2:
                return patterns

            # パターン分析
            topics = [turn.get("topic_category") for turn in context.context_history]
            sentiments = [turn.get("sentiment") for turn in context.context_history]

            # トピック集中パターン
            if len(set(topics)) <= 2:
                patterns.append("focused_discussion")

            # ポジティブトレンドパターン
            positive_count = sentiments.count("positive")
            if positive_count / len(sentiments) > 0.6:
                patterns.append("positive_engagement")

            # 懸念対応パターン
            concerns = []
            for turn in context.context_history:
                concerns.extend(turn.get("concerns", []))
            if concerns:
                patterns.append("objection_handling")

            # 購買シグナルパターン
            signals = []
            for turn in context.context_history:
                signals.extend(turn.get("buying_signals", []))
            if signals:
                patterns.append("buying_signals_present")

            return patterns

        except Exception as e:
            logger.error(f"Pattern identification failed: {e}")
            return []

    async def _suggest_next_actions(self, context: SessionContext) -> List[str]:
        """次のベストアクションを提案"""
        try:
            actions = []

            # エンゲージメントベースの提案
            if context.engagement_trend and context.engagement_trend[-1] > 0.7:
                actions.append("提案を具体化する")
                actions.append("次のステップを明確にする")
            elif context.engagement_trend and context.engagement_trend[-1] < 0.4:
                actions.append("顧客のニーズを再確認する")
                actions.append("異なるアプローチを試す")

            # パターンベースの提案
            if "buying_signals_present" in context.identified_patterns:
                actions.append("クロージングを検討する")
            if "objection_handling" in context.identified_patterns:
                actions.append("懸念事項に対する具体的解決策を提示する")
            if "focused_discussion" in context.identified_patterns:
                actions.append("関連トピックに話題を広げる")

            # 営業モメンタムベースの提案
            if context.sales_momentum == "accelerating":
                actions.append("勢いを活かして提案を進める")
            elif context.sales_momentum == "declining":
                actions.append("新しい価値提案を検討する")

            return actions[:3]  # 上位3つに制限

        except Exception as e:
            logger.error(f"Next actions suggestion failed: {e}")
            return []

    async def _learn_anonymized_patterns(self, context_info: Dict[str, Any]) -> None:
        """匿名化されたパターンを学習"""
        try:
            if not self.privacy_config["pattern_learning"]:
                return

            # 完全に匿名化されたパターンのみ学習
            pattern_data = {
                "topic_flow": f"{context_info.get('topic_category', 'unknown')}",
                "sentiment_pattern": context_info.get("sentiment", "neutral"),
                "engagement_level": context_info.get("engagement_level", 0.5),
                "sales_stage": context_info.get("sales_stage", "unknown"),
                "has_buying_signals": len(context_info.get("buying_signals", [])) > 0,
                "has_concerns": len(context_info.get("concerns", [])) > 0,
            }

            # パターン学習ロジック（将来の実装で詳細化）
            logger.debug(f"Learning anonymized pattern: {pattern_data}")

        except Exception as e:
            logger.error(f"Pattern learning failed: {e}")

    async def _get_topic_continuity_suggestions(
        self, current_topic: str, user_input: str
    ) -> List[str]:
        """トピック継続性の提案"""
        try:
            suggestions = []

            topic_continuity_map = {
                "pricing": [
                    "価格体系についてさらに詳しく説明する",
                    "ROIの具体例を提示する",
                    "支払い条件について説明する",
                ],
                "features": [
                    "具体的な活用例を紹介する",
                    "競合との差別化ポイントを説明する",
                    "カスタマイズ可能性を説明する",
                ],
                "security": [
                    "セキュリティ認証について説明する",
                    "過去のセキュリティ実績を紹介する",
                    "セキュリティ監査プロセスを説明する",
                ],
            }

            return topic_continuity_map.get(current_topic, [])

        except Exception as e:
            logger.error(f"Topic continuity suggestions failed: {e}")
            return []

    async def _get_engagement_suggestions(
        self, engagement_trend: List[float]
    ) -> List[str]:
        """エンゲージメント向上の提案"""
        try:
            if not engagement_trend:
                return []

            current_engagement = engagement_trend[-1]

            if current_engagement > 0.7:
                return ["勢いを維持して詳細な提案に進む"]
            elif current_engagement < 0.4:
                return ["質問形式で顧客の関心を引き出す", "具体例やデモを提案する"]
            else:
                return ["顧客のニーズをより深く探る"]

        except Exception as e:
            logger.error(f"Engagement suggestions failed: {e}")
            return []

    async def _get_sales_stage_suggestions(
        self, sales_momentum: str, patterns: List[str]
    ) -> List[str]:
        """営業ステージ適応の提案"""
        try:
            suggestions = []

            momentum_suggestions = {
                "accelerating": ["積極的にクロージングに向けて進める"],
                "positive": ["提案の詳細化を進める"],
                "neutral": ["顧客のニーズを再確認する"],
                "challenging": ["アプローチを変更して関心を引き直す"],
                "declining": ["新しい価値提案を検討する"],
            }

            suggestions.extend(momentum_suggestions.get(sales_momentum, []))

            return suggestions

        except Exception as e:
            logger.error(f"Sales stage suggestions failed: {e}")
            return []

    async def _get_pattern_based_suggestions(self, patterns: List[str]) -> List[str]:
        """パターンベースの提案"""
        try:
            suggestions = []

            pattern_suggestions = {
                "positive_engagement": ["ポジティブな流れを活かして次のステップに進む"],
                "objection_handling": ["懸念を具体的に解決する提案をする"],
                "buying_signals_present": ["購買意欲を確認してクロージングを検討する"],
                "focused_discussion": ["関連する他の価値提案も紹介する"],
            }

            for pattern in patterns:
                suggestions.extend(pattern_suggestions.get(pattern, []))

            return suggestions

        except Exception as e:
            logger.error(f"Pattern-based suggestions failed: {e}")
            return []

    def _calculate_suggestion_confidence(self, context: SessionContext) -> float:
        """提案の信頼度を計算"""
        try:
            confidence = 0.5  # ベースライン

            # 履歴の長さによる調整
            if len(context.context_history) > 5:
                confidence += 0.2

            # エンゲージメント傾向による調整
            if context.engagement_trend:
                avg_engagement = sum(context.engagement_trend) / len(
                    context.engagement_trend
                )
                confidence += (avg_engagement - 0.5) * 0.3

            # パターン識別による調整
            if context.identified_patterns:
                confidence += len(context.identified_patterns) * 0.1

            return max(0.0, min(1.0, confidence))

        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.5

    async def _cleanup_session(self, session_id: str) -> None:
        """セッションをクリーンアップ"""
        try:
            if session_id in self.session_contexts:
                del self.session_contexts[session_id]
                logger.info(f"Cleaned up session context: {session_id}")

        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")

    async def _periodic_cleanup(self) -> None:
        """定期的なクリーンアップ"""
        try:
            while True:
                await asyncio.sleep(300)  # 5分ごと

                current_time = datetime.now()
                timeout_delta = timedelta(
                    minutes=self.privacy_config["session_timeout_minutes"]
                )

                sessions_to_cleanup = []
                for session_id, context in self.session_contexts.items():
                    if current_time - context.created_at > timeout_delta:
                        sessions_to_cleanup.append(session_id)

                for session_id in sessions_to_cleanup:
                    await self._cleanup_session(session_id)
                    logger.info(f"Auto-cleaned up expired session: {session_id}")

        except Exception as e:
            logger.error(f"Periodic cleanup failed: {e}")

    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """セッションサマリーを取得（個人情報なし）"""
        try:
            if session_id not in self.session_contexts:
                return {"success": False, "error": "Session not found"}

            context = self.session_contexts[session_id]

            return {
                "success": True,
                "session_id": session_id,
                "summary": {
                    "duration_minutes": (
                        datetime.now() - context.created_at
                    ).total_seconds()
                    / 60,
                    "total_turns": len(context.context_history),
                    "main_topics": list(
                        set(
                            [
                                turn.get("topic_category")
                                for turn in context.context_history
                                if turn.get("topic_category")
                            ]
                        )
                    ),
                    "current_topic": context.current_topic,
                    "sales_momentum": context.sales_momentum,
                    "average_engagement": (
                        sum(context.engagement_trend) / len(context.engagement_trend)
                        if context.engagement_trend
                        else 0.5
                    ),
                    "identified_patterns": context.identified_patterns,
                    "next_best_actions": context.next_best_actions,
                },
                "privacy_protected": True,
                "personal_info_stored": False,
            }

        except Exception as e:
            logger.error(f"Session summary failed: {e}")
            return {"success": False, "error": str(e)}

    def get_service_info(self) -> Dict[str, Any]:
        """サービス情報を取得"""
        return {
            "service_name": "Privacy-Aware Context Service",
            "privacy_mode": self.privacy_mode.value,
            "privacy_config": self.privacy_config,
            "active_sessions": len(self.session_contexts),
            "learned_patterns": len(self.context_patterns),
            "features": {
                "personal_info_protection": True,
                "audio_storage": False,
                "content_anonymization": True,
                "pattern_learning": self.privacy_config["pattern_learning"],
                "cross_session_context": self.privacy_config["cross_session_context"],
                "auto_cleanup": True,
            },
        }


# グローバルサービスインスタンス
_privacy_aware_context_service: Optional[PrivacyAwareContextService] = None


def get_privacy_aware_context_service(
    privacy_mode: PrivacyMode = PrivacyMode.STRICT,
) -> PrivacyAwareContextService:
    """Privacy-Aware Context Service のインスタンスを取得"""
    global _privacy_aware_context_service
    if _privacy_aware_context_service is None:
        _privacy_aware_context_service = PrivacyAwareContextService(privacy_mode)
    return _privacy_aware_context_service
