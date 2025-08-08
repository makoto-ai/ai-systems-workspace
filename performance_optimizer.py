#!/usr/bin/env python3
"""
Performance Optimization System
パフォーマンス最適化システム
"""

import asyncio
import time
import psutil
import streamlit as st
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import gc
import tracemalloc

class PerformanceOptimizer:
    """パフォーマンス最適化システム"""
    
    def __init__(self):
        self.setup_logging()
        self.performance_metrics = {}
        self.optimization_history = []
        self.cache = {}
        self.background_tasks = {}
        
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('performance_optimizer.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def monitor_system_performance(self) -> Dict[str, Any]:
        """システム性能監視"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # メモリ使用率
            memory = psutil.virtual_memory()
            
            # ディスク使用率
            disk = psutil.disk_usage('/')
            
            # プロセス数
            process_count = len(psutil.pids())
            
            # ネットワーク使用量
            network = psutil.net_io_counters()
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'disk_percent': disk.percent,
                'disk_free': disk.free,
                'process_count': process_count,
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv
            }
            
            self.performance_metrics = metrics
            return metrics
            
        except Exception as e:
            self.logger.error(f"性能監視エラー: {e}")
            return {}
    
    def optimize_memory_usage(self) -> Dict[str, Any]:
        """メモリ使用量最適化"""
        try:
            # ガベージコレクション実行
            collected = gc.collect()
            
            # メモリ使用量の詳細分析
            memory_info = psutil.virtual_memory()
            
            # 大きなオブジェクトの検出
            tracemalloc.start()
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            
            optimization_result = {
                'timestamp': datetime.now().isoformat(),
                'gc_collected': collected,
                'memory_before': memory_info.used,
                'memory_after': psutil.virtual_memory().used,
                'memory_saved': memory_info.used - psutil.virtual_memory().used,
                'top_memory_users': [
                    {
                        'file': stat.traceback.format()[-1],
                        'size': stat.size,
                        'count': stat.count
                    }
                    for stat in top_stats[:5]
                ]
            }
            
            tracemalloc.stop()
            return optimization_result
            
        except Exception as e:
            self.logger.error(f"メモリ最適化エラー: {e}")
            return {}
    
    def optimize_cache(self, max_size: int = 1000) -> Dict[str, Any]:
        """キャッシュ最適化"""
        try:
            cache_size_before = len(self.cache)
            
            # LRUキャッシュ実装
            if len(self.cache) > max_size:
                # 最も古いエントリを削除
                oldest_keys = sorted(self.cache.keys(), key=lambda k: self.cache[k].get('timestamp', 0))[:len(self.cache) - max_size]
                for key in oldest_keys:
                    del self.cache[key]
            
            cache_size_after = len(self.cache)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cache_size_before': cache_size_before,
                'cache_size_after': cache_size_after,
                'cache_entries_removed': cache_size_before - cache_size_after,
                'max_cache_size': max_size
            }
            
        except Exception as e:
            self.logger.error(f"キャッシュ最適化エラー: {e}")
            return {}
    
    def optimize_background_tasks(self) -> Dict[str, Any]:
        """バックグラウンドタスク最適化"""
        try:
            active_tasks = len(self.background_tasks)
            completed_tasks = 0
            failed_tasks = 0
            
            # 完了したタスクのクリーンアップ
            tasks_to_remove = []
            for task_id, task_info in self.background_tasks.items():
                if task_info.get('status') == 'completed':
                    completed_tasks += 1
                    tasks_to_remove.append(task_id)
                elif task_info.get('status') == 'failed':
                    failed_tasks += 1
                    tasks_to_remove.append(task_id)
            
            # 完了/失敗したタスクを削除
            for task_id in tasks_to_remove:
                del self.background_tasks[task_id]
            
            return {
                'timestamp': datetime.now().isoformat(),
                'active_tasks': len(self.background_tasks),
                'completed_tasks': completed_tasks,
                'failed_tasks': failed_tasks,
                'tasks_cleaned': len(tasks_to_remove)
            }
            
        except Exception as e:
            self.logger.error(f"バックグラウンドタスク最適化エラー: {e}")
            return {}
    
    def add_to_cache(self, key: str, value: Any, ttl: int = 3600):
        """キャッシュに追加"""
        self.cache[key] = {
            'value': value,
            'timestamp': time.time(),
            'ttl': ttl
        }
    
    def get_from_cache(self, key: str) -> Optional[Any]:
        """キャッシュから取得"""
        if key in self.cache:
            cache_entry = self.cache[key]
            if time.time() - cache_entry['timestamp'] < cache_entry['ttl']:
                return cache_entry['value']
            else:
                # TTL期限切れ
                del self.cache[key]
        return None
    
    def run_background_task(self, task_id: str, task_func, *args, **kwargs):
        """バックグラウンドタスク実行"""
        def task_wrapper():
            try:
                self.background_tasks[task_id] = {
                    'status': 'running',
                    'start_time': time.time(),
                    'args': args,
                    'kwargs': kwargs
                }
                
                result = task_func(*args, **kwargs)
                
                self.background_tasks[task_id].update({
                    'status': 'completed',
                    'result': result,
                    'end_time': time.time(),
                    'duration': time.time() - self.background_tasks[task_id]['start_time']
                })
                
                return result
                
            except Exception as e:
                self.background_tasks[task_id].update({
                    'status': 'failed',
                    'error': str(e),
                    'end_time': time.time()
                })
                self.logger.error(f"バックグラウンドタスクエラー {task_id}: {e}")
                raise
        
        # スレッドプールで実行
        with ThreadPoolExecutor(max_workers=4) as executor:
            future = executor.submit(task_wrapper)
            return future
    
    def get_performance_report(self) -> Dict[str, Any]:
        """性能レポート生成"""
        current_metrics = self.monitor_system_performance()
        
        # 最適化実行
        memory_optimization = self.optimize_memory_usage()
        cache_optimization = self.optimize_cache()
        task_optimization = self.optimize_background_tasks()
        
        # 性能スコア計算
        performance_score = self.calculate_performance_score(current_metrics)
        
        return {
            'current_metrics': current_metrics,
            'memory_optimization': memory_optimization,
            'cache_optimization': cache_optimization,
            'task_optimization': task_optimization,
            'performance_score': performance_score,
            'recommendations': self.generate_recommendations(current_metrics)
        }
    
    def calculate_performance_score(self, metrics: Dict[str, Any]) -> float:
        """性能スコア計算"""
        if not metrics:
            return 0.0
        
        score = 100.0
        
        # CPU使用率による減点
        cpu_percent = metrics.get('cpu_percent', 0)
        if cpu_percent > 80:
            score -= 20
        elif cpu_percent > 60:
            score -= 10
        elif cpu_percent > 40:
            score -= 5
        
        # メモリ使用率による減点
        memory_percent = metrics.get('memory_percent', 0)
        if memory_percent > 90:
            score -= 25
        elif memory_percent > 80:
            score -= 15
        elif memory_percent > 70:
            score -= 10
        
        # ディスク使用率による減点
        disk_percent = metrics.get('disk_percent', 0)
        if disk_percent > 90:
            score -= 15
        elif disk_percent > 80:
            score -= 10
        
        return max(0.0, score)
    
    def generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """改善推奨事項生成"""
        recommendations = []
        
        cpu_percent = metrics.get('cpu_percent', 0)
        memory_percent = metrics.get('memory_percent', 0)
        disk_percent = metrics.get('disk_percent', 0)
        
        if cpu_percent > 80:
            recommendations.append("🚨 CPU使用率が高いです。不要なプロセスを終了してください。")
        
        if memory_percent > 90:
            recommendations.append("🚨 メモリ使用率が高いです。メモリリークを確認してください。")
        
        if disk_percent > 90:
            recommendations.append("🚨 ディスク使用率が高いです。不要なファイルを削除してください。")
        
        if cpu_percent < 30 and memory_percent < 50:
            recommendations.append("✅ システム性能は良好です。")
        
        if not recommendations:
            recommendations.append("✅ システムは最適な状態です。")
        
        return recommendations

class AsyncTaskManager:
    """非同期タスク管理"""
    
    def __init__(self):
        self.task_queue = asyncio.Queue()
        self.results = {}
        self.running = False
        
    async def start_worker(self):
        """ワーカー開始"""
        self.running = True
        while self.running:
            try:
                task = await self.task_queue.get()
                if task is None:
                    break
                
                task_id, func, args, kwargs = task
                try:
                    result = await func(*args, **kwargs)
                    self.results[task_id] = {
                        'status': 'completed',
                        'result': result,
                        'timestamp': datetime.now().isoformat()
                    }
                except Exception as e:
                    self.results[task_id] = {
                        'status': 'failed',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                
                self.task_queue.task_done()
                
            except Exception as e:
                logging.error(f"ワーカーエラー: {e}")
    
    async def add_task(self, task_id: str, func, *args, **kwargs):
        """タスク追加"""
        await self.task_queue.put((task_id, func, args, kwargs))
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """タスク結果取得"""
        return self.results.get(task_id)
    
    def stop_worker(self):
        """ワーカー停止"""
        self.running = False

def display_performance_optimizer_interface():
    """パフォーマンス最適化インターフェース表示"""
    st.header("⚡ パフォーマンス最適化システム")
    
    optimizer = PerformanceOptimizer()
    
    # タブ作成
    tab1, tab2, tab3, tab4 = st.tabs(["📊 性能監視", "🔧 最適化", "📈 レポート", "⚙️ 設定"])
    
    with tab1:
        st.subheader("📊 リアルタイム性能監視")
        
        if st.button("🔄 性能監視更新"):
            with st.spinner("性能監視中..."):
                metrics = optimizer.monitor_system_performance()
                
                if metrics:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("CPU使用率", f"{metrics['cpu_percent']:.1f}%")
                        st.metric("プロセス数", metrics['process_count'])
                    
                    with col2:
                        st.metric("メモリ使用率", f"{metrics['memory_percent']:.1f}%")
                        st.metric("利用可能メモリ", f"{metrics['memory_available'] / 1024 / 1024 / 1024:.1f} GB")
                    
                    with col3:
                        st.metric("ディスク使用率", f"{metrics['disk_percent']:.1f}%")
                        st.metric("空き容量", f"{metrics['disk_free'] / 1024 / 1024 / 1024:.1f} GB")
                    
                    with col4:
                        st.metric("送信バイト", f"{metrics['network_bytes_sent'] / 1024 / 1024:.1f} MB")
                        st.metric("受信バイト", f"{metrics['network_bytes_recv'] / 1024 / 1024:.1f} MB")
    
    with tab2:
        st.subheader("🔧 最適化実行")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🧠 メモリ最適化"):
                with st.spinner("メモリ最適化中..."):
                    result = optimizer.optimize_memory_usage()
                    
                    if result:
                        st.success("メモリ最適化完了！")
                        st.metric("節約メモリ", f"{result['memory_saved'] / 1024 / 1024:.1f} MB")
                        st.metric("GC回収", result['gc_collected'])
        
        with col2:
            if st.button("💾 キャッシュ最適化"):
                with st.spinner("キャッシュ最適化中..."):
                    result = optimizer.optimize_cache()
                    
                    if result:
                        st.success("キャッシュ最適化完了！")
                        st.metric("削除エントリ", result['cache_entries_removed'])
                        st.metric("現在サイズ", result['cache_size_after'])
        
        with col3:
            if st.button("⚙️ タスク最適化"):
                with st.spinner("タスク最適化中..."):
                    result = optimizer.optimize_background_tasks()
                    
                    if result:
                        st.success("タスク最適化完了！")
                        st.metric("アクティブタスク", result['active_tasks'])
                        st.metric("完了タスク", result['completed_tasks'])
    
    with tab3:
        st.subheader("📈 性能レポート")
        
        if st.button("📊 レポート生成"):
            with st.spinner("性能レポート生成中..."):
                report = optimizer.get_performance_report()
                
                if report:
                    # 性能スコア
                    st.metric("性能スコア", f"{report['performance_score']:.1f}/100")
                    
                    # 推奨事項
                    st.subheader("💡 改善推奨事項")
                    for recommendation in report['recommendations']:
                        st.write(recommendation)
                    
                    # 詳細レポート
                    with st.expander("📋 詳細レポート"):
                        st.json(report)
    
    with tab4:
        st.subheader("⚙️ 最適化設定")
        
        # キャッシュ設定
        st.write("**💾 キャッシュ設定**")
        cache_key = st.text_input("キャッシュキー")
        cache_value = st.text_input("キャッシュ値")
        cache_ttl = st.number_input("TTL（秒）", min_value=1, value=3600)
        
        if st.button("💾 キャッシュ追加"):
            optimizer.add_to_cache(cache_key, cache_value, cache_ttl)
            st.success(f"キャッシュ追加: {cache_key}")
        
        # キャッシュ検索
        search_key = st.text_input("検索キー")
        if st.button("🔍 キャッシュ検索"):
            result = optimizer.get_from_cache(search_key)
            if result:
                st.success(f"キャッシュヒット: {result}")
            else:
                st.info("キャッシュミス")

if __name__ == "__main__":
    display_performance_optimizer_interface() 