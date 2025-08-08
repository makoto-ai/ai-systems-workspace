-- ===================================================================
-- ANALYTICS DATABASE SCHEMA (TimescaleDB)
-- 音声ロールプレイシステム v2.0.0 - 分析・ROI測定用
-- ===================================================================

-- TimescaleDB拡張の有効化
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 音声分析メトリクステーブル（時系列データ）
CREATE TABLE voice_analysis_metrics (
    time TIMESTAMPTZ NOT NULL,
    session_id UUID NOT NULL,
    conversation_id UUID,
    user_id VARCHAR(50) NOT NULL,
    
    -- 音声特徴データ
    metric_type VARCHAR(50) NOT NULL, -- pitch, pace, volume, pause_duration, intonation
    metric_value DOUBLE PRECISION NOT NULL,
    metric_unit VARCHAR(20), -- Hz, dB, ms, ratio
    
    -- 分析メタデータ
    analysis_engine VARCHAR(20) DEFAULT 'whisperx', -- whisperx, custom_ml
    confidence_score DOUBLE PRECISION,
    analysis_version VARCHAR(10) DEFAULT '1.0',
    
    -- セグメント情報
    audio_segment_start_ms INTEGER,
    audio_segment_end_ms INTEGER,
    segment_duration_ms INTEGER,
    
    PRIMARY KEY (time, session_id, metric_type)
);

-- TimescaleDBハイパーテーブル化
SELECT create_hypertable('voice_analysis_metrics', 'time');

-- トークスキル分析テーブル
CREATE TABLE talk_skill_analysis (
    time TIMESTAMPTZ NOT NULL,
    session_id UUID NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    
    -- スキル評価項目
    skill_category VARCHAR(50) NOT NULL, -- question_technique, listening, closing, confidence
    skill_subcategory VARCHAR(50), -- open_question, fact_question, emotional_listening
    
    -- 評価スコア
    score DOUBLE PRECISION NOT NULL, -- 0-100
    benchmark_score DOUBLE PRECISION, -- 業界平均
    improvement_rate DOUBLE PRECISION, -- 前回からの改善率
    
    -- 評価根拠
    evaluation_criteria JSONB,
    specific_examples JSONB, -- 良い例・悪い例
    improvement_suggestions JSONB,
    
    -- メタデータ
    evaluation_method VARCHAR(30) DEFAULT 'ai_analysis', -- ai_analysis, manual_review
    evaluator_id VARCHAR(50),
    
    PRIMARY KEY (time, session_id, skill_category)
);

SELECT create_hypertable('talk_skill_analysis', 'time');

-- フィリップスROI評価テーブル
CREATE TABLE phillips_roi_evaluation (
    evaluation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(50) NOT NULL,
    
    -- フィリップス4レベル評価
    phillips_level INTEGER NOT NULL CHECK (phillips_level IN (1,2,3,4)),
    
    -- レベル1: 反応 (Reaction)
    satisfaction_score DOUBLE PRECISION, -- システム満足度
    usability_score DOUBLE PRECISION,    -- 使いやすさ
    engagement_score DOUBLE PRECISION,   -- エンゲージメント
    continuation_intent BOOLEAN,         -- 継続利用意向
    
    -- レベル2: 学習 (Learning)
    skill_acquisition_score DOUBLE PRECISION, -- スキル習得度
    knowledge_retention_score DOUBLE PRECISION, -- 知識定着度
    competency_improvement JSONB, -- 能力向上項目別スコア
    
    -- レベル3: 行動変容 (Behavior)
    behavior_change_indicators JSONB, -- 行動変化指標
    performance_improvement DOUBLE PRECISION, -- パフォーマンス向上
    adoption_rate DOUBLE PRECISION, -- 学習内容の実践率
    
    -- レベル4: 結果 (Results)
    business_impact_metrics JSONB, -- ビジネス影響指標
    roi_percentage DOUBLE PRECISION, -- ROI（%）
    cost_savings DECIMAL(12,2), -- コスト削減額
    revenue_increase DECIMAL(12,2), -- 売上増加額
    
    -- 評価期間・条件
    evaluation_period_start DATE,
    evaluation_period_end DATE,
    baseline_period_start DATE,
    baseline_period_end DATE,
    
    -- メタデータ
    evaluation_method VARCHAR(30) DEFAULT 'automated',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50)
);

-- システムパフォーマンスメトリクス
CREATE TABLE system_performance_metrics (
    time TIMESTAMPTZ NOT NULL,
    metric_category VARCHAR(50) NOT NULL, -- response_time, audio_quality, system_load
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    
    -- システム情報
    instance_id VARCHAR(50),
    service_component VARCHAR(50), -- voicevox, whisperx, groq_api, fastapi
    
    -- リクエスト情報
    session_id UUID,
    user_id VARCHAR(50),
    request_id UUID,
    
    -- エラー情報
    error_count INTEGER DEFAULT 0,
    error_details JSONB,
    
    PRIMARY KEY (time, metric_category, metric_name)
);

SELECT create_hypertable('system_performance_metrics', 'time');

-- ユーザー成長トラッキング
CREATE TABLE user_growth_tracking (
    time TIMESTAMPTZ NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    
    -- 成長指標
    overall_progress_score DOUBLE PRECISION, -- 総合進捗スコア
    skill_balance_score DOUBLE PRECISION,    -- スキルバランス
    consistency_score DOUBLE PRECISION,     -- 継続性スコア
    challenge_level DOUBLE PRECISION,       -- 挑戦レベル
    
    -- 具体的成長データ
    sessions_completed INTEGER,
    total_practice_time_minutes INTEGER,
    scenarios_mastered INTEGER,
    skills_improved JSONB,
    
    -- 目標達成状況
    monthly_goal_progress DOUBLE PRECISION,
    quarterly_goal_progress DOUBLE PRECISION,
    target_achievement_date DATE,
    
    -- 推奨事項
    next_recommended_scenario UUID,
    focus_areas JSONB,
    estimated_mastery_timeline JSONB,
    
    PRIMARY KEY (time, user_id)
);

SELECT create_hypertable('user_growth_tracking', 'time');

-- 営業成果トラッキング（ROI計算用）
CREATE TABLE sales_performance_tracking (
    time TIMESTAMPTZ NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    
    -- 営業成果指標
    conversion_rate DOUBLE PRECISION,      -- 成約率
    average_deal_size DECIMAL(12,2),      -- 平均案件サイズ
    sales_cycle_days INTEGER,             -- 営業サイクル
    customer_satisfaction DOUBLE PRECISION, -- 顧客満足度
    
    -- 活動指標
    calls_made INTEGER,
    meetings_scheduled INTEGER,
    proposals_sent INTEGER,
    deals_closed INTEGER,
    
    -- 前年同期比
    yoy_conversion_improvement DOUBLE PRECISION,
    yoy_deal_size_improvement DOUBLE PRECISION,
    yoy_cycle_improvement DOUBLE PRECISION,
    
    -- トレーニング関連
    training_sessions_since_last_measure INTEGER,
    skills_practiced JSONB,
    correlation_score DOUBLE PRECISION, -- トレーニングとパフォーマンスの相関
    
    PRIMARY KEY (time, user_id)
);

SELECT create_hypertable('sales_performance_tracking', 'time');

-- 音声品質分析テーブル
CREATE TABLE audio_quality_analysis (
    time TIMESTAMPTZ NOT NULL,
    session_id UUID NOT NULL,
    audio_file_id UUID,
    
    -- 品質指標
    overall_quality_score DOUBLE PRECISION, -- 総合品質スコア
    clarity_score DOUBLE PRECISION,         -- 明瞭度
    naturalness_score DOUBLE PRECISION,     -- 自然さ
    emotional_expression_score DOUBLE PRECISION, -- 感情表現
    
    -- 技術的品質
    snr_db DOUBLE PRECISION,              -- S/N比
    thd_percentage DOUBLE PRECISION,      -- 歪み率
    frequency_response_score DOUBLE PRECISION, -- 周波数特性
    
    -- 発話特徴
    speech_rate_wpm DOUBLE PRECISION,     -- 発話速度（語/分）
    pause_frequency DOUBLE PRECISION,     -- ポーズ頻度
    volume_consistency DOUBLE PRECISION,   -- 音量一定性
    pitch_variation DOUBLE PRECISION,     -- ピッチ変動
    
    -- 分析エンジン情報
    analysis_engine VARCHAR(30),
    analysis_model_version VARCHAR(20),
    processing_time_ms INTEGER,
    
    PRIMARY KEY (time, session_id)
);

SELECT create_hypertable('audio_quality_analysis', 'time');

-- 集計ビュー（レポート用）
CREATE VIEW monthly_performance_summary AS
SELECT 
    date_trunc('month', time) as month,
    user_id,
    COUNT(*) as total_sessions,
    AVG(score) as avg_skill_score,
    AVG(improvement_rate) as avg_improvement_rate
FROM talk_skill_analysis 
GROUP BY date_trunc('month', time), user_id;

CREATE VIEW daily_system_health AS
SELECT 
    date_trunc('day', time) as day,
    metric_category,
    AVG(metric_value) as avg_value,
    MIN(metric_value) as min_value,
    MAX(metric_value) as max_value,
    COUNT(*) as sample_count
FROM system_performance_metrics 
GROUP BY date_trunc('day', time), metric_category;

-- 自動集計ポリシー（データ保持・圧縮）
SELECT add_retention_policy('voice_analysis_metrics', INTERVAL '2 years');
SELECT add_retention_policy('system_performance_metrics', INTERVAL '1 year');
SELECT add_compression_policy('voice_analysis_metrics', INTERVAL '7 days');
SELECT add_compression_policy('system_performance_metrics', INTERVAL '3 days');

-- インデックス設定
CREATE INDEX idx_voice_metrics_user_time ON voice_analysis_metrics(user_id, time);
CREATE INDEX idx_talk_skill_user_category ON talk_skill_analysis(user_id, skill_category);
CREATE INDEX idx_roi_evaluation_user_level ON phillips_roi_evaluation(user_id, phillips_level);
CREATE INDEX idx_performance_metrics_component ON system_performance_metrics(service_component, time);
