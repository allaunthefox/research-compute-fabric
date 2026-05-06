"""Test tool lifecycle functionality."""

import pytest
from unittest.mock import MagicMock
from nodupe.core.tool_system.lifecycle import ToolLifecycleManager, ToolLifecycleError, ToolState
from nodupe.core.tool_system.registry import ToolRegistry
from nodupe.core.tool_system.base import Tool


class TestToolLifecycleManager:
    """Test tool lifecycle manager core functionality."""

    def test_tool_lifecycle_manager_initialization(self):
        """Test tool lifecycle manager initialization."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        assert lifecycle_manager is not None
        assert isinstance(lifecycle_manager, ToolLifecycleManager)
        assert lifecycle_manager.registry is registry

        # Test that it has expected attributes
        assert hasattr(lifecycle_manager, 'initialize_tool')
        assert hasattr(lifecycle_manager, 'shutdown_tool')
        assert hasattr(lifecycle_manager, 'initialize_all_tools')
        assert hasattr(lifecycle_manager, 'shutdown_all_tools')
        assert hasattr(lifecycle_manager, 'get_tool_state')
        assert hasattr(lifecycle_manager, 'is_tool_initialized')
        assert hasattr(lifecycle_manager, 'is_tool_active')
        assert hasattr(lifecycle_manager, 'get_active_tools')
        assert hasattr(lifecycle_manager, 'get_tool_dependencies')
        assert hasattr(lifecycle_manager, 'set_tool_dependencies')
        assert hasattr(lifecycle_manager, 'initialize')
        assert hasattr(lifecycle_manager, 'shutdown')

    def test_tool_lifecycle_manager_with_container(self):
        """Test tool lifecycle manager with dependency container."""
        from nodupe.core.container import ServiceContainer

        registry = ToolRegistry()
        container = ServiceContainer()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Initialize lifecycle manager with container
        lifecycle_manager.initialize(container)
        assert lifecycle_manager.container is container

    def test_tool_lifecycle_manager_lifecycle(self):
        """Test tool lifecycle manager lifecycle operations."""
        from nodupe.core.container import ServiceContainer

        registry = ToolRegistry()
        container = ServiceContainer()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Test initialization
        lifecycle_manager.initialize(container)
        assert lifecycle_manager.container is container

        # Test shutdown
        lifecycle_manager.shutdown()
        assert lifecycle_manager.container is None

        # Test re-initialization
        lifecycle_manager.initialize(container)
        assert lifecycle_manager.container is container


class TestToolState:
    """Test tool state functionality."""

    def test_tool_state_enum(self):
        """Test tool state enum values."""
        # Test that all expected states are present
        assert hasattr(ToolState, 'UNINITIALIZED')
        assert hasattr(ToolState, 'INITIALIZED')
        assert hasattr(ToolState, 'ACTIVE')
        assert hasattr(ToolState, 'FAILED')

        # Test state values
        assert ToolState.UNINITIALIZED.value == 0
        assert ToolState.INITIALIZED.value == 1
        assert ToolState.ACTIVE.value == 2
        assert ToolState.FAILED.value == 3


class TestToolLifecycleOperations:
    """Test tool lifecycle operations."""

    def test_initialize_tool(self):
        """Test initializing a tool."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Create a test tool
        class TestTool(Tool):
            """Test tool implementation for lifecycle testing."""

            def __init__(self):
                """Initialize the test tool."""
                self.name = "test_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        test_tool = TestTool()
        registry.register(test_tool)

        # Initialize tool
        result = lifecycle_manager.initialize_tool("test_tool")
        assert result is True
        assert test_tool.initialized is True

        # Check tool state
        state = lifecycle_manager.get_tool_state("test_tool")
        assert state == ToolState.INITIALIZED

    def test_shutdown_tool(self):
        """Test shutting down a tool."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Create a test tool
        class TestTool(Tool):
            """Test tool implementation for lifecycle testing."""

            def __init__(self):
                """Initialize the test tool."""
                self.name = "test_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False
                self.shutdown_called = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                self.shutdown_called = True

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        test_tool = TestTool()
        registry.register(test_tool)

        # Initialize tool
        lifecycle_manager.initialize_tool("test_tool")
        assert test_tool.initialized is True

        # Shutdown tool
        result = lifecycle_manager.shutdown_tool("test_tool")
        assert result is True
        assert test_tool.shutdown_called is True

        # Check tool state
        state = lifecycle_manager.get_tool_state("test_tool")
        assert state == ToolState.UNINITIALIZED

    def test_initialize_all_tools(self):
        """Test initializing all tools."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Create multiple test tools
        tools = []
        for i in range(3):
            class TestTool(Tool):
                """Test tool implementation."""

                def __init__(self):
                    """Initialize the test tool."""
                    self.name = f"test_tool_{i}"
                    self.version = "1.0.0"
                    self.dependencies = []
                    self.initialized = False

                def initialize(self, container):
                    """Initialize the tool with the container."""
                    self.initialized = True

                def shutdown(self):
                    """Shutdown the tool."""
                    pass

                def get_capabilities(self):
                    """Get the tool capabilities."""
                    return {"test": True}

                @property
                def api_methods(self):
                    """Get the API methods."""
                    return {}

                def run_standalone(self, args):
                    """Run the tool in standalone mode."""
                    return 0

                def describe_usage(self):
                    """Describe how to use the tool."""
                    return "Test tool"

            test_tool = TestTool()
            tools.append(test_tool)
            registry.register(test_tool)

        # Initialize all tools
        result = lifecycle_manager.initialize_all_tools(MagicMock())
        assert result is True

        # Verify all tools are initialized
        for tool in tools:
            assert tool.initialized is True
            state = lifecycle_manager.get_tool_state(tool.name)
            assert state == ToolState.INITIALIZED

    def test_shutdown_all_tools(self):
        """Test shutting down all tools."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Create multiple test tools
        tools = []
        for i in range(3):
            class TestTool(Tool):
                """Test tool implementation."""

                def __init__(self):
                    """Initialize the test tool."""
                    self.name = f"test_tool_{i}"
                    self.version = "1.0.0"
                    self.dependencies = []
                    self.initialized = False
                    self.shutdown_called = False

                def initialize(self, container):
                    """Initialize the tool with the container."""
                    self.initialized = True

                def shutdown(self):
                    """Shutdown the tool."""
                    self.shutdown_called = True

                def get_capabilities(self):
                    """Get the tool capabilities."""
                    return {"test": True}

                @property
                def api_methods(self):
                    """Get the API methods."""
                    return {}

                def run_standalone(self, args):
                    """Run the tool in standalone mode."""
                    return 0

                def describe_usage(self):
                    """Describe how to use the tool."""
                    return "Test tool"

            test_tool = TestTool()
            tools.append(test_tool)
            registry.register(test_tool)

        # Initialize all tools
        lifecycle_manager.initialize_all_tools(MagicMock())

        # Shutdown all tools
        result = lifecycle_manager.shutdown_all_tools()
        assert result is True

        # Verify all tools are shutdown
        for tool in tools:
            assert tool.shutdown_called is True
            state = lifecycle_manager.get_tool_state(tool.name)
            assert state == ToolState.UNINITIALIZED

    def test_get_tool_state(self):
        """Test getting tool state."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Create a test tool
        class TestTool(Tool):
            """Test tool implementation for lifecycle testing."""

            def __init__(self):
                """Initialize the test tool."""
                self.name = "test_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        test_tool = TestTool()
        registry.register(test_tool)

        # Check initial state
        state = lifecycle_manager.get_tool_state("test_tool")
        assert state == ToolState.UNINITIALIZED

        # Initialize tool
        lifecycle_manager.initialize_tool("test_tool")

        # Check state after initialization
        state = lifecycle_manager.get_tool_state("test_tool")
        assert state == ToolState.INITIALIZED

    def test_is_tool_initialized(self):
        """Test checking if tool is initialized."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Create a test tool
        class TestTool(Tool):
            """Test tool implementation for lifecycle testing."""

            def __init__(self):
                """Initialize the test tool."""
                self.name = "test_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        test_tool = TestTool()
        registry.register(test_tool)

        # Check before initialization
        result = lifecycle_manager.is_tool_initialized("test_tool")
        assert result is False

        # Initialize tool
        lifecycle_manager.initialize_tool("test_tool")

        # Check after initialization
        result = lifecycle_manager.is_tool_initialized("test_tool")
        assert result is True

    def test_is_tool_active(self):
        """Test checking if tool is active."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Create a test tool
        class TestTool(Tool):
            """Test tool implementation for lifecycle testing."""

            def __init__(self):
                """Initialize the test tool."""
                self.name = "test_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        test_tool = TestTool()
        registry.register(test_tool)

        # Check before initialization
        result = lifecycle_manager.is_tool_active("test_tool")
        assert result is False

        # Initialize tool
        lifecycle_manager.initialize_tool("test_tool")

        # Check after initialization (should be active)
        result = lifecycle_manager.is_tool_active("test_tool")
        assert result is True

    def test_get_active_tools(self):
        """Test getting active tools."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Create multiple test tools
        tools = []
        for i in range(3):
            class TestTool(Tool):
                """Test tool implementation."""

                def __init__(self):
                    """Initialize the test tool."""
                    self.name = f"test_tool_{i}"
                    self.version = "1.0.0"
                    self.dependencies = []
                    self.initialized = False

                def initialize(self, container):
                    """Initialize the tool with the container."""
                    self.initialized = True

                def shutdown(self):
                    """Shutdown the tool."""
                    pass

                def get_capabilities(self):
                    """Get the tool capabilities."""
                    return {"test": True}

                @property
                def api_methods(self):
                    """Get the API methods."""
                    return {}

                def run_standalone(self, args):
                    """Run the tool in standalone mode."""
                    return 0

                def describe_usage(self):
                    """Describe how to use the tool."""
                    return "Test tool"

            test_tool = TestTool()
            tools.append(test_tool)
            registry.register(test_tool)

        # Initialize some tools
        lifecycle_manager.initialize_tool("test_tool_0")
        lifecycle_manager.initialize_tool("test_tool_2")

        # Get active tools
        active_tools = lifecycle_manager.get_active_tools()
        assert len(active_tools) == 2
        assert "test_tool_0" in active_tools
        assert "test_tool_2" in active_tools

    def test_get_tool_dependencies(self):
        """Test getting tool dependencies."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Create a test tool
        class TestTool(Tool):
            """Test tool implementation for lifecycle testing."""

            def __init__(self):
                """Initialize the test tool."""
                self.name = "test_tool"
                self.version = "1.0.0"
                self.dependencies = ["dep1", "dep2"]
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        test_tool = TestTool()
        registry.register(test_tool)

        # Get tool dependencies
        dependencies = lifecycle_manager.get_tool_dependencies("test_tool")
        assert dependencies == ["dep1", "dep2"]

    def test_set_tool_dependencies(self):
        """Test setting tool dependencies."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Create a test tool
        class TestTool(Tool):
            """Test tool implementation for lifecycle testing."""

            def __init__(self):
                """Initialize the test tool."""
                self.name = "test_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        test_tool = TestTool()
        registry.register(test_tool)

        # Set tool dependencies
        lifecycle_manager.set_tool_dependencies(
            "test_tool", ["new_dep1", "new_dep2"])

        # Get tool dependencies
        dependencies = lifecycle_manager.get_tool_dependencies("test_tool")
        assert dependencies == ["new_dep1", "new_dep2"]


class TestToolLifecycleEdgeCases:
    """Test tool lifecycle edge cases."""

    def test_initialize_nonexistent_tool(self):
        """Test initializing non-existent tool."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Try to initialize non-existent tool
        result = lifecycle_manager.initialize_tool("nonexistent_tool")
        assert result is False

    def test_shutdown_nonexistent_tool(self):
        """Test shutting down non-existent tool."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Try to shutdown non-existent tool
        result = lifecycle_manager.shutdown_tool("nonexistent_tool")
        assert result is False

    def test_initialize_tool_with_exception(self):
        """Test initializing tool that throws exception."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Create a test tool that throws exception
        class FailingTool(Tool):
            """Test tool implementation for lifecycle testing."""

            def __init__(self):
                """Initialize the test tool."""
                self.name = "failing_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                raise Exception("Initialize failed")

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        failing_tool = FailingTool()
        registry.register(failing_tool)

        # Try to initialize tool
        result = lifecycle_manager.initialize_tool("failing_tool")
        assert result is False

        # Check tool state
        state = lifecycle_manager.get_tool_state("failing_tool")
        assert state == ToolState.FAILED

    def test_shutdown_tool_with_exception(self):
        """Test shutting down tool that throws exception."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Create a test tool that throws exception in shutdown
        class FailingTool(Tool):
            """Test tool implementation for lifecycle testing."""

            def __init__(self):
                """Initialize the test tool."""
                self.name = "failing_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                raise Exception("Shutdown failed")

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        failing_tool = FailingTool()
        registry.register(failing_tool)

        # Initialize tool
        lifecycle_manager.initialize_tool("failing_tool")

        # Try to shutdown tool
        result = lifecycle_manager.shutdown_tool("failing_tool")
        assert result is False

        # Check tool state
        state = lifecycle_manager.get_tool_state("failing_tool")
        assert state == ToolState.FAILED


class TestToolLifecyclePerformance:
    """Test tool lifecycle performance."""

    def test_mass_tool_initialization(self):
        """Test mass tool initialization."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Create many test tools
        tools = []
        for i in range(10):
            class TestTool(Tool):
                """Test tool implementation."""

                def __init__(self):
                    """Initialize the test tool."""
                    self.name = f"test_tool_{i}"
                    self.version = "1.0.0"
                    self.dependencies = []
                    self.initialized = False

                def initialize(self, container):
                    """Initialize the tool with the container."""
                    self.initialized = True

                def shutdown(self):
                    """Shutdown the tool."""
                    pass

                def get_capabilities(self):
                    """Get the tool capabilities."""
                    return {"test": True}

                @property
                def api_methods(self):
                    """Get the API methods."""
                    return {}

                def run_standalone(self, args):
                    """Run the tool in standalone mode."""
                    return 0

                def describe_usage(self):
                    """Describe how to use the tool."""
                    return "Test tool"

            test_tool = TestTool()
            tools.append(test_tool)
            registry.register(test_tool)

        # Initialize all tools
        result = lifecycle_manager.initialize_all_tools(MagicMock())
        assert result is True

        # Verify all tools are initialized
        for tool in tools:
            assert tool.initialized is True

    def test_tool_lifecycle_performance(self):
        """Test tool lifecycle performance."""
        import time

        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Create many test tools
        tools = []
        for i in range(20):
            class TestTool(Tool):
                """Test tool implementation."""

                def __init__(self):
                    """Initialize the test tool."""
                    self.name = f"perf_tool_{i}"
                    self.version = "1.0.0"
                    self.dependencies = []
                    self.initialized = False
                    self.shutdown_called = False

                def initialize(self, container):
                    """Initialize the tool with the container."""
                    self.initialized = True

                def shutdown(self):
                    """Shutdown the tool."""
                    self.shutdown_called = True

                def get_capabilities(self):
                    """Get the tool capabilities."""
                    return {"test": True}

                @property
                def api_methods(self):
                    """Get the API methods."""
                    return {}

                def run_standalone(self, args):
                    """Run the tool in standalone mode."""
                    return 0

                def describe_usage(self):
                    """Describe how to use the tool."""
                    return "Test tool"

            test_tool = TestTool()
            tools.append(test_tool)
            registry.register(test_tool)

        # Test initialization performance
        start_time = time.time()
        lifecycle_manager.initialize_all_tools(MagicMock())
        init_time = time.time() - start_time

        # Test shutdown performance
        start_time = time.time()
        lifecycle_manager.shutdown_all_tools()
        shutdown_time = time.time() - start_time

        # Should be fast operations
        assert init_time < 1.0
        assert shutdown_time < 0.5


class TestToolLifecycleIntegration:
    """Test tool lifecycle integration scenarios."""

    def test_tool_lifecycle_with_registry(self):
        """Test tool lifecycle integration with registry."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Create a test tool
        class TestTool(Tool):
            """Test tool implementation for lifecycle testing."""

            def __init__(self):
                """Initialize the test tool."""
                self.name = "test_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        test_tool = TestTool()
        registry.register(test_tool)

        # Initialize tool through lifecycle manager
        lifecycle_manager.initialize_tool("test_tool")

        # Verify tool is accessible through registry
        retrieved = registry.get_tool("test_tool")
        assert retrieved is test_tool
        assert retrieved.initialized is True

    def test_tool_lifecycle_with_loader(self):
        """Test tool lifecycle integration with loader."""
        from nodupe.core.tool_system.loader import ToolLoader

        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)
        loader = ToolLoader(registry)

        # Create a test tool
        class TestTool(Tool):
            """Test tool implementation for lifecycle testing."""

            def __init__(self):
                """Initialize the test tool."""
                self.name = "test_tool"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False
                self.shutdown_called = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                self.shutdown_called = True

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        test_tool = TestTool()

        # Load tool
        loaded_tool = loader.load_tool(test_tool)

        # Initialize through lifecycle manager
        lifecycle_manager.initialize_tool("test_tool")
        assert test_tool.initialized is True

        # Shutdown through lifecycle manager
        lifecycle_manager.shutdown_tool("test_tool")
        assert test_tool.shutdown_called is True


class TestToolLifecycleErrorHandling:
    """Test tool lifecycle error handling."""

    def test_initialize_tool_with_missing_methods(self):
        """Test initializing tool with missing required methods."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Create a tool missing required methods
        class IncompleteTool(Tool):
            """Test tool implementation for lifecycle testing."""

            def __init__(self):
                """Initialize the test tool."""
                self.name = "incomplete_tool"
                self.version = "1.0.0"
                self.dependencies = []
                # Missing initialize and shutdown methods

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        incomplete_tool = IncompleteTool()
        registry.register(incomplete_tool)

        # Try to initialize tool
        with pytest.raises(ToolLifecycleError):
            lifecycle_manager.initialize_tool("incomplete_tool")


class TestToolLifecycleAdvanced:
    """Test advanced tool lifecycle functionality."""

    def test_tool_lifecycle_with_dependencies(self):
        """Test tool lifecycle with dependencies."""
        registry = ToolRegistry()
        lifecycle_manager = ToolLifecycleManager(registry)

        # Create test tools with dependencies
        class ToolA(Tool):
            """Test tool implementation for lifecycle testing."""

            def __init__(self):
                """Initialize the test tool."""
                self.name = "tool_a"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"feature_a": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        class ToolB(Tool):
            """Test tool implementation for lifecycle testing."""

            def __init__(self):
                """Initialize the test tool."""
                self.name = "tool_b"
                self.version = "1.0.0"
                self.dependencies = ["tool_a"]
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"feature_b": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        tool_a = ToolA()
        tool_b = ToolB()
        registry.register(tool_a)
        registry.register(tool_b)

        # Set dependencies
        lifecycle_manager.set_tool_dependencies("tool_b", ["tool_a"])

        # Initialize tools (should handle dependencies)
        lifecycle_manager.initialize_tool("tool_a")
        lifecycle_manager.initialize_tool("tool_b")

        # Verify both tools are initialized
        assert tool_a.initialized is True
        assert tool_b.initialized is True
