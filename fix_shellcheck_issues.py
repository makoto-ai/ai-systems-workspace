#!/usr/bin/env python3
import re
import sys
from pathlib import Path

def fix_sc2129_redirects(content):
    """SC2129: 複数のリダイレクトを統合"""
    # パターン: 連続するecho >> file を { echo; echo; } >> file に変換
    lines = content.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        if 'echo ' in line and '>>' in line and '"$GITHUB_OUTPUT"' in line:
            # 連続するGITHUB_OUTPUTリダイレクトを探す
            redirect_lines = [line]
            j = i + 1
            while j < len(lines) and 'echo ' in lines[j] and '>>' in lines[j] and '"$GITHUB_OUTPUT"' in lines[j]:
                redirect_lines.append(lines[j])
                j += 1
            
            if len(redirect_lines) > 1:
                # 統合形式に変換
                indent = len(line) - len(line.lstrip())
                prefix = ' ' * indent
                
                result.append(f"{prefix}{{")
                for rline in redirect_lines:
                    # echo ... >> "$GITHUB_OUTPUT" から echo ... を抽出
                    echo_part = rline.split(' >> ')[0].strip()
                    result.append(f"{prefix}  {echo_part}")
                result.append(f'{prefix}}} >> "$GITHUB_OUTPUT"')
                i = j
                continue
        
        result.append(line)
        i += 1
    
    return '\n'.join(result)

def fix_unused_variables(content):
    """SC2034: 未使用変数を修正"""
    # FILE_EXT, GATE_RESULTなどの未使用変数を削除またはコメントアウト
    content = re.sub(r'^(\s+)FILE_EXT=.*$', r'\1# FILE_EXT=... (unused)', content, flags=re.MULTILINE)
    content = re.sub(r'^(\s+)GATE_RESULT=.*$', r'\1# GATE_RESULT=... (unused)', content, flags=re.MULTILINE)
    return content

def fix_quoting_issues(content):
    """SC2086: 変数の引用符問題を修正"""
    # $var を "$var" に変換 (安全な箇所のみ)
    content = re.sub(r'echo ([^"\']*\$[A-Z_]+[^"\'\s]*)', r'echo "\1"', content)
    return content

# 対象ファイルを修正
workflows_dir = Path('.github/workflows')
for yml_file in ['pr-quality-check.yml', 'predictive-quality.yml', 'realtime-quality-guard.yml', 'staged-promotion.yml', 'weekly-golden.yml']:
    file_path = workflows_dir / yml_file
    if file_path.exists():
        with open(file_path, 'r') as f:
            content = f.read()
        
        # 各種修正を適用
        original_content = content
        content = fix_sc2129_redirects(content)
        content = fix_unused_variables(content)
        content = fix_quoting_issues(content)
        
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✅ Fixed: {yml_file}")

print("\n📊 Batch fixes completed!")
