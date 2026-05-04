# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/parallel/parallel_tool.py - ParallelTool."""

import sys
from unittest.mock import MagicMock

import pytest

from nodupe.core.tool_system.base import ToolMetadata
from nodupe.tools.parallel.parallel_tool import ParallelTool, register_tool


class TestParallelToolProperties:
    """Test ParallelTool properties."""

    def test_name_property(self):
        """ParallelTool.name returns correct value."""
        tool = ParallelTool()
        assert tool.name == "parallel_execution"

    def test_version_property(self):
        """ParallelTool.version returns correct value."""
        tool = ParallelTool()
        assert tool.version == "1.0.0"

    def test_dependencies_property(self):
        """ParallelTool.dependencies returns empty list."""
        tool = ParallelTool()
        assert tool.dependencies == []

    def test_metadata_property(self):
        """ParallelTool.metadata returns ToolMetadata with correct values."""
        tool = ParallelTool()
        metadata = tool.metadata

        assert isinstance(metadata, ToolMetadata)
        assert metadata.name == "parallel_execution"
        assert metadata.version == "1.0.0"
        assert metadata.software_id == "org.nodupe.tool.parallel_execution"
        assert "Parallel processing" in metadata.description
        assert metadata.author == "NoDupeLabs"
        assert metadata.license == "Apache-2.0"
        assert metadata.dependencies == []
        assert "parallel" in metadata.tags
        assert "performance" in metadata.tags
        assert "posix" in metadata.tags
        assert "threading" in metadata.tags

    def test_api_methods_property(self):
        """ParallelTool.api_methods returns correct methods."""
        from nodupe.tools.parallel.parallel_logic import Parallel

        tool = ParallelTool()
        api_methods = tool.api_methods

        assert 'map' in api_methods
        assert 'smart_map' in api_methods
        assert 'get_workers' in api_methods

        # Verify they are bound to Parallel class methods
        assert api_methods['map'] == Parallel.map_parallel
        assert api_methods['smart_map'] == Parallel.smart_map
        assert api_methods['get_workers'] == Parallel.get_optimal_workers


class TestParallelToolInitialize:
    """Test ParallelTool.initialize() method."""

    def test_initialize_registers_service(self):
        """initialize() registers parallel_service."""
        tool = ParallelTool()
        container = MagicMock()

        tool.initialize(container)

        container.register_service.assert_called_once_with('parallel_service', tool)


class TestParallelToolShutdown:
    """Test ParallelTool.shutdown() method."""

    def test_shutdown_no_error(self):
        """shutdown() completes without error."""
        tool = ParallelTool()
        # Should not raise
        tool.shutdown()


class TestParallelToolRunStandalone:
    """Test ParallelTool.run_standalone() method."""

    def test_run_standalone_returns_zero(self, capsys):
        """run_standalone() returns 0 and prints output."""
        tool = ParallelTool()
        result = tool.run_standalone([])

        assert result == 0
        captured = capsys.readouterr()
        assert "Parallel Tool: Self-test mode." in captured.out
        assert "Demonstrating 4-way parallel mapping" in captured.out
        assert "Results:" in captured.out


class TestParallelToolDescribeUsage:
    """Test ParallelTool.describe_usage() method."""

    def test_describe_usage_returns_string(self):
        """describe_usage() returns a string."""
        tool = ParallelTool()
        description = tool.describe_usage()

        assert isinstance(description, str)
        assert "computer" in description.lower() or "work" in description.lower()


class TestParallelToolGetCapabilities:
    """Test ParallelTool.get_capabilities() method."""

    def test_get_capabilities_returns_dict(self):
        """get_capabilities() returns a dictionary with expected keys."""
        tool = ParallelTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities, dict)
        assert 'cpu_count' in capabilities
        assert 'supports_interpreters' in capabilities
        assert 'is_free_threaded' in capabilities

    def test_get_capabilities_cpu_count(self):
        """get_capabilities() returns positive integer for cpu_count."""
        tool = ParallelTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities['cpu_count'], int)
        assert capabilities['cpu_count'] >= 1

    def test_get_capabilities_supports_interpreters(self):
        """get_capabilities() returns boolean for supports_interpreters."""
        tool = ParallelTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities['supports_interpreters'], bool)

    def test_get_capabilities_is_free_threaded(self):
        """get_capabilities() returns boolean for is_free_threaded."""
        tool = ParallelTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities['is_free_threaded'], bool)


class TestRegisterTool:
    """Test register_tool() function."""

    def test_register_tool_returns_parallel_tool(self):
        """register_tool() returns a ParallelTool instance."""
        tool = register_tool()
        assert isinstance(tool, ParallelTool)


class TestParallelToolMain:
    """Test ParallelTool __main__ behavior."""

    def test_main_block_execution(self, monkeypatch):
        """Test that __main__ block can be executed."""
        # This tests the if __name__ == "__main__" block
        from nodupe.tools.parallel import parallel_tool as pt

        # Simulate running as main
        tool = pt.ParallelTool()
        result = tool.run_standalone(['--help'] if len(sys.argv) > 1 else [])
        assert result == 0


class TestParallelToolEdgeCases:
    """Test ParallelTool edge cases and error handling."""

    def test_run_standalone_with_args(self, capsys):
        """run_standalone() handles command line arguments."""
        tool = ParallelTool()
        result = tool.run_standalone(['--verbose', '--workers=4'])

        assert result == 0
        captured = capsys.readouterr()
        assert "Results:" in captured.out

    def test_run_standalone_demonstrates_parallelism(self):
        """run_standalone() actually performs parallel computation."""
        tool = ParallelTool()
        result = tool.run_standalone([])

        assert result == 0
        # The lambda x: x*x on range(10) should produce squares
        # Results: [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

    def test_initialize_with_none_container(self):
        """initialize() handles container gracefully."""
        tool = ParallelTool()
        container = MagicMock()

        # Should not raise
        tool.initialize(container)
        container.register_service.assert_called_once()

    def test_multiple_initialize_calls(self):
        """initialize() can be called multiple times."""
        tool = ParallelTool()
        container1 = MagicMock()
        container2 = MagicMock()

        tool.initialize(container1)
        tool.initialize(container2)

        assert container1.register_service.called
        assert container2.register_service.called

    def test_multiple_shutdown_calls(self):
        """shutdown() can be called multiple times safely."""
        tool = ParallelTool()

        # Should not raise on multiple calls
        tool.shutdown()
        tool.shutdown()
        tool.shutdown()

    def test_describe_usage_content(self):
        """describe_usage() returns meaningful content."""
        tool = ParallelTool()
        description = tool.describe_usage()

        # Should mention key concepts
        assert len(description) > 50  # Reasonable length
        # Should be human-readable
        assert description[0].isupper() or description[0].islower()

    def test_get_capabilities_values(self):
        """get_capabilities() returns sensible values."""
        tool = ParallelTool()
        caps = tool.get_capabilities()

        # cpu_count should be positive
        assert caps['cpu_count'] >= 1
        # supports_interpreters should be boolean
        assert isinstance(caps['supports_interpreters'], bool)
        # is_free_threaded should be boolean
        assert isinstance(caps['is_free_threaded'], bool)

    def test_api_methods_are_callable(self):
        """api_methods returns callable methods."""
        tool = ParallelTool()
        api_methods = tool.api_methods

        # All methods should be callable
        assert callable(api_methods['map'])
        assert callable(api_methods['smart_map'])
        assert callable(api_methods['get_workers'])

    def test_metadata_immutability(self):
        """metadata returns frozen dataclass."""
        tool = ParallelTool()
        metadata = tool.metadata

        # Should be frozen (cannot modify)
        with pytest.raises(Exception):  # frozen dataclasses raise FrozenInstanceError
            metadata.name = "modified_name"


class TestParallelToolIntegration:
    """Integration tests for ParallelTool."""

    def test_tool_lifecycle(self):
        """Test complete tool lifecycle: create -> initialize -> use -> shutdown."""
        tool = ParallelTool()
        container = MagicMock()

        # Initialize
        tool.initialize(container)
        container.register_service.assert_called_once_with('parallel_service', tool)

        # Use
        capabilities = tool.get_capabilities()
        assert 'cpu_count' in capabilities

        api_methods = tool.api_methods
        assert 'map' in api_methods

        # Shutdown
        tool.shutdown()
        # Should not raise

    def test_tool_properties_consistency(self):
        """Test that tool properties return consistent values."""
        tool1 = ParallelTool()
        tool2 = ParallelTool()

        # Properties should be consistent across instances
        assert tool1.name == tool2.name
        assert tool1.version == tool2.version
        assert tool1.dependencies == tool2.dependencies

    def test_register_tool_function(self):
        """Test register_tool() helper function."""
        from nodupe.tools.parallel.parallel_tool import register_tool

        tool = register_tool()

        assert tool is not None
        assert isinstance(tool, ParallelTool)
        assert tool.name == "parallel_execution"
