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
from datetime import datetime
from pathlib import Path
import shutil
import hashlib
import tarfile
import fcntl
from typing import Dict, List

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
        
        # 重要なファイル・ディレクトリ（クリティカルバックアップ対象）
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
        
        # ロックファイル
        self.lock_file = self.project_root / ".auto_backup.lock"

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
            "notify_on_backup": True,
            "full_backup": False,
            "full_backup_excludes": [
                ".git",
                "backups",
                "venv",
                "node_modules",
                "__pycache__",
                ".DS_Store",
                "*.log"
            ],
            "package_tar_gz": True,
            "remote_sync_dir": ""
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
    
    def _acquire_lock(self):
        self.lock_fp = open(self.lock_file, 'w')
        try:
            fcntl.flock(self.lock_fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            logger.warning("バックアップは既に実行中のためスキップ")
            return False
    
    def _release_lock(self):
        try:
            fcntl.flock(self.lock_fp.fileno(), fcntl.LOCK_UN)
            self.lock_fp.close()
            self.lock_file.unlink(missing_ok=True)
        except Exception:
            pass

    def create_backup(self, mode: str = "critical") -> str:
        """バックアップ作成
        mode: "critical" | "full"
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{mode}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        if not self._acquire_lock():
            return ""
        
        try:
            # バックアップディレクトリ作成
            backup_path.mkdir(exist_ok=True)
            
            if mode == "full":
                self._copy_full_project(backup_path)
            else:
                # 重要なファイルをコピー
                self._copy_critical_paths(backup_path)
            
            # メタデータ保存
            metadata = self._generate_metadata(backup_name, mode)
            with open(backup_path / "backup_metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # パッケージ化
            if self.config.get("package_tar_gz", True):
                self._package_backup(backup_path)
            
            # 外部同期
            self._sync_remote(backup_path)
            
            logger.info(f"バックアップ作成完了: {backup_name} ({metadata.get('files_count', 0)}ファイル)")
            return backup_name
            
        except Exception as e:
            logger.error(f"バックアップ作成エラー: {e}")
            return ""
        finally:
            self._release_lock()
    
    def _copy_critical_paths(self, backup_path: Path):
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
        return copied_files
    
    def _copy_full_project(self, backup_path: Path):
        excludes = set(self.config.get("full_backup_excludes", []))
        
        def _should_exclude(rel: str) -> bool:
            # 簡易パターン除外
            for pat in excludes:
                if pat.startswith("*.") and rel.endswith(pat[1:]):
                    return True
                if rel == pat or rel.startswith(pat + "/"):
                    return True
            return False
        
        files_copied = 0
        for root, dirs, files in os.walk(self.project_root):
            rel_root = os.path.relpath(root, self.project_root)
            if rel_root == ".":
                rel_root = ""
            if rel_root and _should_exclude(rel_root):
                dirs[:] = []
                continue
            # ディレクトリ除外
            dirs[:] = [d for d in dirs if not _should_exclude(os.path.join(rel_root, d))]
            
            for fname in files:
                rel_path = os.path.join(rel_root, fname) if rel_root else fname
                if _should_exclude(rel_path):
                    continue
                src = self.project_root / rel_path
                dst = backup_path / rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                files_copied += 1
        return files_copied

    def _generate_metadata(self, backup_name: str, mode: str) -> Dict[str, any]:
        file_hashes = self._calculate_file_hashes()
        files_count = 0
        for root, _, files in os.walk(self.backup_dir / backup_name):
            files_count += len(files)
        return {
            "backup_name": backup_name,
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "git_status": self._get_git_status(),
            "file_hashes": file_hashes,
            "files_count": files_count
        }

    def verify_backup(self, backup_name: str) -> bool:
        """バックアップ整合性検証（重要ファイルの存在とハッシュ一致、.pyファイル数等）"""
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            logger.error(f"バックアップが見つかりません: {backup_name}")
            return False
        
        # 重要ファイルのMD5比較
        metadata_file = backup_path / "backup_metadata.json"
        if not metadata_file.exists():
            logger.error("メタデータがありません")
            return False
        metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
        hashes = metadata.get("file_hashes", {})
        ok = True
        for rel, md5 in hashes.items():
            src = self.project_root / rel
            dst = backup_path / rel
            if not dst.exists():
                logger.error(f"バックアップに不足: {rel}")
                ok = False
                continue
            if src.exists() and src.is_file():
                cur_md5 = self._md5_file(src)
                if cur_md5 != md5:
                    logger.warning(f"MD5差異: {rel} (live:{cur_md5} != backup:{md5})")
        
        # .pyファイル数検証（ライブ vs バックアップ）
        live_py = self._count_py(self.project_root)
        backup_py = self._count_py(backup_path)
        logger.info(f".py count live={live_py}, backup={backup_py}")
        
        return ok

    def _package_backup(self, backup_path: Path) -> Path:
        tar_path = backup_path.with_suffix(".tar.gz")
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(backup_path, arcname=backup_path.name)
        logger.info(f"バックアップをパッケージ化: {tar_path.name}")
        return tar_path

    def _sync_remote(self, backup_path: Path):
        remote_dir = os.getenv("REMOTE_BACKUP_DIR", self.config.get("remote_sync_dir", "").strip())
        # 環境変数/チルダ展開
        if remote_dir:
            remote_dir = os.path.expanduser(os.path.expandvars(remote_dir))
        if not remote_dir:
            # iCloudがあれば既定同期
            icloud = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/AI-Backups"
            if icloud.exists():
                remote_dir = str(icloud)
        if not remote_dir:
            return
        
        dest = Path(remote_dir) / backup_path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            if backup_path.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(backup_path, dest)
            else:
                shutil.copy2(backup_path, dest)
            logger.info(f"リモート同期完了: {dest}")
        except Exception as e:
            logger.warning(f"リモート同期失敗: {e}")

    def git_auto_commit(self, message: str = None) -> bool:
        """Git自動コミット"""
        if not self.config["git_auto_commit"]:
            return True
        
        try:
            status = subprocess.check_output(
                ["git", "status", "--porcelain"], 
                cwd=self.project_root,
                text=True
            ).strip()
            if not status:
                logger.info("コミットする変更なし")
                return True
            if not message:
                message = f"🔄 自動バックアップ - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
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
        """Cursor設定の保護（ダミー・ログのみ）"""
        if not self.config["protect_cursor_configs"]:
            return
        cursor_dir = self.project_root / ".cursor"
        if not cursor_dir.exists():
            return
        important_configs = [
            "mcp.json", "composer.json", "memory_composer.json",
            "mcp_security.json", "mcp_audit.json", "project-rules.json"
        ]
        for config in important_configs:
            if (cursor_dir / config).exists():
                logger.info(f"Cursor設定保護: {config}")
    
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
        """バックアップから復元（上書き注意）"""
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            logger.error(f"バックアップが見つかりません: {backup_name}")
            return False
        try:
            if self.config["backup_before_changes"]:
                self.create_backup("critical")
            restored_files = 0
            for root, dirs, files in os.walk(backup_path):
                rel_root = os.path.relpath(root, backup_path)
                for fname in files:
                    src = Path(root) / fname
                    rel = os.path.join(rel_root, fname) if rel_root != "." else fname
                    dst = self.project_root / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    restored_files += 1
            logger.info(f"バックアップ復元完了: {backup_name} ({restored_files}ファイル)")
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
    
    def _calculate_file_hashes(self) -> Dict[str, str]:
        """重要ファイルのハッシュ計算"""
        hashes: Dict[str, str] = {}
        for path in self.critical_paths:
            src = self.project_root / path
            if src.exists() and src.is_file():
                hashes[path] = self._md5_file(src)
        return hashes

    def _md5_file(self, p: Path) -> str:
        h = hashlib.md5()
        with open(p, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _count_py(self, base: Path) -> int:
        count = 0
        for root, _, files in os.walk(base):
            count += sum(1 for f in files if f.endswith('.py'))
        return count

    def start_auto_backup(self):
        """自動バックアップ開始"""
        logger.info("自動バックアップ開始")
        while True:
            try:
                mode = "full" if self.config.get("full_backup") else "critical"
                backup_name = self.create_backup(mode)
                self.git_auto_commit()
                self.git_auto_push()
                self.protect_cursor_configs()
                self.cleanup_old_backups()
                if self.config["notify_on_backup"] and backup_name:
                    print(f"✅ 自動バックアップ完了: {backup_name}")
                interval = self.config["backup_interval_minutes"] * 60
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("自動バックアップ停止")
                break
            except Exception as e:
                logger.error(f"自動バックアップエラー: {e}")
                time.sleep(60)

def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description="自動バックアップシステム")
    parser.add_argument("--create", action="store_true", help="バックアップ作成(クリティカル)})")
    parser.add_argument("--full", action="store_true", help="フルバックアップ作成")
    parser.add_argument("--verify", help="バックアップ整合性検証: --verify <backup_name>")
    parser.add_argument("--restore", help="バックアップから復元")
    parser.add_argument("--auto", action="store_true", help="自動バックアップ開始")
    parser.add_argument("--list", action="store_true", help="バックアップ一覧表示")
    parser.add_argument("--config", action="store_true", help="設定表示")
    
    args = parser.parse_args()
    backup_system = AutoBackupSystem()
    
    if args.create:
        backup_name = backup_system.create_backup("critical")
        if backup_name:
            print(f"✅ バックアップ作成完了: {backup_name}")
    
    elif args.full:
        backup_name = backup_system.create_backup("full")
        if backup_name:
            print(f"✅ フルバックアップ作成完了: {backup_name}")
    
    elif args.verify:
        ok = backup_system.verify_backup(args.verify)
        print("✅ 整合性OK" if ok else "❌ 整合性NG")
    
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