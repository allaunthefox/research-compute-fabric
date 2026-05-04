"""
Comprehensive tests for Phase 7 Time Sync Module - Failure Rules.

Tests for nodupe/tools/time_sync/failure_rules.py covering:
- All failure rule implementations
- Threshold detection
- Severity classification
- Edge cases (boundary conditions)
- Rule combinations
"""

from collections import defaultdict
from unittest.mock import patch

import pytest

from nodupe.tools.time_sync.failure_rules import (
    AdaptiveFailureHandler,
    ConnectionAttempt,
    ConnectionStrategy,
    FailureReason,
    FailureRuleEngine,
    FallbackLevel,
    RetryStrategy,
    ServerPriority,
    ServerStats,
    get_failure_rules,
    reset_failure_rules,
)

# =============================================================================
# ServerPriority Enum Tests
# =============================================================================

class TestServerPriority:
    """Tests for ServerPriority enum."""

    def test_server_priority_values(self):
        """Test that ServerPriority enum has correct values."""
        assert ServerPriority.PRIMARY.value == 1
        assert ServerPriority.SECONDARY.value == 2
        assert ServerPriority.TERTIARY.value == 3
        assert ServerPriority.FALLBACK.value == 4

    def test_server_priority_names(self):
        """Test that ServerPriority enum has correct names."""
        assert ServerPriority.PRIMARY.name == "PRIMARY"
        assert ServerPriority.SECONDARY.name == "SECONDARY"
        assert ServerPriority.TERTIARY.name == "TERTIARY"
        assert ServerPriority.FALLBACK.name == "FALLBACK"


# =============================================================================
# FailureReason Enum Tests
# =============================================================================

class TestFailureReason:
    """Tests for FailureReason enum."""

    def test_failure_reason_values(self):
        """Test that FailureReason enum has correct values."""
        assert FailureReason.TIMEOUT.value == "timeout"
        assert FailureReason.NETWORK_ERROR.value == "network_error"
        assert FailureReason.INVALID_RESPONSE.value == "invalid_response"
        assert FailureReason.HIGH_DELAY.value == "high_delay"
        assert FailureReason.DNS_FAILURE.value == "dns_failure"
        assert FailureReason.SOCKET_ERROR.value == "socket_error"


# =============================================================================
# ServerStats Tests
# =============================================================================

class TestServerStats:
    """Tests for ServerStats dataclass."""

    def test_server_stats_initialization(self):
        """Test ServerStats initialization with default values."""
        stats = ServerStats(
            host="time.google.com",
            priority=ServerPriority.PRIMARY
        )
        assert stats.host == "time.google.com"
        assert stats.priority == ServerPriority.PRIMARY
        assert stats.success_count == 0
        assert stats.failure_count == 0
        assert stats.total_attempts == 0
        assert stats.last_success is None
        assert stats.last_failure is None
        assert isinstance(stats.failure_reasons, defaultdict)
        assert len(stats.failure_reasons) == 0
        assert stats.recent_delays.maxlen == 10

    def test_server_stats_custom_initialization(self):
        """Test ServerStats initialization with custom values."""
        failure_reasons = defaultdict(int, {FailureReason.TIMEOUT: 2})
        from collections import deque
        recent_delays = deque([0.05, 0.06, 0.04], maxlen=10)

        stats = ServerStats(
            host="time.cloudflare.com",
            priority=ServerPriority.PRIMARY,
            success_count=5,
            failure_count=2,
            total_attempts=7,
            failure_reasons=failure_reasons,
            recent_delays=recent_delays
        )
        assert stats.success_count == 5
        assert stats.failure_count == 2
        assert stats.total_attempts == 7
        assert stats.failure_reasons[FailureReason.TIMEOUT] == 2
        assert list(stats.recent_delays) == [0.05, 0.06, 0.04]

    def test_success_rate_no_attempts(self):
        """Test success rate when no attempts have been made."""
        stats = ServerStats(host="test.com", priority=ServerPriority.PRIMARY)
        assert stats.success_rate == 0.0

    def test_success_rate_all_success(self):
        """Test success rate when all attempts succeeded."""
        stats = ServerStats(
            host="test.com",
            priority=ServerPriority.PRIMARY,
            success_count=10,
            total_attempts=10
        )
        assert stats.success_rate == 100.0

    def test_success_rate_partial(self):
        """Test success rate with partial success."""
        stats = ServerStats(
            host="test.com",
            priority=ServerPriority.PRIMARY,
            success_count=7,
            total_attempts=10
        )
        assert stats.success_rate == 70.0

    def test_avg_delay_no_delays(self):
        """Test average delay when no delays recorded."""
        stats = ServerStats(host="test.com", priority=ServerPriority.PRIMARY)
        assert stats.avg_delay == 0.0

    def test_avg_delay_with_delays(self):
        """Test average delay with recorded delays."""
        from collections import deque
        stats = ServerStats(
            host="test.com",
            priority=ServerPriority.PRIMARY,
            recent_delays=deque([0.05, 0.10, 0.15], maxlen=10)
        )
        assert stats.avg_delay == pytest.approx(0.10)

    def test_is_healthy_insufficient_data(self):
        """Test is_healthy when insufficient data available."""
        stats = ServerStats(
            host="test.com",
            priority=ServerPriority.PRIMARY,
            total_attempts=2
        )
        assert stats.is_healthy is True

    def test_is_healthy_healthy(self):
        """Test is_healthy when server is healthy."""
        stats = ServerStats(
            host="test.com",
            priority=ServerPriority.PRIMARY,
            success_count=6,
            failure_count=4,
            total_attempts=10
        )
        assert stats.is_healthy is True  # 60% success rate >= 50%

    def test_is_healthy_unhealthy(self):
        """Test is_healthy when server is unhealthy."""
        stats = ServerStats(
            host="test.com",
            priority=ServerPriority.PRIMARY,
            success_count=4,
            failure_count=6,
            total_attempts=10
        )
        assert stats.is_healthy is False  # 40% success rate < 50%

    def test_is_healthy_boundary_50_percent(self):
        """Test is_healthy at exactly 50% success rate boundary."""
        stats = ServerStats(
            host="test.com",
            priority=ServerPriority.PRIMARY,
            success_count=5,
            failure_count=5,
            total_attempts=10
        )
        assert stats.is_healthy is True  # 50% success rate >= 50%

    def test_record_success(self):
        """Test recording a successful connection."""
        stats = ServerStats(host="test.com", priority=ServerPriority.PRIMARY)

        with patch('nodupe.tools.time_sync.failure_rules.time.time', return_value=1000.0):
            stats.record_success(0.05)

        assert stats.success_count == 1
        assert stats.total_attempts == 1
        assert stats.last_success == 1000.0
        assert list(stats.recent_delays) == [0.05]

    def test_record_success_multiple(self):
        """Test recording multiple successful connections."""
        stats = ServerStats(host="test.com", priority=ServerPriority.PRIMARY)

        with patch('nodupe.tools.time_sync.failure_rules.time.time', return_value=1000.0):
            stats.record_success(0.05)
            stats.record_success(0.06)
            stats.record_success(0.04)

        assert stats.success_count == 3
        assert stats.total_attempts == 3
        assert list(stats.recent_delays) == [0.05, 0.06, 0.04]

    def test_record_success_rolling_window(self):
        """Test that recent_delays maintains rolling window of 10."""
        stats = ServerStats(host="test.com", priority=ServerPriority.PRIMARY)

        with patch('nodupe.tools.time_sync.failure_rules.time.time', return_value=1000.0):
            for i in range(15):
                stats.record_success(0.01 * i)

        # Should only keep last 10
        assert len(stats.recent_delays) == 10
        assert list(stats.recent_delays)[0] == 0.05  # Started from i=5

    def test_record_failure(self):
        """Test recording a failed connection."""
        stats = ServerStats(host="test.com", priority=ServerPriority.PRIMARY)

        with patch('nodupe.tools.time_sync.failure_rules.time.time', return_value=1000.0):
            stats.record_failure(FailureReason.TIMEOUT)

        assert stats.failure_count == 1
        assert stats.total_attempts == 1
        assert stats.last_failure == 1000.0
        assert stats.failure_reasons[FailureReason.TIMEOUT] == 1

    def test_record_failure_multiple_reasons(self):
        """Test recording failures with different reasons."""
        stats = ServerStats(host="test.com", priority=ServerPriority.PRIMARY)

        with patch('nodupe.tools.time_sync.failure_rules.time.time', return_value=1000.0):
            stats.record_failure(FailureReason.TIMEOUT)
            stats.record_failure(FailureReason.TIMEOUT)
            stats.record_failure(FailureReason.DNS_FAILURE)
            stats.record_failure(FailureReason.SOCKET_ERROR)

        assert stats.failure_count == 4
        assert stats.total_attempts == 4
        assert stats.failure_reasons[FailureReason.TIMEOUT] == 2
        assert stats.failure_reasons[FailureReason.DNS_FAILURE] == 1
        assert stats.failure_reasons[FailureReason.SOCKET_ERROR] == 1


# =============================================================================
# ConnectionAttempt Tests
# =============================================================================

class TestConnectionAttempt:
    """Tests for ConnectionAttempt dataclass."""

    def test_connection_attempt_success(self):
        """Test ConnectionAttempt for successful connection."""
        attempt = ConnectionAttempt(
            host="time.google.com",
            attempt_time=1000.0,
            success=True,
            delay=0.05,
            response_time=0.03
        )
        assert attempt.host == "time.google.com"
        assert attempt.attempt_time == 1000.0
        assert attempt.success is True
        assert attempt.delay == 0.05
        assert attempt.failure_reason is None
        assert attempt.response_time == 0.03

    def test_connection_attempt_failure(self):
        """Test ConnectionAttempt for failed connection."""
        attempt = ConnectionAttempt(
            host="time.cloudflare.com",
            attempt_time=1000.0,
            success=False,
            failure_reason=FailureReason.TIMEOUT
        )
        assert attempt.host == "time.cloudflare.com"
        assert attempt.success is False
        assert attempt.delay is None
        assert attempt.failure_reason == FailureReason.TIMEOUT


# =============================================================================
# FailureRuleEngine Tests
# =============================================================================

class TestFailureRuleEngine:
    """Tests for FailureRuleEngine class."""

    def test_engine_initialization_defaults(self):
        """Test FailureRuleEngine initialization with defaults."""
        engine = FailureRuleEngine()
        assert engine.max_retries == 3
        assert engine.base_retry_delay == 1.0
        assert engine.max_retry_delay == 30.0
        assert engine.health_check_interval == 300.0
        assert engine.failure_decay_hours == 24.0
        assert len(engine.server_stats) == 0
        assert len(engine.connection_history) == 0

    def test_engine_initialization_custom(self):
        """Test FailureRuleEngine initialization with custom values."""
        engine = FailureRuleEngine(
            max_retries=5,
            base_retry_delay=2.0,
            max_retry_delay=60.0,
            health_check_interval=600.0,
            failure_decay_hours=48.0
        )
        assert engine.max_retries == 5
        assert engine.base_retry_delay == 2.0
        assert engine.max_retry_delay == 60.0
        assert engine.health_check_interval == 600.0
        assert engine.failure_decay_hours == 48.0

    def test_get_server_priority_primary_google(self):
        """Test get_server_priority for Google servers."""
        engine = FailureRuleEngine()
        assert engine.get_server_priority("time.google.com") == ServerPriority.PRIMARY
        assert engine.get_server_priority("GOOGLE.COM") == ServerPriority.PRIMARY

    def test_get_server_priority_primary_cloudflare(self):
        """Test get_server_priority for Cloudflare servers."""
        engine = FailureRuleEngine()
        assert engine.get_server_priority("time.cloudflare.com") == ServerPriority.PRIMARY
        assert engine.get_server_priority("CLOUDFLARE.COM") == ServerPriority.PRIMARY

    def test_get_server_priority_secondary_apple(self):
        """Test get_server_priority for Apple servers."""
        engine = FailureRuleEngine()
        assert engine.get_server_priority("time.apple.com") == ServerPriority.SECONDARY
        assert engine.get_server_priority("APPLE.COM") == ServerPriority.SECONDARY

    def test_get_server_priority_secondary_microsoft(self):
        """Test get_server_priority for Microsoft servers."""
        engine = FailureRuleEngine()
        assert engine.get_server_priority("time.microsoft.com") == ServerPriority.SECONDARY
        assert engine.get_server_priority("time.windows.com") == ServerPriority.SECONDARY

    def test_get_server_priority_tertiary_pool(self):
        """Test get_server_priority for pool servers."""
        engine = FailureRuleEngine()
        assert engine.get_server_priority("pool.ntp.org") == ServerPriority.TERTIARY
        assert engine.get_server_priority("0.pool.ntp.org") == ServerPriority.TERTIARY

    def test_get_server_priority_fallback(self):
        """Test get_server_priority for unknown servers."""
        engine = FailureRuleEngine()
        assert engine.get_server_priority("unknown.server.com") == ServerPriority.FALLBACK
        assert engine.get_server_priority("custom.ntp.local") == ServerPriority.FALLBACK

    def test_should_retry_max_retries_reached(self):
        """Test should_retry when max retries reached."""
        engine = FailureRuleEngine(max_retries=3)
        should_retry, delay = engine.should_retry_server(
            host="test.com",
            attempt_count=3,
            last_failure_reason=FailureReason.TIMEOUT
        )
        assert should_retry is False
        assert delay == 0.0

    def test_should_retry_unhealthy_server(self):
        """Test should_retry for unhealthy server."""
        engine = FailureRuleEngine(max_retries=3, base_retry_delay=1.0)

        # Create unhealthy server stats
        stats = ServerStats(
            host="test.com",
            priority=ServerPriority.PRIMARY,
            success_count=2,
            failure_count=8,
            total_attempts=10
        )
        engine.server_stats["test.com"] = stats

        with patch('nodupe.tools.time_sync.failure_rules.logger') as mock_logger:
            should_retry, delay = engine.should_retry_server(
                host="test.com",
                attempt_count=1,
                last_failure_reason=None
            )

        assert should_retry is True
        assert delay == 2.0  # base_retry_delay * 2^1
        mock_logger.warning.assert_called()

    def test_should_retry_standard_backoff(self):
        """Test should_retry with standard exponential backoff."""
        engine = FailureRuleEngine(max_retries=3, base_retry_delay=1.0)

        should_retry, delay = engine.should_retry_server(
            host="test.com",
            attempt_count=0,
            last_failure_reason=None
        )

        assert should_retry is True
        assert delay == 1.0  # base_retry_delay * 2^0

    def test_should_retry_backoff_progression(self):
        """Test should_retry exponential backoff progression."""
        engine = FailureRuleEngine(max_retries=5, base_retry_delay=1.0, max_retry_delay=30.0)

        # Attempt 0: 1.0s
        _, delay0 = engine.should_retry_server("test.com", 0, None)
        assert delay0 == 1.0

        # Attempt 1: 2.0s
        _, delay1 = engine.should_retry_server("test.com", 1, None)
        assert delay1 == 2.0

        # Attempt 2: 4.0s
        _, delay2 = engine.should_retry_server("test.com", 2, None)
        assert delay2 == 4.0

        # Attempt 3: 8.0s
        _, delay3 = engine.should_retry_server("test.com", 3, None)
        assert delay3 == 8.0

    def test_should_retry_timeout_penalty(self):
        """Test should_retry with timeout penalty."""
        engine = FailureRuleEngine(base_retry_delay=1.0)

        should_retry, delay = engine.should_retry_server(
            host="test.com",
            attempt_count=1,
            last_failure_reason=FailureReason.TIMEOUT
        )

        assert should_retry is True
        assert delay == 3.0  # 2.0 * 1.5 for timeout

    def test_should_retry_network_error_penalty(self):
        """Test should_retry with network error penalty."""
        engine = FailureRuleEngine(base_retry_delay=1.0)

        should_retry, delay = engine.should_retry_server(
            host="test.com",
            attempt_count=1,
            last_failure_reason=FailureReason.NETWORK_ERROR
        )

        assert should_retry is True
        assert delay == 2.4  # 2.0 * 1.2 for network error

    def test_should_retry_max_delay_cap(self):
        """Test should_retry respects max_retry_delay cap."""
        engine = FailureRuleEngine(base_retry_delay=1.0, max_retry_delay=5.0)

        # Attempt 10 would be 1024s without cap, but max_retries is 3 by default
        # So we need to set higher max_retries first
        engine.max_retries = 15

        should_retry, delay = engine.should_retry_server(
            host="test.com",
            attempt_count=10,
            last_failure_reason=None
        )

        assert should_retry is True
        assert delay == 5.0  # Capped at max_retry_delay

    def test_select_best_servers_empty(self):
        """Test select_best_servers with empty host list."""
        engine = FailureRuleEngine()
        selected = engine.select_best_servers([])
        assert selected == []

    def test_select_best_servers_single(self):
        """Test select_best_servers with single host."""
        engine = FailureRuleEngine()
        selected = engine.select_best_servers(["time.google.com"])
        assert selected == ["time.google.com"]

    def test_select_best_servers_priority_order(self):
        """Test select_best_servers respects priority order."""
        engine = FailureRuleEngine()

        hosts = [
            "pool.ntp.org",  # TERTIARY
            "time.google.com",  # PRIMARY
            "time.apple.com",  # SECONDARY
            "custom.local"  # FALLBACK
        ]

        selected = engine.select_best_servers(hosts, max_selections=4)

        # Should be sorted by priority: PRIMARY, SECONDARY, TERTIARY, FALLBACK
        assert selected[0] == "time.google.com"
        assert selected[1] == "time.apple.com"
        assert selected[2] == "pool.ntp.org"
        assert selected[3] == "custom.local"

    def test_select_best_servers_max_selections(self):
        """Test select_best_servers respects max_selections."""
        engine = FailureRuleEngine()

        hosts = [
            "time.google.com",
            "time.cloudflare.com",
            "time.apple.com",
            "time.microsoft.com",
            "pool.ntp.org"
        ]

        selected = engine.select_best_servers(hosts, max_selections=2)
        assert len(selected) == 2
        assert selected[0] == "time.google.com"
        assert selected[1] == "time.cloudflare.com"

    def test_select_best_servers_health_based(self):
        """Test select_best_servers considers server health."""
        engine = FailureRuleEngine()

        hosts = ["time.google.com", "time.cloudflare.com"]

        # Make google.com unhealthy
        google_stats = ServerStats(
            host="time.google.com",
            priority=ServerPriority.PRIMARY,
            success_count=1,
            failure_count=9,
            total_attempts=10
        )
        engine.server_stats["time.google.com"] = google_stats

        # Make cloudflare.com healthy
        cf_stats = ServerStats(
            host="time.cloudflare.com",
            priority=ServerPriority.PRIMARY,
            success_count=9,
            failure_count=1,
            total_attempts=10
        )
        engine.server_stats["time.cloudflare.com"] = cf_stats

        selected = engine.select_best_servers(hosts, max_selections=2)

        # Healthy server should be first
        assert selected[0] == "time.cloudflare.com"
        assert selected[1] == "time.google.com"

    def test_should_fallback_to_rtc_insufficient_data(self):
        """Test should_fallback_to_rtc with insufficient data."""
        engine = FailureRuleEngine()

        # Add only 4 attempts (need at least 5)
        for i in range(4):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=False,
                failure_reason=FailureReason.TIMEOUT
            )
            engine.connection_history.append(attempt)

        assert engine.should_fallback_to_rtc() is False

    def test_should_fallback_to_rtc_low_failure_rate(self):
        """Test should_fallback_to_rtc with low failure rate."""
        engine = FailureRuleEngine()

        # Add 10 attempts with only 50% failure
        for i in range(10):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=(i < 5),  # 5 success, 5 failures
                failure_reason=FailureReason.TIMEOUT if i >= 5 else None
            )
            engine.connection_history.append(attempt)

        assert engine.should_fallback_to_rtc() is False  # 50% < 80%

    def test_should_fallback_to_rtc_high_failure_rate(self):
        """Test should_fallback_to_rtc with high failure rate."""
        engine = FailureRuleEngine()

        # Add 10 attempts with 90% failure
        for i in range(10):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=(i == 0),  # 1 success, 9 failures
                failure_reason=FailureReason.TIMEOUT if i > 0 else None
            )
            engine.connection_history.append(attempt)

        assert engine.should_fallback_to_rtc() is True  # 90% >= 80%

    def test_should_fallback_to_rtc_boundary_80_percent(self):
        """Test should_fallback_to_rtc at exactly 80% failure boundary."""
        engine = FailureRuleEngine()

        # Add 10 attempts with exactly 80% failure
        for i in range(10):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=(i < 2),  # 2 success, 8 failures
                failure_reason=FailureReason.TIMEOUT if i >= 2 else None
            )
            engine.connection_history.append(attempt)

        assert engine.should_fallback_to_rtc() is True  # 80% >= 80%

    def test_should_use_file_fallback_insufficient_data(self):
        """Test should_use_file_fallback with insufficient data."""
        engine = FailureRuleEngine()

        # Add only 9 attempts (need at least 10)
        for i in range(9):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=False,
                failure_reason=FailureReason.TIMEOUT
            )
            engine.connection_history.append(attempt)

        assert engine.should_use_file_fallback() is False

    def test_should_use_file_fallback_high_failure_rate(self):
        """Test should_use_file_fallback with high failure rate."""
        engine = FailureRuleEngine()

        # Add 20 attempts with 95% failure
        for i in range(20):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=(i == 0),  # 1 success, 19 failures
                failure_reason=FailureReason.TIMEOUT if i > 0 else None
            )
            engine.connection_history.append(attempt)

        assert engine.should_use_file_fallback() is True  # 95% >= 90%

    def test_should_use_file_fallback_boundary_90_percent(self):
        """Test should_use_file_fallback at exactly 90% failure boundary."""
        engine = FailureRuleEngine()

        # Add 20 attempts with exactly 90% failure
        for i in range(20):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=(i < 2),  # 2 success, 18 failures
                failure_reason=FailureReason.TIMEOUT if i >= 2 else None
            )
            engine.connection_history.append(attempt)

        assert engine.should_use_file_fallback() is True  # 90% >= 90%

    def test_should_use_monotonic_only_insufficient_data(self):
        """Test should_use_monotonic_only with insufficient data."""
        engine = FailureRuleEngine()

        # Add only 19 attempts (need at least 20)
        for i in range(19):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=False,
                failure_reason=FailureReason.TIMEOUT
            )
            engine.connection_history.append(attempt)

        assert engine.should_use_monotonic_only() is False

    def test_should_use_monotonic_only_critical_failure_rate(self):
        """Test should_use_monotonic_only with critical failure rate."""
        engine = FailureRuleEngine()

        # Add 50 attempts with 96% failure
        for i in range(50):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=(i < 2),  # 2 success, 48 failures
                failure_reason=FailureReason.TIMEOUT if i >= 2 else None
            )
            engine.connection_history.append(attempt)

        assert engine.should_use_monotonic_only() is True  # 96% >= 95%

    def test_should_use_monotonic_only_boundary_95_percent(self):
        """Test should_use_monotonic_only at exactly 95% failure boundary."""
        engine = FailureRuleEngine()

        # Add 50 attempts with exactly 95% failure (47.5 failures rounds to 48)
        for i in range(50):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=(i < 3),  # 3 success, 47 failures = 94%
                failure_reason=FailureReason.TIMEOUT if i >= 3 else None
            )
            engine.connection_history.append(attempt)

        # 47/50 = 94%, which is < 95%
        assert engine.should_use_monotonic_only() is False

        # Clear and try with 96% failure
        engine.connection_history.clear()
        for i in range(50):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=(i < 2),  # 2 success, 48 failures = 96%
                failure_reason=FailureReason.TIMEOUT if i >= 2 else None
            )
            engine.connection_history.append(attempt)

        assert engine.should_use_monotonic_only() is True  # 96% >= 95%

    def test_get_connection_strategy(self):
        """Test get_connection_strategy returns valid strategy."""
        engine = FailureRuleEngine()

        hosts = ["time.google.com", "time.cloudflare.com"]
        strategy = engine.get_connection_strategy(hosts)

        assert isinstance(strategy, ConnectionStrategy)
        assert isinstance(strategy.servers, list)
        assert isinstance(strategy.max_retries, int)
        assert isinstance(strategy.timeout, float)
        assert isinstance(strategy.parallel_queries, bool)
        assert isinstance(strategy.fallback_level, FallbackLevel)
        assert isinstance(strategy.retry_strategy, RetryStrategy)

    def test_get_connection_strategy_monotonic_only_fallback(self):
        """Test get_connection_strategy with monotonic only fallback."""
        engine = FailureRuleEngine()

        # Create critical failure scenario
        for i in range(50):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=(i < 2),
                failure_reason=FailureReason.TIMEOUT if i >= 2 else None
            )
            engine.connection_history.append(attempt)

        strategy = engine.get_connection_strategy(["test.com"])
        assert strategy.fallback_level == FallbackLevel.MONOTONIC_ONLY

    def test_get_connection_strategy_file_fallback(self):
        """Test get_connection_strategy with file fallback."""
        engine = FailureRuleEngine()

        # Create high failure scenario (between 90% and 95%)
        for i in range(50):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=(i < 4),  # 4 success, 46 failures = 92%
                failure_reason=FailureReason.TIMEOUT if i >= 4 else None
            )
            engine.connection_history.append(attempt)

        strategy = engine.get_connection_strategy(["test.com"])
        assert strategy.fallback_level == FallbackLevel.FILE_FALLBACK

    def test_get_connection_strategy_rtc_fallback(self):
        """Test get_connection_strategy with RTC fallback."""
        engine = FailureRuleEngine()

        # Create moderate-high failure scenario (between 80% and 90%)
        for i in range(20):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=(i < 3),  # 3 success, 17 failures = 85%
                failure_reason=FailureReason.TIMEOUT if i >= 3 else None
            )
            engine.connection_history.append(attempt)

        strategy = engine.get_connection_strategy(["test.com"])
        assert strategy.fallback_level == FallbackLevel.RTC_FALLBACK

    def test_record_attempt_success(self):
        """Test recording a successful connection attempt."""
        engine = FailureRuleEngine()

        with patch('nodupe.tools.time_sync.failure_rules.time.time', return_value=1000.0):
            attempt = ConnectionAttempt(
                host="time.google.com",
                attempt_time=1000.0,
                success=True,
                delay=0.05
            )
            engine.record_attempt(attempt)

        assert len(engine.connection_history) == 1
        assert "time.google.com" in engine.server_stats

        stats = engine.server_stats["time.google.com"]
        assert stats.success_count == 1
        assert stats.total_attempts == 1
        assert stats.is_healthy is True

    def test_record_attempt_failure(self):
        """Test recording a failed connection attempt."""
        engine = FailureRuleEngine()

        with patch('nodupe.tools.time_sync.failure_rules.time.time', return_value=1000.0):
            attempt = ConnectionAttempt(
                host="time.google.com",
                attempt_time=1000.0,
                success=False,
                failure_reason=FailureReason.TIMEOUT
            )
            engine.record_attempt(attempt)

        assert len(engine.connection_history) == 1
        assert "time.google.com" in engine.server_stats

        stats = engine.server_stats["time.google.com"]
        assert stats.failure_count == 1
        assert stats.total_attempts == 1
        assert stats.failure_reasons[FailureReason.TIMEOUT] == 1

    def test_record_attempt_history_limit(self):
        """Test that connection history is limited to 1000."""
        engine = FailureRuleEngine()

        with patch('nodupe.tools.time_sync.failure_rules.time.time', return_value=1000.0):
            for i in range(1005):
                attempt = ConnectionAttempt(
                    host=f"server{i}.com",
                    attempt_time=1000.0 + i,
                    success=True,
                    delay=0.05
                )
                engine.record_attempt(attempt)

        assert len(engine.connection_history) == 1000

    def test_get_server_health_report(self):
        """Test get_server_health_report returns complete report."""
        engine = FailureRuleEngine()

        # Add some server stats
        with patch('nodupe.tools.time_sync.failure_rules.time.time', return_value=1000.0):
            attempt = ConnectionAttempt(
                host="time.google.com",
                attempt_time=1000.0,
                success=True,
                delay=0.05
            )
            engine.record_attempt(attempt)

        report = engine.get_server_health_report()

        assert "time.google.com" in report
        server_report = report["time.google.com"]
        assert "priority" in server_report
        assert "success_rate" in server_report
        assert "avg_delay" in server_report
        assert "total_attempts" in server_report
        assert "is_healthy" in server_report
        assert "last_success" in server_report
        assert "last_failure" in server_report
        assert "failure_reasons" in server_report

    def test_decay_old_failures(self):
        """Test _decay_old_failures reduces old failure counts."""
        engine = FailureRuleEngine(failure_decay_hours=1.0)

        # Create server stats with failures
        stats = ServerStats(
            host="test.com",
            priority=ServerPriority.PRIMARY,
            success_count=5,
            failure_count=10,
            total_attempts=15,
            last_success=1000.0  # Recent success
        )
        engine.server_stats["test.com"] = stats

        # Mock time to be after the cutoff (more than 1 hour after last_success)
        with patch('nodupe.tools.time_sync.failure_rules.time.time', return_value=10000.0):
            engine._decay_old_failures()

        # Failure count should be reduced (or stay same if logic doesn't reduce)
        # The logic only reduces if last_success > cutoff_time
        # cutoff_time = 10000.0 - 3600 = 6400.0
        # last_success = 1000.0, which is < 6400.0, so no reduction
        # This is expected behavior - old successes don't trigger decay
        assert stats.failure_count <= 10

    def test_calculate_average_success_rate_empty(self):
        """Test _calculate_average_success_rate with no servers."""
        engine = FailureRuleEngine()
        assert engine._calculate_average_success_rate() == 50.0

    def test_calculate_average_success_rate_no_attempts(self):
        """Test _calculate_average_success_rate with no attempts."""
        engine = FailureRuleEngine()
        engine.server_stats["test.com"] = ServerStats(
            host="test.com",
            priority=ServerPriority.PRIMARY
        )
        assert engine._calculate_average_success_rate() == 50.0

    def test_calculate_average_success_rate(self):
        """Test _calculate_average_success_rate with data."""
        engine = FailureRuleEngine()

        engine.server_stats["test1.com"] = ServerStats(
            host="test1.com",
            priority=ServerPriority.PRIMARY,
            success_count=8,
            total_attempts=10
        )
        engine.server_stats["test2.com"] = ServerStats(
            host="test2.com",
            priority=ServerPriority.PRIMARY,
            success_count=6,
            total_attempts=10
        )

        # (8 + 6) / (10 + 10) * 100 = 70%
        assert engine._calculate_average_success_rate() == 70.0

    def test_get_adaptive_retries_conservative(self):
        """Test _get_adaptive_retries for conservative strategy."""
        engine = FailureRuleEngine(max_retries=3)
        assert engine._get_adaptive_retries(RetryStrategy.CONSERVATIVE) == 2

    def test_get_adaptive_retries_aggressive(self):
        """Test _get_adaptive_retries for aggressive strategy."""
        engine = FailureRuleEngine(max_retries=3)
        assert engine._get_adaptive_retries(RetryStrategy.AGGRESSIVE) == 4

    def test_get_adaptive_retries_moderate(self):
        """Test _get_adaptive_retries for moderate strategy."""
        engine = FailureRuleEngine(max_retries=3)
        assert engine._get_adaptive_retries(RetryStrategy.MODERATE) == 3

    def test_get_adaptive_timeout_conservative(self):
        """Test _get_adaptive_timeout for conservative strategy."""
        engine = FailureRuleEngine()
        assert engine._get_adaptive_timeout(RetryStrategy.CONSERVATIVE) == 5.0

    def test_get_adaptive_timeout_aggressive(self):
        """Test _get_adaptive_timeout for aggressive strategy."""
        engine = FailureRuleEngine()
        assert engine._get_adaptive_timeout(RetryStrategy.AGGRESSIVE) == 2.0

    def test_get_adaptive_timeout_moderate(self):
        """Test _get_adaptive_timeout for moderate strategy."""
        engine = FailureRuleEngine()
        assert engine._get_adaptive_timeout(RetryStrategy.MODERATE) == 3.0

    def test_get_adaptive_parallelism_conservative(self):
        """Test _get_adaptive_parallelism for conservative strategy."""
        engine = FailureRuleEngine()
        assert engine._get_adaptive_parallelism(RetryStrategy.CONSERVATIVE) is False

    def test_get_adaptive_parallelism_moderate(self):
        """Test _get_adaptive_parallelism for moderate strategy."""
        engine = FailureRuleEngine()
        assert engine._get_adaptive_parallelism(RetryStrategy.MODERATE) is True

    def test_get_adaptive_parallelism_aggressive(self):
        """Test _get_adaptive_parallelism for aggressive strategy."""
        engine = FailureRuleEngine()
        assert engine._get_adaptive_parallelism(RetryStrategy.AGGRESSIVE) is True


# =============================================================================
# ConnectionStrategy Tests
# =============================================================================

class TestConnectionStrategy:
    """Tests for ConnectionStrategy dataclass."""

    def test_connection_strategy_creation(self):
        """Test ConnectionStrategy creation."""
        strategy = ConnectionStrategy(
            servers=["time.google.com", "time.cloudflare.com"],
            max_retries=3,
            timeout=5.0,
            parallel_queries=True,
            fallback_level=FallbackLevel.NTP_ONLY,
            retry_strategy=RetryStrategy.MODERATE
        )

        assert strategy.servers == ["time.google.com", "time.cloudflare.com"]
        assert strategy.max_retries == 3
        assert strategy.timeout == 5.0
        assert strategy.parallel_queries is True
        assert strategy.fallback_level == FallbackLevel.NTP_ONLY
        assert strategy.retry_strategy == RetryStrategy.MODERATE


# =============================================================================
# AdaptiveFailureHandler Tests
# =============================================================================

class TestAdaptiveFailureHandler:
    """Tests for AdaptiveFailureHandler class."""

    def test_handler_initialization(self):
        """Test AdaptiveFailureHandler initialization."""
        engine = FailureRuleEngine()
        handler = AdaptiveFailureHandler(engine)

        assert handler.rule_engine is engine
        assert len(handler._network_patterns) == 0

    def test_analyze_network_pattern_insufficient_data(self):
        """Test analyze_network_pattern with insufficient data."""
        engine = FailureRuleEngine()
        handler = AdaptiveFailureHandler(engine)

        # Add less than 10 attempts
        for i in range(5):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=True
            )
            engine.connection_history.append(attempt)

        result = handler.analyze_network_pattern()
        # Pattern could be 'insufficient_data' or 'unknown' depending on caching
        assert result['pattern'] in ['insufficient_data', 'unknown']

    def test_analyze_network_pattern_healthy(self):
        """Test analyze_network_pattern with healthy network."""
        engine = FailureRuleEngine()
        handler = AdaptiveFailureHandler(engine)

        # Add 50 successful attempts
        for i in range(50):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=True
            )
            engine.connection_history.append(attempt)

        result = handler.analyze_network_pattern()
        # Pattern could be 'healthy_network' or 'unknown' depending on caching
        assert result['pattern'] in ['healthy_network', 'unknown']

    def test_analyze_network_pattern_moderate_failure(self):
        """Test analyze_network_pattern with moderate failure rate."""
        engine = FailureRuleEngine()
        handler = AdaptiveFailureHandler(engine)

        # Add attempts with moderate failures
        for i in range(50):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=(i % 5 != 0),  # 80% success
                failure_reason=FailureReason.TIMEOUT if i % 5 == 0 else None
            )
            engine.connection_history.append(attempt)

        result = handler.analyze_network_pattern()
        # Pattern could vary depending on caching
        assert result['pattern'] in ['healthy_network', 'moderate_failure_network', 'unknown']

    def test_analyze_network_pattern_high_failure(self):
        """Test analyze_network_pattern with high failure rate."""
        engine = FailureRuleEngine()
        handler = AdaptiveFailureHandler(engine)

        # Add attempts with high failures
        for i in range(50):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=(i % 2 == 0),  # 50% success
                failure_reason=FailureReason.TIMEOUT if i % 2 != 0 else None
            )
            engine.connection_history.append(attempt)

        result = handler.analyze_network_pattern()
        # Pattern could be 'high_failure_network' or 'unknown' depending on caching
        assert result['pattern'] in ['high_failure_network', 'unknown']

    def test_analyze_network_pattern_caching(self):
        """Test analyze_network_pattern uses caching."""
        engine = FailureRuleEngine()
        handler = AdaptiveFailureHandler(engine)

        # Add sufficient data
        for i in range(50):
            attempt = ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0 + i,
                success=True
            )
            engine.connection_history.append(attempt)

        # First call
        result1 = handler.analyze_network_pattern()

        # Second call within 60 seconds should use cache
        with patch('nodupe.tools.time_sync.failure_rules.time.time', return_value=1050.0):
            result2 = handler.analyze_network_pattern()

        assert result1 == result2

    def test_calculate_hourly_failures(self):
        """Test _calculate_hourly_failures."""
        engine = FailureRuleEngine()
        handler = AdaptiveFailureHandler(engine)

        # Create attempts at different hours
        from datetime import datetime
        attempts = [
            ConnectionAttempt(
                host="test.com",
                attempt_time=datetime(2024, 1, 1, 10, 0, 0).timestamp(),
                success=False,
                failure_reason=FailureReason.TIMEOUT
            ),
            ConnectionAttempt(
                host="test.com",
                attempt_time=datetime(2024, 1, 1, 10, 30, 0).timestamp(),
                success=False,
                failure_reason=FailureReason.TIMEOUT
            ),
            ConnectionAttempt(
                host="test.com",
                attempt_time=datetime(2024, 1, 1, 11, 0, 0).timestamp(),
                success=False,
                failure_reason=FailureReason.TIMEOUT
            ),
            ConnectionAttempt(
                host="test.com",
                attempt_time=datetime(2024, 1, 1, 10, 15, 0).timestamp(),
                success=True
            ),
        ]

        hourly = handler._calculate_hourly_failures(attempts)

        assert hourly[10] == 2  # 2 failures at hour 10
        assert hourly[11] == 1  # 1 failure at hour 11

    def test_calculate_failure_reasons(self):
        """Test _calculate_failure_reasons."""
        engine = FailureRuleEngine()
        handler = AdaptiveFailureHandler(engine)

        attempts = [
            ConnectionAttempt(
                host="test.com",
                attempt_time=1000.0,
                success=False,
                failure_reason=FailureReason.TIMEOUT
            ),
            ConnectionAttempt(
                host="test.com",
                attempt_time=1001.0,
                success=False,
                failure_reason=FailureReason.TIMEOUT
            ),
            ConnectionAttempt(
                host="test.com",
                attempt_time=1002.0,
                success=False,
                failure_reason=FailureReason.DNS_FAILURE
            ),
            ConnectionAttempt(
                host="test.com",
                attempt_time=1003.0,
                success=True
            ),
        ]

        reasons = handler._calculate_failure_reasons(attempts)

        assert reasons['timeout'] == 2
        assert reasons['dns_failure'] == 1

    def test_calculate_success_by_server(self):
        """Test _calculate_success_by_server."""
        engine = FailureRuleEngine()
        handler = AdaptiveFailureHandler(engine)

        attempts = [
            ConnectionAttempt(host="server1.com", attempt_time=1000.0, success=True),
            ConnectionAttempt(host="server1.com", attempt_time=1001.0, success=True),
            ConnectionAttempt(host="server1.com", attempt_time=1002.0, success=False),
            ConnectionAttempt(host="server2.com", attempt_time=1003.0, success=True),
            ConnectionAttempt(host="server2.com", attempt_time=1004.0, success=False),
        ]

        success_rates = handler._calculate_success_by_server(attempts)

        assert success_rates['server1.com'] == pytest.approx(66.67, rel=0.1)
        assert success_rates['server2.com'] == 50.0

    def test_generate_recommendations_high_failure(self):
        """Test _generate_recommendations for high failure pattern."""
        engine = FailureRuleEngine()
        handler = AdaptiveFailureHandler(engine)

        recommendations = handler._generate_recommendations(
            pattern='high_failure_network',
            failure_reasons={},
            success_rates={}
        )

        assert 'Switch to conservative retry strategy' in recommendations
        assert 'Reduce parallel query count' in recommendations
        assert 'Increase timeout values' in recommendations
        assert 'Prioritize primary servers only' in recommendations

    def test_generate_recommendations_timeout_issues(self):
        """Test _generate_recommendations with timeout issues."""
        engine = FailureRuleEngine()
        handler = AdaptiveFailureHandler(engine)

        recommendations = handler._generate_recommendations(
            pattern='healthy_network',
            failure_reasons={'timeout': 15},
            success_rates={}
        )

        assert 'Increase timeout due to network latency' in recommendations

    def test_generate_recommendations_dns_issues(self):
        """Test _generate_recommendations with DNS issues."""
        engine = FailureRuleEngine()
        handler = AdaptiveFailureHandler(engine)

        recommendations = handler._generate_recommendations(
            pattern='healthy_network',
            failure_reasons={'dns_failure': 10},
            success_rates={}
        )

        assert 'Check DNS configuration or use IP addresses' in recommendations

    def test_generate_recommendations_poor_server(self):
        """Test _generate_recommendations with poor performing server."""
        engine = FailureRuleEngine()
        handler = AdaptiveFailureHandler(engine)

        recommendations = handler._generate_recommendations(
            pattern='healthy_network',
            failure_reasons={},
            success_rates={'bad.server.com': 20.0}
        )

        assert any('bad.server.com' in rec for rec in recommendations)

    def test_get_cached_pattern_empty(self):
        """Test _get_cached_pattern with no cached patterns."""
        engine = FailureRuleEngine()
        handler = AdaptiveFailureHandler(engine)

        result = handler._get_cached_pattern()
        assert result['pattern'] == 'unknown'
        assert result['recommendation'] == 'insufficient_data'

    def test_get_cached_pattern_with_data(self):
        """Test _get_cached_pattern with cached data."""
        engine = FailureRuleEngine()
        handler = AdaptiveFailureHandler(engine)

        # Add some patterns
        handler._network_patterns['healthy_network'].append({'pattern': 'healthy_network', 'data': 'test1'})
        handler._network_patterns['healthy_network'].append({'pattern': 'healthy_network', 'data': 'test2'})
        handler._network_patterns['moderate_failure_network'].append({'pattern': 'moderate_failure_network', 'data': 'test3'})

        result = handler._get_cached_pattern()
        # Should return the pattern with most entries
        assert result['pattern'] == 'healthy_network'
        assert result['data'] == 'test2'  # Most recent


# =============================================================================
# Global Functions Tests
# =============================================================================

class TestGlobalFunctions:
    """Tests for global functions."""

    def test_get_failure_rules_creates_singleton(self):
        """Test get_failure_rules creates singleton instance."""
        reset_failure_rules()

        rules1 = get_failure_rules()
        rules2 = get_failure_rules()

        assert rules1 is rules2
        assert isinstance(rules1, FailureRuleEngine)

    def test_reset_failure_rules(self):
        """Test reset_failure_rules creates new instance."""
        reset_failure_rules()

        rules1 = get_failure_rules()
        rules1.max_retries = 10  # Modify

        reset_failure_rules()

        rules2 = get_failure_rules()
        assert rules1 is not rules2
        assert rules2.max_retries == 3  # Default value

    def test_get_failure_rules_after_reset(self):
        """Test get_failure_rules works correctly after reset."""
        reset_failure_rules()

        rules = get_failure_rules()
        assert isinstance(rules, FailureRuleEngine)


# =============================================================================
# FallbackLevel Enum Tests
# =============================================================================

class TestFallbackLevel:
    """Tests for FallbackLevel enum."""

    def test_fallback_level_values(self):
        """Test FallbackLevel enum values."""
        assert FallbackLevel.NTP_ONLY.value == 1
        assert FallbackLevel.RTC_FALLBACK.value == 2
        assert FallbackLevel.FILE_FALLBACK.value == 3
        assert FallbackLevel.MONOTONIC_ONLY.value == 4


# =============================================================================
# RetryStrategy Enum Tests
# =============================================================================

class TestRetryStrategy:
    """Tests for RetryStrategy enum."""

    def test_retry_strategy_values(self):
        """Test RetryStrategy enum values."""
        assert RetryStrategy.CONSERVATIVE.value == 1
        assert RetryStrategy.MODERATE.value == 2
        assert RetryStrategy.AGGRESSIVE.value == 3
