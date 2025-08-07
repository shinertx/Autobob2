#!/usr/bin/env python3
import asyncio
import argparse
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openai_strategist import OpenAIStrategist
import asyncpg
import json

async def run_sentiment_analysis():
    """Run sentiment analysis on current market data"""
    
    strategist = OpenAIStrategist()
    
    # Fetch recent news/social data (placeholder)
    news_data = [
        "Bitcoin breaks $45k resistance level",
        "Ethereum upgrade scheduled for next month", 
        "Major exchange announces new trading pairs",
        "Regulatory clarity expected soon",
        "Institutional adoption continues"
    ]
    
    sentiment = await strategist.analyze_sentiment(news_data)
    
    print(json.dumps(sentiment, indent=2))
    return sentiment

async def run_pattern_evolution():
    """Evolve top performing patterns"""
    
    strategist = OpenAIStrategist()
    
    # Connect to database
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # Get top patterns for evolution
        patterns = await conn.fetch("""
            SELECT pattern_hash, entry_conditions, exit_conditions, 
                   win_rate, sharpe_ratio, test_count, generation
            FROM discovered_patterns 
            WHERE is_active = true AND win_rate > 0.65
            ORDER BY sharpe_ratio DESC 
            LIMIT 10
        """)
        
        if not patterns:
            print("No patterns ready for evolution")
            return
        
        evolved_count = 0
        
        for pattern in patterns:
            pattern_dict = {
                'hash': pattern['pattern_hash'],
                'entry_conditions': pattern['entry_conditions'],
                'exit_conditions': pattern['exit_conditions'],
                'win_rate': float(pattern['win_rate']),
                'sharpe_ratio': float(pattern['sharpe_ratio']),
                'test_count': pattern['test_count'],
                'generation': pattern['generation']
            }
            
            variations = await strategist.evolve_pattern(pattern_dict)
            
            # Store evolved patterns
            for variation in variations:
                await conn.execute("""
                    INSERT INTO discovered_patterns 
                    (pattern_hash, entry_conditions, exit_conditions, generation, parent_patterns, ai_enhanced)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                variation['hash'],
                json.dumps(variation.get('entry_conditions', [])),
                json.dumps(variation.get('exit_conditions', [])),
                variation.get('generation', 0),
                [pattern_dict['hash']],
                True
                )
                
                evolved_count += 1
        
        print(f"✅ Evolved {evolved_count} new patterns from {len(patterns)} top performers")
        
    finally:
        await conn.close()

async def run_mega_synthesis():
    """Weekly mega strategy synthesis"""
    
    strategist = OpenAIStrategist()
    
    # Connect to database
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # Get all successful patterns
        patterns = await conn.fetch("""
            SELECT pattern_hash, entry_conditions, exit_conditions, 
                   win_rate, sharpe_ratio, total_profit, test_count
            FROM discovered_patterns 
            WHERE is_active = true AND test_count >= 100
            ORDER BY sharpe_ratio DESC
        """)
        
        pattern_list = []
        for p in patterns:
            pattern_list.append({
                'hash': p['pattern_hash'],
                'entry_conditions': p['entry_conditions'],
                'exit_conditions': p['exit_conditions'],
                'win_rate': float(p['win_rate']),
                'sharpe_ratio': float(p['sharpe_ratio']),
                'total_profit': float(p['total_profit']),
                'test_count': p['test_count']
            })
        
        if len(pattern_list) < 10:
            print("Not enough patterns for mega synthesis")
            return
        
        mega_strategy = await strategist.synthesize_mega_strategy(pattern_list)
        
        # Save mega strategy to file
        with open('mega_strategy.py', 'w') as f:
            f.write(mega_strategy)
        
        print("✅ Mega strategy synthesized and saved")
        
    finally:
        await conn.close()

async def main():
    parser = argparse.ArgumentParser(description='Run OpenAI Strategy Components')
    parser.add_argument('--mode', choices=[
        'sentiment_analysis', 
        'pattern_evolution',
        'mega_synthesis'
    ], required=True)
    
    args = parser.parse_args()
    
    if args.mode == 'sentiment_analysis':
        await run_sentiment_analysis()
    elif args.mode == 'pattern_evolution':
        await run_pattern_evolution()
    elif args.mode == 'mega_synthesis':
        await run_mega_synthesis()

if __name__ == "__main__":
    asyncio.run(main())
