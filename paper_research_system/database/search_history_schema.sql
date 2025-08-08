-- Paper Research System - Search History Database Schema
-- 論文検索システム - 検索履歴データベーススキーマ

-- 検索履歴メインテーブル
CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,                    -- 検索クエリ
    search_type TEXT NOT NULL,              -- 'integrated' or 'specialized'
    domain TEXT,                            -- specialized検索の場合のドメイン
    thinking_mode TEXT,                     -- specialized検索の場合のモード
    max_results INTEGER NOT NULL,          -- 最大結果数
    output_format TEXT NOT NULL,           -- 出力形式
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    execution_time_seconds REAL,           -- 検索実行時間（秒）
    total_results INTEGER DEFAULT 0,       -- 実際に取得した結果数
    api_calls TEXT,                        -- 使用したAPI (JSON形式)
    saved_to_obsidian BOOLEAN DEFAULT FALSE,
    notes TEXT,                            -- ユーザーノート
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 検索結果詳細テーブル
CREATE TABLE IF NOT EXISTS search_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    search_history_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    authors TEXT,                          -- JSON形式で著者情報
    publication_year INTEGER,
    citation_count INTEGER DEFAULT 0,
    doi TEXT,
    url TEXT,
    abstract TEXT,
    journal TEXT,
    venue TEXT,
    keywords TEXT,                         -- JSON形式
    api_source TEXT NOT NULL,              -- 'openalex', 'crossref', 'semantic_scholar'
    relevance_score REAL,
    total_score REAL,
    domain_score REAL,                     -- specialized検索の場合
    mode_score REAL,                       -- specialized検索の場合
    rank_position INTEGER,                 -- 検索結果内での順位
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (search_history_id) REFERENCES search_history (id) ON DELETE CASCADE
);

-- 検索統計集計テーブル
CREATE TABLE IF NOT EXISTS search_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,                    -- 日付
    total_searches INTEGER DEFAULT 0,      -- 日別検索回数
    unique_queries INTEGER DEFAULT 0,      -- ユニーク検索クエリ数
    most_common_domain TEXT,               -- 最頻ドメイン
    most_common_thinking_mode TEXT,        -- 最頻思考モード
    avg_results_per_search REAL,          -- 平均結果数
    avg_execution_time REAL,              -- 平均実行時間
    api_usage TEXT,                       -- API使用統計 (JSON形式)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date)
);

-- 人気キーワードテーブル
CREATE TABLE IF NOT EXISTS popular_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL UNIQUE,
    search_count INTEGER DEFAULT 1,
    last_searched DATETIME DEFAULT CURRENT_TIMESTAMP,
    first_searched DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_search_history_timestamp ON search_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_search_history_query ON search_history(query);
CREATE INDEX IF NOT EXISTS idx_search_history_type ON search_history(search_type);
CREATE INDEX IF NOT EXISTS idx_search_history_domain ON search_history(domain);
CREATE INDEX IF NOT EXISTS idx_search_results_search_id ON search_results(search_history_id);
CREATE INDEX IF NOT EXISTS idx_search_results_api_source ON search_results(api_source);
CREATE INDEX IF NOT EXISTS idx_search_results_citation_count ON search_results(citation_count);
CREATE INDEX IF NOT EXISTS idx_popular_keywords_count ON popular_keywords(search_count);
CREATE INDEX IF NOT EXISTS idx_statistics_date ON search_statistics(date);

-- トリガー: 統計情報の自動更新
CREATE TRIGGER IF NOT EXISTS update_search_statistics 
AFTER INSERT ON search_history
BEGIN
    INSERT OR REPLACE INTO search_statistics (
        date, 
        total_searches, 
        unique_queries,
        avg_results_per_search,
        avg_execution_time
    )
    SELECT 
        DATE(NEW.timestamp) as date,
        COUNT(*) as total_searches,
        COUNT(DISTINCT query) as unique_queries,
        AVG(total_results) as avg_results_per_search,
        AVG(execution_time_seconds) as avg_execution_time
    FROM search_history 
    WHERE DATE(timestamp) = DATE(NEW.timestamp);
END;

-- キーワード統計の更新トリガー
CREATE TRIGGER IF NOT EXISTS update_keyword_stats
AFTER INSERT ON search_history
BEGIN
    INSERT OR REPLACE INTO popular_keywords (keyword, search_count, last_searched)
    SELECT 
        NEW.query,
        COALESCE((SELECT search_count FROM popular_keywords WHERE keyword = NEW.query), 0) + 1,
        NEW.timestamp;
END;