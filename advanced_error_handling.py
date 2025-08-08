#!/usr/bin/env python3
"""
Advanced Error Handling and Recovery System
高度なエラーハンドリング・リカバリシステム
"""

import traceback
import sys
import logging
import streamlit as st
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import json
import time
from functools import wraps
import threading
import queue

class ErrorSeverity:
    """エラー重要度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorHandler:
    """高度なエラーハンドラー"""
    
    def __init__(self):
        self.setup_logging()
        self.error_history = []
        self.recovery_strategies = {}
        self.error_patterns = {}
        self.auto_recovery_enabled = True
        
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('error_handler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None, severity: str = ErrorSeverity.MEDIUM):
        """エラーログ記録"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'severity': severity,
            'context': context or {},
            'recovered': False
        }
        
        self.error_history.append(error_info)
        
        # ログ出力
        if severity == ErrorSeverity.CRITICAL:
            self.logger.error(f"重大エラー: {error}")
        elif severity == ErrorSeverity.HIGH:
            self.logger.warning(f"高重要度エラー: {error}")
        else:
            self.logger.info(f"エラー: {error}")
        
        # エラーパターン分析
        self.analyze_error_pattern(error_info)
        
        return error_info
    
    def analyze_error_pattern(self, error_info: Dict[str, Any]):
        """エラーパターン分析"""
        error_type = error_info['error_type']
        
        if error_type not in self.error_patterns:
            self.error_patterns[error_type] = {
                'count': 0,
                'first_occurrence': error_info['timestamp'],
                'last_occurrence': error_info['timestamp'],
                'severity_distribution': {}
            }
        
        pattern = self.error_patterns[error_type]
        pattern['count'] += 1
        pattern['last_occurrence'] = error_info['timestamp']
        
        severity = error_info['severity']
        if severity not in pattern['severity_distribution']:
            pattern['severity_distribution'][severity] = 0
        pattern['severity_distribution'][severity] += 1
    
    def register_recovery_strategy(self, error_type: str, recovery_func: Callable):
        """リカバリ戦略登録"""
        self.recovery_strategies[error_type] = recovery_func
        self.logger.info(f"リカバリ戦略登録: {error_type}")
    
    def attempt_recovery(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """リカバリ試行"""
        if not self.auto_recovery_enabled:
            return {'success': False, 'reason': 'Auto recovery disabled'}
        
        error_type = error_info['error_type']
        
        if error_type in self.recovery_strategies:
            try:
                recovery_func = self.recovery_strategies[error_type]
                result = recovery_func(error_info)
                
                error_info['recovered'] = True
                error_info['recovery_result'] = result
                
                self.logger.info(f"リカバリ成功: {error_type}")
                return {'success': True, 'result': result}
                
            except Exception as recovery_error:
                self.logger.error(f"リカバリ失敗: {recovery_error}")
                return {'success': False, 'error': str(recovery_error)}
        else:
            return {'success': False, 'reason': 'No recovery strategy available'}
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """エラー統計取得"""
        if not self.error_history:
            return {}
        
        total_errors = len(self.error_history)
        recovered_errors = len([e for e in self.error_history if e.get('recovered', False)])
        
        severity_counts = {}
        for error in self.error_history:
            severity = error['severity']
            if severity not in severity_counts:
                severity_counts[severity] = 0
            severity_counts[severity] += 1
        
        return {
            'total_errors': total_errors,
            'recovered_errors': recovered_errors,
            'recovery_rate': (recovered_errors / total_errors * 100) if total_errors > 0 else 0,
            'severity_distribution': severity_counts,
            'error_patterns': self.error_patterns,
            'auto_recovery_enabled': self.auto_recovery_enabled
        }
    
    def get_recent_errors(self, hours: int = 24) -> List[Dict[str, Any]]:
        """最近のエラー取得"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        return [e for e in self.error_history if datetime.fromisoformat(e['timestamp']).timestamp() > cutoff_time]

class CircuitBreaker:
    """サーキットブレーカー"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        
    def call(self, func: Callable, *args, **kwargs):
        """サーキットブレーカー付き関数呼び出し"""
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
    
    def on_success(self):
        """成功時の処理"""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def on_failure(self):
        """失敗時の処理"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'

class RetryMechanism:
    """リトライメカニズム"""
    
    def __init__(self, max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.delay = delay
        self.backoff_factor = backoff_factor
    
    def retry(self, func: Callable, *args, **kwargs):
        """リトライ付き関数実行"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    sleep_time = self.delay * (self.backoff_factor ** attempt)
                    time.sleep(sleep_time)
                else:
                    break
        
        raise last_exception

class ErrorDecorator:
    """エラーハンドリングデコレーター"""
    
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
    
    def handle_errors(self, severity: str = ErrorSeverity.MEDIUM):
        """エラーハンドリングデコレーター"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_info = self.error_handler.log_error(e, {
                        'function': func.__name__,
                        'args': args,
                        'kwargs': kwargs
                    }, severity)
                    
                    # リカバリ試行
                    recovery_result = self.error_handler.attempt_recovery(error_info)
                    
                    if not recovery_result['success']:
                        raise e
                    
                    return recovery_result['result']
            
            return wrapper
        return decorator

class AdvancedErrorRecovery:
    """高度なエラーリカバリシステム"""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.circuit_breakers = {}
        self.retry_mechanisms = {}
        self.setup_default_recovery_strategies()
    
    def setup_default_recovery_strategies(self):
        """デフォルトリカバリ戦略設定"""
        # ネットワークエラーリカバリ
        self.error_handler.register_recovery_strategy('ConnectionError', self.recover_network_error)
        self.error_handler.register_recovery_strategy('TimeoutError', self.recover_timeout_error)
        self.error_handler.register_recovery_strategy('ValueError', self.recover_value_error)
        self.error_handler.register_recovery_strategy('KeyError', self.recover_key_error)
    
    def recover_network_error(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """ネットワークエラーリカバリ"""
        # 簡易的なリカバリ（実際の実装ではより複雑）
        return {
            'strategy': 'network_retry',
            'attempts': 3,
            'backoff_delay': 2.0
        }
    
    def recover_timeout_error(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """タイムアウトエラーリカバリ"""
        return {
            'strategy': 'timeout_increase',
            'new_timeout': 30.0
        }
    
    def recover_value_error(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """値エラーリカバリ"""
        return {
            'strategy': 'default_value',
            'default_value': None
        }
    
    def recover_key_error(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """キーエラーリカバリ"""
        return {
            'strategy': 'safe_access',
            'safe_key': 'default'
        }
    
    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """サーキットブレーカー取得"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker()
        return self.circuit_breakers[name]
    
    def get_retry_mechanism(self, name: str) -> RetryMechanism:
        """リトライメカニズム取得"""
        if name not in self.retry_mechanisms:
            self.retry_mechanisms[name] = RetryMechanism()
        return self.retry_mechanisms[name]

def display_advanced_error_handling_interface():
    """高度なエラーハンドリングインターフェース表示"""
    st.header("🛡️ 高度なエラーハンドリング・リカバリシステム")
    
    recovery_system = AdvancedErrorRecovery()
    
    # タブ作成
    tab1, tab2, tab3, tab4 = st.tabs(["📊 エラー監視", "🔧 リカバリ", "📈 統計", "⚙️ 設定"])
    
    with tab1:
        st.subheader("📊 エラー監視")
        
        # エラー統計
        stats = recovery_system.error_handler.get_error_statistics()
        
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("総エラー数", stats['total_errors'])
                st.metric("リカバリ成功", stats['recovered_errors'])
            
            with col2:
                st.metric("リカバリ率", f"{stats['recovery_rate']:.1f}%")
                st.metric("自動リカバリ", "✅" if stats['auto_recovery_enabled'] else "❌")
            
            with col3:
                if 'severity_distribution' in stats:
                    st.write("**重要度分布:**")
                    for severity, count in stats['severity_distribution'].items():
                        st.write(f"- {severity}: {count}")
            
            with col4:
                if 'error_patterns' in stats:
                    st.write("**エラーパターン:**")
                    for pattern, info in list(stats['error_patterns'].items())[:3]:
                        st.write(f"- {pattern}: {info['count']}回")
        
        # 最近のエラー
        st.subheader("🕐 最近のエラー")
        recent_errors = recovery_system.error_handler.get_recent_errors(24)
        
        if recent_errors:
            for error in recent_errors[-5:]:  # 最新5件
                with st.expander(f"❌ {error['error_type']} - {error['timestamp'][:19]}"):
                    st.write(f"**メッセージ:** {error['error_message']}")
                    st.write(f"**重要度:** {error['severity']}")
                    st.write(f"**リカバリ:** {'✅' if error.get('recovered') else '❌'}")
                    
                    if error.get('recovery_result'):
                        st.write("**リカバリ結果:**")
                        st.json(error['recovery_result'])
        else:
            st.success("最近のエラーはありません")
    
    with tab2:
        st.subheader("🔧 リカバリ戦略")
        
        # リカバリ戦略テスト
        st.write("**🧪 リカバリ戦略テスト**")
        
        test_error_type = st.selectbox("テストエラー種別", ["ConnectionError", "TimeoutError", "ValueError", "KeyError"])
        
        if st.button("🔧 リカバリテスト"):
            # テストエラー作成
            test_error_info = {
                'error_type': test_error_type,
                'error_message': f'Test {test_error_type}',
                'severity': ErrorSeverity.MEDIUM
            }
            
            with st.spinner("リカバリテスト中..."):
                recovery_result = recovery_system.error_handler.attempt_recovery(test_error_info)
                
                if recovery_result['success']:
                    st.success("リカバリ成功！")
                    st.json(recovery_result['result'])
                else:
                    st.error(f"リカバリ失敗: {recovery_result.get('reason', 'Unknown error')}")
        
        # サーキットブレーカーテスト
        st.subheader("⚡ サーキットブレーカーテスト")
        
        breaker_name = st.text_input("ブレーカー名", "test_breaker")
        
        if st.button("⚡ ブレーカーテスト"):
            circuit_breaker = recovery_system.get_circuit_breaker(breaker_name)
            
            st.write(f"**状態:** {circuit_breaker.state}")
            st.write(f"**失敗回数:** {circuit_breaker.failure_count}")
            st.write(f"**閾値:** {circuit_breaker.failure_threshold}")
    
    with tab3:
        st.subheader("📈 エラー統計")
        
        if st.button("📊 統計更新"):
            stats = recovery_system.error_handler.get_error_statistics()
            
            if stats:
                # エラートレンド
                st.subheader("📈 エラートレンド")
                
                # 重要度別エラー数
                if 'severity_distribution' in stats:
                    severity_data = stats['severity_distribution']
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**重要度別エラー数:**")
                        for severity, count in severity_data.items():
                            st.metric(severity, count)
                    
                    with col2:
                        st.write("**リカバリ統計:**")
                        st.metric("総エラー", stats['total_errors'])
                        st.metric("リカバリ成功", stats['recovered_errors'])
                        st.metric("リカバリ率", f"{stats['recovery_rate']:.1f}%")
                
                # 詳細統計
                with st.expander("📋 詳細統計"):
                    st.json(stats)
    
    with tab4:
        st.subheader("⚙️ エラーハンドリング設定")
        
        # 自動リカバリ設定
        auto_recovery = st.checkbox("自動リカバリ有効", value=recovery_system.error_handler.auto_recovery_enabled)
        
        if st.button("💾 設定保存"):
            recovery_system.error_handler.auto_recovery_enabled = auto_recovery
            st.success("設定保存完了！")
        
        # エラーログクリア
        if st.button("🗑️ エラーログクリア"):
            recovery_system.error_handler.error_history.clear()
            st.success("エラーログクリア完了！")
        
        # カスタムリカバリ戦略
        st.subheader("🔧 カスタムリカバリ戦略")
        
        strategy_error_type = st.text_input("エラー種別")
        strategy_code = st.text_area("リカバリコード", "return {'strategy': 'custom'}")
        
        if st.button("➕ 戦略追加"):
            try:
                # 簡易的な戦略追加（実際の実装ではより安全）
                def custom_recovery(error_info):
                    return eval(strategy_code)
                
                recovery_system.error_handler.register_recovery_strategy(strategy_error_type, custom_recovery)
                st.success(f"リカバリ戦略追加: {strategy_error_type}")
                
            except Exception as e:
                st.error(f"戦略追加エラー: {e}")

if __name__ == "__main__":
    display_advanced_error_handling_interface() 