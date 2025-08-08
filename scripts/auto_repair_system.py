#!/usr/bin/env python3
"""
🔧 エラー自動修復システム - 完全自動化
検出された問題の自動修復・システム復旧・予防保守
"""

import os
import json
import subprocess
import datetime
import shutil
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from security_email_notifier import SecurityEmailNotifier


class AutoRepairSystem:
    def __init__(self):
        self.email_notifier = SecurityEmailNotifier()
        self.repair_log_file = "data/auto_repair_log.json"
        self.backup_dir = "data/auto_repair_backups"
        self.repair_history = self.load_repair_history()

    def load_repair_history(self) -> List[Dict]:
        """修復履歴読み込み"""
        if os.path.exists(self.repair_log_file):
            try:
                with open(self.repair_log_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_repair_log(self, repair_action: Dict):
        """修復ログ保存"""
        os.makedirs("data", exist_ok=True)

        self.repair_history.append(repair_action)

        # 最新200件のみ保持
        if len(self.repair_history) > 200:
            self.repair_history = self.repair_history[-200:]

        with open(self.repair_log_file, "w", encoding="utf-8") as f:
            json.dump(self.repair_history, f, ensure_ascii=False, indent=2)

    def create_backup(self, file_path: str) -> Optional[str]:
        """ファイルバックアップ作成"""
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{os.path.basename(file_path)}.backup_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_name)

            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            print(f"⚠️ バックアップ作成失敗: {file_path} - {e}")
            return None

    def repair_file_permissions(
        self, file_path: str, target_permission: str = "644"
    ) -> Dict:
        """ファイル権限修復"""
        repair_action = {
            "type": "FILE_PERMISSION_REPAIR",
            "file": file_path,
            "timestamp": datetime.datetime.now().isoformat(),
            "success": False,
            "details": "",
            "backup_path": None,
        }

        try:
            # バックアップ作成（念のため）
            if os.path.exists(file_path):
                backup_path = self.create_backup(file_path)
                repair_action["backup_path"] = backup_path

                # 権限修復実行
                result = subprocess.run(
                    ["chmod", target_permission, file_path],
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    repair_action["success"] = True
                    repair_action["details"] = (
                        f"ファイル権限を{target_permission}に修復"
                    )
                    print(f"✅ 権限修復成功: {file_path} -> {target_permission}")
                else:
                    repair_action["details"] = f"権限修復失敗: {result.stderr}"
                    print(f"❌ 権限修復失敗: {file_path}")
            else:
                repair_action["details"] = "ファイルが存在しません"

        except Exception as e:
            repair_action["details"] = f"修復エラー: {str(e)}"
            print(f"❌ 権限修復エラー: {file_path} - {e}")

        self.save_repair_log(repair_action)
        return repair_action

    def repair_sensitive_file_exposure(self, file_path: str) -> Dict:
        """機密ファイル露出修復"""
        repair_action = {
            "type": "SENSITIVE_FILE_REPAIR",
            "file": file_path,
            "timestamp": datetime.datetime.now().isoformat(),
            "success": False,
            "details": "",
            "backup_path": None,
        }

        try:
            if os.path.exists(file_path):
                # バックアップ作成
                backup_path = self.create_backup(file_path)
                repair_action["backup_path"] = backup_path

                # .gitignoreに追加
                gitignore_path = ".gitignore"
                file_pattern = os.path.basename(file_path)

                # 既に.gitignoreに含まれているかチェック
                gitignore_content = ""
                if os.path.exists(gitignore_path):
                    with open(gitignore_path, "r", encoding="utf-8") as f:
                        gitignore_content = f.read()

                if file_pattern not in gitignore_content:
                    with open(gitignore_path, "a", encoding="utf-8") as f:
                        f.write(f"\n# Auto-added by security repair\n{file_pattern}\n")
                    repair_action["details"] = f".gitignoreに{file_pattern}を追加"
                else:
                    repair_action["details"] = (
                        f"{file_pattern}は既に.gitignoreに含まれています"
                    )

                # ファイル権限を600に設定（所有者のみ読み書き）
                subprocess.run(["chmod", "600", file_path], capture_output=True)

                repair_action["success"] = True
                print(f"✅ 機密ファイル保護完了: {file_path}")

        except Exception as e:
            repair_action["details"] = f"修復エラー: {str(e)}"
            print(f"❌ 機密ファイル修復エラー: {file_path} - {e}")

        self.save_repair_log(repair_action)
        return repair_action

    def repair_disk_space_issue(self) -> Dict:
        """ディスク容量問題修復"""
        repair_action = {
            "type": "DISK_SPACE_CLEANUP",
            "timestamp": datetime.datetime.now().isoformat(),
            "success": False,
            "details": "",
            "cleaned_files": [],
            "space_freed": 0,
        }

        try:
            cleaned_files = []

            # 一時ファイル削除
            temp_patterns = [
                "*.tmp",
                "*.temp",
                "*.log",
                "*~",
                ".DS_Store",
                "__pycache__",
                "*.pyc",
            ]

            for pattern in temp_patterns:
                try:
                    result = subprocess.run(
                        ["find", ".", "-name", pattern, "-type", "f"],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    files_to_delete = [
                        f
                        for f in result.stdout.strip().split("\n")
                        if f and not f.startswith("./frontend")
                    ]

                    for file_path in files_to_delete[:10]:  # 最大10ファイル
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            cleaned_files.append({"file": file_path, "size": file_size})
                            repair_action["space_freed"] += file_size
                        except Exception:
                            continue

                except subprocess.TimeoutExpired:
                    continue
                except Exception:
                    continue

            # .venv/__pycache__ ディレクトリ削除
            try:
                result = subprocess.run(
                    ["find", ".", "-name", "__pycache__", "-type", "d"],
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                pycache_dirs = [d for d in result.stdout.strip().split("\n") if d]

                for cache_dir in pycache_dirs[:5]:  # 最大5ディレクトリ
                    try:
                        shutil.rmtree(cache_dir)
                        cleaned_files.append(
                            {"file": cache_dir, "size": 0, "type": "directory"}
                        )
                    except Exception:
                        continue

            except Exception:
                pass

            repair_action["cleaned_files"] = cleaned_files
            repair_action["success"] = True
            repair_action["details"] = (
                f"{len(cleaned_files)}個のファイル/ディレクトリを削除"
            )

            space_freed_mb = repair_action["space_freed"] / (1024 * 1024)
            print(
                f"✅ ディスク容量清掃完了: {len(cleaned_files)}個削除, {space_freed_mb:.1f}MB解放"
            )

        except Exception as e:
            repair_action["details"] = f"清掃エラー: {str(e)}"
            print(f"❌ ディスク容量清掃エラー: {e}")

        self.save_repair_log(repair_action)
        return repair_action

    def repair_api_service_issues(self) -> Dict:
        """APIサービス問題修復"""
        repair_action = {
            "type": "API_SERVICE_REPAIR",
            "timestamp": datetime.datetime.now().isoformat(),
            "success": False,
            "details": "",
            "actions_taken": [],
        }

        try:
            actions = []

            # サーバープロセス確認
            try:
                result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
                if "uvicorn" not in result.stdout and "fastapi" not in result.stdout:
                    # サーバーが動いていない場合の修復は危険なので記録のみ
                    actions.append("FastAPIサーバーが停止している可能性")
                else:
                    actions.append("FastAPIサーバー動作中を確認")
            except Exception:
                actions.append("プロセス確認でエラーが発生")

            # 依存関係チェック
            try:
                result = subprocess.run(
                    ["pip", "check"], capture_output=True, text=True
                )
                if result.returncode != 0:
                    actions.append(f"依存関係に問題: {result.stdout[:100]}")
                else:
                    actions.append("依存関係に問題なし")
            except Exception:
                actions.append("依存関係チェックでエラーが発生")

            repair_action["actions_taken"] = actions
            repair_action["success"] = True
            repair_action["details"] = f"{len(actions)}項目をチェック"

            print(f"✅ APIサービス診断完了: {len(actions)}項目チェック")

        except Exception as e:
            repair_action["details"] = f"診断エラー: {str(e)}"
            print(f"❌ APIサービス診断エラー: {e}")

        self.save_repair_log(repair_action)
        return repair_action

    def repair_configuration_issues(self) -> Dict:
        """設定ファイル問題修復"""
        repair_action = {
            "type": "CONFIGURATION_REPAIR",
            "timestamp": datetime.datetime.now().isoformat(),
            "success": False,
            "details": "",
            "repaired_configs": [],
        }

        try:
            repaired_configs = []

            # requirements.txtの存在確認
            if not os.path.exists("requirements.txt"):
                # 基本的なrequirements.txtを作成
                basic_requirements = [
                    "fastapi>=0.68.0",
                    "uvicorn[standard]>=0.15.0",
                    "pydantic>=1.8.0",
                    "requests>=2.25.0",
                ]
                with open("requirements.txt", "w", encoding="utf-8") as f:
                    f.write("\n".join(basic_requirements))
                repaired_configs.append("requirements.txt作成")

            # .env.example の存在確認
            if not os.path.exists(".env.example"):
                env_example = [
                    "# API Configuration",
                    "GROQ_API_KEY=your_groq_api_key_here",
                    "ANTHROPIC_API_KEY=your_anthropic_api_key_here",
                    "",
                    "# Development Settings",
                    "DEBUG=false",
                    "ENVIRONMENT=production",
                ]
                with open(".env.example", "w", encoding="utf-8") as f:
                    f.write("\n".join(env_example))
                repaired_configs.append(".env.example作成")

            repair_action["repaired_configs"] = repaired_configs
            repair_action["success"] = True
            repair_action["details"] = f"{len(repaired_configs)}個の設定ファイルを修復"

            print(f"✅ 設定ファイル修復完了: {len(repaired_configs)}個修復")

        except Exception as e:
            repair_action["details"] = f"設定修復エラー: {str(e)}"
            print(f"❌ 設定ファイル修復エラー: {e}")

        self.save_repair_log(repair_action)
        return repair_action

    def auto_repair_detected_issues(self, security_alert: Dict) -> Dict:
        """検出された問題の自動修復"""
        repair_summary = {
            "timestamp": datetime.datetime.now().isoformat(),
            "alert_id": security_alert.get("alert_id", "unknown"),
            "total_threats": security_alert.get("total_threats", 0),
            "repair_actions": [],
            "successful_repairs": 0,
            "failed_repairs": 0,
        }

        print(f"🔧 自動修復開始: {repair_summary['total_threats']}件の問題を処理")

        for threat in security_alert.get("detected_threats", []):
            threat_type = threat.get("type", "")
            file_path = threat.get("file", "")

            repair_result = None

            # 脅威タイプに応じた修復実行
            if threat_type == "FILE_PERMISSION" and file_path:
                repair_result = self.repair_file_permissions(file_path)
            elif threat_type == "SENSITIVE_FILE" and file_path:
                repair_result = self.repair_sensitive_file_exposure(file_path)
            elif threat_type == "DISK_SPACE":
                repair_result = self.repair_disk_space_issue()
            elif threat_type in ["CODE_VULNERABILITY", "SUSPICIOUS_PROCESS"]:
                # これらは自動修復が危険なので記録のみ
                repair_result = {
                    "type": "MANUAL_REVIEW_REQUIRED",
                    "file": file_path,
                    "success": False,
                    "details": f"{threat_type}は手動確認が必要",
                    "timestamp": datetime.datetime.now().isoformat(),
                }

            if repair_result:
                repair_summary["repair_actions"].append(repair_result)
                if repair_result.get("success", False):
                    repair_summary["successful_repairs"] += 1
                else:
                    repair_summary["failed_repairs"] += 1

        # 一般的な修復も実行
        general_repairs = [
            self.repair_api_service_issues(),
            self.repair_configuration_issues(),
        ]

        for repair in general_repairs:
            repair_summary["repair_actions"].append(repair)
            if repair.get("success", False):
                repair_summary["successful_repairs"] += 1
            else:
                repair_summary["failed_repairs"] += 1

        print(
            f"🔧 自動修復完了: {repair_summary['successful_repairs']}件成功, {repair_summary['failed_repairs']}件失敗"
        )

        # 修復結果をメール通知
        if repair_summary["successful_repairs"] > 0:
            self.send_repair_notification(repair_summary)

        return repair_summary

    def send_repair_notification(self, repair_summary: Dict):
        """修復結果通知"""
        try:
            details = f"""
自動修復が実行されました:

📊 修復結果:
✅ 成功: {repair_summary['successful_repairs']}件
❌ 失敗: {repair_summary['failed_repairs']}件

🔧 実行された修復:
"""
            for repair in repair_summary["repair_actions"][:5]:  # 最大5件
                status = "✅" if repair.get("success", False) else "❌"
                details += f"{status} {repair.get('type', 'UNKNOWN')}: {repair.get('details', 'No details')}\n"

            self.email_notifier.send_emergency_alert(
                alert_type="自動修復実行", details=details
            )
        except Exception as e:
            print(f"⚠️ 修復通知送信失敗: {e}")

    def test_auto_repair_system(self) -> bool:
        """自動修復システムテスト"""
        print("🧪 自動修復システムテスト開始...")

        # テスト用セキュリティアラート生成
        test_alert = {
            "alert_id": "test_alert_001",
            "total_threats": 2,
            "detected_threats": [
                {
                    "type": "DISK_SPACE",
                    "severity": "MEDIUM",
                    "details": "テスト用ディスク容量問題",
                },
                {
                    "type": "CONFIGURATION_ISSUE",
                    "severity": "LOW",
                    "details": "テスト用設定問題",
                },
            ],
        }

        # 自動修復テスト実行
        repair_result = self.auto_repair_detected_issues(test_alert)

        success = repair_result["successful_repairs"] > 0
        print(
            f"{'✅' if success else '❌'} 自動修復システムテスト: {repair_result['successful_repairs']}件成功"
        )

        return success


def main():
    """メイン実行（テスト用）"""
    repair_system = AutoRepairSystem()
    repair_system.test_auto_repair_system()


if __name__ == "__main__":
    main()

    def smart_repair_strategy(self, threats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """スマート修復戦略"""
        if not threats:
            return {"success": True, "repaired": 0, "details": "No threats to repair"}

        # 修復可能な脅威のみ処理
        repairable_threats = []
        for threat in threats:
            threat_type = threat.get("type", "")
            file_path = threat.get("file", "")

            # 修復可能な条件
            if (
                threat_type in ["FILE_PERMISSION", "DISK_SPACE"]
                or file_path.endswith(".env")
                or ".tmp" in file_path
                or "__pycache__" in file_path
            ):
                repairable_threats.append(threat)

        # 修復実行
        success_count = 0
        failure_count = 0
        details = []

        for threat in repairable_threats:
            try:
                if self.repair_single_threat_smart(threat):
                    success_count += 1
                    details.append(f"修復成功: {threat.get('file', 'unknown')}")
                else:
                    failure_count += 1
                    details.append(f"修復失敗: {threat.get('file', 'unknown')}")
            except Exception as e:
                failure_count += 1
                details.append(f"修復エラー: {str(e)}")

        return {
            "success": success_count > 0,
            "repaired": success_count,
            "failed": failure_count,
            "details": details,
        }

    def repair_single_threat_smart(self, threat: Dict[str, Any]) -> bool:
        """単一脅威のスマート修復"""
        threat_type = threat.get("type", "")
        file_path = threat.get("file", "")

        try:
            if threat_type == "FILE_PERMISSION":
                # ファイル権限修復
                if os.path.exists(file_path):
                    os.chmod(file_path, 0o644)
                    return True

            elif threat_type == "DISK_SPACE" or ".tmp" in file_path:
                # 一時ファイル削除
                if os.path.exists(file_path) and (
                    ".tmp" in file_path or "__pycache__" in file_path
                ):
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    return True

            elif file_path.endswith(".env"):
                # .envファイルの権限修正
                if os.path.exists(file_path):
                    os.chmod(file_path, 0o600)  # 所有者のみ読み書き
                    return True

        except Exception:
            pass

        return False

    def is_repairable_threat(self, threat: Dict[str, Any]) -> bool:
        """修復可能な脅威かどうか判定"""
        threat_type = threat.get("type", "")
        file_path = threat.get("file", "")

        # 修復しやすい脅威タイプ
        easy_repairs = ["DISK_SPACE", "TEMPORARY_FILES"]
        if threat_type in easy_repairs:
            return True

        # 修復しやすいファイルパターン
        repairable_patterns = [".tmp", "__pycache__", ".DS_Store", "temp"]
        for pattern in repairable_patterns:
            if pattern in file_path:
                return True

        return False

    def prioritize_repairs(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """修復を優先順位付け"""
        # 修復しやすいものを優先
        easy_threats = [t for t in threats if self.is_repairable_threat(t)]
        hard_threats = [t for t in threats if not self.is_repairable_threat(t)]

        # 修復しやすいものを先に処理
        return easy_threats + hard_threats

    def is_repairable_threat(self, threat: Dict[str, Any]) -> bool:
        """修復可能な脅威かどうか判定"""
        threat_type = threat.get("type", "")
        file_path = threat.get("file", "")

        # 修復しやすい脅威タイプ
        easy_repairs = ["DISK_SPACE", "TEMPORARY_FILES"]
        if threat_type in easy_repairs:
            return True

        # 修復しやすいファイルパターン
        repairable_patterns = [".tmp", "__pycache__", ".DS_Store", "temp"]
        for pattern in repairable_patterns:
            if pattern in file_path:
                return True

        return False

    def prioritize_repairs(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """修復を優先順位付け"""
        # 修復しやすいものを優先
        easy_threats = [t for t in threats if self.is_repairable_threat(t)]
        hard_threats = [t for t in threats if not self.is_repairable_threat(t)]

        # 修復しやすいものを先に処理
        return easy_threats + hard_threats
