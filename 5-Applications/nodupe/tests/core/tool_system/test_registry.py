"""Tests for the tool_system registry module."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from nodupe.core.tool_system.registry import PluginRegistry, ToolRegistry


class ConcreteTool:
    """Mock concrete tool for testing."""

    def __init__(self, name: str = "TestTool", version: str = "1.0.0"):
        """Initialize the concrete tool with name and version.

        Args:
            name: The name of the tool.
            version: The version string of the tool.
        """
        self._name = name
        self._version = version
        self._initialized = False
        self._shutdown_called = False

    @property
    def name(self) -> str:
        """Get the name of the tool.

        Returns:
            The tool name.
        """
        return self._name

    @property
    def version(self) -> str:
        """Get the version of the tool.

        Returns:
            The tool version.
        """
        return self._version

    @property
    def dependencies(self) -> list[str]:
        """Get the list of tool dependencies.

        Returns:
            List of dependency names.
        """
        return []

    def initialize(self, container) -> None:
        """Initialize the tool with a container.

        Args:
            container: The container to initialize with.
        """
        self._initialized = True

    def shutdown(self) -> None:
        """Shutdown the tool and release resources."""
        self._shutdown_called = True

    def get_capabilities(self) -> dict:
        """Get the tool's capabilities.

        Returns:
            Dictionary of capabilities.
        """
        return {"test": "capability"}

    @property
    def api_methods(self) -> dict:
        """Get the tool's API methods.

        Returns:
            Dictionary of API methods.
        """
        return {}

    def run_standalone(self, args: list[str]) -> int:
        """Run the tool as a standalone application.

        Args:
            args: Command-line arguments.

        Returns:
            Exit code.
        """
        return 0

    def describe_usage(self) -> str:
        """Get a description of tool usage.

        Returns:
            Usage description string.
        """
        return "Test tool usage"


@pytest.fixture(scope="function")
def reset_registry():
    """Reset ToolRegistry singleton for test isolation."""
    try:
        yield
    finally:
        ToolRegistry._reset_instance()


class TestToolRegistryInitialization:
    """Test ToolRegistry initialization."""

    def test_tool_registry_singleton(self, reset_registry):
        """Test ToolRegistry singleton pattern."""
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()

        assert registry1 is registry2
        assert id(registry1) == id(registry2)

    def test_tool_registry_initial_state(self, reset_registry):
        """Test ToolRegistry initial state."""
        registry = ToolRegistry()

        assert registry._tools == {}
        assert registry._initialized is False
        assert registry.container is None

    def test_tool_registry_initialize(self, reset_registry):
        """Test ToolRegistry initialization with container."""
        registry = ToolRegistry()
        container = Mock()

        registry.initialize(container)

        assert registry._container is container
        assert registry._initialized is True

    def test_tool_registry_initialize_multiple_times(self, reset_registry):
        """Test ToolRegistry can be initialized multiple times."""
        registry = ToolRegistry()
        container1 = Mock()
        container2 = Mock()

        registry.initialize(container1)
        registry.initialize(container2)

        assert registry._container is container2


class TestToolRegistryRegistration:
    """Test tool registration functionality."""

    def test_register_tool_success(self, reset_registry):
        """Test successful tool registration."""
        registry = ToolRegistry()

        tool = ConcreteTool(name="TestTool")
        registry.register(tool)

        assert "TestTool" in registry._tools
        assert registry._tools["TestTool"] is tool

    def test_register_tool_with_container(self, reset_registry):
        """Test tool registration with container initializes tool."""
        registry = ToolRegistry()
        container = Mock()
        registry.initialize(container)

        tool = ConcreteTool(name="TestTool")
        registry.register(tool)

        assert tool._initialized is True

    def test_register_tool_without_container(self, reset_registry):
        """Test tool registration without container doesn't initialize."""
        registry = ToolRegistry()

        tool = ConcreteTool(name="TestTool")
        registry.register(tool)

        # Tool should not be initialized without container
        assert tool._initialized is False

    def test_register_duplicate_tool(self, reset_registry):
        """Test registering a duplicate tool raises error."""
        registry = ToolRegistry()

        tool1 = ConcreteTool(name="TestTool")
        tool2 = ConcreteTool(name="TestTool")

        registry.register(tool1)

        with pytest.raises(ValueError) as exc_info:
            registry.register(tool2)

        assert "already registered" in str(exc_info.value)

    def test_register_multiple_tools(self, reset_registry):
        """Test registering multiple tools."""
        registry = ToolRegistry()

        tool1 = ConcreteTool(name="Tool1")
        tool2 = ConcreteTool(name="Tool2")
        tool3 = ConcreteTool(name="Tool3")

        registry.register(tool1)
        registry.register(tool2)
        registry.register(tool3)

        assert len(registry._tools) == 3
        assert "Tool1" in registry._tools
        assert "Tool2" in registry._tools
        assert "Tool3" in registry._tools


class TestToolRegistryUnregistration:
    """Test tool unregistration functionality."""

    def test_unregister_tool(self, reset_registry):
        """Test tool unregistration."""
        registry = ToolRegistry()

        tool = ConcreteTool(name="TestTool")
        registry.register(tool)

        registry.unregister("TestTool")

        assert "TestTool" not in registry._tools
        assert tool._shutdown_called is True

    def test_unregister_nonexistent_tool(self, reset_registry):
        """Test unregistering a nonexistent tool raises error."""
        registry = ToolRegistry()

        with pytest.raises(KeyError) as exc_info:
            registry.unregister("NonExistentTool")

        assert "not found" in str(exc_info.value)

    def test_unregister_tool_not_initialized(self, reset_registry):
        """Test unregistering a tool that wasn't initialized."""
        registry = ToolRegistry()

        tool = ConcreteTool(name="TestTool")
        registry.register(tool)
        # Don't initialize

        registry.unregister("TestTool")

        assert "TestTool" not in registry._tools


class TestToolRegistryRetrieval:
    """Test tool retrieval functionality."""

    def test_get_tool_exists(self, reset_registry):
        """Test getting an existing tool."""
        registry = ToolRegistry()

        tool = ConcreteTool(name="TestTool")
        registry.register(tool)

        result = registry.get_tool("TestTool")
        assert result is tool

    def test_get_tool_not_exists(self, reset_registry):
        """Test getting a nonexistent tool."""
        registry = ToolRegistry()

        result = registry.get_tool("NonExistentTool")
        assert result is None

    def test_get_tools_empty(self, reset_registry):
        """Test getting all tools when empty."""
        registry = ToolRegistry()

        result = registry.get_tools()
        assert result == []

    def test_get_tools_multiple(self, reset_registry):
        """Test getting all tools."""
        registry = ToolRegistry()

        tool1 = ConcreteTool(name="Tool1")
        tool2 = ConcreteTool(name="Tool2")

        registry.register(tool1)
        registry.register(tool2)

        result = registry.get_tools()

        assert len(result) == 2
        assert tool1 in result
        assert tool2 in result

    def test_get_tools_returns_copy(self, reset_registry):
        """Test get_tools returns a copy, not the original."""
        registry = ToolRegistry()

        tool = ConcreteTool(name="TestTool")
        registry.register(tool)

        result = registry.get_tools()

        # Modifying result should not affect registry
        result.clear()

        assert len(registry._tools) == 1


class TestToolRegistryClear:
    """Test registry clear functionality."""

    def test_clear_all_tools(self, reset_registry):
        """Test clearing all tools."""
        registry = ToolRegistry()

        tool1 = ConcreteTool(name="Tool1")
        tool2 = ConcreteTool(name="Tool2")

        registry.register(tool1)
        registry.register(tool2)

        registry.clear()

        assert len(registry._tools) == 0

    def test_clear_empty_registry(self, reset_registry):
        """Test clearing an empty registry."""
        registry = ToolRegistry()

        # Should not raise
        registry.clear()

        assert len(registry._tools) == 0


class TestToolRegistryShutdown:
    """Test registry shutdown functionality."""

    def test_shutdown_all_tools(self, reset_registry):
        """Test shutting down all tools."""
        registry = ToolRegistry()

        tool1 = ConcreteTool(name="Tool1")
        tool2 = ConcreteTool(name="Tool2")

        registry.register(tool1)
        registry.register(tool2)

        registry.shutdown()

        assert tool1._shutdown_called is True
        assert tool2._shutdown_called is True
        assert len(registry._tools) == 0

    def test_shutdown_clears_container(self, reset_registry):
        """Test shutdown clears container."""
        registry = ToolRegistry()
        container = Mock()
        registry.initialize(container)

        registry.shutdown()

        assert registry._container is None

    def test_shutdown_resets_initialized(self, reset_registry):
        """Test shutdown resets initialized flag."""
        registry = ToolRegistry()
        container = Mock()
        registry.initialize(container)

        registry.shutdown()

        assert registry._initialized is False

    def test_shutdown_handles_tool_exception(self, reset_registry, caplog):
        """Test shutdown handles tool exception gracefully."""
        registry = ToolRegistry()

        tool = Mock()
        tool.name = "FailingTool"
        tool.shutdown = Mock(side_effect=Exception("Shutdown failed"))

        registry._tools["FailingTool"] = tool

        # Should not raise
        registry.shutdown()

        tool.shutdown.assert_called_once()

    def test_shutdown_empty_registry(self, reset_registry):
        """Test shutting down an empty registry."""
        registry = ToolRegistry()

        # Should not raise
        registry.shutdown()


class TestToolRegistryContainer:
    """Test registry container functionality."""

    def test_container_property_get(self, reset_registry):
        """Test container property getter."""
        registry = ToolRegistry()
        container = Mock()
        registry._container = container

        assert registry.container is container

    def test_container_property_set(self, reset_registry):
        """Test container property setter."""
        registry = ToolRegistry()
        container = Mock()

        registry.container = container

        assert registry._container is container

    def test_container_property_default(self, reset_registry):
        """Test container property default value."""
        registry = ToolRegistry()

        assert registry.container is None


class TestToolRegistryReset:
    """Test registry reset functionality."""

    def test_reset_instance(self, reset_registry):
        """Test resetting the singleton instance."""
        registry1 = ToolRegistry()

        tool = ConcreteTool(name="TestTool")
        registry1.register(tool)

        assert len(registry1._tools) == 1

        # Reset the instance
        ToolRegistry._reset_instance()

        # Create a new instance
        registry2 = ToolRegistry()

        # Should be a fresh instance
        assert registry1 is not registry2
        assert len(registry2._tools) == 0

    def test_reset_instance_multiple_times(self, reset_registry):
        """Test resetting the instance multiple times."""
        ToolRegistry._reset_instance()
        ToolRegistry._reset_instance()
        ToolRegistry._reset_instance()

        registry = ToolRegistry()
        assert registry is not None


class TestPluginRegistryAlias:
    """Test PluginRegistry backward compatibility alias."""

    def test_plugin_registry_is_tool_registry(self, reset_registry):
        """Test PluginRegistry is the same as ToolRegistry."""
        assert PluginRegistry is ToolRegistry

    def test_plugin_registry_singleton(self, reset_registry):
        """Test PluginRegistry singleton pattern."""
        registry1 = PluginRegistry()
        registry2 = PluginRegistry()

        assert registry1 is registry2

    def test_plugin_registry_functionality(self, reset_registry):
        """Test PluginRegistry has same functionality as ToolRegistry."""
        registry = PluginRegistry()

        tool = ConcreteTool(name="TestTool")
        registry.register(tool)

        assert registry.get_tool("TestTool") is tool


class TestToolRegistryEdgeCases:
    """Test edge cases for ToolRegistry."""

    def test_register_tool_with_special_name(self, reset_registry):
        """Test registering tool with special characters in name."""
        registry = ToolRegistry()

        tool = ConcreteTool(name="Tool-With_Special.Chars")
        registry.register(tool)

        assert registry.get_tool("Tool-With_Special.Chars") is tool

    def test_register_tool_with_empty_name(self, reset_registry):
        """Test registering tool with empty name."""
        registry = ToolRegistry()

        tool = ConcreteTool(name="")
        registry.register(tool)

        assert registry.get_tool("") is tool

    def test_register_tool_with_unicode_name(self, reset_registry):
        """Test registering tool with unicode name."""
        registry = ToolRegistry()

        tool = ConcreteTool(name="\u0422\u0435\u0441\u0442\u043e\u0432\u044b\u0439\u0418\u043d\u0441\u0442\u0440\u0443\u043c\u0435\u043d\u0442")
        registry.register(tool)

        assert registry.get_tool("\u0422\u0435\u0441\u0442\u043e\u0432\u044b\u0439\u0418\u043d\u0441\u0442\u0440\u0443\u043c\u0435\u043d\u0442") is tool

    def test_get_tool_case_sensitive(self, reset_registry):
        """Test tool name lookup is case sensitive."""
        registry = ToolRegistry()

        tool = ConcreteTool(name="TestTool")
        registry.register(tool)

        assert registry.get_tool("TestTool") is tool
        assert registry.get_tool("testtool") is None
        assert registry.get_tool("TESTTOOL") is None

    def test_register_tool_none(self, reset_registry):
        """Test registering None as tool."""
        registry = ToolRegistry()

        with pytest.raises(AttributeError):
            registry.register(None)  # type: ignore

    def test_unregister_tool_twice(self, reset_registry):
        """Test unregistering a tool twice."""
        registry = ToolRegistry()

        tool = ConcreteTool(name="TestTool")
        registry.register(tool)

        registry.unregister("TestTool")

        with pytest.raises(KeyError):
            registry.unregister("TestTool")

    def test_register_after_shutdown(self, reset_registry):
        """Test registering tools after shutdown."""
        registry = ToolRegistry()

        tool1 = ConcreteTool(name="Tool1")
        registry.register(tool1)

        registry.shutdown()

        tool2 = ConcreteTool(name="Tool2")
        registry.register(tool2)

        assert registry.get_tool("Tool2") is tool2

    def test_initialize_after_shutdown(self, reset_registry):
        """Test initializing after shutdown."""
        registry = ToolRegistry()

        container1 = Mock()
        registry.initialize(container1)
        registry.shutdown()

        container2 = Mock()
        registry.initialize(container2)

        assert registry._container is container2
        assert registry._initialized is True

    def test_register_many_tools(self, reset_registry):
        """Test registering many tools."""
        registry = ToolRegistry()

        for i in range(100):
            tool = ConcreteTool(name=f"Tool{i}")
            registry.register(tool)

        assert len(registry._tools) == 100

    def test_shutdown_many_tools(self, reset_registry):
        """Test shutting down many tools."""
        registry = ToolRegistry()

        tools = []
        for i in range(100):
            tool = ConcreteTool(name=f"Tool{i}")
            registry.register(tool)
            tools.append(tool)

        registry.shutdown()

        for tool in tools:
            assert tool._shutdown_called is True

        assert len(registry._tools) == 0
