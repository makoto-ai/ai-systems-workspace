#!/usr/bin/env python3
"""
Academic Paper Research Assistant - Search History Manager
論文検索履歴管理システム
"""

from services.search_history_db import get_search_history_db
import click
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import List, Dict, Any
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))


console = Console()
logger = logging.getLogger(__name__)


@click.group()
def history_cli():
    """論文検索履歴管理システム"""


@history_cli.command()
@click.option("--limit", "-n", default=20, help="表示件数")
@click.option(
    "--search-type",
    "-t",
    type=click.Choice(["integrated", "specialized"]),
    help="検索タイプフィルタ",
)
@click.option(
    "--domain",
    "-d",
    type=click.Choice(
        [
            "sales_psychology",
            "management_psychology",
            "behavioral_economics",
            "universal_psychology",
        ]
    ),
    help="ドメインフィルタ",
)
@click.option("--days", default=30, help="過去N日間")
@click.option("--verbose", "-v", is_flag=True, help="詳細表示")
def list(limit: int, search_type: str, domain: str, days: int, verbose: bool):
    """検索履歴の一覧表示"""
    console.print(
        Panel.fit(
            "📚 Academic Paper Research Assistant\n🕒 検索履歴管理システム",
            style="bold blue",
        )
    )

    try:
        history_db = get_search_history_db()
        histories = history_db.get_search_history(
            limit=limit, search_type=search_type, domain=domain, days_back=days
        )

        if not histories:
            console.print("❌ 検索履歴がありません")
            return

        # 履歴テーブル表示
        _display_history_table(histories, verbose)

        console.print(
            f"\n💡 詳細表示: [bold cyan]python3 main_history.py detail <ID>[/bold cyan]"
        )
        console.print(
            f"💡 統計表示: [bold cyan]python3 main_history.py stats[/bold cyan]"
        )

    except Exception as e:
        logger.error(f"履歴取得エラー: {e}")
        console.print(f"❌ エラーが発生しました: {e}")


@history_cli.command()
@click.argument("history_id", type=int)
def detail(history_id: int):
    """特定検索の詳細表示"""
    console.print(Panel.fit(f"📄 検索履歴詳細 - ID: {history_id}", style="bold green"))

    try:
        history_db = get_search_history_db()

        # 履歴基本情報取得
        histories = history_db.get_search_history(limit=1000)  # 全取得して該当IDを探す
        target_history = None
        for h in histories:
            if h["id"] == history_id:
                target_history = h
                break

        if not target_history:
            console.print(f"❌ ID {history_id} の履歴が見つかりません")
            return

        # 検索結果詳細取得
        results = history_db.get_search_results(history_id)

        # 詳細表示
        _display_history_detail(target_history, results)

    except Exception as e:
        logger.error(f"履歴詳細取得エラー: {e}")
        console.print(f"❌ エラーが発生しました: {e}")


@history_cli.command()
@click.option("--days", default=30, help="過去N日間")
def stats(days: int):
    """検索統計の表示"""
    console.print(Panel.fit(f"📊 検索統計 - 過去{days}日間", style="bold magenta"))

    try:
        history_db = get_search_history_db()
        statistics = history_db.get_statistics(days_back=days)

        if not statistics:
            console.print("❌ 統計データがありません")
            return

        _display_statistics(statistics)

    except Exception as e:
        logger.error(f"統計取得エラー: {e}")
        console.print(f"❌ エラーが発生しました: {e}")


@history_cli.command()
@click.option("--days", default=30, help="過去N日間")
@click.option(
    "--granularity",
    "-g",
    type=click.Choice(["day", "week"]),
    default="day",
    help="集計単位",
)
def trends(days: int, granularity: str):
    """検索トレンド分析"""
    console.print(
        Panel.fit(
            f"📈 検索トレンド分析 - 過去{days}日間（{granularity}別）",
            style="bold cyan",
        )
    )

    try:
        history_db = get_search_history_db()

        # 履歴データ取得
        histories = history_db.get_search_history(limit=1000, days_back=days)

        if not histories:
            console.print("❌ 分析対象データがありません")
            return

        _display_trend_analysis(histories, granularity)

    except Exception as e:
        logger.error(f"トレンド分析エラー: {e}")
        console.print(f"❌ エラーが発生しました: {e}")


@history_cli.command()
@click.option("--days", default=30, help="過去N日間")
def performance(days: int):
    """パフォーマンス分析"""
    console.print(
        Panel.fit(f"⚡ パフォーマンス分析 - 過去{days}日間", style="bold red")
    )

    try:
        history_db = get_search_history_db()
        histories = history_db.get_search_history(limit=1000, days_back=days)

        if not histories:
            console.print("❌ 分析対象データがありません")
            return

        _display_performance_analysis(histories)

    except Exception as e:
        logger.error(f"パフォーマンス分析エラー: {e}")
        console.print(f"❌ エラーが発生しました: {e}")


@history_cli.command()
@click.argument("search_query", required=False)
@click.option("--limit", "-n", default=10, help="表示件数")
def search(search_query: str, limit: int):
    """履歴内検索"""
    if not search_query:
        console.print("❌ 検索クエリを指定してください")
        return

    console.print(Panel.fit(f"🔍 履歴内検索: '{search_query}'", style="bold yellow"))

    try:
        history_db = get_search_history_db()

        # 全履歴から検索
        all_histories = history_db.get_search_history(limit=1000)
        matching_histories = []

        for history in all_histories:
            if search_query.lower() in history["query"].lower():
                matching_histories.append(history)

        if not matching_histories:
            console.print(f"❌ '{search_query}' に関連する履歴が見つかりません")
            return

        # 結果表示
        limited_results = matching_histories[:limit]
        _display_history_table(limited_results, verbose=False)

        if len(matching_histories) > limit:
            console.print(
                f"\n💡 {
                    len(matching_histories) -
                    limit}件の追加結果があります。--limit オプションで表示数を増やせます。"
            )

    except Exception as e:
        logger.error(f"履歴検索エラー: {e}")
        console.print(f"❌ エラーが発生しました: {e}")


def _display_history_table(histories: List[Dict[str, Any]], verbose: bool = False):
    """履歴テーブル表示"""
    table = Table(title="📚 検索履歴一覧")

    table.add_column("ID", style="cyan", width=6)
    table.add_column("検索クエリ", style="green", width=25)
    table.add_column("タイプ", style="blue", width=12)
    table.add_column("ドメイン", style="magenta", width=15)
    table.add_column("結果数", style="yellow", width=8)
    table.add_column("実行時間", style="red", width=10)
    table.add_column("実行日時", style="white", width=16)

    if verbose:
        table.add_column("形式", width=8)
        table.add_column("Obsidian", width=8)

    for history in histories:
        # 実行時間フォーマット
        exec_time = (
            f"{
            history['execution_time_seconds']:.1f}s"
            if history["execution_time_seconds"]
            else "N/A"
        )

        # 日時フォーマット
        timestamp = datetime.fromisoformat(history["timestamp"].replace("Z", "+00:00"))
        formatted_time = timestamp.strftime("%m/%d %H:%M")

        # ドメイン名の短縮
        domain_short = {
            "sales_psychology": "営業心理",
            "management_psychology": "マネジメント",
            "behavioral_economics": "行動経済",
            "universal_psychology": "汎用心理",
        }.get(history["domain"], history["domain"] or "-")

        # 基本カラム
        row = [
            str(history["id"]),
            (
                history["query"][:23] + "..."
                if len(history["query"]) > 23
                else history["query"]
            ),
            history["search_type"],
            domain_short,
            str(history["total_results"]),
            exec_time,
            formatted_time,
        ]

        # 詳細カラム
        if verbose:
            row.extend(
                [
                    history["output_format"],
                    "✅" if history["saved_to_obsidian"] else "❌",
                ]
            )

        table.add_row(*row)

    console.print(table)
    console.print(f"\n📊 合計: {len(histories)}件")


def _display_history_detail(history: Dict[str, Any], results: List[Dict[str, Any]]):
    """履歴詳細表示"""
    # 基本情報パネル
    info_text = f"""
🔍 検索クエリ: {history['query']}
📋 検索タイプ: {history['search_type']}
🎯 ドメイン: {history['domain'] or 'N/A'}
🧠 思考モード: {history['thinking_mode'] or 'N/A'}
📊 最大結果数: {history['max_results']}
📄 出力形式: {history['output_format']}
⏱️ 実行時間: {history['execution_time_seconds']:.2f}秒
📈 実際結果数: {history['total_results']}
🗂️ Obsidian保存: {'✅' if history['saved_to_obsidian'] else '❌'}
📅 実行日時: {history['timestamp']}
"""

    if history["notes"]:
        info_text += f"\n📝 ノート: {history['notes']}"

    console.print(Panel(info_text.strip(), title="📋 検索情報", border_style="blue"))

    # 検索結果詳細
    if results:
        results_table = Table(title="📄 検索結果詳細")
        results_table.add_column("順位", width=6)
        results_table.add_column("タイトル", width=35)
        results_table.add_column("年", width=6)
        results_table.add_column("引用数", width=8)
        results_table.add_column("API", width=12)
        results_table.add_column("スコア", width=8)

        for result in results:
            relevance_score = (
                f"{
                result['relevance_score']:.1f}"
                if result["relevance_score"]
                else "N/A"
            )
            title_truncated = (
                result["title"][:33] + "..."
                if len(result["title"]) > 33
                else result["title"]
            )

            results_table.add_row(
                str(result["rank_position"]),
                title_truncated,
                (
                    str(result["publication_year"])
                    if result["publication_year"]
                    else "N/A"
                ),
                str(result["citation_count"]) if result["citation_count"] else "0",
                result["api_source"],
                relevance_score,
            )

        console.print(results_table)
    else:
        console.print("❌ 検索結果の詳細データがありません")


def _display_statistics(stats: Dict[str, Any]):
    """統計表示"""
    basic = stats.get("basic", {})

    # 基本統計
    basic_panel = f"""
📊 総検索回数: {basic.get('total_searches', 0)}件
🔍 ユニーク検索: {basic.get('unique_queries', 0)}件
📈 平均結果数: {basic.get('avg_results', 0):.1f}件/回
⏱️ 平均実行時間: {basic.get('avg_execution_time', 0):.1f}秒
🗂️ Obsidian保存: {basic.get('saved_to_obsidian_count', 0)}件
"""

    console.print(Panel(basic_panel.strip(), title="📊 基本統計", border_style="green"))

    # 人気キーワード
    popular_keywords = stats.get("popular_keywords", [])
    if popular_keywords:
        keywords_table = Table(title="🔥 人気キーワード TOP10")
        keywords_table.add_column("順位", width=6)
        keywords_table.add_column("キーワード", width=30)
        keywords_table.add_column("検索回数", width=10)

        for i, keyword in enumerate(popular_keywords, 1):
            keywords_table.add_row(
                str(i), keyword["keyword"], str(keyword["search_count"])
            )

        console.print(keywords_table)

    # ドメイン別統計
    domain_stats = stats.get("domain_stats", [])
    if domain_stats:
        domain_table = Table(title="🎯 ドメイン別検索")
        domain_table.add_column("ドメイン", width=20)
        domain_table.add_column("検索回数", width=10)

        for domain in domain_stats:
            domain_name = {
                "sales_psychology": "営業心理学",
                "management_psychology": "マネジメント心理学",
                "behavioral_economics": "行動経済学",
                "universal_psychology": "汎用心理学",
            }.get(domain["domain"], domain["domain"])

            domain_table.add_row(domain_name, str(domain["count"]))

        console.print(domain_table)

    # API使用統計
    api_stats = stats.get("api_stats", [])
    if api_stats:
        api_table = Table(title="🔌 API使用統計")
        api_table.add_column("API", width=15)
        api_table.add_column("使用回数", width=10)

        for api in api_stats:
            api_table.add_row(api["api_source"].title(), str(api["count"]))

        console.print(api_table)


def _display_trend_analysis(histories: List[Dict[str, Any]], granularity: str):
    """トレンド分析表示"""
    from collections import defaultdict, Counter

    # 日付別集計
    date_counts = defaultdict(int)
    date_exec_times = defaultdict(list)
    date_domains = defaultdict(Counter)

    for history in histories:
        timestamp = datetime.fromisoformat(history["timestamp"].replace("Z", "+00:00"))

        if granularity == "week":
            # 週の開始日（月曜日）を計算
            days_since_monday = timestamp.weekday()
            week_start = timestamp - timedelta(days=days_since_monday)
            date_key = week_start.strftime("%Y-%m-%d")
        else:
            date_key = timestamp.strftime("%Y-%m-%d")

        date_counts[date_key] += 1

        if history["execution_time_seconds"]:
            date_exec_times[date_key].append(history["execution_time_seconds"])

        if history["domain"]:
            date_domains[date_key][history["domain"]] += 1

    # 日別検索回数テーブル
    if date_counts:
        trend_table = Table(title=f"📅 {granularity}別検索トレンド")
        trend_table.add_column("日付", width=12)
        trend_table.add_column("検索回数", width=10)
        trend_table.add_column("平均実行時間", width=12)
        trend_table.add_column("主要ドメイン", width=15)

        sorted_dates = sorted(date_counts.keys(), reverse=True)[:14]  # 最新14日/週

        for date_key in sorted_dates:
            count = date_counts[date_key]

            # 平均実行時間
            exec_times = date_exec_times[date_key]
            avg_time = (
                f"{
                sum(exec_times) /
                len(exec_times):.1f}s"
                if exec_times
                else "N/A"
            )

            # 主要ドメイン
            domain_counter = date_domains[date_key]
            top_domain = (
                domain_counter.most_common(1)[0][0] if domain_counter else "N/A"
            )
            domain_display = {
                "sales_psychology": "営業心理",
                "management_psychology": "マネジメント",
                "behavioral_economics": "行動経済",
                "universal_psychology": "汎用心理",
            }.get(top_domain, top_domain)

            trend_table.add_row(date_key, str(count), avg_time, domain_display)

        console.print(trend_table)

    # キーワード分析
    keyword_analysis = _analyze_keywords([h["query"] for h in histories])
    if keyword_analysis:
        keyword_table = Table(title="🔤 キーワード分析")
        keyword_table.add_column("キーワード", width=20)
        keyword_table.add_column("出現回数", width=10)
        keyword_table.add_column("関連語", width=30)

        for keyword, data in keyword_analysis.items():
            related = ", ".join(data["related"][:3])  # 上位3つの関連語
            keyword_table.add_row(keyword, str(data["count"]), related)

        console.print(keyword_table)


def _display_performance_analysis(histories: List[Dict[str, Any]]):
    """パフォーマンス分析表示"""
    from statistics import mean, median

    # 実行時間分析
    exec_times = [
        h["execution_time_seconds"] for h in histories if h["execution_time_seconds"]
    ]
    result_counts = [h["total_results"] for h in histories]

    if exec_times:
        perf_stats = f"""
⚡ 実行時間統計:
  • 平均: {mean(exec_times):.2f}秒
  • 中央値: {median(exec_times):.2f}秒
  • 最速: {min(exec_times):.2f}秒
  • 最遅: {max(exec_times):.2f}秒

📊 結果数統計:
  • 平均結果数: {mean(result_counts):.1f}件
  • 最大結果数: {max(result_counts)}件
  • 最小結果数: {min(result_counts)}件
"""

        console.print(
            Panel(
                perf_stats.strip(), title="📊 基本パフォーマンス", border_style="yellow"
            )
        )

    # 検索タイプ別パフォーマンス
    type_performance = {}
    for history in histories:
        search_type = history["search_type"]
        if search_type not in type_performance:
            type_performance[search_type] = {"times": [], "results": []}

        if history["execution_time_seconds"]:
            type_performance[search_type]["times"].append(
                history["execution_time_seconds"]
            )
        type_performance[search_type]["results"].append(history["total_results"])

    if type_performance:
        type_table = Table(title="🔍 検索タイプ別パフォーマンス")
        type_table.add_column("検索タイプ", width=15)
        type_table.add_column("平均実行時間", width=12)
        type_table.add_column("平均結果数", width=10)
        type_table.add_column("検索回数", width=8)

        for search_type, data in type_performance.items():
            avg_time = (
                f"{
                mean(
                    data['times']):.2f}s"
                if data["times"]
                else "N/A"
            )
            avg_results = (
                f"{
                mean(
                    data['results']):.1f}"
                if data["results"]
                else "N/A"
            )

            type_table.add_row(
                search_type, avg_time, avg_results, str(len(data["results"]))
            )

        console.print(type_table)

    # 時間帯別分析
    hour_counts = {}
    for history in histories:
        timestamp = datetime.fromisoformat(history["timestamp"].replace("Z", "+00:00"))
        hour = timestamp.hour
        hour_counts[hour] = hour_counts.get(hour, 0) + 1

    if hour_counts:
        # 最もアクティブな時間帯を特定
        peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        peak_lines = [
            f"🕐 検索時間帯分析:",
            f"  • 最もアクティブ: {peak_hours[0][0]:02d}:00 ({peak_hours[0][1]}回)",
        ]

        if len(peak_hours) > 1:
            peak_lines.append(
                f"  • 2番目: {
                    peak_hours[1][0]:02d}:00 ({
                    peak_hours[1][1]}回)"
            )
        if len(peak_hours) > 2:
            peak_lines.append(
                f"  • 3番目: {
                    peak_hours[2][0]:02d}:00 ({
                    peak_hours[2][1]}回)"
            )

        peak_text = "\n".join(peak_lines)

        console.print(
            Panel(peak_text.strip(), title="🕒 時間帯分析", border_style="green")
        )


def _analyze_keywords(queries: List[str]) -> Dict[str, Dict]:
    """キーワード分析"""
    import re
    from collections import Counter, defaultdict

    # すべてのクエリからキーワードを抽出
    all_words = []
    word_cooccurrence = defaultdict(Counter)

    for query in queries:
        # 英語と日本語の単語を抽出
        words = re.findall(r"\b[a-zA-Z]{3,}\b|[ぁ-んァ-ヶ一-龠]{2,}", query.lower())
        all_words.extend(words)

        # 共起関係を記録
        for i, word1 in enumerate(words):
            for word2 in words[i + 1 :]:
                word_cooccurrence[word1][word2] += 1
                word_cooccurrence[word2][word1] += 1

    # 頻出キーワード（3回以上出現）
    word_counts = Counter(all_words)
    frequent_words = {word: count for word, count in word_counts.items() if count >= 2}

    # 関連語の特定
    result = {}
    for word, count in frequent_words.items():
        related_words = word_cooccurrence[word].most_common(5)
        result[word] = {"count": count, "related": [w for w, _ in related_words]}

    # 頻度順でソート
    return dict(sorted(result.items(), key=lambda x: x[1]["count"], reverse=True)[:10])


if __name__ == "__main__":
    history_cli()
