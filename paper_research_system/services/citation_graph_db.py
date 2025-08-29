"""
Citation Graph Database Service
引用ネットワーク グラフデータベース サービス
"""

from services.citation_network_engine import CitationNetwork, CitationNode, CitationEdge
import sqlite3
import json
import logging
import networkx as nx
from typing import List, Dict, Set, Tuple, Optional, Any
from pathlib import Path
from dataclasses import asdict
import sys

sys.path.append(str(Path(__file__).parent.parent))


logger = logging.getLogger(__name__)


class CitationGraphDB:
    """引用ネットワーク グラフデータベース"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初期化

        Args:
            db_path: データベースファイルパス
        """
        if db_path is None:
            self.db_path = (
                Path(__file__).parent.parent / "database" / "citation_graph.db"
            )
        else:
            self.db_path = Path(db_path)

        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()

    def _init_database(self):
        """データベース初期化"""
        schema_path = self.db_path.parent / "citation_graph_schema.sql"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            if schema_path.exists():
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                    conn.executescript(schema_sql)
            else:
                logger.warning(f"スキーマファイルが見つかりません: {schema_path}")

        logger.info(f"引用グラフDB初期化完了: {self.db_path}")

    def save_network(self, network: CitationNetwork, analysis_name: str) -> int:
        """
        引用ネットワークをデータベースに保存

        Args:
            network: 保存する引用ネットワーク
            analysis_name: 分析名

        Returns:
            analysis_id: 保存された分析のID
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # 既存の同名分析を削除
            conn.execute(
                "DELETE FROM network_analysis WHERE analysis_name = ?", (analysis_name,)
            )

            # ノード保存
            self._save_nodes(conn, network.nodes)

            # エッジ保存
            self._save_edges(conn, network.edges)

            # ネットワーク統計保存
            analysis_id = self._save_network_analysis(conn, network, analysis_name)

            conn.commit()
            logger.info(f"ネットワーク保存完了: {analysis_name} (ID: {analysis_id})")

        return analysis_id

    def _save_nodes(self, conn: sqlite3.Connection, nodes: Dict[str, CitationNode]):
        """ノード保存"""
        for node in nodes.values():
            authors_json = json.dumps(node.authors, ensure_ascii=False)
            title_normalized = node.title.lower().strip()
            year_range = f"{node.year // 10 * 10}s" if node.year else None

            conn.execute(
                """
                INSERT OR REPLACE INTO citation_nodes (
                    paper_id, title, authors, publication_year, citation_count,
                    doi, source_api, depth, in_degree, out_degree,
                    title_normalized, year_range, author_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    node.paper_id,
                    node.title,
                    authors_json,
                    node.year,
                    node.citation_count,
                    node.doi,
                    node.source_api,
                    node.depth,
                    len(node.cited_by),
                    len(node.references),
                    title_normalized,
                    year_range,
                    len(node.authors),
                ),
            )

    def _save_edges(self, conn: sqlite3.Connection, edges: List[CitationEdge]):
        """エッジ保存"""
        for edge in edges:
            conn.execute(
                """
                INSERT OR REPLACE INTO citation_edges (
                    from_paper_id, to_paper_id, citation_context, weight
                ) VALUES (?, ?, ?, ?)
            """,
                (edge.from_paper_id, edge.to_paper_id, edge.citation_context, 1.0),
            )

    def _save_network_analysis(
        self, conn: sqlite3.Connection, network: CitationNetwork, analysis_name: str
    ) -> int:
        """ネットワーク分析結果保存"""
        root_papers_json = json.dumps(network.root_papers, ensure_ascii=False)

        # 年代範囲計算
        years = [node.year for node in network.nodes.values() if node.year]
        year_start = min(years) if years else None
        year_end = max(years) if years else None

        # ネットワーク密度計算
        total_nodes = len(network.nodes)
        total_edges = len(network.edges)
        density = (
            total_edges / (total_nodes * (total_nodes - 1)) if total_nodes > 1 else 0
        )

        cursor = conn.execute(
            """
            INSERT INTO network_analysis (
                analysis_name, root_papers, total_nodes, total_edges,
                network_density, max_depth, year_range_start, year_range_end
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                analysis_name,
                root_papers_json,
                total_nodes,
                total_edges,
                density,
                network.max_depth,
                year_start,
                year_end,
            ),
        )

        return cursor.lastrowid

    def load_network(self, analysis_name: str) -> Optional[CitationNetwork]:
        """
        データベースから引用ネットワークを読み込み

        Args:
            analysis_name: 読み込む分析名

        Returns:
            引用ネットワーク（存在しない場合はNone）
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # 分析情報取得
            analysis_row = conn.execute(
                """
                SELECT * FROM network_analysis WHERE analysis_name = ?
            """,
                (analysis_name,),
            ).fetchone()

            if not analysis_row:
                return None

            # ノード取得
            nodes = self._load_nodes(conn)

            # エッジ取得
            edges = self._load_edges(conn)

            network = CitationNetwork(
                nodes=nodes,
                edges=edges,
                root_papers=json.loads(analysis_row["root_papers"]),
                total_citations=analysis_row["total_edges"],
                max_depth=analysis_row["max_depth"],
            )

            logger.info(f"ネットワーク読み込み完了: {analysis_name}")
            return network

    def _load_nodes(self, conn: sqlite3.Connection) -> Dict[str, CitationNode]:
        """ノード読み込み"""
        nodes = {}
        rows = conn.execute("SELECT * FROM citation_nodes").fetchall()

        for row in rows:
            authors = json.loads(row["authors"]) if row["authors"] else []

            # cited_byとreferencesを再構築
            cited_by = set()
            references = set()

            # エッジから引用関係を復元
            citing_rows = conn.execute(
                """
                SELECT from_paper_id FROM citation_edges WHERE to_paper_id = ?
            """,
                (row["paper_id"],),
            ).fetchall()
            cited_by = {r["from_paper_id"] for r in citing_rows}

            ref_rows = conn.execute(
                """
                SELECT to_paper_id FROM citation_edges WHERE from_paper_id = ?
            """,
                (row["paper_id"],),
            ).fetchall()
            references = {r["to_paper_id"] for r in ref_rows}

            node = CitationNode(
                paper_id=row["paper_id"],
                title=row["title"],
                authors=authors,
                year=row["publication_year"],
                citation_count=row["citation_count"],
                doi=row["doi"],
                source_api=row["source_api"],
                cited_by=cited_by,
                references=references,
                depth=row["depth"],
            )
            nodes[row["paper_id"]] = node

        return nodes

    def _load_edges(self, conn: sqlite3.Connection) -> List[CitationEdge]:
        """エッジ読み込み"""
        edges = []
        rows = conn.execute("SELECT * FROM citation_edges").fetchall()

        for row in rows:
            edge = CitationEdge(
                from_paper_id=row["from_paper_id"],
                to_paper_id=row["to_paper_id"],
                citation_context=row["citation_context"],
            )
            edges.append(edge)

        return edges

    def calculate_network_metrics(self, analysis_name: str) -> Dict[str, Any]:
        """
        保存されたネットワークの詳細メトリクスを計算

        Args:
            analysis_name: 分析名

        Returns:
            ネットワークメトリクス
        """
        network = self.load_network(analysis_name)
        if not network:
            return {}

        # NetworkXグラフ作成
        G = nx.DiGraph()

        # ノード追加
        for node in network.nodes.values():
            G.add_node(
                node.paper_id,
                title=node.title,
                year=node.year,
                citation_count=node.citation_count,
            )

        # エッジ追加
        for edge in network.edges:
            G.add_edge(edge.from_paper_id, edge.to_paper_id)

        # メトリクス計算
        metrics = {
            "basic_stats": {
                "nodes": len(G.nodes()),
                "edges": len(G.edges()),
                "density": nx.density(G),
                "is_connected": nx.is_weakly_connected(G),
            }
        }

        if G.nodes():
            # 中心性指標
            try:
                pagerank = nx.pagerank(G)
                betweenness = nx.betweenness_centrality(G)
                in_degree = dict(G.in_degree())
                out_degree = dict(G.out_degree())

                # PageRankをデータベースに保存
                self._update_pagerank_scores(analysis_name, pagerank)

                # トップ論文
                top_pagerank = max(pagerank.items(), key=lambda x: x[1])
                top_cited = max(in_degree.items(), key=lambda x: x[1])
                top_citing = max(out_degree.items(), key=lambda x: x[1])

                metrics["centrality"] = {
                    "top_pagerank": {
                        "paper_id": top_pagerank[0],
                        "score": top_pagerank[1],
                        "title": network.nodes[top_pagerank[0]].title,
                    },
                    "most_cited": {
                        "paper_id": top_cited[0],
                        "citations": top_cited[1],
                        "title": network.nodes[top_cited[0]].title,
                    },
                    "most_citing": {
                        "paper_id": top_citing[0],
                        "references": top_citing[1],
                        "title": network.nodes[top_citing[0]].title,
                    },
                }

            except Exception as e:
                logger.error(f"中心性計算エラー: {e}")
                metrics["centrality"] = {}

        # 年代分析
        years = [node.year for node in network.nodes.values() if node.year]
        if years:
            metrics["temporal"] = {
                "year_range": (min(years), max(years)),
                "span_years": max(years) - min(years),
                "papers_per_year": len(years) / (max(years) - min(years) + 1),
            }

        return metrics

    def _update_pagerank_scores(self, analysis_name: str, pagerank: Dict[str, float]):
        """PageRankスコアをデータベースに更新"""
        with sqlite3.connect(self.db_path) as conn:
            for paper_id, score in pagerank.items():
                conn.execute(
                    """
                    UPDATE citation_nodes
                    SET pagerank_score = ?
                    WHERE paper_id = ?
                """,
                    (score, paper_id),
                )
            conn.commit()

    def search_papers_in_network(
        self, analysis_name: str, query: str, search_type: str = "title"
    ) -> List[Dict[str, Any]]:
        """
        ネットワーク内で論文を検索

        Args:
            analysis_name: 分析名
            query: 検索クエリ
            search_type: 検索タイプ（title, author, year）

        Returns:
            検索結果
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if search_type == "title":
                rows = conn.execute(
                    """
                    SELECT * FROM paper_network_stats
                    WHERE title_normalized LIKE ?
                    ORDER BY pagerank_score DESC
                """,
                    (f"%{query.lower()}%",),
                ).fetchall()

            elif search_type == "author":
                rows = conn.execute(
                    """
                    SELECT * FROM paper_network_stats
                    WHERE authors LIKE ?
                    ORDER BY pagerank_score DESC
                """,
                    (f"%{query}%",),
                ).fetchall()

            elif search_type == "year":
                try:
                    year = int(query)
                    rows = conn.execute(
                        """
                        SELECT * FROM paper_network_stats
                        WHERE publication_year = ?
                        ORDER BY pagerank_score DESC
                    """,
                        (year,),
                    ).fetchall()
                except ValueError:
                    return []

            else:
                return []

            return [dict(row) for row in rows]

    def get_citation_path(
        self, start_paper_id: str, end_paper_id: str
    ) -> Optional[List[str]]:
        """
        2つの論文間の引用経路を取得

        Args:
            start_paper_id: 開始論文ID
            end_paper_id: 終了論文ID

        Returns:
            引用経路（論文IDのリスト）
        """
        with sqlite3.connect(self.db_path) as conn:
            # キャッシュから検索
            row = conn.execute(
                """
                SELECT path_nodes FROM citation_paths
                WHERE start_paper_id = ? AND end_paper_id = ?
            """,
                (start_paper_id, end_paper_id),
            ).fetchone()

            if row:
                return json.loads(row[0])

            # NetworkXで経路計算
            network = self.load_network("current")  # 現在のネットワークを仮定
            if not network:
                return None

            G = nx.DiGraph()
            for edge in network.edges:
                G.add_edge(edge.from_paper_id, edge.to_paper_id)

            try:
                path = nx.shortest_path(G, start_paper_id, end_paper_id)

                # キャッシュに保存
                path_json = json.dumps(path)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO citation_paths
                    (start_paper_id, end_paper_id, path_length, path_nodes)
                    VALUES (?, ?, ?, ?)
                """,
                    (start_paper_id, end_paper_id, len(path), path_json),
                )
                conn.commit()

                return path

            except nx.NetworkXNoPath:
                return None

    def list_analyses(self) -> List[Dict[str, Any]]:
        """保存されている分析の一覧を取得"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT analysis_name, total_nodes, total_edges,
                       network_density, max_depth, created_at
                FROM network_analysis
                ORDER BY created_at DESC
            """
            ).fetchall()

            return [dict(row) for row in rows]


# シングルトンインスタンス
_citation_graph_db = None


def get_citation_graph_db() -> CitationGraphDB:
    """CitationGraphDBのシングルトンインスタンスを取得"""
    global _citation_graph_db
    if _citation_graph_db is None:
        _citation_graph_db = CitationGraphDB()
    return _citation_graph_db
