# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""NoDupeLabs Core Plugins Module.

This module provides tool management functionality for the core system.
It serves as a compatibility layer and re-exports the tool system components.
"""

from .tool_system.registry import ToolRegistry

# Create tool manager instance
tool_manager = ToolRegistry()
PluginManager = ToolRegistry
PluginRegistry = ToolRegistry  # Alias for compatibility
ToolManager = ToolRegistry  # Alias for compatibility

__all__ = [
    'PluginManager',
    'PluginRegistry',
    'ToolManager',
    'tool_manager'
]
