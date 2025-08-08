-- ===================================================================
-- ROLEPLAY DATABASE SCHEMA (PostgreSQL)
-- 音声ロールプレイシステム v2.0.0 - リアルタイム処理用
-- ===================================================================

-- ユーザー管理テーブル
CREATE TABLE users (
    user_id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    username VARCHAR(100),
    user_type VARCHAR(20) DEFAULT 'sales_person', -- sales_person, manager, admin
    experience_level VARCHAR(20) DEFAULT 'beginner', -- beginner, intermediate, expert
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    
    -- プロフィール情報
    department VARCHAR(100),
    position VARCHAR(100),
    industry VARCHAR(100),
    target_skills JSONB, -- 強化したいスキル一覧
    
    -- システム設定
    preferences JSONB DEFAULT '{}', -- UI設定、音声設定等
    notification_settings JSONB DEFAULT '{
        "email_enabled": true,
        "reminder_days": [3, 1, 0],
        "timezone": "Asia/Tokyo",
        "enable_shame_system": false
    }'
);

-- セッション管理テーブル
CREATE TABLE roleplay_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(50) REFERENCES users(user_id),
    scenario_id UUID REFERENCES scenarios(scenario_id),
    
    -- セッション状態
    status VARCHAR(20) DEFAULT 'active', -- active, completed, paused, cancelled
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- 会話設定
    speaker_id INTEGER DEFAULT 6, -- VOICEVOX話者ID
    ai_provider VARCHAR(20) DEFAULT 'groq', -- groq, openai, anthropic, google
    conversation_mode VARCHAR(30) DEFAULT 'sales_training', -- sales_training, objection_handling, closing
    
    -- セッション文脈
    conversation_context JSONB DEFAULT '{}',
    customer_profile JSONB DEFAULT '{}', -- 想定顧客プロフィール
    
    -- パフォーマンス指標（リアルタイム用）
    total_interactions INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER,
    audio_quality_score DECIMAL(3,2),
    
    -- メタデータ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 会話履歴テーブル
CREATE TABLE conversation_history (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES roleplay_sessions(session_id) ON DELETE CASCADE,
    
    -- 会話情報
    sequence_number INTEGER NOT NULL, -- セッション内順序
    speaker_role VARCHAR(10) NOT NULL, -- 'user' or 'ai'
    
    -- 音声データ
    audio_file_path TEXT,
    audio_duration_ms INTEGER,
    audio_format VARCHAR(10) DEFAULT 'wav',
    
    -- テキストデータ
    transcription TEXT,
    ai_response_text TEXT,
    confidence_score DECIMAL(3,2),
    
    -- タイミング情報
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    audio_processed_at TIMESTAMP WITH TIME ZONE,
    ai_responded_at TIMESTAMP WITH TIME ZONE,
    synthesis_completed_at TIMESTAMP WITH TIME ZONE,
    
    -- 分析用メタデータ
    intent_detected VARCHAR(100),
    sentiment_score DECIMAL(3,2),
    objection_type VARCHAR(50),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 音声ファイル管理テーブル
CREATE TABLE audio_files (
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversation_history(conversation_id),
    
    -- ファイル情報
    file_path TEXT NOT NULL,
    file_name VARCHAR(255),
    file_size_bytes BIGINT,
    mime_type VARCHAR(50),
    
    -- 音声品質情報
    sample_rate INTEGER,
    bit_depth INTEGER,
    channels INTEGER,
    duration_ms INTEGER,
    
    -- 処理状況
    processing_status VARCHAR(20) DEFAULT 'pending', -- pending, processed, failed
    quality_score DECIMAL(3,2),
    noise_level_db DECIMAL(4,1),
    
    -- ライフサイクル管理
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ロールプレイシナリオテーブル
CREATE TABLE scenarios (
    scenario_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- シナリオ基本情報
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50), -- sales_basics, objection_handling, closing, etc.
    difficulty_level VARCHAR(20) DEFAULT 'beginner', -- beginner, intermediate, expert
    industry VARCHAR(100),
    
    -- シナリオ詳細
    customer_persona JSONB, -- 顧客ペルソナ情報
    scenario_script JSONB, -- シナリオ台本・フロー
    success_criteria JSONB, -- 成功基準
    common_objections JSONB, -- よくある異議
    
    -- メタデータ
    created_by VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 利用制限管理テーブル（現在のJSONファイルからの移行）
CREATE TABLE user_usage_limits (
    user_id VARCHAR(50) PRIMARY KEY REFERENCES users(user_id),
    
    -- 制限情報
    roleplay_sessions_remaining INTEGER DEFAULT 100,
    video_processing_minutes_used INTEGER DEFAULT 0,
    monthly_limit_roleplay INTEGER DEFAULT 100,
    monthly_limit_video_minutes INTEGER DEFAULT 60,
    
    -- リセット管理
    last_reset_date DATE DEFAULT CURRENT_DATE,
    total_roleplay_sessions INTEGER DEFAULT 0,
    consecutive_days INTEGER DEFAULT 0,
    
    -- 最新活動
    last_roleplay_date DATE,
    recent_sessions JSONB DEFAULT '[]',
    recent_improvement_points JSONB DEFAULT '[]',
    
    -- 管理情報
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- インデックス設定（パフォーマンス最適化）
CREATE INDEX idx_sessions_user_status ON roleplay_sessions(user_id, status);
CREATE INDEX idx_sessions_created_at ON roleplay_sessions(created_at);
CREATE INDEX idx_conversations_session_sequence ON conversation_history(session_id, sequence_number);
CREATE INDEX idx_conversations_created_at ON conversation_history(created_at);
CREATE INDEX idx_audio_files_expires_at ON audio_files(expires_at);
CREATE INDEX idx_scenarios_category_difficulty ON scenarios(category, difficulty_level);

-- トリガー設定（自動更新）
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON roleplay_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_scenarios_updated_at BEFORE UPDATE ON scenarios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_usage_limits_updated_at BEFORE UPDATE ON user_usage_limits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
