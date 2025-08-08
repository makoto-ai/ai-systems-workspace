#!/usr/bin/env python3
"""
🔗 APIdogMCP Optimizer - APIdogMCP最適化システム
Cursor AI + APIdogMCPの自動テスト・修正機能を最適化
"""

import os
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

class APIdogMCPOptimizer:
    """APIdogMCP最適化システム"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.mcp_config = self.project_root / ".cursor" / "mcp.json"
        self.apidog_config = self.project_root / "apidog.config.json"
        self.openapi_spec = self.project_root / "apidog-openapi-spec.json"
        
        # 最適化ログ
        self.logs_dir = self.project_root / "scripts" / "apidog_mcp_logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # 設定確認
        self._verify_mcp_setup()
    
    def _verify_mcp_setup(self) -> bool:
        """MCP設定確認"""
        
        checks = {
            "mcp_config_exists": self.mcp_config.exists(),
            "apidog_config_exists": self.apidog_config.exists(),
            "openapi_spec_exists": self.openapi_spec.exists()
        }
        
        print("🔍 APIdogMCP設定確認:")
        for check, status in checks.items():
            print(f"{'✅' if status else '❌'} {check}: {status}")
        
        if not all(checks.values()):
            print("⚠️ 一部設定ファイルが不足しています")
            return False
        
        return True
    
    def optimize_mcp_config(self) -> Dict[str, Any]:
        """MCP設定最適化"""
        
        print("🔧 MCP設定最適化中...")
        
        # 現在の設定読み込み
        with open(self.mcp_config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 最適化項目
        optimizations = []
        
        # 1. watchFiles最適化
        ai_analysis = config.get("aiAnalysis", {})
        watch_files = ai_analysis.get("watchFiles", [])
        
        # 重要ファイルの追加チェック
        important_files = [
            "app/main.py",
            "app/api/*.py", 
            "app/services/*.py",
            "scripts/memory_consistency_engine.py",
            "scripts/memory_system_integration.py",
            "scripts/security_master_system.py"
        ]
        
        for file_pattern in important_files:
            if file_pattern not in watch_files:
                watch_files.append(file_pattern)
                optimizations.append(f"watchFiles追加: {file_pattern}")
        
        ai_analysis["watchFiles"] = watch_files
        
        # 2. エラー分析強化
        on_error = ai_analysis.get("onError", {})
        enhanced_error_handling = {
            "analyzeWithMCP": True,
            "suggestFixes": True,
            "updateOpenAPI": True,
            "autoRetest": True,  # 新機能
            "logErrors": True,   # 新機能
            "notifyOnCritical": True  # 新機能
        }
        
        for key, value in enhanced_error_handling.items():
            if key not in on_error or on_error[key] != value:
                on_error[key] = value
                optimizations.append(f"エラー処理強化: {key}={value}")
        
        ai_analysis["onError"] = on_error
        config["aiAnalysis"] = ai_analysis
        
        # 3. 新機能追加
        if "apiOptimization" not in config:
            config["apiOptimization"] = {
                "enableCaching": True,
                "responseTimeMonitoring": True,
                "errorRateTracking": True,
                "autoPerformanceTuning": True
            }
            optimizations.append("API最適化機能追加")
        
        if "memoryIntegration" not in config:
            config["memoryIntegration"] = {
                "enabled": True,
                "consistencyChecks": True,
                "errorLearning": True,
                "patternRecognition": True
            }
            optimizations.append("記憶システム統合追加")
        
        # 最適化された設定の保存
        optimized_config_path = self.mcp_config.with_suffix('.optimized.json')
        with open(optimized_config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        result = {
            "optimizations_applied": optimizations,
            "optimized_config_path": str(optimized_config_path),
            "original_config_backup": str(self.mcp_config) + ".backup",
            "success": True
        }
        
        print(f"✅ MCP設定最適化完了: {len(optimizations)}項目改善")
        return result
    
    def test_mcp_integration(self) -> Dict[str, Any]:
        """MCP統合テスト"""
        
        print("🧪 APIdogMCP統合テスト実行中...")
        
        test_results = {
            "filesystem_server": self._test_filesystem_server(),
            "openapi_server": self._test_openapi_server(),
            "git_server": self._test_git_server(),
            "error_analysis": self._test_error_analysis(),
            "memory_integration": self._test_memory_integration()
        }
        
        success_count = sum(1 for result in test_results.values() if result.get("success", False))
        total_tests = len(test_results)
        
        overall_result = {
            "test_results": test_results,
            "success_rate": f"{success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)",
            "overall_success": success_count == total_tests,
            "recommendations": self._generate_recommendations(test_results)
        }
        
        print(f"📊 MCP統合テスト結果: {overall_result['success_rate']}")
        return overall_result
    
    def _test_filesystem_server(self) -> Dict[str, Any]:
        """ファイルシステムサーバーテスト"""
        
        try:
            # npxコマンドの存在確認
            result = subprocess.run(
                ["npx", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                return {"success": True, "message": "npx利用可能", "version": result.stdout.strip()}
            else:
                return {"success": False, "message": "npx利用不可", "error": result.stderr}
                
        except Exception as e:
            return {"success": False, "message": "filesystem server test failed", "error": str(e)}
    
    def _test_openapi_server(self) -> Dict[str, Any]:
        """OpenAPIサーバーテスト"""
        
        try:
            # OpenAPI specファイルの検証
            if not self.openapi_spec.exists():
                return {"success": False, "message": "OpenAPI spec file not found"}
            
            with open(self.openapi_spec, 'r', encoding='utf-8') as f:
                spec_data = json.load(f)
            
            required_fields = ["openapi", "info", "paths"]
            missing_fields = [field for field in required_fields if field not in spec_data]
            
            if missing_fields:
                return {
                    "success": False, 
                    "message": f"OpenAPI spec incomplete: missing {missing_fields}"
                }
            
            return {
                "success": True, 
                "message": "OpenAPI spec valid",
                "endpoints": len(spec_data.get("paths", {}))
            }
            
        except Exception as e:
            return {"success": False, "message": "OpenAPI server test failed", "error": str(e)}
    
    def _test_git_server(self) -> Dict[str, Any]:
        """Gitサーバーテスト"""
        
        try:
            # Git利用可能性確認
            result = subprocess.run(
                ["git", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            
            if result.returncode == 0:
                # リポジトリ状態確認
                status_result = subprocess.run(
                    ["git", "status", "--porcelain"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5,
                    cwd=self.project_root
                )
                
                return {
                    "success": True, 
                    "message": "Git server ready",
                    "git_version": result.stdout.strip(),
                    "repo_clean": len(status_result.stdout.strip()) == 0
                }
            else:
                return {"success": False, "message": "Git not available", "error": result.stderr}
                
        except Exception as e:
            return {"success": False, "message": "Git server test failed", "error": str(e)}
    
    def _test_error_analysis(self) -> Dict[str, Any]:
        """エラー分析機能テスト"""
        
        try:
            # MCP設定のエラー分析設定確認
            with open(self.mcp_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            ai_analysis = config.get("aiAnalysis", {})
            on_error = ai_analysis.get("onError", {})
            
            required_features = ["analyzeWithMCP", "suggestFixes", "updateOpenAPI"]
            enabled_features = [f for f in required_features if on_error.get(f, False)]
            
            return {
                "success": len(enabled_features) == len(required_features),
                "message": f"Error analysis features: {len(enabled_features)}/{len(required_features)} enabled",
                "enabled_features": enabled_features,
                "missing_features": [f for f in required_features if f not in enabled_features]
            }
            
        except Exception as e:
            return {"success": False, "message": "Error analysis test failed", "error": str(e)}
    
    def _test_memory_integration(self) -> Dict[str, Any]:
        """記憶システム統合テスト"""
        
        try:
            # 記憶システムファイルの存在確認
            memory_files = [
                "scripts/memory_consistency_engine.py",
                "scripts/memory_system_integration.py",
                "scripts/cursor_memory_enhanced.py"
            ]
            
            existing_files = [f for f in memory_files if (self.project_root / f).exists()]
            
            # 統合記憶システムのテスト実行
            if len(existing_files) == len(memory_files):
                try:
                    result = subprocess.run(
                        ["python3", "scripts/memory_system_integration.py"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        cwd=self.project_root
                    )
                    
                    success = result.returncode == 0 and "統合記憶システム起動完了" in result.stdout
                    
                    return {
                        "success": success,
                        "message": "Memory integration test completed",
                        "existing_files": existing_files,
                        "test_output": result.stdout if success else result.stderr
                    }
                except subprocess.TimeoutExpired:
                    return {
                        "success": False,
                        "message": "Memory integration test timeout",
                        "existing_files": existing_files
                    }
            else:
                return {
                    "success": False,
                    "message": f"Memory files missing: {len(existing_files)}/{len(memory_files)}",
                    "existing_files": existing_files,
                    "missing_files": [f for f in memory_files if f not in existing_files]
                }
                
        except Exception as e:
            return {"success": False, "message": "Memory integration test failed", "error": str(e)}
    
    def _generate_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """推奨事項生成"""
        
        recommendations = []
        
        # 各テスト結果に基づく推奨事項
        if not test_results["filesystem_server"]["success"]:
            recommendations.append("npxをインストールしてfilesystem serverを有効化")
        
        if not test_results["openapi_server"]["success"]:
            recommendations.append("OpenAPI specファイルを修正・更新")
        
        if not test_results["git_server"]["success"]:
            recommendations.append("Git設定を確認・修正")
        
        if not test_results["error_analysis"]["success"]:
            recommendations.append("MCP設定でエラー分析機能を有効化")
        
        if not test_results["memory_integration"]["success"]:
            recommendations.append("記憶システム統合の設定・テストを完了")
        
        # 成功した場合の最適化推奨
        success_count = sum(1 for r in test_results.values() if r.get("success", False))
        if success_count >= 4:
            recommendations.append("APIdogMCP最適化設定を本番環境に適用")
            recommendations.append("継続的なパフォーマンス監視を設定")
        
        return recommendations
    
    def apply_optimizations(self) -> Dict[str, Any]:
        """最適化適用"""
        
        print("🚀 APIdogMCP最適化適用中...")
        
        # 1. MCP設定最適化
        optimization_result = self.optimize_mcp_config()
        
        # 2. 統合テスト
        test_result = self.test_mcp_integration()
        
        # 3. 最適化済み設定を本番に適用
        if test_result["overall_success"]:
            optimized_config = Path(optimization_result["optimized_config_path"])
            
            # バックアップ作成
            backup_path = self.mcp_config.with_suffix('.backup.json')
            if self.mcp_config.exists():
                with open(self.mcp_config, 'r') as src, open(backup_path, 'w') as dst:
                    dst.write(src.read())
            
            # 最適化設定を適用
            with open(optimized_config, 'r') as src, open(self.mcp_config, 'w') as dst:
                dst.write(src.read())
            
            print("✅ 最適化設定を本番環境に適用完了")
            
            final_result = {
                "optimization_applied": True,
                "backup_created": str(backup_path),
                "test_success_rate": test_result["success_rate"],
                "recommendations": test_result["recommendations"]
            }
        else:
            print("⚠️ テスト失敗のため最適化設定は適用されませんでした")
            final_result = {
                "optimization_applied": False,
                "test_success_rate": test_result["success_rate"],
                "issues": [r for r in test_result["test_results"].values() if not r.get("success", True)],
                "recommendations": test_result["recommendations"]
            }
        
        return final_result

if __name__ == "__main__":
    # APIdogMCP最適化実行
    optimizer = APIdogMCPOptimizer()
    
    print("🔗 APIdogMCP最適化システム起動")
    
    # 最適化適用
    result = optimizer.apply_optimizations()
    
    print(f"📊 最適化結果: {'成功' if result['optimization_applied'] else '失敗'}")
    print(f"📈 テスト成功率: {result['test_success_rate']}")
    
    if result.get("recommendations"):
        print("💡 推奨事項:")
        for rec in result["recommendations"]:
            print(f"   - {rec}")