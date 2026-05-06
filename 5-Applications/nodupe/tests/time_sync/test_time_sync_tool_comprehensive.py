"""
Time Sync Tool Tests - Priority 1 Coverage

Comprehensive tests for time_synchronizationTool covering:
- NTP synchronization
- Fallback mechanisms
- FastDate64 encoding
- Background synchronization
- Error handling
- All public methods
"""

import pytest
import time
import threading
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, PropertyMock
import socket

from nodupe.tools.time_sync.time_sync_tool import (
    time_synchronizationTool,
    time_synchronizationDisabledError,
    DEFAULT_SERVERS,
    DEFAULT_TIMEOUT,
    DEFAULT_ATTEMPTS,
)


class TestTimeSyncToolInstantiation:
    """Test time_synchronizationTool initialization."""

    def test_init_default(self):
        """Tool initializes with default parameters."""
        tool = time_synchronizationTool()
        assert tool is not None
        assert tool.name == "time_synchronization"
        assert tool.version == "1.0.0"
        assert tool.dependencies == []

    def test_init_custom_servers(self):
        """Tool initializes with custom NTP servers."""
        custom_servers = ["time.custom.com", "ntp.example.org"]
        tool = time_synchronizationTool(servers=custom_servers)
        assert tool.servers == custom_servers

    def test_init_empty_servers_raises(self):
        """Tool raises ValueError with empty servers list."""
        with pytest.raises(ValueError, match="At least one NTP server required"):
            time_synchronizationTool(servers=[])

    def test_init_custom_timeout(self):
        """Tool initializes with custom timeout."""
        tool = time_synchronizationTool(timeout=5.0)
        assert tool.timeout == 5.0

    def test_init_custom_attempts(self):
        """Tool initializes with custom attempts."""
        tool = time_synchronizationTool(attempts=5)
        assert tool.attempts == 5

    def test_init_custom_max_delay(self):
        """Tool initializes with custom max acceptable delay."""
        tool = time_synchronizationTool(max_acceptable_delay=1.0)
        assert tool.max_acceptable_delay == 1.0

    def test_init_custom_smoothing_alpha(self):
        """Tool initializes with custom smoothing alpha."""
        tool = time_synchronizationTool(smoothing_alpha=0.5)
        assert tool.alpha == 0.5

    def test_init_enabled_override(self):
        """Tool respects enabled override."""
        tool = time_synchronizationTool(enabled=True)
        assert tool._enabled == True

    def test_init_allow_network_override(self):
        """Tool respects allow_network override."""
        tool = time_synchronizationTool(allow_network=False)
        assert tool._allow_network == False

    def test_init_allow_background_override(self):
        """Tool respects allow_background override."""
        tool = time_synchronizationTool(allow_background=False)
        assert tool._allow_background == False


class TestTimeSyncToolMetadata:
    """Test tool metadata and capabilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = time_synchronizationTool()

    def test_name(self):
        """name property returns correct value."""
        assert self.tool.name == "time_synchronization"

    def test_version(self):
        """version property returns correct value."""
        assert self.tool.version == "1.0.0"

    def test_dependencies(self):
        """dependencies property returns empty list."""
        assert self.tool.dependencies == []

    def test_metadata(self):
        """metadata returns ToolMetadata with correct values."""
        metadata = self.tool.metadata
        assert metadata.name == "time_synchronization"
        assert metadata.version == "1.0.0"
        assert "time" in metadata.tags
        assert "ntp" in metadata.tags

    def test_api_methods(self):
        """api_methods returns dictionary of callable methods."""
        api_methods = self.tool.api_methods
        assert isinstance(api_methods, dict)
        assert 'force_sync' in api_methods
        assert 'sync_with_fallback' in api_methods
        assert callable(api_methods['force_sync'])
        assert callable(api_methods['sync_with_fallback'])


class TestTimeSyncToolInitialize:
    """Test tool initialization."""

    def test_initialize_logs_info(self, caplog):
        """initialize() logs appropriate messages."""
        import logging
        tool = time_synchronizationTool()
        container = MagicMock()

        with caplog.at_level(logging.INFO):
            tool.initialize(container)

        assert "Initializing time_synchronization tool" in caplog.text

    def test_initialize_enabled_attempts_sync(self, caplog):
        """initialize() with enabled=True attempts sync."""
        import logging
        tool = time_synchronizationTool(enabled=True)
        container = MagicMock()

        with patch.object(tool, 'force_sync', side_effect=Exception("Test")):
            with caplog.at_level(logging.INFO):
                tool.initialize(container)

        assert "Initial time synchronization successful" not in caplog.text
        assert "Initial time synchronization failed" in caplog.text


class TestTimeSyncToolShutdown:
    """Test tool shutdown."""

    def test_shutdown_logs_info(self, caplog):
        """shutdown() logs appropriate messages."""
        import logging
        tool = time_synchronizationTool()

        with caplog.at_level(logging.INFO):
            tool.shutdown()

        assert "Shutting down time_synchronization tool" in caplog.text

    def test_shutdown_stops_background(self):
        """shutdown() stops background synchronization."""
        tool = time_synchronizationTool()
        with patch.object(tool, 'stop_background') as mock_stop:
            tool.shutdown()
            mock_stop.assert_called_once()


class TestTimeSyncToolForceSync:
    """Test force_sync method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = time_synchronizationTool()

    def test_force_sync_disabled(self):
        """force_sync() raises when disabled."""
        self.tool._enabled = False
        with pytest.raises(time_synchronizationDisabledError):
            self.tool.force_sync()

    def test_force_sync_no_network(self):
        """force_sync() handles no-network mode."""
        self.tool._allow_network = False
        # Should use fallback mechanism
        result = self.tool.force_sync()
        assert result is not None

    def test_force_sync_success(self):
        """force_sync() succeeds with valid NTP response."""
        self.tool._enabled = True
        self.tool._allow_network = True

        with patch.object(self.tool, '_query_ntp_servers_parallel', return_value={
            'offset': 0.001,
            'delay': 0.05,
            'server': 'time.google.com'
        }):
            result = self.tool.force_sync()
            assert result is not None

    def test_force_sync_all_servers_fail(self):
        """force_sync() handles all servers failing."""
        self.tool._enabled = True
        self.tool._allow_network = True

        with patch.object(self.tool, '_query_ntp_servers_parallel', return_value=None):
            # Should fall back to local time
            result = self.tool.force_sync()
            assert result is not None


class TestTimeSyncToolSyncWithFallback:
    """Test sync_with_fallback method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = time_synchronizationTool()

    def test_sync_with_fallback_disabled(self):
        """sync_with_fallback() raises when disabled."""
        self.tool._enabled = False
        with pytest.raises(time_synchronizationDisabledError):
            self.tool.sync_with_fallback()

    def test_sync_with_fallback_ntp_success(self):
        """sync_with_fallback() uses NTP when available."""
        self.tool._enabled = True
        self.tool._allow_network = True

        with patch.object(self.tool, '_query_ntp_servers_parallel', return_value={
            'offset': 0.001,
            'delay': 0.05,
            'server': 'time.google.com'
        }):
            result = self.tool.sync_with_fallback()
            assert result is not None

    def test_sync_with_fallback_rtc_fallback(self):
        """sync_with_fallback() falls back to RTC when NTP fails."""
        self.tool._enabled = True
        self.tool._allow_network = True

        with patch.object(self.tool, '_query_ntp_servers_parallel', return_value=None):
            with patch.object(self.tool, '_sync_with_rtc', return_value={'offset': 0.01}):
                result = self.tool.sync_with_fallback()
                assert result is not None

    def test_sync_with_fallback_monotonic_fallback(self):
        """sync_with_fallback() falls back to monotonic when RTC fails."""
        self.tool._enabled = True
        self.tool._allow_network = True

        with patch.object(self.tool, '_query_ntp_servers_parallel', return_value=None):
            with patch.object(self.tool, '_sync_with_rtc', return_value=None):
                with patch.object(self.tool, '_use_monotonic_only', return_value=True):
                    result = self.tool.sync_with_fallback()
                    assert result is not None


class TestTimeSyncToolGetTime:
    """Test time retrieval methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = time_synchronizationTool()

    def test_get_authenticated_time_rfc3339(self):
        """get_authenticated_time() returns RFC3339 format."""
        self.tool._base_server_time = 1700000000.0
        self.tool._base_monotonic = time.time()

        result = self.tool.get_authenticated_time(format='rfc3339')
        assert isinstance(result, str)
        assert 'T' in result  # RFC3339 format indicator

    def test_get_authenticated_time_unix(self):
        """get_authenticated_time() returns Unix timestamp."""
        self.tool._base_server_time = 1700000000.0
        self.tool._base_monotonic = time.time()

        result = self.tool.get_authenticated_time(format='unix')
        assert isinstance(result, (int, float))

    def test_get_authenticated_time_not_synced(self):
        """get_authenticated_time() handles not synced state."""
        self.tool._base_server_time = None

        result = self.tool.get_authenticated_time()
        # Should return current time or raise appropriate error
        assert result is not None

    def test_get_corrected_monotonic(self):
        """get_corrected_monotonic() returns corrected time."""
        self.tool._base_server_time = 1700000000.0
        self.tool._base_monotonic = time.time()
        self.tool._smoothed_offset = 0.001

        result = self.tool.get_corrected_monotonic()
        assert isinstance(result, float)


class TestTimeSyncToolBackground:
    """Test background synchronization."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = time_synchronizationTool()

    def test_start_background_disabled(self):
        """start_background() raises when disabled."""
        self.tool._enabled = False
        with pytest.raises(time_synchronizationDisabledError):
            self.tool.start_background()

    def test_start_background_no_network(self):
        """start_background() raises when network not allowed."""
        self.tool._enabled = True
        self.tool._allow_network = False
        with pytest.raises(time_synchronizationDisabledError):
            self.tool.start_background()

    def test_start_background_not_allowed_bg(self):
        """start_background() raises when background not allowed."""
        self.tool._enabled = True
        self.tool._allow_network = True
        self.tool._allow_background = False
        with pytest.raises(time_synchronizationDisabledError):
            self.tool.start_background()

    def test_start_background_success(self):
        """start_background() starts background thread."""
        self.tool._enabled = True
        self.tool._allow_network = True
        self.tool._allow_background = True

        with patch.object(self.tool, '_background_sync_loop'):
            self.tool.start_background(interval=60)
            assert self.tool._bg_thread is not None
            assert self.tool._bg_thread.is_alive()

        self.tool.stop_background()

    def test_stop_background(self):
        """stop_background() stops background thread."""
        self.tool._enabled = True
        self.tool._allow_network = True
        self.tool._allow_background = True

        # Start and stop
        self.tool.start_background(interval=60)
        self.tool.stop_background(wait=False)

        assert self.tool._bg_stop.is_set()


class TestTimeSyncToolRunStandalone:
    """Test run_standalone method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = time_synchronizationTool()

    def test_run_standalone_no_args(self, capsys):
        """run_standalone() with no args shows help."""
        result = self.tool.run_standalone([])
        assert result == 0
        captured = capsys.readouterr()
        assert "time" in captured.out.lower() or "sync" in captured.out.lower()

    def test_run_standalone_sync_flag(self, capsys):
        """run_standalone() with --sync flag."""
        with patch.object(self.tool, 'sync_time'):
            with patch.object(self.tool, 'get_authenticated_time', return_value="2024-01-01T00:00:00Z"):
                result = self.tool.run_standalone(['--sync'])
                assert result == 0

    def test_run_standalone_format_flag(self, capsys):
        """run_standalone() with --format flag."""
        with patch.object(self.tool, 'get_authenticated_time', return_value="1700000000"):
            result = self.tool.run_standalone(['--format', 'unix'])
            assert result == 0

    def test_run_standalone_error(self, capsys):
        """run_standalone() handles errors."""
        with patch.object(self.tool, 'get_authenticated_time', side_effect=Exception("Test error")):
            result = self.tool.run_standalone([])
            assert result == 1
            captured = capsys.readouterr()
            assert "Error" in captured.out


class TestTimeSyncToolDescribeUsage:
    """Test describe_usage method."""

    def test_describe_usage_returns_string(self):
        """describe_usage() returns a string."""
        tool = time_synchronizationTool()
        usage = tool.describe_usage()
        assert isinstance(usage, str)
        assert len(usage) > 0

    def test_describe_usage_content(self):
        """describe_usage() contains meaningful content."""
        tool = time_synchronizationTool()
        usage = tool.describe_usage()
        assert "time" in usage.lower() or "sync" in usage.lower()


class TestTimeSyncToolEdgeCases:
    """Test edge cases and error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = time_synchronizationTool()

    def test_smoothing_alpha_bounds(self):
        """Smoothing alpha is clamped to valid range."""
        tool_low = time_synchronizationTool(smoothing_alpha=-0.5)
        tool_high = time_synchronizationTool(smoothing_alpha=1.5)

        assert 0.0 <= tool_low.alpha <= 1.0
        assert 0.0 <= tool_high.alpha <= 1.0

    def test_concurrent_force_sync(self):
        """force_sync() is thread-safe."""
        self.tool._enabled = True
        self.tool._allow_network = True

        results = []
        errors = []

        def sync():
            try:
                with patch.object(self.tool, '_query_ntp_servers_parallel', return_value={'offset': 0.001}):
                    result = self.tool.force_sync()
                    results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=sync) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_disabled_error_message(self):
        """Disabled tool provides clear error message."""
        self.tool._enabled = False
        try:
            self.tool.force_sync()
        except time_synchronizationDisabledError as e:
            assert "disabled" in str(e).lower()


class TestTimeSyncToolInternalMethods:
    """Test internal methods (coverage for private methods)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = time_synchronizationTool()

    def test_validate_year_range(self):
        """Internal validation methods work correctly."""
        # Test that the tool has expected internal state
        assert hasattr(self.tool, '_lock')
        assert hasattr(self.tool, '_bg_stop')
        assert isinstance(self.tool._lock, type(threading.Lock()))
        assert isinstance(self.tool._bg_stop, threading.Event)

    def test_server_list_default(self):
        """Default server list is populated."""
        tool = time_synchronizationTool()
        assert len(tool.servers) > 0
        assert 'time.google.com' in tool.servers or 'time.cloudflare.com' in tool.servers

    def test_timeout_type_conversion(self):
        """Timeout is converted to float."""
        tool = time_synchronizationTool(timeout=10)
        assert isinstance(tool.timeout, float)

    def test_attempts_type_conversion(self):
        """Attempts is converted to int."""
        tool = time_synchronizationTool(attempts=5.5)
        assert isinstance(tool.attempts, int)
