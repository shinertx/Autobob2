-- V26MEME Database Schema
-- PostgreSQL with TimescaleDB for time-series data

-- Create database (run as superuser)
-- CREATE DATABASE v26meme;
-- CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Main pattern discovery table
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
    last_triggered TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Individual trade records
CREATE TABLE trades (
    trade_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    fees DECIMAL(10,2),
    execution_time_ms INTEGER,
    strategy_type VARCHAR(50), -- 'discovered', 'mev', 'arbitrage', 'sniping'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Make trades table a hypertable for time-series optimization
SELECT create_hypertable('trades', 'entry_time');

-- Pattern evolution history
CREATE TABLE evolution_history (
    generation INTEGER PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    patterns_before INTEGER,
    patterns_after INTEGER,
    avg_fitness_before DECIMAL(8,4),
    avg_fitness_after DECIMAL(8,4),
    top_performer_hash VARCHAR(64),
    evolution_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Capital tracking
CREATE TABLE capital_history (
    timestamp TIMESTAMPTZ NOT NULL,
    total_capital DECIMAL(15,2) NOT NULL,
    available_capital DECIMAL(15,2) NOT NULL,
    allocated_capital DECIMAL(15,2) NOT NULL,
    daily_profit DECIMAL(15,2),
    cumulative_profit DECIMAL(15,2),
    drawdown_pct DECIMAL(5,4),
    risk_events TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('capital_history', 'timestamp');

-- Risk management events
CREATE TABLE risk_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL, -- 'circuit_breaker', 'emergency_stop', 'position_limit'
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    description TEXT NOT NULL,
    pattern_hash VARCHAR(64),
    capital_at_event DECIMAL(15,2),
    action_taken TEXT,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- OpenAI usage tracking
CREATE TABLE openai_usage (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_type VARCHAR(50) NOT NULL, -- 'evolve_pattern', 'sentiment_analysis', 'mega_strategy'
    tokens_used INTEGER,
    cost_usd DECIMAL(8,4),
    pattern_hash VARCHAR(64),
    success BOOLEAN,
    response_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Exchange API status
CREATE TABLE api_status (
    timestamp TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('online', 'offline', 'degraded')),
    latency_ms INTEGER,
    error_rate DECIMAL(5,4),
    last_successful_order TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('api_status', 'timestamp');

-- Market data cache
CREATE TABLE market_data (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8),
    bid DECIMAL(20,8),
    ask DECIMAL(20,8),
    exchange VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('market_data', 'timestamp');

-- Indexes for performance
CREATE INDEX idx_patterns_active ON discovered_patterns(is_active) WHERE is_active = true;
CREATE INDEX idx_patterns_generation ON discovered_patterns(generation);
CREATE INDEX idx_patterns_win_rate ON discovered_patterns(win_rate) WHERE win_rate IS NOT NULL;
CREATE INDEX idx_trades_pattern ON trades(pattern_hash);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_profit ON trades(profit_loss) WHERE profit_loss IS NOT NULL;
CREATE INDEX idx_capital_timestamp ON capital_history(timestamp DESC);
CREATE INDEX idx_risk_events_type ON risk_events(event_type);
CREATE INDEX idx_risk_events_severity ON risk_events(severity);

-- Views for common queries
CREATE VIEW active_patterns AS
SELECT 
    pattern_hash,
    win_rate,
    sharpe_ratio,
    test_count,
    total_profit,
    generation,
    ai_enhanced,
    last_triggered
FROM discovered_patterns 
WHERE is_active = true
ORDER BY sharpe_ratio DESC;

CREATE VIEW daily_performance AS
SELECT 
    DATE(entry_time) as trade_date,
    COUNT(*) as total_trades,
    COUNT(*) FILTER (WHERE profit_loss > 0) as winning_trades,
    ROUND(COUNT(*) FILTER (WHERE profit_loss > 0) * 100.0 / COUNT(*), 2) as win_rate_pct,
    SUM(profit_loss) as daily_profit,
    AVG(profit_loss) as avg_profit_per_trade,
    STRING_AGG(DISTINCT strategy_type, ', ') as strategies_used
FROM trades 
WHERE entry_time >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(entry_time)
ORDER BY trade_date DESC;

CREATE VIEW pattern_performance AS
SELECT 
    p.pattern_hash,
    p.generation,
    p.ai_enhanced,
    COUNT(t.trade_id) as executed_trades,
    COUNT(t.trade_id) FILTER (WHERE t.profit_loss > 0) as winning_trades,
    COALESCE(ROUND(COUNT(t.trade_id) FILTER (WHERE t.profit_loss > 0) * 100.0 / NULLIF(COUNT(t.trade_id), 0), 2), 0) as win_rate_pct,
    COALESCE(SUM(t.profit_loss), 0) as total_profit,
    COALESCE(AVG(t.profit_loss), 0) as avg_profit_per_trade,
    p.sharpe_ratio
FROM discovered_patterns p
LEFT JOIN trades t ON p.pattern_hash = t.pattern_hash
WHERE p.is_active = true
GROUP BY p.pattern_hash, p.generation, p.ai_enhanced, p.sharpe_ratio
ORDER BY total_profit DESC;

-- Functions for data cleanup and maintenance
CREATE OR REPLACE FUNCTION cleanup_old_market_data() RETURNS void AS $$
BEGIN
    -- Keep only last 7 days of market data
    DELETE FROM market_data WHERE timestamp < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-market-data', '0 2 * * *', 'SELECT cleanup_old_market_data();');

-- Trigger to update pattern win rates
CREATE OR REPLACE FUNCTION update_pattern_stats() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.exit_time IS NOT NULL AND NEW.profit_loss IS NOT NULL THEN
        UPDATE discovered_patterns 
        SET 
            test_count = (
                SELECT COUNT(*) FROM trades 
                WHERE pattern_hash = NEW.pattern_hash AND exit_time IS NOT NULL
            ),
            win_count = (
                SELECT COUNT(*) FROM trades 
                WHERE pattern_hash = NEW.pattern_hash AND profit_loss > 0
            ),
            total_profit = (
                SELECT COALESCE(SUM(profit_loss), 0) FROM trades 
                WHERE pattern_hash = NEW.pattern_hash
            ),
            updated_at = NOW()
        WHERE pattern_hash = NEW.pattern_hash;
        
        -- Update calculated fields
        UPDATE discovered_patterns 
        SET 
            win_rate = CASE 
                WHEN test_count > 0 THEN win_count::decimal / test_count 
                ELSE 0 
            END
        WHERE pattern_hash = NEW.pattern_hash;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_pattern_stats_trigger
    AFTER INSERT OR UPDATE ON trades
    FOR EACH ROW
    EXECUTE FUNCTION update_pattern_stats();

-- Insert initial data
INSERT INTO evolution_history (generation, timestamp, patterns_before, patterns_after, avg_fitness_before, avg_fitness_after)
VALUES (0, NOW(), 0, 0, 0, 0);

INSERT INTO capital_history (timestamp, total_capital, available_capital, allocated_capital, daily_profit, cumulative_profit, drawdown_pct)
VALUES (NOW(), 200.00, 200.00, 0.00, 0.00, 0.00, 0.00);
