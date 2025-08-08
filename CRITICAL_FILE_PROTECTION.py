#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ 重要ファイル完全保護システム
絶対に重要ファイルを削除させない安全システム

作成日: 2025-08-02
目的: ユーザーの重要ファイルを完全保護
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Set, Dict, Any
import json
import hashlib

class CriticalFileProtector:
    """重要ファイル完全保護システム"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or "/Users/araimakoto/ai-driven/ai-systems-workspace")
        self.protection_config_file = self.project_root / "PROTECTION_CONFIG.json"
        self.backup_dir = self.project_root / ".critical_backups"
        self.log_file = self.project_root / "protection_system.log"
        
        # 初期化
        self._load_or_create_config()
        self._ensure_backup_directory()
        
    def _load_or_create_config(self):
        """保護設定をロードまたは作成"""
        default_config = {
            "critical_files": [
                # Python実行ファイル
                "**/*.py",
                "**main*.py",
                "**/*fact_check*.py",
                "**/*manuscript*.py",
                "**/settings.py",
                "**/config.py",
                
                # データベース
                "**/*.db",
                "**/*.sqlite",
                "**/*.sql",
                
                # 設定ファイル
                "**/*.json",
                "**/*.yaml",
                "**/*.yml",
                "**/*.toml",
                "**/*.ini",
                
                # ドキュメント
                "**/*.md",
                "**/*.txt",
                
                # 依存関係
                "**/requirements*.txt",
                "**/package*.json",
                "**/Dockerfile",
                "**/docker-compose*.yml",
                
                # スクリプト
                "**/*.sh",
                "**/*.bash",
                
                # Git設定
                "**/.git/**",
                "**/.gitignore",
                
                # 仮想環境（重要）
                "**/.venv/**",
                "**/venv/**",
                
                # Obsidian
                "**/obsidian-knowledge/**",
                "**/.obsidian/**"
            ],
            "allowed_deletions": [
                # 一時ファイル（削除OK）
                "**/__pycache__/**",
                "**/*.pyc",
                "**/*.pyo",
                "**/.DS_Store",
                "**/Thumbs.db",
                "**/*.tmp",
                "**/*.temp",
                "**/*.bak",
                "**/*.backup",
                "**/*.log",
                "**/node_modules/**",
                "**/.pytest_cache/**",
                "**/*.egg-info/**"
            ],
            "protection_enabled": True,
            "backup_before_any_operation": True,
            "require_confirmation": True,
            "log_all_operations": True
        }
        
        if self.protection_config_file.exists():
            with open(self.protection_config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                # 新しい設定項目を追加
                for key, value in default_config.items():
                    if key not in self.config:
                        self.config[key] = value
        else:
            self.config = default_config
            
        self._save_config()
    
    def _save_config(self):
        """設定を保存"""
        with open(self.protection_config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _ensure_backup_directory(self):
        """バックアップディレクトリを確保"""
        self.backup_dir.mkdir(exist_ok=True)
        
    def _log(self, message: str, level: str = "INFO"):
        """ログ記録"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(f"🛡️ [{level}] {message}")
    
    def _is_critical_file(self, file_path: Path) -> bool:
        """ファイルが重要かどうかチェック"""
        if not self.config["protection_enabled"]:
            return False
        
        # 絶対パスに変換
        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path
            
        try:
            relative_path = file_path.relative_to(self.project_root)
        except ValueError:
            # プロジェクトルート外のファイルは相対パスとして扱う
            relative_path = file_path
        
        for pattern in self.config["critical_files"]:
            if relative_path.match(pattern):
                return True
        return False
    
    def _is_allowed_deletion(self, file_path: Path) -> bool:
        """削除が許可されているファイルかチェック"""
        # 絶対パスに変換
        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path
            
        try:
            relative_path = file_path.relative_to(self.project_root)
        except ValueError:
            # プロジェクトルート外のファイルは相対パスとして扱う
            relative_path = file_path
        
        for pattern in self.config["allowed_deletions"]:
            if relative_path.match(pattern):
                return True
        return False
    
    def _create_backup(self, target_path: Path) -> Path:
        """ファイル/ディレクトリのバックアップを作成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{target_path.name}_{timestamp}.backup"
        backup_path = self.backup_dir / backup_name
        
        if target_path.is_file():
            shutil.copy2(target_path, backup_path)
        elif target_path.is_dir():
            shutil.copytree(target_path, backup_path)
        
        self._log(f"バックアップ作成: {target_path} → {backup_path}")
        return backup_path
    
    def check_operation_safety(self, operation: str, target_paths: List[str]) -> Dict[str, Any]:
        """操作の安全性をチェック"""
        if not self.config["protection_enabled"]:
            return {"safe": True, "message": "保護無効"}
        
        results = {
            "safe": True,
            "blocked_files": [],
            "allowed_files": [],
            "warnings": [],
            "backups_created": []
        }
        
        for path_str in target_paths:
            path = Path(path_str)
            
            if not path.exists():
                continue
                
            # ディレクトリの場合は再帰チェック
            if path.is_dir():
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        self._check_single_file(file_path, results, operation)
            else:
                self._check_single_file(path, results, operation)
        
        return results
    
    def _check_single_file(self, file_path: Path, results: Dict, operation: str):
        """単一ファイルの安全性チェック"""
        if self._is_critical_file(file_path) and not self._is_allowed_deletion(file_path):
            results["safe"] = False
            results["blocked_files"].append(str(file_path))
            self._log(f"🚫 BLOCKED: {operation} on critical file: {file_path}", "WARNING")
        elif self._is_allowed_deletion(file_path):
            results["allowed_files"].append(str(file_path))
            
            # バックアップ作成（重要でない場合でも）
            if self.config["backup_before_any_operation"]:
                backup_path = self._create_backup(file_path)
                results["backups_created"].append(str(backup_path))
    
    def safe_delete(self, target_paths: List[str], force: bool = False) -> bool:
        """安全な削除実行"""
        self._log(f"安全削除要求: {target_paths}")
        
        # 安全性チェック
        safety_check = self.check_operation_safety("DELETE", target_paths)
        
        if not safety_check["safe"] and not force:
            self._log("🚫 削除ブロック: 重要ファイルが含まれています", "ERROR")
            print("🚫 削除がブロックされました！")
            print("重要ファイル:")
            for blocked in safety_check["blocked_files"]:
                print(f"  - {blocked}")
            return False
        
        # 確認要求
        if self.config["require_confirmation"] and not force:
            print("\n⚠️ 削除確認:")
            print(f"削除対象: {len(target_paths)}個")
            if safety_check["allowed_files"]:
                print("削除許可ファイル:")
                for allowed in safety_check["allowed_files"][:5]:  # 最初の5個のみ表示
                    print(f"  - {allowed}")
                if len(safety_check["allowed_files"]) > 5:
                    print(f"  ... 他{len(safety_check['allowed_files']) - 5}個")
            
            confirm = input("\n本当に削除しますか？ (yes/no): ")
            if confirm.lower() != "yes":
                self._log("ユーザーが削除をキャンセル")
                return False
        
        # 実際の削除実行
        deleted_count = 0
        for path_str in target_paths:
            path = Path(path_str)
            if path.exists() and str(path) in safety_check["allowed_files"]:
                try:
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        shutil.rmtree(path)
                    deleted_count += 1
                    self._log(f"削除完了: {path}")
                except Exception as e:
                    self._log(f"削除エラー: {path} - {e}", "ERROR")
        
        self._log(f"削除完了: {deleted_count}個のファイル/ディレクトリ")
        return True
    
    def emergency_restore(self, target_name: str = None) -> bool:
        """緊急復旧"""
        if not self.backup_dir.exists():
            self._log("バックアップディレクトリが存在しません", "ERROR")
            return False
        
        backups = list(self.backup_dir.glob("*.backup"))
        if not backups:
            self._log("復旧可能なバックアップがありません", "ERROR")
            return False
        
        # 最新のバックアップを表示
        print("\n🔄 利用可能なバックアップ:")
        for i, backup in enumerate(sorted(backups, reverse=True)[:10]):
            print(f"  {i+1}. {backup.name}")
        
        if target_name:
            # 特定ファイルの復旧
            matching_backups = [b for b in backups if target_name in b.name]
            if matching_backups:
                latest_backup = sorted(matching_backups, reverse=True)[0]
                self._restore_backup(latest_backup)
                return True
        
        return False
    
    def _restore_backup(self, backup_path: Path):
        """バックアップからの復旧"""
        # バックアップ名から元のパスを推定
        original_name = backup_path.name.split('_')[0]
        restore_path = self.project_root / original_name
        
        try:
            if backup_path.is_file():
                shutil.copy2(backup_path, restore_path)
            elif backup_path.is_dir():
                shutil.copytree(backup_path, restore_path)
            
            self._log(f"復旧完了: {backup_path} → {restore_path}")
            print(f"✅ 復旧完了: {restore_path}")
        except Exception as e:
            self._log(f"復旧エラー: {e}", "ERROR")
    
    def status_report(self) -> str:
        """保護システムの状態レポート"""
        report = f"""
🛡️ ファイル保護システム状態レポート
=====================================

📊 基本設定:
- 保護有効: {'✅ YES' if self.config['protection_enabled'] else '❌ NO'}
- 操作前バックアップ: {'✅ YES' if self.config['backup_before_any_operation'] else '❌ NO'}
- 確認要求: {'✅ YES' if self.config['require_confirmation'] else '❌ NO'}

📁 保護対象:
- 重要ファイルパターン: {len(self.config['critical_files'])}個
- 削除許可パターン: {len(self.config['allowed_deletions'])}個

💾 バックアップ:
- バックアップディレクトリ: {self.backup_dir}
- 利用可能バックアップ: {len(list(self.backup_dir.glob('*.backup')))}個

📋 ログファイル: {self.log_file}
🔧 設定ファイル: {self.protection_config_file}
"""
        return report

# グローバル保護インスタンス
protector = CriticalFileProtector()

def safe_rm(*args):
    """安全なrmコマンド代替"""
    return protector.safe_delete(list(args))

def emergency_restore(target=None):
    """緊急復旧関数"""
    return protector.emergency_restore(target)

def protection_status():
    """保護状態確認"""
    print(protector.status_report())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "status":
            protection_status()
        elif command == "restore":
            target = sys.argv[2] if len(sys.argv) > 2 else None
            emergency_restore(target)
        elif command == "safe-rm":
            safe_rm(*sys.argv[2:])
        else:
            print("使用法: python CRITICAL_FILE_PROTECTION.py [status|restore|safe-rm] [args...]")
    else:
        protection_status()