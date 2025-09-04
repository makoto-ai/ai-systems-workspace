"""
Search History Database Manager
検索履歴データベース管理サービス
"""

from ..core.paper_model import Paper
import sqlite3
import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


logger = logging.getLogger(__name__)


class SearchHistoryDB:
    """検索履歴データベース管理クラス"""

    def __init__(self, db_path: str = None):
        """
        初期化

        Args:
            db_path: データベースファイルパス（デフォルト: database/search_history.db）
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent / "database" / "search_history.db"

        self.db_path = Path(db_path)
        self.schema_path = (
            Path(__file__).parent.parent / "database" / "search_history_schema.sql"
        )

        # データベースディレクトリ作成
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # データベース初期化
        self._initialize_database()

    def _initialize_database(self):
        """データベースとテーブルを初期化"""
        try:
            # スキーマファイルを読み込んで実行
            with open(self.schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()

            with self.get_connection() as conn:
                conn.executescript(schema_sql)
                conn.commit()

            logger.info(f"データベース初期化完了: {self.db_path}")

        except Exception as e:
            logger.error(f"データベース初期化エラー: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """データベース接続を取得（コンテキストマネージャー）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能
        try:
            yield conn
        finally:
            conn.close()

    def record_search(
        self,
        query: str,
        search_type: str,
        max_results: int,
        output_format: str,
        results: List[Paper],
        execution_time: float,
        domain: str = None,
        thinking_mode: str = None,
        api_calls: Dict[str, int] = None,
        saved_to_obsidian: bool = False,
        notes: str = None,
    ) -> int:
        """
        検索履歴を記録

        Args:
            query: 検索クエリ
            search_type: 検索タイプ ('integrated' or 'specialized')
            max_results: 最大結果数
            output_format: 出力形式
            results: 検索結果の論文リスト
            execution_time: 実行時間（秒）
            domain: ドメイン（specialized検索の場合）
            thinking_mode: 思考モード（specialized検索の場合）
            api_calls: API呼び出し統計
            saved_to_obsidian: Obsidian保存フラグ
            notes: ユーザーノート

        Returns:
            作成された検索履歴のID
        """
        try:
            with self.get_connection() as conn:
                # 検索履歴メイン記録
                cursor = conn.execute(
                    """
                    INSERT INTO search_history (
                        query, search_type, domain, thinking_mode, max_results,
                        output_format, execution_time_seconds, total_results,
                        api_calls, saved_to_obsidian, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        query,
                        search_type,
                        domain,
                        thinking_mode,
                        max_results,
                        output_format,
                        execution_time,
                        len(results),
                        json.dumps(api_calls) if api_calls else None,
                        saved_to_obsidian,
                        notes,
                    ),
                )

                search_history_id = cursor.lastrowid

                # 検索結果詳細記録
                for i, paper in enumerate(results):
                    self._record_paper_result(conn, search_history_id, paper, i + 1)

                conn.commit()
                logger.info(
                    f"検索履歴記録完了: ID={search_history_id}, クエリ='{query}', 結果数={
                        len(results)}"
                )
                return search_history_id

        except Exception as e:
            logger.error(f"検索履歴記録エラー: {e}")
            raise

    def _record_paper_result(
        self, conn: sqlite3.Connection, search_history_id: int, paper: Paper, rank: int
    ):
        """個別論文結果を記録"""
        conn.execute(
            """
            INSERT INTO search_results (
                search_history_id, title, authors, publication_year, citation_count,
                doi, url, abstract, journal, venue, keywords, api_source,
                relevance_score, total_score, domain_score, mode_score, rank_position
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                search_history_id,
                paper.title,
                json.dumps(
                    [
                        {"name": a.name, "institution": a.institution}
                        for a in paper.authors
                    ]
                ),
                paper.publication_year,
                paper.citation_count,
                paper.doi,
                paper.url,
                paper.abstract,
                paper.journal,
                paper.venue,
                json.dumps(paper.keywords) if paper.keywords else None,
                paper.source_api,
                paper.relevance_score,
                paper.total_score,
                getattr(paper, "domain_score", None),
                getattr(paper, "mode_score", None),
                rank,
            ),
        )

    def get_search_history(
        self,
        limit: int = 50,
        search_type: str = None,
        domain: str = None,
        days_back: int = None,
    ) -> List[Dict[str, Any]]:
        """
        検索履歴を取得

        Args:
            limit: 取得件数上限
            search_type: 検索タイプフィルタ
            domain: ドメインフィルタ
            days_back: 過去N日間

        Returns:
            検索履歴リスト
        """
        try:
            with self.get_connection() as conn:
                conditions = []
                params = []

                if search_type:
                    conditions.append("search_type = ?")
                    params.append(search_type)

                if domain:
                    conditions.append("domain = ?")
                    params.append(domain)

                if days_back:
                    conditions.append(
                        "timestamp >= datetime('now', '-{} days')".format(days_back)
                    )

                where_clause = (
                    " WHERE " + " AND ".join(conditions) if conditions else ""
                )

                cursor = conn.execute(
                    f"""
                    SELECT * FROM search_history
                    {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT ?
                """,
                    params + [limit],
                )

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"検索履歴取得エラー: {e}")
            return []

    def get_search_results(self, search_history_id: int) -> List[Dict[str, Any]]:
        """特定の検索の結果詳細を取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM search_results
                    WHERE search_history_id = ?
                    ORDER BY rank_position
                """,
                    (search_history_id,),
                )

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"検索結果取得エラー: {e}")
            return []

    def get_statistics(self, days_back: int = 30) -> Dict[str, Any]:
        """検索統計を取得"""
        try:
            with self.get_connection() as conn:
                # 基本統計
                cursor = conn.execute(
                    """
                    SELECT
                        COUNT(*) as total_searches,
                        COUNT(DISTINCT query) as unique_queries,
                        AVG(total_results) as avg_results,
                        AVG(execution_time_seconds) as avg_execution_time,
                        COUNT(CASE WHEN saved_to_obsidian THEN 1 END) as saved_to_obsidian_count
                    FROM search_history
                    WHERE timestamp >= datetime('now', '-{} days')
                """.format(
                        days_back
                    )
                )

                basic_stats = dict(cursor.fetchone())

                # 人気キーワード
                cursor = conn.execute(
                    """
                    SELECT keyword, search_count
                    FROM popular_keywords
                    ORDER BY search_count DESC
                    LIMIT 10
                """
                )

                popular_keywords = [dict(row) for row in cursor.fetchall()]

                # ドメイン別統計
                cursor = conn.execute(
                    """
                    SELECT domain, COUNT(*) as count
                    FROM search_history
                    WHERE domain IS NOT NULL
                    AND timestamp >= datetime('now', '-{} days')
                    GROUP BY domain
                    ORDER BY count DESC
                """.format(
                        days_back
                    )
                )

                domain_stats = [dict(row) for row in cursor.fetchall()]

                # API使用統計
                cursor = conn.execute(
                    """
                    SELECT api_source, COUNT(*) as count
                    FROM search_results sr
                    JOIN search_history sh ON sr.search_history_id = sh.id
                    WHERE sh.timestamp >= datetime('now', '-{} days')
                    GROUP BY api_source
                    ORDER BY count DESC
                """.format(
                        days_back
                    )
                )

                api_stats = [dict(row) for row in cursor.fetchall()]

                return {
                    "basic": basic_stats,
                    "popular_keywords": popular_keywords,
                    "domain_stats": domain_stats,
                    "api_stats": api_stats,
                    "period_days": days_back,
                }

        except Exception as e:
            logger.error(f"統計取得エラー: {e}")
            return {}

    def add_note(self, search_history_id: int, note: str):
        """検索履歴にノートを追加"""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    """
                    UPDATE search_history
                    SET notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (note, search_history_id),
                )
                conn.commit()

        except Exception as e:
            logger.error(f"ノート追加エラー: {e}")
            raise


# シングルトンインスタンス
_db_instance = None


def get_search_history_db() -> SearchHistoryDB:
    """SearchHistoryDBのシングルトンインスタンスを取得"""
    global _db_instance
    if _db_instance is None:
        _db_instance = SearchHistoryDB()
    return _db_instance
