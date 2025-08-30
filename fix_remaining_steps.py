#!/usr/bin/env python3
import re
from pathlib import Path

def fix_all_step_names(file_path):
    """すべてのステップ名に引用符を追加（絵文字含む）"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # より包括的なパターン
    pattern = r'^(      - name: )([^"\'\n]+)$'
    replacement = r'\1"\2"'
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # 4スペースインデントのパターンも
    pattern2 = r'^(    - name: )([^"\'\n]+)$'
    new_content = re.sub(pattern2, r'\1"\2"', new_content, flags=re.MULTILINE)
    
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        return True
    return False

# 特定のファイルを処理
files_to_fix = [
    '.github/workflows/deploy.yml',
    '.github/workflows/model-experiment.yml',
    '.github/workflows/realtime-quality-guard.yml',
    '.github/workflows/weekly-golden.yml'
]

for file_path in files_to_fix:
    if Path(file_path).exists():
        if fix_all_step_names(file_path):
            print(f"✅ Fixed: {file_path}")

# 再度全ファイルチェック
workflows_dir = Path('.github/workflows')
for yml_file in workflows_dir.glob('*.yml'):
    if yml_file.name.endswith('.disabled'):
        continue
    fix_all_step_names(yml_file)
