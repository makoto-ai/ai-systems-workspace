#!/usr/bin/env python3
"""
🔗 Memory System Integration - 記憶システム統合管理
既存のCursorEnhancedMemoryと新しいMemoryConsistencyEngineを統合
"""

import os
import sys
from pathlib import Path

# パス設定
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from cursor_memory_enhanced import CursorEnhancedMemory
from memory_consistency_engine import MemoryConsistencyEngine


class IntegratedMemorySystem:
    """統合記憶システム - 高精度記憶 + 一貫性保持"""

    def __init__(self, obsidian_vault_path: str = "docs/obsidian-knowledge"):
        # 既存システム
        self.enhanced_memory = CursorEnhancedMemory(obsidian_vault_path)

        # 新規一貫性エンジン
        self.consistency_engine = MemoryConsistencyEngine()

        print("🧠 統合記憶システム起動完了")
        print("✅ CursorEnhancedMemory: 高精度記憶・感情分析")
        print("✅ MemoryConsistencyEngine: 評価改竄防止・矛盾検知")

    def record_conversation_with_consistency(
        self,
        user_message: str,
        ai_response: str,
        context_before: str = "",
        context_after: str = "",
    ) -> dict:
        """一貫性チェック付き会話記録"""

        # 1. 高精度記憶システムで記録
        enhanced_id = self.enhanced_memory.record_enhanced_conversation(
            user_message, ai_response, context_before, context_after
        )

        # 2. 評価・発言の抽出と一貫性チェック
        consistency_results = self._process_consistency_checks(
            user_message, ai_response
        )

        # 3. 結果統合
        result = {
            "enhanced_conversation_id": enhanced_id,
            "consistency_checks": consistency_results,
            "safe_to_proceed": all(
                check.get("can_proceed", True) for check in consistency_results
            ),
            "warnings": [
                warning
                for check in consistency_results
                for warning in check.get("warnings", [])
            ],
        }

        return result

    def _process_consistency_checks(self, user_message: str, ai_response: str) -> list:
        """一貫性チェック処理"""

        results = []

        # AI回答から評価発言を検出
        evaluation_phrases = self._extract_evaluations(ai_response)

        for phrase in evaluation_phrases:
            # 評価前チェック
            context = self._determine_context(user_message, phrase)
            check_result = self.consistency_engine.check_before_evaluation(
                context, phrase
            )

            if check_result["warnings"]:
                print(f"⚠️ 一貫性警告: {phrase}")
                for warning in check_result["warnings"]:
                    print(f"   {warning['message']}")

            # 評価記録
            if check_result["can_proceed"]:
                eval_id = self.consistency_engine.record_evaluation(context, phrase)
                check_result["evaluation_id"] = eval_id

            results.append(check_result)

        # 一般発言の記録
        if not evaluation_phrases:
            statement_id = self.consistency_engine.record_statement(
                ai_response, "general"
            )
            results.append(
                {"statement_id": statement_id, "can_proceed": True, "warnings": []}
            )

        return results

    def _extract_evaluations(self, text: str) -> list:
        """評価発言の抽出"""

        evaluation_indicators = [
            r".*(完成|完了|達成).*",
            r".*(\d+%|\d+％|\d+点).*",
            r".*(成功|失敗|excellent|perfect).*",
            r".*(実装済み|未実装|動作中).*",
        ]

        import re

        phrases = []

        for pattern in evaluation_indicators:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # 文全体を抽出
                sentences = text.split("。")
                for sentence in sentences:
                    if any(
                        match in sentence for match in matches if isinstance(match, str)
                    ):
                        phrases.append(sentence.strip())
                    elif any(
                        any(m in sentence for m in match)
                        for match in matches
                        if isinstance(match, tuple)
                    ):
                        phrases.append(sentence.strip())

        return list(set(phrases))  # 重複除去

    def _determine_context(self, user_message: str, ai_phrase: str) -> str:
        """コンテキスト判定"""

        context_keywords = {
            "セキュリティシステム": ["セキュリティ", "security", "脅威", "監視"],
            "記憶システム": ["記憶", "memory", "覚え", "忘れ"],
            "APIシステム": ["API", "apidog", "テスト", "統合"],
            "YouTube原稿": ["YouTube", "原稿", "script", "ハルシネーション"],
            "論文検索": ["論文", "paper", "検索", "research"],
        }

        combined_text = f"{user_message} {ai_phrase}".lower()

        for context, keywords in context_keywords.items():
            if any(keyword.lower() in combined_text for keyword in keywords):
                return context

        return "一般システム"

    def generate_memory_health_report(self) -> dict:
        """記憶システム健全性レポート"""

        # 既存記憶システムの状況
        enhanced_status = {
            "workflow_memory_files": len(
                list(self.enhanced_memory.workflow_memory.glob("*.json"))
            ),
            "detailed_conversations": len(
                list(self.enhanced_memory.detailed_conversations.glob("*.json"))
            ),
            "auto_summaries": len(
                list(self.enhanced_memory.auto_summaries.glob("*.md"))
            ),
        }

        # 一貫性エンジンの状況
        consistency_report = self.consistency_engine.get_consistency_report()

        # 統合レポート
        overall_health = {
            "enhanced_memory": enhanced_status,
            "consistency_engine": consistency_report,
            "integration_status": "active",
            "memory_reliability": consistency_report["reliability_level"],
            "recommendation": self._generate_recommendation(consistency_report),
        }

        return overall_health

    def _generate_recommendation(self, consistency_report: dict) -> str:
        """推奨アクション生成"""

        reliability = consistency_report["reliability_level"]
        contradictions = consistency_report["recent_contradictions"]

        if reliability == "high" and contradictions == 0:
            return "記憶システム正常動作中。現状維持推奨。"
        elif reliability == "medium":
            return f"軽微な一貫性問題あり（{contradictions}件）。発言時の確認強化推奨。"
        else:
            return f"重大な一貫性問題（{contradictions}件）。即座に発言パターンの見直し必要。"

    def enforce_consistency_check(self, ai_response: str) -> dict:
        """強制一貫性チェック - AI回答前の検証"""

        evaluations = self._extract_evaluations(ai_response)

        if not evaluations:
            return {"approved": True, "warnings": []}

        results = {"approved": True, "warnings": [], "blocked_phrases": []}

        for evaluation in evaluations:
            context = self._determine_context("", evaluation)
            check = self.consistency_engine.check_before_evaluation(context, evaluation)

            if not check["can_proceed"]:
                results["approved"] = False
                results["blocked_phrases"].append(evaluation)

            results["warnings"].extend(check["warnings"])

        return results


if __name__ == "__main__":
    # 統合システムテスト
    integrated_system = IntegratedMemorySystem()

    print("\n🧪 統合システムテスト実行")

    # サンプル会話でテスト
    test_user_message = "セキュリティシステムの評価を教えて"
    test_ai_response = "真の100%達成完了！セキュリティシステムは完璧です。"

    result = integrated_system.record_conversation_with_consistency(
        test_user_message, test_ai_response
    )

    print(f"✅ 会話記録結果: {result['safe_to_proceed']}")
    if result["warnings"]:
        print("⚠️ 検出された警告:")
        for warning in result["warnings"]:
            print(f"   - {warning}")

    # 健全性レポート
    health_report = integrated_system.generate_memory_health_report()
    print(f"\n📊 記憶システム健全性: {health_report['memory_reliability']}")
    print(f"💡 推奨アクション: {health_report['recommendation']}")
