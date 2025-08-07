"""
Database setup script for V26MEME Autonomous Trading System
Creates PostgreSQL database with TimescaleDB extensions
"""

import os
import asyncio
import asyncpg
from asyncpg.pool import Pool
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseSetup:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/v26meme')
        self.pool: Pool = None
        
    async def initialize(self):
        """Initialize database connection pool"""
        # Connect to postgres database first to create v26meme
        postgres_url = self.database_url.replace('/v26meme', '/postgres')
        
        try:
            # Create database
            conn = await asyncpg.connect(postgres_url)
            
            # Check if database exists
            exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = 'v26meme')"
            )
            
            if not exists:
                await conn.execute('CREATE DATABASE v26meme')
                logger.info("Created database v26meme")
            
            await conn.close()
            
            # Now connect to v26meme database
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=10,
                max_size=20,
                command_timeout=60
            )
            
            logger.info("Database connection pool established")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def setup_extensions(self):
        """Setup required PostgreSQL extensions"""
        async with self.pool.acquire() as conn:
            # Install extensions
            await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            await conn.execute('CREATE EXTENSION IF NOT EXISTS "timescaledb"')
            logger.info("Extensions installed")
    
    async def run_schema(self):
        """Execute the database schema"""
        schema_path = Path(__file__).parent / 'init.sql'
        
        if not schema_path.exists():
            logger.error(f"Schema file not found: {schema_path}")
            return
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        async with self.pool.acquire() as conn:
            # Split and execute statements
            statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
            
            for statement in statements:
                if statement and not statement.startswith('\\'):
                    try:
                        await conn.execute(statement)
                    except asyncpg.exceptions.DuplicateTableError:
                        logger.info(f"Table already exists, skipping...")
                    except Exception as e:
                        logger.error(f"Error executing statement: {e}")
                        logger.error(f"Statement: {statement[:100]}...")
        
        logger.info("Database schema created successfully")
    
    async def verify_setup(self):
        """Verify database setup is complete"""
        async with self.pool.acquire() as conn:
            # Check tables exist
            tables = await conn.fetch("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """)
            
            table_names = [t['tablename'] for t in tables]
            required_tables = [
                'discovered_patterns', 'test_results', 'trades',
                'evolution_history', 'daily_performance'
            ]
            
            for table in required_tables:
                if table in table_names:
                    logger.info(f"✅ Table {table} exists")
                else:
                    logger.error(f"❌ Table {table} missing")
            
            # Check TimescaleDB hypertables
            hypertables = await conn.fetch("""
                SELECT hypertable_name FROM timescaledb_information.hypertables
            """)
            
            if hypertables:
                logger.info(f"✅ TimescaleDB hypertables configured: {[h['hypertable_name'] for h in hypertables]}")
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def run(self):
        """Main setup process"""
        try:
            await self.initialize()
            await self.setup_extensions()
            await self.run_schema()
            await self.verify_setup()
            logger.info("✅ Database setup complete!")
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise
        finally:
            await self.close()

if __name__ == "__main__":
    setup = DatabaseSetup()
    asyncio.run(setup.run())
