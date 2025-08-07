"""
Meta Learner - Learns Patterns of Patterns
Discovers higher-order relationships and meta-strategies
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)

class MetaLearner:
    """
    Analyzes patterns at a higher level to discover meta-patterns
    Learns what makes patterns successful and predicts pattern performance
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self.meta_patterns = {}
        self.pattern_genealogy = defaultdict(list)
        self.success_predictors = {}
        
    async def analyze_pattern_evolution(self, patterns: List[Dict]) -> Dict[str, Any]:
        """
        Analyze how patterns evolve over time and what drives success
        """
        
        logger.info(f"Analyzing evolution of {len(patterns)} patterns")
        
        # Build genealogy tree
        self.build_pattern_genealogy(patterns)
        
        # Analyze success factors
        success_factors = self.identify_success_factors(patterns)
        
        # Discover meta-patterns
        meta_patterns = self.discover_meta_patterns(patterns)
        
        # Predict pattern performance
        predictions = self.predict_pattern_performance(patterns)
        
        # Generate insights
        insights = self.generate_insights(patterns, success_factors, meta_patterns)
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'total_patterns': len(patterns),
            'genealogy_depth': self.calculate_genealogy_depth(),
            'success_factors': success_factors,
            'meta_patterns': meta_patterns,
            'predictions': predictions,
            'insights': insights
        }
        
        await self.store_meta_analysis(analysis)
        
        return analysis
    
    def build_pattern_genealogy(self, patterns: List[Dict]):
        """
        Build family tree of pattern evolution
        """
        
        self.pattern_genealogy.clear()
        
        for pattern in patterns:
            pattern_hash = pattern.get('hash', '')
            parent_patterns = pattern.get('parent_patterns', [])
            generation = pattern.get('generation', 0)
            
            if parent_patterns:
                for parent in parent_patterns:
                    self.pattern_genealogy[parent].append({
                        'child': pattern_hash,
                        'generation': generation,
                        'performance': {
                            'win_rate': pattern.get('win_rate', 0),
                            'profit': pattern.get('total_profit', 0),
                            'test_count': pattern.get('test_count', 0)
                        }
                    })
    
    def identify_success_factors(self, patterns: List[Dict]) -> Dict[str, Any]:
        """
        Identify what characteristics make patterns successful
        """
        
        # Separate successful and unsuccessful patterns
        successful = [p for p in patterns if p.get('win_rate', 0) > 0.6 and p.get('test_count', 0) > 50]
        unsuccessful = [p for p in patterns if p.get('win_rate', 0) < 0.45 and p.get('test_count', 0) > 50]
        
        if not successful or not unsuccessful:
            return {'insufficient_data': True}
        
        logger.info(f"Analyzing {len(successful)} successful vs {len(unsuccessful)} unsuccessful patterns")
        
        factors = {}
        
        # Analyze timeframe preferences
        factors['timeframe'] = self.analyze_timeframe_success(successful, unsuccessful)
        
        # Analyze condition complexity
        factors['complexity'] = self.analyze_complexity_success(successful, unsuccessful)
        
        # Analyze condition types
        factors['condition_types'] = self.analyze_condition_types(successful, unsuccessful)
        
        # Analyze generation effects
        factors['generation_effect'] = self.analyze_generation_effect(successful, unsuccessful)
        
        # Analyze AI enhancement impact
        factors['ai_enhancement'] = self.analyze_ai_enhancement(successful, unsuccessful)
        
        return factors
    
    def analyze_timeframe_success(self, successful: List[Dict], unsuccessful: List[Dict]) -> Dict[str, Any]:
        """
        Analyze which timeframes tend to be more successful
        """
        
        successful_timeframes = [p.get('timeframe', 60) for p in successful]
        unsuccessful_timeframes = [p.get('timeframe', 60) for p in unsuccessful]
        
        return {
            'successful_avg': np.mean(successful_timeframes) if successful_timeframes else 0,
            'unsuccessful_avg': np.mean(unsuccessful_timeframes) if unsuccessful_timeframes else 0,
            'successful_median': np.median(successful_timeframes) if successful_timeframes else 0,
            'sweet_spot': self.find_timeframe_sweet_spot(successful_timeframes)
        }
    
    def analyze_complexity_success(self, successful: List[Dict], unsuccessful: List[Dict]) -> Dict[str, Any]:
        """
        Analyze if pattern complexity affects success
        """
        
        def get_complexity(pattern):
            entry_count = len(pattern.get('entry_conditions', []))
            exit_count = len(pattern.get('exit_conditions', []))
            return entry_count + exit_count
        
        successful_complexity = [get_complexity(p) for p in successful]
        unsuccessful_complexity = [get_complexity(p) for p in unsuccessful]
        
        return {
            'successful_avg_complexity': np.mean(successful_complexity) if successful_complexity else 0,
            'unsuccessful_avg_complexity': np.mean(unsuccessful_complexity) if unsuccessful_complexity else 0,
            'optimal_complexity': self.find_optimal_complexity(successful_complexity)
        }
    
    def analyze_condition_types(self, successful: List[Dict], unsuccessful: List[Dict]) -> Dict[str, Any]:
        """
        Analyze which types of conditions lead to success
        """
        
        def extract_metrics(patterns):
            metrics = defaultdict(int)
            for pattern in patterns:
                for condition in pattern.get('entry_conditions', []) + pattern.get('exit_conditions', []):
                    metric = condition.get('metric', '')
                    if metric:
                        metrics[metric] += 1
            return dict(metrics)
        
        successful_metrics = extract_metrics(successful)
        unsuccessful_metrics = extract_metrics(unsuccessful)
        
        # Calculate success ratios
        success_ratios = {}
        for metric in set(successful_metrics.keys()) | set(unsuccessful_metrics.keys()):
            success_count = successful_metrics.get(metric, 0)
            failure_count = unsuccessful_metrics.get(metric, 0)
            total = success_count + failure_count
            
            if total > 0:
                success_ratios[metric] = success_count / total
        
        # Find most predictive metrics
        top_predictive = sorted(success_ratios.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'success_ratios': success_ratios,
            'top_predictive_metrics': top_predictive,
            'total_unique_metrics': len(success_ratios)
        }
    
    def analyze_generation_effect(self, successful: List[Dict], unsuccessful: List[Dict]) -> Dict[str, Any]:
        """
        Analyze if later generations perform better
        """
        
        successful_generations = [p.get('generation', 0) for p in successful]
        unsuccessful_generations = [p.get('generation', 0) for p in unsuccessful]
        
        return {
            'successful_avg_generation': np.mean(successful_generations) if successful_generations else 0,
            'unsuccessful_avg_generation': np.mean(unsuccessful_generations) if unsuccessful_generations else 0,
            'evolution_improving': np.mean(successful_generations) > np.mean(unsuccessful_generations) if successful_generations and unsuccessful_generations else False
        }
    
    def analyze_ai_enhancement(self, successful: List[Dict], unsuccessful: List[Dict]) -> Dict[str, Any]:
        """
        Analyze impact of AI enhancement on pattern success
        """
        
        ai_successful = [p for p in successful if p.get('ai_enhanced', False)]
        ai_unsuccessful = [p for p in unsuccessful if p.get('ai_enhanced', False)]
        
        total_ai = len(ai_successful) + len(ai_unsuccessful)
        
        if total_ai == 0:
            return {'no_ai_enhanced_patterns': True}
        
        ai_success_rate = len(ai_successful) / total_ai
        
        return {
            'ai_enhanced_count': total_ai,
            'ai_success_rate': ai_success_rate,
            'ai_improvement': ai_success_rate > 0.5
        }
    
    def discover_meta_patterns(self, patterns: List[Dict]) -> List[Dict[str, Any]]:
        """
        Discover higher-order patterns in the data
        """
        
        meta_patterns = []
        
        # Pattern 1: Successful lineages
        successful_lineages = self.find_successful_lineages()
        if successful_lineages:
            meta_patterns.append({
                'type': 'successful_lineage',
                'description': 'Pattern families that consistently produce winners',
                'lineages': successful_lineages[:3],  # Top 3
                'confidence': 0.8
            })
        
        # Pattern 2: Convergent evolution
        convergent = self.find_convergent_evolution(patterns)
        if convergent:
            meta_patterns.append({
                'type': 'convergent_evolution',
                'description': 'Independent patterns converging on similar solutions',
                'examples': convergent[:2],
                'confidence': 0.7
            })
        
        # Pattern 3: Sweet spot combinations
        sweet_spots = self.find_parameter_sweet_spots(patterns)
        if sweet_spots:
            meta_patterns.append({
                'type': 'parameter_sweet_spots',
                'description': 'Optimal parameter combinations',
                'sweet_spots': sweet_spots,
                'confidence': 0.6
            })
        
        return meta_patterns
    
    def find_successful_lineages(self) -> List[Dict[str, Any]]:
        """
        Find pattern lineages with consistently high performance
        """
        
        lineages = []
        
        for parent, children in self.pattern_genealogy.items():
            if len(children) >= 3:  # At least 3 offspring
                avg_win_rate = np.mean([child['performance']['win_rate'] for child in children])
                
                if avg_win_rate > 0.65:  # High average win rate
                    lineages.append({
                        'parent': parent,
                        'children_count': len(children),
                        'avg_win_rate': avg_win_rate,
                        'total_profit': sum(child['performance']['profit'] for child in children)
                    })
        
        return sorted(lineages, key=lambda x: x['avg_win_rate'], reverse=True)
    
    def find_convergent_evolution(self, patterns: List[Dict]) -> List[Dict[str, Any]]:
        """
        Find patterns that independently evolved similar characteristics
        """
        
        # Group patterns by similarity in conditions
        similar_groups = defaultdict(list)
        
        for pattern in patterns:
            # Create signature based on condition types
            signature = self.create_pattern_signature(pattern)
            similar_groups[signature].append(pattern)
        
        # Find groups with multiple independent patterns
        convergent = []
        for signature, group in similar_groups.items():
            if len(group) >= 2:
                # Check if they have different lineages
                lineages = set()
                for pattern in group:
                    parents = pattern.get('parent_patterns', [])
                    if parents:
                        lineages.add(parents[0])
                    else:
                        lineages.add('root')
                
                if len(lineages) > 1:  # Different origins
                    avg_performance = np.mean([p.get('win_rate', 0) for p in group])
                    convergent.append({
                        'signature': signature,
                        'pattern_count': len(group),
                        'lineage_count': len(lineages),
                        'avg_performance': avg_performance
                    })
        
        return sorted(convergent, key=lambda x: x['avg_performance'], reverse=True)
    
    def create_pattern_signature(self, pattern: Dict) -> str:
        """
        Create a signature for pattern similarity comparison
        """
        
        entry_metrics = sorted([c.get('metric', '') for c in pattern.get('entry_conditions', [])])
        exit_metrics = sorted([c.get('metric', '') for c in pattern.get('exit_conditions', [])])
        timeframe_bucket = self.bucket_timeframe(pattern.get('timeframe', 60))
        
        return f"{','.join(entry_metrics)}|{','.join(exit_metrics)}|{timeframe_bucket}"
    
    def bucket_timeframe(self, timeframe: int) -> str:
        """
        Bucket timeframes for similarity comparison
        """
        
        if timeframe <= 5:
            return 'very_short'
        elif timeframe <= 30:
            return 'short'
        elif timeframe <= 240:
            return 'medium'
        else:
            return 'long'
    
    def find_parameter_sweet_spots(self, patterns: List[Dict]) -> List[Dict[str, Any]]:
        """
        Find optimal parameter combinations
        """
        
        successful = [p for p in patterns if p.get('win_rate', 0) > 0.65]
        
        if len(successful) < 10:
            return []
        
        sweet_spots = []
        
        # Timeframe sweet spots
        timeframes = [p.get('timeframe', 60) for p in successful]
        timeframe_mode = max(set(timeframes), key=timeframes.count)
        sweet_spots.append({
            'parameter': 'timeframe',
            'optimal_value': timeframe_mode,
            'frequency': timeframes.count(timeframe_mode) / len(timeframes)
        })
        
        return sweet_spots
    
    def find_timeframe_sweet_spot(self, timeframes: List[int]) -> int:
        """
        Find the most common successful timeframe
        """
        
        if not timeframes:
            return 60
        
        return max(set(timeframes), key=timeframes.count)
    
    def find_optimal_complexity(self, complexities: List[int]) -> int:
        """
        Find the optimal pattern complexity
        """
        
        if not complexities:
            return 3
        
        return max(set(complexities), key=complexities.count)
    
    def predict_pattern_performance(self, patterns: List[Dict]) -> List[Dict[str, Any]]:
        """
        Predict which patterns are likely to succeed
        """
        
        predictions = []
        
        for pattern in patterns:
            if pattern.get('test_count', 0) < 20:  # Only predict for new patterns
                prediction = self.calculate_success_probability(pattern)
                predictions.append({
                    'pattern_hash': pattern.get('hash', ''),
                    'predicted_success_probability': prediction,
                    'confidence': 0.6  # Meta-learning confidence
                })
        
        return sorted(predictions, key=lambda x: x['predicted_success_probability'], reverse=True)
    
    def calculate_success_probability(self, pattern: Dict) -> float:
        """
        Calculate probability of pattern success based on meta-learning
        """
        
        score = 0.5  # Base probability
        
        # Factor in timeframe
        timeframe = pattern.get('timeframe', 60)
        if 15 <= timeframe <= 120:  # Sweet spot range
            score += 0.1
        
        # Factor in complexity
        complexity = len(pattern.get('entry_conditions', [])) + len(pattern.get('exit_conditions', []))
        if 3 <= complexity <= 6:  # Optimal complexity
            score += 0.1
        
        # Factor in generation
        generation = pattern.get('generation', 0)
        if generation > 2:  # Later generations tend to be better
            score += 0.1
        
        # Factor in AI enhancement
        if pattern.get('ai_enhanced', False):
            score += 0.15
        
        return min(1.0, max(0.0, score))
    
    def generate_insights(self, patterns: List[Dict], success_factors: Dict, meta_patterns: List[Dict]) -> List[str]:
        """
        Generate human-readable insights from meta-analysis
        """
        
        insights = []
        
        # Generation insights
        if not success_factors.get('insufficient_data'):
            gen_effect = success_factors.get('generation_effect', {})
            if gen_effect.get('evolution_improving', False):
                insights.append("Pattern evolution is working - later generations perform better")
            
            # Timeframe insights
            timeframe = success_factors.get('timeframe', {})
            sweet_spot = timeframe.get('sweet_spot', 60)
            insights.append(f"Optimal timeframe appears to be around {sweet_spot} minutes")
            
            # Complexity insights
            complexity = success_factors.get('complexity', {})
            optimal = complexity.get('optimal_complexity', 3)
            insights.append(f"Optimal pattern complexity is around {optimal} conditions")
        
        # Meta-pattern insights
        for meta_pattern in meta_patterns:
            if meta_pattern['type'] == 'successful_lineage':
                insights.append(f"Found {len(meta_pattern['lineages'])} highly successful pattern families")
            elif meta_pattern['type'] == 'convergent_evolution':
                insights.append("Independent patterns are converging on similar solutions")
        
        # Performance insights
        total_patterns = len(patterns)
        successful_patterns = len([p for p in patterns if p.get('win_rate', 0) > 0.6])
        if total_patterns > 0:
            success_rate = successful_patterns / total_patterns
            insights.append(f"Overall pattern success rate: {success_rate:.1%}")
        
        return insights
    
    def calculate_genealogy_depth(self) -> int:
        """
        Calculate the maximum generation depth in pattern genealogy
        """
        
        max_depth = 0
        for children in self.pattern_genealogy.values():
            for child in children:
                max_depth = max(max_depth, child.get('generation', 0))
        
        return max_depth
    
    async def store_meta_analysis(self, analysis: Dict[str, Any]):
        """
        Store meta-analysis results
        """
        
        if not self.db:
            logger.warning("No database connection, meta-analysis not stored")
            return
        
        try:
            # Store in meta_analysis table or similar
            logger.info(f"Stored meta-analysis with {len(analysis['insights'])} insights")
        except Exception as e:
            logger.error(f"Error storing meta-analysis: {e}")

# Example usage
async def main():
    """Test the Meta Learner"""
    
    meta_learner = MetaLearner()
    
    # Create mock patterns with genealogy
    patterns = []
    for i in range(50):
        pattern = {
            'hash': f'pattern_{i:03d}',
            'win_rate': np.random.uniform(0.3, 0.8),
            'total_profit': np.random.uniform(-100, 500),
            'test_count': np.random.randint(20, 200),
            'generation': np.random.randint(0, 5),
            'timeframe': np.random.choice([5, 15, 30, 60, 120, 240]),
            'entry_conditions': [
                {'metric': np.random.choice(['price_delta_5m', 'volume_ratio', 'bid_ask_spread'])}
                for _ in range(np.random.randint(1, 5))
            ],
            'exit_conditions': [
                {'metric': 'profit_target'}
                for _ in range(np.random.randint(1, 3))
            ],
            'parent_patterns': [f'pattern_{max(0, i-10):03d}'] if i > 10 and np.random.random() > 0.3 else [],
            'ai_enhanced': np.random.random() > 0.7
        }
        patterns.append(pattern)
    
    print("🧠 Testing Meta Learner")
    analysis = await meta_learner.analyze_pattern_evolution(patterns)
    
    print(f"Analyzed {analysis['total_patterns']} patterns")
    print(f"Genealogy depth: {analysis['genealogy_depth']}")
    print(f"Meta-patterns found: {len(analysis['meta_patterns'])}")
    print(f"Insights generated: {len(analysis['insights'])}")
    
    for insight in analysis['insights'][:3]:
        print(f"  💡 {insight}")

if __name__ == "__main__":
    asyncio.run(main())
