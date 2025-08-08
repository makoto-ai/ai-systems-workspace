#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube原稿構成検証スクリプト
YouTube原稿が構成テンプレートに準拠しているかを検証する
"""

import json
import sys
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/structure_validation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class StructureValidator:
    """YouTube原稿構成検証クラス"""
    
    def __init__(self):
        self.validation_results = []
        self.required_sections = [
            "導入",
            "本論",
            "結論"
        ]
        self.optional_sections = [
            "アウトライン",
            "まとめ",
            "次の動画"
        ]
        
    def extract_sections(self, script_text: str) -> Dict[str, str]:
        """原稿からセクションを抽出"""
        sections = {}
        
        # セクション区切りパターン（# や ## で始まる行）
        section_pattern = r'^#{1,3}\s*(.+)$'
        
        lines = script_text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            match = re.match(section_pattern, line)
            if match:
                # 前のセクションを保存
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # 新しいセクション開始
                current_section = match.group(1).strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # 最後のセクションを保存
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def validate_section_length(self, section_name: str, content: str, min_length: int = 50) -> Dict:
        """セクションの長さを検証"""
        word_count = len(content.split())
        char_count = len(content)
        
        return {
            "section": section_name,
            "word_count": word_count,
            "char_count": char_count,
            "min_length_met": char_count >= min_length,
            "recommended_min_length": min_length
        }
    
    def validate_introduction_section(self, content: str) -> Dict:
        """導入セクションの検証"""
        issues = []
        score = 100
        
        # フックの存在チェック
        hook_patterns = [
            r'あなたは|あなたも|想像してみてください|考えてみてください',
            r'驚くべき|興味深い|意外な|衝撃的な',
            r'なぜ|どうして|どのように'
        ]
        
        has_hook = any(re.search(pattern, content) for pattern in hook_patterns)
        if not has_hook:
            issues.append("フック（視聴者の興味を引く要素）が見つかりません")
            score -= 20
        
        # 問題提起の存在チェック
        problem_patterns = [
            r'問題|課題|困難|悩み',
            r'解決|改善|向上|最適化'
        ]
        
        has_problem = any(re.search(pattern, content) for pattern in problem_patterns)
        if not has_problem:
            issues.append("問題提起が見つかりません")
            score -= 15
        
        # 動画の目的説明
        purpose_patterns = [
            r'この動画では|今回の動画では|今日は',
            r'学べます|理解できます|分かります'
        ]
        
        has_purpose = any(re.search(pattern, content) for pattern in purpose_patterns)
        if not has_purpose:
            issues.append("動画の目的説明が見つかりません")
            score -= 15
        
        return {
            "section": "導入",
            "score": max(0, score),
            "issues": issues,
            "has_hook": has_hook,
            "has_problem": has_problem,
            "has_purpose": has_purpose
        }
    
    def validate_main_content_section(self, content: str) -> Dict:
        """本論セクションの検証"""
        issues = []
        score = 100
        
        # 構造化のチェック
        structure_patterns = [
            r'まず|最初に|第一に',
            r'次に|第二に|続いて',
            r'最後に|まとめると|結論として'
        ]
        
        structure_count = sum(1 for pattern in structure_patterns if re.search(pattern, content))
        if structure_count < 2:
            issues.append("構造化の表現が不足しています")
            score -= 20
        
        # 具体例の存在
        example_patterns = [
            r'例えば|例として|具体例',
            r'実際に|実際の|実例'
        ]
        
        has_examples = any(re.search(pattern, content) for pattern in example_patterns)
        if not has_examples:
            issues.append("具体例が見つかりません")
            score -= 15
        
        # データや根拠の存在
        evidence_patterns = [
            r'研究によると|調査によると|データによると',
            r'統計|数値|パーセント|%'
        ]
        
        has_evidence = any(re.search(pattern, content) for pattern in evidence_patterns)
        if not has_evidence:
            issues.append("データや根拠が見つかりません")
            score -= 10
        
        return {
            "section": "本論",
            "score": max(0, score),
            "issues": issues,
            "structure_count": structure_count,
            "has_examples": has_examples,
            "has_evidence": has_evidence
        }
    
    def validate_conclusion_section(self, content: str) -> Dict:
        """結論セクションの検証"""
        issues = []
        score = 100
        
        # まとめの存在
        summary_patterns = [
            r'まとめると|要約すると|結論として',
            r'以上が|これで|このように'
        ]
        
        has_summary = any(re.search(pattern, content) for pattern in summary_patterns)
        if not has_summary:
            issues.append("まとめが見つかりません")
            score -= 25
        
        # アクションの呼びかけ
        action_patterns = [
            r'試してみてください|実践してみてください',
            r'チャンネル登録|いいね|コメント',
            r'次の動画|関連動画'
        ]
        
        has_action = any(re.search(pattern, content) for pattern in action_patterns)
        if not has_action:
            issues.append("アクションの呼びかけが見つかりません")
            score -= 25
        
        return {
            "section": "結論",
            "score": max(0, score),
            "issues": issues,
            "has_summary": has_summary,
            "has_action": has_action
        }
    
    def validate_structure(self, script_text: str) -> Dict:
        """原稿の構成を検証"""
        try:
            sections = self.extract_sections(script_text)
            
            validation_result = {
                "script_length": len(script_text),
                "sections_found": list(sections.keys()),
                "required_sections": self.required_sections,
                "optional_sections": self.optional_sections,
                "section_validations": {},
                "overall_score": 0,
                "issues": [],
                "recommendations": [],
                "validated_at": datetime.now().isoformat()
            }
            
            # 必須セクションの存在チェック
            missing_sections = []
            for required_section in self.required_sections:
                if required_section not in sections:
                    missing_sections.append(required_section)
            
            if missing_sections:
                validation_result["issues"].append(f"必須セクションが不足: {', '.join(missing_sections)}")
            
            # 各セクションの詳細検証
            section_scores = []
            
            for section_name, content in sections.items():
                # 長さ検証
                length_validation = self.validate_section_length(section_name, content)
                
                # セクション固有の検証
                if section_name == "導入":
                    section_validation = self.validate_introduction_section(content)
                elif section_name == "本論":
                    section_validation = self.validate_main_content_section(content)
                elif section_name == "結論":
                    section_validation = self.validate_conclusion_section(content)
                else:
                    section_validation = {
                        "section": section_name,
                        "score": 100,
                        "issues": []
                    }
                
                section_validation["length_validation"] = length_validation
                validation_result["section_validations"][section_name] = section_validation
                section_scores.append(section_validation["score"])
            
            # 全体スコアの計算
            if section_scores:
                validation_result["overall_score"] = sum(section_scores) / len(section_scores)
            
            # 推奨事項の生成
            if validation_result["overall_score"] < 70:
                validation_result["recommendations"].append("全体的な構成を改善してください")
            
            for section_name, validation in validation_result["section_validations"].items():
                if validation["score"] < 80:
                    validation_result["recommendations"].append(f"{section_name}セクションの改善が必要です")
            
            self.validation_results.append(validation_result)
            return validation_result
            
        except Exception as e:
            logging.error(f"構成検証エラー: {e}")
            return {
                "error": str(e),
                "validated_at": datetime.now().isoformat()
            }
    
    def save_results(self, output_file="structure_validation_results.json"):
        """検証結果をJSONファイルに保存"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.validation_results, f, indent=2, ensure_ascii=False)
            logging.info(f"✅ 検証結果を保存しました: {output_file}")
        except Exception as e:
            logging.error(f"❌ 結果保存エラー: {e}")
    
    def generate_report(self):
        """構成検証レポートの生成"""
        if not self.validation_results:
            logging.warning("検証結果がありません")
            return
        
        total_validations = len(self.validation_results)
        high_score_count = sum(1 for result in self.validation_results if result.get("overall_score", 0) >= 80)
        medium_score_count = sum(1 for result in self.validation_results if 60 <= result.get("overall_score", 0) < 80)
        low_score_count = sum(1 for result in self.validation_results if result.get("overall_score", 0) < 60)
        
        logging.info(f"\n📊 構成検証レポート:")
        logging.info(f"総検証数: {total_validations}")
        logging.info(f"高評価 (80点以上): {high_score_count}")
        logging.info(f"中評価 (60-79点): {medium_score_count}")
        logging.info(f"低評価 (60点未満): {low_score_count}")

def main():
    """メイン関数"""
    validator = StructureValidator()
    
    # テスト用原稿
    test_script = """
# 導入
あなたは、AI技術の進歩に驚いたことはありませんか？
今日は、AIが私たちの生活をどのように変えているかについて詳しく見ていきましょう。

# 本論
まず、AI技術の現状について説明します。
次に、具体的な活用事例を見ていきましょう。
例えば、医療分野ではAIによる診断支援システムが導入されています。
最後に、今後の展望についてお話しします。

# 結論
まとめると、AI技術は私たちの生活を大きく変えています。
この動画が参考になったら、チャンネル登録をお願いします。
次回は、AIの倫理について詳しく解説します。
"""
    
    logging.info("🚀 構成検証開始")
    
    # 構成検証実行
    result = validator.validate_structure(test_script)
    
    if result.get("overall_score"):
        logging.info(f"✅ 全体スコア: {result['overall_score']:.1f}点")
        
        for section_name, validation in result.get("section_validations", {}).items():
            logging.info(f"📋 {section_name}: {validation['score']}点")
            if validation.get("issues"):
                for issue in validation["issues"]:
                    logging.warning(f"   ⚠️ {issue}")
    
    # 結果保存
    validator.save_results()
    
    # レポート生成
    validator.generate_report()
    
    logging.info("✅ 構成検証完了")

if __name__ == "__main__":
    main()
