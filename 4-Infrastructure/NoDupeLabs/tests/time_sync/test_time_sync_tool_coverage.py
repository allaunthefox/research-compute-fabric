# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 NoDupeLabs

"""Tests to achieve 100% coverage on time_sync_tool.py module.

This test file targets the missing coverage in:
- time_sync_tool.py: Fallback logic, RTC access, background sync errors
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.time_sync.time_sync_tool import (
    LeapYearCalculator,
    register_tool,
    time_synchronizationDisabledError,
    time_synchronizationTool,
)


class TestTimeSyncToolFallbackCoverage:
    """Tests for time_synchronizationTool fallback logic."""

    def test_sync_with_fallback_disabled_instance(self):
        """Test sync_with_fallback raises when instance disabled."""
        tool = time_synchronizationTool(enabled=False)

        with pytest.raises(time_synchronizationDisabledError, match="instance is disabled"):
            tool.sync_with_fallback()

    def test_sync_with_fallback_network_disabled_falls_back(self):
        """Test sync_with_fallback falls back when network disabled."""
        tool = time_synchronizationTool()
        tool.disable_network()

        # Should fall back to RTC
        with patch.object(tool, '_get_rtc_time', return_value=time.time()):
            with patch('nodupe.tools.time_sync.time_sync_tool.time.monotonic', return_value=100.0):
                result = tool.sync_with_fallback()

        assert result[0] == "rtc"

    def test_sync_with_fallback_ntp_success(self):
        """Test sync_with_fallback when NTP succeeds."""
        tool = time_synchronizationTool()

        with patch.object(tool, 'force_sync', return_value=("time.google.com", time.time(), 0.05, 0.03)):
            result = tool.sync_with_fallback()

        assert result[0] == "ntp"

    def test_sync_with_fallback_rtc_success(self):
        """Test sync_with_fallback falls back to RTC successfully."""
        tool = time_synchronizationTool()
        tool.disable_network()

        with patch.object(tool, '_get_rtc_time', return_value=time.time()):
            with patch('nodupe.tools.time_sync.time_sync_tool.time.monotonic', return_value=100.0):
                result = tool.sync_with_fallback()

        assert result[0] == "rtc"

    def test_sync_with_fallback_rtc_fails_falls_to_system(self):
        """Test sync_with_fallback falls back to system time when RTC fails."""
        tool = time_synchronizationTool()
        tool.disable_network()

        with patch.object(tool, '_get_rtc_time', side_effect=Exception("RTC failed")):
            with patch('nodupe.tools.time_sync.time_sync_tool.time.time', return_value=1700000000.0):
                with patch('nodupe.tools.time_sync.time_sync_tool.time.monotonic', side_effect=[100.0, 100.1, 100.05]):
                    result = tool.sync_with_fallback()

        assert result[0] == "system"

    def test_sync_with_fallback_system_invalid_time_past(self):
        """Test sync_with_fallback rejects system time too far in past."""
        tool = time_synchronizationTool()
        tool.disable_network()

        with patch.object(tool, '_get_rtc_time', side_effect=Exception("RTC failed")):
            with patch.object(tool, '_get_file_timestamp', return_value=1700000000.0):
                # System time before 2010
                with patch('nodupe.tools.time_sync.time_sync_tool.time.time', return_value=1262303999):
                    with patch('nodupe.tools.time_sync.time_sync_tool.time.monotonic', side_effect=lambda: 100.0):
                        result = tool.sync_with_fallback()

        # Should fall through to file fallback
        assert result[0] in ["file", "monotonic_estimated", "monotonic"]

    def test_sync_with_fallback_system_drift_detected(self):
        """Test sync_with_fallback rejects system time with large drift."""
        tool = time_synchronizationTool()
        tool.disable_network()

        call_count = [0]
        def mock_time():
            """Mock time function that returns different values on successive calls."""
            call_count[0] += 1
            if call_count[0] == 1:
                return 1700000000.0  # First call
            return 1700000600.0  # Second call - 10 minutes difference

        with patch.object(tool, '_get_rtc_time', side_effect=Exception("RTC failed")):
            with patch.object(tool, '_get_file_timestamp', return_value=1700000000.0):
                with patch('nodupe.tools.time_sync.time_sync_tool.time.time', side_effect=mock_time):
                    with patch('nodupe.tools.time_sync.time_sync_tool.time.monotonic', side_effect=lambda: 100.0):
                        result = tool.sync_with_fallback()

        # Should fall through to file fallback
        assert result[0] in ["file", "monotonic_estimated", "monotonic"]

    def test_sync_with_fallback_file_success(self):
        """Test sync_with_fallback falls back to file timestamp successfully."""
        tool = time_synchronizationTool()
        tool.disable_network()

        with patch.object(tool, '_get_rtc_time', side_effect=Exception("RTC failed")):
            # Force system time fallback to fail by returning 0 (before 2010)
            with patch('nodupe.tools.time_sync.time_sync_tool.time.time', return_value=0):
                with patch.object(tool, '_get_file_timestamp', return_value=time.time()):
                    with patch('nodupe.tools.time_sync.time_sync_tool.time.monotonic', side_effect=range(100, 200)):
                        result = tool.sync_with_fallback()

        assert result[0] == "file"

    def test_sync_with_fallback_file_stale_falls_to_monotonic_estimated(self):
        """Test sync_with_fallback falls to monotonic_estimated when file is stale."""
        tool = time_synchronizationTool()
        tool.disable_network()

        with patch.object(tool, '_get_rtc_time', side_effect=Exception("RTC failed")):
            # Force system time fallback to fail
            with patch('nodupe.tools.time_sync.time_sync_tool.time.time', return_value=0):
                # File timestamp is 2 days old
                with patch.object(tool, '_get_file_timestamp', return_value=time.time() - 172800):
                    with patch('nodupe.tools.time_sync.time_sync_tool.time.monotonic', side_effect=range(100, 200)):
                        result = tool.sync_with_fallback()

        # Should fall through to monotonic_estimated or monotonic
        assert result[0] in ["monotonic_estimated", "monotonic"]

    def test_sync_with_fallback_monotonic_estimated_success(self):
        """Test sync_with_fallback uses monotonic_estimated successfully."""
        tool = time_synchronizationTool()
        tool.disable_network()

        with patch.object(tool, '_get_rtc_time', side_effect=Exception("RTC failed")):
            # Force system time fallback to fail (first call < 2010), then allow estimation validation
            with patch('nodupe.tools.time_sync.time_sync_tool.time.time', side_effect=[0, 1700000000.0, 1700000000.0, 1700000000.0]):
                # Fallback 3 fails (Exception), Fallback 4 succeeds (Returns value)
                with patch.object(tool, '_get_file_timestamp', side_effect=[Exception("Fallback 3 fail"), 1700000000.0]):
                    with patch('nodupe.tools.time_sync.time_sync_tool.time.monotonic', side_effect=lambda: 100.0):
                        result = tool.sync_with_fallback()

        # Should use monotonic_estimated
        assert result[0] == "monotonic_estimated"

    def test_sync_with_fallback_pure_monotonic(self):
        """Test sync_with_fallback falls back to pure monotonic."""
        tool = time_synchronizationTool()
        tool.disable_network()

        with patch.object(tool, '_get_rtc_time', side_effect=Exception("RTC failed")):
            # Force system time fallback to fail
            with patch('nodupe.tools.time_sync.time_sync_tool.time.time', return_value=0):
                with patch.object(tool, '_get_file_timestamp', side_effect=Exception("File failed")):
                    with patch('nodupe.tools.time_sync.time_sync_tool.time.monotonic', side_effect=range(100, 200)):
                        result = tool.sync_with_fallback()

        assert result[0] == "monotonic"


class TestTimeSyncToolGetAuthenticatedTimeCoverage:
    """Tests for get_authenticated_time method."""

    def test_get_authenticated_time_disabled(self):
        """Test get_authenticated_time raises when disabled."""
        tool = time_synchronizationTool(enabled=False)

        with pytest.raises(time_synchronizationDisabledError):
            tool.get_authenticated_time()

    def test_get_authenticated_time_iso8601(self):
        """Test get_authenticated_time with iso8601 format."""
        tool = time_synchronizationTool()

        with patch.object(tool, 'sync_with_fallback', return_value=("ntp", time.time(), 0.0, 0.0)):
            with patch.object(tool, 'get_corrected_time', return_value=1700000000.0):
                result = tool.get_authenticated_time(format="iso8601")

        assert "Z" in result or "+00:00" in result

    def test_get_authenticated_time_rfc3339(self):
        """Test get_authenticated_time with rfc3339 format."""
        tool = time_synchronizationTool()

        with patch.object(tool, 'sync_with_fallback', return_value=("ntp", time.time(), 0.0, 0.0)):
            with patch.object(tool, 'get_corrected_time', return_value=1700000000.0):
                result = tool.get_authenticated_time(format="rfc3339")

        assert "Z" in result or "+00:00" in result

    def test_get_authenticated_time_unix(self):
        """Test get_authenticated_time with unix format."""
        tool = time_synchronizationTool()

        with patch.object(tool, 'sync_with_fallback', return_value=("ntp", time.time(), 0.0, 0.0)):
            with patch.object(tool, 'get_corrected_time', return_value=1700000000.123456):
                result = tool.get_authenticated_time(format="unix")

        assert "1700000000.123456" == result

    def test_get_authenticated_time_human(self):
        """Test get_authenticated_time with human format."""
        tool = time_synchronizationTool()

        with patch.object(tool, 'sync_with_fallback', return_value=("ntp", time.time(), 0.0, 0.0)):
            with patch.object(tool, 'get_corrected_time', return_value=1700000000.0):
                result = tool.get_authenticated_time(format="human")

        assert "UTC" in result

    def test_get_authenticated_time_failure_format(self):
        """Test get_authenticated_time with failure format."""
        tool = time_synchronizationTool()

        with patch.object(tool, 'sync_with_fallback', side_effect=Exception("All failed")):
            result = tool.get_authenticated_time(format="failure")

        assert result == "[Null Time - Failure]"
        assert tool.is_enabled() is False  # Tool should be disabled

    def test_get_authenticated_time_unsupported_format(self):
        """Test get_authenticated_time with unsupported format."""
        tool = time_synchronizationTool()

        with patch.object(tool, 'sync_with_fallback', return_value=("ntp", time.time(), 0.0, 0.0)):
            with patch.object(tool, 'get_corrected_time', return_value=1700000000.0):
                # get_authenticated_time wraps ValueError in RuntimeError
                with pytest.raises(RuntimeError, match="Unsupported format"):
                    tool.get_authenticated_time(format="invalid")

    def test_get_authenticated_time_monotonic_warning(self, caplog):
        """Test get_authenticated_time logs warning for monotonic source."""
        import logging
        tool = time_synchronizationTool()

        with patch.object(tool, 'sync_with_fallback', return_value=("monotonic", time.time(), 0.0, 0.0)):
            with patch.object(tool, 'get_corrected_time', return_value=1700000000.0):
                with caplog.at_level(logging.WARNING):
                    tool.get_authenticated_time(format="iso8601")

        assert "pure monotonic" in caplog.text.lower() or "monotonic" in caplog.text.lower()

    def test_get_authenticated_time_fallback_warning(self, caplog):
        """Test get_authenticated_time logs warning for fallback source."""
        import logging
        tool = time_synchronizationTool()

        with patch.object(tool, 'sync_with_fallback', return_value=("rtc", time.time(), 0.0, 0.0)):
            with patch.object(tool, 'get_corrected_time', return_value=1700000000.0):
                with caplog.at_level(logging.WARNING):
                    tool.get_authenticated_time(format="iso8601")

        assert "fallback" in caplog.text.lower()


class TestTimeSyncToolFileTimestampCoverage:
    """Tests for file timestamp methods."""

    def test_get_file_timestamp_success(self):
        """Test _get_file_timestamp succeeds."""
        tool = time_synchronizationTool()

        mock_scanner = MagicMock()
        mock_scanner.get_recent_file_time.return_value = 1700000000.0

        with patch('nodupe.tools.time_sync.time_sync_tool.TargetedFileScanner', return_value=mock_scanner):
            result = tool._get_file_timestamp()

        assert result == 1700000000.0

    def test_get_file_timestamp_scanner_returns_none(self):
        """Test _get_file_timestamp when scanner returns None."""
        tool = time_synchronizationTool()

        mock_scanner = MagicMock()
        mock_scanner.get_recent_file_time.return_value = None

        with patch('nodupe.tools.time_sync.time_sync_tool.TargetedFileScanner', return_value=mock_scanner):
            with patch.object(tool, '_get_file_timestamp_fallback', return_value=1700000000.0):
                result = tool._get_file_timestamp()

        assert result == 1700000000.0

    def test_get_file_timestamp_scanner_exception(self):
        """Test _get_file_timestamp when scanner raises."""
        tool = time_synchronizationTool()

        mock_scanner = MagicMock()
        mock_scanner.get_recent_file_time.side_effect = Exception("Scanner failed")

        with patch('nodupe.tools.time_sync.time_sync_tool.TargetedFileScanner', return_value=mock_scanner):
            with patch.object(tool, '_get_file_timestamp_fallback', return_value=1700000000.0):
                result = tool._get_file_timestamp()

        assert result == 1700000000.0

    def test_get_file_timestamp_fallback_success(self):
        """Test _get_file_timestamp_fallback succeeds."""
        tool = time_synchronizationTool()

        with patch('nodupe.tools.time_sync.time_sync_tool.os.path.exists', return_value=True):
            with patch('nodupe.tools.time_sync.time_sync_tool.glob.glob', return_value=["/tmp/test.txt"]):
                with patch('nodupe.tools.time_sync.time_sync_tool.os.path.getmtime', return_value=1700000000.0):
                    result = tool._get_file_timestamp_fallback()

        assert result == 1700000000.0

    def test_get_file_timestamp_fallback_no_files(self):
        """Test _get_file_timestamp_fallback when no files found."""
        tool = time_synchronizationTool()

        with patch('nodupe.tools.time_sync.time_sync_tool.os.path.exists', return_value=False):
            with pytest.raises(RuntimeError, match="No suitable recent files"):
                tool._get_file_timestamp_fallback()

    def test_get_file_timestamp_fallback_invalid_timestamp(self):
        """Test _get_file_timestamp_fallback filters invalid timestamps."""
        tool = time_synchronizationTool()

        with patch('nodupe.tools.time_sync.time_sync_tool.os.path.exists', return_value=True):
            with patch('nodupe.tools.time_sync.time_sync_tool.glob.glob', return_value=["/tmp/test.txt"]):
                # Timestamp before 2002
                with patch('nodupe.tools.time_sync.time_sync_tool.os.path.getmtime', return_value=1000000000.0):
                    with pytest.raises(RuntimeError, match="No suitable recent files"):
                        tool._get_file_timestamp_fallback()

    def test_get_file_timestamp_fallback_os_error(self):
        """Test _get_file_timestamp_fallback handles OSError."""
        tool = time_synchronizationTool()

        with patch('nodupe.tools.time_sync.time_sync_tool.os.path.exists', return_value=True):
            with patch('nodupe.tools.time_sync.time_sync_tool.glob.glob', return_value=["/tmp/test.txt"]):
                with patch('nodupe.tools.time_sync.time_sync_tool.os.path.getmtime', side_effect=OSError("Permission denied")):
                    with pytest.raises(RuntimeError, match="No suitable recent files"):
                        tool._get_file_timestamp_fallback()


class TestTimeSyncToolRTCCoverage:
    """Tests for RTC methods."""

    def test_get_rtc_time_success(self):
        """Test _get_rtc_time succeeds."""
        tool = time_synchronizationTool()

        with patch('nodupe.tools.time_sync.time_sync_tool.time.time', return_value=1700000000.0):
            result = tool._get_rtc_time()

        assert result == 1700000000.0

    def test_get_rtc_time_invalid_past(self):
        """Test _get_rtc_time rejects time too far in past."""
        tool = time_synchronizationTool()

        with patch('nodupe.tools.time_sync.time_sync_tool.time.time', return_value=999999999.0):
            with pytest.raises(RuntimeError, match="RTC time appears invalid"):
                tool._get_rtc_time()

    def test_get_rtc_time_exception(self):
        """Test _get_rtc_time handles exceptions."""
        tool = time_synchronizationTool()

        with patch('nodupe.tools.time_sync.time_sync_tool.time.time', side_effect=Exception("Time failed")):
            with pytest.raises(RuntimeError, match="Failed to read system RTC"):
                tool._get_rtc_time()


class TestTimeSyncToolBackgroundCoverage:
    """Tests for background synchronization."""

    def test_start_background_disabled_instance(self):
        """Test start_background raises when instance disabled."""
        tool = time_synchronizationTool(enabled=False)

        with pytest.raises(time_synchronizationDisabledError, match="instance is disabled"):
            tool.start_background()

    def test_start_background_disabled_bg(self):
        """Test start_background raises when background disabled."""
        tool = time_synchronizationTool()
        tool.disable_background()

        with pytest.raises(time_synchronizationDisabledError, match="Background syncing is disabled"):
            tool.start_background()

    def test_start_background_disabled_network(self):
        """Test start_background raises when network disabled."""
        tool = time_synchronizationTool()
        tool.disable_network()

        with pytest.raises(time_synchronizationDisabledError, match="network is disabled"):
            tool.start_background()

    def test_start_background_already_running(self):
        """Test start_background when already running."""
        tool = time_synchronizationTool()

        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        tool._bg_thread = mock_thread

        # Should not raise, just return
        tool.start_background()

    def test_start_background_initial_sync_fails(self, caplog):
        """Test start_background when initial sync fails."""
        tool = time_synchronizationTool()

        with patch.object(tool, 'force_sync', side_effect=Exception("Sync failed")):
            with patch('nodupe.tools.time_sync.time_sync_tool.threading.Thread') as mock_thread_class:
                mock_thread = MagicMock()
                mock_thread_class.return_value = mock_thread
                tool.start_background(initial_sync=True)

        # Thread should still be started
        mock_thread.start.assert_called()

    def test_start_background_loop_sync_fails(self, caplog):
        """Test start_background loop when sync fails."""
        tool = time_synchronizationTool()

        call_count = [0]
        def mock_wait(timeout):
            """Mock wait function for background sync loop testing."""
            call_count[0] += 1
            if call_count[0] >= 3:
                return True  # Stop the loop
            return False

        mock_stop_event = MagicMock()
        mock_stop_event.wait.side_effect = mock_wait

        with patch.object(tool, 'force_sync', side_effect=Exception("Sync failed")):
            with patch('nodupe.tools.time_sync.time_sync_tool.threading.Event', return_value=mock_stop_event):
                with patch('nodupe.tools.time_sync.time_sync_tool.threading.Thread') as mock_thread_class:
                    mock_thread = MagicMock()
                    mock_thread_class.return_value = mock_thread

                    tool._bg_stop = mock_stop_event
                    tool.start_background(interval=0.1)

                    # Run the loop function manually to test error handling
                    # Get the target function from Thread call
                    target_func = mock_thread_class.call_args[1]['target']
                    # Run a few iterations
                    for _ in range(2):
                        try:
                            target_func()
                        except:
                            pass

    def test_stop_background_no_thread(self):
        """Test stop_background when no thread exists."""
        tool = time_synchronizationTool()
        tool._bg_thread = None

        # Should not raise
        tool.stop_background()

    def test_stop_background_with_wait(self):
        """Test stop_background with wait=True."""
        tool = time_synchronizationTool()

        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        tool._bg_thread = mock_thread

        tool.stop_background(wait=True, timeout=1.0)

        mock_thread.join.assert_called_with(timeout=1.0)

    def test_stop_background_without_wait(self):
        """Test stop_background with wait=False."""
        tool = time_synchronizationTool()

        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        tool._bg_thread = mock_thread

        tool.stop_background(wait=False)

        mock_thread.join.assert_not_called()


class TestTimeSyncToolStatusCoverage:
    """Tests for status and getter methods."""

    def test_get_sync_status_no_sync(self):
        """Test get_sync_status when not synced."""
        tool = time_synchronizationTool()

        status = tool.get_sync_status()

        assert status["sync_method"] == "none"
        assert status["sync_time"] is None

    def test_get_sync_status_ntp(self):
        """Test get_sync_status after NTP sync."""
        tool = time_synchronizationTool()
        tool._base_server_time = 1700000000.0
        tool._base_monotonic = 100.0
        tool._last_delay = 0.05

        status = tool.get_sync_status()

        assert status["sync_method"] == "ntp"
        assert status["has_external_reference"] is True

    def test_get_sync_status_rtc(self):
        """Test get_sync_status after RTC sync."""
        tool = time_synchronizationTool()
        tool._base_server_time = 1700000000.0
        tool._base_monotonic = 100.0
        tool._last_delay = None
        tool._smoothed_offset = 1700000000.0 - 100.0

        status = tool.get_sync_status()

        assert status["sync_method"] == "rtc"

    def test_get_sync_status_monotonic(self):
        """Test get_sync_status with monotonic only."""
        tool = time_synchronizationTool()
        tool._base_server_time = 1700000000.0
        tool._base_monotonic = 100.0
        tool._last_delay = None
        tool._smoothed_offset = 0.0  # Different from server_time - monotonic

        status = tool.get_sync_status()

        assert status["sync_method"] == "monotonic"

    def test_get_corrected_time_disabled(self):
        """Test get_corrected_time when disabled."""
        tool = time_synchronizationTool(enabled=False)

        result = tool.get_corrected_time()

        # Should return monotonic
        assert isinstance(result, float)

    def test_get_corrected_time_not_synced(self):
        """Test get_corrected_time when not synced."""
        tool = time_synchronizationTool()

        result = tool.get_corrected_time()

        # Should return monotonic
        assert isinstance(result, float)

    def test_get_corrected_time_synced(self):
        """Test get_corrected_time when synced."""
        tool = time_synchronizationTool()
        tool._base_server_time = 1700000000.0
        tool._base_monotonic = 100.0

        with patch('nodupe.tools.time_sync.time_sync_tool.time.monotonic', return_value=110.0):
            result = tool.get_corrected_time()

        assert result == 1700000010.0

    def test_get_corrected_fast64(self):
        """Test get_corrected_fast64."""
        tool = time_synchronizationTool()
        tool._base_server_time = 1700000000.0
        tool._base_monotonic = 100.0

        with patch('nodupe.tools.time_sync.time_sync_tool.time.monotonic', return_value=100.0):
            result = tool.get_corrected_fast64()

        assert isinstance(result, int)

    def test_get_offset_estimate(self):
        """Test get_offset_estimate."""
        tool = time_synchronizationTool()
        tool._smoothed_offset = 0.05

        result = tool.get_offset_estimate()

        assert result == 0.05

    def test_get_last_delay(self):
        """Test get_last_delay."""
        tool = time_synchronizationTool()
        tool._last_delay = 0.03

        result = tool.get_last_delay()

        assert result == 0.03


class TestTimeSyncToolFastDateCoverage:
    """Tests for FastDate encoding methods."""

    def test_encode_fastdate32_success(self):
        """Test encode_fastdate32 succeeds."""
        tool = time_synchronizationTool()

        result = tool.encode_fastdate(1000000.0)

        assert isinstance(result, int)

    def test_encode_fastdate32_negative(self):
        """Test encode_fastdate32 rejects negative."""
        tool = time_synchronizationTool()

        with pytest.raises(ValueError, match="Negative timestamps"):
            tool.encode_fastdate(-1.0)

    def test_encode_fastdate32_overflow(self):
        """Test encode_fastdate32 rejects overflow."""
        tool = time_synchronizationTool()

        # 2^22 = 4194304 seconds max
        with pytest.raises(ValueError, match="too large"):
            tool.encode_fastdate(5000000.0)

    def test_decode_fastdate32(self):
        """Test decode_fastdate32."""
        tool = time_synchronizationTool()

        encoded = tool.encode_fastdate(1000000.5)
        decoded = tool.decode_fastdate(encoded)

        assert abs(decoded - 1000000.5) < 0.002

    def test_encode_safedate_success(self):
        """Test encode_safedate succeeds."""
        tool = time_synchronizationTool()

        # Timestamp after 2024
        result = tool.encode_safedate(1704067201.0)

        assert isinstance(result, int)

    def test_encode_safedate_too_old(self):
        """Test encode_safedate rejects too old."""
        tool = time_synchronizationTool()

        # Timestamp before 2024
        with pytest.raises(ValueError, match="too far in the past"):
            tool.encode_safedate(1704067199.0)

    def test_encode_safedate_too_future(self):
        """Test encode_safedate rejects too far future."""
        tool = time_synchronizationTool()

        # Very far future
        with pytest.raises(ValueError, match="too far in the future"):
            tool.encode_safedate(1704067200.0 + 5000000.0)

    def test_decode_safedate(self):
        """Test decode_safedate."""
        tool = time_synchronizationTool()

        encoded = tool.encode_safedate(1704067201.5)
        decoded = tool.decode_safedate(encoded)

        assert abs(decoded - 1704067201.5) < 0.002

    def test_fastdate64_to_iso(self):
        """Test fastdate64_to_iso."""
        ts = 1700000000.0
        encoded = time_synchronizationTool.encode_fastdate64(ts)

        result = time_synchronizationTool.fastdate64_to_iso(encoded)

        assert "2023" in result or "2024" in result  # Around Nov 2023

    def test_iso_to_fastdate64_with_tz(self):
        """Test iso_to_fastdate64 with timezone."""
        iso = "2023-11-14T12:00:00+00:00"

        result = time_synchronizationTool.iso_to_fastdate64(iso)

        assert isinstance(result, int)

    def test_iso_to_fastdate64_without_tz(self):
        """Test iso_to_fastdate64 without timezone."""
        iso = "2023-11-14T12:00:00"

        result = time_synchronizationTool.iso_to_fastdate64(iso)

        assert isinstance(result, int)


class TestTimeSyncToolConvenienceCoverage:
    """Tests for convenience methods."""

    def test_get_timestamp_alias(self):
        """Test get_timestamp is alias for get_corrected_time."""
        tool = time_synchronizationTool()
        tool._base_server_time = 1700000000.0
        tool._base_monotonic = 100.0

        with patch('nodupe.tools.time_sync.time_sync_tool.time.monotonic', return_value=100.0):
            result1 = tool.get_corrected_time()
            result2 = tool.get_timestamp()

        assert result1 == result2

    def test_get_timestamp_fast64_alias(self):
        """Test get_timestamp_fast64 is alias for get_corrected_fast64."""
        tool = time_synchronizationTool()
        tool._base_server_time = 1700000000.0
        tool._base_monotonic = 100.0

        with patch('nodupe.tools.time_sync.time_sync_tool.time.monotonic', return_value=100.0):
            result1 = tool.get_corrected_fast64()
            result2 = tool.get_timestamp_fast64()

        assert result1 == result2

    def test_get_status(self):
        """Test get_status returns complete status."""
        tool = time_synchronizationTool()
        tool._base_server_time = 1700000000.0
        tool._base_monotonic = 100.0
        tool._smoothed_offset = 0.05
        tool._last_delay = 0.03

        status = tool.get_status()

        assert status["enabled"] is True
        assert status["base_server_time"] == 1700000000.0
        assert status["smoothed_offset"] == 0.05
        assert status["last_delay"] == 0.03


class TestLeapYearCalculatorCoverage:
    """Tests for LeapYearCalculator edge cases."""

    def test_calculator_initialization_exception(self):
        """Test LeapYearCalculator initialization when import fails."""
        with patch('nodupe.tools.leap_year.LeapYearTool', side_effect=ImportError("Not found")):
            calc = LeapYearCalculator()

        assert calc._use_tool is False
        assert calc._leap_year_tool is None

    def test_is_leap_year_tool_exception_fallback(self):
        """Test is_leap_year falls back on tool exception."""
        calc = LeapYearCalculator()
        calc._use_tool = True
        calc._leap_year_tool = MagicMock()
        calc._leap_year_tool.is_leap_year.side_effect = Exception("Tool error")

        # Should fall back to builtin
        result = calc.is_leap_year(2024)

        assert result is True  # 2024 is a leap year


class TestRegisterToolCoverage:
    """Tests for register_tool function."""

    def test_register_tool(self):
        """Test register_tool returns tool instance."""
        tool = register_tool()

        assert isinstance(tool, time_synchronizationTool)
        assert tool.name == "time_synchronization"


class TestDescribeUsageCoverage:
    """Tests for describe_usage method."""

    def test_describe_usage(self):
        """Test describe_usage returns usage string."""
        tool = time_synchronizationTool()

        usage = tool.describe_usage()

        assert "Time Synchronization Tool Usage" in usage
        assert "NTP" in usage
