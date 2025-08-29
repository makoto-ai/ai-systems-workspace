"""
Citation Network Analysis CLI
引用ネットワーク分析 CLI
"""

import time
from services.safe_rate_limited_search_service import (
    get_safe_rate_limited_search_service,
)
from services.citation_visualization import (
    get_citation_visualization,
    VisualizationConfig,
)
from services.citation_graph_db import get_citation_graph_db
from services.citation_network_engine import (
    get_citation_network_engine,
    CitationNetwork,
)
import asyncio
import click
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

sys.path.append(str(Path(__file__).parent))


console = Console()
logger = logging.getLogger(__name__)


@click.group()
def citation_cli():
    """引用ネットワーク分析システム"""


@citation_cli.command()
@click.argument("query", required=True)
@click.option("--max-papers", "-n", default=5, help="基となる論文の最大数")
@click.option("--max-depth", "-d", default=2, help="引用関係を辿る最大深度")
@click.option(
    "--direction",
    "-dir",
    default="both",
    type=click.Choice(["forward", "backward", "both"]),
    help="引用関係の方向",
)
@click.option("--save-name", "-s", help="ネットワーク保存名")
@click.option("--verbose", "-v", is_flag=True, help="詳細出力")
def build(
    query: str,
    max_papers: int,
    max_depth: int,
    direction: str,
    save_name: str,
    verbose: bool,
):
    """
    検索クエリから引用ネットワークを構築

    指定されたクエリで論文を検索し、その引用関係を分析して
    ネットワークを構築します。

    例:
        python3 main_citation_network.py build "sales psychology" --max-depth 3
    """
    console.print(
        Panel.fit(
            "🌐 Citation Network Builder\n引用ネットワーク構築システム",
            style="bold blue",
        )
    )

    console.print(f"🔍 検索クエリ: [bold cyan]{query}[/bold cyan]")
    console.print(
        f"📊 基論文数: {max_papers}, 最大深度: {max_depth}, 方向: {direction}"
    )

    if verbose:
        logging.basicConfig(level=logging.INFO)

    asyncio.run(
        _build_network_async(
            query, max_papers, max_depth, direction, save_name, verbose
        )
    )


async def _build_network_async(
    query: str,
    max_papers: int,
    max_depth: int,
    direction: str,
    save_name: str,
    verbose: bool,
):
    """非同期でネットワーク構築"""

    # 基となる論文を検索
    with console.status("[bold green]基論文を検索中..."):
        search_service = get_safe_rate_limited_search_service()
        start_time = time.time()
        root_papers = await search_service.search_papers(query, max_results=max_papers)
        search_time = time.time() - start_time

    if not root_papers:
        console.print("❌ 基となる論文が見つかりませんでした")
        return

    console.print(
        f"✅ 基論文検索完了: {len(root_papers)}件 (検索時間: {search_time:.2f}秒)"
    )

    # 引用ネットワーク構築
    citation_engine = get_citation_network_engine(
        max_depth=max_depth, max_papers_per_level=10
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("引用ネットワーク構築中...", total=None)

        network_start = time.time()
        network = await citation_engine.build_citation_network(root_papers, direction)
        network_time = time.time() - network_start

    console.print(
        f"✅ ネットワーク構築完了: ノード{len(network.nodes)}件, エッジ{len(network.edges)}件"
    )
    console.print(f"⏱️ 構築時間: {network_time:.2f}秒")

    # ネットワーク統計表示
    _display_network_statistics(network)

    # データベースに保存
    if save_name:
        graph_db = get_citation_graph_db()
        analysis_id = graph_db.save_network(network, save_name)
        console.print(f"💾 ネットワーク保存完了: '{save_name}' (ID: {analysis_id})")

    console.print("\n💡 [bold cyan]次のステップ[/bold cyan]:")
    console.print("  • 可視化: [bold]python3 main_citation_network.py visualize[/bold]")
    console.print("  • 分析: [bold]python3 main_citation_network.py analyze[/bold]")
    console.print("  • 検索: [bold]python3 main_citation_network.py search[/bold]")


@citation_cli.command()
@click.option("--analysis-name", "-a", help="分析名（指定しない場合は一覧表示）")
@click.option(
    "--diagram-type",
    "-t",
    default="network",
    type=click.Choice(["network", "summary", "cluster", "temporal"]),
    help="図表タイプ",
)
@click.option("--max-nodes", default=15, help="最大ノード数")
def visualize(analysis_name: str, diagram_type: str, max_nodes: int):
    """
    保存されたネットワークを可視化

    Mermaid形式の図表を生成して、引用関係を視覚的に表示します。

    例:
        python3 main_citation_network.py visualize -a "sales_research" -t network
    """
    console.print(
        Panel.fit(
            "📊 Citation Network Visualizer\n引用ネットワーク可視化システム",
            style="bold green",
        )
    )

    graph_db = get_citation_graph_db()

    if not analysis_name:
        # 分析一覧表示
        analyses = graph_db.list_analyses()
        if not analyses:
            console.print("❌ 保存された分析がありません")
            return

        table = Table(title="保存されている引用ネットワーク分析")
        table.add_column("分析名", style="cyan")
        table.add_column("ノード数", justify="right")
        table.add_column("エッジ数", justify="right")
        table.add_column("密度", justify="right")
        table.add_column("作成日時", style="green")

        for analysis in analyses:
            table.add_row(
                analysis["analysis_name"],
                str(analysis["total_nodes"]),
                str(analysis["total_edges"]),
                f"{analysis['network_density']:.3f}",
                analysis["created_at"][:16],
            )

        console.print(table)
        console.print(
            "\n💡 特定の分析を可視化するには: [bold]--analysis-name[/bold] を指定してください"
        )
        return

    # ネットワーク読み込み
    network = graph_db.load_network(analysis_name)
    if not network:
        console.print(f"❌ 分析 '{analysis_name}' が見つかりません")
        return

    # 可視化生成
    viz = get_citation_visualization()
    config = VisualizationConfig(max_nodes=max_nodes)

    console.print(f"🎨 {diagram_type}図を生成中...")

    if diagram_type == "network":
        diagram = viz.generate_mermaid_diagram(network, config)
    elif diagram_type == "summary":
        diagram = viz.generate_network_summary(network)
    elif diagram_type == "cluster":
        diagram = viz.generate_cluster_diagram(network)
    elif diagram_type == "temporal":
        diagram = viz.generate_temporal_flow_diagram(network)

    console.print("\n" + "=" * 80)
    console.print(
        f"📊 [bold green]{
            diagram_type.title()} Citation Network Diagram[/bold green]"
    )
    console.print("=" * 80)
    console.print(diagram)
    console.print("=" * 80)

    console.print(f"\n✅ {diagram_type}図生成完了")
    console.print(
        "💡 上記のMermaidコードをMermaid対応エディタにコピーして可視化できます"
    )


@citation_cli.command()
@click.option("--analysis-name", "-a", required=True, help="分析名")
def analyze(analysis_name: str):
    """
    ネットワークの詳細分析を実行

    PageRank、中心性、クラスタリングなどの高度な分析を実行します。

    例:
        python3 main_citation_network.py analyze -a "sales_research"
    """
    console.print(
        Panel.fit(
            "🔬 Citation Network Analyzer\n引用ネットワーク詳細分析システム",
            style="bold magenta",
        )
    )

    graph_db = get_citation_graph_db()

    # ネットワーク存在確認
    network = graph_db.load_network(analysis_name)
    if not network:
        console.print(f"❌ 分析 '{analysis_name}' が見つかりません")
        return

    console.print(f"🔍 分析対象: [bold cyan]{analysis_name}[/bold cyan]")

    # 詳細メトリクス計算
    with console.status("[bold yellow]ネットワーク分析実行中..."):
        metrics = graph_db.calculate_network_metrics(analysis_name)

    if not metrics:
        console.print("❌ 分析の実行に失敗しました")
        return

    # 基本統計
    console.print("\n📊 [bold green]基本統計[/bold green]")
    basic = metrics.get("basic_stats", {})
    console.print(f"  • ノード数: {basic.get('nodes', 0)}")
    console.print(f"  • エッジ数: {basic.get('edges', 0)}")
    console.print(f"  • ネットワーク密度: {basic.get('density', 0):.4f}")
    console.print(
        f"  • 弱連結: {
            'はい' if basic.get(
                'is_connected',
                False) else 'いいえ'}"
    )

    # 中心性分析
    if "centrality" in metrics:
        console.print("\n🏆 [bold green]重要論文[/bold green]")
        centrality = metrics["centrality"]

        if "top_pagerank" in centrality:
            pr = centrality["top_pagerank"]
            console.print(
                f"  • 最高PageRank: {pr['title'][:50]}... (スコア: {pr['score']:.4f})"
            )

        if "most_cited" in centrality:
            mc = centrality["most_cited"]
            console.print(
                f"  • 最多被引用: {mc['title'][:50]}... ({mc['citations']}件)"
            )

        if "most_citing" in centrality:
            mcit = centrality["most_citing"]
            console.print(
                f"  • 最多引用: {mcit['title'][:50]}... ({mcit['references']}件)"
            )

    # 時系列分析
    if "temporal" in metrics:
        console.print("\n📅 [bold green]時系列分析[/bold green]")
        temporal = metrics["temporal"]
        year_range = temporal.get("year_range", (None, None))
        console.print(f"  • 年代範囲: {year_range[0]} - {year_range[1]}")
        console.print(f"  • 研究期間: {temporal.get('span_years', 0)}年")
        console.print(f"  • 年平均論文数: {temporal.get('papers_per_year', 0):.1f}件")

    console.print("\n✅ 分析完了")


@citation_cli.command()
@click.argument("search_query", required=True)
@click.option("--analysis-name", "-a", required=True, help="検索対象の分析名")
@click.option(
    "--search-type",
    "-t",
    default="title",
    type=click.Choice(["title", "author", "year"]),
    help="検索タイプ",
)
def search(search_query: str, analysis_name: str, search_type: str):
    """
    ネットワーク内で論文を検索

    保存されたネットワーク内で論文を検索し、関連情報を表示します。

    例:
        python3 main_citation_network.py search "machine learning" -a "sales_research"
    """
    console.print(
        Panel.fit("🔍 Network Paper Search\nネットワーク内論文検索", style="bold cyan")
    )

    graph_db = get_citation_graph_db()

    console.print(f"🎯 検索クエリ: [bold cyan]{search_query}[/bold cyan]")
    console.print(f"📊 検索対象: {analysis_name} ({search_type})")

    # 検索実行
    results = graph_db.search_papers_in_network(
        analysis_name, search_query, search_type
    )

    if not results:
        console.print("❌ 該当する論文が見つかりませんでした")
        return

    # 結果表示
    table = Table(title=f"検索結果 ({len(results)}件)")
    table.add_column("タイトル", style="green", width=40)
    table.add_column("年", justify="center")
    table.add_column("被引用", justify="right")
    table.add_column("引用", justify="right")
    table.add_column("PageRank", justify="right")
    table.add_column("種別", style="yellow")

    for result in results[:20]:  # 上位20件
        table.add_row(
            (
                result["title"][:38] + "..."
                if len(result["title"]) > 38
                else result["title"]
            ),
            str(result["publication_year"]) if result["publication_year"] else "N/A",
            str(result["in_degree"]),
            str(result["out_degree"]),
            f"{result['pagerank_score']:.4f}" if result["pagerank_score"] else "0.0000",
            result.get("paper_type_network", "unknown"),
        )

    console.print(table)

    if len(results) > 20:
        console.print(f"\n💡 表示は上位20件です。全{len(results)}件の結果があります。")

    console.print("\n✅ 検索完了")


def _display_network_statistics(network: CitationNetwork):
    """ネットワーク統計表示"""
    console.print("\n📈 [bold green]ネットワーク統計[/bold green]")

    # 基本統計
    total_nodes = len(network.nodes)
    total_edges = len(network.edges)
    density = total_edges / (total_nodes * (total_nodes - 1)) if total_nodes > 1 else 0

    console.print(f"  • 総ノード数: {total_nodes}")
    console.print(f"  • 総エッジ数: {total_edges}")
    console.print(f"  • ネットワーク密度: {density:.4f}")
    console.print(f"  • 最大深度: {network.max_depth}")

    # 年代分布
    years = [node.year for node in network.nodes.values() if node.year]
    if years:
        console.print(f"  • 年代範囲: {min(years)} - {max(years)}")

        # 年代別統計
        year_counts = {}
        for year in years:
            decade = (year // 10) * 10
            decade_key = f"{decade}s"
            year_counts[decade_key] = year_counts.get(decade_key, 0) + 1

        console.print("  • 年代分布:")
        for decade, count in sorted(year_counts.items()):
            console.print(f"    - {decade}: {count}件")

    # トップ論文
    most_cited = max(
        network.nodes.values(), key=lambda n: len(n.cited_by), default=None
    )
    if most_cited:
        citations = len(most_cited.cited_by)
        title = (
            most_cited.title[:50] + "..."
            if len(most_cited.title) > 50
            else most_cited.title
        )
        console.print(f"  • 最多被引用論文: {title} ({citations}件)")


if __name__ == "__main__":
    citation_cli()
