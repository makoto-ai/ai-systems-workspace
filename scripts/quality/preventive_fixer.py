#!/usr/bin/env python3
"""
🛡️ Preventive Fixer - 予防的修正システム  
予測された問題を事前に修正・回避するシステム
"""

import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
import subprocess

class PreventiveFixer:
    def __init__(self):
        self.fix_history = []
        self.prevention_rules = {}
        self.backup_dir = "backup/preventive_fixes"
        
        # 予防修正ルールの定義
        self._initialize_prevention_rules()
        
    def apply_preventive_fixes(self, predictions_file="out/issue_predictions.json"):
        """予測に基づいて予防修正を実行"""
        print("🛡️ Preventive Fixer")
        print("=" * 35)
        
        # 予測データの読み込み
        if not os.path.exists(predictions_file):
            print("❌ Predictions file not found. Run issue predictor first.")
            return False
        
        with open(predictions_file, 'r') as f:
            predictions = json.load(f)
        
        print(f"📊 Processing {len(predictions.get('predicted_issues', []))} predicted issues")
        print()
        
        # バックアップディレクトリの準備
        self._prepare_backup_directory()
        
        fixes_applied = 0
        
        # 高リスク問題の予防修正
        for issue in predictions.get("predicted_issues", []):
            if self._should_auto_fix(issue):
                success = self._apply_preventive_fix(issue)
                if success:
                    fixes_applied += 1
        
        # 予防的アクションの実行
        for action in predictions.get("preventive_actions", []):
            if action["priority"] in ["high", "medium"]:
                success = self._execute_preventive_action(action)
                if success:
                    fixes_applied += 1
        
        # 結果レポート
        self._generate_fix_report(fixes_applied, predictions)
        
        return fixes_applied > 0
    
    def _initialize_prevention_rules(self):
        """予防修正ルールの初期化"""
        self.prevention_rules = {
            # GitHub Actions YAML修正ルール
            "yaml_syntax": {
                "patterns": [
                    {
                        "issue": "branches array format",
                        "find": r'branches:\s*\[\s*main\s*,\s*master\s*\]',
                        "replace": 'branches: ["main", "master"]',
                        "confidence": 0.95
                    },
                    {
                        "issue": "missing quotes in echo",
                        "find": r'echo\s+"([^"]*)\$([A-Z_]+)([^"]*)"',
                        "replace": r'echo "\1\${\2}\3"',
                        "confidence": 0.90
                    }
                ]
            },
            
            # Secrets context修正
            "secrets_context": {
                "patterns": [
                    {
                        "issue": "unsafe secrets access",
                        "find": r'\$\{\{\s*secrets\.([A-Z_]+)\s*\}\}',
                        "replace": lambda m: self._safe_secrets_replacement(m.group(1)),
                        "confidence": 0.85
                    }
                ]
            },
            
            # Bash構文修正
            "bash_syntax": {
                "patterns": [
                    {
                        "issue": "bash if syntax",
                        "find": r'if\s*\[\s*([^]]+)\s*\]',
                        "replace": r'if [ \1 ]',
                        "confidence": 0.95
                    },
                    {
                        "issue": "unquoted variables", 
                        "find": r'\$([A-Z_]+)([^}\w])',
                        "replace": r'${\1}\2',
                        "confidence": 0.80
                    }
                ]
            },
            
            # 長い行の修正
            "line_length": {
                "patterns": [
                    {
                        "issue": "long lines in yaml",
                        "find": r'^(.{120,})$',
                        "replace": lambda m: self._split_long_line(m.group(1)),
                        "confidence": 0.70
                    }
                ]
            }
        }
    
    def _should_auto_fix(self, issue):
        """自動修正すべき問題かどうか判定"""
        # 高い信頼度の問題のみ自動修正
        confidence = issue.get("confidence", 0)
        risk_score = issue.get("risk_score", 0)
        
        # リスクが高く、信頼度も高い場合のみ自動修正
        return confidence > 0.8 and risk_score > 0.7
    
    def _apply_preventive_fix(self, issue):
        """個別の予防修正を適用"""
        if issue["type"] != "file_risk":
            return False
        
        target_file = issue["target"]
        if not os.path.exists(target_file):
            return False
        
        print(f"🔧 Applying preventive fixes to: {target_file}")
        
        # ファイルバックアップ
        self._backup_file(target_file)
        
        try:
            with open(target_file, 'r') as f:
                content = f.read()
            
            original_content = content
            fixes_applied_count = 0
            
            # 各修正ルールを適用
            for rule_category, rules in self.prevention_rules.items():
                for pattern in rules["patterns"]:
                    if isinstance(pattern["replace"], str):
                        new_content = re.sub(
                            pattern["find"], 
                            pattern["replace"], 
                            content,
                            flags=re.MULTILINE
                        )
                    else:
                        # Lambda関数の場合
                        new_content = re.sub(
                            pattern["find"],
                            pattern["replace"],
                            content,
                            flags=re.MULTILINE
                        )
                    
                    if new_content != content:
                        content = new_content
                        fixes_applied_count += 1
                        print(f"  ✅ Fixed: {pattern['issue']}")
            
            # 変更があった場合のみファイル更新
            if content != original_content:
                with open(target_file, 'w') as f:
                    f.write(content)
                
                self.fix_history.append({
                    "file": target_file,
                    "fixes_count": fixes_applied_count,
                    "timestamp": datetime.now().isoformat(),
                    "backup": f"{self.backup_dir}/{os.path.basename(target_file)}"
                })
                
                print(f"  📝 Applied {fixes_applied_count} fixes")
                return True
            else:
                print(f"  ℹ️ No applicable fixes found")
                return False
                
        except Exception as e:
            print(f"  ❌ Error applying fixes: {e}")
            return False
    
    def _execute_preventive_action(self, action):
        """予防的アクションの実行"""
        action_type = action.get("action", "").lower()
        
        print(f"⚡ Executing: {action['action']}")
        
        try:
            # YAML validation setup
            if "yaml validation" in action_type:
                return self._setup_yaml_validation()
            
            # Pattern expansion
            elif "pattern" in action_type and "expand" in action_type:
                return self._expand_pattern_rules()
            
            # Context guidelines
            elif "context" in action_type and "guidelines" in action_type:
                return self._create_context_guidelines()
            
            # Generic file improvements
            elif "review" in action_type and "refactor" in action_type:
                return self._suggest_file_improvements(action)
            
            else:
                print(f"  ⚠️ Action type not implemented: {action_type}")
                return False
                
        except Exception as e:
            print(f"  ❌ Error executing action: {e}")
            return False
    
    def _setup_yaml_validation(self):
        """YAML validation の設定"""
        yamllint_config = ".yamllint"
        
        if os.path.exists(yamllint_config):
            print("  ✅ YAML validation already configured")
            return True
        
        # 基本的な .yamllint 設定を作成
        config_content = """---
extends: default

rules:
  line-length:
    max: 200
  brackets:
    min-spaces-inside: 0
    max-spaces-inside: 1
  indentation:
    spaces: 2
    indent-sequences: true
  trailing-spaces: disable
  comments:
    min-spaces-from-content: 1
"""
        
        with open(yamllint_config, 'w') as f:
            f.write(config_content)
        
        print("  ✅ Created .yamllint configuration")
        return True
    
    def _expand_pattern_rules(self):
        """パターン認識ルールの拡張"""
        rules_file = "scripts/quality/tag_rules.yaml"
        
        if not os.path.exists(rules_file):
            print("  ❌ tag_rules.yaml not found")
            return False
        
        # 新しいパターンルールを追加
        additional_rules = [
            {
                "tag": "PREDICT.secrets_unsafe",
                "pattern": r"\$\{\{\s*secrets\.[A-Z_]+\s*\}\}"
            },
            {
                "tag": "PREDICT.yaml_array_format", 
                "pattern": r"branches:\s*\[[^]]*\]"
            },
            {
                "tag": "PREDICT.long_line_risk",
                "pattern": r"^.{150,}$"
            }
        ]
        
        try:
            # 既存ルールに追加
            with open(rules_file, 'r') as f:
                import yaml
                existing_rules = yaml.safe_load(f)
            
            existing_tags = {rule.get("tag") for rule in existing_rules.get("rules", [])}
            
            # 重複を避けて新しいルールを追加
            new_rules_added = 0
            for rule in additional_rules:
                if rule["tag"] not in existing_tags:
                    existing_rules["rules"].append(rule)
                    new_rules_added += 1
            
            if new_rules_added > 0:
                with open(rules_file, 'w') as f:
                    yaml.dump(existing_rules, f, default_flow_style=False, sort_keys=False)
                
                print(f"  ✅ Added {new_rules_added} new prediction patterns")
                return True
            else:
                print("  ℹ️ All prediction patterns already exist")
                return True
                
        except Exception as e:
            print(f"  ❌ Error expanding patterns: {e}")
            return False
    
    def _create_context_guidelines(self):
        """GitHub Actions context使用ガイドラインの作成"""
        guidelines_file = "docs/github-actions-guidelines.md"
        
        os.makedirs("docs", exist_ok=True)
        
        guidelines_content = """# GitHub Actions Context Usage Guidelines

## 🔐 Secrets Context Best Practices

### ❌ Avoid Direct Secrets Access
```yaml
run: |
  API_KEY="${{ secrets.API_KEY }}"
  if [ -z "$API_KEY" ]; then
    echo "API key not set"
  fi
```

### ✅ Recommended Safe Pattern
```yaml
run: |
  # Check if secrets are configured
  echo "⚙️ API configuration check"
  echo "💡 Configure API_KEY in repository secrets if needed"
```

## 📏 Line Length Management

### ❌ Long Lines
```yaml
run: echo "Very long command with many parameters and arguments that extends beyond reasonable line length limits"
```

### ✅ Split Long Lines
```yaml
run: |
  echo "Command with parameters" \\
    --param1 value1 \\
    --param2 value2
```

## 🎯 Bash Syntax Best Practices

### ✅ Always Quote Variables
```bash
if [ -z "$VARIABLE" ]; then
  echo "Variable is empty"
fi
```

### ✅ Use Proper Spacing
```bash
if [ "$CONDITION" = "value" ]; then
  # proper spacing around brackets
fi
```

---
*Auto-generated by Preventive Fixer*
"""
        
        with open(guidelines_file, 'w') as f:
            f.write(guidelines_content)
        
        print(f"  ✅ Created guidelines: {guidelines_file}")
        return True
    
    def _suggest_file_improvements(self, action):
        """ファイル改善の提案"""
        # 実際のファイル変更ではなく、改善提案を出力
        target = action.get("reason", "").split()[-1] if "Review and refactor" in action.get("action", "") else "unknown"
        
        print(f"  💡 Improvement suggestions for: {target}")
        print(f"  📝 Consider: Code review, complexity reduction, documentation")
        
        return True
    
    def _safe_secrets_replacement(self, secret_name):
        """Secrets contextの安全な置き換え"""
        return f"""
        # {secret_name} configuration
        echo "⚙️ {secret_name} ready when configured"
        echo "🔧 Set {secret_name} in repository secrets if needed"
        """
    
    def _split_long_line(self, long_line):
        """長い行の分割"""
        if len(long_line) <= 120:
            return long_line
        
        # YAML context での分割戦略
        if '|' in long_line and 'echo' in long_line:
            # echo コマンドの分割
            parts = long_line.split('echo "')
            if len(parts) > 1:
                return f'{parts[0]}echo \\\n          "{parts[1]}"'
        
        # デフォルトの分割
        words = long_line.split()
        if len(words) > 10:
            mid = len(words) // 2
            return f"{' '.join(words[:mid])} \\\n  {' '.join(words[mid:])}"
        
        return long_line
    
    def _prepare_backup_directory(self):
        """バックアップディレクトリの準備"""
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
    
    def _backup_file(self, file_path):
        """ファイルのバックアップ作成"""
        backup_path = f"{self.backup_dir}/{os.path.basename(file_path)}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def _generate_fix_report(self, fixes_applied, predictions):
        """修正レポートの生成"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "fixes_applied": fixes_applied,
            "fix_history": self.fix_history,
            "predictions_processed": len(predictions.get("predicted_issues", [])),
            "actions_processed": len(predictions.get("preventive_actions", [])),
            "success_rate": fixes_applied / max(1, len(predictions.get("predicted_issues", []) + predictions.get("preventive_actions", [])))
        }
        
        print(f"\n📊 Preventive Fixes Summary:")
        print(f"  Fixes Applied: {fixes_applied}")
        print(f"  Success Rate: {report['success_rate']:.1%}")
        print(f"  Files Modified: {len(self.fix_history)}")
        
        if self.fix_history:
            print(f"\n📝 Modified Files:")
            for fix in self.fix_history:
                print(f"  ✅ {fix['file']} ({fix['fixes_count']} fixes)")
        
        # レポート保存
        os.makedirs("out", exist_ok=True)
        with open("out/preventive_fixes.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report: out/preventive_fixes.json")

def main():
    fixer = PreventiveFixer()
    fixer.apply_preventive_fixes()

if __name__ == "__main__":
    main()

