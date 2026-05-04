#!/usr/bin/env python3
"""
Swarm Benchmarking Suite

Comprehensive benchmarking for the Enhanced Integrated Swarm System:
- Timing benchmarks for swarm operations
- Memory usage benchmarks
- Scalability benchmarks
- System throughput measurements
"""

import sys
import time
import tracemalloc
import json
import math
import sqlite3
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from statistics import mean, median, stdev

# Import from enhanced_integrated_swarm
sys.path.insert(0, str(Path(__file__).parent))
from enhanced_integrated_swarm import (
    TopologyGraph, TopologyNode, TopologyEdge, WireSegment, Component,
    SensorReading, PCBSpecifications, MathDatabase, MathEntity,
    NIICore, NIICoreStatus, EnhancedGeometricParams, EnhancedSwarmAgent,
    EnhancedSwarmState, NIICoreRegistry, EnhancedTopologyMapper,
    EnhancedIntegratedSwarm
)

# ═══════════════════════════════════════════════════════════════════════════
# Benchmark Data Structures
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class TimingMetrics:
    """Timing metrics for swarm operations"""
    initialization_time_ms: float
    agent_analysis_time_ms: float
    consensus_computation_time_ms: float
    math_query_time_ms: float
    topology_mapping_time_ms: float
    total_swarm_time_ms: float

@dataclass
class MemoryMetrics:
    """Memory usage metrics"""
    peak_memory_mb: float
    agent_memory_mb: float
    topology_memory_mb: float
    math_db_memory_mb: float
    total_memory_mb: float

@dataclass
class ScalabilityMetrics:
    """Scalability metrics"""
    agents_count: int
    nodes_count: int
    edges_count: int
    throughput_ops_per_sec: float
    latency_ms: float
    scaling_efficiency: float

@dataclass
class BenchmarkResult:
    """Complete benchmark result"""
    timing: TimingMetrics
    memory: MemoryMetrics
    scalability: ScalabilityMetrics
    swarm_state: EnhancedSwarmState

# ═══════════════════════════════════════════════════════════════════════════
# Benchmark Suite
# ═══════════════════════════════════════════════════════════════════════════

class SwarmBenchmark:
    """Comprehensive benchmarking suite for swarm system"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
    
    def create_scalable_topology(self, nodes_count: int, edges_count: int) -> TopologyGraph:
        """Create topology with specified size for scalability testing"""
        wire_segments = {}
        components = {}
        edges = []
        nodes = {}
        
        # Create nodes
        for i in range(nodes_count):
            component = Component(
                name=f"Component_{i}",
                type="generic",
                location=(float(i * 10.0), float(i * 10.0)),
                voltage_mv=1200.0,
                current_ma=1000.0,
                temperature_c=40.0,
                power_mw=1200.0
            )
            components[f"node_{i}"] = component
            
            node = TopologyNode(
                id=f"node_{i}",
                component=component,
                connections=[f"node_{(i+1) % nodes_count}"],
                voltage_mv=1200.0,
                current_ma=1000.0,
                timing_ps=100.0
            )
            nodes[f"node_{i}"] = node
        
        # Create wire segments and edges
        for i in range(min(edges_count, nodes_count)):
            wire_segment = WireSegment(
                name=f"wire_{i}",
                length_mm=2.0 + float(i),
                resistance_ohm=0.05 + float(i) * 0.01,
                capacitance_pf=2.0 + float(i) * 0.5,
                inductance_nh=1.5 + float(i) * 0.2,
                impedance_ohm=50.0,
                propagation_delay_ps=100.0 + float(i) * 10.0
            )
            wire_segments[f"wire_{i}"] = wire_segment
            
            edge = TopologyEdge(
                source=f"node_{i}",
                target=f"node_{(i+1) % nodes_count}",
                wire_segment=wire_segment,
                voltage_drop_mv=100.0 + float(i) * 10.0,
                current_ma=1000.0,
                timing_ps=100.0 + float(i) * 10.0,
                impedance_ohm=50.0
            )
            edges.append(edge)
        
        return TopologyGraph(
            nodes=nodes,
            edges=edges,
            wire_segments=wire_segments,
            components=components,
            sensor_readings=[],
            timestamp=0.0
        )
    
    def benchmark_timing(self, swarm: EnhancedIntegratedSwarm, base_params: Dict[str, float], 
                        subject: str = "topology", iterations: int = 10) -> TimingMetrics:
        """Benchmark timing metrics for swarm operations"""
        init_times = []
        analysis_times = []
        consensus_times = []
        math_query_times = []
        topology_mapping_times = []
        total_times = []
        
        for _ in range(iterations):
            # Benchmark initialization
            start = time.perf_counter()
            swarm.initialize_agents(base_params, subject)
            init_time = (time.perf_counter() - start) * 1000
            init_times.append(init_time)
            
            # Benchmark topology mapping
            start = time.perf_counter()
            topology_factors = swarm.mapper.calculate_topology_factors()
            topology_time = (time.perf_counter() - start) * 1000
            topology_mapping_times.append(topology_time)
            
            # Benchmark math query
            start = time.perf_counter()
            math_entities = swarm.math_db.query_by_subject(subject)
            math_time = (time.perf_counter() - start) * 1000
            math_query_times.append(math_time)
            
            # Benchmark agent analysis
            start = time.perf_counter()
            for agent in swarm.agents:
                swarm.run_agent_analysis(agent)
            analysis_time = (time.perf_counter() - start) * 1000
            analysis_times.append(analysis_time)
            
            # Benchmark consensus computation
            start = time.perf_counter()
            consensus = swarm.compute_consensus()
            consensus_time = (time.perf_counter() - start) * 1000
            consensus_times.append(consensus_time)
            
            # Total time
            total_time = init_time + topology_time + math_time + analysis_time + consensus_time
            total_times.append(total_time)
        
        return TimingMetrics(
            initialization_time_ms=mean(init_times),
            agent_analysis_time_ms=mean(analysis_times),
            consensus_computation_time_ms=mean(consensus_times),
            math_query_time_ms=mean(math_query_times),
            topology_mapping_time_ms=mean(topology_mapping_times),
            total_swarm_time_ms=mean(total_times)
        )
    
    def benchmark_memory(self, swarm: EnhancedIntegratedSwarm, base_params: Dict[str, float],
                       subject: str = "topology") -> MemoryMetrics:
        """Benchmark memory usage metrics"""
        tracemalloc.start()
        
        # Baseline memory
        baseline_snapshot = tracemalloc.take_snapshot()
        
        # Initialize swarm
        swarm.initialize_agents(base_params, subject)
        
        # Memory after agent initialization
        agent_snapshot = tracemalloc.take_snapshot()
        agent_memory = sum(stat.size for stat in agent_snapshot.compare_to(baseline_snapshot, 'lineno')) / 1024 / 1024
        
        # Topology memory
        topology_snapshot = tracemalloc.take_snapshot()
        topology_memory = sum(stat.size for stat in topology_snapshot.compare_to(agent_snapshot, 'lineno')) / 1024 / 1024
        
        # Math DB memory
        math_snapshot = tracemalloc.take_snapshot()
        math_memory = sum(stat.size for stat in math_snapshot.compare_to(topology_snapshot, 'lineno')) / 1024 / 1024
        
        # Peak memory
        peak_memory = tracemalloc.get_traced_memory()[0] / 1024 / 1024
        
        tracemalloc.stop()
        
        return MemoryMetrics(
            peak_memory_mb=peak_memory,
            agent_memory_mb=agent_memory,
            topology_memory_mb=topology_memory,
            math_db_memory_mb=math_memory,
            total_memory_mb=peak_memory
        )
    
    def benchmark_scalability(self, nodes_counts: List[int], edges_counts: List[int],
                            base_params: Dict[str, float], subject: str = "topology") -> List[ScalabilityMetrics]:
        """Benchmark scalability across different topology sizes"""
        scalability_results = []
        
        for nodes_count, edges_count in zip(nodes_counts, edges_counts):
            # Create scalable topology
            topology = self.create_scalable_topology(nodes_count, edges_count)
            math_db = MathDatabase()
            swarm = EnhancedIntegratedSwarm(topology, math_db)
            
            # Measure latency
            start = time.perf_counter()
            swarm.initialize_agents(base_params, subject)
            for agent in swarm.agents:
                swarm.run_agent_analysis(agent)
            consensus = swarm.compute_consensus()
            latency_ms = (time.perf_counter() - start) * 1000
            
            # Calculate throughput (operations per second)
            operations = len(swarm.agents) + nodes_count + edges_count
            throughput_ops_per_sec = operations / (latency_ms / 1000)
            
            # Calculate scaling efficiency (throughput / nodes)
            scaling_efficiency = throughput_ops_per_sec / nodes_count if nodes_count > 0 else 0
            
            scalability_results.append(ScalabilityMetrics(
                agents_count=len(swarm.agents),
                nodes_count=nodes_count,
                edges_count=edges_count,
                throughput_ops_per_sec=throughput_ops_per_sec,
                latency_ms=latency_ms,
                scaling_efficiency=scaling_efficiency
            ))
        
        return scalability_results
    
    def run_comprehensive_benchmark(self, base_params: Dict[str, float], 
                                   subject: str = "topology") -> BenchmarkResult:
        """Run comprehensive benchmark including timing, memory, and scalability"""
        # Create demo topology
        topology = self.create_scalable_topology(10, 5)
        math_db = MathDatabase()
        swarm = EnhancedIntegratedSwarm(topology, math_db)
        
        # Run timing benchmarks
        timing = self.benchmark_timing(swarm, base_params, subject, iterations=5)
        
        # Run memory benchmarks
        memory = self.benchmark_memory(swarm, base_params, subject)
        
        # Run scalability benchmarks
        scalability_results = self.benchmark_scalability(
            nodes_counts=[5, 10, 20, 50],
            edges_counts=[3, 5, 10, 25],
            base_params=base_params,
            subject=subject
        )
        
        # Use median scalability result
        median_scalability = scalability_results[len(scalability_results) // 2]
        
        # Run full swarm analysis for state
        swarm_state = swarm.run_swarm_analysis(base_params, subject)
        
        return BenchmarkResult(
            timing=timing,
            memory=memory,
            scalability=median_scalability,
            swarm_state=swarm_state
        )
    
    def generate_report(self, result: BenchmarkResult) -> str:
        """Generate comprehensive benchmark report"""
        report = []
        report.append("="*70)
        report.append("ENHANCED INTEGRATED SWARM BENCHMARK REPORT")
        report.append("="*70)
        
        # Timing metrics
        report.append("\n[Timing Metrics]")
        report.append(f"  Initialization: {result.timing.initialization_time_ms:.3f} ms")
        report.append(f"  Agent Analysis: {result.timing.agent_analysis_time_ms:.3f} ms")
        report.append(f"  Consensus Computation: {result.timing.consensus_computation_time_ms:.3f} ms")
        report.append(f"  Math Query: {result.timing.math_query_time_ms:.3f} ms")
        report.append(f"  Topology Mapping: {result.timing.topology_mapping_time_ms:.3f} ms")
        report.append(f"  Total Swarm Time: {result.timing.total_swarm_time_ms:.3f} ms")
        
        # Memory metrics
        report.append("\n[Memory Metrics]")
        report.append(f"  Peak Memory: {result.memory.peak_memory_mb:.3f} MB")
        report.append(f"  Agent Memory: {result.memory.agent_memory_mb:.3f} MB")
        report.append(f"  Topology Memory: {result.memory.topology_memory_mb:.3f} MB")
        report.append(f"  Math DB Memory: {result.memory.math_db_memory_mb:.3f} MB")
        report.append(f"  Total Memory: {result.memory.total_memory_mb:.3f} MB")
        
        # Scalability metrics
        report.append("\n[Scalability Metrics]")
        report.append(f"  Agents Count: {result.scalability.agents_count}")
        report.append(f"  Nodes Count: {result.scalability.nodes_count}")
        report.append(f"  Edges Count: {result.scalability.edges_count}")
        report.append(f"  Throughput: {result.scalability.throughput_ops_per_sec:.3f} ops/sec")
        report.append(f"  Latency: {result.scalability.latency_ms:.3f} ms")
        report.append(f"  Scaling Efficiency: {result.scalability.scaling_efficiency:.3f}")
        
        # Swarm state
        report.append("\n[Swarm State]")
        report.append(f"  Consensus: {result.swarm_state.consensus:.3f}")
        report.append(f"  Topology Optimization Score: {result.swarm_state.topology_optimization_score:.3f}")
        report.append(f"  Math Coverage Score: {result.swarm_state.math_coverage_score:.3f}")
        report.append(f"  Lean Coverage Score: {result.swarm_state.lean_coverage_score:.3f}")
        report.append(f"  Overall System Score: {result.swarm_state.overall_system_score:.3f}")
        
        # Performance summary
        report.append("\n[Performance Summary]")
        if result.timing.total_swarm_time_ms < 100:
            report.append("  Status: EXCELLENT (< 100ms)")
        elif result.timing.total_swarm_time_ms < 500:
            report.append("  Status: GOOD (< 500ms)")
        elif result.timing.total_swarm_time_ms < 1000:
            report.append("  Status: ACCEPTABLE (< 1s)")
        else:
            report.append("  Status: NEEDS OPTIMIZATION")
        
        if result.memory.total_memory_mb < 100:
            report.append("  Memory: EXCELLENT (< 100MB)")
        elif result.memory.total_memory_mb < 500:
            report.append("  Memory: GOOD (< 500MB)")
        elif result.memory.total_memory_mb < 1000:
            report.append("  Memory: ACCEPTABLE (< 1GB)")
        else:
            report.append("  Memory: NEEDS OPTIMIZATION")
        
        if result.scalability.throughput_ops_per_sec > 1000:
            report.append("  Throughput: EXCELLENT (> 1000 ops/sec)")
        elif result.scalability.throughput_ops_per_sec > 500:
            report.append("  Throughput: GOOD (> 500 ops/sec)")
        elif result.scalability.throughput_ops_per_sec > 100:
            report.append("  Throughput: ACCEPTABLE (> 100 ops/sec)")
        else:
            report.append("  Throughput: NEEDS OPTIMIZATION")
        
        report.append("="*70)
        
        return "\n".join(report)

# ═══════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point for swarm benchmarking"""
    print("[INFO] Swarm Benchmarking Suite")
    print("="*70)
    
    # Initialize benchmark suite
    benchmark = SwarmBenchmark()
    
    # Base geometric parameters
    base_params = {
        'kappa_squared': 0.5,
        'rho_seq': 0.5,
        'v_epigenetic': 0.5,
        'tau_structure': 0.5,
        'sigma_entropy': 0.5,
        'q_conservation': 0.5,
        'kappa_hierarchy': 0.5,
        'epsilon_mutation': 0.5
    }
    
    # Run comprehensive benchmark
    print("[INFO] Running comprehensive benchmark...")
    result = benchmark.run_comprehensive_benchmark(base_params, subject="topology")
    
    # Generate and print report
    report = benchmark.generate_report(result)
    print(report)
    
    # Save results to JSON
    results_path = "/home/allaun/Documents/Research Stack/data/swarm_benchmark_results.json"
    with open(results_path, 'w') as f:
        json.dump(asdict(result), f, indent=2)
    print(f"\n[OK] Benchmark results saved to {results_path}")

if __name__ == "__main__":
    main()
