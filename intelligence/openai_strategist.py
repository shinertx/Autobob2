"""
OpenAI Strategy Enhancement System
Budget: $1.00/day maximum

CRITICAL: This does NOT create strategies from scratch
It only evolves patterns the discovery engine finds
"""

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
        api_key = os.getenv('OPENAI_API_KEY')
        
        # Check if we're using a mock key
        self.is_mock_mode = (
            not api_key or 
            'mock' in api_key.lower() or 
            'test' in api_key.lower()
        )
        
        if self.is_mock_mode:
            print("🧪 OpenAIStrategist: Running in MOCK mode - no real API calls")
            self.client = None
        else:
            print("🔥 OpenAIStrategist: Running in LIVE mode - real OpenAI API calls")
            self.client = AsyncOpenAI(api_key=api_key)
            
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
        
        # Mock mode - return simulated variations
        if self.is_mock_mode:
            print(f"🧪 MOCK: Evolving pattern {pattern.get('hash', 'unknown')[:8]} - Simulated")
            
            # Generate mock variations
            variations = []
            for i in range(3):  # Create 3 mock variations
                variation = {
                    'hash': f"mock_variation_{pattern.get('hash', 'unknown')[:8]}_{i}",
                    'parent_hash': pattern['hash'],
                    'generation': pattern.get('generation', 0) + 1,
                    'ai_enhanced': True,
                    'mock_mode': True,
                    'entry_conditions': pattern.get('entry_conditions', []),
                    'exit_conditions': pattern.get('exit_conditions', []),
                    'timeframe': pattern.get('timeframe', 60) + (i * 5),  # Slightly different timeframes
                }
                variations.append(variation)
            
            return variations
        
        # Real OpenAI mode
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

# Example usage
async def main():
    """Test the OpenAI Strategist"""
    strategist = OpenAIStrategist()
    
    # Test pattern evolution
    test_pattern = {
        "hash": "pattern_test123",
        "win_rate": 67.5,
        "sharpe_ratio": 1.8,
        "test_count": 150,
        "entry_conditions": [{"type": "price_movement", "threshold": 2.5}],
        "exit_conditions": [{"type": "profit_target", "percentage": 1.2}]
    }
    
    variations = await strategist.evolve_pattern(test_pattern)
    print(f"Generated {len(variations)} variations")
    
    # Test sentiment analysis
    news = ["Bitcoin price surges", "Ethereum upgrade delayed", "Regulatory clarity improves"]
    sentiment = await strategist.analyze_sentiment(news)
    print(f"Market sentiment: {sentiment.get('overall_sentiment', 0)}")
    
    print(f"Budget status: {strategist.get_budget_status()}")

if __name__ == "__main__":
    asyncio.run(main())
