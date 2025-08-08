-- AI Systems データベース初期化スクリプト

-- データベース作成
CREATE DATABASE IF NOT EXISTS ai_systems;

-- 使用するデータベースを設定
\c ai_systems;

-- 拡張機能の有効化
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ユーザーテーブル
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API Keys テーブル
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_name VARCHAR(100) NOT NULL,
    key_type VARCHAR(50) NOT NULL, -- 'claude', 'openai', 'groq'
    key_value TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 論文メタデータテーブル
CREATE TABLE IF NOT EXISTS paper_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    authors TEXT[] NOT NULL,
    abstract TEXT,
    doi VARCHAR(255),
    publication_year INTEGER,
    journal VARCHAR(255),
    citation_count INTEGER,
    institutions TEXT[],
    keywords TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- スクリプト生成履歴テーブル
CREATE TABLE IF NOT EXISTS script_generations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    paper_id UUID REFERENCES paper_metadata(id) ON DELETE CASCADE,
    script_type VARCHAR(50) NOT NULL, -- 'composer', 'mcp', 'hybrid'
    style VARCHAR(50) NOT NULL,
    input_data JSONB NOT NULL,
    output_script TEXT NOT NULL,
    generation_time_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- システムメトリクステーブル
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    metric_unit VARCHAR(20),
    service_name VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ログテーブル
CREATE TABLE IF NOT EXISTS system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level VARCHAR(10) NOT NULL, -- 'DEBUG', 'INFO', 'WARNING', 'ERROR'
    service_name VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- アラート履歴テーブル
CREATE TABLE IF NOT EXISTS alert_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_name VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL, -- 'info', 'warning', 'critical'
    message TEXT NOT NULL,
    details JSONB,
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- バックアップ履歴テーブル
CREATE TABLE IF NOT EXISTS backup_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backup_type VARCHAR(50) NOT NULL, -- 'database', 'files', 'vault'
    backup_path VARCHAR(500) NOT NULL,
    backup_size_bytes BIGINT,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_type ON api_keys(key_type);
CREATE INDEX IF NOT EXISTS idx_paper_metadata_title ON paper_metadata USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_paper_metadata_authors ON paper_metadata USING gin(authors);
CREATE INDEX IF NOT EXISTS idx_paper_metadata_keywords ON paper_metadata USING gin(keywords);
CREATE INDEX IF NOT EXISTS idx_script_generations_user_id ON script_generations(user_id);
CREATE INDEX IF NOT EXISTS idx_script_generations_paper_id ON script_generations(paper_id);
CREATE INDEX IF NOT EXISTS idx_script_generations_created_at ON script_generations(created_at);
CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_service ON system_logs(service_name);
CREATE INDEX IF NOT EXISTS idx_alert_history_created_at ON alert_history(created_at);
CREATE INDEX IF NOT EXISTS idx_alert_history_severity ON alert_history(severity);
CREATE INDEX IF NOT EXISTS idx_backup_history_created_at ON backup_history(created_at);

-- ビュー作成
CREATE OR REPLACE VIEW script_generation_stats AS
SELECT 
    script_type,
    style,
    COUNT(*) as total_generations,
    COUNT(CASE WHEN success = true THEN 1 END) as successful_generations,
    COUNT(CASE WHEN success = false THEN 1 END) as failed_generations,
    AVG(generation_time_ms) as avg_generation_time_ms,
    MIN(created_at) as first_generation,
    MAX(created_at) as last_generation
FROM script_generations
GROUP BY script_type, style;

CREATE OR REPLACE VIEW system_health_summary AS
SELECT 
    service_name,
    COUNT(*) as total_metrics,
    AVG(metric_value) as avg_metric_value,
    MAX(metric_value) as max_metric_value,
    MIN(metric_value) as min_metric_value,
    MAX(timestamp) as last_updated
FROM system_metrics
WHERE timestamp >= NOW() - INTERVAL '1 hour'
GROUP BY service_name;

-- 関数作成
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- トリガー作成
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON api_keys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_paper_metadata_updated_at BEFORE UPDATE ON paper_metadata
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 初期データ挿入
INSERT INTO users (username, email, password_hash, role) VALUES
('admin', 'admin@ai-systems.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3ZxQQxq3Hy', 'admin'),
('demo_user', 'demo@ai-systems.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3ZxQQxq3Hy', 'user')
ON CONFLICT (username) DO NOTHING;

-- サンプル論文メタデータ
INSERT INTO paper_metadata (title, authors, abstract, doi, publication_year, journal, citation_count, institutions, keywords) VALUES
('AI技術を用いた営業効率化の研究', ARRAY['田中太郎', '佐藤花子'], '本研究では、AI技術を用いて営業活動の効率化を図る手法を提案する。', '10.1000/example.2024.001', 2024, 'AI研究ジャーナル', 15, ARRAY['東京大学'], ARRAY['AI', '営業効率化', '機械学習']),
('音声AIシステムの実用化に関する考察', ARRAY['山田次郎', '鈴木美咲'], '音声AIシステムの実用化における課題と解決策について考察する。', '10.1000/example.2024.002', 2024, '音声技術研究', 8, ARRAY['京都大学'], ARRAY['音声AI', '実用化', '音声認識'])
ON CONFLICT DO NOTHING;

-- 権限設定
GRANT ALL PRIVILEGES ON DATABASE ai_systems TO ai_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ai_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ai_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO ai_user;

-- テーブル作成後の権限付与
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ai_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ai_user;

-- 完了メッセージ
SELECT 'AI Systems データベース初期化完了' as status; 