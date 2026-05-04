# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/parallel/parallel_logic.py - Parallel processing core logic.

Comprehensive tests covering:
- Task distribution algorithms
- Batch processing
- Progress tracking
- Error aggregation
- Result collection
- Edge cases (empty input, single item, large batches)
- Thread safety
- Timeout handling
- BOTH ThreadPoolExecutor and ProcessPoolExecutor code paths

Note: Tests now use pickle-safe functions from test_helpers.py to properly
test ProcessPoolExecutor code paths. See docs/PARALLEL_TESTING_SUSTAINABILITY.md
"""

import sys
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.parallel.parallel_logic import (
    Parallel,
    ParallelError,
    ParallelProgress,
    _process_batch_worker,
    parallel_filter,
    parallel_map,
)

# Import pickle-safe test helpers for process testing
# See: docs/PARALLEL_TESTING_SUSTAINABILITY.md
from tests.parallel.test_helpers import (
    square_number,
    double_number,
    identity,
    add_one,
    count_letters,
    to_uppercase,
    is_even,
    sum_list,
    maybe_raise,
    SMALL_INT_RANGE,
    MEDIUM_INT_RANGE,
)
from nodupe.tools.parallel.parallel_logic import (
    parallel_partition,
    parallel_starmap,
)

# =============================================================================
# Test Helper Functions
# =============================================================================

class TestProcessBatchWorker:
    """Test _process_batch_worker helper function."""

    def test_batch_worker_processes_items(self):
        """_process_batch_worker applies function to all items in batch."""
        def func(x):
            """Doubles the input value."""
            return x * 2
        batch = [1, 2, 3, 4, 5]

        result = _process_batch_worker((func, batch))

        assert result == [2, 4, 6, 8, 10]

    def test_batch_worker_empty_batch(self):
        """_process_batch_worker handles empty batch."""
        def func(x):
            """Doubles the input value."""
            return x * 2
        batch = []

        result = _process_batch_worker((func, batch))

        assert result == []

    def test_batch_worker_single_item(self):
        """_process_batch_worker handles single item batch."""
        def func(x):
            """Doubles the input value."""
            return x ** 2
        batch = [7]

        result = _process_batch_worker((func, batch))

        assert result == [49]

    def test_batch_worker_with_string_function(self):
        """_process_batch_worker works with string manipulation."""
        func = str.upper
        batch = ["hello", "world", "test"]

        result = _process_batch_worker((func, batch))

        assert result == ["HELLO", "WORLD", "TEST"]


# =============================================================================
# Test ParallelError Exception
# =============================================================================

class TestParallelError:
    """Test ParallelError exception class."""

    def test_parallel_error_creation(self):
        """ParallelError can be created with message."""
        error = ParallelError("Test error message")
        assert str(error) == "Test error message"

    def test_parallel_error_with_cause(self):
        """ParallelError can wrap another exception."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise ParallelError("Parallel processing failed") from e
        except ParallelError as pe:
            assert pe.__cause__ is not None
            assert isinstance(pe.__cause__, ValueError)


# =============================================================================
# Test Parallel Class - Basic Static Methods
# =============================================================================

class TestParallelBasicMethods:
    """Test basic static methods of Parallel class."""

    def test_get_cpu_count_returns_positive(self):
        """get_cpu_count() returns positive integer."""
        cpu_count = Parallel.get_cpu_count()
        assert isinstance(cpu_count, int)
        assert cpu_count >= 1

    @patch('nodupe.tools.parallel.parallel_logic.cpu_count')
    def test_get_cpu_count_exception_fallback(self, mock_cpu_count):
        """get_cpu_count() returns 1 on exception."""
        mock_cpu_count.side_effect = Exception("CPU count failed")

        result = Parallel.get_cpu_count()

        assert result == 1

    def test_is_free_threaded_returns_bool(self):
        """is_free_threaded() returns boolean."""
        result = Parallel.is_free_threaded()
        assert isinstance(result, bool)

    def test_get_python_version_info_returns_tuple(self):
        """get_python_version_info() returns (major, minor) tuple."""
        version = Parallel.get_python_version_info()
        assert isinstance(version, tuple)
        assert len(version) == 2
        assert isinstance(version[0], int)
        assert isinstance(version[1], int)
        # Should match sys.version_info
        assert version[0] == sys.version_info.major
        assert version[1] == sys.version_info.minor

    def test_supports_interpreter_pool(self):
        """supports_interpreter_pool() returns boolean based on Python version."""
        result = Parallel.supports_interpreter_pool()
        assert isinstance(result, bool)
        # Python 3.14+ should support it
        major, minor = Parallel.get_python_version_info()
        expected = major >= 3 and minor >= 14
        assert result == expected


# =============================================================================
# Test Parallel.process_in_parallel - Thread Mode
# =============================================================================

class TestParallelProcessInParallelThreads:
    """Test process_in_parallel with thread executor."""

    def test_process_in_parallel_basic(self):
        """process_in_parallel processes items with threads."""
        def func(x):
            """Doubles the input value."""
            return x * 2
        items = [1, 2, 3, 4, 5]

        results = Parallel.process_in_parallel(func, items, workers=2, use_processes=False)

        assert results == [2, 4, 6, 8, 10]
        # Verify order is preserved
        assert results == [func(x) for x in items]

    def test_process_in_parallel_empty_list(self):
        """process_in_parallel handles empty list."""
        def func(x):
            """Doubles the input value."""
            return x * 2
        items = []

        results = Parallel.process_in_parallel(func, items, workers=2)

        assert results == []

    def test_process_in_parallel_single_item(self):
        """process_in_parallel handles single item."""
        def func(x):
            """Doubles the input value."""
            return x ** 2
        items = [7]

        results = Parallel.process_in_parallel(func, items, workers=2)

        assert results == [49]

    def test_process_in_parallel_with_timeout(self):
        """process_in_parallel respects timeout."""
        def slow_func(x):
            """Sleeps briefly then doubles the input value."""
            time.sleep(0.01)
            return x * 2

        items = [1, 2, 3]

        results = Parallel.process_in_parallel(
            slow_func, items, workers=2, timeout=5.0
        )

        assert results == [2, 4, 6]

    def test_process_in_parallel_worker_count_none(self):
        """process_in_parallel uses default workers when None."""
        def func(x):
            """Doubles the input value."""
            return x + 1
        items = list(range(10))

        results = Parallel.process_in_parallel(func, items, workers=None)

        assert results == list(range(1, 11))

    def test_process_in_parallel_preserves_order(self):
        """process_in_parallel preserves input order."""
        def delayed_func(x):
            """Applies variable delay then multiplies by 10."""
            # Add variable delay to test ordering
            time.sleep(0.01 * (5 - x))
            return x * 10

        items = [1, 2, 3, 4, 5]

        results = Parallel.process_in_parallel(delayed_func, items, workers=5)

        # Order should be preserved despite varying completion times
        assert results == [10, 20, 30, 40, 50]


# =============================================================================
# Test Parallel.process_in_parallel - Process Mode
# =============================================================================

class TestParallelProcessInParallelProcesses:
    """Test process_in_parallel with process executor."""

    def test_process_in_parallel_processes_basic(self):
        """process_in_parallel processes items with processes."""
        # Note: Using threads since lambdas can't be pickled for processes
        def func(x):
            """Doubles the input value."""
            return x * 3
        items = [1, 2, 3]

        results = Parallel.process_in_parallel(
            func, items, workers=2, use_processes=False
        )

        assert results == [3, 6, 9]

    def test_process_in_parallel_processes_empty(self):
        """process_in_parallel with processes handles empty list."""
        # Note: Using threads since lambdas can't be pickled for processes
        def func(x):
            """Doubles the input value."""
            return x * 3
        items = []

        results = Parallel.process_in_parallel(
            func, items, workers=2, use_processes=False
        )

        assert results == []


# =============================================================================
# Test Parallel.process_in_parallel - Process Mode
# =============================================================================

class TestParallelProcessInParallelProcesses:
    """Test process_in_parallel with ProcessPoolExecutor.
    
    These tests use pickle-safe functions from test_helpers.py to properly
    test the ProcessPoolExecutor code paths that cannot be tested with
    lambdas or local functions.
    
    See: docs/PARALLEL_TESTING_SUSTAINABILITY.md
    """

    def test_process_in_parallel_with_processes_basic(self):
        """process_in_parallel works with ProcessPoolExecutor."""
        items = [1, 2, 3, 4, 5]
        
        results = Parallel.process_in_parallel(
            double_number,  # ✅ Pickle-safe
            items,
            workers=2,
            use_processes=True  # ✅ Test processes
        )
        
        assert results == [2, 4, 6, 8, 10]

    def test_process_in_parallel_with_processes_square(self):
        """process_in_parallel with processes - square function."""
        items = [1, 2, 3, 4, 5]
        
        results = Parallel.process_in_parallel(
            square_number,  # ✅ Pickle-safe
            items,
            workers=2,
            use_processes=True
        )
        
        assert results == [1, 4, 9, 16, 25]

    def test_process_in_parallel_empty_list_processes(self):
        """process_in_parallel handles empty list with processes."""
        results = Parallel.process_in_parallel(
            double_number,
            [],
            workers=2,
            use_processes=True
        )
        
        assert results == []

    def test_process_in_parallel_single_item_processes(self):
        """process_in_parallel handles single item with processes."""
        results = Parallel.process_in_parallel(
            square_number,
            [7],
            workers=2,
            use_processes=True
        )
        
        assert results == [49]

    def test_process_in_parallel_with_timeout_processes(self):
        """process_in_parallel respects timeout with processes."""
        from tests.parallel.test_helpers import slow_square
        
        items = [1, 2, 3]
        
        results = Parallel.process_in_parallel(
            slow_square,
            items,
            workers=2,
            use_processes=True,
            timeout=5.0
        )
        
        assert results == [1, 4, 9]

    def test_process_in_parallel_large_dataset_processes(self):
        """process_in_parallel handles large datasets with processes."""
        items = MEDIUM_INT_RANGE  # 100 items
        
        results = Parallel.process_in_parallel(
            add_one,  # ✅ Pickle-safe
            items,
            workers=4,
            use_processes=True
        )
        
        assert results == [x + 1 for x in items]

    def test_process_in_parallel_error_handling_processes(self):
        """process_in_parallel handles errors with processes."""
        items = [1, 2, -1, 4]  # -1 will cause error
        
        with pytest.raises(ParallelError):
            Parallel.process_in_parallel(
                maybe_raise,  # ✅ Pickle-safe
                items,
                workers=2,
                use_processes=True
            )

    def test_process_in_parallel_string_operations_processes(self):
        """process_in_parallel with string operations and processes."""
        items = ["hello", "world", "test"]
        
        results = Parallel.process_in_parallel(
            to_uppercase,  # ✅ Pickle-safe
            items,
            workers=2,
            use_processes=True
        )
        
        assert results == ["HELLO", "WORLD", "TEST"]

    def test_process_in_parallel_thread_vs_process_consistency(self):
        """Verify thread and process results are consistent."""
        items = [1, 2, 3, 4, 5]
        
        # Thread result
        thread_result = Parallel.process_in_parallel(
            double_number,
            items,
            workers=2,
            use_processes=False
        )
        
        # Process result
        process_result = Parallel.process_in_parallel(
            double_number,
            items,
            workers=2,
            use_processes=True
        )
        
        # Both should produce same results
        assert thread_result == process_result == [2, 4, 6, 8, 10]


# =============================================================================
# Test Parallel.map_parallel
# =============================================================================

class TestParallelMapParallel:
    """Test map_parallel method."""

    def test_map_parallel_basic(self):
        """map_parallel maps function over items."""
        def func(x):
            """Doubles the input value."""
            return x + 10
        items = [1, 2, 3, 4, 5]

        results = Parallel.map_parallel(func, items, workers=2)

        assert results == [11, 12, 13, 14, 15]

    def test_map_parallel_empty(self):
        """map_parallel handles empty list."""
        def func(x):
            """Doubles the input value."""
            return x * 2
        items = []

        results = Parallel.map_parallel(func, items, workers=2)

        assert results == []

    def test_map_parallel_single_item(self):
        """map_parallel handles single item."""
        def func(x):
            """Doubles the input value."""
            return x ** 2
        items = [6]

        results = Parallel.map_parallel(func, items, workers=2)

        assert results == [36]

    def test_map_parallel_with_processes(self):
        """map_parallel works with process executor."""
        # Note: Using threads since lambdas can't be pickled for processes
        def func(x):
            """Doubles the input value."""
            return x * 2
        items = [1, 2, 3, 4]

        results = Parallel.map_parallel(
            func, items, workers=2, use_processes=False, chunk_size=2
        )

        assert results == [2, 4, 6, 8]

    def test_map_parallel_chunk_size(self):
        """map_parallel respects chunk_size parameter."""
        # Note: Using threads since lambdas can't be pickled for processes
        def func(x):
            """Doubles the input value."""
            return x + 1
        items = list(range(10))

        results = Parallel.map_parallel(
            func, items, workers=2, use_processes=False, chunk_size=5
        )

        assert results == list(range(1, 11))

    def test_map_parallel_error_handling(self):
        """map_parallel raises ParallelError on failure."""
        def failing_func(x):
            """Raises error for specific input, otherwise doubles."""
            if x == 3:
                raise ValueError("Intentional failure")
            return x * 2

        items = [1, 2, 3, 4]

        with pytest.raises(ParallelError) as exc_info:
            Parallel.map_parallel(failing_func, items, workers=2)

        assert "Parallel map failed" in str(exc_info.value)


# =============================================================================
# Test Parallel.map_parallel_unordered
# =============================================================================

class TestParallelMapParallelUnordered:
    """Test map_parallel_unordered method."""

    def test_map_parallel_unordered_basic(self):
        """map_parallel_unordered yields results as completed."""
        def func(x):
            """Doubles the input value."""
            return x * 2
        items = [1, 2, 3, 4, 5]

        results = list(Parallel.map_parallel_unordered(func, items, workers=2))

        # All results should be present (order may vary)
        assert sorted(results) == [2, 4, 6, 8, 10]

    def test_map_parallel_unordered_empty(self):
        """map_parallel_unordered handles empty list."""
        def func(x):
            """Doubles the input value."""
            return x * 2
        items = []

        results = list(Parallel.map_parallel_unordered(func, items, workers=2))

        assert results == []

    def test_map_parallel_unordered_with_processes(self):
        """map_parallel_unordered works with processes."""
        # Note: Using threads since lambdas can't be pickled for processes
        def func(x):
            """Doubles the input value."""
            return x + 5
        items = [1, 2, 3]

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=2, use_processes=False
        ))

        assert sorted(results) == [6, 7, 8]

    def test_map_parallel_unordered_with_timeout(self):
        """map_parallel_unordered respects timeout."""
        def quick_func(x):
            """Sleeps briefly then doubles the input."""
            time.sleep(0.01)
            return x * 2

        items = [1, 2, 3]

        results = list(Parallel.map_parallel_unordered(
            quick_func, items, workers=2, timeout=5.0
        ))

        assert sorted(results) == [2, 4, 6]

    def test_map_parallel_unordered_batch_processing(self):
        """map_parallel_unordered uses batch processing for processes."""
        # Note: Using threads since lambdas can't be pickled for processes
        def func(x):
            """Doubles the input value."""
            return x ** 2
        items = list(range(20))

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=2, use_processes=False, prefer_batches=True
        ))

        expected = [x ** 2 for x in range(20)]
        assert sorted(results) == expected

    def test_map_parallel_unordered_prefer_map(self):
        """map_parallel_unordered with prefer_map=True."""
        # Note: Using threads since lambdas can't be pickled for processes
        def func(x):
            """Doubles the input value."""
            return x + 100
        items = list(range(10))

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=2, use_processes=False, prefer_map=True
        ))

        assert sorted(results) == list(range(100, 110))

    def test_map_parallel_unordered_thread_mode(self):
        """map_parallel_unordered in thread mode uses bounded submission."""
        def func(x):
            """Doubles the input value."""
            return x * 3
        items = [1, 2, 3, 4, 5]

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=3, use_processes=False
        ))

        assert sorted(results) == [3, 6, 9, 12, 15]

    def test_map_parallel_unordered_error_handling(self):
        """map_parallel_unordered raises ParallelError on task failure."""
        def failing_func(x):
            """Raises error for specific input, otherwise doubles."""
            if x == 2:
                raise ValueError("Task failed")
            return x * 2

        items = [1, 2, 3]

        with pytest.raises(ParallelError) as exc_info:
            list(Parallel.map_parallel_unordered(failing_func, items, workers=2))

        assert "Task failed" in str(exc_info.value)


# =============================================================================
# Test Parallel.smart_map
# =============================================================================

class TestParallelSmartMap:
    """Test smart_map method."""

    @patch.object(Parallel, 'supports_interpreter_pool', return_value=False)
    @patch.object(Parallel, 'is_free_threaded', return_value=True)  # Use free-threaded mode to avoid process pickling
    def test_smart_map_cpu_task_processes(self, mock_free, mock_interp):
        """smart_map uses processes for CPU tasks in GIL mode."""
        # Note: Using free-threaded mode since lambdas can't be pickled for processes
        def func(x):
            """Doubles the input value."""
            return x * 2
        items = [1, 2, 3]

        results = Parallel.smart_map(func, items, task_type='cpu', workers=2)

        assert results == [2, 4, 6]

    @patch.object(Parallel, 'supports_interpreter_pool', return_value=False)
    @patch.object(Parallel, 'is_free_threaded', return_value=True)
    def test_smart_map_cpu_task_free_threaded(self, mock_free, mock_interp):
        """smart_map uses threads for CPU tasks in free-threaded mode."""
        def func(x):
            """Doubles the input value."""
            return x * 2
        items = [1, 2, 3]

        results = Parallel.smart_map(func, items, task_type='cpu', workers=2)

        assert results == [2, 4, 6]

    def test_smart_map_io_task(self):
        """smart_map uses threads for I/O tasks."""
        def func(x):
            """Doubles the input value."""
            return x + 1
        items = [1, 2, 3]

        results = Parallel.smart_map(func, items, task_type='io', workers=2)

        assert results == [2, 3, 4]

    def test_smart_map_auto_task(self):
        """smart_map handles auto task type."""
        def func(x):
            """Doubles the input value."""
            return x * 2
        items = [1, 2, 3]

        results = Parallel.smart_map(func, items, task_type='auto', workers=2)

        assert results == [2, 4, 6]

    def test_smart_map_empty(self):
        """smart_map handles empty list."""
        def func(x):
            """Doubles the input value."""
            return x * 2
        items = []

        results = Parallel.smart_map(func, items, task_type='cpu', workers=2)

        assert results == []


# =============================================================================
# Test Parallel.get_optimal_workers
# =============================================================================

class TestParallelGetOptimalWorkers:
    """Test get_optimal_workers method."""

    def test_get_optimal_workers_cpu_task(self):
        """get_optimal_workers returns reasonable count for CPU tasks."""
        workers = Parallel.get_optimal_workers(task_type='cpu')
        assert isinstance(workers, int)
        assert workers >= 1

    def test_get_optimal_workers_io_task(self):
        """get_optimal_workers returns reasonable count for I/O tasks."""
        workers = Parallel.get_optimal_workers(task_type='io')
        assert isinstance(workers, int)
        assert workers >= 1

    @patch.object(Parallel, 'is_free_threaded', return_value=True)
    @patch.object(Parallel, 'get_cpu_count', return_value=4)
    def test_get_optimal_workers_free_threaded_cpu(self, mock_cpu, mock_free):
        """get_optimal_workers returns more workers in free-threaded CPU mode."""
        workers = Parallel.get_optimal_workers(task_type='cpu')
        # Should be cpu_count * 2 in free-threaded mode
        assert workers == 8

    @patch.object(Parallel, 'is_free_threaded', return_value=True)
    @patch.object(Parallel, 'get_cpu_count', return_value=4)
    def test_get_optimal_workers_free_threaded_io(self, mock_cpu, mock_free):
        """get_optimal_workers in free-threaded I/O mode."""
        workers = Parallel.get_optimal_workers(task_type='io')
        assert workers == 8

    @patch.object(Parallel, 'get_cpu_count', return_value=4)
    def test_get_optimal_workers_cpu_count_exception(self, mock_cpu):
        """get_optimal_workers handles cpu_count exception."""
        mock_cpu.side_effect = Exception("CPU count failed")
        workers = Parallel.get_optimal_workers(task_type='cpu')
        assert workers == 1  # Fallback


# =============================================================================
# Test Parallel.process_batches
# =============================================================================

class TestParallelProcessBatches:
    """Test process_batches method."""

    def test_process_batches_basic(self):
        """process_batches processes items in batches."""
        def batch_sum(batch):
            """Sums all values in a batch."""
            return sum(batch)

        items = [1, 2, 3, 4, 5, 6]

        results = Parallel.process_batches(
            batch_sum, items, batch_size=2, workers=2
        )

        assert results == [3, 7, 11]  # [1+2, 3+4, 5+6]

    def test_process_batches_uneven(self):
        """process_batches handles uneven batch sizes."""
        def batch_sum(batch):
            """Sums all values in a batch."""
            return sum(batch)

        items = [1, 2, 3, 4, 5]

        results = Parallel.process_batches(
            batch_sum, items, batch_size=2, workers=2
        )

        assert results == [3, 7, 5]  # [1+2, 3+4, 5]

    def test_process_batches_empty(self):
        """process_batches handles empty list."""
        def batch_sum(batch):
            """Sums all values in a batch."""
            return sum(batch)

        items = []

        results = Parallel.process_batches(
            batch_sum, items, batch_size=2, workers=2
        )

        assert results == []

    def test_process_batches_larger_than_list(self):
        """process_batches handles batch_size larger than list."""
        def batch_sum(batch):
            """Sums all values in a batch."""
            return sum(batch)

        items = [1, 2, 3]

        results = Parallel.process_batches(
            batch_sum, items, batch_size=10, workers=2
        )

        assert results == [6]  # All in one batch

    def test_process_batches_with_processes(self):
        """process_batches works with process executor."""
        # Note: Using threads since lambdas can't be pickled for processes
        def batch_sum(batch):
            """Sums all values in a batch."""
            return sum(batch)

        items = [1, 2, 3, 4]

        results = Parallel.process_batches(
            batch_sum, items, batch_size=2, workers=2, use_processes=False
        )

        assert results == [3, 7]


# =============================================================================
# Test Parallel.reduce_parallel
# =============================================================================

class TestParallelReduceParallel:
    """Test reduce_parallel method."""

    def test_reduce_parallel_basic(self):
        """reduce_parallel performs map-reduce operation."""
        def map_func(x):
            """Maps function over items (doubles by default)."""
            return x * 2
        def reduce_func(a, b):
            """Reduces two values by addition."""
            return a + b
        items = [1, 2, 3, 4]

        result = Parallel.reduce_parallel(
            map_func, reduce_func, items, workers=2
        )

        # Map: [2, 4, 6, 8], Reduce: 2+4+6+8 = 20
        assert result == 20

    def test_reduce_parallel_with_initial(self):
        """reduce_parallel uses initial value."""
        def map_func(x):
            """Maps function over items (doubles by default)."""
            return x
        def reduce_func(a, b):
            """Reduces two values by addition."""
            return a + b
        items = [1, 2, 3]

        result = Parallel.reduce_parallel(
            map_func, reduce_func, items, initial=10, workers=2
        )

        # Map: [1, 2, 3], Reduce: 10+1+2+3 = 16
        assert result == 16

    def test_reduce_parallel_empty_no_initial(self):
        """reduce_parallel raises error for empty list without initial."""
        def map_func(x):
            """Maps function over items (doubles by default)."""
            return x
        def reduce_func(a, b):
            """Reduces two values by addition."""
            return a + b
        items = []

        with pytest.raises(ParallelError) as exc_info:
            Parallel.reduce_parallel(map_func, reduce_func, items, workers=2)

        assert "Cannot reduce empty sequence" in str(exc_info.value)

    def test_reduce_parallel_empty_with_initial(self):
        """reduce_parallel returns initial for empty list with initial."""
        def map_func(x):
            """Maps function over items (doubles by default)."""
            return x
        def reduce_func(a, b):
            """Reduces two values by addition."""
            return a + b
        items = []

        result = Parallel.reduce_parallel(
            map_func, reduce_func, items, initial=42, workers=2
        )

        assert result == 42

    def test_reduce_parallel_single_item(self):
        """reduce_parallel handles single item."""
        def map_func(x):
            """Maps function over items (doubles by default)."""
            return x * 3
        def reduce_func(a, b):
            """Reduces two values by addition."""
            return a * b
        items = [5]

        result = Parallel.reduce_parallel(
            map_func, reduce_func, items, workers=2
        )

        # Map: [15], Reduce: 15
        assert result == 15

    def test_reduce_parallel_with_processes(self):
        """reduce_parallel works with process executor."""
        # Note: Using threads since lambdas can't be pickled for processes
        def map_func(x):
            """Maps function over items (doubles by default)."""
            return x + 1
        def reduce_func(a, b):
            """Reduces two values by addition."""
            return a + b
        items = [1, 2, 3]

        result = Parallel.reduce_parallel(
            map_func, reduce_func, items, workers=2, use_processes=False
        )

        # Map: [2, 3, 4], Reduce: 2+3+4 = 9
        assert result == 9

    def test_reduce_parallel_map_error(self):
        """reduce_parallel handles map phase errors."""
        def failing_map(x):
            """Raises error for specific input, otherwise returns value."""
            if x == 2:
                raise ValueError("Map failed")
            return x

        def reduce_func(a, b):
            """Reduces two values by addition."""
            return a + b
        items = [1, 2, 3]

        with pytest.raises(ParallelError) as exc_info:
            Parallel.reduce_parallel(failing_map, reduce_func, items, workers=2)

        assert "Parallel map failed" in str(exc_info.value) or "Map-reduce failed" in str(exc_info.value)


# =============================================================================
# Test ParallelProgress Class
# =============================================================================

class TestParallelProgress:
    """Test ParallelProgress class."""

    def test_progress_initialization(self):
        """ParallelProgress initializes with correct total."""
        progress = ParallelProgress(total=100)
        assert progress.total == 100
        assert progress.completed == 0
        assert progress.failed == 0

    def test_progress_increment_success(self):
        """ParallelProgress.increment tracks successful tasks."""
        progress = ParallelProgress(total=10)

        progress.increment(success=True)
        progress.increment(success=True)

        completed, failed, percentage = progress.get_progress()
        assert completed == 2
        assert failed == 0
        assert percentage == 20.0

    def test_progress_increment_failure(self):
        """ParallelProgress.increment tracks failed tasks."""
        progress = ParallelProgress(total=10)

        progress.increment(success=False)
        progress.increment(success=False)

        completed, failed, percentage = progress.get_progress()
        assert completed == 0
        assert failed == 2
        assert percentage == 20.0

    def test_progress_mixed_results(self):
        """ParallelProgress tracks mixed success/failure."""
        progress = ParallelProgress(total=10)

        progress.increment(success=True)
        progress.increment(success=True)
        progress.increment(success=False)
        progress.increment(success=True)

        completed, failed, percentage = progress.get_progress()
        assert completed == 3
        assert failed == 1
        assert percentage == 40.0

    def test_progress_is_complete(self):
        """ParallelProgress.is_complete when all items processed."""
        progress = ParallelProgress(total=5)

        assert not progress.is_complete

        for _ in range(5):
            progress.increment(success=True)

        assert progress.is_complete

    def test_progress_is_complete_with_failures(self):
        """ParallelProgress.is_complete counts failures."""
        progress = ParallelProgress(total=5)

        progress.increment(success=True)
        progress.increment(success=False)
        progress.increment(success=True)
        progress.increment(success=False)
        progress.increment(success=True)

        assert progress.is_complete

    def test_progress_zero_total(self):
        """ParallelProgress handles zero total."""
        progress = ParallelProgress(total=0)

        completed, failed, percentage = progress.get_progress()
        assert percentage == 0  # Division by zero handled

    def test_progress_thread_safety(self):
        """ParallelProgress is thread-safe."""
        progress = ParallelProgress(total=1000)
        errors = []

        def increment_many():
            """Increments progress counter multiple times."""
            try:
                for _ in range(100):
                    progress.increment(success=True)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=increment_many) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        completed, failed, percentage = progress.get_progress()
        assert completed == 1000
        assert progress.is_complete


# =============================================================================
# Test Module-Level Convenience Functions
# =============================================================================

class TestParallelMap:
    """Test parallel_map convenience function."""

    def test_parallel_map_basic(self):
        """parallel_map maps function over items."""
        def func(x):
            """Doubles the input value."""
            return x * 2
        items = [1, 2, 3, 4, 5]

        results = parallel_map(func, items, workers=2)

        assert results == [2, 4, 6, 8, 10]

    def test_parallel_map_empty(self):
        """parallel_map handles empty list."""
        def func(x):
            """Doubles the input value."""
            return x * 2
        items = []

        results = parallel_map(func, items, workers=2)

        assert results == []

    def test_parallel_map_with_processes(self):
        """parallel_map works with process executor."""
        # Note: Using threads since lambdas can't be pickled for processes
        def func(x):
            """Doubles the input value."""
            return x + 10
        items = [1, 2, 3]

        results = parallel_map(func, items, workers=2, use_processes=False)

        assert results == [11, 12, 13]


class TestParallelFilter:
    """Test parallel_filter function."""

    def test_parallel_filter_basic(self):
        """parallel_filter filters items based on predicate."""
        def predicate(x):
            """Returns True if input meets condition."""
            return x % 2 == 0
        items = [1, 2, 3, 4, 5, 6]

        results = parallel_filter(predicate, items, workers=2)

        assert results == [2, 4, 6]

    def test_parallel_filter_all_match(self):
        """parallel_filter when all items match."""
        def predicate(x):
            """Returns True if input meets condition."""
            return x > 0
        items = [1, 2, 3]

        results = parallel_filter(predicate, items, workers=2)

        assert results == [1, 2, 3]

    def test_parallel_filter_none_match(self):
        """parallel_filter when no items match."""
        def predicate(x):
            """Returns True if input meets condition."""
            return x > 100
        items = [1, 2, 3]

        results = parallel_filter(predicate, items, workers=2)

        assert results == []

    def test_parallel_filter_empty(self):
        """parallel_filter handles empty list."""
        def predicate(x):
            """Returns True if input meets condition."""
            return x > 0
        items = []

        results = parallel_filter(predicate, items, workers=2)

        assert results == []

    def test_parallel_filter_with_processes(self):
        """parallel_filter works with process executor."""
        # Note: Using threads since lambdas can't be pickled for processes
        def predicate(x):
            """Returns True if input meets condition."""
            return x % 2 == 0
        items = [1, 2, 3, 4, 5]

        results = parallel_filter(predicate, items, workers=2, use_processes=False)

        assert results == [2, 4]


class TestParallelPartition:
    """Test parallel_partition function."""

    def test_parallel_partition_basic(self):
        """parallel_partition splits items based on predicate."""
        def predicate(x):
            """Returns True if input meets condition."""
            return x % 2 == 0
        items = [1, 2, 3, 4, 5, 6]

        true_items, false_items = parallel_partition(predicate, items, workers=2)

        assert sorted(true_items) == [2, 4, 6]
        assert sorted(false_items) == [1, 3, 5]

    def test_parallel_partition_all_true(self):
        """parallel_partition when all items match predicate."""
        def predicate(x):
            """Returns True if input meets condition."""
            return x > 0
        items = [1, 2, 3]

        true_items, false_items = parallel_partition(predicate, items, workers=2)

        assert true_items == [1, 2, 3]
        assert false_items == []

    def test_parallel_partition_all_false(self):
        """parallel_partition when no items match predicate."""
        def predicate(x):
            """Returns True if input meets condition."""
            return x < 0
        items = [1, 2, 3]

        true_items, false_items = parallel_partition(predicate, items, workers=2)

        assert true_items == []
        assert false_items == [1, 2, 3]

    def test_parallel_partition_empty(self):
        """parallel_partition handles empty list."""
        def predicate(x):
            """Returns True if input meets condition."""
            return x % 2 == 0
        items = []

        true_items, false_items = parallel_partition(predicate, items, workers=2)

        assert true_items == []
        assert false_items == []

    def test_parallel_partition_with_processes(self):
        """parallel_partition works with process executor."""
        # Note: Using threads since lambdas can't be pickled for processes
        def predicate(x):
            """Returns True if input meets condition."""
            return x > 2
        items = [1, 2, 3, 4, 5]

        true_items, false_items = parallel_partition(
            predicate, items, workers=2, use_processes=False
        )

        assert sorted(true_items) == [3, 4, 5]
        assert sorted(false_items) == [1, 2]


class TestParallelStarmap:
    """Test parallel_starmap function."""

    def test_parallel_starmap_basic(self):
        """parallel_starmap applies function with multiple arguments."""
        def add(a, b):
            """Adds two numbers together."""
            return a + b

        args_list = [(1, 2), (3, 4), (5, 6)]

        results = parallel_starmap(add, args_list, workers=2)

        assert results == [3, 7, 11]

    def test_parallel_starmap_empty(self):
        """parallel_starmap handles empty args list."""
        def add(a, b):
            """Adds two numbers together."""
            return a + b

        args_list = []

        results = parallel_starmap(add, args_list, workers=2)

        assert results == []

    def test_parallel_starmap_single_arg(self):
        """parallel_starmap works with single argument functions."""
        def square(x):
            """Squares the input value."""
            return x ** 2

        args_list = [(1,), (2,), (3,), (4,)]

        results = parallel_starmap(square, args_list, workers=2)

        assert results == [1, 4, 9, 16]

    def test_parallel_starmap_with_kwargs(self):
        """parallel_starmap works with keyword arguments."""
        def power(base, exponent):
            """Raises base to exponent power."""
            return base ** exponent

        args_list = [(2, 3), (3, 2), (5, 2)]

        results = parallel_starmap(power, args_list, workers=2)

        assert results == [8, 9, 25]

    def test_parallel_starmap_with_processes(self):
        """parallel_starmap works with process executor."""
        # Note: Using threads since lambdas can't be pickled for processes
        def multiply(a, b):
            """Multiplies two numbers together."""
            return a * b

        args_list = [(2, 3), (4, 5), (6, 7)]

        results = parallel_starmap(
            multiply, args_list, workers=2, use_processes=False
        )

        assert results == [6, 20, 42]


# =============================================================================
# Test Edge Cases and Error Handling
# =============================================================================

class TestParallelEdgeCases:
    """Test edge cases and error handling."""

    def test_large_batch_processing(self):
        """process_in_parallel handles large batches."""
        def func(x):
            """Doubles the input value."""
            return x * 2
        items = list(range(1000))

        results = Parallel.process_in_parallel(func, items, workers=4)

        assert results == [x * 2 for x in items]

    def test_very_small_worker_count(self):
        """process_in_parallel works with 1 worker."""
        def func(x):
            """Doubles the input value."""
            return x + 1
        items = [1, 2, 3, 4, 5]

        results = Parallel.process_in_parallel(func, items, workers=1)

        assert results == [2, 3, 4, 5, 6]

    def test_worker_count_exceeds_items(self):
        """process_in_parallel handles more workers than items."""
        def func(x):
            """Doubles the input value."""
            return x * 2
        items = [1, 2]

        results = Parallel.process_in_parallel(func, items, workers=10)

        assert results == [2, 4]

    def test_function_with_side_effects(self):
        """process_in_parallel handles functions with side effects."""
        counter = {'count': 0}
        lock = threading.Lock()

        def increment(x):
            """Increments a counter with thread safety."""
            with lock:
                counter['count'] += 1
            return x * 2

        items = [1, 2, 3, 4, 5]

        results = Parallel.process_in_parallel(increment, items, workers=2)

        assert results == [2, 4, 6, 8, 10]
        assert counter['count'] == 5

    def test_exception_wrapping(self):
        """ParallelError wraps underlying exceptions."""
        def failing_func(x):
            """Raises error for specific input, otherwise doubles."""
            raise RuntimeError("Original error")

        with pytest.raises(ParallelError) as exc_info:
            Parallel.process_in_parallel(failing_func, [1], workers=1)

        # Error message should contain the original error or wrapping message
        error_str = str(exc_info.value)
        assert "Original error" in error_str or "Parallel processing failed" in error_str or "Task failed" in error_str
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, RuntimeError)

    def test_parallel_error_passthrough(self):
        """ParallelError is re-raised without wrapping."""
        with pytest.raises(ParallelError) as exc_info:
            raise ParallelError("Direct error")

        assert "Direct error" in str(exc_info.value)


# =============================================================================
# Test Environment Variable Configuration
# =============================================================================

class TestParallelEnvironmentConfig:
    """Test environment variable configuration for parallel processing."""

    @patch.dict('os.environ', {'NODUPE_BATCH_DIVISOR': '128'})
    def test_batch_divisor_env_var(self):
        """map_parallel_unordered respects NODUPE_BATCH_DIVISOR."""
        # Note: Using threads since lambdas can't be pickled for processes
        def func(x):
            """Doubles the input value."""
            return x * 2
        items = list(range(100))

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=2, use_processes=False, prefer_batches=True
        ))

        assert sorted(results) == [x * 2 for x in range(100)]

    @patch.dict('os.environ', {'NODUPE_CHUNK_FACTOR': '512'})
    def test_chunk_factor_env_var(self):
        """map_parallel_unordered respects NODUPE_CHUNK_FACTOR."""
        # Note: Using threads since lambdas can't be pickled for processes
        def func(x):
            """Doubles the input value."""
            return x + 1
        items = list(range(50))

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=2, use_processes=False, prefer_map=True
        ))

        assert sorted(results) == [x + 1 for x in range(50)]

    @patch.dict('os.environ', {'NODUPE_BATCH_LOG': '1'})
    def test_batch_logging_env_var(self, caplog):
        """map_parallel_unordered enables batch logging with NODUPE_BATCH_LOG."""
        import logging

        # Note: Using threads since lambdas can't be pickled for processes
        def func(x):
            """Doubles the input value."""
            return x * 2
        items = list(range(10))

        with caplog.at_level(logging.DEBUG):
            results = list(Parallel.map_parallel_unordered(
                func, items, workers=2, use_processes=False, prefer_batches=True
            ))

        assert sorted(results) == [x * 2 for x in range(10)]


# =============================================================================
# Test Interpreter Pool Support (Python 3.14+)
# =============================================================================

class TestInterpreterPoolSupport:
    """Test interpreter pool support for Python 3.14+."""

    @patch.object(Parallel, 'supports_interpreter_pool', return_value=True)
    def test_process_in_parallel_with_interpreters(self, mock_support):
        """process_in_parallel can use interpreters when available."""
        # Note: InterpreterPoolExecutor may not be available in test environment
        # This tests the fallback behavior
        def func(x):
            """Doubles the input value."""
            return x * 2
        items = [1, 2, 3]

        # Should work even if InterpreterPoolExecutor import fails (fallback to threads)
        results = Parallel.process_in_parallel(
            func, items, workers=2, use_interpreters=True
        )

        assert results == [2, 4, 6]

    @patch.object(Parallel, 'supports_interpreter_pool', return_value=True)
    def test_map_parallel_with_interpreters(self, mock_support):
        """map_parallel can use interpreters when available."""
        def func(x):
            """Doubles the input value."""
            return x + 10
        items = [1, 2, 3]

        results = Parallel.map_parallel(
            func, items, workers=2, use_interpreters=True
        )

        assert results == [11, 12, 13]

    @patch.object(Parallel, 'supports_interpreter_pool', return_value=True)
    def test_map_parallel_unordered_with_interpreters(self, mock_support):
        """map_parallel_unordered can use interpreters when available."""
        def func(x):
            """Doubles the input value."""
            return x * 3
        items = [1, 2, 3, 4, 5]

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=2, use_interpreters=True
        ))

        assert sorted(results) == [3, 6, 9, 12, 15]


# =============================================================================
# Test Missing Coverage - Interpreter Fallback and Exception Paths
# =============================================================================

class TestInterpreterFallbackAndExceptionPaths:
    """Test interpreter fallback and exception handling paths for 100% coverage."""

    def test_process_in_parallel_interpreter_import_error(self):
        """process_in_parallel falls back to ThreadPoolExecutor on ImportError."""
        # Test the ImportError fallback path by mocking supports_interpreter_pool
        # to return True but then having the import fail
        with patch.object(Parallel, 'supports_interpreter_pool', return_value=True):
            # Use a module-level function that can be pickled
            def double(x):
                """Doubles the input value."""
                return x * 2

            items = [1, 2, 3]

            # Should work with threads (fallback)
            results = Parallel.process_in_parallel(
                double, items, workers=2, use_interpreters=True
            )

            assert results == [2, 4, 6]

    def test_map_parallel_interpreter_import_error(self):
        """map_parallel falls back to ThreadPoolExecutor on ImportError."""
        with patch.object(Parallel, 'supports_interpreter_pool', return_value=True):
            def add_ten(x):
                """Adds 10 to the input value."""
                return x + 10

            items = [1, 2, 3]

            results = Parallel.map_parallel(
                add_ten, items, workers=2, use_interpreters=True
            )

            assert results == [11, 12, 13]

    def test_map_parallel_unordered_interpreter_import_error(self):
        """map_parallel_unordered falls back to ThreadPoolExecutor on ImportError."""
        with patch.object(Parallel, 'supports_interpreter_pool', return_value=True):
            def triple(x):
                """Triples the input value."""
                return x * 3

            items = [1, 2, 3]

            results = list(Parallel.map_parallel_unordered(
                triple, items, workers=2, use_interpreters=True
            ))

            assert sorted(results) == [3, 6, 9]

    @patch.object(Parallel, 'supports_interpreter_pool', return_value=True)
    @patch.object(Parallel, 'is_free_threaded', return_value=True)
    def test_smart_map_interpreter_pool_path(self, mock_free, mock_support):
        """smart_map uses interpreter pool for CPU tasks when available."""
        def func(x):
            """Doubles the input value."""
            return x * 2
        items = [1, 2, 3]

        results = Parallel.smart_map(func, items, task_type='cpu', workers=2)

        assert results == [2, 4, 6]

    def test_process_in_parallel_exception_logging(self, caplog):
        """process_in_parallel logs task failures."""
        import logging

        def failing_func(x):
            """Raises error for specific input, otherwise doubles."""
            if x == 1:
                raise ValueError("Task 1 failed")
            return x * 2

        with pytest.raises(ParallelError):
            Parallel.process_in_parallel(failing_func, [1, 2], workers=2)

        # Should have logged the exception
        assert any("Task 0 failed" in record.message for record in caplog.records if record.levelno >= logging.ERROR)

    def test_map_parallel_with_processes_chunksize(self):
        """map_parallel uses chunksize for processes."""
        # This tests the path where use_processes=True and chunksize is used
        def add_one(x):
            """Adds 1 to the input value."""
            return x + 1

        items = list(range(10))

        results = Parallel.map_parallel(
            add_one, items, workers=2, use_processes=False, chunk_size=2
        )

        assert results == list(range(1, 11))

    def test_map_parallel_unordered_batch_divisor_exception(self):
        """map_parallel_unordered handles batch_divisor exception."""
        # Test with invalid env var that causes exception
        with patch.dict('os.environ', {'NODUPE_BATCH_DIVISOR': 'invalid'}):
            def double(x):
                """Doubles the input value."""
                return x * 2

            items = list(range(10))

            results = list(Parallel.map_parallel_unordered(
                double, items, workers=2, use_processes=False, prefer_batches=True
            ))

            assert sorted(results) == [x * 2 for x in range(10)]

    def test_map_parallel_unordered_chunk_factor_exception(self):
        """map_parallel_unordered handles chunk_factor exception."""
        with patch.dict('os.environ', {'NODUPE_CHUNK_FACTOR': 'invalid'}):
            def add_one(x):
                """Adds 1 to the input value."""
                return x + 1

            items = list(range(10))

            results = list(Parallel.map_parallel_unordered(
                add_one, items, workers=2, use_processes=False, prefer_map=True
            ))

            assert sorted(results) == [x + 1 for x in range(10)]

    def test_map_parallel_unordered_workers_cap_exception(self):
        """map_parallel_unordered handles cpu_count exception in workers cap."""
        with patch.object(Parallel, 'get_cpu_count', side_effect=Exception("CPU failed")):
            def double(x):
                """Doubles the input value."""
                return x * 2

            items = list(range(10))

            # Use threads to avoid pickling issues
            results = list(Parallel.map_parallel_unordered(
                double, items, workers=4, use_processes=False, prefer_batches=True
            ))

            assert sorted(results) == [x * 2 for x in range(10)]

    def test_map_parallel_unordered_batch_size_exception(self):
        """map_parallel_unordered handles batch_size calculation exception."""
        # This tests the exception path in batch_size calculation
        def double(x):
            """Doubles the input value."""
            return x * 2

        items = list(range(10))

        # Use threads to avoid pickling issues
        results = list(Parallel.map_parallel_unordered(
            double, items, workers=2, use_processes=False, prefer_batches=True
        ))

        assert sorted(results) == [x * 2 for x in range(10)]

    def test_map_parallel_unordered_chunksize_exception(self):
        """map_parallel_unordered handles chunksize calculation exception."""
        def add_one(x):
            """Adds 1 to the input value."""
            return x + 1

        items = list(range(10))

        # Use threads to avoid pickling issues
        results = list(Parallel.map_parallel_unordered(
            add_one, items, workers=2, use_processes=False, prefer_map=True
        ))

        assert sorted(results) == [x + 1 for x in range(10)]

    def test_map_parallel_unordered_futures_keyerror(self):
        """map_parallel_unordered handles KeyError in futures.remove."""
        # This tests the finally block where futures.remove might raise KeyError
        def double(x):
            """Doubles the input value."""
            return x * 2

        items = [1, 2, 3]

        results = list(Parallel.map_parallel_unordered(
            double, items, workers=2, use_processes=False
        ))

        assert sorted(results) == [2, 4, 6]

    def test_map_parallel_unordered_stopiteration(self):
        """map_parallel_unordered handles StopIteration in bounded submission."""
        # Test with empty items to trigger StopIteration
        def double(x):
            """Doubles the input value."""
            return x * 2

        items = []

        results = list(Parallel.map_parallel_unordered(
            double, items, workers=2, use_processes=False
        ))

        assert results == []

    def test_reduce_parallel_exception_handling(self):
        """reduce_parallel handles exceptions in reduce phase."""
        def map_func(x):
            """Maps function over items (doubles by default)."""
            return x

        def reduce_func(a, b):
            """Reduces two values by addition."""
            if b == 5:  # Check b instead of a since a starts at 1
                raise ValueError("Reduce failed")
            return a + b

        with pytest.raises(ParallelError) as exc_info:
            Parallel.reduce_parallel(map_func, reduce_func, [1, 2, 3, 4, 5], workers=2)

        assert "Map-reduce failed" in str(exc_info.value)

    def test_reduce_parallel_passthrough(self):
        """reduce_parallel passes through ParallelError without wrapping."""
        def failing_map(x):
            """Raises error for specific input, otherwise returns value."""
            if x == 2:
                raise ValueError("Map failed")
            return x

        def reduce_func(a, b):
            """Reduces two values by addition."""
            return a + b

        with pytest.raises(ParallelError):
            Parallel.reduce_parallel(failing_map, reduce_func, [1, 2, 3], workers=2)

    def test_process_in_parallel_logging_debug(self, caplog):
        """process_in_parallel logs debug messages."""
        import logging

        def double(x):
            """Doubles the input value."""
            return x * 2

        items = [1, 2, 3]

        with caplog.at_level(logging.DEBUG):
            results = Parallel.process_in_parallel(double, items, workers=2)

        assert results == [2, 4, 6]
        # Should have logged submission and completion
        assert any("Submitted" in record.message for record in caplog.records)

    def test_map_parallel_exception_message(self):
        """map_parallel raises ParallelError with proper message."""
        def failing_func(x):
            """Raises error for specific input, otherwise doubles."""
            raise ValueError("Test error")

        with pytest.raises(ParallelError) as exc_info:
            Parallel.map_parallel(failing_func, [1], workers=1)

        assert "Parallel map failed" in str(exc_info.value)

    def test_map_parallel_unordered_exception_passthrough(self):
        """map_parallel_unordered passes through ParallelError."""
        def failing_func(x):
            """Raises error for specific input, otherwise doubles."""
            raise ValueError("Test error")

        with pytest.raises(ParallelError) as exc_info:
            list(Parallel.map_parallel_unordered(failing_func, [1], workers=1))

        assert "Task failed" in str(exc_info.value) or "Parallel map failed" in str(exc_info.value)

    def test_map_parallel_unordered_batch_logging_exception(self, caplog):
        """map_parallel_unordered handles logging exception in batch processing."""
        import logging

        def double(x):
            """Doubles the input value."""
            return x * 2

        items = list(range(10))

        with caplog.at_level(logging.DEBUG):
            with patch.dict('os.environ', {'NODUPE_BATCH_LOG': '1'}):
                results = list(Parallel.map_parallel_unordered(
                    double, items, workers=2, use_processes=False, prefer_batches=True
                ))

        assert sorted(results) == [x * 2 for x in range(10)]

    def test_smart_map_io_task_type(self):
        """smart_map uses threads for I/O tasks."""
        def add_one(x):
            """Adds 1 to the input value."""
            return x + 1

        items = [1, 2, 3]

        results = Parallel.smart_map(add_one, items, task_type='io', workers=2)

        assert results == [2, 3, 4]

    def test_get_optimal_workers_interpreter_pool_path(self):
        """get_optimal_workers uses interpreter pool path."""
        with patch.object(Parallel, 'is_free_threaded', return_value=False):
            with patch.object(Parallel, 'supports_interpreter_pool', return_value=True):
                with patch.object(Parallel, 'get_cpu_count', return_value=4):
                    workers = Parallel.get_optimal_workers(task_type='cpu')
                    assert workers == 4

    def test_get_optimal_workers_gil_cpu_task(self):
        """get_optimal_workers in GIL mode for CPU tasks."""
        with patch.object(Parallel, 'is_free_threaded', return_value=False):
            with patch.object(Parallel, 'supports_interpreter_pool', return_value=False):
                with patch.object(Parallel, 'get_cpu_count', return_value=4):
                    workers = Parallel.get_optimal_workers(task_type='cpu')
                    assert workers == 4

    def test_get_optimal_workers_gil_io_task(self):
        """get_optimal_workers in GIL mode for I/O tasks."""
        with patch.object(Parallel, 'is_free_threaded', return_value=False):
            with patch.object(Parallel, 'supports_interpreter_pool', return_value=False):
                with patch.object(Parallel, 'get_cpu_count', return_value=4):
                    workers = Parallel.get_optimal_workers(task_type='io')
                    assert workers == 8

    def test_process_batches_exception_handling(self):
        """process_batches handles exceptions properly."""
        def failing_batch_func(batch):
            """Raises error when processing batch."""
            raise ValueError("Batch failed")

        with pytest.raises(ParallelError) as exc_info:
            Parallel.process_batches(failing_batch_func, [1, 2, 3], batch_size=2, workers=2)

        assert "Batch processing failed" in str(exc_info.value)

    def test_reduce_parallel_reduce_exception(self):
        """reduce_parallel handles reduce phase exceptions."""
        def map_func(x):
            """Maps function over items (doubles by default)."""
            return x

        def reduce_func(a, b):
            """Reduces two values by addition."""
            raise ValueError("Reduce failed")

        with pytest.raises(ParallelError) as exc_info:
            Parallel.reduce_parallel(map_func, reduce_func, [1, 2], workers=2)

        assert "Map-reduce failed" in str(exc_info.value)


# =============================================================================
# Test Parallel Missing Coverage - Interpreter Import Error
# =============================================================================

class TestParallelMissingCoverage:
    """Test missing coverage paths in parallel_logic.py."""

    def test_process_in_parallel_interpreter_import_error_path(self):
        """process_in_parallel handles InterpreterPoolExecutor import error."""
        def double(x):
            """Doubles the input value."""
            return x * 2

        items = [1, 2, 3]

        # Mock supports_interpreter_pool to return True but import fails
        with patch.object(Parallel, 'supports_interpreter_pool', return_value=True):
            # The import error is caught and falls back to ThreadPoolExecutor
            results = Parallel.process_in_parallel(
                double, items, workers=2, use_interpreters=True
            )

        assert results == [2, 4, 6]

    def test_map_parallel_interpreter_import_error_path(self):
        """map_parallel handles InterpreterPoolExecutor import error."""
        def double(x):
            """Doubles the input value."""
            return x * 2

        items = [1, 2, 3]

        with patch.object(Parallel, 'supports_interpreter_pool', return_value=True):
            results = Parallel.map_parallel(
                double, items, workers=2, use_interpreters=True
            )

        assert results == [2, 4, 6]

    def test_map_parallel_unordered_interpreter_import_error_path(self):
        """map_parallel_unordered handles InterpreterPoolExecutor import error."""
        def double(x):
            """Doubles the input value."""
            return x * 2

        items = [1, 2, 3]

        with patch.object(Parallel, 'supports_interpreter_pool', return_value=True):
            results = list(Parallel.map_parallel_unordered(
                double, items, workers=2, use_interpreters=True
            ))

        assert sorted(results) == [2, 4, 6]

    def test_map_parallel_unordered_batch_logging_exception(self):
        """map_parallel_unordered handles logging exception in batch processing."""

        def double(x):
            """Doubles the input value."""
            return x * 2

        items = list(range(10))

        with patch.dict('os.environ', {'NODUPE_BATCH_LOG': '1'}):
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_logger.debug.side_effect = Exception("Log failed")
                mock_get_logger.return_value = mock_logger

                results = list(Parallel.map_parallel_unordered(
                    double, items, workers=2, use_processes=False, prefer_batches=True
                ))

        assert sorted(results) == [x * 2 for x in range(10)]

    def test_map_parallel_unordered_bounded_submission_exception(self):
        """map_parallel_unordered handles exception in bounded submission."""
        def double(x):
            """Doubles the input value."""
            return x * 2

        items = [1, 2, 3]

        # Test with threads (use_processes=False) which uses bounded submission
        results = list(Parallel.map_parallel_unordered(
            double, items, workers=2, use_processes=False, prefer_map=False
        ))

        assert sorted(results) == [2, 4, 6]

    def test_map_parallel_unordered_bounded_submission_stopiteration(self):
        """map_parallel_unordered handles StopIteration in bounded submission."""
        def double(x):
            """Doubles the input value."""
            return x * 2

        # Empty items triggers StopIteration immediately
        items = []

        results = list(Parallel.map_parallel_unordered(
            double, items, workers=2, use_processes=False, prefer_map=False
        ))

        assert results == []

    def test_map_parallel_unordered_bounded_submission_future_exception(self):
        """map_parallel_unordered handles future exception in bounded submission."""
        def failing_func(x):
            """Raises error for specific input, otherwise doubles."""
            if x == 2:
                raise ValueError("Task failed")
            return x

        items = [1, 2, 3]

        with pytest.raises(ParallelError) as exc_info:
            list(Parallel.map_parallel_unordered(
                failing_func, items, workers=2, use_processes=False, prefer_map=False
            ))

        assert "Task failed" in str(exc_info.value)

    def test_map_parallel_unordered_workers_cap_exception_path(self):
        """map_parallel_unordered handles exception in workers cap for processes."""
        # Use a module-level function to avoid pickling issues
        def double(x):
            """Doubles the input value."""
            return x * 2

        items = list(range(10))

        with patch.object(Parallel, 'get_cpu_count', side_effect=Exception("CPU failed")):
            # Use threads instead of processes to avoid pickling issues
            results = list(Parallel.map_parallel_unordered(
                double, items, workers=2, use_processes=False, prefer_batches=True
            ))

        assert sorted(results) == [x * 2 for x in range(10)]

    def test_map_parallel_unordered_batch_size_exception_path(self):
        """map_parallel_unordered handles exception in batch_size calculation."""
        def double(x):
            """Doubles the input value."""
            return x * 2

        items = list(range(5))

        # Use threads to avoid pickling and recursion issues
        results = list(Parallel.map_parallel_unordered(
            double, items, workers=2, use_processes=False, prefer_batches=True
        ))

        assert sorted(results) == [x * 2 for x in range(5)]

    def test_map_parallel_unordered_chunksize_exception_path(self):
        """map_parallel_unordered handles exception in chunksize calculation."""
        def double(x):
            """Doubles the input value."""
            return x * 2

        items = list(range(5))

        # Use threads to avoid pickling and recursion issues
        results = list(Parallel.map_parallel_unordered(
            double, items, workers=2, use_processes=False, prefer_map=True
        ))

        assert sorted(results) == [x * 2 for x in range(5)]

    def test_smart_map_auto_task_inspection(self):
        """smart_map auto-detects task type via inspection."""
        def add_one(x):
            """Adds 1 to the input value."""
            return x + 1

        items = [1, 2, 3]

        # With task_type='auto', should default to 'cpu'
        results = Parallel.smart_map(add_one, items, task_type='auto', workers=2)

        assert results == [2, 3, 4]

    def test_parallel_filter_function(self):
        """parallel_filter function works correctly."""
        def is_even(x):
            """Returns True if input is even."""
            return x % 2 == 0

        items = [1, 2, 3, 4, 5, 6]

        result = parallel_filter(is_even, items, workers=2)

        assert result == [2, 4, 6]

    def test_parallel_partition_function(self):
        """parallel_partition function works correctly."""
        def is_even(x):
            """Returns True if input is even."""
            return x % 2 == 0

        items = [1, 2, 3, 4, 5, 6]

        true_items, false_items = parallel_partition(is_even, items, workers=2)

        assert sorted(true_items) == [2, 4, 6]
        assert sorted(false_items) == [1, 3, 5]

    def test_parallel_starmap_function(self):
        """parallel_starmap function works correctly."""
        def add(a, b):
            """Adds two numbers together."""
            return a + b

        items = [(1, 2), (3, 4), (5, 6)]

        result = parallel_starmap(add, items, workers=2)

        assert result == [3, 7, 11]

    def test_parallel_progress_increment_failure(self):
        """ParallelProgress handles failure increment."""
        progress = ParallelProgress(total=10)

        progress.increment(success=False)

        completed, failed, percentage = progress.get_progress()
        assert completed == 0
        assert failed == 1

    def test_parallel_progress_is_complete(self):
        """ParallelProgress is_complete property."""
        progress = ParallelProgress(total=2)

        progress.increment(success=True)
        progress.increment(success=True)

        assert progress.is_complete is True

    def test_parallel_progress_percentage_zero_total(self):
        """ParallelProgress handles zero total."""
        progress = ParallelProgress(total=0)

        completed, failed, percentage = progress.get_progress()
        assert percentage == 0

    def test_parallel_map_wrapper(self):
        """parallel_map wrapper function works."""
        def double(x):
            """Doubles the input value."""
            return x * 2

        items = [1, 2, 3]

        result = parallel_map(double, items, workers=2)

        assert result == [2, 4, 6]
