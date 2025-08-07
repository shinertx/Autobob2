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

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="dashboard/web/static"), name="static")

class DashboardData:
    """Read-only data provider for monitoring"""
    
    def __init__(self):
        self.db_pool = None
        
    async def init_db(self):
        """Initialize database connection pool"""
        self.db_pool = await asyncpg.create_pool(
            os.getenv('DATABASE_URL', 'postgresql://localhost:5432/v26meme')
        )
        
    async def get_metrics(self) -> Dict:
        """Get current metrics from database"""
        
        # Get current capital
        capital_query = """
            SELECT SUM(profit_loss) + 200 as current_capital 
            FROM trades WHERE status = 'closed'
        """
        current_capital = await self.db_pool.fetchval(capital_query) or 200.0
        
        # Get pattern count
        pattern_query = "SELECT COUNT(*) FROM discovered_patterns WHERE is_active = true"
        active_patterns = await self.db_pool.fetchval(pattern_query) or 0
        
        # Get win rate
        win_query = """
            SELECT 
                COUNT(CASE WHEN profit_loss > 0 THEN 1 END)::float / 
                NULLIF(COUNT(*), 0) as win_rate
            FROM trades WHERE status = 'closed'
        """
        win_rate = await self.db_pool.fetchval(win_query) or 0.0
        
        # Get discovery rate
        discovery_query = """
            SELECT COUNT(*) as new_patterns
            FROM discovered_patterns 
            WHERE discovery_timestamp > NOW() - INTERVAL '1 hour'
        """
        discovery_rate = await self.db_pool.fetchval(discovery_query) or 0
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "current_capital": float(current_capital),
            "pnl": float(current_capital - 200),
            "pnl_percentage": ((current_capital - 200) / 200) * 100,
            "active_patterns": active_patterns,
            "win_rate": float(win_rate) * 100,
            "discovery_rate": discovery_rate,
            "target_capital": 1000000,
            "progress_percentage": (current_capital / 1000000) * 100
        }

dashboard = DashboardData()

@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    await dashboard.init_db()

@app.get("/")
async def get():
    """Serve the dashboard HTML"""
    with open("dashboard/web/static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    
    await websocket.accept()
    
    try:
        while True:
            # Send metrics every second
            metrics = await dashboard.get_metrics()
            await websocket.send_json(metrics)
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")

@app.get("/api/metrics")
async def get_metrics():
    """Get current metrics"""
    return await dashboard.get_metrics()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
            # Get recent risk events
            events = await conn.fetch("""
                SELECT event_type, severity, description, timestamp
                FROM risk_events
                WHERE timestamp > NOW() - INTERVAL '1 hour'
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            
            # Calculate current drawdown
            metrics = await conn.fetchrow("""
                SELECT 
                    total_capital,
                    (SELECT MAX(total_capital) FROM performance_metrics) as all_time_high
                FROM performance_metrics
                ORDER BY metric_date DESC
                LIMIT 1
            """)
            
            current = float(metrics['total_capital']) if metrics else 200.0
            ath = float(metrics['all_time_high']) if metrics else 200.0
            drawdown = ((ath - current) / ath * 100) if ath > 0 else 0
            
            return {
                'drawdown_pct': drawdown,
                'risk_level': 'HIGH' if drawdown > 20 else 'MEDIUM' if drawdown > 10 else 'LOW',
                'recent_events': [
                    {
                        'type': e['event_type'],
                        'severity': e['severity'],
                        'description': e['description'],
                        'time': e['timestamp'].isoformat()
                    }
                    for e in events
                ]
            }
    
    async def get_historical_data(self, days: int = 7) -> List[Dict]:
        """Get historical performance data"""
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT metric_date, total_capital, daily_pnl, total_trades, winning_trades
                FROM performance_metrics
                WHERE metric_date >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY metric_date
            """, days)
            
            return [
                {
                    'date': row['metric_date'].isoformat(),
                    'capital': float(row['total_capital']),
                    'pnl': float(row['daily_pnl']),
                    'trades': row['total_trades'],
                    'wins': row['winning_trades']
                }
                for row in rows
            ]

dashboard = DashboardData()

@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    await dashboard.init_db()

@app.get("/")
async def get():
    """Serve the dashboard HTML"""
    with open("dashboard/web/static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    
    await websocket.accept()
    
    try:
        while True:
            # Send updates every second
            data = {
                'stats': await dashboard.get_current_stats(),
                'patterns': await dashboard.get_pattern_performance(),
                'risk': await dashboard.get_risk_metrics(),
                'history': await dashboard.get_historical_data(1)
            }
            
            await websocket.send_json(data)
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")

@app.get("/api/stats")
async def get_stats():
    """Get current statistics"""
    return await dashboard.get_current_stats()

@app.get("/api/patterns")
async def get_patterns():
    """Get pattern performance"""
    return await dashboard.get_pattern_performance()

@app.get("/api/risk")
async def get_risk():
    """Get risk metrics"""
    return await dashboard.get_risk_metrics()

@app.get("/api/history/{days}")
async def get_history(days: int):
    """Get historical data"""
    return await dashboard.get_historical_data(days)
