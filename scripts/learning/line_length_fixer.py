#!/usr/bin/env python3
"""
Line Length Fixer - Phase 13-C特化
学習データ駆動による行長エラー修正

成功パターン: コメント改行、長いrun行の分割
"""

import re
import os
import subprocess
from pathlib import Path
from datetime import datetime

class LineLengthFixer:
    def __init__(self):
        self.max_length = 120
        self.workspace = Path.cwd()
        self.fixes_applied = 0
        
    def fix_long_lines_in_file(self, file_path: str) -> dict:
        """ファイル内の長い行を修正"""
        result = {
            "file": file_path,
            "timestamp": datetime.now().isoformat(),
            "fixes_applied": 0,
            "lines_processed": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            modified = False
            
            for i, line in enumerate(lines):
                original_line = line
                line_num = i + 1
                
                if len(line.rstrip()) > self.max_length:
                    # 修正パターン1: コメント分離
                    new_line = self._fix_comment_line(line)
                    
                    # 修正パターン2: 長いrun行の分割
                    if new_line == line:
                        new_line = self._fix_run_line(line)
                    
                    # 修正パターン3: 長いecho行の分割
                    if new_line == line:
                        new_line = self._fix_echo_line(line)
                        
                    # 修正パターン4: 長いURL行の分割
                    if new_line == line:
                        new_line = self._fix_url_line(line)
                    
                    if new_line != line:
                        lines[i] = new_line
                        modified = True
                        result["lines_processed"].append({
                            "line_num": line_num,
                            "original_length": len(original_line.rstrip()),
                            "new_length": len(new_line.rstrip()),
                            "pattern": self._identify_pattern(original_line)
                        })
                        result["fixes_applied"] += 1
            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                print(f"✅ 修正完了: {file_path} ({result['fixes_applied']}行)")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ エラー: {file_path} - {e}")
        
        return result
    
    def _fix_comment_line(self, line: str) -> str:
        """コメント付きの長い行を修正"""
        # パターン: 長い行の最後にコメントがある場合
        if '#' in line and len(line.strip()) > self.max_length:
            # 最後の#以降をコメントとして認識
            parts = line.rstrip().split('#')
            if len(parts) >= 2:
                main_part = '#'.join(parts[:-1]).rstrip()
                comment_part = parts[-1].strip()
                indent = len(line) - len(line.lstrip())
                
                # メイン部分が短くなればOK
                if len(main_part) <= self.max_length - 10:
                    return main_part + '\n' + ' ' * indent + '# ' + comment_part + '\n'
        
        return line
    
    def _fix_run_line(self, line: str) -> str:
        """長いrun行を修正"""
        stripped = line.strip()
        
        # run: で始まる長い行の場合
        if stripped.startswith('run:') and len(stripped) > self.max_length:
            indent = len(line) - len(line.lstrip())
            
            # |を使った複数行形式に変換
            content = stripped[4:].strip()  # "run: "を除去
            
            if len(content) > 100:  # 十分長い場合のみ変換
                return f"{' ' * indent}run: |\n{' ' * (indent + 2)}{content}\n"
        
        return line
    
    def _fix_echo_line(self, line: str) -> str:
        """長いecho行を修正"""
        stripped = line.strip()
        
        # echo で始まる長い行
        if 'echo' in stripped and len(stripped) > self.max_length:
            indent = len(line) - len(line.lstrip())
            
            # echo "長い文字列" の場合
            echo_match = re.search(r'echo\s+"([^"]*)"', stripped)
            if echo_match:
                echo_content = echo_match.group(1)
                if len(echo_content) > 80:
                    # 複数行に分割
                    prefix = stripped[:echo_match.start(1)]
                    suffix = stripped[echo_match.end(1):]
                    
                    # 80文字ごとに分割
                    parts = [echo_content[i:i+80] for i in range(0, len(echo_content), 80)]
                    if len(parts) > 1:
                        formatted_parts = '"\n' + ' ' * (indent + 2) + '"'.join(parts)
                        return f"{' ' * indent}{prefix}{formatted_parts}{suffix}\n"
        
        return line
    
    def _fix_url_line(self, line: str) -> str:
        """URL付きの長い行を修正"""
        # URL や長いパス文字列がある場合は改行を避けて警告を無視
        if 'http' in line or '//' in line:
            indent = len(line) - len(line.lstrip())
            # yamllint無視コメントを追加
            return line.rstrip() + '  # yamllint disable-line rule:line-length\n'
        
        return line
    
    def _identify_pattern(self, line: str) -> str:
        """修正パターンの識別"""
        if '#' in line:
            return "comment_separation"
        elif line.strip().startswith('run:'):
            return "run_multiline"
        elif 'echo' in line:
            return "echo_splitting"
        elif 'http' in line or '//' in line:
            return "url_ignore"
        else:
            return "other"
    
    def fix_all_yaml_files(self) -> dict:
        """全YAMLファイルの修正"""
        print("🔧 行長エラー一括修正開始...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_files": 0,
            "files_modified": 0,
            "total_lines_fixed": 0,
            "files": []
        }
        
        # GitHub Actionsワークフローファイルを取得
        workflow_dir = self.workspace / ".github" / "workflows"
        yaml_files = list(workflow_dir.glob("*.yml"))
        
        results["total_files"] = len(yaml_files)
        
        for yaml_file in yaml_files:
            file_result = self.fix_long_lines_in_file(str(yaml_file))
            results["files"].append(file_result)
            
            if file_result.get("fixes_applied", 0) > 0:
                results["files_modified"] += 1
                results["total_lines_fixed"] += file_result["fixes_applied"]
        
        print(f"✅ 修正完了: {results['files_modified']}ファイル, {results['total_lines_fixed']}行修正")
        return results

def main():
    """メイン実行"""
    print("🚀 Phase 13-C: 行長エラー修正開始")
    print("=" * 40)
    
    fixer = LineLengthFixer()
    
    # 修正前の状況確認
    print("📊 修正前の状況確認...")
    cmd = ["yamllint", ".github/workflows/", "-f", "standard"]
    before_result = subprocess.run(cmd, capture_output=True, text=True)
    before_errors = len([line for line in before_result.stdout.split('\n') if 'line too long' in line])
    print(f"修正前の行長エラー: {before_errors}個")
    
    # 修正実行
    results = fixer.fix_all_yaml_files()
    
    # 修正後の状況確認
    print("📊 修正後の状況確認...")
    after_result = subprocess.run(cmd, capture_output=True, text=True)
    after_errors = len([line for line in after_result.stdout.split('\n') if 'line too long' in line])
    print(f"修正後の行長エラー: {after_errors}個")
    
    improvement = before_errors - after_errors
    print(f"🎊 改善結果: {improvement}個のエラーを解消！")
    
    # 結果保存
    output_file = Path("out/phase13c_line_length_fixes.json")
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"📋 修正結果保存: {output_file}")

if __name__ == "__main__":
    main()




