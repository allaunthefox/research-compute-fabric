"""Extra tests for remaining coverage gaps."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from nodupe.core.tool_system.hot_reload import ToolHotReload
from nodupe.core.tool_system.registry import ToolRegistry


class TestRemainingCoverageExtra:
    """Test remaining coverage gaps."""

    def test_poll_loop_stop_event_mid_iteration_break(self, tmp_path):
        """Test _poll_loop breaks when stop event is set mid-iteration."""
        hot_reload = ToolHotReload(poll_interval=0.01)

        tool_path = tmp_path / "test_tool.py"
        tool_path.write_text("# Test")
        hot_reload.watch_tool("TestTool", tool_path)

        # Mock _reload_tool to track if it's called
        hot_reload._reload_tool = MagicMock()

        # Set stop event during iteration by mocking stat
        call_count = [0]
        def stat_and_stop():
            """Mock stat to set stop event on first call.

            Returns:
                MockStat object with st_mtime attribute.
            """
            call_count[0] += 1
            if call_count[0] == 1:
                # First call - set stop event to break mid-iteration
                hot_reload._stop_event.set()
            # Return a mock stat result
            class MockStat:
                """Mock stat result for testing."""
                st_mtime = 0
            return MockStat()

        with patch.object(Path, 'stat', side_effect=stat_and_stop):
            # Run poll loop - should break mid-iteration
            hot_reload._poll_loop()

        # _reload_tool should NOT be called since we broke before checking mtime
        hot_reload._reload_tool.assert_not_called()

    def test_reload_tool_shutdown_success_false_warning(self, tmp_path, caplog):
        """Test _reload_tool logs warning when shutdown_tool returns False."""
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

        # Should log warning about tool not running or failed to shutdown
        assert any("not running" in record.message.lower() or "failed to shutdown" in record.message.lower() for record in caplog.records)
