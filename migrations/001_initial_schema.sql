-- V26MEME Initial Schema Migration
-- This creates the foundation for autonomous pattern discovery

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Core table for discovered trading patterns
CREATE TABLE discovered_patterns (
    pattern_hash VARCHAR(64) PRIMARY KEY,
    discovery_timestamp TIMESTAMPTZ DEFAULT NOW(),
    entry_conditions JSONB NOT NULL,
    exit_conditions JSONB NOT NULL,
    timeframe_minutes INTEGER,
    test_count INTEGER DEFAULT 0,
    win_count INTEGER DEFAULT 0,
    total_profit DECIMAL(15,2) DEFAULT 0,
    win_rate DECIMAL(5,4) DEFAULT 0,
    sharpe_ratio DECIMAL(8,4) DEFAULT 0,
    generation INTEGER DEFAULT 0,
    parent_patterns TEXT[] DEFAULT '{}',
    ai_enhanced BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT FALSE,
    last_triggered TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- All trades executed by the system
CREATE TABLE trades (
    trade_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_hash VARCHAR(64) REFERENCES discovered_patterns(pattern_hash),
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(4) NOT NULL CHECK (side IN ('buy', 'sell')),
    entry_price DECIMAL(20,8) NOT NULL,
    entry_time TIMESTAMPTZ NOT NULL,
    exit_price DECIMAL(20,8),
    exit_time TIMESTAMPTZ,
    position_size DECIMAL(15,2) NOT NULL,
    profit_loss DECIMAL(15,2),
    profit_loss_pct DECIMAL(8,4),
    fees DECIMAL(10,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed', 'cancelled')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Evolution history tracking
CREATE TABLE evolution_history (
    generation INTEGER PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    patterns_before INTEGER NOT NULL,
    patterns_after INTEGER NOT NULL,
    avg_fitness_before DECIMAL(8,4),
    avg_fitness_after DECIMAL(8,4),
    top_performer_hash VARCHAR(64),
    mutation_count INTEGER DEFAULT 0,
    crossover_count INTEGER DEFAULT 0,
    ai_enhanced_count INTEGER DEFAULT 0
);

-- Risk management events
CREATE TABLE risk_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    description TEXT NOT NULL,
    capital_at_event DECIMAL(15,2),
    drawdown_pct DECIMAL(5,4),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Performance metrics cache
CREATE TABLE performance_metrics (
    metric_date DATE PRIMARY KEY,
    total_capital DECIMAL(15,2),
    daily_pnl DECIMAL(15,2),
    total_trades INTEGER,
    winning_trades INTEGER,
    active_patterns INTEGER,
    avg_win_rate DECIMAL(5,4),
    best_pattern_hash VARCHAR(64),
    worst_pattern_hash VARCHAR(64),
    sharpe_ratio DECIMAL(8,4),
    max_drawdown DECIMAL(5,4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_patterns_active ON discovered_patterns(is_active);
CREATE INDEX idx_patterns_generation ON discovered_patterns(generation);
CREATE INDEX idx_patterns_win_rate ON discovered_patterns(win_rate DESC);
CREATE INDEX idx_patterns_sharpe ON discovered_patterns(sharpe_ratio DESC);

CREATE INDEX idx_trades_pattern ON trades(pattern_hash);
CREATE INDEX idx_trades_time ON trades(entry_time);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_status ON trades(status);

CREATE INDEX idx_evolution_generation ON evolution_history(generation);
CREATE INDEX idx_risk_events_type ON risk_events(event_type);
CREATE INDEX idx_risk_events_time ON risk_events(timestamp);

-- Functions for automatic timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_patterns_updated_at BEFORE UPDATE ON discovered_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Initial risk event
INSERT INTO risk_events (event_type, severity, description, capital_at_event)
VALUES ('system_start', 'info', 'V26MEME system initialized', 200.00);

-- Initial performance metric
INSERT INTO performance_metrics (metric_date, total_capital, daily_pnl, total_trades, winning_trades, active_patterns)
VALUES (CURRENT_DATE, 200.00, 0.00, 0, 0, 0);
