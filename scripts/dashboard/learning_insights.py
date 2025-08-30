#!/usr/bin/env python3
"""
🎯 Learning Insights Dashboard
学習効果の可視化とシステム健康度レポート
"""

import json
import os
import glob
from datetime import datetime
import subprocess
from collections import defaultdict, Counter

class LearningInsights:
    def __init__(self):
        self.out_dir = "out"
        self.logs_dir = "logs"
        self.scripts_dir = "scripts/quality"
        
    def analyze_learning_data(self):
        """学習データの分析"""
        insights = {
            "timestamp": datetime.now().isoformat(),
            "learning_effectiveness": {},
            "fix_success_rates": {},
            "pattern_recognition": {},
            "system_health": {}
        }
        
        # 1. 出力ファイル分析
        insights["learning_effectiveness"] = self._analyze_output_files()
        
        # 2. 修正成功率分析
        insights["fix_success_rates"] = self._analyze_fix_success()
        
        # 3. パターン認識精度
        insights["pattern_recognition"] = self._analyze_patterns()
        
        # 4. システム健康度
        insights["system_health"] = self._check_system_health()
        
        return insights
    
    def _analyze_output_files(self):
        """出力ファイルから学習効果を分析"""
        if not os.path.exists(self.out_dir):
            return {"status": "no_data", "files": 0}
            
        files = glob.glob(f"{self.out_dir}/*.json")
        
        # ファイル数の推移
        recent_files = [f for f in files if self._is_recent_file(f, days=7)]
        
        # パフォーマンス改善の追跡
        performance_data = self._extract_performance_metrics(files)
        
        return {
            "total_output_files": len(files),
            "recent_files": len(recent_files),
            "performance_trends": performance_data,
            "active_learning": len(recent_files) > 0
        }
    
    def _analyze_fix_success(self):
        """修正成功率の分析"""
        success_patterns = {
            "yaml_fixes": 0,
            "context_warnings": 0,
            "bash_syntax": 0,
            "total_attempts": 0
        }
        
        # Git コミットログから修正履歴を分析
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "--since=1 week ago", "--grep=fix"],
                capture_output=True, text=True, cwd="."
            )
            
            if result.returncode == 0:
                commits = result.stdout.strip().split('\n')
                success_patterns["total_attempts"] = len([c for c in commits if c.strip()])
                
                for commit in commits:
                    if 'yaml' in commit.lower():
                        success_patterns["yaml_fixes"] += 1
                    if 'context' in commit.lower() or 'warning' in commit.lower():
                        success_patterns["context_warnings"] += 1
                    if 'bash' in commit.lower() or 'syntax' in commit.lower():
                        success_patterns["bash_syntax"] += 1
                        
        except Exception as e:
            success_patterns["error"] = str(e)
            
        return success_patterns
    
    def _analyze_patterns(self):
        """パターン認識の精度分析"""
        patterns = {"recognized_patterns": 0, "accuracy": "unknown"}
        
        # tag_rules.yaml の確認
        tag_rules_file = f"{self.scripts_dir}/tag_rules.yaml"
        if os.path.exists(tag_rules_file):
            try:
                with open(tag_rules_file, 'r') as f:
                    content = f.read()
                    patterns["recognized_patterns"] = content.count("pattern:")
                    patterns["status"] = "active"
            except:
                patterns["status"] = "error"
        
        return patterns
    
    def _check_system_health(self):
        """システム健康度チェック"""
        health = {
            "overall_status": "healthy",
            "components": {},
            "last_activity": None,
            "warnings": []
        }
        
        # 各コンポーネントの確認
        components = {
            "learning_scripts": f"{self.scripts_dir}/",
            "output_directory": self.out_dir,
            "continuous_learner": f"{self.scripts_dir}/continuous_learner.py",
            "auto_fix_generator": f"{self.scripts_dir}/auto_fix_generator.py"
        }
        
        for name, path in components.items():
            health["components"][name] = {
                "status": "ok" if os.path.exists(path) else "missing",
                "last_modified": self._get_last_modified(path) if os.path.exists(path) else None
            }
            
            if not os.path.exists(path):
                health["warnings"].append(f"{name} not found: {path}")
        
        # 最近の活動確認
        if os.path.exists(self.out_dir):
            recent_files = glob.glob(f"{self.out_dir}/*.json")
            if recent_files:
                latest_file = max(recent_files, key=os.path.getmtime)
                health["last_activity"] = self._get_last_modified(latest_file)
        
        return health
    
    def _is_recent_file(self, filepath, days=7):
        """ファイルが最近のものかチェック"""
        try:
            file_time = os.path.getmtime(filepath)
            current_time = datetime.now().timestamp()
            return (current_time - file_time) < (days * 24 * 3600)
        except:
            return False
    
    def _extract_performance_metrics(self, files):
        """パフォーマンスメトリクスの抽出"""
        metrics = {"pass_rates": [], "improvement_trend": "unknown"}
        
        for file in files[-10:]:  # 最新10ファイルを確認
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    
                # pass_rate やshadow_pass_rate を探す
                if isinstance(data, dict):
                    for key, value in data.items():
                        if 'pass_rate' in str(key).lower() and isinstance(value, (int, float)):
                            metrics["pass_rates"].append(float(value))
                        elif isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                if 'pass_rate' in str(sub_key).lower() and isinstance(sub_value, (int, float)):
                                    metrics["pass_rates"].append(float(sub_value))
            except:
                continue
        
        # 改善トレンドの分析
        if len(metrics["pass_rates"]) >= 2:
            recent_avg = sum(metrics["pass_rates"][-3:]) / min(3, len(metrics["pass_rates"]))
            older_avg = sum(metrics["pass_rates"][:3]) / min(3, len(metrics["pass_rates"]))
            
            if recent_avg > older_avg + 5:
                metrics["improvement_trend"] = "improving"
            elif recent_avg < older_avg - 5:
                metrics["improvement_trend"] = "declining"  
            else:
                metrics["improvement_trend"] = "stable"
        
        return metrics
    
    def _get_last_modified(self, filepath):
        """最終更新時刻を取得"""
        try:
            timestamp = os.path.getmtime(filepath)
            return datetime.fromtimestamp(timestamp).isoformat()
        except:
            return None
    
    def generate_report(self):
        """レポート生成"""
        print("🎯 Learning Insights Dashboard")
        print("=" * 50)
        
        insights = self.analyze_learning_data()
        
        # 1. 学習効果レポート
        print("\n📊 学習効果分析")
        print("-" * 30)
        learning = insights["learning_effectiveness"]
        print(f"総出力ファイル数: {learning.get('total_output_files', 0)}")
        print(f"最近の活動 (7日以内): {learning.get('recent_files', 0)}ファイル")
        print(f"学習アクティブ状態: {'✅' if learning.get('active_learning') else '❌'}")
        
        if learning.get('performance_trends', {}).get('pass_rates'):
            rates = learning['performance_trends']['pass_rates']
            print(f"パフォーマンス: 平均 {sum(rates)/len(rates):.1f}%")
            print(f"改善トレンド: {learning['performance_trends']['improvement_trend']}")
        
        # 2. 修正成功率レポート
        print("\n🔧 修正成功率分析")
        print("-" * 30)
        fixes = insights["fix_success_rates"]
        print(f"総修正試行数: {fixes.get('total_attempts', 0)}")
        print(f"YAML修正: {fixes.get('yaml_fixes', 0)}回")
        print(f"Context警告修正: {fixes.get('context_warnings', 0)}回")
        print(f"Bash構文修正: {fixes.get('bash_syntax', 0)}回")
        
        if fixes.get('total_attempts', 0) > 0:
            success_rate = (fixes.get('yaml_fixes', 0) + fixes.get('context_warnings', 0) + fixes.get('bash_syntax', 0)) / fixes['total_attempts'] * 100
            print(f"全体成功率: {success_rate:.1f}%")
        
        # 3. パターン認識レポート
        print("\n🎯 パターン認識状況")
        print("-" * 30)
        patterns = insights["pattern_recognition"]
        print(f"認識パターン数: {patterns.get('recognized_patterns', 0)}")
        print(f"システム状態: {patterns.get('status', 'unknown')}")
        
        # 4. システム健康度レポート
        print("\n💚 システム健康度")
        print("-" * 30)
        health = insights["system_health"]
        print(f"全体状態: {health.get('overall_status', 'unknown')}")
        
        for component, status in health.get('components', {}).items():
            status_icon = "✅" if status['status'] == 'ok' else "❌"
            print(f"{component}: {status_icon}")
        
        if health.get('last_activity'):
            print(f"最新活動: {health['last_activity']}")
        
        if health.get('warnings'):
            print("\n⚠️  警告:")
            for warning in health['warnings']:
                print(f"  - {warning}")
        
        # 5. 推奨アクション
        print("\n🚀 推奨アクション")
        print("-" * 30)
        
        recommendations = []
        
        if learning.get('recent_files', 0) == 0:
            recommendations.append("学習データが古い - 新しい実行を推奨")
        
        if fixes.get('total_attempts', 0) < 5:
            recommendations.append("修正履歴が少ない - より多くの修正データを蓄積")
            
        if patterns.get('recognized_patterns', 0) < 10:
            recommendations.append("パターン認識を強化 - tag_rules.yaml の拡充")
        
        if not recommendations:
            recommendations.append("システム状態良好 - Phase 2実装の準備完了!")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        
        # JSON出力
        output_file = "out/learning_insights.json"
        os.makedirs("out", exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(insights, f, indent=2)
        
        print(f"\n📄 詳細データ: {output_file}")
        return insights

def main():
    dashboard = LearningInsights()
    dashboard.generate_report()

if __name__ == "__main__":
    main()


