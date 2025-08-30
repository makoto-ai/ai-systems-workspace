#!/usr/bin/env python3
"""
🧠 Phase 4: AIベース最適化提案エンジン
===================================

Phase 1-3の学習データを統合分析し、問題の重要度・影響度を自動算出、
修正効果を予測して優先順位付けするインテリジェント最適化システム

主要機能:
- 学習データ統合分析
- 問題重要度AI算出
- 修正効果予測エンジン
- 優先順位付け最適化
- アクション推奨生成
"""

import os
import sys
import json
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re
import math


@dataclass
class QualityIssue:
    """品質問題データクラス"""
    id: str
    file_path: str
    issue_type: str
    severity: str
    frequency: int
    last_seen: datetime
    impact_score: float
    fix_difficulty: float
    business_impact: float
    technical_debt: float
    predicted_fix_time: int  # minutes


@dataclass  
class OptimizationRecommendation:
    """最適化推奨データクラス"""
    priority_rank: int
    issue: QualityIssue
    action: str
    expected_improvement: float
    effort_estimate: str
    success_probability: float
    roi_score: float
    detailed_steps: List[str]
    prerequisites: List[str]


class DataIntegrationEngine:
    """学習データ統合エンジン"""
    
    def __init__(self):
        self.base_dir = Path(".")
        self.data_sources = [
            "out/learning_insights.json",      # Phase 1
            "out/system_health.json",          # Phase 1
            "out/issue_predictions.json",      # Phase 2
            "out/preventive_fixes.json",       # Phase 2
            "out/realtime_quality.json",       # Phase 3
            "out/feedback_history.json",       # Phase 3
            "out/gate_learning.json",          # Phase 3
            "out/auto_guard_learning.json",    # Phase 3
        ]
        
    def load_integrated_data(self) -> Dict[str, Any]:
        """全データソースを統合読み込み"""
        integrated_data = {
            "phase1_insights": {},
            "phase1_health": {},
            "phase2_predictions": {},
            "phase2_fixes": {},
            "phase3_realtime": {},
            "phase3_feedback": [],
            "phase3_gates": {},
            "phase3_guards": [],
            "last_updated": datetime.now().isoformat()
        }
        
        # Phase 1 データ
        integrated_data["phase1_insights"] = self._load_json("out/learning_insights.json")
        integrated_data["phase1_health"] = self._load_json("out/system_health.json")
        
        # Phase 2 データ
        integrated_data["phase2_predictions"] = self._load_json("out/issue_predictions.json")
        integrated_data["phase2_fixes"] = self._load_json("out/preventive_fixes.json")
        
        # Phase 3 データ
        integrated_data["phase3_realtime"] = self._load_json("out/realtime_quality.json")
        integrated_data["phase3_feedback"] = self._load_jsonl("out/feedback_history.json")
        integrated_data["phase3_gates"] = self._load_json("out/gate_learning.json")
        integrated_data["phase3_guards"] = self._load_jsonl("out/auto_guard_learning.json")
        
        return integrated_data
    
    def _load_json(self, filepath: str) -> Dict[str, Any]:
        """JSON ファイル読み込み"""
        try:
            with open(filepath) as f:
                return json.load(f)
        except:
            return {}
    
    def _load_jsonl(self, filepath: str) -> List[Dict[str, Any]]:
        """JSONL ファイル読み込み"""
        try:
            data = []
            with open(filepath) as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
            return data
        except:
            return []


class IssueAnalysisEngine:
    """問題分析エンジン"""
    
    def __init__(self, integrated_data: Dict[str, Any]):
        self.data = integrated_data
        self.issue_patterns = self._load_issue_patterns()
        
    def _load_issue_patterns(self) -> Dict[str, Any]:
        """既存の問題パターンを読み込み"""
        patterns = {
            "yaml_issues": {
                "trailing_spaces": {"severity": 3, "fix_difficulty": 1, "frequency_weight": 1.2},
                "indentation": {"severity": 4, "fix_difficulty": 2, "frequency_weight": 1.1},
                "syntax_error": {"severity": 5, "fix_difficulty": 3, "frequency_weight": 1.5}
            },
            "python_issues": {
                "missing_docstring": {"severity": 2, "fix_difficulty": 2, "frequency_weight": 0.8},
                "long_function": {"severity": 3, "fix_difficulty": 4, "frequency_weight": 1.0},
                "complex_logic": {"severity": 4, "fix_difficulty": 5, "frequency_weight": 1.3}
            },
            "security_issues": {
                "exposed_secrets": {"severity": 5, "fix_difficulty": 2, "frequency_weight": 2.0},
                "unsafe_permissions": {"severity": 4, "fix_difficulty": 3, "frequency_weight": 1.7}
            }
        }
        return patterns
    
    def analyze_all_issues(self) -> List[QualityIssue]:
        """全問題の統合分析"""
        issues = []
        
        # Phase 2 予測問題
        if "predictions" in self.data["phase2_predictions"]:
            for pred in self.data["phase2_predictions"]["predictions"]:
                issue = self._create_issue_from_prediction(pred)
                if issue:
                    issues.append(issue)
        
        # Phase 3 リアルタイム問題
        for feedback in self.data["phase3_feedback"]:
            if feedback.get("level") in ["warning", "error"]:
                issue = self._create_issue_from_feedback(feedback)
                if issue:
                    issues.append(issue)
        
        # Phase 3 ガード問題
        for guard in self.data["phase3_guards"]:
            if not guard.get("success", True):
                issue = self._create_issue_from_guard(guard)
                if issue:
                    issues.append(issue)
        
        # 重複除去・統合
        issues = self._deduplicate_issues(issues)
        
        return issues
    
    def _create_issue_from_prediction(self, pred: Dict) -> Optional[QualityIssue]:
        """予測データから問題を生成"""
        try:
            return QualityIssue(
                id=f"pred_{hash(str(pred))}",
                file_path=pred.get("file", "unknown"),
                issue_type="predicted",
                severity=pred.get("risk_level", "medium"),
                frequency=1,
                last_seen=datetime.now(),
                impact_score=self._calculate_impact_score(pred),
                fix_difficulty=self._estimate_fix_difficulty(pred),
                business_impact=self._calculate_business_impact(pred),
                technical_debt=self._calculate_technical_debt(pred),
                predicted_fix_time=self._estimate_fix_time(pred)
            )
        except:
            return None
    
    def _create_issue_from_feedback(self, feedback: Dict) -> Optional[QualityIssue]:
        """フィードバックから問題を生成"""
        try:
            return QualityIssue(
                id=f"feedback_{hash(str(feedback))}",
                file_path=feedback.get("file", "unknown"),
                issue_type="quality_feedback",
                severity=feedback.get("level", "warning"),
                frequency=1,
                last_seen=datetime.fromisoformat(feedback["timestamp"]),
                impact_score=1.0 - feedback.get("score", 0.5),
                fix_difficulty=2.0 if feedback.get("level") == "error" else 1.5,
                business_impact=self._calculate_business_impact(feedback),
                technical_debt=1.0 - feedback.get("score", 0.5),
                predicted_fix_time=15 if feedback.get("level") == "error" else 10
            )
        except:
            return None
    
    def _create_issue_from_guard(self, guard: Dict) -> Optional[QualityIssue]:
        """ガード問題から生成"""
        try:
            return QualityIssue(
                id=f"guard_{hash(str(guard))}",
                file_path=guard.get("file", "unknown"),
                issue_type="auto_guard",
                severity=guard.get("severity", "medium"),
                frequency=1,
                last_seen=datetime.fromisoformat(guard["timestamp"]),
                impact_score=2.0 if guard.get("severity") == "critical" else 1.0,
                fix_difficulty=3.0 if guard.get("action") == "emergency_rollback" else 2.0,
                business_impact=self._calculate_business_impact(guard),
                technical_debt=2.0 if not guard.get("success") else 0.5,
                predicted_fix_time=30 if guard.get("severity") == "critical" else 20
            )
        except:
            return None
    
    def _deduplicate_issues(self, issues: List[QualityIssue]) -> List[QualityIssue]:
        """重複問題の除去・統合"""
        file_issues = {}
        
        for issue in issues:
            key = f"{issue.file_path}:{issue.issue_type}"
            if key in file_issues:
                # 頻度を増やし、最新の情報で更新
                existing = file_issues[key]
                existing.frequency += 1
                if issue.last_seen > existing.last_seen:
                    existing.last_seen = issue.last_seen
                    existing.severity = issue.severity
                # 影響度は平均化
                existing.impact_score = (existing.impact_score + issue.impact_score) / 2
            else:
                file_issues[key] = issue
        
        return list(file_issues.values())
    
    def _calculate_impact_score(self, data: Dict) -> float:
        """影響度スコア計算"""
        base_score = 1.0
        
        # ファイル重要度
        file_path = data.get("file", "")
        if "critical" in file_path or ".github/workflows" in file_path:
            base_score *= 1.5
        elif "tests/" in file_path:
            base_score *= 1.2
        
        # リスクレベル
        risk = data.get("risk_level", data.get("severity", "medium"))
        if risk == "critical":
            base_score *= 2.0
        elif risk == "high":
            base_score *= 1.5
        elif risk == "medium":
            base_score *= 1.0
        else:
            base_score *= 0.7
        
        return min(5.0, base_score)
    
    def _estimate_fix_difficulty(self, data: Dict) -> float:
        """修正難易度推定"""
        difficulty = 2.0  # デフォルト
        
        issue_type = data.get("issue_type", data.get("action", ""))
        
        if "syntax" in issue_type or "yaml" in issue_type:
            difficulty = 1.5
        elif "security" in issue_type or "rollback" in issue_type:
            difficulty = 4.0
        elif "complex" in issue_type or "architecture" in issue_type:
            difficulty = 5.0
        
        return difficulty
    
    def _calculate_business_impact(self, data: Dict) -> float:
        """ビジネス影響度計算"""
        impact = 1.0
        
        file_path = data.get("file", "")
        
        # クリティカルファイル
        if any(critical in file_path for critical in [
            ".github/workflows", "deploy", "production", "main", "master"
        ]):
            impact = 3.0
        # 重要ファイル
        elif any(important in file_path for important in [
            "api", "service", "core", "src"
        ]):
            impact = 2.0
        # テスト・ドキュメント
        elif any(low in file_path for low in [
            "test", "doc", "example", "demo"
        ]):
            impact = 0.5
        
        return impact
    
    def _calculate_technical_debt(self, data: Dict) -> float:
        """技術的負債計算"""
        debt = 1.0
        
        # 修正の緊急度・複雑度から推定
        severity = data.get("severity", "medium")
        if severity == "critical":
            debt = 3.0
        elif severity == "high":
            debt = 2.0
        elif severity == "low":
            debt = 0.5
        
        return debt
    
    def _estimate_fix_time(self, data: Dict) -> int:
        """修正時間推定（分）"""
        base_time = 15
        
        difficulty = self._estimate_fix_difficulty(data)
        severity = data.get("severity", "medium")
        
        multiplier = 1.0
        if severity == "critical":
            multiplier = 2.0
        elif severity == "high":
            multiplier = 1.5
        
        return int(base_time * difficulty * multiplier)


class OptimizationEngine:
    """最適化エンジン"""
    
    def __init__(self):
        self.success_rates = {
            "yaml_fixes": 0.9,
            "python_fixes": 0.8,
            "security_fixes": 0.95,
            "documentation": 0.7,
            "refactoring": 0.6
        }
    
    def generate_recommendations(self, issues: List[QualityIssue]) -> List[OptimizationRecommendation]:
        """最適化推奨生成"""
        recommendations = []
        
        # 各問題を分析して推奨を生成
        for issue in issues:
            rec = self._create_recommendation(issue)
            if rec:
                recommendations.append(rec)
        
        # ROIでソート（効果/工数の最大化）
        recommendations.sort(key=lambda x: x.roi_score, reverse=True)
        
        # 優先順位付け
        for i, rec in enumerate(recommendations, 1):
            rec.priority_rank = i
        
        return recommendations[:20]  # 上位20個まで
    
    def _create_recommendation(self, issue: QualityIssue) -> Optional[OptimizationRecommendation]:
        """個別推奨作成"""
        try:
            action = self._determine_action(issue)
            expected_improvement = self._calculate_expected_improvement(issue)
            effort_estimate = self._categorize_effort(issue.predicted_fix_time)
            success_probability = self._estimate_success_probability(issue)
            roi_score = self._calculate_roi(expected_improvement, issue.predicted_fix_time, success_probability)
            
            return OptimizationRecommendation(
                priority_rank=0,  # 後で設定
                issue=issue,
                action=action,
                expected_improvement=expected_improvement,
                effort_estimate=effort_estimate,
                success_probability=success_probability,
                roi_score=roi_score,
                detailed_steps=self._generate_detailed_steps(issue),
                prerequisites=self._determine_prerequisites(issue)
            )
        except:
            return None
    
    def _determine_action(self, issue: QualityIssue) -> str:
        """アクション決定"""
        if issue.issue_type == "predicted":
            return f"予防的修正: {issue.severity} レベル問題の解決"
        elif issue.issue_type == "quality_feedback":
            return f"品質改善: スコア {(1-issue.impact_score):.2f} から向上"
        elif issue.issue_type == "auto_guard":
            return f"ガード修正: {issue.severity} 問題の解決"
        else:
            return f"品質向上: {issue.file_path} の改善"
    
    def _calculate_expected_improvement(self, issue: QualityIssue) -> float:
        """期待改善効果計算"""
        base_improvement = issue.impact_score * issue.business_impact * (issue.frequency / 2.0)
        
        # 技術的負債軽減効果
        debt_reduction = issue.technical_debt * 0.3
        
        # 全体的な品質向上効果
        quality_boost = min(1.0, base_improvement + debt_reduction)
        
        return quality_boost
    
    def _categorize_effort(self, minutes: int) -> str:
        """工数カテゴリ化"""
        if minutes <= 15:
            return "簡単 (15分以内)"
        elif minutes <= 60:
            return "標準 (1時間以内)"
        elif minutes <= 240:
            return "中程度 (半日以内)"
        else:
            return "大規模 (1日以上)"
    
    def _estimate_success_probability(self, issue: QualityIssue) -> float:
        """成功確率推定"""
        base_probability = 0.8
        
        # 難易度による調整
        difficulty_factor = max(0.3, 1.0 - (issue.fix_difficulty - 1) * 0.15)
        
        # 問題タイプによる調整
        type_factor = 1.0
        if issue.issue_type == "predicted":
            type_factor = 0.9  # 予測なのでやや不確実
        elif issue.issue_type == "auto_guard":
            type_factor = 0.95  # 自動ガードが検出済みなので確実
        
        return base_probability * difficulty_factor * type_factor
    
    def _calculate_roi(self, improvement: float, time_minutes: int, success_prob: float) -> float:
        """ROI 計算"""
        # 効果を時間で割って、成功確率を掛ける
        roi = (improvement * success_prob) / (time_minutes / 60.0)  # 時間単位
        return roi
    
    def _generate_detailed_steps(self, issue: QualityIssue) -> List[str]:
        """詳細ステップ生成"""
        steps = []
        
        if "yaml" in issue.file_path:
            steps = [
                "1. yamllint でファイルの構文チェック実行",
                "2. 自動修正可能な項目を scripts/quality/yaml_auto_fixer.py で修正",
                "3. 手動修正が必要な項目をエディタで修正",
                "4. 修正後に再度 yamllint で確認"
            ]
        elif ".py" in issue.file_path:
            steps = [
                "1. Python ファイルの構文・品質チェック",
                "2. docstring の追加・改善",
                "3. コード複雑度の軽減",
                "4. テスト実行で動作確認"
            ]
        else:
            steps = [
                "1. ファイルの現在の状態を確認",
                "2. 問題箇所の特定・分析",
                "3. 修正計画の策定",
                "4. 修正実行・テスト",
                "5. 品質向上効果の確認"
            ]
        
        return steps
    
    def _determine_prerequisites(self, issue: QualityIssue) -> List[str]:
        """前提条件決定"""
        prerequisites = []
        
        if issue.fix_difficulty >= 3:
            prerequisites.append("バックアップの作成")
        
        if issue.business_impact >= 2:
            prerequisites.append("ステージング環境での事前テスト")
        
        if issue.issue_type == "auto_guard" and issue.severity == "critical":
            prerequisites.append("緊急対応チームの準備")
        
        if "security" in issue.issue_type:
            prerequisites.append("セキュリティレビューの実施")
        
        return prerequisites if prerequisites else ["特になし"]


class IntelligentOptimizerEngine:
    """インテリジェント最適化メインエンジン"""
    
    def __init__(self):
        self.data_engine = DataIntegrationEngine()
        self.optimization_engine = OptimizationEngine()
        self.last_analysis = None
    
    def analyze_and_optimize(self) -> Dict[str, Any]:
        """分析・最適化実行"""
        print("🧠 インテリジェント品質最適化分析開始...")
        
        # データ統合
        integrated_data = self.data_engine.load_integrated_data()
        print(f"📊 {len(self.data_engine.data_sources)} データソースを統合")
        
        # 問題分析
        analysis_engine = IssueAnalysisEngine(integrated_data)
        issues = analysis_engine.analyze_all_issues()
        print(f"🔍 {len(issues)} 個の品質問題を検出・分析")
        
        # 最適化推奨生成
        recommendations = self.optimization_engine.generate_recommendations(issues)
        print(f"💡 {len(recommendations)} 個の最適化推奨を生成")
        
        # 結果統合
        result = {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_issues": len(issues),
            "total_recommendations": len(recommendations),
            "data_sources_analyzed": len(self.data_engine.data_sources),
            "top_recommendations": [self._rec_to_dict(rec) for rec in recommendations[:10]],
            "summary_statistics": self._calculate_summary_stats(issues, recommendations),
            "next_actions": self._generate_next_actions(recommendations[:5])
        }
        
        # 結果保存
        self._save_results(result)
        
        self.last_analysis = result
        return result
    
    def _rec_to_dict(self, rec: OptimizationRecommendation) -> Dict[str, Any]:
        """推奨を辞書形式に変換"""
        return {
            "priority": rec.priority_rank,
            "file": rec.issue.file_path,
            "issue_type": rec.issue.issue_type,
            "severity": rec.issue.severity,
            "action": rec.action,
            "expected_improvement": round(rec.expected_improvement, 3),
            "effort": rec.effort_estimate,
            "success_probability": round(rec.success_probability, 3),
            "roi_score": round(rec.roi_score, 3),
            "detailed_steps": rec.detailed_steps,
            "prerequisites": rec.prerequisites
        }
    
    def _calculate_summary_stats(self, issues: List[QualityIssue], recommendations: List[OptimizationRecommendation]) -> Dict[str, Any]:
        """統計サマリー計算"""
        if not recommendations:
            return {"total_improvement": 0, "average_roi": 0, "effort_distribution": {}}
        
        total_improvement = sum(rec.expected_improvement for rec in recommendations)
        average_roi = sum(rec.roi_score for rec in recommendations) / len(recommendations)
        
        effort_dist = {}
        for rec in recommendations:
            effort_dist[rec.effort_estimate] = effort_dist.get(rec.effort_estimate, 0) + 1
        
        severity_dist = {}
        for issue in issues:
            severity_dist[issue.severity] = severity_dist.get(issue.severity, 0) + 1
        
        return {
            "total_expected_improvement": round(total_improvement, 3),
            "average_roi": round(average_roi, 3),
            "effort_distribution": effort_dist,
            "severity_distribution": severity_dist,
            "high_impact_issues": len([i for i in issues if i.business_impact >= 2]),
            "quick_wins": len([r for r in recommendations if "簡単" in r.effort_estimate and r.roi_score >= 1.0])
        }
    
    def _generate_next_actions(self, top_recs: List[OptimizationRecommendation]) -> List[str]:
        """次のアクション生成"""
        if not top_recs:
            return ["品質分析データが不足しています。Phase 1-3システムを使用してデータを蓄積してください。"]
        
        actions = []
        
        # 最優先項目
        if top_recs[0].roi_score >= 2.0:
            actions.append(f"🚀 最優先: {top_recs[0].action} (ROI: {top_recs[0].roi_score:.1f})")
        else:
            actions.append(f"⚡ 推奨: {top_recs[0].action}")
        
        # クイックウィン
        quick_wins = [r for r in top_recs if "簡単" in r.effort_estimate]
        if quick_wins:
            actions.append(f"💡 クイックウィン: {len(quick_wins)}個の簡単修正から開始")
        
        # 高インパクト
        high_impact = [r for r in top_recs if r.expected_improvement >= 2.0]
        if high_impact:
            actions.append(f"🎯 高影響: {len(high_impact)}個の高効果修正を計画")
        
        return actions[:5]
    
    def _save_results(self, result: Dict[str, Any]):
        """結果保存"""
        try:
            os.makedirs("out", exist_ok=True)
            with open("out/intelligent_optimization.json", "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"結果保存エラー: {e}")
    
    def display_results(self):
        """結果表示"""
        if not self.last_analysis:
            print("❌ 分析結果がありません。analyze_and_optimize() を先に実行してください。")
            return
        
        result = self.last_analysis
        
        print("\n🧠 インテリジェント品質最適化分析結果")
        print("=" * 50)
        
        print(f"📊 総合統計:")
        print(f"   検出問題数: {result['total_issues']}")
        print(f"   推奨項目数: {result['total_recommendations']}")
        print(f"   データソース: {result['data_sources_analyzed']}")
        
        stats = result['summary_statistics']
        print(f"\n💎 効果予測:")
        print(f"   期待改善効果: {stats['total_expected_improvement']:.2f}")
        print(f"   平均ROI: {stats['average_roi']:.2f}")
        print(f"   クイックウィン: {stats.get('quick_wins', 0)}個")
        print(f"   高インパクト: {stats.get('high_impact_issues', 0)}個")
        
        print(f"\n🚀 次のアクション:")
        for action in result['next_actions']:
            print(f"   • {action}")
        
        print(f"\n🏆 トップ5推奨項目:")
        for i, rec in enumerate(result['top_recommendations'][:5], 1):
            print(f"   {i}. {rec['action']}")
            print(f"      ファイル: {rec['file']}")
            print(f"      効果: {rec['expected_improvement']:.2f}, 工数: {rec['effort']}, ROI: {rec['roi_score']:.2f}")


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="🧠 Intelligent Quality Optimizer")
    parser.add_argument("--analyze", action="store_true", help="Run analysis and optimization")
    parser.add_argument("--display", action="store_true", help="Display last analysis results")
    parser.add_argument("--top", type=int, default=10, help="Show top N recommendations")
    
    args = parser.parse_args()
    
    optimizer = IntelligentOptimizerEngine()
    
    if args.analyze:
        result = optimizer.analyze_and_optimize()
        optimizer.display_results()
        
    elif args.display:
        # 保存された結果を読み込み表示
        try:
            with open("out/intelligent_optimization.json") as f:
                result = json.load(f)
                optimizer.last_analysis = result
                optimizer.display_results()
        except:
            print("❌ 保存された分析結果が見つかりません。--analyze を先に実行してください。")
    
    else:
        print("❌ --analyze または --display を指定してください")
        parser.print_help()


if __name__ == "__main__":
    main()
