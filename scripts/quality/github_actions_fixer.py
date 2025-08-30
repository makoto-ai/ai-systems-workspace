#!/usr/bin/env python3
"""
GitHub Actions Specific Fixer - IDE/Schema警告の完全解消
- Bash構文エラー修正
- GitHub Actions Schema準拠
- VS Code YAML拡張警告解消
"""
import re
from pathlib import Path

class GitHubActionsFixer:
    def __init__(self):
        self.workflows_dir = Path(".github/workflows")
        
    def fix_bash_conditionals(self, content):
        """Bash条件文を修正"""
        fixes_applied = []
        
        # if [-f → if [ -f  (スペース追加)
        if re.search(r'if \[-', content):
            content = re.sub(r'if \[-', 'if [ -', content)
            fixes_applied.append("bash_conditional_spacing")
        
        # if [$var → if [ $var  (スペース追加)
        if re.search(r'if \[\$', content):
            content = re.sub(r'if \[\$', 'if [ $', content)
            fixes_applied.append("bash_variable_spacing")
        
        # 条件文の終端 ]; → ]; の修正
        content = re.sub(r'\]; then', ' ]; then', content)
        
        return content, fixes_applied
    
    def fix_github_actions_schema(self, content):
        """GitHub Actions Schema問題を修正"""
        fixes_applied = []
        
        # branches: [main, master] → branches: ["main", "master"]
        if 'branches: [main, master]' in content:
            content = content.replace('branches: [main, master]', 'branches: ["main", "master"]')
            fixes_applied.append("branches_quoting")
        
        return content, fixes_applied
    
    def fix_multiline_strings(self, content):
        """多行文字列の修正"""
        fixes_applied = []
        
        # |+ → | (不適切な文字列指定子)
        if '|+' in content:
            content = content.replace('|+', '|')
            fixes_applied.append("multiline_string_operator")
        
        return content, fixes_applied
    
    def fix_file(self, file_path):
        """単一ファイルを修正"""
        print(f"🔧 修正中: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        all_fixes = []
        
        # Bash条件文修正
        content, bash_fixes = self.fix_bash_conditionals(content)
        all_fixes.extend(bash_fixes)
        
        # GitHub Actions Schema修正
        content, schema_fixes = self.fix_github_actions_schema(content)
        all_fixes.extend(schema_fixes)
        
        # 多行文字列修正
        content, string_fixes = self.fix_multiline_strings(content)
        all_fixes.extend(string_fixes)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ 修正適用: {', '.join(all_fixes) if all_fixes else 'formatting'}")
            return True
        else:
            print(f"  ➖ 修正不要")
            return False
    
    def run_github_actions_fix(self):
        """全GitHub Actionsファイルを修正"""
        print("🚀 GitHub Actions IDE警告修正開始")
        print("=" * 45)
        
        target_files = [
            "canary-auto-promote.yml",
            "deploy.yml", 
            "model-experiment.yml",
            "pr-quality-check.yml",
            "staged-promotion.yml",
            "weekly-golden.yml"
        ]
        
        fixed_files = 0
        
        for filename in target_files:
            file_path = self.workflows_dir / filename
            if file_path.exists():
                success = self.fix_file(file_path)
                if success:
                    fixed_files += 1
            else:
                print(f"⚠️  {filename} が見つかりません")
        
        print("=" * 45)
        print(f"🎉 GitHub Actions修正完了!")
        print(f"   修正ファイル: {fixed_files}/{len(target_files)}")
        
        return fixed_files

def main():
    fixer = GitHubActionsFixer()
    fixed_count = fixer.run_github_actions_fix()
    
    if fixed_count > 0:
        print(f"\n✅ {fixed_count}個のファイルを修正しました")
        print("🔍 IDE警告を再確認してください")
    else:
        print("\n🤔 修正対象が見つかりませんでした")

if __name__ == "__main__":
    main()
