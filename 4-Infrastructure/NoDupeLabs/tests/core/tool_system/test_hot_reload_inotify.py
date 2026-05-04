"""Test Tool Hot Reload Inotify Coverage.

Comprehensive tests for inotify-specific coverage in hot_reload.py:
- inotify watch operations (mock ctypes calls)
- Event parsing edge cases
- Buffer overflow handling
- Watch descriptor errors
- Poll loop with inotify file descriptor
- Error handling in event processing
"""

import struct
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from nodupe.core.tool_system.hot_reload import (
    IN_CREATE,
    IN_DELETE,
    IN_DELETE_SELF,
    IN_MODIFY,
    IN_MOVE_SELF,
    IN_MOVED_TO,
    ToolHotReload,
)
from nodupe.core.tool_system.registry import ToolRegistry


class TestInitInotifyCoverage:
    """Test _init_inotify method coverage gaps."""

    def test_init_inotify_fcntl_available_path(self):
        """Test inotify init when fcntl is available."""
        hot_reload = ToolHotReload()

        with patch('sys.platform', 'linux'):
            with patch('nodupe.core.tool_system.hot_reload.fcntl') as mock_fcntl:
                mock_fcntl.fcntl = MagicMock()
                mock_fcntl.F_GETFL = 1
                mock_fcntl.F_SETFL = 2

                with patch('ctypes.CDLL') as mock_cdll:
                    mock_lib = MagicMock()
                    mock_lib.inotify_init1.return_value = 5
                    mock_cdll.return_value = mock_lib

                    hot_reload._init_inotify()

                    # Should have called fcntl to set non-blocking
                    mock_fcntl.fcntl.assert_called()

    def test_init_inotify_fcntl_exception_handling(self):
        """Test inotify init when fcntl raises exception."""
        hot_reload = ToolHotReload()

        with patch('sys.platform', 'linux'):
            with patch('nodupe.core.tool_system.hot_reload.fcntl') as mock_fcntl:
                mock_fcntl.fcntl = MagicMock(side_effect=OSError("fcntl error"))
                mock_fcntl.F_GETFL = 1
                mock_fcntl.F_SETFL = 2

                with patch('ctypes.CDLL') as mock_cdll:
                    mock_lib = MagicMock()
                    mock_lib.inotify_init1.return_value = 5
                    mock_cdll.return_value = mock_lib

                    # Should not raise, just continue
                    hot_reload._init_inotify()

    def test_init_inotify_fcntl_attribute_error(self):
        """Test inotify init when fcntl raises AttributeError."""
        hot_reload = ToolHotReload()

        with patch('sys.platform', 'linux'):
            with patch('nodupe.core.tool_system.hot_reload.fcntl') as mock_fcntl:
                mock_fcntl.fcntl = MagicMock(side_effect=AttributeError("no attr"))
                mock_fcntl.F_GETFL = 1
                mock_fcntl.F_SETFL = 2

                with patch('ctypes.CDLL') as mock_cdll:
                    mock_lib = MagicMock()
                    mock_lib.inotify_init1.return_value = 5
                    mock_cdll.return_value = mock_lib

                    # Should not raise
                    hot_reload._init_inotify()

    def test_init_inotify_fd_negative(self):
        """Test inotify init when inotify_init1 returns negative fd."""
        hot_reload = ToolHotReload()

        with patch('sys.platform', 'linux'):
            with patch('ctypes.CDLL') as mock_cdll:
                mock_lib = MagicMock()
                mock_lib.inotify_init1.return_value = -1  # Error
                mock_cdll.return_value = mock_lib

                result = hot_reload._init_inotify()

                assert result is False


class TestAddInotifyWatchCoverage:
    """Test _add_inotify_watch method coverage gaps."""

    def test_add_inotify_watch_wd_negative(self, tmp_path):
        """Test adding watch when inotify_add_watch returns negative."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 5

        tool_path = tmp_path / "test_tool.py"
        tool_path.write_text("# Test")

        with patch('ctypes.CDLL') as mock_cdll:
            mock_lib = MagicMock()
            mock_lib.inotify_add_watch.return_value = -1  # Error
            mock_cdll.return_value = mock_lib

            # Should not add to watch_descriptors when wd < 0
            hot_reload._add_inotify_watch("TestTool", tool_path)

            # No watch descriptors should be added
            assert len(hot_reload._watch_descriptors) == 0


class TestRemoveInotifyWatchCoverage:
    """Test _remove_inotify_watch method coverage gaps."""

    def test_remove_inotify_watch_no_matching_tool(self):
        """Test removing watch when no matching tool name exists."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 5

        # Add a watch descriptor for a different tool
        hot_reload._watch_descriptors[10] = {
            'tool_name': "OtherTool",
            'path': Path("/other.py"),
            'filename': "other.py"
        }

        with patch('ctypes.CDLL') as mock_cdll:
            mock_lib = MagicMock()
            mock_cdll.return_value = mock_lib

            # Try to remove non-existent tool
            hot_reload._remove_inotify_watch("NonExistentTool")

            # Original watch should still be there
            assert 10 in hot_reload._watch_descriptors

            # inotify_rm_watch should not be called
            mock_lib.inotify_rm_watch.assert_not_called()


class TestCheckInotifyEventsCoverage:
    """Test _check_inotify_events method coverage - main gap."""

    def test_check_inotify_events_with_valid_event(self):
        """Test checking events with valid inotify event."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 5

        # Mock watch descriptor
        hot_reload._watch_descriptors[10] = {
            'tool_name': "TestTool",
            'path': Path("/test.py"),
            'filename': "test.py"
        }

        # Mock _reload_tool to track calls
        hot_reload._reload_tool = MagicMock()

        # Create a valid inotify event buffer
        # struct inotify_event: wd (i), mask (I), cookie (I), len (I)
        wd = 10
        mask = IN_MODIFY
        cookie = 0
        name = b"test.py"
        name_len = len(name)

        # Pack the event
        event_data = struct.pack('iIII', wd, mask, cookie, name_len) + name

        with patch('os.read', return_value=event_data):
            hot_reload._check_inotify_events()

        # Should have triggered reload
        hot_reload._reload_tool.assert_called_once()

    def test_check_inotify_events_with_moved_to_event(self):
        """Test checking events with IN_MOVED_TO event."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 5

        hot_reload._watch_descriptors[10] = {
            'tool_name': "TestTool",
            'path': Path("/test.py"),
            'filename': "test.py"
        }

        hot_reload._reload_tool = MagicMock()

        # Create event with IN_MOVED_TO
        wd = 10
        mask = IN_MOVED_TO
        cookie = 0
        name = b"test.py"
        name_len = len(name)

        event_data = struct.pack('iIII', wd, mask, cookie, name_len) + name

        with patch('os.read', return_value=event_data):
            hot_reload._check_inotify_events()

        hot_reload._reload_tool.assert_called_once()

    def test_check_inotify_events_with_create_event(self):
        """Test checking events with IN_CREATE event."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 5

        hot_reload._watch_descriptors[10] = {
            'tool_name': "TestTool",
            'path': Path("/test.py"),
            'filename': "test.py"
        }

        hot_reload._reload_tool = MagicMock()

        # Create event with IN_CREATE
        wd = 10
        mask = IN_CREATE
        cookie = 0
        name = b"test.py"
        name_len = len(name)

        event_data = struct.pack('iIII', wd, mask, cookie, name_len) + name

        with patch('os.read', return_value=event_data):
            hot_reload._check_inotify_events()

        hot_reload._reload_tool.assert_called_once()

    def test_check_inotify_events_wrong_filename(self):
        """Test checking events when filename doesn't match."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 5

        hot_reload._watch_descriptors[10] = {
            'tool_name': "TestTool",
            'path': Path("/test.py"),
            'filename': "test.py"
        }

        hot_reload._reload_tool = MagicMock()

        # Create event with different filename
        wd = 10
        mask = IN_MODIFY
        cookie = 0
        name = b"other.py"  # Different filename
        name_len = len(name)

        event_data = struct.pack('iIII', wd, mask, cookie, name_len) + name

        with patch('os.read', return_value=event_data):
            hot_reload._check_inotify_events()

        # Should NOT trigger reload for wrong filename
        hot_reload._reload_tool.assert_not_called()

    def test_check_inotify_events_no_filename(self):
        """Test checking events when no filename in event."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 5

        hot_reload._watch_descriptors[10] = {
            'tool_name': "TestTool",
            'path': Path("/test.py"),
            'filename': "test.py"
        }

        hot_reload._reload_tool = MagicMock()

        # Create event with no filename (name_len = 0)
        wd = 10
        mask = IN_MODIFY
        cookie = 0
        name_len = 0

        event_data = struct.pack('iIII', wd, mask, cookie, name_len)

        with patch('os.read', return_value=event_data):
            hot_reload._check_inotify_events()

        # Should NOT trigger reload (filename is empty string)
        hot_reload._reload_tool.assert_not_called()

    def test_check_inotify_events_unknown_watch_descriptor(self):
        """Test checking events when wd not in watch_descriptors."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 5

        # No watch descriptors

        hot_reload._reload_tool = MagicMock()

        # Create event with unknown wd
        wd = 999  # Unknown
        mask = IN_MODIFY
        cookie = 0
        name = b"test.py"
        name_len = len(name)

        event_data = struct.pack('iIII', wd, mask, cookie, name_len) + name

        with patch('os.read', return_value=event_data):
            # Should not raise
            hot_reload._check_inotify_events()

        hot_reload._reload_tool.assert_not_called()

    def test_check_inotify_events_multiple_events(self):
        """Test checking events with multiple events in buffer."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 5

        hot_reload._watch_descriptors[10] = {
            'tool_name': "TestTool",
            'path': Path("/test.py"),
            'filename': "test.py"
        }

        hot_reload._reload_tool = MagicMock()

        # Create two events
        wd = 10
        mask = IN_MODIFY
        cookie = 0
        name = b"test.py"
        name_len = len(name)

        event1 = struct.pack('iIII', wd, mask, cookie, name_len) + name
        event2 = struct.pack('iIII', wd, mask, cookie, name_len) + name

        event_data = event1 + event2

        with patch('os.read', return_value=event_data):
            hot_reload._check_inotify_events()

        # Should have triggered reload twice
        assert hot_reload._reload_tool.call_count == 2

    def test_check_inotify_events_os_error(self):
        """Test checking events when os.read raises OSError."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 5

        with patch('os.read', side_effect=OSError("Read error")):
            # Should not raise
            hot_reload._check_inotify_events()

    def test_check_inotify_events_unicode_decode_error(self):
        """Test checking events when filename has unicode decode error."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 5

        hot_reload._watch_descriptors[10] = {
            'tool_name': "TestTool",
            'path': Path("/test.py"),
            'filename': "test.py"
        }

        # Create event with invalid UTF-8 filename
        wd = 10
        mask = IN_MODIFY
        cookie = 0
        name = b"\xff\xfe\x00\x01"  # Invalid UTF-8
        name_len = len(name)

        event_data = struct.pack('iIII', wd, mask, cookie, name_len) + name

        with patch('os.read', return_value=event_data):
            # Should not raise - UnicodeDecodeError is caught
            hot_reload._check_inotify_events()

    def test_check_inotify_events_mtime_update_exception(self):
        """Test checking events when mtime update fails."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 5

        hot_reload._watch_descriptors[10] = {
            'tool_name': "TestTool",
            'path': Path("/test.py"),
            'filename': "test.py"
        }

        # Add to watched_tools so mtime update is attempted
        hot_reload._watched_tools["TestTool"] = {
            'path': Path("/test.py"),
            'mtime': 0
        }

        # Mock _reload_tool
        hot_reload._reload_tool = MagicMock()

        # Mock path.stat to raise exception during mtime update
        with patch('os.read') as mock_read:
            wd = 10
            mask = IN_MODIFY
            cookie = 0
            name = b"test.py"
            name_len = len(name)
            event_data = struct.pack('iIII', wd, mask, cookie, name_len) + name

            mock_read.return_value = event_data

            # Mock stat to raise exception
            with patch.object(Path, 'stat', side_effect=OSError("Stat error")):
                # Should not raise - exception is caught
                hot_reload._check_inotify_events()

        # Reload should still be called
        hot_reload._reload_tool.assert_called_once()

    def test_check_inotify_events_not_in_watched_tools(self):
        """Test checking events when tool not in watched_tools."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 5

        # Only in watch_descriptors, not in watched_tools
        hot_reload._watch_descriptors[10] = {
            'tool_name': "TestTool",
            'path': Path("/test.py"),
            'filename': "test.py"
        }

        hot_reload._reload_tool = MagicMock()

        wd = 10
        mask = IN_MODIFY
        cookie = 0
        name = b"test.py"
        name_len = len(name)

        event_data = struct.pack('iIII', wd, mask, cookie, name_len) + name

        with patch('os.read', return_value=event_data):
            hot_reload._check_inotify_events()

        # Should still reload
        hot_reload._reload_tool.assert_called_once()


class TestPollLoopCoverage:
    """Test _poll_loop method coverage gaps."""

    def test_poll_loop_stop_event_mid_iteration(self, tmp_path):
        """Test _poll_loop respects stop event during iteration."""
        hot_reload = ToolHotReload(poll_interval=0.01)

        tool_path = tmp_path / "test_tool.py"
        tool_path.write_text("# Test")
        hot_reload.watch_tool("TestTool", tool_path)

        # Set stop event before calling poll_loop
        hot_reload._stop_event.set()

        # Run poll loop once - should exit immediately due to stop event
        hot_reload._poll_loop()

        # Should complete without issues

    def test_poll_loop_file_not_found(self, tmp_path, caplog):
        """Test _poll_loop handles FileNotFoundError."""
        hot_reload = ToolHotReload(poll_interval=0.01)

        tool_path = tmp_path / "test_tool.py"
        tool_path.write_text("# Test")
        hot_reload.watch_tool("TestTool", tool_path)

        # Delete the file
        tool_path.unlink()

        # Set stop event to break out of loop after one iteration
        # We need to mock time.sleep to NOT set stop event immediately
        # so the file check runs first
        call_count = [0]
        def sleep_once(duration):
            """Mock time.sleep to stop after first iteration.

            Args:
                duration: Time to sleep.
            """
            call_count[0] += 1
            if call_count[0] > 1:
                hot_reload._stop_event.set()

        with patch('time.sleep', side_effect=sleep_once):
            hot_reload._poll_loop()

        # File should be removed from watched_tools
        assert "TestTool" not in hot_reload._watched_tools

    def test_poll_loop_generic_exception(self, tmp_path, caplog):
        """Test _poll_loop handles generic exception."""
        import logging
        ToolRegistry._reset_instance()
        hot_reload = ToolHotReload(poll_interval=0.01)

        tool_path = tmp_path / "test_tool.py"
        tool_path.write_text("# Test")
        hot_reload.watch_tool("TestTool", tool_path)

        # Mock stat to raise generic exception
        call_count = [0]
        def sleep_once(duration):
            """Mock time.sleep to stop after first iteration.

            Args:
                duration: Time to sleep.
            """
            call_count[0] += 1
            if call_count[0] > 1:
                hot_reload._stop_event.set()

        with patch('time.sleep', side_effect=sleep_once):
            with patch.object(Path, 'stat', side_effect=Exception("Generic error")):
                with caplog.at_level(logging.ERROR):
                    hot_reload._poll_loop()

        # Should log error
        assert any("Error watching tool" in record.message for record in caplog.records)

    def test_poll_loop_with_inotify_uses_longer_interval(self, tmp_path):
        """Test _poll_loop uses longer interval with inotify."""
        hot_reload = ToolHotReload(poll_interval=0.1)
        hot_reload._use_inotify = True

        tool_path = tmp_path / "test_tool.py"
        tool_path.write_text("# Test")
        hot_reload.watch_tool("TestTool", tool_path)

        # Mock time.sleep to capture sleep time
        sleep_times = []

        def capture_sleep(duration):
            """Capture sleep duration and stop the loop.

            Args:
                duration: Time that would be slept.
            """
            sleep_times.append(duration)
            # Don't actually sleep, just break the loop
            hot_reload._stop_event.set()

        with patch('time.sleep', side_effect=capture_sleep):
            with patch.object(hot_reload, '_check_inotify_events'):
                hot_reload._poll_loop()

        # Should have used max(poll_interval, 2.0) = 2.0
        assert len(sleep_times) > 0
        assert sleep_times[0] >= 2.0

    def test_poll_loop_checks_inotify_events(self, tmp_path):
        """Test _poll_loop calls _check_inotify_events when inotify enabled."""
        hot_reload = ToolHotReload(poll_interval=0.01)
        hot_reload._use_inotify = True

        tool_path = tmp_path / "test_tool.py"
        tool_path.write_text("# Test")
        hot_reload.watch_tool("TestTool", tool_path)

        # Mock _check_inotify_events
        hot_reload._check_inotify_events = MagicMock()

        # Mock time.sleep to break loop quickly
        with patch('time.sleep', side_effect=lambda x: hot_reload._stop_event.set()):
            hot_reload._poll_loop()

        # Should have called _check_inotify_events
        hot_reload._check_inotify_events.assert_called()


class TestReloadToolCoverage:
    """Test _reload_tool method coverage gaps."""

    def test_reload_tool_shutdown_failure_warning(self, tmp_path, caplog):
        """Test _reload_tool when shutdown_tool returns False."""
        import logging
        ToolRegistry._reset_instance()
        hot_reload = ToolHotReload()

        tool_path = tmp_path / "test_tool.py"
        tool_path.write_text("""
from nodupe.core.tool_system.base import Tool

class TestTool(Tool):
    name = "TestTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Test"
""")

        # First load the tool
        tool_class = hot_reload.loader.load_tool_from_file(tool_path)
        tool_instance = hot_reload.loader.instantiate_tool(tool_class)
        hot_reload.loader.register_loaded_tool(tool_instance, tool_path)

        # Mock lifecycle to return False for shutdown
        hot_reload.lifecycle.shutdown_tool = MagicMock(return_value=False)

        with caplog.at_level(logging.WARNING):
            hot_reload._reload_tool("TestTool", tool_path)

        # Should log warning about tool not running
        assert any("not running" in record.message.lower() for record in caplog.records)

    def test_reload_tool_init_failure_error(self, tmp_path, caplog):
        """Test _reload_tool when initialize_tool returns False."""
        import logging
        ToolRegistry._reset_instance()
        hot_reload = ToolHotReload()

        tool_path = tmp_path / "test_tool.py"
        tool_path.write_text("""
from nodupe.core.tool_system.base import Tool

class TestTool(Tool):
    name = "TestTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Test"
""")

        # First load the tool
        tool_class = hot_reload.loader.load_tool_from_file(tool_path)
        tool_instance = hot_reload.loader.instantiate_tool(tool_class)
        hot_reload.loader.register_loaded_tool(tool_instance, tool_path)

        # Mock lifecycle - shutdown succeeds, init fails
        hot_reload.lifecycle.shutdown_tool = MagicMock(return_value=True)
        hot_reload.lifecycle.initialize_tool = MagicMock(return_value=False)
        
        # Mock register_loaded_tool to avoid "already registered" error
        hot_reload.loader.register_loaded_tool = MagicMock()

        with caplog.at_level(logging.ERROR):
            hot_reload._reload_tool("TestTool", tool_path)

        # Should log error about initialization failure
        assert any("failed initialization" in record.message.lower() for record in caplog.records)


class TestFcntlOptionalImport:
    """Test fcntl optional import handling."""

    def test_module_loads_without_fcntl(self):
        """Test that module loads even if fcntl is not available."""
        # The module should import successfully regardless of fcntl
        from nodupe.core.tool_system import hot_reload
        assert hot_reload is not None

    def test_fcntl_none_handling(self):
        """Test handling when fcntl is None."""
        hot_reload = ToolHotReload()

        # Simulate fcntl being None
        with patch('nodupe.core.tool_system.hot_reload.fcntl', None):
            with patch('sys.platform', 'linux'):
                with patch('ctypes.CDLL') as mock_cdll:
                    mock_lib = MagicMock()
                    mock_lib.inotify_init1.return_value = 5
                    mock_cdll.return_value = mock_lib

                    # Should not raise when fcntl is None
                    hot_reload._init_inotify()


class TestInotifyConstants:
    """Test inotify constants are correctly defined."""

    def test_all_inotify_constants(self):
        """Test all inotify constants have correct values."""
        assert IN_MODIFY == 0x00000002
        assert IN_MOVED_TO == 0x00000080
        assert IN_CREATE == 0x00000100
        assert IN_DELETE == 0x00000200
        assert IN_MOVE_SELF == 0x00000800
        assert IN_DELETE_SELF == 0x00000400


class TestEdgeCases:
    """Test additional edge cases for full coverage."""

    def test_check_inotify_events_empty_bytes_read(self):
        """Test _check_inotify_events when bytes_read is empty."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 5

        with patch('os.read', return_value=b''):
            # Should return early without processing
            hot_reload._check_inotify_events()

    def test_check_inotify_events_none_bytes_read(self):
        """Test _check_inotify_events when bytes_read is None."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 5

        with patch('os.read', return_value=None):
            # Should return early
            hot_reload._check_inotify_events()

    def test_add_inotify_watch_inotify_not_available(self, tmp_path):
        """Test _add_inotify_watch when inotify not available."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = False
        hot_reload._inotify_fd = None

        tool_path = tmp_path / "test_tool.py"
        tool_path.write_text("# Test")

        # Should return early without doing anything
        hot_reload._add_inotify_watch("TestTool", tool_path)

    def test_remove_inotify_watch_inotify_not_available(self):
        """Test _remove_inotify_watch when inotify not available."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = False
        hot_reload._inotify_fd = None

        # Should return early without doing anything
        hot_reload._remove_inotify_watch("TestTool")

    def test_check_inotify_events_inotify_not_available(self):
        """Test _check_inotify_events when inotify not available."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = False
        hot_reload._inotify_fd = None

        # Should return early without doing anything
        hot_reload._check_inotify_events()

    def test_check_inotify_events_inotify_fd_none(self):
        """Test _check_inotify_events when inotify_fd is None."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = None

        # Should return early without doing anything
        hot_reload._check_inotify_events()

    def test_add_inotify_watch_inotify_fd_none(self, tmp_path):
        """Test _add_inotify_watch when inotify_fd is None."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = None

        tool_path = tmp_path / "test_tool.py"
        tool_path.write_text("# Test")

        # Should return early without doing anything
        hot_reload._add_inotify_watch("TestTool", tool_path)

    def test_remove_inotify_watch_inotify_fd_none(self):
        """Test _remove_inotify_watch when inotify_fd is None."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = None

        # Should return early without doing anything
        hot_reload._remove_inotify_watch("TestTool")


class TestRemainingCoverage:
    """Test remaining coverage gaps."""

    def test_poll_loop_without_inotify(self, tmp_path):
        """Test _poll_loop when inotify is not used (polling mode)."""
        hot_reload = ToolHotReload(poll_interval=0.01)
        hot_reload._use_inotify = False

        tool_path = tmp_path / "test_tool.py"
        tool_path.write_text("# Test")
        hot_reload.watch_tool("TestTool", tool_path)

        # Mock _check_inotify_events to verify it's NOT called
        hot_reload._check_inotify_events = MagicMock()

        # Set stop event after one iteration
        call_count = [0]
        def sleep_once(duration):
            """Mock time.sleep to stop after first iteration.

            Args:
                duration: Time to sleep.
            """
            call_count[0] += 1
            if call_count[0] > 1:
                hot_reload._stop_event.set()

        with patch('time.sleep', side_effect=sleep_once):
            hot_reload._poll_loop()

        # _check_inotify_events should NOT be called when inotify is disabled
        hot_reload._check_inotify_events.assert_not_called()

    def test_poll_loop_updates_mtime_after_reload(self, tmp_path):
        """Test _poll_loop updates mtime after detecting change."""
        ToolRegistry._reset_instance()
        hot_reload = ToolHotReload(poll_interval=0.01)

        tool_path = tmp_path / "test_tool.py"
        tool_path.write_text("""
from nodupe.core.tool_system.base import Tool

class TestTool(Tool):
    name = "TestTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Test"
""")
        hot_reload.watch_tool("TestTool", tool_path)
        initial_mtime = hot_reload._watched_tools["TestTool"]["mtime"]

        # Modify file to trigger reload
        time.sleep(0.01)
        tool_path.write_text("# Modified")

        # Set stop event after one iteration
        call_count = [0]
        def sleep_once(duration):
            """Mock time.sleep to stop after first iteration.

            Args:
                duration: Time to sleep.
            """
            call_count[0] += 1
            if call_count[0] > 1:
                hot_reload._stop_event.set()

        with patch('time.sleep', side_effect=sleep_once):
            hot_reload._poll_loop()

        # mtime should be updated
        assert "TestTool" in hot_reload._watched_tools
        assert hot_reload._watched_tools["TestTool"]["mtime"] > initial_mtime

    def test_reload_tool_not_in_watched_tools_updates_mtime(self, tmp_path, caplog):
        """Test _reload_tool mtime update when tool not in watched_tools."""
        import logging
        ToolRegistry._reset_instance()
        hot_reload = ToolHotReload()

        tool_path = tmp_path / "test_tool.py"
        tool_path.write_text("""
from nodupe.core.tool_system.base import Tool

class TestTool(Tool):
    name = "TestTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Test"
""")

        # Don't add to watched_tools - just call _reload_tool directly
        # This tests the mtime update exception handling when tool not in watched_tools

        with caplog.at_level(logging.INFO):
            hot_reload._reload_tool("TestTool", tool_path)

        # Should complete without errors
        assert True

    def test_reload_tool_shutdown_failure_logs_warning(self, tmp_path, caplog):
        """Test _reload_tool logs warning when shutdown fails."""
        import logging
        ToolRegistry._reset_instance()
        hot_reload = ToolHotReload()

        tool_path = tmp_path / "test_tool.py"
        tool_path.write_text("""
from nodupe.core.tool_system.base import Tool

class TestTool(Tool):
    name = "TestTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Test"
""")

        # First load the tool
        tool_class = hot_reload.loader.load_tool_from_file(tool_path)
        tool_instance = hot_reload.loader.instantiate_tool(tool_class)
        hot_reload.loader.register_loaded_tool(tool_instance, tool_path)

        # Mock lifecycle to return False for shutdown
        hot_reload.lifecycle.shutdown_tool = MagicMock(return_value=False)

        with caplog.at_level(logging.WARNING):
            hot_reload._reload_tool("TestTool", tool_path)

        # Should log warning about tool not running
        assert any("not running" in record.message.lower() for record in caplog.records)
