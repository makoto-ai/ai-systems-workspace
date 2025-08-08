#!/usr/bin/env python3
"""
Enhanced Backup System
自動バックアップ機能の強化
"""

import os
import shutil
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

class EnhancedBackup:
    """強化されたバックアップシステム"""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = backup_dir
        self.setup_logging()
        self.ensure_backup_dir()
        
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('backup_system.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def ensure_backup_dir(self):
        """バックアップディレクトリ作成"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            self.logger.info(f"バックアップディレクトリ作成: {self.backup_dir}")
    
    def calculate_file_hash(self, file_path: str) -> str:
        """ファイルハッシュ計算"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self.logger.error(f"ハッシュ計算エラー {file_path}: {e}")
            return ""
    
    def get_backup_targets(self) -> List[str]:
        """バックアップ対象ファイル取得"""
        targets = [
            "streamlit_app.py",
            "quality_metrics.py",
            "modules/",
            "scripts/",
            "requirements.txt",
            "config/",
            "data/"
        ]
        
        valid_targets = []
        for target in targets:
            if os.path.exists(target):
                valid_targets.append(target)
            else:
                self.logger.warning(f"バックアップ対象が見つかりません: {target}")
                
        return valid_targets
    
    def create_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """バックアップ作成"""
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
        
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            os.makedirs(backup_path, exist_ok=True)
            
            targets = self.get_backup_targets()
            backup_info = {
                'timestamp': datetime.now().isoformat(),
                'backup_name': backup_name,
                'files': [],
                'total_size': 0
            }
            
            for target in targets:
                if os.path.isfile(target):
                    # ファイルのコピー
                    dest_path = os.path.join(backup_path, target)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.copy2(target, dest_path)
                    
                    file_hash = self.calculate_file_hash(target)
                    file_size = os.path.getsize(target)
                    
                    backup_info['files'].append({
                        'path': target,
                        'hash': file_hash,
                        'size': file_size
                    })
                    backup_info['total_size'] += file_size
                    
                elif os.path.isdir(target):
                    # ディレクトリのコピー
                    dest_path = os.path.join(backup_path, target)
                    shutil.copytree(target, dest_path, dirs_exist_ok=True)
                    
                    # ディレクトリ内ファイルの情報収集
                    for root, dirs, files in os.walk(target):
                        for file in files:
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, '.')
                            
                            file_hash = self.calculate_file_hash(file_path)
                            file_size = os.path.getsize(file_path)
                            
                            backup_info['files'].append({
                                'path': rel_path,
                                'hash': file_hash,
                                'size': file_size
                            })
                            backup_info['total_size'] += file_size
            
            # バックアップ情報を保存
            info_path = os.path.join(backup_path, 'backup_info.json')
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"バックアップ完了: {backup_name} ({len(backup_info['files'])}ファイル)")
            return backup_info
            
        except Exception as e:
            self.logger.error(f"バックアップエラー: {e}")
            return {}
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """バックアップ一覧取得"""
        backups = []
        
        if not os.path.exists(self.backup_dir):
            return backups
        
        for item in os.listdir(self.backup_dir):
            backup_path = os.path.join(self.backup_dir, item)
            info_path = os.path.join(backup_path, 'backup_info.json')
            
            if os.path.isdir(backup_path) and os.path.exists(info_path):
                try:
                    with open(info_path, 'r', encoding='utf-8') as f:
                        backup_info = json.load(f)
                        backups.append(backup_info)
                except Exception as e:
                    self.logger.error(f"バックアップ情報読み込みエラー {item}: {e}")
        
        return sorted(backups, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    def restore_backup(self, backup_name: str, target_dir: str = ".") -> bool:
        """バックアップ復元"""
        backup_path = os.path.join(self.backup_dir, backup_name)
        info_path = os.path.join(backup_path, 'backup_info.json')
        
        if not os.path.exists(info_path):
            self.logger.error(f"バックアップが見つかりません: {backup_name}")
            return False
        
        try:
            with open(info_path, 'r', encoding='utf-8') as f:
                backup_info = json.load(f)
            
            # 復元実行
            for file_info in backup_info.get('files', []):
                source_path = os.path.join(backup_path, file_info['path'])
                dest_path = os.path.join(target_dir, file_info['path'])
                
                if os.path.exists(source_path):
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.copy2(source_path, dest_path)
                    
                    # ハッシュ検証
                    restored_hash = self.calculate_file_hash(dest_path)
                    if restored_hash != file_info['hash']:
                        self.logger.warning(f"ハッシュ不一致: {file_info['path']}")
            
            self.logger.info(f"復元完了: {backup_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"復元エラー: {e}")
            return False
    
    def cleanup_old_backups(self, keep_days: int = 7):
        """古いバックアップ削除"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        backups = self.list_backups()
        for backup in backups:
            backup_date = datetime.fromisoformat(backup['timestamp'])
            if backup_date < cutoff_date:
                backup_name = backup['backup_name']
                backup_path = os.path.join(self.backup_dir, backup_name)
                
                try:
                    shutil.rmtree(backup_path)
                    self.logger.info(f"古いバックアップ削除: {backup_name}")
                except Exception as e:
                    self.logger.error(f"バックアップ削除エラー {backup_name}: {e}")

def auto_backup():
    """自動バックアップ実行"""
    backup_system = EnhancedBackup()
    backup_info = backup_system.create_backup()
    
    if backup_info:
        print(f"自動バックアップ完了: {backup_info['backup_name']}")
        print(f"ファイル数: {len(backup_info['files'])}")
        print(f"総サイズ: {backup_info['total_size'] / 1024 / 1024:.2f} MB")
    
    # 古いバックアップをクリーンアップ
    backup_system.cleanup_old_backups()

if __name__ == "__main__":
    auto_backup() 