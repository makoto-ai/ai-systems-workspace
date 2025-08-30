#!/usr/bin/env python3
"""
🔮 Issue Predictor - 問題予測エンジン
Phase 1で蓄積されたデータから将来の問題を予測
"""

import json
import os
import glob
import re
import subprocess
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import yaml

class IssuePredictionEngine:
    def __init__(self):
        self.prediction_confidence = {}
        self.risk_patterns = {}
        self.historical_data = {}
        self.phase1_insights = {}
        
        # Phase 1データの読み込み
        self._load_phase1_data()
        self._load_pattern_rules()
        self._analyze_historical_trends()
        
    def predict_future_issues(self, target_files=None, prediction_days=7):
        """将来の問題を予測"""
        print("🔮 Issue Prediction Engine")
        print("=" * 40)
        
        predictions = {
            "timestamp": datetime.now().isoformat(),
            "prediction_horizon_days": prediction_days,
            "confidence_threshold": 0.7,
            "predicted_issues": [],
            "risk_assessment": {},
            "preventive_actions": []
        }
        
        # 1. ファイル変更パターンからの予測
        file_risks = self._predict_file_risks(target_files)
        
        # 2. 時系列パターンからの予測  
        temporal_risks = self._predict_temporal_risks(prediction_days)
        
        # 3. パターン認識による予測
        pattern_risks = self._predict_pattern_risks()
        
        # 4. 統合リスク評価
        integrated_risks = self._integrate_risk_assessments(
            file_risks, temporal_risks, pattern_risks
        )
        
        predictions["predicted_issues"] = integrated_risks["high_risk_issues"]
        predictions["risk_assessment"] = integrated_risks["risk_summary"] 
        predictions["preventive_actions"] = self._generate_preventive_actions(
            integrated_risks
        )
        
        return predictions
    
    def _load_phase1_data(self):
        """Phase 1の蓄積データを読み込み"""
        # Learning insights データ
        insights_file = "out/learning_insights.json"
        if os.path.exists(insights_file):
            with open(insights_file, 'r') as f:
                self.phase1_insights = json.load(f)
        
        # System health データ
        health_file = "out/system_health.json"
        if os.path.exists(health_file):
            with open(health_file, 'r') as f:
                self.phase1_insights["system_health"] = json.load(f)
        
        # 全データファイルの分析
        json_files = glob.glob("out/*.json")
        self.historical_data = {}
        
        for file in json_files[-20:]:  # 最新20ファイルを分析
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    file_key = os.path.basename(file)
                    self.historical_data[file_key] = data
            except:
                continue
    
    def _load_pattern_rules(self):
        """パターン認識ルールの読み込み"""
        rules_files = [
            "scripts/quality/tag_rules.yaml",
            "scripts/quality/yaml_tag_rules.yaml"
        ]
        
        self.risk_patterns = {
            "known_failures": [],
            "warning_signs": [],
            "success_patterns": []
        }
        
        for rules_file in rules_files:
            if os.path.exists(rules_file):
                try:
                    with open(rules_file, 'r') as f:
                        rules = yaml.safe_load(f)
                        for rule in rules.get('rules', []):
                            self.risk_patterns["known_failures"].append({
                                "tag": rule.get("tag"),
                                "pattern": rule.get("pattern"),
                                "confidence": 0.8
                            })
                except:
                    continue
    
    def _analyze_historical_trends(self):
        """過去データのトレンド分析"""
        # コミット履歴からの傾向分析
        try:
            result = subprocess.run([
                "git", "log", "--oneline", "--since=30 days ago"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                commits = result.stdout.strip().split('\n')
                
                # 問題パターンの分析
                fix_commits = [c for c in commits if 'fix' in c.lower()]
                error_commits = [c for c in commits if any(
                    word in c.lower() for word in ['error', 'warning', 'fail', 'bug']
                )]
                
                self.historical_data["commit_analysis"] = {
                    "total_commits": len([c for c in commits if c.strip()]),
                    "fix_commits": len(fix_commits),
                    "error_commits": len(error_commits),
                    "fix_frequency": len(fix_commits) / max(1, len([c for c in commits if c.strip()]))
                }
        except:
            pass
    
    def _predict_file_risks(self, target_files):
        """ファイル変更パターンからリスク予測"""
        file_risks = {}
        
        # GitHub Actions ワークフローの変更リスク
        workflow_files = glob.glob(".github/workflows/*.yml")
        
        for workflow in workflow_files:
            risk_score = 0.0
            risk_factors = []
            
            try:
                with open(workflow, 'r') as f:
                    content = f.read()
                    
                # 高リスクパターンの検出
                if 'secrets.' in content:
                    risk_score += 0.3
                    risk_factors.append("secrets context usage")
                
                if len(content.split('\n')) > 200:
                    risk_score += 0.2
                    risk_factors.append("complex workflow (200+ lines)")
                
                if content.count('run:') > 10:
                    risk_score += 0.2
                    risk_factors.append("many run steps")
                
                if 'python' in content and 'pip install' in content:
                    risk_score += 0.1
                    risk_factors.append("dependency management")
                    
                # Phase 1で検出されたパターンとの照合
                for pattern in self.risk_patterns["known_failures"]:
                    if pattern["pattern"] and re.search(pattern["pattern"], content, re.IGNORECASE):
                        risk_score += 0.4
                        risk_factors.append(f"known failure pattern: {pattern['tag']}")
                
                file_risks[workflow] = {
                    "risk_score": min(risk_score, 1.0),
                    "risk_factors": risk_factors,
                    "confidence": 0.8 if risk_factors else 0.3
                }
                
            except:
                continue
        
        return file_risks
    
    def _predict_temporal_risks(self, prediction_days):
        """時系列パターンからの予測"""
        temporal_risks = {
            "time_based_risks": [],
            "seasonal_patterns": {},
            "workday_patterns": {}
        }
        
        # Phase 1データから時系列パターンを分析
        if "fix_success_rates" in self.phase1_insights:
            fix_data = self.phase1_insights["fix_success_rates"]
            total_attempts = fix_data.get("total_attempts", 0)
            
            # 修正頻度から将来の問題発生を予測
            if total_attempts > 0:
                daily_avg_fixes = total_attempts / 14  # 2週間のデータと仮定
                predicted_issues_count = int(daily_avg_fixes * prediction_days)
                
                temporal_risks["time_based_risks"].append({
                    "type": "routine_maintenance",
                    "predicted_count": predicted_issues_count,
                    "confidence": 0.7,
                    "timeframe": f"next {prediction_days} days"
                })
        
        # 週末・平日パターン
        current_day = datetime.now().weekday()
        if current_day >= 5:  # 土日
            temporal_risks["workday_patterns"]["weekend_risk"] = {
                "risk_level": "low",
                "reason": "reduced development activity"
            }
        else:
            temporal_risks["workday_patterns"]["weekday_risk"] = {
                "risk_level": "medium",
                "reason": "active development period"
            }
        
        return temporal_risks
    
    def _predict_pattern_risks(self):
        """パターン認識による予測"""
        pattern_risks = {
            "high_probability": [],
            "medium_probability": [],
            "emerging_patterns": []
        }
        
        # Phase 1で学習したパターンの分析
        if "pattern_recognition" in self.phase1_insights:
            pattern_data = self.phase1_insights["pattern_recognition"]
            pattern_count = pattern_data.get("recognized_patterns", 0)
            
            if pattern_count < 10:
                pattern_risks["emerging_patterns"].append({
                    "type": "pattern_insufficiency",
                    "description": "Low pattern recognition coverage",
                    "risk_level": "medium",
                    "mitigation": "Expand tag_rules.yaml"
                })
        
        # 成功率データからのリスク予測
        if "fix_success_rates" in self.phase1_insights:
            fix_rates = self.phase1_insights["fix_success_rates"]
            
            # YAML修正の頻度から将来のYAML問題を予測
            yaml_fixes = fix_rates.get("yaml_fixes", 0)
            if yaml_fixes > 2:
                pattern_risks["high_probability"].append({
                    "type": "yaml_syntax_issues",
                    "description": "Frequent YAML fixes indicate ongoing syntax challenges",
                    "probability": 0.75,
                    "impact": "medium"
                })
            
            # Context警告の頻度
            context_warnings = fix_rates.get("context_warnings", 0)
            if context_warnings > 5:
                pattern_risks["high_probability"].append({
                    "type": "github_actions_context_issues", 
                    "description": "High context warning frequency suggests template issues",
                    "probability": 0.85,
                    "impact": "low"
                })
        
        return pattern_risks
    
    def _integrate_risk_assessments(self, file_risks, temporal_risks, pattern_risks):
        """リスク評価の統合"""
        integrated = {
            "high_risk_issues": [],
            "medium_risk_issues": [],
            "low_risk_issues": [],
            "risk_summary": {}
        }
        
        # ファイルリスクの統合
        for file, risk_data in file_risks.items():
            risk_level = "high" if risk_data["risk_score"] > 0.7 else \
                        "medium" if risk_data["risk_score"] > 0.4 else "low"
            
            issue = {
                "type": "file_risk",
                "target": file,
                "risk_score": risk_data["risk_score"],
                "factors": risk_data["risk_factors"],
                "confidence": risk_data["confidence"]
            }
            
            integrated[f"{risk_level}_risk_issues"].append(issue)
        
        # パターンリスクの統合
        for risk in pattern_risks["high_probability"]:
            integrated["high_risk_issues"].append({
                "type": "pattern_risk",
                "description": risk["description"],
                "probability": risk["probability"],
                "impact": risk["impact"]
            })
        
        # 時系列リスクの統合
        for risk in temporal_risks["time_based_risks"]:
            integrated["medium_risk_issues"].append({
                "type": "temporal_risk",
                "description": f"Predicted {risk['predicted_count']} issues in {risk['timeframe']}",
                "confidence": risk["confidence"]
            })
        
        # サマリー作成
        integrated["risk_summary"] = {
            "total_high_risk": len(integrated["high_risk_issues"]),
            "total_medium_risk": len(integrated["medium_risk_issues"]),
            "total_low_risk": len(integrated["low_risk_issues"]),
            "overall_risk_level": self._calculate_overall_risk(integrated)
        }
        
        return integrated
    
    def _calculate_overall_risk(self, integrated):
        """全体リスクレベルの計算"""
        high_count = len(integrated["high_risk_issues"])
        medium_count = len(integrated["medium_risk_issues"])
        
        if high_count > 3:
            return "high"
        elif high_count > 0 or medium_count > 5:
            return "medium"
        else:
            return "low"
    
    def _generate_preventive_actions(self, integrated_risks):
        """予防的アクションの生成"""
        actions = []
        
        # 高リスク問題への対応
        for issue in integrated_risks["high_risk_issues"]:
            if issue["type"] == "file_risk":
                actions.append({
                    "priority": "high",
                    "action": f"Review and refactor {issue['target']}",
                    "reason": ", ".join(issue["factors"]),
                    "estimated_effort": "30 minutes"
                })
            
            elif issue["type"] == "pattern_risk":
                if "yaml" in issue["description"].lower():
                    actions.append({
                        "priority": "high", 
                        "action": "Implement YAML validation in pre-commit hooks",
                        "reason": issue["description"],
                        "estimated_effort": "45 minutes"
                    })
                
                elif "context" in issue["description"].lower():
                    actions.append({
                        "priority": "medium",
                        "action": "Create GitHub Actions context usage guidelines",
                        "reason": issue["description"],
                        "estimated_effort": "20 minutes"
                    })
        
        # パターン不足への対応
        if integrated_risks["risk_summary"]["total_high_risk"] + integrated_risks["risk_summary"]["total_medium_risk"] < 3:
            actions.append({
                "priority": "low",
                "action": "Expand pattern recognition rules",
                "reason": "Low risk diversity suggests insufficient pattern coverage",
                "estimated_effort": "15 minutes"
            })
        
        return actions
    
    def generate_prediction_report(self, target_files=None, prediction_days=7):
        """予測レポートの生成"""
        predictions = self.predict_future_issues(target_files, prediction_days)
        
        print(f"\n📅 Prediction Horizon: {prediction_days} days")
        print(f"🎯 Analysis Timestamp: {predictions['timestamp']}")
        print()
        
        # リスクサマリー
        risk_summary = predictions["risk_assessment"]
        overall_risk = risk_summary["overall_risk_level"]
        
        risk_icon = "🔴" if overall_risk == "high" else "🟡" if overall_risk == "medium" else "🟢"
        print(f"🎯 Overall Risk Level: {risk_icon} {overall_risk.upper()}")
        print()
        
        print(f"📊 Risk Distribution:")
        print(f"  High Risk Issues: {risk_summary['total_high_risk']}")
        print(f"  Medium Risk Issues: {risk_summary['total_medium_risk']}")  
        print(f"  Low Risk Issues: {risk_summary['total_low_risk']}")
        print()
        
        # 主要な予測問題
        if predictions["predicted_issues"]:
            print("🚨 High Priority Predictions:")
            print("-" * 35)
            for i, issue in enumerate(predictions["predicted_issues"][:3], 1):
                print(f"{i}. {issue.get('description', issue.get('target', 'Unknown issue'))}")
                if 'factors' in issue:
                    print(f"   Factors: {', '.join(issue['factors'][:2])}")
                if 'probability' in issue:
                    print(f"   Probability: {issue['probability']:.1%}")
                print()
        
        # 推奨予防アクション
        if predictions["preventive_actions"]:
            print("🛡️ Recommended Preventive Actions:")
            print("-" * 38)
            for i, action in enumerate(predictions["preventive_actions"][:3], 1):
                priority_icon = "🔴" if action["priority"] == "high" else "🟡" if action["priority"] == "medium" else "🟢"
                print(f"{i}. {priority_icon} {action['action']}")
                print(f"   Effort: {action['estimated_effort']}")
                print(f"   Reason: {action['reason']}")
                print()
        
        # JSONファイルに保存
        os.makedirs("out", exist_ok=True)
        with open("out/issue_predictions.json", 'w') as f:
            json.dump(predictions, f, indent=2)
        
        print(f"📄 Detailed predictions saved: out/issue_predictions.json")
        
        return predictions

def main():
    predictor = IssuePredictionEngine()
    predictor.generate_prediction_report(prediction_days=7)

if __name__ == "__main__":
    main()


