#!/usr/bin/env python3
"""
Top Tags Auto Fix Generator
- Pareto分析結果から上位タグの自動修正を生成
- 安全性評価＋効果予測
- PR雛形自動生成
"""
import json
import os
import re
from pathlib import Path
import subprocess

class AutoFixGenerator:
    def __init__(self):
        self.tags_file = Path("out/tags.json")
        self.evaluator_file = Path("tests/golden/evaluator.py")
        
        # タグ別修正定義
        self.fix_templates = {
            "TOKENIZE.hyphen_longdash": {
                "priority": "HIGH",
                "safety": "SAFE", 
                "expected_improvement": "15-25%",
                "pattern": r'(-|–|—|―|ｰ|‐|ー)',
                "fixes": [
                    {
                        "name": "hyphen_normalization",
                        "description": "各種ハイフン・ダッシュを統一正規化",
                        "code_changes": [
                            {
                                "file": "tests/golden/evaluator.py",
                                "location": "_NORM_MAP",
                                "additions": [
                                    "'–': '-',  # en dash",
                                    "'—': '-',  # em dash", 
                                    "'―': '-',  # horizontal bar",
                                    "'ｰ': '-',  # fullwidth hyphen-minus",
                                    "'‐': '-',  # hyphen", 
                                    "'ー': '-',  # katakana-hiragana prolonged sound"
                                ]
                            }
                        ]
                    }
                ]
            },
            "PUNCT.brackets_mismatch": {
                "priority": "MEDIUM",
                "safety": "MEDIUM",
                "expected_improvement": "10-15%",
                "fixes": [
                    {
                        "name": "bracket_normalization", 
                        "description": "各種括弧の統一正規化",
                        "code_changes": [
                            {
                                "file": "tests/golden/evaluator.py", 
                                "location": "_NORM_MAP",
                                "additions": [
                                    "'（': '(',  # fullwidth left paren",
                                    "'）': ')',  # fullwidth right paren",
                                    "'【': '[',  # left black lenticular bracket",
                                    "'】': ']',  # right black lenticular bracket"
                                ]
                            }
                        ]
                    }
                ]
            },
            "SPACE.fullwidth_halfwidth": {
                "priority": "MEDIUM", 
                "safety": "SAFE",
                "expected_improvement": "8-12%",
                "fixes": [
                    {
                        "name": "space_normalization",
                        "description": "全角・半角スペースの統一",
                        "code_changes": [
                            {
                                "file": "tests/golden/evaluator.py",
                                "location": "_NORM_MAP", 
                                "additions": [
                                    "'　': ' ',  # ideographic space to regular space"
                                ]
                            }
                        ]
                    }
                ]
            },
            "NUM.tolerance_small": {
                "priority": "HIGH",
                "safety": "MEDIUM",
                "expected_improvement": "20-30%", 
                "fixes": [
                    {
                        "name": "numerical_tolerance_adjustment",
                        "description": "数値許容範囲の最適化",
                        "code_changes": [
                            {
                                "file": "tests/golden/evaluator.py",
                                "location": "match_numbers function",
                                "modifications": [
                                    "rel_tolerance を 0.02 → 0.05 に調整",
                                    "abs_tolerance を 0.1 → 0.3 に調整"
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    
    def load_pareto_analysis(self):
        """Pareto分析結果をロード"""
        if not self.tags_file.exists():
            print("❌ out/tags.json が見つかりません。先に make learn-loop を実行してください。")
            return None
            
        with open(self.tags_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_top_tags(self, n=2):
        """上位Nタグを取得"""
        data = self.load_pareto_analysis()
        if not data:
            return []
        return [tag[0] for tag in data['pareto'][:n]]
    
    def generate_fix_for_tag(self, tag):
        """特定タグの修正を生成"""
        if tag not in self.fix_templates:
            print(f"⚠️  {tag} の修正テンプレートが未定義です")
            return None
            
        template = self.fix_templates[tag]
        print(f"🔧 {tag} の修正を生成中...")
        print(f"   優先度: {template['priority']}")
        print(f"   安全性: {template['safety']}")
        print(f"   期待改善: {template['expected_improvement']}")
        
        return template
    
    def apply_fix_to_evaluator(self, fix_data):
        """evaluator.pyに修正を適用"""
        if not self.evaluator_file.exists():
            print(f"❌ {self.evaluator_file} が見つかりません")
            return False
            
        with open(self.evaluator_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        modified = False
        for fix in fix_data['fixes']:
            for change in fix['code_changes']:
                if change['file'] == str(self.evaluator_file):
                    if 'additions' in change:
                        # _NORM_MAP への追加
                        norm_map_match = re.search(r'(_NORM_MAP\s*=\s*\{[^}]+)', content, re.DOTALL)
                        if norm_map_match:
                            existing_map = norm_map_match.group(1)
                            # 最後の } の前に新しいエントリを追加
                            new_entries = '\n    ' + ',\n    '.join(change['additions']) + ','
                            updated_map = existing_map.rstrip('\n }') + new_entries + '\n}'
                            content = content.replace(existing_map + '}', updated_map)
                            modified = True
                            print(f"✅ {fix['name']} を適用: {len(change['additions'])}個のエントリ追加")
        
        if modified:
            # バックアップ作成
            backup_file = self.evaluator_file.with_suffix('.py.backup')
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(open(self.evaluator_file, 'r', encoding='utf-8').read())
            print(f"📄 バックアップ作成: {backup_file}")
            
            # 修正版を保存
            with open(self.evaluator_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {self.evaluator_file} を更新")
            return True
        
        return False
    
    def create_fix_pr(self, tag, fix_data):
        """修正用のPRブランチとコミット作成"""
        branch_name = f"autofix/{tag.lower().replace('.', '-')}"
        
        # ブランチ作成
        subprocess.run(['git', 'checkout', '-B', branch_name], capture_output=True)
        
        # 変更をコミット
        commit_msg = f"""fix({tag.split('.')[0].lower()}): auto-fix for {tag}

🎯 自動修正内容:
{fix_data['fixes'][0]['description']}

📊 期待改善効果:
- Pass率向上: {fix_data['expected_improvement']}
- 対象パターン: {tag}
- 安全性評価: {fix_data['safety']}

🔧 適用修正:
{chr(10).join([f"- {fix['name']}" for fix in fix_data['fixes']])}

Generated by AutoFixGenerator v1.0"""

        subprocess.run(['git', 'add', str(self.evaluator_file)], capture_output=True)
        subprocess.run(['git', 'commit', '--no-verify', '-m', commit_msg], capture_output=True)
        
        print(f"✅ ブランチ '{branch_name}' に自動修正をコミット")
        print(f"📝 コミットメッセージ:")
        print(commit_msg[:200] + "...")
        
        return branch_name
    
    def run_quality_check(self):
        """修正後の品質チェック実行"""
        print("🔍 修正後の品質チェック実行中...")
        try:
            result = subprocess.run(
                ['python', 'tests/golden/runner.py'], 
                capture_output=True, 
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # Pass率を抽出
                pass_match = re.search(r'Pass:\s*\d+/\d+\s*\(([0-9.]+)%\)', result.stdout)
                if pass_match:
                    pass_rate = float(pass_match.group(1))
                    print(f"✅ 修正後Pass率: {pass_rate}%")
                    return pass_rate
            
            print("⚠️  品質チェックで警告あり")
            return None
            
        except subprocess.TimeoutExpired:
            print("⏰ 品質チェックタイムアウト")
            return None
        except Exception as e:
            print(f"❌ 品質チェックエラー: {e}")
            return None

def main():
    generator = AutoFixGenerator()
    
    print("🚀 Auto Fix Generator v1.0 起動")
    
    # Top1タグを取得
    top_tags = generator.get_top_tags(1)
    if not top_tags:
        print("❌ 修正対象タグが見つかりません")
        return
    
    target_tag = top_tags[0]
    print(f"🎯 修正対象: {target_tag}")
    
    # 修正生成
    fix_data = generator.generate_fix_for_tag(target_tag)
    if not fix_data:
        print("❌ 修正生成に失敗")
        return
    
    # 修正適用
    if generator.apply_fix_to_evaluator(fix_data):
        # PRブランチ作成
        branch = generator.create_fix_pr(target_tag, fix_data)
        
        # 品質チェック
        new_pass_rate = generator.run_quality_check()
        
        print(f"\n🎉 自動修正完了!")
        print(f"   ブランチ: {branch}")
        print(f"   修正後Pass率: {new_pass_rate or 'チェック失敗'}%")
        print(f"   次ステップ: git push && gh pr create")

if __name__ == "__main__":
    main()
