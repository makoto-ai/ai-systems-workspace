#!/usr/bin/env python3
"""
💚 System Health Monitor
リアルタイム品質監視とアラートシステム
"""

import os
import json
import glob
import subprocess
from datetime import datetime, timedelta
from collections import defaultdict

class HealthMonitor:
    def __init__(self):
        self.alerts = []
        self.metrics = {}
        self.thresholds = {
            "max_age_days": 7,
            "min_success_rate": 70,
            "max_warnings": 5,
            "min_activity_files": 3
        }
    
    def check_all_systems(self):
        """全システムの健康度チェック"""
        print("💚 System Health Monitor")
        print("=" * 40)
        
        checks = [
            ("🔧 Learning System", self._check_learning_system),
            ("📊 Data Pipeline", self._check_data_pipeline),
            ("🚀 Automation", self._check_automation),
            ("⚠️  Quality Gates", self._check_quality_gates),
            ("🔄 Continuous Learning", self._check_continuous_learning)
        ]
        
        overall_health = "healthy"
        
        for check_name, check_func in checks:
            print(f"\n{check_name}")
            print("-" * 25)
            
            try:
                result = check_func()
                status = result.get("status", "unknown")
                
                if status == "critical":
                    overall_health = "critical"
                    print("❌ CRITICAL")
                elif status == "warning" and overall_health != "critical":
                    overall_health = "warning"  
                    print("⚠️  WARNING")
                else:
                    print("✅ OK")
                
                # 詳細表示
                for detail in result.get("details", []):
                    print(f"   • {detail}")
                    
                # アラート追加
                for alert in result.get("alerts", []):
                    self.alerts.append(f"{check_name}: {alert}")
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
                self.alerts.append(f"{check_name}: Exception - {str(e)}")
                overall_health = "critical"
        
        # 総合評価
        print(f"\n🎯 Overall System Health")
        print("=" * 30)
        
        if overall_health == "healthy":
            print("✅ HEALTHY - All systems operating normally")
        elif overall_health == "warning":
            print("⚠️  WARNING - Some issues detected")
        else:
            print("❌ CRITICAL - Immediate attention required")
        
        # アラート表示
        if self.alerts:
            print(f"\n🚨 Active Alerts ({len(self.alerts)})")
            print("-" * 20)
            for i, alert in enumerate(self.alerts, 1):
                print(f"{i}. {alert}")
        else:
            print("\n✨ No active alerts")
        
        # レポート保存
        self._save_health_report(overall_health)
        
        return overall_health
    
    def _check_learning_system(self):
        """学習システムの確認"""
        result = {"status": "healthy", "details": [], "alerts": []}
        
        # 必須スクリプトの確認
        required_scripts = [
            "scripts/quality/continuous_learner.py",
            "scripts/quality/auto_fix_generator.py",
            "scripts/quality/tag_failures.py",
            "scripts/dashboard/learning_insights.py"
        ]
        
        missing_scripts = []
        for script in required_scripts:
            if not os.path.exists(script):
                missing_scripts.append(script)
        
        if missing_scripts:
            result["status"] = "critical"
            result["alerts"].append(f"Missing {len(missing_scripts)} critical scripts")
            result["details"] = [f"Missing: {script}" for script in missing_scripts]
        else:
            result["details"].append(f"All {len(required_scripts)} scripts present")
        
        # 設定ファイルの確認
        config_files = [
            "scripts/quality/tag_rules.yaml",
            "scripts/quality/yaml_tag_rules.yaml"  
        ]
        
        present_configs = [f for f in config_files if os.path.exists(f)]
        result["details"].append(f"Config files: {len(present_configs)}/{len(config_files)}")
        
        if len(present_configs) < len(config_files):
            result["status"] = "warning"
            result["alerts"].append("Some config files missing")
        
        return result
    
    def _check_data_pipeline(self):
        """データパイプラインの確認"""
        result = {"status": "healthy", "details": [], "alerts": []}
        
        # out/ ディレクトリの確認
        if not os.path.exists("out"):
            result["status"] = "critical"
            result["alerts"].append("Output directory missing")
            return result
        
        # 最近のデータファイル確認
        json_files = glob.glob("out/*.json")
        recent_files = []
        
        cutoff_date = datetime.now() - timedelta(days=self.thresholds["max_age_days"])
        
        for file in json_files:
            try:
                file_time = datetime.fromtimestamp(os.path.getmtime(file))
                if file_time > cutoff_date:
                    recent_files.append(file)
            except:
                continue
        
        result["details"].append(f"Total data files: {len(json_files)}")
        result["details"].append(f"Recent files (7 days): {len(recent_files)}")
        
        if len(recent_files) < self.thresholds["min_activity_files"]:
            result["status"] = "warning"
            result["alerts"].append("Low recent activity in data pipeline")
        
        # ログファイルの確認
        log_files = glob.glob("logs/*.log") + glob.glob("out/*.log")
        result["details"].append(f"Log files: {len(log_files)}")
        
        return result
    
    def _check_automation(self):
        """自動化システムの確認"""
        result = {"status": "healthy", "details": [], "alerts": []}
        
        # Makefileの確認
        if os.path.exists("Makefile"):
            try:
                with open("Makefile", 'r') as f:
                    content = f.read()
                    
                # 学習関連コマンドの確認
                learning_commands = ["learn-loop", "auto-improve", "pareto"]
                present_commands = [cmd for cmd in learning_commands if cmd in content]
                
                result["details"].append(f"Learning commands: {len(present_commands)}/{len(learning_commands)}")
                
                if len(present_commands) < len(learning_commands):
                    result["status"] = "warning"
                    result["alerts"].append("Some automation commands missing")
                    
            except Exception as e:
                result["status"] = "warning"
                result["alerts"].append(f"Makefile read error: {e}")
        else:
            result["status"] = "warning"
            result["alerts"].append("Makefile not found")
        
        # GitHub Actions の確認
        workflow_files = glob.glob(".github/workflows/*.yml")
        result["details"].append(f"GitHub workflows: {len(workflow_files)}")
        
        if len(workflow_files) < 3:
            result["status"] = "warning"
            result["alerts"].append("Few GitHub Actions workflows")
        
        return result
    
    def _check_quality_gates(self):
        """品質ゲートの確認"""
        result = {"status": "healthy", "details": [], "alerts": []}
        
        # 最近のlinter実行結果確認
        try:
            # yamllint の実行テスト
            lint_result = subprocess.run(
                ["yamllint", "--version"],
                capture_output=True, text=True
            )
            
            if lint_result.returncode == 0:
                result["details"].append("yamllint available")
            else:
                result["status"] = "warning"
                result["alerts"].append("yamllint not properly configured")
                
        except FileNotFoundError:
            result["status"] = "warning" 
            result["alerts"].append("yamllint not installed")
        
        # .yamllint設定ファイルの確認
        if os.path.exists(".yamllint"):
            result["details"].append("yamllint config present")
        else:
            result["status"] = "warning"
            result["alerts"].append(".yamllint config missing")
        
        # pre-commit の確認 (存在する場合)
        if os.path.exists(".pre-commit-config.yaml"):
            result["details"].append("pre-commit config present")
        
        return result
    
    def _check_continuous_learning(self):
        """継続学習機能の確認"""
        result = {"status": "healthy", "details": [], "alerts": []}
        
        # 最近の学習活動確認
        recent_commits = self._get_recent_learning_commits()
        result["details"].append(f"Recent learning commits: {len(recent_commits)}")
        
        if len(recent_commits) == 0:
            result["status"] = "warning"
            result["alerts"].append("No recent learning activity detected")
        
        # 学習データの品質確認
        insights_file = "out/learning_insights.json"
        if os.path.exists(insights_file):
            try:
                with open(insights_file, 'r') as f:
                    data = json.load(f)
                    
                success_data = data.get("fix_success_rates", {})
                total_attempts = success_data.get("total_attempts", 0)
                
                result["details"].append(f"Tracked fix attempts: {total_attempts}")
                
                if total_attempts < 5:
                    result["status"] = "warning"
                    result["alerts"].append("Low learning data volume")
                    
            except Exception as e:
                result["status"] = "warning"
                result["alerts"].append(f"Learning data read error: {e}")
        
        return result
    
    def _get_recent_learning_commits(self):
        """最近の学習関連コミット取得"""
        try:
            result = subprocess.run([
                "git", "log", "--oneline", "--since=2 weeks ago", 
                "--grep=fix", "--grep=learn", "--grep=improve"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                commits = [line for line in result.stdout.strip().split('\n') if line.strip()]
                return commits
        except:
            pass
        
        return []
    
    def _save_health_report(self, overall_health):
        """健康度レポートの保存"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": overall_health,
            "alerts_count": len(self.alerts),
            "alerts": self.alerts,
            "thresholds": self.thresholds
        }
        
        os.makedirs("out", exist_ok=True)
        with open("out/system_health.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Health report saved: out/system_health.json")

def main():
    monitor = HealthMonitor()
    health = monitor.check_all_systems()
    
    # 終了コード設定
    if health == "critical":
        exit(2)
    elif health == "warning":
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    main()
