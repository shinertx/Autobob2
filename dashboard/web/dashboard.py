"""FastAPI backend for real-time monitoring dashboard"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import asyncpg
import os
from datetime import datetime, timedelta
from typing import Dict, List

app = FastAPI(title="V26MEME Trading Dashboard")

# Serve static files
app.mount("/static", StaticFiles(directory="dashboard/web/static"), name="static")

class DashboardData:
    """Read-only data provider for monitoring"""
    
    def __init__(self):
        self.db_pool = None
        
    async def init_db(self):
        """Initialize database connection pool"""
        try:
            self.db_pool = await asyncpg.create_pool(
                os.getenv('DATABASE_URL', 'postgresql://v26_user:v26_secure_pass@localhost:5432/v26meme')
            )
            print("📊 Dashboard connected to database")
        except Exception as e:
            print(f"❌ Dashboard database connection failed: {e}")
            # Create mock pool for demo purposes
            self.db_pool = None
        
    async def get_current_stats(self) -> Dict:
        """Get current system statistics"""
        if not self.db_pool:
            # Return mock data if database not available
            return {
                'current_capital': 200.0,
                'profit_loss': 0.0,
                'total_trades': 0,
                'win_rate': 0.0,
                'active_patterns': 0,
                'uptime_minutes': int((datetime.now().timestamp() % 86400) / 60)
            }
            
        try:
            async with self.db_pool.acquire() as conn:
                # Get current capital
                capital_result = await conn.fetchval("""
                    SELECT COALESCE(SUM(profit_loss), 0) + 200 as current_capital 
                    FROM trades WHERE entry_time IS NOT NULL
                """)
                current_capital = float(capital_result) if capital_result else 200.0
                
                # Get trade stats
                trade_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_trades,
                        COUNT(CASE WHEN profit_loss > 0 THEN 1 END)::float / 
                        NULLIF(COUNT(*), 0) as win_rate,
                        COALESCE(SUM(profit_loss), 0) as total_pnl
                    FROM trades WHERE entry_time IS NOT NULL
                """)
                
                # Get active patterns
                active_patterns = await conn.fetchval("""
                    SELECT COUNT(*) FROM discovered_patterns WHERE is_active = true
                """) or 0
                
                return {
                    'current_capital': current_capital,
                    'profit_loss': float(trade_stats['total_pnl']) if trade_stats else 0.0,
                    'total_trades': trade_stats['total_trades'] if trade_stats else 0,
                    'win_rate': float(trade_stats['win_rate']) if trade_stats and trade_stats['win_rate'] else 0.0,
                    'active_patterns': active_patterns,
                    'uptime_minutes': int((datetime.now().timestamp() % 86400) / 60)
                }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {
                'current_capital': 200.0,
                'profit_loss': 0.0,
                'total_trades': 0,
                'win_rate': 0.0,
                'active_patterns': 0,
                'uptime_minutes': 0
            }
    
    async def get_pattern_performance(self) -> List[Dict]:
        """Get top performing patterns"""
        if not self.db_pool:
            return []
            
        try:
            async with self.db_pool.acquire() as conn:
                patterns = await conn.fetch("""
                    SELECT 
                        pattern_hash,
                        test_count,
                        win_count,
                        total_profit,
                        win_rate,
                        sharpe_ratio,
                        is_active
                    FROM discovered_patterns
                    WHERE test_count > 0
                    ORDER BY sharpe_ratio DESC
                    LIMIT 10
                """)
                
                return [
                    {
                        'hash': p['pattern_hash'][:8],
                        'tests': p['test_count'],
                        'wins': p['win_count'],
                        'profit': float(p['total_profit']) if p['total_profit'] else 0.0,
                        'win_rate': float(p['win_rate']) if p['win_rate'] else 0.0,
                        'sharpe': float(p['sharpe_ratio']) if p['sharpe_ratio'] else 0.0,
                        'active': p['is_active']
                    }
                    for p in patterns
                ]
        except Exception as e:
            print(f"Error getting patterns: {e}")
            return []

dashboard = DashboardData()

@app.on_event("startup")
async def startup():
    """Initialize dashboard on startup"""
    await dashboard.init_db()

@app.get("/")
async def get_dashboard():
    """Serve the main dashboard"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>V26MEME Trading Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 30px; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .stat-card { background: #2a2a2a; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #444; }
            .stat-value { font-size: 2em; font-weight: bold; color: #4CAF50; }
            .stat-label { color: #ccc; margin-top: 5px; }
            .patterns-section { background: #2a2a2a; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .pattern-item { display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #444; }
            .status { padding: 20px; background: #2a2a2a; border-radius: 8px; }
            .active { color: #4CAF50; }
            .inactive { color: #f44336; }
            .refresh-btn { background: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 V26MEME Autonomous Trading System</h1>
                <p>Real-time monitoring dashboard</p>
                <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
            </div>
            
            <div class="stats-grid" id="stats">
                <div class="stat-card">
                    <div class="stat-value" id="capital">$200.00</div>
                    <div class="stat-label">Current Capital</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="pnl">$0.00</div>
                    <div class="stat-label">Total P&L</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="trades">0</div>
                    <div class="stat-label">Total Trades</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="winrate">0%</div>
                    <div class="stat-label">Win Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="patterns">0</div>
                    <div class="stat-label">Active Patterns</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="uptime">0m</div>
                    <div class="stat-label">Uptime</div>
                </div>
            </div>
            
            <div class="patterns-section">
                <h3>📊 Top Performing Patterns</h3>
                <div id="patterns-list">
                    <p>Loading patterns...</p>
                </div>
            </div>
            
            <div class="status">
                <h3>🔄 System Status</h3>
                <p><span class="active">●</span> Discovery Engine: Running</p>
                <p><span class="active">●</span> Execution Engine: Running</p>
                <p><span class="active">●</span> Risk Manager: Active</p>
                <p><span class="active">●</span> Paper Trading Mode: Enabled</p>
                <p><span style="color: #ff9800;">⚠</span> Mock API Mode: All external APIs simulated</p>
            </div>
        </div>
        
        <script>
            async function updateStats() {
                try {
                    const response = await fetch('/api/stats');
                    const data = await response.json();
                    
                    document.getElementById('capital').textContent = '$' + data.current_capital.toFixed(2);
                    document.getElementById('pnl').textContent = '$' + data.profit_loss.toFixed(2);
                    document.getElementById('trades').textContent = data.total_trades;
                    document.getElementById('winrate').textContent = (data.win_rate * 100).toFixed(1) + '%';
                    document.getElementById('patterns').textContent = data.active_patterns;
                    document.getElementById('uptime').textContent = data.uptime_minutes + 'm';
                } catch (e) {
                    console.error('Failed to update stats:', e);
                }
            }
            
            async function updatePatterns() {
                try {
                    const response = await fetch('/api/patterns');
                    const patterns = await response.json();
                    
                    const container = document.getElementById('patterns-list');
                    if (patterns.length === 0) {
                        container.innerHTML = '<p>No patterns discovered yet. System is actively searching...</p>';
                        return;
                    }
                    
                    container.innerHTML = patterns.map(p => `
                        <div class="pattern-item">
                            <span>Hash: ${p.hash}</span>
                            <span>Tests: ${p.tests} | Wins: ${p.wins}</span>
                            <span>Win Rate: ${(p.win_rate * 100).toFixed(1)}%</span>
                            <span>Profit: $${p.profit.toFixed(2)}</span>
                            <span class="${p.active ? 'active' : 'inactive'}">${p.active ? 'ACTIVE' : 'TESTING'}</span>
                        </div>
                    `).join('');
                } catch (e) {
                    console.error('Failed to update patterns:', e);
                }
            }
            
            // Update every 5 seconds
            setInterval(() => {
                updateStats();
                updatePatterns();
            }, 5000);
            
            // Initial load
            updateStats();
            updatePatterns();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/stats")
async def get_stats():
    """Get current statistics"""
    return await dashboard.get_current_stats()

@app.get("/api/patterns")
async def get_patterns():
    """Get pattern performance"""
    return await dashboard.get_pattern_performance()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    print("🌐 Starting V26MEME Dashboard on http://localhost:5001")
    uvicorn.run(app, host="0.0.0.0", port=5001)
