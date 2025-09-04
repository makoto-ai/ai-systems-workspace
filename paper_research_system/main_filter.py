"""
Interactive Advanced Filter CLI for Academic Paper Search
学術論文検索用インタラクティブ高度フィルタCLI
"""

import time
from .core.paper_model import Paper
from .services.search_history_db import get_search_history_db
from .services.obsidian_paper_saver import ObsidianPaperSaver
from .services.safe_rate_limited_search_service import (
    get_safe_rate_limited_search_service,
)
from .services.advanced_filter_engine import SearchFilters, get_filter_engine
import asyncio
import click
import logging
import sys
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm

sys.path.append(str(Path(__file__).parent))


console = Console()
logger = logging.getLogger(__name__)


@click.command()
@click.argument("query", required=True)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    default=True,
    help="インタラクティブフィルタ設定",
)
@click.option(
    "--preset",
    "-p",
    type=click.Choice(["recent", "highly_cited", "peer_reviewed"]),
    help="プリセットフィルタ",
)
@click.option("--save-obsidian", is_flag=True, help="検索結果をObsidianに自動保存")
@click.option("--no-history", is_flag=True, help="履歴を記録しない")
@click.option("--verbose", "-v", is_flag=True, help="詳細出力")
def advanced_search(
    query: str,
    interactive: bool,
    preset: Optional[str],
    save_obsidian: bool,
    no_history: bool,
    verbose: bool,
):
    """
    高度フィルタ付き論文検索システム

    インタラクティブに詳細な検索条件を設定して、
    精密な論文検索を実行します。

    使用例:
        python3 main_filter.py "machine learning" --interactive
        python3 main_filter.py "sales psychology" --preset recent
    """
    console.print(
        Panel.fit(
            "🎯 Advanced Academic Paper Search\n高度フィルタ付き論文検索システム",
            style="bold blue",
        )
    )

    console.print(f"🔍 検索クエリ: [bold cyan]{query}[/bold cyan]")

    # フィルタ設定
    if preset:
        filters = _create_preset_filter(preset)
        console.print(f"📋 プリセット適用: [bold green]{preset}[/bold green]")
    elif interactive:
        filters = _interactive_filter_setup()
    else:
        filters = SearchFilters()  # フィルタなし

    if filters:
        filter_summary = get_filter_engine().create_filter_summary(filters)
        console.print(f"🔧 適用フィルタ: {filter_summary}")

    # 検索実行
    search_service = get_safe_rate_limited_search_service()

    with console.status("[bold green]論文検索中..."):
        start_time = time.time()
        papers = asyncio.run(
            search_service.search_papers(query, max_results=50)
        )  # 多めに取得
        search_time = time.time() - start_time

    console.print(
        f"✅ 初期検索完了: {len(papers)}件取得 (検索時間: {search_time:.2f}秒)"
    )

    # フィルタ適用
    if filters and papers:
        filter_engine = get_filter_engine()
        with console.status("[bold yellow]フィルタ適用中..."):
            filter_start = time.time()
            filtered_papers = filter_engine.apply_filters(papers, filters)
            filter_time = time.time() - filter_start

        console.print(
            f"🔧 フィルタ適用完了: {
                len(papers)}件 → {
                len(filtered_papers)}件 (フィルタ時間: {
                filter_time:.2f}秒)"
        )
        papers = filtered_papers

    # 結果表示
    if papers:
        _display_filtered_results(papers, filters)

        # Obsidian保存
        if save_obsidian:
            try:
                obsidian_saver = ObsidianPaperSaver()
                saved_path = obsidian_saver.save_search_results(
                    query=query,
                    papers=papers,
                    search_type="advanced_filter",
                    metadata={
                        "filters": get_filter_engine().create_filter_summary(filters),
                        "original_count": len(papers),
                        "search_time": search_time,
                    },
                )
                console.print(f"\n📚 [bold green]Obsidian保存完了![/bold green]")
                console.print(f"📁 保存先: {saved_path.name}")
            except Exception as e:
                console.print(f"\n❌ [bold red]Obsidian保存エラー:[/bold red] {e}")
    else:
        console.print("❌ フィルタ条件に一致する論文が見つかりませんでした")
        console.print("💡 フィルタ条件を緩和してみてください")

    # 履歴記録
    total_time = time.time() - start_time
    if not no_history:
        try:
            history_db = get_search_history_db()
            api_usage = {
                "openalex": len([p for p in papers if p.source_api == "openalex"]),
                "crossref": len([p for p in papers if p.source_api == "crossref"]),
                "semantic_scholar": len(
                    [p for p in papers if p.source_api == "semantic_scholar"]
                ),
            }

            history_id = history_db.record_search(
                query=query,
                search_type="advanced_filter",
                max_results=50,
                output_format="table",
                results=papers,
                execution_time=total_time,
                api_calls=api_usage,
                saved_to_obsidian=save_obsidian,
            )
            console.print(f"\n📊 検索履歴記録完了: ID={history_id}")
        except Exception as e:
            logger.error(f"履歴記録エラー: {e}")
            console.print(f"\n⚠️ 履歴記録に失敗しましたが、検索は正常に完了しました")


def _create_preset_filter(preset: str) -> SearchFilters:
    """プリセットフィルタを作成"""
    current_year = 2025

    if preset == "recent":
        return SearchFilters(
            year_from=current_year - 3, require_abstract=True  # 過去3年
        )
    elif preset == "highly_cited":
        return SearchFilters(min_citations=50, require_doi=True, year_from=2010)
    elif preset == "peer_reviewed":
        return SearchFilters(
            require_doi=True,
            require_abstract=True,
            paper_types=["journal"],
            exclude_journals=["arxiv", "preprint"],
        )

    return SearchFilters()


def _interactive_filter_setup() -> Optional[SearchFilters]:
    """インタラクティブフィルタ設定"""
    console.print("\n" + "=" * 60)
    console.print("🔧 [bold cyan]インタラクティブフィルタ設定[/bold cyan]")
    console.print("=" * 60)

    console.print("💡 各項目でフィルタ条件を設定してください（Enterでスキップ）")

    filters = SearchFilters()

    # 年代フィルタ
    if Confirm.ask("\n📅 年代範囲を指定しますか？", default=False):
        try:
            year_from = IntPrompt.ask("開始年", default=2010)
            year_to = IntPrompt.ask("終了年", default=2025)
            if year_from <= year_to:
                filters.year_from = year_from
                filters.year_to = year_to
            else:
                console.print(
                    "⚠️ 開始年が終了年より大きいため、年代フィルタをスキップします"
                )
        except Exception:
            console.print("⚠️ 無効な年度入力、年代フィルタをスキップします")

    # 引用数フィルタ
    if Confirm.ask("\n📊 引用数範囲を指定しますか？", default=False):
        try:
            min_cit = IntPrompt.ask("最小引用数", default=0)
            if Confirm.ask("最大引用数を設定しますか？", default=False):
                max_cit = IntPrompt.ask("最大引用数", default=10000)
                filters.max_citations = max_cit
            filters.min_citations = min_cit
        except Exception:
            console.print("⚠️ 無効な引用数入力、引用数フィルタをスキップします")

    # 著者フィルタ
    if Confirm.ask("\n👥 特定の著者を指定しますか？", default=False):
        authors_input = Prompt.ask("著者名（カンマ区切りで複数指定可能）", default="")
        if authors_input.strip():
            filters.authors = [author.strip() for author in authors_input.split(",")]

    # ジャーナルフィルタ
    if Confirm.ask("\n📚 特定のジャーナル/会議を指定しますか？", default=False):
        journals_input = Prompt.ask(
            "ジャーナル名（カンマ区切りで複数指定可能）", default=""
        )
        if journals_input.strip():
            filters.journals = [
                journal.strip() for journal in journals_input.split(",")
            ]

    # コンテンツ要件
    console.print("\n📋 コンテンツ要件:")
    filters.require_doi = Confirm.ask("DOI必須？", default=False)
    filters.require_abstract = Confirm.ask("概要必須？", default=False)

    # 論文種別
    if Confirm.ask("\n📄 論文種別を指定しますか？", default=False):
        console.print("選択可能な種別:")
        console.print("  1. journal (学術雑誌)")
        console.print("  2. conference (会議)")
        console.print("  3. preprint (プレプリント)")
        console.print("  4. book (書籍)")

        types_input = Prompt.ask("種別番号（カンマ区切りで複数選択可能）", default="")
        if types_input.strip():
            type_map = {"1": "journal", "2": "conference", "3": "preprint", "4": "book"}
            selected_types = []
            for num in types_input.split(","):
                num = num.strip()
                if num in type_map:
                    selected_types.append(type_map[num])
            if selected_types:
                filters.paper_types = selected_types

    # キーワードフィルタ
    if Confirm.ask("\n🔍 必須キーワードを指定しますか？", default=False):
        keywords_input = Prompt.ask(
            "必須キーワード（カンマ区切りで複数指定可能）", default=""
        )
        if keywords_input.strip():
            filters.required_keywords = [kw.strip() for kw in keywords_input.split(",")]

    # フィルタ確認
    if _has_any_filter(filters):
        console.print("\n" + "=" * 60)
        console.print("📋 [bold green]設定されたフィルタ[/bold green]")
        console.print("=" * 60)
        summary = get_filter_engine().create_filter_summary(filters)
        console.print(summary)

        if Confirm.ask("\nこの設定で検索を実行しますか？", default=True):
            return filters
        else:
            console.print("フィルタ設定をキャンセルしました")
            return None
    else:
        console.print("\n💡 フィルタが設定されていません。通常検索を実行します。")
        return None


def _has_any_filter(filters: SearchFilters) -> bool:
    """フィルタが設定されているかチェック"""
    return any(
        [
            filters.year_from,
            filters.year_to,
            filters.min_citations,
            filters.max_citations,
            filters.authors,
            filters.exclude_authors,
            filters.journals,
            filters.exclude_journals,
            filters.require_doi,
            filters.require_abstract,
            filters.allowed_sources,
            filters.required_keywords,
            filters.excluded_keywords,
            filters.paper_types,
        ]
    )


def _display_filtered_results(papers: List[Paper], filters: Optional[SearchFilters]):
    """フィルタ適用結果を表示"""
    console.print("\n" + "=" * 80)
    console.print("📊 [bold green]フィルタ適用結果[/bold green]")
    console.print("=" * 80)

    if not papers:
        console.print("❌ 条件に一致する論文がありません")
        return

    # 結果テーブル
    table = Table(title=f"🎯 高度フィルタ検索結果 ({len(papers)}件)")
    table.add_column("順位", style="cyan", width=6)
    table.add_column("タイトル", style="green", width=40)
    table.add_column("著者", style="blue", width=25)
    table.add_column("年", style="yellow", width=6)
    table.add_column("引用数", style="red", width=8)
    table.add_column("ジャーナル", style="magenta", width=20)
    table.add_column("API", style="bright_black", width=10)

    for i, paper in enumerate(papers[:20], 1):  # 上位20件表示
        # 著者名の短縮
        author_names = []
        if paper.authors:
            for author in paper.authors[:2]:
                if author.name:
                    author_names.append(author.name)
        author_text = ", ".join(author_names)
        if len(paper.authors) > 2:
            author_text += f", 他{len(paper.authors) - 2}名"

        # タイトルの短縮
        title_text = paper.title[:38] + "..." if len(paper.title) > 38 else paper.title

        # ジャーナルの短縮
        journal_text = (
            (paper.journal or "N/A")[:18] + "..."
            if len(paper.journal or "") > 18
            else (paper.journal or "N/A")
        )

        table.add_row(
            str(i),
            title_text,
            author_text,
            str(paper.publication_year) if paper.publication_year else "N/A",
            str(paper.citation_count) if paper.citation_count else "0",
            journal_text,
            paper.source_api.title() if paper.source_api else "N/A",
        )

    console.print(table)

    if len(papers) > 20:
        console.print(
            f"\n💡 表示は上位20件のみです。全{len(papers)}件の結果があります。"
        )

    # フィルタ統計
    _display_filter_statistics(papers)

    console.print("\n💡 [bold cyan]使用方法[/bold cyan]:")
    console.print("  • より詳細な検索: [bold]--interactive[/bold]")
    console.print(
        "  • プリセット使用: [bold]--preset recent/highly_cited/peer_reviewed[/bold]"
    )
    console.print("  • Obsidian保存: [bold]--save-obsidian[/bold]")


def _display_filter_statistics(papers: List[Paper]):
    """フィルタ統計を表示"""
    console.print("\n📈 [bold cyan]検索結果統計[/bold cyan]:")

    # 年度分布
    years = [p.publication_year for p in papers if p.publication_year]
    if years:
        console.print(f"  📅 年度範囲: {min(years)} - {max(years)}")

    # 引用数統計
    citations = [p.citation_count for p in papers if p.citation_count]
    if citations:
        avg_citations = sum(citations) / len(citations)
        console.print(f"  📊 引用数: 平均 {avg_citations:.1f}, 最大 {max(citations)}")

    # API別分布
    api_counts = {}
    for paper in papers:
        api = paper.source_api or "unknown"
        api_counts[api] = api_counts.get(api, 0) + 1

    api_info = ", ".join(
        [f"{api.title()}: {count}件" for api, count in api_counts.items()]
    )
    console.print(f"  🔗 API別: {api_info}")


if __name__ == "__main__":
    advanced_search()
