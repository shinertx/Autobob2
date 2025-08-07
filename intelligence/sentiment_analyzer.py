"""
Sentiment Analyzer - Market Sentiment Analysis for Trading Context
Processes news, social media, and market data to gauge sentiment
"""

import asyncio
import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Analyzes market sentiment from multiple data sources
    Provides context for pattern performance and market conditions
    """
    
    def __init__(self, openai_strategist=None):
        self.openai = openai_strategist
        self.sentiment_cache = {}
        self.cache_duration = timedelta(minutes=30)
        
    async def analyze_market_sentiment(self, 
                                     news_data: List[str] = None,
                                     social_data: List[str] = None,
                                     price_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Comprehensive sentiment analysis from multiple sources
        """
        
        # Check cache first
        cache_key = "market_sentiment"
        if self.is_cached(cache_key):
            logger.info("Using cached sentiment analysis")
            return self.sentiment_cache[cache_key]['data']
        
        logger.info("Performing fresh sentiment analysis")
        
        sentiment = {
            'timestamp': datetime.now().isoformat(),
            'overall_score': 0.0,
            'confidence': 0.0,
            'sources': {},
            'signals': [],
            'risk_factors': []
        }
        
        # Analyze news sentiment
        if news_data:
            news_sentiment = await self.analyze_news_sentiment(news_data)
            sentiment['sources']['news'] = news_sentiment
            sentiment['overall_score'] += news_sentiment.get('score', 0) * 0.4
        
        # Analyze social sentiment
        if social_data:
            social_sentiment = await self.analyze_social_sentiment(social_data)
            sentiment['sources']['social'] = social_sentiment
            sentiment['overall_score'] += social_sentiment.get('score', 0) * 0.3
        
        # Analyze price action sentiment
        if price_data:
            price_sentiment = self.analyze_price_sentiment(price_data)
            sentiment['sources']['price'] = price_sentiment
            sentiment['overall_score'] += price_sentiment.get('score', 0) * 0.3
        
        # Normalize overall score
        sentiment['overall_score'] = max(-1.0, min(1.0, sentiment['overall_score']))
        
        # Calculate confidence based on data availability
        sources_count = len([s for s in sentiment['sources'].values() if s])
        sentiment['confidence'] = min(1.0, sources_count / 3.0)
        
        # Generate trading signals based on sentiment
        sentiment['signals'] = self.generate_sentiment_signals(sentiment)
        
        # Identify risk factors
        sentiment['risk_factors'] = self.identify_risk_factors(sentiment)
        
        # Cache the result
        self.cache_sentiment(cache_key, sentiment)
        
        return sentiment
    
    async def analyze_news_sentiment(self, news_data: List[str]) -> Dict[str, Any]:
        """
        Analyze news headlines and articles for sentiment
        """
        
        if not news_data:
            return {'score': 0.0, 'count': 0}
        
        # Use OpenAI for sophisticated analysis if available
        if self.openai:
            try:
                ai_sentiment = await self.openai.analyze_sentiment(news_data)
                return {
                    'score': ai_sentiment.get('overall_sentiment', 0),
                    'count': len(news_data),
                    'fear_greed': ai_sentiment.get('fear_greed_index', 50),
                    'key_themes': ai_sentiment.get('unusual_patterns', [])
                }
            except Exception as e:
                logger.warning(f"OpenAI sentiment analysis failed: {e}")
        
        # Fallback to simple keyword analysis
        return self.simple_news_sentiment(news_data)
    
    def simple_news_sentiment(self, news_data: List[str]) -> Dict[str, Any]:
        """
        Simple keyword-based sentiment analysis
        """
        
        positive_words = [
            'bull', 'bullish', 'rise', 'surge', 'gain', 'profit', 'moon',
            'breakthrough', 'adoption', 'institutional', 'rally', 'pump'
        ]
        
        negative_words = [
            'bear', 'bearish', 'fall', 'crash', 'loss', 'dump', 'fear',
            'regulation', 'ban', 'hack', 'scam', 'sell-off', 'decline'
        ]
        
        positive_count = 0
        negative_count = 0
        
        for text in news_data:
            text_lower = text.lower()
            positive_count += sum(1 for word in positive_words if word in text_lower)
            negative_count += sum(1 for word in negative_words if word in text_lower)
        
        total_signals = positive_count + negative_count
        if total_signals == 0:
            score = 0.0
        else:
            score = (positive_count - negative_count) / total_signals
        
        return {
            'score': score,
            'count': len(news_data),
            'positive_signals': positive_count,
            'negative_signals': negative_count
        }
    
    async def analyze_social_sentiment(self, social_data: List[str]) -> Dict[str, Any]:
        """
        Analyze social media posts for sentiment
        """
        
        if not social_data:
            return {'score': 0.0, 'count': 0}
        
        # Social media tends to be more extreme than news
        sentiment = self.simple_news_sentiment(social_data)
        
        # Amplify social sentiment (more volatile)
        if sentiment['score'] != 0:
            sentiment['score'] *= 1.5
            sentiment['score'] = max(-1.0, min(1.0, sentiment['score']))
        
        # Add social-specific metrics
        sentiment['emoji_sentiment'] = self.analyze_emoji_sentiment(social_data)
        sentiment['engagement_level'] = self.estimate_engagement(social_data)
        
        return sentiment
    
    def analyze_price_sentiment(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Derive sentiment from price action and volume
        """
        
        if not price_data:
            return {'score': 0.0}
        
        sentiment = {'score': 0.0, 'signals': []}
        
        # Price change sentiment
        price_change = price_data.get('price_change_24h', 0)
        if price_change > 0.05:  # +5%
            sentiment['score'] += 0.5
            sentiment['signals'].append('strong_price_rise')
        elif price_change < -0.05:  # -5%
            sentiment['score'] -= 0.5
            sentiment['signals'].append('strong_price_decline')
        
        # Volume sentiment
        volume_change = price_data.get('volume_change_24h', 0)
        if volume_change > 0.2:  # +20% volume
            sentiment['score'] += 0.2 if price_change > 0 else -0.2
            sentiment['signals'].append('high_volume')
        
        # Volatility sentiment
        volatility = price_data.get('volatility', 0)
        if volatility > 0.1:  # High volatility
            sentiment['score'] *= 1.2  # Amplify sentiment during volatility
            sentiment['signals'].append('high_volatility')
        
        sentiment['score'] = max(-1.0, min(1.0, sentiment['score']))
        return sentiment
    
    def analyze_emoji_sentiment(self, texts: List[str]) -> float:
        """
        Analyze emoji sentiment in social media posts
        """
        
        positive_emojis = ['🚀', '🌙', '💎', '💰', '📈', '🔥', '💪', '🎯']
        negative_emojis = ['📉', '💸', '😢', '😭', '💀', '🔴', '⬇️', '🐻']
        
        positive_count = 0
        negative_count = 0
        
        for text in texts:
            positive_count += sum(text.count(emoji) for emoji in positive_emojis)
            negative_count += sum(text.count(emoji) for emoji in negative_emojis)
        
        total = positive_count + negative_count
        if total == 0:
            return 0.0
        
        return (positive_count - negative_count) / total
    
    def estimate_engagement(self, social_data: List[str]) -> str:
        """
        Estimate engagement level from social data
        """
        
        if len(social_data) > 100:
            return 'high'
        elif len(social_data) > 20:
            return 'medium'
        else:
            return 'low'
    
    def generate_sentiment_signals(self, sentiment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate trading signals based on sentiment analysis
        """
        
        signals = []
        score = sentiment.get('overall_score', 0)
        confidence = sentiment.get('confidence', 0)
        
        if confidence < 0.3:
            return signals  # Not enough data for reliable signals
        
        # Strong positive sentiment
        if score > 0.6:
            signals.append({
                'type': 'bullish_sentiment',
                'strength': score,
                'action': 'consider_long',
                'confidence': confidence
            })
        
        # Strong negative sentiment
        elif score < -0.6:
            signals.append({
                'type': 'bearish_sentiment',
                'strength': abs(score),
                'action': 'consider_short',
                'confidence': confidence
            })
        
        # Neutral but high confidence
        elif -0.2 < score < 0.2 and confidence > 0.7:
            signals.append({
                'type': 'neutral_sentiment',
                'strength': confidence,
                'action': 'range_bound',
                'confidence': confidence
            })
        
        return signals
    
    def identify_risk_factors(self, sentiment: Dict[str, Any]) -> List[str]:
        """
        Identify risk factors from sentiment analysis
        """
        
        risk_factors = []
        
        # Low confidence in sentiment
        if sentiment.get('confidence', 0) < 0.3:
            risk_factors.append('low_data_confidence')
        
        # Extreme sentiment (could indicate reversal)
        score = abs(sentiment.get('overall_score', 0))
        if score > 0.8:
            risk_factors.append('extreme_sentiment')
        
        # Conflicting signals between sources
        sources = sentiment.get('sources', {})
        if len(sources) > 1:
            scores = [s.get('score', 0) for s in sources.values() if isinstance(s, dict)]
            if len(scores) > 1 and max(scores) - min(scores) > 1.0:
                risk_factors.append('conflicting_signals')
        
        return risk_factors
    
    def is_cached(self, key: str) -> bool:
        """
        Check if sentiment analysis is cached and fresh
        """
        
        if key not in self.sentiment_cache:
            return False
        
        cache_time = self.sentiment_cache[key]['timestamp']
        return datetime.now() - cache_time < self.cache_duration
    
    def cache_sentiment(self, key: str, data: Dict[str, Any]):
        """
        Cache sentiment analysis results
        """
        
        self.sentiment_cache[key] = {
            'timestamp': datetime.now(),
            'data': data
        }

# Example usage
async def main():
    """Test the Sentiment Analyzer"""
    
    analyzer = SentimentAnalyzer()
    
    # Mock data
    news = [
        "Bitcoin reaches new all-time high as institutional adoption grows",
        "Crypto market sees massive rally amid positive regulatory news",
        "Major exchange reports security breach, prices decline"
    ]
    
    social = [
        "🚀🚀🚀 To the moon! #Bitcoin #BullRun",
        "HODL strong 💎👐",
        "This crash is making me nervous 😢📉"
    ]
    
    price_data = {
        'price_change_24h': 0.08,  # +8%
        'volume_change_24h': 0.25,  # +25%
        'volatility': 0.12
    }
    
    print("📊 Testing Sentiment Analyzer")
    sentiment = await analyzer.analyze_market_sentiment(
        news_data=news,
        social_data=social,
        price_data=price_data
    )
    
    print(f"Overall sentiment: {sentiment['overall_score']:.2f}")
    print(f"Confidence: {sentiment['confidence']:.2f}")
    print(f"Signals: {len(sentiment['signals'])}")
    print(f"Risk factors: {sentiment['risk_factors']}")

if __name__ == "__main__":
    asyncio.run(main())
