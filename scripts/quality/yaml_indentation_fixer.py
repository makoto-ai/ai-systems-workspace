#!/usr/bin/env python3
"""
YAML Indentation Fixer - GitHub Actions用の安全なインデンテーション修正
- expected 6 but found 4 -> GitHub Actionsのsteps配下のプロパティ
- 構文安全性を最優先に修正
"""
import re
from pathlib import Path
import subprocess
import yaml

class YAMLIndentationFixer:
    def __init__(self):
        self.workflows_dir = Path(".github/workflows")
        
    def analyze_indentation_errors(self):
        """インデンテーションエラーを分析"""
        result = subprocess.run([
            'find', str(self.workflows_dir), '-name', '*.yml',
            '-exec', 'yamllint', '-d',
            '{extends: default, rules: {line-length: {max: 200}, document-start: disable, truthy: {allowed-values: ["true", "false", "on", "off"]}}}',
            '{}', ';'
        ], capture_output=True, text=True)
        
        errors = []
        for line in result.stdout.split('\n'):
            if 'wrong indentation' in line:
                errors.append(line)
        
        return errors
    
    def fix_github_actions_indentation(self):
        """GitHub Actions特有のインデンテーション問題を安全に修正"""
        print("🔧 GitHub Actions インデンテーション修正中...")
        fixed_files = 0
        
        for yml_file in self.workflows_dir.glob("*.yml"):
            print(f"  📄 処理中: {yml_file.name}")
            
            with open(yml_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            modified = False
            new_lines = []
            in_steps = False
            
            for i, line in enumerate(lines):
                original_line = line
                
                # steps: セクションの検出
                if re.match(r'^    steps:\s*$', line):
                    in_steps = True
                    new_lines.append(line)
                    continue
                
                # 別のjobセクション開始でstepsから抜ける
                if re.match(r'^  [a-zA-Z0-9_-]+:\s*$', line):
                    in_steps = False
                
                # steps内で expected 6 but found 4 パターンを修正
                if in_steps:
                    # - name: で始まる行は6スペースが正しい
                    if re.match(r'^    - name:', line):
                        line = re.sub(r'^    - name:', '      - name:', line)
                        modified = True
                    # uses:, with:, run:, env:, if: などは8スペースが正しい  
                    elif re.match(r'^    (uses|with|run|env|if|id|continue-on-error):', line):
                        line = re.sub(r'^    ', '        ', line)
                        modified = True
                    # with:配下のプロパティは10スペースが正しい
                    elif re.match(r'^      [a-zA-Z0-9_-]+:', line):
                        if i > 0 and re.search(r'with:\s*$', lines[i-1]):
                            line = re.sub(r'^      ', '          ', line)
                            modified = True
                
                new_lines.append(line)
            
            if modified:
                # YAML構文チェック
                try:
                    yaml.safe_load(''.join(new_lines))
                    with open(yml_file, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                    fixed_files += 1
                    print(f"    ✅ 修正適用")
                except yaml.YAMLError as e:
                    print(f"    ⚠️  構文エラーのためスキップ: {e}")
            else:
                print(f"    ➖ 修正不要")
        
        return fixed_files
    
    def run_safe_indentation_fix(self):
        """安全なインデンテーション修正実行"""
        print("🚀 安全なインデンテーション修正開始")
        print("="*40)
        
        # 修正前警告数
        before_warnings = len(self.analyze_indentation_errors())
        print(f"修正前インデンテーション警告: {before_warnings}件")
        
        # 修正実行
        fixed_files = self.fix_github_actions_indentation()
        
        # 修正後警告数
        after_warnings = len(self.analyze_indentation_errors())
        improvement = before_warnings - after_warnings
        
        print("="*40)
        print(f"🎉 インデンテーション修正完了!")
        print(f"   修正ファイル: {fixed_files}個")
        print(f"   インデンテーション警告: {before_warnings} → {after_warnings} (-{improvement})")
        
        # 全体警告数も確認
        total_warnings = subprocess.run([
            'find', str(self.workflows_dir), '-name', '*.yml',
            '-exec', 'yamllint', '-d',
            '{extends: default, rules: {line-length: {max: 200}, document-start: disable, truthy: {allowed-values: ["true", "false", "on", "off"]}}}',
            '{}', ';'
        ], capture_output=True, text=True)
        
        total_count = len([line for line in total_warnings.stdout.split('\n') if line.strip()])
        print(f"   全体警告数: {total_count}件")
        
        if total_count == 0:
            print("🏆 全警告完全解消！YAML品質100%達成！")
        
        return {
            'indentation_before': before_warnings,
            'indentation_after': after_warnings,
            'indentation_improvement': improvement,
            'total_warnings': total_count,
            'fixed_files': fixed_files
        }

def main():
    fixer = YAMLIndentationFixer()
    results = fixer.run_safe_indentation_fix()
    
    if results['total_warnings'] == 0:
        print("\n🎊 完全勝利！YAML品質システム完成！")

if __name__ == "__main__":
    main()
