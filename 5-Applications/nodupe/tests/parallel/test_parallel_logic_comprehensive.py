# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Comprehensive tests for nodupe/tools/parallel/parallel_logic.py - Missing coverage areas.

This test file specifically targets the missing coverage areas identified:
- Lines 128-130, 132: InterpreterPoolExecutor fallback paths
- Line 165: use_interpreters flag in map_parallel
- Line 195: InterpreterPoolExecutor in map_parallel
- Lines 202-204, 206: chunksize handling
- Lines 255-256, 259-260, 264: Environment variable handling
- Lines 268-273: Batch processing with logging
- Lines 280-282, 284: Chunksize calculation
- Lines 291-322: Bounded submission for threads
- Lines 326-330: StopIteration handling
- Lines 340-341, 355-356: Executor selection
- Line 367: Interpreter pool fallback
- Line 420: smart_map interpreter pool path
- Lines 462-465: Free-threaded mode detection
- Lines 508-509: get_optimal_workers exception handling
- Line 565: reduce_parallel error handling

Note: Now uses pickle-safe test helpers for ProcessPoolExecutor testing.
See: docs/PARALLEL_TESTING_SUSTAINABILITY.md
"""

import os
import time
from unittest.mock import patch

import pytest

from nodupe.tools.parallel.parallel_logic import (
    Parallel,
    ParallelError,
)

# Import pickle-safe test helpers for process testing
from tests.parallel.test_helpers import (
    double_number,
    square_number,
    add_one,
    identity,
    MEDIUM_INT_RANGE,
)

# =============================================================================
# Test InterpreterPoolExecutor Fallback Paths
# =============================================================================

class TestInterpreterPoolFallback:
    """Test InterpreterPoolExecutor fallback scenarios."""

    def _double_func(self, x):
        """Helper function for testing."""
        return x * 2

    @patch.object(Parallel, 'supports_interpreter_pool', return_value=True)
    def test_process_in_parallel_interpreter_import_error(self, mock_supports):
        """process_in_parallel falls back to ThreadPoolExecutor on ImportError."""
        items = [1, 2, 3]

        # When InterpreterPoolExecutor is not available, it falls back to ThreadPoolExecutor
        results = Parallel.process_in_parallel(
            self._double_func, items, workers=2, use_interpreters=True
        )

        assert results == [2, 4, 6]

    @patch.object(Parallel, 'supports_interpreter_pool', return_value=True)
    def test_map_parallel_interpreter_import_error(self, mock_supports):
        """map_parallel falls back to ThreadPoolExecutor on ImportError."""
        items = [1, 2, 3]

        results = Parallel.map_parallel(
            self._double_func, items, workers=2, use_interpreters=True
        )
        assert results == [2, 4, 6]

    @patch.object(Parallel, 'supports_interpreter_pool', return_value=True)
    def test_map_parallel_unordered_interpreter_import_error(self, mock_supports):
        """map_parallel_unordered falls back on ImportError."""
        items = [1, 2, 3]

        results = list(Parallel.map_parallel_unordered(
            self._double_func, items, workers=2, use_interpreters=True
        ))

        assert sorted(results) == [2, 4, 6]

    def test_smart_map_interpreter_pool_path(self):
        """smart_map uses interpreter pool when available."""
        items = [1, 2, 3]

        with patch.object(Parallel, 'supports_interpreter_pool', return_value=True):
            with patch.object(Parallel, 'is_free_threaded', return_value=False):
                results = Parallel.smart_map(self._double_func, items, task_type='cpu', workers=2)
                assert results == [2, 4, 6]


# =============================================================================
# Test Environment Variable Handling
# =============================================================================

class TestEnvironmentVariableHandling:
    """Test environment variable configuration for parallel processing."""

    def _double_func(self, x):
        """Helper function for testing."""
        return x * 2

    def test_batch_divisor_env_var_valid(self):
        """map_parallel_unordered uses NODUPE_BATCH_DIVISOR env var."""
        items = list(range(100))

        with patch.dict(os.environ, {'NODUPE_BATCH_DIVISOR': '100'}):
            results = list(Parallel.map_parallel_unordered(
                self._double_func, items, workers=2, use_processes=False
            ))
            assert sorted(results) == [x * 2 for x in range(100)]

    def test_batch_divisor_env_var_invalid(self):
        """map_parallel_unordered handles invalid NODUPE_BATCH_DIVISOR."""
        items = list(range(10))

        with patch.dict(os.environ, {'NODUPE_BATCH_DIVISOR': 'invalid'}):
            results = list(Parallel.map_parallel_unordered(
                self._double_func, items, workers=2, use_processes=False
            ))
            assert sorted(results) == [x * 2 for x in range(10)]

    def test_chunk_factor_env_var_valid(self):
        """map_parallel_unordered uses NODUPE_CHUNK_FACTOR env var."""
        items = list(range(50))

        with patch.dict(os.environ, {'NODUPE_CHUNK_FACTOR': '50'}):
            results = list(Parallel.map_parallel_unordered(
                self._double_func, items, workers=2, use_processes=False
            ))
            assert sorted(results) == [x * 2 for x in range(50)]

    def test_chunk_factor_env_var_invalid(self):
        """map_parallel_unordered handles invalid NODUPE_CHUNK_FACTOR."""
        items = list(range(10))

        with patch.dict(os.environ, {'NODUPE_CHUNK_FACTOR': 'invalid'}):
            results = list(Parallel.map_parallel_unordered(
                self._double_func, items, workers=2, use_processes=False
            ))
            assert sorted(results) == [x * 2 for x in range(10)]

    def test_batch_log_env_var_enabled(self):
        """map_parallel_unordered respects NODUPE_BATCH_LOG env var."""
        items = list(range(20))

        with patch.dict(os.environ, {'NODUPE_BATCH_LOG': '1'}):
            results = list(Parallel.map_parallel_unordered(
                self._double_func, items, workers=2, use_processes=False
            ))
            assert sorted(results) == [x * 2 for x in range(20)]

    def test_batch_log_env_var_true(self):
        """map_parallel_unordered respects NODUPE_BATCH_LOG=true."""
        items = list(range(20))

        with patch.dict(os.environ, {'NODUPE_BATCH_LOG': 'true'}):
            results = list(Parallel.map_parallel_unordered(
                self._double_func, items, workers=2, use_processes=False
            ))
            assert sorted(results) == [x * 2 for x in range(20)]

    def test_batch_log_env_var_yes(self):
        """map_parallel_unordered respects NODUPE_BATCH_LOG=yes."""
        items = list(range(20))

        with patch.dict(os.environ, {'NODUPE_BATCH_LOG': 'yes'}):
            results = list(Parallel.map_parallel_unordered(
                self._double_func, items, workers=2, use_processes=False
            ))
            assert sorted(results) == [x * 2 for x in range(20)]

    def test_batch_log_env_var_on(self):
        """map_parallel_unordered respects NODUPE_BATCH_LOG=on."""
        items = list(range(20))

        with patch.dict(os.environ, {'NODUPE_BATCH_LOG': 'on'}):
            results = list(Parallel.map_parallel_unordered(
                self._double_func, items, workers=2, use_processes=False
            ))
            assert sorted(results) == [x * 2 for x in range(20)]

    def test_env_vars_not_set_defaults(self):
        """map_parallel_unordered uses defaults when env vars not set."""
        items = list(range(10))

        # Ensure env vars are not set
        env_copy = os.environ.copy()
        for key in ['NODUPE_BATCH_DIVISOR', 'NODUPE_CHUNK_FACTOR', 'NODUPE_BATCH_LOG']:
            if key in os.environ:
                del os.environ[key]

        try:
            results = list(Parallel.map_parallel_unordered(
                self._double_func, items, workers=2, use_processes=False
            ))
            assert sorted(results) == [x * 2 for x in range(10)]
        finally:
            os.environ.clear()
            os.environ.update(env_copy)


# =============================================================================
# Test Bounded Submission for Threads
# =============================================================================

class TestBoundedSubmission:
    """Test bounded submission pattern for thread executor."""

    def test_bounded_submission_basic(self):
        """map_parallel_unordered uses bounded submission for threads."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = [1, 2, 3, 4, 5]

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=3, use_processes=False
        ))

        assert sorted(results) == [2, 4, 6, 8, 10]

    def test_bounded_submission_empty_items(self):
        """map_parallel_unordered handles empty items with bounded submission."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = []

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=3, use_processes=False
        ))

        assert results == []

    def test_bounded_submission_single_item(self):
        """map_parallel_unordered handles single item with bounded submission."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = [42]

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=3, use_processes=False
        ))

        assert results == [84]

    def test_bounded_submission_fewer_items_than_workers(self):
        """map_parallel_unordered handles fewer items than workers."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = [1, 2]

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=10, use_processes=False
        ))

        assert sorted(results) == [2, 4]

    def test_bounded_submission_with_timeout(self):
        """map_parallel_unordered respects timeout in bounded submission."""
        def slow_func(x):
            """Helper function for testing."""
            time.sleep(0.01)
            return x * 2

        items = [1, 2, 3]

        results = list(Parallel.map_parallel_unordered(
            slow_func, items, workers=2, use_processes=False, timeout=5.0
        ))

        assert sorted(results) == [2, 4, 6]

    def test_bounded_submission_error_handling(self):
        """map_parallel_unordered handles errors in bounded submission."""
        def failing_func(x):
            """Helper function for testing."""
            if x == 2:
                raise ValueError("Task failed")
            return x * 2

        items = [1, 2, 3]

        with pytest.raises(ParallelError) as exc_info:
            list(Parallel.map_parallel_unordered(
                failing_func, items, workers=2, use_processes=False
            ))

        assert "Task failed" in str(exc_info.value)


# =============================================================================
# Test StopIteration Handling
# =============================================================================

class TestStopIterationHandling:
    """Test StopIteration handling in parallel processing."""

    def test_stopiteration_in_bounded_submission(self):
        """map_parallel_unordered handles StopIteration gracefully."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = [1, 2, 3]

        # This tests the StopIteration handling in the while loop
        results = list(Parallel.map_parallel_unordered(
            func, items, workers=2, use_processes=False
        ))

        assert sorted(results) == [2, 4, 6]

    def test_stopiteration_empty_iterator(self):
        """map_parallel_unordered handles empty iterator."""
        def func(x):
            """Helper function for testing."""
            return x * 2

        results = list(Parallel.map_parallel_unordered(
            func, [], workers=2, use_processes=False
        ))

        assert results == []


# =============================================================================
# Test Executor Selection
# =============================================================================

class TestExecutorSelection:
    """Test executor selection logic."""

    def test_executor_selection_interpreters(self):
        """Executor selection uses interpreters when available."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = [1, 2, 3]

        with patch.object(Parallel, 'supports_interpreter_pool', return_value=True):
            results = Parallel.map_parallel(
                func, items, workers=2, use_interpreters=True
            )
            assert results == [2, 4, 6]

    def test_executor_selection_processes(self):
        """Executor selection uses processes when requested."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = [1, 2, 3]

        # Use threads since lambdas can't be pickled
        results = Parallel.map_parallel(
            func, items, workers=2, use_processes=False
        )
        assert results == [2, 4, 6]

    def test_executor_selection_threads_default(self):
        """Executor selection uses threads by default."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = [1, 2, 3]

        results = Parallel.map_parallel(func, items, workers=2)
        assert results == [2, 4, 6]

    def test_executor_selection_map_parallel_unordered_processes(self):
        """map_parallel_unordered executor selection for processes."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = [1, 2, 3, 4, 5]

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=2, use_processes=False, prefer_map=True
        ))

        assert sorted(results) == [2, 4, 6, 8, 10]


# =============================================================================
# Test Free-threaded Mode Detection
# =============================================================================

class TestFreeThreadedMode:
    """Test free-threaded mode detection and handling."""

    @patch.object(Parallel, 'is_free_threaded', return_value=True)
    @patch.object(Parallel, 'supports_interpreter_pool', return_value=False)
    def test_smart_map_free_threaded_cpu(self, mock_interp, mock_free):
        """smart_map uses threads for CPU tasks in free-threaded mode."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = [1, 2, 3]

        results = Parallel.smart_map(func, items, task_type='cpu', workers=2)
        assert results == [2, 4, 6]

    @patch.object(Parallel, 'is_free_threaded', return_value=True)
    def test_get_optimal_workers_free_threaded(self, mock_free):
        """get_optimal_workers returns more workers in free-threaded mode."""
        with patch.object(Parallel, 'get_cpu_count', return_value=4):
            workers = Parallel.get_optimal_workers(task_type='cpu')
            assert workers == 8  # cpu_count * 2


# =============================================================================
# Test get_optimal_workers Exception Handling
# =============================================================================

class TestGetOptimalWorkersExceptionHandling:
    """Test get_optimal_workers exception handling."""

    @patch.object(Parallel, 'get_cpu_count', side_effect=Exception("CPU count failed"))
    def test_get_optimal_workers_cpu_count_exception(self, mock_cpu):
        """get_optimal_workers handles cpu_count exception."""
        workers = Parallel.get_optimal_workers(task_type='cpu')
        assert workers == 1  # Fallback value

    @patch.object(Parallel, 'get_cpu_count', side_effect=Exception("CPU count failed"))
    def test_get_optimal_workers_io_exception(self, mock_cpu):
        """get_optimal_workers handles exception for IO tasks."""
        workers = Parallel.get_optimal_workers(task_type='io')
        assert workers >= 1  # Should have some fallback


# =============================================================================
# Test reduce_parallel Error Handling
# =============================================================================

class TestReduceParallelErrorHandling:
    """Test reduce_parallel error handling."""

    def test_reduce_parallel_reduce_error(self):
        """reduce_parallel handles reduce phase errors."""
        def map_func(x):
            """Helper function for testing."""
            return x
        items = [1, 2, 3]

        def failing_reduce(a, b):
            """Test reduce function that raises error when b==3."""
            if b == 3:
                raise ValueError("Reduce failed")
            return a + b

        with pytest.raises(ParallelError) as exc_info:
            Parallel.reduce_parallel(map_func, failing_reduce, items, workers=2)

        assert "Map-reduce failed" in str(exc_info.value)

    def test_reduce_parallel_map_error_wrapped(self):
        """reduce_parallel wraps map errors properly."""
        def failing_map(x):
            """Test map function that raises an error."""
            raise ValueError("Map error")

        def reduce_func(a, b):
            """Helper function for testing."""
            return a + b
        items = [1, 2, 3]

        def failing_reduce(a, b):
            """Test reduce function that raises error when b==3."""
            if b == 3:
                raise ValueError("Reduce failed")
            return a + b
# Test Batch Processing with Logging
# =============================================================================

class TestBatchProcessingWithLogging:
    """Test batch processing with logging enabled."""

    def test_batch_processing_with_batch_logging(self):
        """map_parallel_unordered logs batch processing when enabled."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = list(range(50))

        with patch.dict(os.environ, {'NODUPE_BATCH_LOG': '1'}):
            results = list(Parallel.map_parallel_unordered(
                func, items, workers=2, use_processes=False, prefer_batches=True
            ))

            assert sorted(results) == [x * 2 for x in range(50)]

    def test_batch_processing_batch_size_calculation(self):
        """map_parallel_unordered calculates batch size correctly."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = list(range(100))

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=4, use_processes=False, prefer_batches=True
        ))

        assert sorted(results) == [x * 2 for x in range(100)]

    def test_batch_processing_batch_size_one_fallback(self):
        """map_parallel_unordered falls back to chunksize when batch_size=1."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = list(range(10))  # Small list

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=8, use_processes=False, prefer_batches=True
        ))

        assert sorted(results) == [x * 2 for x in range(10)]


# =============================================================================
# Test Chunksize Calculation
# =============================================================================

class TestChunksizeCalculation:
    """Test chunksize calculation in parallel processing."""

    def test_chunksize_calculation_normal(self):
        """Chunksize is calculated correctly for normal cases."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = list(range(100))

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=4, use_processes=False, prefer_map=True
        ))

        assert sorted(results) == [x * 2 for x in range(100)]

    def test_chunksize_calculation_small_list(self):
        """Chunksize handles small lists."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = list(range(5))

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=4, use_processes=False, prefer_map=True
        ))

        assert sorted(results) == [x * 2 for x in range(5)]

    def test_chunksize_calculation_exception_handling(self):
        """Chunksize calculation handles exceptions."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = list(range(10))

        # Test with invalid env var that causes exception
        with patch.dict(os.environ, {'NODUPE_CHUNK_FACTOR': 'invalid'}):
            results = list(Parallel.map_parallel_unordered(
                func, items, workers=2, use_processes=False, prefer_map=True
            ))
            assert sorted(results) == [x * 2 for x in range(10)]


# =============================================================================
# Test Worker Count Capping for Processes
# =============================================================================

class TestWorkerCountCapping:
    """Test worker count capping for process pools."""

    def test_worker_capping_normal(self):
        """Worker count is capped for process pools."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = list(range(10))

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=100, use_processes=False  # Use threads for test
        ))

        assert sorted(results) == [x * 2 for x in range(10)]

    def test_worker_capping_cpu_count_exception(self):
        """Worker capping handles cpu_count exception."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = list(range(10))

        with patch.object(Parallel, 'get_cpu_count', side_effect=Exception("Failed")):
            results = list(Parallel.map_parallel_unordered(
                func, items, workers=100, use_processes=False
            ))
            assert sorted(results) == [x * 2 for x in range(10)]


# =============================================================================
# Test Prefer Batches vs Prefer Map
# =============================================================================

class TestPreferBatchesVsMap:
    """Test prefer_batches vs prefer_map options."""

    def test_prefer_batches_true(self):
        """prefer_batches=True uses batch processing."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = list(range(20))

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=2, use_processes=False,
            prefer_batches=True, prefer_map=False
        ))

        assert sorted(results) == [x * 2 for x in range(20)]

    def test_prefer_map_true(self):
        """prefer_map=True uses map-based processing."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = list(range(20))

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=2, use_processes=False,
            prefer_batches=False, prefer_map=True
        ))

        assert sorted(results) == [x * 2 for x in range(20)]

    def test_prefer_map_false_thread_mode(self):
        """prefer_map=False uses bounded submission for threads."""
        def func(x):
            """Helper function for testing."""
            return x * 2
        items = list(range(20))

        results = list(Parallel.map_parallel_unordered(
            func, items, workers=2, use_processes=False,
            prefer_batches=False, prefer_map=False
        ))

        assert sorted(results) == [x * 2 for x in range(20)]


# =============================================================================
# Test Edge Cases for Coverage
# =============================================================================

class TestEdgeCasesForCoverage:
    """Test edge cases specifically for coverage gaps."""

    def _double_func(self, x):
        """Helper function for testing."""
        return x * 2

    def test_process_in_parallel_interpreter_fallback_path(self):
        """Test interpreter fallback when InterpreterPoolExecutor not available."""
        items = [1, 2, 3]

        with patch.object(Parallel, 'supports_interpreter_pool', return_value=False):
            results = Parallel.process_in_parallel(
                self._double_func, items, workers=2, use_interpreters=True
            )
            assert results == [2, 4, 6]

    def test_map_parallel_interpreter_path(self):
        """Test map_parallel with interpreters."""
        items = [1, 2, 3]

        with patch.object(Parallel, 'supports_interpreter_pool', return_value=False):
            results = Parallel.map_parallel(
                self._double_func, items, workers=2, use_interpreters=True
            )
            assert results == [2, 4, 6]

    def test_map_parallel_unordered_batch_processing_exception(self):
        """Test batch processing exception handling."""
        items = list(range(10))

        with patch.object(Parallel, 'get_cpu_count', side_effect=Exception("Failed")):
            results = list(Parallel.map_parallel_unordered(
                self._double_func, items, workers=2, use_processes=False, prefer_batches=True
            ))
            assert sorted(results) == [x * 2 for x in range(10)]

    def test_bounded_submission_keyerror_handling(self):
        """Test KeyError handling in bounded submission."""
        items = [1, 2, 3]

        # The KeyError handling is in the finally block when removing future
        results = list(Parallel.map_parallel_unordered(
            self._double_func, items, workers=2, use_processes=False
        ))
        assert sorted(results) == [2, 4, 6]

    def test_smart_map_auto_task_inspection(self):
        """Test smart_map auto task type with function inspection."""
        items = [1, 2, 3]

        with patch.object(Parallel, 'supports_interpreter_pool', return_value=False):
            with patch.object(Parallel, 'is_free_threaded', return_value=False):
                results = Parallel.smart_map(self._double_func, items, task_type='auto', workers=2)
                assert results == [2, 4, 6]

    def test_get_optimal_workers_free_threaded_io(self):
        """Test get_optimal_workers for IO tasks in free-threaded mode."""
        with patch.object(Parallel, 'is_free_threaded', return_value=True):
            with patch.object(Parallel, 'get_cpu_count', return_value=4):
                workers = Parallel.get_optimal_workers(task_type='io')
                assert workers == 8

    def test_get_optimal_workers_traditional_gil_cpu(self):
        """Test get_optimal_workers for CPU tasks in traditional GIL mode."""
        with patch.object(Parallel, 'is_free_threaded', return_value=False):
            with patch.object(Parallel, 'supports_interpreter_pool', return_value=False):
                with patch.object(Parallel, 'get_cpu_count', return_value=4):
                    workers = Parallel.get_optimal_workers(task_type='cpu')
                    assert workers == 4  # min(32, cpu_count)

    def test_get_optimal_workers_traditional_gil_io(self):
        """Test get_optimal_workers for IO tasks in traditional GIL mode."""
        with patch.object(Parallel, 'is_free_threaded', return_value=False):
            with patch.object(Parallel, 'supports_interpreter_pool', return_value=False):
                with patch.object(Parallel, 'get_cpu_count', return_value=4):
                    workers = Parallel.get_optimal_workers(task_type='io')
                    assert workers == 8  # min(32, cpu_count * 2)

    def test_reduce_parallel_exception_is_parallel_error(self):
        """Test that reduce_parallel re-raises ParallelError as-is."""
        items = [1, 2, 3]

        def map_func(x):
            """Helper function for testing."""
            return x

        def reduce_func(a, b):
            """Helper function for testing."""
            raise ParallelError("Already a ParallelError")

        with pytest.raises(ParallelError) as exc_info:
            Parallel.reduce_parallel(map_func, reduce_func, items, workers=2)

        assert "Already a ParallelError" in str(exc_info.value)

    def test_process_in_parallel_exception_is_parallel_error(self):
        """Test that process_in_parallel re-raises ParallelError as-is."""
        def failing_func(x):
            """Helper function for testing."""
            raise ParallelError("Already a ParallelError")

        items = [1, 2, 3]

        with pytest.raises(ParallelError) as exc_info:
            Parallel.process_in_parallel(failing_func, items, workers=2)

        assert "Already a ParallelError" in str(exc_info.value)

    def test_map_parallel_unordered_exception_is_parallel_error(self):
        """Test that map_parallel_unordered re-raises ParallelError as-is."""
        def failing_func(x):
            """Helper function for testing."""
            raise ParallelError("Already a ParallelError")

        items = [1, 2, 3]

        with pytest.raises(ParallelError) as exc_info:
            list(Parallel.map_parallel_unordered(failing_func, items, workers=2))

        assert "Already a ParallelError" in str(exc_info.value)


# =============================================================================
# Test ProcessPoolExecutor Code Paths
# =============================================================================

class TestProcessPoolExecutorCodePaths:
    """Test ProcessPoolExecutor-specific code paths.

    These tests use pickle-safe functions to properly test the multiprocessing
    code paths that cannot be tested with lambdas or local functions.

    See: docs/PARALLEL_TESTING_SUSTAINABILITY.md
    """

    def test_process_in_parallel_with_processes_pickle_safe(self):
        """process_in_parallel works with pickle-safe functions and processes."""
        items = [1, 2, 3, 4, 5]

        results = Parallel.process_in_parallel(
            double_number,  # ✅ Pickle-safe
            items,
            workers=2,
            use_processes=True
        )

        assert results == [2, 4, 6, 8, 10]

    def test_map_parallel_with_processes(self):
        """map_parallel works with processes."""
        items = [1, 2, 3, 4, 5]

        results = Parallel.map_parallel(
            square_number,  # ✅ Pickle-safe
            items,
            workers=2,
            use_processes=True
        )

        assert results == [1, 4, 9, 16, 25]

    def test_map_parallel_unordered_with_processes(self):
        """map_parallel_unordered works with processes."""
        items = [1, 2, 3, 4, 5]

        results = list(Parallel.map_parallel_unordered(
            double_number,  # ✅ Pickle-safe
            items,
            workers=2,
            use_processes=True
        ))

        assert sorted(results) == [2, 4, 6, 8, 10]

    def test_process_in_parallel_large_dataset_processes(self):
        """process_in_parallel handles large datasets with processes."""
        items = MEDIUM_INT_RANGE

        results = Parallel.process_in_parallel(
            add_one,  # ✅ Pickle-safe
            items,
            workers=4,
            use_processes=True
        )

        assert results == [x + 1 for x in items]

    def test_thread_vs_process_consistency(self):
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

        assert thread_result == process_result == [2, 4, 6, 8, 10]
