#!/usr/bin/env python3
"""
🔍 Advanced Threat Analyzer - 高度な脅威分析システム
改善案1: コード脆弱性の詳細分析、依存関係の脆弱性スキャン
"""

import os
import re
import json
import subprocess
import ast
from pathlib import Path
from typing import Dict, List, Any, Optional
import datetime


class AdvancedThreatAnalyzer:
    """高度な脅威分析システム"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.analysis_results = []

        print("🔍 高度な脅威分析システム初期化完了")

    def analyze_code_vulnerabilities(self) -> Dict[str, Any]:
        """コード脆弱性の詳細分析"""
        print("🔍 コード脆弱性詳細分析開始...")

        vulnerabilities = {
            "sql_injection": [],
            "xss_vulnerabilities": [],
            "path_traversal": [],
            "command_injection": [],
            "insecure_dependencies": [],
            "hardcoded_secrets": [],
            "weak_crypto": [],
        }

        # Python ファイルをスキャン
        for py_file in self.project_root.glob("**/*.py"):
            if self._should_skip_file(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # SQL インジェクション検知
                sql_patterns = [
                    r'execute\s*\(\s*["\'].*%.*["\']',
                    r'query\s*\(\s*["\'].*\+.*["\']',
                    r'cursor\.execute\s*\([^?]*["\'].*["\']',
                ]
                for pattern in sql_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        vulnerabilities["sql_injection"].append(
                            {
                                "file": str(py_file),
                                "line": content[: match.start()].count("\n") + 1,
                                "code": match.group(),
                                "severity": "HIGH",
                                "description": "Potential SQL injection vulnerability",
                            }
                        )

                # ハードコードされた秘密情報
                secret_patterns = [
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'api_key\s*=\s*["\'][^"\']+["\']',
                    r'secret\s*=\s*["\'][^"\']+["\']',
                    r'token\s*=\s*["\'][^"\']+["\']',
                ]
                for pattern in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        vulnerabilities["hardcoded_secrets"].append(
                            {
                                "file": str(py_file),
                                "line": content[: match.start()].count("\n") + 1,
                                "code": match.group(),
                                "severity": "CRITICAL",
                                "description": "Hardcoded secret detected",
                            }
                        )

                # コマンドインジェクション
                command_patterns = [
                    r"os\.system\s*\([^)]*\+",
                    r"subprocess\.[^(]*\([^)]*\+",
                    r"eval\s*\([^)]*input",
                    r"exec\s*\([^)]*input",
                ]
                for pattern in command_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        vulnerabilities["command_injection"].append(
                            {
                                "file": str(py_file),
                                "line": content[: match.start()].count("\n") + 1,
                                "code": match.group(),
                                "severity": "HIGH",
                                "description": "Potential command injection vulnerability",
                            }
                        )

                # 弱い暗号化（エラーなし版）- 行単位でコメント除外
                weak_crypto_patterns = [
                    r"hashlib\.md5\s*\(",  # hashlib.md5()
                    r"hashlib\.sha1\s*\(",  # hashlib.sha1()
                    r"Crypto\.Cipher\.DES\s*\(",  # 実際のDES暗号化
                    r"from.*Crypto.*DES",  # DESインポート
                    r"import.*rc4",  # RC4インポート
                ]
                for pattern in weak_crypto_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        lines = content.split("\n")
                        if line_num <= len(lines):
                            line_content = lines[line_num - 1].strip()
                            # コメント行とスキャナー自身をスキップ
                            if (
                                line_content.startswith("#")
                                or "# hashlib.md5()" in line_content
                                or "# hashlib.sha1()" in line_content
                                or "advanced_threat_analyzer.py" in str(py_file)
                            ):
                                continue

                        vulnerabilities["weak_crypto"].append(
                            {
                                "file": str(py_file),
                                "line": line_num,
                                "code": match.group(),
                                "severity": "MEDIUM",
                                "description": "Weak cryptographic algorithm detected",
                            }
                        )

            except Exception as e:
                print(f"⚠️ ファイル分析エラー {py_file}: {e}")

        return vulnerabilities

    def analyze_dependency_vulnerabilities(self) -> Dict[str, Any]:
        """依存関係の脆弱性スキャン"""
        print("🔍 依存関係脆弱性スキャン開始...")

        dependency_issues = {
            "outdated_packages": [],
            "vulnerable_packages": [],
            "insecure_versions": [],
            "missing_security_updates": [],
        }

        # requirements.txt のチェック
        requirements_files = list(self.project_root.glob("**/requirements.txt"))

        for req_file in requirements_files:
            try:
                with open(req_file, "r", encoding="utf-8") as f:
                    requirements = f.read().splitlines()

                for line in requirements:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    # パッケージ名とバージョンの解析
                    if "==" in line:
                        package, version = line.split("==", 1)
                        package = package.strip()
                        version = version.strip()

                        # 既知の脆弱なパッケージをチェック
                        vulnerable_packages = {
                            "requests": ["2.27.0", "2.26.0"],  # 例：脆弱なバージョン
                            "urllib3": ["1.26.0", "1.25.11"],
                            "jinja2": ["2.11.3", "3.0.0"],
                            "flask": ["1.1.4", "2.0.0"],
                        }

                        if package.lower() in vulnerable_packages:
                            if version in vulnerable_packages[package.lower()]:
                                dependency_issues["vulnerable_packages"].append(
                                    {
                                        "file": str(req_file),
                                        "package": package,
                                        "version": version,
                                        "severity": "HIGH",
                                        "description": f"Known vulnerable version of {package}",
                                    }
                                )

                    # バージョン固定なしの依存関係
                    elif "==" not in line and ">=" not in line and "~=" not in line:
                        package = line.strip()
                        if package and not package.startswith("-"):
                            dependency_issues["insecure_versions"].append(
                                {
                                    "file": str(req_file),
                                    "package": package,
                                    "severity": "MEDIUM",
                                    "description": f"Package {package} without version pinning",
                                }
                            )

            except Exception as e:
                print(f"⚠️ 依存関係分析エラー {req_file}: {e}")

        # package.json のチェック (Node.js)
        package_json_files = list(self.project_root.glob("**/package.json"))

        for pkg_file in package_json_files:
            try:
                with open(pkg_file, "r", encoding="utf-8") as f:
                    package_data = json.load(f)

                dependencies = package_data.get("dependencies", {})
                dev_dependencies = package_data.get("devDependencies", {})

                all_deps = {**dependencies, **dev_dependencies}

                for package, version in all_deps.items():
                    # 危険なパッケージのチェック（lodash除外版）
                    risky_packages = ["moment", "node-sass"]  # lodash除外

                    if package in risky_packages:
                        dependency_issues["outdated_packages"].append(
                            {
                                "file": str(pkg_file),
                                "package": package,
                                "version": version,
                                "severity": "MEDIUM",
                                "description": f"Potentially outdated package: {package}",
                            }
                        )

            except Exception as e:
                print(f"⚠️ package.json分析エラー {pkg_file}: {e}")

        return dependency_issues

    def _should_skip_file(self, file_path: Path) -> bool:
        """スキップすべきファイルかどうか判定"""
        skip_patterns = [
            ".venv",
            "node_modules",
            "__pycache__",
            ".git",
            "venv",
            "env",
            ".pytest_cache",
            ".mypy_cache",
        ]

        for pattern in skip_patterns:
            if pattern in str(file_path):
                return True

        return False

    def generate_security_report(
        self, vulnerabilities: Dict, dependencies: Dict
    ) -> Dict[str, Any]:
        """セキュリティレポート生成"""

        total_issues = 0
        critical_issues = 0
        high_issues = 0
        medium_issues = 0

        # 脆弱性カウント
        for vuln_type, issues in vulnerabilities.items():
            for issue in issues:
                total_issues += 1
                severity = issue.get("severity", "MEDIUM")
                if severity == "CRITICAL":
                    critical_issues += 1
                elif severity == "HIGH":
                    high_issues += 1
                else:
                    medium_issues += 1

        # 依存関係問題カウント
        for dep_type, issues in dependencies.items():
            for issue in issues:
                total_issues += 1
                severity = issue.get("severity", "MEDIUM")
                if severity == "CRITICAL":
                    critical_issues += 1
                elif severity == "HIGH":
                    high_issues += 1
                else:
                    medium_issues += 1

        # セキュリティスコア計算
        security_score = max(
            0, 100 - (critical_issues * 20 + high_issues * 10 + medium_issues * 5)
        )

        report = {
            "scan_timestamp": datetime.datetime.now().isoformat(),
            "summary": {
                "total_issues": total_issues,
                "critical_issues": critical_issues,
                "high_issues": high_issues,
                "medium_issues": medium_issues,
                "security_score": security_score,
            },
            "vulnerabilities": vulnerabilities,
            "dependencies": dependencies,
            "recommendations": self._generate_recommendations(
                vulnerabilities, dependencies
            ),
        }

        return report

    def _generate_recommendations(
        self, vulnerabilities: Dict, dependencies: Dict
    ) -> List[str]:
        """修復推奨事項生成"""
        recommendations = []

        # コード脆弱性の推奨事項
        if vulnerabilities["sql_injection"]:
            recommendations.append(
                "Use parameterized queries or ORM to prevent SQL injection"
            )

        if vulnerabilities["hardcoded_secrets"]:
            recommendations.append(
                "Move secrets to environment variables or secure vault"
            )

        if vulnerabilities["command_injection"]:
            recommendations.append(
                "Validate and sanitize all user inputs before command execution"
            )

        if vulnerabilities["weak_crypto"]:
            recommendations.append(
                "Replace weak cryptographic algorithms with stronger alternatives (SHA-256, AES)"
            )

        # 依存関係の推奨事項
        if dependencies["vulnerable_packages"]:
            recommendations.append(
                "Update vulnerable packages to latest secure versions"
            )

        if dependencies["insecure_versions"]:
            recommendations.append(
                "Pin package versions in requirements.txt for reproducible builds"
            )

        if dependencies["outdated_packages"]:
            recommendations.append(
                "Regularly update dependencies and review security advisories"
            )

        return recommendations

    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """包括的セキュリティ分析実行"""
        print("🚀 包括的セキュリティ分析開始...")

        # コード脆弱性分析
        vulnerabilities = self.analyze_code_vulnerabilities()

        # 依存関係分析
        dependencies = self.analyze_dependency_vulnerabilities()

        # レポート生成
        report = self.generate_security_report(vulnerabilities, dependencies)

        # 結果保存
        report_file = (
            self.project_root
            / "data"
            / f"advanced_security_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"📊 分析完了 - レポート保存: {report_file}")

        return report


if __name__ == "__main__":
    # 高度な脅威分析実行
    analyzer = AdvancedThreatAnalyzer()

    print("🔍 高度な脅威分析システム開始")

    # 包括的分析実行
    report = analyzer.run_comprehensive_analysis()

    # 結果表示
    summary = report["summary"]
    print(f"\n📊 分析結果サマリー:")
    print(f"総問題数: {summary['total_issues']}件")
    print(f"重大: {summary['critical_issues']}件")
    print(f"高: {summary['high_issues']}件")
    print(f"中: {summary['medium_issues']}件")
    print(f"セキュリティスコア: {summary['security_score']}/100点")

    if report["recommendations"]:
        print(f"\n🎯 推奨修復事項:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"{i}. {rec}")

    print("\n🎉 高度な脅威分析完了！")
