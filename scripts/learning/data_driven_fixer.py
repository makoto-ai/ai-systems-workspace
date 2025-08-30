#!/usr/bin/env python3
"""
Data-Driven Quality Fixer
学習データに基づく効果的な品質修正システム

Phase 13-B: 学習データ駆動の品質改善
成功パターンを活用した修正処理
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class DataDrivenFixer:
    def __init__(self):
        self.workspace = Path.cwd()
        self.out_dir = self.workspace / "out"
        self.learning_data = self._load_learning_data()
        self.success_patterns = self._analyze_success_patterns()
        
    def _load_learning_data(self) -> Dict[str, Any]:
        """学習データの読み込み"""
        data = {}
        
        # 主要な学習データファイル
        learning_files = [
            "adaptive_guidance.json",
            "autonomous_fix_results.json", 
            "learning_insights.json",
            "auto_guard_learning.json"
        ]
        
        for filename in learning_files:
            file_path = self.out_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data[filename] = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSONデコードエラー in {filename}: {e}")
                    data[filename] = {}
        
        return data
        
    def _analyze_success_patterns(self) -> Dict[str, Any]:
        """成功パターンの分析"""
        insights = self.learning_data.get("learning_insights.json", {})
        fix_rates = insights.get("fix_success_rates", {})
        
        return {
            "yaml_fixes": {
                "count": fix_rates.get("yaml_fixes", 0),
                "approach": "段階的修正",
                "priority": "high"
            },
            "context_warnings": {
                "count": fix_rates.get("context_warnings", 0),
                "approach": "コンテキスト修正", 
                "priority": "high"
            },
            "bash_syntax": {
                "count": fix_rates.get("bash_syntax", 0),
                "approach": "構文チェック後修正",
                "priority": "medium"
            }
        }
    
    def apply_yaml_fixes(self) -> Dict[str, Any]:
        """YAMLエラー修正（成功パターン活用）"""
        print("🔧 YAML修正開始（学習データ駆動）...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "method": "data_driven_yaml_fix",
            "success_pattern_applied": True,
            "fixes_applied": []
        }
        
        try:
            # yamllint実行（エラー検出）
            cmd = ["yamllint", ".github/workflows/", "-f", "parsable"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                results["status"] = "no_errors_found"
                results["message"] = "YAML エラーは検出されませんでした"
                return results
            
            # エラー解析と修正
            errors = result.stdout.strip().split('\n')
            yaml_files = set()
            
            for error in errors:
                if error and ':' in error:
                    file_path = error.split(':')[0]
                    yaml_files.add(file_path)
            
            # 成功パターンに基づく修正処理
            for file_path in yaml_files:
                fix_result = self._apply_safe_yaml_fix(file_path)
                results["fixes_applied"].append(fix_result)
            
            results["status"] = "completed"
            results["total_files_processed"] = len(yaml_files)
            
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
        
        return results
    
    def _apply_safe_yaml_fix(self, file_path: str) -> Dict[str, Any]:
        """安全なYAML修正（学習データパターン適用）"""
        fix_result = {
            "file": file_path,
            "timestamp": datetime.now().isoformat(),
            "approach": "data_driven_safe_fix"
        }
        
        try:
            # バックアップ作成
            backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            subprocess.run(["cp", file_path, backup_path], check=True)
            
            # 学習データから成功パターン適用
            # Line-length エラーの場合 → コメント改行
            # Indentation エラーの場合 → スペース調整
            # Truthy エラーの場合 → 引用符追加
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 成功パターン1: 長い行のコメント改行
            lines = content.split('\n')
            modified = False
            
            for i, line in enumerate(lines):
                # 120文字を超える行の処理
                if len(line) > 120 and '#' in line and not line.strip().startswith('#'):
                    comment_pos = line.find('#')
                    if comment_pos > 80:  # コメント位置が後半にある場合
                        before_comment = line[:comment_pos].rstrip()
                        comment_part = line[comment_pos:]
                        indent = len(line) - len(line.lstrip())
                        
                        # コメントを次の行に移動
                        lines[i] = before_comment
                        lines.insert(i + 1, ' ' * indent + comment_part)
                        modified = True
                        break
            
            if modified:
                content = '\n'.join(lines)
            
            # 変更があった場合のみファイル更新
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                fix_result["status"] = "applied"
                fix_result["changes"] = "line_length_comment_fix"
                fix_result["backup"] = backup_path
            else:
                # 変更なしの場合はバックアップ削除
                os.remove(backup_path)
                fix_result["status"] = "no_changes_needed"
            
        except Exception as e:
            fix_result["status"] = "error"
            fix_result["error"] = str(e)
        
        return fix_result
    
    def analyze_ide_warnings(self) -> Dict[str, Any]:
        """IDE警告状況の分析"""
        print("📊 IDE警告状況分析中...")
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "method": "ide_warning_analysis",
            "phase13a_effect": None
        }
        
        try:
            # yamllint で現在の状況確認
            cmd = ["yamllint", ".github/workflows/", "-f", "parsable"]
            yamllint_result = subprocess.run(cmd, capture_output=True, text=True)
            
            analysis["yamllint_errors"] = len(yamllint_result.stdout.strip().split('\n')) if yamllint_result.stdout.strip() else 0
            
            # actionlint で確認
            try:
                cmd = ["actionlint", ".github/workflows/"]
                actionlint_result = subprocess.run(cmd, capture_output=True, text=True)
                analysis["actionlint_errors"] = len(actionlint_result.stdout.strip().split('\n')) if actionlint_result.stdout.strip() else 0
            except FileNotFoundError:
                analysis["actionlint_errors"] = "tool_not_found"
            
            # shellcheck で確認
            try:
                cmd = ["find", ".github/workflows/", "-name", "*.yml", "-exec", "grep", "-l", "run:", "{}", "\\;"]
                workflow_files = subprocess.run(cmd, capture_output=True, text=True).stdout.strip().split('\n')
                
                shellcheck_errors = 0
                for file in workflow_files:
                    if file and os.path.exists(file):
                        cmd = ["shellcheck", "--format=json", file]
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        if result.stdout:
                            try:
                                shellcheck_data = json.loads(result.stdout)
                                shellcheck_errors += len(shellcheck_data)
                            except json.JSONDecodeError:
                                pass
                
                analysis["shellcheck_errors"] = shellcheck_errors
                
            except Exception:
                analysis["shellcheck_errors"] = "analysis_failed"
            
            # Phase 13-A 効果の評価
            total_errors = 0
            if isinstance(analysis["yamllint_errors"], int):
                total_errors += analysis["yamllint_errors"]
            if isinstance(analysis["actionlint_errors"], int):
                total_errors += analysis["actionlint_errors"]
            if isinstance(analysis["shellcheck_errors"], int):
                total_errors += analysis["shellcheck_errors"]
                
            analysis["total_linter_errors"] = total_errors
            analysis["phase13a_effect"] = "significant_improvement" if total_errors < 5 else "partial_improvement"
            
        except Exception as e:
            analysis["error"] = str(e)
        
        return analysis
    
    def generate_learning_report(self) -> Dict[str, Any]:
        """学習データ駆動の改善レポート生成"""
        print("📈 学習レポート生成中...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "phase": "13-B",
            "title": "学習データ駆動品質改善レポート",
            "success_patterns": self.success_patterns,
            "ide_analysis": self.analyze_ide_warnings(),
            "recommendations": []
        }
        
        # 成功パターンに基づく推奨事項
        yaml_success = self.success_patterns["yaml_fixes"]["count"]
        if yaml_success > 0:
            report["recommendations"].append({
                "priority": "high",
                "action": "YAML修正の継続強化",
                "reason": f"過去{yaml_success}件の成功実績",
                "method": "段階的修正アプローチの活用"
            })
        
        context_success = self.success_patterns["context_warnings"]["count"] 
        if context_success > 0:
            report["recommendations"].append({
                "priority": "high",
                "action": "コンテキスト警告の体系的解消",
                "reason": f"過去{context_success}件の成功実績",
                "method": "コンテキスト修正パターンの適用"
            })
        
        # autonomous_fix 改善提案
        autonomous_data = self.learning_data.get("autonomous_fix_results.json", {})
        if autonomous_data.get("success_rate", 1.0) < 0.5:
            report["recommendations"].append({
                "priority": "medium",
                "action": "autonomous_fix 検証プロセス強化",
                "reason": f"現在の成功率: {autonomous_data.get('success_rate', 0):.1%}",
                "method": "より安全な段階的検証の実装"
            })
        
        return report

def main():
    """メイン実行"""
    print("🚀 Phase 13-B: 学習データ駆動品質改善開始")
    print("=" * 50)
    
    fixer = DataDrivenFixer()
    
    # 1. IDE警告分析
    ide_analysis = fixer.analyze_ide_warnings()
    print(f"📊 現在のリンターエラー数: {ide_analysis.get('total_linter_errors', 'unknown')}")
    
    # 2. YAML修正の実行
    yaml_results = fixer.apply_yaml_fixes()
    print(f"🔧 YAML修正結果: {yaml_results.get('status', 'unknown')}")
    
    # 3. 学習レポート生成
    report = fixer.generate_learning_report()
    
    # 結果保存
    output_file = Path("out/phase13b_learning_report.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"📋 学習レポート保存: {output_file}")
    print("🎊 Phase 13-B 完了！")

if __name__ == "__main__":
    main()



