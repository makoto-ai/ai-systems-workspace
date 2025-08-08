"""
Citation Network Engine for Academic Paper Analysis
学術論文引用ネットワーク分析エンジン
"""

from services.safe_rate_limited_search_service import (
    get_safe_rate_limited_search_service,
)
from core.paper_model import Paper
import asyncio
import logging
import json
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


logger = logging.getLogger(__name__)


@dataclass
class CitationNode:
    """引用ネットワークのノード（論文）"""

    paper_id: str
    title: str
    authors: List[str]
    year: Optional[int]
    citation_count: int
    doi: Optional[str]
    source_api: str

    # ネットワーク情報
    cited_by: Set[str]  # この論文を引用している論文のID
    references: Set[str]  # この論文が引用している論文のID
    depth: int = 0  # 検索の起点からの深度


@dataclass
class CitationEdge:
    """引用ネットワークのエッジ（引用関係）"""

    from_paper_id: str  # 引用している論文
    to_paper_id: str  # 引用されている論文
    citation_context: Optional[str] = None  # 引用の文脈


@dataclass
class CitationNetwork:
    """引用ネットワーク全体"""

    nodes: Dict[str, CitationNode]
    edges: List[CitationEdge]
    root_papers: List[str]  # 検索の起点となった論文
    total_citations: int
    max_depth: int


class CitationNetworkEngine:
    """引用ネットワーク分析エンジン"""

    def __init__(self, max_depth: int = 2, max_papers_per_level: int = 10):
        """
        初期化

        Args:
            max_depth: 引用関係を辿る最大深度
            max_papers_per_level: 各階層で収集する最大論文数
        """
        self.max_depth = max_depth
        self.max_papers_per_level = max_papers_per_level
        self.search_service = get_safe_rate_limited_search_service()

    async def build_citation_network(
        self, root_papers: List[Paper], direction: str = "both"
    ) -> CitationNetwork:
        """
        論文リストから引用ネットワークを構築

        Args:
            root_papers: 起点となる論文リスト
            direction: 引用関係の方向 ("forward": 被引用, "backward": 引用, "both": 両方向)

        Returns:
            構築された引用ネットワーク
        """
        logger.info(
            f"引用ネットワーク構築開始: 起点論文数={
                len(root_papers)}, 最大深度={
                self.max_depth}"
        )

        nodes: Dict[str, CitationNode] = {}
        edges: List[CitationEdge] = []
        total_citations = 0

        # 起点論文をノードとして追加
        root_paper_ids = []
        for paper in root_papers:
            paper_id = self._generate_paper_id(paper)
            root_paper_ids.append(paper_id)

            node = CitationNode(
                paper_id=paper_id,
                title=paper.title or "Unknown Title",
                authors=[
                    author.name for author in (paper.authors or []) if author.name
                ],
                year=paper.publication_year,
                citation_count=paper.citation_count or 0,
                doi=paper.doi,
                source_api=paper.source_api or "unknown",
                cited_by=set(),
                references=set(),
                depth=0,
            )
            nodes[paper_id] = node

        # 各深度で引用関係を収集
        for depth in range(self.max_depth):
            current_level_papers = [
                node for node in nodes.values() if node.depth == depth
            ]

            if not current_level_papers:
                break

            logger.info(
                f"深度{depth}の引用収集: {len(current_level_papers)}件の論文を処理"
            )

            for node in current_level_papers:
                try:
                    # 引用関係を収集
                    if direction in ["forward", "both"]:
                        citing_papers = await self._get_citing_papers(node)
                        await self._add_citation_relationships(
                            node, citing_papers, nodes, edges, "forward", depth + 1
                        )

                    if direction in ["backward", "both"]:
                        referenced_papers = await self._get_referenced_papers(node)
                        await self._add_citation_relationships(
                            node, referenced_papers, nodes, edges, "backward", depth + 1
                        )

                except Exception as e:
                    logger.error(f"論文 {node.paper_id} の引用収集エラー: {e}")
                    continue

        # 統計計算
        total_citations = sum(
            len(node.cited_by) + len(node.references) for node in nodes.values()
        )

        network = CitationNetwork(
            nodes=nodes,
            edges=edges,
            root_papers=root_paper_ids,
            total_citations=total_citations,
            max_depth=max(node.depth for node in nodes.values()) if nodes else 0,
        )

        logger.info(
            f"引用ネットワーク構築完了: ノード数={len(nodes)}, エッジ数={len(edges)}"
        )
        return network

    async def _get_citing_papers(self, node: CitationNode) -> List[Paper]:
        """指定論文を引用している論文を取得"""
        if not node.doi and not node.title:
            return []

        try:
            # DOIまたはタイトルで被引用論文を検索
            search_query = (
                f'cites:"{
                node.doi}"'
                if node.doi
                else f'cites:"{
                node.title}"'
            )
            citing_papers = await self.search_service.search_papers(
                search_query, max_results=self.max_papers_per_level
            )

            logger.debug(f"論文 {node.paper_id} の被引用論文: {len(citing_papers)}件")
            return citing_papers

        except Exception as e:
            logger.error(f"被引用論文検索エラー for {node.paper_id}: {e}")
            return []

    async def _get_referenced_papers(self, node: CitationNode) -> List[Paper]:
        """指定論文が引用している論文を取得"""
        if not node.doi and not node.title:
            return []

        try:
            # 参考文献情報を検索（APIの制限により簡易実装）
            search_query = (
                f'references:"{
                node.doi}"'
                if node.doi
                else f'references:"{
                node.title}"'
            )
            referenced_papers = await self.search_service.search_papers(
                search_query, max_results=self.max_papers_per_level
            )

            logger.debug(
                f"論文 {
                    node.paper_id} の参考文献: {
                    len(referenced_papers)}件"
            )
            return referenced_papers

        except Exception as e:
            logger.error(f"参考文献検索エラー for {node.paper_id}: {e}")
            return []

    async def _add_citation_relationships(
        self,
        source_node: CitationNode,
        related_papers: List[Paper],
        nodes: Dict[str, CitationNode],
        edges: List[CitationEdge],
        direction: str,
        next_depth: int,
    ):
        """引用関係をネットワークに追加"""
        for paper in related_papers:
            paper_id = self._generate_paper_id(paper)

            # 新しいノードの場合は追加
            if paper_id not in nodes:
                new_node = CitationNode(
                    paper_id=paper_id,
                    title=paper.title or "Unknown Title",
                    authors=[
                        author.name for author in (paper.authors or []) if author.name
                    ],
                    year=paper.publication_year,
                    citation_count=paper.citation_count or 0,
                    doi=paper.doi,
                    source_api=paper.source_api or "unknown",
                    cited_by=set(),
                    references=set(),
                    depth=next_depth,
                )
                nodes[paper_id] = new_node

            # 引用関係を記録
            if direction == "forward":
                # source_node が paper を引用している
                source_node.references.add(paper_id)
                nodes[paper_id].cited_by.add(source_node.paper_id)

                edge = CitationEdge(
                    from_paper_id=source_node.paper_id, to_paper_id=paper_id
                )
                edges.append(edge)

            elif direction == "backward":
                # paper が source_node を引用している
                source_node.cited_by.add(paper_id)
                nodes[paper_id].references.add(source_node.paper_id)

                edge = CitationEdge(
                    from_paper_id=paper_id, to_paper_id=source_node.paper_id
                )
                edges.append(edge)

    def _generate_paper_id(self, paper: Paper) -> str:
        """論文の一意IDを生成"""
        if paper.doi:
            return f"doi:{paper.doi}"
        elif paper.title:
            # タイトルから簡易IDを生成
            title_hash = hash(paper.title.lower().strip())
            return f"title:{abs(title_hash)}"
        else:
            # 最後の手段として著者と年から
            authors_str = ",".join(
                [author.name for author in (paper.authors or [])[:3] if author.name]
            )
            year_str = (
                str(paper.publication_year) if paper.publication_year else "unknown"
            )
            combined_hash = hash(f"{authors_str}:{year_str}")
            return f"hash:{abs(combined_hash)}"

    def analyze_network_metrics(self, network: CitationNetwork) -> Dict[str, Any]:
        """ネットワークの指標を分析"""
        if not network.nodes:
            return {}

        # 基本統計
        total_nodes = len(network.nodes)
        total_edges = len(network.edges)

        # 中心性指標
        in_degree = defaultdict(int)  # 被引用数
        out_degree = defaultdict(int)  # 引用数

        for edge in network.edges:
            out_degree[edge.from_paper_id] += 1
            in_degree[edge.to_paper_id] += 1

        # 最も引用されている論文
        most_cited = max(
            network.nodes.values(), key=lambda n: len(n.cited_by), default=None
        )

        # 最も多く引用している論文
        most_citing = max(
            network.nodes.values(), key=lambda n: len(n.references), default=None
        )

        # 年代分布
        years = [node.year for node in network.nodes.values() if node.year]
        year_range = (min(years), max(years)) if years else None

        metrics = {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "network_density": (
                total_edges / (total_nodes * (total_nodes - 1))
                if total_nodes > 1
                else 0
            ),
            "average_citations_per_paper": (
                total_edges / total_nodes if total_nodes > 0 else 0
            ),
            "most_cited_paper": (
                {"title": most_cited.title, "citations": len(most_cited.cited_by)}
                if most_cited
                else None
            ),
            "most_citing_paper": (
                {"title": most_citing.title, "references": len(most_citing.references)}
                if most_citing
                else None
            ),
            "year_range": year_range,
            "max_depth": network.max_depth,
        }

        return metrics

    def export_network(
        self, network: CitationNetwork, format_type: str = "json"
    ) -> str:
        """ネットワークをエクスポート"""
        if format_type == "json":
            # JSON形式でエクスポート
            export_data = {
                "nodes": [asdict(node) for node in network.nodes.values()],
                "edges": [asdict(edge) for edge in network.edges],
                "metadata": {
                    "root_papers": network.root_papers,
                    "total_citations": network.total_citations,
                    "max_depth": network.max_depth,
                },
            }

            # セットを配列に変換
            for node in export_data["nodes"]:
                node["cited_by"] = list(node["cited_by"])
                node["references"] = list(node["references"])

            return json.dumps(export_data, indent=2, ensure_ascii=False)

        elif format_type == "dot":
            # Graphviz DOT形式でエクスポート
            lines = ["digraph citation_network {"]
            lines.append("  rankdir=TB;")
            lines.append("  node [shape=box, style=rounded];")

            # ノード定義
            for node in network.nodes.values():
                label = node.title[:50] + "..." if len(node.title) > 50 else node.title
                lines.append(
                    f'  "{
                        node.paper_id}" [label="{label}\\n({
                        node.year})"];'
                )

            # エッジ定義
            for edge in network.edges:
                lines.append(f'  "{edge.from_paper_id}" -> "{edge.to_paper_id}";')

            lines.append("}")
            return "\n".join(lines)

        else:
            raise ValueError(f"未サポートの形式: {format_type}")


# シングルトンインスタンス
_citation_engine = None


def get_citation_network_engine(
    max_depth: int = 2, max_papers_per_level: int = 10
) -> CitationNetworkEngine:
    """CitationNetworkEngineのシングルトンインスタンスを取得"""
    global _citation_engine
    if _citation_engine is None:
        _citation_engine = CitationNetworkEngine(max_depth, max_papers_per_level)
    return _citation_engine
