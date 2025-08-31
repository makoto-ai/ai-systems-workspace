#!/usr/bin/env python3
"""
⚡ Phase 5: 動的リソース配分エンジン
===============================

品質処理ワークロードに対する計算リソースの動的最適配分システム
システム負荷・予測需要・コスト効率を考慮した自動リソース管理

主要機能:
- システムリソース監視
- ワークロード需要予測  
- 動的リソース配分
- 負荷分散・スケジューリング
- コスト効率最適化
"""

import os
import sys
import json
import psutil
import threading
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
import math


class ResourceType(Enum):
    """リソースタイプ"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    PROCESS_SLOTS = "process_slots"


class WorkloadPriority(Enum):
    """ワークロード優先度"""
    CRITICAL = 1    # SLA違反対応
    HIGH = 2       # Phase 4 AI分析
    MEDIUM = 3     # Phase 3 リアルタイム
    LOW = 4       # Phase 1-2 バッチ処理


@dataclass
class SystemResources:
    """システムリソース情報"""
    timestamp: datetime
    cpu_percent: float
    cpu_cores: int
    memory_percent: float
    memory_total_gb: float
    memory_available_gb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_sent_mb: float
    network_io_recv_mb: float
    active_processes: int
    load_average: Tuple[float, float, float]  # 1, 5, 15 min


@dataclass
class QualityWorkload:
    """品質処理ワークロード"""
    workload_id: str
    workload_type: str  # "sla_monitoring", "autonomous_fix", "ai_analysis", etc.
    priority: WorkloadPriority
    estimated_cpu_usage: float
    estimated_memory_mb: float
    estimated_duration_seconds: int
    required_resources: Dict[ResourceType, float]
    dependencies: List[str]
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    resource_allocation: Dict[str, Any]


@dataclass
class ResourceAllocation:
    """リソース配分結果"""
    allocation_id: str
    workload_id: str
    allocated_resources: Dict[ResourceType, float]
    allocation_efficiency: float
    estimated_completion_time: datetime
    cost_estimate: float
    allocation_strategy: str
    constraints: List[str]


class SystemMonitor:
    """システムリソース監視"""
    
    def __init__(self, monitoring_interval: int = 30):
        self.monitoring_interval = monitoring_interval
        self.monitoring_active = False
        self.resource_history = []
        self.max_history_size = 100
        
    def start_monitoring(self):
        """監視開始"""
        self.monitoring_active = True
        monitoring_thread = threading.Thread(target=self._monitoring_loop)
        monitoring_thread.daemon = True
        monitoring_thread.start()
        print("📊 システムリソース監視開始")
    
    def stop_monitoring(self):
        """監視停止"""
        self.monitoring_active = False
        print("📊 システムリソース監視停止")
    
    def _monitoring_loop(self):
        """監視ループ"""
        while self.monitoring_active:
            try:
                resources = self.collect_system_resources()
                self.resource_history.append(resources)
                
                # 履歴サイズ制限
                if len(self.resource_history) > self.max_history_size:
                    self.resource_history = self.resource_history[-self.max_history_size:]
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"監視エラー: {e}")
                time.sleep(self.monitoring_interval)
    
    def collect_system_resources(self) -> SystemResources:
        """現在のシステムリソース収集"""
        try:
            # CPU情報
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_cores = psutil.cpu_count()
            
            # メモリ情報
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_total_gb = memory.total / (1024**3)
            memory_available_gb = memory.available / (1024**3)
            
            # ディスクI/O
            disk_io = psutil.disk_io_counters()
            disk_read_mb = disk_io.read_bytes / (1024**2) if disk_io else 0
            disk_write_mb = disk_io.write_bytes / (1024**2) if disk_io else 0
            
            # ネットワークI/O
            net_io = psutil.net_io_counters()
            net_sent_mb = net_io.bytes_sent / (1024**2) if net_io else 0
            net_recv_mb = net_io.bytes_recv / (1024**2) if net_io else 0
            
            # プロセス情報
            active_processes = len(psutil.pids())
            
            # ロードアベレージ（Unix系のみ）
            try:
                load_avg = os.getloadavg()
            except AttributeError:
                load_avg = (cpu_percent/100 * cpu_cores, 0.0, 0.0)  # Fallback for Windows
            
            return SystemResources(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                cpu_cores=cpu_cores,
                memory_percent=memory_percent,
                memory_total_gb=memory_total_gb,
                memory_available_gb=memory_available_gb,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_io_sent_mb=net_sent_mb,
                network_io_recv_mb=net_recv_mb,
                active_processes=active_processes,
                load_average=load_avg
            )
            
        except Exception as e:
            print(f"リソース収集エラー: {e}")
            return SystemResources(
                timestamp=datetime.now(),
                cpu_percent=50.0,
                cpu_cores=4,
                memory_percent=60.0,
                memory_total_gb=8.0,
                memory_available_gb=3.2,
                disk_io_read_mb=100.0,
                disk_io_write_mb=50.0,
                network_io_sent_mb=10.0,
                network_io_recv_mb=15.0,
                active_processes=100,
                load_average=(1.5, 1.2, 1.0)
            )
    
    def get_resource_trend(self, resource_type: str, window_minutes: int = 30) -> Dict[str, float]:
        """リソース使用傾向分析"""
        if len(self.resource_history) < 2:
            return {"trend": 0.0, "volatility": 0.0, "current": 0.0}
        
        # 指定時間窓内のデータ抽出
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_data = [r for r in self.resource_history if r.timestamp > cutoff_time]
        
        if not recent_data:
            recent_data = self.resource_history[-10:]  # 最低限のデータ
        
        # リソース値抽出
        if resource_type == "cpu":
            values = [r.cpu_percent for r in recent_data]
        elif resource_type == "memory":
            values = [r.memory_percent for r in recent_data]
        elif resource_type == "disk_io":
            values = [r.disk_io_read_mb + r.disk_io_write_mb for r in recent_data]
        elif resource_type == "network_io":
            values = [r.network_io_sent_mb + r.network_io_recv_mb for r in recent_data]
        else:
            values = [0.0] * len(recent_data)
        
        if len(values) < 2:
            return {"trend": 0.0, "volatility": 0.0, "current": values[0] if values else 0.0}
        
        # トレンド計算（線形回帰の傾き）
        n = len(values)
        x_vals = list(range(n))
        x_mean = statistics.mean(x_vals)
        y_mean = statistics.mean(values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, values))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)
        
        trend = numerator / denominator if denominator != 0 else 0.0
        volatility = statistics.stdev(values) if len(values) > 1 else 0.0
        
        return {
            "trend": trend,
            "volatility": volatility,
            "current": values[-1],
            "avg": statistics.mean(values),
            "min": min(values),
            "max": max(values)
        }


class WorkloadPredictor:
    """ワークロード予測エンジン"""
    
    def __init__(self):
        self.workload_patterns = self._load_workload_patterns()
        self.prediction_horizon_hours = 2
    
    def _load_workload_patterns(self) -> Dict[str, Any]:
        """ワークロードパターン読み込み"""
        return {
            "sla_monitoring": {
                "frequency_minutes": 15,
                "cpu_usage": 5.0,
                "memory_mb": 50,
                "duration_seconds": 30,
                "peak_hours": [9, 10, 11, 14, 15, 16]
            },
            "autonomous_fix": {
                "frequency_minutes": 60,
                "cpu_usage": 25.0,
                "memory_mb": 200,
                "duration_seconds": 300,
                "peak_hours": [10, 11, 15, 16]
            },
            "ai_analysis": {
                "frequency_minutes": 120,
                "cpu_usage": 60.0,
                "memory_mb": 800,
                "duration_seconds": 600,
                "peak_hours": [9, 13, 17]
            },
            "realtime_monitoring": {
                "frequency_minutes": 5,
                "cpu_usage": 10.0,
                "memory_mb": 100,
                "duration_seconds": 60,
                "peak_hours": [8, 9, 10, 11, 13, 14, 15, 16, 17]
            }
        }
    
    def predict_workload_demand(self, hours_ahead: int = 2) -> List[QualityWorkload]:
        """ワークロード需要予測"""
        predicted_workloads = []
        current_time = datetime.now()
        
        for workload_type, pattern in self.workload_patterns.items():
            frequency_minutes = pattern["frequency_minutes"]
            
            # 予測期間内のワークロード生成
            time_cursor = current_time
            end_time = current_time + timedelta(hours=hours_ahead)
            
            workload_counter = 0
            while time_cursor <= end_time:
                # ピーク時間での頻度調整
                hour = time_cursor.hour
                frequency_multiplier = 1.5 if hour in pattern["peak_hours"] else 1.0
                
                adjusted_frequency = frequency_minutes / frequency_multiplier
                
                workload = QualityWorkload(
                    workload_id=f"{workload_type}_{int(time_cursor.timestamp())}_{workload_counter}",
                    workload_type=workload_type,
                    priority=self._determine_workload_priority(workload_type),
                    estimated_cpu_usage=pattern["cpu_usage"] * frequency_multiplier,
                    estimated_memory_mb=pattern["memory_mb"],
                    estimated_duration_seconds=pattern["duration_seconds"],
                    required_resources=self._calculate_required_resources(pattern, frequency_multiplier),
                    dependencies=[],
                    scheduled_at=time_cursor,
                    started_at=None,
                    completed_at=None,
                    resource_allocation={}
                )
                predicted_workloads.append(workload)
                
                time_cursor += timedelta(minutes=adjusted_frequency)
                workload_counter += 1
        
        return sorted(predicted_workloads, key=lambda w: w.scheduled_at)
    
    def _determine_workload_priority(self, workload_type: str) -> WorkloadPriority:
        """ワークロード優先度決定"""
        priority_map = {
            "sla_monitoring": WorkloadPriority.CRITICAL,
            "autonomous_fix": WorkloadPriority.HIGH,
            "ai_analysis": WorkloadPriority.HIGH,
            "realtime_monitoring": WorkloadPriority.MEDIUM,
            "batch_analysis": WorkloadPriority.LOW
        }
        return priority_map.get(workload_type, WorkloadPriority.MEDIUM)
    
    def _calculate_required_resources(self, pattern: Dict, multiplier: float) -> Dict[ResourceType, float]:
        """必要リソース計算"""
        return {
            ResourceType.CPU: pattern["cpu_usage"] * multiplier / 100.0,  # CPU使用率を0-1に正規化
            ResourceType.MEMORY: pattern["memory_mb"],
            ResourceType.PROCESS_SLOTS: 1,
            ResourceType.DISK_IO: 10.0 * multiplier,  # MB/s
            ResourceType.NETWORK_IO: 5.0 * multiplier  # MB/s
        }


class ResourceOptimizer:
    """リソース最適化エンジン"""
    
    def __init__(self, monitor: SystemMonitor):
        self.monitor = monitor
        self.optimization_strategies = ["greedy", "load_balanced", "cost_optimized"]
    
    def optimize_allocation(self, workloads: List[QualityWorkload], current_resources: SystemResources) -> List[ResourceAllocation]:
        """リソース配分最適化"""
        allocations = []
        
        # ワークロードを優先度でソート
        sorted_workloads = sorted(workloads, key=lambda w: (w.priority.value, w.scheduled_at))
        
        # 利用可能リソース計算
        available_resources = self._calculate_available_resources(current_resources)
        
        for workload in sorted_workloads:
            allocation = self._allocate_resources(workload, available_resources, current_resources)
            
            if allocation:
                allocations.append(allocation)
                # 配分後のリソース更新
                self._update_available_resources(available_resources, allocation)
        
        return allocations
    
    def _calculate_available_resources(self, current_resources: SystemResources) -> Dict[ResourceType, float]:
        """利用可能リソース計算"""
        # 安全マージン考慮
        cpu_margin = 0.8  # 80%まで使用可
        memory_margin = 0.85  # 85%まで使用可
        
        return {
            ResourceType.CPU: max(0, (100 - current_resources.cpu_percent) * cpu_margin / 100),
            ResourceType.MEMORY: current_resources.memory_available_gb * 1024 * memory_margin,  # MB
            ResourceType.PROCESS_SLOTS: max(0, 50 - current_resources.active_processes // 10),  # 簡易計算
            ResourceType.DISK_IO: 100.0,  # MB/s の仮定値
            ResourceType.NETWORK_IO: 50.0  # MB/s の仮定値
        }
    
    def _allocate_resources(self, workload: QualityWorkload, available_resources: Dict[ResourceType, float], 
                           current_resources: SystemResources) -> Optional[ResourceAllocation]:
        """個別ワークロードリソース配分"""
        allocated = {}
        allocation_efficiency = 1.0
        
        # 各リソースタイプの配分チェック
        for resource_type, required in workload.required_resources.items():
            available = available_resources.get(resource_type, 0)
            
            if available >= required:
                allocated[resource_type] = required
            else:
                # リソース不足の場合の対応戦略
                if workload.priority in [WorkloadPriority.CRITICAL, WorkloadPriority.HIGH]:
                    # 高優先度は利用可能なリソースを最大限使用
                    allocated[resource_type] = available
                    allocation_efficiency *= (available / required) if required > 0 else 1.0
                else:
                    # 低優先度はリソース不足時にスキップ
                    return None
        
        # 効率性の最小値保証
        allocation_efficiency = max(0.1, allocation_efficiency)  # 最低10%の効率は保証
        
        if allocation_efficiency < 0.5 and workload.priority not in [WorkloadPriority.CRITICAL]:
            # 効率性が低すぎる場合はスキップ（Critical以外）
            return None
        
        # コスト推定
        cost_estimate = self._estimate_cost(allocated, workload.estimated_duration_seconds)
        
        # 完了予定時刻計算（ゼロ除算防止）
        duration_factor = max(1.0, 1.0 / allocation_efficiency)
        estimated_completion = datetime.now() + timedelta(seconds=workload.estimated_duration_seconds * duration_factor)
        
        return ResourceAllocation(
            allocation_id=f"alloc_{workload.workload_id}",
            workload_id=workload.workload_id,
            allocated_resources=allocated,
            allocation_efficiency=allocation_efficiency,
            estimated_completion_time=estimated_completion,
            cost_estimate=cost_estimate,
            allocation_strategy="priority_based",
            constraints=self._identify_constraints(allocated, available_resources)
        )
    
    def _update_available_resources(self, available_resources: Dict[ResourceType, float], allocation: ResourceAllocation):
        """配分後の利用可能リソース更新"""
        for resource_type, allocated_amount in allocation.allocated_resources.items():
            current = available_resources.get(resource_type, 0)
            available_resources[resource_type] = max(0, current - allocated_amount)
    
    def _estimate_cost(self, allocated_resources: Dict[ResourceType, float], duration_seconds: int) -> float:
        """コスト推定"""
        # 簡易的なコストモデル
        cost_per_cpu_hour = 0.05  # $0.05 per CPU% hour
        cost_per_gb_hour = 0.01   # $0.01 per GB hour
        
        cpu_cost = allocated_resources.get(ResourceType.CPU, 0) * cost_per_cpu_hour * (duration_seconds / 3600)
        memory_cost = allocated_resources.get(ResourceType.MEMORY, 0) / 1024 * cost_per_gb_hour * (duration_seconds / 3600)
        
        return cpu_cost + memory_cost
    
    def _identify_constraints(self, allocated: Dict[ResourceType, float], available: Dict[ResourceType, float]) -> List[str]:
        """制約識別"""
        constraints = []
        
        for resource_type in ResourceType:
            allocated_amount = allocated.get(resource_type, 0)
            available_amount = available.get(resource_type, 0)
            
            if allocated_amount > available_amount * 0.8:
                constraints.append(f"{resource_type.value}_limited")
        
        return constraints


class WorkloadScheduler:
    """ワークロードスケジューラー"""
    
    def __init__(self, max_concurrent_workloads: int = 5):
        self.max_concurrent_workloads = max_concurrent_workloads
        self.active_workloads = {}
        self.workload_queue = queue.PriorityQueue()
        self.scheduler_active = False
        
    def start_scheduler(self):
        """スケジューラー開始"""
        self.scheduler_active = True
        scheduler_thread = threading.Thread(target=self._scheduler_loop)
        scheduler_thread.daemon = True
        scheduler_thread.start()
        print("📅 ワークロードスケジューラー開始")
    
    def stop_scheduler(self):
        """スケジューラー停止"""
        self.scheduler_active = False
        print("📅 ワークロードスケジューラー停止")
    
    def schedule_workload(self, workload: QualityWorkload, allocation: ResourceAllocation):
        """ワークロードスケジュール登録"""
        priority_value = workload.priority.value
        scheduled_time = workload.scheduled_at or datetime.now()
        
        # 優先度キュー項目作成 (priority, scheduled_time, workload, allocation)
        self.workload_queue.put((priority_value, scheduled_time, workload, allocation))
    
    def _scheduler_loop(self):
        """スケジューラーループ"""
        while self.scheduler_active:
            try:
                current_time = datetime.now()
                
                # 完了したワークロードのクリーンアップ
                self._cleanup_completed_workloads()
                
                # 新しいワークロードの実行チェック
                if len(self.active_workloads) < self.max_concurrent_workloads:
                    if not self.workload_queue.empty():
                        priority, scheduled_time, workload, allocation = self.workload_queue.get()
                        
                        if scheduled_time <= current_time:
                            self._execute_workload(workload, allocation)
                        else:
                            # まだ実行時刻ではないので戻す
                            self.workload_queue.put((priority, scheduled_time, workload, allocation))
                
                time.sleep(10)  # 10秒間隔でチェック
                
            except Exception as e:
                print(f"スケジューラーエラー: {e}")
                time.sleep(10)
    
    def _execute_workload(self, workload: QualityWorkload, allocation: ResourceAllocation):
        """ワークロード実行"""
        print(f"🚀 ワークロード実行開始: {workload.workload_type}")
        
        workload.started_at = datetime.now()
        
        # ワークロードタイプに応じた実行
        execution_result = self._run_workload_by_type(workload.workload_type)
        
        # 実行結果記録
        self.active_workloads[workload.workload_id] = {
            "workload": workload,
            "allocation": allocation,
            "started_at": workload.started_at,
            "execution_result": execution_result
        }
    
    def _run_workload_by_type(self, workload_type: str) -> Dict[str, Any]:
        """ワークロードタイプ別実行"""
        try:
            if workload_type == "sla_monitoring":
                result = subprocess.run(
                    ["python", "scripts/quality/sla_management_system.py", "--monitor"],
                    capture_output=True, text=True, timeout=60
                )
                return {"status": "success" if result.returncode == 0 else "failed", "output": result.stdout}
                
            elif workload_type == "autonomous_fix":
                result = subprocess.run(
                    ["python", "scripts/quality/autonomous_fix_engine.py", "--run"],
                    capture_output=True, text=True, timeout=300
                )
                return {"status": "success" if result.returncode == 0 else "failed", "output": result.stdout}
                
            elif workload_type == "ai_analysis":
                result = subprocess.run(
                    ["python", "scripts/quality/intelligent_optimizer.py", "--analyze"],
                    capture_output=True, text=True, timeout=600
                )
                return {"status": "success" if result.returncode == 0 else "failed", "output": result.stdout}
                
            elif workload_type == "realtime_monitoring":
                result = subprocess.run(
                    ["python", "scripts/quality/realtime_monitor.py", "--test"],
                    capture_output=True, text=True, timeout=120
                )
                return {"status": "success" if result.returncode == 0 else "failed", "output": result.stdout}
                
            else:
                # シミュレート実行
                time.sleep(2)  # 実行をシミュレート
                return {"status": "simulated", "output": f"Simulated execution of {workload_type}"}
                
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "output": f"Workload {workload_type} timed out"}
        except Exception as e:
            return {"status": "error", "output": str(e)}
    
    def _cleanup_completed_workloads(self):
        """完了ワークロードのクリーンアップ"""
        completed_ids = []
        current_time = datetime.now()
        
        for workload_id, workload_info in self.active_workloads.items():
            workload = workload_info["workload"]
            started_at = workload_info["started_at"]
            
            # 推定完了時間を過ぎていれば完了とみなす
            if started_at and (current_time - started_at).total_seconds() > workload.estimated_duration_seconds:
                workload.completed_at = current_time
                completed_ids.append(workload_id)
                print(f"✅ ワークロード完了: {workload.workload_type}")
        
        # 完了ワークロードを削除
        for workload_id in completed_ids:
            del self.active_workloads[workload_id]


class DynamicResourceAllocator:
    """動的リソース配分エンジン メインクラス"""
    
    def __init__(self):
        self.monitor = SystemMonitor(monitoring_interval=30)
        self.predictor = WorkloadPredictor()
        self.optimizer = ResourceOptimizer(self.monitor)
        self.scheduler = WorkloadScheduler(max_concurrent_workloads=3)
        self.allocation_history = []
        
    def start_dynamic_allocation(self) -> Dict[str, Any]:
        """動的リソース配分開始"""
        print("⚡ 動的リソース配分エンジン開始...")
        
        # 監視・スケジューリング開始
        self.monitor.start_monitoring()
        self.scheduler.start_scheduler()
        
        # 現在のシステム状態取得
        current_resources = self.monitor.collect_system_resources()
        
        # ワークロード需要予測
        predicted_workloads = self.predictor.predict_workload_demand(hours_ahead=2)
        print(f"📈 予測ワークロード数: {len(predicted_workloads)}")
        
        # リソース配分最適化
        allocations = self.optimizer.optimize_allocation(predicted_workloads, current_resources)
        print(f"⚡ 最適化配分数: {len(allocations)}")
        
        # ワークロードスケジューリング
        scheduled_count = 0
        for allocation in allocations:
            # 対応するワークロードを検索
            workload = next((w for w in predicted_workloads if w.workload_id == allocation.workload_id), None)
            if workload:
                self.scheduler.schedule_workload(workload, allocation)
                scheduled_count += 1
        
        print(f"📅 スケジュール登録数: {scheduled_count}")
        
        # 実行結果サマリー作成
        summary = {
            "execution_timestamp": datetime.now().isoformat(),
            "system_resources": {
                "cpu_percent": current_resources.cpu_percent,
                "memory_percent": current_resources.memory_percent,
                "memory_available_gb": current_resources.memory_available_gb,
                "active_processes": current_resources.active_processes
            },
            "workload_prediction": {
                "total_workloads": len(predicted_workloads),
                "workload_types": list(set(w.workload_type for w in predicted_workloads)),
                "priority_distribution": self._analyze_priority_distribution(predicted_workloads)
            },
            "resource_allocation": {
                "total_allocations": len(allocations),
                "scheduled_workloads": scheduled_count,
                "avg_allocation_efficiency": statistics.mean([a.allocation_efficiency for a in allocations]) if allocations else 0,
                "total_estimated_cost": sum(a.cost_estimate for a in allocations)
            },
            "optimization_metrics": self._calculate_optimization_metrics(allocations, current_resources)
        }
        
        # 結果保存
        self._save_allocation_results(summary, allocations)
        
        print("✅ 動的リソース配分セットアップ完了")
        return summary
    
    def stop_dynamic_allocation(self):
        """動的リソース配分停止"""
        print("⚡ 動的リソース配分エンジン停止...")
        self.monitor.stop_monitoring()
        self.scheduler.stop_scheduler()
        print("✅ 動的リソース配分停止完了")
    
    def get_allocation_status(self) -> Dict[str, Any]:
        """配分状態取得"""
        current_resources = self.monitor.collect_system_resources()
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "system_status": {
                "cpu_percent": current_resources.cpu_percent,
                "memory_percent": current_resources.memory_percent,
                "load_average": current_resources.load_average,
                "active_processes": current_resources.active_processes
            },
            "active_workloads": len(self.scheduler.active_workloads),
            "queue_size": self.scheduler.workload_queue.qsize(),
            "resource_trends": {
                "cpu": self.monitor.get_resource_trend("cpu"),
                "memory": self.monitor.get_resource_trend("memory")
            },
            "allocation_efficiency": self._calculate_current_efficiency()
        }
        
        return status
    
    def _analyze_priority_distribution(self, workloads: List[QualityWorkload]) -> Dict[str, int]:
        """優先度分布分析"""
        distribution = {}
        for workload in workloads:
            priority = workload.priority.name
            distribution[priority] = distribution.get(priority, 0) + 1
        return distribution
    
    def _calculate_optimization_metrics(self, allocations: List[ResourceAllocation], resources: SystemResources) -> Dict[str, float]:
        """最適化メトリクス計算"""
        if not allocations:
            return {}
        
        return {
            "resource_utilization_score": self._calculate_utilization_score(allocations, resources),
            "cost_efficiency_score": self._calculate_cost_efficiency(allocations),
            "priority_satisfaction_score": self._calculate_priority_satisfaction(allocations)
        }
    
    def _calculate_utilization_score(self, allocations: List[ResourceAllocation], resources: SystemResources) -> float:
        """リソース利用効率スコア"""
        total_cpu_allocated = sum(a.allocated_resources.get(ResourceType.CPU, 0) for a in allocations)
        total_memory_allocated = sum(a.allocated_resources.get(ResourceType.MEMORY, 0) for a in allocations)
        
        cpu_efficiency = min(1.0, total_cpu_allocated / (resources.cpu_cores * 0.8))  # 80%を最大とする
        memory_efficiency = min(1.0, total_memory_allocated / (resources.memory_total_gb * 1024 * 0.8))
        
        return (cpu_efficiency + memory_efficiency) / 2
    
    def _calculate_cost_efficiency(self, allocations: List[ResourceAllocation]) -> float:
        """コスト効率スコア"""
        if not allocations:
            return 0.0
        
        avg_efficiency = statistics.mean([a.allocation_efficiency for a in allocations])
        avg_cost = statistics.mean([a.cost_estimate for a in allocations])
        
        # 効率が高く、コストが低いほど良いスコア
        return avg_efficiency / max(0.01, avg_cost)
    
    def _calculate_priority_satisfaction(self, allocations: List[ResourceAllocation]) -> float:
        """優先度満足度スコア"""
        if not allocations:
            return 0.0
        
        # 高優先度のワークロードが十分なリソースを得ているかを評価
        high_priority_efficiency = []
        for allocation in allocations:
            if allocation.allocation_efficiency >= 0.8:  # 80%以上の効率
                high_priority_efficiency.append(allocation.allocation_efficiency)
        
        return statistics.mean(high_priority_efficiency) if high_priority_efficiency else 0.5
    
    def _calculate_current_efficiency(self) -> float:
        """現在の配分効率計算"""
        if not self.scheduler.active_workloads:
            return 0.0
        
        efficiencies = []
        for workload_info in self.scheduler.active_workloads.values():
            allocation = workload_info.get("allocation")
            if allocation:
                efficiencies.append(allocation.allocation_efficiency)
        
        return statistics.mean(efficiencies) if efficiencies else 0.0
    
    def _save_allocation_results(self, summary: Dict[str, Any], allocations: List[ResourceAllocation]):
        """配分結果保存"""
        try:
            os.makedirs("out", exist_ok=True)
            
            # サマリー保存
            with open("out/dynamic_allocation_summary.json", "w") as f:
                json.dump(summary, f, indent=2)
            
            # 詳細配分結果保存
            allocation_details = []
            for allocation in allocations:
                detail = asdict(allocation)
                detail["estimated_completion_time"] = allocation.estimated_completion_time.isoformat()
                # ResourceType enum を文字列に変換
                detail["allocated_resources"] = {k.value if hasattr(k, 'value') else str(k): v 
                                                for k, v in allocation.allocated_resources.items()}
                allocation_details.append(detail)
            
            with open("out/resource_allocations.json", "w") as f:
                json.dump(allocation_details, f, indent=2)
                
        except Exception as e:
            print(f"結果保存エラー: {e}")
    
    def display_allocation_status(self, summary: Dict[str, Any]):
        """配分状態表示"""
        print("\n⚡ 動的リソース配分エンジン実行結果")
        print("=" * 50)
        
        resources = summary["system_resources"]
        print(f"📊 システムリソース:")
        print(f"   CPU使用率: {resources['cpu_percent']:.1f}%")
        print(f"   メモリ使用率: {resources['memory_percent']:.1f}%")
        print(f"   利用可能メモリ: {resources['memory_available_gb']:.1f}GB")
        print(f"   アクティブプロセス: {resources['active_processes']}")
        
        prediction = summary["workload_prediction"]
        print(f"\n📈 ワークロード予測:")
        print(f"   予測ワークロード数: {prediction['total_workloads']}")
        print(f"   ワークロードタイプ: {len(prediction['workload_types'])}")
        
        allocation = summary["resource_allocation"]
        print(f"\n⚡ リソース配分:")
        print(f"   配分成功数: {allocation['total_allocations']}")
        print(f"   スケジュール登録数: {allocation['scheduled_workloads']}")
        print(f"   平均配分効率: {allocation['avg_allocation_efficiency']:.3f}")
        print(f"   推定総コスト: ${allocation['total_estimated_cost']:.4f}")
        
        if summary.get("optimization_metrics"):
            metrics = summary["optimization_metrics"]
            print(f"\n📊 最適化メトリクス:")
            print(f"   リソース利用効率: {metrics.get('resource_utilization_score', 0):.3f}")
            print(f"   コスト効率: {metrics.get('cost_efficiency_score', 0):.3f}")
            print(f"   優先度満足度: {metrics.get('priority_satisfaction_score', 0):.3f}")


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="⚡ Dynamic Resource Allocator")
    parser.add_argument("--start", action="store_true", help="Start dynamic allocation")
    parser.add_argument("--status", action="store_true", help="Show allocation status")
    parser.add_argument("--stop", action="store_true", help="Stop dynamic allocation")
    
    args = parser.parse_args()
    
    allocator = DynamicResourceAllocator()
    
    if args.stop:
        allocator.stop_dynamic_allocation()
    elif args.status:
        status = allocator.get_allocation_status()
        print("\n⚡ 動的リソース配分状態")
        print("=" * 30)
        print(f"CPU使用率: {status['system_status']['cpu_percent']:.1f}%")
        print(f"メモリ使用率: {status['system_status']['memory_percent']:.1f}%")
        print(f"アクティブワークロード: {status['active_workloads']}")
        print(f"キュー待機数: {status['queue_size']}")
        print(f"現在の配分効率: {status['allocation_efficiency']:.3f}")
    elif args.start:
        summary = allocator.start_dynamic_allocation()
        allocator.display_allocation_status(summary)
        
        print("\n🔄 動的配分が開始されました。停止するには --stop を実行してください。")
    else:
        # デフォルト: 短期実行
        summary = allocator.start_dynamic_allocation()
        allocator.display_allocation_status(summary)
        
        # 短時間実行後停止
        print("\n⏱️ 30秒間の動的配分実行...")
        time.sleep(30)
        allocator.stop_dynamic_allocation()


if __name__ == "__main__":
    main()
