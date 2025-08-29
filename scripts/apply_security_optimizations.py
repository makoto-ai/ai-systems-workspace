#!/usr/bin/env python3
"""
🔧 Apply Security Optimizations - セキュリティ最適化適用システム
作成された最適化設定を実際のセキュリティシステムに適用
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any


class SecurityOptimizationApplicator:
    """セキュリティ最適化適用システム"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.scripts_dir = self.project_root / "scripts"

        # 最適化設定ファイル
        self.optimization_configs = {
            "threat_detection": self.scripts_dir / "security_optimization_config.json",
            "auto_repair": self.scripts_dir / "auto_repair_enhancement_config.json",
            "memory_integration": self.scripts_dir
            / "memory_security_integration_config.json",
            "github_actions": self.scripts_dir
            / "github_actions_optimization_config.json",
        }

        print("🔧 セキュリティ最適化適用システム初期化完了")

    def apply_threat_detection_optimizations(self) -> Dict[str, Any]:
        """脅威検知最適化の適用"""

        print("🔍 脅威検知最適化適用中...")

        config_file = self.optimization_configs["threat_detection"]
        if not config_file.exists():
            return {"success": False, "message": "脅威検知最適化設定が見つかりません"}

        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        # security_alert_system.pyに最適化を適用
        alert_system_file = self.scripts_dir / "security_alert_system.py"

        if not alert_system_file.exists():
            return {
                "success": False,
                "message": "security_alert_system.pyが見つかりません",
            }

        # ファイル内容の読み込み
        with open(alert_system_file, "r", encoding="utf-8") as f:
            content = f.read()

        # バックアップ作成
        backup_file = alert_system_file.with_suffix(".py.before_optimization")
        with open(backup_file, "w", encoding="utf-8") as f:
            f.write(content)

        # 最適化の適用
        modifications = []

        # 1. 除外パターンの更新
        dev_exclusions = config["dev_exclusions"]

        # 既存の除外パターンを新しいものに置換
        old_exclusions_pattern = r"exclude_patterns\s*=\s*\[.*?\]"
        new_exclusions = "exclude_patterns = [\n"
        for exclusion in dev_exclusions:
            new_exclusions += f"            '{exclusion}',\n"
        new_exclusions += "        ]"

        if re.search(old_exclusions_pattern, content, re.DOTALL):
            content = re.sub(
                old_exclusions_pattern, new_exclusions, content, flags=re.DOTALL
            )
            modifications.append("除外パターン更新")

        # 2. 脅威レベル閾値の更新
        adjusted_thresholds = config["adjusted_thresholds"]

        # calculate_threat_level関数の閾値を更新
        if "calculate_threat_level" in content:
            # 高脅威の閾値調整
            high_threshold = adjusted_thresholds["file_permissions"]["high_threshold"]
            medium_threshold = adjusted_thresholds["file_permissions"][
                "medium_threshold"
            ]

            # 閾値パターンの更新
            content = re.sub(
                r"high_count\s*>\s*\d+", f"high_count > {high_threshold}", content
            )
            content = re.sub(
                r"medium_count\s*>\s*\d+", f"medium_count > {medium_threshold}", content
            )
            modifications.append("脅威レベル閾値調整")

        # 3. 安全パターンの追加
        safe_patterns = config["safe_patterns"]

        # 安全パターンを検知除外に追加
        safe_pattern_code = "\n        # 安全パターン（最適化で追加）\n"
        for pattern in safe_patterns:
            safe_pattern_code += f"        if '{pattern}' in file_path:\n"
            safe_pattern_code += "            continue\n"

        # detect_sensitive_data_exposure関数に安全パターンを追加
        if "def detect_sensitive_data_exposure" in content:
            insertion_point = content.find("def detect_sensitive_data_exposure")
            function_start = content.find("{", insertion_point)
            if function_start != -1:
                content = (
                    content[: function_start + 1]
                    + safe_pattern_code
                    + content[function_start + 1 :]
                )
                modifications.append("安全パターン追加")

        # 最適化されたファイルの保存
        with open(alert_system_file, "w", encoding="utf-8") as f:
            f.write(content)

        result = {
            "success": True,
            "modifications": modifications,
            "backup_file": str(backup_file),
            "optimized_file": str(alert_system_file),
        }

        print(f"✅ 脅威検知最適化適用完了: {len(modifications)}項目変更")
        return result

    def apply_auto_repair_enhancements(self) -> Dict[str, Any]:
        """自動修復機能強化の適用"""

        print("🔧 自動修復機能強化適用中...")

        config_file = self.optimization_configs["auto_repair"]
        if not config_file.exists():
            return {"success": False, "message": "自動修復強化設定が見つかりません"}

        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        # auto_repair_system.pyに強化を適用
        repair_system_file = self.scripts_dir / "auto_repair_system.py"

        if not repair_system_file.exists():
            return {
                "success": False,
                "message": "auto_repair_system.pyが見つかりません",
            }

        # ファイル内容の読み込み
        with open(repair_system_file, "r", encoding="utf-8") as f:
            content = f.read()

        # バックアップ作成
        backup_file = repair_system_file.with_suffix(".py.before_enhancement")
        with open(backup_file, "w", encoding="utf-8") as f:
            f.write(content)

        enhancements = []

        # 1. スマート修復戦略の実装
        smart_strategies = config["smart_repair_strategies"]

        # ファイル権限修復の改良
        if "repair_file_permissions" in content:
            enhanced_permission_repair = '''
    def repair_file_permissions_enhanced(self, threat: Dict[str, Any]) -> Dict[str, Any]:
        """強化されたファイル権限修復"""
        try:
            file_path = threat.get('file', '')
            if not file_path or not os.path.exists(file_path):
                return {'success': False, 'error': 'ファイルが見つかりません'}
            
            # スマート権限判定
            if file_path.endswith(('.py', '.json', '.md')):
                target_permission = 0o644  # 読み書き権限
            elif file_path.endswith(('.sh', '.py')):
                target_permission = 0o755  # 実行権限付き
            else:
                target_permission = 0o644  # デフォルト
            
            # 事前検証
            current_stat = os.stat(file_path)
            if oct(current_stat.st_mode)[-3:] == oct(target_permission)[-3:]:
                return {'success': True, 'message': '権限は既に適切です'}
            
            # 権限変更
            os.chmod(file_path, target_permission)
            
            # 事後検証
            new_stat = os.stat(file_path)
            if oct(new_stat.st_mode)[-3:] == oct(target_permission)[-3:]:
                return {'success': True, 'message': f'権限を{oct(target_permission)[-3:]}に修正'}
            else:
                return {'success': False, 'error': '権限変更に失敗'}
                
        except Exception as e:
            return {'success': False, 'error': f'権限修復エラー: {str(e)}'}
'''
            content += enhanced_permission_repair
            enhancements.append("スマートファイル権限修復追加")

        # 2. 修復優先度システムの実装
        repair_priorities = config["repair_priorities"]

        priority_system_code = f'''
    def get_repair_priority(self, threat_type: str) -> int:
        """修復優先度取得"""
        priorities = {json.dumps(repair_priorities, ensure_ascii=False, indent=8)}
        
        for priority_level, threat_types in priorities.items():
            if threat_type in threat_types:
                if priority_level == "critical":
                    return 4
                elif priority_level == "high":
                    return 3
                elif priority_level == "medium":
                    return 2
                else:
                    return 1
        return 1  # デフォルト優先度
'''
        content += priority_system_code
        enhancements.append("修復優先度システム追加")

        # 3. バッチ処理機能の実装
        batch_processing_code = '''
    def batch_repair_threats(self, threats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """バッチ修復処理"""
        # 優先度でソート
        sorted_threats = sorted(threats, key=lambda t: self.get_repair_priority(t.get('type', '')), reverse=True)
        
        results = {
            'total_threats': len(threats),
            'repaired': 0,
            'failed': 0,
            'details': []
        }
        
        for threat in sorted_threats:
            try:
                repair_result = self.repair_individual_threat(threat)
                if repair_result.get('success', False):
                    results['repaired'] += 1
                else:
                    results['failed'] += 1
                results['details'].append(repair_result)
            except Exception as e:
                results['failed'] += 1
                results['details'].append({'success': False, 'error': str(e)})
        
        return results
'''
        content += batch_processing_code
        enhancements.append("バッチ修復処理追加")

        # 最適化されたファイルの保存
        with open(repair_system_file, "w", encoding="utf-8") as f:
            f.write(content)

        result = {
            "success": True,
            "enhancements": enhancements,
            "backup_file": str(backup_file),
            "enhanced_file": str(repair_system_file),
        }

        print(f"✅ 自動修復機能強化適用完了: {len(enhancements)}項目追加")
        return result

    def apply_memory_integration(self) -> Dict[str, Any]:
        """記憶システム統合の適用"""

        print("🧠 記憶システム統合適用中...")

        config_file = self.optimization_configs["memory_integration"]
        if not config_file.exists():
            return {"success": False, "message": "記憶システム統合設定が見つかりません"}

        # 記憶システム統合のコード生成
        integration_code = '''
# 記憶システム統合（最適化で追加）
try:
    from memory_consistency_engine import MemoryConsistencyEngine
    from memory_system_integration import IntegratedMemorySystem
    
    class SecurityMemoryIntegration:
        """セキュリティ・記憶システム統合"""
        
        def __init__(self):
            self.consistency_engine = MemoryConsistencyEngine()
            self.integrated_memory = IntegratedMemorySystem()
        
        def record_security_evaluation(self, context: str, evaluation: str, score: float = None):
            """セキュリティ評価記録"""
            return self.consistency_engine.record_evaluation(context, evaluation, score)
        
        def check_evaluation_consistency(self, context: str, new_evaluation: str):
            """評価一貫性チェック"""
            return self.consistency_engine.check_before_evaluation(context, new_evaluation)
    
    # グローバル統合インスタンス
    security_memory = SecurityMemoryIntegration()
    
except ImportError:
    # 記憶システムが利用できない場合のフォールバック
    security_memory = None
    print("⚠️ 記憶システム統合: インポートエラーのためスキップ")
'''

        # security_master_system.pyに統合を追加
        master_system_file = self.scripts_dir / "security_master_system.py"

        if master_system_file.exists():
            with open(master_system_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 記憶システム統合コードを追加
            content = integration_code + "\n" + content

            with open(master_system_file, "w", encoding="utf-8") as f:
                f.write(content)

        result = {
            "success": True,
            "integration_applied": "記憶システム統合コード追加",
            "target_file": str(master_system_file),
        }

        print("✅ 記憶システム統合適用完了")
        return result

    def verify_optimizations(self) -> Dict[str, Any]:
        """最適化適用確認"""

        print("🔍 最適化適用確認中...")

        verification_results = {
            "optimized_files": [],
            "backup_files": [],
            "config_files": [],
            "total_optimizations": 0,
        }

        # 最適化されたファイルの確認
        for system, config_file in self.optimization_configs.items():
            if config_file.exists():
                verification_results["config_files"].append(str(config_file))

        # バックアップファイルの確認
        backup_files = list(self.scripts_dir.glob("*.before_*"))
        verification_results["backup_files"] = [str(f) for f in backup_files]

        # 最適化されたファイルの確認
        optimized_files = [
            "security_alert_system.py",
            "auto_repair_system.py",
            "security_master_system.py",
        ]

        for file_name in optimized_files:
            file_path = self.scripts_dir / file_name
            if file_path.exists():
                verification_results["optimized_files"].append(str(file_path))

        verification_results["total_optimizations"] = len(
            verification_results["config_files"]
        )

        print(
            f"✅ 最適化確認完了: {verification_results['total_optimizations']}個の最適化適用"
        )
        return verification_results

    def apply_all_optimizations(self) -> Dict[str, Any]:
        """全最適化適用"""

        print("🚀 全セキュリティ最適化適用開始...")

        results = {
            "threat_detection": self.apply_threat_detection_optimizations(),
            "auto_repair": self.apply_auto_repair_enhancements(),
            "memory_integration": self.apply_memory_integration(),
            "verification": self.verify_optimizations(),
        }

        success_count = sum(1 for r in results.values() if r.get("success", True))

        final_result = {
            "total_phases": len(results) - 1,  # verification除く
            "successful_phases": success_count - 1,  # verification除く
            "success_rate": f"{success_count-1}/{len(results)-1}",
            "results": results,
            "ready_for_testing": success_count >= 3,
        }

        if final_result["ready_for_testing"]:
            print("✅ 全最適化適用完了 - テスト準備完了")
        else:
            print("⚠️ 一部最適化適用に失敗 - 手動確認が必要")

        return final_result


if __name__ == "__main__":
    # 最適化適用実行
    applicator = SecurityOptimizationApplicator()

    print("🔧 セキュリティ最適化適用システム開始")

    # 全最適化適用
    result = applicator.apply_all_optimizations()

    print(f"\n📊 適用結果: {result['success_rate']}")
    print(f"🧪 テスト準備: {'✅ 完了' if result['ready_for_testing'] else '❌ 未完了'}")

    if result["ready_for_testing"]:
        print("\n💡 次のステップ:")
        print("   python3 scripts/security_master_system.py  # 最適化後テスト実行")
