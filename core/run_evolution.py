#!/usr/bin/env python3
import asyncio
import argparse
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'intelligence'))

from evolution_ai import EvolutionEngine
from openai_strategist import OpenAIStrategist
import asyncpg
import json

async def run_daily_evolution():
    """Run the daily evolution cycle"""
    
    # Connect to database
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # Initialize components
        openai_strategist = OpenAIStrategist()
        evolution_engine = EvolutionEngine(openai_strategist, conn)
        
        # Get all current patterns
        patterns_data = await conn.fetch("""
            SELECT pattern_hash, entry_conditions, exit_conditions, 
                   timeframe, test_count, win_count, total_profit,
                   win_rate, sharpe_ratio, generation, parent_patterns,
                   ai_enhanced, is_active
            FROM discovered_patterns
        """)
        
        patterns = []
        for p in patterns_data:
            patterns.append({
                'hash': p['pattern_hash'],
                'entry_conditions': p['entry_conditions'],
                'exit_conditions': p['exit_conditions'],
                'timeframe': p['timeframe'],
                'test_count': p['test_count'],
                'win_count': p['win_count'],
                'total_profit': float(p['total_profit']) if p['total_profit'] else 0.0,
                'win_rate': float(p['win_rate']) if p['win_rate'] else 0.0,
                'sharpe_ratio': float(p['sharpe_ratio']) if p['sharpe_ratio'] else 0.0,
                'generation': p['generation'],
                'parent_patterns': p['parent_patterns'] or [],
                'ai_enhanced': p['ai_enhanced'],
                'is_active': p['is_active']
            })
        
        print(f"🧬 Starting evolution with {len(patterns)} patterns")
        
        # Run evolution
        next_generation = await evolution_engine.daily_evolution_cycle(patterns)
        
        # Clear existing patterns and insert new generation
        await conn.execute("DELETE FROM discovered_patterns")
        
        for pattern in next_generation:
            await conn.execute("""
                INSERT INTO discovered_patterns 
                (pattern_hash, entry_conditions, exit_conditions, timeframe,
                 test_count, win_count, total_profit, win_rate, sharpe_ratio,
                 generation, parent_patterns, ai_enhanced, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
            pattern['hash'],
            json.dumps(pattern.get('entry_conditions', [])),
            json.dumps(pattern.get('exit_conditions', [])),
            pattern.get('timeframe', 60),
            pattern.get('test_count', 0),
            pattern.get('win_count', 0),
            pattern.get('total_profit', 0.0),
            pattern.get('win_rate', 0.0),
            pattern.get('sharpe_ratio', 0.0),
            pattern.get('generation', 0),
            pattern.get('parent_patterns', []),
            pattern.get('ai_enhanced', False),
            pattern.get('is_active', False)
            )
        
        print(f"✅ Evolution complete - {len(next_generation)} patterns in next generation")
        
    finally:
        await conn.close()

async def main():
    parser = argparse.ArgumentParser(description='Run Evolution Engine')
    parser.add_argument('--mode', choices=['daily_evolution'], required=True)
    
    args = parser.parse_args()
    
    if args.mode == 'daily_evolution':
        await run_daily_evolution()

if __name__ == "__main__":
    asyncio.run(main())
