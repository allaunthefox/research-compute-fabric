# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/core/tools.py - ToolRegistry re-exports."""

from nodupe.core.tool_system.registry import ToolRegistry
from nodupe.core.tools import PluginManager, tool_manager


class TestPluginManagerAlias:
    """Test that PluginManager is correctly aliased to ToolRegistry."""

    def test_plugin_manager_is_tool_registry(self):
        """PluginManager should be the same class as ToolRegistry."""
        assert PluginManager is ToolRegistry

    def test_plugin_manager_can_be_instantiated(self):
        """PluginManager can be instantiated."""
        manager = PluginManager()
        assert isinstance(manager, ToolRegistry)


class TestToolManager:
    """Test the tool_manager instance."""

    def test_tool_manager_is_tool_registry_instance(self):
        """tool_manager should be a ToolRegistry instance."""
        assert isinstance(tool_manager, ToolRegistry)

    def test_tool_manager_is_singleton(self):
        """tool_manager should be the same instance on repeated imports."""
        from nodupe.core import tools
        assert tools.tool_manager is tool_manager
