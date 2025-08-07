# copilot-instructions.md

```markdown
# Copilot Instructions: Build V26MEME Autonomous Trading Intelligence

Do not create new files outside what is in README.md UNLESS IT IS APPROVED BY THE USER. ALWAYS follow the strict build order and do not deviate from it.

## 🎯 YOUR MISSION
Build a fully autonomous trading AI that discovers its own strategies and grows $200 to $1,000,000 in 90 days without ANY human intervention after deployment.

## ⚠️ CRITICAL CONTEXT
- This system starts with ZERO trading knowledge
- It must discover ALL strategies through random hypothesis testing
- It runs 2,000+ strategies simultaneously by day 90
- OpenAI enhances discovered patterns but doesn't create base strategies
- The discovery engine is THE MOST IMPORTANT component

## 🏗️ BUILD ORDER (STRICT - DO NOT DEVIATE)

### PHASE 1: Discovery Engine (Rust) - BUILD THIS FIRST!
Location: `core/discovery_engine.rs`

```rust
use std::collections::HashMap;
use rand::Rng;
use serde::{Serialize, Deserialize};
use sha2::{Sha256, Digest};
use chrono::Utc;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Hypothesis {
    hash: String,
    entry_conditions: Vec<Condition>,
    exit_conditions: Vec<Condition>,
    timeframe: u32,  // minutes
    created_at: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Condition {
    metric: String,      // random metric like "price_delta_5m"
    operator: String,    // >, <, ==, crosses
    value: f64,         // threshold
    weight: f64,        // importance 0.0-1.0
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Pattern {
    hash: String,
    hypothesis: Hypothesis,
    test_count: u32,
    win_count: u32,
    total_profit: f64,
    win_rate: f64,
    sharpe_ratio: f64,
    is_active: bool,
    generation: u32,
    parent_patterns: Vec<String>,
}

struct DiscoveryEngine {
    hypotheses_per_hour: u32,  // Target: 50-100
    test_capital: f64,         // $5 per test
    min_tests_required: u32,   // 100 before validation
    min_win_rate: f64,         // 0.55 to activate
    active_patterns: HashMap<String, Pattern>,
    pattern_queue: Vec<Pattern>,
}

impl DiscoveryEngine {
    pub fn new() -> Self {
        DiscoveryEngine {
            hypotheses_per_hour: 50,
            test_capital: 5.0,
            min_tests_required: 100,
            min_win_rate: 0.55,
            active_patterns: HashMap::new(),
            pattern_queue: Vec::new(),
        }
    }
    
    /// Generate completely random hypothesis with NO human logic
    pub fn generate_hypothesis(&self) -> Hypothesis {
        let mut rng = rand::thread_rng();
        
        // Create random hash
        let mut hasher = Sha256::new();
        hasher.update(format!("{}{}", Utc::now().timestamp_nanos(), rng.gen::<u64>()));
        let hash = format!("{:x}", hasher.finalize());
        
        // Generate 1-5 random entry conditions
        let entry_count = rng.gen_range(1..=5);
        let mut entry_conditions = Vec::new();
        
        for _ in 0..entry_count {
            entry_conditions.push(self.generate_random_condition());
        }
        
        // Generate 1-3 random exit conditions
        let exit_count = rng.gen_range(1..=3);
        let mut exit_conditions = Vec::new();
        
        for _ in 0..exit_count {
            exit_conditions.push(self.generate_random_condition());
        }
        
        Hypothesis {
            hash: hash[..16].to_string(),
            entry_conditions,
            exit_conditions,
            timeframe: rng.gen_range(1..1440), // 1 min to 24 hours
            created_at: Utc::now().timestamp(),
        }
    }
    
    fn generate_random_condition(&self) -> Condition {
        let mut rng = rand::thread_rng();
        
        // Random metrics that could correlate with price movement
        let metrics = vec![
            "price_delta_1m", "price_delta_5m", "price_delta_15m",
            "volume_ratio_1m", "volume_ratio_5m", "volume_spike",
            "order_book_imbalance", "bid_ask_spread",
            "trade_count_1m", "buy_sell_ratio",
            "price_acceleration", "volume_acceleration",
            format!("pattern_{:x}", rng.gen::<u32>()), // Random pattern reference
            format!("metric_{:x}", rng.gen::<u32>()),  // Completely random metric
        ];
        
        let operators = vec![">", "<", "==", "crosses_above", "crosses_below"];
        
        Condition {
            metric: metrics[rng.gen_range(0..metrics.len())].clone(),
            operator: operators[rng.gen_range(0..operators.len())].to_string(),
            value: rng.gen_range(-100.0..100.0),
            weight: rng.gen_range(0.1..1.0),
        }
    }
    
    /// Test hypothesis with real money
    pub async fn test_hypothesis(&mut self, h: &Hypothesis) -> TestResult {
        // This connects to actual exchange and places $5 order
        // NO PAPER TRADING - real money only for valid results
        
        println!("Testing hypothesis: {}", h.hash);
        
        // Execute trade
        let result = self.execute_test_trade(h, self.test_capital).await;
        
        // Store result for pattern validation
        self.store_test_result(&h.hash, &result);
        
        result
    }
    
    /// Promote successful patterns to active trading
    pub fn validate_pattern(&mut self, h: &Hypothesis, results: Vec<TestResult>) {
        if results.len() >= self.min_tests_required as usize {
            let wins = results.iter().filter(|r| r.profitable).count();
            let win_rate = wins as f64 / results.len() as f64;
            
            if win_rate >= self.min_win_rate {
                let sharpe = self.calculate_sharpe_ratio(&results);
                
                let pattern = Pattern {
                    hash: h.hash.clone(),
                    hypothesis: h.clone(),
                    test_count: results.len() as u32,
                    win_count: wins as u32,
                    total_profit: results.iter().map(|r| r.profit).sum(),
                    win_rate,
                    sharpe_ratio: sharpe,
                    is_active: true,
                    generation: 0,
                    parent_patterns: vec![],
                };
                
                self.active_patterns.insert(pattern.hash.clone(), pattern.clone());
                self.pattern_queue.push(pattern.clone());
                
                println!("🎯 NEW PATTERN DISCOVERED: {} - Win Rate: {:.2}%", 
                         pattern.hash, win_rate * 100.0);
            }
        }
    }
    
    /// Main discovery loop - runs 24/7
    pub async fn run_discovery_loop(&mut self) {
        loop {
            // Generate new hypothesis
            let hypothesis = self.generate_hypothesis();
            
            // Test with real money
            let result = self.test_hypothesis(&hypothesis).await;
            
            // Check if ready for validation
            if let Some(results) = self.get_test_results(&hypothesis.hash) {
                if results.len() >= self.min_tests_required as usize {
                    self.validate_pattern(&hypothesis, results);
                }
            }
            
            // Control rate
            tokio::time::sleep(tokio::time::Duration::from_secs(
                3600 / self.hypotheses_per_hour as u64
            )).await;
        }
    }
}

struct TestResult {
    profitable: bool,
    profit: f64,
    entry_price: f64,
    exit_price: f64,
    duration_seconds: u64,
}
```

### PHASE 2: OpenAI Intelligence Layer (Python)
Location: `intelligence/openai_strategist.py`

```python
import os
import json
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta
from openai import AsyncOpenAI
import hashlib

class OpenAIStrategist:
    """
    Enhances discovered patterns using GPT-4
    Budget: $1.00/day maximum
    
    CRITICAL: This does NOT create strategies from scratch
    It only evolves patterns the discovery engine finds
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4-turbo-preview"
        self.daily_budget = 1.00
        self.usage_today = 0.0
        self.usage_reset = datetime.now()
        
    async def evolve_pattern(self, pattern: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Takes a discovered pattern and creates sophisticated variations
        Only called for patterns with >65% win rate
        
        Cost: ~$0.03 per evolution
        Frequency: 10-20 times per day
        """
        
        if not self.within_budget(0.03):
            return []
        
        prompt = f"""
        A pattern was discovered through random testing with these results:
        
        Pattern Hash: {pattern['hash']}
        Entry Conditions: {json.dumps(pattern['entry_conditions'], indent=2)}
        Exit Conditions: {json.dumps(pattern['exit_conditions'], indent=2)}
        Win Rate: {pattern['win_rate']}%
        Sharpe Ratio: {pattern['sharpe_ratio']}
        Total Tests: {pattern['test_count']}
        
        This pattern was discovered without any human strategy input.
        
        Create 5 sophisticated variations that might improve performance:
        1. Optimize the timeframes while preserving the core pattern
        2. Add filters to avoid false signals
        3. Create an inverse pattern for the opposite market condition
        4. Combine with correlated market indicators
        5. Add dynamic position sizing based on confidence
        
        Return Python code for each variation.
        Maintain the discovered pattern's core logic - don't replace with traditional strategies.
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are enhancing discovered trading patterns. Never suggest traditional strategies like RSI or MACD. Work only with the pattern provided."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        self.usage_today += 0.03
        
        # Parse response into executable strategies
        variations = self.parse_strategy_code(response.choices[0].message.content)
        
        # Add metadata to track AI enhancement
        for v in variations:
            v['parent_hash'] = pattern['hash']
            v['generation'] = pattern.get('generation', 0) + 1
            v['ai_enhanced'] = True
            v['hash'] = hashlib.sha256(
                f"{pattern['hash']}_{datetime.now().timestamp()}".encode()
            ).hexdigest()[:16]
        
        return variations
    
    async def analyze_sentiment(self, news_data: List[str]) -> Dict[str, Any]:
        """
        Analyzes aggregated news/social data for market sentiment
        Runs every 30 minutes to stay within budget
        
        Cost: ~$0.01 per analysis
        Frequency: 48 times per day
        Daily cost: ~$0.48
        """
        
        if not self.within_budget(0.01):
            return {"sentiment": 0, "signals": []}
        
        prompt = f"""
        Analyze the following crypto market news and social media data:
        
        {' '.join(news_data[:50])}  # Limit to 50 items
        
        Provide a JSON response with:
        {{
            "overall_sentiment": -1.0 to 1.0,
            "fear_greed_index": 0 to 100,
            "potential_pumps": ["coin": "reason"],
            "risk_events": ["event": "impact"],
            "unusual_patterns": ["description"],
            "trade_signals": [
                {{
                    "action": "buy/sell/wait",
                    "confidence": 0.0 to 1.0,
                    "reasoning": "brief explanation"
                }}
            ]
        }}
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        self.usage_today += 0.01
        
        return json.loads(response.choices[0].message.content)
    
    async def synthesize_mega_strategy(self, patterns: List[Dict]) -> str:
        """
        Weekly synthesis combining all successful patterns
        This is where true AI power emerges
        
        Cost: ~$0.50
        Frequency: Weekly
        """
        
        if not self.within_budget(0.50):
            return ""
        
        # Only synthesize the top 50 patterns
        top_patterns = sorted(patterns, key=lambda x: x['sharpe_ratio'], reverse=True)[:50]
        
        prompt = f"""
        Synthesize these {len(top_patterns)} discovered patterns into a master trading system.
        
        Top 5 Patterns:
        {json.dumps(top_patterns[:5], indent=2)}
        
        Requirements:
        1. Manage correlations between patterns
        2. Optimize capital allocation using Kelly Criterion
        3. Detect market regimes and adjust pattern usage
        4. Scale position sizes with capital growth
        5. Include risk management for all patterns
        
        Generate a complete Python implementation that can run all patterns efficiently.
        The system should be able to execute 1000+ patterns simultaneously.
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=4000
        )
        
        self.usage_today += 0.50
        
        return response.choices[0].message.content
    
    async def explain_pattern_success(self, pattern: Dict) -> Dict:
        """
        Understand WHY a pattern works to generate similar ones
        
        Cost: ~$0.02
        Frequency: 20 times per day for top patterns
        """
        
        if not self.within_budget(0.02):
            return {}
        
        prompt = f"""
        This randomly discovered pattern is highly profitable:
        {json.dumps(pattern, indent=2)}
        
        Analyze and explain:
        1. Why this pattern might work (market microstructure theory)
        2. What market conditions it exploits
        3. When it would likely fail
        4. Similar patterns to test
        5. Risk factors to monitor
        
        Return as JSON.
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        self.usage_today += 0.02
        
        return json.loads(response.choices[0].message.content)
    
    def within_budget(self, cost: float) -> bool:
        """Check if we're within daily budget"""
        
        # Reset budget counter daily
        if datetime.now() - self.usage_reset > timedelta(days=1):
            self.usage_today = 0.0
            self.usage_reset = datetime.now()
        
        return (self.usage_today + cost) <= self.daily_budget
    
    def parse_strategy_code(self, code_text: str) -> List[Dict]:
        """Parse AI-generated code into executable strategies"""
        
        strategies = []
        # Extract code blocks and convert to strategy dictionaries
        # Implementation depends on response format
        
        return strategies
```

### PHASE 3: Execution Engine (Go)
Location: `core/execution_engine.go`

```go
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "log"
    "math"
    "sync"
    "sync/atomic"
    "time"
)

type Pattern struct {
    Hash           string          `json:"hash"`
    EntryConditions []Condition    `json:"entry_conditions"`
    ExitConditions  []Condition    `json:"exit_conditions"`
    Timeframe      int             `json:"timeframe"`
    WinRate        float64         `json:"win_rate"`
    SharpeRatio    float64         `json:"sharpe_ratio"`
    IsActive       bool            `json:"is_active"`
    LastTriggered  time.Time       `json:"last_triggered"`
}

type Condition struct {
    Metric   string  `json:"metric"`
    Operator string  `json:"operator"`
    Value    float64 `json:"value"`
    Weight   float64 `json:"weight"`
}

type ExecutionEngine struct {
    // Baseline profit engines
    mevBot          *MEVBot
    arbitrageBot    *ArbitrageBot
    tokenSniper     *TokenSniper
    marketMaker     *MarketMaker
    
    // Discovered patterns - can grow to thousands
    activePatterns  map[string]*Pattern
    patternMutex    sync.RWMutex
    
    // Infrastructure
    orderRouter     *OrderRouter
    riskManager     *RiskManager
    capitalAllocator *CapitalAllocator
    
    // Performance tracking
    totalTrades     int64
    profitableCount int64
    totalProfit     float64
}

func NewExecutionEngine() *ExecutionEngine {
    return &ExecutionEngine{
        activePatterns: make(map[string]*Pattern),
        mevBot:         NewMEVBot(),
        arbitrageBot:   NewArbitrageBot(),
        tokenSniper:    NewTokenSniper(),
        marketMaker:    NewMarketMaker(),
        orderRouter:    NewOrderRouter(),
        riskManager:    NewRiskManager(200.0), // Starting capital
        capitalAllocator: NewCapitalAllocator(),
    }
}

func (e *ExecutionEngine) Run(ctx context.Context) {
    log.Println("🚀 Starting Execution Engine")
    
    var wg sync.WaitGroup
    
    // Run baseline strategies (always profitable)
    wg.Add(4)
    go e.runMEV(ctx, &wg)
    go e.runArbitrage(ctx, &wg)
    go e.runTokenSniping(ctx, &wg)
    go e.runMarketMaking(ctx, &wg)
    
    // Run all discovered patterns in parallel
    go e.runDiscoveredPatterns(ctx)
    
    // Monitor and report
    go e.performanceMonitor(ctx)
    
    wg.Wait()
}

func (e *ExecutionEngine) runDiscoveredPatterns(ctx context.Context) {
    ticker := time.NewTicker(100 * time.Millisecond) // Check every 100ms
    defer ticker.Stop()
    
    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            e.patternMutex.RLock()
            patterns := make([]*Pattern, 0, len(e.activePatterns))
            for _, p := range e.activePatterns {
                patterns = append(patterns, p)
            }
            e.patternMutex.RUnlock()
            
            // Execute all patterns that trigger
            var wg sync.WaitGroup
            for _, pattern := range patterns {
                if e.shouldTriggerPattern(pattern) {
                    wg.Add(1)
                    go e.executePattern(ctx, pattern, &wg)
                }
            }
            wg.Wait()
        }
    }
}

func (e *ExecutionEngine) shouldTriggerPattern(p *Pattern) bool {
    // Check if pattern conditions are met
    // This evaluates the random conditions discovered by the system
    
    for _, condition := range p.EntryConditions {
        if !e.evaluateCondition(condition) {
            return false
        }
    }
    
    // Rate limit to prevent over-trading
    if time.Since(p.LastTriggered) < time.Duration(p.Timeframe) * time.Minute {
        return false
    }
    
    return true
}

func (e *ExecutionEngine) executePattern(ctx context.Context, p *Pattern, wg *sync.WaitGroup) {
    defer wg.Done()
    
    // Calculate position size using Kelly Criterion
    capital := e.capitalAllocator.GetAvailableCapital()
    positionSize := e.riskManager.CalculatePositionSize(p, capital)
    
    // Risk check
    if !e.riskManager.ApproveOrder(p.Hash, positionSize) {
        return
    }
    
    // Execute with <100ms latency
    startTime := time.Now()
    
    order := &Order{
        PatternHash: p.Hash,
        Side:        "buy", // Determined by pattern
        Size:        positionSize,
        Timestamp:   time.Now(),
    }
    
    result := e.orderRouter.Execute(order)
    
    executionTime := time.Since(startTime)
    if executionTime > 100*time.Millisecond {
        log.Printf("⚠️ Slow execution: %v", executionTime)
    }
    
    // Track performance
    if result.Profitable {
        atomic.AddInt64(&e.profitableCount, 1)
    }
    atomic.AddInt64(&e.totalTrades, 1)
    
    // Update pattern statistics
    p.LastTriggered = time.Now()
}

// MEV Bot Implementation
type MEVBot struct {
    flashbotsClient *FlashbotsClient
    mempoolMonitor  *MempoolMonitor
    dailyProfit     float64
    mu              sync.Mutex
}

func NewMEVBot() *MEVBot {
    return &MEVBot{
        flashbotsClient: NewFlashbotsClient(),
        mempoolMonitor:  NewMempoolMonitor(),
    }
}

func (m *MEVBot) Run(ctx context.Context, wg *sync.WaitGroup) {
    defer wg.Done()
    
    log.Println("🤖 MEV Bot started - Target: $500-2000 daily")
    
    for {
        select {
        case <-ctx.Done():
            return
        default:
            // Monitor mempool for sandwich opportunities
            if opp := m.findSandwichOpportunity(); opp != nil {
                profit := m.executeSandwich(opp)
                m.mu.Lock()
                m.dailyProfit += profit
                m.mu.Unlock()
                
                if profit > 0 {
                    log.Printf("💰 MEV Profit: $%.2f (Daily Total: $%.2f)", 
                        profit, m.dailyProfit)
                }
            }
            
            // Check for arbitrage via flash loans
            if arb := m.findFlashLoanArbitrage(); arb != nil {
                profit := m.executeFlashLoan(arb)
                m.mu.Lock()
                m.dailyProfit += profit
                m.mu.Unlock()
            }
            
            time.Sleep(10 * time.Millisecond) // Ultra-fast checking
        }
    }
}

// Arbitrage Bot
type ArbitrageBot struct {
    exchanges       []Exchange
    minProfitPct    float64
    opportunities   chan *ArbitrageOpp
}

func NewArbitrageBot() *ArbitrageBot {
    return &ArbitrageBot{
        exchanges:    InitializeExchanges(),
        minProfitPct: 0.005, // 0.5% minimum
        opportunities: make(chan *ArbitrageOpp, 100),
    }
}

func (a *ArbitrageBot) Run(ctx context.Context, wg *sync.WaitGroup) {
    defer wg.Done()
    
    log.Println("💱 Arbitrage Bot started - Target: 0.5-2% per opportunity")
    
    // Start price monitoring on all exchanges
    go a.monitorPrices(ctx)
    
    // Execute opportunities
    for {
        select {
        case <-ctx.Done():
            return
        case opp := <-a.opportunities:
            if opp.ProfitPct > a.minProfitPct {
                go a.executeArbitrage(opp)
            }
        }
    }
}

// Token Sniper
type TokenSniper struct {
    dexMonitor     *DEXMonitor
    sniperWallet   *Wallet
    minLiquidity   float64
    maxBuyAmount   float64
}

func NewTokenSniper() *TokenSniper {
    return &TokenSniper{
        dexMonitor:   NewDEXMonitor(),
        sniperWallet: NewWallet(),
        minLiquidity: 10000.0,  // $10k minimum liquidity
        maxBuyAmount: 50.0,      // $50 max per snipe
    }
}

func (t *TokenSniper) Run(ctx context.Context, wg *sync.WaitGroup) {
    defer wg.Done()
    
    log.Println("🎯 Token Sniper started - Target: 10-100x on launches")
    
    for {
        select {
        case <-ctx.Done():
            return
        default:
            // Monitor for new token launches
            if launch := t.dexMonitor.DetectNewToken(); launch != nil {
                if t.isViableToken(launch) {
                    profit := t.snipeToken(launch)
                    if profit > 0 {
                        log.Printf("🚀 Sniped %s: %.2fx profit!", 
                            launch.Symbol, profit/t.maxBuyAmount)
                    }
                }
            }
            
            time.Sleep(100 * time.Millisecond)
        }
    }
}

func (e *ExecutionEngine) performanceMonitor(ctx context.Context) {
    ticker := time.NewTicker(1 * time.Minute)
    defer ticker.Stop()
    
    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            trades := atomic.LoadInt64(&e.totalTrades)
            profitable := atomic.LoadInt64(&e.profitableCount)
            
            winRate := float64(profitable) / float64(trades) * 100
            
            e.patternMutex.RLock()
            patternCount := len(e.activePatterns)
            e.patternMutex.RUnlock()
            
            log.Printf("📊 Performance - Trades: %d | Win Rate: %.2f%% | Active Patterns: %d",
                trades, winRate, patternCount)
        }
    }
}
```

### PHASE 4: Evolution Engine
Location: `core/evolution_ai.py`

```python
import asyncio
import random
import numpy as np
from typing import List, Dict, Any
from datetime import datetime
import hashlib

class EvolutionEngine:
    """
    Implements genetic algorithm with OpenAI enhancement
    Creates exponential growth in profitable patterns
    """
    
    def __init__(self, openai_strategist, db_connection):
        self.openai = openai_strategist
        self.db = db_connection
        self.generation = 0
        self.mutation_rate = 0.1
        self.crossover_rate = 0.3
        self.selection_pressure = 0.2  # Top 20% reproduce
        
    async def daily_evolution_cycle(self, patterns: List[Dict]) -> List[Dict]:
        """
        Runs every 24 hours at midnight UTC
        Evolves patterns through natural selection + AI enhancement
        """
        
        print(f"🧬 Evolution Generation {self.generation}")
        print(f"   Starting patterns: {len(patterns)}")
        
        # 1. Calculate fitness scores
        patterns = self.calculate_fitness(patterns)
        
        # 2. Natural selection - survival of the fittest
        patterns.sort(key=lambda x: x['fitness'], reverse=True)
        
        # Kill bottom 50%
        survivors = patterns[:int(len(patterns) * 0.5)]
        killed = patterns[int(len(patterns) * 0.5):]
        
        print(f"   ☠️ Killed {len(killed)} underperformers")
        
        # 3. Reproduction - top performers create offspring
        elite = patterns[:int(len(patterns) * self.selection_pressure)]
        offspring = []
        
        for parent in elite:
            # AI-enhanced evolution for top performers
            if parent['win_rate'] > 0.65 and parent['sharpe_ratio'] > 1.5:
                print(f"   🤖 AI evolving pattern {parent['hash'][:8]} (WR: {parent['win_rate']:.2%})")
                ai_variations = await self.openai.evolve_pattern(parent)
                offspring.extend(ai_variations[:3])  # Limit AI variations
            
            # Standard mutations
            for _ in range(3):
                mutant = self.mutate_pattern(parent)
                offspring.append(mutant)
            
            # Crossbreeding with other elites
            if len(elite) > 1:
                partner = random.choice([e for e in elite if e['hash'] != parent['hash']])
                child = self.crossbreed_patterns(parent, partner)
                offspring.append(child)
        
        # 4. Random introduction for diversity
        random_patterns = []
        for _ in range(10):
            random_pattern = self.generate_completely_random_pattern()
            random_patterns.append(random_pattern)
        
        # 5. Combine all patterns for next generation
        next_generation = survivors + offspring + random_patterns
        
        self.generation += 1
        
        print(f"✅ Evolution complete:")
        print(f"   Survivors: {len(survivors)}")
        print(f"   Offspring: {len(offspring)}")
        print(f"   Random: {len(random_patterns)}")
        print(f"   Next generation: {len(next_generation)} patterns")
        
        # Store evolution history
        await self.store_evolution_history(patterns, next_generation)
        
        return next_generation
    
    def calculate_fitness(self, patterns: List[Dict]) -> List[Dict]:
        """
        Fitness = combination of multiple factors
        Designed to favor consistent, profitable patterns
        """
        
        for pattern in patterns:
            # Avoid division by zero
            if pattern.get('test_count', 0) == 0:
                pattern['fitness'] = 0
                continue
            
            # Multi-factor fitness score
            win_rate = pattern.get('win_rate', 0)
            sharpe = max(0, pattern.get('sharpe_ratio', 0))
            profit = pattern.get('total_profit', 0)
            tests = pattern.get('test_count', 1)
            
            # Penalize under-tested patterns
            confidence_factor = min(1.0, tests / 100.0)
            
            # Calculate composite fitness
            pattern['fitness'] = (
                (win_rate ** 2) * 0.3 +           # Favor high win rates
                (sharpe / 3.0) * 0.3 +             # Normalize Sharpe
                (profit / 1000.0) * 0.2 +         # Scale profit
                confidence_factor * 0.2             # Confidence in results
            )
            
            # Bonus for consistent patterns
            if win_rate > 0.6 and sharpe > 1.5:
                pattern['fitness'] *= 1.5
        
        return patterns
    
    def mutate_pattern(self, pattern: Dict) -> Dict:
        """
        Create variations through random mutations
        """
        
        import copy
        mutant = copy.deepcopy(pattern)
        
        # Generate new hash
        mutant['hash'] = hashlib.sha256(
            f"{pattern['hash']}_mut_{random.randint(1000,9999)}_{datetime.now().timestamp()}".encode()
        ).hexdigest()[:16]
        
        mutant['generation'] = pattern.get('generation', 0) + 1
        mutant['parent_patterns'] = [pattern['hash']]
        mutant['mutation_type'] = []
        
        # Mutate timeframe
        if random.random() < self.mutation_rate:
            factor = random.uniform(0.8, 1.2)
            mutant['timeframe'] = int(pattern.get('timeframe', 60) * factor)
            mutant['mutation_type'].append('timeframe')
        
        # Mutate entry conditions
        if random.random() < self.mutation_rate and 'entry_conditions' in mutant:
            action = random.choice(['add', 'remove', 'modify'])
            
            if action == 'add' and len(mutant['entry_conditions']) < 8:
                # Add random condition
                new_condition = self.generate_random_condition()
                mutant['entry_conditions'].append(new_condition)
                mutant['mutation_type'].append('add_entry')
                
            elif action == 'remove' and len(mutant['entry_conditions']) > 1:
                # Remove random condition
                idx = random.randint(0, len(mutant['entry_conditions']) - 1)
                mutant['entry_conditions'].pop(idx)
                mutant['mutation_type'].append('remove_entry')
                
            elif action == 'modify' and mutant['entry_conditions']:
                # Modify random condition
                idx = random.randint(0, len(mutant['entry_conditions']) - 1)
                condition = mutant['entry_conditions'][idx]
                
                # Adjust threshold
                if 'value' in condition:
                    condition['value'] *= random.uniform(0.9, 1.1)
                
                mutant['mutation_type'].append('modify_entry')
        
        # Mutate exit conditions similarly
        if random.random() < self.mutation_rate and 'exit_conditions' in mutant:
            # Similar logic for exit conditions
            pass
        
        # Reset performance stats for new pattern
        mutant['test_count'] = 0
        mutant['win_count'] = 0
        mutant['win_rate'] = 0
        mutant['total_profit'] = 0
        mutant['is_active'] = False  # Needs re-validation
        
        return mutant
    
    def crossbreed_patterns(self, parent1: Dict, parent2: Dict) -> Dict:
        """
        Combine two successful patterns to create offspring
        """
        
        child = {
            'hash': hashlib.sha256(
                f"cross_{parent1['hash'][:8]}_{parent2['hash'][:8]}_{datetime.now().timestamp()}".encode()
            ).hexdigest()[:16],
            'generation': max(parent1.get('generation', 0), parent2.get('generation', 0)) + 1,
            'parent_patterns': [parent1['hash'], parent2['hash']],
            
            # Take entry from better performer, exit from other
            'entry_conditions': parent1['entry_conditions'] if parent1['fitness'] > parent2['fitness'] else parent2['entry_conditions'],
            'exit_conditions': parent2['exit_conditions'] if parent1['fitness'] > parent2['fitness'] else parent1['exit_conditions'],
            
            # Average the parameters
            'timeframe': int((parent1.get('timeframe', 60) + parent2.get('timeframe', 60)) / 2),
            
            # Reset stats
            'test_count': 0,
            'win_count': 0,
            'win_rate': 0,
            'total_profit': 0,
            'is_active': False,
        }
        
        return child
    
    def generate_random_condition(self) -> Dict:
        """Generate a completely random condition"""
        
        metrics = [
            'price_delta_1m', 'price_delta_5m', 'price_delta_15m',
            'volume_ratio', 'volume_spike', 'order_imbalance',
            'bid_ask_spread', 'trade_velocity', 'whale_activity',
            f'random_metric_{random.randint(1000,9999)}'
        ]
        
        return {
            'metric': random.choice(metrics),
            'operator': random.choice(['>', '<', '==', 'crosses']),
            'value': random.uniform(-100, 100),
            'weight': random.uniform(0.1, 1.0)
        }
    
    def generate_completely_random_pattern(self) -> Dict:
        """Create entirely new random pattern for diversity"""
        
        return {
            'hash': hashlib.sha256(
                f"random_{datetime.now().timestamp()}_{random.randint(1000000,9999999)}".encode()
            ).hexdigest()[:16],
            'entry_conditions': [self.generate_random_condition() for _ in range(random.randint(1, 5))],
            'exit_conditions': [self.generate_random_condition() for _ in range(random.randint(1, 3))],
            'timeframe': random.randint(1, 1440),
            'generation': self.generation,
            'parent_patterns': [],
            'test_count': 0,
            'win_count': 0,
            'win_rate': 0,
            'total_profit': 0,
            'is_active': False,
        }
    
    async def store_evolution_history(self, before: List[Dict], after: List[Dict]):
        """Track evolution progress in database"""
        
        query = """
        INSERT INTO evolution_history 
        (generation, timestamp, patterns_before, patterns_after, 
         avg_fitness_before, avg_fitness_after, top_performer_hash)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        
        avg_fitness_before = np.mean([p.get('fitness', 0) for p in before])
        avg_fitness_after = np.mean([p.get('fitness', 0) for p in after])
        top_performer = max(after, key=lambda x: x.get('fitness', 0))
        
        await self.db.execute(
            query,
            self.generation,
            datetime.now(),
            len(before),
            len(after),
            avg_fitness_before,
            avg_fitness_after,
            top_performer['hash']
        )
```

### PHASE 5: Risk Manager
Location: `core/risk_manager.rs`

```rust
use std::sync::atomic::{AtomicBool, AtomicI64, Ordering};
use std::sync::{Arc, Mutex};
use std::collections::HashMap;
use chrono::{DateTime, Utc, Duration};

pub struct RiskManager {
    // Hard limits that cannot be overridden
    max_position_size_pct: f64,     // 0.25 (25% of capital)
    max_daily_drawdown_pct: f64,    // 0.30 (30% stop)
    max_concurrent_positions: u32,   // 10 per strategy type
    min_win_rate: f64,              // 0.55 minimum to trade
    
    // Kelly Criterion parameters
    kelly_fraction: f64,            // 0.25 (conservative)
    
    // Circuit breakers
    emergency_stop: Arc<AtomicBool>,
    circuit_breaker_15min: Arc<AtomicBool>,
    circuit_breaker_1hr: Arc<AtomicBool>,
    
    // Capital tracking
    starting_capital: f64,
    current_capital: Arc<Mutex<f64>>,
    daily_high: Arc<Mutex<f64>>,
    
    // Loss tracking
    losses_15min: Arc<Mutex<Vec<(DateTime<Utc>, f64)>>>,
    losses_1hr: Arc<Mutex<Vec<(DateTime<Utc>, f64)>>>,
    losses_24hr: Arc<Mutex<Vec<(DateTime<Utc>, f64)>>>,
    
    // Position tracking
    open_positions: Arc<Mutex<HashMap<String, Position>>>,
    position_correlations: Arc<Mutex<HashMap<(String, String), f64>>>,
}

#[derive(Clone, Debug)]
pub struct Position {
    pattern_hash: String,
    size: f64,
    entry_price: f64,
    entry_time: DateTime<Utc>,
    stop_loss: f64,
    take_profit: f64,
}

impl RiskManager {
    pub fn new(starting_capital: f64) -> Self {
        RiskManager {
            max_position_size_pct: 0.25,
            max_daily_drawdown_pct: 0.30,
            max_concurrent_positions: 10,
            min_win_rate: 0.55,
            kelly_fraction: 0.25,
            
            emergency_stop: Arc::new(AtomicBool::new(false)),
            circuit_breaker_15min: Arc::new(AtomicBool::new(false)),
            circuit_breaker_1hr: Arc::new(AtomicBool::new(false)),
            
            starting_capital,
            current_capital: Arc::new(Mutex::new(starting_capital)),
            daily_high: Arc::new(Mutex::new(starting_capital)),
            
            losses_15min: Arc::new(Mutex::new(Vec::new())),
            losses_1hr: Arc::new(Mutex::new(Vec::new())),
            losses_24hr: Arc::new(Mutex::new(Vec::new())),
            
            open_positions: Arc::new(Mutex::new(HashMap::new())),
            position_correlations: Arc::new(Mutex::new(HashMap::new())),
        }
    }
    
    pub fn calculate_position_size(&self, pattern: &Pattern, available_capital: f64) -> f64 {
        // Never trade patterns below minimum win rate
        if pattern.win_rate < self.min_win_rate {
            return 0.0;
        }
        
        // Kelly Criterion with safety factor
        let win_prob = pattern.win_rate;
        let loss_prob = 1.0 - win_prob;
        
        // Get average win/loss from pattern history
        let avg_win = pattern.avg_win_amount;
        let avg_loss = pattern.avg_loss_amount.abs();
        
        if avg_loss == 0.0 || avg_win == 0.0 {
            // No position if we can't calculate risk/reward
            return 0.0;
        }
        
        // Kelly formula: f = (p*b - q) / b
        // where p = win probability, q = loss probability, b = win/loss ratio
        let b = avg_win / avg_loss;
        let kelly_pct = (win_prob * b - loss_prob) / b;
        
        // Apply safety factor (quarter Kelly)
        let safe_kelly = kelly_pct * self.kelly_fraction;
        
        // Apply maximum position size limit
        let max_position = available_capital * self.max_position_size_pct;
        let kelly_position = available_capital * safe_kelly.max(0.0);
        
        // Use the smaller of Kelly or max position
        let position_size = kelly_position.min(max_position);
        
        // Minimum position size (don't trade dust)
        if position_size < 5.0 {
            return 0.0;
        }
        
        position_size
    }
    
    pub fn check_risk_limits(&self) -> bool {
        // Check emergency stop
        if self.emergency_stop.load(Ordering::SeqCst) {
            println!("🚨 Emergency stop is active");
            return false;
        }
        
        // Check circuit breakers
        if self.circuit_breaker_15min.load(Ordering::SeqCst) {
            println!("⚠️ 15-minute circuit breaker active");
            return false;
        }
        
        if self.circuit_breaker_1hr.load(Ordering::SeqCst) {
            println!("⚠️ 1-hour circuit breaker active");
            return false;
        }
        
        // Calculate current drawdown
        let current = *self.current_capital.lock().unwrap();
        let daily_high = *self.daily_high.lock().unwrap();
        
        let drawdown = (daily_high - current) / daily_high;
        
        // Check daily drawdown limit
        if drawdown > self.max_daily_drawdown_pct {
            self.trigger_emergency_stop();
            return false;
        }
        
        // Check 15-minute loss rate
        let loss_15min = self.calculate_period_loss(Duration::minutes(15));
        if loss_15min > 0.10 {
            self.trigger_circuit_breaker_15min();
            return false;
        }
        
        // Check 1-hour loss rate
        let loss_1hr = self.calculate_period_loss(Duration::hours(1));
        if loss_1hr > 0.20 {
            self.trigger_circuit_breaker_1hr();
            return false;
        }
        
        true
    }
    
    fn calculate_period_loss(&self, period: Duration) -> f64 {
        let now = Utc::now();
        let cutoff = now - period;
        
        let losses = match period.num_minutes() {
            15 => self.losses_15min.lock().unwrap(),
            60 => self.losses_1hr.lock().unwrap(),
            _ => self.losses_24hr.lock().unwrap(),
        };
        
        let period_losses: f64 = losses
            .iter()
            .filter(|(time, _)| *time > cutoff)
            .map(|(_, loss)| loss)
            .sum();
        
        let current = *self.current_capital.lock().unwrap();
        period_losses / current
    }
    
    fn trigger_emergency_stop(&self) {
        println!("🚨🚨🚨 EMERGENCY STOP TRIGGERED - 30% DAILY LOSS 🚨🚨🚨");
        println!("System will halt all trading and require manual intervention");
        
        self.emergency_stop.store(true, Ordering::SeqCst);
        
        // Close all positions immediately
        self.close_all_positions();
        
        // Save state to database
        self.save_emergency_state();
        
        // Send alerts to all configured channels
        self.send_emergency_alerts();
    }
    
    fn trigger_circuit_breaker_15min(&self) {
        println!("⚠️ 15-minute circuit breaker triggered - 10% loss");
        self.circuit_breaker_15min.store(true, Ordering::SeqCst);
        
        // Schedule re-enable after 1 hour
        std::thread::spawn(move || {
            std::thread::sleep(std::time::Duration::from_secs(3600));
            // Re-enable after cooldown
        });
    }
    
    fn trigger_circuit_breaker_1hr(&self) {
        println!("⚠️ 1-hour circuit breaker triggered - 20% loss");
        self.circuit_breaker_1hr.store(true, Ordering::SeqCst);
        
        // Schedule re-enable after 6 hours
        std::thread::spawn(move || {
            std::thread::sleep(std::time::Duration::from_secs(21600));
            // Re-enable after cooldown
        });
    }
    
    pub fn approve_order(&self, pattern_hash: &str, size: f64) -> bool {
        // Check if emergency stop is active
        if self.emergency_stop.load(Ordering::SeqCst) {
            return false;
        }
        
        // Check circuit breakers
        if !self.check_risk_limits() {
            return false;
        }
        
        // Check concurrent position limits
        let positions = self.open_positions.lock().unwrap();
        let pattern_positions = positions
            .values()
            .filter(|p| p.pattern_hash == pattern_hash)
            .count();
        
        if pattern_positions >= self.max_concurrent_positions as usize {
            println!("Max concurrent positions reached for pattern {}", pattern_hash);
            return false;
        }
        
        // Check portfolio correlation
        if self.calculate_portfolio_correlation(pattern_hash) > 0.7 {
            println!("Position too correlated with existing portfolio");
            return false;
        }
        
        // Check if we have enough capital
        let current = *self.current_capital.lock().unwrap();
        if size > current * 0.5 {
            println!("Position size too large relative to capital");
            return false;
        }
        
        true
    }
    
    fn calculate_portfolio_correlation(&self, new_pattern: &str) -> f64 {
        // Calculate correlation between new pattern and existing positions
        // Simplified - in production would use historical correlation matrix
        
        let positions = self.open_positions.lock().unwrap();
        if positions.is_empty() {
            return 0.0;
        }
        
        // Check if adding this position would over-correlate portfolio
        let correlations = self.position_correlations.lock().unwrap();
        
        let max_correlation = positions
            .keys()
            .filter_map(|existing| {
                correlations.get(&(existing.clone(), new_pattern.to_string()))
                    .or_else(|| correlations.get(&(new_pattern.to_string(), existing.clone())))
            })
            .fold(0.0, |max, &corr| max.max(corr.abs()));
        
        max_correlation
    }
    
    pub fn update_capital(&self, new_capital: f64) {
        let mut current = self.current_capital.lock().unwrap();
        let mut daily_high = self.daily_high.lock().unwrap();
        
        *current = new_capital;
        
        // Update daily high water mark
        if new_capital > *daily_high {
            *daily_high = new_capital;
        }
        
        // Track losses for circuit breakers
        if new_capital < *current {
            let loss = *current - new_capital;
            let now = Utc::now();
            
            self.losses_15min.lock().unwrap().push((now, loss));
            self.losses_1hr.lock().unwrap().push((now, loss));
            self.losses_24hr.lock().unwrap().push((now, loss));
            
            // Clean old entries
            self.clean_old_losses();
        }
    }
    
    fn clean_old_losses(&self) {
        let now = Utc::now();
        
        // Clean 15-minute window
        let mut losses_15 = self.losses_15min.lock().unwrap();
        losses_15.retain(|(time, _)| *time > now - Duration::minutes(15));
        
        // Clean 1-hour window
        let mut losses_1h = self.losses_1hr.lock().unwrap();
        losses_1h.retain(|(time, _)| *time > now - Duration::hours(1));
        
        // Clean 24-hour window
        let mut losses_24h = self.losses_24hr.lock().unwrap();
        losses_24h.retain(|(time, _)| *time > now - Duration::hours(24));
    }
    
    fn close_all_positions(&self) {
        println!("📕 Closing all positions...");
        let positions = self.open_positions.lock().unwrap();
        
        for (hash, position) in positions.iter() {
            println!("Closing position: {} Size: ${:.2}", hash, position.size);
            // Execute market close
            // In production, this would interface with exchange
        }
    }
    
    fn save_emergency_state(&self) {
        // Save current state to database for post-mortem analysis
        println!("💾 Saving emergency state to database...");
    }
    
    fn send_emergency_alerts(&self) {
        // Send alerts via Discord, email, SMS, etc.
        println!("📨 Sending emergency alerts...");
    }
}

// Pattern structure for reference
#[derive(Debug, Clone)]
pub struct Pattern {
    pub hash: String,
    pub win_rate: f64,
    pub avg_win_amount: f64,
    pub avg_loss_amount: f64,
    pub sharpe_ratio: f64,
}
```

## 🔧 CRITICAL IMPLEMENTATION NOTES

### Database Schema
```sql
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
```

### Environment Variables (.env)
```bash
# CRITICAL - Never commit this file
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
COINBASE_API_KEY=xxxxxxxxxxxxx
COINBASE_SECRET=xxxxxxxxxxxxx
KRAKEN_API_KEY=xxxxxxxxxxxxx
KRAKEN_SECRET=xxxxxxxxxxxxx
ALCHEMY_API_KEY=xxxxxxxxxxxxx
FLASHBOTS_SIGNER_KEY=0x...

# DO NOT CHANGE THESE
MAX_POSITION_SIZE_PCT=0.25
MAX_DAILY_DRAWDOWN_PCT=0.30
INITIAL_CAPITAL=200.00
TEST_POSITION_SIZE=5.00
MIN_WIN_RATE=0.55
KELLY_FRACTION=0.25

DATABASE_URL=postgresql://localhost:5432/v26meme
REDIS_URL=redis://localhost:6379
```

## 🚨 BUILD VALIDATION CHECKLIST

Before ANY other code:
- [ ] Discovery engine generates random patterns (NO human strategies)
- [ ] Pattern testing uses REAL money ($5 positions)
- [ ] Hypothesis generation rate >= 50/hour
- [ ] Pattern validation after 100+ tests

After Phase 1:
- [ ] OpenAI integration < $1/day budget
- [ ] AI only enhances discovered patterns
- [ ] Evolution runs daily
- [ ] Natural selection kills bottom 50%

After Phase 2:
- [ ] Execution latency < 100ms
- [ ] Can run 2000+ patterns simultaneously
- [ ] MEV bot operational
- [ ] Arbitrage bot operational

After Phase 3:
- [ ] Risk limits enforced
- [ ] Circuit breakers working
- [ ] Emergency stop tested
- [ ] Kelly Criterion position sizing

Final validation:
- [ ] System runs 7 days paper trading
- [ ] Positive returns demonstrated
- [ ] No human intervention needed
- [ ] Ready for $200 deployment

## 🎯 REMEMBER

1. **Discovery Engine is EVERYTHING** - Build it first and perfectly
2. **NO Human Strategies** - The system discovers everything itself
3. **Real Money Testing** - Paper trading doesn't validate patterns
4. **OpenAI Enhances, Doesn't Create** - AI improves discovered patterns
5. **Speed Matters** - <100ms execution, patterns checked every 100ms
6. **Evolution is Mandatory** - Daily cycles with natural selection
7. **Risk Management is Non-Negotiable** - Hard limits that can't be overridden

The goal: An AI that starts knowing NOTHING and discovers how to turn $200 into $1,000,000 in 90 days through pure autonomous evolution.

BUILD THIS EXACTLY AS SPECIFIED. NO DEVIATIONS.
```