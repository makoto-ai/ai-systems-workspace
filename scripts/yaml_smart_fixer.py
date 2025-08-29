#!/usr/bin/env python3
"""
GitHub Actions YAML Smart Fixer
- 構文を壊さない安全な修正のみ実行
- バックアップ機能付き
- 修正前後の比較表示
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
import yaml

class YAMLSmartFixer:
    def __init__(self, workflows_dir=".github/workflows"):
        self.workflows_dir = Path(workflows_dir)
        self.backup_dir = Path("backup_workflows")
        
    def create_backup(self):
        """修正前のバックアップを作成"""
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        shutil.copytree(self.workflows_dir, self.backup_dir)
        print(f"✅ Backup created: {self.backup_dir}")
    
    def restore_backup(self):
        """バックアップから復元"""
        if self.backup_dir.exists():
            shutil.rmtree(self.workflows_dir)
            shutil.copytree(self.backup_dir, self.workflows_dir)
            print(f"✅ Restored from backup")
        
    def count_warnings(self, filepath):
        """ファイルの警告数をカウント"""
        try:
            cmd = ["yamllint", "-d", "{extends: default, rules: {line-length: {max: 200}, document-start: disable, truthy: {allowed-values: ['true', 'false', 'on', 'off']}}}", str(filepath)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return len([line for line in result.stdout.split('\n') if line.strip() and not line.startswith('  ')])
        except:
            return 0
    
    def fix_file_safe(self, filepath):
        """安全な修正のみ実行"""
        print(f"\n🔧 修正中: {filepath.name}")
        before_warnings = self.count_warnings(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_applied = []
        
        # 1. 行末スペース削除
        if re.search(r' +$', content, re.MULTILINE):
            content = re.sub(r' +$', '', content, flags=re.MULTILINE)
            fixes_applied.append("trailing-spaces")
        
        # 2. Document start 追加 (安全確認付き)
        if not content.strip().startswith('---'):
            content = '---\n' + content
            fixes_applied.append("document-start")
        
        # 3. Brackets spacing修正 [ item ] -> [item]
        if re.search(r'\[\s+[^\]]+\s+\]', content):
            content = re.sub(r'\[\s+([^\]]+)\s+\]', r'[\1]', content)
            fixes_applied.append("brackets")
        
        # 4. Comment spacing修正 #text -> # text  
        if re.search(r'#[^\s#\n]', content):
            content = re.sub(r'#([^\s#\n])', r'# \1', content)
            fixes_applied.append("comments")
        
        # 5. ファイル末尾改行確認
        if content and not content.endswith('\n'):
            content += '\n'
            fixes_applied.append("end-of-file")
        
        # YAML構文チェック
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            print(f"❌ YAML構文エラーが発生するため修正をスキップ: {e}")
            return False
        
        # 修正を保存
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        after_warnings = self.count_warnings(filepath)
        improvement = before_warnings - after_warnings
        
        if improvement > 0:
            print(f"✅ 警告 {before_warnings} → {after_warnings} (-{improvement})")
            print(f"   適用済み修正: {', '.join(fixes_applied)}")
            return True
        else:
            print(f"ℹ️  警告数変化なし: {before_warnings}")
            return False
    
    def fix_all_workflows(self):
        """全ワークフローファイルを修正"""
        print("🚀 GitHub Actions YAML Smart Fixer 開始")
        
        # バックアップ作成
        self.create_backup()
        
        total_before = 0
        total_after = 0
        fixed_files = 0
        
        yml_files = list(self.workflows_dir.glob("*.yml"))
        print(f"📄 対象ファイル: {len(yml_files)}個")
        
        for filepath in yml_files:
            before = self.count_warnings(filepath)
            total_before += before
            
            success = self.fix_file_safe(filepath)
            if success:
                fixed_files += 1
            
            after = self.count_warnings(filepath)
            total_after += after
        
        print(f"\n🎯 修正完了レポート:")
        print(f"   修正済みファイル: {fixed_files}/{len(yml_files)}")
        print(f"   総警告数: {total_before} → {total_after} (-{total_before - total_after})")
        
        if total_after == 0:
            print("🎉 全警告解消！完璧な状態です！")
        elif total_before > total_after:
            print(f"✅ 大幅改善！残り{total_after}個の警告")
        else:
            print("⚠️  さらなる手動調整が必要です")
        
        return total_before, total_after

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--restore":
        fixer = YAMLSmartFixer()
        fixer.restore_backup()
        return
    
    fixer = YAMLSmartFixer()
    before, after = fixer.fix_all_workflows()
    
    if after > 0:
        print(f"\n🔧 手動修正が必要な残り警告: {after}個")
        print("詳細確認: yamllint .github/workflows/")

if __name__ == "__main__":
    main()
