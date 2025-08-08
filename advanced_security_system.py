#!/usr/bin/env python3
"""
Advanced Security and Audit System
高度なセキュリティ・監査システム
"""

import hashlib
import hmac
import secrets
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import streamlit as st
from dataclasses import dataclass
from enum import Enum
import jwt
import bcrypt

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    timestamp: datetime
    event_type: str
    user_id: str
    ip_address: str
    action: str
    resource: str
    security_level: SecurityLevel
    details: Dict[str, Any]

class AdvancedSecuritySystem:
    """高度なセキュリティシステム"""
    
    def __init__(self):
        self.setup_logging()
        self.security_events = []
        self.blocked_ips = set()
        self.rate_limits = {}
        self.api_keys = {}
        self.session_tokens = {}
        
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('security_system.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def generate_api_key(self, user_id: str, permissions: List[str]) -> str:
        """APIキー生成"""
        api_key = secrets.token_urlsafe(32)
        self.api_keys[api_key] = {
            'user_id': user_id,
            'permissions': permissions,
            'created_at': datetime.now(),
            'last_used': None
        }
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """APIキー検証"""
        if api_key not in self.api_keys:
            return None
        
        key_info = self.api_keys[api_key]
        key_info['last_used'] = datetime.now()
        
        return key_info
    
    def log_security_event(self, event: SecurityEvent):
        """セキュリティイベント記録"""
        self.security_events.append(event)
        
        # イベントログ出力
        self.logger.info(f"セキュリティイベント: {event.event_type} - {event.user_id} - {event.action}")
        
        # セキュリティレベルに応じた処理
        if event.security_level == SecurityLevel.CRITICAL:
            self.handle_critical_event(event)
        elif event.security_level == SecurityLevel.HIGH:
            self.handle_high_security_event(event)
    
    def handle_critical_event(self, event: SecurityEvent):
        """重大イベント処理"""
        # IPアドレスをブロック
        self.blocked_ips.add(event.ip_address)
        
        # 管理者通知
        self.send_security_alert(event)
        
        # セッション無効化
        self.invalidate_user_sessions(event.user_id)
    
    def handle_high_security_event(self, event: SecurityEvent):
        """高セキュリティイベント処理"""
        # レート制限チェック
        if self.check_rate_limit(event.ip_address):
            self.blocked_ips.add(event.ip_address)
    
    def check_rate_limit(self, ip_address: str, limit: int = 100, window: int = 3600) -> bool:
        """レート制限チェック"""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(seconds=window)
        
        # 過去のリクエストをクリーンアップ
        if ip_address in self.rate_limits:
            self.rate_limits[ip_address] = [
                t for t in self.rate_limits[ip_address] 
                if t > cutoff_time
            ]
        else:
            self.rate_limits[ip_address] = []
        
        # 新しいリクエストを追加
        self.rate_limits[ip_address].append(current_time)
        
        # 制限チェック
        return len(self.rate_limits[ip_address]) > limit
    
    def send_security_alert(self, event: SecurityEvent):
        """セキュリティアラート送信"""
        alert = {
            'timestamp': event.timestamp.isoformat(),
            'level': event.security_level.value,
            'user_id': event.user_id,
            'ip_address': event.ip_address,
            'action': event.action,
            'resource': event.resource,
            'details': event.details
        }
        
        self.logger.warning(f"セキュリティアラート: {json.dumps(alert, ensure_ascii=False)}")
    
    def invalidate_user_sessions(self, user_id: str):
        """ユーザーセッション無効化"""
        tokens_to_remove = []
        for token, session_info in self.session_tokens.items():
            if session_info['user_id'] == user_id:
                tokens_to_remove.append(token)
        
        for token in tokens_to_remove:
            del self.session_tokens[token]
    
    def create_session_token(self, user_id: str, permissions: List[str]) -> str:
        """セッショントークン作成"""
        token = secrets.token_urlsafe(32)
        self.session_tokens[token] = {
            'user_id': user_id,
            'permissions': permissions,
            'created_at': datetime.now(),
            'last_activity': datetime.now()
        }
        return token
    
    def validate_session_token(self, token: str) -> Optional[Dict[str, Any]]:
        """セッショントークン検証"""
        if token not in self.session_tokens:
            return None
        
        session_info = self.session_tokens[token]
        session_info['last_activity'] = datetime.now()
        
        # セッション有効期限チェック（24時間）
        if datetime.now() - session_info['created_at'] > timedelta(hours=24):
            del self.session_tokens[token]
            return None
        
        return session_info
    
    def hash_password(self, password: str) -> str:
        """パスワードハッシュ化"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """パスワード検証"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def encrypt_sensitive_data(self, data: str, key: str) -> str:
        """機密データ暗号化"""
        # 簡易的な暗号化（実際の実装ではより強固な暗号化を使用）
        key_bytes = key.encode('utf-8')
        data_bytes = data.encode('utf-8')
        
        # HMAC-SHA256で暗号化
        encrypted = hmac.new(key_bytes, data_bytes, hashlib.sha256).hexdigest()
        return encrypted
    
    def get_security_report(self) -> Dict[str, Any]:
        """セキュリティレポート生成"""
        recent_events = [
            event for event in self.security_events
            if event.timestamp > datetime.now() - timedelta(hours=24)
        ]
        
        critical_events = [e for e in recent_events if e.security_level == SecurityLevel.CRITICAL]
        high_events = [e for e in recent_events if e.security_level == SecurityLevel.HIGH]
        
        return {
            'total_events_24h': len(recent_events),
            'critical_events': len(critical_events),
            'high_security_events': len(high_events),
            'blocked_ips': len(self.blocked_ips),
            'active_sessions': len(self.session_tokens),
            'active_api_keys': len(self.api_keys),
            'security_score': self.calculate_security_score(recent_events)
        }
    
    def calculate_security_score(self, events: List[SecurityEvent]) -> float:
        """セキュリティスコア計算"""
        if not events:
            return 100.0
        
        score = 100.0
        
        # 重大イベントによる減点
        critical_count = len([e for e in events if e.security_level == SecurityLevel.CRITICAL])
        score -= critical_count * 20
        
        # 高セキュリティイベントによる減点
        high_count = len([e for e in events if e.security_level == SecurityLevel.HIGH])
        score -= high_count * 10
        
        # ブロックされたIPによる減点
        score -= len(self.blocked_ips) * 5
        
        return max(0.0, score)

class AuditSystem:
    """監査システム"""
    
    def __init__(self):
        self.audit_log = []
        self.compliance_rules = {}
        self.data_retention_policy = {}
        
    def log_audit_event(self, user_id: str, action: str, resource: str, 
                       details: Dict[str, Any], compliance_category: str = None):
        """監査イベント記録"""
        audit_event = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'details': details,
            'compliance_category': compliance_category
        }
        
        self.audit_log.append(audit_event)
        
        # コンプライアンスチェック
        if compliance_category:
            self.check_compliance(audit_event)
    
    def check_compliance(self, audit_event: Dict[str, Any]):
        """コンプライアンスチェック"""
        category = audit_event['compliance_category']
        
        if category == 'data_access':
            # データアクセスコンプライアンス
            self.verify_data_access_compliance(audit_event)
        elif category == 'privacy':
            # プライバシーコンプライアンス
            self.verify_privacy_compliance(audit_event)
        elif category == 'security':
            # セキュリティコンプライアンス
            self.verify_security_compliance(audit_event)
    
    def verify_data_access_compliance(self, audit_event: Dict[str, Any]):
        """データアクセスコンプライアンス検証"""
        # GDPR、CCPA等のコンプライアンスチェック
        pass
    
    def verify_privacy_compliance(self, audit_event: Dict[str, Any]):
        """プライバシーコンプライアンス検証"""
        # 個人情報保護法、GDPR等のチェック
        pass
    
    def verify_security_compliance(self, audit_event: Dict[str, Any]):
        """セキュリティコンプライアンス検証"""
        # ISO27001、SOC2等のセキュリティフレームワークチェック
        pass
    
    def generate_compliance_report(self) -> Dict[str, Any]:
        """コンプライアンスレポート生成"""
        recent_audit_events = [
            event for event in self.audit_log
            if datetime.fromisoformat(event['timestamp']) > datetime.now() - timedelta(days=30)
        ]
        
        compliance_summary = {
            'total_audit_events': len(recent_audit_events),
            'data_access_events': len([e for e in recent_audit_events if e.get('compliance_category') == 'data_access']),
            'privacy_events': len([e for e in recent_audit_events if e.get('compliance_category') == 'privacy']),
            'security_events': len([e for e in recent_audit_events if e.get('compliance_category') == 'security']),
            'compliance_score': self.calculate_compliance_score(recent_audit_events)
        }
        
        return compliance_summary
    
    def calculate_compliance_score(self, events: List[Dict[str, Any]]) -> float:
        """コンプライアンススコア計算"""
        if not events:
            return 100.0
        
        # コンプライアンス違反の検出
        violations = 0
        total_events = len(events)
        
        for event in events:
            # 簡易的な違反検出ロジック
            if event.get('action') in ['unauthorized_access', 'data_breach', 'privacy_violation']:
                violations += 1
        
        score = 100.0 - (violations / total_events * 100)
        return max(0.0, score)

def display_advanced_security_interface():
    """高度なセキュリティインターフェース表示"""
    st.header("🔒 高度なセキュリティ・監査システム")
    
    security_system = AdvancedSecuritySystem()
    audit_system = AuditSystem()
    
    # タブ作成
    tab1, tab2, tab3, tab4 = st.tabs(["🔐 セキュリティ監視", "📊 監査ログ", "⚙️ 設定", "📈 レポート"])
    
    with tab1:
        st.subheader("🔐 セキュリティ監視")
        
        # セキュリティレポート
        security_report = security_system.get_security_report()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("セキュリティスコア", f"{security_report['security_score']:.1f}/100")
        
        with col2:
            st.metric("24時間イベント", security_report['total_events_24h'])
        
        with col3:
            st.metric("ブロックIP数", security_report['blocked_ips'])
        
        with col4:
            st.metric("アクティブセッション", security_report['active_sessions'])
        
        # セキュリティイベント
        st.subheader("🚨 最近のセキュリティイベント")
        
        if security_system.security_events:
            recent_events = security_system.security_events[-10:]  # 最新10件
            
            for event in recent_events:
                color = "red" if event.security_level == SecurityLevel.CRITICAL else "orange"
                st.markdown(f"<span style='color:{color}'>⚠️ {event.timestamp.strftime('%H:%M:%S')} - {event.event_type} - {event.user_id}</span>", unsafe_allow_html=True)
        else:
            st.success("セキュリティイベントはありません")
    
    with tab2:
        st.subheader("📊 監査ログ")
        
        # 監査イベント表示
        if audit_system.audit_log:
            recent_audit_events = audit_system.audit_log[-20:]  # 最新20件
            
            for event in recent_audit_events:
                with st.expander(f"📝 {event['timestamp'][:19]} - {event['action']} by {event['user_id']}"):
                    st.write(f"**リソース:** {event['resource']}")
                    st.write(f"**カテゴリ:** {event.get('compliance_category', 'N/A')}")
                    st.json(event['details'])
        else:
            st.info("監査ログはありません")
    
    with tab3:
        st.subheader("⚙️ セキュリティ設定")
        
        # APIキー管理
        st.write("**🔑 APIキー管理**")
        
        if st.button("🔑 新しいAPIキー生成"):
            api_key = security_system.generate_api_key("test_user", ["read", "write"])
            st.success(f"APIキー生成: {api_key[:20]}...")
        
        # セッション管理
        st.write("**👤 セッション管理**")
        
        if st.button("🚫 全セッション無効化"):
            security_system.session_tokens.clear()
            st.success("全セッションが無効化されました")
    
    with tab4:
        st.subheader("📈 セキュリティ・コンプライアンスレポート")
        
        # セキュリティレポート
        security_report = security_system.get_security_report()
        compliance_report = audit_system.generate_compliance_report()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🔒 セキュリティレポート**")
            st.metric("セキュリティスコア", f"{security_report['security_score']:.1f}/100")
            st.metric("重大イベント", security_report['critical_events'])
            st.metric("高セキュリティイベント", security_report['high_security_events'])
        
        with col2:
            st.write("**📋 コンプライアンスレポート**")
            st.metric("コンプライアンススコア", f"{compliance_report['compliance_score']:.1f}/100")
            st.metric("監査イベント", compliance_report['total_audit_events'])
            st.metric("プライバシーイベント", compliance_report['privacy_events'])
        
        # 詳細レポート
        st.subheader("📊 詳細分析")
        
        if st.button("📊 詳細レポート生成"):
            st.json({
                "security": security_report,
                "compliance": compliance_report,
                "timestamp": datetime.now().isoformat()
            })

if __name__ == "__main__":
    display_advanced_security_interface() 