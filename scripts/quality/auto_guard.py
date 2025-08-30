#!/usr/bin/env python3
"""
🛡️ Phase 3: 自動品質ガードシステム
===============================

品質劣化を自動検知し、修正・ロールバックを実行するシステム

主要機能:
- 品質劣化の自動検知
- 修正可能な問題の自動修正
- 修正不可能な場合のロールバック
- リアルタイムアラート
- 学習データ統合
"""

import os
import sys
import json
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import tempfile
import git


class AutoGuardEngine:
    """自動品質ガードエンジン"""
    
    def __init__(self):
        self.base_dir = Path(".")
        self.backup_dir = Path("backups/auto_guard")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Git repository
        try:
            self.repo = git.Repo(".")
        except:
            self.repo = None
            
        # 学習データ読み込み
        self.learning_data = self._load_learning_data()
        
        # 修正ルール読み込み
        self.fix_rules = self._load_fix_rules()
        
        # 品質閾値設定
        self.quality_thresholds = {
            "critical": 0.3,    # この以下は緊急対応
            "warning": 0.6,     # この以下は警告
            "degradation": 0.2  # この以下の劣化で自動対応
        }
    
    def _load_learning_data(self) -> Dict[str, Any]:
        """学習データ読み込み"""
        try:
            if os.path.exists("out/continuous_learning.json"):
                with open("out/continuous_learning.json") as f:
                    return json.load(f)
        except:
            pass
        return {"patterns": {}, "fixes": {}, "success_rates": {}}
    
    def _load_fix_rules(self) -> Dict[str, Any]:
        """修正ルール読み込み"""
        return {
            "yaml": {
                "trailing_spaces": r's/\s+$//g',
                "missing_document_start": '1i---',
                "wrong_indentation": 'indentation_fix'
            },
            "python": {
                "missing_docstring": 'add_docstring',
                "long_lines": 'break_long_lines',
                "unused_imports": 'remove_unused_imports'
            },
            "general": {
                "missing_newline": '$a\\',
                "tab_to_spaces": 's/\t/    /g'
            }
        }
    
    def analyze_quality_change(self, file_path: str, current_score: float, previous_score: float) -> Dict[str, Any]:
        """品質変化分析"""
        analysis = {
            "file": file_path,
            "timestamp": datetime.now().isoformat(),
            "current_score": current_score,
            "previous_score": previous_score,
            "change": current_score - previous_score,
            "severity": "none",
            "action_needed": False,
            "recommended_action": "none",
            "confidence": 0.0
        }
        
        # 変化の大きさで重要度判定
        change = analysis["change"]
        
        if change <= -self.quality_thresholds["degradation"]:
            if current_score <= self.quality_thresholds["critical"]:
                analysis["severity"] = "critical"
                analysis["action_needed"] = True
                analysis["recommended_action"] = "emergency_rollback"
                analysis["confidence"] = 0.95
            elif current_score <= self.quality_thresholds["warning"]:
                analysis["severity"] = "high"
                analysis["action_needed"] = True
                analysis["recommended_action"] = "auto_fix"
                analysis["confidence"] = 0.8
            else:
                analysis["severity"] = "medium"
                analysis["action_needed"] = True
                analysis["recommended_action"] = "guided_fix"
                analysis["confidence"] = 0.6
        elif change <= -0.1:  # 軽微な劣化
            analysis["severity"] = "low"
            analysis["recommended_action"] = "monitor"
            analysis["confidence"] = 0.4
        
        return analysis
    
    def create_backup(self, file_path: str) -> str:
        """ファイルバックアップ作成"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = Path(file_path).name
            backup_path = self.backup_dir / f"{file_name}.{timestamp}.backup"
            
            shutil.copy2(file_path, backup_path)
            
            # バックアップ情報記録
            backup_info = {
                "original_file": file_path,
                "backup_path": str(backup_path),
                "timestamp": datetime.now().isoformat(),
                "reason": "auto_guard_backup"
            }
            
            info_path = backup_path.with_suffix(".backup.json")
            with open(info_path, "w") as f:
                json.dump(backup_info, f, indent=2)
            
            return str(backup_path)
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return ""
    
    def attempt_auto_fix(self, file_path: str, issues: List[str]) -> Tuple[bool, List[str]]:
        """自動修正試行"""
        backup_path = self.create_backup(file_path)
        if not backup_path:
            return False, ["Backup creation failed"]
        
        fix_results = []
        success = True
        
        try:
            file_ext = Path(file_path).suffix.lower()
            
            # ファイル種別に応じた修正
            if file_ext in ['.yml', '.yaml']:
                success, results = self._fix_yaml_file(file_path, issues)
                fix_results.extend(results)
            elif file_ext == '.py':
                success, results = self._fix_python_file(file_path, issues)
                fix_results.extend(results)
            else:
                success, results = self._fix_general_file(file_path, issues)
                fix_results.extend(results)
            
            # 修正後の品質チェック
            if success:
                success = self._verify_fix_quality(file_path)
                if not success:
                    fix_results.append("Quality verification failed")
            
            return success, fix_results
            
        except Exception as e:
            fix_results.append(f"Auto-fix error: {e}")
            return False, fix_results
    
    def _fix_yaml_file(self, file_path: str, issues: List[str]) -> Tuple[bool, List[str]]:
        """YAML ファイル自動修正"""
        results = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            modified = False
            
            # 末尾空白削除
            if 'trailing-spaces' in str(issues):
                lines = content.split('\n')
                lines = [line.rstrip() for line in lines]
                content = '\n'.join(lines)
                modified = True
                results.append("Fixed trailing spaces")
            
            # ドキュメント開始追加
            if 'document-start' in str(issues) and not content.strip().startswith('---'):
                content = '---\n' + content
                modified = True
                results.append("Added document start")
            
            # ファイル末尾改行
            if not content.endswith('\n'):
                content += '\n'
                modified = True
                results.append("Added final newline")
            
            if modified:
                with open(file_path, 'w') as f:
                    f.write(content)
                results.append(f"YAML file modified: {len(results)-1} fixes applied")
            
            return True, results
            
        except Exception as e:
            return False, [f"YAML fix error: {e}"]
    
    def _fix_python_file(self, file_path: str, issues: List[str]) -> Tuple[bool, List[str]]:
        """Python ファイル自動修正"""
        results = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            modified = False
            
            # 基本的なフォーマット修正
            if not content.endswith('\n'):
                content += '\n'
                modified = True
                results.append("Added final newline")
            
            # タブをスペースに変換
            if '\t' in content:
                content = content.expandtabs(4)
                modified = True
                results.append("Converted tabs to spaces")
            
            if modified:
                with open(file_path, 'w') as f:
                    f.write(content)
            
            return True, results
            
        except Exception as e:
            return False, [f"Python fix error: {e}"]
    
    def _fix_general_file(self, file_path: str, issues: List[str]) -> Tuple[bool, List[str]]:
        """一般ファイル自動修正"""
        results = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # ファイル末尾改行
            if not content.endswith('\n'):
                content += '\n'
                with open(file_path, 'w') as f:
                    f.write(content)
                results.append("Added final newline")
            
            return True, results
            
        except Exception as e:
            return False, [f"General fix error: {e}"]
    
    def _verify_fix_quality(self, file_path: str) -> bool:
        """修正後品質検証"""
        try:
            # 基本的な構文チェック
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext in ['.yml', '.yaml']:
                # yamllint チェック
                result = subprocess.run(
                    ["yamllint", file_path],
                    capture_output=True, text=True
                )
                return result.returncode == 0
            
            elif file_ext == '.py':
                # Python 構文チェック
                result = subprocess.run(
                    ["python", "-m", "py_compile", file_path],
                    capture_output=True, text=True
                )
                return result.returncode == 0
            
            return True  # 他のファイル形式は基本的にOK
            
        except:
            return False
    
    def emergency_rollback(self, file_path: str) -> Tuple[bool, str]:
        """緊急ロールバック"""
        try:
            # 最新のバックアップを検索
            file_name = Path(file_path).name
            backup_files = list(self.backup_dir.glob(f"{file_name}.*.backup"))
            
            if not backup_files:
                return False, "No backup found"
            
            # 最新のバックアップを選択
            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
            
            # ロールバック実行
            shutil.copy2(latest_backup, file_path)
            
            rollback_info = {
                "file": file_path,
                "backup_used": str(latest_backup),
                "timestamp": datetime.now().isoformat(),
                "reason": "emergency_rollback"
            }
            
            # ロールバック記録保存
            os.makedirs("out", exist_ok=True)
            with open("out/rollback_history.json", "a") as f:
                f.write(json.dumps(rollback_info) + "\n")
            
            return True, f"Rolled back to {latest_backup}"
            
        except Exception as e:
            return False, f"Rollback failed: {e}"
    
    def process_quality_degradation(self, file_path: str, current_score: float, previous_score: float, issues: List[str] = None) -> Dict[str, Any]:
        """品質劣化処理"""
        issues = issues or []
        
        # 品質変化分析
        analysis = self.analyze_quality_change(file_path, current_score, previous_score)
        
        result = {
            "analysis": analysis,
            "actions_taken": [],
            "success": False,
            "final_state": "unknown"
        }
        
        if not analysis["action_needed"]:
            result["success"] = True
            result["final_state"] = "no_action_needed"
            return result
        
        print(f"🛡️ Auto Guard: Processing {analysis['severity']} quality issue in {Path(file_path).name}")
        
        # 推奨アクションに応じた処理
        if analysis["recommended_action"] == "emergency_rollback":
            success, message = self.emergency_rollback(file_path)
            result["actions_taken"].append(f"emergency_rollback: {message}")
            result["success"] = success
            result["final_state"] = "rolled_back" if success else "rollback_failed"
            
        elif analysis["recommended_action"] == "auto_fix":
            success, fix_results = self.attempt_auto_fix(file_path, issues)
            result["actions_taken"].extend([f"auto_fix: {r}" for r in fix_results])
            result["success"] = success
            result["final_state"] = "auto_fixed" if success else "fix_failed"
            
            # 自動修正失敗時はロールバック
            if not success:
                rollback_success, rollback_message = self.emergency_rollback(file_path)
                result["actions_taken"].append(f"fallback_rollback: {rollback_message}")
                result["final_state"] = "rolled_back" if rollback_success else "critical_state"
                
        elif analysis["recommended_action"] == "guided_fix":
            result["actions_taken"].append("guided_fix: Manual intervention recommended")
            result["success"] = True  # ガイダンス提供は成功とする
            result["final_state"] = "awaiting_manual_fix"
            
        else:
            result["actions_taken"].append(f"monitor: Continuing observation")
            result["success"] = True
            result["final_state"] = "monitoring"
        
        # 学習データ更新
        self._update_learning_data(result)
        
        return result
    
    def _update_learning_data(self, result: Dict[str, Any]):
        """学習データ更新"""
        try:
            # 処理結果を学習データに追加
            learning_entry = {
                "timestamp": datetime.now().isoformat(),
                "file": result["analysis"]["file"],
                "severity": result["analysis"]["severity"],
                "action": result["analysis"]["recommended_action"],
                "success": result["success"],
                "final_state": result["final_state"]
            }
            
            # 学習履歴ファイルに追加
            os.makedirs("out", exist_ok=True)
            with open("out/auto_guard_learning.json", "a") as f:
                f.write(json.dumps(learning_entry) + "\n")
                
        except Exception as e:
            print(f"Learning data update error: {e}")
    
    def send_alert(self, result: Dict[str, Any]):
        """アラート送信"""
        analysis = result["analysis"]
        
        if analysis["severity"] in ["critical", "high"]:
            message = f"""
🚨 Auto Guard Alert: {analysis['severity'].upper()}

File: {analysis['file']}
Score Change: {analysis['previous_score']:.2f} → {analysis['current_score']:.2f}
Actions Taken: {', '.join(result['actions_taken'])}
Final State: {result['final_state']}
Time: {analysis['timestamp']}
"""
            print(message)
            
            # アラート履歴保存
            try:
                os.makedirs("out", exist_ok=True)
                with open("out/auto_guard_alerts.json", "a") as f:
                    f.write(json.dumps({
                        "timestamp": analysis["timestamp"],
                        "severity": analysis["severity"],
                        "file": analysis["file"],
                        "message": message.strip()
                    }) + "\n")
            except:
                pass


def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="🛡️ Auto Guard System")
    parser.add_argument("--file", "-f", help="File to guard")
    parser.add_argument("--current-score", type=float, default=0.5, help="Current quality score")
    parser.add_argument("--previous-score", type=float, default=0.8, help="Previous quality score")
    parser.add_argument("--test", action="store_true", help="Run test mode")
    
    args = parser.parse_args()
    
    guard = AutoGuardEngine()
    
    if args.test:
        # テストモード
        print("🧪 Auto Guard Test Mode")
        print("=====================")
        
        # テストファイルで品質劣化をシミュレート
        test_file = "test_guard_file.txt"
        
        with open(test_file, "w") as f:
            f.write("Test content for auto guard")
        
        result = guard.process_quality_degradation(
            test_file, 
            0.3,  # 低いスコア（劣化）
            0.8,  # 高い以前のスコア
            ["general formatting issues"]
        )
        
        print(f"Test Result: {result['final_state']}")
        print(f"Actions: {', '.join(result['actions_taken'])}")
        
        # テストファイル削除
        if os.path.exists(test_file):
            os.remove(test_file)
            
        # バックアップが作成されたか確認
        backup_count = len(list(guard.backup_dir.glob("*.backup")))
        print(f"Backup files created: {backup_count}")
        
    elif args.file:
        # 実際のファイル処理
        if not os.path.exists(args.file):
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
        
        result = guard.process_quality_degradation(
            args.file,
            args.current_score,
            args.previous_score
        )
        
        print(f"🛡️ Auto Guard Result: {result['final_state']}")
        
        if result["actions_taken"]:
            print("Actions taken:")
            for action in result["actions_taken"]:
                print(f"  • {action}")
        
        # アラート送信
        guard.send_alert(result)
        
    else:
        print("❌ Please specify --file or --test")
        parser.print_help()


if __name__ == "__main__":
    main()


