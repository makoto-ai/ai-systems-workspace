"""
Citation Network Visualization Engine
引用ネットワーク可視化エンジン
"""

from .citation_network_engine import CitationNetwork, CitationNode, CitationEdge
import logging
import math
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


logger = logging.getLogger(__name__)


@dataclass
class VisualizationConfig:
    """可視化設定"""

    max_nodes: int = 20
    max_edges: int = 50
    show_years: bool = True
    show_citations: bool = True
    color_by_year: bool = True
    edge_thickness_by_citations: bool = True
    layout_algorithm: str = "hierarchical"  # hierarchical, circular, force


class CitationVisualization:
    """引用ネットワーク可視化エンジン"""

    def __init__(self):
        """初期化"""
        self.year_colors = {
            "2020s": "#2E86AB",  # 青
            "2010s": "#A23B72",  # 紫
            "2000s": "#F18F01",  # オレンジ
            "1990s": "#C73E1D",  # 赤
            "unknown": "#6C757D",  # グレー
        }

    def generate_mermaid_diagram(
        self, network: CitationNetwork, config: VisualizationConfig = None
    ) -> str:
        """
        Mermaid引用関係図を生成

        Args:
            network: 引用ネットワーク
            config: 可視化設定

        Returns:
            Mermaidダイアグラム文字列
        """
        if config is None:
            config = VisualizationConfig()

        # ネットワークをフィルタリング
        filtered_nodes, filtered_edges = self._filter_network(network, config)

        logger.info(
            f"Mermaid図生成: ノード{
                len(filtered_nodes)}件, エッジ{
                len(filtered_edges)}件"
        )

        # Mermaidコード生成
        mermaid_lines = []
        mermaid_lines.append("graph TD")

        # ノード定義
        for node in filtered_nodes.values():
            node_id = self._sanitize_id(node.paper_id)
            label = self._create_node_label(node, config)
            style = self._get_node_style(node, config)

            mermaid_lines.append(f'    {node_id}["{label}"]')
            if style:
                mermaid_lines.append(f'    {node_id} --> {node_id}_style["{style}"]')

        # エッジ定義
        for edge in filtered_edges:
            from_id = self._sanitize_id(edge.from_paper_id)
            to_id = self._sanitize_id(edge.to_paper_id)

            if from_id in [
                self._sanitize_id(n.paper_id) for n in filtered_nodes.values()
            ] and to_id in [
                self._sanitize_id(n.paper_id) for n in filtered_nodes.values()
            ]:

                edge_style = self._get_edge_style(edge, filtered_nodes, config)
                mermaid_lines.append(f"    {from_id} {edge_style} {to_id}")

        # スタイル定義
        mermaid_lines.extend(self._generate_mermaid_styles(config))

        return "\n".join(mermaid_lines)

    def generate_network_summary(self, network: CitationNetwork) -> str:
        """
        ネットワーク概要のMermaid図を生成

        Args:
            network: 引用ネットワーク

        Returns:
            概要Mermaidダイアグラム
        """
        # 年代別統計
        year_stats = self._calculate_year_distribution(network)

        # 最重要ノード抽出
        top_nodes = self._get_top_nodes(network, top_k=5)

        mermaid_lines = []
        mermaid_lines.append("graph LR")
        mermaid_lines.append('    subgraph "Citation Network Overview"')

        # 統計情報
        total_nodes = len(network.nodes)
        total_edges = len(network.edges)
        mermaid_lines.append(
            f'    Stats["Total Papers: {total_nodes}<br/>Citations: {total_edges}<br/>Max Depth: {
                network.max_depth}"]'
        )

        # 年代分布
        for year_range, count in year_stats.items():
            if count > 0:
                year_id = year_range.replace("s", "")
                mermaid_lines.append(f'    {year_id}["{year_range}: {count} papers"]')
                mermaid_lines.append(f"    Stats --> {year_id}")

        # トップ論文
        for i, (node_id, node) in enumerate(top_nodes.items()):
            top_id = f"Top{i + 1}"
            title_short = (
                node.title[:30] + "..." if len(node.title) > 30 else node.title
            )
            citations = len(node.cited_by)
            mermaid_lines.append(
                f'    {top_id}["{title_short}<br/>Citations: {citations}"]'
            )
            mermaid_lines.append(f"    Stats --> {top_id}")

        mermaid_lines.append("    end")

        # スタイル
        mermaid_lines.append(
            "    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px"
        )
        mermaid_lines.append(
            "    classDef statsNode fill:#e1f5fe,stroke:#01579b,stroke-width:3px"
        )
        mermaid_lines.append("    class Stats statsNode")

        return "\n".join(mermaid_lines)

    def generate_cluster_diagram(self, network: CitationNetwork) -> str:
        """
        研究クラスター分析図を生成

        Args:
            network: 引用ネットワーク

        Returns:
            クラスター分析Mermaidダイアグラム
        """
        # 年代別クラスタリング
        year_clusters = self._cluster_by_year(network)

        mermaid_lines = []
        mermaid_lines.append("graph TB")

        cluster_id = 0
        for year_range, papers in year_clusters.items():
            if len(papers) < 2:  # 最低2件以上のクラスターのみ表示
                continue

            cluster_id += 1
            mermaid_lines.append(f'    subgraph "Cluster {cluster_id}: {year_range}"')

            # クラスター内論文
            for paper in papers[:8]:  # 最大8件まで表示
                node_id = self._sanitize_id(paper.paper_id)
                title_short = (
                    paper.title[:25] + "..." if len(paper.title) > 25 else paper.title
                )
                citations = len(paper.cited_by)
                mermaid_lines.append(
                    f'    {node_id}["{title_short}<br/>({citations} cites)"]'
                )

            mermaid_lines.append("    end")

        # クラスター間の関係
        cluster_connections = self._find_cluster_connections(
            year_clusters, network.edges
        )
        for from_cluster, to_cluster, strength in cluster_connections:
            if strength > 1:  # 複数の引用関係があるもののみ
                mermaid_lines.append(
                    f"    Cluster{from_cluster} -.->|{strength} citations| Cluster{to_cluster}"
                )

        return "\n".join(mermaid_lines)

    def _filter_network(
        self, network: CitationNetwork, config: VisualizationConfig
    ) -> Tuple[Dict[str, CitationNode], List[CitationEdge]]:
        """ネットワークをフィルタリング"""
        # ノードを重要度でソート（PageRank風）
        nodes_by_importance = sorted(
            network.nodes.values(),
            key=lambda n: len(n.cited_by) + len(n.references) + (n.citation_count or 0),
            reverse=True,
        )

        # 上位ノードを選択
        selected_nodes = {
            node.paper_id: node for node in nodes_by_importance[: config.max_nodes]
        }

        # 選択されたノード間のエッジのみ抽出
        filtered_edges = [
            edge
            for edge in network.edges[: config.max_edges]
            if edge.from_paper_id in selected_nodes
            and edge.to_paper_id in selected_nodes
        ]

        return selected_nodes, filtered_edges

    def _sanitize_id(self, paper_id: str) -> str:
        """MermaidID用にサニタイズ"""
        # 英数字とアンダースコアのみ許可
        sanitized = "".join(c if c.isalnum() or c == "_" else "_" for c in paper_id)
        return f"N{sanitized}"  # 数字開始を避ける

    def _create_node_label(
        self, node: CitationNode, config: VisualizationConfig
    ) -> str:
        """ノードラベル作成"""
        title = node.title[:40] + "..." if len(node.title) > 40 else node.title
        label_parts = [title]

        if config.show_years and node.year:
            label_parts.append(f"({node.year})")

        if config.show_citations:
            citations = len(node.cited_by)
            if citations > 0:
                label_parts.append(f"[{citations} cites]")

        return "<br/>".join(label_parts)

    def _get_node_style(self, node: CitationNode, config: VisualizationConfig) -> str:
        """ノードスタイル取得"""
        if not config.color_by_year:
            return ""

        year_range = self._get_year_range(node.year)
        color = self.year_colors.get(year_range, self.year_colors["unknown"])

        return f"fill:{color},stroke:#333,stroke-width:2px"

    def _get_edge_style(
        self,
        edge: CitationEdge,
        nodes: Dict[str, CitationNode],
        config: VisualizationConfig,
    ) -> str:
        """エッジスタイル取得"""
        if not config.edge_thickness_by_citations:
            return "-->"

        # 引用先論文の重要度に基づいてエッジの太さを決定
        to_node = None
        for node in nodes.values():
            if node.paper_id == edge.to_paper_id:
                to_node = node
                break

        if to_node and len(to_node.cited_by) > 5:
            return "==>"  # 太いエッジ
        else:
            return "-->"  # 通常エッジ

    def _generate_mermaid_styles(self, config: VisualizationConfig) -> List[str]:
        """Mermaidスタイル定義生成"""
        styles = []

        if config.color_by_year:
            for year_range, color in self.year_colors.items():
                class_name = f"year{year_range.replace('s', '')}"
                styles.append(
                    f"    classDef {class_name} fill:{color},stroke:#333,stroke-width:2px"
                )

        styles.append("    classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px")

        return styles

    def _get_year_range(self, year: Optional[int]) -> str:
        """年代レンジ取得"""
        if not year:
            return "unknown"

        decade = (year // 10) * 10
        return f"{decade}s"

    def _calculate_year_distribution(self, network: CitationNetwork) -> Dict[str, int]:
        """年代分布計算"""
        year_counts = {}

        for node in network.nodes.values():
            year_range = self._get_year_range(node.year)
            year_counts[year_range] = year_counts.get(year_range, 0) + 1

        return year_counts

    def _get_top_nodes(
        self, network: CitationNetwork, top_k: int = 5
    ) -> Dict[str, CitationNode]:
        """最重要ノード取得"""
        nodes_by_citations = sorted(
            network.nodes.values(), key=lambda n: len(n.cited_by), reverse=True
        )

        return {node.paper_id: node for node in nodes_by_citations[:top_k]}

    def _cluster_by_year(
        self, network: CitationNetwork
    ) -> Dict[str, List[CitationNode]]:
        """年代別クラスタリング"""
        clusters = {}

        for node in network.nodes.values():
            year_range = self._get_year_range(node.year)
            if year_range not in clusters:
                clusters[year_range] = []
            clusters[year_range].append(node)

        return clusters

    def _find_cluster_connections(
        self, clusters: Dict[str, List[CitationNode]], edges: List[CitationEdge]
    ) -> List[Tuple[str, str, int]]:
        """クラスター間接続検出"""
        # 年代範囲からクラスターIDへのマッピング
        year_to_cluster = {}
        cluster_id = 0
        for year_range in clusters.keys():
            cluster_id += 1
            year_to_cluster[year_range] = cluster_id

        # ノードIDから年代範囲へのマッピング
        node_to_year = {}
        for year_range, nodes in clusters.items():
            for node in nodes:
                node_to_year[node.paper_id] = year_range

        # クラスター間接続カウント
        connections = {}

        for edge in edges:
            from_year = node_to_year.get(edge.from_paper_id)
            to_year = node_to_year.get(edge.to_paper_id)

            if from_year and to_year and from_year != to_year:
                from_cluster = year_to_cluster[from_year]
                to_cluster = year_to_cluster[to_year]
                key = (from_cluster, to_cluster)
                connections[key] = connections.get(key, 0) + 1

        return [(f, t, c) for (f, t), c in connections.items()]

    def generate_temporal_flow_diagram(self, network: CitationNetwork) -> str:
        """
        時系列引用フロー図を生成

        Args:
            network: 引用ネットワーク

        Returns:
            時系列フローMermaidダイアグラム
        """
        # 年代順にノードをソート
        nodes_by_year = {}
        for node in network.nodes.values():
            if node.year:
                year = node.year
                if year not in nodes_by_year:
                    nodes_by_year[year] = []
                nodes_by_year[year].append(node)

        if not nodes_by_year:
            return 'graph LR\n    NoData["No temporal data available"]'

        mermaid_lines = []
        mermaid_lines.append("graph LR")

        # 年代順に配置
        sorted_years = sorted(nodes_by_year.keys())

        for i, year in enumerate(sorted_years):
            papers = nodes_by_year[year]

            # 各年代で最も重要な論文を表示
            top_paper = max(papers, key=lambda n: len(n.cited_by))

            node_id = f"Y{year}"
            title_short = (
                top_paper.title[:25] + "..."
                if len(top_paper.title) > 25
                else top_paper.title
            )
            citations = len(top_paper.cited_by)

            mermaid_lines.append(
                f'    {node_id}["{year}<br/>{title_short}<br/>({citations} cites)"]'
            )

            # 時系列つながり
            if i > 0:
                prev_year_id = f"Y{sorted_years[i - 1]}"
                mermaid_lines.append(f"    {prev_year_id} --> {node_id}")

        # スタイル
        mermaid_lines.append(
            "    classDef default fill:#e3f2fd,stroke:#1976d2,stroke-width:2px"
        )

        return "\n".join(mermaid_lines)


# シングルトンインスタンス
_citation_viz = None


def get_citation_visualization() -> CitationVisualization:
    """CitationVisualizationのシングルトンインスタンスを取得"""
    global _citation_viz
    if _citation_viz is None:
        _citation_viz = CitationVisualization()
    return _citation_viz
