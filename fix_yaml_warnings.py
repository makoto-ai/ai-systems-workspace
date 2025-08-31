#!/usr/bin/env python3
import os
import re
import sys

def fix_yaml_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    for i, line in enumerate(lines):
        # Remove trailing spaces
        line = line.rstrip() + '\n'
        
        # Fix bracket spacing: [ main ] -> [main]
        line = re.sub(r'\[\s+([^\]]+)\s+\]', r'[\1]', line)
        
        # Fix comment spacing (add space after #)
        line = re.sub(r'#([^ \n])', r'# \1', line)
        
        fixed_lines.append(line)
    
    # Fix indentation for GitHub Actions (steps should be indented 4 from jobs level)
    final_lines = []
    in_job = False
    job_indent = 0
    
    for line in fixed_lines:
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)
        
        # Detect job blocks
        if re.match(r'^\s*[\w-]+:\s*$', line) and current_indent <= 2:
            in_job = True
            job_indent = current_indent
        elif line.strip() == '' or line.startswith('#'):
            pass  # Skip empty lines and comments
        elif current_indent <= job_indent and stripped and in_job:
            in_job = False
        
        # Fix steps indentation in jobs
        if in_job and stripped.startswith('- name:'):
            if current_indent != job_indent + 4:
                line = ' ' * (job_indent + 4) + stripped
        elif in_job and stripped.startswith('uses:') or stripped.startswith('run:') or stripped.startswith('with:') or stripped.startswith('env:') or stripped.startswith('if:'):
            if current_indent != job_indent + 6:
                line = ' ' * (job_indent + 6) + stripped
        
        final_lines.append(line)
    
    # Ensure file ends with newline
    if final_lines and not final_lines[-1].endswith('\n'):
        final_lines[-1] += '\n'
    
    with open(filepath, 'w') as f:
        f.writelines(final_lines)
    
    print(f"Fixed: {filepath}")

# Fix all workflow files
for file in os.listdir('.github/workflows/'):
    if file.endswith('.yml'):
        fix_yaml_file(os.path.join('.github/workflows/', file))

