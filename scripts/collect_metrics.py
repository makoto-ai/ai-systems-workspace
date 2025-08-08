#!/usr/bin/env python3
"""
メトリクス収集スクリプト
OpenTelemetryとPrometheusの統合メトリクス収集
"""

import os
import time
import logging
import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any, List

# OpenTelemetry設定
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self):
        self.meter = metrics.get_meter(__name__)
        self.setup_metrics()
        self.client = httpx.AsyncClient(timeout=10.0)
        
    def setup_metrics(self):
        """メトリクスの設定"""
        # カウンター
        self.request_counter = self.meter.create_counter(
            name="ai_systems_requests_total",
            description="Total number of requests",
            unit="1"
        )
        
        self.error_counter = self.meter.create_counter(
            name="ai_systems_errors_total",
            description="Total number of errors",
            unit="1"
        )
        
        # ヒストグラム
        self.response_time_histogram = self.meter.create_histogram(
            name="ai_systems_response_time_seconds",
            description="Response time in seconds",
            unit="s"
        )
        
        # ゲージ
        self.active_connections_gauge = self.meter.create_up_down_counter(
            name="ai_systems_active_connections",
            description="Number of active connections",
            unit="1"
        )
        
        # システムメトリクス
        self.cpu_usage_gauge = self.meter.create_up_down_counter(
            name="ai_systems_cpu_usage_percent",
            description="CPU usage percentage",
            unit="1"
        )
        
        self.memory_usage_gauge = self.meter.create_up_down_counter(
            name="ai_systems_memory_usage_percent",
            description="Memory usage percentage",
            unit="1"
        )
        
        logger.info("メトリクス設定完了")
    
    async def collect_system_metrics(self):
        """システムメトリクスの収集"""
        try:
            import psutil
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage_gauge.add(cpu_percent)
            
            # メモリ使用率
            memory = psutil.virtual_memory()
            self.memory_usage_gauge.add(memory.percent)
            
            logger.debug(f"システムメトリクス: CPU={cpu_percent}%, Memory={memory.percent}%")
            
        except Exception as e:
            logger.error(f"システムメトリクス収集エラー: {e}")
    
    async def collect_service_metrics(self):
        """サービスメトリクスの収集"""
        services = [
            {"name": "main-app", "url": "http://localhost:8000/health"},
            {"name": "mcp-service", "url": "http://localhost:8001/health"},
            {"name": "composer-service", "url": "http://localhost:8002/health"},
            {"name": "grafana", "url": "http://localhost:3000/api/health"},
            {"name": "prometheus", "url": "http://localhost:9090/-/healthy"},
            {"name": "vault", "url": "http://localhost:8200/v1/sys/health"}
        ]
        
        for service in services:
            try:
                start_time = time.time()
                response = await self.client.get(service["url"])
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.request_counter.add(1, {"service": service["name"], "status": "success"})
                    self.response_time_histogram.record(response_time, {"service": service["name"]})
                    logger.debug(f"{service['name']}: 正常 (応答時間: {response_time:.3f}s)")
                else:
                    self.error_counter.add(1, {"service": service["name"], "status": "error"})
                    logger.warning(f"{service['name']}: 異常 (ステータス: {response.status_code})")
                    
            except Exception as e:
                self.error_counter.add(1, {"service": service["name"], "status": "error"})
                logger.error(f"{service['name']} メトリクス収集エラー: {e}")
    
    async def collect_ai_metrics(self):
        """AI関連メトリクスの収集"""
        try:
            # Composer API テスト
            start_time = time.time()
            response = await self.client.post(
                "http://localhost:8000/composer/generate",
                json={
                    "metadata": {
                        "title": "テスト",
                        "authors": ["テスト"],
                        "abstract": "テスト"
                    },
                    "abstract": "テスト要約",
                    "style": "popular"
                }
            )
            composer_time = time.time() - start_time
            
            if response.status_code == 200:
                self.request_counter.add(1, {"service": "composer", "status": "success"})
                self.response_time_histogram.record(composer_time, {"service": "composer"})
                logger.debug(f"Composer: 成功 (応答時間: {composer_time:.3f}s)")
            else:
                self.error_counter.add(1, {"service": "composer", "status": "error"})
                logger.warning(f"Composer: 失敗 (ステータス: {response.status_code})")
                
        except Exception as e:
            self.error_counter.add(1, {"service": "composer", "status": "error"})
            logger.error(f"Composer メトリクス収集エラー: {e}")
        
        try:
            # MCP API テスト
            start_time = time.time()
            response = await self.client.post(
                "http://localhost:8000/mcp/generate",
                json={
                    "title": "テスト",
                    "content": "テスト内容",
                    "style": "educational"
                }
            )
            mcp_time = time.time() - start_time
            
            if response.status_code == 200:
                self.request_counter.add(1, {"service": "mcp", "status": "success"})
                self.response_time_histogram.record(mcp_time, {"service": "mcp"})
                logger.debug(f"MCP: 成功 (応答時間: {mcp_time:.3f}s)")
            else:
                self.error_counter.add(1, {"service": "mcp", "status": "error"})
                logger.warning(f"MCP: 失敗 (ステータス: {response.status_code})")
                
        except Exception as e:
            self.error_counter.add(1, {"service": "mcp", "status": "error"})
            logger.error(f"MCP メトリクス収集エラー: {e}")
    
    async def collect_database_metrics(self):
        """データベースメトリクスの収集"""
        try:
            # PostgreSQL接続テスト
            import psycopg2
            
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="ai_systems",
                user="ai_user",
                password=os.getenv("POSTGRES_PASSWORD", "")
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            self.request_counter.add(1, {"service": "postgresql", "status": "success"})
            logger.debug("PostgreSQL: 正常")
            
        except Exception as e:
            self.error_counter.add(1, {"service": "postgresql", "status": "error"})
            logger.error(f"PostgreSQL メトリクス収集エラー: {e}")
        
        try:
            # Redis接続テスト
            import redis
            
            r = redis.Redis(host="localhost", port=6379, decode_responses=True)
            r.ping()
            
            self.request_counter.add(1, {"service": "redis", "status": "success"})
            logger.debug("Redis: 正常")
            
        except Exception as e:
            self.error_counter.add(1, {"service": "redis", "status": "error"})
            logger.error(f"Redis メトリクス収集エラー: {e}")
    
    async def run_collection_loop(self):
        """メトリクス収集ループ"""
        logger.info("メトリクス収集を開始しました")
        
        while True:
            try:
                # システムメトリクス
                await self.collect_system_metrics()
                
                # サービスメトリクス
                await self.collect_service_metrics()
                
                # AI関連メトリクス
                await self.collect_ai_metrics()
                
                # データベースメトリクス
                await self.collect_database_metrics()
                
                logger.info("メトリクス収集完了")
                
                # 60秒待機
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"メトリクス収集ループエラー: {e}")
                await asyncio.sleep(60)

async def main():
    """メイン関数"""
    collector = MetricsCollector()
    await collector.run_collection_loop()

if __name__ == "__main__":
    asyncio.run(main()) 