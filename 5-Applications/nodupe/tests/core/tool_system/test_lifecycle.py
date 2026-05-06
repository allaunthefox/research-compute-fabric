"""Tests for the tool_system lifecycle module."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from nodupe.core.tool_system.base import AccessibleTool, Tool
from nodupe.core.tool_system.lifecycle import (
    ToolLifecycleError,
    ToolLifecycleManager,
    ToolState,
    create_lifecycle_manager,
)
from nodupe.core.tool_system.registry import ToolRegistry


class ConcreteTool(Tool):
    """Concrete tool implementation for testing."""

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
        return {}

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
        return "Usage"


class ConcreteAccessibleTool(AccessibleTool):
    """Concrete accessible tool for testing."""

    def __init__(self, name: str = "AccessibleTool", version: str = "1.0.0"):
        """Initialize the accessible tool with name and version.

        Args:
            name: The name of the tool.
            version: The version string of the tool.
        """
        self._name = name
        self._version = version

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
        pass

    def shutdown(self) -> None:
        """Shutdown the tool and release resources."""
        pass

    def get_capabilities(self) -> dict:
        """Get the tool's capabilities.

        Returns:
            Dictionary of capabilities.
        """
        return {}

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
        return "Usage"


class TestToolState:
    """Test ToolState enum."""

    def test_tool_state_values(self):
        """Test ToolState enum values."""
        assert ToolState.UNLOADED.value == "unloaded"
        assert ToolState.LOADED.value == "loaded"
        assert ToolState.INITIALIZING.value == "initializing"
        assert ToolState.INITIALIZED.value == "initialized"
        assert ToolState.SHUTTING_DOWN.value == "shutting_down"
        assert ToolState.SHUTDOWN.value == "shutdown"
        assert ToolState.ERROR.value == "error"


class TestToolLifecycleManagerInitialization:
    """Test ToolLifecycleManager initialization."""

    def test_lifecycle_manager_creation(self):
        """Test ToolLifecycleManager instance creation."""
        manager = ToolLifecycleManager()

        assert manager is not None
        assert manager._tool_states == {}
        assert manager._tool_dependencies == {}
        assert manager._tool_containers == {}
        assert manager.container is None

    def test_lifecycle_manager_with_registry(self):
        """Test ToolLifecycleManager with custom registry."""
        mock_registry = Mock()
        manager = ToolLifecycleManager(mock_registry)

        assert manager.registry is mock_registry

    def test_lifecycle_manager_default_registry(self):
        """Test ToolLifecycleManager creates default registry."""
        manager = ToolLifecycleManager()

        assert isinstance(manager.registry, ToolRegistry)

    def test_lifecycle_manager_initialize(self):
        """Test ToolLifecycleManager initialization with container."""
        manager = ToolLifecycleManager()
        container = Mock()

        manager.initialize(container)

        assert manager.container is container


class TestToolLifecycleInitialization:
    """Test tool initialization."""

    def test_initialize_tool_success(self):
        """Test successful tool initialization."""
        manager = ToolLifecycleManager()
        container = Mock()

        tool = ConcreteTool(name="TestTool")

        result = manager.initialize_tool(tool, container)

        assert result is True
        assert tool._initialized is True
        assert manager.get_tool_state("TestTool") == ToolState.INITIALIZED

    def test_initialize_tool_already_initialized(self):
        """Test initializing already initialized tool."""
        manager = ToolLifecycleManager()
        container = Mock()

        tool = ConcreteTool(name="TestTool")
        manager._tool_states["TestTool"] = ToolState.INITIALIZED

        result = manager.initialize_tool(tool, container)

        assert result is True
        assert tool._initialized is False  # initialize not called again

    def test_initialize_tool_with_dependencies_satisfied(self):
        """Test tool initialization with satisfied dependencies."""
        manager = ToolLifecycleManager()
        container = Mock()

        tool = ConcreteTool(name="TestTool")
        manager._tool_states["DependencyTool"] = ToolState.INITIALIZED

        result = manager.initialize_tool(tool, container, dependencies=["DependencyTool"])

        assert result is True
        assert tool._initialized is True

    def test_initialize_tool_with_dependencies_not_satisfied(self):
        """Test tool initialization with unsatisfied dependencies."""
        manager = ToolLifecycleManager()
        container = Mock()

        tool = ConcreteTool(name="TestTool")

        with pytest.raises(ToolLifecycleError) as exc_info:
            manager.initialize_tool(tool, container, dependencies=["MissingDep"])

        assert "Dependencies not satisfied" in str(exc_info.value)
        assert tool._initialized is False

    def test_initialize_tool_failure(self):
        """Test tool initialization failure."""
        manager = ToolLifecycleManager()
        container = Mock()

        tool = Mock(spec=Tool)
        tool.name = "FailingTool"
        tool.initialize = Mock(side_effect=Exception("Init failed"))

        with pytest.raises(ToolLifecycleError) as exc_info:
            manager.initialize_tool(tool, container)

        assert "Failed to initialize tool" in str(exc_info.value)
        assert manager.get_tool_state("FailingTool") == ToolState.ERROR

    def test_initialize_multiple_tools(self):
        """Test initializing multiple tools."""
        manager = ToolLifecycleManager()
        container = Mock()

        tool1 = ConcreteTool(name="Tool1")
        tool2 = ConcreteTool(name="Tool2")

        manager.initialize_tools([tool1, tool2])

        assert tool1._initialized is True
        assert tool2._initialized is True


class TestToolLifecycleShutdown:
    """Test tool shutdown."""

    def test_shutdown_tool_success(self):
        """Test successful tool shutdown."""
        manager = ToolLifecycleManager()

        tool = ConcreteTool(name="TestTool")

        mock_registry = Mock()
        mock_registry.get_tool.return_value = tool
        manager.registry = mock_registry

        manager._tool_states["TestTool"] = ToolState.INITIALIZED

        result = manager.shutdown_tool("TestTool")

        assert result is True
        assert tool._shutdown_called is True
        assert manager.get_tool_state("TestTool") == ToolState.SHUTDOWN

    def test_shutdown_tool_not_found(self):
        """Test shutting down nonexistent tool."""
        manager = ToolLifecycleManager()

        mock_registry = Mock()
        mock_registry.get_tool.return_value = None
        manager.registry = mock_registry

        result = manager.shutdown_tool("NonExistentTool")

        assert result is False

    def test_shutdown_tool_already_shutdown(self):
        """Test shutting down already shutdown tool."""
        manager = ToolLifecycleManager()

        tool = ConcreteTool(name="TestTool")

        mock_registry = Mock()
        mock_registry.get_tool.return_value = tool
        manager.registry = mock_registry

        manager._tool_states["TestTool"] = ToolState.SHUTDOWN

        result = manager.shutdown_tool("TestTool")

        assert result is True
        assert tool._shutdown_called is False

    def test_shutdown_tool_unloaded_state(self):
        """Test shutting down tool in UNLOADED state."""
        manager = ToolLifecycleManager()

        tool = ConcreteTool(name="TestTool")

        mock_registry = Mock()
        mock_registry.get_tool.return_value = tool
        manager.registry = mock_registry

        manager._tool_states["TestTool"] = ToolState.UNLOADED

        result = manager.shutdown_tool("TestTool")

        assert result is True
        assert tool._shutdown_called is False

    def test_shutdown_tool_with_error(self):
        """Test tool shutdown with error."""
        manager = ToolLifecycleManager()

        tool = Mock(spec=Tool)
        tool.name = "FailingTool"
        tool.shutdown = Mock(side_effect=Exception("Shutdown failed"))

        mock_registry = Mock()
        mock_registry.get_tool.return_value = tool
        manager.registry = mock_registry

        manager._tool_states["FailingTool"] = ToolState.INITIALIZED

        # Should not raise, just log warning
        result = manager.shutdown_tool("FailingTool")

        assert result is True
        tool.shutdown.assert_called_once()

    def test_shutdown_multiple_tools(self):
        """Test shutting down multiple tools."""
        manager = ToolLifecycleManager()

        tool1 = ConcreteTool(name="Tool1")
        tool2 = ConcreteTool(name="Tool2")

        mock_registry = Mock()
        mock_registry.get_tool.side_effect = lambda name: tool1 if name == "Tool1" else tool2
        manager.registry = mock_registry

        manager._tool_states["Tool1"] = ToolState.INITIALIZED
        manager._tool_states["Tool2"] = ToolState.INITIALIZED

        manager.shutdown_tools([tool1, tool2])

        assert tool1._shutdown_called is True
        assert tool2._shutdown_called is True


class TestToolLifecycleAllTools:
    """Test all tools lifecycle management."""

    def test_initialize_all_tools_success(self):
        """Test successful initialization of all tools."""
        manager = ToolLifecycleManager()
        container = Mock()

        tool1 = ConcreteTool(name="Tool1")
        tool2 = ConcreteTool(name="Tool2")

        mock_registry = Mock()
        mock_registry.get_tools.return_value = [tool1, tool2]
        manager.registry = mock_registry

        result = manager.initialize_all_tools(container)

        assert result is True
        assert tool1._initialized is True
        assert tool2._initialized is True

    def test_initialize_all_tools_failure(self):
        """Test initialization failure of one tool."""
        manager = ToolLifecycleManager()
        container = Mock()

        tool1 = ConcreteTool(name="Tool1")
        tool2 = Mock(spec=Tool)
        tool2.name = "FailingTool"
        tool2.initialize = Mock(side_effect=Exception("Init failed"))

        mock_registry = Mock()
        mock_registry.get_tools.return_value = [tool1, tool2]
        manager.registry = mock_registry

        with pytest.raises(ToolLifecycleError):
            manager.initialize_all_tools(container)

        assert tool1._initialized is True
        assert manager.get_tool_state("FailingTool") == ToolState.ERROR

    def test_shutdown_all_tools(self):
        """Test shutting down all tools."""
        manager = ToolLifecycleManager()

        tool1 = ConcreteTool(name="Tool1")
        tool2 = ConcreteTool(name="Tool2")

        mock_registry = Mock()
        mock_registry.get_tools.return_value = [tool1, tool2]
        mock_registry.get_tool.side_effect = lambda name: tool1 if name == "Tool1" else tool2
        manager.registry = mock_registry

        manager._tool_states["Tool1"] = ToolState.INITIALIZED
        manager._tool_states["Tool2"] = ToolState.INITIALIZED

        result = manager.shutdown_all_tools()

        assert result is True
        assert tool1._shutdown_called is True
        assert tool2._shutdown_called is True

    def test_shutdown_all_tools_handles_exception(self):
        """Test shutdown all tools handles exceptions."""
        manager = ToolLifecycleManager()

        tool1 = Mock(spec=Tool)
        tool1.name = "FailingTool"
        tool1.shutdown = Mock(side_effect=Exception("Shutdown failed"))
        tool2 = ConcreteTool(name="Tool2")

        mock_registry = Mock()
        mock_registry.get_tools.return_value = [tool1, tool2]
        mock_registry.get_tool.side_effect = lambda name: tool1 if name == "FailingTool" else tool2
        manager.registry = mock_registry

        manager._tool_states["FailingTool"] = ToolState.INITIALIZED
        manager._tool_states["Tool2"] = ToolState.INITIALIZED

        # Should not raise
        result = manager.shutdown_all_tools()

        assert result is True


class TestToolLifecycleStateManagement:
    """Test lifecycle state management."""

    def test_get_tool_states(self):
        """Test getting all tool states."""
        manager = ToolLifecycleManager()

        manager._tool_states = {
            "Tool1": ToolState.INITIALIZED,
            "Tool2": ToolState.SHUTDOWN,
            "Tool3": ToolState.ERROR
        }

        result = manager.get_tool_states()

        assert result == manager._tool_states
        assert result is not manager._tool_states  # Should be a copy

    def test_get_tool_state(self):
        """Test getting specific tool state."""
        manager = ToolLifecycleManager()

        manager._tool_states["TestTool"] = ToolState.INITIALIZED

        result = manager.get_tool_state("TestTool")
        assert result == ToolState.INITIALIZED

    def test_get_tool_state_not_found(self):
        """Test getting state for nonexistent tool."""
        manager = ToolLifecycleManager()

        result = manager.get_tool_state("NonExistentTool")
        assert result == ToolState.UNLOADED

    def test_is_tool_initialized_true(self):
        """Test is_tool_initialized returns True."""
        manager = ToolLifecycleManager()

        manager._tool_states["TestTool"] = ToolState.INITIALIZED

        assert manager.is_tool_initialized("TestTool") is True

    def test_is_tool_initialized_false(self):
        """Test is_tool_initialized returns False."""
        manager = ToolLifecycleManager()

        manager._tool_states["TestTool"] = ToolState.LOADED

        assert manager.is_tool_initialized("TestTool") is False

    def test_is_tool_active_initialized(self):
        """Test is_tool_active for initialized tool."""
        manager = ToolLifecycleManager()

        manager._tool_states["TestTool"] = ToolState.INITIALIZED

        assert manager.is_tool_active("TestTool") is True

    def test_is_tool_active_initializing(self):
        """Test is_tool_active for initializing tool."""
        manager = ToolLifecycleManager()

        manager._tool_states["TestTool"] = ToolState.INITIALIZING

        assert manager.is_tool_active("TestTool") is True

    def test_is_tool_active_shutdown(self):
        """Test is_tool_active for shutdown tool."""
        manager = ToolLifecycleManager()

        manager._tool_states["TestTool"] = ToolState.SHUTDOWN

        assert manager.is_tool_active("TestTool") is False

    def test_get_active_tools(self):
        """Test getting active tools."""
        manager = ToolLifecycleManager()

        manager._tool_states = {
            "ActiveTool1": ToolState.INITIALIZED,
            "ActiveTool2": ToolState.INITIALIZING,
            "InactiveTool": ToolState.SHUTDOWN
        }

        result = manager.get_active_tools()

        assert "ActiveTool1" in result
        assert "ActiveTool2" in result
        assert "InactiveTool" not in result


class TestToolLifecycleDependencies:
    """Test lifecycle dependency management."""

    def test_get_tool_dependencies(self):
        """Test getting tool dependencies."""
        manager = ToolLifecycleManager()

        manager.set_tool_dependencies("TestTool", ["dep1", "dep2"])

        result = manager.get_tool_dependencies("TestTool")
        assert result == ["dep1", "dep2"]

    def test_get_tool_dependencies_not_found(self):
        """Test getting dependencies for nonexistent tool."""
        manager = ToolLifecycleManager()

        result = manager.get_tool_dependencies("NonExistentTool")
        assert result == []

    def test_set_tool_dependencies(self):
        """Test setting tool dependencies."""
        manager = ToolLifecycleManager()

        manager.set_tool_dependencies("TestTool", ["dep1"])

        assert manager._tool_dependencies["TestTool"] == ["dep1"]

    def test_check_dependencies_satisfied(self):
        """Test checking satisfied dependencies."""
        manager = ToolLifecycleManager()

        manager._tool_states["Dep1"] = ToolState.INITIALIZED
        manager._tool_dependencies["TestTool"] = ["Dep1"]

        result = manager._check_dependencies("TestTool")
        assert result is True

    def test_check_dependencies_not_satisfied(self):
        """Test checking unsatisfied dependencies."""
        manager = ToolLifecycleManager()

        manager._tool_states["Dep1"] = ToolState.UNLOADED
        manager._tool_dependencies["TestTool"] = ["Dep1"]

        result = manager._check_dependencies("TestTool")
        assert result is False

    def test_check_dependencies_empty(self):
        """Test checking empty dependencies."""
        manager = ToolLifecycleManager()

        result = manager._check_dependencies("TestTool")
        assert result is True

    def test_sort_tools_by_dependencies(self):
        """Test sorting tools by dependencies."""
        manager = ToolLifecycleManager()

        tool_a = ConcreteTool(name="ToolA")
        tool_b = ConcreteTool(name="ToolB")
        tool_c = ConcreteTool(name="ToolC")

        manager.set_tool_dependencies("ToolB", ["ToolA"])
        manager.set_tool_dependencies("ToolC", ["ToolB"])

        result = manager._sort_tools_by_dependencies([tool_a, tool_b, tool_c])

        assert result[0].name == "ToolA"
        assert result[1].name == "ToolB"
        assert result[2].name == "ToolC"

    def test_sort_tools_circular_dependency(self):
        """Test sorting tools with circular dependency."""
        manager = ToolLifecycleManager()

        tool_a = ConcreteTool(name="ToolA")
        tool_b = ConcreteTool(name="ToolB")

        manager.set_tool_dependencies("ToolA", ["ToolB"])
        manager.set_tool_dependencies("ToolB", ["ToolA"])

        with pytest.raises(ToolLifecycleError) as exc_info:
            manager._sort_tools_by_dependencies([tool_a, tool_b])

        assert "Circular dependency" in str(exc_info.value)


class TestToolLifecycleAccessibleTool:
    """Test lifecycle with accessible tools."""

    def test_initialize_accessible_tool(self):
        """Test initializing accessible tool."""
        manager = ToolLifecycleManager()
        container = Mock()

        tool = ConcreteAccessibleTool(name="AccessibleTool")

        result = manager.initialize_tool(tool, container)

        assert result is True

    def test_shutdown_accessible_tool(self):
        """Test shutting down accessible tool."""
        manager = ToolLifecycleManager()

        tool = ConcreteAccessibleTool(name="AccessibleTool")

        mock_registry = Mock()
        mock_registry.get_tool.return_value = tool
        manager.registry = mock_registry

        manager._tool_states["AccessibleTool"] = ToolState.INITIALIZED

        result = manager.shutdown_tool("AccessibleTool")

        assert result is True


class TestCreateLifecycleManager:
    """Test create_lifecycle_manager function."""

    def test_create_lifecycle_manager_no_registry(self):
        """Test create_lifecycle_manager without registry."""
        manager = create_lifecycle_manager()

        assert isinstance(manager, ToolLifecycleManager)
        assert isinstance(manager.registry, ToolRegistry)

    def test_create_lifecycle_manager_with_registry(self):
        """Test create_lifecycle_manager with registry."""
        mock_registry = Mock()
        manager = create_lifecycle_manager(mock_registry)

        assert manager.registry is mock_registry


class TestToolLifecycleEdgeCases:
    """Test edge cases for lifecycle management."""

    def test_initialize_tool_exception_in_outer_try(self):
        """Test initialize_tool with exception in outer try block."""
        manager = ToolLifecycleManager()
        container = Mock()

        tool = Mock(spec=Tool)
        tool.name = "TestTool"
        tool.initialize = Mock(side_effect=RuntimeError("Unexpected error"))

        with pytest.raises(ToolLifecycleError):
            manager.initialize_tool(tool, container)

        assert manager.get_tool_state("TestTool") == ToolState.ERROR

    def test_shutdown_tool_exception_in_outer_try(self):
        """Test shutdown_tool with exception in outer try block."""
        manager = ToolLifecycleManager()

        mock_registry = Mock()
        mock_registry.get_tool.side_effect = RuntimeError("Registry error")
        manager.registry = mock_registry

        with pytest.raises(ToolLifecycleError):
            manager.shutdown_tool("TestTool")

    def test_initialize_all_tools_exception(self):
        """Test initialize_all_tools with general exception."""
        manager = ToolLifecycleManager()
        container = Mock()

        mock_registry = Mock()
        mock_registry.get_tools.side_effect = Exception("Registry error")
        manager.registry = mock_registry

        with pytest.raises(ToolLifecycleError):
            manager.initialize_all_tools(container)

    def test_shutdown_all_tools_exception(self):
        """Test shutdown_all_tools with general exception."""
        manager = ToolLifecycleManager()

        mock_registry = Mock()
        mock_registry.get_tools.side_effect = Exception("Registry error")
        manager.registry = mock_registry

        with pytest.raises(ToolLifecycleError):
            manager.shutdown_all_tools()

    def test_lifecycle_manager_with_none_registry(self):
        """Test lifecycle manager with None registry."""
        manager = ToolLifecycleManager(None)

        assert isinstance(manager.registry, ToolRegistry)

    def test_tool_lifecycle_error_exception(self):
        """Test ToolLifecycleError exception."""
        error = ToolLifecycleError("Test error message")

        assert str(error) == "Test error message"

    def test_initialize_tools_empty_list(self):
        """Test initialize_tools with empty list."""
        manager = ToolLifecycleManager()

        # Should not raise
        manager.initialize_tools([])

    def test_shutdown_tools_empty_list(self):
        """Test shutdown_tools with empty list."""
        manager = ToolLifecycleManager()

        # Should not raise
        manager.shutdown_tools([])
