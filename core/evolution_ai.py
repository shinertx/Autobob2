"""
Evolution Engine - Pattern Evolution Through Natural Selection + AI Enhancement
Creates exponential growth in profitable patterns through genetic algorithms
"""

import asyncio
import random
import numpy as np
from typing import List, Dict, Any
from datetime import datetime
import hashlib

class EvolutionEngine:
    """
    Implements genetic algorithm with OpenAI enhancement
    Creates exponential growth in profitable patterns
    """
    
    def __init__(self, openai_strategist, db_connection):
        self.openai = openai_strategist
        self.db = db_connection
        self.generation = 0
        self.mutation_rate = 0.1
        self.crossover_rate = 0.3
        self.selection_pressure = 0.2  # Top 20% reproduce
        
    async def daily_evolution_cycle(self, patterns: List[Dict]) -> List[Dict]:
        """
        Runs every 24 hours at midnight UTC
        Evolves patterns through natural selection + AI enhancement
        """
        
        print(f"🧬 Evolution Generation {self.generation}")
        print(f"   Starting patterns: {len(patterns)}")
        
        # 1. Calculate fitness scores
        patterns = self.calculate_fitness(patterns)
        
        # 2. Natural selection - survival of the fittest
        patterns.sort(key=lambda x: x['fitness'], reverse=True)
        
        # Kill bottom 50%
        survivors = patterns[:int(len(patterns) * 0.5)]
        killed = patterns[int(len(patterns) * 0.5):]
        
        print(f"   ☠️ Killed {len(killed)} underperformers")
        
        # 3. Reproduction - top performers create offspring
        elite = patterns[:int(len(patterns) * self.selection_pressure)]
        offspring = []
        
        for parent in elite:
            # AI-enhanced evolution for top performers
            if parent['win_rate'] > 0.65 and parent['sharpe_ratio'] > 1.5:
                print(f"   🤖 AI evolving pattern {parent['hash'][:8]} (WR: {parent['win_rate']:.2%})")
                ai_variations = await self.openai.evolve_pattern(parent)
                offspring.extend(ai_variations[:3])  # Limit AI variations
            
            # Standard mutations
            for _ in range(3):
                mutant = self.mutate_pattern(parent)
                offspring.append(mutant)
            
            # Crossbreeding with other elites
            if len(elite) > 1:
                partner = random.choice([e for e in elite if e['hash'] != parent['hash']])
                child = self.crossbreed_patterns(parent, partner)
                offspring.append(child)
        
        # 4. Random introduction for diversity
        random_patterns = []
        for _ in range(10):
            random_pattern = self.generate_completely_random_pattern()
            random_patterns.append(random_pattern)
        
        # 5. Combine all patterns for next generation
        next_generation = survivors + offspring + random_patterns
        
        self.generation += 1
        
        print(f"✅ Evolution complete:")
        print(f"   Survivors: {len(survivors)}")
        print(f"   Offspring: {len(offspring)}")
        print(f"   Random: {len(random_patterns)}")
        print(f"   Next generation: {len(next_generation)} patterns")
        
        # Store evolution history
        await self.store_evolution_history(patterns, next_generation)
        
        return next_generation
    
    def calculate_fitness(self, patterns: List[Dict]) -> List[Dict]:
        """
        Fitness = combination of multiple factors
        Designed to favor consistent, profitable patterns
        """
        
        for pattern in patterns:
            # Avoid division by zero
            if pattern.get('test_count', 0) == 0:
                pattern['fitness'] = 0
                continue
            
            # Multi-factor fitness score
            win_rate = pattern.get('win_rate', 0)
            sharpe = max(0, pattern.get('sharpe_ratio', 0))
            profit = pattern.get('total_profit', 0)
            tests = pattern.get('test_count', 1)
            
            # Penalize under-tested patterns
            confidence_factor = min(1.0, tests / 100.0)
            
            # Calculate composite fitness
            pattern['fitness'] = (
                (win_rate ** 2) * 0.3 +           # Favor high win rates
                (sharpe / 3.0) * 0.3 +             # Normalize Sharpe
                (profit / 1000.0) * 0.2 +         # Scale profit
                confidence_factor * 0.2             # Confidence in results
            )
            
            # Bonus for consistent patterns
            if win_rate > 0.6 and sharpe > 1.5:
                pattern['fitness'] *= 1.5
        
        return patterns
    
    def mutate_pattern(self, pattern: Dict) -> Dict:
        """
        Create variations through random mutations
        """
        
        import copy
        mutant = copy.deepcopy(pattern)
        
        # Generate new hash
        mutant['hash'] = hashlib.sha256(
            f"{pattern['hash']}_mut_{random.randint(1000,9999)}_{datetime.now().timestamp()}".encode()
        ).hexdigest()[:16]
        
        mutant['generation'] = pattern.get('generation', 0) + 1
        mutant['parent_patterns'] = [pattern['hash']]
        mutant['mutation_type'] = []
        
        # Mutate timeframe
        if random.random() < self.mutation_rate:
            factor = random.uniform(0.8, 1.2)
            mutant['timeframe'] = int(pattern.get('timeframe', 60) * factor)
            mutant['mutation_type'].append('timeframe')
        
        # Mutate entry conditions
        if random.random() < self.mutation_rate and 'entry_conditions' in mutant:
            action = random.choice(['add', 'remove', 'modify'])
            
            if action == 'add' and len(mutant['entry_conditions']) < 8:
                # Add random condition
                new_condition = self.generate_random_condition()
                mutant['entry_conditions'].append(new_condition)
                mutant['mutation_type'].append('add_entry')
                
            elif action == 'remove' and len(mutant['entry_conditions']) > 1:
                # Remove random condition
                idx = random.randint(0, len(mutant['entry_conditions']) - 1)
                mutant['entry_conditions'].pop(idx)
                mutant['mutation_type'].append('remove_entry')
                
            elif action == 'modify' and mutant['entry_conditions']:
                # Modify random condition
                idx = random.randint(0, len(mutant['entry_conditions']) - 1)
                condition = mutant['entry_conditions'][idx]
                
                # Adjust threshold
                if 'value' in condition:
                    condition['value'] *= random.uniform(0.9, 1.1)
                
                mutant['mutation_type'].append('modify_entry')
        
        # Mutate exit conditions similarly
        if random.random() < self.mutation_rate and 'exit_conditions' in mutant:
            # Similar logic for exit conditions
            pass
        
        # Reset performance stats for new pattern
        mutant['test_count'] = 0
        mutant['win_count'] = 0
        mutant['win_rate'] = 0
        mutant['total_profit'] = 0
        mutant['is_active'] = False  # Needs re-validation
        
        return mutant
    
    def crossbreed_patterns(self, parent1: Dict, parent2: Dict) -> Dict:
        """
        Combine two successful patterns to create offspring
        """
        
        child = {
            'hash': hashlib.sha256(
                f"cross_{parent1['hash'][:8]}_{parent2['hash'][:8]}_{datetime.now().timestamp()}".encode()
            ).hexdigest()[:16],
            'generation': max(parent1.get('generation', 0), parent2.get('generation', 0)) + 1,
            'parent_patterns': [parent1['hash'], parent2['hash']],
            
            # Take entry from better performer, exit from other
            'entry_conditions': parent1['entry_conditions'] if parent1['fitness'] > parent2['fitness'] else parent2['entry_conditions'],
            'exit_conditions': parent2['exit_conditions'] if parent1['fitness'] > parent2['fitness'] else parent1['exit_conditions'],
            
            # Average the parameters
            'timeframe': int((parent1.get('timeframe', 60) + parent2.get('timeframe', 60)) / 2),
            
            # Reset stats
            'test_count': 0,
            'win_count': 0,
            'win_rate': 0,
            'total_profit': 0,
            'is_active': False,
        }
        
        return child
    
    def generate_random_condition(self) -> Dict:
        """Generate a completely random condition"""
        
        metrics = [
            'price_delta_1m', 'price_delta_5m', 'price_delta_15m',
            'volume_ratio', 'volume_spike', 'order_imbalance',
            'bid_ask_spread', 'trade_velocity', 'whale_activity',
            f'random_metric_{random.randint(1000,9999)}'
        ]
        
        return {
            'metric': random.choice(metrics),
            'operator': random.choice(['>', '<', '==', 'crosses']),
            'value': random.uniform(-100, 100),
            'weight': random.uniform(0.1, 1.0)
        }
    
    def generate_completely_random_pattern(self) -> Dict:
        """Create entirely new random pattern for diversity"""
        
        return {
            'hash': hashlib.sha256(
                f"random_{datetime.now().timestamp()}_{random.randint(1000000,9999999)}".encode()
            ).hexdigest()[:16],
            'entry_conditions': [self.generate_random_condition() for _ in range(random.randint(1, 5))],
            'exit_conditions': [self.generate_random_condition() for _ in range(random.randint(1, 3))],
            'timeframe': random.randint(1, 1440),
            'generation': self.generation,
            'parent_patterns': [],
            'test_count': 0,
            'win_count': 0,
            'win_rate': 0,
            'total_profit': 0,
            'is_active': False,
        }
    
    async def store_evolution_history(self, before: List[Dict], after: List[Dict]):
        """Track evolution progress in database"""
        
        query = """
        INSERT INTO evolution_history 
        (generation, timestamp, patterns_before, patterns_after, 
         avg_fitness_before, avg_fitness_after, top_performer_hash)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        
        avg_fitness_before = np.mean([p.get('fitness', 0) for p in before])
        avg_fitness_after = np.mean([p.get('fitness', 0) for p in after])
        top_performer = max(after, key=lambda x: x.get('fitness', 0))
        
        await self.db.execute(
            query,
            self.generation,
            datetime.now(),
            len(before),
            len(after),
            avg_fitness_before,
            avg_fitness_after,
            top_performer['hash']
        )
        if not self.db:
            logger.warning("No database connection, skipping evolution history storage")
            return
        
        try:
            query = """
            INSERT INTO evolution_history 
            (generation, timestamp, patterns_before, patterns_after, 
             avg_fitness_before, avg_fitness_after, top_performer_hash)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """
            
            avg_fitness_before = np.mean([p.get('fitness', 0) for p in before]) if before else 0
            avg_fitness_after = np.mean([p.get('fitness', 0) for p in after]) if after else 0
            top_performer = max(after, key=lambda x: x.get('fitness', 0)) if after else {'hash': 'none'}
            
            await self.db.execute(
                query,
                self.generation,
                datetime.now(),
                len(before),
                len(after),
                avg_fitness_before,
                avg_fitness_after,
                top_performer['hash']
            )
            
            logger.info(f"Stored evolution history for generation {self.generation}")
            
        except Exception as e:
            logger.error(f"Error storing evolution history: {e}")

# Example usage
async def main():
    """Test the Evolution Engine"""
    from intelligence.openai_strategist import OpenAIStrategist
    
    # Mock database and strategist for testing
    class MockDB:
        async def execute(self, query, *args):
            print(f"DB Query: {query[:50]}... with {len(args)} args")
    
    strategist = OpenAIStrategist()
    db = MockDB()
    
    evolution = EvolutionEngine(strategist, db)
    
    # Create test patterns
    test_patterns = []
    for i in range(20):
        pattern = {
            'hash': f'test_pattern_{i:03d}',
            'win_rate': random.uniform(0.4, 0.8),
            'sharpe_ratio': random.uniform(0.5, 3.0),
            'total_profit': random.uniform(-100, 500),
            'test_count': random.randint(50, 200),
            'generation': 0,
            'entry_conditions': [evolution.generate_random_condition() for _ in range(3)],
            'exit_conditions': [evolution.generate_random_condition() for _ in range(2)],
            'timeframe': random.randint(5, 240),
        }
        test_patterns.append(pattern)
    
    print("🧬 Testing Evolution Engine")
    print(f"Starting with {len(test_patterns)} patterns")
    
    # Run evolution cycle
    next_gen = await evolution.daily_evolution_cycle(test_patterns)
    
    print(f"Evolution produced {len(next_gen)} patterns for next generation")
    print(f"Top performer: {max(next_gen, key=lambda x: x.get('fitness', 0))['hash']}")

if __name__ == "__main__":
    asyncio.run(main())
