#!/usr/bin/env python3
"""
AI Systems セキュリティスキャンスクリプト
包括的なセキュリティチェックと脆弱性分析
"""

import os
import sys
import json
import logging
import subprocess
import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityScanner:
    def __init__(self):
        self.scan_results = {
            "vulnerabilities": [],
            "security_issues": [],
            "compliance_checks": [],
            "recommendations": []
        }
        self.services = [
            "ai-systems-app:8000",
            "mcp-service:8001", 
            "composer-service:8002",
            "vault:8200",
            "grafana:3000",
            "prometheus:9090"
        ]
    
    def scan_dependencies(self) -> Dict[str, Any]:
        """依存関係のセキュリティスキャン"""
        logger.info("依存関係セキュリティスキャン開始")
        
        results = {
            "python_packages": [],
            "node_packages": [],
            "docker_images": [],
            "system_packages": []
        }
        
        try:
            # Python依存関係スキャン
            if os.path.exists("requirements.txt"):
                logger.info("Python依存関係をスキャン中...")
                try:
                    # bandit セキュリティスキャン
                    result = subprocess.run([
                        "bandit", "-r", ".", "-f", "json"
                    ], capture_output=True, text=True, timeout=300)
                    
                    if result.returncode == 0:
                        bandit_results = json.loads(result.stdout)
                        results["python_packages"] = bandit_results
                        logger.info(f"Banditスキャン完了: {len(bandit_results.get('results', []))} 件")
                    else:
                        logger.warning("Banditスキャン失敗")
                        
                except Exception as e:
                    logger.error(f"Python依存関係スキャンエラー: {e}")
            
            # Node.js依存関係スキャン
            if os.path.exists("package.json"):
                logger.info("Node.js依存関係をスキャン中...")
                try:
                    # npm audit
                    result = subprocess.run([
                        "npm", "audit", "--json"
                    ], capture_output=True, text=True, timeout=300)
                    
                    if result.returncode == 0:
                        npm_results = json.loads(result.stdout)
                        results["node_packages"] = npm_results
                        logger.info("npm audit完了")
                    else:
                        logger.warning("npm audit失敗")
                        
                except Exception as e:
                    logger.error(f"Node.js依存関係スキャンエラー: {e}")
            
            # Dockerイメージスキャン
            logger.info("Dockerイメージをスキャン中...")
            try:
                # Trivy スキャン
                result = subprocess.run([
                    "trivy", "image", "--format", "json", "ai-systems-hybrid-app:latest"
                ], capture_output=True, text=True, timeout=600)
                
                if result.returncode == 0:
                    trivy_results = json.loads(result.stdout)
                    results["docker_images"] = trivy_results
                    logger.info("Trivyスキャン完了")
                else:
                    logger.warning("Trivyスキャン失敗")
                    
            except Exception as e:
                logger.error(f"Dockerイメージスキャンエラー: {e}")
            
        except Exception as e:
            logger.error(f"依存関係スキャンエラー: {e}")
        
        return results
    
    async def scan_network_security(self) -> Dict[str, Any]:
        """ネットワークセキュリティスキャン"""
        logger.info("ネットワークセキュリティスキャン開始")
        
        results = {
            "open_ports": [],
            "ssl_certificates": [],
            "firewall_rules": [],
            "network_vulnerabilities": []
        }
        
        try:
            # ポートスキャン
            for service in self.services:
                host, port = service.split(":")
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"http://{host}:{port}/health", timeout=5.0)
                        results["open_ports"].append({
                            "service": service,
                            "status": "open",
                            "response_code": response.status_code
                        })
                except Exception as e:
                    results["open_ports"].append({
                        "service": service,
                        "status": "closed",
                        "error": str(e)
                    })
            
            # SSL証明書チェック
            ssl_services = ["grafana:3000", "prometheus:9090"]
            for service in ssl_services:
                host, port = service.split(":")
                try:
                    result = subprocess.run([
                        "openssl", "s_client", "-connect", f"{host}:{port}", "-servername", host
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        results["ssl_certificates"].append({
                            "service": service,
                            "status": "valid",
                            "details": result.stdout
                        })
                    else:
                        results["ssl_certificates"].append({
                            "service": service,
                            "status": "invalid",
                            "error": result.stderr
                        })
                except Exception as e:
                    results["ssl_certificates"].append({
                        "service": service,
                        "status": "error",
                        "error": str(e)
                    })
                    
        except Exception as e:
            logger.error(f"ネットワークセキュリティスキャンエラー: {e}")
        
        return results
    
    def scan_file_permissions(self) -> Dict[str, Any]:
        """ファイル権限スキャン"""
        logger.info("ファイル権限スキャン開始")
        
        results = {
            "sensitive_files": [],
            "permission_issues": [],
            "world_writable_files": []
        }
        
        sensitive_patterns = [
            "*.key", "*.pem", "*.crt", "*.p12", "*.pfx",
            "*.env", "*.secret", "*.password", "*.token",
            "config.json", "secrets.json", "vault.json"
        ]
        
        try:
            # 機密ファイル検索
            for pattern in sensitive_patterns:
                for file_path in Path(".").rglob(pattern):
                    try:
                        stat = file_path.stat()
                        results["sensitive_files"].append({
                            "file": str(file_path),
                            "permissions": oct(stat.st_mode)[-3:],
                            "owner": stat.st_uid,
                            "group": stat.st_gid
                        })
                    except Exception as e:
                        logger.error(f"ファイル権限取得エラー: {e}")
            
            # 世界書き込み可能ファイル検索
            for file_path in Path(".").rglob("*"):
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        if stat.st_mode & 0o002:  # 世界書き込み可能
                            results["world_writable_files"].append({
                                "file": str(file_path),
                                "permissions": oct(stat.st_mode)[-3:]
                            })
                    except Exception as e:
                        pass
            
        except Exception as e:
            logger.error(f"ファイル権限スキャンエラー: {e}")
        
        return results
    
    def scan_code_security(self) -> Dict[str, Any]:
        """コードセキュリティスキャン"""
        logger.info("コードセキュリティスキャン開始")
        
        results = {
            "hardcoded_secrets": [],
            "sql_injection": [],
            "xss_vulnerabilities": [],
            "insecure_deserialization": [],
            "security_misconfigurations": []
        }
        
        try:
            # ハードコードされたシークレット検索
            secret_patterns = [
                r"password\s*=\s*['\"][^'\"]+['\"]",
                r"api_key\s*=\s*['\"][^'\"]+['\"]",
                r"secret\s*=\s*['\"][^'\"]+['\"]",
                r"token\s*=\s*['\"][^'\"]+['\"]",
                r"key\s*=\s*['\"][^'\"]+['\"]"
            ]
            
            for file_path in Path(".").rglob("*.py"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for pattern in secret_patterns:
                            import re
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches:
                                results["hardcoded_secrets"].append({
                                    "file": str(file_path),
                                    "pattern": pattern,
                                    "matches": len(matches)
                                })
                except Exception as e:
                    logger.error(f"ファイル読み込みエラー: {e}")
            
            # SQLインジェクション検索
            sql_patterns = [
                r"execute\s*\(\s*[^)]*\+\s*[^)]*\)",
                r"query\s*=\s*[^=]*\+\s*[^=]*",
                r"f\"SELECT.*{.*}\"",
                r"f\"INSERT.*{.*}\"",
                r"f\"UPDATE.*{.*}\"",
                r"f\"DELETE.*{.*}\""
            ]
            
            for file_path in Path(".").rglob("*.py"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for pattern in sql_patterns:
                            import re
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches:
                                results["sql_injection"].append({
                                    "file": str(file_path),
                                    "pattern": pattern,
                                    "matches": len(matches)
                                })
                except Exception as e:
                    logger.error(f"ファイル読み込みエラー: {e}")
                    
        except Exception as e:
            logger.error(f"コードセキュリティスキャンエラー: {e}")
        
        return results
    
    def scan_configuration_security(self) -> Dict[str, Any]:
        """設定セキュリティスキャン"""
        logger.info("設定セキュリティスキャン開始")
        
        results = {
            "environment_variables": [],
            "database_config": [],
            "api_config": [],
            "logging_config": [],
            "cors_config": []
        }
        
        try:
            # 環境変数チェック
            env_files = [".env", "env.hybrid.example", ".env.local"]
            for env_file in env_files:
                if os.path.exists(env_file):
                    try:
                        with open(env_file, 'r') as f:
                            content = f.read()
                            # 機密情報が平文で含まれていないかチェック
                            if "password" in content.lower() or "secret" in content.lower():
                                results["environment_variables"].append({
                                    "file": env_file,
                                    "issue": "機密情報が含まれている可能性",
                                    "severity": "high"
                                })
                    except Exception as e:
                        logger.error(f"環境変数ファイル読み込みエラー: {e}")
            
            # データベース設定チェック
            db_config_files = ["docker-compose.hybrid.yml", "database/init/*.sql"]
            for config_file in db_config_files:
                if os.path.exists(config_file):
                    try:
                        with open(config_file, 'r') as f:
                            content = f.read()
                            if "password" in content.lower():
                                results["database_config"].append({
                                    "file": config_file,
                                    "issue": "データベースパスワードが平文",
                                    "severity": "high"
                                })
                    except Exception as e:
                        logger.error(f"データベース設定ファイル読み込みエラー: {e}")
            
            # API設定チェック
            api_config_files = ["main_hybrid.py", "mcp_service.py", "composer_service.py"]
            for config_file in api_config_files:
                if os.path.exists(config_file):
                    try:
                        with open(config_file, 'r') as f:
                            content = f.read()
                            if "cors" in content.lower():
                                results["cors_config"].append({
                                    "file": config_file,
                                    "status": "CORS設定あり"
                                })
                    except Exception as e:
                        logger.error(f"API設定ファイル読み込みエラー: {e}")
                        
        except Exception as e:
            logger.error(f"設定セキュリティスキャンエラー: {e}")
        
        return results
    
    def generate_security_report(self, all_results: Dict[str, Any]):
        """セキュリティレポート生成"""
        logger.info("セキュリティレポート生成開始")
        
        # 脆弱性の集計
        vulnerabilities = []
        security_issues = []
        
        # 依存関係の脆弱性
        if "dependencies" in all_results:
            deps_results = all_results["dependencies"]
            if deps_results.get("python_packages"):
                for result in deps_results["python_packages"].get("results", []):
                    if result.get("issue_severity") in ["HIGH", "MEDIUM"]:
                        vulnerabilities.append({
                            "type": "python_package",
                            "severity": result.get("issue_severity"),
                            "description": result.get("issue_text"),
                            "location": result.get("filename")
                        })
        
        # ネットワークセキュリティ問題
        if "network" in all_results:
            net_results = all_results["network"]
            for port_info in net_results.get("open_ports", []):
                if port_info.get("status") == "open":
                    security_issues.append({
                        "type": "open_port",
                        "severity": "medium",
                        "description": f"ポート {port_info['service']} が開放されています",
                        "service": port_info["service"]
                    })
        
        # ファイル権限問題
        if "file_permissions" in all_results:
            file_results = all_results["file_permissions"]
            for file_info in file_results.get("world_writable_files", []):
                security_issues.append({
                    "type": "world_writable_file",
                    "severity": "high",
                    "description": f"世界書き込み可能ファイル: {file_info['file']}",
                    "file": file_info["file"]
                })
        
        # コードセキュリティ問題
        if "code_security" in all_results:
            code_results = all_results["code_security"]
            for secret_info in code_results.get("hardcoded_secrets", []):
                security_issues.append({
                    "type": "hardcoded_secret",
                    "severity": "critical",
                    "description": f"ハードコードされたシークレット: {secret_info['file']}",
                    "file": secret_info["file"]
                })
        
        # レポート生成
        report = {
            "scan_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_vulnerabilities": len(vulnerabilities),
                "total_security_issues": len(security_issues),
                "scan_duration": "completed"
            },
            "vulnerabilities": vulnerabilities,
            "security_issues": security_issues,
            "detailed_results": all_results,
            "recommendations": self.generate_security_recommendations(vulnerabilities, security_issues)
        }
        
        # レポートをファイルに保存
        report_file = f"/app/logs/security_scan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"セキュリティレポート生成完了: {report_file}")
        
        # レポート概要を出力
        print("\n" + "="*50)
        print("セキュリティスキャン結果概要")
        print("="*50)
        print(f"脆弱性数: {len(vulnerabilities)}")
        print(f"セキュリティ問題数: {len(security_issues)}")
        
        if vulnerabilities:
            print("\n🔴 脆弱性:")
            for vuln in vulnerabilities[:5]:  # 上位5件
                print(f"  - {vuln['description']} ({vuln['severity']})")
        
        if security_issues:
            print("\n⚠️ セキュリティ問題:")
            for issue in security_issues[:5]:  # 上位5件
                print(f"  - {issue['description']} ({issue['severity']})")
        
        print("="*50)
    
    def generate_security_recommendations(self, vulnerabilities: List[Dict], security_issues: List[Dict]) -> List[str]:
        """セキュリティ推奨事項生成"""
        recommendations = []
        
        # 脆弱性に基づく推奨事項
        if vulnerabilities:
            recommendations.append("依存関係の脆弱性を修正してください")
            recommendations.append("定期的なセキュリティアップデートを実施してください")
        
        # セキュリティ問題に基づく推奨事項
        for issue in security_issues:
            if issue["type"] == "hardcoded_secret":
                recommendations.append("ハードコードされたシークレットを環境変数に移動してください")
            elif issue["type"] == "world_writable_file":
                recommendations.append("ファイル権限を適切に設定してください")
            elif issue["type"] == "open_port":
                recommendations.append("不要なポートを閉じてください")
        
        if not recommendations:
            recommendations.append("現在のセキュリティ状態は良好です")
        
        return recommendations
    
    async def run_comprehensive_scan(self):
        """包括的セキュリティスキャン"""
        logger.info("包括的セキュリティスキャン開始")
        
        all_results = {}
        
        # 依存関係スキャン
        logger.info("依存関係スキャン実行中...")
        all_results["dependencies"] = self.scan_dependencies()
        
        # ネットワークセキュリティスキャン
        logger.info("ネットワークセキュリティスキャン実行中...")
        all_results["network"] = await self.scan_network_security()
        
        # ファイル権限スキャン
        logger.info("ファイル権限スキャン実行中...")
        all_results["file_permissions"] = self.scan_file_permissions()
        
        # コードセキュリティスキャン
        logger.info("コードセキュリティスキャン実行中...")
        all_results["code_security"] = self.scan_code_security()
        
        # 設定セキュリティスキャン
        logger.info("設定セキュリティスキャン実行中...")
        all_results["configuration"] = self.scan_configuration_security()
        
        # レポート生成
        self.generate_security_report(all_results)
        
        return all_results

async def main():
    """メイン関数"""
    scanner = SecurityScanner()
    
    try:
        results = await scanner.run_comprehensive_scan()
        logger.info("セキュリティスキャン完了")
        return results
    except Exception as e:
        logger.error(f"セキュリティスキャンエラー: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(main()) 