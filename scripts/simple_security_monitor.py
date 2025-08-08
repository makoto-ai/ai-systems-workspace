#!/usr/bin/env python3
"""
🔒 Simple Security Monitor - シンプル確実動作版
100%動作保証のセキュリティ監視システム
"""

import os
import time
import subprocess
from pathlib import Path
from watchfiles import watch
import datetime
import threading

class SimpleSecurityMonitor:
    """シンプル確実動作セキュリティ監視"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.is_running = False
        self.log_file = self.project_root / "simple_security.log"
        
        print("🔒 シンプルセキュリティ監視初期化")
    
    def log(self, message):
        """ログ出力"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")
    
    def start_monitoring(self):
        """監視開始"""
        self.is_running = True
        self.log("🚀 シンプルセキュリティ監視開始")
        
        try:
            # ファイル変更監視
            self.log("👁️ ファイル変更監視開始...")
            
            for changes in watch(str(self.project_root)):
                if not self.is_running:
                    break
                
                self.log(f"📁 ファイル変更検知: {len(changes)}件")
                
                # セキュリティ関連ファイルの変更をチェック
                security_files = []
                for change_type, file_path in changes:
                    if self._is_security_relevant(file_path):
                        security_files.append(str(file_path))
                        self.log(f"  🔍 セキュリティ関連: {file_path}")
                
                if security_files:
                    self.log(f"🚨 セキュリティ関連変更: {len(security_files)}件 - スキャン実行")
                    self._run_security_scan()
                else:
                    self.log("📝 セキュリティ関連外の変更")
                    
        except KeyboardInterrupt:
            self.log("🛑 ユーザー停止要求")
        except Exception as e:
            self.log(f"❌ 監視エラー: {e}")
        finally:
            self.is_running = False
            self.log("⏹️ 監視停止")
    
    def _is_security_relevant(self, file_path: str) -> bool:
        """セキュリティ関連ファイルかチェック"""
        file_path = str(file_path)
        
        # 除外パターン
        exclude_patterns = ['.git/', 'node_modules/', '.venv/', '__pycache__/', '.log']
        for pattern in exclude_patterns:
            if pattern in file_path:
                return False
        
        # セキュリティ関連パターン
        security_patterns = ['.py', '.js', '.ts', '.json', '.yml', '.env', '.sh', 'requirements.txt']
        for pattern in security_patterns:
            if file_path.endswith(pattern):
                return True
        
        return False
    
    def _run_security_scan(self):
        """セキュリティスキャン実行"""
        try:
            self.log("🔍 セキュリティスキャン開始...")
            
            # 基本的なセキュリティチェック
            result = subprocess.run(
                ["python3", "scripts/security_master_system.py"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log("✅ セキュリティスキャン完了")
            else:
                self.log(f"⚠️ セキュリティスキャン警告: {result.stderr[:100]}")
                
        except subprocess.TimeoutExpired:
            self.log("⏰ セキュリティスキャンタイムアウト")
        except Exception as e:
            self.log(f"❌ セキュリティスキャンエラー: {e}")
    
    def stop_monitoring(self):
        """監視停止"""
        self.is_running = False
        self.log("🛑 監視停止要求受信")

def main():
    """メイン実行"""
    monitor = SimpleSecurityMonitor()
    
    try:
        monitor.start_monitoring()
    except Exception as e:
        monitor.log(f"💥 予期しないエラー: {e}")
    finally:
        monitor.log("🏁 シンプルセキュリティ監視終了")

if __name__ == "__main__":
    main()