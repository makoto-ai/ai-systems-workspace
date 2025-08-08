"""
親しみやすさ分析サービス
営業における適度な距離感と親しみやすさを評価
"""

from typing import Dict, Any, List, Optional, Tuple
import re
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FriendlinessLevel(Enum):
    """親しみやすさレベル"""

    TOO_DISTANT = "too_distant"  # 距離が遠すぎる
    FORMAL_DISTANT = "formal_distant"  # 丁寧だが距離感がある
    BALANCED = "balanced"  # バランスが良い
    FRIENDLY = "friendly"  # 親しみやすい
    TOO_CASUAL = "too_casual"  # カジュアルすぎる


class DistanceIssueType(Enum):
    """距離感の問題タイプ"""

    EXCESSIVE_FORMALITY = "excessive_formality"  # 過度に堅い
    LACK_OF_WARMTH = "lack_of_warmth"  # 温かみ不足
    MISSING_EMPATHY = "missing_empathy"  # 共感表現不足
    OVERLY_BUSINESS = "overly_business"  # ビジネス的すぎる
    DISTANCE_CREATING = "distance_creating"  # 距離を作る表現
    INSUFFICIENT_RAPPORT = "insufficient_rapport"  # 信頼関係構築不足


@dataclass
class FriendlinessIssue:
    """親しみやすさの問題"""

    issue_type: DistanceIssueType
    severity: float
    description: str
    suggestion: str
    examples: List[str]


@dataclass
class FriendlinessAnalysis:
    """親しみやすさ分析結果"""

    level: FriendlinessLevel
    score: float
    balance_score: float
    warmth_indicators: List[str]
    distance_indicators: List[str]
    issues: List[FriendlinessIssue]
    recommendations: List[str]


class FriendlinessAnalyzer:
    """親しみやすさ分析器"""

    def __init__(self):
        self.initialize_patterns()

    def initialize_patterns(self):
        """パターンの初期化"""

        # 親しみやすさを高める表現
        self.warmth_expressions = {
            "empathy": {
                "patterns": [
                    "お気持ちお察しします",
                    "よくわかります",
                    "そうですよね",
                    "なるほど",
                    "確かに",
                    "おっしゃる通り",
                    "同感です",
                ],
                "weight": 0.3,
            },
            "understanding": {
                "patterns": [
                    "ご心配",
                    "ご不安",
                    "お困り",
                    "大変ですね",
                    "お忙しい",
                    "ご苦労",
                    "お疲れ様",
                ],
                "weight": 0.25,
            },
            "positive_emotion": {
                "patterns": [
                    "嬉しい",
                    "楽しみ",
                    "安心",
                    "喜んで",
                    "ワクワク",
                    "期待",
                    "頼もしい",
                ],
                "weight": 0.2,
            },
            "personal_touch": {
                "patterns": [
                    "私も",
                    "実は",
                    "正直に",
                    "個人的に",
                    "経験上",
                    "率直に",
                    "本音で",
                ],
                "weight": 0.15,
            },
            "collaborative": {
                "patterns": [
                    "一緒に",
                    "協力して",
                    "お手伝い",
                    "サポート",
                    "共に",
                    "チームで",
                    "パートナー",
                ],
                "weight": 0.1,
            },
        }

        # 距離を作る表現
        self.distance_expressions = {
            "overly_formal": {
                "patterns": [
                    "恐縮至極",
                    "謹んで",
                    "畏敬の念",
                    "恭謹",
                    "拝察",
                    "謹言",
                    "恐懼",
                    "畏怖",
                ],
                "severity": 0.9,
                "description": "過度に堅い敬語で距離感を作っています",
            },
            "bureaucratic": {
                "patterns": [
                    "規定により",
                    "手続き上",
                    "システム上",
                    "制度上",
                    "方針として",
                    "原則として",
                    "基本的に",
                ],
                "severity": 0.7,
                "description": "お役所的な表現で親しみにくい印象です",
            },
            "rejection_heavy": {
                "patterns": [
                    "承りかねます",
                    "致しかねます",
                    "お受けできません",
                    "対応いたしかねます",
                    "難しいところです",
                ],
                "severity": 0.8,
                "description": "拒否的な表現が多く冷たい印象です",
            },
            "impersonal": {
                "patterns": [
                    "弊社では",
                    "当社の方針",
                    "システム的に",
                    "一般的には",
                    "通常",
                    "標準的",
                ],
                "severity": 0.6,
                "description": "個人的な温かみが不足しています",
            },
        }

        # 共感・理解を示す表現
        self.empathy_expressions = {
            "acknowledgment": [
                "おっしゃる通り",
                "確かに",
                "そうですね",
                "なるほど",
                "同感です",
                "よくわかります",
                "理解できます",
            ],
            "validation": [
                "お気持ちお察しします",
                "ご心配ですね",
                "大変ですね",
                "お困りでしょう",
                "ご苦労されて",
                "お忙しい中",
            ],
            "support": [
                "お手伝いします",
                "サポートします",
                "一緒に考えましょう",
                "お任せください",
                "安心してください",
                "大丈夫です",
            ],
        }

        # 自然な表現（堅すぎない）
        self.natural_expressions = {
            "casual_polite": [
                "そうですね",
                "なるほど",
                "実は",
                "ちなみに",
                "例えば",
                "要するに",
                "つまり",
                "簡単に言うと",
            ],
            "conversational": [
                "お話しましょう",
                "相談しましょう",
                "話し合いましょう",
                "聞かせてください",
                "教えてください",
                "一緒に",
            ],
            "approachable": [
                "気軽に",
                "遠慮なく",
                "お気軽に",
                "いつでも",
                "何でも",
                "どんなことでも",
                "お声がけください",
            ],
        }

        # 感情表現
        self.emotional_expressions = {
            "positive": [
                "嬉しい",
                "楽しみ",
                "喜んで",
                "ワクワク",
                "期待",
                "安心",
                "頼もしい",
                "心強い",
                "素晴らしい",
            ],
            "concern": ["心配", "不安", "気になる", "気がかり", "懸念"],
            "enthusiasm": ["ぜひ", "きっと", "必ず", "絶対", "間違いなく"],
        }

    def analyze_friendliness(
        self, text: str, context: str = "sales", customer_relationship: str = "new"
    ) -> FriendlinessAnalysis:
        """
        親しみやすさの総合分析

        Args:
            text: 分析対象テキスト
            context: 文脈（sales, meeting, negotiation）
            customer_relationship: 顧客との関係性（new, existing, long_term）
        """

        # 1. 温かみ指標の分析
        warmth_score, warmth_indicators = self._analyze_warmth(text)

        # 2. 距離感指標の分析
        distance_score, distance_indicators = self._analyze_distance(text)

        # 3. 共感・理解表現の分析
        empathy_score, empathy_indicators = self._analyze_empathy(text)

        # 4. 自然さの分析
        naturalness_score, naturalness_indicators = self._analyze_naturalness(text)

        # 5. 感情表現の分析
        emotion_score, emotion_indicators = self._analyze_emotional_expression(text)

        # 6. 問題の検出
        issues = self._detect_friendliness_issues(text, context, customer_relationship)

        # 7. 総合スコア計算
        overall_score = self._calculate_friendliness_score(
            warmth_score,
            distance_score,
            empathy_score,
            naturalness_score,
            emotion_score,
        )

        # 8. バランススコア計算
        balance_score = self._calculate_balance_score(
            warmth_score, distance_score, empathy_score, naturalness_score
        )

        # 9. レベル判定
        level = self._determine_friendliness_level(overall_score, balance_score, issues)

        # 10. 推奨事項生成
        recommendations = self._generate_recommendations(
            level, issues, warmth_score, empathy_score, context, customer_relationship
        )

        return FriendlinessAnalysis(
            level=level,
            score=overall_score,
            balance_score=balance_score,
            warmth_indicators=warmth_indicators
            + empathy_indicators
            + emotion_indicators,
            distance_indicators=distance_indicators,
            issues=issues,
            recommendations=recommendations,
        )

    def _analyze_warmth(self, text: str) -> Tuple[float, List[str]]:
        """温かみの分析"""
        warmth_score = 0.0
        found_indicators = []

        for category, data in self.warmth_expressions.items():
            category_score = 0.0
            category_indicators = []

            for pattern in data["patterns"]:
                if pattern in text:
                    category_score += 1
                    category_indicators.append(pattern)

            # カテゴリ別重み付け（発見された項目数に応じてスコアを上げる）
            if category_score > 0:
                # 発見された項目があれば、その比率に基づいてスコアを計算
                pattern_ratio = min(1.0, category_score / len(data["patterns"]))
                # 実際に発見された項目数も考慮（1つでも発見されれば基本スコアを与える）
                base_category_score = 0.5 + (pattern_ratio * 0.5)  # 0.5-1.0の範囲
                weighted_score = base_category_score * data["weight"]
                warmth_score += weighted_score
            found_indicators.extend(category_indicators)

        return min(1.0, warmth_score), found_indicators

    def _analyze_distance(self, text: str) -> Tuple[float, List[str]]:
        """距離感の分析（低いほど良い）"""
        distance_score = 0.0
        found_indicators = []

        for category, data in self.distance_expressions.items():
            for pattern in data["patterns"]:
                if pattern in text:
                    distance_score += data["severity"] * 0.1  # 重み調整
                    found_indicators.append(pattern)

        return min(1.0, distance_score), found_indicators

    def _analyze_empathy(self, text: str) -> Tuple[float, List[str]]:
        """共感・理解表現の分析"""
        empathy_score = 0.0
        found_indicators = []

        total_patterns = sum(
            len(patterns) for patterns in self.empathy_expressions.values()
        )
        found_patterns = 0

        for category, patterns in self.empathy_expressions.items():
            for pattern in patterns:
                if pattern in text:
                    found_patterns += 1
                    found_indicators.append(pattern)

        empathy_score = found_patterns / total_patterns if total_patterns > 0 else 0.0
        return min(1.0, empathy_score), found_indicators

    def _analyze_naturalness(self, text: str) -> Tuple[float, List[str]]:
        """自然さの分析"""
        naturalness_score = 0.0
        found_indicators = []

        total_patterns = sum(
            len(patterns) for patterns in self.natural_expressions.values()
        )
        found_patterns = 0

        for category, patterns in self.natural_expressions.items():
            for pattern in patterns:
                if pattern in text:
                    found_patterns += 1
                    found_indicators.append(pattern)

        naturalness_score = (
            found_patterns / total_patterns if total_patterns > 0 else 0.0
        )
        return min(1.0, naturalness_score), found_indicators

    def _analyze_emotional_expression(self, text: str) -> Tuple[float, List[str]]:
        """感情表現の分析"""
        emotion_score = 0.0
        found_indicators = []

        total_patterns = sum(
            len(patterns) for patterns in self.emotional_expressions.values()
        )
        found_patterns = 0

        for category, patterns in self.emotional_expressions.items():
            for pattern in patterns:
                if pattern in text:
                    found_patterns += 1
                    found_indicators.append(pattern)

        emotion_score = found_patterns / total_patterns if total_patterns > 0 else 0.0
        return min(1.0, emotion_score), found_indicators

    def _detect_friendliness_issues(
        self, text: str, context: str, customer_relationship: str
    ) -> List[FriendlinessIssue]:
        """親しみやすさの問題を検出"""
        issues = []

        # 1. 過度に堅い表現の検出
        for category, data in self.distance_expressions.items():
            found_patterns = [p for p in data["patterns"] if p in text]
            if found_patterns:
                issues.append(
                    FriendlinessIssue(
                        issue_type=DistanceIssueType.EXCESSIVE_FORMALITY,
                        severity=data["severity"],
                        description=data["description"],
                        suggestion=self._get_friendliness_suggestion(category),
                        examples=found_patterns,
                    )
                )

        # 2. 温かみ不足の検出（閾値を下げて現実的に）
        warmth_score, _ = self._analyze_warmth(text)
        if warmth_score < 0.15:  # 0.3から0.15に下げる
            issues.append(
                FriendlinessIssue(
                    issue_type=DistanceIssueType.LACK_OF_WARMTH,
                    severity=0.6,  # 0.7から0.6に下げる
                    description="温かみのある表現が不足しています",
                    suggestion="相手を気遣う表現や共感を示す言葉を追加してください",
                    examples=["お気持ちお察しします", "そうですね", "なるほど"],
                )
            )

        # 3. 共感表現不足の検出（閾値を下げて現実的に）
        empathy_score, _ = self._analyze_empathy(text)
        if empathy_score < 0.1:  # 0.2から0.1に下げる
            issues.append(
                FriendlinessIssue(
                    issue_type=DistanceIssueType.MISSING_EMPATHY,
                    severity=0.7,  # 0.8から0.7に下げる
                    description="相手への共感や理解を示す表現が不足しています",
                    suggestion="相手の立場に立った表現を心がけてください",
                    examples=["よくわかります", "おっしゃる通り", "大変ですね"],
                )
            )

        # 4. 関係性に応じた問題検出
        if customer_relationship == "long_term":
            # 長期顧客には親しみやすさが重要（閾値を下げて現実的に）
            if warmth_score < 0.3:  # 0.5から0.3に下げる
                issues.append(
                    FriendlinessIssue(
                        issue_type=DistanceIssueType.INSUFFICIENT_RAPPORT,
                        severity=0.5,  # 0.6から0.5に下げる
                        description="長期のお客様にはより親しみやすい表現が効果的です",
                        suggestion="信頼関係を活かした温かみのある表現を使用してください",
                        examples=["いつもありがとうございます", "お久しぶりです"],
                    )
                )

        return sorted(issues, key=lambda x: x.severity, reverse=True)

    def _calculate_friendliness_score(
        self,
        warmth: float,
        distance: float,
        empathy: float,
        naturalness: float,
        emotion: float,
    ) -> float:
        """親しみやすさの総合スコア計算"""

        # 重み付け（調整済み）
        weights = {
            "warmth": 0.35,
            "empathy": 0.30,
            "naturalness": 0.20,
            "emotion": 0.15,
            "distance_penalty": 0.5,  # 距離感のペナルティを強化
        }

        # 距離感は減点要素（より強い影響）
        distance_penalty = distance * weights["distance_penalty"]

        # 基本スコア計算
        positive_score = (
            warmth * weights["warmth"]
            + empathy * weights["empathy"]
            + naturalness * weights["naturalness"]
            + emotion * weights["emotion"]
        )

        # 最低スコア保証（完全に0になることを防ぐ）
        base_score = max(0.1, positive_score)

        # 距離感による減点を適用
        final_score = max(0.0, base_score - distance_penalty)

        # スコアを0-1の範囲に正規化（さらに甘めに調整）
        adjusted_score = min(1.0, final_score * 2.5)  # 2.5倍で調整

        return adjusted_score

    def _calculate_balance_score(
        self, warmth: float, distance: float, empathy: float, naturalness: float
    ) -> float:
        """バランススコアの計算"""

        # 理想的なバランス（より現実的な値に調整）
        target_warmth = 0.4  # 温かみの目標値を下げる
        target_empathy = 0.3  # 共感の目標値を下げる
        target_naturalness = 0.2  # 自然さの目標値を下げる
        target_distance = 0.1  # 距離感の目標値を下げる

        # 各要素の理想値からの差（正規化）
        warmth_diff = abs(warmth - target_warmth) / max(target_warmth, 1.0)
        empathy_diff = abs(empathy - target_empathy) / max(target_empathy, 1.0)
        naturalness_diff = abs(naturalness - target_naturalness) / max(
            target_naturalness, 1.0
        )
        distance_diff = (
            abs(distance - target_distance) / max(target_distance, 1.0)
            if target_distance > 0
            else distance
        )

        # 重み付き平均差
        weighted_diff = (
            warmth_diff * 0.3
            + empathy_diff * 0.3
            + naturalness_diff * 0.2
            + distance_diff * 0.2
        )

        # バランススコア（差が小さいほど高い、0.0-1.0の範囲）
        balance_score = max(0.0, 1.0 - weighted_diff)

        return balance_score

    def _determine_friendliness_level(
        self, score: float, balance: float, issues: List[FriendlinessIssue]
    ) -> FriendlinessLevel:
        """親しみやすさレベルの判定"""

        high_severity_issues = [i for i in issues if i.severity >= 0.8]
        medium_severity_issues = [i for i in issues if i.severity >= 0.6]

        # 高い重要度の問題が複数ある場合
        if len(high_severity_issues) >= 2:
            return FriendlinessLevel.TOO_DISTANT

        # スコアベースの判定（さらに現実的に調整）
        if score >= 0.7 and balance >= 0.4:
            return FriendlinessLevel.FRIENDLY
        elif score >= 0.5 and balance >= 0.3:
            return FriendlinessLevel.BALANCED
        elif score >= 0.3 and len(high_severity_issues) == 0:
            return FriendlinessLevel.FORMAL_DISTANT
        else:
            return FriendlinessLevel.TOO_DISTANT

    def _generate_recommendations(
        self,
        level: FriendlinessLevel,
        issues: List[FriendlinessIssue],
        warmth_score: float,
        empathy_score: float,
        context: str,
        customer_relationship: str,
    ) -> List[str]:
        """推奨事項の生成"""

        recommendations = []

        # レベル別の基本推奨事項
        if level == FriendlinessLevel.TOO_DISTANT:
            recommendations.extend(
                [
                    "相手との距離を縮める表現を積極的に使用してください",
                    "共感や理解を示す言葉を追加してください",
                    "過度に堅い表現を見直してください",
                ]
            )
        elif level == FriendlinessLevel.FORMAL_DISTANT:
            recommendations.extend(
                [
                    "適度な親しみやすさを加えてください",
                    "自然な会話表現を取り入れてください",
                ]
            )
        elif level == FriendlinessLevel.BALANCED:
            recommendations.extend(
                [
                    "現在のバランスを保ちながら、さらに相手に寄り添う表現を心がけてください"
                ]
            )

        # 問題別の推奨事項
        for issue in issues:
            if issue.issue_type == DistanceIssueType.LACK_OF_WARMTH:
                recommendations.append("温かみのある表現を増やしてください")
            elif issue.issue_type == DistanceIssueType.MISSING_EMPATHY:
                recommendations.append("相手の気持ちに寄り添う表現を使用してください")
            elif issue.issue_type == DistanceIssueType.EXCESSIVE_FORMALITY:
                recommendations.append(
                    "丁寧さを保ちながら、より親しみやすい表現を使用してください"
                )

        # 関係性別の推奨事項
        if customer_relationship == "new":
            recommendations.append(
                "初回のお客様には親しみやすさと信頼性のバランスを心がけてください"
            )
        elif customer_relationship == "long_term":
            recommendations.append(
                "長期のお客様には信頼関係を活かした温かみのある表現を使用してください"
            )

        return recommendations

    def _get_friendliness_suggestion(self, category: str) -> str:
        """カテゴリ別の改善提案"""
        suggestions = {
            "overly_formal": "より自然で親しみやすい丁寧語を使用してください",
            "bureaucratic": "お役所的な表現を避け、個人的な温かみを加えてください",
            "rejection_heavy": "断りの表現をより柔らかく、代案を提示してください",
            "impersonal": "個人的な関心や気遣いを表現してください",
        }
        return suggestions.get(category, "より親しみやすい表現を心がけてください")

    def get_friendliness_tips(self, level: FriendlinessLevel) -> Dict[str, List[str]]:
        """親しみやすさ向上のヒント"""

        tips = {
            FriendlinessLevel.TOO_DISTANT: {
                "immediate": [
                    "「そうですね」「なるほど」で相槌を打つ",
                    "「お気持ちお察しします」で共感を示す",
                    "「一緒に考えましょう」で協力姿勢を示す",
                ],
                "practice": [
                    "相手の立場に立った表現を練習する",
                    "自然な会話表現を身につける",
                    "感情表現を適度に取り入れる",
                ],
            },
            FriendlinessLevel.FORMAL_DISTANT: {
                "immediate": [
                    "「実は」「正直に」などの自然な表現を使う",
                    "「嬉しいです」「楽しみです」などの感情を表現する",
                    "「お気軽に」「遠慮なく」で親しみやすさを演出する",
                ],
                "practice": [
                    "丁寧語と親しみやすさのバランスを練習する",
                    "相手との距離感を意識した表現を身につける",
                ],
            },
            FriendlinessLevel.BALANCED: {
                "immediate": ["現在のバランスを維持する", "相手に応じて表現を調整する"],
                "practice": [
                    "より高度な共感表現を身につける",
                    "場面に応じた表現の使い分けを練習する",
                ],
            },
        }

        return tips.get(level, {"immediate": [], "practice": []})


# サービスインスタンス
friendliness_analyzer = FriendlinessAnalyzer()
