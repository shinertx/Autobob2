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
            .fold(0.0_f64, |max, &corr| max.max(corr.abs()));
        
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

#[tokio::main]
async fn main() {
    println!("🛡️ Starting V26MEME Risk Manager");
    
    let risk_manager = RiskManager::new(200.0); // Starting with $200
    
    // Keep the risk manager running and monitoring
    loop {
        if !risk_manager.check_risk_limits() {
            println!("⚠️ Risk limits triggered, waiting...");
        }
        
        tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
    }
}
