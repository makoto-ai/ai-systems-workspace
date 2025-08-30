#!/usr/bin/env python3
"""
🤖 Phase 4: 学習データ統合知能化エンジン
===================================

全Phaseのデータを統合AI分析し、パターン認識・トレンド予測を行い、
継続学習による自己進化システムを提供するインテリジェンス・エンジン

主要機能:
- 全フェーズデータ統合分析
- AIパターン認識エンジン
- 予測・トレンド分析
- 継続学習システム
- 自己進化アルゴリズム
"""

import os
import sys
import json
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import statistics
import re
import pickle
from collections import defaultdict, Counter


@dataclass
class LearningPattern:
    """学習パターンデータクラス"""
    pattern_id: str
    pattern_type: str  # "improvement", "regression", "cyclical", "anomaly"
    confidence_score: float
    frequency: int
    impact_score: float
    conditions: Dict[str, Any]
    outcomes: Dict[str, Any]
    discovered_at: datetime
    last_seen: datetime


@dataclass  
class IntelligenceInsight:
    """知能分析洞察データクラス"""
    insight_id: str
    insight_type: str  # "prediction", "recommendation", "warning", "opportunity"
    title: str
    description: str
    evidence: List[str]
    confidence: float
    actionable_items: List[str]
    expected_impact: float
    time_sensitivity: str  # "immediate", "short_term", "medium_term", "long_term"
    generated_at: datetime


class DataUnificationEngine:
    """データ統合エンジン"""
    
    def __init__(self):
        self.data_sources = {
            "phase1": [
                "out/learning_insights.json",
                "out/system_health.json"
            ],
            "phase2": [
                "out/issue_predictions.json", 
                "out/preventive_fixes.json"
            ],
            "phase3": [
                "out/realtime_quality.json",
                "out/feedback_history.json",
                "out/gate_learning.json",
                "out/auto_guard_learning.json"
            ],
            "phase4": [
                "out/intelligent_optimization.json",
                "out/adaptive_guidance.json",
                "out/project_optimization.json"
            ]
        }
        
        self.unified_schema = {
            "timestamp": "datetime",
            "source_phase": "string",
            "data_type": "string",
            "quality_metrics": "dict",
            "improvement_actions": "list",
            "success_indicators": "dict",
            "failure_patterns": "list",
            "context_metadata": "dict"
        }
    
    def unify_all_data(self) -> Dict[str, Any]:
        """全データ統合"""
        print("🤖 全フェーズデータ統合開始...")
        
        unified_data = {
            "metadata": {
                "unification_timestamp": datetime.now().isoformat(),
                "total_sources": 0,
                "successful_loads": 0,
                "data_quality_score": 0.0
            },
            "phase1_data": [],
            "phase2_data": [],
            "phase3_data": [],
            "phase4_data": [],
            "time_series": [],
            "quality_metrics_timeline": [],
            "improvement_actions_history": [],
            "pattern_indicators": {}
        }
        
        # 各フェーズのデータを統合
        for phase, sources in self.data_sources.items():
            phase_data = []
            for source in sources:
                data = self._load_and_normalize_data(source, phase)
                if data:
                    phase_data.extend(data if isinstance(data, list) else [data])
                    unified_data["metadata"]["successful_loads"] += 1
                unified_data["metadata"]["total_sources"] += 1
            
            unified_data[f"{phase}_data"] = phase_data
        
        # 時系列データ構築
        unified_data["time_series"] = self._build_time_series(unified_data)
        unified_data["quality_metrics_timeline"] = self._extract_quality_timeline(unified_data)
        unified_data["improvement_actions_history"] = self._extract_actions_history(unified_data)
        
        # データ品質評価
        unified_data["metadata"]["data_quality_score"] = self._assess_data_quality(unified_data)
        
        print(f"✅ データ統合完了: {unified_data['metadata']['successful_loads']}/{unified_data['metadata']['total_sources']} ソース成功")
        return unified_data
    
    def _load_and_normalize_data(self, source_path: str, phase: str) -> Optional[List[Dict]]:
        """データ読み込み・正規化"""
        try:
            if not os.path.exists(source_path):
                return None
            
            # ファイル形式に応じた読み込み
            if source_path.endswith('.json'):
                with open(source_path) as f:
                    data = json.load(f)
            elif source_path.endswith('.jsonl'):
                data = []
                with open(source_path) as f:
                    for line in f:
                        if line.strip():
                            data.append(json.loads(line))
            else:
                return None
            
            # データ正規化
            normalized = self._normalize_to_schema(data, phase, source_path)
            return normalized
            
        except Exception as e:
            print(f"データ読み込みエラー {source_path}: {e}")
            return None
    
    def _normalize_to_schema(self, data: Any, phase: str, source_path: str) -> List[Dict]:
        """スキーマ正規化"""
        normalized = []
        
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            return []
        
        for item in data:
            if not isinstance(item, dict):
                continue
                
            normalized_item = {
                "timestamp": self._extract_timestamp(item),
                "source_phase": phase,
                "data_type": Path(source_path).stem,
                "quality_metrics": self._extract_quality_metrics(item),
                "improvement_actions": self._extract_improvement_actions(item),
                "success_indicators": self._extract_success_indicators(item),
                "failure_patterns": self._extract_failure_patterns(item),
                "context_metadata": self._extract_context_metadata(item),
                "raw_data": item  # 元データも保持
            }
            
            normalized.append(normalized_item)
        
        return normalized
    
    def _extract_timestamp(self, item: Dict) -> str:
        """タイムスタンプ抽出"""
        timestamp_fields = ["timestamp", "created_at", "last_updated", "analysis_timestamp"]
        
        for field in timestamp_fields:
            if field in item and item[field]:
                return str(item[field])
        
        return datetime.now().isoformat()
    
    def _extract_quality_metrics(self, item: Dict) -> Dict[str, float]:
        """品質メトリクス抽出"""
        metrics = {}
        
        # 様々なメトリクス形式に対応
        if "score" in item:
            metrics["overall_score"] = float(item["score"])
        if "quality_score" in item:
            metrics["quality_score"] = float(item["quality_score"])
        if "pass_rate" in item:
            metrics["pass_rate"] = float(item["pass_rate"])
        if "improvement" in item:
            metrics["improvement"] = float(item["improvement"])
        
        return metrics
    
    def _extract_improvement_actions(self, item: Dict) -> List[str]:
        """改善アクション抽出"""
        actions = []
        
        action_fields = ["actions", "recommendations", "fixes", "steps", "action"]
        for field in action_fields:
            if field in item and item[field]:
                if isinstance(item[field], list):
                    actions.extend(item[field])
                elif isinstance(item[field], str):
                    actions.append(item[field])
        
        return actions
    
    def _extract_success_indicators(self, item: Dict) -> Dict[str, Any]:
        """成功指標抽出"""
        indicators = {}
        
        if "success" in item:
            indicators["success"] = item["success"]
        if "status" in item:
            indicators["status"] = item["status"]
        if "final_state" in item:
            indicators["final_state"] = item["final_state"]
        
        return indicators
    
    def _extract_failure_patterns(self, item: Dict) -> List[str]:
        """失敗パターン抽出"""
        patterns = []
        
        if "errors" in item and isinstance(item["errors"], list):
            patterns.extend(item["errors"])
        if "issues" in item and isinstance(item["issues"], list):
            patterns.extend(item["issues"])
        if "severity" in item and item["severity"] in ["error", "critical"]:
            patterns.append(f"severity_{item['severity']}")
        
        return patterns
    
    def _extract_context_metadata(self, item: Dict) -> Dict[str, Any]:
        """コンテキストメタデータ抽出"""
        metadata = {}
        
        context_fields = ["file", "project_id", "developer_id", "project_type", "environment"]
        for field in context_fields:
            if field in item:
                metadata[field] = item[field]
        
        return metadata
    
    def _build_time_series(self, unified_data: Dict) -> List[Dict]:
        """時系列データ構築"""
        time_series = []
        
        for phase in ["phase1", "phase2", "phase3", "phase4"]:
            phase_data = unified_data.get(f"{phase}_data", [])
            
            for item in phase_data:
                time_point = {
                    "timestamp": item["timestamp"],
                    "phase": item["source_phase"],
                    "data_type": item["data_type"],
                    "metrics": item["quality_metrics"]
                }
                time_series.append(time_point)
        
        # タイムスタンプでソート
        time_series.sort(key=lambda x: x["timestamp"])
        return time_series
    
    def _extract_quality_timeline(self, unified_data: Dict) -> List[Dict]:
        """品質メトリクス時系列抽出"""
        timeline = []
        
        for item in unified_data["time_series"]:
            if item["metrics"]:
                timeline_point = {
                    "timestamp": item["timestamp"],
                    "phase": item["phase"],
                    "overall_score": item["metrics"].get("overall_score", 0),
                    "quality_score": item["metrics"].get("quality_score", 0)
                }
                timeline.append(timeline_point)
        
        return timeline
    
    def _extract_actions_history(self, unified_data: Dict) -> List[Dict]:
        """改善アクション履歴抽出"""
        history = []
        
        for phase in ["phase1", "phase2", "phase3", "phase4"]:
            phase_data = unified_data.get(f"{phase}_data", [])
            
            for item in phase_data:
                if item["improvement_actions"]:
                    history_item = {
                        "timestamp": item["timestamp"],
                        "phase": item["source_phase"],
                        "actions": item["improvement_actions"],
                        "success_indicators": item["success_indicators"]
                    }
                    history.append(history_item)
        
        return history
    
    def _assess_data_quality(self, unified_data: Dict) -> float:
        """データ品質評価"""
        total_items = 0
        quality_score = 0
        
        for phase in ["phase1", "phase2", "phase3", "phase4"]:
            phase_data = unified_data.get(f"{phase}_data", [])
            
            for item in phase_data:
                total_items += 1
                item_quality = 0
                
                # タイムスタンプの存在
                if item["timestamp"]:
                    item_quality += 0.2
                
                # メトリクスの存在
                if item["quality_metrics"]:
                    item_quality += 0.3
                
                # アクションの存在
                if item["improvement_actions"]:
                    item_quality += 0.2
                
                # 成功指標の存在
                if item["success_indicators"]:
                    item_quality += 0.15
                
                # コンテキストメタデータの存在
                if item["context_metadata"]:
                    item_quality += 0.15
                
                quality_score += item_quality
        
        return quality_score / max(1, total_items)


class PatternRecognitionEngine:
    """パターン認識エンジン"""
    
    def __init__(self):
        self.known_patterns = self._load_known_patterns()
        self.pattern_threshold = 0.7
    
    def _load_known_patterns(self) -> Dict[str, Any]:
        """既知パターン読み込み"""
        return {
            "improvement_patterns": [
                {"name": "gradual_improvement", "indicators": ["increasing_scores", "consistent_actions"]},
                {"name": "breakthrough", "indicators": ["sudden_jump", "new_methodology"]},
                {"name": "plateau", "indicators": ["stable_scores", "no_major_changes"]}
            ],
            "failure_patterns": [
                {"name": "recurring_failure", "indicators": ["repeated_errors", "same_root_cause"]},
                {"name": "cascading_failure", "indicators": ["multiple_failures", "dependency_issues"]},
                {"name": "degradation", "indicators": ["declining_scores", "increasing_complexity"]}
            ],
            "cyclical_patterns": [
                {"name": "weekly_cycle", "period": 7, "indicators": ["day_of_week_variance"]},
                {"name": "deployment_cycle", "period": 14, "indicators": ["release_related_changes"]}
            ]
        }
    
    def recognize_patterns(self, unified_data: Dict) -> List[LearningPattern]:
        """パターン認識実行"""
        print("🔍 AIパターン認識開始...")
        
        patterns = []
        
        # 改善パターン認識
        improvement_patterns = self._recognize_improvement_patterns(unified_data)
        patterns.extend(improvement_patterns)
        
        # 失敗パターン認識
        failure_patterns = self._recognize_failure_patterns(unified_data)
        patterns.extend(failure_patterns)
        
        # 周期パターン認識
        cyclical_patterns = self._recognize_cyclical_patterns(unified_data)
        patterns.extend(cyclical_patterns)
        
        # 異常パターン認識
        anomaly_patterns = self._recognize_anomaly_patterns(unified_data)
        patterns.extend(anomaly_patterns)
        
        print(f"✅ パターン認識完了: {len(patterns)}個のパターンを発見")
        return patterns
    
    def _recognize_improvement_patterns(self, unified_data: Dict) -> List[LearningPattern]:
        """改善パターン認識"""
        patterns = []
        
        timeline = unified_data["quality_metrics_timeline"]
        if len(timeline) < 3:
            return patterns
        
        # トレンド分析
        scores = [item.get("overall_score", 0) for item in timeline[-10:]]  # 直近10件
        
        if len(scores) >= 3:
            # 改善トレンド検出
            if self._is_improving_trend(scores):
                pattern = LearningPattern(
                    pattern_id="improvement_trend_1",
                    pattern_type="improvement",
                    confidence_score=0.8,
                    frequency=len([s for s in scores if s > 0]),
                    impact_score=max(scores) - min(scores),
                    conditions={"trend": "improving", "data_points": len(scores)},
                    outcomes={"score_improvement": max(scores) - scores[0]},
                    discovered_at=datetime.now(),
                    last_seen=datetime.now()
                )
                patterns.append(pattern)
        
        return patterns
    
    def _recognize_failure_patterns(self, unified_data: Dict) -> List[LearningPattern]:
        """失敗パターン認識"""
        patterns = []
        
        # 失敗履歴分析
        failure_count = 0
        recurring_issues = []
        
        for phase in ["phase1", "phase2", "phase3", "phase4"]:
            phase_data = unified_data.get(f"{phase}_data", [])
            
            for item in phase_data:
                failure_patterns = item.get("failure_patterns", [])
                if failure_patterns:
                    failure_count += 1
                    recurring_issues.extend(failure_patterns)
        
        # 繰り返し失敗パターン
        if failure_count >= 3:
            common_issues = [issue for issue, count in Counter(recurring_issues).most_common(3)]
            
            pattern = LearningPattern(
                pattern_id="recurring_failure_1",
                pattern_type="regression",
                confidence_score=0.7,
                frequency=failure_count,
                impact_score=failure_count / 10.0,
                conditions={"failure_count": failure_count, "common_issues": common_issues},
                outcomes={"identified_patterns": common_issues},
                discovered_at=datetime.now(),
                last_seen=datetime.now()
            )
            patterns.append(pattern)
        
        return patterns
    
    def _recognize_cyclical_patterns(self, unified_data: Dict) -> List[LearningPattern]:
        """周期パターン認識"""
        patterns = []
        
        timeline = unified_data["quality_metrics_timeline"]
        if len(timeline) < 14:  # 最低2週間のデータが必要
            return patterns
        
        # 簡易的な周期性検出
        scores = [item.get("overall_score", 0) for item in timeline]
        
        # 週次パターン（7日周期）の検出
        if self._detect_weekly_pattern(scores):
            pattern = LearningPattern(
                pattern_id="weekly_cycle_1",
                pattern_type="cyclical",
                confidence_score=0.6,
                frequency=7,
                impact_score=0.3,
                conditions={"period": 7, "pattern_type": "weekly"},
                outcomes={"detected_cycle": "weekly"},
                discovered_at=datetime.now(),
                last_seen=datetime.now()
            )
            patterns.append(pattern)
        
        return patterns
    
    def _recognize_anomaly_patterns(self, unified_data: Dict) -> List[LearningPattern]:
        """異常パターン認識"""
        patterns = []
        
        timeline = unified_data["quality_metrics_timeline"]
        if len(timeline) < 5:
            return patterns
        
        scores = [item.get("overall_score", 0) for item in timeline[-20:]]  # 直近20件
        
        if scores:
            mean_score = statistics.mean(scores)
            std_dev = statistics.stdev(scores) if len(scores) > 1 else 0
            
            # 異常値検出（標準偏差の2倍以上）
            anomalies = [s for s in scores if abs(s - mean_score) > 2 * std_dev]
            
            if anomalies:
                pattern = LearningPattern(
                    pattern_id="anomaly_1",
                    pattern_type="anomaly",
                    confidence_score=0.9,
                    frequency=len(anomalies),
                    impact_score=max(abs(a - mean_score) for a in anomalies),
                    conditions={"mean": mean_score, "std_dev": std_dev, "threshold": 2 * std_dev},
                    outcomes={"anomaly_count": len(anomalies), "anomaly_values": anomalies},
                    discovered_at=datetime.now(),
                    last_seen=datetime.now()
                )
                patterns.append(pattern)
        
        return patterns
    
    def _is_improving_trend(self, scores: List[float]) -> bool:
        """改善トレンド判定"""
        if len(scores) < 3:
            return False
        
        # 直近の値が過去より高いかチェック
        recent_avg = statistics.mean(scores[-3:])
        earlier_avg = statistics.mean(scores[:-3]) if len(scores) > 3 else scores[0]
        
        return recent_avg > earlier_avg * 1.05  # 5%以上の改善
    
    def _detect_weekly_pattern(self, scores: List[float]) -> bool:
        """週次パターン検出"""
        if len(scores) < 14:
            return False
        
        # 簡易的な週次相関チェック
        weekly_scores = []
        for i in range(0, len(scores) - 7, 7):
            week_score = statistics.mean(scores[i:i+7])
            weekly_scores.append(week_score)
        
        if len(weekly_scores) >= 2:
            # 週ごとのスコア変動を確認
            variance = statistics.variance(weekly_scores)
            return variance < 0.1  # 変動が小さければ周期性あり
        
        return False


class PredictiveTrendEngine:
    """予測トレンドエンジン"""
    
    def __init__(self):
        self.prediction_horizon = 30  # days
    
    def predict_trends(self, unified_data: Dict, patterns: List[LearningPattern]) -> List[IntelligenceInsight]:
        """トレンド予測"""
        print("🔮 予測トレンド分析開始...")
        
        insights = []
        
        # 品質スコア予測
        quality_predictions = self._predict_quality_trends(unified_data)
        insights.extend(quality_predictions)
        
        # 改善効果予測
        improvement_predictions = self._predict_improvement_effects(unified_data, patterns)
        insights.extend(improvement_predictions)
        
        # リスク予測
        risk_predictions = self._predict_risk_areas(unified_data, patterns)
        insights.extend(risk_predictions)
        
        # 機会予測
        opportunity_predictions = self._predict_opportunities(unified_data, patterns)
        insights.extend(opportunity_predictions)
        
        print(f"✅ 予測分析完了: {len(insights)}個の洞察を生成")
        return insights
    
    def _predict_quality_trends(self, unified_data: Dict) -> List[IntelligenceInsight]:
        """品質トレンド予測"""
        insights = []
        
        timeline = unified_data["quality_metrics_timeline"]
        if len(timeline) < 5:
            return insights
        
        recent_scores = [item.get("overall_score", 0) for item in timeline[-10:]]
        
        if recent_scores:
            trend_slope = self._calculate_trend_slope(recent_scores)
            
            if trend_slope > 0.01:  # 改善トレンド
                insight = IntelligenceInsight(
                    insight_id="quality_trend_positive",
                    insight_type="prediction",
                    title="品質スコア改善トレンド継続予測",
                    description=f"現在の改善トレンド（{trend_slope:.3f}/期間）が継続すれば、30日後に{recent_scores[-1] + trend_slope * 30:.2f}のスコア達成予測",
                    evidence=[f"直近10回の平均改善率: {trend_slope:.3f}", f"現在スコア: {recent_scores[-1]:.2f}"],
                    confidence=0.7,
                    actionable_items=[
                        "現在の改善アプローチを継続",
                        "成功要因の文書化・標準化",
                        "改善効果の定期測定"
                    ],
                    expected_impact=trend_slope * 30,
                    time_sensitivity="medium_term",
                    generated_at=datetime.now()
                )
                insights.append(insight)
            elif trend_slope < -0.01:  # 悪化トレンド
                insight = IntelligenceInsight(
                    insight_id="quality_trend_negative",
                    insight_type="warning",
                    title="品質スコア悪化トレンド警告",
                    description=f"品質スコアが悪化傾向（{trend_slope:.3f}/期間）。対策なしでは30日後に{recent_scores[-1] + trend_slope * 30:.2f}まで低下予測",
                    evidence=[f"直近10回の平均悪化率: {trend_slope:.3f}", f"現在スコア: {recent_scores[-1]:.2f}"],
                    confidence=0.8,
                    actionable_items=[
                        "緊急品質改善計画の策定",
                        "悪化要因の根本分析",
                        "追加品質チェック導入"
                    ],
                    expected_impact=abs(trend_slope * 30),
                    time_sensitivity="immediate",
                    generated_at=datetime.now()
                )
                insights.append(insight)
        
        return insights
    
    def _predict_improvement_effects(self, unified_data: Dict, patterns: List[LearningPattern]) -> List[IntelligenceInsight]:
        """改善効果予測"""
        insights = []
        
        improvement_patterns = [p for p in patterns if p.pattern_type == "improvement"]
        
        for pattern in improvement_patterns:
            if pattern.confidence_score >= 0.7:
                insight = IntelligenceInsight(
                    insight_id=f"improvement_effect_{pattern.pattern_id}",
                    insight_type="recommendation",
                    title="継続的改善効果の最大化",
                    description=f"発見されたパターン '{pattern.pattern_id}' の継続により、{pattern.impact_score:.2f}ポイントの追加改善が期待される",
                    evidence=[f"パターン信頼度: {pattern.confidence_score:.2f}", f"過去の改善実績: {pattern.impact_score:.2f}"],
                    confidence=pattern.confidence_score,
                    actionable_items=[
                        "成功パターンの再現・標準化",
                        "同様の条件での展開検討",
                        "効果測定の継続実施"
                    ],
                    expected_impact=pattern.impact_score * 1.5,  # 最大化効果
                    time_sensitivity="short_term",
                    generated_at=datetime.now()
                )
                insights.append(insight)
        
        return insights
    
    def _predict_risk_areas(self, unified_data: Dict, patterns: List[LearningPattern]) -> List[IntelligenceInsight]:
        """リスク領域予測"""
        insights = []
        
        failure_patterns = [p for p in patterns if p.pattern_type in ["regression", "anomaly"]]
        
        for pattern in failure_patterns:
            if pattern.confidence_score >= 0.6:
                insight = IntelligenceInsight(
                    insight_id=f"risk_prediction_{pattern.pattern_id}",
                    insight_type="warning",
                    title="潜在的リスク領域の特定",
                    description=f"パターン '{pattern.pattern_id}' に基づき、{pattern.frequency}回の類似問題発生リスクあり",
                    evidence=[f"過去の発生頻度: {pattern.frequency}回", f"影響度: {pattern.impact_score:.2f}"],
                    confidence=pattern.confidence_score,
                    actionable_items=[
                        "予防的対策の実施",
                        "監視強化による早期発見",
                        "コンティンジェンシープランの策定"
                    ],
                    expected_impact=pattern.impact_score,
                    time_sensitivity="short_term" if pattern.confidence_score >= 0.8 else "medium_term",
                    generated_at=datetime.now()
                )
                insights.append(insight)
        
        return insights
    
    def _predict_opportunities(self, unified_data: Dict, patterns: List[LearningPattern]) -> List[IntelligenceInsight]:
        """機会予測"""
        insights = []
        
        # データ分析から機会を発見
        actions_history = unified_data["improvement_actions_history"]
        
        if actions_history:
            # 成功率の高いアクションタイプを特定
            successful_actions = []
            for item in actions_history:
                success_indicators = item.get("success_indicators", {})
                if success_indicators.get("success", False) or success_indicators.get("status") == "passed":
                    successful_actions.extend(item.get("actions", []))
            
            if successful_actions:
                action_counts = Counter(successful_actions)
                top_actions = action_counts.most_common(3)
                
                insight = IntelligenceInsight(
                    insight_id="opportunity_successful_actions",
                    insight_type="opportunity",
                    title="高成功率アクションの拡大機会",
                    description=f"成功率の高いアクション '{top_actions[0][0]}' を他の領域にも適用することで追加改善が期待される",
                    evidence=[f"成功実績: {top_actions[0][1]}回", "類似条件での適用可能性"],
                    confidence=0.6,
                    actionable_items=[
                        "成功アクションの他領域適用検討",
                        "適用条件の分析・文書化",
                        "段階的展開計画の策定"
                    ],
                    expected_impact=0.3,
                    time_sensitivity="medium_term",
                    generated_at=datetime.now()
                )
                insights.append(insight)
        
        return insights
    
    def _calculate_trend_slope(self, scores: List[float]) -> float:
        """トレンド傾きの計算"""
        if len(scores) < 2:
            return 0
        
        # 簡単な線形回帰の傾き
        n = len(scores)
        x_values = list(range(n))
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(scores)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, scores))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return 0
        
        return numerator / denominator


class ContinuousLearningEngine:
    """継続学習エンジン"""
    
    def __init__(self):
        self.learning_models = {}
        self.feedback_history = []
    
    def update_learning_models(self, unified_data: Dict, patterns: List[LearningPattern], insights: List[IntelligenceInsight]) -> Dict[str, Any]:
        """学習モデル更新"""
        print("🧠 継続学習システム更新開始...")
        
        learning_updates = {
            "model_updates": 0,
            "new_patterns": len(patterns),
            "insight_accuracy": 0.0,
            "learning_effectiveness": 0.0,
            "next_learning_goals": []
        }
        
        # パターンモデル更新
        self._update_pattern_models(patterns)
        learning_updates["model_updates"] += 1
        
        # 予測モデル更新
        self._update_prediction_models(insights)
        learning_updates["model_updates"] += 1
        
        # 学習効果測定
        effectiveness = self._measure_learning_effectiveness(unified_data)
        learning_updates["learning_effectiveness"] = effectiveness
        
        # 次の学習目標設定
        goals = self._set_next_learning_goals(patterns, insights)
        learning_updates["next_learning_goals"] = goals
        
        print(f"✅ 継続学習更新完了: 効果度{effectiveness:.2f}")
        return learning_updates
    
    def _update_pattern_models(self, patterns: List[LearningPattern]):
        """パターンモデル更新"""
        for pattern in patterns:
            model_key = f"pattern_{pattern.pattern_type}"
            
            if model_key not in self.learning_models:
                self.learning_models[model_key] = {
                    "instances": [],
                    "accuracy": 0.0,
                    "confidence_threshold": 0.7
                }
            
            self.learning_models[model_key]["instances"].append({
                "pattern_id": pattern.pattern_id,
                "confidence": pattern.confidence_score,
                "impact": pattern.impact_score,
                "conditions": pattern.conditions,
                "timestamp": pattern.discovered_at
            })
            
            # 最新50個まで保持
            if len(self.learning_models[model_key]["instances"]) > 50:
                self.learning_models[model_key]["instances"] = self.learning_models[model_key]["instances"][-50:]
    
    def _update_prediction_models(self, insights: List[IntelligenceInsight]):
        """予測モデル更新"""
        for insight in insights:
            model_key = f"prediction_{insight.insight_type}"
            
            if model_key not in self.learning_models:
                self.learning_models[model_key] = {
                    "predictions": [],
                    "accuracy_history": [],
                    "confidence_calibration": 1.0
                }
            
            self.learning_models[model_key]["predictions"].append({
                "insight_id": insight.insight_id,
                "confidence": insight.confidence,
                "expected_impact": insight.expected_impact,
                "time_sensitivity": insight.time_sensitivity,
                "timestamp": insight.generated_at
            })
    
    def _measure_learning_effectiveness(self, unified_data: Dict) -> float:
        """学習効果測定"""
        # 簡易的な効果測定
        timeline = unified_data["quality_metrics_timeline"]
        
        if len(timeline) < 10:
            return 0.5
        
        recent_scores = [item.get("overall_score", 0) for item in timeline[-10:]]
        earlier_scores = [item.get("overall_score", 0) for item in timeline[-20:-10]] if len(timeline) >= 20 else recent_scores
        
        if recent_scores and earlier_scores:
            recent_avg = statistics.mean(recent_scores)
            earlier_avg = statistics.mean(earlier_scores)
            
            improvement = (recent_avg - earlier_avg) / max(0.01, earlier_avg)  # 正規化された改善率
            return max(0.0, min(1.0, improvement + 0.5))  # 0-1に正規化
        
        return 0.5
    
    def _set_next_learning_goals(self, patterns: List[LearningPattern], insights: List[IntelligenceInsight]) -> List[str]:
        """次の学習目標設定"""
        goals = []
        
        # パターンベースの目標
        low_confidence_patterns = [p for p in patterns if p.confidence_score < 0.7]
        if low_confidence_patterns:
            goals.append(f"低信頼度パターンの精度向上 ({len(low_confidence_patterns)}個)")
        
        # 予測精度改善目標
        warning_insights = [i for i in insights if i.insight_type == "warning"]
        if warning_insights:
            goals.append(f"警告予測の精度向上 ({len(warning_insights)}個)")
        
        # 一般的な改善目標
        goals.extend([
            "データ品質の継続向上",
            "新しいパターン発見の促進",
            "予測モデルの精度向上"
        ])
        
        return goals[:5]  # 上位5個まで


class IntelligenceEngineSystem:
    """インテリジェンス・エンジン・システム メインクラス"""
    
    def __init__(self):
        self.data_engine = DataUnificationEngine()
        self.pattern_engine = PatternRecognitionEngine()
        self.prediction_engine = PredictiveTrendEngine()
        self.learning_engine = ContinuousLearningEngine()
    
    def run_full_intelligence_analysis(self) -> Dict[str, Any]:
        """完全インテリジェンス分析実行"""
        print("🤖 インテリジェンス・エンジン・システム開始...")
        
        # Step 1: データ統合
        unified_data = self.data_engine.unify_all_data()
        
        # Step 2: パターン認識
        patterns = self.pattern_engine.recognize_patterns(unified_data)
        
        # Step 3: 予測・トレンド分析
        insights = self.prediction_engine.predict_trends(unified_data, patterns)
        
        # Step 4: 継続学習更新
        learning_updates = self.learning_engine.update_learning_models(unified_data, patterns, insights)
        
        # 結果統合
        result = {
            "analysis_metadata": {
                "execution_timestamp": datetime.now().isoformat(),
                "data_quality_score": unified_data["metadata"]["data_quality_score"],
                "total_data_sources": unified_data["metadata"]["total_sources"],
                "successful_loads": unified_data["metadata"]["successful_loads"]
            },
            "pattern_analysis": {
                "total_patterns": len(patterns),
                "pattern_types": list(set(p.pattern_type for p in patterns)),
                "high_confidence_patterns": len([p for p in patterns if p.confidence_score >= 0.8]),
                "patterns_summary": [self._pattern_to_dict(p) for p in patterns[:10]]
            },
            "predictive_insights": {
                "total_insights": len(insights),
                "insight_types": list(set(i.insight_type for i in insights)),
                "immediate_actions": len([i for i in insights if i.time_sensitivity == "immediate"]),
                "insights_summary": [self._insight_to_dict(i) for i in insights[:10]]
            },
            "learning_updates": learning_updates,
            "intelligence_score": self._calculate_intelligence_score(patterns, insights, learning_updates),
            "next_recommendations": self._generate_next_recommendations(insights[:5])
        }
        
        # 結果保存
        self._save_intelligence_results(result)
        
        print(f"✅ インテリジェンス分析完了: 知能スコア {result['intelligence_score']:.2f}")
        return result
    
    def _pattern_to_dict(self, pattern: LearningPattern) -> Dict[str, Any]:
        """パターンを辞書形式に変換"""
        return {
            "id": pattern.pattern_id,
            "type": pattern.pattern_type,
            "confidence": round(pattern.confidence_score, 3),
            "frequency": pattern.frequency,
            "impact": round(pattern.impact_score, 3),
            "conditions": pattern.conditions
        }
    
    def _insight_to_dict(self, insight: IntelligenceInsight) -> Dict[str, Any]:
        """洞察を辞書形式に変換"""
        return {
            "id": insight.insight_id,
            "type": insight.insight_type,
            "title": insight.title,
            "confidence": round(insight.confidence, 3),
            "expected_impact": round(insight.expected_impact, 3),
            "time_sensitivity": insight.time_sensitivity,
            "actionable_items": insight.actionable_items[:3]  # 上位3個まで
        }
    
    def _calculate_intelligence_score(self, patterns: List[LearningPattern], insights: List[IntelligenceInsight], learning_updates: Dict) -> float:
        """知能スコア計算"""
        score = 0.0
        
        # パターン認識スコア (0.4)
        if patterns:
            avg_pattern_confidence = statistics.mean([p.confidence_score for p in patterns])
            pattern_diversity = len(set(p.pattern_type for p in patterns)) / 4.0  # 4種類のパターン
            score += (avg_pattern_confidence * 0.7 + pattern_diversity * 0.3) * 0.4
        
        # 洞察生成スコア (0.3)
        if insights:
            avg_insight_confidence = statistics.mean([i.confidence for i in insights])
            insight_diversity = len(set(i.insight_type for i in insights)) / 4.0  # 4種類の洞察
            score += (avg_insight_confidence * 0.8 + insight_diversity * 0.2) * 0.3
        
        # 学習効果スコア (0.3)
        learning_effectiveness = learning_updates.get("learning_effectiveness", 0.5)
        score += learning_effectiveness * 0.3
        
        return min(1.0, score)
    
    def _generate_next_recommendations(self, top_insights: List[IntelligenceInsight]) -> List[str]:
        """次の推奨アクション生成"""
        recommendations = []
        
        for insight in top_insights:
            if insight.time_sensitivity == "immediate":
                recommendations.append(f"🚨 緊急: {insight.actionable_items[0] if insight.actionable_items else insight.title}")
            elif insight.insight_type == "opportunity":
                recommendations.append(f"💡 機会: {insight.actionable_items[0] if insight.actionable_items else insight.title}")
            elif insight.insight_type == "warning":
                recommendations.append(f"⚠️ 注意: {insight.actionable_items[0] if insight.actionable_items else insight.title}")
            else:
                recommendations.append(f"📊 分析: {insight.actionable_items[0] if insight.actionable_items else insight.title}")
        
        return recommendations[:10]
    
    def _save_intelligence_results(self, result: Dict[str, Any]):
        """インテリジェンス結果保存"""
        try:
            os.makedirs("out", exist_ok=True)
            with open("out/intelligence_analysis.json", "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"結果保存エラー: {e}")
    
    def display_intelligence_results(self, result: Dict[str, Any]):
        """インテリジェンス結果表示"""
        print("\n🤖 インテリジェンス・エンジン分析結果")
        print("=" * 60)
        
        metadata = result["analysis_metadata"]
        pattern_analysis = result["pattern_analysis"]
        insights = result["predictive_insights"]
        learning = result["learning_updates"]
        
        print(f"📊 システム統計:")
        print(f"   データ品質スコア: {metadata['data_quality_score']:.2f}")
        print(f"   データソース: {metadata['successful_loads']}/{metadata['total_data_sources']}")
        print(f"   知能スコア: {result['intelligence_score']:.2f}")
        
        print(f"\n🔍 パターン認識結果:")
        print(f"   発見パターン: {pattern_analysis['total_patterns']}個")
        print(f"   高信頼度パターン: {pattern_analysis['high_confidence_patterns']}個")
        print(f"   パターン種別: {', '.join(pattern_analysis['pattern_types'])}")
        
        print(f"\n🔮 予測洞察結果:")
        print(f"   生成洞察: {insights['total_insights']}個")
        print(f"   緊急対応項目: {insights['immediate_actions']}個")
        print(f"   洞察種別: {', '.join(insights['insight_types'])}")
        
        print(f"\n🧠 学習システム:")
        print(f"   学習効果: {learning['learning_effectiveness']:.2f}")
        print(f"   モデル更新: {learning['model_updates']}個")
        print(f"   次の学習目標: {len(learning['next_learning_goals'])}個")
        
        print(f"\n🚀 次の推奨アクション:")
        for rec in result["next_recommendations"][:5]:
            print(f"   • {rec}")


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="🤖 Intelligence Engine System")
    parser.add_argument("--full-analysis", action="store_true", help="Run full intelligence analysis")
    parser.add_argument("--display-only", action="store_true", help="Display last intelligence results")
    
    args = parser.parse_args()
    
    system = IntelligenceEngineSystem()
    
    if args.display_only:
        try:
            with open("out/intelligence_analysis.json") as f:
                result = json.load(f)
                system.display_intelligence_results(result)
        except:
            print("❌ 保存されたインテリジェンス分析結果が見つかりません")
    elif args.full_analysis:
        result = system.run_full_intelligence_analysis()
        system.display_intelligence_results(result)
    else:
        result = system.run_full_intelligence_analysis()
        system.display_intelligence_results(result)


if __name__ == "__main__":
    main()


