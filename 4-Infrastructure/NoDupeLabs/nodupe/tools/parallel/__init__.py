"""Parallel Tools Package.

This package provides parallel processing capabilities for NoDupeLabs.

Modules:
    parallel_logic: Core parallel processing logic
    parallel_tool: Tool integration for the tool system
    pools: Resource pooling utilities

Key Features:
    - Thread-based parallelism for I/O-bound tasks
    - Process-based parallelism for CPU-bound tasks
    - Sub-interpreter support for Python 3.14+
    - Free-threaded mode detection
    - Progress tracking
    - Resource pooling

Usage:
    from nodupe.tools.parallel import Parallel
    
    # Simple parallel map
    results = Parallel.map_parallel(lambda x: x*2, [1, 2, 3, 4])
    
    # With process pool
    results = Parallel.map_parallel(lambda x: x*2, [1, 2, 3, 4], use_processes=True)
"""

from .parallel_logic import (
    Parallel,
    ParallelError,
    ParallelProgress,
    parallel_map,
    parallel_filter,
    parallel_partition,
    parallel_starmap
)
from .parallel_tool import ParallelTool, register_tool
from .pools import (
    ObjectPool,
    ConnectionPool,
    WorkerPool,
    Pools,
    PoolError
)

__all__ = [
    # Core parallel processing
    'Parallel',
    'ParallelError',
    'ParallelProgress',
    'parallel_map',
    'parallel_filter',
    'parallel_partition',
    'parallel_starmap',
    # Tool integration
    'ParallelTool',
    'register_tool',
    # Pooling utilities
    'ObjectPool',
    'ConnectionPool',
    'WorkerPool',
    'Pools',
    'PoolError',
]
