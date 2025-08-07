CREATE DATABASE v26meme;

CREATE TABLE discovered_patterns (
    pattern_hash VARCHAR(64) PRIMARY KEY,
    discovery_timestamp TIMESTAMPTZ DEFAULT NOW(),
    entry_conditions JSONB NOT NULL,
    exit_conditions JSONB NOT NULL,
    timeframe_minutes INTEGER,
    test_count INTEGER DEFAULT 0,
    win_count INTEGER DEFAULT 0,
    total_profit DECIMAL(15,2) DEFAULT 0,
    win_rate DECIMAL(5,4),
    sharpe_ratio DECIMAL(8,4),
    generation INTEGER DEFAULT 0,
    parent_patterns TEXT[],
    ai_enhanced BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT FALSE,
    last_triggered TIMESTAMPTZ
);

CREATE TABLE trades (
    trade_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_hash VARCHAR(64),
    exchange VARCHAR(50),
    symbol VARCHAR(20),
    side VARCHAR(4),
    entry_price DECIMAL(20,8),
    entry_time TIMESTAMPTZ,
    exit_price DECIMAL(20,8),
    exit_time TIMESTAMPTZ,
    position_size DECIMAL(15,2),
    profit_loss DECIMAL(15,2),
    profit_loss_pct DECIMAL(8,4),
    fees DECIMAL(10,2)
);

CREATE TABLE evolution_history (
    generation INTEGER PRIMARY KEY,
    timestamp TIMESTAMPTZ,
    patterns_before INTEGER,
    patterns_after INTEGER,
    avg_fitness_before DECIMAL(8,4),
    avg_fitness_after DECIMAL(8,4),
    top_performer_hash VARCHAR(64)
);

CREATE INDEX idx_patterns_active ON discovered_patterns(is_active);
CREATE INDEX idx_patterns_generation ON discovered_patterns(generation);
CREATE INDEX idx_trades_pattern ON trades(pattern_hash);
CREATE INDEX idx_trades_time ON trades(entry_time);
