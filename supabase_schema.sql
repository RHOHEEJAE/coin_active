-- Supabase SQL Editor에서 한 번 실행 (테이블 생성)
-- Dashboard > SQL Editor > New query > 붙여넣기 > Run

CREATE TABLE IF NOT EXISTS top_holders (
  symbol VARCHAR(20) NOT NULL,
  rank INT NOT NULL,
  wallet_address TEXT NOT NULL,
  balance_raw TEXT NOT NULL,
  balance_human TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (symbol, rank)
);

CREATE TABLE IF NOT EXISTS holder_max (
  symbol VARCHAR(20) PRIMARY KEY,
  wallet_address TEXT NOT NULL,
  balance_raw TEXT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS holder_alerts (
  id BIGSERIAL PRIMARY KEY,
  symbol VARCHAR(20) NOT NULL,
  alert_type VARCHAR(10) NOT NULL,
  wallet_address TEXT NOT NULL,
  rank INT,
  balance_before TEXT,
  balance_after TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS holder_last_balance (
  symbol VARCHAR(20) NOT NULL,
  wallet_address TEXT NOT NULL,
  balance_raw TEXT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (symbol, wallet_address)
);

-- RLS 정책: 익명/인증 사용자 읽기 허용 (Vercel 대시보드용)
ALTER TABLE top_holders ENABLE ROW LEVEL SECURITY;
ALTER TABLE holder_alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read top_holders" ON top_holders FOR SELECT USING (true);
CREATE POLICY "Allow public read holder_alerts" ON holder_alerts FOR SELECT USING (true);
