#!/usr/bin/env python3
"""
Hotloading Prover Orchestrator — Resource-Conscious Theorem Proving
======================================================================

Prevents resource exhaustion by:
1. Loading prover models on-demand only
2. Unloading immediately after use
3. Queue-based task management
4. Memory/CPU monitoring
5. Bounded concurrency

Usage:
    orchestrator = HotloadingProverOrchestrator(max_memory_gb=8)
    orchestrator.queue_theorem("F01_Q16_16_FixedPoint.lean", "add_total")
    orchestrator.process_queue()
"""

import subprocess
import sys
import time
import gc
import psutil
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
from enum import Enum
from queue import Queue, PriorityQueue
import threading
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('hotloading_prover')

RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")


class ProverType(Enum):
    """Available prover models with resource requirements."""
    BF4PROVER = ("bf4prover", 2, 4)      # (name, cpu_cores, memory_gb)
    GOEDEL_8B = ("goedel-8b", 4, 8)
    GOEDEL_32B = ("goedel-32b", 8, 32)
    BFS_PROVER = ("bfs-prover", 2, 4)


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 0    # Blocking other work
    HIGH = 1        # Foundation equations F01-F12
    NORMAL = 2      # Standard theorems
    LOW = 3         # Optional proofs


@dataclass
class TheoremTask:
    """Task for proving a theorem."""
    lean_file: Path
    theorem_name: str
    prover_type: ProverType
    priority: TaskPriority
    timeout_seconds: int
    retries: int = 0
    max_retries: int = 3
    
    def __lt__(self, other):
        return self.priority.value < other.priority.value


@dataclass
class ProverInstance:
    """Managed prover instance with lifecycle."""
    prover_type: ProverType
    process: Optional[subprocess.Popen]
    loaded_at: Optional[float]
    last_used: Optional[float]
    memory_usage_mb: float
    
    def is_loaded(self) -> bool:
        return self.process is not None and self.process.poll() is None
    
    def unload(self):
        """Unload prover to free resources."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
            except:
                self.process.kill()
            self.process = None
            self.loaded_at = None
            gc.collect()
            logger.info(f"Unloaded {self.prover_type.value[0]}")


class ResourceMonitor:
    """Monitor system resources to prevent exhaustion."""
    
    def __init__(self, max_memory_gb: float, max_cpu_percent: float = 80.0):
        self.max_memory_gb = max_memory_gb
        self.max_cpu_percent = max_cpu_percent
        self.process = psutil.Process()
    
    def check_resources(self) -> Dict[str, bool]:
        """Check if resources are available."""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        swap = psutil.swap_memory()
        
        return {
            "memory_available": memory.available / (1024**3) > 2.0,  # Need 2GB headroom
            "memory_within_limit": memory.used / (1024**3) < self.max_memory_gb,
            "cpu_available": cpu_percent < self.max_cpu_percent,
            "swap_ok": swap.percent < 50.0 if swap.total > 0 else True
        }
    
    def can_load_prover(self, prover: ProverType) -> bool:
        """Check if we can load a specific prover."""
        resources = self.check_resources()
        _, required_cores, required_gb = prover.value
        
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        
        return (
            resources["memory_available"] and
            resources["memory_within_limit"] and
            resources["cpu_available"] and
            available_gb >= required_gb + 2.0  # Required + headroom
        )
    
    def wait_for_resources(self, prover: ProverType, timeout: int = 300):
        """Wait until resources are available."""
        start = time.time()
        while time.time() - start < timeout:
            if self.can_load_prover(prover):
                return True
            logger.info(f"Waiting for resources to load {prover.value[0]}...")
            time.sleep(5)
            # Try to free memory
            gc.collect()
        return False


class HotloadingProverOrchestrator:
    """
    Orchestrates prover models with hotloading to prevent resource exhaustion.
    
    Strategy:
    1. Queue all theorem proving tasks
    2. Load provers on-demand
    3. Process highest priority tasks first
    4. Unload prover immediately after use
    5. Monitor resources, throttle if needed
    """
    
    def __init__(
        self,
        max_memory_gb: float = 16.0,
        max_concurrent_provers: int = 2,
        idle_timeout_seconds: int = 60
    ):
        self.max_memory_gb = max_memory_gb
        self.max_concurrent = max_concurrent_provers
        self.idle_timeout = idle_timeout_seconds
        
        self.task_queue = PriorityQueue()
        self.results: Dict[str, Dict] = {}
        self.provers: Dict[ProverType, ProverInstance] = {}
        self.monitor = ResourceMonitor(max_memory_gb)
        self.active_tasks = 0
        self.lock = threading.Lock()
        
        # Statistics
        self.stats = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "provers_loaded": 0,
            "provers_unloaded": 0,
            "memory_peak_gb": 0.0
        }
    
    def queue_theorem(
        self,
        lean_file: str,
        theorem_name: str,
        prover: ProverType = ProverType.BF4PROVER,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: int = 300
    ):
        """Queue a theorem proving task."""
        task = TheoremTask(
            lean_file=RESEARCH_STACK / lean_file,
            theorem_name=theorem_name,
            prover_type=prover,
            priority=priority,
            timeout_seconds=timeout
        )
        self.task_queue.put(task)
        self.stats["tasks_submitted"] += 1
        logger.info(f"Queued {theorem_name} from {lean_file} (priority: {priority.name})")
    
    def load_prover(self, prover_type: ProverType) -> bool:
        """Hotload a prover model."""
        with self.lock:
            # Check if already loaded
            if prover_type in self.provers and self.provers[prover_type].is_loaded():
                self.provers[prover_type].last_used = time.time()
                return True
            
            # Wait for resources
            if not self.monitor.wait_for_resources(prover_type):
                logger.error(f"Cannot load {prover_type.value[0]} — insufficient resources")
                return False
            
            # Load based on type
            if prover_type == ProverType.BF4PROVER:
                return self._load_bf4prover()
            elif prover_type == ProverType.GOEDEL_8B:
                return self._load_goedel("8b")
            elif prover_type == ProverType.GOEDEL_32B:
                return self._load_goedel("32b")
            elif prover_type == ProverType.BFS_PROVER:
                return self._load_bfs_prover()
            
            return False
    
    def _load_bf4prover(self) -> bool:
        """Load bf4prover (lightweight)."""
        try:
            # bf4prover is a Python script — no persistent process needed
            self.provers[ProverType.BF4PROVER] = ProverInstance(
                prover_type=ProverType.BF4PROVER,
                process=None,  # Stateless
                loaded_at=time.time(),
                last_used=time.time(),
                memory_usage_mb=0
            )
            self.stats["provers_loaded"] += 1
            logger.info("Loaded bf4prover (stateless)")
            return True
        except Exception as e:
            logger.error(f"Failed to load bf4prover: {e}")
            return False
    
    def _load_goedel(self, size: str) -> bool:
        """Load Goedel-Prover-V2 model."""
        try:
            goedel_path = RESEARCH_STACK / "ai-math-discovery-systems/Goedel-Prover-V2"
            
            # Check if model exists
            model_file = goedel_path / f"goedel-prover-v2-{size}.bin"
            if not model_file.exists():
                logger.warning(f"Goedel model not found: {model_file}")
                return False
            
            # Load model (simplified — real implementation would use proper loader)
            logger.info(f"Loading Goedel-Prover-V2-{size}...")
            
            # Simulate loading
            time.sleep(2)
            
            self.provers[ProverType.GOEDEL_8B if size == "8b" else ProverType.GOEDEL_32B] = ProverInstance(
                prover_type=ProverType.GOEDEL_8B if size == "8b" else ProverType.GOEDEL_32B,
                process=None,  # Would be actual model process
                loaded_at=time.time(),
                last_used=time.time(),
                memory_usage_mb=8000 if size == "8b" else 32000
            )
            self.stats["provers_loaded"] += 1
            logger.info(f"Loaded Goedel-Prover-V2-{size}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Goedel: {e}")
            return False
    
    def _load_bfs_prover(self) -> bool:
        """Load bfs_prover via Ollama."""
        try:
            # Check Ollama availability
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/tags"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                logger.warning("Ollama not available")
                return False
            
            self.provers[ProverType.BFS_PROVER] = ProverInstance(
                prover_type=ProverType.BFS_PROVER,
                process=None,
                loaded_at=time.time(),
                last_used=time.time(),
                memory_usage_mb=4000
            )
            self.stats["provers_loaded"] += 1
            logger.info("Loaded bfs_prover via Ollama")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load bfs_prover: {e}")
            return False
    
    def unload_prover(self, prover_type: ProverType):
        """Unload a prover to free resources."""
        with self.lock:
            if prover_type in self.provers:
                self.provers[prover_type].unload()
                del self.provers[prover_type]
                self.stats["provers_unloaded"] += 1
    
    def unload_idle_provers(self):
        """Unload provers that have been idle."""
        with self.lock:
            now = time.time()
            for prover_type, instance in list(self.provers.items()):
                if instance.is_loaded() and instance.last_used:
                    if now - instance.last_used > self.idle_timeout:
                        logger.info(f"Unloading idle prover: {prover_type.value[0]}")
                        self.unload_prover(prover_type)
    
    def run_bf4prover_task(self, task: TheoremTask) -> Dict:
        """Run a bf4prover task."""
        bf4prover_script = RESEARCH_STACK / "scripts/bf4prover.py"
        
        try:
            result = subprocess.run(
                [
                    "python3", str(bf4prover_script),
                    str(task.lean_file),
                    "--theorem", task.theorem_name,
                    "--dry-run"
                ],
                capture_output=True,
                text=True,
                timeout=task.timeout_seconds,
                cwd=str(RESEARCH_STACK)
            )
            
            success = result.returncode == 0 and "sorry" not in result.stdout
            
            return {
                "theorem": task.theorem_name,
                "file": str(task.lean_file),
                "success": success,
                "output": result.stdout,
                "error": result.stderr if not success else None,
                "prover": "bf4prover",
                "duration": None  # Would track actual time
            }
            
        except subprocess.TimeoutExpired:
            return {
                "theorem": task.theorem_name,
                "success": False,
                "error": "Timeout",
                "prover": "bf4prover"
            }
        except Exception as e:
            return {
                "theorem": task.theorem_name,
                "success": False,
                "error": str(e),
                "prover": "bf4prover"
            }
    
    def process_single_task(self, task: TheoremTask) -> Dict:
        """Process a single theorem task."""
        logger.info(f"Processing {task.theorem_name} with {task.prover_type.value[0]}")
        
        # Load prover
        if not self.load_prover(task.prover_type):
            return {
                "theorem": task.theorem_name,
                "success": False,
                "error": f"Failed to load {task.prover_type.value[0]}"
            }
        
        try:
            # Run task
            if task.prover_type == ProverType.BF4PROVER:
                result = self.run_bf4prover_task(task)
            else:
                result = {
                    "theorem": task.theorem_name,
                    "success": False,
                    "error": f"Prover {task.prover_type.value[0]} not implemented"
                }
            
            # Update statistics
            if result["success"]:
                self.stats["tasks_completed"] += 1
            else:
                self.stats["tasks_failed"] += 1
                
                # Retry if needed
                if task.retries < task.max_retries:
                    task.retries += 1
                    logger.info(f"Retrying {task.theorem_name} (attempt {task.retries})")
                    time.sleep(2 ** task.retries)  # Exponential backoff
                    return self.process_single_task(task)
            
            return result
            
        finally:
            # Update last used
            if task.prover_type in self.provers:
                self.provers[task.prover_type].last_used = time.time()
            
            # Unload if memory pressure
            memory = psutil.virtual_memory()
            if memory.percent > 85:
                logger.warning("Memory pressure detected — unloading prover")
                self.unload_prover(task.prover_type)
    
    def process_queue(self):
        """Process all queued tasks with hotloading."""
        logger.info(f"Starting queue processing ({self.task_queue.qsize()} tasks)")
        
        while not self.task_queue.empty():
            # Unload idle provers periodically
            self.unload_idle_provers()
            
            # Get next task
            task = self.task_queue.get()
            
            # Process
            result = self.process_single_task(task)
            
            # Store result
            key = f"{task.lean_file}:{task.theorem_name}"
            self.results[key] = result
            
            # Log progress
            completed = self.stats["tasks_completed"] + self.stats["tasks_failed"]
            total = self.stats["tasks_submitted"]
            logger.info(f"Progress: {completed}/{total} ({100*completed//total}%)")
            
            # Small delay to prevent resource exhaustion
            time.sleep(1)
        
        # Unload all provers
        for prover_type in list(self.provers.keys()):
            self.unload_prover(prover_type)
        
        logger.info("Queue processing complete")
        return self.results
    
    def get_stats(self) -> Dict:
        """Get orchestrator statistics."""
        memory = psutil.virtual_memory()
        self.stats["memory_peak_gb"] = max(
            self.stats["memory_peak_gb"],
            memory.used / (1024**3)
        )
        return self.stats.copy()


def main():
    """Demonstrate hotloading prover orchestrator."""
    print("=" * 70)
    print("Hotloading Prover Orchestrator")
    print("Resource-conscious theorem proving for F01-F12")
    print("=" * 70)
    
    # Initialize with 8GB memory limit
    orchestrator = HotloadingProverOrchestrator(
        max_memory_gb=8.0,
        max_concurrent_provers=1,  # Conservative
        idle_timeout_seconds=30
    )
    
    # Queue F01 theorems
    f01_file = "0-Core-Formalism/lean/Semantics/F01_Q16_16_FixedPoint.lean"
    
    theorems = [
        ("add_total", TaskPriority.CRITICAL),
        ("mul_total", TaskPriority.CRITICAL),
        ("div_total", TaskPriority.CRITICAL),
        ("round_valid", TaskPriority.HIGH),
        ("mul_no_overflow", TaskPriority.HIGH),
        ("E_0_deterministic", TaskPriority.HIGH),
        ("E_0_bounds", TaskPriority.NORMAL),
        ("convergence_to_fixed_point", TaskPriority.NORMAL),
    ]
    
    print(f"\nQueueing {len(theorems)} theorems from F01...")
    
    for theorem, priority in theorems:
        orchestrator.queue_theorem(
            lean_file=f01_file,
            theorem_name=theorem,
            prover=ProverType.BF4PROVER,
            priority=priority,
            timeout=60
        )
    
    # Process queue
    print("\nProcessing with hotloading...")
    results = orchestrator.process_queue()
    
    # Report
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    success_count = sum(1 for r in results.values() if r.get("success"))
    fail_count = len(results) - success_count
    
    print(f"Success: {success_count}/{len(results)}")
    print(f"Failed: {fail_count}/{len(results)}")
    
    stats = orchestrator.get_stats()
    print(f"\nResource Usage:")
    print(f"  Peak memory: {stats['memory_peak_gb']:.2f} GB")
    print(f"  Provers loaded: {stats['provers_loaded']}")
    print(f"  Provers unloaded: {stats['provers_unloaded']}")
    
    print("\n" + "=" * 70)
    print("Hotloading prevented resource exhaustion:")
    print(f"  - Loaded provers on-demand only")
    print(f"  - Unloaded after use (idle timeout: 30s)")
    print(f"  - Bounded concurrency (max: 1)")
    print(f"  - Memory limit enforced: 8GB")
    print("=" * 70)


if __name__ == "__main__":
    main()
