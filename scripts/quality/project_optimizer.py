#!/usr/bin/env python3
"""
🎯 Phase 4: プロジェクト特性別推奨システム
=====================================

プロジェクト種別・重要度を自動分析し、コンテキスト適応型品質基準で
ビジネス価値連動の優先順位付けを行うプロジェクト最適化システム

主要機能:
- プロジェクト特性自動分析
- コンテキスト適応品質基準
- ビジネス価値評価
- 優先順位付け最適化
- プロジェクト別推奨生成
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re
import yaml


@dataclass
class ProjectProfile:
    """プロジェクトプロファイルデータクラス"""
    project_id: str
    project_type: str  # "library", "web_app", "api", "cli_tool", "data_science", "devops"
    business_criticality: str  # "low", "medium", "high", "critical"
    development_phase: str  # "prototype", "development", "testing", "production", "maintenance"
    team_size: int
    technology_stack: List[str]
    deployment_frequency: str  # "daily", "weekly", "monthly", "quarterly"
    user_impact_scale: str  # "internal", "team", "organization", "public"
    quality_requirements: Dict[str, float]
    last_updated: datetime


@dataclass
class ProjectRecommendation:
    """プロジェクト推奨データクラス"""
    project_id: str
    recommendation_type: str
    priority_level: int  # 1-5
    business_impact: float
    technical_impact: float
    effort_required: str
    title: str
    description: str
    implementation_steps: List[str]
    success_metrics: List[str]
    timeline: str
    dependencies: List[str]
    risk_factors: List[str]


class ProjectAnalysisEngine:
    """プロジェクト分析エンジン"""
    
    def __init__(self):
        self.base_dir = Path(".")
        self.analysis_patterns = self._load_analysis_patterns()
    
    def _load_analysis_patterns(self) -> Dict[str, Any]:
        """分析パターン読み込み"""
        return {
            "project_type_indicators": {
                "library": {
                    "files": ["setup.py", "pyproject.toml", "__init__.py"],
                    "patterns": [r"import.*", r"class.*", r"def.*"],
                    "directories": ["src", "lib", "tests"]
                },
                "web_app": {
                    "files": ["app.py", "main.py", "wsgi.py", "asgi.py"],
                    "patterns": [r"@app\.route", r"FastAPI", r"Flask", r"Django"],
                    "directories": ["templates", "static", "views"]
                },
                "api": {
                    "files": ["api.py", "server.py", "endpoints.py"],
                    "patterns": [r"@api\.", r"/api/", r"REST", r"GraphQL"],
                    "directories": ["api", "endpoints", "routes"]
                },
                "cli_tool": {
                    "files": ["cli.py", "main.py", "__main__.py"],
                    "patterns": [r"argparse", r"click", r"typer", r"if __name__"],
                    "directories": ["cli", "commands"]
                },
                "data_science": {
                    "files": ["*.ipynb", "*.py"],
                    "patterns": [r"pandas", r"numpy", r"sklearn", r"tensorflow", r"pytorch"],
                    "directories": ["data", "notebooks", "models"]
                },
                "devops": {
                    "files": ["Dockerfile", "docker-compose.yml", "*.yml"],
                    "patterns": [r"FROM", r"RUN", r"actions/", r"workflow"],
                    "directories": [".github", "docker", "k8s", "terraform"]
                }
            },
            "business_criticality_indicators": {
                "critical": {
                    "keywords": ["production", "live", "critical", "main", "master"],
                    "files": ["deploy.yml", "production.yml", "Dockerfile"],
                    "patterns": [r"prod", r"live", r"critical"]
                },
                "high": {
                    "keywords": ["api", "server", "service", "core"],
                    "files": ["server.py", "api.py", "service.py"],
                    "patterns": [r"server", r"service", r"api"]
                },
                "medium": {
                    "keywords": ["tool", "utility", "helper", "lib"],
                    "files": ["tool.py", "util.py", "helper.py"],
                    "patterns": [r"tool", r"util", r"helper"]
                },
                "low": {
                    "keywords": ["test", "demo", "example", "prototype"],
                    "files": ["test.py", "demo.py", "example.py"],
                    "patterns": [r"test", r"demo", r"example"]
                }
            }
        }
    
    def analyze_project(self, project_path: str = ".") -> ProjectProfile:
        """プロジェクト分析実行"""
        print(f"🎯 プロジェクト分析開始: {project_path}")
        
        project_id = Path(project_path).name
        project_type = self._determine_project_type(project_path)
        business_criticality = self._assess_business_criticality(project_path)
        development_phase = self._determine_development_phase(project_path)
        team_size = self._estimate_team_size(project_path)
        technology_stack = self._identify_technology_stack(project_path)
        deployment_frequency = self._analyze_deployment_frequency(project_path)
        user_impact_scale = self._assess_user_impact_scale(project_path)
        quality_requirements = self._determine_quality_requirements(
            project_type, business_criticality, development_phase
        )
        
        profile = ProjectProfile(
            project_id=project_id,
            project_type=project_type,
            business_criticality=business_criticality,
            development_phase=development_phase,
            team_size=team_size,
            technology_stack=technology_stack,
            deployment_frequency=deployment_frequency,
            user_impact_scale=user_impact_scale,
            quality_requirements=quality_requirements,
            last_updated=datetime.now()
        )
        
        print(f"✅ プロジェクト分析完了: {project_type} ({business_criticality} criticality)")
        return profile
    
    def _determine_project_type(self, project_path: str) -> str:
        """プロジェクトタイプ判定"""
        path = Path(project_path)
        
        # ファイルとディレクトリの存在確認
        for proj_type, indicators in self.analysis_patterns["project_type_indicators"].items():
            score = 0
            
            # ファイル存在チェック
            for file_pattern in indicators["files"]:
                if "*" in file_pattern:
                    # ワイルドカード対応
                    pattern = file_pattern.replace("*", "")
                    matching_files = list(path.rglob(f"*{pattern}"))
                    if matching_files:
                        score += 2
                else:
                    if (path / file_pattern).exists():
                        score += 2
            
            # ディレクトリ存在チェック
            for dir_name in indicators["directories"]:
                if (path / dir_name).exists():
                    score += 1
            
            # パターンマッチング（ファイル内容）
            for pattern in indicators["patterns"]:
                if self._search_pattern_in_files(path, pattern):
                    score += 1
            
            # 暫定的な閾値判定
            if score >= 3:
                return proj_type
        
        return "general"  # デフォルト
    
    def _search_pattern_in_files(self, path: Path, pattern: str) -> bool:
        """ファイル内のパターン検索"""
        try:
            for file_path in path.rglob("*.py"):
                if file_path.is_file() and file_path.stat().st_size < 100000:  # 100KB以下のファイルのみ
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if re.search(pattern, content, re.IGNORECASE):
                                return True
                    except:
                        continue
            return False
        except:
            return False
    
    def _assess_business_criticality(self, project_path: str) -> str:
        """ビジネス重要度評価"""
        path = Path(project_path)
        
        for criticality, indicators in self.analysis_patterns["business_criticality_indicators"].items():
            score = 0
            
            # キーワードチェック
            project_name = path.name.lower()
            for keyword in indicators["keywords"]:
                if keyword in project_name:
                    score += 2
            
            # ファイル存在チェック
            for file_name in indicators["files"]:
                if (path / file_name).exists():
                    score += 2
            
            # パターンマッチング
            for pattern in indicators["patterns"]:
                if self._search_pattern_in_files(path, pattern):
                    score += 1
            
            if score >= 3:
                return criticality
        
        return "medium"  # デフォルト
    
    def _determine_development_phase(self, project_path: str) -> str:
        """開発段階判定"""
        path = Path(project_path)
        
        # 判定指標
        has_tests = bool(list(path.rglob("test*.py")))
        has_docs = bool(list(path.rglob("README*"))) or bool(list(path.rglob("docs/*")))
        has_ci = (path / ".github" / "workflows").exists()
        has_deployment = bool(list(path.rglob("deploy*"))) or bool(list(path.rglob("Dockerfile")))
        has_version = (path / "setup.py").exists() or (path / "pyproject.toml").exists()
        
        # 段階判定
        if has_deployment and has_ci and has_tests and has_docs:
            return "production"
        elif has_ci and has_tests:
            return "testing"
        elif has_tests or has_docs or has_version:
            return "development"
        else:
            return "prototype"
    
    def _estimate_team_size(self, project_path: str) -> int:
        """チームサイズ推定"""
        try:
            import git
            repo = git.Repo(project_path)
            
            # Git コントリビュータ数から推定
            contributors = set()
            for commit in repo.iter_commits(max_count=100):
                contributors.add(commit.author.email)
            
            return max(1, len(contributors))
        except:
            return 1  # デフォルト
    
    def _identify_technology_stack(self, project_path: str) -> List[str]:
        """技術スタック特定"""
        path = Path(project_path)
        tech_stack = []
        
        # Python環境
        if (path / "requirements.txt").exists() or (path / "setup.py").exists():
            tech_stack.append("Python")
        
        # JavaScript/Node.js
        if (path / "package.json").exists():
            tech_stack.append("Node.js")
        
        # Docker
        if (path / "Dockerfile").exists():
            tech_stack.append("Docker")
        
        # GitHub Actions
        if (path / ".github" / "workflows").exists():
            tech_stack.append("GitHub Actions")
        
        # YAML設定
        yaml_files = list(path.rglob("*.yml")) + list(path.rglob("*.yaml"))
        if yaml_files:
            tech_stack.append("YAML")
        
        return tech_stack if tech_stack else ["Unknown"]
    
    def _analyze_deployment_frequency(self, project_path: str) -> str:
        """デプロイ頻度分析"""
        try:
            import git
            repo = git.Repo(project_path)
            
            # 直近のコミット頻度から推定
            recent_commits = []
            for commit in repo.iter_commits(max_count=50):
                if commit.committed_datetime.replace(tzinfo=None) > datetime.now() - timedelta(days=30):
                    recent_commits.append(commit)
            
            commits_per_week = len(recent_commits) / 4.0  # 月を4週として計算
            
            if commits_per_week >= 7:
                return "daily"
            elif commits_per_week >= 2:
                return "weekly"
            elif commits_per_week >= 0.5:
                return "monthly"
            else:
                return "quarterly"
        except:
            return "monthly"  # デフォルト
    
    def _assess_user_impact_scale(self, project_path: str) -> str:
        """ユーザー影響規模評価"""
        path = Path(project_path)
        
        # 公開指標
        if (path / "setup.py").exists() or (path / "pyproject.toml").exists():
            return "public"
        
        # 組織レベル指標
        if any(keyword in path.name.lower() for keyword in ["api", "service", "core", "main"]):
            return "organization"
        
        # チームレベル指標
        if any(keyword in path.name.lower() for keyword in ["tool", "utility", "lib", "helper"]):
            return "team"
        
        return "internal"  # デフォルト
    
    def _determine_quality_requirements(self, project_type: str, business_criticality: str, development_phase: str) -> Dict[str, float]:
        """品質要件決定"""
        base_requirements = {
            "code_coverage": 0.7,
            "documentation": 0.6,
            "error_handling": 0.7,
            "performance": 0.6,
            "security": 0.7,
            "maintainability": 0.7
        }
        
        # プロジェクトタイプによる調整
        type_adjustments = {
            "library": {"documentation": 0.2, "maintainability": 0.1},
            "api": {"performance": 0.2, "security": 0.2, "error_handling": 0.1},
            "web_app": {"performance": 0.1, "security": 0.2},
            "cli_tool": {"error_handling": 0.1, "documentation": 0.1},
            "data_science": {"documentation": 0.1, "performance": 0.1},
            "devops": {"security": 0.2, "error_handling": 0.2}
        }
        
        # ビジネス重要度による調整
        criticality_multipliers = {
            "critical": 1.3,
            "high": 1.2,
            "medium": 1.0,
            "low": 0.8
        }
        
        # 開発段階による調整
        phase_adjustments = {
            "production": {"security": 0.2, "performance": 0.1, "error_handling": 0.2},
            "testing": {"code_coverage": 0.1, "documentation": 0.1},
            "development": {},
            "prototype": {"code_coverage": -0.2, "documentation": -0.1}
        }
        
        # 調整適用
        adjusted_requirements = base_requirements.copy()
        
        # タイプ調整
        if project_type in type_adjustments:
            for key, adjustment in type_adjustments[project_type].items():
                adjusted_requirements[key] += adjustment
        
        # 重要度調整
        multiplier = criticality_multipliers.get(business_criticality, 1.0)
        for key in adjusted_requirements:
            adjusted_requirements[key] *= multiplier
        
        # 段階調整
        if development_phase in phase_adjustments:
            for key, adjustment in phase_adjustments[development_phase].items():
                adjusted_requirements[key] += adjustment
        
        # 範囲制限
        for key in adjusted_requirements:
            adjusted_requirements[key] = max(0.0, min(1.0, adjusted_requirements[key]))
        
        return adjusted_requirements


class ProjectOptimizationEngine:
    """プロジェクト最適化エンジン"""
    
    def __init__(self):
        self.optimization_strategies = self._load_optimization_strategies()
    
    def _load_optimization_strategies(self) -> Dict[str, Any]:
        """最適化戦略読み込み"""
        return {
            "library": {
                "high_priority": ["documentation", "maintainability", "api_design"],
                "medium_priority": ["testing", "performance"],
                "low_priority": ["ui", "deployment"]
            },
            "web_app": {
                "high_priority": ["performance", "security", "user_experience"],
                "medium_priority": ["testing", "maintainability"],
                "low_priority": ["documentation"]
            },
            "api": {
                "high_priority": ["performance", "security", "error_handling"],
                "medium_priority": ["documentation", "testing"],
                "low_priority": ["ui"]
            },
            "cli_tool": {
                "high_priority": ["error_handling", "user_experience", "documentation"],
                "medium_priority": ["testing", "maintainability"],
                "low_priority": ["performance"]
            },
            "data_science": {
                "high_priority": ["documentation", "reproducibility", "data_validation"],
                "medium_priority": ["performance", "maintainability"],
                "low_priority": ["security"]
            },
            "devops": {
                "high_priority": ["security", "reliability", "monitoring"],
                "medium_priority": ["maintainability", "documentation"],
                "low_priority": ["performance"]
            }
        }
    
    def generate_project_recommendations(self, profile: ProjectProfile) -> List[ProjectRecommendation]:
        """プロジェクト推奨生成"""
        recommendations = []
        
        # プロジェクトタイプ別最適化戦略取得
        strategies = self.optimization_strategies.get(profile.project_type, 
                                                     self.optimization_strategies["library"])
        
        # 高優先度推奨
        for i, area in enumerate(strategies["high_priority"], 1):
            rec = self._create_high_priority_recommendation(profile, area, i)
            if rec:
                recommendations.append(rec)
        
        # 中優先度推奨
        for i, area in enumerate(strategies["medium_priority"], len(strategies["high_priority"]) + 1):
            rec = self._create_medium_priority_recommendation(profile, area, i)
            if rec:
                recommendations.append(rec)
        
        # ビジネス重要度に応じた追加推奨
        if profile.business_criticality in ["critical", "high"]:
            critical_rec = self._create_critical_business_recommendation(profile)
            if critical_rec:
                recommendations.insert(0, critical_rec)  # 最優先に挿入
        
        return recommendations[:10]  # 上位10個まで
    
    def _create_high_priority_recommendation(self, profile: ProjectProfile, area: str, priority: int) -> Optional[ProjectRecommendation]:
        """高優先度推奨作成"""
        templates = {
            "documentation": {
                "title": f"{profile.project_type}プロジェクトのドキュメント強化",
                "description": "ユーザビリティとメンテナンス性向上のための包括的ドキュメント整備",
                "steps": [
                    "README.md の詳細化（インストール、使用方法、例）",
                    "API ドキュメントの自動生成設定",
                    "コードコメント・docstring の充実",
                    "コントリビューションガイドライン作成"
                ],
                "timeline": "2-3週間",
                "business_impact": 0.8,
                "technical_impact": 0.7
            },
            "performance": {
                "title": f"{profile.project_type}のパフォーマンス最適化",
                "description": "ユーザーエクスペリエンス向上のためのパフォーマンス改善",
                "steps": [
                    "パフォーマンスベンチマーク設定",
                    "ボトルネック分析・特定",
                    "最適化実装（キャッシュ、並列処理等）",
                    "パフォーマンス監視の継続化"
                ],
                "timeline": "3-4週間",
                "business_impact": 0.9,
                "technical_impact": 0.8
            },
            "security": {
                "title": f"{profile.project_type}のセキュリティ強化",
                "description": "セキュリティリスク軽減とコンプライアンス確保",
                "steps": [
                    "セキュリティ監査・脆弱性スキャン実行",
                    "認証・認可機能の強化",
                    "入力値検証・サニタイズ改善",
                    "セキュリティ監視・ログ強化"
                ],
                "timeline": "4-6週間",
                "business_impact": 1.0,
                "technical_impact": 0.9
            },
            "maintainability": {
                "title": f"{profile.project_type}のメンテナンス性向上",
                "description": "長期的な開発効率とコード品質の改善",
                "steps": [
                    "コード構造のリファクタリング",
                    "自動テストカバレッジ向上",
                    "CI/CD パイプライン最適化",
                    "コード品質メトリクス導入"
                ],
                "timeline": "3-5週間",
                "business_impact": 0.7,
                "technical_impact": 0.9
            },
            "error_handling": {
                "title": f"{profile.project_type}のエラーハンドリング改善",
                "description": "堅牢性向上とユーザーエクスペリエンス改善",
                "steps": [
                    "エラーケース分析・特定",
                    "包括的例外処理実装",
                    "ユーザーフレンドリーなエラーメッセージ",
                    "エラー監視・アラート設定"
                ],
                "timeline": "2-3週間",
                "business_impact": 0.8,
                "technical_impact": 0.8
            }
        }
        
        if area not in templates:
            return None
        
        template = templates[area]
        
        return ProjectRecommendation(
            project_id=profile.project_id,
            recommendation_type=area,
            priority_level=priority,
            business_impact=template["business_impact"],
            technical_impact=template["technical_impact"],
            effort_required=self._determine_effort_level(template["timeline"]),
            title=template["title"],
            description=template["description"],
            implementation_steps=template["steps"],
            success_metrics=self._generate_success_metrics(area, profile),
            timeline=template["timeline"],
            dependencies=self._determine_dependencies(area, profile),
            risk_factors=self._identify_risk_factors(area, profile)
        )
    
    def _create_medium_priority_recommendation(self, profile: ProjectProfile, area: str, priority: int) -> Optional[ProjectRecommendation]:
        """中優先度推奨作成"""
        # 簡略版テンプレート
        templates = {
            "testing": {
                "title": "テスト戦略の改善",
                "description": "品質保証とリグレッション防止",
                "timeline": "2-4週間",
                "business_impact": 0.6,
                "technical_impact": 0.8
            },
            "monitoring": {
                "title": "監視・ログシステム導入",
                "description": "運用可視性の向上",
                "timeline": "3-4週間",
                "business_impact": 0.7,
                "technical_impact": 0.7
            }
        }
        
        if area not in templates:
            return None
        
        template = templates[area]
        
        return ProjectRecommendation(
            project_id=profile.project_id,
            recommendation_type=area,
            priority_level=priority,
            business_impact=template["business_impact"],
            technical_impact=template["technical_impact"],
            effort_required=self._determine_effort_level(template["timeline"]),
            title=template["title"],
            description=template["description"],
            implementation_steps=[f"{area}の改善実装"],
            success_metrics=[f"{area}指標の改善"],
            timeline=template["timeline"],
            dependencies=[],
            risk_factors=[]
        )
    
    def _create_critical_business_recommendation(self, profile: ProjectProfile) -> ProjectRecommendation:
        """ビジネス重要推奨作成"""
        return ProjectRecommendation(
            project_id=profile.project_id,
            recommendation_type="business_critical",
            priority_level=1,
            business_impact=1.0,
            technical_impact=0.9,
            effort_required="高",
            title=f"ビジネス重要プロジェクト最優先対応",
            description=f"{profile.business_criticality}重要度プロジェクトの緊急品質向上",
            implementation_steps=[
                "緊急品質監査の実施",
                "高優先度問題の即座修正",
                "24/7 監視体制の確立",
                "エスカレーション手順の整備"
            ],
            success_metrics=[
                "ダウンタイム ゼロ達成",
                "品質メトリクス 90% 以上",
                "ユーザー満足度向上"
            ],
            timeline="1-2週間",
            dependencies=["ステークホルダー承認", "リソース確保"],
            risk_factors=["高負荷による他作業への影響", "スケジュール遅延リスク"]
        )
    
    def _determine_effort_level(self, timeline: str) -> str:
        """工数レベル決定"""
        if "1" in timeline or "2週間" in timeline:
            return "低"
        elif "3" in timeline or "4週間" in timeline:
            return "中"
        else:
            return "高"
    
    def _generate_success_metrics(self, area: str, profile: ProjectProfile) -> List[str]:
        """成功指標生成"""
        metrics_map = {
            "documentation": ["ドキュメントカバレッジ 80% 以上", "ユーザーフィードバック改善"],
            "performance": ["レスポンス時間 50% 向上", "スループット向上"],
            "security": ["脆弱性ゼロ達成", "セキュリティスコア向上"],
            "maintainability": ["技術的負債削減", "開発速度向上"],
            "error_handling": ["エラー率 50% 削減", "ユーザー体験向上"]
        }
        
        return metrics_map.get(area, [f"{area}関連指標の改善"])
    
    def _determine_dependencies(self, area: str, profile: ProjectProfile) -> List[str]:
        """依存関係決定"""
        dependencies_map = {
            "security": ["セキュリティ専門家レビュー", "コンプライアンス確認"],
            "performance": ["パフォーマンス測定環境", "ベンチマークツール"],
            "documentation": ["技術ライター協力（オプション）"]
        }
        
        return dependencies_map.get(area, [])
    
    def _identify_risk_factors(self, area: str, profile: ProjectProfile) -> List[str]:
        """リスク要因特定"""
        risks_map = {
            "security": ["既存機能への影響", "パフォーマンス劣化リスク"],
            "performance": ["最適化による複雑性増加", "新規バグ導入リスク"],
            "maintainability": ["大規模リファクタリングのリスク"]
        }
        
        return risks_map.get(area, ["実装時間超過リスク"])


class ProjectOptimizationSystem:
    """プロジェクト最適化システム メインクラス"""
    
    def __init__(self):
        self.analysis_engine = ProjectAnalysisEngine()
        self.optimization_engine = ProjectOptimizationEngine()
    
    def optimize_project(self, project_path: str = ".") -> Dict[str, Any]:
        """プロジェクト最適化実行"""
        print(f"🎯 プロジェクト特性別最適化開始: {project_path}")
        
        # プロジェクト分析
        profile = self.analysis_engine.analyze_project(project_path)
        
        # 最適化推奨生成
        recommendations = self.optimization_engine.generate_project_recommendations(profile)
        
        # 結果構造化
        result = {
            "project_profile": {
                "id": profile.project_id,
                "type": profile.project_type,
                "business_criticality": profile.business_criticality,
                "development_phase": profile.development_phase,
                "team_size": profile.team_size,
                "technology_stack": profile.technology_stack,
                "deployment_frequency": profile.deployment_frequency,
                "user_impact_scale": profile.user_impact_scale,
                "quality_requirements": profile.quality_requirements
            },
            "optimization_recommendations": [
                self._rec_to_dict(rec) for rec in recommendations
            ],
            "priority_summary": self._create_priority_summary(recommendations),
            "business_impact_analysis": self._analyze_business_impact(recommendations),
            "implementation_roadmap": self._create_implementation_roadmap(recommendations),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        # 結果保存
        self._save_results(result)
        
        return result
    
    def _rec_to_dict(self, rec: ProjectRecommendation) -> Dict[str, Any]:
        """推奨を辞書形式に変換"""
        return {
            "priority": rec.priority_level,
            "type": rec.recommendation_type,
            "title": rec.title,
            "description": rec.description,
            "business_impact": rec.business_impact,
            "technical_impact": rec.technical_impact,
            "effort_required": rec.effort_required,
            "timeline": rec.timeline,
            "implementation_steps": rec.implementation_steps,
            "success_metrics": rec.success_metrics,
            "dependencies": rec.dependencies,
            "risk_factors": rec.risk_factors
        }
    
    def _create_priority_summary(self, recommendations: List[ProjectRecommendation]) -> Dict[str, Any]:
        """優先順位サマリー作成"""
        high_priority = [r for r in recommendations if r.priority_level <= 3]
        medium_priority = [r for r in recommendations if 4 <= r.priority_level <= 6]
        low_priority = [r for r in recommendations if r.priority_level > 6]
        
        return {
            "high_priority_count": len(high_priority),
            "medium_priority_count": len(medium_priority),
            "low_priority_count": len(low_priority),
            "immediate_action_required": len([r for r in recommendations if r.recommendation_type == "business_critical"])
        }
    
    def _analyze_business_impact(self, recommendations: List[ProjectRecommendation]) -> Dict[str, Any]:
        """ビジネス影響分析"""
        if not recommendations:
            return {"total_impact": 0, "high_impact_items": 0}
        
        total_impact = sum(r.business_impact for r in recommendations)
        high_impact_items = len([r for r in recommendations if r.business_impact >= 0.8])
        
        return {
            "total_business_impact": round(total_impact, 2),
            "average_impact": round(total_impact / len(recommendations), 2),
            "high_impact_items": high_impact_items,
            "roi_potential": "高" if total_impact > 5.0 else "中" if total_impact > 3.0 else "低"
        }
    
    def _create_implementation_roadmap(self, recommendations: List[ProjectRecommendation]) -> List[Dict[str, Any]]:
        """実装ロードマップ作成"""
        roadmap = []
        
        # 優先度順にソート
        sorted_recs = sorted(recommendations, key=lambda x: x.priority_level)
        
        current_week = 1
        for rec in sorted_recs[:5]:  # 上位5個
            # タイムライン解析
            weeks = self._parse_timeline(rec.timeline)
            
            roadmap.append({
                "phase": f"Phase {rec.priority_level}",
                "weeks": f"{current_week}-{current_week + weeks - 1}",
                "title": rec.title,
                "effort": rec.effort_required,
                "expected_outcome": rec.success_metrics[0] if rec.success_metrics else "改善達成"
            })
            
            current_week += weeks
        
        return roadmap
    
    def _parse_timeline(self, timeline: str) -> int:
        """タイムライン解析（週数）"""
        if "週間" in timeline:
            # "2-3週間" から最大値を抽出
            weeks = re.findall(r'(\d+)', timeline)
            if weeks:
                return int(weeks[-1])  # 最後の数値（最大値）
        return 2  # デフォルト
    
    def _save_results(self, result: Dict[str, Any]):
        """結果保存"""
        try:
            os.makedirs("out", exist_ok=True)
            with open("out/project_optimization.json", "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"結果保存エラー: {e}")
    
    def display_results(self, result: Dict[str, Any]):
        """結果表示"""
        profile = result["project_profile"]
        recommendations = result["optimization_recommendations"]
        priority_summary = result["priority_summary"]
        business_impact = result["business_impact_analysis"]
        
        print("\n🎯 プロジェクト特性別最適化結果")
        print("=" * 50)
        
        print(f"📊 プロジェクトプロファイル:")
        print(f"   プロジェクト: {profile['id']}")
        print(f"   タイプ: {profile['type']}")
        print(f"   重要度: {profile['business_criticality']}")
        print(f"   段階: {profile['development_phase']}")
        print(f"   チームサイズ: {profile['team_size']}人")
        print(f"   技術スタック: {', '.join(profile['technology_stack'])}")
        
        print(f"\n💎 ビジネス影響分析:")
        print(f"   総合ビジネス影響: {business_impact['total_business_impact']}")
        print(f"   ROI ポテンシャル: {business_impact['roi_potential']}")
        print(f"   高影響項目: {business_impact['high_impact_items']}個")
        
        print(f"\n🚀 優先順位サマリー:")
        print(f"   高優先度: {priority_summary['high_priority_count']}個")
        print(f"   中優先度: {priority_summary['medium_priority_count']}個")
        print(f"   緊急対応: {priority_summary['immediate_action_required']}個")
        
        print(f"\n🏆 トップ5推奨項目:")
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"   {i}. {rec['title']}")
            print(f"      影響度: ビジネス{rec['business_impact']:.1f}/技術{rec['technical_impact']:.1f}, 工数: {rec['effort_required']}")


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="🎯 Project Optimization System")
    parser.add_argument("--path", "-p", default=".", help="Project path to analyze")
    parser.add_argument("--display-only", action="store_true", help="Display last optimization result")
    
    args = parser.parse_args()
    
    system = ProjectOptimizationSystem()
    
    if args.display_only:
        try:
            with open("out/project_optimization.json") as f:
                result = json.load(f)
                system.display_results(result)
        except:
            print("❌ 保存された最適化結果が見つかりません")
    else:
        result = system.optimize_project(args.path)
        system.display_results(result)


if __name__ == "__main__":
    main()

