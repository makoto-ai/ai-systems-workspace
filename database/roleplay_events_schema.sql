-- Roleplay Events Schema (Postgres)
-- Safe template. Apply with: psql $DATABASE_URL -f database/roleplay_events_schema.sql

BEGIN;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tenants (optional reference)
CREATE TABLE IF NOT EXISTS tenants (
  tenant_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Users (scoped by tenant)
CREATE TABLE IF NOT EXISTS users (
  user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
  email TEXT,
  display_name TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Sessions (training/roleplay session)
CREATE TABLE IF NOT EXISTS sessions (
  session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
  user_id UUID REFERENCES users(user_id),
  started_at TIMESTAMPTZ DEFAULT now(),
  ended_at TIMESTAMPTZ,
  scenario_id TEXT
);

-- Turns (per utterance)
CREATE TABLE IF NOT EXISTS turns (
  turn_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID NOT NULL REFERENCES sessions(session_id),
  tenant_id TEXT NOT NULL,
  role TEXT NOT NULL, -- user/ai
  text TEXT,
  latency_ms INT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Scores (evaluation metrics per turn/session)
CREATE TABLE IF NOT EXISTS scores (
  score_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID NOT NULL REFERENCES sessions(session_id),
  turn_id UUID REFERENCES turns(turn_id),
  tenant_id TEXT NOT NULL,
  metrics JSONB NOT NULL, -- {ng_rate, rebuttal_success, silence_ratio, ...}
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Scenarios (branching definitions)
CREATE TABLE IF NOT EXISTS scenarios (
  scenario_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  definition JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Simulation runs
CREATE TABLE IF NOT EXISTS sim_runs (
  sim_run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id TEXT NOT NULL,
  scenario_id TEXT REFERENCES scenarios(scenario_id),
  params JSONB,
  result JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Append-only Events (integration layer)
CREATE TABLE IF NOT EXISTS events (
  event_id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  session_id UUID,
  turn_id UUID,
  event_type TEXT NOT NULL, -- ingest_turn, score, sim_run, etc
  payload JSONB NOT NULL,
  ts TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_events_tenant_ts ON events(tenant_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_events_type_ts ON events(event_type, ts DESC);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);

-- Row Level Security (RLS) - tenant isolation
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
CREATE POLICY IF NOT EXISTS events_tenant_isolation ON events
  USING (tenant_id = current_setting('app.tenant_id', true));

ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY IF NOT EXISTS sessions_tenant_isolation ON sessions
  USING (tenant_id = current_setting('app.tenant_id', true));

ALTER TABLE turns ENABLE ROW LEVEL SECURITY;
CREATE POLICY IF NOT EXISTS turns_tenant_isolation ON turns
  USING (tenant_id = current_setting('app.tenant_id', true));

ALTER TABLE scores ENABLE ROW LEVEL SECURITY;
CREATE POLICY IF NOT EXISTS scores_tenant_isolation ON scores
  USING (tenant_id = current_setting('app.tenant_id', true));

-- Materialized view for nightly KPIs (example)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kpi_overview AS
SELECT
  tenant_id,
  date_trunc('day', ts) AS day,
  COUNT(*) FILTER (WHERE event_type = 'ingest_turn') AS turns,
  AVG((payload->>'rebuttal_success')::NUMERIC) FILTER (WHERE event_type='score') AS rebuttal_success_rate,
  AVG((payload->>'ng_rate')::NUMERIC) FILTER (WHERE event_type='score') AS ng_rate,
  AVG((payload->>'silence_ratio')::NUMERIC) FILTER (WHERE event_type='score') AS silence_ratio
FROM events
GROUP BY tenant_id, date_trunc('day', ts);

CREATE INDEX IF NOT EXISTS idx_mv_kpi_overview_tenant_day ON mv_kpi_overview(tenant_id, day DESC);

COMMIT;


