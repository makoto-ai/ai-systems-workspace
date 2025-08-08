#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI出力ハルシネーション検出スクリプト
AI出力と原文を照合し、一致性を検査する
"""

import json
import sys
import logging
import difflib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/hallucination_check.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class HallucinationChecker:
    """ハルシネーション検出クラス"""
    
    def __init__(self):
        self.check_results = []
        
    def preprocess_text(self, text: str) -> str:
        """テキストの前処理"""
        # 空白の正規化
        text = ' '.join(text.split())
        # 小文字化
        text = text.lower()
        # 句読点の除去
        import re
        text = re.sub(r'[^\w\s]', '', text)
        return text
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """テキスト間の類似度を計算"""
        processed_text1 = self.preprocess_text(text1)
        processed_text2 = self.preprocess_text(text2)
        
        # SequenceMatcherを使用して類似度を計算
        similarity = difflib.SequenceMatcher(None, processed_text1, processed_text2).ratio()
        return similarity
    
    def extract_key_claims(self, text: str) -> List[str]:
        """テキストから主要な主張を抽出"""
        # 簡単な実装：文単位で分割
        sentences = text.split('。')
        # 長い文（20文字以上）を主要な主張として扱う
        key_claims = [s.strip() for s in sentences if len(s.strip()) >= 20]
        return key_claims
    
    def check_factual_consistency(self, ai_output: str, source_text: str) -> Dict:
        """事実の一貫性をチェック"""
        # 主要な主張を抽出
        ai_claims = self.extract_key_claims(ai_output)
        source_claims = self.extract_key_claims(source_text)
        
        consistency_score = 0
        matched_claims = []
        unmatched_claims = []
        
        for ai_claim in ai_claims:
            best_match = None
            best_similarity = 0
            
            for source_claim in source_claims:
                similarity = self.calculate_similarity(ai_claim, source_claim)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = source_claim
            
            if best_similarity > 0.7:  # 70%以上の類似度で一致とみなす
                matched_claims.append({
                    "ai_claim": ai_claim,
                    "source_claim": best_match,
                    "similarity": best_similarity
                })
                consistency_score += best_similarity
            else:
                unmatched_claims.append({
                    "ai_claim": ai_claim,
                    "similarity": best_similarity
                })
        
        return {
            "consistency_score": consistency_score / len(ai_claims) if ai_claims else 0,
            "matched_claims": matched_claims,
            "unmatched_claims": unmatched_claims,
            "total_claims": len(ai_claims),
            "matched_count": len(matched_claims)
        }
    
    def check_hallucination(self, ai_output: str, source_text: str) -> Dict:
        """ハルシネーションをチェック"""
        try:
            # 全体的な類似度
            overall_similarity = self.calculate_similarity(ai_output, source_text)
            
            # 事実の一貫性チェック
            consistency_result = self.check_factual_consistency(ai_output, source_text)
            
            # ハルシネーション判定
            hallucination_score = 1 - consistency_result["consistency_score"]
            
            # 判定基準
            if hallucination_score < 0.2:
                hallucination_level = "低"
                is_hallucination = False
            elif hallucination_score < 0.5:
                hallucination_level = "中"
                is_hallucination = True
            else:
                hallucination_level = "高"
                is_hallucination = True
            
            result = {
                "ai_output": ai_output[:200] + "..." if len(ai_output) > 200 else ai_output,
                "source_text": source_text[:200] + "..." if len(source_text) > 200 else source_text,
                "overall_similarity": overall_similarity,
                "consistency_score": consistency_result["consistency_score"],
                "hallucination_score": hallucination_score,
                "hallucination_level": hallucination_level,
                "is_hallucination": is_hallucination,
                "matched_claims": consistency_result["matched_claims"],
                "unmatched_claims": consistency_result["unmatched_claims"],
                "total_claims": consistency_result["total_claims"],
                "matched_count": consistency_result["matched_count"],
                "checked_at": datetime.now().isoformat()
            }
            
            self.check_results.append(result)
            return result
            
        except Exception as e:
            logging.error(f"ハルシネーションチェックエラー: {e}")
            return {
                "error": str(e),
                "checked_at": datetime.now().isoformat()
            }
    
    def save_results(self, output_file="hallucination_check_results.json"):
        """チェック結果をJSONファイルに保存"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.check_results, f, indent=2, ensure_ascii=False)
            logging.info(f"✅ チェック結果を保存しました: {output_file}")
        except Exception as e:
            logging.error(f"❌ 結果保存エラー: {e}")
    
    def generate_report(self):
        """ハルシネーションチェックレポートの生成"""
        if not self.check_results:
            logging.warning("チェック結果がありません")
            return
        
        total_checks = len(self.check_results)
        hallucination_count = sum(1 for result in self.check_results if result.get("is_hallucination", False))
        
        logging.info(f"\n📊 ハルシネーションチェックレポート:")
        logging.info(f"総チェック数: {total_checks}")
        logging.info(f"ハルシネーション検出: {hallucination_count}")
        logging.info(f"正常: {total_checks - hallucination_count}")
        logging.info(f"ハルシネーション率: {(hallucination_count/total_checks)*100:.1f}%" if total_checks > 0 else "0%")

def main():
    """メイン関数"""
    checker = HallucinationChecker()
    
    # テスト用データ
    test_cases = [
        {
            "ai_output": "この研究では、AI技術を用いて画像認識の精度を向上させました。実験結果によると、従来の手法と比較して30%の精度向上を達成しました。",
            "source_text": "本研究では、ディープラーニングを用いて画像認識の精度を向上させました。実験結果によると、従来の手法と比較して25%の精度向上を達成しました。"
        },
        {
            "ai_output": "この論文では、量子コンピューティングの新しいアルゴリズムを提案しています。",
            "source_text": "この研究では、機械学習を用いた自然言語処理の改善について述べています。"
        }
    ]
    
    logging.info("🚀 ハルシネーションチェック開始")
    
    for i, test_case in enumerate(test_cases, 1):
        logging.info(f"\n📋 テストケース {i} のチェック中...")
        result = checker.check_hallucination(test_case["ai_output"], test_case["source_text"])
        
        if result.get("is_hallucination", False):
            logging.warning(f"❌ ハルシネーション検出: レベル {result.get('hallucination_level', 'N/A')}")
        else:
            logging.info(f"✅ 正常: 類似度 {result.get('overall_similarity', 0):.2f}")
    
    # 結果保存
    checker.save_results()
    
    # レポート生成
    checker.generate_report()
    
    logging.info("✅ ハルシネーションチェック完了")

if __name__ == "__main__":
    main()
