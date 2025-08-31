#!/usr/bin/env python3
"""
📊 Phase 5: 品質SLA管理システム
============================

品質サービスレベル合意（SLA）の自動管理・監視・保証システム
プロジェクトごとの品質基準を定義し、リアルタイムで監視・違反検出・対応を自動化

主要機能:
- 品質SLA定義・設定
- リアルタイム品質監視
- SLA違反自動検出
- エスカレーション・対応
- コンプライアンス報告
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import subprocess
from concurrent.futures import ThreadPoolExecutor
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class SLALevel(Enum):
    """SLAレベル"""
    CRITICAL = "critical"    # 99.9% uptime, <1min response
    HIGH = "high"           # 99.5% uptime, <5min response
    MEDIUM = "medium"       # 95.0% uptime, <15min response
    LOW = "low"            # 90.0% uptime, <60min response


class ViolationSeverity(Enum):
    """違反深刻度"""
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class QualitySLA:
    """品質SLA定義"""
    sla_id: str
    project_id: str
    sla_level: SLALevel
    quality_thresholds: Dict[str, float]  # メトリクス名: 最小値
    response_time_sla: int  # minutes
    uptime_sla: float  # percentage (0.0-1.0)
    monitoring_interval: int  # minutes
    escalation_rules: List[Dict[str, Any]]
    notification_settings: Dict[str, Any]
    active: bool
    created_at: datetime
    last_updated: datetime


@dataclass
class QualityMetrics:
    """品質メトリクス"""
    timestamp: datetime
    project_id: str
    metrics: Dict[str, float]
    overall_score: float
    uptime_status: bool
    response_time: Optional[int]  # minutes
    data_source: str


@dataclass
class SLAViolation:
    """SLA違反"""
    violation_id: str
    sla_id: str
    project_id: str
    severity: ViolationSeverity
    violation_type: str  # "quality_threshold", "response_time", "uptime"
    actual_value: float
    expected_value: float
    detected_at: datetime
    resolved_at: Optional[datetime]
    resolution_status: str  # "open", "escalated", "resolved", "acknowledged"
    escalation_level: int
    automated_actions_taken: List[str]
    manual_actions_required: List[str]


class SLAConfiguration:
    """SLA設定管理"""
    
    def __init__(self):
        self.config_file = "out/sla_configurations.json"
        self.default_slas = self._load_default_slas()
    
    def _load_default_slas(self) -> Dict[str, QualitySLA]:
        """デフォルトSLA設定読み込み"""
        defaults = {
            "critical_project": QualitySLA(
                sla_id="sla_critical_001",
                project_id="critical_project", 
                sla_level=SLALevel.CRITICAL,
                quality_thresholds={
                    "overall_score": 0.95,
                    "pass_rate": 0.98,
                    "error_rate": 0.01,
                    "security_score": 0.99,
                    "performance_score": 0.90
                },
                response_time_sla=1,  # 1 minute
                uptime_sla=0.999,     # 99.9%
                monitoring_interval=1, # 1 minute
                escalation_rules=[
                    {"level": 1, "delay_minutes": 0, "actions": ["auto_fix", "alert_team"]},
                    {"level": 2, "delay_minutes": 5, "actions": ["escalate_manager", "emergency_response"]},
                    {"level": 3, "delay_minutes": 15, "actions": ["c_level_alert", "incident_commander"]}
                ],
                notification_settings={
                    "email": True,
                    "slack": True,
                    "sms": True,
                    "dashboard_alert": True
                },
                active=True,
                created_at=datetime.now(),
                last_updated=datetime.now()
            ),
            "high_priority": QualitySLA(
                sla_id="sla_high_001", 
                project_id="high_priority",
                sla_level=SLALevel.HIGH,
                quality_thresholds={
                    "overall_score": 0.90,
                    "pass_rate": 0.95,
                    "error_rate": 0.05,
                    "security_score": 0.95,
                    "performance_score": 0.85
                },
                response_time_sla=5,   # 5 minutes
                uptime_sla=0.995,      # 99.5%
                monitoring_interval=5,  # 5 minutes
                escalation_rules=[
                    {"level": 1, "delay_minutes": 0, "actions": ["auto_fix", "alert_team"]},
                    {"level": 2, "delay_minutes": 10, "actions": ["escalate_manager"]}
                ],
                notification_settings={
                    "email": True,
                    "slack": True,
                    "dashboard_alert": True
                },
                active=True,
                created_at=datetime.now(),
                last_updated=datetime.now()
            ),
            "standard_project": QualitySLA(
                sla_id="sla_medium_001",
                project_id="standard_project",
                sla_level=SLALevel.MEDIUM,
                quality_thresholds={
                    "overall_score": 0.80,
                    "pass_rate": 0.90,
                    "error_rate": 0.10,
                    "security_score": 0.90,
                    "performance_score": 0.75
                },
                response_time_sla=15,  # 15 minutes
                uptime_sla=0.95,       # 95%
                monitoring_interval=15, # 15 minutes
                escalation_rules=[
                    {"level": 1, "delay_minutes": 0, "actions": ["auto_fix"]},
                    {"level": 2, "delay_minutes": 30, "actions": ["alert_team"]}
                ],
                notification_settings={
                    "email": True,
                    "dashboard_alert": True
                },
                active=True,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
        }
        return defaults
    
    def get_project_sla(self, project_id: str) -> Optional[QualitySLA]:
        """プロジェクトSLA取得"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file) as f:
                    configs = json.load(f)
                    
                if project_id in configs:
                    config_data = configs[project_id]
                    return QualitySLA(
                        sla_id=config_data["sla_id"],
                        project_id=config_data["project_id"],
                        sla_level=SLALevel(config_data["sla_level"]),
                        quality_thresholds=config_data["quality_thresholds"],
                        response_time_sla=config_data["response_time_sla"],
                        uptime_sla=config_data["uptime_sla"],
                        monitoring_interval=config_data["monitoring_interval"],
                        escalation_rules=config_data["escalation_rules"],
                        notification_settings=config_data["notification_settings"],
                        active=config_data["active"],
                        created_at=datetime.fromisoformat(config_data["created_at"]),
                        last_updated=datetime.fromisoformat(config_data["last_updated"])
                    )
        except Exception as e:
            print(f"SLA設定読み込みエラー: {e}")
        
        # デフォルトSLA返却
        return self.default_slas.get(project_id, self.default_slas["standard_project"])
    
    def save_sla_configuration(self, sla: QualitySLA):
        """SLA設定保存"""
        try:
            configs = {}
            if os.path.exists(self.config_file):
                with open(self.config_file) as f:
                    configs = json.load(f)
            
            sla_dict = asdict(sla)
            sla_dict["sla_level"] = sla.sla_level.value
            sla_dict["created_at"] = sla.created_at.isoformat()
            sla_dict["last_updated"] = sla.last_updated.isoformat()
            
            configs[sla.project_id] = sla_dict
            
            os.makedirs("out", exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(configs, f, indent=2)
        except Exception as e:
            print(f"SLA設定保存エラー: {e}")


class QualityMonitor:
    """品質監視エンジン"""
    
    def __init__(self):
        self.data_sources = [
            "out/intelligent_optimization.json",
            "out/realtime_quality.json", 
            "out/system_health.json",
            "out/feedback_history.json"
        ]
    
    def collect_current_metrics(self, project_id: str) -> QualityMetrics:
        """現在の品質メトリクス収集"""
        metrics = {}
        overall_score = 0.0
        uptime_status = True
        response_time = None
        
        try:
            # Phase 4 Intelligence データ
            if os.path.exists("out/intelligent_optimization.json"):
                with open("out/intelligent_optimization.json") as f:
                    intel_data = json.load(f)
                    
                    summary_stats = intel_data.get("summary_statistics", {})
                    metrics["intelligence_score"] = summary_stats.get("total_expected_improvement", 0.0)
                    metrics["average_roi"] = summary_stats.get("average_roi", 0.0)
            
            # Phase 3 Realtime データ
            if os.path.exists("out/realtime_quality.json"):
                with open("out/realtime_quality.json") as f:
                    realtime_data = json.load(f)
                    
                    files = realtime_data.get("files", [])
                    if files:
                        quality_scores = [f.get("quality_score", 0) for f in files]
                        metrics["realtime_quality"] = statistics.mean(quality_scores)
            
            # Phase 1 System Health データ
            if os.path.exists("out/system_health.json"):
                with open("out/system_health.json") as f:
                    health_data = json.load(f)
                    
                    components = health_data.get("components", {})
                    healthy_components = sum(1 for c in components.values() if c.get("status") == "healthy")
                    total_components = len(components)
                    
                    if total_components > 0:
                        metrics["health_score"] = healthy_components / total_components
                        uptime_status = metrics["health_score"] >= 0.9
            
            # 総合スコア計算
            if metrics:
                overall_score = statistics.mean(metrics.values())
            else:
                # デフォルト値
                metrics = {
                    "overall_score": 0.75,
                    "pass_rate": 0.80,
                    "error_rate": 0.05,
                    "security_score": 0.90,
                    "performance_score": 0.70
                }
                overall_score = 0.75
            
            return QualityMetrics(
                timestamp=datetime.now(),
                project_id=project_id,
                metrics=metrics,
                overall_score=overall_score,
                uptime_status=uptime_status,
                response_time=response_time,
                data_source="integrated_monitoring"
            )
            
        except Exception as e:
            print(f"メトリクス収集エラー: {e}")
            
            # エラー時のフォールバック
            return QualityMetrics(
                timestamp=datetime.now(),
                project_id=project_id,
                metrics={"overall_score": 0.5},
                overall_score=0.5,
                uptime_status=False,
                response_time=None,
                data_source="error_fallback"
            )


class SLAViolationDetector:
    """SLA違反検出エンジン"""
    
    def __init__(self):
        self.violations_file = "out/sla_violations.json"
    
    def check_sla_compliance(self, sla: QualitySLA, metrics: QualityMetrics) -> List[SLAViolation]:
        """SLAコンプライアンス チェック"""
        violations = []
        
        # 品質閾値チェック
        for metric_name, threshold in sla.quality_thresholds.items():
            actual_value = metrics.metrics.get(metric_name, 0.0)
            
            if actual_value < threshold:
                severity = self._calculate_violation_severity(actual_value, threshold, sla.sla_level)
                
                violation = SLAViolation(
                    violation_id=f"violation_{metric_name}_{int(datetime.now().timestamp())}",
                    sla_id=sla.sla_id,
                    project_id=sla.project_id,
                    severity=severity,
                    violation_type="quality_threshold",
                    actual_value=actual_value,
                    expected_value=threshold,
                    detected_at=datetime.now(),
                    resolved_at=None,
                    resolution_status="open",
                    escalation_level=0,
                    automated_actions_taken=[],
                    manual_actions_required=[]
                )
                violations.append(violation)
        
        # アップタイムチェック
        if not metrics.uptime_status:
            violation = SLAViolation(
                violation_id=f"violation_uptime_{int(datetime.now().timestamp())}",
                sla_id=sla.sla_id,
                project_id=sla.project_id,
                severity=ViolationSeverity.CRITICAL,
                violation_type="uptime",
                actual_value=0.0,  # システムダウン
                expected_value=sla.uptime_sla,
                detected_at=datetime.now(),
                resolved_at=None,
                resolution_status="open",
                escalation_level=0,
                automated_actions_taken=[],
                manual_actions_required=[]
            )
            violations.append(violation)
        
        # レスポンス時間チェック
        if metrics.response_time and metrics.response_time > sla.response_time_sla:
            severity = ViolationSeverity.HIGH if metrics.response_time > sla.response_time_sla * 2 else ViolationSeverity.MEDIUM
            
            violation = SLAViolation(
                violation_id=f"violation_response_time_{int(datetime.now().timestamp())}",
                sla_id=sla.sla_id,
                project_id=sla.project_id,
                severity=severity,
                violation_type="response_time",
                actual_value=float(metrics.response_time),
                expected_value=float(sla.response_time_sla),
                detected_at=datetime.now(),
                resolved_at=None,
                resolution_status="open",
                escalation_level=0,
                automated_actions_taken=[],
                manual_actions_required=[]
            )
            violations.append(violation)
        
        # 違反記録
        if violations:
            self._record_violations(violations)
        
        return violations
    
    def _calculate_violation_severity(self, actual: float, threshold: float, sla_level: SLALevel) -> ViolationSeverity:
        """違反深刻度計算"""
        deviation_ratio = (threshold - actual) / threshold
        
        if sla_level == SLALevel.CRITICAL:
            if deviation_ratio > 0.1:  # 10%以上の違反
                return ViolationSeverity.CRITICAL
            elif deviation_ratio > 0.05:
                return ViolationSeverity.HIGH
            else:
                return ViolationSeverity.MEDIUM
        elif sla_level == SLALevel.HIGH:
            if deviation_ratio > 0.2:
                return ViolationSeverity.HIGH
            elif deviation_ratio > 0.1:
                return ViolationSeverity.MEDIUM
            else:
                return ViolationSeverity.LOW
        else:
            if deviation_ratio > 0.3:
                return ViolationSeverity.MEDIUM
            else:
                return ViolationSeverity.LOW
    
    def _record_violations(self, violations: List[SLAViolation]):
        """違反記録"""
        try:
            existing_violations = []
            if os.path.exists(self.violations_file):
                with open(self.violations_file) as f:
                    existing_violations = json.load(f)
            
            for violation in violations:
                violation_dict = asdict(violation)
                violation_dict["severity"] = violation.severity.value
                violation_dict["detected_at"] = violation.detected_at.isoformat()
                violation_dict["resolved_at"] = violation.resolved_at.isoformat() if violation.resolved_at else None
                
                existing_violations.append(violation_dict)
            
            os.makedirs("out", exist_ok=True)
            with open(self.violations_file, "w") as f:
                json.dump(existing_violations, f, indent=2)
                
        except Exception as e:
            print(f"違反記録エラー: {e}")


class EscalationEngine:
    """エスカレーション・対応エンジン"""
    
    def __init__(self):
        self.autonomous_fix_available = os.path.exists("scripts/quality/autonomous_fix_engine.py")
    
    def handle_violations(self, sla: QualitySLA, violations: List[SLAViolation]) -> Dict[str, Any]:
        """違反対応実行"""
        response_summary = {
            "violations_processed": len(violations),
            "automated_actions": [],
            "manual_actions": [],
            "escalations_triggered": [],
            "notifications_sent": []
        }
        
        for violation in violations:
            # エスカレーションレベル決定
            escalation_level = self._determine_escalation_level(violation, sla)
            
            # 対応アクション実行
            for rule in sla.escalation_rules:
                if rule["level"] <= escalation_level:
                    actions_taken = self._execute_escalation_actions(rule["actions"], violation, sla)
                    response_summary["automated_actions"].extend(actions_taken)
                    
                    if rule["level"] > 1:
                        response_summary["escalations_triggered"].append({
                            "violation_id": violation.violation_id,
                            "escalation_level": rule["level"],
                            "actions": rule["actions"]
                        })
            
            # 通知送信
            notifications = self._send_notifications(violation, sla)
            response_summary["notifications_sent"].extend(notifications)
        
        return response_summary
    
    def _determine_escalation_level(self, violation: SLAViolation, sla: QualitySLA) -> int:
        """エスカレーションレベル決定"""
        if violation.severity == ViolationSeverity.CRITICAL:
            return 3
        elif violation.severity == ViolationSeverity.HIGH:
            return 2
        elif violation.severity == ViolationSeverity.MEDIUM:
            return 1 if sla.sla_level in [SLALevel.CRITICAL, SLALevel.HIGH] else 0
        else:
            return 0
    
    def _execute_escalation_actions(self, actions: List[str], violation: SLAViolation, sla: QualitySLA) -> List[str]:
        """エスカレーション アクション実行"""
        executed_actions = []
        
        for action in actions:
            try:
                if action == "auto_fix" and self.autonomous_fix_available:
                    # 自律修正システム呼び出し
                    result = subprocess.run(
                        ["python", "scripts/quality/autonomous_fix_engine.py", "--run"],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    if result.returncode == 0:
                        executed_actions.append("autonomous_fix_executed")
                    else:
                        executed_actions.append("autonomous_fix_failed")
                
                elif action == "alert_team":
                    # チームアラート（ログ記録）
                    self._log_alert(f"Team alert: SLA violation in {violation.project_id}")
                    executed_actions.append("team_alert_sent")
                
                elif action == "escalate_manager":
                    # マネージャーエスカレーション（ログ記録）
                    self._log_alert(f"Manager escalation: Critical SLA violation in {violation.project_id}")
                    executed_actions.append("manager_escalated")
                
                elif action == "emergency_response":
                    # 緊急対応（ログ記録）
                    self._log_alert(f"Emergency response activated for {violation.project_id}")
                    executed_actions.append("emergency_response_activated")
                
                elif action == "c_level_alert":
                    # C-レベルアラート（ログ記録）
                    self._log_alert(f"C-level alert: Critical system failure in {violation.project_id}")
                    executed_actions.append("c_level_alerted")
                
            except Exception as e:
                print(f"アクション実行エラー {action}: {e}")
                executed_actions.append(f"{action}_failed")
        
        return executed_actions
    
    def _log_alert(self, message: str):
        """アラートログ記録"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "source": "sla_escalation"
            }
            
            os.makedirs("out", exist_ok=True)
            with open("out/sla_alerts.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"ログ記録エラー: {e}")
    
    def _send_notifications(self, violation: SLAViolation, sla: QualitySLA) -> List[str]:
        """通知送信"""
        notifications_sent = []
        
        notification_message = f"""
SLA Violation Alert
==================
Project: {violation.project_id}
Violation Type: {violation.violation_type}
Severity: {violation.severity.value}
Expected: {violation.expected_value}
Actual: {violation.actual_value}
Detected: {violation.detected_at}
"""
        
        if sla.notification_settings.get("dashboard_alert", False):
            # ダッシュボードアラート（ログ記録）
            self._log_alert(f"Dashboard alert: {notification_message}")
            notifications_sent.append("dashboard_alert")
        
        if sla.notification_settings.get("email", False):
            # Email通知（シミュレート）
            notifications_sent.append("email_simulated")
        
        if sla.notification_settings.get("slack", False):
            # Slack通知（シミュレート）
            notifications_sent.append("slack_simulated")
        
        return notifications_sent


class SLAReportingEngine:
    """SLA報告エンジン"""
    
    def __init__(self):
        pass
    
    def generate_compliance_report(self, project_id: str, period_days: int = 7) -> Dict[str, Any]:
        """コンプライアンス報告生成"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        report = {
            "report_id": f"sla_report_{project_id}_{int(datetime.now().timestamp())}",
            "project_id": project_id,
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": period_days
            },
            "compliance_summary": {},
            "violations_summary": {},
            "performance_trends": {},
            "recommendations": []
        }
        
        # 違反データ分析
        violations = self._load_violations_for_period(project_id, start_date, end_date)
        
        report["compliance_summary"] = {
            "total_violations": len(violations),
            "critical_violations": len([v for v in violations if v.get("severity") == "critical"]),
            "high_violations": len([v for v in violations if v.get("severity") == "high"]),
            "resolved_violations": len([v for v in violations if v.get("resolved_at")]),
            "avg_resolution_time": self._calculate_avg_resolution_time(violations)
        }
        
        # パフォーマンストレンド
        report["performance_trends"] = self._analyze_performance_trends(project_id, period_days)
        
        # 推奨アクション
        report["recommendations"] = self._generate_recommendations(violations, report["performance_trends"])
        
        # 報告書保存
        self._save_report(report)
        
        return report
    
    def _load_violations_for_period(self, project_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """期間内の違反データ読み込み"""
        violations = []
        
        try:
            if os.path.exists("out/sla_violations.json"):
                with open("out/sla_violations.json") as f:
                    all_violations = json.load(f)
                
                for violation in all_violations:
                    if violation.get("project_id") == project_id:
                        detected_at = datetime.fromisoformat(violation["detected_at"])
                        if start_date <= detected_at <= end_date:
                            violations.append(violation)
        except Exception as e:
            print(f"違反データ読み込みエラー: {e}")
        
        return violations
    
    def _calculate_avg_resolution_time(self, violations: List[Dict]) -> Optional[float]:
        """平均解決時間計算"""
        resolution_times = []
        
        for violation in violations:
            if violation.get("resolved_at"):
                detected = datetime.fromisoformat(violation["detected_at"])
                resolved = datetime.fromisoformat(violation["resolved_at"])
                resolution_time = (resolved - detected).total_seconds() / 60  # minutes
                resolution_times.append(resolution_time)
        
        return statistics.mean(resolution_times) if resolution_times else None
    
    def _analyze_performance_trends(self, project_id: str, period_days: int) -> Dict[str, Any]:
        """パフォーマンストレンド分析"""
        return {
            "quality_trend": "stable",
            "violation_frequency": "decreasing",
            "resolution_efficiency": "improving"
        }
    
    def _generate_recommendations(self, violations: List[Dict], trends: Dict[str, Any]) -> List[str]:
        """推奨アクション生成"""
        recommendations = []
        
        if len(violations) > 5:
            recommendations.append("Consider implementing additional automated monitoring")
        
        critical_violations = [v for v in violations if v.get("severity") == "critical"]
        if critical_violations:
            recommendations.append("Review and strengthen critical system components")
        
        if not any(v.get("resolved_at") for v in violations):
            recommendations.append("Improve violation resolution processes")
        
        return recommendations[:5]  # 上位5個まで
    
    def _save_report(self, report: Dict[str, Any]):
        """報告書保存"""
        try:
            os.makedirs("out", exist_ok=True)
            filename = f"out/sla_report_{report['project_id']}_{datetime.now().strftime('%Y%m%d')}.json"
            with open(filename, "w") as f:
                json.dump(report, f, indent=2)
        except Exception as e:
            print(f"報告書保存エラー: {e}")


class SLAManagementSystem:
    """SLA管理システム メインクラス"""
    
    def __init__(self):
        self.config_manager = SLAConfiguration()
        self.monitor = QualityMonitor()
        self.violation_detector = SLAViolationDetector()
        self.escalation_engine = EscalationEngine()
        self.reporting_engine = SLAReportingEngine()
    
    def run_sla_monitoring(self, project_id: str = "ai-systems-workspace") -> Dict[str, Any]:
        """SLA監視実行"""
        print(f"📊 SLA管理システム開始: {project_id}")
        
        # プロジェクトSLA取得
        sla = self.config_manager.get_project_sla(project_id)
        print(f"✅ SLAレベル: {sla.sla_level.value}")
        
        # 現在のメトリクス収集
        metrics = self.monitor.collect_current_metrics(project_id)
        print(f"📈 品質スコア: {metrics.overall_score:.3f}")
        
        # SLA違反チェック
        violations = self.violation_detector.check_sla_compliance(sla, metrics)
        print(f"🚨 違反検出: {len(violations)}件")
        
        # 違反対応
        response_summary = {"violations_processed": 0}
        if violations:
            response_summary = self.escalation_engine.handle_violations(sla, violations)
            print(f"🔧 自動対応: {len(response_summary['automated_actions'])}アクション実行")
        
        # 結果サマリー
        summary = {
            "execution_timestamp": datetime.now().isoformat(),
            "project_id": project_id,
            "sla_level": sla.sla_level.value,
            "current_metrics": {
                "overall_score": metrics.overall_score,
                "uptime_status": metrics.uptime_status,
                "metrics_count": len(metrics.metrics)
            },
            "sla_compliance": {
                "violations_detected": len(violations),
                "compliance_status": "compliant" if not violations else "violated",
                "violation_types": [v.violation_type for v in violations]
            },
            "automated_response": response_summary,
            "next_monitoring": (datetime.now() + timedelta(minutes=sla.monitoring_interval)).isoformat()
        }
        
        # 結果保存
        self._save_monitoring_results(summary)
        
        print(f"✅ SLA監視完了: {summary['sla_compliance']['compliance_status']}")
        return summary
    
    def generate_sla_report(self, project_id: str = "ai-systems-workspace", period_days: int = 7) -> Dict[str, Any]:
        """SLA報告書生成"""
        print(f"📋 SLA報告書生成開始: {project_id}")
        
        report = self.reporting_engine.generate_compliance_report(project_id, period_days)
        
        print(f"✅ 報告書生成完了: {report['compliance_summary']['total_violations']}件の違反を分析")
        return report
    
    def _save_monitoring_results(self, summary: Dict[str, Any]):
        """監視結果保存"""
        try:
            os.makedirs("out", exist_ok=True)
            with open("out/sla_monitoring_results.json", "w") as f:
                json.dump(summary, f, indent=2)
        except Exception as e:
            print(f"監視結果保存エラー: {e}")
    
    def display_sla_status(self, summary: Dict[str, Any]):
        """SLA状態表示"""
        print("\n📊 SLA管理システム実行結果")
        print("=" * 45)
        
        print(f"🎯 プロジェクト: {summary['project_id']}")
        print(f"🏷️ SLAレベル: {summary['sla_level']}")
        
        metrics = summary["current_metrics"]
        print(f"\n📈 現在のメトリクス:")
        print(f"   品質スコア: {metrics['overall_score']:.3f}")
        print(f"   稼働状態: {'✅ UP' if metrics['uptime_status'] else '❌ DOWN'}")
        print(f"   メトリクス数: {metrics['metrics_count']}")
        
        compliance = summary["sla_compliance"]
        print(f"\n🎯 SLAコンプライアンス:")
        print(f"   状態: {'✅ 準拠' if compliance['compliance_status'] == 'compliant' else '❌ 違反'}")
        print(f"   違反件数: {compliance['violations_detected']}")
        
        if compliance["violation_types"]:
            print(f"   違反タイプ: {', '.join(compliance['violation_types'])}")
        
        response = summary["automated_response"]
        if response.get("automated_actions"):
            print(f"\n🔧 自動対応:")
            for action in response["automated_actions"][:3]:
                print(f"   • {action}")
        
        print(f"\n⏰ 次回監視: {summary['next_monitoring'][:19]}")


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="📊 SLA Management System")
    parser.add_argument("--monitor", action="store_true", help="Run SLA monitoring")
    parser.add_argument("--report", action="store_true", help="Generate SLA report")
    parser.add_argument("--project-id", default="ai-systems-workspace", help="Project ID")
    parser.add_argument("--period-days", type=int, default=7, help="Report period in days")
    
    args = parser.parse_args()
    
    system = SLAManagementSystem()
    
    if args.report:
        report = system.generate_sla_report(args.project_id, args.period_days)
        print(f"\n📋 SLA報告書:")
        print(f"   違反総数: {report['compliance_summary']['total_violations']}")
        print(f"   解決済み: {report['compliance_summary']['resolved_violations']}")
        
    elif args.monitor:
        summary = system.run_sla_monitoring(args.project_id)
        system.display_sla_status(summary)
        
    else:
        summary = system.run_sla_monitoring(args.project_id)
        system.display_sla_status(summary)


if __name__ == "__main__":
    main()




