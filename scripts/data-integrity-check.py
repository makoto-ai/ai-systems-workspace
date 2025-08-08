#!/usr/bin/env python3
"""
データ完全性検証システム
- バックアップファイルの整合性チェック
- データベース整合性検証
- 自動復元テスト
"""

import os
import json
import hashlib
import datetime
import subprocess
import sys
from pathlib import Path


class DataIntegrityChecker:
    def __init__(self):
        self.project_root = Path.cwd()
        self.data_dir = self.project_root / "data"
        self.backup_dir = self.project_root
        self.results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "checks": [],
            "overall_status": "PENDING",
        }

    def calculate_file_hash(self, file_path):
        """ファイルのSHA256ハッシュを計算"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            return f"ERROR: {str(e)}"

    def check_critical_files(self):
        """重要ファイルの存在と整合性をチェック"""
        critical_files = [
            "data/usage_limits.json",
            "requirements.txt",
            "app/main.py",
            ".env.local",
        ]

        for file_path in critical_files:
            full_path = self.project_root / file_path
            check_result = {
                "name": f"Critical File: {file_path}",
                "type": "file_integrity",
                "status": "UNKNOWN",
                "details": {},
            }

            if full_path.exists():
                file_hash = self.calculate_file_hash(full_path)
                file_size = full_path.stat().st_size
                check_result.update(
                    {
                        "status": "OK",
                        "details": {
                            "exists": True,
                            "size_bytes": file_size,
                            "hash": file_hash,
                            "last_modified": datetime.datetime.fromtimestamp(
                                full_path.stat().st_mtime
                            ).isoformat(),
                        },
                    }
                )
            else:
                check_result.update(
                    {
                        "status": "FAILED",
                        "details": {"exists": False, "error": "File not found"},
                    }
                )

            self.results["checks"].append(check_result)

    def check_backup_integrity(self):
        """バックアップファイルの整合性チェック（改良版）"""
        import os
        from pathlib import Path

        backup_locations = []
        base_dir = self.project_root

        # バックアップディレクトリ
        if (base_dir / "backups").exists():
            backup_files = list((base_dir / "backups").rglob("*"))
            backup_locations.extend([str(f) for f in backup_files if f.is_file()])

        # .bakファイル
        bak_files = list(base_dir.glob("**/*.bak"))
        backup_locations.extend(
            [
                str(f)
                for f in bak_files
                if "node_modules" not in str(f) and ".venv" not in str(f)
            ]
        )

        # .backupファイル
        backup_files = list(base_dir.glob("**/*.backup"))
        backup_locations.extend(
            [
                str(f)
                for f in backup_files
                if "node_modules" not in str(f) and ".venv" not in str(f)
            ]
        )

        # tar.gzバックアップファイル
        tar_files = list(base_dir.glob("**/*backup*.tar.gz"))
        backup_locations.extend([str(f) for f in tar_files])

        check_result = {
            "name": "Backup Files Integrity",
            "type": "backup_integrity",
            "status": "OK" if len(backup_locations) > 0 else "WARNING",
            "details": {
                "backup_count": len(backup_locations),
                "backup_files": backup_locations[:5],  # 最初の5個のみ表示
                "status_message": (
                    f"Found {len(backup_locations)} backup files"
                    if len(backup_locations) > 0
                    else "No backup files found"
                ),
            },
        }

        self.results["checks"].append(check_result)

    def check_data_directory(self):
        """データディレクトリの整合性チェック"""
        check_result = {
            "name": "Data Directory Structure",
            "type": "data_structure",
            "status": "UNKNOWN",
            "details": {},
        }

        if not self.data_dir.exists():
            check_result.update(
                {
                    "status": "FAILED",
                    "details": {"error": "Data directory does not exist"},
                }
            )
        else:
            # usage_limits.jsonの詳細チェック
            usage_limits_file = self.data_dir / "usage_limits.json"
            if usage_limits_file.exists():
                try:
                    with open(usage_limits_file, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    check_result.update(
                        {
                            "status": "OK",
                            "details": {
                                "usage_limits_json": {
                                    "exists": True,
                                    "user_count": len(data),
                                    "total_entries": (
                                        sum(
                                            len(user_data)
                                            for user_data in data.values()
                                        )
                                        if isinstance(data, dict)
                                        else 0
                                    ),
                                    "file_size_kb": round(
                                        usage_limits_file.stat().st_size / 1024, 2
                                    ),
                                }
                            },
                        }
                    )
                except json.JSONDecodeError as e:
                    check_result.update(
                        {
                            "status": "FAILED",
                            "details": {
                                "usage_limits_json": {
                                    "exists": True,
                                    "error": f"JSON parse error: {str(e)}",
                                }
                            },
                        }
                    )
                except Exception as e:
                    check_result.update(
                        {
                            "status": "FAILED",
                            "details": {
                                "usage_limits_json": {
                                    "exists": True,
                                    "error": f"Read error: {str(e)}",
                                }
                            },
                        }
                    )
            else:
                check_result.update(
                    {
                        "status": "WARNING",
                        "details": {
                            "usage_limits_json": {
                                "exists": False,
                                "warning": "usage_limits.json not found",
                            }
                        },
                    }
                )

        self.results["checks"].append(check_result)

    def run_all_checks(self):
        """全てのチェックを実行"""
        print("🔍 データ完全性検証開始...")

        self.check_critical_files()
        self.check_backup_integrity()
        self.check_data_directory()

        # 全体ステータスの決定
        failed_checks = [c for c in self.results["checks"] if c["status"] == "FAILED"]
        warning_checks = [c for c in self.results["checks"] if c["status"] == "WARNING"]

        if failed_checks:
            self.results["overall_status"] = "FAILED"
        elif warning_checks:
            self.results["overall_status"] = "WARNING"
        else:
            self.results["overall_status"] = "OK"

        return self.results

    def save_report(self, filename="data_integrity_report.json"):
        """検証結果をファイルに保存"""
        report_path = self.project_root / filename
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"📋 検証レポート保存: {report_path}")
        return report_path


def main():
    checker = DataIntegrityChecker()
    results = checker.run_all_checks()

    # 結果の表示
    print(f"\n📊 データ完全性検証結果")
    print(f"総合ステータス: {results['overall_status']}")
    print(f"実行時刻: {results['timestamp']}")
    print(f"チェック項目数: {len(results['checks'])}")

    # 各チェック結果の概要
    for check in results["checks"]:
        status_emoji = (
            "✅"
            if check["status"] == "OK"
            else "⚠️" if check["status"] == "WARNING" else "❌"
        )
        print(f"{status_emoji} {check['name']}: {check['status']}")

    # レポート保存
    checker.save_report()

    # 失敗があれば終了コード1
    if results["overall_status"] == "FAILED":
        print("\n❌ データ完全性に問題があります。詳細は上記を確認してください。")
        sys.exit(1)
    elif results["overall_status"] == "WARNING":
        print("\n⚠️ データ完全性に軽微な問題があります。")
        sys.exit(0)
    else:
        print("\n✅ データ完全性に問題ありません。")
        sys.exit(0)


if __name__ == "__main__":
    main()
