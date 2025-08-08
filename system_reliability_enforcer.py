#!/usr/bin/env python3
"""
システム信頼性強制執行システム
「完成してます」発言を防ぐ機能

Author: AI Assistant（反省版）
"""

import asyncio
import datetime
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class SystemTest:
    """システムテスト結果"""

    system_name: str
    test_function: str
    result: bool
    error: Optional[str]
    timestamp: datetime.datetime


@dataclass
class ReliabilityReport:
    """信頼性レポート"""

    system_name: str
    tests_passed: int
    tests_failed: int
    overall_status: str  # "verified", "unreliable", "untested"
    last_tested: datetime.datetime
    issues: List[str]


class SystemReliabilityEnforcer:
    """システム信頼性強制執行システム"""

    def __init__(self):
        self.test_results = {}
        self.reliability_reports = {}
        self.forbidden_phrases = [
            "完成してます",
            "完璧です",
            "動作します",
            "100%動作",
            "完全統合",
            "問題ありません",
            "全て動作",
            "確実に動作",
            "完全に動作",
        ]

        # 許可される表現
        self.allowed_phrases = [
            "テスト中です",
            "開発中です",
            "動作確認済み（テスト済み）",
            "限定的に動作",
            "部分的に動作",
            "動作確認が必要",
            "実装中です",
        ]

    async def test_system_functionality(self, system_name: str) -> ReliabilityReport:
        """システム機能テスト実行"""

        print(f"🔍 {system_name} 信頼性テスト開始")
        print("=" * 60)

        tests = []

        # 論文検索システムテスト
        if "論文検索" in system_name or "paper" in system_name.lower():
            test_result = await self._test_paper_search_system()
            tests.append(test_result)

        # YouTube原稿システムテスト
        if "YouTube" in system_name or "原稿" in system_name:
            test_result = await self._test_youtube_script_system()
            tests.append(test_result)

        # 統合システムテスト
        if "統合" in system_name or "integration" in system_name.lower():
            test_result = await self._test_integration_system()
            tests.append(test_result)

        # 結果集計
        passed_tests = [t for t in tests if t.result]
        failed_tests = [t for t in tests if not t.result]

        # 総合評価
        if len(failed_tests) == 0:
            overall_status = "verified"
        elif len(passed_tests) > len(failed_tests):
            overall_status = "partially_working"
        else:
            overall_status = "unreliable"

        # 問題点抽出
        issues = [f"{t.system_name}: {t.error}" for t in failed_tests if t.error]

        report = ReliabilityReport(
            system_name=system_name,
            tests_passed=len(passed_tests),
            tests_failed=len(failed_tests),
            overall_status=overall_status,
            last_tested=datetime.datetime.now(),
            issues=issues,
        )

        self.reliability_reports[system_name] = report

        print(f"\n🏆 {system_name} テスト結果:")
        print(f"   成功: {len(passed_tests)}/{len(tests)}")
        print(f"   状態: {overall_status}")
        print(f"   問題: {len(issues)}件")

        return report

    async def _test_paper_search_system(self) -> SystemTest:
        """論文検索システムテスト"""

        try:
            import sys
            from pathlib import Path

            sys.path.append(str(Path("../paper_research_system")))

            from services.safe_rate_limited_search_service import (
                SafeRateLimitedSearchService,
            )

            service = SafeRateLimitedSearchService()

            papers = await service.search_papers("test query", 1)

            if papers and len(papers) > 0:
                return SystemTest(
                    system_name="論文検索システム",
                    test_function="_test_paper_search_system",
                    result=True,
                    error=None,
                    timestamp=datetime.datetime.now(),
                )
            else:
                return SystemTest(
                    system_name="論文検索システム",
                    test_function="_test_paper_search_system",
                    result=False,
                    error="論文取得に失敗",
                    timestamp=datetime.datetime.now(),
                )

        except Exception as e:
            return SystemTest(
                system_name="論文検索システム",
                test_function="_test_paper_search_system",
                result=False,
                error=str(e),
                timestamp=datetime.datetime.now(),
            )

    async def _test_youtube_script_system(self) -> SystemTest:
        """YouTube原稿システムテスト"""

        try:
            # working_youtube_script_system.pyをテスト
            from working_youtube_script_system import create_working_youtube_script

            result = await create_working_youtube_script("test topic")

            if result.get("success"):
                return SystemTest(
                    system_name="YouTube原稿システム",
                    test_function="_test_youtube_script_system",
                    result=True,
                    error=None,
                    timestamp=datetime.datetime.now(),
                )
            else:
                return SystemTest(
                    system_name="YouTube原稿システム",
                    test_function="_test_youtube_script_system",
                    result=False,
                    error=result.get("error", "原稿生成失敗"),
                    timestamp=datetime.datetime.now(),
                )

        except Exception as e:
            return SystemTest(
                system_name="YouTube原稿システム",
                test_function="_test_youtube_script_system",
                result=False,
                error=str(e),
                timestamp=datetime.datetime.now(),
            )

    async def _test_integration_system(self) -> SystemTest:
        """統合システムテスト"""

        try:
            # 論文検索→原稿生成の一気通貫テスト
            from working_youtube_script_system import create_working_youtube_script

            result = await create_working_youtube_script(
                topic="営業 才能", title="テスト用タイトル"
            )

            # 統合機能の確認
            integration_checks = [
                result.get("success", False),
                "research_data" in result,
                "verified_info" in result,
                "verification_result" in result,
            ]

            if all(integration_checks):
                return SystemTest(
                    system_name="統合システム",
                    test_function="_test_integration_system",
                    result=True,
                    error=None,
                    timestamp=datetime.datetime.now(),
                )
            else:
                missing_features = []
                if not result.get("success"):
                    missing_features.append("基本機能")
                if "research_data" not in result:
                    missing_features.append("論文検索連携")
                if "verified_info" not in result:
                    missing_features.append("情報検証")
                if "verification_result" not in result:
                    missing_features.append("品質検証")

                return SystemTest(
                    system_name="統合システム",
                    test_function="_test_integration_system",
                    result=False,
                    error=f"統合機能不足: {', '.join(missing_features)}",
                    timestamp=datetime.datetime.now(),
                )

        except Exception as e:
            return SystemTest(
                system_name="統合システム",
                test_function="_test_integration_system",
                result=False,
                error=str(e),
                timestamp=datetime.datetime.now(),
            )

    def check_statement_reliability(self, statement: str) -> Dict[str, Any]:
        """発言の信頼性チェック"""

        # 禁止フレーズチェック
        forbidden_found = []
        for phrase in self.forbidden_phrases:
            if phrase in statement:
                forbidden_found.append(phrase)

        # 許可フレーズチェック
        allowed_found = []
        for phrase in self.allowed_phrases:
            if phrase in statement:
                allowed_found.append(phrase)

        # 評価
        if forbidden_found and not allowed_found:
            reliability = "unreliable"
            warning = f"禁止フレーズ検出: {forbidden_found}"
        elif forbidden_found and allowed_found:
            reliability = "mixed"
            warning = f"禁止フレーズ: {forbidden_found}, 許可フレーズ: {allowed_found}"
        elif allowed_found:
            reliability = "reliable"
            warning = None
        else:
            reliability = "neutral"
            warning = None

        return {
            "reliability": reliability,
            "forbidden_phrases_found": forbidden_found,
            "allowed_phrases_found": allowed_found,
            "warning": warning,
            "recommendation": self._get_recommendation(reliability),
        }

    def _get_recommendation(self, reliability: str) -> str:
        """推奨事項"""

        if reliability == "unreliable":
            return (
                "❌ この発言は控えてください。実動テストを行ってから発言してください。"
            )
        elif reliability == "mixed":
            return (
                "⚠️ 表現を見直してください。より正確な表現に変更することをお勧めします。"
            )
        elif reliability == "reliable":
            return "✅ 適切な表現です。"
        else:
            return "ℹ️ 中立的な表現です。"

    def generate_reliability_summary(self) -> str:
        """信頼性サマリー生成"""

        if not self.reliability_reports:
            return "❌ システムテストが実行されていません。"

        summary = "🔍 システム信頼性レポート\n"
        summary += "=" * 60 + "\n"

        for system_name, report in self.reliability_reports.items():
            summary += f"\n📋 {system_name}:\n"
            summary += f"   状態: {report.overall_status}\n"
            summary += f"   テスト: {report.tests_passed}成功/{report.tests_passed + report.tests_failed}実行\n"
            summary += (
                f"   最終テスト: {report.last_tested.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )

            if report.issues:
                summary += "   問題:\n"
                for issue in report.issues:
                    summary += f"     - {issue}\n"

        return summary


# 使用例
async def enforce_system_reliability():
    """システム信頼性強制執行"""

    enforcer = SystemReliabilityEnforcer()

    # 各システムのテスト実行
    systems_to_test = ["論文検索システム", "YouTube原稿システム", "統合システム"]

    for system in systems_to_test:
        await enforcer.test_system_functionality(system)

    # レポート生成
    summary = enforcer.generate_reliability_summary()
    print(summary)

    return enforcer


if __name__ == "__main__":
    print("🛡️ システム信頼性強制執行システム")
    print("=" * 60)
    print("「完成してます」発言を防ぐための実動テストシステム")

    async def demo():
        enforcer = await enforce_system_reliability()

        # 発言チェックのデモ
        test_statements = [
            "完成してます！",
            "動作確認済み（テスト済み）です",
            "開発中です",
            "100%動作します！",
        ]

        print("\n🗣️ 発言信頼性チェック:")
        for statement in test_statements:
            check = enforcer.check_statement_reliability(statement)
            print(
                f"   「{statement}」 → {check['reliability']} {check['recommendation']}"
            )

    # asyncio.run(demo())  # 必要に応じてコメントアウト解除
