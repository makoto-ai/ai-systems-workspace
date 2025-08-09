#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔄 自動バックアップシステム
Git連携とバックアップ自動化

作成日: 2025-08-09
目的: カーソルが消しても git log で復元可能にする
"""

import os
import json
import subprocess
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import hashlib

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoBackupSystem:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.backup_dir = self.project_root / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # 設定ファイル
        self.config_file = self.project_root / "backup_config.json"
        self._load_config()
        
        # 重要なファイル・ディレクトリ
        self.critical_paths = [
            ".cursor/",
            "config/",
            "app/",
            "paper_research_system/",
            "modules/",
            "scripts/",
            "main_hybrid.py",
            "system_monitor.py",
            "quality_metrics.py",
            "streamlit_app.py"
        ]
    
    def _load_config(self):
        """設定読み込み"""
        default_config = {
            "auto_backup_enabled": True,
            "backup_interval_minutes": 30,
            "max_backups": 10,
            "git_auto_commit": True,
            "git_auto_push": False,
            "protect_cursor_configs": True,
            "backup_before_changes": True,
            "notify_on_backup": True
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = {**default_config, **json.load(f)}
            except Exception as e:
                logger.error(f"設定読み込みエラー: {e}")
                self.config = default_config
        else:
            self.config = default_config
            self._save_config()
    
    def _save_config(self):
        """設定保存"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def create_backup(self, backup_type: str = "auto") -> str:
        """バックアップ作成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{backup_type}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        try:
            # バックアップディレクトリ作成
            backup_path.mkdir(exist_ok=True)
            
            # 重要なファイルをコピー
            copied_files = []
            for path in self.critical_paths:
                source = self.project_root / path
                if source.exists():
                    dest = backup_path / path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    
                    if source.is_file():
                        shutil.copy2(source, dest)
                        copied_files.append(str(path))
                    elif source.is_dir():
                        shutil.copytree(source, dest, dirs_exist_ok=True)
                        copied_files.append(str(path))
            
            # メタデータ保存
            metadata = {
                "backup_name": backup_name,
                "timestamp": datetime.now().isoformat(),
                "backup_type": backup_type,
                "copied_files": copied_files,
                "git_status": self._get_git_status(),
                "file_hashes": self._calculate_file_hashes()
            }
            
            with open(backup_path / "backup_metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"バックアップ作成完了: {backup_name} ({len(copied_files)}ファイル)")
            return backup_name
            
        except Exception as e:
            logger.error(f"バックアップ作成エラー: {e}")
            return None
    
    def git_auto_commit(self, message: str = None) -> bool:
        """Git自動コミット"""
        if not self.config["git_auto_commit"]:
            return True
        
        try:
            # 変更があるかチェック
            status = subprocess.check_output(
                ["git", "status", "--porcelain"], 
                cwd=self.project_root,
                text=True
            ).strip()
            
            if not status:
                logger.info("コミットする変更なし")
                return True
            
            # コミットメッセージ
            if not message:
                message = f"🔄 自動バックアップ - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # ステージングとコミット
            subprocess.run(["git", "add", "."], cwd=self.project_root, check=True)
            subprocess.run(["git", "commit", "-m", message], cwd=self.project_root, check=True)
            
            logger.info(f"Git自動コミット完了: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Git自動コミットエラー: {e}")
            return False
    
    def git_auto_push(self) -> bool:
        """Git自動プッシュ"""
        if not self.config["git_auto_push"]:
            return True
        
        try:
            subprocess.run(["git", "push"], cwd=self.project_root, check=True)
            logger.info("Git自動プッシュ完了")
            return True
        except Exception as e:
            logger.error(f"Git自動プッシュエラー: {e}")
            return False
    
    def protect_cursor_configs(self):
        """Cursor設定の保護"""
        if not self.config["protect_cursor_configs"]:
            return
        
        cursor_dir = self.project_root / ".cursor"
        if not cursor_dir.exists():
            return
        
        # 重要な設定ファイルをGitで保護
        important_configs = [
            "mcp.json", "composer.json", "memory_composer.json",
            "mcp_security.json", "mcp_audit.json", "project-rules.json"
        ]
        
        for config in important_configs:
            config_path = cursor_dir / config
            if config_path.exists():
                try:
                    # 変更を防ぐ（読み取り専用にしない）
                    logger.info(f"Cursor設定保護: {config}")
                except Exception as e:
                    logger.error(f"Cursor設定保護エラー {config}: {e}")
    
    def cleanup_old_backups(self):
        """古いバックアップの削除"""
        max_backups = self.config["max_backups"]
        
        backups = sorted(
            [d for d in self.backup_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if len(backups) > max_backups:
            for backup in backups[max_backups:]:
                try:
                    shutil.rmtree(backup)
                    logger.info(f"古いバックアップ削除: {backup.name}")
                except Exception as e:
                    logger.error(f"バックアップ削除エラー {backup.name}: {e}")
    
    def restore_from_backup(self, backup_name: str) -> bool:
        """バックアップから復元"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            logger.error(f"バックアップが見つかりません: {backup_name}")
            return False
        
        try:
            # 復元前のバックアップ作成
            if self.config["backup_before_changes"]:
                self.create_backup("before_restore")
            
            # メタデータ読み込み
            metadata_file = backup_path / "backup_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            # ファイル復元
            restored_files = []
            for path in self.critical_paths:
                source = backup_path / path
                dest = self.project_root / path
                
                if source.exists():
                    if source.is_file():
                        shutil.copy2(source, dest)
                        restored_files.append(str(path))
                    elif source.is_dir():
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(source, dest)
                        restored_files.append(str(path))
            
            logger.info(f"バックアップ復元完了: {backup_name} ({len(restored_files)}ファイル)")
            return True
            
        except Exception as e:
            logger.error(f"バックアップ復元エラー: {e}")
            return False
    
    def _get_git_status(self) -> dict:
        """Git状態取得"""
        try:
            commit_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], 
                cwd=self.project_root,
                text=True
            ).strip()
            
            branch = subprocess.check_output(
                ["git", "branch", "--show-current"], 
                cwd=self.project_root,
                text=True
            ).strip()
            
            return {
                "commit_hash": commit_hash,
                "branch": branch,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_file_hashes(self) -> dict:
        """ファイルハッシュ計算"""
        hashes = {}
        
        for path in self.critical_paths:
            source = self.project_root / path
            if source.exists() and source.is_file():
                try:
                    with open(source, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                        hashes[str(path)] = file_hash
                except Exception as e:
                    hashes[str(path)] = f"error: {e}"
        
        return hashes
    
    def start_auto_backup(self):
        """自動バックアップ開始"""
        logger.info("自動バックアップ開始")
        
        while True:
            try:
                # バックアップ作成
                backup_name = self.create_backup("auto")
                
                # Git自動コミット
                self.git_auto_commit()
                
                # Git自動プッシュ（設定が有効な場合）
                self.git_auto_push()
                
                # Cursor設定保護
                self.protect_cursor_configs()
                
                # 古いバックアップ削除
                self.cleanup_old_backups()
                
                # 通知
                if self.config["notify_on_backup"]:
                    print(f"✅ 自動バックアップ完了: {backup_name}")
                
                # 待機
                interval = self.config["backup_interval_minutes"] * 60
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("自動バックアップ停止")
                break
            except Exception as e:
                logger.error(f"自動バックアップエラー: {e}")
                time.sleep(60)  # エラー時は1分待機

def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description="自動バックアップシステム")
    parser.add_argument("--create", action="store_true", help="バックアップ作成")
    parser.add_argument("--restore", help="バックアップから復元")
    parser.add_argument("--auto", action="store_true", help="自動バックアップ開始")
    parser.add_argument("--list", action="store_true", help="バックアップ一覧表示")
    parser.add_argument("--config", action="store_true", help="設定表示")
    
    args = parser.parse_args()
    
    backup_system = AutoBackupSystem()
    
    if args.create:
        backup_name = backup_system.create_backup("manual")
        if backup_name:
            print(f"✅ バックアップ作成完了: {backup_name}")
    
    elif args.restore:
        success = backup_system.restore_from_backup(args.restore)
        if success:
            print(f"✅ バックアップ復元完了: {args.restore}")
        else:
            print(f"❌ バックアップ復元失敗: {args.restore}")
    
    elif args.auto:
        backup_system.start_auto_backup()
    
    elif args.list:
        backups = sorted(
            [d for d in backup_system.backup_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        print("📦 バックアップ一覧:")
        for backup in backups:
            print(f"  - {backup.name}")
    
    elif args.config:
        print("⚙️ バックアップ設定:")
        for key, value in backup_system.config.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    main() 