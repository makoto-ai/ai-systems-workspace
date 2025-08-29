#!/usr/bin/env python3
"""
Normalization Rules Suggestion Tool
正規化ルール候補自動生成システム
"""

import json
import yaml
import argparse
import unicodedata
import re
from pathlib import Path
from typing import Dict, List, Set, Any
from collections import defaultdict

class NormRuleSuggester:
    """正規化ルール提案システム"""
    
    def __init__(self):
        # 基本的な記号統一ルール
        self.punctuation_rules = {
            # 括弧類
            "［": "[", "【": "[", "（": "(", "〔": "[",
            "］": "]", "】": "]", "）": ")", "〕": "]",
            # 句読点
            "，": ",", "．": ".", "；": ";", "：": ":",
            "？": "?", "！": "!", "〜": "~", "～": "~",
            # 長音・ダッシュ
            "ー": "-", "―": "-", "‐": "-", "–": "-", "—": "-",
            # 引用符
            """: '"', """: '"', "'": "'", "'": "'",
            "「": '"', "」": '"', "『": '"', "』": '"'
        }
        
        # 単位・表記ゆれ
        self.unit_rules = {
            "％": "%", "㌫": "%", "パーセント": "%",
            "ミリ秒": "ms", "ミリセカンド": "ms", "msec": "ms",
            "秒": "s", "セカンド": "s", "sec": "s",
            "分": "min", "分間": "min", "minute": "min",
            "時間": "h", "時": "h", "hour": "h"
        }
        
        # ドメイン固有同義語
        self.domain_synonyms = {
            "導入": ["実装", "インストール", "セットアップ"],
            "合格率": ["パス率", "成功率", "通過率"],
            "判定": ["評価", "チェック", "検証"],
            "辞書": ["正規化ルール", "ルールセット", "マッピング"],
            "可視化": ["表示", "描画", "レンダリング"],
            "監視": ["モニタリング", "観測", "追跡"],
            "分析": ["解析", "調査", "検証"],
            "ダッシュボード": ["管理画面", "コントロールパネル", "画面"],
            "メトリクス": ["指標", "測定値", "数値"],
            "システム": ["仕組み", "機構", "構造"],
            "ツール": ["道具", "手段", "機能"],
            "構築": ["作成", "建設", "設置"]
        }
    
    def analyze_failures(self, failures_data: Dict[str, Any]) -> Dict[str, Any]:
        """失敗データを分析してルール候補を生成"""
        failures = failures_data.get("new_failures", [])
        
        # 各種パターンを収集
        punctuation_issues = []
        number_issues = []
        similar_pairs = []
        synonym_candidates = defaultdict(set)
        
        for failure in failures:
            reference = failure.get("reference", "")
            prediction = failure.get("prediction", "")
            diff_analysis = failure.get("diff_analysis", {})
            
            # 記号・句読点の問題を検出
            punct_issues = self._detect_punctuation_issues(reference, prediction)
            punctuation_issues.extend(punct_issues)
            
            # 数値の問題を検出
            num_issues = self._detect_number_issues(reference, prediction)
            number_issues.extend(num_issues)
            
            # 類似ペアから同義語候補を抽出
            pairs = diff_analysis.get("similar_pairs", [])
            for pair in pairs:
                if pair.get("similarity", 0) > 0.7:
                    missing = pair["missing"]
                    extra = pair["extra"]
                    similar_pairs.append(pair)
                    
                    # 同義語候補として登録
                    if len(missing) > 2 and len(extra) > 2:  # 短すぎる語は除外
                        synonym_candidates[missing].add(extra)
                        synonym_candidates[extra].add(missing)
        
        return {
            "punctuation_issues": punctuation_issues,
            "number_issues": number_issues,
            "similar_pairs": similar_pairs,
            "synonym_candidates": dict(synonym_candidates)
        }
    
    def _detect_punctuation_issues(self, reference: str, prediction: str) -> List[Dict[str, str]]:
        """記号・句読点の問題を検出"""
        issues = []
        
        # 全角/半角の違いを検出
        ref_chars = set(reference)
        pred_chars = set(prediction)
        
        for char in ref_chars | pred_chars:
            # NFKC正規化で変化するかチェック
            normalized = unicodedata.normalize('NFKC', char)
            if char != normalized:
                issues.append({
                    "type": "nfkc_normalization",
                    "original": char,
                    "normalized": normalized,
                    "context": f"'{char}' → '{normalized}'"
                })
        
        return issues
    
    def _detect_number_issues(self, reference: str, prediction: str) -> List[Dict[str, Any]]:
        """数値の問題を検出"""
        issues = []
        
        # 数値パターンを抽出
        ref_numbers = re.findall(r'\d+(?:\.\d+)?', reference)
        pred_numbers = re.findall(r'\d+(?:\.\d+)?', prediction)
        
        # 数値の近似チェック
        for ref_num_str in ref_numbers:
            ref_num = float(ref_num_str)
            for pred_num_str in pred_numbers:
                pred_num = float(pred_num_str)
                
                # 絶対誤差・相対誤差チェック
                abs_diff = abs(ref_num - pred_num)
                rel_diff = abs_diff / max(abs(ref_num), abs(pred_num), 1e-10)
                
                if abs_diff <= 1 or rel_diff <= 0.05:  # ±1 or ±5%
                    issues.append({
                        "type": "number_approximation",
                        "reference_value": ref_num,
                        "prediction_value": pred_num,
                        "abs_diff": abs_diff,
                        "rel_diff": rel_diff
                    })
        
        return issues
    
    def generate_rules(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """分析結果から正規化ルールを生成"""
        rules = {
            "normalization": {
                "nfkc_enabled": True,
                "casefold_enabled": True,
                "space_compression": True,
                "punctuation_mapping": self.punctuation_rules.copy(),
                "unit_mapping": self.unit_rules.copy()
            },
            "similarity": {
                "number_tolerance": {
                    "absolute_threshold": 1.0,
                    "relative_threshold": 0.05
                },
                "token_similarity_threshold": 0.92
            },
            "synonyms": self.domain_synonyms.copy()
        }
        
        # 分析結果から追加ルールを生成
        
        # 記号問題から追加マッピング
        for issue in analysis.get("punctuation_issues", []):
            if issue["type"] == "nfkc_normalization":
                rules["normalization"]["punctuation_mapping"][issue["original"]] = issue["normalized"]
        
        # 類似ペアから同義語追加
        synonym_candidates = analysis.get("synonym_candidates", {})
        for key, values in synonym_candidates.items():
            if len(values) > 0:
                # 既存の同義語グループに追加または新規作成
                found_group = False
                for existing_key, existing_values in rules["synonyms"].items():
                    if key in existing_values or key == existing_key:
                        existing_values.extend(values)
                        found_group = True
                        break
                
                if not found_group:
                    rules["synonyms"][key] = list(values)
        
        return rules
    
    def save_rules(self, rules: Dict[str, Any], output_path: str):
        """ルールをYAMLファイルに保存"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # YAMLコメント付きで保存
        yaml_content = f"""# Golden Test Normalization Rules
# 自動生成日時: {datetime.now().isoformat()}

# 基本正規化設定
normalization:
  nfkc_enabled: {rules['normalization']['nfkc_enabled']}
  casefold_enabled: {rules['normalization']['casefold_enabled']}
  space_compression: {rules['normalization']['space_compression']}
  
  # 記号・句読点統一
  punctuation_mapping:
"""
        
        for original, normalized in rules['normalization']['punctuation_mapping'].items():
            yaml_content += f'    "{original}": "{normalized}"\n'
        
        yaml_content += f"""
  # 単位・表記統一
  unit_mapping:
"""
        
        for original, normalized in rules['normalization']['unit_mapping'].items():
            yaml_content += f'    "{original}": "{normalized}"\n'
        
        yaml_content += f"""

# 類似度判定設定
similarity:
  number_tolerance:
    absolute_threshold: {rules['similarity']['number_tolerance']['absolute_threshold']}
    relative_threshold: {rules['similarity']['number_tolerance']['relative_threshold']}
  token_similarity_threshold: {rules['similarity']['token_similarity_threshold']}

# 同義語グループ
synonyms:
"""
        
        for key, values in rules['synonyms'].items():
            yaml_content += f'  "{key}":\n'
            for value in values:
                yaml_content += f'    - "{value}"\n'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        print(f"✅ 正規化ルール候補を保存: {output_file}")

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Normalization Rules Suggestion Tool")
    parser.add_argument("--in", dest="input_file", type=str, required=True,
                       help="入力ファイル（new_fails.json）")
    parser.add_argument("--out", type=str, required=True,
                       help="出力ファイル（norm_rule_candidates.yaml）")
    
    args = parser.parse_args()
    
    try:
        # 入力データ読み込み
        with open(args.input_file, 'r', encoding='utf-8') as f:
            failures_data = json.load(f)
        
        print(f"📊 新規失敗 {failures_data.get('total_new_failures', 0)} 件を分析中...")
        
        # ルール提案システム初期化
        suggester = NormRuleSuggester()
        
        # 失敗データ分析
        analysis = suggester.analyze_failures(failures_data)
        
        print(f"🔍 検出された問題:")
        print(f"  - 記号問題: {len(analysis['punctuation_issues'])}件")
        print(f"  - 数値問題: {len(analysis['number_issues'])}件")
        print(f"  - 類似ペア: {len(analysis['similar_pairs'])}件")
        print(f"  - 同義語候補: {len(analysis['synonym_candidates'])}グループ")
        
        # ルール生成
        rules = suggester.generate_rules(analysis)
        
        # ルール保存
        suggester.save_rules(rules, args.out)
        
        print(f"✅ 正規化ルール候補生成完了")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    import sys
    from datetime import datetime
    
    success = main()
    sys.exit(0 if success else 1)
