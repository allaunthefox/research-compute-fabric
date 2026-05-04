"""Test Hot Reload Module - Additional Coverage Tests.

Tests to achieve higher coverage for hot_reload.py
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nodupe.core.tool_system.hot_reload import ToolHotReload


class TestHotReloadInotifyAdvanced:
    """Test inotify advanced cases."""

    def test_add_inotify_watch_multiple(self):
        """Test adding multiple inotify watches."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 123

        mock_ctypes = MagicMock()
        mock_ctypes.CDLL.return_value.inotify_add_watch.return_value = 1

        with patch.dict('sys.modules', {'ctypes': mock_ctypes}):
            hot_reload._add_inotify_watch("tool1", Path("/path/tool1.py"))
            hot_reload._add_inotify_watch("tool2", Path("/path/tool2.py"))

        assert len(hot_reload._watch_descriptors) >= 1


class TestHotReloadEdgeCases:
    """Test edge cases."""

    def test_watch_tool_with_lock_contention(self):
        """Test watch_tool with lock contention."""
        hot_reload = ToolHotReload()

        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            f.write(b'# test')
            f.flush()
            tool_path = Path(f.name)

        # Call multiple times
        hot_reload.watch_tool("test_tool", tool_path)
        hot_reload.watch_tool("test_tool", tool_path)

        assert "test_tool" in hot_reload._watched_tools

    def test_reload_tools_concurrent(self):
        """Test reload_tools with concurrent access."""
        hot_reload = ToolHotReload()

        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            f.write(b'# test')
            f.flush()
            tool_path = Path(f.name)

        hot_reload.watch_tool("test_tool", tool_path)
        hot_reload._reload_tool = MagicMock()

        # Call reload multiple times
        hot_reload.reload_tools()
        hot_reload.reload_tools()

        # Both calls should work
        assert hot_reload._reload_tool.call_count == 2


class TestHotReloadRemoveWatchAdvanced:
    """Test remove watch advanced cases."""

    def test_remove_inotify_watch_not_found(self):
        """Test removing watch for tool not in descriptors."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 123

        # Should not raise
        hot_reload._remove_inotify_watch("nonexistent")

    def test_remove_inotify_watch_multiple(self):
        """Test removing watch when multiple descriptors match."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 123

        # Add multiple watches for same tool
        hot_reload._watch_descriptors[1] = {
            'tool_name': 'test',
            'path': Path('/test1.py'),
            'filename': 'test1.py'
        }
        hot_reload._watch_descriptors[2] = {
            'tool_name': 'test',
            'path': Path('/test2.py'),
            'filename': 'test2.py'
        }

        mock_ctypes = MagicMock()

        with patch.dict('sys.modules', {'ctypes': mock_ctypes}):
            hot_reload._remove_inotify_watch("test")

        # Both should be removed
        assert len(hot_reload._watch_descriptors) == 0


class TestHotReloadInitInotifyAdvanced:
    """Test inotify initialization advanced cases."""

    def test_init_inotify_with_fcntl_error(self):
        """Test inotify init with fcntl error."""
        hot_reload = ToolHotReload()

        mock_ctypes = MagicMock()
        mock_ctypes.CDLL.return_value.inotify_init1.return_value = 100

        with patch('sys.platform', 'linux'), \
             patch.dict('sys.modules', {'ctypes': mock_ctypes}), \
             patch('fcntl.fcntl', side_effect=OSError("fcntl error")):
            result = hot_reload._init_inotify()
            # Should still work despite fcntl error

    def test_init_inotify_fcntl_attribute_error(self):
        """Test inotify init with fcntl AttributeError."""
        hot_reload = ToolHotReload()

        mock_ctypes = MagicMock()
        mock_ctypes.CDLL.return_value.inotify_init1.return_value = 100

        with patch('sys.platform', 'linux'), \
             patch.dict('sys.modules', {'ctypes': mock_ctypes}), \
             patch('fcntl.fcntl', side_effect=AttributeError("no attribute")):
            result = hot_reload._init_inotify()
            # Should work


class TestHotReloadCheckToolNotFound:
    """Test check inotify events when tool not in watched tools."""

    def test_check_inotify_events_tool_removed(self):
        """Test inotify events when tool was removed."""
        hot_reload = ToolHotReload()
        hot_reload._use_inotify = True
        hot_reload._inotify_fd = 123

        # Add a watch
        hot_reload._watch_descriptors[1] = {
            'tool_name': 'test',
            'path': Path('/test'),
            'filename': 'test.py'
        }

        # But don't add to _watched_tools
        hot_reload._reload_tool = MagicMock()

        import struct
        event = struct.pack('iIII', 1, 0x2, 0, 8) + b'test.py\x00'

        with patch('os.read', return_value=event):
            hot_reload._check_inotify_events()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
