#!/usr/bin/env python3
"""
🔒 Security Full Automation System - 完全自動化セキュリティシステム
プロジェクト全体を24/7監視し、新システム自動検知・保護
"""

import os
import time
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from watchfiles import watch
import json
import datetime

class SecurityFullAutomation:
    """完全自動化セキュリティシステム"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.is_running = False
        self.monitoring_threads = []
        
        # 監視対象パターン
        self.watch_patterns = [
            "**/*.py",      # Python ファイル
            "**/*.js",      # JavaScript ファイル  
            "**/*.ts",      # TypeScript ファイル
            "**/*.json",    # 設定ファイル
            "**/*.yml",     # YAML ファイル
            "**/*.yaml",    # YAML ファイル
            "**/*.env*",    # 環境変数ファイル
            "**/*.sh",      # シェルスクリプト
            "**/requirements.txt",  # 依存関係
            "**/package.json",      # Node.js 依存関係
        ]
        
        # 除外パターン  
        self.exclude_patterns = [
            ".git/**",
            "node_modules/**", 
            ".venv/**",
            "__pycache__/**",
            "*.pyc",
            ".pytest_cache/**",
            "frontend/**/node_modules/**",
        ]
        
        # 自動実行間隔
        self.intervals = {
            "file_scan": 30,        # ファイル変更30秒後スキャン
            "full_scan": 3600,      # 1時間毎フルスキャン
            "learning": 1800,       # 30分毎学習更新
            "health_check": 300,    # 5分毎ヘルスチェック
        }
        
        print("🔒 完全自動化セキュリティシステム初期化完了")
    
    def start_full_automation(self):
        """完全自動化開始"""
        print("🚀 完全自動化セキュリティシステム開始...")
        
        self.is_running = True
        
        # 1. ファイル監視スレッド
        file_monitor_thread = threading.Thread(
            target=self._file_change_monitor,
            daemon=True
        )
        file_monitor_thread.start()
        self.monitoring_threads.append(file_monitor_thread)
        
        # 2. 定期フルスキャンスレッド
        full_scan_thread = threading.Thread(
            target=self._periodic_full_scan,
            daemon=True
        )
        full_scan_thread.start()
        self.monitoring_threads.append(full_scan_thread)
        
        # 3. 学習エンジンスレッド
        learning_thread = threading.Thread(
            target=self._periodic_learning,
            daemon=True
        )
        learning_thread.start()
        self.monitoring_threads.append(learning_thread)
        
        # 4. ヘルスチェックスレッド
        health_thread = threading.Thread(
            target=self._periodic_health_check,
            daemon=True
        )
        health_thread.start()
        self.monitoring_threads.append(health_thread)
        
        print("✅ 4つの監視スレッド開始完了")
        print("🛡️ プロジェクト全体の24/7セキュリティ監視開始")
        
        return True
    
    def _file_change_monitor(self):
        """ファイル変更リアルタイム監視"""
        print("👁️ ファイル変更監視開始...")
        
        retry_count = 0
        max_retries = 3
        
        while self.is_running and retry_count < max_retries:
            try:
                print(f"📂 監視対象: {self.project_root}")
                print(f"🚫 除外パターン: {len(self.exclude_patterns)}個")
                
                # watchfilesによる監視開始（正しい使用方法）
                for changes in watch(str(self.project_root)):
                    if not self.is_running:
                        print("🛑 監視停止要求")
                        break
                    
                    print(f"📁 ファイル変更検知: {len(changes)}件")
                    
                    # 変更されたファイルの分析
                    changed_files = []
                    for change_type, file_path in changes:
                        if self._should_scan_file(file_path):
                            changed_files.append(str(file_path))
                            print(f"  📄 対象ファイル: {file_path}")
                    
                    if changed_files:
                        print(f"🔍 セキュリティスキャン対象: {len(changed_files)}ファイル")
                        
                        # 30秒待機してから自動スキャン
                        print(f"⏳ {self.intervals['file_scan']}秒待機後にスキャン実行...")
                        time.sleep(self.intervals["file_scan"])
                        
                        if self.is_running:
                            self._auto_security_scan(changed_files)
                    else:
                        print("📝 スキャン対象外の変更")
                
            except Exception as e:
                retry_count += 1
                print(f"⚠️ ファイル監視エラー (試行{retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    print(f"🔄 5秒後に監視再開...")
                    time.sleep(5)
                else:
                    print("❌ ファイル監視の最大試行回数に達しました")
                    break
    
    def _periodic_full_scan(self):
        """定期フルスキャン"""
        print("🔄 定期フルスキャン開始...")
        
        while self.is_running:
            try:
                print("🔍 1時間毎フルセキュリティスキャン実行中...")
                
                # 高度脅威分析実行
                self._run_advanced_threat_analyzer()
                
                print("✅ 定期フルスキャン完了")
                
                # 1時間待機
                time.sleep(self.intervals["full_scan"])
                
            except Exception as e:
                print(f"⚠️ 定期スキャンエラー: {e}")
                time.sleep(300)  # エラー時5分待機
    
    def _periodic_learning(self):
        """定期学習・予測更新"""
        print("🧠 定期学習エンジン開始...")
        
        while self.is_running:
            try:
                print("🧠 30分毎学習・予測エンジン実行中...")
                
                # 学習・予測エンジン実行
                self._run_learning_prediction_engine()
                
                print("✅ 学習・予測更新完了")
                
                # 30分待機
                time.sleep(self.intervals["learning"])
                
            except Exception as e:
                print(f"⚠️ 学習エンジンエラー: {e}")
                time.sleep(300)  # エラー時5分待機
    
    def _periodic_health_check(self):
        """定期ヘルスチェック"""
        print("❤️ 定期ヘルスチェック開始...")
        
        while self.is_running:
            try:
                # システム全体ヘルスチェック
                health_status = self._check_system_health()
                
                if health_status["status"] != "healthy":
                    print(f"⚠️ システム問題検知: {health_status['issues']}")
                    # 自動修復試行
                    self._auto_repair_attempt()
                
                # 5分待機
                time.sleep(self.intervals["health_check"])
                
            except Exception as e:
                print(f"⚠️ ヘルスチェックエラー: {e}")
                time.sleep(60)  # エラー時1分待機
    
    def _should_scan_file(self, file_path: str) -> bool:
        """ファイルをスキャンすべきかチェック"""
        file_path = str(file_path)
        
        # 除外パターンチェック（より厳密）
        exclude_dirs = ['.git', 'node_modules', '.venv', '__pycache__', '.pytest_cache', 'frontend/voice-roleplay-frontend/node_modules']
        exclude_extensions = ['.pyc', '.log', '.tmp']
        
        for exclude_dir in exclude_dirs:
            if exclude_dir in file_path:
                return False
        
        for exclude_ext in exclude_extensions:
            if file_path.endswith(exclude_ext):
                return False
        
        # スキャン対象パターンチェック（より明確）
        target_extensions = ['.py', '.js', '.ts', '.json', '.yml', '.yaml', '.sh']
        target_files = ['requirements.txt', 'package.json', '.env']
        
        # 拡張子チェック
        for ext in target_extensions:
            if file_path.endswith(ext):
                return True
        
        # 特定ファイル名チェック
        for filename in target_files:
            if filename in file_path:
                return True
        
        return False
    
    def _auto_security_scan(self, files: List[str]):
        """自動セキュリティスキャン"""
        try:
            print(f"🔍 自動セキュリティスキャン開始: {len(files)}ファイル")
            
            # セキュリティマスターシステム実行
            result = subprocess.run(
                ["python3", "scripts/security_master_system.py"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                print("✅ 自動セキュリティスキャン完了")
                
                # 問題が検出された場合の通知
                if "脅威" in result.stdout or "WARNING" in result.stdout:
                    print("⚠️ セキュリティ問題検出 - 自動修復を試行")
                    self._auto_repair_attempt()
                    
            else:
                print(f"❌ セキュリティスキャンエラー: {result.stderr}")
                
        except Exception as e:
            print(f"⚠️ 自動スキャンエラー: {e}")
    
    def _run_advanced_threat_analyzer(self):
        """高度脅威分析実行"""
        try:
            result = subprocess.run(
                ["python3", "scripts/advanced_threat_analyzer.py"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                print("✅ 高度脅威分析完了")
            else:
                print(f"❌ 高度脅威分析エラー: {result.stderr}")
                
        except Exception as e:
            print(f"⚠️ 高度脅威分析エラー: {e}")
    
    def _run_learning_prediction_engine(self):
        """学習・予測エンジン実行"""
        try:
            result = subprocess.run(
                ["python3", "scripts/learning_prediction_engine.py"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                print("✅ 学習・予測エンジン完了")
            else:
                print(f"❌ 学習・予測エンジンエラー: {result.stderr}")
                
        except Exception as e:
            print(f"⚠️ 学習・予測エンジンエラー: {e}")
    
    def _check_system_health(self) -> Dict[str, Any]:
        """システムヘルスチェック"""
        health_status = {
            "status": "healthy",
            "issues": [],
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        try:
            # ディスク容量チェック
            disk_usage = os.statvfs(self.project_root)
            free_space_gb = (disk_usage.f_bavail * disk_usage.f_frsize) / (1024**3)
            
            if free_space_gb < 1.0:  # 1GB未満
                health_status["status"] = "warning"
                health_status["issues"].append(f"ディスク容量不足: {free_space_gb:.1f}GB")
            
            # 重要ファイル存在チェック
            critical_files = [
                "scripts/security_master_system.py",
                "scripts/advanced_threat_analyzer.py", 
                "scripts/learning_prediction_engine.py"
            ]
            
            for file_path in critical_files:
                if not (self.project_root / file_path).exists():
                    health_status["status"] = "critical"
                    health_status["issues"].append(f"重要ファイル不在: {file_path}")
            
        except Exception as e:
            health_status["status"] = "error"
            health_status["issues"].append(f"ヘルスチェックエラー: {e}")
        
        return health_status
    
    def _auto_repair_attempt(self):
        """自動修復試行"""
        try:
            print("🔧 自動修復試行中...")
            
            # 自動修復システム実行
            result = subprocess.run(
                ["python3", "scripts/auto_repair_system.py"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                print("✅ 自動修復完了")
            else:
                print(f"❌ 自動修復エラー: {result.stderr}")
                
        except Exception as e:
            print(f"⚠️ 自動修復エラー: {e}")
    
    def stop_automation(self):
        """自動化停止"""
        print("⏹️ 完全自動化停止中...")
        self.is_running = False
        
        # 全スレッド終了待機
        for thread in self.monitoring_threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        print("✅ 完全自動化停止完了")
    
    def get_status(self) -> Dict[str, Any]:
        """システム状態取得"""
        return {
            "is_running": self.is_running,
            "active_threads": len([t for t in self.monitoring_threads if t.is_alive()]),
            "project_root": str(self.project_root),
            "intervals": self.intervals,
            "watch_patterns": self.watch_patterns,
            "exclude_patterns": self.exclude_patterns
        }

def run_in_background():
    """バックグラウンド実行"""
    automation = SecurityFullAutomation()
    
    try:
        automation.start_full_automation()
        
        # メインループ（無限実行）
        while automation.is_running:
            time.sleep(60)  # 1分毎状態確認
            
    except KeyboardInterrupt:
        print("\n🛑 ユーザー停止要求")
        automation.stop_automation()
    except Exception as e:
        print(f"💥 システムエラー: {e}")
        automation.stop_automation()

if __name__ == "__main__":
    print("🔒 完全自動化セキュリティシステム")
    print("=" * 50)
    
    automation = SecurityFullAutomation()
    
    print("🎯 システム設定:")
    status = automation.get_status()
    for key, value in status.items():
        if isinstance(value, list):
            print(f"  {key}: {len(value)}項目")
        else:
            print(f"  {key}: {value}")
    
    print("\n🚀 完全自動化開始...")
    run_in_background()