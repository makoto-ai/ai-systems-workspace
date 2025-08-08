-- Citation Network Graph Database Schema
-- 引用ネットワーク グラフデータベース スキーマ

-- ノード（論文）テーブル
CREATE TABLE IF NOT EXISTS citation_nodes (
    paper_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    authors TEXT,  -- JSON形式の著者リスト
    publication_year INTEGER,
    citation_count INTEGER DEFAULT 0,
    doi TEXT,
    source_api TEXT,
    abstract TEXT,
    journal TEXT,
    url TEXT,
    
    -- ネットワーク分析用
    depth INTEGER DEFAULT 0,  -- 検索起点からの深度
    in_degree INTEGER DEFAULT 0,  -- 被引用数
    out_degree INTEGER DEFAULT 0,  -- 引用数
    betweenness_centrality REAL DEFAULT 0.0,  -- 媒介中心性
    pagerank_score REAL DEFAULT 0.0,  -- PageRankスコア
    
    -- メタデータ
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    -- インデックス用
    title_normalized TEXT,  -- 正規化タイトル
    year_range TEXT,  -- 年代レンジ（例: "2020s"）
    author_count INTEGER DEFAULT 0
);

-- エッジ（引用関係）テーブル
CREATE TABLE IF NOT EXISTS citation_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_paper_id TEXT NOT NULL,
    to_paper_id TEXT NOT NULL,
    citation_context TEXT,  -- 引用の文脈
    citation_type TEXT DEFAULT 'direct',  -- direct, co-citation, bibliographic
    weight REAL DEFAULT 1.0,  -- 引用の重み
    
    -- メタデータ
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (from_paper_id) REFERENCES citation_nodes (paper_id) ON DELETE CASCADE,
    FOREIGN KEY (to_paper_id) REFERENCES citation_nodes (paper_id) ON DELETE CASCADE,
    
    -- 重複防止
    UNIQUE(from_paper_id, to_paper_id)
);

-- ネットワーク分析結果テーブル
CREATE TABLE IF NOT EXISTS network_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_name TEXT NOT NULL,
    root_papers TEXT,  -- JSON形式の起点論文リスト
    total_nodes INTEGER,
    total_edges INTEGER,
    network_density REAL,
    max_depth INTEGER,
    
    -- 分析メトリクス
    average_clustering_coefficient REAL,
    diameter INTEGER,
    average_path_length REAL,
    
    -- トップ論文
    most_cited_paper_id TEXT,
    most_citing_paper_id TEXT,
    highest_pagerank_paper_id TEXT,
    
    -- 時間情報
    year_range_start INTEGER,
    year_range_end INTEGER,
    
    -- メタデータ
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    analysis_parameters TEXT,  -- JSON形式の分析パラメータ
    
    FOREIGN KEY (most_cited_paper_id) REFERENCES citation_nodes (paper_id),
    FOREIGN KEY (most_citing_paper_id) REFERENCES citation_nodes (paper_id),
    FOREIGN KEY (highest_pagerank_paper_id) REFERENCES citation_nodes (paper_id)
);

-- クラスター/コミュニティテーブル
CREATE TABLE IF NOT EXISTS citation_clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_name TEXT NOT NULL,
    analysis_id INTEGER NOT NULL,
    cluster_algorithm TEXT,  -- louvain, leiden, infomap など
    modularity_score REAL,
    
    -- クラスター特徴
    size INTEGER,  -- クラスター内論文数
    dominant_year INTEGER,  -- 主要年代
    dominant_keywords TEXT,  -- JSON形式のキーワードリスト
    
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (analysis_id) REFERENCES network_analysis (id) ON DELETE CASCADE
);

-- ノード-クラスター関係テーブル
CREATE TABLE IF NOT EXISTS node_cluster_membership (
    paper_id TEXT,
    cluster_id INTEGER,
    membership_strength REAL DEFAULT 1.0,  -- クラスターへの所属度
    
    PRIMARY KEY (paper_id, cluster_id),
    FOREIGN KEY (paper_id) REFERENCES citation_nodes (paper_id) ON DELETE CASCADE,
    FOREIGN KEY (cluster_id) REFERENCES citation_clusters (id) ON DELETE CASCADE
);

-- パス（経路）キャッシュテーブル
CREATE TABLE IF NOT EXISTS citation_paths (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_paper_id TEXT NOT NULL,
    end_paper_id TEXT NOT NULL,
    path_length INTEGER NOT NULL,
    path_nodes TEXT,  -- JSON形式のノードパス
    path_weight REAL,
    
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (start_paper_id) REFERENCES citation_nodes (paper_id) ON DELETE CASCADE,
    FOREIGN KEY (end_paper_id) REFERENCES citation_nodes (paper_id) ON DELETE CASCADE,
    
    UNIQUE(start_paper_id, end_paper_id)
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_citation_nodes_year ON citation_nodes(publication_year);
CREATE INDEX IF NOT EXISTS idx_citation_nodes_citations ON citation_nodes(citation_count DESC);
CREATE INDEX IF NOT EXISTS idx_citation_nodes_depth ON citation_nodes(depth);
CREATE INDEX IF NOT EXISTS idx_citation_nodes_pagerank ON citation_nodes(pagerank_score DESC);
CREATE INDEX IF NOT EXISTS idx_citation_nodes_title_norm ON citation_nodes(title_normalized);
CREATE INDEX IF NOT EXISTS idx_citation_nodes_doi ON citation_nodes(doi);

CREATE INDEX IF NOT EXISTS idx_citation_edges_from ON citation_edges(from_paper_id);
CREATE INDEX IF NOT EXISTS idx_citation_edges_to ON citation_edges(to_paper_id);
CREATE INDEX IF NOT EXISTS idx_citation_edges_weight ON citation_edges(weight DESC);

CREATE INDEX IF NOT EXISTS idx_network_analysis_created ON network_analysis(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_citation_clusters_analysis ON citation_clusters(analysis_id);
CREATE INDEX IF NOT EXISTS idx_node_cluster_paper ON node_cluster_membership(paper_id);
CREATE INDEX IF NOT EXISTS idx_node_cluster_cluster ON node_cluster_membership(cluster_id);

CREATE INDEX IF NOT EXISTS idx_citation_paths_start ON citation_paths(start_paper_id);
CREATE INDEX IF NOT EXISTS idx_citation_paths_end ON citation_paths(end_paper_id);
CREATE INDEX IF NOT EXISTS idx_citation_paths_length ON citation_paths(path_length);

-- ビュー作成
-- 論文の詳細情報とネットワーク統計
CREATE VIEW IF NOT EXISTS paper_network_stats AS
SELECT 
    n.paper_id,
    n.title,
    n.authors,
    n.publication_year,
    n.citation_count,
    n.doi,
    n.in_degree,
    n.out_degree,
    n.betweenness_centrality,
    n.pagerank_score,
    (n.in_degree + n.out_degree) AS total_connections,
    CASE 
        WHEN n.in_degree > n.out_degree THEN 'highly_cited'
        WHEN n.out_degree > n.in_degree THEN 'review_paper'
        ELSE 'balanced'
    END AS paper_type_network
FROM citation_nodes n;

-- エッジ統計ビュー
CREATE VIEW IF NOT EXISTS citation_edge_stats AS
SELECT 
    e.from_paper_id,
    e.to_paper_id,
    e.weight,
    n1.title AS from_title,
    n1.publication_year AS from_year,
    n2.title AS to_title,
    n2.publication_year AS to_year,
    (n1.publication_year - n2.publication_year) AS citation_lag
FROM citation_edges e
JOIN citation_nodes n1 ON e.from_paper_id = n1.paper_id
JOIN citation_nodes n2 ON e.to_paper_id = n2.paper_id;

-- 年代別引用ネットワーク統計
CREATE VIEW IF NOT EXISTS yearly_citation_stats AS
SELECT 
    n.publication_year,
    COUNT(*) AS papers_count,
    AVG(n.citation_count) AS avg_citations,
    AVG(n.in_degree) AS avg_in_degree,
    AVG(n.out_degree) AS avg_out_degree,
    AVG(n.pagerank_score) AS avg_pagerank
FROM citation_nodes n
WHERE n.publication_year IS NOT NULL
GROUP BY n.publication_year
ORDER BY n.publication_year;