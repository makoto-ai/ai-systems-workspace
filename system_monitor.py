#!/usr/bin/env python3
"""
🔍 AI Systems Monitor
作成日: 2025-08-04
目的: システム監視とメトリクス収集
"""

import os
import time
import psutil  # type: ignore
import logging
import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST  # type: ignore
from fastapi import Response, WebSocket  # type: ignore
import threading
import queue

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemMonitor:
    """システム監視クラス"""
    
    def __init__(self):
        # Prometheusメトリクス
        self.request_counter = Counter(
            'ai_systems_requests_total',
            'Total number of requests',
            ['endpoint', 'method', 'status']
        )
        
        self.request_duration = Histogram(
            'ai_systems_request_duration_seconds',
            'Request duration in seconds',
            ['endpoint', 'method']
        )
        
        self.error_counter = Counter(
            'ai_systems_errors_total',
            'Total number of errors',
            ['endpoint', 'error_type']
        )
        
        self.cpu_usage = Gauge(
            'ai_systems_cpu_usage_percent',
            'CPU usage percentage'
        )
        
        self.memory_usage = Gauge(
            'ai_systems_memory_usage_percent',
            'Memory usage percentage'
        )
        
        self.disk_usage = Gauge(
            'ai_systems_disk_usage_percent',
            'Disk usage percentage'
        )
        
        self.active_connections = Gauge(
            'ai_systems_active_connections',
            'Number of active connections'
        )
        
        self.system_health = Gauge(
            'ai_systems_health_status',
            'System health status (1=healthy, 0=unhealthy)'
        )
        
        # 監視データ
        self.metrics_history = []
        self.alert_history = []
        self.health_history = []
        self.performance_history = []
        self._monitoring_started = False
        
        # アラート設定
        self.alert_thresholds = {
            'cpu_critical': 90,
            'cpu_warning': 80,
            'memory_critical': 95,
            'memory_warning': 85,
            'disk_critical': 95,
            'disk_warning': 90,
            'response_time_critical': 5.0,  # 秒
            'response_time_warning': 2.0    # 秒
        }
        
        # 監視設定
        self.monitoring_config = {
            'metrics_retention_hours': 24,
            'alert_cooldown_minutes': 5,
            'max_history_size': 1000
        }
        
        # WebSocket接続管理
        self.active_connections: List[WebSocket] = []
        self.websocket_lock = asyncio.Lock()
        
        # リアルタイムデータ配信
        self.real_time_data_queue = queue.Queue(maxsize=100)
        self.real_time_thread = None
        self.real_time_running = False
        
        # 監視イベント
        self.monitoring_events = {
            'critical_alerts': [],
            'performance_spikes': [],
            'system_changes': []
        }
    
    def start_monitoring(self):
        """監視開始"""
        if self._monitoring_started:
            logger.info("監視は既に開始されています")
            return
            
        logger.info("システム監視を開始しました")
        self._monitoring_started = True
        
        # イベントループが実行中の場合のみタスクを作成
        try:
            loop = asyncio.get_running_loop()
            if not hasattr(self, '_metrics_task') or self._metrics_task.done():
                self._metrics_task = asyncio.create_task(self.collect_system_metrics())
            if not hasattr(self, '_health_task') or self._health_task.done():
                self._health_task = asyncio.create_task(self.check_system_health())
            logger.info("監視タスクを作成しました")
        except RuntimeError:
            # イベントループが実行されていない場合は、後で開始する
            logger.info("イベントループが実行されていないため、監視タスクの開始を延期します")
        except Exception as e:
            logger.error(f"監視開始エラー: {e}")
            self._monitoring_started = False
    
    async def ensure_monitoring_started(self):
        """監視が開始されていることを確認"""
        if not self._monitoring_started:
            self.start_monitoring()
            # 少し待ってからタスクを開始
            await asyncio.sleep(0.1)
            try:
                loop = asyncio.get_running_loop()
                if not hasattr(self, '_metrics_task') or self._metrics_task.done():
                    self._metrics_task = asyncio.create_task(self.collect_system_metrics())
                if not hasattr(self, '_health_task') or self._health_task.done():
                    self._health_task = asyncio.create_task(self.check_system_health())
                logger.info("監視タスクを開始しました")
            except RuntimeError:
                logger.warning("イベントループが利用できません")
            except Exception as e:
                logger.error(f"監視タスク開始エラー: {e}")
    
    async def collect_system_metrics(self):
        """システムメトリクス収集"""
        while self._monitoring_started:
            try:
                # システムメトリクスを取得
                metrics = self.get_system_metrics()

                # Prometheusメトリクスを更新（キー整合性修正）
                self.cpu_usage.set(metrics.get('cpu', {}).get('usage_percent', 0))
                self.memory_usage.set(metrics.get('memory', {}).get('percent', 0))
                self.disk_usage.set(metrics.get('disk', {}).get('percent', 0))

                # メトリクス履歴に追加
                record = {
                    'timestamp': datetime.now().isoformat(),
                    'metrics': metrics
                }
                self.metrics_history.append(record)

                # パフォーマンス記録を追加
                performance_data = {
                    'cpu_percent': metrics.get('cpu', {}).get('usage_percent', 0),
                    'memory_percent': metrics.get('memory', {}).get('percent', 0),
                    'disk_percent': metrics.get('disk', {}).get('percent', 0),
                    # 接続数は system メトリクスで提供
                    'active_connections': metrics.get('system', {}).get('connections', 0)
                }
                self.add_performance_record(performance_data)

                # アラートチェック
                alerts = self.check_alerts(performance_data)
                for alert in alerts:
                    self.record_alert(alert['type'], alert['message'])

                # 古いデータのクリーンアップ（60サンプル毎 ≒ 1時間）
                if len(self.metrics_history) % 60 == 0:
                    self.cleanup_old_data()

            except Exception as e:
                logger.error(f"メトリクス収集エラー: {e}")
            finally:
                # 失敗時も一定間隔で再試行
                await asyncio.sleep(60)

    async def check_system_health(self):
        """システム健全性チェック"""
        while self._monitoring_started:
            try:
                # 健全性サマリーを取得
                health_summary = self.get_health_summary()

                # 健全性記録を追加
                self.add_health_record(health_summary)

                # 健全性ステータスをPrometheusメトリクスに反映
                health_status = 1 if health_summary.get('status') == 'healthy' else 0
                self.system_health.set(health_status)

                # 警告やクリティカルアラートを記録
                for warning in health_summary.get('warnings', []):
                    self.record_alert('health_warning', warning)

                for critical in health_summary.get('critical_alerts', []):
                    self.record_alert('health_critical', critical)
            except Exception as e:
                logger.error(f"健全性チェックエラー: {e}")
            finally:
                await asyncio.sleep(300)  # 5分間隔
    
    def record_request(self, endpoint: str, method: str, status: int, duration: float):
        """リクエスト記録"""
        try:
            self.request_counter.labels(endpoint=endpoint, method=method, status=status).inc()
            self.request_duration.labels(endpoint=endpoint, method=method).observe(duration)

            if status >= 400:
                self.error_counter.labels(endpoint=endpoint, error_type=f"http_{status}").inc()
        except Exception as e:
            logger.error(f"リクエスト記録エラー: {e}")
                
    def record_error(self, endpoint: str, error_type: str):
        """エラー記録"""
        try:
            self.error_counter.labels(endpoint=endpoint, error_type=error_type).inc()
        except Exception as e:
            logger.error(f"エラー記録エラー: {e}")
    
    def record_alert(self, alert_type: str, message: str):
        """アラート記録"""
        alert = {
            'type': alert_type,
            'message': message,
                    'timestamp': datetime.now().isoformat(),
            'severity': 'warning' if 'warning' in alert_type.lower() else 'critical'
        }
        self.alert_history.append(alert)
        
        # 履歴サイズ制限
        if len(self.alert_history) > self.monitoring_config['max_history_size']:
            self.alert_history = self.alert_history[-self.monitoring_config['max_history_size']:]
        
        logger.warning(f"アラート記録: {alert_type} - {message}")

    def add_health_record(self, health_data: Dict[str, Any]):
        """健全性記録を追加"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'status': health_data.get('status', 'unknown'),
            'score': health_data.get('overall_score', 0),
            'metrics': health_data.get('metrics', {}),
            'warnings': health_data.get('warnings', []),
            'critical_alerts': health_data.get('critical_alerts', [])
        }
        self.health_history.append(record)
        
        # 履歴サイズ制限
        if len(self.health_history) > self.monitoring_config['max_history_size']:
            self.health_history = self.health_history[-self.monitoring_config['max_history_size']:]

    def add_performance_record(self, performance_data: Dict[str, Any]):
        """パフォーマンス記録を追加"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': performance_data.get('cpu_percent', 0),
            'memory_percent': performance_data.get('memory_percent', 0),
            'disk_percent': performance_data.get('disk_percent', 0),
            'response_time': performance_data.get('response_time', 0),
            'active_connections': performance_data.get('active_connections', 0)
        }
        self.performance_history.append(record)
        
        # 履歴サイズ制限
        if len(self.performance_history) > self.monitoring_config['max_history_size']:
            self.performance_history = self.performance_history[-self.monitoring_config['max_history_size']:]

    def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """アラートチェック"""
        alerts = []
        
        # CPU使用率アラート
        cpu_percent = metrics.get('cpu_percent', 0)
        if cpu_percent > self.alert_thresholds['cpu_critical']:
            alerts.append({
                'type': 'cpu_critical',
                'message': f'Critical CPU usage: {cpu_percent}%',
                'severity': 'critical',
                'value': cpu_percent,
                'threshold': self.alert_thresholds['cpu_critical']
            })
        elif cpu_percent > self.alert_thresholds['cpu_warning']:
            alerts.append({
                'type': 'cpu_warning',
                'message': f'High CPU usage: {cpu_percent}%',
                'severity': 'warning',
                'value': cpu_percent,
                'threshold': self.alert_thresholds['cpu_warning']
            })
        
        # メモリ使用率アラート
        memory_percent = metrics.get('memory_percent', 0)
        if memory_percent > self.alert_thresholds['memory_critical']:
            alerts.append({
                'type': 'memory_critical',
                'message': f'Critical memory usage: {memory_percent}%',
                'severity': 'critical',
                'value': memory_percent,
                'threshold': self.alert_thresholds['memory_critical']
            })
        elif memory_percent > self.alert_thresholds['memory_warning']:
            alerts.append({
                'type': 'memory_warning',
                'message': f'High memory usage: {memory_percent}%',
                'severity': 'warning',
                'value': memory_percent,
                'threshold': self.alert_thresholds['memory_warning']
            })
        
        # ディスク使用率アラート
        disk_percent = metrics.get('disk_percent', 0)
        if disk_percent > self.alert_thresholds['disk_critical']:
            alerts.append({
                'type': 'disk_critical',
                'message': f'Critical disk usage: {disk_percent:.1f}%',
                'severity': 'critical',
                'value': disk_percent,
                'threshold': self.alert_thresholds['disk_critical']
            })
        elif disk_percent > self.alert_thresholds['disk_warning']:
            alerts.append({
                'type': 'disk_warning',
                'message': f'High disk usage: {disk_percent:.1f}%',
                'severity': 'warning',
                'value': disk_percent,
                'threshold': self.alert_thresholds['disk_warning']
            })
        
        return alerts

    def get_performance_analysis(self) -> Dict[str, Any]:
        """パフォーマンス分析を取得"""
        try:
            if not self.performance_history:
                return {'error': 'No performance data available'}

            # 統計計算
            cpu_values = [record['cpu_percent'] for record in self.performance_history]
            memory_values = [record['memory_percent'] for record in self.performance_history]
            disk_values = [record['disk_percent'] for record in self.performance_history]

            analysis = {
                'cpu': {
                    'current': cpu_values[-1] if cpu_values else 0,
                    'average': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                    'max': max(cpu_values) if cpu_values else 0,
                    'min': min(cpu_values) if cpu_values else 0,
                    'trend': self._calculate_trend(cpu_values)
                },
                'memory': {
                    'current': memory_values[-1] if memory_values else 0,
                    'average': sum(memory_values) / len(memory_values) if memory_values else 0,
                    'max': max(memory_values) if memory_values else 0,
                    'min': min(memory_values) if memory_values else 0,
                    'trend': self._calculate_trend(memory_values)
                },
                'disk': {
                    'current': disk_values[-1] if disk_values else 0,
                    'average': sum(disk_values) / len(disk_values) if disk_values else 0,
                    'max': max(disk_values) if disk_values else 0,
                    'min': min(disk_values) if disk_values else 0,
                    'trend': self._calculate_trend(disk_values)
                },
                'data_points': len(self.performance_history),
                'time_range': self._get_time_range()
            }

            return analysis
        except Exception as e:
            logger.error(f"パフォーマンス分析エラー: {e}")
            return {'error': str(e)}

    def _calculate_trend(self, values: List[float]) -> str:
        """トレンドを計算"""
        if len(values) < 2:
            return 'stable'
        
        recent_avg = sum(values[-5:]) / len(values[-5:]) if len(values) >= 5 else values[-1]
        older_avg = sum(values[:5]) / len(values[:5]) if len(values) >= 5 else values[0]
        
        if recent_avg > older_avg * 1.1:
            return 'increasing'
        elif recent_avg < older_avg * 0.9:
            return 'decreasing'
        else:
            return 'stable'

    def _get_time_range(self) -> Dict[str, str]:
        """時間範囲を取得"""
        if not self.performance_history:
            return {'start': '', 'end': ''}
        
        start_time = self.performance_history[0]['timestamp']
        end_time = self.performance_history[-1]['timestamp']
        
        return {
            'start': start_time,
            'end': end_time
        }

    def get_health_trends(self) -> Dict[str, Any]:
        """健全性トレンドを取得"""
        try:
            if not self.health_history:
                return {'error': 'No health data available'}
            
            # ステータス分布
            status_counts = {}
            for record in self.health_history:
                status = record['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # スコアトレンド
            scores = [record['score'] for record in self.health_history]
            
            # 警告統計
            total_warnings = sum(len(record['warnings']) for record in self.health_history)
            total_critical = sum(len(record['critical_alerts']) for record in self.health_history)
            
            trends = {
                'status_distribution': status_counts,
                'score': {
                    'current': scores[-1] if scores else 0,
                    'average': sum(scores) / len(scores) if scores else 0,
                    'max': max(scores) if scores else 0,
                    'min': min(scores) if scores else 0,
                    'trend': self._calculate_trend(scores)
                },
                'alerts': {
                    'total_warnings': total_warnings,
                    'total_critical': total_critical,
                    'average_warnings_per_check': total_warnings / len(self.health_history) if self.health_history else 0
                },
                'data_points': len(self.health_history),
                'time_range': self._get_health_time_range()
            }
            
            return trends
        except Exception as e:
            logger.error(f"健全性トレンド取得エラー: {e}")
            return {'error': str(e)}

    def _get_health_time_range(self) -> Dict[str, str]:
        """健全性データの時間範囲を取得"""
        if not self.health_history:
            return {'start': '', 'end': ''}
        
        start_time = self.health_history[0]['timestamp']
        end_time = self.health_history[-1]['timestamp']
        
        return {
            'start': start_time,
            'end': end_time
        }

    def cleanup_old_data(self):
        """古いデータをクリーンアップ"""
        try:
            retention_hours = self.monitoring_config.get('metrics_retention_hours', 24)
            cutoff_time = datetime.now() - timedelta(hours=retention_hours)

            # メトリクス履歴のクリーンアップ
            self.metrics_history = [
                record for record in self.metrics_history
                if datetime.fromisoformat(record['timestamp']) > cutoff_time
            ]

            # パフォーマンス履歴のクリーンアップ
            self.performance_history = [
                record for record in self.performance_history
                if datetime.fromisoformat(record['timestamp']) > cutoff_time
            ]

            # 健全性履歴のクリーンアップ
            self.health_history = [
                record for record in self.health_history
                if datetime.fromisoformat(record['timestamp']) > cutoff_time
            ]

            logger.info(
                f"古いデータをクリーンアップしました: {len(self.metrics_history)} メトリクス, "
                f"{len(self.performance_history)} パフォーマンス, {len(self.health_history)} 健全性記録"
            )
        except Exception as e:
            logger.error(f"データクリーンアップエラー: {e}")

    def get_system_recommendations(self) -> List[str]:
        """システム推奨事項を取得"""
        recommendations = []
        try:
            # 最新の健全性データを取得
            if self.health_history:
                latest_health = self.health_history[-1]
                
                # CPU推奨事項
                cpu_percent = latest_health.get('metrics', {}).get('cpu_percent', 0)
                if cpu_percent > 70:
                    recommendations.append("CPU使用率が高いため、プロセスの最適化を検討してください")
                
                # メモリ推奨事項
                memory_percent = latest_health.get('metrics', {}).get('memory_percent', 0)
                if memory_percent > 80:
                    recommendations.append("メモリ使用率が高いため、メモリリークの確認やリソース解放を検討してください")
                
                # ディスク推奨事項
                disk_percent = latest_health.get('metrics', {}).get('disk_percent', 0)
                if disk_percent > 85:
                    recommendations.append("ディスク使用率が高いため、不要ファイルの削除やストレージ拡張を検討してください")
                
                # スコア推奨事項
                score = latest_health.get('score', 100)
                if score < 70:
                    recommendations.append("システム健全性スコアが低いため、全体的なシステム最適化を検討してください")
                elif score < 85:
                    recommendations.append("システム健全性スコアが中程度のため、継続的な監視を推奨します")
            
            # パフォーマンス分析からの推奨事項
            performance_analysis = self.get_performance_analysis()
            if 'error' not in performance_analysis:
                cpu_trend = performance_analysis.get('cpu', {}).get('trend', 'stable')
                if cpu_trend == 'increasing':
                    recommendations.append("CPU使用率が上昇傾向のため、負荷分散やスケーリングを検討してください")
                
                memory_trend = performance_analysis.get('memory', {}).get('trend', 'stable')
                if memory_trend == 'increasing':
                    recommendations.append("メモリ使用率が上昇傾向のため、メモリ管理の見直しを検討してください")
            
            if not recommendations:
                recommendations.append("システムは良好な状態です。継続的な監視を維持してください")
        except Exception as e:
            logger.error(f"推奨事項取得エラー: {e}")
            recommendations.append("推奨事項の取得中にエラーが発生しました")

        return recommendations

    # WebSocket接続管理
    async def connect_websocket(self, websocket: WebSocket):
        """WebSocket接続を追加"""
        await websocket.accept()
        async with self.websocket_lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket接続追加: 総接続数 {len(self.active_connections)}")

    async def disconnect_websocket(self, websocket: WebSocket):
        """WebSocket接続を削除"""
        async with self.websocket_lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket接続削除: 総接続数 {len(self.active_connections)}")

    async def broadcast_to_websockets(self, message: Dict[str, Any]):
        """WebSocket接続にメッセージをブロードキャスト"""
        if not self.active_connections:
            return
        
        disconnected = []
        async with self.websocket_lock:
            for websocket in self.active_connections:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"WebSocket送信エラー: {e}")
                    disconnected.append(websocket)
            
            # 切断された接続を削除
            for websocket in disconnected:
                self.active_connections.remove(websocket)
        
        if disconnected:
            logger.info(f"切断されたWebSocket接続: {len(disconnected)}")

    def start_real_time_monitoring(self):
        """リアルタイム監視開始"""
        if self.real_time_running:
            return
        
        self.real_time_running = True
        self.real_time_thread = threading.Thread(target=self._real_time_monitoring_loop, daemon=True)
        self.real_time_thread.start()
        logger.info("リアルタイム監視を開始しました")

    def stop_real_time_monitoring(self):
        """リアルタイム監視停止"""
        self.real_time_running = False
        if self.real_time_thread:
            self.real_time_thread.join(timeout=5)
        logger.info("リアルタイム監視を停止しました")

    def _real_time_monitoring_loop(self):
        """リアルタイム監視ループ"""
        while self.real_time_running:
            try:
                # リアルタイムデータを収集
                real_time_data = self._collect_real_time_data()
                
                # WebSocket接続に配信
                asyncio.run(self.broadcast_to_websockets(real_time_data))
                
                # イベント検出
                self._detect_monitoring_events(real_time_data)
                
                time.sleep(5)  # 5秒間隔
                
            except Exception as e:
                logger.error(f"リアルタイム監視エラー: {e}")
                time.sleep(10)

    def _collect_real_time_data(self) -> Dict[str, Any]:
        """リアルタイムデータを収集"""
        try:
            # 基本メトリクス
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # ネットワーク情報
            net_io = psutil.net_io_counters()
            
            # プロセス情報
            processes = len(list(psutil.process_iter()))
            
            # システムロード
            load_avg = os.getloadavg()
            
            real_time_data = {
                'timestamp': datetime.now().isoformat(),
                'metrics': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': (disk.used / disk.total) * 100,
                    'network_bytes_sent': net_io.bytes_sent,
                    'network_bytes_recv': net_io.bytes_recv,
                    'process_count': processes,
                    'load_1min': load_avg[0],
                    'load_5min': load_avg[1],
                    'load_15min': load_avg[2]
                },
                'status': self._get_real_time_status(cpu_percent, memory.percent, (disk.used / disk.total) * 100),
                'alerts': self._get_real_time_alerts(cpu_percent, memory.percent, (disk.used / disk.total) * 100)
            }
            
            return real_time_data
            
        except Exception as e:
            logger.error(f"リアルタイムデータ収集エラー: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }

    def _get_real_time_status(self, cpu_percent: float, memory_percent: float, disk_percent: float) -> str:
        """リアルタイムステータスを取得"""
        if cpu_percent > 90 or memory_percent > 95 or disk_percent > 95:
            return 'critical'
        elif cpu_percent > 80 or memory_percent > 85 or disk_percent > 90:
            return 'warning'
        else:
            return 'healthy'

    def _get_real_time_alerts(self, cpu_percent: float, memory_percent: float, disk_percent: float) -> List[Dict[str, Any]]:
        """リアルタイムアラートを取得"""
        alerts = []
        
        if cpu_percent > 90:
            alerts.append({
                'type': 'cpu_critical',
                'message': f'Critical CPU usage: {cpu_percent}%',
                'severity': 'critical',
                'value': cpu_percent
            })
        elif cpu_percent > 80:
            alerts.append({
                'type': 'cpu_warning',
                'message': f'High CPU usage: {cpu_percent}%',
                'severity': 'warning',
                'value': cpu_percent
            })
        
        if memory_percent > 95:
            alerts.append({
                'type': 'memory_critical',
                'message': f'Critical memory usage: {memory_percent}%',
                'severity': 'critical',
                'value': memory_percent
            })
        elif memory_percent > 85:
            alerts.append({
                'type': 'memory_warning',
                'message': f'High memory usage: {memory_percent}%',
                'severity': 'warning',
                'value': memory_percent
            })
        if disk_percent > 95:
            alerts.append({
                'type': 'disk_critical',
                'message': f'Critical disk usage: {disk_percent:.1f}%',
                'severity': 'critical',
                'value': disk_percent
            })
        elif disk_percent > 90:
            alerts.append({
                'type': 'disk_warning',
                'message': f'High disk usage: {disk_percent:.1f}%',
                'severity': 'warning',
                'value': disk_percent
            })
        
        return alerts

    def _detect_monitoring_events(self, real_time_data: Dict[str, Any]):
        """監視イベントを検出"""
        try:
            metrics = real_time_data.get('metrics', {})
            alerts = real_time_data.get('alerts', [])

            # クリティカルアラートの検出
            critical_alerts = [alert for alert in alerts if alert.get('severity') == 'critical']
            if critical_alerts:
                self.monitoring_events['critical_alerts'].extend(critical_alerts)
                # 履歴サイズ制限
                if len(self.monitoring_events['critical_alerts']) > 50:
                    self.monitoring_events['critical_alerts'] = self.monitoring_events['critical_alerts'][-50:]
            
            # パフォーマンススパイクの検出
            cpu_percent = metrics.get('cpu_percent', 0)
            if cpu_percent > 95:
                self.monitoring_events['performance_spikes'].append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'cpu_spike',
                    'value': cpu_percent
                })
                # 履歴サイズ制限
                if len(self.monitoring_events['performance_spikes']) > 20:
                    self.monitoring_events['performance_spikes'] = self.monitoring_events['performance_spikes'][-20:]
            
            # システム変更の検出
            memory_percent = metrics.get('memory_percent', 0)
            if memory_percent > 90:
                self.monitoring_events['system_changes'].append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'memory_pressure',
                    'value': memory_percent
                })
                # 履歴サイズ制限
                if len(self.monitoring_events['system_changes']) > 30:
                    self.monitoring_events['system_changes'] = self.monitoring_events['system_changes'][-30:]
        except Exception as e:
            logger.error(f"監視イベント検出エラー: {e}")

    def get_monitoring_events(self) -> Dict[str, Any]:
        """監視イベントを取得"""
        return {
            'critical_alerts': self.monitoring_events['critical_alerts'][-10:],  # 最新10件
            'performance_spikes': self.monitoring_events['performance_spikes'][-5:],  # 最新5件
            'system_changes': self.monitoring_events['system_changes'][-10:],  # 最新10件
            'total_events': {
                'critical_alerts': len(self.monitoring_events['critical_alerts']),
                'performance_spikes': len(self.monitoring_events['performance_spikes']),
                'system_changes': len(self.monitoring_events['system_changes'])
            }
        }

    def get_predictive_analysis(self) -> Dict[str, Any]:
        """予測分析を取得"""
        try:
            if len(self.performance_history) < 10:
                return {'error': 'Insufficient data for predictive analysis'}
            
            # トレンド分析
            cpu_trend = self._analyze_trend([record['cpu_percent'] for record in self.performance_history])
            memory_trend = self._analyze_trend([record['memory_percent'] for record in self.performance_history])
            disk_trend = self._analyze_trend([record['disk_percent'] for record in self.performance_history])
            
            # 予測計算
            predictions = {
                'cpu': self._predict_next_value([record['cpu_percent'] for record in self.performance_history]),
                'memory': self._predict_next_value([record['memory_percent'] for record in self.performance_history]),
                'disk': self._predict_next_value([record['disk_percent'] for record in self.performance_history])
            }
            
            # 異常検出
            anomalies = self._detect_anomalies()
            
            return {
                'trends': {
                    'cpu': cpu_trend,
                    'memory': memory_trend,
                    'disk': disk_trend
                },
                'predictions': predictions,
                'anomalies': anomalies,
                'confidence_level': self._calculate_confidence_level()
            }
        except Exception as e:
            logger.error(f"予測分析エラー: {e}")
            return {'error': str(e)}

    def _analyze_trend(self, values: List[float]) -> Dict[str, Any]:
        """トレンド分析"""
        if len(values) < 2:
            return {'direction': 'stable', 'slope': 0, 'strength': 'weak'}
        
        # 線形回帰による傾き計算
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * val for i, val in enumerate(values))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        # トレンド強度の計算
        mean_y = y_sum / n
        ss_tot = sum((val - mean_y) ** 2 for val in values)
        ss_res = sum((val - (slope * i + (y_sum / n - slope * x_sum / n))) ** 2 for i, val in enumerate(values))
        
        if ss_tot == 0:
            r_squared = 0
        else:
            r_squared = 1 - (ss_res / ss_tot)
        
        # 方向と強度の判定
        if abs(slope) < 0.1:
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
        
        if r_squared > 0.7:
            strength = 'strong'
        elif r_squared > 0.3:
            strength = 'moderate'
        else:
            strength = 'weak'
        
        return {
            'direction': direction,
            'slope': slope,
            'strength': strength,
            'r_squared': r_squared
        }

    def _predict_next_value(self, values: List[float]) -> Dict[str, Any]:
        """次の値を予測"""
        if len(values) < 5:
            return {'predicted': 0, 'confidence': 0, 'range': [0, 0]}
        
        # 移動平均による予測
        recent_values = values[-5:]
        predicted = sum(recent_values) / len(recent_values)
        
        # 信頼区間の計算
        variance = sum((val - predicted) ** 2 for val in recent_values) / len(recent_values)
        std_dev = variance ** 0.5
        
        confidence_range = [max(0, predicted - 2 * std_dev), min(100, predicted + 2 * std_dev)]
        
        # 信頼度の計算
        trend_consistency = 1 - (std_dev / predicted) if predicted > 0 else 0
        confidence = max(0, min(1, trend_consistency))
        
        return {
            'predicted': predicted,
            'confidence': confidence,
            'range': confidence_range,
            'std_dev': std_dev
        }

    def _detect_anomalies(self) -> List[Dict[str, Any]]:
        """異常検出"""
        anomalies = []
        try:
            if len(self.performance_history) < 10:
                return anomalies
            
            # 統計的異常検出
            cpu_values = [record['cpu_percent'] for record in self.performance_history]
            memory_values = [record['memory_percent'] for record in self.performance_history]
            disk_values = [record['disk_percent'] for record in self.performance_history]
            
            # CPU異常検出
            cpu_mean = sum(cpu_values) / len(cpu_values)
            cpu_std = (sum((val - cpu_mean) ** 2 for val in cpu_values) / len(cpu_values)) ** 0.5
            
            for i, val in enumerate(cpu_values[-5:]):  # 最新5件をチェック
                if abs(val - cpu_mean) > 2 * cpu_std:
                    anomalies.append({
                        'type': 'cpu_anomaly',
                        'value': val,
                        'expected_range': [cpu_mean - 2 * cpu_std, cpu_mean + 2 * cpu_std],
                        'severity': 'high' if abs(val - cpu_mean) > 3 * cpu_std else 'medium',
                        'timestamp': self.performance_history[-(5-i)]['timestamp']
                    })
            
            # メモリ異常検出
            memory_mean = sum(memory_values) / len(memory_values)
            memory_std = (sum((val - memory_mean) ** 2 for val in memory_values) / len(memory_values)) ** 0.5
            
            for i, val in enumerate(memory_values[-5:]):
                if abs(val - memory_mean) > 2 * memory_std:
                    anomalies.append({
                        'type': 'memory_anomaly',
                        'value': val,
                        'expected_range': [memory_mean - 2 * memory_std, memory_mean + 2 * memory_std],
                        'severity': 'high' if abs(val - memory_mean) > 3 * memory_std else 'medium',
                        'timestamp': self.performance_history[-(5-i)]['timestamp']
                    })
            
            # 急激な変化の検出
            if len(cpu_values) >= 3:
                recent_cpu_change = abs(cpu_values[-1] - cpu_values[-2])
                if recent_cpu_change > 20:  # 20%以上の急激な変化
                    anomalies.append({
                        'type': 'sudden_cpu_change',
                        'change': recent_cpu_change,
                        'from': cpu_values[-2],
                        'to': cpu_values[-1],
                        'severity': 'high' if recent_cpu_change > 30 else 'medium',
                        'timestamp': self.performance_history[-1]['timestamp']
                    })
        except Exception as e:
            logger.error(f"異常検出エラー: {e}")

        return anomalies

    def _calculate_confidence_level(self) -> float:
        """信頼度レベルを計算"""
        try:
            if len(self.performance_history) < 10:
                return 0.5
            
            # データの一貫性を評価
            cpu_values = [record['cpu_percent'] for record in self.performance_history]
            memory_values = [record['memory_percent'] for record in self.performance_history]
            
            # 変動係数の計算
            cpu_mean = sum(cpu_values) / len(cpu_values)
            cpu_cv = (sum((val - cpu_mean) ** 2 for val in cpu_values) / len(cpu_values)) ** 0.5 / cpu_mean if cpu_mean > 0 else 0
            
            memory_mean = sum(memory_values) / len(memory_values)
            memory_cv = (sum((val - memory_mean) ** 2 for val in memory_values) / len(memory_values)) ** 0.5 / memory_mean if memory_mean > 0 else 0
            
            # 信頼度の計算（変動が少ないほど信頼度が高い）
            confidence = max(0, min(1, 1 - (cpu_cv + memory_cv) / 2))
            
            return confidence
            
        except Exception as e:
            logger.error(f"信頼度計算エラー: {e}")
            return 0.5

    def get_security_audit(self) -> Dict[str, Any]:
        """セキュリティ監査を実行"""
        try:
            audit_results = {
                'timestamp': datetime.now().isoformat(),
                'checks': [],
                'overall_score': 100,
                'recommendations': []
            }

            # ファイル権限チェック
            critical_files = [
                ('/etc/passwd', 0o644),
                ('/etc/shadow', 0o600),
                ('/etc/sudoers', 0o440)
            ]

            for file_path, expected_perms in critical_files:
                if os.path.exists(file_path):
                    try:
                        stat = os.stat(file_path)
                        actual_perms = stat.st_mode & 0o777
                        if actual_perms != expected_perms:
                            audit_results['checks'].append({
                                'type': 'file_permissions',
                                'file': file_path,
                                'expected': oct(expected_perms),
                                'actual': oct(actual_perms),
                                'status': 'warning',
                                'score_deduction': 10
                            })
                            audit_results['overall_score'] -= 10
                        else:
                            audit_results['checks'].append({
                                'type': 'file_permissions',
                                'file': file_path,
                                'status': 'pass',
                                'score_deduction': 0
                            })
                    except Exception as e:
                        audit_results['checks'].append({
                            'type': 'file_permissions',
                            'file': file_path,
                            'status': 'error',
                            'error': str(e),
                            'score_deduction': 5
                        })
                        audit_results['overall_score'] -= 5

            # 環境変数セキュリティチェック
            sensitive_vars = ['API_KEY', 'SECRET', 'PASSWORD', 'TOKEN', 'PRIVATE_KEY']
            for var in sensitive_vars:
                if os.environ.get(var):
                    audit_results['checks'].append({
                        'type': 'environment_variables',
                        'variable': var,
                        'status': 'warning',
                        'message': f'Sensitive environment variable {var} is set',
                        'score_deduction': 5
                    })
                    audit_results['overall_score'] -= 5

            # プロセスセキュリティチェック
            try:
                current_process = psutil.Process()
                if current_process.username() == 'root':
                    audit_results['checks'].append({
                        'type': 'process_security',
                        'status': 'warning',
                        'message': 'Process running as root',
                        'score_deduction': 15
                    })
                    audit_results['overall_score'] -= 15
                else:
                    audit_results['checks'].append({
                        'type': 'process_security',
                        'status': 'pass',
                        'message': 'Process running with appropriate privileges',
                        'score_deduction': 0
                    })
            except Exception as e:
                audit_results['checks'].append({
                    'type': 'process_security',
                    'status': 'error',
                    'error': str(e),
                    'score_deduction': 5
                })
                audit_results['overall_score'] -= 5

            # 推奨事項の生成
            if audit_results['overall_score'] < 80:
                audit_results['recommendations'].append("セキュリティスコアが低いため、セキュリティ設定の見直しを推奨します")

            for check in audit_results['checks']:
                if check['status'] == 'warning':
                    if check.get('type') == 'file_permissions':
                        audit_results['recommendations'].append(
                            f"ファイル {check['file']} の権限を {check.get('expected', '適切値')} に変更してください"
                        )
                    elif check.get('type') == 'environment_variables':
                        audit_results['recommendations'].append(
                            f"環境変数 {check['variable']} の使用を最小限に抑えてください"
                        )
                    elif check.get('type') == 'process_security':
                        audit_results['recommendations'].append("可能であれば、非特権ユーザーでプロセスを実行してください")

            return audit_results
        except Exception as e:
            logger.error(f"セキュリティ監査エラー: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'overall_score': 0
            }

    def get_auto_recovery_suggestions(self) -> List[Dict[str, Any]]:
        """自動修復提案を取得"""
        suggestions = []
        
        try:
            # 最新の健全性データを取得
            if self.health_history:
                latest_health = self.health_history[-1]
                metrics = latest_health.get('metrics', {})
                
                # CPU関連の修復提案
                cpu_percent = metrics.get('cpu_percent', 0)
                if cpu_percent > 80:
                    suggestions.append({
                        'type': 'cpu_optimization',
                        'priority': 'high' if cpu_percent > 90 else 'medium',
                        'action': 'process_optimization',
                        'description': f'CPU使用率が{cpu_percent}%と高いため、プロセスの最適化を実行してください',
                        'commands': [
                            'ps aux --sort=-%cpu | head -10',  # 高CPUプロセスを確認
                            'kill -TERM <PID>',  # 不要なプロセスを終了
                            'nice -n 10 <command>'  # プロセス優先度を下げる
                        ],
                        'automated': False
                    })
                
                # メモリ関連の修復提案
                memory_percent = metrics.get('memory_percent', 0)
                if memory_percent > 85:
                    suggestions.append({
                        'type': 'memory_cleanup',
                        'priority': 'high' if memory_percent > 95 else 'medium',
                        'action': 'memory_cleanup',
                        'description': f'メモリ使用率が{memory_percent}%と高いため、メモリクリーンアップを実行してください',
                        'commands': [
                            'sync && echo 3 > /proc/sys/vm/drop_caches',  # キャッシュクリア
                            'ps aux --sort=-%mem | head -10',  # 高メモリプロセスを確認
                            'kill -TERM <PID>'  # 不要なプロセスを終了
                        ],
                        'automated': True
                    })
                
                # ディスク関連の修復提案
                disk_percent = metrics.get('disk_percent', 0)
                if disk_percent > 85:
                    suggestions.append({
                        'type': 'disk_cleanup',
                        'priority': 'high' if disk_percent > 95 else 'medium',
                        'action': 'disk_cleanup',
                        'description': f'ディスク使用率が{disk_percent:.1f}%と高いため、ディスククリーンアップを実行してください',
                        'commands': [
                            'df -h',  # ディスク使用量を確認
                            'du -sh /* | sort -hr | head -10',  # 大容量ディレクトリを確認
                            'rm -rf /tmp/*',  # 一時ファイルを削除
                            'apt-get clean'  # パッケージキャッシュをクリア
                        ],
                        'automated': True
                    })
                
                # プロセス関連の修復提案
                if latest_health.get('processes', {}).get('zombie_processes', 0) > 0:
                    suggestions.append({
                        'type': 'zombie_cleanup',
                        'priority': 'medium',
                        'action': 'zombie_cleanup',
                        'description': f'ゾンビプロセスが{latest_health["processes"]["zombie_processes"]}個検出されました',
                        'commands': [
                            'ps aux | grep -w Z',  # ゾンビプロセスを確認
                            'kill -9 <PPID>'  # 親プロセスを終了
                        ],
                        'automated': False
                    })
            
            # 予測分析からの修復提案
            predictive_analysis = self.get_predictive_analysis()
            if 'error' not in predictive_analysis:
                predictions = predictive_analysis.get('predictions', {})
                
                if predictions.get('cpu', {}).get('predicted', 0) > 90:
                    suggestions.append({
                        'type': 'predictive_cpu_warning',
                        'priority': 'medium',
                        'action': 'preventive_optimization',
                        'description': 'CPU使用率が上昇傾向のため、事前の最適化を推奨します',
                        'commands': [
                            'systemctl stop unnecessary-services',
                            'nice -n 15 <command>'
                        ],
                        'automated': False
                    })
                
                if predictions.get('memory', {}).get('predicted', 0) > 95:
                    suggestions.append({
                        'type': 'predictive_memory_warning',
                        'priority': 'high',
                        'action': 'preventive_memory_cleanup',
                        'description': 'メモリ使用率が上昇傾向のため、事前のクリーンアップを推奨します',
                        'commands': [
                            'sync && echo 3 > /proc/sys/vm/drop_caches',
                            'systemctl restart memory-intensive-services'
                        ],
                        'automated': True
                    })
            
        except Exception as e:
            logger.error(f"自動修復提案取得エラー: {e}")
            suggestions.append({
                'type': 'error',
                'priority': 'low',
                'action': 'error_recovery',
                'description': f'修復提案の取得中にエラーが発生しました: {e}',
                'commands': [],
                'automated': False
            })
        
        return suggestions

    def get_dashboard_html(self) -> str:
        """監視ダッシュボードHTMLを取得"""
        return """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Systems Monitor Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .header h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
            text-align: center;
        }
        
        .status-indicator {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 1.1em;
            margin: 10px;
        }
        
        .status-healthy { background: #2ecc71; color: white; }
        .status-warning { background: #f39c12; color: white; }
        .status-critical { background: #e74c3c; color: white; }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 10px 0;
            padding: 10px;
            background: rgba(52, 152, 219, 0.1);
            border-radius: 8px;
        }
        
        .metric-label {
            font-weight: 600;
            color: #2c3e50;
        }
        
        .metric-value {
            font-weight: bold;
            color: #3498db;
        }
        
        .alert {
            padding: 10px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid;
        }
        
        .alert-critical {
            background: rgba(231, 76, 60, 0.1);
            border-left-color: #e74c3c;
            color: #c0392b;
        }
        
        .alert-warning {
            background: rgba(243, 156, 18, 0.1);
            border-left-color: #f39c12;
            color: #d68910;
        }
        
        .chart-container {
            position: relative;
            height: 300px;
            margin: 20px 0;
        }
        
        .real-time-indicator {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(46, 204, 113, 0.9);
            color: white;
            padding: 10px 15px;
            border-radius: 20px;
            font-weight: bold;
            z-index: 1000;
        }
        
        .connection-status {
            position: fixed;
            top: 60px;
            right: 20px;
            padding: 8px 12px;
            border-radius: 15px;
            font-size: 0.9em;
            z-index: 1000;
        }
        
        .connected { background: rgba(46, 204, 113, 0.9); color: white; }
        .disconnected { background: rgba(231, 76, 60, 0.9); color: white; }
        
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="real-time-indicator">🔄 リアルタイム監視</div>
    <div class="connection-status" id="connectionStatus">接続中...</div>
    
    <div class="container">
        <div class="header">
            <h1>🤖 AI Systems Monitor Dashboard</h1>
            <div style="text-align: center;">
                <span class="status-indicator" id="systemStatus">健全性チェック中...</span>
                <span class="status-indicator" id="scoreIndicator">スコア: --</span>
            </div>
        </div>
        
        <div class="dashboard-grid">
            <div class="card">
                <h3>📊 リアルタイムメトリクス</h3>
                <div class="metric">
                    <span class="metric-label">CPU使用率</span>
                    <span class="metric-value" id="cpuUsage">--%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">メモリ使用率</span>
                    <span class="metric-value" id="memoryUsage">--%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">ディスク使用率</span>
                    <span class="metric-value" id="diskUsage">--%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">プロセス数</span>
                    <span class="metric-value" id="processCount">--</span>
                </div>
                <div class="metric">
                    <span class="metric-label">システムロード</span>
                    <span class="metric-value" id="loadAverage">--</span>
                </div>
            </div>
            
            <div class="card">
                <h3>⚠️ アクティブアラート</h3>
                <div id="alertsContainer">
                    <p style="text-align: center; color: #7f8c8d;">アラートなし</p>
                </div>
            </div>
            
            <div class="card">
                <h3>📈 パフォーマンスグラフ</h3>
                <div class="chart-container">
                    <canvas id="performanceChart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <h3>🔍 監視イベント</h3>
                <div id="eventsContainer">
                    <p style="text-align: center; color: #7f8c8d;">イベントなし</p>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h3>📋 システム推奨事項</h3>
            <div id="recommendationsContainer">
                <p style="text-align: center; color: #7f8c8d;">推奨事項を読み込み中...</p>
            </div>
        </div>
    </div>

    <script>
        let websocket = null;
        let performanceChart = null;
        let performanceData = {
            labels: [],
            cpu: [],
            memory: [],
            disk: []
        };
        
        // WebSocket接続
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/monitor`;
            
            websocket = new WebSocket(wsUrl);
            
            websocket.onopen = function() {
                document.getElementById('connectionStatus').textContent = '接続済み';
                document.getElementById('connectionStatus').className = 'connection-status connected';
            };
            
            websocket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            websocket.onclose = function() {
                document.getElementById('connectionStatus').textContent = '切断中';
                document.getElementById('connectionStatus').className = 'connection-status disconnected';
                // 再接続を試行
                setTimeout(connectWebSocket, 5000);
            };
            
            websocket.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }
        
        // ダッシュボード更新
        function updateDashboard(data) {
            // メトリクス更新
            if (data.metrics) {
                document.getElementById('cpuUsage').textContent = data.metrics.cpu_percent.toFixed(1) + '%';
                document.getElementById('memoryUsage').textContent = data.metrics.memory_percent.toFixed(1) + '%';
                document.getElementById('diskUsage').textContent = data.metrics.disk_percent.toFixed(1) + '%';
                document.getElementById('processCount').textContent = data.metrics.process_count;
                document.getElementById('loadAverage').textContent = data.metrics.load_1min.toFixed(2);
            }
            
            // ステータス更新
            if (data.status) {
                const statusElement = document.getElementById('systemStatus');
                statusElement.textContent = data.status === 'healthy' ? '健全' : 
                                          data.status === 'warning' ? '警告' : 'クリティカル';
                statusElement.className = 'status-indicator status-' + data.status;
            }
            
            // アラート更新
            if (data.alerts && data.alerts.length > 0) {
                updateAlerts(data.alerts);
            }
            
            // パフォーマンスグラフ更新
            updatePerformanceChart(data);
        }
        
        // アラート更新
        function updateAlerts(alerts) {
            const container = document.getElementById('alertsContainer');
            container.innerHTML = '';
            
            alerts.forEach(alert => {
                const alertDiv = document.createElement('div');
                alertDiv.className = `alert alert-${alert.severity}`;
                alertDiv.innerHTML = `
                    <strong>${alert.type}:</strong> ${alert.message}
                    <br><small>値: ${alert.value}</small>
                `;
                container.appendChild(alertDiv);
            });
        }
        
        // パフォーマンスグラフ更新
        function updatePerformanceChart(data) {
            if (!data.metrics) return;
            
            const now = new Date().toLocaleTimeString();
            performanceData.labels.push(now);
            performanceData.cpu.push(data.metrics.cpu_percent);
            performanceData.memory.push(data.metrics.memory_percent);
            performanceData.disk.push(data.metrics.disk_percent);
            
            // データポイントを制限
            if (performanceData.labels.length > 20) {
                performanceData.labels.shift();
                performanceData.cpu.shift();
                performanceData.memory.shift();
                performanceData.disk.shift();
            }
            
            if (!performanceChart) {
                const ctx = document.getElementById('performanceChart').getContext('2d');
                performanceChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: performanceData.labels,
                        datasets: [
                            {
                                label: 'CPU (%)',
                                data: performanceData.cpu,
                                borderColor: '#e74c3c',
                                backgroundColor: 'rgba(231, 76, 60, 0.1)',
                                tension: 0.4
                            },
                            {
                                label: 'Memory (%)',
                                data: performanceData.memory,
                                borderColor: '#3498db',
                                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                                tension: 0.4
                            },
                            {
                                label: 'Disk (%)',
                                data: performanceData.disk,
                                borderColor: '#2ecc71',
                                backgroundColor: 'rgba(46, 204, 113, 0.1)',
                                tension: 0.4
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100
                            }
                        },
                        plugins: {
                            legend: {
                                position: 'top'
                            }
                        }
                    }
                });
            } else {
                performanceChart.data.labels = performanceData.labels;
                performanceChart.data.datasets[0].data = performanceData.cpu;
                performanceChart.data.datasets[1].data = performanceData.memory;
                performanceChart.data.datasets[2].data = performanceData.disk;
                performanceChart.update('none');
            }
        }
        
        // 推奨事項を読み込み
        async function loadRecommendations() {
            try {
                const response = await fetch('/system/recommendations');
                const data = await response.json();
                
                const container = document.getElementById('recommendationsContainer');
                container.innerHTML = '';
                
                if (data.recommendations && data.recommendations.length > 0) {
                    data.recommendations.forEach(rec => {
                        const recDiv = document.createElement('div');
                        recDiv.style.padding = '10px';
                        recDiv.style.margin = '5px 0';
                        recDiv.style.background = 'rgba(52, 152, 219, 0.1)';
                        recDiv.style.borderRadius = '8px';
                        recDiv.style.borderLeft = '4px solid #3498db';
                        recDiv.textContent = rec;
                        container.appendChild(recDiv);
                    });
                } else {
                    container.innerHTML = '<p style="text-align: center; color: #7f8c8d;">推奨事項なし</p>';
                }
            } catch (error) {
                console.error('推奨事項読み込みエラー:', error);
            }
        }
        
        // 初期化
        document.addEventListener('DOMContentLoaded', function() {
            connectWebSocket();
            loadRecommendations();
            
            // 定期的に推奨事項を更新
            setInterval(loadRecommendations, 30000);
        });
    </script>
</body>
</html>
        """
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクス取得"""
        try:
            # 現在のプロセスIDを取得
            current_pid = os.getpid()
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu': self._get_cpu_metrics(),
                'memory': self._get_memory_metrics(),
                'disk': self._get_disk_metrics(),
                'network': self._get_network_metrics(),
                'process': self._get_process_metrics(current_pid),
                'system': self._get_system_metrics()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"メトリクス取得エラー: {e}")
            return {'error': str(e)}
    
    def _get_cpu_metrics(self) -> Dict[str, Any]:
        """CPUメトリクス取得"""
        try:
            cpu_percent = psutil.cpu_percent()
            return {
                'usage_percent': cpu_percent,
                'count': psutil.cpu_count(),
                'frequency': self._get_cpu_frequency()
            }
        except Exception as e:
            logger.debug(f"CPUメトリクス取得エラー: {e}")
            return {'error': str(e)}
    
    def _get_memory_metrics(self) -> Dict[str, Any]:
        """メモリメトリクス取得"""
        try:
            memory = psutil.virtual_memory()
            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent
            }
        except Exception as e:
            logger.debug(f"メモリメトリクス取得エラー: {e}")
            return {'error': str(e)}
    
    def _get_disk_metrics(self) -> Dict[str, Any]:
        """ディスクメトリクス取得"""
        try:
            disk = psutil.disk_usage('/')
            return {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': (disk.used / disk.total) * 100
            }
        except Exception as e:
            logger.debug(f"ディスクメトリクス取得エラー: {e}")
            return {'error': str(e)}
    
    def _get_network_metrics(self) -> Dict[str, Any]:
        """ネットワークメトリクス取得"""
        try:
            network = psutil.net_io_counters()
            return {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
        except Exception as e:
            logger.debug(f"ネットワークメトリクス取得エラー: {e}")
            return {'error': str(e)}
    
    def _get_process_metrics(self, pid: int) -> Dict[str, Any]:
        """プロセスメトリクス取得"""
        try:
            process = psutil.Process(pid)
            
            # メモリ情報を安全に取得
            memory_info = None
            try:
                memory_info = process.memory_info()._asdict()
            except Exception as e:
                logger.debug(f"プロセスメモリ情報取得エラー: {e}")
            
            # CPU使用率を安全に取得
            cpu_percent = 0.0
            try:
                cpu_percent = process.cpu_percent()
            except Exception as e:
                logger.debug(f"プロセスCPU使用率取得エラー: {e}")
            
            # スレッド数を安全に取得
            num_threads = 0
            try:
                num_threads = process.num_threads()
            except Exception as e:
                logger.debug(f"プロセススレッド数取得エラー: {e}")
            
            return {
                'pid': pid,
                'memory_info': memory_info,
                'cpu_percent': cpu_percent,
                'num_threads': num_threads
            }
        except Exception as e:
            logger.debug(f"プロセスメトリクス取得エラー: {e}")
            return {
                'pid': pid,
                'memory_info': None,
                'cpu_percent': 0.0,
                'num_threads': 0
            }
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクス取得"""
        try:
            # ブート時間を安全に取得
            boot_time = None
            try:
                boot_time = psutil.boot_time()
            except Exception as e:
                logger.debug(f"ブート時間取得エラー: {e}")
            
            # ユーザー数を安全に取得
            users_count = 0
            try:
                users_count = len(psutil.users())
            except Exception as e:
                logger.debug(f"ユーザー数取得エラー: {e}")
            
            # 接続数を安全に取得
            connections_count = 0
            try:
                connections_count = len(psutil.net_connections())
            except Exception as e:
                logger.debug(f"接続数取得エラー: {e}")
            
            return {
                'boot_time': boot_time,
                'users': users_count,
                'connections': connections_count
            }
        except Exception as e:
            logger.debug(f"システムメトリクス取得エラー: {e}")
            return {
                'boot_time': None,
                'users': 0,
                'connections': 0
            }
    
    def get_metrics_history(self) -> List[Dict[str, Any]]:
        """メトリクス履歴取得"""
        try:
            return self.metrics_history
        except Exception as e:
            logger.error(f"メトリクス履歴取得エラー: {e}")
            return []
    
    def get_alert_history(self) -> List[Dict[str, Any]]:
        """アラート履歴取得"""
        try:
            return self.alert_history
        except Exception as e:
            logger.error(f"アラート履歴取得エラー: {e}")
            return []
    
    def get_prometheus_metrics(self) -> Response:
        """Prometheusメトリクス出力"""
        try:
            return Response(
                content=generate_latest(),
                media_type=CONTENT_TYPE_LATEST
            )
        except Exception as e:
            logger.error(f"Prometheusメトリクス取得エラー: {e}")
            return Response(
                content="",
                media_type=CONTENT_TYPE_LATEST
            )
    
    def get_health_summary(self) -> Dict[str, Any]:
        """健全性サマリー取得"""
        try:
            # CPU使用率を安全に取得
            cpu_percent = 0.0
            try:
                cpu_percent = psutil.cpu_percent()
            except Exception as e:
                logger.debug(f"CPU使用率取得エラー: {e}")
            
            # メモリ使用率を安全に取得
            memory_percent = 0.0
            memory_info = {}
            try:
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_info = {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'free': memory.free,
                    'percent': memory.percent
                }
            except Exception as e:
                logger.debug(f"メモリ使用率取得エラー: {e}")
            
            # ディスク使用率を安全に取得
            disk_percent = 0.0
            disk_info = {}
            try:
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                disk_info = {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk_percent
                }
            except Exception as e:
                logger.debug(f"ディスク使用率取得エラー: {e}")
            
            # ネットワーク接続を監視
            network_info = self._get_network_health()
            
            # プロセス監視
            process_info = self._get_process_health()
            
            # システムロード監視
            load_info = self._get_system_load()
            
            # セキュリティ監視
            security_info = self._get_security_health()
            
            # サービス監視
            service_info = self._get_service_health()
            
            # 健全性判定
            health_status = "healthy"
            warnings = []
            critical_alerts = []
            
            # CPU警告
            if cpu_percent > 90:
                health_status = "critical"
                critical_alerts.append(f"Critical CPU usage: {cpu_percent}%")
            elif cpu_percent > 80:
                health_status = "warning"
                warnings.append(f"High CPU usage: {cpu_percent}%")
            
            # メモリ警告
            if memory_percent > 95:
                health_status = "critical"
                critical_alerts.append(f"Critical memory usage: {memory_percent}%")
            elif memory_percent > 85:
                health_status = "warning"
                warnings.append(f"High memory usage: {memory_percent}%")
            
            # ディスク警告
            if disk_percent > 95:
                health_status = "critical"
                critical_alerts.append(f"Critical disk usage: {disk_percent:.1f}%")
            elif disk_percent > 90:
                health_status = "warning"
                warnings.append(f"High disk usage: {disk_percent:.1f}%")
            
            # ネットワーク警告
            if network_info.get('status') == 'error':
                health_status = "warning"
                warnings.append("Network connectivity issues detected")
            
            # プロセス警告
            if process_info.get('zombie_processes', 0) > 0:
                health_status = "warning"
                warnings.append(f"Zombie processes detected: {process_info['zombie_processes']}")
            
            # セキュリティ警告
            if security_info.get('status') == 'warning':
                health_status = "warning"
                warnings.extend(security_info.get('warnings', []))
            
            return {
                'status': health_status,
                'timestamp': datetime.now().isoformat(),
                'metrics': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'disk_percent': disk_percent,
                    'memory_info': memory_info,
                    'disk_info': disk_info
                },
                'network': network_info,
                'processes': process_info,
                'load': load_info,
                'security': security_info,
                'services': service_info,
                'warnings': warnings,
                'critical_alerts': critical_alerts,
                'overall_score': self._calculate_health_score(cpu_percent, memory_percent, disk_percent)
            }
            
        except Exception as e:
            logger.error(f"健全性サマリー取得エラー: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _get_network_health(self) -> Dict[str, Any]:
        """ネットワーク健全性を取得"""
        try:
            # ネットワーク接続を確認
            connections = psutil.net_connections()
            active_connections = len([conn for conn in connections if conn.status == 'ESTABLISHED'])
            
            # ネットワークインターフェース情報
            net_io = psutil.net_io_counters()
            
            return {
                'status': 'healthy',
                'active_connections': active_connections,
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        except Exception as e:
            logger.debug(f"ネットワーク健全性取得エラー: {e}")
            return {'status': 'error', 'error': str(e)}

    def _get_process_health(self) -> Dict[str, Any]:
        """プロセス健全性を取得"""
        try:
            processes = psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent'])
            
            total_processes = 0
            zombie_processes = 0
            high_cpu_processes = []
            high_memory_processes = []
            
            for proc in processes:
                try:
                    total_processes += 1
                    info = proc.info
                    
                    if info['status'] == 'zombie':
                        zombie_processes += 1
                    
                    if info['cpu_percent'] and info['cpu_percent'] > 50:
                        high_cpu_processes.append({
                            'pid': info['pid'],
                            'name': info['name'],
                            'cpu_percent': info['cpu_percent']
                        })
                    
                    if info['memory_percent'] and info['memory_percent'] > 10:
                        high_memory_processes.append({
                            'pid': info['pid'],
                            'name': info['name'],
                            'memory_percent': info['memory_percent']
                        })
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                'total_processes': total_processes,
                'zombie_processes': zombie_processes,
                'high_cpu_processes': high_cpu_processes[:5],  # 上位5件
                'high_memory_processes': high_memory_processes[:5]  # 上位5件
            }
        except Exception as e:
            logger.debug(f"プロセス健全性取得エラー: {e}")
            return {'error': str(e)}

    def _get_system_load(self) -> Dict[str, Any]:
        """システムロード情報を取得"""
        try:
            load_avg = os.getloadavg()
            return {
                'load_1min': load_avg[0],
                'load_5min': load_avg[1],
                'load_15min': load_avg[2]
            }
        except Exception as e:
            logger.debug(f"システムロード取得エラー: {e}")
            return {'error': str(e)}

    def _get_security_health(self) -> Dict[str, Any]:
        """セキュリティ健全性を取得"""
        try:
            warnings = []
            
            # 重要なファイルの権限チェック
            critical_files = ['/etc/passwd', '/etc/shadow', '/etc/sudoers']
            for file_path in critical_files:
                if os.path.exists(file_path):
                    try:
                        stat = os.stat(file_path)
                        if stat.st_mode & 0o777 != 0o644:  # 適切な権限でない場合
                            warnings.append(f"Unsafe permissions on {file_path}")
                    except Exception:
                        pass
            
            # 環境変数のセキュリティチェック
            sensitive_vars = ['API_KEY', 'SECRET', 'PASSWORD', 'TOKEN']
            for var in sensitive_vars:
                if os.environ.get(var):
                    warnings.append(f"Sensitive environment variable {var} is set")
            
            return {
                'status': 'healthy' if not warnings else 'warning',
                'warnings': warnings
            }
        except Exception as e:
            logger.debug(f"セキュリティ健全性取得エラー: {e}")
            return {'status': 'error', 'error': str(e)}

    def _get_service_health(self) -> Dict[str, Any]:
        """サービス健全性を取得"""
        try:
            # 現在のプロセスがPythonプロセスかチェック
            current_pid = os.getpid()
            current_process = psutil.Process(current_pid)
            
            services = {
                'main_process': {
                    'pid': current_pid,
                    'name': current_process.name(),
                    'status': 'running',
                    'cpu_percent': current_process.cpu_percent(),
                    'memory_percent': current_process.memory_percent()
                }
            }
            
            return services
        except Exception as e:
            logger.debug(f"サービス健全性取得エラー: {e}")
            return {'error': str(e)}

    def _calculate_health_score(self, cpu_percent: float, memory_percent: float, disk_percent: float) -> int:
        """健全性スコアを計算（0-100）"""
        try:
            score = 100
            
            # CPU使用率による減点
            if cpu_percent > 90:
                score -= 30
            elif cpu_percent > 80:
                score -= 20
            elif cpu_percent > 70:
                score -= 10
            
            # メモリ使用率による減点
            if memory_percent > 95:
                score -= 30
            elif memory_percent > 85:
                score -= 20
            elif memory_percent > 75:
                score -= 10
            
            # ディスク使用率による減点
            if disk_percent > 95:
                score -= 30
            elif disk_percent > 90:
                score -= 20
            elif disk_percent > 80:
                score -= 10
            
            return max(0, score)
        except Exception:
            return 50  # エラーの場合は中間値

    def _get_cpu_frequency(self) -> Dict[str, Any]:
        """CPU周波数情報を安全に取得"""
        try:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                return {
                    'current': cpu_freq.current,
                    'min': cpu_freq.min,
                    'max': cpu_freq.max
                }
            else:
                return None
        except Exception as e:
            logger.debug(f"CPU周波数情報取得エラー（無視）: {e}")
            return None

# グローバルインスタンス（遅延初期化）
_system_monitor = None

def get_system_monitor():
    """システムモニターインスタンスを取得（遅延初期化）"""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor()
    return _system_monitor

# エクスポートするクラスと関数
__all__ = ['SystemMonitor', 'get_system_monitor']