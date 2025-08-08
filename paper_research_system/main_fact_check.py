#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 原稿事実確認・添削システム - メインインターフェース
YouTube原稿の事実確認とハルシネーション修正

Usage:
    python main_fact_check.py "原稿テキスト"
    python main_fact_check.py --file manuscript.txt
    python main_fact_check.py --interactive
"""

import argparse
import sys
from pathlib import Path
import json

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "services"))

from services.manuscript_fact_checker import ManuscriptFactChecker


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(
        description="📝 原稿事実確認・添削システム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🎯 使用例:
  python main_fact_check.py "ペルティエの2018年研究によると..."
  python main_fact_check.py --file my_script.txt
  python main_fact_check.py --interactive

📊 機能:
  ✅ ハルシネーション検出
  ✅ 事実確認
  ✅ 代替エビデンス検索
  ✅ 文体保持リライト
  ✅ YouTube最適化
        """
    )
    
    # 引数定義
    parser.add_argument(
        "manuscript",
        nargs="?",
        help="事実確認する原稿テキスト"
    )
    
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="原稿ファイルパス"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="対話モード"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="修正版の保存先ファイル"
    )
    
    parser.add_argument(
        "--detailed", "-d",
        action="store_true",
        help="詳細な分析結果を表示"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON形式で結果を出力"
    )

    args = parser.parse_args()

    # 原稿取得
    manuscript = get_manuscript(args)
    if not manuscript:
        print("❌ 原稿が指定されていません")
        parser.print_help()
        return

    print("╭" + "─" * 50 + "╮")
    print("│ 🎯 原稿事実確認・添削システム           │")
    print("│ ハルシネーション検出 & 信頼性向上        │")
    print("╰" + "─" * 50 + "╯")
    print()

    # 事実確認実行
    checker = ManuscriptFactChecker()
    
    try:
        result = checker.run_full_fact_check(manuscript)
        
        # 結果表示
        display_results(result, args)
        
        # ファイル保存
        if args.output:
            save_corrected_manuscript(result['corrected_manuscript'], args.output)
            print(f"💾 修正版を保存: {args.output}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return


def get_manuscript(args) -> str:
    """原稿を取得"""
    if args.manuscript:
        return args.manuscript
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"❌ ファイルが見つかりません: {args.file}")
            return ""
    elif args.interactive:
        return get_interactive_manuscript()
    else:
        return ""


def get_interactive_manuscript() -> str:
    """対話モードで原稿を取得"""
    print("📝 原稿を入力してください（終了は Ctrl+D または空行2回）:")
    print("-" * 50)
    
    lines = []
    empty_line_count = 0
    
    try:
        while True:
            line = input()
            if not line.strip():
                empty_line_count += 1
                if empty_line_count >= 2:
                    break
            else:
                empty_line_count = 0
            lines.append(line)
    except EOFError:
        pass
    
    return "\n".join(lines)


def display_results(result: dict, args):
    """結果を表示"""
    if args.json:
        # JSON形式で出力
        json_output = {
            "original_manuscript": result["original_manuscript"],
            "corrected_manuscript": result["corrected_manuscript"],
            "total_claims": result["total_claims"],
            "hallucination_count": result["hallucination_count"],
            "low_confidence_count": result["low_confidence_count"],
            "improvement_summary": result["improvement_summary"]
        }
        print(json.dumps(json_output, ensure_ascii=False, indent=2))
        return

    # 通常表示
    print("📊 事実確認結果:")
    print("=" * 50)
    print(f"📝 検出した主張: {result['total_claims']}個")
    print(f"❌ ハルシネーション: {result['hallucination_count']}個")
    print(f"⚠️ 低信頼性: {result['low_confidence_count']}個")
    print()
    
    if result['hallucination_count'] > 0 or result['low_confidence_count'] > 0:
        print("✏️ 修正版原稿:")
        print("-" * 50)
        print(result['corrected_manuscript'])
        print("-" * 50)
        print()
    else:
        print("✅ 事実確認に問題ありません！")
        print()

    print(result['improvement_summary'])
    
    if args.detailed:
        print("\n🔍 詳細分析:")
        print("-" * 50)
        for i, fact_result in enumerate(result['fact_check_results'], 1):
            print(f"{i}. {fact_result.original_claim.content[:50]}...")
            print(f"   ハルシネーション: {'❌' if fact_result.is_hallucination else '✅'}")
            print(f"   信頼度: {fact_result.verification_score:.2f}")
            print(f"   推奨: {fact_result.recommendation}")
            print()


def save_corrected_manuscript(manuscript: str, filepath: str):
    """修正版原稿を保存"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(manuscript)


if __name__ == "__main__":
    main()