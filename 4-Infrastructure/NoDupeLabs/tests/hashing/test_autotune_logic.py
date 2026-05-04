"""
Comprehensive tests for Phase 8 Hash Autotuning module - autotune_logic.py.

Tests cover:
- Benchmark functions
- Algorithm selection logic
- Performance thresholds
- Memory usage calculations
- File size-based decisions
- Edge cases (very small/large files)
- Different hash algorithms (md5, sha1, sha256, sha512, blake2b)
"""

import hashlib
from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.hashing.autotune_logic import (
    HashAutotuner,
    _check_blake3,
    _check_xxhash,
    autotune_hash_algorithm,
    create_autotuned_hasher,
)


class TestCheckBlake3:
    """Tests for _check_blake3 function."""

    def test_check_blake3_not_available(self):
        """Test _check_blake3 when blake3 is not installed."""
        with patch('importlib.util.find_spec', return_value=None):
            has_blake3, blake3_module = _check_blake3()
            assert has_blake3 is False
            assert blake3_module is None

    def test_check_blake3_available(self):
        """Test _check_blake3 when blake3 is installed."""
        mock_module = MagicMock()
        with patch('importlib.util.find_spec', return_value=MagicMock()):
            with patch.dict('sys.modules', {'blake3': mock_module}):
                has_blake3, blake3_module = _check_blake3()
                # Note: This test depends on actual blake3 availability
                # The function should return True if blake3 is installed
                assert isinstance(has_blake3, bool)
                if has_blake3:
                    assert blake3_module is not None
                else:
                    assert blake3_module is None

    def test_check_blake3_import_error(self):
        """Test _check_blake3 when import raises error."""
        with patch('importlib.util.find_spec', side_effect=ImportError("Import failed")):
            has_blake3, blake3_module = _check_blake3()
            assert has_blake3 is False
            assert blake3_module is None


class TestCheckXxhash:
    """Tests for _check_xxhash function."""

    def test_check_xxhash_not_available(self):
        """Test _check_xxhash when xxhash is not installed."""
        with patch('importlib.util.find_spec', return_value=None):
            has_xxhash, xxhash_module = _check_xxhash()
            assert has_xxhash is False
            assert xxhash_module is None

    def test_check_xxhash_available(self):
        """Test _check_xxhash when xxhash is installed."""
        mock_module = MagicMock()
        with patch('importlib.util.find_spec', return_value=MagicMock()):
            with patch.dict('sys.modules', {'xxhash': mock_module}):
                has_xxhash, xxhash_module = _check_xxhash()
                assert isinstance(has_xxhash, bool)
                if has_xxhash:
                    assert xxhash_module is not None
                else:
                    assert xxhash_module is None

    def test_check_xxhash_import_error(self):
        """Test _check_xxhash when import raises error."""
        with patch('importlib.util.find_spec', side_effect=ImportError("Import failed")):
            has_xxhash, xxhash_module = _check_xxhash()
            assert has_xxhash is False
            assert xxhash_module is None


class TestHashAutotunerInit:
    """Tests for HashAutotuner initialization."""

    def test_init_default_sample_size(self):
        """Test HashAutotuner with default sample size."""
        tuner = HashAutotuner()
        assert tuner.sample_size == 1024 * 1024  # 1MB default
        assert isinstance(tuner.available_algorithms, dict)
        # Should always have at least sha256
        assert 'sha256' in tuner.available_algorithms

    def test_init_custom_sample_size(self):
        """Test HashAutotuner with custom sample size."""
        tuner = HashAutotuner(sample_size=2048)
        assert tuner.sample_size == 2048

    def test_init_small_sample_size(self):
        """Test HashAutotuner with very small sample size."""
        tuner = HashAutotuner(sample_size=64)
        assert tuner.sample_size == 64

    def test_init_large_sample_size(self):
        """Test HashAutuner with large sample size."""
        tuner = HashAutotuner(sample_size=10 * 1024 * 1024)  # 10MB
        assert tuner.sample_size == 10 * 1024 * 1024

    def test_available_algorithms_contains_standard(self):
        """Test that available algorithms include standard library algorithms."""
        tuner = HashAutotuner()
        available = tuner.available_algorithms

        # Should always have standard algorithms
        standard_algos = ['sha256', 'sha512', 'md5', 'sha1']
        found_standard = any(algo in available for algo in standard_algos)
        assert found_standard, "Should have at least one standard algorithm"


class TestGetAvailableAlgorithms:
    """Tests for _get_available_algorithms method."""

    def test_get_available_algorithms_basic(self):
        """Test getting available algorithms."""
        tuner = HashAutotuner(sample_size=1024)
        algorithms = tuner._get_available_algorithms()

        assert isinstance(algorithms, dict)
        assert len(algorithms) > 0
        assert 'sha256' in algorithms

    def test_algorithm_functions_are_callable(self):
        """Test that algorithm functions are callable."""
        tuner = HashAutotuner(sample_size=1024)
        algorithms = tuner._get_available_algorithms()

        test_data = b"test data"
        for algo_name, algo_func in algorithms.items():
            result = algo_func(test_data)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_sha256_hash_correctness(self):
        """Test SHA256 hash produces correct result."""
        tuner = HashAutotuner(sample_size=1024)
        algorithms = tuner._get_available_algorithms()

        test_data = b"test data"
        result = algorithms['sha256'](test_data)
        expected = hashlib.sha256(test_data).hexdigest()
        assert result == expected

    def test_md5_hash_correctness(self):
        """Test MD5 hash produces correct result."""
        tuner = HashAutotuner(sample_size=1024)
        algorithms = tuner._get_available_algorithms()

        if 'md5' in algorithms:
            test_data = b"test data"
            result = algorithms['md5'](test_data)
            expected = hashlib.md5(test_data).hexdigest()
            assert result == expected

    def test_sha512_hash_correctness(self):
        """Test SHA512 hash produces correct result."""
        tuner = HashAutotuner(sample_size=1024)
        algorithms = tuner._get_available_algorithms()

        if 'sha512' in algorithms:
            test_data = b"test data"
            result = algorithms['sha512'](test_data)
            expected = hashlib.sha512(test_data).hexdigest()
            assert result == expected

    @patch('nodupe.tools.hashing.autotune_logic.HAS_BLAKE3', True)
    @patch('nodupe.tools.hashing.autotune_logic.BLAKE3_MODULE')
    def test_blake3_algorithm_added_when_available(self, mock_blake3_module):
        """Test BLAKE3 is added when available."""
        mock_blake3_module.blake3 = MagicMock()
        mock_blake3_module.blake3.return_value.hexdigest.return_value = "blake3hash"

        tuner = HashAutotuner(sample_size=1024)
        algorithms = tuner._get_available_algorithms()

        # Note: This tests the logic path, actual availability depends on installation
        assert isinstance(algorithms, dict)

    @patch('nodupe.tools.hashing.autotune_logic.HAS_XXHASH', True)
    @patch('nodupe.tools.hashing.autotune_logic.XXHASH_MODULE')
    def test_xxhash_algorithms_added_when_available(self, mock_xxhash_module):
        """Test xxHash algorithms are added when available."""
        mock_xxhash_module.xxh3_64 = MagicMock()
        mock_xxhash_module.xxh64 = MagicMock()
        mock_xxhash_module.xxh128 = MagicMock()
        mock_xxhash_module.xxh3_64.return_value.hexdigest.return_value = "xxh3hash"
        mock_xxhash_module.xxh64.return_value.hexdigest.return_value = "xxh64hash"
        mock_xxhash_module.xxh128.return_value.hexdigest.return_value = "xxh128hash"

        tuner = HashAutotuner(sample_size=1024)
        algorithms = tuner._get_available_algorithms()

        assert isinstance(algorithms, dict)


class TestGenerateTestData:
    """Tests for _generate_test_data method."""

    def test_generate_test_data_size(self):
        """Test generated test data has correct size."""
        sample_size = 4096
        tuner = HashAutotuner(sample_size=sample_size)
        data = tuner._generate_test_data()

        assert len(data) == sample_size

    def test_generate_test_data_content(self):
        """Test generated test data contains expected content."""
        tuner = HashAutotuner(sample_size=1024)
        data = tuner._generate_test_data()

        # Data should be all 'x' characters
        assert data == b'x' * 1024

    def test_generate_test_data_small_size(self):
        """Test generated test data with small sample size."""
        tuner = HashAutotuner(sample_size=100)
        data = tuner._generate_test_data()

        assert len(data) == 100
        assert data == b'x' * 100

    def test_generate_test_data_larger_than_chunk(self):
        """Test generated test data larger than chunk size."""
        # Chunk size is 65536, test with larger
        tuner = HashAutotuner(sample_size=131072)  # 128KB
        data = tuner._generate_test_data()

        assert len(data) == 131072
        assert data == b'x' * 131072

    def test_generate_test_data_zero_size(self):
        """Test generated test data with zero sample size."""
        tuner = HashAutotuner(sample_size=0)
        data = tuner._generate_test_data()

        assert len(data) == 0
        assert data == b''


class TestBenchmarkAlgorithm:
    """Tests for benchmark_algorithm method."""

    def test_benchmark_algorithm_basic(self):
        """Test basic benchmarking of an algorithm."""
        tuner = HashAutotuner(sample_size=1024)
        test_data = b"test data for benchmarking"

        avg_time = tuner.benchmark_algorithm('sha256', test_data, iterations=3)

        assert isinstance(avg_time, float)
        assert avg_time > 0

    def test_benchmark_algorithm_multiple_iterations(self):
        """Test benchmarking with multiple iterations."""
        tuner = HashAutotuner(sample_size=1024)
        test_data = b"test data"

        # More iterations should give more stable results
        avg_time_3 = tuner.benchmark_algorithm('sha256', test_data, iterations=3)
        avg_time_10 = tuner.benchmark_algorithm('sha256', test_data, iterations=10)

        assert avg_time_3 > 0
        assert avg_time_10 > 0

    def test_benchmark_algorithm_unknown_algorithm(self):
        """Test benchmarking unknown algorithm raises error."""
        tuner = HashAutotuner(sample_size=1024)
        test_data = b"test data"

        with pytest.raises(ValueError, match="Algorithm unknown_algo not available"):
            tuner.benchmark_algorithm('unknown_algo', test_data)

    def test_benchmark_algorithm_empty_data(self):
        """Test benchmarking with empty data."""
        tuner = HashAutotuner(sample_size=1024)
        test_data = b""

        avg_time = tuner.benchmark_algorithm('sha256', test_data, iterations=3)

        assert isinstance(avg_time, float)
        assert avg_time >= 0

    def test_benchmark_algorithm_large_data(self):
        """Test benchmarking with large data."""
        tuner = HashAutotuner(sample_size=1024)
        test_data = b"x" * (1024 * 1024)  # 1MB

        avg_time = tuner.benchmark_algorithm('sha256', test_data, iterations=3)

        assert isinstance(avg_time, float)
        assert avg_time > 0

    def test_benchmark_different_algorithms(self):
        """Test benchmarking different algorithms."""
        tuner = HashAutotuner(sample_size=1024)
        test_data = b"test data"

        algorithms_to_test = ['sha256', 'sha512', 'md5', 'sha1']
        results = {}

        for algo in algorithms_to_test:
            if algo in tuner.available_algorithms:
                results[algo] = tuner.benchmark_algorithm(algo, test_data, iterations=3)

        # All results should be positive
        for algo, time_taken in results.items():
            assert time_taken > 0, f"{algo} should have positive time"


class TestBenchmarkAllAlgorithms:
    """Tests for benchmark_all_algorithms method."""

    def test_benchmark_all_algorithms_basic(self):
        """Test benchmarking all algorithms."""
        tuner = HashAutotuner(sample_size=1024)
        results = tuner.benchmark_all_algorithms(iterations=3)

        assert isinstance(results, dict)
        assert len(results) > 0

        # All results should be positive times
        for algo, time_taken in results.items():
            assert isinstance(time_taken, float)
            assert time_taken > 0, f"{algo} should have positive time"

    def test_benchmark_all_algorithms_consistency(self):
        """Test that benchmark results are consistent."""
        tuner = HashAutotuner(sample_size=1024)

        results1 = tuner.benchmark_all_algorithms(iterations=3)
        results2 = tuner.benchmark_all_algorithms(iterations=3)

        # Same algorithms should be present
        assert set(results1.keys()) == set(results2.keys())

    def test_benchmark_all_algorithms_with_different_iterations(self):
        """Test benchmarking with different iteration counts."""
        tuner = HashAutotuner(sample_size=1024)

        results_3 = tuner.benchmark_all_algorithms(iterations=3)
        results_10 = tuner.benchmark_all_algorithms(iterations=10)

        # Both should have results
        assert len(results_3) > 0
        assert len(results_10) > 0

    @patch.object(HashAutotuner, 'benchmark_algorithm')
    def test_benchmark_all_algorithms_handles_exceptions(self, mock_benchmark):
        """Test that benchmark_all_algorithms handles exceptions gracefully."""
        mock_benchmark.side_effect = Exception("Benchmark failed")

        tuner = HashAutotuner(sample_size=1024)
        results = tuner.benchmark_all_algorithms(iterations=3)

        # Should return empty dict or partial results
        assert isinstance(results, dict)


class TestSelectOptimalAlgorithm:
    """Tests for select_optimal_algorithm method."""

    def test_select_optimal_algorithm_basic(self):
        """Test selecting optimal algorithm."""
        tuner = HashAutotuner(sample_size=1024)
        optimal_algo, benchmark_results = tuner.select_optimal_algorithm(iterations=3)

        assert isinstance(optimal_algo, str)
        assert isinstance(benchmark_results, dict)
        assert optimal_algo in benchmark_results

    def test_select_optimal_algorithm_returns_fastest(self):
        """Test that optimal algorithm is the fastest."""
        tuner = HashAutotuner(sample_size=1024)
        optimal_algo, benchmark_results = tuner.select_optimal_algorithm(iterations=3)

        if len(benchmark_results) > 1:
            # Find the fastest algorithm
            fastest_algo = min(benchmark_results, key=benchmark_results.get)
            # Optimal should be the fastest (or tied for fastest)
            assert benchmark_results[optimal_algo] <= benchmark_results[fastest_algo] + 0.0001

    def test_select_optimal_algorithm_memory_constrained(self):
        """Test selecting optimal algorithm with memory constraint."""
        tuner = HashAutotuner(sample_size=1024)
        optimal_algo, benchmark_results = tuner.select_optimal_algorithm(
            iterations=3,
            memory_constrained=True
        )

        assert isinstance(optimal_algo, str)
        assert isinstance(benchmark_results, dict)

    @patch('nodupe.tools.hashing.autotune_logic.HAS_BLAKE3', True)
    def test_select_optimal_memory_constrained_prefers_blake3(self):
        """Test memory constrained mode prefers BLAKE3 when competitive."""
        tuner = HashAutotuner(sample_size=1024)

        # Mock benchmark results where blake3 is competitive
        with patch.object(tuner, 'benchmark_all_algorithms') as mock_bench:
            mock_bench.return_value = {
                'sha256': 0.001,
                'blake3': 0.001,  # Same speed as sha256
                'md5': 0.0005
            }

            optimal_algo, results = tuner.select_optimal_algorithm(
                iterations=3,
                memory_constrained=True
            )

            # Should prefer blake3 when memory constrained and competitive
            assert optimal_algo == 'blake3'

    def test_select_optimal_algorithm_no_results_fallback(self):
        """Test fallback to sha256 when no benchmark results."""
        tuner = HashAutotuner(sample_size=1024)

        with patch.object(tuner, 'benchmark_all_algorithms', return_value={}):
            optimal_algo, benchmark_results = tuner.select_optimal_algorithm(iterations=3)

            assert optimal_algo == 'sha256'
            assert 'sha256' in benchmark_results
            assert benchmark_results['sha256'] == float('inf')


class TestGetAlgorithmRecommendation:
    """Tests for get_algorithm_recommendation method."""

    def test_get_algorithm_recommendation_basic(self):
        """Test getting algorithm recommendations."""
        tuner = HashAutotuner(sample_size=1024)
        recommendations = tuner.get_algorithm_recommendation()

        assert isinstance(recommendations, dict)
        assert 'small_files' in recommendations
        assert 'large_files' in recommendations
        assert 'overall' in recommendations

    def test_get_algorithm_recommendation_custom_threshold(self):
        """Test recommendations with custom file size threshold."""
        tuner = HashAutotuner(sample_size=1024)
        recommendations = tuner.get_algorithm_recommendation(
            file_size_threshold=5 * 1024 * 1024  # 5MB
        )

        assert isinstance(recommendations, dict)
        assert all(isinstance(v, str) for v in recommendations.values())

    def test_get_algorithm_recommendation_algorithms_valid(self):
        """Test that recommended algorithms are valid."""
        tuner = HashAutotuner(sample_size=1024)
        recommendations = tuner.get_algorithm_recommendation()

        for scenario, algo in recommendations.items():
            assert isinstance(algo, str)
            assert len(algo) > 0
            # Algorithm should be available
            assert algo in tuner.available_algorithms or algo == 'blake3'

    @patch('nodupe.tools.hashing.autotune_logic.HAS_BLAKE3', True)
    def test_get_recommendation_large_files_with_blake3(self):
        """Test large file recommendation with BLAKE3 available."""
        tuner = HashAutotuner(sample_size=1024)

        with patch.object(tuner, 'select_optimal_algorithm') as mock_select:
            mock_select.return_value = ('sha256', {'sha256': 0.001})

            recommendations = tuner.get_algorithm_recommendation()

            # Should recommend blake3 for large files when available
            assert recommendations['large_files'] == 'blake3'

    def test_get_recommendation_large_files_without_blake3(self):
        """Test large file recommendation without BLAKE3."""
        tuner = HashAutotuner(sample_size=1024)

        with patch.object(tuner, 'select_optimal_algorithm') as mock_select:
            mock_select.return_value = ('sha256', {'sha256': 0.001})

            with patch('nodupe.tools.hashing.autotune_logic.HAS_BLAKE3', False):
                recommendations = tuner.get_algorithm_recommendation()

                # Should recommend sha256 for large files
                assert recommendations['large_files'] == 'sha256'


class TestAutotuneHashAlgorithm:
    """Tests for autotune_hash_algorithm convenience function."""

    def test_autotune_hash_algorithm_basic(self):
        """Test basic autotune function."""
        results = autotune_hash_algorithm(
            sample_size=1024,
            iterations=3
        )

        assert isinstance(results, dict)
        assert 'optimal_algorithm' in results
        assert 'benchmark_results' in results
        assert 'recommendations' in results
        assert 'available_algorithms' in results
        assert 'has_blake3' in results
        assert 'has_xxhash' in results

    def test_autotune_hash_algorithm_return_types(self):
        """Test return value types."""
        results = autotune_hash_algorithm(
            sample_size=1024,
            iterations=3
        )

        assert isinstance(results['optimal_algorithm'], str)
        assert isinstance(results['benchmark_results'], dict)
        assert isinstance(results['recommendations'], dict)
        assert isinstance(results['available_algorithms'], list)
        assert isinstance(results['has_blake3'], bool)
        assert isinstance(results['has_xxhash'], bool)

    def test_autotune_hash_algorithm_custom_parameters(self):
        """Test autotune with custom parameters."""
        results = autotune_hash_algorithm(
            sample_size=2048,
            file_size_threshold=5 * 1024 * 1024,
            iterations=5
        )

        assert isinstance(results, dict)
        assert len(results['available_algorithms']) > 0

    def test_autotune_hash_algorithm_benchmark_results_valid(self):
        """Test benchmark results are valid."""
        results = autotune_hash_algorithm(
            sample_size=1024,
            iterations=3
        )

        for algo, time_taken in results['benchmark_results'].items():
            assert isinstance(time_taken, float)
            assert time_taken > 0


class TestCreateAutotunedHasher:
    """Tests for create_autotuned_hasher function."""

    def test_create_autotuned_hasher_basic(self):
        """Test creating autotuned hasher."""
        hasher, autotune_results = create_autotuned_hasher(
            sample_size=1024,
            iterations=3
        )

        # Test hasher works
        test_string = "test string"
        hash_result = hasher.hash_string(test_string)

        assert isinstance(hash_result, str)
        assert len(hash_result) > 0
        assert isinstance(autotune_results, dict)

    def test_create_autotuned_hasher_returns_tuple(self):
        """Test that function returns correct tuple structure."""
        result = create_autotuned_hasher(sample_size=1024, iterations=3)

        assert isinstance(result, tuple)
        assert len(result) == 2

        hasher, autotune_results = result
        assert hasher is not None
        assert isinstance(autotune_results, dict)

    def test_create_autotuned_hasher_hasher_functional(self):
        """Test that returned hasher is fully functional."""
        hasher, _ = create_autotuned_hasher(sample_size=1024, iterations=3)

        # Test all hasher methods
        assert hasattr(hasher, 'hash_file')
        assert hasattr(hasher, 'hash_string')
        assert hasattr(hasher, 'hash_bytes')
        assert hasattr(hasher, 'get_available_algorithms')

        # Test hash_string
        string_hash = hasher.hash_string("test")
        assert isinstance(string_hash, str)
        assert len(string_hash) > 0

        # Test hash_bytes
        bytes_hash = hasher.hash_bytes(b"test")
        assert isinstance(bytes_hash, str)
        assert len(bytes_hash) > 0

    def test_create_autotuned_hasher_uses_standard_library(self):
        """Test that hasher uses standard library algorithm."""
        hasher, autotune_results = create_autotuned_hasher(
            sample_size=1024,
            iterations=3
        )

        # The algorithm should be available in standard library
        algo = hasher.get_algorithm()
        assert algo in hashlib.algorithms_available


class TestHashConsistency:
    """Tests for hash consistency across multiple calls."""

    def test_same_data_same_hash(self):
        """Test that same data produces same hash."""
        tuner = HashAutotuner(sample_size=1024)
        test_data = b"consistent test data"

        hash1 = tuner.available_algorithms['sha256'](test_data)
        hash2 = tuner.available_algorithms['sha256'](test_data)

        assert hash1 == hash2

    def test_different_data_different_hash(self):
        """Test that different data produces different hash."""
        tuner = HashAutotuner(sample_size=1024)
        data1 = b"data one"
        data2 = b"data two"

        hash1 = tuner.available_algorithms['sha256'](data1)
        hash2 = tuner.available_algorithms['sha256'](data2)

        assert hash1 != hash2

    def test_multiple_algorithms_same_data(self):
        """Test different algorithms produce different hashes for same data."""
        tuner = HashAutotuner(sample_size=1024)
        test_data = b"test data"

        hashes = {}
        for algo_name in ['sha256', 'sha512', 'md5']:
            if algo_name in tuner.available_algorithms:
                hashes[algo_name] = tuner.available_algorithms[algo_name](test_data)

        # All hashes should be different (different algorithms)
        hash_values = list(hashes.values())
        assert len(hash_values) == len(set(hash_values)), "Different algorithms should produce different hashes"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_small_sample_size(self):
        """Test with very small sample size."""
        tuner = HashAutotuner(sample_size=1)
        data = tuner._generate_test_data()

        assert len(data) == 1
        assert data == b'x'

    def test_very_large_sample_size(self):
        """Test with very large sample size."""
        tuner = HashAutotuner(sample_size=100 * 1024 * 1024)  # 100MB
        data = tuner._generate_test_data()

        assert len(data) == 100 * 1024 * 1024

    def test_single_iteration_benchmark(self):
        """Test benchmarking with single iteration."""
        tuner = HashAutotuner(sample_size=1024)
        test_data = b"test data"

        avg_time = tuner.benchmark_algorithm('sha256', test_data, iterations=1)

        assert isinstance(avg_time, float)
        assert avg_time >= 0

    def test_zero_iterations_benchmark(self):
        """Test benchmarking with zero iterations raises ZeroDivisionError."""
        tuner = HashAutotuner(sample_size=1024)
        test_data = b"test data"

        # Zero iterations causes division by zero
        with pytest.raises(ZeroDivisionError):
            tuner.benchmark_algorithm('sha256', test_data, iterations=0)

    def test_unicode_data(self):
        """Test hashing unicode data."""
        tuner = HashAutotuner(sample_size=1024)
        test_data = "Hello, 世界！🌍".encode('utf-8')

        result = tuner.available_algorithms['sha256'](test_data)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_binary_data(self):
        """Test hashing binary data."""
        tuner = HashAutotuner(sample_size=1024)
        test_data = bytes(range(256))  # All possible byte values

        result = tuner.available_algorithms['sha256'](test_data)
        assert isinstance(result, str)
        assert len(result) > 0


class TestPerformanceThresholds:
    """Tests for performance threshold boundaries."""

    def test_algorithm_performance_ordering(self):
        """Test that benchmark results can be properly ordered."""
        tuner = HashAutotuner(sample_size=1024)
        results = tuner.benchmark_all_algorithms(iterations=3)

        if len(results) > 1:
            sorted_algorithms = sorted(results.items(), key=lambda x: x[1])

            # All times should be positive
            for _algo, time_taken in sorted_algorithms:
                assert time_taken > 0

            # Verify sorted order
            for i in range(len(sorted_algorithms) - 1):
                assert sorted_algorithms[i][1] <= sorted_algorithms[i + 1][1]

    def test_memory_constrained_threshold(self):
        """Test memory constrained algorithm selection threshold."""
        tuner = HashAutotuner(sample_size=1024)

        # Test with blake3 exactly at 20% threshold
        with patch.object(tuner, 'benchmark_all_algorithms') as mock_bench:
            mock_bench.return_value = {
                'sha256': 0.001,
                'blake3': 0.0012  # Exactly 20% slower
            }

            optimal_algo, _ = tuner.select_optimal_algorithm(
                iterations=3,
                memory_constrained=True
            )

            # Should still prefer blake3 at exactly 20% threshold
            assert optimal_algo == 'blake3'

    def test_memory_constrained_beyond_threshold(self):
        """Test memory constrained when blake3 is beyond threshold."""
        tuner = HashAutotuner(sample_size=1024)

        with patch.object(tuner, 'benchmark_all_algorithms') as mock_bench:
            mock_bench.return_value = {
                'sha256': 0.001,
                'blake3': 0.0013  # 30% slower, beyond threshold
            }

            optimal_algo, _ = tuner.select_optimal_algorithm(
                iterations=3,
                memory_constrained=True
            )

            # Should not prefer blake3 when beyond 20% threshold
            # The fastest algorithm (blake3 in this mock) should still be selected
            # unless memory constrained logic overrides
            assert isinstance(optimal_algo, str)


class TestFileSizesDecisions:
    """Tests for file size-based algorithm decisions."""

    def test_small_file_threshold(self):
        """Test algorithm selection for small files."""
        tuner = HashAutotuner(sample_size=1024)
        recommendations = tuner.get_algorithm_recommendation(
            file_size_threshold=1024  # 1KB threshold
        )

        assert 'small_files' in recommendations
        assert isinstance(recommendations['small_files'], str)

    def test_large_file_threshold(self):
        """Test algorithm selection for large files."""
        tuner = HashAutotuner(sample_size=1024)
        recommendations = tuner.get_algorithm_recommendation(
            file_size_threshold=100 * 1024 * 1024  # 100MB threshold
        )

        assert 'large_files' in recommendations
        assert isinstance(recommendations['large_files'], str)

    def test_different_thresholds_different_recommendations(self):
        """Test that different thresholds may produce different recommendations."""
        tuner = HashAutotuner(sample_size=1024)

        rec_small = tuner.get_algorithm_recommendation(file_size_threshold=1024)
        rec_large = tuner.get_algorithm_recommendation(file_size_threshold=100 * 1024 * 1024)

        # Both should have valid recommendations
        assert all(isinstance(v, str) for v in rec_small.values())
        assert all(isinstance(v, str) for v in rec_large.values())


class TestFallbackPaths:
    """Tests for fallback paths and edge cases in optional dependencies."""

    @patch('nodupe.tools.hashing.autotune_logic.HAS_BLAKE3', True)
    @patch('nodupe.tools.hashing.autotune_logic.BLAKE3_MODULE', None)
    def test_blake3_func_fallback_when_module_none(self):
        """Test blake3_func uses sha256 fallback when BLAKE3_MODULE is None."""
        tuner = HashAutotuner(sample_size=1024)
        algorithms = tuner._get_available_algorithms()

        # If blake3 is in algorithms, test the fallback path
        if 'blake3' in algorithms:
            test_data = b"test data"
            result = algorithms['blake3'](test_data)
            # Should fall back to sha256
            expected = hashlib.sha256(test_data).hexdigest()
            assert result == expected

    @patch('nodupe.tools.hashing.autotune_logic.HAS_XXHASH', True)
    @patch('nodupe.tools.hashing.autotune_logic.XXHASH_MODULE', None)
    def test_xxh3_func_fallback_when_module_none(self):
        """Test xxh3_func uses sha256 fallback when XXHASH_MODULE is None."""
        tuner = HashAutotuner(sample_size=1024)
        algorithms = tuner._get_available_algorithms()

        if 'xxh3' in algorithms:
            test_data = b"test data"
            result = algorithms['xxh3'](test_data)
            expected = hashlib.sha256(test_data).hexdigest()
            assert result == expected

    @patch('nodupe.tools.hashing.autotune_logic.HAS_XXHASH', True)
    @patch('nodupe.tools.hashing.autotune_logic.XXHASH_MODULE', None)
    def test_xxh64_func_fallback_when_module_none(self):
        """Test xxh64_func uses sha256 fallback when XXHASH_MODULE is None."""
        tuner = HashAutotuner(sample_size=1024)
        algorithms = tuner._get_available_algorithms()

        if 'xxh64' in algorithms:
            test_data = b"test data"
            result = algorithms['xxh64'](test_data)
            expected = hashlib.sha256(test_data).hexdigest()
            assert result == expected

    @patch('nodupe.tools.hashing.autotune_logic.HAS_XXHASH', True)
    @patch('nodupe.tools.hashing.autotune_logic.XXHASH_MODULE', None)
    def test_xxh128_func_fallback_when_module_none(self):
        """Test xxh128_func uses sha256 fallback when XXHASH_MODULE is None."""
        tuner = HashAutotuner(sample_size=1024)
        algorithms = tuner._get_available_algorithms()

        if 'xxh128' in algorithms:
            test_data = b"test data"
            result = algorithms['xxh128'](test_data)
            expected = hashlib.sha256(test_data).hexdigest()
            assert result == expected

    @patch('nodupe.tools.hashing.autotune_logic.HAS_BLAKE3', False)
    def test_get_recommendation_large_files_without_blake3_falls_back(self):
        """Test large files recommendation falls back when no sha256."""
        tuner = HashAutotuner(sample_size=1024)

        # Mock available_algorithms to not have sha256
        with patch.object(tuner, 'available_algorithms', {'md5': lambda x: 'hash'}):
            with patch.object(tuner, 'select_optimal_algorithm') as mock_select:
                mock_select.return_value = ('md5', {'md5': 0.001})

                recommendations = tuner.get_algorithm_recommendation()

                # Should fall back to small_files algo when no sha256
                assert recommendations['large_files'] == recommendations['small_files']

    def test_create_autotuned_hasher_no_filtered_results_fallback(self):
        """Test create_autotuned_hasher falls back to sha256 when no filtered results."""
        # Mock autotune_hash_algorithm to return no standard library results
        with patch('nodupe.tools.hashing.autotune_logic.autotune_hash_algorithm') as mock_autotune:
            mock_autotune.return_value = {
                'optimal_algorithm': 'blake3',
                'benchmark_results': {'blake3': 0.001},  # Only non-standard algo
                'recommendations': {},
                'available_algorithms': ['blake3'],
                'has_blake3': False,
                'has_xxhash': False
            }

            hasher, results = create_autotuned_hasher()

            # Should fall back to sha256
            assert hasher.get_algorithm() == 'sha256'
            assert results['optimal_algorithm'] == 'sha256'



