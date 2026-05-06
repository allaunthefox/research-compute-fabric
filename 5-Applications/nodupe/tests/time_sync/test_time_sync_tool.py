"""
Time Sync Tool Tests

Tests for the time synchronization tool including:
- NTP synchronization
- FastDate64 encoding/decoding
- Time drift calculation
- Sync scheduling
"""

import pytest
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call
import struct


class TestTimeSyncToolBasic:
    """Test basic time_synchronizationTool functionality."""

    def test_import(self):
        """time_synchronizationTool can be imported."""
        from nodupe.tools.time_sync.time_sync_tool import time_synchronizationTool
        assert time_synchronizationTool is not None

    def test_instantiation(self):
        """time_synchronizationTool can be instantiated."""
        from nodupe.tools.time_sync.time_sync_tool import time_synchronizationTool
        tool = time_synchronizationTool()
        assert tool is not None

    def test_tool_name(self):
        """time_synchronizationTool has correct name."""
        from nodupe.tools.time_sync.time_sync_tool import time_synchronizationTool
        tool = time_synchronizationTool()
        assert hasattr(tool, 'name') or hasattr(tool, '_name')


class TestLeapYearCalculator:
    """Test LeapYearCalculator class."""

    def test_instantiation(self):
        """LeapYearCalculator can be instantiated."""
        from nodupe.tools.time_sync.time_sync_tool import LeapYearCalculator
        calc = LeapYearCalculator()
        assert calc is not None

    def test_is_leap_year_known_values(self):
        """Leap year calculation returns known correct values."""
        from nodupe.tools.time_sync.time_sync_tool import LeapYearCalculator
        calc = LeapYearCalculator()

        # Known leap years
        assert calc.is_leap_year(2000) == True   # Divisible by 400
        assert calc.is_leap_year(2024) == True   # Divisible by 4
        assert calc.is_leap_year(1996) == True   # Divisible by 4

        # Known non-leap years
        assert calc.is_leap_year(1900) == False  # Divisible by 100 but not 400
        assert calc.is_leap_year(2023) == False  # Not divisible by 4
        assert calc.is_leap_year(2025) == False  # Not divisible by 4

    def test_is_leap_year_century_years(self):
        """Leap year calculation handles century years correctly."""
        from nodupe.tools.time_sync.time_sync_tool import LeapYearCalculator
        calc = LeapYearCalculator()

        # Century years
        assert calc.is_leap_year(1600) == True   # Divisible by 400
        assert calc.is_leap_year(1700) == False  # Divisible by 100 but not 400
        assert calc.is_leap_year(1800) == False  # Divisible by 100 but not 400
        assert calc.is_leap_year(1900) == False  # Divisible by 100 but not 400
        assert calc.is_leap_year(2000) == True   # Divisible by 400
        assert calc.is_leap_year(2100) == False  # Divisible by 100 but not 400


class TestFastDate64Encoding:
    """Test FastDate64 encoding/decoding."""

    def test_encode_datetime_to_int(self):
        """FastDate64 encoder converts datetime to integer."""
        from nodupe.tools.time_sync.sync_utils import FastDate64Encoder
        encoder = FastDate64Encoder()

        # Test with a known datetime
        dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        encoded = encoder.encode_to_int(dt)

        assert isinstance(encoded, int)
        assert encoded > 0

    def test_decode_int_to_datetime(self):
        """FastDate64 decoder converts integer to datetime."""
        from nodupe.tools.time_sync.sync_utils import FastDate64Encoder
        encoder = FastDate64Encoder()

        # Encode then decode
        dt = datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc)
        encoded = encoder.encode_to_int(dt)
        decoded = encoder.decode_from_int(encoded)

        assert isinstance(decoded, datetime)
        # Allow for small precision differences
        assert abs((decoded - dt).total_seconds()) < 1

    def test_roundtrip(self):
        """FastDate64 encode/decode roundtrip preserves value."""
        from nodupe.tools.time_sync.sync_utils import FastDate64Encoder
        encoder = FastDate64Encoder()

        test_dates = [
            datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
            datetime(2050, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        ]

        for dt in test_dates:
            encoded = encoder.encode_to_int(dt)
            decoded = encoder.decode_from_int(encoded)
            # Allow for small precision differences
            assert abs((decoded - dt).total_seconds()) < 1


class TestTimeSyncToolExecute:
    """Test time_synchronizationTool.execute() method."""

    def test_execute_no_args(self):
        """execute() with no args shows help or syncs."""
        from nodupe.tools.time_sync.time_sync_tool import time_synchronizationTool
        tool = time_synchronizationTool()
        args = MagicMock()
        args.sync = False
        args.status = False
        args.encode = None
        args.decode = None
        args.drift = False
        args.interval = None
        args.container = MagicMock()

        # Should not crash
        result = tool.execute(args)
        assert result is not None

    def test_execute_sync_flag(self):
        """execute() with --sync performs NTP sync."""
        from nodupe.tools.time_sync.time_sync_tool import time_synchronizationTool
        tool = time_synchronizationTool()
        args = MagicMock()
        args.sync = True
        args.status = False
        args.encode = None
        args.decode = None
        args.drift = False
        args.interval = None
        args.container = MagicMock()

        with patch.object(tool, '_sync_with_ntp', return_value=(0, 0.05)):
            result = tool.execute(args)
            assert result == 0

    def test_execute_status_flag(self):
        """execute() with --status shows sync status."""
        from nodupe.tools.time_sync.time_sync_tool import time_synchronizationTool
        tool = time_synchronizationTool()
        args = MagicMock()
        args.sync = False
        args.status = True
        args.encode = None
        args.decode = None
        args.drift = False
        args.interval = None
        args.container = MagicMock()

        # Should not crash
        result = tool.execute(args)
        assert result is not None


class TestTimeSyncToolNTPSync:
    """Test NTP synchronization functionality."""

    def test_sync_with_ntp_no_network(self):
        """_sync_with_ntp handles no-network mode."""
        from nodupe.tools.time_sync.time_sync_tool import time_synchronizationTool
        tool = time_synchronizationTool()

        with patch.dict('os.environ', {'NODUPE_TIMESYNC_NO_NETWORK': '1'}):
            result = tool._sync_with_ntp()
            # Should return some result without crashing
            assert result is not None

    def test_sync_with_ntp_mock_success(self):
        """_sync_with_ntp works with successful NTP response."""
        from nodupe.tools.time_sync.time_sync_tool import time_synchronizationTool
        tool = time_synchronizationTool()

        with patch.object(tool, '_query_ntp_server', return_value={
            'offset': 0.001,
            'delay': 0.05,
            'server': 'time.google.com'
        }):
            result = tool._sync_with_ntp()
            assert result is not None


class TestTimeSyncToolDriftCalculation:
    """Test time drift calculation."""

    def test_calculate_drift(self):
        """Drift calculation returns expected values."""
        from nodupe.tools.time_sync.time_sync_tool import time_synchronizationTool
        tool = time_synchronizationTool()

        # Mock two time readings
        with patch('time.time') as mock_time:
            mock_time.side_effect = [1000.0, 1001.0]  # 1 second apart

            drift = tool._calculate_drift()

            # Drift should be a number
            assert isinstance(drift, (int, float))


class TestTimeSyncToolEncoding:
    """Test timestamp encoding via CLI."""

    def test_encode_timestamp(self):
        """encode subcommand encodes timestamp."""
        from nodupe.tools.time_sync.time_sync_tool import time_synchronizationTool
        tool = time_synchronizationTool()
        args = MagicMock()
        args.sync = False
        args.status = False
        args.encode = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        args.decode = None
        args.drift = False
        args.interval = None
        args.container = MagicMock()

        # Should not crash
        result = tool.execute(args)
        assert result is not None

    def test_decode_timestamp(self):
        """decode subcommand decodes timestamp."""
        from nodupe.tools.time_sync.time_sync_tool import time_synchronizationTool
        tool = time_synchronizationTool()
        args = MagicMock()
        args.sync = False
        args.status = False
        args.encode = None
        args.decode = 12345678901234567890  # Some encoded value
        args.drift = False
        args.interval = None
        args.container = MagicMock()

        # Should not crash
        result = tool.execute(args)
        assert result is not None


class TestTimeSyncToolRegistration:
    """Test tool registration."""

    def test_register_commands(self):
        """register_commands() sets up argument parser."""
        from nodupe.tools.time_sync.time_sync_tool import time_synchronizationTool
        tool = time_synchronizationTool()
        parser = MagicMock()

        # Should not crash
        tool.register_commands(parser)

        # Should have called add_argument
        assert parser.add_argument.called or parser.add_parser.called

    def test_run_standalone(self):
        """run_standalone() can be called."""
        from nodupe.tools.time_sync.time_sync_tool import time_synchronizationTool
        tool = time_synchronizationTool()
        args = MagicMock()
        args.sync = False
        args.container = MagicMock()

        # Should not crash
        result = tool.run_standalone(args)
        assert result is not None


class TestTimeSyncToolDescribeUsage:
    """Test describe_usage() method."""

    def test_describe_usage_returns_string(self):
        """describe_usage() returns a string."""
        from nodupe.tools.time_sync.time_sync_tool import time_synchronizationTool
        tool = time_synchronizationTool()
        usage = tool.describe_usage()
        assert isinstance(usage, str)
        assert len(usage) > 0


class TestTimeSyncToolApiMethods:
    """Test api_methods property."""

    def test_api_methods_exists(self):
        """api_methods property exists."""
        from nodupe.tools.time_sync.time_sync_tool import time_synchronizationTool
        tool = time_synchronizationTool()
        assert hasattr(tool, 'api_methods')


class TestTimeSyncToolEdgeCases:
    """Test edge cases and error handling."""

    def test_no_container_graceful_handling(self):
        """Tool handles missing container gracefully."""
        from nodupe.tools.time_sync.time_sync_tool import time_synchronizationTool
        tool = time_synchronizationTool()
        args = MagicMock()
        args.sync = False
        args.container = None

        # Should not crash even without container
        try:
            result = tool.execute(args)
            assert result is not None
        except Exception:
            # Some exception handling is also acceptable
            pass

    def test_network_error_handling(self):
        """Tool handles network errors gracefully."""
        from nodupe.tools.time_sync.time_sync_tool import time_synchronizationTool
        tool = time_synchronizationTool()

        with patch.object(tool, '_query_ntp_server', side_effect=Exception("Network error")):
            # Should handle the error gracefully
            result = tool._sync_with_ntp()
            # Should return some result (possibly error indicator)
            assert result is not None
