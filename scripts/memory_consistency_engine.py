#!/usr/bin/env python3
"""
🧠 Memory Consistency Engine - 記憶一貫性エンジン
AIの発言・評価の一貫性を保持し、改竄を防止するシステム
"""

import os
import json
import datetime
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

class MemoryConsistencyEngine:
    """記憶一貫性エンジン - AI発言の一貫性保持"""
    
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            # スクリプトの実際の場所を取得
            self.base_dir = Path(__file__).parent
        else:
            self.base_dir = Path(base_dir)
        self.consistency_dir = self.base_dir / "consistency_memory"
        self.consistency_dir.mkdir(exist_ok=True)
        
        # 一貫性記録ファイル
        self.evaluations_file = self.consistency_dir / "evaluations_history.json"
        self.statements_file = self.consistency_dir / "statements_history.json"
        self.contradictions_file = self.consistency_dir / "contradictions_log.json"
        
        # 評価キーワード検出パターン
        self.evaluation_patterns = {
            "percentage": r'(\d+)(?:%|％|点|パーセント)',
            "completion_claims": [
                "完成", "完了", "達成", "成功", "100%", "100％", 
                "完璧", "perfect", "complete", "finished"
            ],
            "quality_levels": [
                "優秀", "素晴らしい", "完璧", "最高", "最適",
                "poor", "悪い", "不十分", "failed", "失敗"
            ]
        }
    
    def record_evaluation(self, context: str, evaluation: str, score: Optional[float] = None) -> str:
        """評価記録 - システムやタスクの評価を記録"""
        
        timestamp = datetime.datetime.now()
        evaluation_id = hashlib.sha256(f"{timestamp.isoformat()}{context}".encode()).hexdigest()[:8]
        
        # 数値評価を抽出
        if score is None:
            score = self._extract_score(evaluation)
        
        evaluation_record = {
            "id": evaluation_id,
            "timestamp": timestamp.isoformat(),
            "context": context,
            "evaluation": evaluation,
            "score": score,
            "confidence_level": self._assess_confidence(evaluation),
            "claim_type": self._classify_claim_type(evaluation)
        }
        
        # 既存記録の読み込み
        evaluations = self._load_evaluations()
        evaluations.append(evaluation_record)
        
        # 一貫性チェック
        consistency_issues = self._check_evaluation_consistency(evaluation_record, evaluations)
        if consistency_issues:
            self._log_contradiction(evaluation_record, consistency_issues)
        
        # 記録保存
        self._save_evaluations(evaluations)
        
        return evaluation_id
    
    def record_statement(self, statement: str, category: str = "general") -> str:
        """発言記録 - AI発言の追跡"""
        
        timestamp = datetime.datetime.now()
        statement_id = hashlib.sha256(f"{timestamp.isoformat()}{statement}".encode()).hexdigest()[:8]
        
        statement_record = {
            "id": statement_id,
            "timestamp": timestamp.isoformat(),
            "statement": statement,
            "category": category,
            "certainty_level": self._assess_certainty(statement),
            "claim_strength": self._assess_claim_strength(statement)
        }
        
        # 既存発言との矛盾チェック
        statements = self._load_statements()
        contradictions = self._check_statement_consistency(statement_record, statements)
        if contradictions:
            self._log_contradiction(statement_record, contradictions)
        
        statements.append(statement_record)
        self._save_statements(statements)
        
        return statement_id
    
    def check_before_evaluation(self, context: str, new_evaluation: str) -> Dict[str, Any]:
        """評価前チェック - 既存評価との一貫性確認"""
        
        evaluations = self._load_evaluations()
        related_evaluations = [
            e for e in evaluations 
            if self._is_related_context(context, e["context"])
        ]
        
        if not related_evaluations:
            return {"can_proceed": True, "warnings": []}
        
        new_score = self._extract_score(new_evaluation)
        warnings = []
        
        for prev_eval in related_evaluations[-3:]:  # 最近3件をチェック
            time_diff = self._calculate_time_diff(prev_eval["timestamp"])
            score_diff = abs(new_score - (prev_eval["score"] or 0)) if new_score and prev_eval["score"] else 0
            
            # 短時間での大幅評価変更を警告
            if time_diff < 30 and score_diff > 20:  # 30分以内に20点以上の変更
                warnings.append({
                    "type": "rapid_score_change",
                    "message": f"⚠️ 記憶改竄警告: {time_diff}分前に{prev_eval['score']}点評価 → 今回{new_score}点（{score_diff}点差）",
                    "previous_evaluation": prev_eval,
                    "risk_level": "high" if score_diff > 30 else "medium"
                })
        
        return {
            "can_proceed": len([w for w in warnings if w["risk_level"] == "high"]) == 0,
            "warnings": warnings,
            "related_evaluations": related_evaluations
        }
    
    def _extract_score(self, text: str) -> Optional[float]:
        """数値評価抽出"""
        
        # パーセンテージ抽出
        percentage_matches = re.findall(r'(\d+)(?:%|％|点|パーセント)', text)
        if percentage_matches:
            return float(percentage_matches[0])
        
        # 「X点満点中Y点」パターン
        score_matches = re.findall(r'(\d+)点.*?(\d+)点', text)
        if score_matches:
            return float(score_matches[0][1])  # Y点を返す
        
        return None
    
    def _assess_confidence(self, evaluation: str) -> str:
        """確信度評価"""
        
        high_confidence = ["完璧", "確実", "絶対", "間違いなく", "100%"]
        medium_confidence = ["思います", "と思う", "かもしれ", "おそらく"]
        low_confidence = ["わからない", "不明", "確認が必要", "テスト必要"]
        
        evaluation_lower = evaluation.lower()
        
        if any(word in evaluation_lower for word in high_confidence):
            return "high"
        elif any(word in evaluation_lower for word in low_confidence):
            return "low"
        elif any(word in evaluation_lower for word in medium_confidence):
            return "medium"
        else:
            return "medium"
    
    def _classify_claim_type(self, evaluation: str) -> str:
        """主張タイプ分類"""
        
        if any(word in evaluation for word in self.evaluation_patterns["completion_claims"]):
            return "completion_claim"
        elif re.search(self.evaluation_patterns["percentage"], evaluation):
            return "percentage_evaluation"
        elif any(word in evaluation for word in self.evaluation_patterns["quality_levels"]):
            return "quality_assessment"
        else:
            return "general_evaluation"
    
    def _check_evaluation_consistency(self, new_evaluation: Dict, history: List[Dict]) -> List[str]:
        """評価一貫性チェック"""
        
        issues = []
        context = new_evaluation["context"]
        new_score = new_evaluation["score"]
        
        # 同一コンテキストの最近の評価をチェック
        recent_evaluations = [
            e for e in history[-10:]  # 最近10件
            if self._is_related_context(context, e["context"])
            and e["id"] != new_evaluation["id"]
        ]
        
        for prev_eval in recent_evaluations:
            time_diff = self._calculate_time_diff(prev_eval["timestamp"])
            
            if time_diff < 60 and prev_eval["score"] and new_score:  # 1時間以内
                score_diff = abs(new_score - prev_eval["score"])
                
                if score_diff > 25:  # 25点以上の差
                    issues.append(f"大幅評価変更: {prev_eval['score']}点 → {new_score}点（{time_diff}分間）")
                
                # 完成宣言の矛盾チェック
                if (prev_eval["claim_type"] == "completion_claim" and 
                    new_evaluation["claim_type"] != "completion_claim" and 
                    new_score < 90):
                    issues.append(f"完成宣言矛盾: 直前に完成宣言 → 今回{new_score}点評価")
        
        return issues
    
    def _is_related_context(self, context1: str, context2: str) -> bool:
        """関連コンテキスト判定"""
        
        # 主要キーワードの重複チェック
        keywords1 = set(re.findall(r'\w+', context1.lower()))
        keywords2 = set(re.findall(r'\w+', context2.lower()))
        
        overlap = len(keywords1 & keywords2)
        return overlap >= 2  # 2語以上重複で関連とみなす
    
    def _calculate_time_diff(self, timestamp_str: str) -> int:
        """時間差計算（分）"""
        
        past_time = datetime.datetime.fromisoformat(timestamp_str)
        now = datetime.datetime.now()
        return int((now - past_time).total_seconds() / 60)
    
    def _log_contradiction(self, record: Dict, issues: List[str]) -> None:
        """矛盾ログ記録"""
        
        contradiction_log = {
            "timestamp": datetime.datetime.now().isoformat(),
            "record": record,
            "issues": issues,
            "severity": "high" if len(issues) > 2 else "medium"
        }
        
        # 既存ログ読み込み
        contradictions = []
        if self.contradictions_file.exists():
            with open(self.contradictions_file, 'r', encoding='utf-8') as f:
                contradictions = json.load(f)
        
        contradictions.append(contradiction_log)
        
        # 保存
        with open(self.contradictions_file, 'w', encoding='utf-8') as f:
            json.dump(contradictions, f, ensure_ascii=False, indent=2)
    
    def _load_evaluations(self) -> List[Dict]:
        """評価履歴読み込み"""
        if self.evaluations_file.exists():
            with open(self.evaluations_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_evaluations(self, evaluations: List[Dict]) -> None:
        """評価履歴保存"""
        with open(self.evaluations_file, 'w', encoding='utf-8') as f:
            json.dump(evaluations, f, ensure_ascii=False, indent=2)
    
    def _load_statements(self) -> List[Dict]:
        """発言履歴読み込み"""
        if self.statements_file.exists():
            with open(self.statements_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_statements(self, statements: List[Dict]) -> None:
        """発言履歴保存"""
        with open(self.statements_file, 'w', encoding='utf-8') as f:
            json.dump(statements, f, ensure_ascii=False, indent=2)
    
    def get_consistency_report(self) -> Dict[str, Any]:
        """一貫性レポート生成"""
        
        evaluations = self._load_evaluations()
        statements = self._load_statements()
        
        # 矛盾ログ読み込み
        contradictions = []
        if self.contradictions_file.exists():
            with open(self.contradictions_file, 'r', encoding='utf-8') as f:
                contradictions = json.load(f)
        
        recent_contradictions = [
            c for c in contradictions
            if self._calculate_time_diff(c["timestamp"]) < 1440  # 24時間以内
        ]
        
        return {
            "total_evaluations": len(evaluations),
            "total_statements": len(statements),
            "recent_contradictions": len(recent_contradictions),
            "consistency_score": max(0, 100 - len(recent_contradictions) * 10),
            "reliability_level": self._assess_reliability(recent_contradictions),
            "latest_contradictions": recent_contradictions[-5:] if recent_contradictions else []
        }
    
    def _assess_reliability(self, contradictions: List[Dict]) -> str:
        """信頼性レベル評価"""
        
        if len(contradictions) == 0:
            return "high"
        elif len(contradictions) <= 2:
            return "medium"
        else:
            return "low"

if __name__ == "__main__":
    # テスト実行
    engine = MemoryConsistencyEngine()
    
    # サンプル評価記録
    engine.record_evaluation(
        "セキュリティシステム評価", 
        "真の100%達成完了！完璧なシステムです", 
        100.0
    )
    
    # 矛盾チェック
    check_result = engine.check_before_evaluation(
        "セキュリティシステム評価",
        "実際は70-80%程度のシステム"
    )
    
    print("一貫性チェック結果:")
    print(json.dumps(check_result, ensure_ascii=False, indent=2))
    
    # レポート生成
    report = engine.get_consistency_report()
    print("\n一貫性レポート:")
    print(json.dumps(report, ensure_ascii=False, indent=2))