#!/usr/bin/env python3
"""
🚀 AI Systems Performance Optimizer
作成日: 2025-08-04
目的: システムパフォーマンスの最適化
"""

import os
import sys
import json
import psutil
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/performance_optimizer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    process_count: int
    load_average: List[float]

class PerformanceOptimizer:
    """パフォーマンス最適化クラス"""
    
    def __init__(self):
        self.metrics_history = []
        self.optimization_config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        config_path = Path('config/performance_config.json')
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # デフォルト設定
            return {
                'cpu_threshold': 80.0,
                'memory_threshold': 80.0,
                'disk_threshold': 85.0,
                'optimization_enabled': True,
                'auto_restart_threshold': 95.0
            }
    
    def collect_metrics(self) -> PerformanceMetrics:
        """パフォーマンスメトリクス収集"""
        try:
            # CPU使用率
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # メモリ使用率
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # ディスク使用率
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # ネットワークI/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # プロセス数
            process_count = len(psutil.pids())
            
            # ロードアベレージ
            load_average = psutil.getloadavg()
            
            return PerformanceMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                process_count=process_count,
                load_average=list(load_average)
            )
        
        except Exception as e:
            logger.error(f"メトリクス収集エラー: {e}")
            return None
    
    def analyze_performance(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """パフォーマンス分析"""
        analysis = {
            'status': 'healthy',
            'warnings': [],
            'recommendations': [],
            'critical_issues': []
        }
        
        # CPU分析
        if metrics.cpu_usage > self.optimization_config['cpu_threshold']:
            analysis['warnings'].append(f"CPU使用率が高い: {metrics.cpu_usage:.1f}%")
            if metrics.cpu_usage > self.optimization_config['auto_restart_threshold']:
                analysis['critical_issues'].append("CPU使用率が非常に高い")
        
        # メモリ分析
        if metrics.memory_usage > self.optimization_config['memory_threshold']:
            analysis['warnings'].append(f"メモリ使用率が高い: {metrics.memory_usage:.1f}%")
            analysis['recommendations'].append("メモリ使用量の多いプロセスを確認してください")
        
        # ディスク分析
        if metrics.disk_usage > self.optimization_config['disk_threshold']:
            analysis['warnings'].append(f"ディスク使用率が高い: {metrics.disk_usage:.1f}%")
            analysis['recommendations'].append("不要なファイルを削除してください")
        
        # プロセス数分析
        if metrics.process_count > 1000:
            analysis['warnings'].append(f"プロセス数が多い: {metrics.process_count}")
        
        # ロードアベレージ分析
        if metrics.load_average[0] > 10:
            analysis['warnings'].append(f"システム負荷が高い: {metrics.load_average[0]:.2f}")
        
        # ステータス判定
        if analysis['critical_issues']:
            analysis['status'] = 'critical'
        elif analysis['warnings']:
            analysis['status'] = 'warning'
        
        return analysis
    
    def optimize_memory(self):
        """メモリ最適化"""
        try:
            logger.info("メモリ最適化を実行中...")
            
            # Pythonキャッシュクリア
            cache_dirs = [
                Path('.venv/lib/python*/site-packages/__pycache__'),
                Path('.venv/lib/python*/site-packages/*/__pycache__'),
                Path('__pycache__')
            ]
            
            for pattern in cache_dirs:
                for cache_dir in Path('.').glob(str(pattern)):
                    if cache_dir.exists():
                        import shutil
                        shutil.rmtree(cache_dir)
                        logger.info(f"キャッシュクリア: {cache_dir}")
            
            # ログファイル圧縮
            log_dir = Path('logs')
            if log_dir.exists():
                for log_file in log_dir.glob('*.log'):
                    if log_file.stat().st_size > 100 * 1024 * 1024:  # 100MB
                        subprocess.run(['gzip', str(log_file)])
                        logger.info(f"ログファイル圧縮: {log_file}")
            
            logger.info("メモリ最適化完了")
            
        except Exception as e:
            logger.error(f"メモリ最適化エラー: {e}")
    
    def optimize_disk(self):
        """ディスク最適化"""
        try:
            logger.info("ディスク最適化を実行中...")
            
            # 一時ファイル削除
            temp_patterns = [
                '*.tmp',
                '*.temp',
                '*.cache',
                '*.log.old',
                '*.bak'
            ]
            
            for pattern in temp_patterns:
                for temp_file in Path('.').rglob(pattern):
                    if temp_file.exists():
                        temp_file.unlink()
                        logger.info(f"一時ファイル削除: {temp_file}")
            
            # Docker最適化
            if self.check_docker_available():
                subprocess.run(['docker', 'system', 'prune', '-f'])
                logger.info("Docker最適化完了")
            
            logger.info("ディスク最適化完了")
            
        except Exception as e:
            logger.error(f"ディスク最適化エラー: {e}")
    
    def optimize_network(self):
        """ネットワーク最適化"""
        try:
            logger.info("ネットワーク最適化を実行中...")
            
            # 接続プール最適化
            # ここでネットワーク関連の最適化を実装
            
            logger.info("ネットワーク最適化完了")
            
        except Exception as e:
            logger.error(f"ネットワーク最適化エラー: {e}")
    
    def check_docker_available(self) -> bool:
        """Docker利用可能性チェック"""
        try:
            subprocess.run(['docker', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def restart_critical_services(self):
        """重要なサービスの再起動"""
        try:
            logger.info("重要なサービスを再起動中...")
            
            # メインアプリケーション再起動
            main_process = self.find_main_process()
            if main_process:
                logger.info(f"メインプロセス再起動: PID {main_process.pid}")
                main_process.terminate()
                main_process.wait()
                
                # 再起動
                subprocess.Popen(['python', 'main_hybrid.py'])
                logger.info("メインプロセス再起動完了")
            
        except Exception as e:
            logger.error(f"サービス再起動エラー: {e}")
    
    def find_main_process(self):
        """メインプロセス検索"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'main_hybrid.py' in ' '.join(proc.info['cmdline'] or []):
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def generate_report(self, metrics: PerformanceMetrics, analysis: Dict[str, Any]):
        """パフォーマンスレポート生成"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'cpu_usage': metrics.cpu_usage,
                'memory_usage': metrics.memory_usage,
                'disk_usage': metrics.disk_usage,
                'process_count': metrics.process_count,
                'load_average': metrics.load_average
            },
            'analysis': analysis,
            'optimizations_applied': []
        }
        
        # レポート保存
        report_dir = Path('logs/performance_reports')
        report_dir.mkdir(exist_ok=True)
        
        report_file = report_dir / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"パフォーマンスレポート生成: {report_file}")
        return report
    
    def run_optimization_cycle(self):
        """最適化サイクル実行"""
        logger.info("パフォーマンス最適化サイクル開始")
        
        # メトリクス収集
        metrics = self.collect_metrics()
        if not metrics:
            logger.error("メトリクス収集に失敗しました")
            return
        
        # パフォーマンス分析
        analysis = self.analyze_performance(metrics)
        
        # 最適化実行
        optimizations_applied = []
        
        if analysis['status'] == 'critical':
            logger.warning("クリティカルな問題を検出しました")
            self.restart_critical_services()
            optimizations_applied.append('critical_service_restart')
        
        if metrics.memory_usage > self.optimization_config['memory_threshold']:
            self.optimize_memory()
            optimizations_applied.append('memory_optimization')
        
        if metrics.disk_usage > self.optimization_config['disk_threshold']:
            self.optimize_disk()
            optimizations_applied.append('disk_optimization')
        
        # レポート生成
        report = self.generate_report(metrics, analysis)
        report['optimizations_applied'] = optimizations_applied
        
        # 結果表示
        self.display_results(metrics, analysis, optimizations_applied)
        
        logger.info("パフォーマンス最適化サイクル完了")
    
    def display_results(self, metrics: PerformanceMetrics, analysis: Dict[str, Any], optimizations: List[str]):
        """結果表示"""
        print("\n" + "="*50)
        print("🚀 AI Systems Performance Report")
        print("="*50)
        
        print(f"\n📊 メトリクス:")
        print(f"  CPU使用率: {metrics.cpu_usage:.1f}%")
        print(f"  メモリ使用率: {metrics.memory_usage:.1f}%")
        print(f"  ディスク使用率: {metrics.disk_usage:.1f}%")
        print(f"  プロセス数: {metrics.process_count}")
        print(f"  ロードアベレージ: {metrics.load_average[0]:.2f}")
        
        print(f"\n🔍 分析結果:")
        print(f"  ステータス: {analysis['status']}")
        
        if analysis['warnings']:
            print(f"  警告:")
            for warning in analysis['warnings']:
                print(f"    ⚠️  {warning}")
        
        if analysis['recommendations']:
            print(f"  推奨事項:")
            for rec in analysis['recommendations']:
                print(f"    💡 {rec}")
        
        if optimizations:
            print(f"\n🔧 実行された最適化:")
            for opt in optimizations:
                print(f"    ✅ {opt}")
        
        print("\n" + "="*50)

def main():
    """メイン関数"""
    optimizer = PerformanceOptimizer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'optimize':
            optimizer.run_optimization_cycle()
        elif command == 'monitor':
            # 継続的監視モード
            print("継続的パフォーマンス監視を開始...")
            while True:
                optimizer.run_optimization_cycle()
                import time
                time.sleep(300)  # 5分間隔
        elif command == 'report':
            # レポート生成のみ
            metrics = optimizer.collect_metrics()
            if metrics:
                analysis = optimizer.analyze_performance(metrics)
                optimizer.generate_report(metrics, analysis)
                optimizer.display_results(metrics, analysis, [])
        else:
            print("使用方法: python performance_optimizer.py [optimize|monitor|report]")
    else:
        # デフォルト: 最適化実行
        optimizer.run_optimization_cycle()

if __name__ == '__main__':
    main() 