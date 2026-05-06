"""
Comprehensive tests for Phase 7 Time Sync Module - Sync Utilities.

Tests for nodupe/tools/time_sync/sync_utils.py covering:
- NTP query functions
- Time drift calculations
- Sync correction
- Error handling
- Network failure scenarios
- Mock time sources for deterministic testing
"""

import socket
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.time_sync.sync_utils import (  # Constants; Classes; Functions
    DEFAULT_ATTEMPTS,
    DEFAULT_MAX_ACCEPTABLE_DELAY,
    DEFAULT_SMOOTHING_ALPHA,
    DEFAULT_TIMEOUT,
    FASTDATE_FRAC_BITS,
    FASTDATE_FRAC_SCALE,
    FASTDATE_SECONDS_BITS,
    FASTDATE_SECONDS_MAX,
    NTP_PACKET_STRUCT,
    NTP_TIMESTAMP_STRUCT,
    NTP_TO_UNIX,
    DNSCache,
    FastDate64Encoder,
    MonotonicTimeCalculator,
    NTPResponse,
    ParallelNTPClient,
    ParallelQueryResult,
    PerformanceMetrics,
    TargetedFileScanner,
    clear_global_caches,
    get_global_dns_cache,
    get_global_metrics,
    performance_timer,
)

# =============================================================================
# Constants Tests
# =============================================================================

class TestConstants:
    """Tests for module constants."""

    def test_ntp_to_unix_constant(self):
        """Test NTP_TO_UNIX constant value."""
        assert NTP_TO_UNIX == 2208988800

    def test_default_timeout(self):
        """Test DEFAULT_TIMEOUT constant."""
        assert DEFAULT_TIMEOUT == 3.0

    def test_default_attempts(self):
        """Test DEFAULT_ATTEMPTS constant."""
        assert DEFAULT_ATTEMPTS == 2

    def test_default_max_acceptable_delay(self):
        """Test DEFAULT_MAX_ACCEPTABLE_DELAY constant."""
        assert DEFAULT_MAX_ACCEPTABLE_DELAY == 0.5

    def test_default_smoothing_alpha(self):
        """Test DEFAULT_SMOOTHING_ALPHA constant."""
        assert DEFAULT_SMOOTHING_ALPHA == 0.3

    def test_precompiled_struct_formats(self):
        """Test precompiled struct formats."""
        assert NTP_PACKET_STRUCT.format == "!12I"
        assert NTP_TIMESTAMP_STRUCT.format == "!II"

    def test_fastdate64_constants(self):
        """Test FastDate64 constants."""
        assert FASTDATE_SECONDS_BITS == 34
        assert FASTDATE_FRAC_BITS == 30
        assert FASTDATE_FRAC_SCALE == (1 << 30)
        assert FASTDATE_SECONDS_MAX == ((1 << 34) - 1)


# =============================================================================
# NTPResponse Tests
# =============================================================================

class TestNTPResponse:
    """Tests for NTPResponse dataclass."""

    def test_ntp_response_creation(self):
        """Test NTPResponse creation with all fields."""
        response = NTPResponse(
            server_time=1700000000.0,
            offset=0.05,
            delay=0.03,
            host="time.google.com",
            address=("216.239.35.0", 123),
            attempt=1,
            timestamp=1700000000.0
        )

        assert response.server_time == 1700000000.0
        assert response.offset == 0.05
        assert response.delay == 0.03
        assert response.host == "time.google.com"
        assert response.address == ("216.239.35.0", 123)
        assert response.attempt == 1
        assert response.timestamp == 1700000000.0

    def test_ntp_response_default_values(self):
        """Test NTPResponse with default values where applicable."""
        response = NTPResponse(
            server_time=1700000000.0,
            offset=0.0,
            delay=0.0,
            host="time.google.com",
            address=("127.0.0.1", 123),
            attempt=0,
            timestamp=1700000000.0
        )

        assert response.offset == 0.0
        assert response.delay == 0.0
        assert response.attempt == 0


# =============================================================================
# ParallelQueryResult Tests
# =============================================================================

class TestParallelQueryResult:
    """Tests for ParallelQueryResult dataclass."""

    def test_parallel_query_result_success(self):
        """Test ParallelQueryResult for successful query."""
        response = NTPResponse(
            server_time=1700000000.0,
            offset=0.05,
            delay=0.03,
            host="time.google.com",
            address=("216.239.35.0", 123),
            attempt=1,
            timestamp=1700000000.0
        )

        result = ParallelQueryResult(
            success=True,
            best_response=response,
            all_responses=[response],
            errors=[]
        )

        assert result.success is True
        assert result.best_response is response
        assert len(result.all_responses) == 1
        assert len(result.errors) == 0

    def test_parallel_query_result_failure(self):
        """Test ParallelQueryResult for failed query."""
        result = ParallelQueryResult(
            success=False,
            best_response=None,
            all_responses=[],
            errors=[("time.google.com", Exception("Timeout"))]
        )

        assert result.success is False
        assert result.best_response is None
        assert len(result.all_responses) == 0
        assert len(result.errors) == 1

    def test_parallel_query_result_multiple_responses(self):
        """Test ParallelQueryResult with multiple responses."""
        responses = [
            NTPResponse(
                server_time=1700000000.0 + i,
                offset=0.05 + i * 0.01,
                delay=0.03 + i * 0.01,
                host=f"server{i}.com",
                address=("127.0.0.1", 123),
                attempt=i,
                timestamp=1700000000.0
            )
            for i in range(3)
        ]

        result = ParallelQueryResult(
            success=True,
            best_response=responses[0],
            all_responses=responses,
            errors=[]
        )

        assert len(result.all_responses) == 3
        assert result.best_response.delay == 0.03  # Best (lowest) delay


# =============================================================================
# DNSCache Tests
# =============================================================================

class TestDNSCache:
    """Tests for DNSCache class."""

    def test_dns_cache_initialization(self):
        """Test DNSCache initialization with defaults."""
        cache = DNSCache()
        assert cache._ttl == 30.0
        assert cache._max_size == 100
        assert len(cache._cache) == 0

    def test_dns_cache_custom_initialization(self):
        """Test DNSCache initialization with custom values."""
        cache = DNSCache(ttl=60.0, max_size=200)
        assert cache._ttl == 60.0
        assert cache._max_size == 200

    def test_dns_cache_set_and_get(self):
        """Test DNSCache set and get operations."""
        cache = DNSCache()
        addresses = [(2, 2, 17, '', ('216.239.35.0', 123))]

        cache.set("time.google.com", 123, addresses)
        result = cache.get("time.google.com", 123)

        assert result == addresses

    def test_dns_cache_miss(self):
        """Test DNSCache get for non-existent entry."""
        cache = DNSCache()
        result = cache.get("unknown.com", 123)
        assert result is None

    def test_dns_cache_ttl_expiration(self):
        """Test DNSCache TTL expiration."""
        cache = DNSCache(ttl=1.0)
        addresses = [(2, 2, 17, '', ('216.239.35.0', 123))]

        cache.set("time.google.com", 123, addresses)

        # Immediately get - should exist
        result = cache.get("time.google.com", 123)
        assert result == addresses

        # After TTL expires
        with patch('nodupe.tools.time_sync.sync_utils.time.time', return_value=time.time() + 2.0):
            result = cache.get("time.google.com", 123)
            assert result is None

    def test_dns_cache_max_size_eviction(self):
        """Test DNSCache max size eviction (LRU)."""
        cache = DNSCache(max_size=3)

        # Add 3 entries
        cache.set("server1.com", 123, [("addr1", 123)])
        cache.set("server2.com", 123, [("addr2", 123)])
        cache.set("server3.com", 123, [("addr3", 123)])

        # Access server1 to make it recently used
        cache.get("server1.com", 123)

        # Add 4th entry - should evict server2 (least recently used)
        cache.set("server4.com", 123, [("addr4", 123)])

        assert cache.get("server1.com", 123) is not None  # Recently used
        assert cache.get("server2.com", 123) is None  # Evicted
        assert cache.get("server3.com", 123) is not None
        assert cache.get("server4.com", 123) is not None

    def test_dns_cache_clear(self):
        """Test DNSCache clear operation."""
        cache = DNSCache()
        cache.set("time.google.com", 123, [("addr", 123)])
        cache.set("time.cloudflare.com", 123, [("addr", 123)])

        cache.clear()

        assert cache.get("time.google.com", 123) is None
        assert cache.get("time.cloudflare.com", 123) is None

    def test_dns_cache_invalidate(self):
        """Test DNSCache invalidate operation."""
        cache = DNSCache()
        cache.set("time.google.com", 123, [("addr", 123)])
        cache.set("time.cloudflare.com", 123, [("addr", 123)])

        cache.invalidate("time.google.com", 123)

        assert cache.get("time.google.com", 123) is None
        assert cache.get("time.cloudflare.com", 123) is not None

    def test_dns_cache_invalidate_nonexistent(self):
        """Test DNSCache invalidate for non-existent entry."""
        cache = DNSCache()
        # Should not raise
        cache.invalidate("unknown.com", 123)

    def test_dns_cache_different_ports(self):
        """Test DNSCache with different ports."""
        cache = DNSCache()
        cache.set("time.google.com", 123, [("addr1", 123)])
        cache.set("time.google.com", 1234, [("addr2", 1234)])

        assert cache.get("time.google.com", 123) == [("addr1", 123)]
        assert cache.get("time.google.com", 1234) == [("addr2", 1234)]

    def test_dns_cache_thread_safety(self):
        """Test DNSCache thread safety with concurrent access."""
        import threading

        cache = DNSCache(max_size=100)
        errors = []

        def worker(thread_id):
            """Thread worker for concurrent DNS cache access testing."""
            try:
                for i in range(10):
                    cache.set(f"server{thread_id}_{i}.com", 123, [(f"addr{i}", 123)])
                    cache.get(f"server{thread_id}_{i}.com", 123)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


# =============================================================================
# MonotonicTimeCalculator Tests
# =============================================================================

class TestMonotonicTimeCalculator:
    """Tests for MonotonicTimeCalculator class."""

    def test_calculator_initialization(self):
        """Test MonotonicTimeCalculator initialization."""
        calc = MonotonicTimeCalculator()
        assert calc._wall_start is None
        assert calc._mono_start is None

    def test_start_timing(self):
        """Test start_timing returns wall and monotonic timestamps."""
        calc = MonotonicTimeCalculator()

        with patch('nodupe.tools.time_sync.sync_utils.time.time', return_value=1000.0):
            with patch('nodupe.tools.time_sync.sync_utils.time.monotonic', return_value=500.0):
                wall, mono = calc.start_timing()

        assert wall == 1000.0
        assert mono == 500.0
        assert calc._wall_start == 1000.0
        assert calc._mono_start == 500.0

    def test_elapsed_monotonic(self):
        """Test elapsed_monotonic calculation."""
        calc = MonotonicTimeCalculator()

        with patch('nodupe.tools.time_sync.sync_utils.time.time', return_value=1000.0):
            with patch('nodupe.tools.time_sync.sync_utils.time.monotonic', return_value=500.0):
                calc.start_timing()

        with patch('nodupe.tools.time_sync.sync_utils.time.monotonic', return_value=510.0):
            elapsed = calc.elapsed_monotonic()

        assert elapsed == 10.0

    def test_elapsed_monotonic_not_started(self):
        """Test elapsed_monotonic raises when not started."""
        calc = MonotonicTimeCalculator()

        with pytest.raises(ValueError, match="Timing not started"):
            calc.elapsed_monotonic()

    def test_wall_time_from_monotonic(self):
        """Test wall_time_from_monotonic conversion."""
        calc = MonotonicTimeCalculator()

        with patch('nodupe.tools.time_sync.sync_utils.time.time', return_value=1000.0):
            with patch('nodupe.tools.time_sync.sync_utils.time.monotonic', return_value=500.0):
                calc.start_timing()

        # 5 seconds of monotonic elapsed time
        wall_time = calc.wall_time_from_monotonic(5.0)
        assert wall_time == 1005.0

    def test_wall_time_from_monotonic_not_started(self):
        """Test wall_time_from_monotonic raises when not started."""
        calc = MonotonicTimeCalculator()

        with pytest.raises(ValueError, match="Timing not started"):
            calc.wall_time_from_monotonic(5.0)

    def test_calculate_ntp_rtt(self):
        """Test calculate_ntp_rtt calculation."""
        # t1_wall: Client send time
        # t2_wall: Server receive time
        # t3_wall: Server send time
        # t4_mono: Client receive time (monotonic)
        # mono_start: Monotonic start time

        t1_wall = 1000.0
        t2_wall = 1000.05  # Server received 50ms after client sent
        t3_wall = 1000.05  # Server sent immediately
        t4_mono = 10.1     # Client received 100ms after start (monotonic)
        mono_start = 10.0  # Monotonic start

        delay, offset = MonotonicTimeCalculator.calculate_ntp_rtt(
            t1_wall, t2_wall, t3_wall, t4_mono, mono_start
        )

        # t4_wall = t1_wall + (t4_mono - mono_start) = 1000.0 + 0.1 = 1000.1
        # delay = (t4_wall - t1_wall) - (t3_wall - t2_wall) = 0.1 - 0 = 0.1
        # offset = ((t2_wall - t1_wall) + (t3_wall - t4_wall)) / 2 = (0.05 + (-0.05)) / 2 = 0
        assert delay == pytest.approx(0.1, abs=0.001)
        assert offset == pytest.approx(0.0, abs=0.001)

    def test_calculate_ntp_rtt_with_offset(self):
        """Test calculate_ntp_rtt with clock offset."""
        t1_wall = 1000.0
        t2_wall = 1000.1    # Server clock is 100ms ahead
        t3_wall = 1000.1
        t4_mono = 0.15
        mono_start = 0.0

        delay, offset = MonotonicTimeCalculator.calculate_ntp_rtt(
            t1_wall, t2_wall, t3_wall, t4_mono, mono_start
        )

        # t4_wall = 1000.15
        # delay = (1000.15 - 1000.0) - (1000.1 - 1000.1) = 0.15
        # offset = ((1000.1 - 1000.0) + (1000.1 - 1000.15)) / 2 = (0.1 + (-0.05)) / 2 = 0.025
        assert delay == pytest.approx(0.15, abs=0.001)
        assert offset == pytest.approx(0.025, abs=0.001)


# =============================================================================
# TargetedFileScanner Tests
# =============================================================================

class TestTargetedFileScanner:
    """Tests for TargetedFileScanner class."""

    def test_scanner_initialization(self):
        """Test TargetedFileScanner initialization."""
        scanner = TargetedFileScanner()
        assert scanner._max_files == 100
        assert scanner._max_depth == 2

    def test_scanner_custom_initialization(self):
        """Test TargetedFileScanner with custom values."""
        scanner = TargetedFileScanner(max_files=50, max_depth=3)
        assert scanner._max_files == 50
        assert scanner._max_depth == 3

    def test_scanner_trusted_paths(self):
        """Test TargetedFileScanner trusted paths."""
        scanner = TargetedFileScanner()
        expected_paths = ["/etc/adjtime", "/etc/localtime", "/var/log", "/tmp"]
        assert scanner._trusted_paths == expected_paths

    def test_get_recent_file_time_no_files(self):
        """Test get_recent_file_time when no files found."""
        scanner = TargetedFileScanner()

        # Mock os.path.exists to return False for all paths
        with patch('nodupe.tools.time_sync.sync_utils.os.path.exists', return_value=False):
            result = scanner.get_recent_file_time()

        assert result is None

    def test_get_recent_file_time_with_files(self):
        """Test get_recent_file_time with existing files."""
        scanner = TargetedFileScanner()

        # Mock os.path.exists and os.path.getmtime
        with patch('nodupe.tools.time_sync.sync_utils.os.path.exists', return_value=True):
            with patch('nodupe.tools.time_sync.sync_utils.os.path.isfile', return_value=True):
                with patch('nodupe.tools.time_sync.sync_utils.os.path.getmtime', return_value=1700000000.0):
                    result = scanner.get_recent_file_time()

        assert result == 1700000000.0

    def test_get_recent_file_time_invalid_timestamp(self):
        """Test get_recent_file_time filters invalid timestamps."""
        scanner = TargetedFileScanner()

        with patch('nodupe.tools.time_sync.sync_utils.os.path.exists', return_value=True):
            with patch('nodupe.tools.time_sync.sync_utils.os.path.isfile', return_value=True):
                # Timestamp before year 2002 should be filtered
                with patch('nodupe.tools.time_sync.sync_utils.os.path.getmtime', return_value=1000000000.0):
                    result = scanner.get_recent_file_time()

        assert result is None

    def test_get_recent_file_time_additional_paths(self):
        """Test get_recent_file_time with additional paths."""
        scanner = TargetedFileScanner()

        with patch('nodupe.tools.time_sync.sync_utils.os.path.exists', return_value=True):
            with patch('nodupe.tools.time_sync.sync_utils.os.path.isfile', return_value=True):
                with patch('nodupe.tools.time_sync.sync_utils.os.path.getmtime', return_value=1700000000.0):
                    result = scanner.get_recent_file_time(
                        additional_paths=["/custom/path1", "/custom/path2"]
                    )

        assert result == 1700000000.0

    def test_scan_path_nonexistent(self):
        """Test _scan_path for non-existent path."""
        scanner = TargetedFileScanner()

        with patch('nodupe.tools.time_sync.sync_utils.os.path.exists', return_value=False):
            result = scanner._scan_path("/nonexistent", 0)

        assert result == 0.0

    def test_scan_path_file(self):
        """Test _scan_path for single file."""
        scanner = TargetedFileScanner()

        with patch('nodupe.tools.time_sync.sync_utils.os.path.exists', return_value=True):
            with patch('nodupe.tools.time_sync.sync_utils.os.path.isfile', return_value=True):
                with patch('nodupe.tools.time_sync.sync_utils.os.path.getmtime', return_value=1700000000.0):
                    result = scanner._scan_path("/path/to/file.txt", 0)

        assert result == 1700000000.0

    def test_scan_path_directory(self):
        """Test _scan_path for directory."""
        scanner = TargetedFileScanner()

        mock_walk_data = [
            ("/test", ["subdir"], ["file1.txt", "file2.txt"]),
            ("/test/subdir", [], ["file3.txt"]),
        ]

        def mock_getmtime(path):
            """Mock getmtime function for testing file timestamp retrieval."""
            return 1700000000.0

        with patch('nodupe.tools.time_sync.sync_utils.os.path.exists', return_value=True):
            with patch('nodupe.tools.time_sync.sync_utils.os.path.isfile', return_value=False):
                with patch('nodupe.tools.time_sync.sync_utils.os.walk', return_value=mock_walk_data):
                    with patch('nodupe.tools.time_sync.sync_utils.os.path.getmtime', side_effect=mock_getmtime):
                        result = scanner._scan_path("/test", 0)

        assert result == 1700000000.0

    def test_scan_path_depth_limit(self):
        """Test _scan_path respects max_depth."""
        scanner = TargetedFileScanner(max_depth=1)

        mock_walk_data = [
            ("/test", ["subdir1"], ["file1.txt"]),
            ("/test/subdir1", ["subdir2"], ["file2.txt"]),
            ("/test/subdir1/subdir2", [], ["file3.txt"]),  # Should be skipped
        ]

        files_scanned = []

        def mock_getmtime(path):
            """Mock getmtime function for tracking scanned files in depth limit test."""
            files_scanned.append(path)
            return 1700000000.0


        with patch('nodupe.tools.time_sync.sync_utils.os.path.exists', return_value=True):
            with patch('nodupe.tools.time_sync.sync_utils.os.path.isfile', return_value=False):
                with patch('nodupe.tools.time_sync.sync_utils.os.walk', return_value=mock_walk_data):
                    with patch('nodupe.tools.time_sync.sync_utils.os.path.getmtime', side_effect=mock_getmtime):
                        scanner._scan_path("/test", 0)

        # file3.txt in subdir2 should not be scanned (depth > 1)
        assert not any("subdir2" in f for f in files_scanned)

    def test_scan_path_file_count_limit(self):
        """Test _scan_path respects max_files."""
        scanner = TargetedFileScanner(max_files=5)

        mock_walk_data = [
            ("/test", [], [f"file{i}.txt" for i in range(10)]),
        ]

        files_scanned = []

        def mock_getmtime(path):
            """Mock getmtime function for tracking scanned files in depth limit test."""
            files_scanned.append(path)
            return 1700000000.0


        with patch('nodupe.tools.time_sync.sync_utils.os.path.exists', return_value=True):
            with patch('nodupe.tools.time_sync.sync_utils.os.path.isfile', return_value=False):
                with patch('nodupe.tools.time_sync.sync_utils.os.walk', return_value=mock_walk_data):
                    with patch('nodupe.tools.time_sync.sync_utils.os.path.getmtime', side_effect=mock_getmtime):
                        scanner._scan_path("/test", 0)

        # Should stop after max_files
        assert len(files_scanned) <= 5

    def test_scan_path_os_error(self):
        """Test _scan_path handles OSError gracefully."""
        scanner = TargetedFileScanner()

        def mock_getmtime(path):
            """Mock getmtime function that raises OSError for error handling test."""
            raise OSError("Permission denied")


        with patch('nodupe.tools.time_sync.sync_utils.os.path.exists', return_value=True):
            with patch('nodupe.tools.time_sync.sync_utils.os.path.isfile', return_value=True):
                with patch('nodupe.tools.time_sync.sync_utils.os.path.getmtime', side_effect=mock_getmtime):
                    result = scanner._scan_path("/protected/file.txt", 0)

        assert result == 0.0


# =============================================================================
# ParallelNTPClient Tests
# =============================================================================

class TestParallelNTPClient:
    """Tests for ParallelNTPClient class."""

    def test_client_initialization_defaults(self):
        """Test ParallelNTPClient initialization with defaults."""
        client = ParallelNTPClient()
        assert client._timeout == DEFAULT_TIMEOUT
        assert client._max_workers == min(32, (os_cpu_count_or_1() + 4))
        assert isinstance(client._dns_cache, DNSCache)

    def test_client_initialization_custom(self):
        """Test ParallelNTPClient with custom values."""
        dns_cache = DNSCache()
        client = ParallelNTPClient(timeout=5.0, max_workers=16, dns_cache=dns_cache)
        assert client._timeout == 5.0
        assert client._max_workers == 16
        assert client._dns_cache is dns_cache

    def test_executor_lazy_creation(self):
        """Test executor is created lazily."""
        client = ParallelNTPClient()
        assert client._executor is None

        # Access executor property
        executor = client.executor
        assert executor is not None
        assert isinstance(executor, ThreadPoolExecutor)

    def test_executor_recreation_after_shutdown(self):
        """Test executor is recreated after shutdown."""
        client = ParallelNTPClient()
        executor1 = client.executor
        client.shutdown()

        executor2 = client.executor
        assert executor1 is not executor2

    def test_query_hosts_parallel_no_hosts(self):
        """Test query_hosts_parallel with no resolvable hosts."""
        client = ParallelNTPClient()

        with patch.object(client, '_resolve_host_addresses', return_value=[]):
            result = client.query_hosts_parallel(["unresolvable.host"])

        assert result.success is False
        assert result.best_response is None
        assert len(result.errors) == 1

    def test_query_hosts_parallel_single_host(self):
        """Test query_hosts_parallel with single host."""
        client = ParallelNTPClient()

        mock_response = NTPResponse(
            server_time=1700000000.0,
            offset=0.05,
            delay=0.03,
            host="time.google.com",
            address=("216.239.35.0", 123),
            attempt=0,
            timestamp=1700000000.0
        )

        with patch.object(client, '_resolve_host_addresses', return_value=[(2, 2, 17, '', ('216.239.35.0', 123))]):
            with patch.object(client, '_query_single_address', return_value=mock_response):
                result = client.query_hosts_parallel(["time.google.com"])

        assert result.success is True
        assert result.best_response is not None
        assert result.best_response.host == "time.google.com"

    def test_query_hosts_parallel_multiple_hosts(self):
        """Test query_hosts_parallel with multiple hosts."""
        client = ParallelNTPClient()

        responses = {
            "time.google.com": NTPResponse(
                server_time=1700000000.0,
                offset=0.05,
                delay=0.03,
                host="time.google.com",
                address=("216.239.35.0", 123),
                attempt=0,
                timestamp=1700000000.0
            ),
            "time.cloudflare.com": NTPResponse(
                server_time=1700000000.0,
                offset=0.06,
                delay=0.02,  # Better delay
                host="time.cloudflare.com",
                address=("162.159.200.1", 123),
                attempt=0,
                timestamp=1700000000.0
            ),
        }

        def mock_query(query_id, host, addr_info, attempt):

            """Mock query for NTP response simulation."""
            return responses[host]

        def mock_resolve(host):

            """Mock DNS resolver for testing."""
            return [(2, 2, 17, '', ('1.2.3.4', 123))]

        with patch.object(client, '_resolve_host_addresses', side_effect=mock_resolve):
            with patch.object(client, '_query_single_address', side_effect=mock_query):
                result = client.query_hosts_parallel(["time.google.com", "time.cloudflare.com"])

        assert result.success is True
        # Best response should have lowest delay (0.02 from cloudflare)
        assert result.best_response is not None
        # The best_response should be the one with lowest delay
        assert result.best_response.delay <= 0.03

    def test_query_hosts_parallel_early_termination(self):
        """Test query_hosts_parallel early termination on good result."""
        client = ParallelNTPClient()

        good_response = NTPResponse(
            server_time=1700000000.0,
            offset=0.05,
            delay=0.05,  # Below threshold
            host="time.google.com",
            address=("216.239.35.0", 123),
            attempt=0,
            timestamp=1700000000.0
        )

        def mock_query(query_id, host, addr_info, attempt):

            """Mock query for early termination testing."""
            return good_response

        def mock_resolve(host):

            """Mock DNS resolver for testing."""
            return [(2, 2, 17, '', ('1.2.3.4', 123))]

        with patch.object(client, '_resolve_host_addresses', side_effect=mock_resolve):
            with patch.object(client, '_query_single_address', side_effect=mock_query):
                result = client.query_hosts_parallel(
                    ["time.google.com", "time.cloudflare.com"],
                    stop_on_good_result=True,
                    good_delay_threshold=0.1
                )

        assert result.success is True

    def test_query_hosts_parallel_with_errors(self):
        """Test query_hosts_parallel handles errors gracefully."""
        client = ParallelNTPClient()

        def mock_query(query_id, host, addr_info, attempt):

            """Mock query that raises exceptions for error testing."""
            raise Exception("Connection failed")

        def mock_resolve(host):

            """Mock DNS resolver for testing."""
            return [(2, 2, 17, '', ('1.2.3.4', 123))]

        with patch.object(client, '_resolve_host_addresses', side_effect=mock_resolve):
            with patch.object(client, '_query_single_address', side_effect=mock_query):
                result = client.query_hosts_parallel(["time.google.com"])

        assert result.success is False
        assert len(result.errors) > 0

    def test_resolve_host_addresses_cache_hit(self):
        """Test _resolve_host_addresses uses cache."""
        client = ParallelNTPClient()
        cached_addresses = [(2, 2, 17, '', ('216.239.35.0', 123))]
        client._dns_cache.set("time.google.com", 123, cached_addresses)

        result = client._resolve_host_addresses("time.google.com")
        assert result == cached_addresses

    def test_resolve_host_addresses_cache_miss(self):
        """Test _resolve_host_addresses on cache miss."""
        client = ParallelNTPClient()

        mock_addresses = [(2, 2, 17, '', ('216.239.35.0', 123))]

        with patch('nodupe.tools.time_sync.sync_utils.socket.getaddrinfo', return_value=mock_addresses):
            result = client._resolve_host_addresses("time.google.com")

        assert result == mock_addresses
        # Verify it's cached
        assert client._dns_cache.get("time.google.com", 123) == mock_addresses

    def test_resolve_host_addresses_dns_failure(self):
        """Test _resolve_host_addresses handles DNS failure."""
        client = ParallelNTPClient()

        with patch('nodupe.tools.time_sync.sync_utils.socket.getaddrinfo', side_effect=socket.gaierror("DNS failure")):
            result = client._resolve_host_addresses("unresolvable.host")

        assert result == []
        # Verify failure is cached
        assert client._dns_cache.get("unresolvable.host", 123) == []

    def test_query_single_address_success(self):
        """Test _query_single_address successful query."""
        client = ParallelNTPClient(timeout=3.0)

        # Create mock socket with proper recvfrom behavior
        mock_socket = MagicMock()
        mock_response_data = create_mock_ntp_response(t2=1700000000.05, t3=1700000000.05)
        mock_socket.recvfrom.return_value = (mock_response_data, ('216.239.35.0', 123))
        mock_socket.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket.__exit__ = MagicMock(return_value=False)

        with patch('nodupe.tools.time_sync.sync_utils.socket.socket', return_value=mock_socket):
            with patch('nodupe.tools.time_sync.sync_utils.time.time', return_value=1700000000.0):
                with patch('nodupe.tools.time_sync.sync_utils.time.monotonic', return_value=100.0):
                    response = client._query_single_address(
                        query_id=1,
                        host="time.google.com",
                        addr_info=(2, 2, 17, '', ('216.239.35.0', 123)),
                        attempt=0
                    )

        assert response.host == "time.google.com"
        assert response.address == ('216.239.35.0', 123)
        assert response.attempt == 0

    def test_query_single_address_short_response(self):
        """Test _query_single_address with short response."""
        client = ParallelNTPClient()

        mock_socket = MagicMock()
        mock_socket.recvfrom.return_value = (b'short', ('127.0.0.1', 123))  # Less than 48 bytes
        mock_socket.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket.__exit__ = MagicMock(return_value=False)

        with patch('nodupe.tools.time_sync.sync_utils.socket.socket', return_value=mock_socket):
            with patch('nodupe.tools.time_sync.sync_utils.time.time', return_value=1700000000.0):
                with patch('nodupe.tools.time_sync.sync_utils.time.monotonic', return_value=100.0):
                    with pytest.raises(ValueError, match="Short NTP response"):
                        client._query_single_address(
                            query_id=1,
                            host="time.google.com",
                            addr_info=(2, 2, 17, '', ('216.239.35.0', 123)),
                            attempt=0
                        )

    def test_query_single_address_timeout(self):
        """Test _query_single_address timeout."""
        client = ParallelNTPClient(timeout=0.1)

        mock_socket = MagicMock()
        mock_socket.recvfrom.side_effect = socket.timeout("Timeout")
        mock_socket.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket.__exit__ = MagicMock(return_value=False)

        with patch('nodupe.tools.time_sync.sync_utils.socket.socket', return_value=mock_socket):
            with patch('nodupe.tools.time_sync.sync_utils.time.time', return_value=1700000000.0):
                with patch('nodupe.tools.time_sync.sync_utils.time.monotonic', return_value=100.0):
                    with pytest.raises(socket.timeout):
                        client._query_single_address(
                            query_id=1,
                            host="time.google.com",
                            addr_info=(2, 2, 17, '', ('216.239.35.0', 123)),
                            attempt=0
                        )

    def test_to_ntp_conversion(self):
        """Test _to_ntp timestamp conversion."""
        client = ParallelNTPClient()

        # Unix timestamp for 2024-01-01 00:00:00 UTC
        unix_ts = 1704067200.0
        sec, frac = client._to_ntp(unix_ts)

        # NTP timestamp = Unix + NTP_TO_UNIX
        expected_ntp = unix_ts + NTP_TO_UNIX
        assert sec == int(expected_ntp)

    def test_from_ntp_conversion(self):
        """Test _from_ntp timestamp conversion."""
        client = ParallelNTPClient()

        # NTP timestamp
        ntp_sec = int(1704067200.0 + NTP_TO_UNIX)
        ntp_frac = 0

        unix_ts = client._from_ntp(ntp_sec, ntp_frac)
        assert unix_ts == pytest.approx(1704067200.0, abs=1.0)

    def test_to_from_ntp_roundtrip(self):
        """Test _to_ntp and _from_ntp roundtrip."""
        client = ParallelNTPClient()

        original_ts = 1700000000.5
        sec, frac = client._to_ntp(original_ts)
        result_ts = client._from_ntp(sec, frac)

        assert result_ts == pytest.approx(original_ts, abs=0.001)

    def test_shutdown(self):
        """Test shutdown method."""
        client = ParallelNTPClient()
        _ = client.executor  # Create executor

        client.shutdown(wait=True)
        assert client._executor is None

    def test_shutdown_no_wait(self):
        """Test shutdown with wait=False."""
        client = ParallelNTPClient()
        _ = client.executor  # Create executor

        client.shutdown(wait=False)
        assert client._executor is None


# =============================================================================
# FastDate64Encoder Tests
# =============================================================================

class TestFastDate64Encoder:
    """Tests for FastDate64Encoder class."""

    def test_encode_basic(self):
        """Test basic encode operation."""
        ts = 1700000000.0
        encoded = FastDate64Encoder.encode(ts)

        assert isinstance(encoded, int)
        assert encoded > 0

    def test_encode_with_fraction(self):
        """Test encode with fractional seconds."""
        ts = 1700000000.5
        encoded = FastDate64Encoder.encode(ts)

        decoded = FastDate64Encoder.decode(encoded)
        assert decoded == pytest.approx(ts, abs=0.000001)

    def test_encode_negative_raises(self):
        """Test encode raises ValueError for negative timestamps."""
        with pytest.raises(ValueError, match="Negative timestamps"):
            FastDate64Encoder.encode(-1.0)

    def test_encode_overflow_raises(self):
        """Test encode raises OverflowError for too large timestamps."""
        # Timestamp beyond 34 bits
        large_ts = float(1 << 40)
        with pytest.raises(OverflowError):
            FastDate64Encoder.encode(large_ts)

    def test_decode_basic(self):
        """Test basic decode operation."""
        encoded = 12345678901234567890
        decoded = FastDate64Encoder.decode(encoded)

        assert isinstance(decoded, float)
        assert decoded > 0

    def test_encode_decode_roundtrip(self):
        """Test encode/decode roundtrip."""
        test_timestamps = [
            0.0,
            1000000000.0,
            1700000000.0,
            1700000000.123456,
            2000000000.999999,
        ]

        for ts in test_timestamps:
            encoded = FastDate64Encoder.encode(ts)
            decoded = FastDate64Encoder.decode(encoded)
            assert decoded == pytest.approx(ts, abs=0.000001)

    def test_encode_safe_negative(self):
        """Test encode_safe with negative timestamp."""
        result = FastDate64Encoder.encode_safe(-1.0)
        assert result == 0

    def test_encode_safe_overflow(self):
        """Test encode_safe with overflow."""
        large_ts = float(1 << 40)
        result = FastDate64Encoder.encode_safe(large_ts)
        assert result == 0

    def test_encode_safe_valid(self):
        """Test encode_safe with valid timestamp."""
        ts = 1700000000.0
        result = FastDate64Encoder.encode_safe(ts)
        assert result > 0

    def test_decode_safe_invalid(self):
        """Test decode_safe with invalid value."""
        # Any int should decode successfully, but test edge cases
        result = FastDate64Encoder.decode_safe(-1)  # Negative int
        assert isinstance(result, float)

    def test_decode_safe_valid(self):
        """Test decode_safe with valid value."""
        encoded = FastDate64Encoder.encode(1700000000.0)
        result = FastDate64Encoder.decode_safe(encoded)
        assert result == pytest.approx(1700000000.0, abs=0.000001)

    def test_encode_zero(self):
        """Test encode with zero timestamp."""
        encoded = FastDate64Encoder.encode(0.0)
        decoded = FastDate64Encoder.decode(encoded)
        assert decoded == 0.0

    def test_encode_maximum_valid(self):
        """Test encode with maximum valid timestamp."""
        max_ts = float(FASTDATE_SECONDS_MAX)
        encoded = FastDate64Encoder.encode(max_ts)
        decoded = FastDate64Encoder.decode(encoded)
        assert decoded == pytest.approx(max_ts, abs=1.0)


# =============================================================================
# PerformanceMetrics Tests
# =============================================================================

class TestPerformanceMetrics:
    """Tests for PerformanceMetrics class."""

    def test_metrics_initialization(self):
        """Test PerformanceMetrics initialization."""
        metrics = PerformanceMetrics()
        assert metrics._metrics['ntp_queries'] == []
        assert metrics._metrics['dns_cache_hits'] == 0
        assert metrics._metrics['dns_cache_misses'] == 0
        assert metrics._metrics['parallel_queries'] == []
        assert metrics._metrics['fallback_usage'] == []
        assert metrics._metrics['errors'] == []

    def test_record_ntp_query(self):
        """Test record_ntp_query."""
        metrics = PerformanceMetrics()
        metrics.record_ntp_query("time.google.com", 0.05, True, 0.1)

        assert len(metrics._metrics['ntp_queries']) == 1
        query = metrics._metrics['ntp_queries'][0]
        assert query['host'] == "time.google.com"
        assert query['delay'] == 0.05
        assert query['success'] is True
        assert query['duration'] == 0.1

    def test_record_dns_cache_hit(self):
        """Test record_dns_cache_hit."""
        metrics = PerformanceMetrics()
        metrics.record_dns_cache_hit()
        metrics.record_dns_cache_hit()

        assert metrics._metrics['dns_cache_hits'] == 2

    def test_record_dns_cache_miss(self):
        """Test record_dns_cache_miss."""
        metrics = PerformanceMetrics()
        metrics.record_dns_cache_miss()
        metrics.record_dns_cache_miss()
        metrics.record_dns_cache_miss()

        assert metrics._metrics['dns_cache_misses'] == 3

    def test_record_parallel_query(self):
        """Test record_parallel_query."""
        metrics = PerformanceMetrics()
        metrics.record_parallel_query(
            num_hosts=4,
            num_addresses=8,
            success=True,
            duration=0.5,
            best_delay=0.03
        )

        assert len(metrics._metrics['parallel_queries']) == 1
        query = metrics._metrics['parallel_queries'][0]
        assert query['hosts'] == 4
        assert query['addresses'] == 8
        assert query['success'] is True
        assert query['duration'] == 0.5
        assert query['best_delay'] == 0.03

    def test_record_fallback_usage(self):
        """Test record_fallback_usage."""
        metrics = PerformanceMetrics()
        metrics.record_fallback_usage("rtc", 0.0)
        metrics.record_fallback_usage("file", 0.1)

        assert len(metrics._metrics['fallback_usage']) == 2
        assert metrics._metrics['fallback_usage'][0]['method'] == "rtc"
        assert metrics._metrics['fallback_usage'][1]['method'] == "file"

    def test_record_error(self):
        """Test record_error."""
        metrics = PerformanceMetrics()
        metrics.record_error("timeout", "Connection timed out")

        assert len(metrics._metrics['errors']) == 1
        error = metrics._metrics['errors'][0]
        assert error['type'] == "timeout"
        assert error['message'] == "Connection timed out"

    def test_get_summary_empty(self):
        """Test get_summary with no data."""
        metrics = PerformanceMetrics()
        summary = metrics.get_summary()

        assert summary['total_queries'] == 0
        assert summary['success_rate'] == 0.0
        assert summary['avg_delay'] == 0.0
        assert summary['avg_duration'] == 0.0
        assert summary['dns_cache_hit_rate'] == 0.0
        assert summary['total_parallel_queries'] == 0
        assert summary['fallback_count'] == 0
        assert summary['error_count'] == 0

    def test_get_summary_with_data(self):
        """Test get_summary with data."""
        metrics = PerformanceMetrics()

        # Add some queries
        metrics.record_ntp_query("time.google.com", 0.05, True, 0.1)
        metrics.record_ntp_query("time.cloudflare.com", 0.03, True, 0.08)
        metrics.record_ntp_query("time.apple.com", 0.10, False, 0.15)

        # Add DNS stats
        metrics.record_dns_cache_hit()
        metrics.record_dns_cache_hit()
        metrics.record_dns_cache_miss()

        summary = metrics.get_summary()

        assert summary['total_queries'] == 3
        assert summary['success_rate'] == pytest.approx(0.667, rel=0.01)
        assert summary['avg_delay'] == pytest.approx(0.04, rel=0.01)
        assert summary['dns_cache_hit_rate'] == pytest.approx(0.667, rel=0.01)

    def test_get_summary_division_by_zero(self):
        """Test get_summary handles division by zero."""
        metrics = PerformanceMetrics()

        # Add failed queries only
        metrics.record_ntp_query("time.google.com", 0.0, False, 0.1)
        metrics.record_ntp_query("time.cloudflare.com", 0.0, False, 0.1)

        summary = metrics.get_summary()
        # Should not raise, success queries is 0
        assert summary['success_rate'] == 0.0
        assert summary['avg_delay'] == 0.0


# =============================================================================
# Global Functions Tests
# =============================================================================

class TestGlobalFunctions:
    """Tests for global functions."""

    def test_get_global_dns_cache(self):
        """Test get_global_dns_cache returns singleton."""
        cache1 = get_global_dns_cache()
        cache2 = get_global_dns_cache()
        assert cache1 is cache2
        assert isinstance(cache1, DNSCache)

    def test_get_global_metrics(self):
        """Test get_global_metrics returns singleton."""
        metrics1 = get_global_metrics()
        metrics2 = get_global_metrics()
        assert metrics1 is metrics2
        assert isinstance(metrics1, PerformanceMetrics)

    def test_clear_global_caches(self):
        """Test clear_global_caches."""
        cache = get_global_dns_cache()
        cache.set("time.google.com", 123, [("addr", 123)])

        clear_global_caches()

        assert cache.get("time.google.com", 123) is None

    def test_performance_timer_success(self):
        """Test performance_timer context manager."""
        with patch('nodupe.tools.time_sync.sync_utils.logger') as mock_logger:
            with performance_timer("test_operation"):
                pass

        mock_logger.debug.assert_called()

    def test_performance_timer_with_exception(self):
        """Test performance_timer handles exceptions."""
        with patch('nodupe.tools.time_sync.sync_utils.logger') as mock_logger:
            with pytest.raises(ValueError):
                with performance_timer("failing_operation"):
                    raise ValueError("Test error")

        # Should still log duration
        mock_logger.debug.assert_called()


# =============================================================================
# Helper Functions
# =============================================================================

def os_cpu_count_or_1():
    """Get CPU count or 1 if unavailable."""
    import os
    return os.cpu_count() or 1


def create_mock_ntp_response(t2: float, t3: float) -> bytes:
    """Create a mock NTP response packet.

    Args:
        t2: Server receive time
        t3: Server send time

    Returns:
        48-byte NTP response packet
    """
    packet = bytearray(48)

    # Set mode and version in first byte
    packet[0] = 0x24  # LI=0, VN=4, Mode=4 (server)

    # Pack t2 (server receive time)
    t2_ntp = t2 + NTP_TO_UNIX
    t2_sec = int(t2_ntp)
    t2_frac = int((t2_ntp - t2_sec) * (1 << 32))
    NTP_TIMESTAMP_STRUCT.pack_into(packet, 32, t2_sec, t2_frac)

    # Pack t3 (server send time)
    t3_ntp = t3 + NTP_TO_UNIX
    t3_sec = int(t3_ntp)
    t3_frac = int((t3_ntp - t3_sec) * (1 << 32))
    NTP_TIMESTAMP_STRUCT.pack_into(packet, 40, t3_sec, t3_frac)

    return bytes(packet)
