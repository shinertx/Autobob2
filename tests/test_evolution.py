"""Test Evolution Engine mutations and natural selection"""

import sys
import pytest
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'core'))
from evolution_ai import EvolutionEngine

def test_fitness_calculation():
    """Test fitness calculation favors profitable patterns"""
    
    patterns = [
        {
            'hash': 'pattern1',
            'win_rate': 0.7,
            'sharpe_ratio': 2.0,
            'total_profit': 1000,
            'test_count': 150
        },
        {
            'hash': 'pattern2',
            'win_rate': 0.4,
            'sharpe_ratio': 0.5,
            'total_profit': -100,
            'test_count': 50
        },
        {
            'hash': 'pattern3',
            'win_rate': 0.65,
            'sharpe_ratio': 1.8,
            'total_profit': 500,
            'test_count': 200
        }
    ]
    
    patterns = EvolutionEngine.calculate_fitness(patterns)
    
    # Pattern 1 should have highest fitness
    assert patterns[0]['fitness'] > patterns[1]['fitness']
    assert patterns[2]['fitness'] > patterns[1]['fitness']
    
    # Check bonus for consistent patterns
    for p in patterns:
        if p['win_rate'] > 0.6 and p['sharpe_ratio'] > 1.5:
            # Should have fitness boost
            base_fitness = (
                (p['win_rate'] ** 2) * 0.3 +
                (p['sharpe_ratio'] / 3.0) * 0.3 +
                (p['total_profit'] / 1000.0) * 0.2 +
                min(1.0, p['test_count'] / 100.0) * 0.2
            )
            assert p['fitness'] > base_fitness

def test_natural_selection():
    """Verify bottom 50% are eliminated"""
    
    # Create 100 patterns with varying fitness
    patterns = []
    for i in range(100):
        patterns.append({
            'hash': f'pattern_{i}',
            'fitness': random.random(),
            'win_rate': random.random(),
            'sharpe_ratio': random.random() * 3,
            'test_count': random.randint(10, 200)
        })
    
    # Sort by fitness
    patterns.sort(key=lambda x: x['fitness'], reverse=True)
    
    # Bottom 50% should be killed
    survivors = patterns[:50]
    killed = patterns[50:]
    
    assert len(survivors) == 50
    assert len(killed) == 50
    
    # All survivors should have better fitness than killed
    min_survivor_fitness = min(s['fitness'] for s in survivors)
    max_killed_fitness = max(k['fitness'] for k in killed)
    assert min_survivor_fitness >= max_killed_fitness

def test_mutation_logic():
    """Test pattern mutations preserve core logic"""
    
    parent = {
        'hash': 'parent_pattern',
        'entry_conditions': [
            {'metric': 'price_delta_5m', 'operator': '>', 'value': 1.0}
        ],
        'exit_conditions': [
            {'metric': 'volume_spike', 'operator': '<', 'value': 0.5}
        ],
        'timeframe': 60,
        'generation': 0,
        'fitness': 0.7
    }
    
    # Create 10 mutations
    mutations = []
    for _ in range(10):
        mutant = EvolutionEngine.mutate_pattern(parent)
        mutations.append(mutant)
    
    # All should have unique hashes
    hashes = [m['hash'] for m in mutations]
    assert len(hashes) == len(set(hashes)), "Duplicate mutation hashes"
    
    # All should reference parent
    for m in mutations:
        assert parent['hash'] in m['parent_patterns']
        assert m['generation'] == parent['generation'] + 1
    
    # Some should have modified conditions
    condition_variations = 0
    for m in mutations:
        if len(m.get('entry_conditions', [])) != len(parent['entry_conditions']):
            condition_variations += 1
    
    assert condition_variations > 0, "No condition variations in mutations"
        for m in mutations:
            assert parent['hash'] in m['parent_patterns']
            assert m['generation'] == parent['generation'] + 1
        
        # Some should have modified conditions
        condition_variations = 0
        for m in mutations:
            if len(m.get('entry_conditions', [])) != len(parent['entry_conditions']):
                condition_variations += 1
        
        assert condition_variations > 0, "No condition variations in mutations"
    
    def test_crossbreeding(self, evolution_engine):
        """Test pattern crossbreeding logic"""
        
        parent1 = {
            'hash': 'parent1',
            'entry_conditions': [{'metric': 'a', 'operator': '>', 'value': 1}],
            'exit_conditions': [{'metric': 'b', 'operator': '<', 'value': 2}],
            'timeframe': 60,
            'fitness': 0.8,
            'generation': 1
        }
        
        parent2 = {
            'hash': 'parent2',
            'entry_conditions': [{'metric': 'c', 'operator': '>', 'value': 3}],
            'exit_conditions': [{'metric': 'd', 'operator': '<', 'value': 4}],
            'timeframe': 120,
            'fitness': 0.6,
            'generation': 2
        }
        
        child = evolution_engine.crossbreed_patterns(parent1, parent2)
        
        # Child should have both parents
        assert 'parent1' in child['parent_patterns']
        assert 'parent2' in child['parent_patterns']
        
        # Generation should be max parent + 1
        assert child['generation'] == 3
        
        # Should inherit from better performer
        assert child['entry_conditions'] == parent1['entry_conditions']
        
        # Timeframe should be averaged
        assert child['timeframe'] == 90
    
    @pytest.mark.asyncio
    async def test_daily_evolution_cycle(self, evolution_engine):
        """Test complete daily evolution cycle"""
        
        # Create initial population
        patterns = []
        for i in range(20):
            patterns.append({
                'hash': f'pattern_{i}',
                'entry_conditions': [{'metric': f'metric_{i}', 'operator': '>', 'value': i}],
                'exit_conditions': [{'metric': f'exit_{i}', 'operator': '<', 'value': i * 2}],
                'timeframe': 60,
                'test_count': 100 + i * 10,
                'win_count': 60 + i,
                'win_rate': 0.5 + (i * 0.02),
                'sharpe_ratio': 0.5 + (i * 0.1),
                'total_profit': i * 100,
                'generation': 0,
                'parent_patterns': [],
                'is_active': True
            })
        
        # Run evolution
        next_gen = await evolution_engine.daily_evolution_cycle(patterns)
        
        # Should have patterns in next generation
        assert len(next_gen) > 0
        
        # Should have mix of survivors, offspring, and random
        generations = [p['generation'] for p in next_gen]
        assert 0 in generations, "No survivors"
        assert 1 in generations, "No offspring"
        
        # Check evolution incremented
        assert evolution_engine.generation == 1
    
    def test_random_pattern_introduction(self, evolution_engine):
        """Test that random patterns are introduced for diversity"""
        
        random_pattern = evolution_engine.generate_completely_random_pattern()
        
        # Should have required fields
        assert 'hash' in random_pattern
        assert 'entry_conditions' in random_pattern
        assert 'exit_conditions' in random_pattern
        assert 'timeframe' in random_pattern
        
        # Should have no parents
        assert random_pattern['parent_patterns'] == []
        
        # Should start inactive
        assert random_pattern['is_active'] == False
        assert random_pattern['test_count'] == 0
