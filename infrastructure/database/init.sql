-- V26MEME Autonomous Trading System Database Schema
-- PostgreSQL + TimescaleDB

CREATE DATABASE v26meme;
\c v26meme;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "timescaledb";

-- Core discovered patterns table
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
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Test results for hypothesis validation
CREATE TABLE test_results (
    id SERIAL PRIMARY KEY,
    pattern_hash VARCHAR(64) REFERENCES discovered_patterns(pattern_hash),
    profitable BOOLEAN NOT NULL,
    profit DECIMAL(15,2) NOT NULL,
    entry_price DECIMAL(20,8) NOT NULL,
    exit_price DECIMAL(20,8) NOT NULL,
    duration_seconds INTEGER NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- All executed trades
CREATE TABLE trades (
    trade_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
    fees DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'open'
);

-- Evolution history
CREATE TABLE evolution_history (
    generation INTEGER PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    patterns_before INTEGER,
    patterns_after INTEGER,
    avg_fitness_before DECIMAL(8,4),
    avg_fitness_after DECIMAL(8,4),
    top_performer_hash VARCHAR(64),
    mutation_count INTEGER DEFAULT 0,
    crossover_count INTEGER DEFAULT 0,
    ai_enhanced_count INTEGER DEFAULT 0
);

-- Daily performance metrics (TimescaleDB hypertable)
CREATE TABLE daily_performance (
    time TIMESTAMPTZ NOT NULL,
    total_capital DECIMAL(15,2),
    daily_pnl DECIMAL(15,2),
    total_trades INTEGER,
    winning_trades INTEGER,
    active_patterns INTEGER,
    discovery_rate INTEGER,
    avg_win_rate DECIMAL(5,4),
    sharpe_ratio DECIMAL(8,4),
    max_drawdown DECIMAL(5,4)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('daily_performance', 'time');
SELECT create_hypertable('trades', 'entry_time');

-- Create indexes for performance
CREATE INDEX idx_patterns_active ON discovered_patterns(is_active);
CREATE INDEX idx_patterns_generation ON discovered_patterns(generation);
CREATE INDEX idx_patterns_win_rate ON discovered_patterns(win_rate DESC);
CREATE INDEX idx_trades_pattern ON trades(pattern_hash);
CREATE INDEX idx_trades_time ON trades(entry_time DESC);
CREATE INDEX idx_test_results_pattern ON test_results(pattern_hash);
