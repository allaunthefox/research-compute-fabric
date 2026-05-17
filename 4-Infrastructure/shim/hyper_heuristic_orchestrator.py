#!/usr/bin/env python3
"""
Hyper-Heuristic Orchestrator for Research Stack

Meta-optimization layer that selects between low-level heuristics across
multiple components: FAMM delay optimization, PIST move selection, and
infrastructure shim selection.

Core idea: Instead of directly solving problems, the hyper-heuristic selects
which low-level heuristic to apply based on current state, performance metrics,
and historical patterns.
"""

import json
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import random


class HeuristicType(Enum):
    """Types of low-level heuristics that can be selected."""
    GREEDY = "greedy"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"
    ADAPTIVE = "adaptive"
    RANDOM = "random"


class ComponentType(Enum):
    """Components that can use hyper-heuristic optimization."""
    FAMM_DELAY = "famm_delay"
    PIST_MOVE = "pist_move"
    SHIM_SELECTION = "shim_selection"
    GPU_SCHEDULING = "gpu_scheduling"
    FPGA_BUILD = "fpga_build"


@dataclass
class HeuristicMetrics:
    """Performance metrics for heuristic evaluation."""
    success_rate: float = 0.0
    avg_cost: float = 0.0
    avg_time: float = 0.0
    total_runs: int = 0
    last_reward: float = 0.0

    def update(self, success: bool, cost: float, exec_time: float, reward: float):
        """Update metrics with new execution result."""
        self.total_runs += 1

        # Exponential moving average for metrics
        alpha = 0.1
        self.success_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * self.success_rate
        self.avg_cost = alpha * cost + (1 - alpha) * self.avg_cost
        self.avg_time = alpha * exec_time + (1 - alpha) * self.avg_time
        self.last_reward = reward

    def score(self) -> float:
        """Compute composite score (higher is better)."""
        # Balance success rate, cost, and time
        return self.success_rate * 100 - self.avg_cost - self.avg_time * 10 + self.last_reward


@dataclass
class HyperHeuristicState:
    """State of the hyper-heuristic for a specific component."""
    component: ComponentType
    current_heuristic: HeuristicType
    metrics: Dict[HeuristicType, HeuristicMetrics] = field(default_factory=dict)
    switch_count: int = 0
    total_operations: int = 0
    exploration_rate: float = 0.1  # Epsilon-greedy exploration

    def __post_init__(self):
        """Initialize metrics for all heuristic types."""
        for ht in HeuristicType:
            if ht not in self.metrics:
                self.metrics[ht] = HeuristicMetrics()

    def select_heuristic(self) -> HeuristicType:
        """Select heuristic using epsilon-greedy strategy."""
        if random.random() < self.exploration_rate:
            # Explore: random selection
            return random.choice(list(HeuristicType))
        else:
            # Exploit: select best performing heuristic
            best_heuristic = self.current_heuristic
            best_score = self.metrics[best_heuristic].score()

            for ht, metrics in self.metrics.items():
                if metrics.score() > best_score and metrics.total_runs > 0:
                    best_score = metrics.score()
                    best_heuristic = ht

            return best_heuristic

    def should_switch(self, candidate: HeuristicType) -> bool:
        """Determine if we should switch to candidate heuristic."""
        if candidate == self.current_heuristic:
            return False

        current_score = self.metrics[self.current_heuristic].score()
        candidate_score = self.metrics[candidate].score()

        # Switch if candidate is significantly better (10% threshold)
        if candidate_score > current_score * 1.1 and self.metrics[candidate].total_runs > 5:
            return True

        return False

    def update(self, heuristic: HeuristicType, success: bool, cost: float,
               exec_time: float, reward: float):
        """Update state after heuristic execution."""
        self.metrics[heuristic].update(success, cost, exec_time, reward)
        self.total_operations += 1

        # Decay exploration rate over time
        self.exploration_rate = max(0.01, self.exploration_rate * 0.9995)


class HyperHeuristicOrchestrator:
    """Main orchestrator managing hyper-heuristics across components."""

    def __init__(self):
        self.states: Dict[ComponentType, HyperHeuristicState] = {}
        self.global_metrics: Dict[str, Any] = defaultdict(list)

    def get_state(self, component: ComponentType) -> HyperHeuristicState:
        """Get or create hyper-heuristic state for component."""
        if component not in self.states:
            default_heuristic = HeuristicType.ADAPTIVE
            self.states[component] = HyperHeuristicState(
                component=component,
                current_heuristic=default_heuristic
            )
        return self.states[component]

    def select_and_execute(self, component: ComponentType,
                           heuristic_func: callable,
                           context: Dict[str, Any]) -> Tuple[Any, HeuristicType]:
        """
        Select heuristic and execute function.

        Args:
            component: Component type
            heuristic_func: Function that takes (heuristic_type, context) and returns result
            context: Execution context

        Returns:
            (result, heuristic_used)
        """
        state = self.get_state(component)
        heuristic = state.select_heuristic()

        # Check if we should switch
        if state.should_switch(heuristic):
            state.current_heuristic = heuristic
            state.switch_count += 1

        # Execute with timing
        start_time = time.time()
        try:
            result = heuristic_func(heuristic, context)
            if isinstance(result, dict):
                success = bool(result.get('success', True))
                cost = float(result.get('cost', 0.0 if success else 100.0))
                reward = float(result.get('reward', 1.0 if success else -10.0))
            else:
                success = True
                cost = 0.0
                reward = 1.0
        except Exception as e:
            result = None
            success = False
            cost = 100.0  # Penalty for failure
            reward = -10.0
            print(f"Heuristic execution failed: {e}")

        exec_time = time.time() - start_time

        # Update state
        state.update(heuristic, success, cost, exec_time, reward)

        # Track global metrics
        self.global_metrics[f"{component.value}_{heuristic.value}"].append({
            'success': success,
            'cost': cost,
            'time': exec_time,
            'reward': reward
        })

        return result, heuristic

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report for all components."""
        report = {
            'components': {},
            'global_stats': {}
        }

        for component, state in self.states.items():
            component_report = {
                'current_heuristic': state.current_heuristic.value,
                'switch_count': state.switch_count,
                'total_operations': state.total_operations,
                'exploration_rate': state.exploration_rate,
                'heuristic_metrics': {}
            }

            for ht, metrics in state.metrics.items():
                component_report['heuristic_metrics'][ht.value] = {
                    'success_rate': metrics.success_rate,
                    'avg_cost': metrics.avg_cost,
                    'avg_time': metrics.avg_time,
                    'total_runs': metrics.total_runs,
                    'score': metrics.score()
                }

            report['components'][component.value] = component_report

        # Global statistics
        total_ops = sum(s.total_operations for s in self.states.values())
        total_switches = sum(s.switch_count for s in self.states.values())
        report['global_stats'] = {
            'total_operations': total_ops,
            'total_switches': total_switches,
            'switch_rate': total_switches / max(1, total_ops)
        }

        return report

    def save_state(self, filepath: str):
        """Save hyper-heuristic state to file."""
        state_data = {
            'states': {},
            'global_metrics': dict(self.global_metrics)
        }

        for component, state in self.states.items():
            state_data['states'][component.value] = {
                'current_heuristic': state.current_heuristic.value,
                'metrics': {
                    ht.value: {
                        'success_rate': m.success_rate,
                        'avg_cost': m.avg_cost,
                        'avg_time': m.avg_time,
                        'total_runs': m.total_runs,
                        'last_reward': m.last_reward
                    }
                    for ht, m in state.metrics.items()
                },
                'switch_count': state.switch_count,
                'total_operations': state.total_operations,
                'exploration_rate': state.exploration_rate
            }

        with open(filepath, 'w') as f:
            json.dump(state_data, f, indent=2)

    def load_state(self, filepath: str):
        """Load hyper-heuristic state from file."""
        with open(filepath, 'r') as f:
            state_data = json.load(f)

        for component_str, component_state in state_data['states'].items():
            component = ComponentType(component_str)
            current_heuristic = HeuristicType(component_state['current_heuristic'])

            metrics = {}
            for ht_str, m_data in component_state['metrics'].items():
                ht = HeuristicType(ht_str)
                metrics[ht] = HeuristicMetrics(
                    success_rate=m_data['success_rate'],
                    avg_cost=m_data['avg_cost'],
                    avg_time=m_data['avg_time'],
                    total_runs=m_data['total_runs'],
                    last_reward=m_data['last_reward']
                )

            self.states[component] = HyperHeuristicState(
                component=component,
                current_heuristic=current_heuristic,
                metrics=metrics,
                switch_count=component_state['switch_count'],
                total_operations=component_state['total_operations'],
                exploration_rate=component_state['exploration_rate']
            )

        self.global_metrics = defaultdict(list, state_data['global_metrics'])


# FAMM-specific hyper-heuristics
class FAMMHyperHeuristics:
    """FAMM delay optimization hyper-heuristics."""

    @staticmethod
    def greedy_minimize(heuristic: HeuristicType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Greedy delay minimization - always minimize delay."""
        bank = context.get('bank', {})
        address = context.get('address', 0)
        target_delay = context.get('target_delay', 1.0)
        max_delay = context.get('max_delay', 10.0)

        adjusted_delay = min(target_delay, max_delay)

        return {
            'strategy': 'greedy_minimize',
            'adjusted_delay': adjusted_delay,
            'success': adjusted_delay <= max_delay
        }

    @staticmethod
    def frustration_balance(heuristic: HeuristicType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Balance competing delays to minimize frustration."""
        bank = context.get('bank', {})
        address = context.get('address', 0)
        target_delay = context.get('target_delay', 1.0)
        max_delay = context.get('max_delay', 10.0)

        # Simulate frustration balancing by averaging with existing delay
        current_delay = bank.get('cells', {}).get(address, {}).get('delay', target_delay)
        adjusted_delay = min((current_delay + target_delay) / 2, max_delay)

        return {
            'strategy': 'frustration_balance',
            'adjusted_delay': adjusted_delay,
            'success': adjusted_delay <= max_delay
        }

    @staticmethod
    def adaptive_weight(heuristic: HeuristicType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Adaptive weighting based on delay mass and weight."""
        bank = context.get('bank', {})
        address = context.get('address', 0)
        target_delay = context.get('target_delay', 1.0)
        max_delay = context.get('max_delay', 10.0)

        cell = bank.get('cells', {}).get(address, {})
        delay_weight = cell.get('delay_weight', 1.0)
        weight = delay_weight / (delay_weight + 1.0)
        current_delay = cell.get('delay', target_delay)

        adjusted_delay = min(current_delay * weight + target_delay * (1 - weight), max_delay)

        return {
            'strategy': 'adaptive_weight',
            'adjusted_delay': adjusted_delay,
            'success': adjusted_delay <= max_delay
        }


# PIST-specific hyper-heuristics
class PISTHyperHeuristics:
    """PIST move selection hyper-heuristics."""

    @staticmethod
    def linear_move(heuristic: HeuristicType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Select linear move (step within shell)."""
        pos = context.get('pos', {'k': 0, 't': 0})
        k = pos.get('k', 0)
        t = pos.get('t', 0)

        # Linear step: increment or decrement t
        new_t = t + 1 if t < 2 * k else t - 1

        return {
            'strategy': 'linear',
            'move_type': 'linearStep',
            'new_pos': {'k': k, 't': new_t},
            'success': True
        }

    @staticmethod
    def resonance_jump(heuristic: HeuristicType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Select resonance jump (preserve mass)."""
        pos = context.get('pos', {'k': 0, 't': 0})
        k = pos.get('k', 0)
        t = pos.get('t', 0)

        # Mirror position to preserve mass
        new_t = 2 * k + 1 - t

        return {
            'strategy': 'resonance',
            'move_type': 'resonanceJump',
            'new_pos': {'k': k, 't': new_t},
            'success': True
        }

    @staticmethod
    def adaptive_move(heuristic: HeuristicType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Adaptive move selection based on phase."""
        pos = context.get('pos', {'k': 0, 't': 0})
        phase = context.get('phase', 'grounded')

        if phase == 'seismic':
            # Use resonance jumps for seismic phase
            return PISTHyperHeuristics.resonance_jump(heuristic, context)
        else:
            # Use linear moves for grounded phase
            return PISTHyperHeuristics.linear_move(heuristic, context)


# Infrastructure shim selection hyper-heuristics
class ShimSelectionHyperHeuristics:
    """Infrastructure shim selection hyper-heuristics."""

    @staticmethod
    def select_by_domain(heuristic: HeuristicType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Select shim based on problem domain."""
        domain = context.get('domain', 'general')
        task_type = context.get('task_type', 'unknown')

        # Domain-based shim mapping
        shim_map = {
            'math': ['math_prover_prior_metaprobe.py', 'intense_math_modeling_router.py'],
            'compression': ['compression_signal_shaping_synthesis.py', 'semantic_compression_theoretical_limits_prior.py'],
            'hardware': ['tang9k_uart_beacon_probe.py', 'fpga_nanokernel_rrc_analysis.py'],
            'general': ['stack_solidification_audit.py', 'parallel_metaprobe_launcher.py']
        }

        candidates = shim_map.get(domain, shim_map['general'])
        selected = candidates[0] if candidates else 'default_shim.py'

        return {
            'strategy': 'domain_based',
            'selected_shim': selected,
            'candidates': candidates,
            'success': True
        }

    @staticmethod
    def select_by_performance(heuristic: HeuristicType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Select shim based on historical performance."""
        domain = context.get('domain', 'general')
        performance_history = context.get('performance_history', {})

        # Select best performing shim for domain
        if domain in performance_history:
            best_shim = max(performance_history[domain].items(), key=lambda x: x[1])[0]
        else:
            best_shim = 'default_shim.py'

        return {
            'strategy': 'performance_based',
            'selected_shim': best_shim,
            'success': True
        }

    @staticmethod
    def select_adaptive(heuristic: HeuristicType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Adaptive shim selection combining domain and performance."""
        domain = context.get('domain', 'general')
        performance_history = context.get('performance_history', {})

        # Try performance-based first, fall back to domain-based
        if domain in performance_history and performance_history[domain]:
            return ShimSelectionHyperHeuristics.select_by_performance(heuristic, context)
        else:
            return ShimSelectionHyperHeuristics.select_by_domain(heuristic, context)


# GPU scheduling hyper-heuristics
class GPUSchedulingHyperHeuristics:
    """GPU task scheduling hyper-heuristics for RTX 4070."""

    @staticmethod
    def round_robin(heuristic: HeuristicType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Round-robin task scheduling across GPU resources."""
        task_queue = context.get('task_queue', [])
        gpu_count = context.get('gpu_count', 1)
        current_gpu = context.get('current_gpu', 0)

        if not task_queue:
            return {'strategy': 'round_robin', 'assigned': [], 'success': True}

        # Assign tasks in round-robin fashion
        assigned = []
        for i, task in enumerate(task_queue):
            gpu_id = (current_gpu + i) % gpu_count
            assigned.append({'task': task, 'gpu_id': gpu_id})

        return {
            'strategy': 'round_robin',
            'assigned': assigned,
            'next_gpu': (current_gpu + len(task_queue)) % gpu_count,
            'success': True
        }

    @staticmethod
    def priority_based(heuristic: HeuristicType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Priority-based scheduling considering task urgency and resource requirements."""
        task_queue = context.get('task_queue', [])
        gpu_memory = context.get('gpu_memory', 12000)  # RTX 4070: ~12GB
        gpu_count = context.get('gpu_count', 1)

        # Sort by priority (higher priority first)
        sorted_tasks = sorted(task_queue, key=lambda t: t.get('priority', 0), reverse=True)

        assigned = []
        memory_used = 0

        for task in sorted_tasks:
            task_memory = task.get('memory_required', 1000)

            # Find GPU with sufficient memory
            if memory_used + task_memory <= gpu_memory:
                assigned.append({'task': task, 'gpu_id': 0, 'reason': 'memory_available'})
                memory_used += task_memory
            else:
                assigned.append({'task': task, 'gpu_id': None, 'reason': 'insufficient_memory'})

        return {
            'strategy': 'priority_based',
            'assigned': assigned,
            'memory_utilization': memory_used / gpu_memory,
            'success': memory_used <= gpu_memory
        }

    @staticmethod
    def load_balancing(heuristic: HeuristicType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Load-aware balancing across GPU resources."""
        task_queue = context.get('task_queue', [])
        gpu_states = context.get('gpu_states', [{'load': 0.5, 'memory': 6000}])

        assigned = []

        for task in enumerate(task_queue):
            # Select least loaded GPU
            best_gpu = min(range(len(gpu_states)), key=lambda i: gpu_states[i]['load'])

            task_load = task[1].get('estimated_load', 0.1)
            gpu_states[best_gpu]['load'] += task_load

            assigned.append({
                'task': task[1],
                'gpu_id': best_gpu,
                'gpu_load_before': gpu_states[best_gpu]['load'] - task_load,
                'gpu_load_after': gpu_states[best_gpu]['load']
            })

        return {
            'strategy': 'load_balancing',
            'assigned': assigned,
            'final_gpu_states': gpu_states,
            'success': True
        }

    @staticmethod
    def memory_aware(heuristic: HeuristicType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Memory-aware scheduling for large model workloads."""
        task_queue = context.get('task_queue', [])
        gpu_memory_total = context.get('gpu_memory', 12000)
        current_usage = context.get('current_memory_usage', 0)

        # Group tasks by memory requirements
        large_tasks = [t for t in task_queue if t.get('memory_required', 0) > 4000]
        small_tasks = [t for t in task_queue if t.get('memory_required', 0) <= 4000]

        assigned = []
        memory_used = current_usage

        # Schedule large tasks first (they're harder to place)
        for task in large_tasks:
            task_memory = task.get('memory_required', 5000)
            if memory_used + task_memory <= gpu_memory_total:
                assigned.append({'task': task, 'gpu_id': 0, 'reason': 'large_task_fit'})
                memory_used += task_memory
            else:
                assigned.append({'task': task, 'gpu_id': None, 'reason': 'insufficient_memory'})

        # Fill remaining space with small tasks
        for task in small_tasks:
            task_memory = task.get('memory_required', 1000)
            if memory_used + task_memory <= gpu_memory_total:
                assigned.append({'task': task, 'gpu_id': 0, 'reason': 'small_task_fill'})
                memory_used += task_memory
            else:
                assigned.append({'task': task, 'gpu_id': None, 'reason': 'insufficient_memory'})

        return {
            'strategy': 'memory_aware',
            'assigned': assigned,
            'memory_utilization': memory_used / gpu_memory_total,
            'large_tasks_scheduled': len([a for a in assigned if a['gpu_id'] is not None and a['task'].get('memory_required', 0) > 4000]),
            'success': memory_used <= gpu_memory_total
        }


# FPGA build optimization hyper-heuristics
class FPGABuildHyperHeuristics:
    """FPGA build and simulation optimization hyper-heuristics."""

    @staticmethod
    def incremental_build(heuristic: HeuristicType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Incremental build strategy - only rebuild changed modules."""
        changed_files = context.get('changed_files', [])
        build_cache = context.get('build_cache', {})

        modules_to_rebuild = []
        cache_hits = []

        for file in changed_files:
            if file in build_cache:
                cache_hits.append(file)
            else:
                modules_to_rebuild.append(file)

        return {
            'strategy': 'incremental_build',
            'modules_to_rebuild': modules_to_rebuild,
            'cache_hits': cache_hits,
            'estimated_speedup': len(cache_hits) / max(1, len(changed_files)),
            'success': True
        }

    @staticmethod
    def parallel_synthesis(heuristic: HeuristicType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parallel synthesis strategy for independent modules."""
        modules = context.get('modules', [])
        dependency_graph = context.get('dependency_graph', {})
        available_cores = context.get('available_cores', 4)

        # Identify independent modules (no dependencies)
        independent_modules = []
        dependent_modules = []

        for module in modules:
            deps = dependency_graph.get(module, [])
            if not deps or all(dep not in modules for dep in deps):
                independent_modules.append(module)
            else:
                dependent_modules.append(module)

        # Schedule independent modules in parallel
        parallel_slots = min(len(independent_modules), available_cores)

        return {
            'strategy': 'parallel_synthesis',
            'parallel_slots': parallel_slots,
            'independent_modules': independent_modules,
            'dependent_modules': dependent_modules,
            'estimated_speedup': parallel_slots / max(1, len(modules)),
            'success': True
        }

    @staticmethod
    def resource_aware(heuristic: HeuristicType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Resource-aware synthesis considering FPGA resource constraints."""
        modules = context.get('modules', [])
        resource_budget = context.get('resource_budget', {'LUT': 43200, 'FF': 86400, 'BRAM': 120})
        module_resources = context.get('module_resources', {})

        scheduled = []
        resource_used = {'LUT': 0, 'FF': 0, 'BRAM': 0}
        deferred = []

        for module in modules:
            req = module_resources.get(module, {'LUT': 1000, 'FF': 2000, 'BRAM': 1})

            # Check if module fits
            fits = all(
                resource_used[r] + req[r] <= resource_budget[r]
                for r in ['LUT', 'FF', 'BRAM']
            )

            if fits:
                scheduled.append(module)
                for r in ['LUT', 'FF', 'BRAM']:
                    resource_used[r] += req[r]
            else:
                deferred.append(module)

        return {
            'strategy': 'resource_aware',
            'scheduled': scheduled,
            'deferred': deferred,
            'resource_utilization': {
                r: resource_used[r] / resource_budget[r] for r in ['LUT', 'FF', 'BRAM']
            },
            'success': len(deferred) == 0
        }

    @staticmethod
    def timing_driven(heuristic: HeuristicType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Timing-driven synthesis for critical path optimization."""
        modules = context.get('modules', [])
        timing_constraints = context.get('timing_constraints', {})
        critical_paths = context.get('critical_paths', [])

        # Prioritize modules on critical paths
        priority_map = {}
        for i, path in enumerate(critical_paths):
            for module in path:
                priority_map[module] = priority_map.get(module, 0) + (len(critical_paths) - i)

        # Sort modules by priority (critical path modules first)
        sorted_modules = sorted(
            modules,
            key=lambda m: priority_map.get(m, 0),
            reverse=True
        )

        return {
            'strategy': 'timing_driven',
            'module_priority': priority_map,
            'build_order': sorted_modules,
            'critical_modules': [m for m in sorted_modules if priority_map.get(m, 0) > 0],
            'success': True
        }


def demo_famm_hyperheuristic():
    """Demonstrate FAMM hyper-heuristic optimization."""
    print("=== FAMM Hyper-Heuristic Demo ===")

    orchestrator = HyperHeuristicOrchestrator()

    # Simulate FAMM operations
    for i in range(20):
        context = {
            'bank': {
                'cells': {
                    0: {'delay': 5.0, 'delay_weight': 1.0},
                    1: {'delay': 3.0, 'delay_weight': 0.5}
                }
            },
            'address': i % 2,
            'target_delay': 4.0,
            'max_delay': 10.0
        }

        # Route to appropriate heuristic function based on current selection
        def famm_heuristic_func(ht, ctx):
            if ht == HeuristicType.GREEDY:
                return FAMMHyperHeuristics.greedy_minimize(ht, ctx)
            elif ht == HeuristicType.BALANCED:
                return FAMMHyperHeuristics.frustration_balance(ht, ctx)
            elif ht == HeuristicType.ADAPTIVE:
                return FAMMHyperHeuristics.adaptive_weight(ht, ctx)
            else:
                return FAMMHyperHeuristics.greedy_minimize(ht, ctx)

        result, heuristic = orchestrator.select_and_execute(
            ComponentType.FAMM_DELAY, famm_heuristic_func, context
        )

        print(f"Op {i+1}: {heuristic.value} -> delay={result['adjusted_delay']:.2f}, success={result['success']}")

    report = orchestrator.get_performance_report()
    print("\n=== FAMM Performance Report ===")
    print(json.dumps(report['components']['famm_delay'], indent=2))


def demo_pist_hyperheuristic():
    """Demonstrate PIST hyper-heuristic optimization."""
    print("\n=== PIST Hyper-Heuristic Demo ===")

    orchestrator = HyperHeuristicOrchestrator()

    # Simulate PIST operations
    for i in range(15):
        context = {
            'pos': {'k': i % 5, 't': i % 10},
            'phase': 'seismic' if i % 3 == 0 else 'grounded'
        }

        def pist_heuristic_func(ht, ctx):
            if ht == HeuristicType.GREEDY:
                return PISTHyperHeuristics.linear_move(ht, ctx)
            elif ht == HeuristicType.ADAPTIVE:
                return PISTHyperHeuristics.adaptive_move(ht, ctx)
            else:
                return PISTHyperHeuristics.resonance_jump(ht, ctx)

        result, heuristic = orchestrator.select_and_execute(
            ComponentType.PIST_MOVE, pist_heuristic_func, context
        )

        print(f"Op {i+1}: {heuristic.value} -> {result['move_type']}, pos={result['new_pos']}")

    report = orchestrator.get_performance_report()
    print("\n=== PIST Performance Report ===")
    print(json.dumps(report['components']['pist_move'], indent=2))


def demo_shim_selection_hyperheuristic():
    """Demonstrate infrastructure shim selection hyper-heuristic."""
    print("\n=== Shim Selection Hyper-Heuristic Demo ===")

    orchestrator = HyperHeuristicOrchestrator()

    # Simulate shim selection
    domains = ['math', 'compression', 'hardware', 'general']
    performance_history = {
        'math': {'math_prover_prior_metaprobe.py': 0.9, 'intense_math_modeling_router.py': 0.7},
        'compression': {'compression_signal_shaping_synthesis.py': 0.8}
    }

    for i in range(12):
        context = {
            'domain': domains[i % len(domains)],
            'task_type': 'optimization',
            'performance_history': performance_history
        }

        def shim_heuristic_func(ht, ctx):
            if ht == HeuristicType.GREEDY:
                return ShimSelectionHyperHeuristics.select_by_domain(ht, ctx)
            elif ht == HeuristicType.ADAPTIVE:
                return ShimSelectionHyperHeuristics.select_adaptive(ht, ctx)
            else:
                return ShimSelectionHyperHeuristics.select_by_performance(ht, ctx)

        result, heuristic = orchestrator.select_and_execute(
            ComponentType.SHIM_SELECTION, shim_heuristic_func, context
        )

        print(f"Op {i+1}: {heuristic.value} -> {result['selected_shim']}")

    report = orchestrator.get_performance_report()
    print("\n=== Shim Selection Performance Report ===")
    print(json.dumps(report['components']['shim_selection'], indent=2))


def demo_gpu_scheduling_hyperheuristic():
    """Demonstrate GPU scheduling hyper-heuristic."""
    print("\n=== GPU Scheduling Hyper-Heuristic Demo ===")

    orchestrator = HyperHeuristicOrchestrator()

    # Simulate GPU task scheduling
    for i in range(15):
        task_queue = [
            {'name': f'task_{i}_{j}', 'priority': (i+j) % 10, 'memory_required': 1000 + (i*j % 4000)}
            for j in range(3)
        ]

        context = {
            'task_queue': task_queue,
            'gpu_memory': 12000,
            'gpu_count': 1,
            'current_memory_usage': i * 500,
            'gpu_states': [{'load': 0.3 + (i % 5) * 0.1, 'memory': 6000}]
        }

        def gpu_heuristic_func(ht, ctx):
            if ht == HeuristicType.GREEDY:
                return GPUSchedulingHyperHeuristics.round_robin(ht, ctx)
            elif ht == HeuristicType.BALANCED:
                return GPUSchedulingHyperHeuristics.priority_based(ht, ctx)
            elif ht == HeuristicType.ADAPTIVE:
                return GPUSchedulingHyperHeuristics.memory_aware(ht, ctx)
            else:
                return GPUSchedulingHyperHeuristics.load_balancing(ht, ctx)

        result, heuristic = orchestrator.select_and_execute(
            ComponentType.GPU_SCHEDULING, gpu_heuristic_func, context
        )

        memory_util = result.get('memory_utilization', 0)
        scheduled = len([a for a in result.get('assigned', []) if a.get('gpu_id') is not None])
        print(f"Op {i+1}: {heuristic.value} -> {scheduled}/{len(task_queue)} tasks, mem={memory_util:.2%}")

    report = orchestrator.get_performance_report()
    print("\n=== GPU Scheduling Performance Report ===")
    print(json.dumps(report['components']['gpu_scheduling'], indent=2))


def demo_fpga_build_hyperheuristic():
    """Demonstrate FPGA build optimization hyper-heuristic."""
    print("\n=== FPGA Build Hyper-Heuristic Demo ===")

    orchestrator = HyperHeuristicOrchestrator()

    # Simulate FPGA build optimization
    for i in range(12):
        modules = [f'module_{j}' for j in range(5)]
        changed_files = [f'{m}.v' for m in modules if (i + hash(m)) % 3 == 0]

        context = {
            'modules': modules,
            'changed_files': changed_files,
            'build_cache': {f: f'cached_{f}' for f in changed_files if hash(f) % 2 == 0},
            'dependency_graph': {
                f'module_{j}': [f'module_{k}' for k in range(j)] if j > 0 else []
                for j in range(5)
            },
            'available_cores': 4,
            'resource_budget': {'LUT': 43200, 'FF': 86400, 'BRAM': 120},
            'module_resources': {
                f'module_{j}': {'LUT': 1000 * (j+1), 'FF': 2000 * (j+1), 'BRAM': j+1}
                for j in range(5)
            },
            'critical_paths': [['module_0', 'module_2', 'module_4'], ['module_1', 'module_3']]
        }

        def fpga_heuristic_func(ht, ctx):
            if ht == HeuristicType.GREEDY:
                return FPGABuildHyperHeuristics.incremental_build(ht, ctx)
            elif ht == HeuristicType.BALANCED:
                return FPGABuildHyperHeuristics.parallel_synthesis(ht, ctx)
            elif ht == HeuristicType.ADAPTIVE:
                return FPGABuildHyperHeuristics.resource_aware(ht, ctx)
            else:
                return FPGABuildHyperHeuristics.timing_driven(ht, ctx)

        result, heuristic = orchestrator.select_and_execute(
            ComponentType.FPGA_BUILD, fpga_heuristic_func, context
        )

        speedup = result.get('estimated_speedup', 0)
        success = result.get('success', False)
        print(f"Op {i+1}: {heuristic.value} -> speedup={speedup:.2f}x, success={success}")

    report = orchestrator.get_performance_report()
    print("\n=== FPGA Build Performance Report ===")
    print(json.dumps(report['components']['fpga_build'], indent=2))


if __name__ == "__main__":
    demo_famm_hyperheuristic()
    demo_pist_hyperheuristic()
    demo_shim_selection_hyperheuristic()
    demo_gpu_scheduling_hyperheuristic()
    demo_fpga_build_hyperheuristic()

    print("\n=== Global Statistics ===")
    orchestrator = HyperHeuristicOrchestrator()
    # Run demos to populate orchestrator
    demo_famm_hyperheuristic()
    demo_pist_hyperheuristic()
    demo_shim_selection_hyperheuristic()
    demo_gpu_scheduling_hyperheuristic()
    demo_fpga_build_hyperheuristic()

    # Note: In real usage, you'd use a single orchestrator instance across demos
