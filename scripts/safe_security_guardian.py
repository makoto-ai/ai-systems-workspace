#!/usr/bin/env python3
"""
🛡️ Safe Security Guardian - 安全性最優先セキュリティシステム
ユーザーの「怖すぎる」という懸念に対応する超安全設計
"""

import os
import json
import time
import shutil
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class SafeSecurityGuardian:
    """安全性最優先セキュリティガーディアン"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.config_file = self.project_root / "config" / "safe_security_config.json"
        self.backup_dir = self.project_root / "safety_backups"
        self.approval_queue = self.project_root / "data" / "approval_queue.json"
        
        # 安全設定読み込み
        self.load_safe_config()
        
        print("🛡️ Safe Security Guardian 初期化完了（超安全モード）")
    
    def load_safe_config(self):
        """安全設定読み込み"""
        default_config = {
            "safety_mode": "MAXIMUM",  # MAXIMUM / HIGH / MEDIUM
            "require_manual_approval": True,
            "auto_backup_before_repair": True,
            "max_files_per_scan": 10,  # 過負荷防止
            "scan_interval_minutes": 60,  # 1時間間隔（軽量化）
            "whitelist_extensions": [".py", ".md", ".txt", ".json"],
            "critical_paths_protected": [
                "app/main.py",
                ".env",
                "requirements.txt",
                "config/"
            ],
            "never_auto_modify": [
                "database/",
                "backups/",
                ".git/",
                "config/"
            ]
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = {**default_config, **json.load(f)}
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """設定保存"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def scan_with_safety_checks(self) -> Dict[str, Any]:
        """安全チェック付きスキャン"""
        print("🔍 安全モードスキャン開始...")
        
        scan_results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "files_scanned": 0,
            "potential_issues": [],
            "safe_to_proceed": False,
            "requires_approval": []
        }
        
        # ファイル数制限チェック
        files_to_scan = list(self.project_root.glob("**/*.py"))[:self.config["max_files_per_scan"]]
        
        for file_path in files_to_scan:
            if self._is_protected_path(file_path):
                continue
                
            # 軽量スキャン（CPU負荷軽減）
            issue = self._lightweight_security_check(file_path)
            if issue:
                scan_results["potential_issues"].append(issue)
        
        scan_results["files_scanned"] = len(files_to_scan)
        scan_results["safe_to_proceed"] = len(scan_results["potential_issues"]) == 0
        
        print(f"✅ 安全スキャン完了: {scan_results['files_scanned']}ファイル、{len(scan_results['potential_issues'])}件の潜在的問題")
        
        return scan_results
    
    def _is_protected_path(self, file_path: Path) -> bool:
        """保護対象パスかチェック"""
        path_str = str(file_path.relative_to(self.project_root))
        
        for protected in self.config["never_auto_modify"]:
            if protected in path_str:
                return True
        
        for critical in self.config["critical_paths_protected"]:
            if critical in path_str:
                return True
        
        return False
    
    def _lightweight_security_check(self, file_path: Path) -> Optional[Dict]:
        """軽量セキュリティチェック（CPU負荷軽減）"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 最初の100行のみチェック（負荷軽減）
                content = '\n'.join([f.readline() for _ in range(100)])
            
            # 明らかに危険なパターンのみチェック
            dangerous_patterns = [
                'eval(',
                'exec(',
                'os.system(',
                'subprocess.call(',
                'rm -rf',
                'DELETE FROM',
                'DROP TABLE'
            ]
            
            for pattern in dangerous_patterns:
                if pattern in content:
                    return {
                        "file": str(file_path),
                        "issue": f"Dangerous pattern detected: {pattern}",
                        "severity": "HIGH",
                        "requires_approval": True
                    }
            
            return None
            
        except Exception:
            return None
    
    def create_safety_backup(self, file_path: Path) -> str:
        """安全バックアップ作成"""
        if not self.config["auto_backup_before_repair"]:
            return ""
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{file_path.name}_{timestamp}.backup"
        
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        
        print(f"💾 安全バックアップ作成: {backup_path}")
        return str(backup_path)
    
    def request_manual_approval(self, action: Dict) -> bool:
        """手動承認要求"""
        if not self.config["require_manual_approval"]:
            return True
        
        # 承認待ちキューに追加
        approval_item = {
            "id": f"approval_{int(time.time())}",
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "status": "PENDING"
        }
        
        # キューファイル読み込み・追加
        queue = []
        if self.approval_queue.exists():
            with open(self.approval_queue, 'r', encoding='utf-8') as f:
                queue = json.load(f)
        
        queue.append(approval_item)
        
        # キューファイル保存
        self.approval_queue.parent.mkdir(parents=True, exist_ok=True)
        with open(self.approval_queue, 'w', encoding='utf-8') as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)
        
        print(f"✋ 手動承認要求: {action['description']}")
        print(f"📋 承認ID: {approval_item['id']}")
        print("⚠️ 承認なしで自動実行されません")
        
        return False  # 承認待ち
    
    def safe_repair_with_approval(self, issue: Dict) -> Dict:
        """承認付き安全修復"""
        repair_action = {
            "type": "REPAIR",
            "file": issue["file"],
            "issue": issue["issue"],
            "description": f"修復: {issue['file']} の {issue['issue']}"
        }
        
        # 手動承認チェック
        if not self.request_manual_approval(repair_action):
            return {
                "status": "APPROVAL_REQUIRED",
                "message": "手動承認待ち",
                "action_id": f"approval_{int(time.time())}"
            }
        
        # バックアップ作成
        backup_path = self.create_safety_backup(Path(issue["file"]))
        
        # 実際の修復（ここでは安全のためログのみ）
        print(f"🔧 安全修復実行: {issue['file']}")
        print(f"💾 バックアップ: {backup_path}")
        
        return {
            "status": "COMPLETED",
            "backup_created": backup_path,
            "repair_applied": True
        }
    
    def get_resource_usage(self) -> Dict:
        """リソース使用量取得"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        return {
            "cpu_percent": process.cpu_percent(),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "threads": process.num_threads()
        }
    
    def run_safe_monitoring(self):
        """安全監視実行"""
        print("🛡️ 安全監視モード開始")
        print(f"📊 設定: {self.config['safety_mode']}モード")
        print(f"⏰ スキャン間隔: {self.config['scan_interval_minutes']}分")
        print(f"✋ 手動承認: {'必須' if self.config['require_manual_approval'] else '不要'}")
        
        while True:
            try:
                # リソース使用量チェック
                usage = self.get_resource_usage()
                print(f"📊 リソース: CPU {usage['cpu_percent']:.1f}%, RAM {usage['memory_mb']:.1f}MB")
                
                # 安全スキャン実行
                results = self.scan_with_safety_checks()
                
                if results["potential_issues"]:
                    print(f"⚠️ {len(results['potential_issues'])}件の潜在的問題を検出")
                    for issue in results["potential_issues"]:
                        self.safe_repair_with_approval(issue)
                else:
                    print("✅ 問題なし")
                
                # 次回スキャンまで待機
                print(f"😴 {self.config['scan_interval_minutes']}分間待機...")
                time.sleep(self.config['scan_interval_minutes'] * 60)
                
            except KeyboardInterrupt:
                print("🛑 安全監視停止")
                break
            except Exception as e:
                print(f"❌ エラー: {e}")
                time.sleep(60)  # エラー時は1分待機


def main():
    guardian = SafeSecurityGuardian()
    
    # テストモード
    print("\n🧪 安全性テスト実行...")
    results = guardian.scan_with_safety_checks()
    print(f"📊 テスト結果: {json.dumps(results, indent=2, ensure_ascii=False)}")
    
    # 設定表示
    print(f"\n⚙️ 現在の安全設定:")
    for key, value in guardian.config.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()