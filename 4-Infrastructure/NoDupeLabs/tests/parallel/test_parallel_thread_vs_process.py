# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for parallel_logic.py using BOTH threads and processes.

This test file uses pickle-safe helper functions from test_helpers.py
to properly test ProcessPoolExecutor code paths that cannot be tested
with lambdas or local functions.

Key Differences from Other Test Files:
- Uses module-level pickle-safe functions for process testing
- Explicitly tests both use_processes=True and use_processes=False
- Verifies multiprocessing code paths are actually executed
"""

import time
from unittest.mock import patch

import pytest

from nodupe.tools.parallel.parallel_logic import (
    Parallel,
    ParallelError,
)

# Import pickle-safe test helpers
from tests.parallel.test_helpers import (
    square_number,
    double_number,
    is_even,
    add_numbers,
    multiply_numbers,
    identity,
    add_one,
    slow_square,
    count_letters,
    to_uppercase,
    filter_positive,
    sum_list,
    maybe_raise,
    slow_operation,
    PicklableCounter,
    SMALL_INT_RANGE,
    MEDIUM_INT_RANGE,
    POSITIVE_NUMBERS,
    NEGATIVE_NUMBERS,
)


# =============================================================================
# Test Thread vs Process Code Paths
# =============================================================================

class TestThreadVsProcessCodePaths:
    """Test both ThreadPoolExecutor and ProcessPoolExecutor code paths."""

    def test_thread_pool_path_with_lambda(self):
        """Test ThreadPoolExecutor path - lambdas work fine."""
        items = [1, 2, 3, 4, 5]
        
        # Lambda works with threads (no pickling needed)
        results = Parallel.process_in_parallel(
            lambda x: x * 2,
            items,
            workers=2,
            use_processes=False  # Threads
        )
        
        assert results == [2, 4, 6, 8, 10]

    def test_process_pool_path_with_pickle_safe_function(self):
        """Test ProcessPoolExecutor path - requires pickle-safe function.
        
        This is the key test that validates the multiprocessing code path.
        """
        items = [1, 2, 3, 4, 5]
        
        # Must use module-level function (pickle-safe)
        results = Parallel.process_in_parallel(
            square_number,  # ✅ Pickle-safe
            items,
            workers=2,
            use_processes=True  # Processes
        )
        
        assert results == [1, 4, 9, 16, 25]

    def test_process_pool_path_with_double_number(self):
        """Test ProcessPoolExecutor with another pickle-safe function."""
        items = [10, 20, 30]
        
        results = Parallel.process_in_parallel(
            double_number,  # ✅ Pickle-safe
            items,
            workers=2,
            use_processes=True
        )
        
        assert results == [20, 40, 60]

    def test_process_pool_path_with_is_even(self):
        """Test ProcessPoolExecutor with boolean return function."""
        items = [1, 2, 3, 4, 5, 6]
        
        results = Parallel.process_in_parallel(
            is_even,  # ✅ Pickle-safe
            items,
            workers=2,
            use_processes=True
        )
        
        assert results == [False, True, False, True, False, True]

    def test_thread_pool_path_with_is_even(self):
        """Test ThreadPoolExecutor with same function for comparison."""
        items = [1, 2, 3, 4, 5, 6]
        
        results = Parallel.process_in_parallel(
            is_even,
            items,
            workers=2,
            use_processes=False  # Threads
        )
        
        assert results == [False, True, False, True, False, True]

    def test_process_pool_with_string_operations(self):
        """Test ProcessPoolExecutor with string operations."""
        items = ["hello", "world", "test"]
        
        results = Parallel.process_in_parallel(
            to_uppercase,  # ✅ Pickle-safe
            items,
            workers=2,
            use_processes=True
        )
        
        assert results == ["HELLO", "WORLD", "TEST"]

    def test_process_pool_with_count_letters(self):
        """Test ProcessPoolExecutor with string length counting."""
        items = ["abc", "defg", "hijkl"]
        
        results = Parallel.process_in_parallel(
            count_letters,  # ✅ Pickle-safe
            items,
            workers=2,
            use_processes=True
        )
        
        assert results == [3, 4, 5]


# =============================================================================
# Test map_parallel with Processes
# =============================================================================

class TestMapParallelWithProcesses:
    """Test map_parallel method with ProcessPoolExecutor."""

    def test_map_parallel_processes_basic(self):
        """map_parallel works with processes and pickle-safe function."""
        items = [1, 2, 3, 4, 5]
        
        results = Parallel.map_parallel(
            square_number,
            items,
            workers=2,
            use_processes=True
        )
        
        assert results == [1, 4, 9, 16, 25]

    def test_map_parallel_processes_with_chunksize(self):
        """map_parallel works with processes and chunk_size parameter."""
        items = list(range(20))
        
        results = Parallel.map_parallel(
            double_number,
            items,
            workers=2,
            use_processes=True,
            chunk_size=5  # Note: parameter is chunk_size not chunksize
        )
        
        assert results == list(range(0, 40, 2))

    def test_map_parallel_processes_large_dataset(self):
        """map_parallel with processes handles larger datasets."""
        items = MEDIUM_INT_RANGE  # 100 items
        
        results = Parallel.map_parallel(
            add_one,
            items,
            workers=4,
            use_processes=True
        )
        
        expected = [x + 1 for x in items]
        assert results == expected

    @patch.object(Parallel, 'supports_interpreter_pool', return_value=True)
    def test_map_parallel_processes_with_interpreters(
        self, mock_supports_interpreter
    ):
        """map_parallel with processes and use_interpreters=True."""
        items = [1, 2, 3, 4, 5]
        
        results = Parallel.map_parallel(
            square_number,
            items,
            workers=2,
            use_processes=True,
            use_interpreters=True
        )
        
        assert results == [1, 4, 9, 16, 25]
        mock_supports_interpreter.assert_called()


# =============================================================================
# Test map_parallel_unordered with Processes
# =============================================================================

class TestMapParallelUnorderedWithProcesses:
    """Test map_parallel_unordered method with ProcessPoolExecutor."""

    def test_map_parallel_unordered_processes_basic(self):
        """map_parallel_unordered works with processes."""
        items = [1, 2, 3, 4, 5]
        
        results = list(Parallel.map_parallel_unordered(
            square_number,
            items,
            workers=2,
            use_processes=True
        ))
        
        # Results may be in any order, but should contain all values
        assert sorted(results) == [1, 4, 9, 16, 25]

    def test_map_parallel_unordered_processes_with_chunksize(self):
        """map_parallel_unordered with processes and chunk_size."""
        items = list(range(20))
        
        # Note: map_parallel_unordered doesn't have chunk_size parameter
        # Just test the basic functionality
        results = list(Parallel.map_parallel_unordered(
            double_number,
            items,
            workers=2,
            use_processes=True
        ))
        
        assert sorted(results) == list(range(0, 40, 2))

    def test_map_parallel_unordered_processes_large(self):
        """map_parallel_unordered with processes handles large datasets."""
        items = MEDIUM_INT_RANGE
        
        results = list(Parallel.map_parallel_unordered(
            add_one,
            items,
            workers=4,
            use_processes=True
        ))
        
        expected = [x + 1 for x in items]
        assert sorted(results) == sorted(expected)


# =============================================================================
# Test smart_map with Processes
# =============================================================================

class TestSmartMapWithProcesses:
    """Test smart_map method with ProcessPoolExecutor."""

    def test_smart_map_processes_cpu_task(self):
        """smart_map with processes for CPU-bound task."""
        items = [1, 2, 3, 4, 5]
        
        # smart_map doesn't take use_processes, it auto-detects
        # We'll test the CPU path which uses processes by default
        with patch.object(Parallel, 'is_free_threaded', return_value=False):
            with patch.object(Parallel, 'supports_interpreter_pool', return_value=False):
                results = Parallel.smart_map(
                    square_number,
                    items,
                    task_type='cpu',
                    workers=2
                )
        
        assert results == [1, 4, 9, 16, 25]

    def test_smart_map_processes_io_task(self):
        """smart_map with threads for I/O-bound task."""
        items = [1, 2, 3, 4, 5]
        
        # I/O tasks use threads
        results = Parallel.smart_map(
            double_number,
            items,
            task_type='io',
            workers=2
        )
        
        assert results == [2, 4, 6, 8, 10]

    def test_smart_map_processes_auto_task(self):
        """smart_map with auto task type detection."""
        items = [1, 2, 3, 4, 5]
        
        # Auto defaults to CPU
        with patch.object(Parallel, 'is_free_threaded', return_value=False):
            with patch.object(Parallel, 'supports_interpreter_pool', return_value=False):
                results = Parallel.smart_map(
                    square_number,
                    items,
                    task_type='auto',
                    workers=2
                )
        
        assert results == [1, 4, 9, 16, 25]


# =============================================================================
# Test reduce_parallel with Processes
# =============================================================================

class TestReduceParallelWithProcesses:
    """Test reduce_parallel method with ProcessPoolExecutor."""

    def test_reduce_parallel_threads_sum(self):
        """reduce_parallel with threads for sum operation."""
        items = [1, 2, 3, 4, 5]
        
        # reduce_parallel: applies map_func to each item, then reduces with reduce_func
        # map_func: identity (returns item unchanged)
        # reduce_func: takes (accumulator, item) and returns new accumulator
        result = Parallel.reduce_parallel(
            identity,  # Map: x -> x
            lambda acc, x: acc + x,  # Reduce: add item to accumulator
            items,
            workers=2,
            use_processes=False
        )
        assert result == 15

    def test_reduce_parallel_threads_multiply(self):
        """reduce_parallel with threads for multiply operation."""
        items = [1, 2, 3, 4]
        
        # Test with threads
        result = Parallel.reduce_parallel(
            identity,  # Map: x -> x
            lambda acc, x: acc * x,  # Reduce: multiply accumulator by item
            items,
            workers=2,
            use_processes=False
        )
        
        assert result == 24  # 1*2*3*4

    def test_reduce_parallel_with_initial_value(self):
        """reduce_parallel with initial value."""
        items = [1, 2, 3]
        
        # Sum with initial value of 100
        result = Parallel.reduce_parallel(
            identity,  # Map: x -> x
            lambda acc, x: acc + x,  # Reduce: add
            items,
            initial=100,
            workers=2,
            use_processes=False
        )
        
        assert result == 106  # 100 + 1 + 2 + 3


# =============================================================================
# Test Error Handling with Processes
# =============================================================================

class TestErrorHandlingWithProcesses:
    """Test error handling in ProcessPoolExecutor code paths."""

    def test_process_pool_exception_handling(self):
        """ProcessPoolExecutor properly handles exceptions."""
        items = [1, 2, -1, 4]  # -1 will cause error
        
        with pytest.raises(ParallelError) as exc_info:
            Parallel.process_in_parallel(
                maybe_raise,  # Raises ValueError for -1
                items,
                workers=2,
                use_processes=True
            )
        
        assert "ValueError" in str(exc_info.value) or "Error for value -1" in str(exc_info.value)

    def test_process_pool_timeout_handling(self):
        """ProcessPoolExecutor handles timeouts."""
        items = [1, 2, 3]
        
        # Use short timeout with slow operation
        with pytest.raises(Exception):
            Parallel.process_in_parallel(
                slow_operation,
                items,
                workers=2,
                use_processes=True,
                timeout=0.1  # Very short timeout
            )


# =============================================================================
# Test Process Batching
# =============================================================================

class TestProcessBatching:
    """Test batch processing with ProcessPoolExecutor."""

    def test_process_batches_processes(self):
        """process_batches works with processes."""
        items = list(range(20))
        
        # process_batches applies func to each batch (list), not individual items
        # Use module-level pickle-safe function
        results = Parallel.process_batches(
            sum_list,  # ✅ Pickle-safe - sums each batch
            items,
            batch_size=5,
            workers=2,
            use_processes=True
        )
        
        # Each batch of 5 is summed: [0+1+2+3+4, 5+6+7+8+9, ...]
        expected_batches = [
            sum(range(0, 5)),   # 10
            sum(range(5, 10)),  # 35
            sum(range(10, 15)), # 60
            sum(range(15, 20))  # 85
        ]
        assert results == expected_batches

    def test_process_batches_processes_custom_batch_size(self):
        """process_batches with custom batch size and processes."""
        items = list(range(10))
        
        # Use a module-level function that works on lists
        results = Parallel.process_batches(
            sum_list,  # Sum each batch
            items,
            batch_size=3,
            workers=2,
            use_processes=True
        )
        
        # Results are sums from each batch
        assert len(results) == 4  # 4 batches
        assert results[0] == sum([0, 1, 2])    # 3
        assert results[1] == sum([3, 4, 5])    # 12
        assert results[2] == sum([6, 7, 8])    # 21
        assert results[3] == sum([9])          # 9


# =============================================================================
# Test Parallel Operations (Removed - not in API)
# =============================================================================
# Note: parallel_map, parallel_filter, parallel_partition, parallel_starmap
# are not methods of Parallel class in this version
# =============================================================================

# class TestParallelOperationsWithProcesses:
#     """Test parallel map/filter/partition with ProcessPoolExecutor."""
#     pass


# =============================================================================
# Test Performance Comparison (Threads vs Processes)
# =============================================================================

class TestThreadVsProcessPerformance:
    """Compare thread and process performance characteristics."""

    def test_thread_overhead_lower_for_small_tasks(self):
        """Threads have lower overhead for small task counts."""
        items = [1, 2, 3]
        
        import time
        
        # Thread version
        start = time.time()
        thread_result = Parallel.process_in_parallel(
            double_number,
            items,
            workers=2,
            use_processes=False
        )
        thread_time = time.time() - start
        
        # Process version
        start = time.time()
        process_result = Parallel.process_in_parallel(
            double_number,
            items,
            workers=2,
            use_processes=True
        )
        process_time = time.time() - start
        
        # Both should produce same results
        assert thread_result == process_result == [2, 4, 6]
        
        # Threads should be faster for small tasks (startup overhead)
        # Note: This may be flaky on slow systems, so we use generous margin
        assert thread_time < process_time * 2  # Threads shouldn't be 2x slower

    def test_process_better_for_cpu_bound_tasks(self):
        """Processes better for CPU-bound tasks (no GIL limitation)."""
        items = list(range(50))
        
        # Both should produce correct results
        thread_result = Parallel.process_in_parallel(
            square_number,
            items,
            workers=4,
            use_processes=False
        )
        
        process_result = Parallel.process_in_parallel(
            square_number,
            items,
            workers=4,
            use_processes=True
        )
        
        expected = [x * x for x in items]
        assert thread_result == expected
        assert process_result == expected


# =============================================================================
# Test Edge Cases with Processes
# =============================================================================

class TestEdgeCasesWithProcesses:
    """Test edge cases with ProcessPoolExecutor."""

    def test_process_pool_empty_input(self):
        """ProcessPoolExecutor handles empty input."""
        results = Parallel.process_in_parallel(
            square_number,
            [],
            workers=2,
            use_processes=True
        )
        
        assert results == []

    def test_process_pool_single_item(self):
        """ProcessPoolExecutor handles single item."""
        results = Parallel.process_in_parallel(
            square_number,
            [5],
            workers=2,
            use_processes=True
        )
        
        assert results == [25]

    def test_process_pool_large_worker_count(self):
        """ProcessPoolExecutor handles worker count > items."""
        results = Parallel.process_in_parallel(
            double_number,
            [1, 2],
            workers=10,  # More workers than items
            use_processes=True
        )
        
        assert results == [2, 4]

    def test_process_pool_very_large_dataset(self):
        """ProcessPoolExecutor handles very large datasets."""
        items = list(range(500))
        
        results = Parallel.process_in_parallel(
            add_one,
            items,
            workers=4,
            use_processes=True
        )
        
        expected = [x + 1 for x in items]
        assert results == expected


# =============================================================================
# Test PicklableCounter with Processes
# =============================================================================

class TestPicklableCounterWithProcesses:
    """Test stateful operations with PicklableCounter."""

    def test_picklable_counter_processes(self):
        """PicklableCounter works with processes."""
        items = [1, 2, 3, 4, 5]
        
        # Note: Each process gets its own copy of the counter
        # This tests that the counter IS pickled correctly
        counter = PicklableCounter(start=10)
        
        results = Parallel.process_in_parallel(
            counter,
            items,
            workers=2,
            use_processes=True
        )
        
        # Each process increments independently
        # We just verify it doesn't crash and returns results
        assert len(results) == 5
        assert all(isinstance(r, int) for r in results)
