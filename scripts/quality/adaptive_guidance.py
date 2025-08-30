#!/usr/bin/env python3
"""
🎓 Phase 4: 開発者スキル適応ガイダンス
=================================

開発者のスキルレベルを自動判定し、レベル別の適切な指導・提案を提供、
学習進捗に応じた難易度調整を行うアダプティブガイダンスシステム

主要機能:
- スキルレベル自動判定
- パーソナライズドガイダンス
- 学習進捗追跡
- 適応的難易度調整
- 成長経路推奨
"""

import os
import sys
import json
import git
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re
import statistics


@dataclass
class DeveloperProfile:
    """開発者プロファイルデータクラス"""
    developer_id: str
    skill_level: str  # "beginner", "intermediate", "advanced", "expert"
    experience_months: int
    specializations: List[str]
    learning_preferences: Dict[str, Any]
    recent_activity: Dict[str, Any]
    growth_areas: List[str]
    strengths: List[str]
    last_updated: datetime


@dataclass
class GuidanceRecommendation:
    """ガイダンス推奨データクラス"""
    developer_id: str
    skill_level: str
    issue_type: str
    guidance_type: str  # "tutorial", "reference", "practice", "mentoring"
    title: str
    description: str
    detailed_steps: List[str]
    difficulty_level: int  # 1-5
    estimated_time: int  # minutes
    learning_objectives: List[str]
    follow_up_actions: List[str]
    resources: List[Dict[str, str]]


class SkillAssessmentEngine:
    """スキル評価エンジン"""
    
    def __init__(self):
        self.base_dir = Path(".")
        self.git_repo = self._initialize_git_repo()
        self.skill_indicators = {
            "code_quality": {
                "docstring_usage": {"weight": 0.15, "expert_threshold": 0.8},
                "function_complexity": {"weight": 0.20, "expert_threshold": 0.7},
                "error_handling": {"weight": 0.15, "expert_threshold": 0.8},
                "naming_conventions": {"weight": 0.10, "expert_threshold": 0.9}
            },
            "git_proficiency": {
                "commit_frequency": {"weight": 0.10, "expert_threshold": 0.7},
                "commit_quality": {"weight": 0.15, "expert_threshold": 0.8},
                "branching_strategy": {"weight": 0.10, "expert_threshold": 0.6}
            },
            "problem_solving": {
                "fix_success_rate": {"weight": 0.20, "expert_threshold": 0.85},
                "issue_resolution_time": {"weight": 0.15, "expert_threshold": 0.7}
            }
        }
    
    def _initialize_git_repo(self) -> Optional[git.Repo]:
        """Git リポジトリ初期化"""
        try:
            return git.Repo(".")
        except:
            return None
    
    def assess_developer_skill(self, developer_id: str = "default") -> DeveloperProfile:
        """開発者スキル評価"""
        print(f"🎯 開発者スキル評価開始: {developer_id}")
        
        # 各スキル領域の評価
        code_quality_score = self._assess_code_quality()
        git_proficiency_score = self._assess_git_proficiency()
        problem_solving_score = self._assess_problem_solving()
        
        # 総合スキルレベル判定
        overall_score = (
            code_quality_score * 0.4 +
            git_proficiency_score * 0.3 +
            problem_solving_score * 0.3
        )
        
        skill_level = self._determine_skill_level(overall_score)
        experience_months = self._estimate_experience()
        specializations = self._identify_specializations()
        learning_preferences = self._analyze_learning_preferences()
        recent_activity = self._analyze_recent_activity()
        growth_areas = self._identify_growth_areas(code_quality_score, git_proficiency_score, problem_solving_score)
        strengths = self._identify_strengths(code_quality_score, git_proficiency_score, problem_solving_score)
        
        profile = DeveloperProfile(
            developer_id=developer_id,
            skill_level=skill_level,
            experience_months=experience_months,
            specializations=specializations,
            learning_preferences=learning_preferences,
            recent_activity=recent_activity,
            growth_areas=growth_areas,
            strengths=strengths,
            last_updated=datetime.now()
        )
        
        print(f"✅ スキル評価完了: レベル={skill_level}, 経験={experience_months}ヶ月")
        return profile
    
    def _assess_code_quality(self) -> float:
        """コード品質評価"""
        score = 0.0
        
        try:
            # Python ファイルからコード品質指標を分析
            python_files = list(Path(".").rglob("*.py"))
            if not python_files:
                return 0.5  # デフォルト
            
            # docstring 使用率
            docstring_score = self._analyze_docstring_usage(python_files)
            score += docstring_score * self.skill_indicators["code_quality"]["docstring_usage"]["weight"]
            
            # 関数複雑度
            complexity_score = self._analyze_function_complexity(python_files)
            score += complexity_score * self.skill_indicators["code_quality"]["function_complexity"]["weight"]
            
            # エラーハンドリング
            error_handling_score = self._analyze_error_handling(python_files)
            score += error_handling_score * self.skill_indicators["code_quality"]["error_handling"]["weight"]
            
            # 命名規則
            naming_score = self._analyze_naming_conventions(python_files)
            score += naming_score * self.skill_indicators["code_quality"]["naming_conventions"]["weight"]
            
        except Exception as e:
            print(f"コード品質評価エラー: {e}")
            score = 0.6  # デフォルト
        
        return min(1.0, score / 0.6)  # 正規化
    
    def _assess_git_proficiency(self) -> float:
        """Git 習熟度評価"""
        if not self.git_repo:
            return 0.5
        
        try:
            # コミット頻度分析
            commits = list(self.git_repo.iter_commits(max_count=100))
            commit_frequency_score = min(1.0, len(commits) / 50)  # 50コミット以上で満点
            
            # コミットメッセージ品質
            commit_quality_score = self._analyze_commit_quality(commits)
            
            # ブランチ戦略
            branches = list(self.git_repo.branches)
            branching_score = min(1.0, len(branches) / 3)  # 3ブランチ以上で満点
            
            git_score = (
                commit_frequency_score * 0.4 +
                commit_quality_score * 0.5 +
                branching_score * 0.1
            )
            
            return git_score
            
        except Exception as e:
            print(f"Git 習熟度評価エラー: {e}")
            return 0.5
    
    def _assess_problem_solving(self) -> float:
        """問題解決能力評価"""
        try:
            # Phase 1-3 のデータから修正成功率を分析
            success_rate = self._analyze_fix_success_rate()
            resolution_time_score = self._analyze_resolution_time()
            
            problem_solving_score = (
                success_rate * 0.7 +
                resolution_time_score * 0.3
            )
            
            return problem_solving_score
            
        except Exception as e:
            print(f"問題解決評価エラー: {e}")
            return 0.6
    
    def _analyze_docstring_usage(self, python_files: List[Path]) -> float:
        """docstring 使用率分析"""
        total_functions = 0
        functions_with_docstring = 0
        
        for file_path in python_files[:10]:  # サンプリング
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # 関数定義を検索
                function_pattern = r'def\s+\w+\s*\([^)]*\):'
                functions = re.findall(function_pattern, content)
                total_functions += len(functions)
                
                # docstring を持つ関数を検索
                docstring_pattern = r'def\s+\w+\s*\([^)]*\):\s*"""'
                functions_with_docstring += len(re.findall(docstring_pattern, content))
                
            except:
                continue
        
        if total_functions == 0:
            return 0.5
        
        return functions_with_docstring / total_functions
    
    def _analyze_function_complexity(self, python_files: List[Path]) -> float:
        """関数複雑度分析"""
        complexity_scores = []
        
        for file_path in python_files[:10]:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                lines = content.split('\n')
                
                # 簡易的な複雑度計算（行数ベース）
                in_function = False
                current_function_lines = 0
                
                for line in lines:
                    if 'def ' in line:
                        if in_function and current_function_lines > 0:
                            # 前の関数の複雑度スコア計算
                            complexity_scores.append(self._calculate_complexity_score(current_function_lines))
                        in_function = True
                        current_function_lines = 0
                    elif in_function:
                        if line.strip() and not line.strip().startswith('#'):
                            current_function_lines += 1
                        if line.strip() == '' and current_function_lines > 0:
                            # 関数終了
                            complexity_scores.append(self._calculate_complexity_score(current_function_lines))
                            in_function = False
            except:
                continue
        
        if not complexity_scores:
            return 0.7
        
        return statistics.mean(complexity_scores)
    
    def _calculate_complexity_score(self, lines: int) -> float:
        """複雑度スコア計算（行数から）"""
        if lines <= 10:
            return 1.0  # シンプル
        elif lines <= 20:
            return 0.8  # 標準
        elif lines <= 50:
            return 0.6  # 複雑
        else:
            return 0.4  # 非常に複雑
    
    def _analyze_error_handling(self, python_files: List[Path]) -> float:
        """エラーハンドリング分析"""
        total_functions = 0
        functions_with_error_handling = 0
        
        for file_path in python_files[:10]:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # 関数定義数
                function_count = len(re.findall(r'def\s+\w+', content))
                total_functions += function_count
                
                # try-except 使用数
                error_handling_count = len(re.findall(r'try:', content))
                functions_with_error_handling += error_handling_count
                
            except:
                continue
        
        if total_functions == 0:
            return 0.6
        
        return min(1.0, functions_with_error_handling / (total_functions * 0.3))  # 30%がエラーハンドリングを持つことを期待
    
    def _analyze_naming_conventions(self, python_files: List[Path]) -> float:
        """命名規則分析"""
        total_names = 0
        good_names = 0
        
        for file_path in python_files[:10]:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # 変数・関数名の抽出
                names = re.findall(r'(?:def|class)\s+(\w+)', content)
                names += re.findall(r'(\w+)\s*=', content)
                
                for name in names:
                    total_names += 1
                    # 良い命名の基準（snake_case、意味のある名前）
                    if re.match(r'^[a-z_][a-z0-9_]*$', name) and len(name) > 2 and not re.match(r'^[a-z]{1,2}$', name):
                        good_names += 1
                
            except:
                continue
        
        if total_names == 0:
            return 0.7
        
        return good_names / total_names
    
    def _analyze_commit_quality(self, commits: List) -> float:
        """コミット品質分析"""
        if not commits:
            return 0.5
        
        quality_scores = []
        
        for commit in commits[:20]:  # 直近20コミット
            message = commit.message.strip()
            
            score = 0.0
            
            # メッセージ長（適切な長さ）
            if 10 <= len(message) <= 100:
                score += 0.3
            
            # プレフィックス使用（feat:, fix:, docs: など）
            if re.match(r'^(feat|fix|docs|style|refactor|test|chore):', message.lower()):
                score += 0.4
            
            # 大文字で開始
            if message and message[0].isupper():
                score += 0.2
            
            # 説明的内容
            if len(message.split()) >= 3:
                score += 0.1
            
            quality_scores.append(min(1.0, score))
        
        return statistics.mean(quality_scores) if quality_scores else 0.5
    
    def _analyze_fix_success_rate(self) -> float:
        """修正成功率分析"""
        try:
            # auto_guard の学習データから成功率を分析
            if os.path.exists("out/auto_guard_learning.json"):
                with open("out/auto_guard_learning.json") as f:
                    guards = []
                    for line in f:
                        if line.strip():
                            guards.append(json.loads(line))
                
                if guards:
                    success_count = sum(1 for g in guards if g.get("success", False))
                    return success_count / len(guards)
            
            return 0.7  # デフォルト
        except:
            return 0.7
    
    def _analyze_resolution_time(self) -> float:
        """解決時間分析"""
        # 簡易実装：フィードバック履歴から推定
        try:
            if os.path.exists("out/feedback_history.json"):
                with open("out/feedback_history.json") as f:
                    for line in f:
                        if line.strip():
                            feedback = json.loads(line)
                            # 解決時間の簡易推定（スコアが高いほど速い解決）
                            score = feedback.get("score", 0.5)
                            if score >= 0.8:
                                return 0.9  # 高速
                            elif score >= 0.6:
                                return 0.7  # 標準
                            else:
                                return 0.5  # 遅い
            
            return 0.7  # デフォルト
        except:
            return 0.7
    
    def _determine_skill_level(self, overall_score: float) -> str:
        """総合スキルレベル判定"""
        if overall_score >= 0.85:
            return "expert"
        elif overall_score >= 0.70:
            return "advanced"
        elif overall_score >= 0.50:
            return "intermediate"
        else:
            return "beginner"
    
    def _estimate_experience(self) -> int:
        """経験年数推定"""
        if self.git_repo:
            try:
                commits = list(self.git_repo.iter_commits())
                if commits:
                    first_commit = commits[-1]
                    months = (datetime.now() - first_commit.committed_datetime.replace(tzinfo=None)).days // 30
                    return max(1, months)
            except:
                pass
        return 6  # デフォルト6ヶ月
    
    def _identify_specializations(self) -> List[str]:
        """専門領域特定"""
        specializations = []
        
        # ファイルタイプから判定
        file_types = {}
        for file_path in Path(".").rglob("*"):
            if file_path.is_file() and not any(skip in str(file_path) for skip in [".git", "__pycache__", "node_modules"]):
                ext = file_path.suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1
        
        # 上位のファイルタイプから専門領域を推定
        sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
        
        for ext, count in sorted_types[:3]:
            if ext == ".py":
                specializations.append("Python")
            elif ext in [".yml", ".yaml"]:
                specializations.append("DevOps/CI/CD")
            elif ext in [".js", ".ts"]:
                specializations.append("JavaScript/TypeScript")
            elif ext in [".md"]:
                specializations.append("Documentation")
        
        return specializations[:3]  # 上位3つまで
    
    def _analyze_learning_preferences(self) -> Dict[str, Any]:
        """学習設定分析"""
        return {
            "preferred_style": "hands-on",  # デフォルト
            "difficulty_progression": "gradual",
            "feedback_frequency": "immediate",
            "resource_types": ["examples", "documentation", "tutorials"]
        }
    
    def _analyze_recent_activity(self) -> Dict[str, Any]:
        """最近の活動分析"""
        activity = {
            "commits_last_week": 0,
            "files_modified": 0,
            "issues_worked_on": 0,
            "last_active": None
        }
        
        if self.git_repo:
            try:
                week_ago = datetime.now() - timedelta(days=7)
                recent_commits = [
                    c for c in self.git_repo.iter_commits(max_count=50)
                    if c.committed_datetime.replace(tzinfo=None) > week_ago
                ]
                activity["commits_last_week"] = len(recent_commits)
                
                if recent_commits:
                    activity["last_active"] = recent_commits[0].committed_datetime.replace(tzinfo=None).isoformat()
                    
                    # 修正ファイル数
                    modified_files = set()
                    for commit in recent_commits:
                        for item in commit.stats.files:
                            modified_files.add(item)
                    activity["files_modified"] = len(modified_files)
            except:
                pass
        
        return activity
    
    def _identify_growth_areas(self, code_quality: float, git_proficiency: float, problem_solving: float) -> List[str]:
        """成長領域特定"""
        growth_areas = []
        
        if code_quality < 0.7:
            growth_areas.append("コード品質とベストプラクティス")
        if git_proficiency < 0.7:
            growth_areas.append("Git・バージョン管理")
        if problem_solving < 0.7:
            growth_areas.append("問題解決・デバッグスキル")
        
        return growth_areas if growth_areas else ["継続的な学習・スキル向上"]
    
    def _identify_strengths(self, code_quality: float, git_proficiency: float, problem_solving: float) -> List[str]:
        """強み特定"""
        strengths = []
        
        if code_quality >= 0.8:
            strengths.append("高品質なコード作成")
        if git_proficiency >= 0.8:
            strengths.append("Git・バージョン管理の熟練")
        if problem_solving >= 0.8:
            strengths.append("効率的な問題解決")
        
        return strengths if strengths else ["基礎的なプログラミングスキル"]


class GuidanceEngine:
    """ガイダンス生成エンジン"""
    
    def __init__(self):
        self.guidance_templates = self._load_guidance_templates()
    
    def _load_guidance_templates(self) -> Dict[str, Any]:
        """ガイダンステンプレート読み込み"""
        return {
            "beginner": {
                "code_quality": {
                    "title": "基本的なコード品質改善",
                    "description": "コメントの追加とコードの整理から始めましょう",
                    "steps": [
                        "1. 関数に簡潔なコメントを追加する",
                        "2. 変数名をわかりやすいものに変更する",
                        "3. 長い関数を小さく分割する",
                        "4. 基本的なエラーハンドリングを追加する"
                    ],
                    "estimated_time": 30,
                    "resources": [
                        {"type": "tutorial", "url": "Python コード品質入門", "description": "基礎から学ぶコード品質"}
                    ]
                },
                "git_proficiency": {
                    "title": "Git基本操作の習得",
                    "description": "Git の基本的なコマンドと作業フローを学びましょう",
                    "steps": [
                        "1. git add, commit, push の基本操作を練習",
                        "2. わかりやすいコミットメッセージの書き方を学習",
                        "3. ブランチの作成と切り替えを練習",
                        "4. 簡単なマージ操作を試す"
                    ],
                    "estimated_time": 60,
                    "resources": [
                        {"type": "tutorial", "url": "Git入門ガイド", "description": "初心者向けGit操作"}
                    ]
                }
            },
            "intermediate": {
                "code_quality": {
                    "title": "コード品質の体系的向上",
                    "description": "設計パターンとテストを取り入れた品質向上",
                    "steps": [
                        "1. docstring を全ての関数に追加",
                        "2. type hints を使用して型安全性向上",
                        "3. 単体テストの作成",
                        "4. linter (flake8, pylint) の導入と修正"
                    ],
                    "estimated_time": 90,
                    "resources": [
                        {"type": "documentation", "url": "Python Best Practices", "description": "Pythonベストプラクティス集"}
                    ]
                }
            },
            "advanced": {
                "code_quality": {
                    "title": "アーキテクチャレベルの品質向上",
                    "description": "設計原則に基づいた高品質なコード作成",
                    "steps": [
                        "1. SOLID原則に基づくクラス設計の見直し",
                        "2. デザインパターンの適用検討",
                        "3. 包括的なテストカバレッジ確保",
                        "4. パフォーマンス最適化の実施"
                    ],
                    "estimated_time": 180,
                    "resources": [
                        {"type": "book", "url": "Clean Code", "description": "クリーンコード原則"}
                    ]
                }
            },
            "expert": {
                "code_quality": {
                    "title": "チーム品質向上のリーダーシップ",
                    "description": "チーム全体の品質向上をリードする",
                    "steps": [
                        "1. コードレビュープロセスの改善",
                        "2. 品質メトリクスの導入と監視",
                        "3. 自動化ツールの導入・カスタマイズ",
                        "4. チームメンバーへの品質教育"
                    ],
                    "estimated_time": 240,
                    "resources": [
                        {"type": "practice", "url": "Team Leadership", "description": "技術リーダーシップ実践"}
                    ]
                }
            }
        }
    
    def generate_personalized_guidance(self, profile: DeveloperProfile, issue_type: str) -> Optional[GuidanceRecommendation]:
        """パーソナライズドガイダンス生成"""
        skill_level = profile.skill_level
        
        if skill_level not in self.guidance_templates:
            skill_level = "intermediate"  # フォールバック
        
        if issue_type not in self.guidance_templates[skill_level]:
            issue_type = "code_quality"  # フォールバック
        
        template = self.guidance_templates[skill_level][issue_type]
        
        # プロファイルに基づいたカスタマイズ
        customized_steps = self._customize_steps(template["steps"], profile)
        difficulty_level = self._determine_difficulty(skill_level)
        learning_objectives = self._generate_learning_objectives(template, profile)
        follow_up_actions = self._generate_follow_up_actions(profile, issue_type)
        
        return GuidanceRecommendation(
            developer_id=profile.developer_id,
            skill_level=skill_level,
            issue_type=issue_type,
            guidance_type="tutorial",
            title=template["title"],
            description=template["description"],
            detailed_steps=customized_steps,
            difficulty_level=difficulty_level,
            estimated_time=template["estimated_time"],
            learning_objectives=learning_objectives,
            follow_up_actions=follow_up_actions,
            resources=template["resources"]
        )
    
    def _customize_steps(self, base_steps: List[str], profile: DeveloperProfile) -> List[str]:
        """プロファイルに基づくステップカスタマイズ"""
        customized = []
        
        for step in base_steps:
            # 専門領域に応じた調整
            if "Python" in profile.specializations and "python" not in step.lower():
                step = step.replace("関数", "Python関数")
            
            customized.append(step)
        
        return customized
    
    def _determine_difficulty(self, skill_level: str) -> int:
        """難易度レベル決定"""
        difficulty_map = {
            "beginner": 2,
            "intermediate": 3,
            "advanced": 4,
            "expert": 5
        }
        return difficulty_map.get(skill_level, 3)
    
    def _generate_learning_objectives(self, template: Dict, profile: DeveloperProfile) -> List[str]:
        """学習目標生成"""
        objectives = []
        
        if profile.skill_level == "beginner":
            objectives = [
                "基本的な品質概念の理解",
                "実践的なスキルの習得",
                "継続的改善の習慣化"
            ]
        elif profile.skill_level == "intermediate":
            objectives = [
                "体系的な品質向上手法の習得",
                "ツール活用による効率化",
                "問題解決能力の向上"
            ]
        elif profile.skill_level == "advanced":
            objectives = [
                "アーキテクチャレベルの品質設計",
                "高度な最適化技術の習得",
                "品質メトリクスの活用"
            ]
        else:  # expert
            objectives = [
                "チーム品質向上のリーダーシップ",
                "組織レベルの品質改善",
                "イノベーションの推進"
            ]
        
        return objectives
    
    def _generate_follow_up_actions(self, profile: DeveloperProfile, issue_type: str) -> List[str]:
        """フォローアップアクション生成"""
        actions = []
        
        # 成長領域に基づく推奨
        for growth_area in profile.growth_areas:
            if "コード品質" in growth_area:
                actions.append("毎日のコード品質チェックを習慣化")
            elif "Git" in growth_area:
                actions.append("Git操作の練習プロジェクトに参加")
            elif "問題解決" in growth_area:
                actions.append("デバッグ技術の向上練習")
        
        # 一般的なフォローアップ
        actions.extend([
            "1週間後の進捗確認",
            "実践結果のレビューと改善",
            "次のステップの計画立案"
        ])
        
        return actions[:5]  # 最大5個まで


class AdaptiveGuidanceSystem:
    """適応ガイダンスシステム メインクラス"""
    
    def __init__(self):
        self.assessment_engine = SkillAssessmentEngine()
        self.guidance_engine = GuidanceEngine()
        self.developer_profiles = {}
    
    def provide_guidance(self, issue_type: str = "code_quality", developer_id: str = "default") -> Dict[str, Any]:
        """ガイダンス提供"""
        print(f"🎓 適応ガイダンス システム開始: {developer_id}")
        
        # 開発者プロファイル評価
        profile = self.assessment_engine.assess_developer_skill(developer_id)
        self.developer_profiles[developer_id] = profile
        
        # パーソナライズドガイダンス生成
        guidance = self.guidance_engine.generate_personalized_guidance(profile, issue_type)
        
        if not guidance:
            return {"error": "ガイダンス生成に失敗しました"}
        
        # 結果構造化
        result = {
            "developer_profile": {
                "id": profile.developer_id,
                "skill_level": profile.skill_level,
                "experience_months": profile.experience_months,
                "specializations": profile.specializations,
                "strengths": profile.strengths,
                "growth_areas": profile.growth_areas
            },
            "personalized_guidance": {
                "title": guidance.title,
                "description": guidance.description,
                "difficulty_level": guidance.difficulty_level,
                "estimated_time": guidance.estimated_time,
                "detailed_steps": guidance.detailed_steps,
                "learning_objectives": guidance.learning_objectives,
                "follow_up_actions": guidance.follow_up_actions,
                "resources": guidance.resources
            },
            "adaptation_info": {
                "customization_applied": True,
                "skill_level_matched": True,
                "specialization_considered": len(profile.specializations) > 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # 結果保存
        self._save_guidance_result(result)
        
        return result
    
    def _save_guidance_result(self, result: Dict[str, Any]):
        """ガイダンス結果保存"""
        try:
            os.makedirs("out", exist_ok=True)
            with open("out/adaptive_guidance.json", "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"結果保存エラー: {e}")
    
    def display_guidance(self, result: Dict[str, Any]):
        """ガイダンス表示"""
        profile = result["developer_profile"]
        guidance = result["personalized_guidance"]
        
        print("\n🎓 アダプティブガイダンス結果")
        print("=" * 50)
        
        print(f"👤 開発者プロファイル:")
        print(f"   スキルレベル: {profile['skill_level']}")
        print(f"   経験: {profile['experience_months']}ヶ月")
        print(f"   専門領域: {', '.join(profile['specializations']) if profile['specializations'] else 'なし'}")
        print(f"   強み: {', '.join(profile['strengths'])}")
        print(f"   成長領域: {', '.join(profile['growth_areas'])}")
        
        print(f"\n💡 パーソナライズドガイダンス:")
        print(f"   タイトル: {guidance['title']}")
        print(f"   説明: {guidance['description']}")
        print(f"   難易度: {guidance['difficulty_level']}/5")
        print(f"   推定時間: {guidance['estimated_time']}分")
        
        print(f"\n📋 詳細ステップ:")
        for step in guidance['detailed_steps']:
            print(f"   • {step}")
        
        print(f"\n🎯 学習目標:")
        for objective in guidance['learning_objectives']:
            print(f"   • {objective}")
        
        print(f"\n🔄 フォローアップアクション:")
        for action in guidance['follow_up_actions']:
            print(f"   • {action}")
        
        if guidance['resources']:
            print(f"\n📚 関連リソース:")
            for resource in guidance['resources']:
                print(f"   • {resource['description']}: {resource['url']}")


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="🎓 Adaptive Guidance System")
    parser.add_argument("--issue-type", default="code_quality", help="Issue type to get guidance for")
    parser.add_argument("--developer-id", default="default", help="Developer ID")
    parser.add_argument("--display-only", action="store_true", help="Display last guidance result")
    
    args = parser.parse_args()
    
    system = AdaptiveGuidanceSystem()
    
    if args.display_only:
        try:
            with open("out/adaptive_guidance.json") as f:
                result = json.load(f)
                system.display_guidance(result)
        except:
            print("❌ 保存されたガイダンス結果が見つかりません")
    else:
        result = system.provide_guidance(args.issue_type, args.developer_id)
        system.display_guidance(result)


if __name__ == "__main__":
    main()
