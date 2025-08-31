#!/usr/bin/env python3
"""
GitHub Actions環境変数の引用符を修正
$GITHUB_ENV, $GITHUB_OUTPUT などを "$GITHUB_ENV" に修正
"""
import re
from pathlib import Path

def fix_github_env_quotes(file_path):
    """GitHub環境変数の引用符を修正"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # パターン: >> $GITHUB_ENV → >> "$GITHUB_ENV"
    content = re.sub(r'>> \$GITHUB_ENV\b', r'>> "$GITHUB_ENV"', content)
    
    # パターン: >> $GITHUB_OUTPUT → >> "$GITHUB_OUTPUT"
    content = re.sub(r'>> \$GITHUB_OUTPUT\b', r'>> "$GITHUB_OUTPUT"', content)
    
    # パターン: >> $GITHUB_STEP_SUMMARY → >> "$GITHUB_STEP_SUMMARY"
    content = re.sub(r'>> \$GITHUB_STEP_SUMMARY\b', r'>> "$GITHUB_STEP_SUMMARY"', content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    workflows_dir = Path(".github/workflows")
    fixed_count = 0
    
    for yml_file in workflows_dir.glob("*.yml"):
        print(f"🔧 チェック中: {yml_file.name}")
        if fix_github_env_quotes(yml_file):
            print(f"  ✅ 修正済み")
            fixed_count += 1
        else:
            print(f"  ➖ 修正不要")
    
    print(f"\n🎉 完了: {fixed_count}ファイルを修正")

if __name__ == "__main__":
    main()
