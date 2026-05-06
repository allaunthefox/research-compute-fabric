"""Tests for the tool_system base module."""

from unittest.mock import MagicMock, Mock

import pytest

from nodupe.core.tool_system.base import AccessibleTool, Tool, ToolMetadata


class ConcreteTool(Tool):
    """Concrete implementation of Tool for testing."""

    def __init__(
        self,
        name: str = "TestTool",
        version: str = "1.0.0",
        dependencies: list[str] | None = None
    ):
        """Initialize ConcreteTool with name, version, and dependencies."""
        self._name = name
        self._version = version
        self._dependencies = dependencies or []
        self._initialized = False
        self._capabilities = {"test": "capability"}
        self._api_methods = {}

    @property
    def name(self) -> str:
        """Tool name property."""
        return self._name

    @property
    def version(self) -> str:
        """Tool version property."""
        return self._version

    @property
    def dependencies(self) -> list[str]:
        """Tool dependencies property."""
        return self._dependencies

    def initialize(self, container) -> None:
        """Initialize the tool with the given container."""
        self._initialized = True

    def shutdown(self) -> None:
        """Shutdown the tool and clean up resources."""
        self._initialized = False

    def get_capabilities(self) -> dict:
        """Get the tool capabilities."""
        return self._capabilities

    @property
    def api_methods(self) -> dict:
        """API methods exposed by this tool."""
        return self._api_methods

    def run_standalone(self, args: list[str]) -> int:
        """Run the tool as a standalone process."""
        return 0

    def describe_usage(self) -> str:
        """Describe how to use this tool."""
        return "Test tool usage description"


class ConcreteAccessibleTool(AccessibleTool):
    """Concrete implementation of AccessibleTool for testing."""

    def __init__(
        self,
        name: str = "AccessibleTestTool",
        version: str = "1.0.0",
        dependencies: list[str] | None = None
    ):
        """Initialize ConcreteAccessibleTool with name, version, and dependencies."""
        self._name = name
        self._version = version
        self._dependencies = dependencies or []
        self._initialized = False
        self._capabilities = {"accessible": True}
        self._api_methods = {}
        self._announced_messages = []
        self._formatted_data = ""

    @property
    def name(self) -> str:
        """Tool name property."""
        return self._name

    @property
    def version(self) -> str:
        """Tool version property."""
        return self._version

    @property
    def dependencies(self) -> list[str]:
        """Tool dependencies property."""
        return self._dependencies

    def initialize(self, container) -> None:
        """Initialize the tool with the given container."""
        self._initialized = True

    def shutdown(self) -> None:
        """Shutdown the tool and clean up resources."""
        self._initialized = False

    def get_capabilities(self) -> dict:
        """Get the tool capabilities."""
        return self._capabilities

    @property
    def api_methods(self) -> dict:
        """API methods exposed by this tool."""
        return self._api_methods

    def run_standalone(self, args: list[str]) -> int:
        """Run the tool as a standalone process."""
        return 0

    def describe_usage(self) -> str:
        """Describe how to use this tool."""
        return "Accessible tool usage description"

    def announce_to_assistive_tech(self, message: str, interrupt: bool = True) -> None:
        """Announce a message to assistive technologies."""
        self._announced_messages.append((message, interrupt))

    def format_for_accessibility(self, data) -> str:
        """Format data for accessibility."""
        self._formatted_data = str(data)
        return self._formatted_data

    def get_ipc_socket_documentation(self) -> dict:
        """Get IPC socket documentation for accessibility."""
        return {"endpoint": "/accessible", "features": ["screen_reader", "braille"]}

    def get_accessible_status(self) -> str:
        """Get accessible status of the tool."""
        return "Tool is accessible and ready"

    def log_accessible_message(self, message: str, level: str = "info") -> None:
        """Log a message with accessibility considerations."""
        pass


class TestToolMetadata:
    """Test ToolMetadata dataclass."""

    def test_tool_metadata_creation(self):
        """Test ToolMetadata instance creation."""
        metadata = ToolMetadata(
            name="TestTool",
            version="1.0.0",
            software_id="org.test.tool",
            description="A test tool",
            author="Test Author",
            license="MIT",
            dependencies=["dep1", "dep2"],
            tags=["test", "tool"]
        )

        assert metadata.name == "TestTool"
        assert metadata.version == "1.0.0"
        assert metadata.software_id == "org.test.tool"
        assert metadata.description == "A test tool"
        assert metadata.author == "Test Author"
        assert metadata.license == "MIT"
        assert metadata.dependencies == ["dep1", "dep2"]
        assert metadata.tags == ["test", "tool"]

    def test_tool_metadata_with_optional_fields(self):
        """Test ToolMetadata with optional fields."""
        metadata = ToolMetadata(
            name="TestTool",
            version="1.0.0",
            software_id="org.test.tool",
            description="A test tool",
            author="Test Author",
            license="MIT",
            dependencies=[],
            tags=[],
            persistent_id="persistent-123",
            entitlement_key="entitlement-key-456"
        )

        assert metadata.persistent_id == "persistent-123"
        assert metadata.entitlement_key == "entitlement-key-456"

    def test_tool_metadata_default_optional_fields(self):
        """Test ToolMetadata default optional fields."""
        metadata = ToolMetadata(
            name="TestTool",
            version="1.0.0",
            software_id="org.test.tool",
            description="A test tool",
            author="Test Author",
            license="MIT",
            dependencies=[],
            tags=[]
        )

        assert metadata.persistent_id is None
        assert metadata.entitlement_key is None

    def test_tool_metadata_immutability(self):
        """Test that ToolMetadata is frozen (immutable)."""
        metadata = ToolMetadata(
            name="TestTool",
            version="1.0.0",
            software_id="org.test.tool",
            description="A test tool",
            author="Test Author",
            license="MIT",
            dependencies=[],
            tags=[]
        )

        # Should not be able to modify frozen dataclass
        with pytest.raises(AttributeError):
            metadata.name = "NewName"


class TestToolBase:
    """Test Tool abstract base class."""

    def test_tool_cannot_be_instantiated(self):
        """Test that Tool cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Tool()

    def test_concrete_tool_instantiation(self):
        """Test concrete Tool implementation instantiation."""
        tool = ConcreteTool()
        assert tool is not None

    def test_tool_name_property(self):
        """Test Tool name property."""
        tool = ConcreteTool(name="MyTool")
        assert tool.name == "MyTool"

    def test_tool_version_property(self):
        """Test Tool version property."""
        tool = ConcreteTool(version="2.0.0")
        assert tool.version == "2.0.0"

    def test_tool_dependencies_property(self):
        """Test Tool dependencies property."""
        tool = ConcreteTool(dependencies=["dep1", "dep2"])
        assert tool.dependencies == ["dep1", "dep2"]

    def test_tool_dependencies_default(self):
        """Test Tool dependencies default value."""
        tool = ConcreteTool()
        assert tool.dependencies == []

    def test_tool_initialize(self):
        """Test Tool initialize method."""
        tool = ConcreteTool()
        container = Mock()

        tool.initialize(container)

        assert tool._initialized is True

    def test_tool_shutdown(self):
        """Test Tool shutdown method."""
        tool = ConcreteTool()
        tool._initialized = True

        tool.shutdown()

        assert tool._initialized is False

    def test_tool_get_capabilities(self):
        """Test Tool get_capabilities method."""
        tool = ConcreteTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities, dict)
        assert "test" in capabilities

    def test_tool_api_methods_property(self):
        """Test Tool api_methods property."""
        tool = ConcreteTool()
        api_methods = tool.api_methods

        assert isinstance(api_methods, dict)

    def test_tool_run_standalone(self):
        """Test Tool run_standalone method."""
        tool = ConcreteTool()
        result = tool.run_standalone(["arg1", "arg2"])

        assert isinstance(result, int)

    def test_tool_describe_usage(self):
        """Test Tool describe_usage method."""
        tool = ConcreteTool()
        usage = tool.describe_usage()

        assert isinstance(usage, str)
        assert len(usage) > 0

    def test_tool_inheritance_check(self):
        """Test that ConcreteTool is subclass of Tool."""
        assert issubclass(ConcreteTool, Tool)

    def test_tool_instance_check(self):
        """Test that concrete instance is instance of Tool."""
        tool = ConcreteTool()
        assert isinstance(tool, Tool)


class TestAccessibleTool:
    """Test AccessibleTool abstract base class."""

    def test_accessible_tool_cannot_be_instantiated(self):
        """Test that AccessibleTool cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AccessibleTool()

    def test_concrete_accessible_tool_instantiation(self):
        """Test concrete AccessibleTool implementation instantiation."""
        tool = ConcreteAccessibleTool()
        assert tool is not None

    def test_accessible_tool_inherits_from_tool(self):
        """Test that AccessibleTool inherits from Tool."""
        assert issubclass(AccessibleTool, Tool)

    def test_accessible_tool_instance_check(self):
        """Test that accessible tool is instance of both classes."""
        tool = ConcreteAccessibleTool()
        assert isinstance(tool, AccessibleTool)
        assert isinstance(tool, Tool)

    def test_announce_to_assistive_tech(self):
        """Test announce_to_assistive_tech method."""
        tool = ConcreteAccessibleTool()

        tool.announce_to_assistive_tech("Test message")

        assert len(tool._announced_messages) == 1
        assert tool._announced_messages[0] == ("Test message", True)

    def test_announce_to_assistive_tech_no_interrupt(self):
        """Test announce_to_assistive_tech with interrupt=False."""
        tool = ConcreteAccessibleTool()

        tool.announce_to_assistive_tech("Test message", interrupt=False)

        assert len(tool._announced_messages) == 1
        assert tool._announced_messages[0] == ("Test message", False)

    def test_format_for_accessibility_string(self):
        """Test format_for_accessibility with string data."""
        tool = ConcreteAccessibleTool()

        result = tool.format_for_accessibility("Test data")

        assert result == "Test data"
        assert tool._formatted_data == "Test data"

    def test_format_for_accessibility_dict(self):
        """Test format_for_accessibility with dict data."""
        tool = ConcreteAccessibleTool()
        data = {"key": "value", "number": 42}

        result = tool.format_for_accessibility(data)

        assert isinstance(result, str)

    def test_format_for_accessibility_none(self):
        """Test format_for_accessibility with None data."""
        tool = ConcreteAccessibleTool()

        result = tool.format_for_accessibility(None)

        assert result == "None"

    def test_get_ipc_socket_documentation(self):
        """Test get_ipc_socket_documentation method."""
        tool = ConcreteAccessibleTool()

        doc = tool.get_ipc_socket_documentation()

        assert isinstance(doc, dict)
        assert "endpoint" in doc
        assert "features" in doc

    def test_get_accessible_status(self):
        """Test get_accessible_status method."""
        tool = ConcreteAccessibleTool()

        status = tool.get_accessible_status()

        assert isinstance(status, str)
        assert len(status) > 0

    def test_log_accessible_message_default_level(self):
        """Test log_accessible_message with default level."""
        tool = ConcreteAccessibleTool()

        # Should not raise
        tool.log_accessible_message("Test message")

    def test_log_accessible_message_custom_level(self):
        """Test log_accessible_message with custom level."""
        tool = ConcreteAccessibleTool()

        # Should not raise for various levels
        tool.log_accessible_message("Info message", level="info")
        tool.log_accessible_message("Warning message", level="warning")
        tool.log_accessible_message("Error message", level="error")
        tool.log_accessible_message("Debug message", level="debug")

    def test_accessible_tool_has_all_required_methods(self):
        """Test that AccessibleTool has all required accessibility methods."""
        tool = ConcreteAccessibleTool()

        assert hasattr(tool, 'announce_to_assistive_tech')
        assert hasattr(tool, 'format_for_accessibility')
        assert hasattr(tool, 'get_ipc_socket_documentation')
        assert hasattr(tool, 'get_accessible_status')
        assert hasattr(tool, 'log_accessible_message')

    def test_accessible_tool_has_all_tool_methods(self):
        """Test that AccessibleTool has all Tool methods."""
        tool = ConcreteAccessibleTool()

        # Tool methods
        assert hasattr(tool, 'name')
        assert hasattr(tool, 'version')
        assert hasattr(tool, 'dependencies')
        assert hasattr(tool, 'initialize')
        assert hasattr(tool, 'shutdown')
        assert hasattr(tool, 'get_capabilities')
        assert hasattr(tool, 'api_methods')
        assert hasattr(tool, 'run_standalone')
        assert hasattr(tool, 'describe_usage')


class TestToolEdgeCases:
    """Test edge cases for Tool and AccessibleTool."""

    def test_tool_with_empty_name(self):
        """Test Tool with empty name."""
        tool = ConcreteTool(name="")
        assert tool.name == ""

    def test_tool_with_empty_version(self):
        """Test Tool with empty version."""
        tool = ConcreteTool(version="")
        assert tool.version == ""

    def test_tool_with_none_dependencies(self):
        """Test Tool with None dependencies."""
        tool = ConcreteTool(dependencies=None)
        assert tool.dependencies == []

    def test_tool_initialize_with_none_container(self):
        """Test Tool initialize with None container."""
        tool = ConcreteTool()

        # Should not raise
        tool.initialize(None)
        assert tool._initialized is True

    def test_tool_run_standalone_with_empty_args(self):
        """Test Tool run_standalone with empty args."""
        tool = ConcreteTool()
        result = tool.run_standalone([])
        assert result == 0

    def test_tool_run_standalone_with_none_args(self):
        """Test Tool run_standalone with None args."""
        tool = ConcreteTool()
        result = tool.run_standalone(None)  # type: ignore
        assert result == 0

    def test_accessible_tool_announce_empty_message(self):
        """Test announce_to_assistive_tech with empty message."""
        tool = ConcreteAccessibleTool()

        tool.announce_to_assistive_tech("")

        assert len(tool._announced_messages) == 1
        assert tool._announced_messages[0][0] == ""

    def test_accessible_tool_format_empty_data(self):
        """Test format_for_accessibility with empty data."""
        tool = ConcreteAccessibleTool()

        result = tool.format_for_accessibility("")

        assert result == ""

    def test_accessible_tool_get_ipc_socket_documentation_empty(self):
        """Test get_ipc_socket_documentation returns valid structure."""
        tool = ConcreteAccessibleTool()

        doc = tool.get_ipc_socket_documentation()

        assert isinstance(doc, dict)

    def test_accessible_tool_get_accessible_status_empty(self):
        """Test get_accessible_status returns non-empty string."""
        tool = ConcreteAccessibleTool()

        status = tool.get_accessible_status()

        assert isinstance(status, str)

    def test_tool_metadata_empty_lists(self):
        """Test ToolMetadata with empty lists."""
        metadata = ToolMetadata(
            name="TestTool",
            version="1.0.0",
            software_id="org.test.tool",
            description="A test tool",
            author="Test Author",
            license="MIT",
            dependencies=[],
            tags=[]
        )

        assert metadata.dependencies == []
        assert metadata.tags == []

    def test_tool_metadata_long_values(self):
        """Test ToolMetadata with long values."""
        long_description = "A" * 10000
        metadata = ToolMetadata(
            name="TestTool",
            version="1.0.0",
            software_id="org.test.tool",
            description=long_description,
            author="Test Author",
            license="MIT",
            dependencies=[],
            tags=[]
        )

        assert len(metadata.description) == 10000

    def test_tool_metadata_special_characters(self):
        """Test ToolMetadata with special characters."""
        metadata = ToolMetadata(
            name="Test-Tool_123",
            version="1.0.0-beta+build.123",
            software_id="org.test.tool-v2",
            description="A test tool with special chars: @#$%",
            author="Test Author <test@example.com>",
            license="Apache-2.0",
            dependencies=[],
            tags=[]
        )

        assert "@" in metadata.description
        assert "Apache-2.0" in metadata.license
