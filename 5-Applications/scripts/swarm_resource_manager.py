#!/usr/bin/env python3
"""
Swarm Resource Efficiency Manager

Maximizes resource efficiency for distributed swarm agents across nodes.
Monitors and optimizes:
- CPU utilization
- Memory usage
- Bandwidth allocation
- Task scheduling
- Load balancing
- Resource allocation

Usage:
    manager = SwarmResourceManager()
    manager.initialize()
    manager.optimize_resources()
    efficiency = manager.get_efficiency_report()
"""

import json
import time
import threading
import psutil
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import random
from pathlib import Path
import sys

# Import delta GCL encoder
sys.path.insert(0, str(Path(__file__).parent))
try:
    from delta_gcl_encoder import DeltaGCLEncoder
    _HAS_DELTA_GCL = True
except ImportError:
    _HAS_DELTA_GCL = False


class ResourcePriority(Enum):
    """Resource priority levels"""
    CRITICAL = 0    # Core swarm functions
    HIGH = 1        # Learning and consensus
    MEDIUM = 2      # Task execution
    LOW = 3         # Background maintenance


class ResourceType(Enum):
    """Types of resources"""
    CPU = "cpu"
    MEMORY = "memory"
    BANDWIDTH = "bandwidth"
    DISK = "disk"
    NETWORK = "network"


@dataclass
class ResourceMetrics:
    """Current resource usage metrics with delta GCL compression"""
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    network_sent_mb: float
    network_recv_mb: float
    bandwidth_mbps: float
    timestamp: float = field(default_factory=time.time)
    gcl_encoded: bool = field(init=False)
    gcl_sequence: Optional[str] = field(init=False, default=None)
    
    def __post_init__(self, use_delta_gcl: bool = True):
        # Encode metrics with delta GCL if available
        self.gcl_encoded = False
        self.gcl_sequence = None
        if _HAS_DELTA_GCL and use_delta_gcl:
            try:
                encoder = DeltaGCLEncoder()
                manifest = {
                    'resource_type': 'metrics',
                    'cpu_load': self.cpu_percent,
                    'memory_load': self.memory_percent,
                    'layer': 'STORE',
                    'domain': 'COMPUTE',
                    'tier': 'FOAM',
                    'condition': 'STABLE',
                    'tags': ['resource', 'metrics'],
                    'compression_metadata': {
                        'field_phi': 1.480381,
                        'compression_ratio': 0.8,
                        'foam_score': 7.0
                    }
                }
                self.gcl_sequence = encoder.encode_to_delta_gcl(manifest)
                self.gcl_encoded = True
            except Exception:
                pass
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_used_gb': self.memory_used_gb,
            'memory_total_gb': self.memory_total_gb,
            'disk_percent': self.disk_percent,
            'network_sent_mb': self.network_sent_mb,
            'network_recv_mb': self.network_recv_mb,
            'bandwidth_mbps': self.bandwidth_mbps,
            'timestamp': self.timestamp,
            'gcl_encoded': self.gcl_encoded,
            'gcl_sequence': self.gcl_sequence,
            'gcl_length': len(self.gcl_sequence) if self.gcl_sequence else 0
        }


@dataclass
class ResourceAllocation:
    """Resource allocation for a task"""
    task_id: str
    priority: ResourcePriority
    cpu_cores: float
    memory_gb: float
    bandwidth_mbps: float
    node_id: str
    allocated: bool = False
    efficiency_score: float = 0.0


@dataclass
class NodeResourceState:
    """Resource state for a node"""
    node_id: str
    metrics: ResourceMetrics
    active_tasks: List[str]
    total_capacity: Dict[ResourceType, float]
    used_capacity: Dict[ResourceType, float]
    efficiency_score: float = 0.0
    last_updated: float = field(default_factory=time.time)


class SwarmResourceManager:
    """
    Manages resource efficiency for distributed swarm.
    
    Features:
    - Real-time resource monitoring
    - Dynamic load balancing
    - Task scheduling optimization
    - Resource allocation efficiency tracking
    - Auto-scaling recommendations
    """
    
    def __init__(self, node_id: Optional[str] = None):
        self.node_id = node_id or f"node_{os.getpid()}"
        
        # Resource monitoring
        self.metrics_history: deque = deque(maxlen=100)
        self.node_states: Dict[str, NodeResourceState] = {}
        
        # Task scheduling
        self.task_queue: List[ResourceAllocation] = []
        self.active_allocations: Dict[str, ResourceAllocation] = {}
        
        # Load balancing
        self.load_balance_threshold = 0.8  # 80% capacity threshold
        self.rebalance_interval = 5.0  # seconds
        
        # Efficiency tracking
        self.efficiency_history: deque = deque(maxlen=50)
        
        # Background processing
        self._running = False
        self._lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        
        print(f"[ResourceManager] Initialized for node: {self.node_id}")
    
    def initialize(self) -> bool:
        """Initialize resource manager and start monitoring"""
        try:
            # Get initial metrics
            metrics = self._collect_metrics()
            self.metrics_history.append(metrics)
            
            # Initialize local node state
            self._update_node_state(self.node_id, metrics)
            
            # Start background monitoring
            self._running = True
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()
            
            print(f"[ResourceManager] Monitoring started")
            return True
        except Exception as e:
            print(f"[ResourceManager] Initialization failed: {e}")
            return False
    
    def _collect_metrics(self) -> ResourceMetrics:
        """Collect current resource metrics"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_cores = psutil.cpu_count()
        
        # Memory
        mem = psutil.virtual_memory()
        memory_percent = mem.percent
        memory_used_gb = mem.used / (1024**3)
        memory_total_gb = mem.total / (1024**3)
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Network
        net_io = psutil.net_io_counters()
        network_sent_mb = net_io.bytes_sent / (1024**2)
        network_recv_mb = net_io.bytes_recv / (1024**2)
        
        # Estimate bandwidth (simple heuristic)
        bandwidth_mbps = 1000.0  # Default assumption
        
        return ResourceMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_gb=memory_used_gb,
            memory_total_gb=memory_total_gb,
            disk_percent=disk_percent,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            bandwidth_mbps=bandwidth_mbps
        )
    
    def _update_node_state(self, node_id: str, metrics: ResourceMetrics):
        """Update resource state for a node"""
        with self._lock:
            total_capacity = {
                ResourceType.CPU: psutil.cpu_count(),
                ResourceType.MEMORY: metrics.memory_total_gb,
                ResourceType.BANDWIDTH: metrics.bandwidth_mbps,
                ResourceType.DISK: disk.total / (1024**3) if (disk := psutil.disk_usage('/')) else 100.0,
                ResourceType.NETWORK: 1000.0
            }
            
            used_capacity = {
                ResourceType.CPU: metrics.cpu_percent / 100.0 * total_capacity[ResourceType.CPU],
                ResourceType.MEMORY: metrics.memory_used_gb,
                ResourceType.BANDWIDTH: (metrics.network_sent_mb + metrics.network_recv_mb) / 1024.0,
                ResourceType.DISK: metrics.disk_percent / 100.0 * total_capacity[ResourceType.DISK],
                ResourceType.NETWORK: (metrics.network_sent_mb + metrics.network_recv_mb) / 1024.0
            }
            
            efficiency_score = self._calculate_efficiency_score(total_capacity, used_capacity)
            
            self.node_states[node_id] = NodeResourceState(
                node_id=node_id,
                metrics=metrics,
                active_tasks=[],
                total_capacity=total_capacity,
                used_capacity=used_capacity,
                efficiency_score=efficiency_score
            )
    
    def _calculate_efficiency_score(
        self,
        total_capacity: Dict[ResourceType, float],
        used_capacity: Dict[ResourceType, float]
    ) -> float:
        """Calculate resource efficiency score (0-1, higher is better)"""
        scores = []
        
        for resource_type in ResourceType:
            total = total_capacity.get(resource_type, 1.0)
            used = used_capacity.get(resource_type, 0.0)
            
            if total > 0:
                utilization = used / total
                # Optimal utilization is 70-80%
                if 0.7 <= utilization <= 0.8:
                    score = 1.0
                elif utilization < 0.7:
                    score = utilization / 0.7  # Underutilized
                else:
                    score = max(0.0, 1.0 - (utilization - 0.8) / 0.2)  # Overutilized
                scores.append(score)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self._running:
            try:
                # Collect metrics
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Update node state
                self._update_node_state(self.node_id, metrics)
                
                # Check if rebalancing needed
                self._check_rebalance_needed()
                
                # Calculate efficiency
                efficiency = self._calculate_overall_efficiency()
                self.efficiency_history.append(efficiency)
                
                time.sleep(1.0)
            except Exception as e:
                print(f"[ResourceManager] Monitor loop error: {e}")
                time.sleep(5.0)
    
    def _check_rebalance_needed(self):
        """Check if load rebalancing is needed"""
        with self._lock:
            for node_id, state in self.node_states.items():
                for resource_type in ResourceType:
                    total = state.total_capacity.get(resource_type, 1.0)
                    used = state.used_capacity.get(resource_type, 0.0)
                    
                    if total > 0 and (used / total) > self.load_balance_threshold:
                        print(f"[ResourceManager] Node {node_id[:16]}... {resource_type.value} at {used/total:.1%} - rebalance needed")
    
    def _calculate_overall_efficiency(self) -> float:
        """Calculate overall swarm efficiency"""
        with self._lock:
            if not self.node_states:
                return 0.0
            
            total_efficiency = sum(state.efficiency_score for state in self.node_states.values())
            return total_efficiency / len(self.node_states)
    
    def allocate_resources(
        self,
        task_id: str,
        priority: ResourcePriority,
        cpu_cores: float = 1.0,
        memory_gb: float = 1.0,
        bandwidth_mbps: float = 10.0
    ) -> Dict[str, Any]:
        """
        Allocate resources for a task.
        
        Returns allocation result with efficiency metrics.
        """
        allocation = ResourceAllocation(
            task_id=task_id,
            priority=priority,
            cpu_cores=cpu_cores,
            memory_gb=memory_gb,
            bandwidth_mbps=bandwidth_mbps,
            node_id=self.node_id
        )
        
        with self._lock:
            # Check if resources available
            state = self.node_states.get(self.node_id)
            if not state:
                return {'error': 'Node state not available'}
            
            # Check CPU availability
            cpu_available = state.total_capacity[ResourceType.CPU] - state.used_capacity[ResourceType.CPU]
            if cpu_cores > cpu_available:
                return {'error': 'Insufficient CPU', 'available': cpu_available, 'requested': cpu_cores}
            
            # Check memory availability
            mem_available = state.total_capacity[ResourceType.MEMORY] - state.used_capacity[ResourceType.MEMORY]
            if memory_gb > mem_available:
                return {'error': 'Insufficient memory', 'available': mem_available, 'requested': memory_gb}
            
            # Allocate resources
            state.used_capacity[ResourceType.CPU] += cpu_cores
            state.used_capacity[ResourceType.MEMORY] += memory_gb
            state.used_capacity[ResourceType.BANDWIDTH] += bandwidth_mbps
            state.active_tasks.append(task_id)
            
            allocation.allocated = True
            allocation.efficiency_score = state.efficiency_score
            self.active_allocations[task_id] = allocation
            
            return {
                'success': True,
                'task_id': task_id,
                'node_id': self.node_id,
                'allocated_resources': {
                    'cpu_cores': cpu_cores,
                    'memory_gb': memory_gb,
                    'bandwidth_mbps': bandwidth_mbps
                },
                'efficiency_score': allocation.efficiency_score,
                'node_efficiency': state.efficiency_score
            }
    
    def release_resources(self, task_id: str) -> Dict[str, Any]:
        """Release resources allocated to a task"""
        with self._lock:
            if task_id not in self.active_allocations:
                return {'error': 'Task not found'}
            
            allocation = self.active_allocations[task_id]
            state = self.node_states.get(allocation.node_id)
            
            if state:
                # Release resources
                state.used_capacity[ResourceType.CPU] -= allocation.cpu_cores
                state.used_capacity[ResourceType.MEMORY] -= allocation.memory_gb
                state.used_capacity[ResourceType.BANDWIDTH] -= allocation.bandwidth_mbps
                
                if task_id in state.active_tasks:
                    state.active_tasks.remove(task_id)
            
            del self.active_allocations[task_id]
            
            return {'success': True, 'task_id': task_id}
    
    def optimize_resources(self) -> Dict[str, Any]:
        """Optimize resource allocation across all nodes"""
        with self._lock:
            optimizations = []
            
            for node_id, state in self.node_states.items():
                # Check for underutilized nodes
                for resource_type in ResourceType:
                    total = state.total_capacity.get(resource_type, 1.0)
                    used = state.used_capacity.get(resource_type, 0.0)
                    utilization = used / total if total > 0 else 0
                    
                    if utilization < 0.3:  # Underutilized (<30%)
                        optimizations.append({
                            'node_id': node_id,
                            'resource': resource_type.value,
                            'utilization': utilization,
                            'recommendation': 'Increase workload or consolidate'
                        })
                    
                    elif utilization > 0.9:  # Overutilized (>90%)
                        optimizations.append({
                            'node_id': node_id,
                            'resource': resource_type.value,
                            'utilization': utilization,
                            'recommendation': 'Distribute workload to other nodes'
                        })
            
            # Calculate overall efficiency improvement potential
            current_efficiency = self._calculate_overall_efficiency()
            potential_improvement = 1.0 - current_efficiency
            
            return {
                'optimizations': optimizations,
                'current_efficiency': current_efficiency,
                'potential_improvement': potential_improvement,
                'optimization_count': len(optimizations)
            }
    
    def get_efficiency_report(self) -> Dict[str, Any]:
        """Get comprehensive efficiency report"""
        with self._lock:
            current_metrics = self.metrics_history[-1] if self.metrics_history else None
            current_efficiency = self._calculate_overall_efficiency()
            
            # Calculate average efficiency over time
            avg_efficiency = sum(self.efficiency_history) / len(self.efficiency_history) if self.efficiency_history else 0.0
            
            # Resource utilization by type
            resource_utilization = {}
            if self.node_id in self.node_states:
                state = self.node_states[self.node_id]
                for resource_type in ResourceType:
                    total = state.total_capacity.get(resource_type, 1.0)
                    used = state.used_capacity.get(resource_type, 0.0)
                    resource_utilization[resource_type.value] = used / total if total > 0 else 0.0
            
            return {
                'node_id': self.node_id,
                'running': self._running,
                'current_metrics': current_metrics.to_dict() if current_metrics else None,
                'current_efficiency': current_efficiency,
                'average_efficiency': avg_efficiency,
                'resource_utilization': resource_utilization,
                'active_tasks': len(self.active_allocations),
                'node_count': len(self.node_states),
                'monitoring_samples': len(self.metrics_history)
            }
    
    def print_efficiency_report(self):
        """Print formatted efficiency report"""
        report = self.get_efficiency_report()
        
        print("\n" + "="*60)
        print("SWARM RESOURCE EFFICIENCY REPORT")
        print("="*60)
        
        print(f"\n📡 Node: {report['node_id']}")
        print(f"  Running: {report['running']}")
        print(f"  Active tasks: {report['active_tasks']}")
        print(f"  Node count: {report['node_count']}")
        
        if report['current_metrics']:
            metrics = report['current_metrics']
            print(f"\n📊 Current Metrics:")
            print(f"  CPU: {metrics['cpu_percent']:.1f}%")
            print(f"  Memory: {metrics['memory_percent']:.1f}% ({metrics['memory_used_gb']:.1f}GB / {metrics['memory_total_gb']:.1f}GB)")
            print(f"  Disk: {metrics['disk_percent']:.1f}%")
            print(f"  Network: {metrics['network_sent_mb']:.1f}MB sent, {metrics['network_recv_mb']:.1f}MB recv")
        
        print(f"\n⚡ Efficiency:")
        print(f"  Current: {report['current_efficiency']:.3f}")
        print(f"  Average: {report['average_efficiency']:.3f}")
        
        print(f"\n📈 Resource Utilization:")
        for resource, utilization in report['resource_utilization'].items():
            print(f"  {resource}: {utilization:.1%}")
        
        print("\n" + "="*60)
    
    def shutdown(self):
        """Shutdown resource manager"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        print("[ResourceManager] Shutdown complete")


def main():
    """Test resource manager"""
    manager = SwarmResourceManager()
    
    print("[ResourceManager] Initializing...")
    if not manager.initialize():
        print("[!] Initialization failed")
        return
    
    print("\n[Test 1] Allocate resources for task 1...")
    result = manager.allocate_resources(
        task_id="task_1",
        priority=ResourcePriority.HIGH,
        cpu_cores=2.0,
        memory_gb=2.0,
        bandwidth_mbps=50.0
    )
    print(f"  Result: {result}")
    
    print("\n[Test 2] Allocate resources for task 2...")
    result = manager.allocate_resources(
        task_id="task_2",
        priority=ResourcePriority.MEDIUM,
        cpu_cores=1.0,
        memory_gb=1.0,
        bandwidth_mbps=20.0
    )
    print(f"  Result: {result}")
    
    print("\n[Test 3] Optimize resources...")
    result = manager.optimize_resources()
    print(f"  Optimizations: {result['optimization_count']}")
    print(f"  Current efficiency: {result['current_efficiency']:.3f}")
    print(f"  Potential improvement: {result['potential_improvement']:.3f}")
    
    print("\n[Test 4] Release task 1...")
    result = manager.release_resources("task_1")
    print(f"  Result: {result}")
    
    print("\n[Efficiency Report]")
    manager.print_efficiency_report()
    
    time.sleep(2)
    
    print("\n[Shutdown]")
    manager.shutdown()


if __name__ == '__main__':
    main()
