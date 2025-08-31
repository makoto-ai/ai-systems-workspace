#!/usr/bin/env python3
import re
import sys
from pathlib import Path

def fix_step_names(file_path):
    """ステップ名に引用符を追加"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # ステップ名のパターン: "    - name: " で始まり、引用符がない
    pattern = r'^(    - name: )([^"\'\n]+)$'
    replacement = r'\1"\2"'
    
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        return True
    return False

# すべてのワークフローファイルを処理
workflows_dir = Path('.github/workflows')
fixed_count = 0
for yml_file in workflows_dir.glob('*.yml'):
    if yml_file.name.endswith('.disabled'):
        continue
    if fix_step_names(yml_file):
        fixed_count += 1
        print(f"✅ Fixed: {yml_file.name}")

print(f"\n📊 Total files fixed: {fixed_count}")
