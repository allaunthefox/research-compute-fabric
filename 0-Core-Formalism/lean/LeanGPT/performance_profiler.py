#!/usr/bin/env python3
"""
Performance Profiler for OTOM Algorithms
Identifies actual bottlenecks before implementing optimizations

Per AGENTS.md §6.1: Python shim for performance analysis only
"""

import json
import time
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class AlgorithmPerformance:
    """Performance metrics for an algorithm"""
    name: str
    file: str
    complexity: str
    estimated_ops: int  # Estimated operations count
    optimization_potential: str  # "high", "medium", "low", "none"
    current_efficiency: str  # "O(1)", "O(n)", "O(n²)", etc.

class PerformanceProfiler:
    """
    Analyzes algorithm performance and identifies actual optimization opportunities.
    
    Process:
    1. Load classified algorithm data
    2. Analyze complexity and operation counts
    3. Estimate optimization potential based on actual implementation
    4. Identify high-impact optimization targets
    """
    
    def __init__(self, classified_file: str = None):
        self.classified_file = classified_file or "/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/LeanGPT/algorithms_classified.json"
        self.bootstrap_file = "/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/LeanGPT/bootstrap_results.json"
        self.performance_data: Dict[str, List[AlgorithmPerformance]] = {}
        
    def load_classified_data(self):
        """Load classified algorithm data"""
        with open(self.classified_file, 'r') as f:
            return json.load(f)
    
    def load_bootstrap_data(self):
        """Load bootstrap algorithm data"""
        with open(self.bootstrap_file, 'r') as f:
            return json.load(f)
    
    def estimate_operations(self, algorithm: dict) -> int:
        """Estimate number of operations for an algorithm"""
        complexity = algorithm.get('complexity', 'O(1)')
        
        # Simple heuristic for operation estimation
        if complexity == 'O(1)':
            return 10  # Constant time operations
        elif complexity == 'O(n)':
            return 100  # Linear operations
        elif complexity == 'O(n²)':
            return 1000  # Quadratic operations
        elif complexity == 'O(log n)':
            return 20  # Logarithmic operations
        else:
            return 50  # Default estimate
    
    def assess_optimization_potential(self, algorithm: dict) -> str:
        """Assess optimization potential based on complexity and type"""
        complexity = algorithm.get('complexity', 'O(1)')
        algo_type = algorithm.get('type', 'compute')
        
        # High potential: O(n²) algorithms
        if complexity == 'O(n²)':
            return 'high'
        
        # Medium potential: O(n) compute/solve algorithms
        if complexity == 'O(n)' and algo_type in ['compute', 'solve']:
            return 'medium'
        
        # Low potential: O(1) or O(log n)
        if complexity in ['O(1)', 'O(log n)']:
            return 'low'
        
        # Medium potential: O(n) search/find algorithms
        if complexity == 'O(n)' and algo_type in ['search', 'find']:
            return 'medium'
        
        return 'low'
    
    def analyze_performance(self):
        """Analyze performance across all algorithms"""
        classified_data = self.load_classified_data()
        bootstrap_data = self.load_bootstrap_data()
        
        # Map algorithm names to their full data
        algo_map = {algo['name']: algo for algo in bootstrap_data['algorithms']}
        
        # Analyze each domain
        for domain, domain_data in classified_data['domain_summary'].items():
            if domain == "unclassified":
                continue
            
            algorithm_names = domain_data['algorithms']
            performances = []
            
            for name in algorithm_names:
                if name in algo_map:
                    algo = algo_map[name]
                    performance = AlgorithmPerformance(
                        name=name,
                        file=algo['file'],
                        complexity=algo.get('complexity', 'O(1)'),
                        estimated_ops=self.estimate_operations(algo),
                        optimization_potential=self.assess_optimization_potential(algo),
                        current_efficiency=algo.get('complexity', 'O(1)')
                    )
                    performances.append(performance)
            
            self.performance_data[domain] = performances
    
    def print_performance_summary(self):
        """Print performance analysis summary"""
        print("=" * 60)
        print("ALGORITHM PERFORMANCE PROFILING")
        print("=" * 60)
        
        total_algorithms = 0
        high_potential_count = 0
        medium_potential_count = 0
        low_potential_count = 0
        none_potential_count = 0
        
        for domain, performances in self.performance_data.items():
            print(f"\n{domain.upper()}")
            print("-" * 60)
            
            high_pot = [p for p in performances if p.optimization_potential == 'high']
            medium_pot = [p for p in performances if p.optimization_potential == 'medium']
            
            if high_pot:
                print(f"  HIGH OPTIMIZATION POTENTIAL ({len(high_pot)}):")
                for p in high_pot[:5]:
                    print(f"    - {p.name:30} | {p.complexity:6} | {p.estimated_ops:4} ops")
                if len(high_pot) > 5:
                    print(f"    ... and {len(high_pot) - 5} more")
            
            if medium_pot:
                print(f"  MEDIUM OPTIMIZATION POTENTIAL ({len(medium_pot)}):")
                for p in medium_pot[:5]:
                    print(f"    - {p.name:30} | {p.complexity:6} | {p.estimated_ops:4} ops")
                if len(medium_pot) > 5:
                    print(f"    ... and {len(medium_pot) - 5} more")
            
            if not high_pot and not medium_pot:
                print(f"  LOW OPTIMIZATION POTENTIAL (already efficient)")
            
            total_algorithms += len(performances)
            high_potential_count += len(high_pot)
            medium_potential_count += len(medium_pot)
            low_potential_count += len([p for p in performances if p.optimization_potential == 'low'])
            none_potential_count += len([p for p in performances if p.optimization_potential == 'none'])
        
        print("\n" + "=" * 60)
        print(f"TOTAL ALGORITHMS ANALYZED: {total_algorithms}")
        print(f"  HIGH optimization potential: {high_potential_count}")
        print(f"  MEDIUM optimization potential: {medium_potential_count}")
        print(f"  LOW optimization potential: {low_potential_count}")
        print(f"  NO optimization potential: {none_potential_count}")
        print("=" * 60)
    
    def save_performance_data(self):
        """Save performance analysis results"""
        results = {
            domain: {
                "count": len(performances),
                "high_potential": len([p for p in performances if p.optimization_potential == 'high']),
                "medium_potential": len([p for p in performances if p.optimization_potential == 'medium']),
                "low_potential": len([p for p in performances if p.optimization_potential == 'low']),
                "algorithms": [
                    {
                        "name": p.name,
                        "file": p.file,
                        "complexity": p.complexity,
                        "estimated_ops": p.estimated_ops,
                        "optimization_potential": p.optimization_potential
                    }
                    for p in performances
                ]
            }
            for domain, performances in self.performance_data.items()
        }
        
        output_file = Path(self.classified_file).parent / "performance_profile.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nPerformance data saved to {output_file}")

if __name__ == "__main__":
    print("=" * 60)
    print("ALGORITHM PERFORMANCE PROFILING")
    print("=" * 60)
    
    profiler = PerformanceProfiler()
    profiler.analyze_performance()
    profiler.print_performance_summary()
    profiler.save_performance_data()
