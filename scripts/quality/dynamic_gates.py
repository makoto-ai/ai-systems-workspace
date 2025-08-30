#!/usr/bin/env python3
"""
🎛️ Phase 3: 動的品質ゲートシステム
===============================

学習データに基づいて動的に品質基準を調整するシステム

主要機能:
- 学習データベースの動的閾値調整
- コンテキスト依存の品質基準
- ファイル種別・重要度別の適応的ゲート
- 段階的品質チェック
- 継続学習による精度向上
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


@dataclass
class QualityGate:
    """品質ゲートデータクラス"""
    name: str
    min_score: float
    warning_score: float
    context: str
    file_pattern: str
    importance_level: int  # 1-5 (5が最重要)
    learning_weight: float
    last_updated: datetime


class ContextAnalyzer:
    """コンテキスト分析クラス"""
    
    def __init__(self):
        self.project_patterns = {
            "critical": [
                r"\.github/workflows/",
                r"scripts/quality/",
                r"tests/golden/",
                r"package\.json",
                r"requirements\.txt",
                r"Dockerfile",
                r"docker-compose\.yml"
            ],
            "important": [
                r"src/",
                r"lib/",
                r"components/",
                r"services/",
                r"api/",
                r"\.py$",
                r"\.ts$",
                r"\.js$"
            ],
            "standard": [
                r"docs/",
                r"examples/",
                r"\.md$",
                r"\.txt$"
            ],
            "experimental": [
                r"experimental/",
                r"test/",
                r"demo/",
                r"sandbox/"
            ]
        }
    
    def analyze_file_context(self, file_path: str) -> Dict[str, Any]:
        """ファイルのコンテキスト分析"""
        path = Path(file_path)
        
        # 重要度レベル判定
        importance = self._determine_importance(file_path)
        
        # ファイル種別判定
        file_type = self._determine_file_type(path)
        
        # プロジェクト段階判定
        project_phase = self._determine_project_phase()
        
        # 変更履歴分析
        change_frequency = self._analyze_change_frequency(file_path)
        
        return {
            "file_path": file_path,
            "importance_level": importance,
            "file_type": file_type,
            "project_phase": project_phase,
            "change_frequency": change_frequency,
            "size_category": self._categorize_file_size(path),
            "complexity_hints": self._analyze_complexity_hints(path)
        }
    
    def _determine_importance(self, file_path: str) -> int:
        """重要度レベル判定 (1-5)"""
        for level, patterns in [
            (5, self.project_patterns["critical"]),
            (4, self.project_patterns["important"]), 
            (3, self.project_patterns["standard"]),
            (2, self.project_patterns["experimental"])
        ]:
            for pattern in patterns:
                if re.search(pattern, file_path):
                    return level
        return 1  # デフォルト
    
    def _determine_file_type(self, path: Path) -> str:
        """ファイル種別判定"""
        ext = path.suffix.lower()
        
        type_mapping = {
            ".py": "python",
            ".js": "javascript", 
            ".ts": "typescript",
            ".yml": "yaml", ".yaml": "yaml",
            ".json": "json",
            ".md": "markdown",
            ".sh": "shell",
            ".dockerfile": "docker"
        }
        
        return type_mapping.get(ext, "other")
    
    def _determine_project_phase(self) -> str:
        """プロジェクト段階判定"""
        # 簡単な判定ロジック
        # 実際のプロジェクトでは、ブランチ名やタグなどから判定
        
        if os.path.exists(".github/workflows/deploy.yml"):
            return "production"
        elif os.path.exists(".github/workflows/pr-quality-check.yml"):
            return "staging"
        else:
            return "development"
    
    def _analyze_change_frequency(self, file_path: str) -> str:
        """変更頻度分析"""
        # 簡易実装: 実際はgit logを分析
        try:
            import git
            repo = git.Repo(".")
            commits = list(repo.iter_commits(paths=file_path, max_count=10))
            
            if len(commits) >= 5:
                return "high"
            elif len(commits) >= 2:
                return "medium"
            else:
                return "low"
        except:
            return "unknown"
    
    def _categorize_file_size(self, path: Path) -> str:
        """ファイルサイズカテゴリ"""
        try:
            size = path.stat().st_size
            
            if size < 1024:  # 1KB
                return "tiny"
            elif size < 10240:  # 10KB
                return "small"
            elif size < 51200:  # 50KB
                return "medium"
            elif size < 102400:  # 100KB
                return "large"
            else:
                return "very_large"
        except:
            return "unknown"
    
    def _analyze_complexity_hints(self, path: Path) -> List[str]:
        """複雑性ヒント分析"""
        hints = []
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            lines = content.split('\n')
            
            # 行数チェック
            if len(lines) > 500:
                hints.append("long_file")
            
            # ネスト深度チェック（簡易）
            max_indent = 0
            for line in lines:
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    max_indent = max(max_indent, indent)
            
            if max_indent > 16:  # 4レベル以上のネスト
                hints.append("deep_nesting")
            
            # 複雑なパターンチェック
            if re.search(r'for.*for.*for', content):
                hints.append("nested_loops")
            
            if content.count('if') > 10:
                hints.append("many_conditions")
                
        except:
            pass
        
        return hints


class LearningEngine:
    """学習エンジンクラス"""
    
    def __init__(self):
        self.learning_data = self._load_learning_data()
        self.performance_history = self._load_performance_history()
    
    def _load_learning_data(self) -> Dict[str, Any]:
        """学習データ読み込み"""
        try:
            if os.path.exists("out/gate_learning.json"):
                with open("out/gate_learning.json") as f:
                    return json.load(f)
        except:
            pass
        
        return {
            "file_type_stats": {},
            "importance_stats": {},
            "size_stats": {},
            "phase_stats": {},
            "threshold_adjustments": [],
            "performance_metrics": []
        }
    
    def _load_performance_history(self) -> List[Dict]:
        """パフォーマンス履歴読み込み"""
        history = []
        
        try:
            if os.path.exists("out/feedback_history.json"):
                with open("out/feedback_history.json") as f:
                    for line in f:
                        if line.strip():
                            history.append(json.loads(line))
        except:
            pass
        
        return history
    
    def calculate_dynamic_thresholds(self, context: Dict[str, Any]) -> Dict[str, float]:
        """動的閾値計算"""
        base_thresholds = {
            "critical": 0.3,
            "warning": 0.6,
            "target": 0.8
        }
        
        # コンテキストベースの調整
        adjustments = self._calculate_context_adjustments(context)
        
        # 学習データベースの調整
        learning_adjustments = self._calculate_learning_adjustments(context)

        # ドリフト耐性（分位点＋EWMA）調整
        drift_adjustments = self._calculate_drift_adjustments(context, base_thresholds)
        
        # 最終閾値計算
        final_thresholds = {}
        for key, base in base_thresholds.items():
            adjustment = (
                adjustments.get(key, 0)
                + learning_adjustments.get(key, 0)
                + drift_adjustments.get(key, 0)
            )
            final_thresholds[key] = max(0.0, min(1.0, base + adjustment))
        
        return final_thresholds
    
    def _calculate_context_adjustments(self, context: Dict[str, Any]) -> Dict[str, float]:
        """コンテキストベース調整計算"""
        adjustments = {"critical": 0, "warning": 0, "target": 0}
        
        # 重要度レベル調整
        importance = context["importance_level"]
        if importance >= 5:  # 最重要
            adjustments["critical"] += 0.1
            adjustments["warning"] += 0.1
            adjustments["target"] += 0.1
        elif importance <= 2:  # 低重要度
            adjustments["critical"] -= 0.1
            adjustments["warning"] -= 0.1
            
        # 影響半径（impact radius）: 重要度×変更頻度で重み付け
        impact_radius = 0.0
        freq = context.get("change_frequency", "unknown")
        if freq == "high":
            impact_radius += 0.05
        elif freq == "medium":
            impact_radius += 0.02
        if context["importance_level"] >= 4:
            impact_radius += 0.05
        adjustments["warning"] += impact_radius
        adjustments["target"] += impact_radius / 2

        # プロジェクト段階調整
        phase = context["project_phase"]
        if phase == "production":
            adjustments["critical"] += 0.15
            adjustments["warning"] += 0.15
            adjustments["target"] += 0.1
        elif phase == "development":
            adjustments["critical"] -= 0.05
            adjustments["warning"] -= 0.05
        
        # ファイルサイズ調整
        size = context["size_category"]
        if size in ["large", "very_large"]:
            adjustments["target"] += 0.05  # 大きなファイルは高品質を求める
        elif size == "tiny":
            adjustments["warning"] -= 0.1  # 小さなファイルは緩和
            
        # 複雑性調整
        complexity_hints = context["complexity_hints"]
        if "long_file" in complexity_hints:
            adjustments["target"] += 0.1
        if "deep_nesting" in complexity_hints:
            adjustments["warning"] += 0.05
            
        return adjustments

    def _calculate_drift_adjustments(self, context: Dict[str, Any], base_thresholds: Dict[str, float]) -> Dict[str, float]:
        """ドリフト耐性のための分位点＋EWMAによる自動調整
        - 類似ファイルの直近スコア分布から分位点（q10, q40, q75）を算出
        - それをアンカーにし、(anchor - base) を調整量とする
        - 前回調整（同タイプ）とのEWMAで平滑化
        """
        try:
            similar = self._find_similar_files(context)
            if not similar:
                return {"critical": 0.0, "warning": 0.0, "target": 0.0}

            scores = sorted([r.get("score", 0.0) for r in similar])
            if len(scores) < 5:
                return {"critical": 0.0, "warning": 0.0, "target": 0.0}

            def quantile(arr, q):
                idx = max(0, min(len(arr) - 1, int(q * (len(arr) - 1))))
                return float(arr[idx])

            q10 = quantile(scores, 0.10)
            q40 = quantile(scores, 0.40)
            q75 = quantile(scores, 0.75)

            # アンカー（過去実績ベース）
            anchors = {
                "critical": max(0.05, min(0.7, q10 + 0.05)),
                "warning": max(0.2, min(0.85, q40)),
                "target": max(0.5, min(0.95, q75)),
            }

            raw_adjustments = {
                key: anchors[key] - base_thresholds[key] for key in anchors
            }

            # EWMA平滑化（同ファイルタイプの直近調整とブレンド）
            ft = context.get("file_type", "other")
            recent = [rec for rec in self.learning_data.get("threshold_adjustments", [])
                      if rec.get("context", {}).get("file_type") == ft]
            if recent:
                last = recent[-1].get("thresholds", {})
                smoothed = {}
                alpha = 0.5
                for k in ["critical", "warning", "target"]:
                    prev_delta = last.get(k, base_thresholds[k]) - base_thresholds[k]
                    smoothed[k] = alpha * raw_adjustments[k] + (1 - alpha) * prev_delta
                return smoothed

            return raw_adjustments

        except Exception:
            return {"critical": 0.0, "warning": 0.0, "target": 0.0}
    
    def _calculate_learning_adjustments(self, context: Dict[str, Any]) -> Dict[str, float]:
        """学習ベース調整計算"""
        adjustments = {"critical": 0, "warning": 0, "target": 0}
        
        if not self.performance_history:
            return adjustments
        
        # 類似ファイルの過去パフォーマンス分析
        similar_files = self._find_similar_files(context)
        
        if similar_files:
            scores = [f["score"] for f in similar_files]
            avg_score = statistics.mean(scores)
            
            # 平均スコアが低い場合は閾値を下げる（現実的な基準に）
            if avg_score < 0.6:
                adjustments["critical"] -= 0.05
                adjustments["warning"] -= 0.05
            elif avg_score > 0.8:
                adjustments["target"] += 0.05
                
        return adjustments
    
    def _find_similar_files(self, context: Dict[str, Any]) -> List[Dict]:
        """類似ファイル検索"""
        similar = []
        
        for record in self.performance_history[-50:]:  # 最新50件
            similarity_score = 0
            
            # ファイルタイプが同じ
            if self._get_file_type(record.get("file", "")) == context["file_type"]:
                similarity_score += 2
            
            # 重要度が近い
            record_importance = self._estimate_importance(record.get("file", ""))
            if abs(record_importance - context["importance_level"]) <= 1:
                similarity_score += 1
            
            # 閾値以上で類似とみなす
            if similarity_score >= 2:
                similar.append(record)
                
        return similar[-10:]  # 最新10件まで
    
    def _get_file_type(self, file_path: str) -> str:
        """ファイルタイプ取得（履歴レコード用）"""
        ext = Path(file_path).suffix.lower()
        return ext
    
    def _estimate_importance(self, file_path: str) -> int:
        """重要度推定（履歴レコード用）"""
        analyzer = ContextAnalyzer()
        return analyzer._determine_importance(file_path)
    
    def update_learning_data(self, context: Dict, thresholds: Dict, actual_score: float, gate_result: Dict):
        """学習データ更新"""
        learning_record = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "thresholds": thresholds,
            "actual_score": actual_score,
            "gate_result": gate_result
        }
        
        self.learning_data["threshold_adjustments"].append(learning_record)
        
        # 最新1000件まで保持
        if len(self.learning_data["threshold_adjustments"]) > 1000:
            self.learning_data["threshold_adjustments"] = self.learning_data["threshold_adjustments"][-1000:]
        
        # 統計更新
        self._update_statistics(context, actual_score)
        
        # 保存
        self._save_learning_data()
    
    def _update_statistics(self, context: Dict, score: float):
        """統計情報更新"""
        # ファイルタイプ統計
        file_type = context["file_type"]
        if file_type not in self.learning_data["file_type_stats"]:
            self.learning_data["file_type_stats"][file_type] = {"count": 0, "total_score": 0}
        
        stats = self.learning_data["file_type_stats"][file_type]
        stats["count"] += 1
        stats["total_score"] += score
        stats["avg_score"] = stats["total_score"] / stats["count"]
    
    def _save_learning_data(self):
        """学習データ保存"""
        try:
            os.makedirs("out", exist_ok=True)
            with open("out/gate_learning.json", "w") as f:
                json.dump(self.learning_data, f, indent=2)
        except Exception as e:
            print(f"Learning data save error: {e}")


class DynamicQualityGate:
    """動的品質ゲートメインクラス"""
    
    def __init__(self):
        self.context_analyzer = ContextAnalyzer()
        self.learning_engine = LearningEngine()
        self.gates = self._initialize_gates()
    
    def _initialize_gates(self) -> List[QualityGate]:
        """初期ゲート設定"""
        return [
            QualityGate(
                name="critical_files",
                min_score=0.4,
                warning_score=0.7,
                context="critical",
                file_pattern=r"\.github/|scripts/quality/",
                importance_level=5,
                learning_weight=0.8,
                last_updated=datetime.now()
            ),
            QualityGate(
                name="source_code",
                min_score=0.3,
                warning_score=0.6,
                context="source",
                file_pattern=r"\.(py|js|ts)$",
                importance_level=4,
                learning_weight=0.7,
                last_updated=datetime.now()
            ),
            QualityGate(
                name="configuration",
                min_score=0.5,
                warning_score=0.8,
                context="config",
                file_pattern=r"\.(yml|yaml|json)$",
                importance_level=4,
                learning_weight=0.6,
                last_updated=datetime.now()
            ),
            QualityGate(
                name="documentation",
                min_score=0.2,
                warning_score=0.5,
                context="docs",
                file_pattern=r"\.md$",
                importance_level=2,
                learning_weight=0.3,
                last_updated=datetime.now()
            )
        ]
    
    def evaluate_file(self, file_path: str, quality_score: float) -> Dict[str, Any]:
        """ファイル評価"""
        # コンテキスト分析
        context = self.context_analyzer.analyze_file_context(file_path)
        
        # 動的閾値計算
        thresholds = self.learning_engine.calculate_dynamic_thresholds(context)
        
        # 適用可能ゲート検索
        applicable_gate = self._find_applicable_gate(file_path)
        
        # ゲート評価
        gate_result = self._evaluate_against_gate(
            quality_score, thresholds, applicable_gate, context
        )
        
        # 学習データ更新
        self.learning_engine.update_learning_data(
            context, thresholds, quality_score, gate_result
        )
        
        return gate_result
    
    def _find_applicable_gate(self, file_path: str) -> Optional[QualityGate]:
        """適用可能ゲート検索"""
        for gate in self.gates:
            if re.search(gate.file_pattern, file_path):
                return gate
        return None
    
    def _evaluate_against_gate(self, score: float, thresholds: Dict, 
                              gate: Optional[QualityGate], context: Dict) -> Dict[str, Any]:
        """ゲート評価実行"""
        result = {
            "file": context["file_path"],
            "score": score,
            "context": context,
            "thresholds": thresholds,
            "gate_name": gate.name if gate else "default",
            "timestamp": datetime.now().isoformat()
        }
        
        # ゲート判定
        if score < thresholds["critical"]:
            result["status"] = "blocked"
            result["level"] = "critical" 
            result["message"] = f"Critical quality issue (score: {score:.2f} < {thresholds['critical']:.2f})"
            result["action"] = "immediate_fix_required"
            
        elif score < thresholds["warning"]:
            result["status"] = "warning"
            result["level"] = "warning"
            result["message"] = f"Quality warning (score: {score:.2f} < {thresholds['warning']:.2f})"
            result["action"] = "improvement_recommended"
            
        elif score < thresholds["target"]:
            result["status"] = "passed_with_notes"
            result["level"] = "info"
            result["message"] = f"Acceptable quality (score: {score:.2f} < target: {thresholds['target']:.2f})"
            result["action"] = "monitoring"
            
        else:
            result["status"] = "passed"
            result["level"] = "success"
            result["message"] = f"High quality (score: {score:.2f} >= {thresholds['target']:.2f})"
            result["action"] = "none"
        
        # 推奨アクション生成
        result["recommendations"] = self._generate_recommendations(result)
        
        return result
    
    def _generate_recommendations(self, result: Dict) -> List[str]:
        """推奨アクション生成"""
        recommendations = []
        
        context = result["context"]
        score = result["score"]
        level = result["level"]
        
        if level == "critical":
            recommendations.append("🚨 Immediate attention required")
            recommendations.append("Consider rollback if this is a regression")
            
            if context["importance_level"] >= 4:
                recommendations.append("This is a critical file - review carefully")
            
        elif level == "warning":
            recommendations.append("⚠️ Quality improvement needed")
            
            complexity_hints = context["complexity_hints"]
            if "long_file" in complexity_hints:
                recommendations.append("Consider breaking down this large file")
            if "deep_nesting" in complexity_hints:
                recommendations.append("Reduce nesting complexity")
                
        elif level == "info":
            recommendations.append("ℹ️ Minor improvements possible")
            
        # ファイルタイプ別推奨
        file_type = context["file_type"]
        if file_type == "yaml" and score < 0.8:
            recommendations.append("Run yamllint for specific issues")
        elif file_type == "python" and score < 0.7:
            recommendations.append("Consider adding docstrings and comments")
            
        return recommendations[:3]  # 最大3つまで
    
    def get_gate_summary(self) -> Dict[str, Any]:
        """ゲートサマリー取得"""
        return {
            "total_gates": len(self.gates),
            "learning_data_points": len(self.learning_engine.learning_data.get("threshold_adjustments", [])),
            "file_type_coverage": len(self.learning_engine.learning_data.get("file_type_stats", {})),
            "last_updated": max([g.last_updated for g in self.gates]).isoformat(),
            "gate_names": [g.name for g in self.gates]
        }


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="🎛️ Dynamic Quality Gates")
    parser.add_argument("--file", "-f", help="File to evaluate")
    parser.add_argument("--score", "-s", type=float, default=0.75, help="Quality score")
    parser.add_argument("--summary", action="store_true", help="Show gate summary")
    parser.add_argument("--test", action="store_true", help="Run test mode")
    
    args = parser.parse_args()
    
    gate_system = DynamicQualityGate()
    
    if args.summary:
        # サマリー表示
        summary = gate_system.get_gate_summary()
        print("🎛️ Dynamic Quality Gates Summary")
        print("=" * 40)
        for key, value in summary.items():
            print(f"{key}: {value}")
            
    elif args.test:
        # テストモード
        print("🧪 Dynamic Quality Gates Test")
        print("=" * 35)
        
        test_files = [
            {"file": ".github/workflows/pr-quality-check.yml", "score": 0.9},
            {"file": "scripts/quality/tag_failures.py", "score": 0.6},
            {"file": "README.md", "score": 0.4},
            {"file": "experimental/test.py", "score": 0.3}
        ]
        
        for test_case in test_files:
            print(f"\\nTesting: {test_case['file']}")
            result = gate_system.evaluate_file(test_case["file"], test_case["score"])
            
            print(f"Status: {result['status']} ({result['level']})")
            print(f"Message: {result['message']}")
            print(f"Action: {result['action']}")
            
            if result["recommendations"]:
                print("Recommendations:")
                for rec in result["recommendations"]:
                    print(f"  • {rec}")
                    
    elif args.file:
        # 実際のファイル評価
        result = gate_system.evaluate_file(args.file, args.score)
        
        print(f"🎛️ Quality Gate Result for {args.file}")
        print("=" * 50)
        print(f"Score: {result['score']:.2f}")
        print(f"Status: {result['status']} ({result['level']})")
        print(f"Gate: {result['gate_name']}")
        print(f"Message: {result['message']}")
        print(f"Action: {result['action']}")
        
        if result["recommendations"]:
            print("\\nRecommendations:")
            for rec in result["recommendations"]:
                print(f"  • {rec}")
        
        # 閾値情報
        thresholds = result["thresholds"]
        print(f"\\nDynamic Thresholds:")
        print(f"  Critical: {thresholds['critical']:.2f}")
        print(f"  Warning:  {thresholds['warning']:.2f}")
        print(f"  Target:   {thresholds['target']:.2f}")
        
    else:
        print("❌ Please specify --file, --summary, or --test")
        parser.print_help()


if __name__ == "__main__":
    main()




