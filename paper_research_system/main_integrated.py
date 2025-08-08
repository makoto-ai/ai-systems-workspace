"""
Academic Paper Research Assistant - Integrated Search Version
論文リサーチ支援システム - 統合検索版
"""

import time
from core.paper_model import Paper
from services.advanced_filter_engine import get_filter_engine, SearchFilters
from services.recommendation_engine import get_recommendation_engine
from services.search_history_db import get_search_history_db
from services.obsidian_paper_saver import ObsidianPaperSaver
from services.safe_rate_limited_search_service import (
    get_safe_rate_limited_search_service,
)
import asyncio
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import List
import click
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))


console = Console()
logger = logging.getLogger(__name__)


@click.command()
@click.argument("query", type=str)
@click.option("--max-results", "-n", default=10, help="最大検索結果数")
@click.option(
    "--output-format",
    "-f",
    default="table",
    type=click.Choice(["table", "chatgpt"]),
    help="出力フォーマット",
)
@click.option("--verbose", "-v", is_flag=True, help="詳細出力")
@click.option("--save-obsidian", is_flag=True, help="検索結果をObsidianに自動保存")
@click.option("--no-history", is_flag=True, help="履歴を記録しない")
@click.option(
    "--with-recommendations",
    is_flag=True,
    help="関連論文推薦を生成（時間がかかります）",
)
@click.option("--year-from", type=int, help="開始年度（例: 2020）")
@click.option("--year-to", type=int, help="終了年度（例: 2025）")
@click.option("--min-citations", type=int, help="最小引用数")
@click.option("--authors", help="著者名（カンマ区切り）")
@click.option("--journals", help="ジャーナル名（カンマ区切り）")
@click.option("--require-doi", is_flag=True, help="DOI必須")
@click.option("--require-abstract", is_flag=True, help="概要必須")
def search_papers_integrated(
    query: str,
    max_results: int,
    output_format: str,
    verbose: bool,
    save_obsidian: bool,
    no_history: bool,
    with_recommendations: bool,
    year_from: int,
    year_to: int,
    min_citations: int,
    authors: str,
    journals: str,
    require_doi: bool,
    require_abstract: bool,
):
    """
    統合論文検索システム

    3つのAPI（OpenAlex、CrossRef、Semantic Scholar）から
    論文を検索して、重複除去・ランキングした結果を提供します。

    対象分野: 営業・マネジメント・心理学・組織行動・リーダーシップ
    """
    console.print(
        Panel.fit(
            "🎯 Academic Paper Research Assistant\n統合検索システム (3 APIs - レート制限完全対応)",
            style="bold blue",
        )
    )

    console.print(f"🔍 検索クエリ: {query}")
    console.print(f"📊 最大結果数: {max_results}")
    console.print(f"📄 出力形式: {output_format}")

    # フィルタ設定
    filters = SearchFilters(
        year_from=year_from,
        year_to=year_to,
        min_citations=min_citations,
        authors=authors.split(",") if authors else None,
        journals=journals.split(",") if journals else None,
        require_doi=require_doi,
        require_abstract=require_abstract,
    )

    # フィルタ有効性チェック
    has_filters = any(
        [
            year_from,
            year_to,
            min_citations,
            authors,
            journals,
            require_doi,
            require_abstract,
        ]
    )
    if has_filters:
        filter_summary = get_filter_engine().create_filter_summary(filters)
        console.print(f"🔧 適用フィルタ: {filter_summary}")

    if verbose:
        logging.basicConfig(level=logging.INFO)

    # 統合検索実行 + 履歴記録
    search_service = get_safe_rate_limited_search_service()

    # 実行時間測定
    start_time = time.time()
    papers = asyncio.run(
        search_service.search_papers(
            query, max_results * 2 if has_filters else max_results
        )
    )  # フィルタ適用時は多めに取得
    search_time = time.time() - start_time

    if verbose:
        console.print(
            f"✅ 統合検索完了: {len(papers)}件取得 (検索時間: {search_time:.2f}秒)"
        )

    # フィルタ適用
    if has_filters and papers:
        filter_engine = get_filter_engine()
        filter_start_time = time.time()
        original_count = len(papers)
        papers = filter_engine.apply_filters(papers, filters)
        filter_time = time.time() - filter_start_time

        if verbose:
            console.print(
                f"🔧 フィルタ適用: {original_count}件 → {
                    len(papers)}件 (フィルタ時間: {
                    filter_time:.2f}秒)"
            )

        # 結果数調整
        papers = papers[:max_results]

    execution_time = time.time() - start_time

    # 関連論文推薦生成
    recommendations = []
    if with_recommendations and papers:
        try:
            if verbose:
                console.print("🔍 関連論文推薦を生成中...")

            recommendation_engine = get_recommendation_engine()
            rec_start_time = time.time()
            recommendations = asyncio.run(
                recommendation_engine.generate_recommendations(
                    source_papers=papers, max_recommendations=5, expand_search=True
                )
            )
            rec_time = time.time() - rec_start_time

            if verbose:
                console.print(
                    f"✅ 推薦生成完了: {
                        len(recommendations)}件 (推薦時間: {
                        rec_time:.2f}秒)"
                )

        except Exception as e:
            logger.error(f"推薦生成エラー: {e}")
            if verbose:
                console.print("⚠️ 推薦生成に失敗しましたが、検索は正常に完了しました")

    # 履歴記録
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
                search_type="integrated",
                max_results=max_results,
                output_format=output_format,
                results=papers,
                execution_time=execution_time,
                api_calls=api_usage,
                saved_to_obsidian=save_obsidian,
            )

            if verbose:
                console.print(f"📊 検索履歴記録完了: ID={history_id}")

        except Exception as e:
            logger.error(f"履歴記録エラー: {e}")
            if verbose:
                console.print("⚠️ 履歴記録に失敗しましたが、検索は正常に完了しました")

    # 結果出力
    if output_format == "table":
        _display_table(papers, save_obsidian, query, recommendations)
    elif output_format == "chatgpt":
        _display_chatgpt_format(papers, recommendations)


def _display_table(
    papers: List[Paper],
    save_obsidian: bool = False,
    query: str = "",
    recommendations: List = None,
):
    """表形式で結果を表示"""
    if not papers:
        console.print("❌ 検索結果がありません")
        return

    table = Table(
        title="📚 統合検索結果", show_header=True, header_style="bold magenta"
    )
    table.add_column("タイトル", style="cyan", width=40)
    table.add_column("著者", style="green", width=20)
    table.add_column("年", justify="center", width=8)
    table.add_column("引用数", justify="right", width=10)
    table.add_column("API", justify="center", width=15)
    table.add_column("スコア", justify="right", width=8)

    for paper in papers:
        # 著者名を結合
        author_names = [author.name for author in paper.authors[:2]]
        if len(paper.authors) > 2:
            author_names.append(f"他{len(paper.authors) - 2}名")
        authors_str = ", ".join(author_names)

        # タイトルを短縮
        title = paper.title[:60] + "..." if len(paper.title) > 60 else paper.title

        # スコア表示
        score_str = f"{paper.total_score:.1f}" if paper.total_score else "N/A"

        table.add_row(
            title,
            authors_str,
            str(paper.publication_year) if paper.publication_year else "N/A",
            str(paper.citation_count) if paper.citation_count else "0",
            paper.source_api.title(),
            score_str,
        )

    console.print(table)

    # Obsidian自動保存
    if save_obsidian:
        try:
            obsidian_saver = ObsidianPaperSaver()
            saved_path = obsidian_saver.save_search_results(
                papers=papers,
                search_query=query,
                domain="general_research",  # 統合検索では汎用ドメイン
                thinking_mode="general",
                metadata={"total_found": len(papers), "final_results": len(papers)},
            )
            console.print("\n📚 [bold green]Obsidian保存完了![/bold green]")
            console.print("📁 保存先: " + saved_path.name)
        except Exception as e:
            console.print("\n❌ [bold red]Obsidian保存エラー:[/bold red] " + str(e))

    console.print("\n💡 使用方法:")
    console.print("この結果をChatGPTやClaudeに投げて要約・原稿化してください")
    console.print("--output-format chatgpt で直接コピペ用の形式を取得できます")
    console.print("--save-obsidian でObsidianに自動保存できます")

    # 関連論文推薦表示
    if recommendations:
        _display_recommendations(recommendations)

    console.print("\n📊 履歴管理:")
    console.print("[bold cyan]python3 main_history.py list[/bold cyan] - 検索履歴一覧")
    console.print("[bold cyan]python3 main_history.py stats[/bold cyan] - 検索統計")
    console.print(
        "[bold cyan]python3 main_history.py performance[/bold cyan] - パフォーマンス分析"
    )


def _display_recommendations(recommendations: List) -> None:
    """関連論文推薦を表示"""
    if not recommendations:
        return

    console.print("\n" + "=" * 60)
    console.print("🔗 関連論文推薦", style="bold magenta")
    console.print("=" * 60)

    rec_table = Table(title="📚 あなたにおすすめの関連論文")
    rec_table.add_column("順位", style="cyan", width=6)
    rec_table.add_column("タイトル", style="green", width=35)
    rec_table.add_column("著者", style="blue", width=20)
    rec_table.add_column("年", style="yellow", width=6)
    rec_table.add_column("類似度", style="red", width=8)
    rec_table.add_column("推薦理由", style="magenta", width=20)

    for i, (paper, similarity, reason) in enumerate(recommendations, 1):
        # 著者名の短縮
        author_names = []
        if paper.authors:
            for author in paper.authors[:2]:  # 最初の2名のみ
                if author.name:
                    author_names.append(author.name)
        author_text = ", ".join(author_names)
        if len(paper.authors) > 2:
            author_text += f", 他{len(paper.authors) - 2}名"

        # タイトルの短縮
        title_text = paper.title[:33] + "..." if len(paper.title) > 33 else paper.title

        rec_table.add_row(
            str(i),
            title_text,
            author_text,
            str(paper.publication_year) if paper.publication_year else "N/A",
            f"{similarity:.2f}",
            reason[:18] + "..." if len(reason) > 18 else reason,
        )

    console.print(rec_table)
    console.print(f"\n💡 推薦論文数: {len(recommendations)}件")
    console.print("💡 これらの論文は検索結果と関連性が高い論文です")


def _display_chatgpt_format(papers: List[Paper], recommendations: List = None):
    """ChatGPT/Claude投入用フォーマットで表示"""
    console.print("\n" + "=" * 60)
    console.print("ChatGPT/Claude投入用データ（コピペ可能）")
    console.print("=" * 60 + "\n")

    for i, paper in enumerate(papers, 1):
        print(f"{i}. ## 📄 {paper.title}")
        print()

        # 著者情報
        author_names = [author.name for author in paper.authors]
        print(f"**著者**: {', '.join(author_names)}")

        # 基本情報
        if paper.publication_year:
            print(f"**発表年**: {paper.publication_year}")
        if paper.citation_count:
            print(f"**引用数**: {paper.citation_count}")
        if paper.doi:
            print(f"**DOI**: {paper.doi}")
        if paper.url:
            print(f"**URL**: {paper.url}")

        print()

        # 概要
        if paper.abstract:
            print("**概要**:")
            print(paper.abstract)
            print()
        else:
            print("**概要**: 概要なし")
            print()

        # メタデータ
        if paper.institutions:
            inst_names = [inst.name for inst in paper.institutions[:2]]
            print(f"**所属機関**: {', '.join(inst_names)}")

        if paper.journal:
            print(f"**ジャーナル**: {paper.journal}")

        print(f"**データソース**: {paper.source_api.title()}")

        if paper.total_score:
            print(f"**総合スコア**: {paper.total_score:.2f}")

        print()

    # 推薦論文をChatGPT形式に含める
    if recommendations:
        print("\n" + "=" * 50)
        print("🔗 関連論文推薦")
        print("=" * 50)

        for i, (paper, similarity, reason) in enumerate(recommendations, 1):
            print(f"\n## 推薦論文 {i}: {paper.title}")

            if paper.authors:
                author_names = [author.name for author in paper.authors if author.name]
                print(f"📝 著者: {', '.join(author_names[:3])}")
                if len(author_names) > 3:
                    print(f"   他{len(author_names) - 3}名")

            if paper.publication_year:
                print(f"📅 発行年: {paper.publication_year}")

            if paper.citation_count:
                print(f"📊 引用数: {paper.citation_count}")

            print(f"🎯 類似度: {similarity:.2f}")
            print(f"💡 推薦理由: {reason}")

            if paper.abstract:
                abstract_preview = (
                    paper.abstract[:200] + "..."
                    if len(paper.abstract) > 200
                    else paper.abstract
                )
                print(f"📄 概要: {abstract_preview}")

            if paper.doi:
                print(f"🔗 DOI: {paper.doi}")
            elif paper.url:
                print(f"🔗 URL: {paper.url}")

        print("\n💡 これらの推薦論文は、検索結果と高い関連性を持つ論文です。")
        print("💡 研究の幅を広げるために、ぜひご活用ください。")

    print("\n" + "=" * 60)
    print("📝 指示例:")
    print("「上記の論文情報を基に、営業スキル向上に関する原稿を作成してください」")
    print()
    console.print("💡 使用方法:")
    console.print("この結果をChatGPTやClaudeに投げて要約・原稿化してください")


if __name__ == "__main__":
    search_papers_integrated()
