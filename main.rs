use std::sync::Arc;
use tokio::time::{interval, Duration};
use chrono::Utc;
use log::{info, error};
use sqlx::PgPool;

mod core;
use core::{discovery_engine::DiscoveryEngine, risk_manager::RiskManager};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize logging
    env_logger::init();
    
    info!("🚀 V26MEME Autonomous Trading Intelligence Starting");
    info!("   Target: $200 → $1,000,000 in 90 days");
    info!("   Mode: Fully autonomous discovery");
    
    // Load environment
    dotenv::dotenv().ok();
    
    // Initialize database
    let database_url = std::env::var("DATABASE_URL")
        .expect("DATABASE_URL must be set");
    let db_pool = PgPool::connect(&database_url).await?;
    
    // Run database migrations
    sqlx::migrate!("./migrations").run(&db_pool).await?;
    
    // Initialize risk manager with starting capital
    let starting_capital = std::env::var("INITIAL_CAPITAL")
        .unwrap_or_else(|_| "200.0".to_string())
        .parse::<f64>()?;
    
    let risk_manager = Arc::new(RiskManager::new(starting_capital));
    
    info!("💰 Starting capital: ${:.2}", starting_capital);
    
    // PHASE 1: Start Discovery Engine (MOST CRITICAL)
    info!("🔬 Starting Discovery Engine - Phase 1");
    let mut discovery_engine = DiscoveryEngine::new(db_pool.clone());
    let discovery_handle = tokio::spawn(async move {
        discovery_engine.run_discovery_loop().await;
    });
    
    // Wait for discovery engine to generate initial patterns
    tokio::time::sleep(Duration::from_secs(10)).await;
    
    // PHASE 2: Start OpenAI Intelligence Layer
    info!("🧠 Starting OpenAI Intelligence Layer - Phase 2");
    let openai_handle = start_openai_layer(db_pool.clone()).await;
    
    // PHASE 3: Start Execution Engine
    info!("⚡ Starting Execution Engine - Phase 3");
    let execution_handle = start_execution_engine(risk_manager.clone()).await;
    
    // PHASE 4: Start Evolution Engine
    info!("🧬 Starting Evolution Engine - Phase 4");
    let evolution_handle = start_evolution_engine(db_pool.clone()).await;
    
    // Start monitoring and reporting
    let monitor_handle = start_monitoring_system(db_pool.clone(), risk_manager.clone()).await;
    
    info!("✅ All systems operational");
    info!("📊 System will begin autonomous trading...");
    
    // Wait for all components
    tokio::try_join!(
        discovery_handle,
        openai_handle,
        execution_handle,
        evolution_handle,
        monitor_handle
    )?;
    
    Ok(())
}

async fn start_openai_layer(db_pool: PgPool) -> tokio::task::JoinHandle<()> {
    tokio::spawn(async move {
        // Initialize Python OpenAI strategist via subprocess
        let mut interval = interval(Duration::from_secs(1800)); // 30 minutes
        
        loop {
            interval.tick().await;
            
            // Call Python OpenAI strategist
            let result = tokio::process::Command::new("python3")
                .arg("intelligence/openai_strategist.py")
                .arg("--mode")
                .arg("sentiment_analysis")
                .output()
                .await;
            
            match result {
                Ok(output) => {
                    if output.status.success() {
                        info!("🧠 OpenAI sentiment analysis completed");
                    } else {
                        error!("❌ OpenAI analysis failed: {}", 
                            String::from_utf8_lossy(&output.stderr));
                    }
                }
                Err(e) => {
                    error!("❌ Failed to execute OpenAI strategist: {}", e);
                }
            }
        }
    })
}

async fn start_execution_engine(risk_manager: Arc<RiskManager>) -> tokio::task::JoinHandle<()> {
    tokio::spawn(async move {
        // Initialize Go execution engine via subprocess
        let mut child = tokio::process::Command::new("./core/execution_engine")
            .spawn()
            .expect("Failed to start execution engine");
        
        // Monitor the process
        let status = child.wait().await.expect("Failed to wait for execution engine");
        
        if !status.success() {
            error!("❌ Execution engine exited with error: {}", status);
        }
    })
}

async fn start_evolution_engine(db_pool: PgPool) -> tokio::task::JoinHandle<()> {
    tokio::spawn(async move {
        let mut interval = interval(Duration::from_secs(86400)); // 24 hours
        
        loop {
            interval.tick().await;
            
            info!("🧬 Starting daily evolution cycle");
            
            // Run Python evolution engine
            let result = tokio::process::Command::new("python3")
                .arg("core/evolution_ai.py")
                .arg("--mode")
                .arg("daily_evolution")
                .output()
                .await;
            
            match result {
                Ok(output) => {
                    if output.status.success() {
                        info!("✅ Evolution cycle completed");
                        info!("📈 {}", String::from_utf8_lossy(&output.stdout));
                    } else {
                        error!("❌ Evolution failed: {}", 
                            String::from_utf8_lossy(&output.stderr));
                    }
                }
                Err(e) => {
                    error!("❌ Failed to execute evolution engine: {}", e);
                }
            }
        }
    })
}

async fn start_monitoring_system(
    db_pool: PgPool, 
    risk_manager: Arc<RiskManager>
) -> tokio::task::JoinHandle<()> {
    tokio::spawn(async move {
        let mut interval = interval(Duration::from_secs(60)); // 1 minute
        
        loop {
            interval.tick().await;
            
            // Check risk limits
            if !risk_manager.check_risk_limits() {
                error!("🚨 Risk limits violated - system may halt trading");
            }
            
            // Query performance metrics (commented out for initial testing)
            /*
            let result = sqlx::query!(
                "SELECT COUNT(*) as total_patterns, 
                 COUNT(*) FILTER (WHERE is_active = true) as active_patterns,
                 AVG(win_rate) as avg_win_rate
                 FROM discovered_patterns"
            )
            .fetch_one(&db_pool)
            .await;
            
            match result {
                Ok(row) => {
                    info!("📊 System Status:");
                    info!("   Total Patterns: {}", row.total_patterns.unwrap_or(0));
                    info!("   Active Patterns: {}", row.active_patterns.unwrap_or(0));
                    info!("   Avg Win Rate: {:.2}%", 
                        row.avg_win_rate.unwrap_or(0.0) * 100.0);
                }
                Err(e) => {
                    error!("❌ Failed to query performance metrics: {}", e);
                }
            }
            */
            
            // Placeholder system status
            info!("📊 System Status: Discovery engine running, collecting patterns...");
        }
    })
}
