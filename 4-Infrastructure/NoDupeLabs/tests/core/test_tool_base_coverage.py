# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Coverage tests for nodupe/core/tool_system/base.py."""

from typing import Any, Callable, Dict, List

import pytest

from nodupe.core.tool_system.base import AccessibleTool, Tool, ToolMetadata


class ConcreteAccessibleTool(AccessibleTool):
    """Concrete implementation of AccessibleTool for testing."""

    @property
    def name(self) -> str:
        """Return the tool name."""
        return "TestTool"

    @property
    def version(self) -> str:
        """Return the tool version."""
        return "1.0.0"

    @property
    def dependencies(self) -> List[str]:
        """Return list of tool dependencies."""
        return []

    def initialize(self, container: Any) -> None:
        """Initialize the tool with a dependency container."""
        pass

    def shutdown(self) -> None:
        """Shutdown the tool and release resources."""
        pass

    def get_capabilities(self) -> Dict[str, Any]:
        """Return the tool's capabilities dictionary."""
        return {}

    @property
    def api_methods(self) -> Dict[str, Callable[..., Any]]:
        """Return the tool's API methods dictionary."""
        return {}

    def run_standalone(self, args: List[str]) -> int:
        """Run the tool as a standalone CLI application."""
        return 0

    def describe_usage(self) -> str:
        """Return a description of tool usage."""
        return ""


def test_accessible_tool_methods():
    """Call the base methods in AccessibleTool to get 100% coverage."""
    tool = ConcreteAccessibleTool()
    
    # Call each method that has a 'pass' in the base class
    tool.announce_to_assistive_tech("hello")
    tool.format_for_accessibility({"data": 1})
    tool.get_ipc_socket_documentation()
    tool.get_accessible_status()
    tool.log_accessible_message("test")


def test_tool_metadata_frozen():
    """Test ToolMetadata dataclass."""
    meta = ToolMetadata(
        name="test",
        version="1.0",
        software_id="id",
        description="desc",
        author="auth",
        license="MIT",
        dependencies=[],
        tags=[]
    )
    assert meta.name == "test"
    
    with pytest.raises(Exception): # frozen=True
        meta.name = "new"
