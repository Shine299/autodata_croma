-- Database schema for AutoData (Supabase / PostgreSQL)

-- 1. Caché de respuestas crudas de Croma
CREATE TABLE IF NOT EXISTS croma_cache (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source        TEXT NOT NULL,          -- 'SBS' | 'SUTRAN' | 'SUNAT' ...
  lookup_key    TEXT NOT NULL,          -- placa normalizada o hash del documento
  payload       JSONB NOT NULL,         -- respuesta cruda, tal cual
  status        TEXT NOT NULL,          -- 'ok' | 'not_found' | 'error'
  fetched_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at    TIMESTAMPTZ NOT NULL,
  UNIQUE (source, lookup_key)
);
CREATE INDEX IF NOT EXISTS idx_croma_cache_expires_at ON croma_cache (expires_at);

-- 2. Registro de Verificaciones
CREATE TABLE IF NOT EXISTS verifications (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plate         TEXT NOT NULL,
  seller_hash   TEXT,                   -- sha256 del documento. NUNCA en claro (Art. VI)
  asking_price  NUMERIC,
  verdict       TEXT NOT NULL,
  risk_score    INT  NOT NULL,
  flags         JSONB NOT NULL DEFAULT '[]',
  payload       JSONB NOT NULL,         -- response completo del endpoint
  channel       TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_verifications_plate ON verifications (plate);

-- 3. Registro de Tasaciones
CREATE TABLE IF NOT EXISTS appraisals (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  verification_id UUID REFERENCES verifications(id) ON DELETE CASCADE,
  asking_price    NUMERIC NOT NULL,
  fair_price      NUMERIC NOT NULL,
  deductions      JSONB NOT NULL DEFAULT '[]',
  script          TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Registro de Cuotas y Bitácora de Croma
CREATE TABLE IF NOT EXISTS quota_log (
  id          BIGSERIAL PRIMARY KEY,
  source      TEXT NOT NULL,
  endpoint    TEXT NOT NULL,
  remaining   INT,
  request_id  TEXT,
  cache_hit   BOOLEAN NOT NULL DEFAULT FALSE,
  latency_ms  INT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Registro de Hilo de Conversación del Bot (Telegram)
CREATE TABLE IF NOT EXISTS conversations (
  chat_id     TEXT PRIMARY KEY,
  state       TEXT NOT NULL DEFAULT 'IDLE',
  context     JSONB NOT NULL DEFAULT '{}',
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
