#!/usr/bin/env python3
"""
Swarm Execution Layer
Receives swarm recommendations and executes them with GPU acceleration support.
Integrates with EnhancedIntegratedSwarm to get prioritized tasks and execute them.
"""

import json
import logging
import subprocess
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    id: str
    description: str
    priority: float
    status: TaskStatus
    gpu_accelerated: bool
    estimated_cycles: int
    actual_cycles: int = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SwarmExecutionLayer:
    """
    Execution layer that receives swarm recommendations and executes them.
    Supports GPU acceleration for suitable tasks and tracks progress.
    """
    
    def __init__(self):
        self.tasks: List[Task] = []
        self.current_cycle = 0
        self.total_cycles = 0
        self.gpu_available = False
        self.gpu_type = None
        self.execution_log: List[Dict[str, Any]] = []
        
        # Check for GPU availability
        self._detect_gpu()
        
    def _detect_gpu(self):
        """Detect GPU availability and type."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.gpu_available = True
                self.gpu_type = result.stdout.strip()
                logger.info(f"GPU detected: {self.gpu_type}")
            else:
                logger.info("No NVIDIA GPU detected")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.info("GPU detection failed - assuming no GPU available")
            self.gpu_available = False
    
    def receive_swarm_recommendations(self, swarm_analysis: Dict[str, Any]) -> List[Task]:
        """
        Receive prioritized tasks from swarm analysis and convert to execution tasks.
        
        Args:
            swarm_analysis: Swarm analysis output containing prioritized tasks
            
        Returns:
            List of Task objects ready for execution
        """
        logger.info("Receiving swarm recommendations for execution...")
        
        # Extract prioritized tasks from swarm analysis
        prioritization = swarm_analysis.get("priority_state_tracking", {})
        current_priorities = prioritization.get("current_priorities", [])
        
        tasks = []
        for idx, priority_item in enumerate(current_priorities):
            task = Task(
                id=f"task_{idx}",
                description=priority_item.get("task", "Unknown task"),
                priority=priority_item.get("current_priority", 0.0),
                status=TaskStatus.PENDING,
                gpu_accelerated=False,
                estimated_cycles=5
            )
            tasks.append(task)
        
        self.tasks = tasks
        self.total_cycles = sum(task.estimated_cycles for task in tasks)
        
        logger.info(f"Received {len(tasks)} tasks, estimated {self.total_cycles} cycles")
        self._log_execution_event("recommendations_received", {"task_count": len(tasks), "total_cycles": self.total_cycles})
        
        return tasks
    
    def _should_use_gpu(self, _task_description: str) -> bool:
        """GPU suitability decision placeholder.
        Per AGENTS.md §6: branching decisions belong in Lean.
        TODO(lean-port): Route through bindserver once SwarmExecution endpoint exists.
        """
        return False
    
    def _estimate_task_cycles(self, _priority_item: Dict[str, Any]) -> int:
        """Cycle estimation placeholder.
        Per AGENTS.md §6: cost computation belongs in Lean.
        TODO(lean-port): Route through bindserver once SwarmExecution endpoint exists.
        """
        return 5
    
    def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a single task with optional GPU acceleration.
        
        Args:
            task: Task to execute
            
        Returns:
            Execution result
        """
        logger.info(f"Executing task: {task.description} (GPU: {task.gpu_accelerated})")
        task.status = TaskStatus.IN_PROGRESS
        
        start_time = time.time()
        
        try:
            # Simulate task execution (in real implementation, this would execute actual work)
            result = self._execute_task_impl(task)
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.actual_cycles = task.estimated_cycles  # In real implementation, track actual cycles
            
            elapsed_time = time.time() - start_time
            logger.info(f"Task completed in {elapsed_time:.2f}s")
            
            self._log_execution_event("task_completed", {
                "task_id": task.id,
                "description": task.description,
                "elapsed_time": elapsed_time,
                "gpu_used": task.gpu_accelerated
            })
            
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"Task failed: {e}")
            
            self._log_execution_event("task_failed", {
                "task_id": task.id,
                "error": str(e)
            })
            
            return {"error": str(e)}
    
    def _execute_task_impl(self, task: Task) -> Dict[str, Any]:
        """
        Implement actual task execution.
        This is a placeholder - real implementation would execute actual work.
        """
        # Simulate execution time based on estimated cycles
        cycle_time = 0.1  # seconds per cycle
        execution_time = task.estimated_cycles * cycle_time
        
        if task.gpu_accelerated and self.gpu_available:
            execution_time /= 4  # GPU acceleration
            logger.info(f"Using GPU acceleration for task")
        
        time.sleep(min(execution_time, 2.0))  # Cap at 2 seconds for demo
        
        return {
            "status": "completed",
            "cycles_used": task.estimated_cycles,
            "gpu_used": task.gpu_accelerated,
            "result": f"Task '{task.description}' executed successfully"
        }
    
    def execute_all_tasks(self) -> Dict[str, Any]:
        """
        Execute all tasks in priority order.
        
        Returns:
            Execution summary
        """
        logger.info(f"Starting execution of {len(self.tasks)} tasks...")
        
        start_time = time.time()
        completed = 0
        failed = 0
        
        # Sort tasks by priority (highest first)
        sorted_tasks = sorted(self.tasks, key=lambda t: t.priority, reverse=True)
        
        for task in sorted_tasks:
            self.current_cycle += 1
            
            result = self.execute_task(task)
            
            if task.status == TaskStatus.COMPLETED:
                completed += 1
            elif task.status == TaskStatus.FAILED:
                failed += 1
            
            # Check for swarm re-priorization every 5 cycles
            if self.current_cycle % 5 == 0:
                logger.info(f"Cycle {self.current_cycle}/{self.total_cycles} - Checking for swarm re-prioritization...")
                # In real implementation, would query swarm for updated priorities
        
        elapsed_time = time.time() - start_time
        
        summary = {
            "total_tasks": len(self.tasks),
            "completed": completed,
            "failed": failed,
            "total_cycles": self.current_cycle,
            "elapsed_time_seconds": elapsed_time,
            "gpu_available": self.gpu_available,
            "gpu_type": self.gpu_type
        }
        
        self._log_execution_event("execution_completed", summary)
        
        logger.info(f"Execution completed: {completed}/{len(self.tasks)} tasks successful in {elapsed_time:.2f}s")
        
        return summary
    
    def _log_execution_event(self, event_type: str, data: Dict[str, Any]):
        """Log execution events for swarm monitoring."""
        event = {
            "timestamp": time.time(),
            "cycle": self.current_cycle,
            "event_type": event_type,
            "data": data
        }
        self.execution_log.append(event)
    
    def get_execution_status(self) -> Dict[str, Any]:
        """Get current execution status."""
        return {
            "current_cycle": self.current_cycle,
            "total_cycles": self.total_cycles,
            "tasks_pending": sum(1 for t in self.tasks if t.status == TaskStatus.PENDING),
            "tasks_in_progress": sum(1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS),
            "tasks_completed": sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED),
            "tasks_failed": sum(1 for t in self.tasks if t.status == TaskStatus.FAILED),
            "gpu_available": self.gpu_available,
            "gpu_type": self.gpu_type
        }
    
    def save_execution_log(self, filepath: str):
        """Save execution log to file."""
        with open(filepath, 'w') as f:
            json.dump(self.execution_log, f, indent=2)
        logger.info(f"Execution log saved to {filepath}")


if __name__ == "__main__":
    # Demo execution layer
    from lean_unified_shim import LeanUnifiedShim
    from enhanced_integrated_swarm import EnhancedIntegratedSwarm
    
    logger.info("Initializing Swarm Execution Layer")
    
    # Get swarm recommendations
    swarm = EnhancedIntegratedSwarm()
    prioritization = swarm.perform_self_prioritization()
    
    # Initialize execution layer
    executor = SwarmExecutionLayer()
    
    # Receive and execute tasks
    tasks = executor.receive_swarm_recommendations(prioritization)
    
    print("\n" + "=" * 60)
    print("SWARM EXECUTION LAYER - TASK QUEUE")
    print("=" * 60)
    for task in tasks:
        print(f"  [{task.id}] {task.description}")
        print(f"      Priority: {task.priority:.2f}")
        print(f"      GPU Accelerated: {task.gpu_accelerated}")
        print(f"      Estimated Cycles: {task.estimated_cycles}")
        print(f"      Status: {task.status.value}")
    
    print("\n" + "=" * 60)
    print("EXECUTING TASKS")
    print("=" * 60)
    
    summary = executor.execute_all_tasks()
    
    print("\n" + "=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)
    print(f"  Total Tasks: {summary['total_tasks']}")
    print(f"  Completed: {summary['completed']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Total Cycles: {summary['total_cycles']}")
    print(f"  Elapsed Time: {summary['elapsed_time_seconds']:.2f}s")
    print(f"  GPU Available: {summary['gpu_available']}")
    print(f"  GPU Type: {summary['gpu_type']}")
    
    # Save execution log
    executor.save_execution_log("execution_log.json")
