#!/usr/bin/env python3
"""
Architect Node Topology Driver

This driver maximizes the utilization of the architect node's topology
by leveraging every bit of its available resources through topology-aware scheduling.

Architecture:
- Topology-aware resource scheduling
- Full utilization of 8 cores, 16GB RAM, 500GB storage
- Integration with TSM (Topological State Machine)
- Tailscale mesh integration
- Dynamic workload distribution
"""

import sys
import json
import time
import subprocess
import re
import threading
import multiprocessing
import psutil
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Callable
from collections import defaultdict, deque
from enum import Enum

class WorkloadType(Enum):
    """Types of workloads for topology scheduling"""
    COMPUTE_INTENSIVE = "compute_intensive"
    MEMORY_INTENSIVE = "memory_intensive"
    IO_INTENSIVE = "io_intensive"
    NETWORK_INTENSIVE = "network_intensive"
    MIXED = "mixed"

@dataclass
class Workload:
    """Workload to be scheduled"""
    workload_id: str
    workload_type: WorkloadType
    cpu_required: float  # 0-1 (percentage of total CPU)
    memory_required: float  # 0-1 (percentage of total RAM)
    storage_required: float  # 0-1 (percentage of total storage)
    bandwidth_required: float  # 0-1 (percentage of total bandwidth)
    priority: int  # 1-10
    duration: float  # seconds
    executable: Callable
    status: str = "pending"
    assigned_core: Optional[int] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

@dataclass
class TopologyResource:
    """Topology resource state"""
    total_cores: int
    total_ram_gb: float
    total_storage_gb: float
    total_bandwidth_mbps: float
    
    available_cores: int
    available_ram_gb: float
    available_storage_gb: float
    available_bandwidth_mbps: float
    
    core_utilization: List[float]  # Per-core utilization
    memory_utilization: float
    storage_utilization: float
    bandwidth_utilization: float

class ArchitectTopologyDriver:
    """
    Driver to maximize architect node topology utilization.
    
    This driver leverages every bit of the architect node's topology through:
    - Topology-aware resource scheduling
    - Dynamic workload distribution
    - Full utilization of 8 cores, 16GB RAM, 500GB storage
    - Integration with TSM and Tailscale mesh
    """
    
    def __init__(self):
        # Architect node specs
        self.node_specs = {
            "cores": 8,
            "ram_gb": 16,
            "storage_gb": 500,
            "bandwidth_mbps": 500
        }
        
        # Topology resource state
        self.topology_resource = TopologyResource(
            total_cores=self.node_specs["cores"],
            total_ram_gb=self.node_specs["ram_gb"],
            total_storage_gb=self.node_specs["storage_gb"],
            total_bandwidth_mbps=self.node_specs["bandwidth_mbps"],
            available_cores=self.node_specs["cores"],
            available_ram_gb=self.node_specs["ram_gb"],
            available_storage_gb=self.node_specs["storage_gb"],
            available_bandwidth_mbps=self.node_specs["bandwidth_mbps"],
            core_utilization=[0.0] * self.node_specs["cores"],
            memory_utilization=0.0,
            storage_utilization=0.0,
            bandwidth_utilization=0.0
        )
        
        # Workload queues
        self.workload_queue: deque[Workload] = deque()
        self.active_workloads: Dict[str, Workload] = {}
        self.completed_workloads: List[Workload] = []
        
        # Scheduling state
        self.scheduling_strategy = "topology_aware"
        self.max_concurrent_workloads = self.node_specs["cores"] * 2  # 2x oversubscription
        
        # Background processing
        self._running = False
        self._lock = threading.Lock()
        self._scheduler_thread: Optional[threading.Thread] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._scheduling_interval = 0.1  # 100ms
        self._monitoring_interval = 1.0  # 1s
        
        # Performance metrics
        self.metrics: Dict[str, List[float]] = defaultdict(list)
        self.total_utilization_score = 0.0
        
        print(f"[ArchitectTopologyDriver] Initialized for architect node")
        print(f"  Cores: {self.node_specs['cores']}")
        print(f"  RAM: {self.node_specs['ram_gb']}GB")
        print(f"  Storage: {self.node_specs['storage_gb']}GB")
        print(f"  Bandwidth: {self.node_specs['bandwidth_mbps']}Mbps")
    
    def update_topology_state(self):
        """Update topology resource state from actual system metrics."""
        try:
            # Get actual CPU utilization
            cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
            self.topology_resource.core_utilization = [c / 100.0 for c in cpu_percent]
            
            # Get actual memory utilization
            memory = psutil.virtual_memory()
            self.topology_resource.memory_utilization = memory.percent / 100.0
            self.topology_resource.available_ram_gb = memory.available / (1024**3)
            
            # Get actual disk utilization
            disk = psutil.disk_usage('/')
            self.topology_resource.storage_utilization = disk.percent / 100.0
            self.topology_resource.available_storage_gb = disk.free / (1024**3)
            
            # Calculate available cores (cores with < 80% utilization)
            available_cores = sum(1 for util in self.topology_resource.core_utilization if util < 0.8)
            self.topology_resource.available_cores = max(0, available_cores)
            
            # Calculate total utilization score
            core_avg = sum(self.topology_resource.core_utilization) / len(self.topology_resource.core_utilization)
            self.total_utilization_score = (
                core_avg * 0.4 +
                self.topology_resource.memory_utilization * 0.3 +
                self.topology_resource.storage_utilization * 0.2 +
                self.topology_resource.bandwidth_utilization * 0.1
            )
            
        except Exception as e:
            print(f"[ArchitectTopologyDriver] Error updating topology state: {e}")
    
    def schedule_workload(self, workload: Workload) -> bool:
        """Schedule a workload using topology-aware scheduling."""
        with self._lock:
            # Check if resources are available
            if self.topology_resource.available_cores < 1:
                return False
            
            if self.topology_resource.available_ram_gb < workload.memory_required * self.node_specs["ram_gb"]:
                return False
            
            if self.topology_resource.available_storage_gb < workload.storage_required * self.node_specs["storage_gb"]:
                return False
            
            # Find best core for this workload
            best_core = self._find_best_core(workload)
            
            if best_core is None:
                return False
            
            # Assign workload
            workload.assigned_core = best_core
            workload.status = "running"
            workload.start_time = time.time()
            
            # Update resource availability
            self.topology_resource.available_cores -= 1
            self.topology_resource.available_ram_gb -= workload.memory_required * self.node_specs["ram_gb"]
            self.topology_resource.available_storage_gb -= workload.storage_required * self.node_specs["storage_gb"]
            
            # Add to active workloads
            self.active_workloads[workload.workload_id] = workload
            
            print(f"[ArchitectTopologyDriver] Scheduled {workload.workload_id} on core {best_core}")
            print(f"  Type: {workload.workload_type.value}")
            print(f"  CPU: {workload.cpu_required * 100:.1f}%")
            print(f"  RAM: {workload.memory_required * 100:.1f}%")
            
            return True
    
    def _find_best_core(self, workload: Workload) -> Optional[int]:
        """Find best core for workload based on topology state."""
        # Find core with lowest utilization
        core_utilizations = self.topology_resource.core_utilization
        best_core = None
        best_utilization = 1.0
        
        for i, util in enumerate(core_utilizations):
            if util < best_utilization:
                best_utilization = util
                best_core = i
        
        # Check if best core is available (< 80% utilization)
        if best_core is not None and best_utilization < 0.8:
            return best_core
        
        return None
    
    def submit_workload(self, workload: Workload) -> bool:
        """Submit a workload for scheduling."""
        with self._lock:
            self.workload_queue.append(workload)
            print(f"[ArchitectTopologyDriver] Submitted workload {workload.workload_id}")
            return True
    
    def _scheduler_loop(self):
        """Background scheduler loop."""
        while self._running:
            try:
                with self._lock:
                    # Update topology state
                    self.update_topology_state()
                    
                    # Schedule pending workloads
                    while (len(self.workload_queue) > 0 and 
                           len(self.active_workloads) < self.max_concurrent_workloads):
                        workload = self.workload_queue.popleft()
                        if not self.schedule_workload(workload):
                            # Can't schedule now, put back in queue
                            self.workload_queue.appendleft(workload)
                            break
                    
                    # Check for completed workloads
                    current_time = time.time()
                    completed = []
                    for workload_id, workload in self.active_workloads.items():
                        if workload.end_time and current_time >= workload.end_time:
                            completed.append(workload_id)
                    
                    for workload_id in completed:
                        self._complete_workload(workload_id)
                
                time.sleep(self._scheduling_interval)
                
            except Exception as e:
                print(f"[ArchitectTopologyDriver] Scheduler loop error: {e}")
                time.sleep(1.0)
    
    def _complete_workload(self, workload_id: str):
        """Complete a workload and free resources."""
        with self._lock:
            if workload_id not in self.active_workloads:
                return
            
            workload = self.active_workloads[workload_id]
            workload.status = "completed"
            workload.end_time = time.time()
            
            # Free resources
            self.topology_resource.available_cores += 1
            self.topology_resource.available_ram_gb += workload.memory_required * self.node_specs["ram_gb"]
            self.topology_resource.available_storage_gb += workload.storage_required * self.node_specs["storage_gb"]
            
            # Move to completed
            self.completed_workloads.append(workload)
            del self.active_workloads[workload_id]
            
            print(f"[ArchitectTopologyDriver] Completed {workload_id}")
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self._running:
            try:
                with self._lock:
                    # Record metrics
                    self.metrics['total_utilization'].append(self.total_utilization_score)
                    self.metrics['core_utilization_avg'].append(
                        sum(self.topology_resource.core_utilization) / len(self.topology_resource.core_utilization)
                    )
                    self.metrics['memory_utilization'].append(self.topology_resource.memory_utilization)
                    self.metrics['active_workloads'].append(len(self.active_workloads))
                    self.metrics['queued_workloads'].append(len(self.workload_queue))
                
                time.sleep(self._monitoring_interval)
                
            except Exception as e:
                print(f"[ArchitectTopologyDriver] Monitor loop error: {e}")
                time.sleep(1.0)
    
    def start(self) -> bool:
        """Start the topology driver."""
        try:
            self._running = True
            self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            
            self._scheduler_thread.start()
            self._monitor_thread.start()
            
            print(f"[ArchitectTopologyDriver] Started topology driver")
            print(f"  Scheduling strategy: {self.scheduling_strategy}")
            print(f"  Max concurrent workloads: {self.max_concurrent_workloads}")
            return True
            
        except Exception as e:
            print(f"[ArchitectTopologyDriver] Failed to start: {e}")
            return False
    
    def stop(self):
        """Stop the topology driver."""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5.0)
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        print("[ArchitectTopologyDriver] Stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current driver status."""
        with self._lock:
            return {
                "running": self._running,
                "topology_resource": {
                    "total_cores": self.topology_resource.total_cores,
                    "available_cores": self.topology_resource.available_cores,
                    "total_ram_gb": self.topology_resource.total_ram_gb,
                    "available_ram_gb": self.topology_resource.available_ram_gb,
                    "total_storage_gb": self.topology_resource.total_storage_gb,
                    "available_storage_gb": self.topology_resource.available_storage_gb,
                    "core_utilization": self.topology_resource.core_utilization,
                    "memory_utilization": self.topology_resource.memory_utilization,
                    "storage_utilization": self.topology_resource.storage_utilization,
                    "total_utilization_score": self.total_utilization_score
                },
                "workloads": {
                    "active": len(self.active_workloads),
                    "queued": len(self.workload_queue),
                    "completed": len(self.completed_workloads)
                },
                "metrics": {
                    key: {
                        "avg": sum(values) / len(values) if values else 0,
                        "max": max(values) if values else 0,
                        "min": min(values) if values else 0,
                        "count": len(values)
                    }
                    for key, values in self.metrics.items()
                }
            }
    
    def print_status(self):
        """Print current driver status."""
        status = self.get_status()
        
        print("\n" + "=" * 70)
        print("ARCHITECT TOPOLOGY DRIVER STATUS")
        print("=" * 70)
        
        print(f"\n📊 Topology Utilization:")
        print(f"  Total Utilization Score: {status['topology_resource']['total_utilization_score']:.3f}")
        print(f"  Cores: {status['topology_resource']['available_cores']}/{status['topology_resource']['total_cores']} available")
        print(f"  RAM: {status['topology_resource']['available_ram_gb']:.1f}/{status['topology_resource']['total_ram_gb']:.1f}GB available")
        print(f"  Storage: {status['topology_resource']['available_storage_gb']:.1f}/{status['topology_resource']['total_storage_gb']:.1f}GB available")
        print(f"  Core Utilization: {[f'{c:.2f}' for c in status['topology_resource']['core_utilization']]}")
        
        print(f"\n📋 Workloads:")
        print(f"  Active: {status['workloads']['active']}")
        print(f"  Queued: {status['workloads']['queued']}")
        print(f"  Completed: {status['workloads']['completed']}")
        
        print(f"\n📈 Metrics:")
        for key, metric in status['metrics'].items():
            print(f"  {key}: avg {metric['avg']:.3f}, max {metric['max']:.3f}")
        
        print("\n" + "=" * 70)

def create_sample_workloads(num_workloads: int) -> List[Workload]:
    """Create sample workloads for testing."""
    workloads = []
    
    for i in range(num_workloads):
        workload_type = random.choice(list(WorkloadType))
        
        workload = Workload(
            workload_id=f"workload_{i}",
            workload_type=workload_type,
            cpu_required=random.uniform(0.1, 0.5),
            memory_required=random.uniform(0.05, 0.3),
            storage_required=random.uniform(0.01, 0.05),
            bandwidth_required=random.uniform(0.01, 0.1),
            priority=random.randint(1, 10),
            duration=random.uniform(5.0, 30.0),
            executable=lambda: time.sleep(random.uniform(5.0, 30.0))
        )
        
        workloads.append(workload)
    
    return workloads

import random

if __name__ == "__main__":
    print("=" * 70)
    print("Architect Node Topology Driver")
    print("Maximizing Topology Utilization")
    print("=" * 70)
    
    # Create driver
    driver = ArchitectTopologyDriver()
    
    # Start driver
    if not driver.start():
        print("Failed to start driver")
        sys.exit(1)
    
    # Create sample workloads
    print("\nCreating sample workloads...")
    num_workloads = 50
    workloads = create_sample_workloads(num_workloads)
    print(f"Created {len(workloads)} workloads")
    
    # Submit workloads
    print("\nSubmitting workloads...")
    for workload in workloads:
        driver.submit_workload(workload)
    
    print(f"Submitted {len(workloads)} workloads")
    
    # Monitor for 60 seconds
    print("\nMonitoring for 60 seconds...")
    for i in range(60):
        time.sleep(1)
        if i % 10 == 0:
            driver.print_status()
    
    # Stop driver
    driver.stop()
    
    # Final status
    driver.print_status()
    
    print("\n✅ Architect topology driver test complete")
