# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Comprehensive tests for nodupe.core.tools module.

This module provides thorough tests to increase coverage for the tools
re-export module, testing all code paths.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestToolsModule:
    """Test the tools module exports and functionality."""

    def test_tools_module_imports(self):
        """Test that the tools module can be imported."""
        from nodupe.core import tools
        assert tools is not None

    def test_plugin_manager_export(self):
        """Test PluginManager is exported."""
        from nodupe.core.tools import PluginManager
        assert PluginManager is not None

    def test_tool_manager_export(self):
        """Test ToolManager is exported."""
        from nodupe.core.tools import ToolManager
        assert ToolManager is not None

    def test_tool_manager_instance(self):
        """Test tool_manager instance is created."""
        from nodupe.core.tools import tool_manager
        assert tool_manager is not None

    def test_all_exports(self):
        """Test __all__ contains expected items."""
        from nodupe.core.tools import __all__
        assert 'PluginManager' in __all__
        assert 'ToolManager' in __all__
        assert 'tool_manager' in __all__

    def test_plugin_manager_is_tool_registry(self):
        """Test that PluginManager is ToolRegistry."""
        from nodupe.core.tool_system.registry import ToolRegistry
        from nodupe.core.tools import PluginManager
        assert PluginManager is ToolRegistry

    def test_tool_manager_is_tool_registry(self):
        """Test that ToolManager is ToolRegistry."""
        from nodupe.core.tool_system.registry import ToolRegistry
        from nodupe.core.tools import ToolManager
        assert ToolManager is ToolRegistry


class TestToolRegistryViaTools:
    """Test ToolRegistry functionality through tools module."""

    def test_tool_registry_singleton(self):
        """Test that tool_manager is a singleton."""
        # Create new instance via PluginManager
        from nodupe.core.tools import PluginManager, tool_manager

        # Should be the same instance
        assert PluginManager() is tool_manager

    def test_tool_registry_register(self):
        """Test registering a tool via tool_manager."""
        from nodupe.core.tools import tool_manager

        # Reset for test isolation
        tool_manager.clear()

        mock_tool = MagicMock()
        mock_tool.name = "test_tool"

        tool_manager.register(mock_tool)
        assert tool_manager.get_tool("test_tool") is mock_tool

        # Cleanup
        tool_manager.clear()

    def test_tool_registry_get_tools(self):
        """Test getting all tools."""
        from nodupe.core.tools import tool_manager

        # Reset for test isolation
        tool_manager.clear()

        mock_tool1 = MagicMock()
        mock_tool1.name = "tool1"
        mock_tool2 = MagicMock()
        mock_tool2.name = "tool2"

        tool_manager.register(mock_tool1)
        tool_manager.register(mock_tool2)

        tools = tool_manager.get_tools()
        assert len(tools) == 2
        assert mock_tool1 in tools
        assert mock_tool2 in tools

        # Cleanup
        tool_manager.clear()

    def test_tool_registry_unregister(self):
        """Test unregistering a tool."""
        from nodupe.core.tools import tool_manager

        # Reset for test isolation
        tool_manager.clear()

        mock_tool = MagicMock()
        mock_tool.name = "test_tool"

        tool_manager.register(mock_tool)
        assert tool_manager.get_tool("test_tool") is not None

        tool_manager.unregister("test_tool")
        assert tool_manager.get_tool("test_tool") is None

    def test_tool_registry_unregister_not_found(self):
        """Test unregistering non-existent tool."""
        from nodupe.core.tools import tool_manager

        # Reset for test isolation
        tool_manager.clear()

        with pytest.raises(KeyError):
            tool_manager.unregister("nonexistent")

    def test_tool_registry_register_duplicate(self):
        """Test registering duplicate tool."""
        from nodupe.core.tools import tool_manager

        # Reset for test isolation
        tool_manager.clear()

        mock_tool = MagicMock()
        mock_tool.name = "duplicate_tool"

        tool_manager.register(mock_tool)

        with pytest.raises(ValueError, match="already registered"):
            tool_manager.register(mock_tool)

        # Cleanup
        tool_manager.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
