"""Extra tests for remaining coverage gaps - part 2."""

import time
from unittest.mock import MagicMock, patch

from nodupe.core.tool_system.hot_reload import ToolHotReload
from nodupe.core.tool_system.registry import ToolRegistry


class TestRemainingCoverageExtra2:
    """Test remaining coverage gaps."""

    def test_poll_loop_mtime_update_name_not_in_watched_tools(self, tmp_path):
        """Test _poll_loop mtime update when name not in watched_tools."""
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

        # Modify file to trigger reload
        time.sleep(0.01)
        tool_path.write_text("# Modified")

        # Mock _reload_tool to delete from watched_tools during reload
        # This simulates the case where the tool is removed during reload
        def mock_reload_and_delete(name, path):
            """Mock reload that removes tool from watched_tools during reload.

            Args:
                name: Name of the tool.
                path: Path to the tool file.
            """
            # Delete from watched_tools during reload
            hot_reload._watched_tools.pop(name, None)
        
        hot_reload._reload_tool = mock_reload_and_delete

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
            # Should not raise even though name not in watched_tools after reload
            hot_reload._poll_loop()

        # Should complete without errors
        assert True

    def test_reload_tool_load_returns_none(self, tmp_path, caplog):
        """Test _reload_tool when load_tool_from_file returns None."""
        import logging
        ToolRegistry._reset_instance()
        hot_reload = ToolHotReload()

        tool_path = tmp_path / "test_tool.py"
        tool_path.write_text("# Test")

        # Mock lifecycle to succeed
        hot_reload.lifecycle.shutdown_tool = MagicMock(return_value=True)
        
        # Mock loader to return None
        hot_reload.loader.load_tool_from_file = MagicMock(return_value=None)

        with caplog.at_level(logging.ERROR):
            hot_reload._reload_tool("TestTool", tool_path)

        # Should log error about failed load
        assert any("Failed to load tool class" in record.message for record in caplog.records)
