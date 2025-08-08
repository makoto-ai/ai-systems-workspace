#!/usr/bin/env python3
"""
🧠 Learning & Prediction Engine - 学習・予測機能システム
改善案2: 過去の問題パターン学習、問題発生予測、自動改善提案
"""

import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import datetime
import re


class LearningPredictionEngine:
    """学習・予測エンジン"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / "data"
        self.models_dir = self.data_dir / "models"
        self.learning_dir = self.data_dir / "learning"

        # ディレクトリ作成
        self.data_dir.mkdir(exist_ok=True)
        self.models_dir.mkdir(exist_ok=True)
        self.learning_dir.mkdir(exist_ok=True)

        # 学習データ
        self.problem_patterns = defaultdict(list)
        self.threat_history = []
        self.repair_history = []

        print("🧠 学習・予測エンジン初期化完了")

    def collect_historical_data(self) -> Dict[str, Any]:
        """過去のデータ収集"""
        print("📊 過去のデータ収集開始...")

        historical_data = {
            "security_reports": [],
            "threat_patterns": [],
            "repair_records": [],
            "system_events": [],
        }

        # セキュリティレポートの収集
        report_files = list(self.data_dir.glob("*security_report*.json"))
        for report_file in report_files:
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    report_data = json.load(f)
                    historical_data["security_reports"].append(report_data)
            except Exception as e:
                print(f"⚠️ レポート読み込みエラー {report_file}: {e}")

        # ログファイルからパターン抽出
        log_files = list(self.data_dir.glob("*.log"))
        for log_file in log_files:
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    log_content = f.read()

                # エラーパターンの抽出
                error_patterns = re.findall(r"ERROR.*", log_content)
                warning_patterns = re.findall(r"WARNING.*", log_content)

                historical_data["system_events"].extend(
                    [
                        {"type": "error", "message": pattern, "file": str(log_file)}
                        for pattern in error_patterns
                    ]
                )
                historical_data["system_events"].extend(
                    [
                        {"type": "warning", "message": pattern, "file": str(log_file)}
                        for pattern in warning_patterns
                    ]
                )

            except Exception as e:
                print(f"⚠️ ログ読み込みエラー {log_file}: {e}")

        print(
            f"📊 データ収集完了: {len(historical_data['security_reports'])}件のレポート"
        )
        return historical_data

    def learn_problem_patterns(self, historical_data: Dict[str, Any]) -> Dict[str, Any]:
        """問題パターンの学習"""
        print("🧠 問題パターン学習開始...")

        patterns = {
            "frequent_threats": Counter(),
            "error_sequences": [],
            "time_patterns": defaultdict(list),
            "file_patterns": defaultdict(list),
            "severity_trends": [],
        }

        # 脅威の頻度分析
        for report in historical_data["security_reports"]:
            vulnerabilities = report.get("vulnerabilities", {})
            for vuln_type, issues in vulnerabilities.items():
                patterns["frequent_threats"][vuln_type] += len(issues)

                for issue in issues:
                    file_path = issue.get("file", "")
                    severity = issue.get("severity", "MEDIUM")

                    # ファイルパターン分析
                    if file_path:
                        file_ext = Path(file_path).suffix
                        patterns["file_patterns"][file_ext].append(vuln_type)

                    # 重要度トレンド
                    patterns["severity_trends"].append(
                        {
                            "type": vuln_type,
                            "severity": severity,
                            "timestamp": report.get("scan_timestamp", ""),
                        }
                    )

        # 時間パターン分析
        for event in historical_data["system_events"]:
            event_type = event.get("type", "")
            message = event.get("message", "")

            # 時間帯別の問題発生パターン
            try:
                # ログメッセージから時刻抽出（簡易版）
                time_match = re.search(r"(\d{2}):(\d{2}):(\d{2})", message)
                if time_match:
                    hour = int(time_match.group(1))
                    patterns["time_patterns"][hour].append(event_type)
            except:
                pass

        # エラーシーケンス分析
        error_sequences = []
        current_sequence = []

        for event in historical_data["system_events"]:
            if event["type"] == "error":
                current_sequence.append(event["message"][:50])  # 最初の50文字
                if len(current_sequence) >= 3:
                    error_sequences.append(current_sequence.copy())
                    current_sequence = current_sequence[-2:]  # オーバーラップ
            else:
                if current_sequence:
                    current_sequence = []

        patterns["error_sequences"] = error_sequences

        # 学習結果保存
        patterns_file = (
            self.learning_dir
            / f"learned_patterns_{datetime.datetime.now().strftime('%Y%m%d')}.json"
        )
        with open(patterns_file, "w", encoding="utf-8") as f:
            # Counter オブジェクトを辞書に変換
            serializable_patterns = {
                "frequent_threats": dict(patterns["frequent_threats"]),
                "error_sequences": patterns["error_sequences"],
                "time_patterns": {
                    k: list(v) for k, v in patterns["time_patterns"].items()
                },
                "file_patterns": {
                    k: list(v) for k, v in patterns["file_patterns"].items()
                },
                "severity_trends": patterns["severity_trends"],
            }
            json.dump(serializable_patterns, f, ensure_ascii=False, indent=2)

        print(f"🧠 パターン学習完了: {patterns_file}")
        return patterns

    def predict_future_threats(
        self, patterns: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """将来の脅威予測"""
        print("🔮 将来脅威予測開始...")

        predictions = {
            "high_risk_threats": [],
            "predicted_timeframes": {},
            "risk_scores": {},
            "preventive_actions": [],
        }

        # 頻出脅威に基づく予測
        frequent_threats = patterns.get("frequent_threats", {})

        for threat_type, frequency in frequent_threats.items():
            if frequency > 2:  # 3回以上発生した脅威
                risk_score = min(95, frequency * 15)  # リスクスコア計算

                predictions["high_risk_threats"].append(
                    {
                        "threat_type": threat_type,
                        "risk_score": risk_score,
                        "frequency": frequency,
                        "prediction": f"{threat_type}の再発リスクが高い",
                    }
                )

                predictions["risk_scores"][threat_type] = risk_score

        # ファイルパターンに基づく予測
        file_patterns = patterns.get("file_patterns", {})
        current_files = self._get_current_file_structure()

        for file_ext, threat_types in file_patterns.items():
            if file_ext in current_files:
                file_count = current_files[file_ext]
                threat_likelihood = len(set(threat_types)) * file_count

                if threat_likelihood > 5:
                    predictions["high_risk_threats"].append(
                        {
                            "threat_type": f"{file_ext}_files_vulnerability",
                            "risk_score": min(90, threat_likelihood * 10),
                            "file_type": file_ext,
                            "file_count": file_count,
                            "prediction": f"{file_ext}ファイルでの脆弱性発生リスク",
                        }
                    )

        # 時間パターンに基づく予測
        time_patterns = patterns.get("time_patterns", {})
        current_hour = datetime.datetime.now().hour

        if str(current_hour) in time_patterns:
            hourly_events = time_patterns[str(current_hour)]
            if len(hourly_events) > 3:
                predictions["predicted_timeframes"][current_hour] = {
                    "risk_level": "HIGH",
                    "expected_events": len(hourly_events),
                    "prediction": f"{current_hour}時台は問題発生頻度が高い",
                }

        # 予防アクション生成
        predictions["preventive_actions"] = self._generate_preventive_actions(
            predictions
        )

        # 予測結果保存
        prediction_file = (
            self.learning_dir
            / f"threat_predictions_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(prediction_file, "w", encoding="utf-8") as f:
            json.dump(predictions, f, ensure_ascii=False, indent=2)

        print(
            f"🔮 脅威予測完了: {len(predictions['high_risk_threats'])}件の高リスク脅威を検出"
        )
        return predictions

    def generate_improvement_suggestions(
        self, patterns: Dict[str, Any], predictions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """自動改善提案生成"""
        print("💡 改善提案生成開始...")

        suggestions = {
            "immediate_actions": [],
            "long_term_improvements": [],
            "automation_opportunities": [],
            "monitoring_enhancements": [],
        }

        # 即座の対応が必要なアクション
        for threat in predictions["high_risk_threats"]:
            if threat["risk_score"] > 80:
                suggestions["immediate_actions"].append(
                    {
                        "priority": "HIGH",
                        "action": f'{threat["threat_type"]}の即座対応',
                        "description": f'リスクスコア{threat["risk_score"]}の脅威に対する緊急対応',
                        "estimated_time": "1-2時間",
                    }
                )

        # 長期改善提案
        frequent_threats = patterns.get("frequent_threats", {})

        for threat_type, frequency in frequent_threats.items():
            if frequency > 5:  # 非常に頻出する脅威
                suggestions["long_term_improvements"].append(
                    {
                        "priority": "MEDIUM",
                        "action": f"{threat_type}の根本的対策",
                        "description": f"{frequency}回発生した{threat_type}の根本原因解決",
                        "estimated_time": "1-2日",
                    }
                )

        # 自動化機会
        error_sequences = patterns.get("error_sequences", [])

        if len(error_sequences) > 3:
            suggestions["automation_opportunities"].append(
                {
                    "priority": "MEDIUM",
                    "action": "エラーシーケンス自動検知システム",
                    "description": f"{len(error_sequences)}個のエラーパターンを自動検知・対応",
                    "estimated_time": "半日",
                }
            )

        # 監視強化提案
        time_patterns = patterns.get("time_patterns", {})

        high_activity_hours = [
            hour for hour, events in time_patterns.items() if len(events) > 5
        ]

        if high_activity_hours:
            suggestions["monitoring_enhancements"].append(
                {
                    "priority": "LOW",
                    "action": f"{len(high_activity_hours)}時間帯の監視強化",
                    "description": f'高活動時間帯（{", ".join(high_activity_hours)}時）の監視頻度向上',
                    "estimated_time": "30分",
                }
            )

        # 改善効果予測
        suggestions["expected_benefits"] = {
            "risk_reduction": f'{len(suggestions["immediate_actions"]) * 20}%',
            "efficiency_improvement": f'{len(suggestions["automation_opportunities"]) * 30}%',
            "monitoring_coverage": f'{len(suggestions["monitoring_enhancements"]) * 15}%',
        }

        # 提案保存
        suggestions_file = (
            self.learning_dir
            / f"improvement_suggestions_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(suggestions_file, "w", encoding="utf-8") as f:
            json.dump(suggestions, f, ensure_ascii=False, indent=2)

        print(f"💡 改善提案生成完了: {suggestions_file}")
        return suggestions

    def _get_current_file_structure(self) -> Dict[str, int]:
        """現在のファイル構造取得"""
        file_counts = defaultdict(int)

        for file_path in self.project_root.glob("**/*"):
            if file_path.is_file():
                ext = file_path.suffix
                if ext:
                    file_counts[ext] += 1

        return dict(file_counts)

    def _generate_preventive_actions(self, predictions: Dict[str, Any]) -> List[str]:
        """予防アクション生成"""
        actions = []

        for threat in predictions["high_risk_threats"]:
            threat_type = threat["threat_type"]

            if "sql_injection" in threat_type:
                actions.append("パラメータ化クエリの使用を徹底する")
            elif "hardcoded_secrets" in threat_type:
                actions.append("環境変数への秘密情報移行を実施する")
            elif "dependency" in threat_type:
                actions.append("依存関係の定期的なアップデートを実施する")
            elif "command_injection" in threat_type:
                actions.append("ユーザー入力の厳格な検証を実装する")
            else:
                actions.append(f"{threat_type}に対する予防的セキュリティ強化")

        return list(set(actions))  # 重複除去

    def run_learning_cycle(self) -> Dict[str, Any]:
        """学習サイクル実行"""
        print("🔄 学習サイクル開始...")

        # データ収集
        historical_data = self.collect_historical_data()

        # パターン学習
        patterns = self.learn_problem_patterns(historical_data)

        # 脅威予測
        current_state = {"timestamp": datetime.datetime.now().isoformat()}
        predictions = self.predict_future_threats(patterns, current_state)

        # 改善提案
        suggestions = self.generate_improvement_suggestions(patterns, predictions)

        # 統合レポート生成
        learning_report = {
            "cycle_timestamp": datetime.datetime.now().isoformat(),
            "data_summary": {
                "reports_analyzed": len(historical_data["security_reports"]),
                "events_processed": len(historical_data["system_events"]),
                "patterns_learned": len(patterns["frequent_threats"]),
                "threats_predicted": len(predictions["high_risk_threats"]),
                "suggestions_generated": (
                    len(suggestions["immediate_actions"])
                    + len(suggestions["long_term_improvements"])
                    + len(suggestions["automation_opportunities"])
                ),
            },
            "patterns": patterns,
            "predictions": predictions,
            "suggestions": suggestions,
        }

        # レポート保存
        report_file = (
            self.learning_dir
            / f"learning_cycle_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w", encoding="utf-8") as f:
            # Counter オブジェクトの処理
            if "frequent_threats" in learning_report["patterns"]:
                learning_report["patterns"]["frequent_threats"] = dict(
                    learning_report["patterns"]["frequent_threats"]
                )
            json.dump(learning_report, f, ensure_ascii=False, indent=2)

        print(f"🔄 学習サイクル完了: {report_file}")
        return learning_report


if __name__ == "__main__":
    # 学習・予測エンジン実行
    engine = LearningPredictionEngine()

    print("🧠 学習・予測エンジン開始")

    # 学習サイクル実行
    report = engine.run_learning_cycle()

    # 結果表示
    summary = report["data_summary"]
    print(f"\n📊 学習サイクル結果:")
    print(f"分析レポート数: {summary['reports_analyzed']}件")
    print(f"処理イベント数: {summary['events_processed']}件")
    print(f"学習パターン数: {summary['patterns_learned']}件")
    print(f"予測脅威数: {summary['threats_predicted']}件")
    print(f"改善提案数: {summary['suggestions_generated']}件")

    if report["suggestions"]["immediate_actions"]:
        print(f"\n🚨 即座対応が必要:")
        for action in report["suggestions"]["immediate_actions"][:3]:
            print(f"- {action['action']}: {action['description']}")

    print("\n🎉 学習・予測エンジン完了！")
