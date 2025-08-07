"""
V26MEME Autonomous Trading System - Main Orchestrator
Runs autonomously for 90 days without human intervention
"""

import asyncio
import os
import sys
import signal
import logging
from datetime import datetime, time
from typing import Optional
import subprocess
from pathlib import Path

# Add project directories to path
sys.path.append(str(Path(__file__).parent / 'core'))
sys.path.append(str(Path(__file__).parent / 'intelligence'))
sys.path.append(str(Path(__file__).parent / 'strategies'))

from intelligence.openai_strategist import OpenAIStrategist
from core.evolution_ai import EvolutionEngine
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('v26meme.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class V26MEMEOrchestrator:
    """
    Main orchestrator that coordinates all components
    """
    
    def __init__(self):
        self.running = False
        self.paper_trading = os.getenv('ENABLE_PAPER_TRADING', 'false').lower() == 'true'
        self.db_pool = None
        self.openai_strategist = None
        self.evolution_engine = None
        
        # Process handles for Rust and Go components
        self.discovery_process = None
        self.execution_process = None
        self.risk_process = None
        
    async def initialize(self):
        """Initialize all components"""
        logger.info("🚀 Initializing V26MEME Autonomous Trading System")
        
        if self.paper_trading:
            logger.warning("⚠️ PAPER TRADING MODE - No real money will be used")
        else:
            logger.warning("💰 LIVE TRADING MODE - Real money at risk!")
        
        # Initialize database connection
        await self.init_database()
        
        # Initialize Python components
        self.openai_strategist = OpenAIStrategist()
        self.evolution_engine = EvolutionEngine(self.openai_strategist, self.db_pool)
        
        # Start Rust components (Discovery Engine & Risk Manager)
        await self.start_rust_components()
        
        # Start Go component (Execution Engine)
        await self.start_go_components()
        
        logger.info("✅ All components initialized successfully")
        
    async def init_database(self):
        """Initialize database connection pool"""
        try:
            self.db_pool = await asyncpg.create_pool(
                os.getenv('DATABASE_URL', 'postgresql://localhost:5432/v26meme'),
                min_size=10,
                max_size=20
            )
            logger.info("📊 Database connection pool established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    async def start_rust_components(self):
        """Compile and start Rust components"""
        try:
            # Build Rust project
            logger.info("🔨 Building Rust components...")
            result = subprocess.run(
                ["cargo", "build", "--release"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Rust build failed: {result.stderr}")
                raise Exception("Failed to build Rust components")
            
            # Start Discovery Engine
            logger.info("🔍 Starting Discovery Engine...")
            self.discovery_process = subprocess.Popen(
                ["./target/release/discovery_engine"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Start Risk Manager
            logger.info("🛡️ Starting Risk Manager...")
            self.risk_process = subprocess.Popen(
                ["./target/release/risk_manager"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            await asyncio.sleep(2)  # Give processes time to start
            
            if self.discovery_process.poll() is not None:
                raise Exception("Discovery Engine failed to start")
            if self.risk_process.poll() is not None:
                raise Exception("Risk Manager failed to start")
                
            logger.info("✅ Rust components started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Rust components: {e}")
            raise
            
    async def start_go_components(self):
        """Build and start Go components"""
        try:
            # Build Go project
            logger.info("🔨 Building Go components...")
            result = subprocess.run(
                ["go", "build", "-o", "execution_engine", "core/execution_engine.go"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Go build failed: {result.stderr}")
                raise Exception("Failed to build Go components")
            
            # Start Execution Engine
            logger.info("⚡ Starting Execution Engine...")
            self.execution_process = subprocess.Popen(
                ["./execution_engine"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            await asyncio.sleep(1)  # Give process time to start
            
            # Check if process started successfully (should still be running)
            if self.execution_process.poll() is not None:
                # Process exited immediately, which indicates an error
                stdout, stderr = self.execution_process.communicate()
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise Exception(f"Execution Engine failed to start: {error_msg}")
                
            logger.info("✅ Go components started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Go components: {e}")
            raise
            
    async def run_evolution_cycle(self):
        """Run daily evolution cycle at midnight UTC"""
        while self.running:
            try:
                now = datetime.utcnow()
                midnight = datetime.combine(now.date(), time(0, 0))
                
                # Calculate seconds until next midnight
                if now.time() > time(0, 0):
                    # Next midnight is tomorrow
                    midnight = datetime.combine(now.date(), time(0, 0))
                    midnight = midnight.replace(day=midnight.day + 1)
                
                seconds_until_midnight = (midnight - now).total_seconds()
                
                logger.info(f"⏰ Next evolution cycle in {seconds_until_midnight/3600:.1f} hours")
                await asyncio.sleep(seconds_until_midnight)
                
                if not self.running:
                    break
                
                # Run evolution
                logger.info("🧬 Starting daily evolution cycle...")
                
                # Get all patterns from database
                query = "SELECT * FROM discovered_patterns WHERE is_active = true"
                rows = await self.db_pool.fetch(query)
                
                patterns = [dict(row) for row in rows]
                
                # Run evolution
                new_patterns = await self.evolution_engine.daily_evolution_cycle(patterns)
                
                # Update database with new generation
                for pattern in new_patterns:
                    await self.update_pattern_in_db(pattern)
                
                logger.info(f"✅ Evolution cycle complete. New generation: {self.evolution_engine.generation}")
                
            except Exception as e:
                logger.error(f"Evolution cycle failed: {e}")
                await asyncio.sleep(3600)  # Wait an hour before retry
                
    async def update_pattern_in_db(self, pattern):
        """Update pattern in database"""
        query = """
            INSERT INTO discovered_patterns 
            (pattern_hash, entry_conditions, exit_conditions, timeframe_minutes, 
             test_count, win_count, total_profit, win_rate, sharpe_ratio, 
             generation, parent_patterns, ai_enhanced, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            ON CONFLICT (pattern_hash) DO UPDATE SET
                test_count = EXCLUDED.test_count,
                win_count = EXCLUDED.win_count,
                total_profit = EXCLUDED.total_profit,
                win_rate = EXCLUDED.win_rate,
                sharpe_ratio = EXCLUDED.sharpe_ratio,
                is_active = EXCLUDED.is_active
        """
        
        await self.db_pool.execute(
            query,
            pattern['hash'],
            pattern.get('entry_conditions', []),
            pattern.get('exit_conditions', []),
            pattern.get('timeframe', 60),
            pattern.get('test_count', 0),
            pattern.get('win_count', 0),
            pattern.get('total_profit', 0),
            pattern.get('win_rate', 0),
            pattern.get('sharpe_ratio', 0),
            pattern.get('generation', 0),
            pattern.get('parent_patterns', []),
            pattern.get('ai_enhanced', False),
            pattern.get('is_active', False)
        )
        
    async def monitor_health(self):
        """Monitor health of all components"""
        while self.running:
            try:
                # Check Rust processes
                if self.discovery_process and self.discovery_process.poll() is not None:
                    logger.error("❌ Discovery Engine crashed! Restarting...")
                    await self.restart_discovery_engine()
                
                if self.risk_process and self.risk_process.poll() is not None:
                    logger.error("❌ Risk Manager crashed! Restarting...")
                    await self.restart_risk_manager()
                
                # Check Go process
                if self.execution_process and self.execution_process.poll() is not None:
                    logger.error("❌ Execution Engine crashed! Restarting...")
                    await self.restart_execution_engine()
                
                # Check database connection
                try:
                    await self.db_pool.fetchval("SELECT 1")
                except:
                    logger.error("❌ Database connection lost! Reconnecting...")
                    await self.init_database()
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(10)
                
    async def restart_discovery_engine(self):
        """Restart Discovery Engine"""
        try:
            if self.discovery_process:
                self.discovery_process.terminate()
                await asyncio.sleep(1)
                
            self.discovery_process = subprocess.Popen(
                ["./target/release/discovery_engine"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info("✅ Discovery Engine restarted")
        except Exception as e:
            logger.error(f"Failed to restart Discovery Engine: {e}")
            
    async def restart_risk_manager(self):
        """Restart Risk Manager"""
        try:
            if self.risk_process:
                self.risk_process.terminate()
                await asyncio.sleep(1)
                
            self.risk_process = subprocess.Popen(
                ["./target/release/risk_manager"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info("✅ Risk Manager restarted")
        except Exception as e:
            logger.error(f"Failed to restart Risk Manager: {e}")
            
    async def restart_execution_engine(self):
        """Restart Execution Engine"""
        try:
            if self.execution_process:
                self.execution_process.terminate()
                await asyncio.sleep(1)
                
            self.execution_process = subprocess.Popen(
                ["./execution_engine"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info("✅ Execution Engine restarted")
        except Exception as e:
            logger.error(f"Failed to restart Execution Engine: {e}")
            
    async def run(self):
        """Main run loop"""
        self.running = True
        
        try:
            # Initialize all components
            await self.initialize()
            
            # Start background tasks
            tasks = [
                asyncio.create_task(self.run_evolution_cycle()),
                asyncio.create_task(self.monitor_health()),
            ]
            
            logger.info("🎯 V26MEME is now running autonomously!")
            logger.info("💵 Starting capital: $200")
            logger.info("🎯 Target: $1,000,000 in 90 days")
            
            # Run until interrupted
            await asyncio.gather(*tasks)
            
        except KeyboardInterrupt:
            logger.info("⏹️ Shutdown signal received")
            await self.shutdown()
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            await self.shutdown()
            
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down V26MEME...")
        self.running = False
        
        # Terminate subprocess
        if self.discovery_process:
            self.discovery_process.terminate()
        if self.risk_process:
            self.risk_process.terminate()
        if self.execution_process:
            self.execution_process.terminate()
        
        # Close database pool
        if self.db_pool:
            await self.db_pool.close()
        
        logger.info("👋 V26MEME shutdown complete")

async def main():
    """Main entry point"""
    orchestrator = V26MEMEOrchestrator()
    await orchestrator.run()

if __name__ == "__main__":
    asyncio.run(main())
