#!/usr/bin/env python3
"""
ログ収集スクリプト
システム全体のログを収集・分析・保存
"""

import os
import sys
import json
import logging
import asyncio
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LogCollector:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'ai_systems'),
            'user': os.getenv('POSTGRES_USER', 'ai_user'),
            'password': os.getenv('POSTGRES_PASSWORD', '')
        }
        self.log_dirs = [
            '/app/logs',
            '/var/log',
            '/app/data/logs'
        ]
        self.services = [
            'ai-systems-app',
            'mcp-service',
            'composer-service',
            'voicevox-engine',
            'ollama',
            'postgres',
            'redis',
            'vault',
            'grafana',
            'prometheus'
        ]
        
    def get_db_connection(self):
        """データベース接続を取得"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            logger.error(f"データベース接続エラー: {e}")
            return None
    
    def insert_log(self, level: str, service_name: str, message: str, details: Dict[str, Any] = None):
        """ログをデータベースに挿入"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_logs (level, service_name, message, details)
                VALUES (%s, %s, %s, %s)
            """, (level, service_name, message, json.dumps(details) if details else None))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"ログ挿入エラー: {e}")
            return False
    
    def collect_docker_logs(self):
        """Dockerコンテナのログを収集"""
        import subprocess
        
        for service in self.services:
            try:
                # Docker logs コマンド実行
                result = subprocess.run([
                    'docker', 'logs', '--since', '1h', service
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    logs = result.stdout.strip().split('\n')
                    for log_line in logs[-100:]:  # 最新100行のみ
                        if log_line.strip():
                            # ログレベルを判定
                            level = self.determine_log_level(log_line)
                            self.insert_log(level, service, log_line)
                    
                    logger.info(f"{service} ログ収集完了: {len(logs)} 行")
                else:
                    logger.warning(f"{service} ログ収集失敗: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                logger.error(f"{service} ログ収集タイムアウト")
            except Exception as e:
                logger.error(f"{service} ログ収集エラー: {e}")
    
    def collect_file_logs(self):
        """ファイルログを収集"""
        log_patterns = [
            '*.log',
            '*.out',
            '*.err',
            '*.txt'
        ]
        
        for log_dir in self.log_dirs:
            if os.path.exists(log_dir):
                for pattern in log_patterns:
                    log_files = Path(log_dir).glob(pattern)
                    for log_file in log_files:
                        try:
                            # 最新のログのみを読み取り
                            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                                lines = f.readlines()
                                for line in lines[-50:]:  # 最新50行のみ
                                    if line.strip():
                                        level = self.determine_log_level(line)
                                        service_name = log_file.stem
                                        self.insert_log(level, service_name, line.strip())
                            
                            logger.info(f"{log_file} ログ収集完了")
                        except Exception as e:
                            logger.error(f"{log_file} ログ収集エラー: {e}")
    
    def determine_log_level(self, log_line: str) -> str:
        """ログレベルを判定"""
        log_line_lower = log_line.lower()
        
        if any(keyword in log_line_lower for keyword in ['error', 'exception', 'failed', 'failure']):
            return 'ERROR'
        elif any(keyword in log_line_lower for keyword in ['warn', 'warning']):
            return 'WARNING'
        elif any(keyword in log_line_lower for keyword in ['debug']):
            return 'DEBUG'
        else:
            return 'INFO'
    
    def collect_system_logs(self):
        """システムログを収集"""
        try:
            import psutil
            
            # システム情報ログ
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            system_info = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'memory_available': memory.available,
                'disk_free': disk.free
            }
            
            self.insert_log('INFO', 'system', 'システム情報収集', system_info)
            
            # プロセス情報
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 上位10プロセス
            top_processes = sorted(processes, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:10]
            self.insert_log('INFO', 'system', 'プロセス情報', {'top_processes': top_processes})
            
        except Exception as e:
            logger.error(f"システムログ収集エラー: {e}")
    
    def collect_application_logs(self):
        """アプリケーション固有のログを収集"""
        # FastAPI アプリケーションログ
        app_logs = [
            '/app/logs/app.log',
            '/app/logs/access.log',
            '/app/logs/error.log'
        ]
        
        for log_file in app_logs:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for line in lines[-100:]:
                            if line.strip():
                                level = self.determine_log_level(line)
                                self.insert_log(level, 'fastapi', line.strip())
                except Exception as e:
                    logger.error(f"アプリケーションログ収集エラー: {e}")
    
    def analyze_logs(self):
        """ログ分析"""
        conn = self.get_db_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            # エラーログ分析
            cursor.execute("""
                SELECT service_name, COUNT(*) as error_count
                FROM system_logs
                WHERE level = 'ERROR' AND timestamp >= NOW() - INTERVAL '1 hour'
                GROUP BY service_name
                ORDER BY error_count DESC
            """)
            
            error_stats = cursor.fetchall()
            if error_stats:
                self.insert_log('INFO', 'log-analyzer', 'エラーログ分析', {
                    'error_stats': dict(error_stats)
                })
            
            # サービス別ログ統計
            cursor.execute("""
                SELECT service_name, level, COUNT(*) as count
                FROM system_logs
                WHERE timestamp >= NOW() - INTERVAL '1 hour'
                GROUP BY service_name, level
                ORDER BY service_name, level
            """)
            
            log_stats = cursor.fetchall()
            if log_stats:
                stats_dict = {}
                for service, level, count in log_stats:
                    if service not in stats_dict:
                        stats_dict[service] = {}
                    stats_dict[service][level] = count
                
                self.insert_log('INFO', 'log-analyzer', 'ログ統計', stats_dict)
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"ログ分析エラー: {e}")
    
    def cleanup_old_logs(self):
        """古いログをクリーンアップ"""
        conn = self.get_db_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            # 30日以上古いログを削除
            cursor.execute("""
                DELETE FROM system_logs
                WHERE timestamp < NOW() - INTERVAL '30 days'
            """)
            
            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            if deleted_count > 0:
                logger.info(f"古いログを削除しました: {deleted_count} 件")
                
        except Exception as e:
            logger.error(f"ログクリーンアップエラー: {e}")
    
    def generate_log_report(self):
        """ログレポート生成"""
        conn = self.get_db_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            # 過去24時間のログ統計
            cursor.execute("""
                SELECT 
                    service_name,
                    level,
                    COUNT(*) as count,
                    MIN(timestamp) as first_log,
                    MAX(timestamp) as last_log
                FROM system_logs
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
                GROUP BY service_name, level
                ORDER BY service_name, level
            """)
            
            daily_stats = cursor.fetchall()
            
            # エラー率計算
            cursor.execute("""
                SELECT 
                    service_name,
                    COUNT(*) as total_logs,
                    COUNT(CASE WHEN level = 'ERROR' THEN 1 END) as error_logs,
                    ROUND(
                        COUNT(CASE WHEN level = 'ERROR' THEN 1 END) * 100.0 / COUNT(*), 2
                    ) as error_rate
                FROM system_logs
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
                GROUP BY service_name
                HAVING COUNT(*) > 0
                ORDER BY error_rate DESC
            """)
            
            error_rates = cursor.fetchall()
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'period': '24 hours',
                'daily_stats': [dict(zip(['service', 'level', 'count', 'first_log', 'last_log'], row)) for row in daily_stats],
                'error_rates': [dict(zip(['service', 'total_logs', 'error_logs', 'error_rate'], row)) for row in error_rates]
            }
            
            # レポートをファイルに保存
            report_file = f"/app/logs/log_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.insert_log('INFO', 'log-analyzer', 'ログレポート生成完了', {
                'report_file': report_file,
                'total_services': len(set(row[0] for row in daily_stats)),
                'total_logs': sum(row[2] for row in daily_stats)
            })
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"ログレポート生成エラー: {e}")
    
    async def run_collection_loop(self):
        """ログ収集ループ"""
        logger.info("ログ収集を開始しました")
        
        while True:
            try:
                # Dockerログ収集
                self.collect_docker_logs()
                
                # ファイルログ収集
                self.collect_file_logs()
                
                # システムログ収集
                self.collect_system_logs()
                
                # アプリケーションログ収集
                self.collect_application_logs()
                
                # ログ分析
                self.analyze_logs()
                
                # 古いログクリーンアップ（毎日1回）
                if datetime.now().hour == 2 and datetime.now().minute < 5:
                    self.cleanup_old_logs()
                
                # ログレポート生成（毎日0時）
                if datetime.now().hour == 0 and datetime.now().minute < 5:
                    self.generate_log_report()
                
                logger.info("ログ収集完了")
                
                # 5分待機
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"ログ収集ループエラー: {e}")
                await asyncio.sleep(60)

async def main():
    """メイン関数"""
    collector = LogCollector()
    await collector.run_collection_loop()

if __name__ == "__main__":
    asyncio.run(main()) 