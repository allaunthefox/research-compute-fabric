"""Test Tools Utilities.

Helper functions for tool-related testing.
"""

from typing import List, Optional
from unittest.mock import MagicMock


def create_mock_tool(name: str = "mock_tool", version: str = "1.0.0") -> MagicMock:
    """Create a mock tool for testing.

    Args:
        name: Tool name
        version: Tool version

    Returns:
        MagicMock configured as a tool
    """
    mock = MagicMock()
    mock.name = name
    mock.version = version
    mock.dependencies = []
    mock.api_methods = []
    mock.metadata = {"version": version}
    return mock


def create_test_tool_class(
    name: str = "test_tool",
    version: str = "1.0.0",
    dependencies: Optional[List[str]] = None,
    api_methods: Optional[List[str]] = None
):
    """Create a test tool class.

    Args:
        name: Tool name
        version: Tool version
        dependencies: List of dependencies
        api_methods: List of API methods

    Returns:
        Tool class for testing
    """
    from nodupe.core.tool_system.base import Tool

    class TestTool(Tool):
        """Test tool for testing purposes."""

        name = name
        version = version
        dependencies = dependencies or []
        api_methods = api_methods or []

        def execute(self, *args, **kwargs):
            """Execute the tool."""
            return {"status": "success"}

    return TestTool


def verify_tool_registration(registry, tool_name: str) -> bool:
    """Verify that a tool is registered in the registry.

    Args:
        registry: Tool registry instance
        tool_name: Name of the tool to verify

    Returns:
        True if tool is registered
    """
    tool = registry.get_tool(tool_name)
    return tool is not None


def get_registered_tool_names(registry) -> List[str]:
    """Get list of registered tool names.

    Args:
        registry: Tool registry instance

    Returns:
        List of tool names
    """
    return [tool.name for tool in registry.get_tools()]




def create_tool_directory_structure(base_path: "Path", tool_defs: list) -> list:
    """Create a directory structure for tools.
    
    Args:
        base_path: Base directory path
        tool_defs: List of tool definitions with 'name' and 'version'
    
    Returns:
        List of created tool paths
    """
    from pathlib import Path
    
    base = Path(base_path)
    tool_paths = []
    
    for tool_def in tool_defs:
        tool_name = tool_def.get("name", "unnamed")
        tool_dir = base / tool_name
        tool_dir.mkdir(parents=True, exist_ok=True)
        
        # Create tool file
        tool_file = tool_dir / f"{tool_name}.py"
        tool_file.write_text(f"# {tool_name} tool\n\nclass {tool_name.capitalize()}Tool:\n    pass\n")
        
        tool_paths.append(tool_dir)
    
    return tool_paths


def mock_tool_loader() -> "MagicMock":
    """Create a mock tool loader.
    
    Returns:
        MagicMock configured as a tool loader
    """
    from unittest.mock import MagicMock
    return MagicMock()


def create_tool_test_scenarios() -> list:
    """Create tool test scenarios.
    
    Returns:
        List of test scenarios
    """
    return [
        {"name": "basic", "tool": "test_tool"},
        {"name": "with_deps", "tool": "test_tool", "dependencies": ["dep1"]},
        {"name": "complex", "tool": "test_tool", "dependencies": ["dep1", "dep2"], "config": {}}
    ]


def create_tool_dependency_graph(tool_defs: list) -> dict:
    """Create a tool dependency graph.
    
    Args:
        tool_defs: List of tool definitions with dependencies
    
    Returns:
        Dictionary mapping tool names to their dependencies
    """
    graph = {}
    for tool_def in tool_defs:
        name = tool_def.get("name")
        deps = tool_def.get("dependencies", [])
        graph[name] = deps
    return graph


def test_tool_dependency_resolution(graph: dict, resolution_order: list) -> bool:
    """Test that a dependency resolution order is valid.
    
    Args:
        graph: Dependency graph
        resolution_order: Proposed resolution order
    
    Returns:
        True if order is valid
    """
    # Build a set of resolved tools
    resolved = set()
    
    for tool in resolution_order:
        deps = graph.get(tool, [])
        # All dependencies should be resolved before this tool
        for dep in deps:
            if dep not in resolved:
                return False
        resolved.add(tool)
    
    return True


def clear_registry(registry) -> None:
    """Clear all tools from registry.

    Args:
        registry: Tool registry instance
    """
    registry.clear()
