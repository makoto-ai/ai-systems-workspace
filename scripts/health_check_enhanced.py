#!/usr/bin/env python3
"""
AI Systems 強化ヘルスチェックスクリプト
包括的なシステム状態監視と自動復旧
"""

import os
import sys
import json
import logging
import asyncio
import httpx
import psutil
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ServiceHealth:
    name: str
    status: str  # healthy, unhealthy, unknown
    response_time: float
    last_check: datetime
    error_count: int = 0
    details: Dict[str, Any] = None

class EnhancedHealthChecker:
    def __init__(self):
        self.services = {
            "ai-systems-app": {"url": "http://localhost:8000/health", "port": 8000},
            "mcp-service": {"url": "http://localhost:8001/health", "port": 8001},
            "composer-service": {"url": "http://localhost:8002/health", "port": 8002},
            "vault": {"url": "http://localhost:8200/v1/sys/health", "port": 8200},
            "grafana": {"url": "http://localhost:3000/api/health", "port": 3000},
            "prometheus": {"url": "http://localhost:9090/-/healthy", "port": 9090},
            "postgres": {"url": "http://localhost:5432", "port": 5432},
            "redis": {"url": "http://localhost:6379", "port": 6379},
            "voicevox-engine": {"url": "http://localhost:50021/health", "port": 50021},
            "ollama": {"url": "http://localhost:11434/api/tags", "port": 11434}
        }
        self.health_history = {}
        self.alert_thresholds = {
            "response_time": 5.0,  # 5秒
            "error_rate": 0.1,     # 10%
            "memory_usage": 85.0,  # 85%
            "cpu_usage": 80.0,     # 80%
            "disk_usage": 90.0     # 90%
        }
    
    async def check_service_health(self, service_name: str, service_config: Dict[str, Any]) -> ServiceHealth:
        """個別サービスのヘルスチェック"""
        start_time = datetime.now()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(service_config["url"])
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                if response.status_code == 200:
                    status = "healthy"
                    error_count = 0
                else:
                    status = "unhealthy"
                    error_count = 1
                
                return ServiceHealth(
                    name=service_name,
                    status=status,
                    response_time=response_time,
                    last_check=end_time,
                    error_count=error_count,
                    details={
                        "status_code": response.status_code,
                        "response_size": len(response.text) if response.text else 0
                    }
                )
                
        except Exception as e:
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            return ServiceHealth(
                name=service_name,
                status="unhealthy",
                response_time=response_time,
                last_check=end_time,
                error_count=1,
                details={"error": str(e)}
            )
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクス取得"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # ネットワーク統計
            network_stats = psutil.net_io_counters()
            
            # プロセス統計
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 上位10プロセス
            top_processes = sorted(processes, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:10]
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
                "disk_percent": disk.percent,
                "disk_free": disk.free,
                "network_bytes_sent": network_stats.bytes_sent,
                "network_bytes_recv": network_stats.bytes_recv,
                "top_processes": top_processes,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"システムメトリクス取得エラー: {e}")
            return {}
    
    def check_docker_services(self) -> Dict[str, Any]:
        """Dockerサービス状態チェック"""
        try:
            result = subprocess.run([
                "docker", "ps", "--format", "json"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                containers = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            container_info = json.loads(line)
                            containers.append({
                                "name": container_info.get("Names", ""),
                                "status": container_info.get("Status", ""),
                                "ports": container_info.get("Ports", ""),
                                "image": container_info.get("Image", "")
                            })
                        except json.JSONDecodeError:
                            continue
                
                return {
                    "running_containers": len(containers),
                    "containers": containers
                }
            else:
                return {"error": "Dockerコマンド実行失敗"}
                
        except Exception as e:
            logger.error(f"Dockerサービスチェックエラー: {e}")
            return {"error": str(e)}
    
    def check_database_health(self) -> Dict[str, Any]:
        """データベースヘルスチェック"""
        try:
            # PostgreSQL接続テスト
            result = subprocess.run([
                "docker", "exec", "postgres", "pg_isready", "-U", "ai_user", "-d", "ai_systems"
            ], capture_output=True, text=True, timeout=10)
            
            postgres_healthy = result.returncode == 0
            
            # Redis接続テスト
            result = subprocess.run([
                "docker", "exec", "redis", "redis-cli", "ping"
            ], capture_output=True, text=True, timeout=10)
            
            redis_healthy = result.returncode == 0 and "PONG" in result.stdout
            
            return {
                "postgres": {
                    "healthy": postgres_healthy,
                    "details": result.stdout if postgres_healthy else result.stderr
                },
                "redis": {
                    "healthy": redis_healthy,
                    "details": result.stdout if redis_healthy else result.stderr
                }
            }
            
        except Exception as e:
            logger.error(f"データベースヘルスチェックエラー: {e}")
            return {"error": str(e)}
    
    def check_vault_health(self) -> Dict[str, Any]:
        """Vaultヘルスチェック"""
        try:
            result = subprocess.run([
                "curl", "-s", "http://localhost:8200/v1/sys/health"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                try:
                    vault_health = json.loads(result.stdout)
                    return {
                        "healthy": vault_health.get("initialized", False),
                        "sealed": vault_health.get("sealed", True),
                        "details": vault_health
                    }
                except json.JSONDecodeError:
                    return {"healthy": False, "error": "JSON解析失敗"}
            else:
                return {"healthy": False, "error": result.stderr}
                
        except Exception as e:
            logger.error(f"Vaultヘルスチェックエラー: {e}")
            return {"healthy": False, "error": str(e)}
    
    def check_log_files(self) -> Dict[str, Any]:
        """ログファイルチェック"""
        log_files = [
            "/app/logs/app.log",
            "/app/logs/error.log",
            "/app/logs/access.log",
            "/app/logs/metrics.log"
        ]
        
        log_status = {}
        
        for log_file in log_files:
            try:
                if os.path.exists(log_file):
                    stat = os.stat(log_file)
                    size_mb = stat.st_size / (1024 * 1024)
                    
                    log_status[log_file] = {
                        "exists": True,
                        "size_mb": size_mb,
                        "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "status": "normal" if size_mb < 100 else "large"
                    }
                else:
                    log_status[log_file] = {
                        "exists": False,
                        "status": "missing"
                    }
            except Exception as e:
                log_status[log_file] = {
                    "exists": False,
                    "error": str(e),
                    "status": "error"
                }
        
        return log_status
    
    def generate_alerts(self, health_results: Dict[str, ServiceHealth], system_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """アラート生成"""
        alerts = []
        
        # サービスアラート
        for service_name, health in health_results.items():
            if health.status == "unhealthy":
                alerts.append({
                    "type": "service_down",
                    "severity": "critical",
                    "service": service_name,
                    "message": f"{service_name} サービスがダウンしています",
                    "timestamp": datetime.now().isoformat()
                })
            
            if health.response_time > self.alert_thresholds["response_time"]:
                alerts.append({
                    "type": "high_response_time",
                    "severity": "warning",
                    "service": service_name,
                    "message": f"{service_name} の応答時間が長い: {health.response_time:.2f}s",
                    "timestamp": datetime.now().isoformat()
                })
        
        # システムアラート
        if system_metrics:
            if system_metrics.get("cpu_percent", 0) > self.alert_thresholds["cpu_usage"]:
                alerts.append({
                    "type": "high_cpu_usage",
                    "severity": "warning",
                    "message": f"CPU使用率が高い: {system_metrics['cpu_percent']:.1f}%",
                    "timestamp": datetime.now().isoformat()
                })
            
            if system_metrics.get("memory_percent", 0) > self.alert_thresholds["memory_usage"]:
                alerts.append({
                    "type": "high_memory_usage",
                    "severity": "warning",
                    "message": f"メモリ使用率が高い: {system_metrics['memory_percent']:.1f}%",
                    "timestamp": datetime.now().isoformat()
                })
            
            if system_metrics.get("disk_percent", 0) > self.alert_thresholds["disk_usage"]:
                alerts.append({
                    "type": "high_disk_usage",
                    "severity": "critical",
                    "message": f"ディスク使用率が高い: {system_metrics['disk_percent']:.1f}%",
                    "timestamp": datetime.now().isoformat()
                })
        
        return alerts
    
    async def perform_auto_recovery(self, health_results: Dict[str, ServiceHealth]) -> List[Dict[str, Any]]:
        """自動復旧実行"""
        recovery_actions = []
        
        for service_name, health in health_results.items():
            if health.status == "unhealthy" and health.error_count > 2:
                logger.info(f"{service_name} の自動復旧を試行中...")
                
                try:
                    # Dockerコンテナ再起動
                    result = subprocess.run([
                        "docker", "restart", service_name
                    ], capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        recovery_actions.append({
                            "service": service_name,
                            "action": "restart",
                            "success": True,
                            "timestamp": datetime.now().isoformat()
                        })
                        logger.info(f"{service_name} の再起動成功")
                    else:
                        recovery_actions.append({
                            "service": service_name,
                            "action": "restart",
                            "success": False,
                            "error": result.stderr,
                            "timestamp": datetime.now().isoformat()
                        })
                        logger.error(f"{service_name} の再起動失敗: {result.stderr}")
                        
                except Exception as e:
                    recovery_actions.append({
                        "service": service_name,
                        "action": "restart",
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.error(f"{service_name} の自動復旧エラー: {e}")
        
        return recovery_actions
    
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """包括的ヘルスチェック実行"""
        logger.info("包括的ヘルスチェック開始")
        
        # サービスヘルスチェック
        health_tasks = []
        for service_name, service_config in self.services.items():
            task = self.check_service_health(service_name, service_config)
            health_tasks.append(task)
        
        health_results = await asyncio.gather(*health_tasks, return_exceptions=True)
        
        # 結果を辞書に変換
        health_dict = {}
        for i, (service_name, _) in enumerate(self.services.items()):
            if isinstance(health_results[i], ServiceHealth):
                health_dict[service_name] = health_results[i]
            else:
                health_dict[service_name] = ServiceHealth(
                    name=service_name,
                    status="unknown",
                    response_time=0.0,
                    last_check=datetime.now(),
                    error_count=1,
                    details={"error": str(health_results[i])}
                )
        
        # システムメトリクス取得
        system_metrics = self.get_system_metrics()
        
        # Dockerサービス状態
        docker_status = self.check_docker_services()
        
        # データベースヘルスチェック
        database_health = self.check_database_health()
        
        # Vaultヘルスチェック
        vault_health = self.check_vault_health()
        
        # ログファイルチェック
        log_status = self.check_log_files()
        
        # アラート生成
        alerts = self.generate_alerts(health_dict, system_metrics)
        
        # 自動復旧実行（必要に応じて）
        recovery_actions = await self.perform_auto_recovery(health_dict)
        
        # 総合結果
        overall_health = {
            "timestamp": datetime.now().isoformat(),
            "services": health_dict,
            "system_metrics": system_metrics,
            "docker_status": docker_status,
            "database_health": database_health,
            "vault_health": vault_health,
            "log_status": log_status,
            "alerts": alerts,
            "recovery_actions": recovery_actions,
            "overall_status": "healthy" if not alerts else "degraded" if len([a for a in alerts if a["severity"] == "warning"]) > 0 else "critical"
        }
        
        # 結果をログに出力
        logger.info(f"ヘルスチェック完了 - 全体状態: {overall_health['overall_status']}")
        logger.info(f"アラート数: {len(alerts)}")
        logger.info(f"復旧アクション数: {len(recovery_actions)}")
        
        # 結果をファイルに保存
        health_file = f"/app/logs/health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(health_file, 'w', encoding='utf-8') as f:
            json.dump(overall_health, f, indent=2, default=str)
        
        return overall_health

async def main():
    """メイン関数"""
    checker = EnhancedHealthChecker()
    
    try:
        results = await checker.run_comprehensive_health_check()
        logger.info("ヘルスチェック完了")
        return results
    except Exception as e:
        logger.error(f"ヘルスチェックエラー: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(main()) 