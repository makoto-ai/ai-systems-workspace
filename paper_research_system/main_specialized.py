"""
Academic Paper Research Assistant - Specialized Search for Sales & Management Psychology
論文リサーチ支援システム - 営業・マネジメント心理学特化版
"""

import time
from core.paper_model import Paper
from services.advanced_filter_engine import get_filter_engine, SearchFilters
from services.recommendation_engine import get_recommendation_engine
from services.search_history_db import get_search_history_db
from services.obsidian_paper_saver import ObsidianPaperSaver
from services.specialized_search_service import get_specialized_search_service
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
@click.argument('query', type=str)
@click.option('--domain', '-d', default='sales_psychology',
              type=click.Choice(['sales_psychology',
                                 'management_psychology',
                                 'behavioral_economics',
                                 'universal_psychology']),
              help='専門分野選択')
@click.option('--thinking-mode', '-t', default='thesis',
              type=click.Choice(
                  ['thesis', 'antithesis', 'synthesis', 'meta_analysis']),
              help='クリティカルシンキングモード')
@click.option('--max-results', '-n', default=8, help='最大検索結果数')
@click.option('--output-format', '-f', default='specialized',
              type=click.Choice(['specialized', 'table', 'chatgpt']),
              help='出力フォーマット')
@click.option('--verbose', '-v', is_flag=True, help='詳細出力')
@click.option('--save-obsidian', is_flag=True, help='検索結果をObsidianに自動保存')
@click.option('--no-history', is_flag=True, help='履歴を記録しない')
@click.option('--with-recommendations', is_flag=True,
              help='関連論文推薦を生成（時間がかかります）')
@click.option('--year-from', type=int, help='開始年度（例: 2020）')
@click.option('--min-citations', type=int, help='最小引用数')
@click.option('--require-abstract', is_flag=True, help='概要必須')
def specialized_search(query: str, domain: str, thinking_mode: str, max_results: int, output_format: str, verbose: bool,
                       save_obsidian: bool, no_history: bool, with_recommendations: bool, year_from: int, min_citations: int, require_abstract: bool):
    """
    営業・マネジメント心理学特化検索システム

    🎯 分野特化:
    - sales_psychology: 営業心理学・行動経済学・神経科学
    - management_psychology: リーダーシップ・チーム・動機づけ
    - behavioral_economics: 意思決定・社会心理・市場行動
    - universal_psychology: 認知・性格・社会心理学

    🧠 クリティカルシンキングモード:
    - thesis: 主流理論・確立された研究（引用数重視）
    - antithesis: 批判・反証・限界研究（関連性重視）
    - synthesis: 統合・発展・応用研究（総合評価）
    - meta_analysis: メタ分析・系統的レビュー重視
    """

    # ヘッダー表示
    domain_names = {
        'sales_psychology': '営業心理学',
        'management_psychology': 'マネジメント心理学',
        'behavioral_economics': '行動経済学',
        'universal_psychology': '汎用心理学'
    }

    mode_names = {
        'thesis': 'テーゼ（主流理論）',
        'antithesis': 'アンチテーゼ（批判研究）',
        'synthesis': 'ジンテーゼ（統合理論）',
        'meta_analysis': 'メタ分析重視'
    }

    header_text = f"🎯 {domain_names[domain]} × 🧠 {mode_names[thinking_mode]}"
    console.print(Panel.fit(header_text, style="bold blue"))

    console.print(f"🔍 検索クエリ: {query}")
    console.print(f"📊 最大結果数: {max_results}")
    console.print(f"📄 出力形式: {output_format}")

    # フィルタ設定
    filters = SearchFilters(
        year_from=year_from,
        min_citations=min_citations,
        require_abstract=require_abstract
    )

    # フィルタ有効性チェック
    has_filters = any([year_from, min_citations, require_abstract])
    if has_filters:
        filter_summary = get_filter_engine().create_filter_summary(filters)
        console.print(f"🔧 適用フィルタ: {filter_summary}")

    if verbose:
        logging.basicConfig(level=logging.INFO)

    # 特化検索実行 + 履歴記録
    search_service = get_specialized_search_service()

    # 実行時間測定
    start_time = time.time()
    papers, metadata = asyncio.run(search_service.specialized_search(
        query, domain, thinking_mode, max_results * 2 if has_filters else max_results
    ))
    search_time = time.time() - start_time

    if verbose:
        console.print(
            f"✅ 特化検索完了: {
                metadata['filtering_stats']} (検索時間: {
                search_time:.2f}秒)")

    # 追加フィルタ適用
    if has_filters and papers:
        filter_engine = get_filter_engine()
        filter_start_time = time.time()
        original_count = len(papers)
        papers = filter_engine.apply_filters(papers, filters)
        filter_time = time.time() - filter_start_time

        if verbose:
            console.print(
                f"🔧 追加フィルタ適用: {original_count}件 → {
                    len(papers)}件 (フィルタ時間: {
                    filter_time:.2f}秒)")

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
                    source_papers=papers,
                    max_recommendations=5,
                    expand_search=True
                )
            )
            rec_time = time.time() - rec_start_time

            if verbose:
                console.print(
                    f"✅ 推薦生成完了: {
                        len(recommendations)}件 (推薦時間: {
                        rec_time:.2f}秒)")

        except Exception as e:
            logger.error(f"推薦生成エラー: {e}")
            if verbose:
                console.print(f"⚠️ 推薦生成に失敗しましたが、検索は正常に完了しました")

    # 履歴記録
    if not no_history:
        try:
            history_db = get_search_history_db()
            api_usage = {
                "openalex": len([p for p in papers if p.source_api == "openalex"]),
                "crossref": len([p for p in papers if p.source_api == "crossref"]),
                "semantic_scholar": len([p for p in papers if p.source_api == "semantic_scholar"])
            }

            history_id = history_db.record_search(
                query=query,
                search_type="specialized",
                max_results=max_results,
                output_format=output_format,
                results=papers,
                execution_time=execution_time,
                domain=domain,
                thinking_mode=thinking_mode,
                api_calls=api_usage,
                saved_to_obsidian=save_obsidian
            )

            if verbose:
                console.print(f"📊 検索履歴記録完了: ID={history_id}")

        except Exception as e:
            logger.error(f"履歴記録エラー: {e}")
            if verbose:
                console.print(f"⚠️ 履歴記録に失敗しましたが、検索は正常に完了しました")

    # 結果出力
    if output_format == 'specialized':
        _display_specialized_format(papers, metadata, recommendations)
    elif output_format == 'table':
        _display_table(papers, recommendations)
    elif output_format == 'chatgpt':
        _display_chatgpt_format(papers, metadata, recommendations)

    # Obsidian自動保存
    if save_obsidian:
        try:
            obsidian_saver = ObsidianPaperSaver()
            saved_path = obsidian_saver.save_search_results(
                papers=papers,
                search_query=query,
                domain=domain,
                thinking_mode=thinking_mode,
                metadata=metadata['filtering_stats']
            )
            console.print(f"\n📚 [bold green]Obsidian保存完了![/bold green]")
            console.print(f"📁 保存先: {saved_path.name}")
        except Exception as e:
            console.print(f"\n❌ [bold red]Obsidian保存エラー:[/bold red] {e}")


def _display_specialized_format(
        papers: List[Paper], metadata: dict, recommendations: List = None):
    """特化フォーマットで結果を表示"""
    if not papers:
        console.print("❌ 検索結果がありません")
        return

    # メタデータ表示
    console.print("\n📊 [bold cyan]検索統計[/bold cyan]")
    stats = metadata['filtering_stats']
    console.print(f"  • 総検索数: {stats['total_found']}件")
    console.print(f"  • フィルタ後: {stats['after_filtering']}件")
    console.print(f"  • 最終結果: {stats['final_results']}件")

    # 結果テーブル
    table = Table(
        title="🎯 特化検索結果",
        show_header=True,
        header_style="bold magenta")
    table.add_column("ランク", justify="center", width=6)
    table.add_column("タイトル", style="cyan", width=35)
    table.add_column("著者", style="green", width=18)
    table.add_column("年", justify="center", width=6)
    table.add_column("引用数", justify="right", width=8)
    table.add_column("特化スコア", justify="right", width=10)
    table.add_column("種別", justify="center", width=12)

    for i, paper in enumerate(papers, 1):
        # 著者名を結合
        author_names = [author.name for author in paper.authors[:2]]
        if len(paper.authors) > 2:
            author_names.append(f"他{len(paper.authors) - 2}名")
        authors_str = ", ".join(author_names)

        # タイトルを短縮
        title = paper.title[:50] + \
            "..." if len(paper.title) > 50 else paper.title

        # 特化スコア
        spec_score = getattr(paper, 'specialized_score', 0)
        score_str = f"{spec_score:.1f}" if spec_score else "N/A"

        # 論文種別判定
        paper_type = _determine_paper_type(paper)

        # ランク色分け
        rank_style = "bold red" if i <= 3 else "bold yellow" if i <= 5 else "dim"

        table.add_row(
            f"[{rank_style}]{i}[/{rank_style}]",
            title,
            authors_str,
            str(paper.publication_year) if paper.publication_year else "N/A",
            str(paper.citation_count) if paper.citation_count else "0",
            score_str,
            paper_type
        )

    console.print(table)

    # 使用方法
    console.print("\n💡 [bold green]活用方法[/bold green]")
    console.print("  • ChatGPT形式: --output-format chatgpt")
    console.print("  • 批判的視点: --thinking-mode antithesis")
    console.print("  • 統合理論: --thinking-mode synthesis")
    console.print("  • メタ分析: --thinking-mode meta_analysis")

    # 推薦論文表示
    if recommendations:
        _display_recommendations_specialized(recommendations)

    console.print("\n📊 [bold green]履歴管理[/bold green]:")
    console.print(
        "  • [bold cyan]python3 main_history.py list[/bold cyan] - 検索履歴一覧")
    console.print(
        "  • [bold cyan]python3 main_history.py stats[/bold cyan] - 検索統計")
    console.print(
        "  • [bold cyan]python3 main_history.py performance[/bold cyan] - パフォーマンス分析")


def _display_recommendations_specialized(recommendations: List) -> None:
    """特化検索向け推薦表示"""
    if not recommendations:
        return

    console.print("\n" + "=" * 60)
    console.print("🔗 関連論文推薦", style="bold magenta")
    console.print("=" * 60)

    rec_table = Table(title="📚 特化検索に基づく関連論文推薦")
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
        title_text = paper.title[:33] + \
            "..." if len(paper.title) > 33 else paper.title

        rec_table.add_row(
            str(i),
            title_text,
            author_text,
            str(paper.publication_year) if paper.publication_year else "N/A",
            f"{similarity:.2f}",
            reason[:18] + "..." if len(reason) > 18 else reason
        )

    console.print(rec_table)
    console.print(f"\n💡 推薦論文数: {len(recommendations)}件")
    console.print("💡 特化検索結果に基づいて、さらに関連性の高い論文を推薦しています")


def _determine_paper_type(paper: Paper) -> str:
    """論文種別を判定"""
    text = f"{paper.title} {paper.abstract or ''}".lower()

    if any(term in text for term in ["meta-analysis", "systematic review"]):
        return "📊 メタ分析"
    elif any(term in text for term in ["review", "survey"]):
        return "📚 レビュー"
    elif any(term in text for term in ["experiment", "experimental"]):
        return "🧪 実験研究"
    elif any(term in text for term in ["case study", "qualitative"]):
        return "📝 事例研究"
    elif any(term in text for term in ["theory", "model", "framework"]):
        return "🏗️ 理論研究"
    else:
        return "📄 実証研究"


def _display_table(papers: List[Paper], recommendations: List = None):
    """通常テーブル形式"""
    table = Table(
        title="📚 検索結果",
        show_header=True,
        header_style="bold magenta")
    table.add_column("タイトル", style="cyan", width=40)
    table.add_column("著者", style="green", width=20)
    table.add_column("年", justify="center", width=8)
    table.add_column("引用数", justify="right", width=10)
    table.add_column("API", justify="center", width=15)

    for paper in papers:
        author_names = [author.name for author in paper.authors[:2]]
        if len(paper.authors) > 2:
            author_names.append(f"他{len(paper.authors) - 2}名")
        authors_str = ", ".join(author_names)

        title = paper.title[:60] + \
            "..." if len(paper.title) > 60 else paper.title

        table.add_row(
            title,
            authors_str,
            str(paper.publication_year) if paper.publication_year else "N/A",
            str(paper.citation_count) if paper.citation_count else "0",
            paper.source_api.title()
        )

    console.print(table)


def _display_chatgpt_format(
        papers: List[Paper], metadata: dict, recommendations: List = None):
    """ChatGPT/Claude投入用フォーマット"""
    domain_names = {
        'sales_psychology': '営業心理学',
        'management_psychology': 'マネジメント心理学',
        'behavioral_economics': '行動経済学',
        'universal_psychology': '汎用心理学'
    }

    mode_names = {
        'thesis': 'テーゼ（主流理論）',
        'antithesis': 'アンチテーゼ（批判研究）',
        'synthesis': 'ジンテーゼ（統合理論）',
        'meta_analysis': 'メタ分析重視'
    }

    print("\n" + "=" * 70)
    print("🎯 営業・マネジメント心理学特化検索結果（ChatGPT/Claude投入用）")
    print("=" * 70)
    print(
        f"📊 検索設定: {domain_names[metadata['domain']]} × {mode_names[metadata['thinking_mode']]}")
    print(f"🔍 元クエリ: {metadata['original_query']}")
    print(f"📈 結果: {metadata['filtering_stats']['final_results']}件")
    print("=" * 70 + "\n")

    for i, paper in enumerate(papers, 1):
        print(f"{i}. ## 📄 {paper.title}")
        print()

        # 基本情報
        author_names = [author.name for author in paper.authors]
        print(f"**著者**: {', '.join(author_names)}")

        if paper.publication_year:
            print(f"**発表年**: {paper.publication_year}")
        if paper.citation_count:
            print(f"**引用数**: {paper.citation_count}")
        if paper.doi:
            print(f"**DOI**: {paper.doi}")

        # 特化情報
        paper_type = _determine_paper_type(paper)
        print(f"**論文種別**: {paper_type}")

        spec_score = getattr(paper, 'specialized_score', 0)
        if spec_score:
            print(f"**特化スコア**: {spec_score:.2f}")

        print()

        # 概要
        if paper.abstract:
            print("**概要**:")
            print(paper.abstract)
        else:
            print("**概要**: 概要なし")

        print()

        # メタデータ
        if paper.journal:
            print(f"**ジャーナル**: {paper.journal}")

        print(f"**データソース**: {paper.source_api.title()}")
        print()

    print("=" * 70)
    print("📝 [分析指示例]")
    print("「上記の論文を基に、営業効率向上のための心理学的アプローチを")
    print("　テーゼ・アンチテーゼ・ジンテーゼの観点から分析してください」")
    print()
    print("💡 クリティカルシンキング活用:")
    print("  • 主流理論の確認 → --thinking-mode thesis")
    print("  • 批判的検証 → --thinking-mode antithesis")
    print("  • 統合的理解 → --thinking-mode synthesis")


if __name__ == "__main__":
    specialized_search()
