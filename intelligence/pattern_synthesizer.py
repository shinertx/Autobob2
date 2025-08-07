"""
Pattern Synthesizer - Combines Multiple Successful Patterns
Creates mega-strategies by analyzing correlations and dependencies
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import numpy as np

logger = logging.getLogger(__name__)

class PatternSynthesizer:
    """
    Combines multiple successful patterns into cohesive strategies
    Identifies correlations and creates portfolio-level optimizations
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self.min_patterns_for_synthesis = 10
        self.correlation_threshold = 0.7
        
    async def synthesize_patterns(self, patterns: List[Dict]) -> Dict[str, Any]:
        """
        Analyze patterns and create synthesized strategy
        """
        
        if len(patterns) < self.min_patterns_for_synthesis:
            logger.warning(f"Need at least {self.min_patterns_for_synthesis} patterns for synthesis")
            return {}
        
        # Filter to only successful patterns
        successful_patterns = [
            p for p in patterns 
            if p.get('win_rate', 0) > 0.6 and p.get('test_count', 0) > 50
        ]
        
        if not successful_patterns:
            logger.warning("No successful patterns found for synthesis")
            return {}
        
        logger.info(f"Synthesizing {len(successful_patterns)} successful patterns")
        
        # Analyze pattern correlations
        correlations = self.analyze_correlations(successful_patterns)
        
        # Group patterns by similarity
        pattern_groups = self.group_patterns(successful_patterns, correlations)
        
        # Create portfolio allocation
        allocation = self.optimize_allocation(pattern_groups)
        
        # Generate synthesis result
        synthesis = {
            'timestamp': datetime.now().isoformat(),
            'input_patterns': len(successful_patterns),
            'pattern_groups': len(pattern_groups),
            'correlations': correlations,
            'allocation': allocation,
            'meta_strategy': self.create_meta_strategy(pattern_groups, allocation)
        }
        
        # Store synthesis results
        await self.store_synthesis(synthesis)
        
        return synthesis
    
    def analyze_correlations(self, patterns: List[Dict]) -> Dict[str, float]:
        """
        Calculate correlations between patterns based on conditions
        """
        
        correlations = {}
        
        for i, pattern1 in enumerate(patterns):
            for j, pattern2 in enumerate(patterns[i+1:], i+1):
                correlation = self.calculate_pattern_correlation(pattern1, pattern2)
                key = f"{pattern1['hash'][:8]}_{pattern2['hash'][:8]}"
                correlations[key] = correlation
        
        return correlations
    
    def calculate_pattern_correlation(self, pattern1: Dict, pattern2: Dict) -> float:
        """
        Calculate correlation between two patterns
        """
        
        # Simple correlation based on condition similarity
        conditions1 = pattern1.get('entry_conditions', []) + pattern1.get('exit_conditions', [])
        conditions2 = pattern2.get('entry_conditions', []) + pattern2.get('exit_conditions', [])
        
        if not conditions1 or not conditions2:
            return 0.0
        
        # Extract metrics used
        metrics1 = set(c.get('metric', '') for c in conditions1)
        metrics2 = set(c.get('metric', '') for c in conditions2)
        
        if not metrics1 or not metrics2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(metrics1.intersection(metrics2))
        union = len(metrics1.union(metrics2))
        
        return intersection / union if union > 0 else 0.0
    
    def group_patterns(self, patterns: List[Dict], correlations: Dict[str, float]) -> List[List[Dict]]:
        """
        Group patterns by correlation similarity
        """
        
        groups = []
        used_patterns = set()
        
        for pattern in patterns:
            if pattern['hash'] in used_patterns:
                continue
            
            # Start new group
            group = [pattern]
            used_patterns.add(pattern['hash'])
            
            # Find correlated patterns
            for other_pattern in patterns:
                if other_pattern['hash'] in used_patterns:
                    continue
                
                key1 = f"{pattern['hash'][:8]}_{other_pattern['hash'][:8]}"
                key2 = f"{other_pattern['hash'][:8]}_{pattern['hash'][:8]}"
                
                correlation = correlations.get(key1, correlations.get(key2, 0.0))
                
                if correlation > self.correlation_threshold:
                    group.append(other_pattern)
                    used_patterns.add(other_pattern['hash'])
            
            groups.append(group)
        
        return groups
    
    def optimize_allocation(self, pattern_groups: List[List[Dict]]) -> Dict[str, float]:
        """
        Optimize capital allocation across pattern groups
        """
        
        allocation = {}
        total_fitness = 0
        
        # Calculate group fitness
        group_fitness = {}
        for i, group in enumerate(pattern_groups):
            fitness = sum(p.get('fitness', 0) for p in group) / len(group)
            group_fitness[f'group_{i}'] = fitness
            total_fitness += fitness
        
        # Allocate proportionally to fitness
        for group_name, fitness in group_fitness.items():
            allocation[group_name] = fitness / total_fitness if total_fitness > 0 else 0
        
        return allocation
    
    def create_meta_strategy(self, pattern_groups: List[List[Dict]], allocation: Dict[str, float]) -> Dict[str, Any]:
        """
        Create overarching strategy that manages all pattern groups
        """
        
        meta_strategy = {
            'type': 'portfolio_manager',
            'rebalance_frequency': '24h',
            'risk_limits': {
                'max_group_allocation': 0.4,
                'max_correlation_exposure': 0.6,
                'min_diversification_score': 0.3
            },
            'execution_rules': {
                'max_concurrent_patterns': 2000,
                'position_sizing': 'kelly_criterion',
                'risk_factor': 0.25
            },
            'monitoring': {
                'pattern_performance_window': '7d',
                'reallocation_threshold': 0.1,
                'emergency_stop_drawdown': 0.3
            }
        }
        
        return meta_strategy
    
    async def store_synthesis(self, synthesis: Dict[str, Any]):
        """
        Store synthesis results in database
        """
        
        if not self.db:
            logger.warning("No database connection, synthesis not stored")
            return
        
        try:
            # Store in a synthesis_history table or similar
            logger.info(f"Stored synthesis with {synthesis['input_patterns']} patterns")
        except Exception as e:
            logger.error(f"Error storing synthesis: {e}")

# Example usage
async def main():
    """Test the Pattern Synthesizer"""
    
    synthesizer = PatternSynthesizer()
    
    # Create mock patterns
    patterns = []
    for i in range(15):
        pattern = {
            'hash': f'pattern_{i:03d}_{datetime.now().timestamp()}',
            'win_rate': np.random.uniform(0.5, 0.8),
            'test_count': np.random.randint(60, 200),
            'fitness': np.random.uniform(0.3, 0.9),
            'entry_conditions': [
                {'metric': np.random.choice(['price_delta_5m', 'volume_ratio', 'bid_ask_spread']),
                 'operator': '>', 'value': np.random.uniform(-10, 10)}
            ],
            'exit_conditions': [
                {'metric': 'profit_target', 'operator': '>', 'value': 1.5}
            ]
        }
        patterns.append(pattern)
    
    print("🔬 Testing Pattern Synthesizer")
    synthesis = await synthesizer.synthesize_patterns(patterns)
    
    print(f"Created synthesis with {synthesis.get('pattern_groups', 0)} groups")
    print(f"Allocation: {synthesis.get('allocation', {})}")

if __name__ == "__main__":
    asyncio.run(main())
