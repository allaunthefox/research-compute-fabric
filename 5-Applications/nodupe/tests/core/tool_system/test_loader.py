"""Test Tool Loader Module.

Comprehensive tests for the tool loading system including:
- Tool loading from files and directories
- Tool instantiation and registration
- Tool unloading and cleanup
- Tool class validation
- Error handling
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nodupe.core.tool_system.base import Tool
from nodupe.core.tool_system.loader import ToolLoader, ToolLoaderError, create_tool_loader
from nodupe.core.tool_system.registry import ToolRegistry


class MockTool(Tool):
    """Mock tool for testing."""

    def __init__(self, name="MockTool", version="1.0.0", dependencies=None):
        """Initialize the mock tool.

        Args:
            name: The name of the tool.
            version: The version string of the tool.
            dependencies: List of tool dependencies.
        """
        self._name = name
        self._version = version
        self._dependencies = dependencies or []
        self._initialized = False

    @property
    def name(self):
        """Get the name of the tool.

        Returns:
            The tool name.
        """
        return self._name

    @property
    def version(self):
        """Get the version of the tool.

        Returns:
            The tool version.
        """
        return self._version

    @property
    def dependencies(self):
        """Get the list of tool dependencies.

        Returns:
            List of dependency names.
        """
        return self._dependencies

    def initialize(self, container):
        """Initialize the tool with a container.

        Args:
            container: The container to initialize with.
        """
        self._initialized = True

    def shutdown(self):
        """Shutdown the tool and release resources."""
        self._initialized = False

    def get_capabilities(self):
        """Get the tool's capabilities.

        Returns:
            Dictionary of capabilities.
        """
        return {"test": "capability"}

    @property
    def api_methods(self):
        """Get the tool's API methods.

        Returns:
            Dictionary of API methods.
        """
        return {}

    def run_standalone(self, args):
        """Run the tool as a standalone application.

        Args:
            args: Command-line arguments.

        Returns:
            Exit code.
        """
        return 0

    def describe_usage(self):
        """Get a description of tool usage.

        Returns:
            Usage description string.
        """
        return "Mock tool usage"


class TestToolLoaderInit:
    """Test ToolLoader initialization."""

    def test_tool_loader_init_default(self):
        """Test basic ToolLoader initialization with defaults."""
        loader = ToolLoader()

        assert isinstance(loader.registry, ToolRegistry)
        assert loader._loaded_tools == {}
        assert loader._tool_modules == {}
        assert loader.container is None

    def test_tool_loader_init_with_registry(self):
        """Test ToolLoader initialization with custom registry."""
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        assert loader.registry is registry

    def test_create_tool_loader_factory(self):
        """Test the create_tool_loader factory function."""
        loader = create_tool_loader()

        assert isinstance(loader, ToolLoader)

    def test_create_tool_loader_with_registry(self):
        """Test create_tool_loader with custom registry."""
        registry = ToolRegistry()
        loader = create_tool_loader(registry)

        assert loader.registry is registry


class TestToolLoaderInitialize:
    """Test ToolLoader initialize method."""

    def test_initialize_sets_container(self):
        """Test that initialize sets the container."""
        loader = ToolLoader()
        container = MagicMock()

        loader.initialize(container)

        assert loader.container is container


class TestLoadTool:
    """Test load_tool method."""

    def test_load_tool_success(self):
        """Test successfully loading a tool."""
        loader = ToolLoader()
        tool = MockTool()

        result = loader.load_tool(tool)

        assert result is tool
        assert tool._initialized is True
        assert "MockTool" in loader._loaded_tools

    def test_load_tool_with_container(self):
        """Test loading tool with container."""
        loader = ToolLoader()
        loader.container = MagicMock()
        tool = MockTool()

        result = loader.load_tool(tool)

        assert result is tool
        assert tool._initialized is True


class TestLoadToolFromFile:
    """Test load_tool_from_file method."""

    def test_load_tool_from_file_success(self, tmp_path):
        """Test successfully loading tool from file."""
        loader = ToolLoader()

        # Create a valid tool file
        tool_file = tmp_path / "test_tool.py"
        tool_file.write_text("""
from nodupe.core.tool_system.base import Tool

class TestTool(Tool):
    name = "TestTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Test tool"
""")

        tool_class = loader.load_tool_from_file(tool_file)

        assert tool_class is not None
        assert tool_class.__name__ == "TestTool"

    def test_load_tool_from_file_not_exists(self, tmp_path):
        """Test loading from nonexistent file."""
        loader = ToolLoader()

        nonexistent_file = tmp_path / "nonexistent.py"

        with pytest.raises(ToolLoaderError) as exc_info:
            loader.load_tool_from_file(nonexistent_file)

        assert "does not exist" in str(exc_info.value)

    def test_load_tool_from_file_not_python(self, tmp_path):
        """Test loading from non-Python file."""
        loader = ToolLoader()

        txt_file = tmp_path / "tool.txt"
        txt_file.write_text("This is not Python")

        with pytest.raises(ToolLoaderError) as exc_info:
            loader.load_tool_from_file(txt_file)

        assert "must be Python" in str(exc_info.value)

    def test_load_tool_from_file_no_tool_class(self, tmp_path):
        """Test loading file without Tool subclass."""
        loader = ToolLoader()

        no_tool_file = tmp_path / "no_tool.py"
        no_tool_file.write_text("""
# Just a regular Python file
def some_function():
    return 42
""")

        with pytest.raises(ToolLoaderError) as exc_info:
            loader.load_tool_from_file(no_tool_file)

        assert "No Tool subclass" in str(exc_info.value)

    def test_load_tool_from_file_invalid_tool_class(self, tmp_path):
        """Test loading file with invalid tool class."""
        loader = ToolLoader()

        invalid_tool_file = tmp_path / "invalid_tool.py"
        invalid_tool_file.write_text("""
from nodupe.core.tool_system.base import Tool

class InvalidTool(Tool):
    # Missing required attributes
    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Invalid tool"
""")

        with pytest.raises(ToolLoaderError) as exc_info:
            loader.load_tool_from_file(invalid_tool_file)

        assert "Invalid tool class" in str(exc_info.value)

    def test_load_tool_from_file_empty_name(self, tmp_path):
        """Test loading file with tool that has empty name."""
        loader = ToolLoader()

        empty_name_file = tmp_path / "empty_name.py"
        empty_name_file.write_text("""
from nodupe.core.tool_system.base import Tool

class EmptyNameTool(Tool):
    name = ""
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Empty name tool"
""")

        with pytest.raises(ToolLoaderError) as exc_info:
            loader.load_tool_from_file(empty_name_file)

        assert "Invalid tool class" in str(exc_info.value)

    def test_load_tool_from_file_stores_module(self, tmp_path):
        """Test that loading stores module reference."""
        loader = ToolLoader()

        tool_file = tmp_path / "test_tool.py"
        tool_file.write_text("""
from nodupe.core.tool_system.base import Tool

class TestTool(Tool):
    name = "TestTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Test tool"
""")

        tool_class = loader.load_tool_from_file(tool_file)

        assert tool_class.__name__ in loader._tool_modules

    def test_load_tool_from_file_accessibility_compliant(self, tmp_path, caplog):
        """Test loading accessibility compliant tool."""
        loader = ToolLoader()

        tool_file = tmp_path / "accessible_tool.py"
        tool_file.write_text("""
from nodupe.core.tool_system.accessible_base import AccessibleTool

class AccessibleTestTool(AccessibleTool):
    name = "AccessibleTestTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Accessible test tool"

    def get_ipc_socket_documentation(self):
        return {}
""")

        import logging
        with caplog.at_level(logging.INFO):
            tool_class = loader.load_tool_from_file(tool_file)

        assert tool_class.__name__ == "AccessibleTestTool"

    def test_load_tool_from_file_not_accessibility_compliant(self, tmp_path, caplog):
        """Test loading non-accessibility compliant tool."""
        loader = ToolLoader()

        tool_file = tmp_path / "non_accessible_tool.py"
        tool_file.write_text("""
from nodupe.core.tool_system.base import Tool

class NonAccessibleTool(Tool):
    name = "NonAccessibleTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Non-accessible tool"
""")

        import logging
        with caplog.at_level(logging.INFO):
            tool_class = loader.load_tool_from_file(tool_file)

        assert tool_class.__name__ == "NonAccessibleTool"


class TestLoadToolFromDirectory:
    """Test load_tool_from_directory method."""

    def test_load_tool_from_directory_success(self, tmp_path):
        """Test loading tools from directory."""
        loader = ToolLoader()

        # Create tool files
        tool_file1 = tmp_path / "tool1.py"
        tool_file1.write_text("""
from nodupe.core.tool_system.base import Tool

class Tool1(Tool):
    name = "Tool1"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Tool 1"
""")

        tool_file2 = tmp_path / "tool2.py"
        tool_file2.write_text("""
from nodupe.core.tool_system.base import Tool

class Tool2(Tool):
    name = "Tool2"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Tool 2"
""")

        loaded_tools = loader.load_tool_from_directory(tmp_path)

        assert len(loaded_tools) == 2
        tool_names = [t.__name__ for t in loaded_tools]
        assert "Tool1" in tool_names
        assert "Tool2" in tool_names

    def test_load_tool_from_directory_not_exists(self, tmp_path):
        """Test loading from nonexistent directory."""
        loader = ToolLoader()

        nonexistent_dir = tmp_path / "nonexistent"

        with pytest.raises(ToolLoaderError) as exc_info:
            loader.load_tool_from_directory(nonexistent_dir)

        assert "does not exist" in str(exc_info.value)

    def test_load_tool_from_directory_not_directory(self, tmp_path):
        """Test loading from path that's not a directory."""
        loader = ToolLoader()

        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        with pytest.raises(ToolLoaderError) as exc_info:
            loader.load_tool_from_directory(file_path)

        assert "not a directory" in str(exc_info.value)

    def test_load_tool_from_directory_excludes_init(self, tmp_path):
        """Test that __init__.py is excluded."""
        loader = ToolLoader()

        # Create __init__.py
        init_file = tmp_path / "__init__.py"
        init_file.write_text("# Package init")

        # Create a tool file
        tool_file = tmp_path / "tool.py"
        tool_file.write_text("""
from nodupe.core.tool_system.base import Tool

class TestTool(Tool):
    name = "TestTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Test tool"
""")

        loaded_tools = loader.load_tool_from_directory(tmp_path)

        assert len(loaded_tools) == 1
        assert loaded_tools[0].__name__ == "TestTool"

    def test_load_tool_from_directory_continues_on_error(self, tmp_path):
        """Test that loading continues even if one tool fails."""
        loader = ToolLoader()

        # Create a valid tool
        tool_file1 = tmp_path / "valid_tool.py"
        tool_file1.write_text("""
from nodupe.core.tool_system.base import Tool

class ValidTool(Tool):
    name = "ValidTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Valid tool"
""")

        # Create an invalid tool (no Tool subclass)
        invalid_file = tmp_path / "invalid_tool.py"
        invalid_file.write_text("# Not a tool")

        loaded_tools = loader.load_tool_from_directory(tmp_path)

        assert len(loaded_tools) == 1
        assert loaded_tools[0].__name__ == "ValidTool"

    def test_load_tool_from_directory_recursive(self, tmp_path):
        """Test loading tools recursively from subdirectories."""
        loader = ToolLoader()

        # Create subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        # Create tool in subdirectory
        tool_file = subdir / "subdir_tool.py"
        tool_file.write_text("""
from nodupe.core.tool_system.base import Tool

class SubdirTool(Tool):
    name = "SubdirTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Subdir tool"
""")

        # Non-recursive should not find the tool
        loaded_tools = loader.load_tool_from_directory(tmp_path, recursive=False)
        assert len(loaded_tools) == 0

        # Recursive should find the tool
        loaded_tools = loader.load_tool_from_directory(tmp_path, recursive=True)
        assert len(loaded_tools) == 1
        assert loaded_tools[0].__name__ == "SubdirTool"


class TestLoadToolByName:
    """Test load_tool_by_name method."""

    def test_load_tool_by_name_found(self, tmp_path):
        """Test loading tool by name when found."""
        loader = ToolLoader()

        # Create tool file
        tool_file = tmp_path / "mytool.py"
        tool_file.write_text("""
from nodupe.core.tool_system.base import Tool

class MyTool(Tool):
    name = "MyTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "My tool"
""")

        tool_class = loader.load_tool_by_name("mytool", [tmp_path])

        assert tool_class is not None
        assert tool_class.__name__ == "MyTool"

    def test_load_tool_by_name_not_found(self, tmp_path):
        """Test loading tool by name when not found."""
        loader = ToolLoader()

        tool_class = loader.load_tool_by_name("nonexistent", [tmp_path])

        assert tool_class is None

    def test_load_tool_by_name_from_subdir(self, tmp_path):
        """Test loading tool from subdirectory with __init__.py."""
        loader = ToolLoader()

        # Create tool subdirectory
        tool_subdir = tmp_path / "mytool"
        tool_subdir.mkdir()

        init_file = tool_subdir / "__init__.py"
        init_file.write_text("""
from nodupe.core.tool_system.base import Tool

class MyTool(Tool):
    name = "MyTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "My tool"
""")

        tool_class = loader.load_tool_by_name("mytool", [tmp_path])

        assert tool_class is not None
        assert tool_class.__name__ == "MyTool"

    def test_load_tool_by_name_multiple_dirs(self, tmp_path):
        """Test loading tool by name from multiple directories."""
        loader = ToolLoader()

        # Create tool in second directory
        dir2 = tmp_path / "dir2"
        dir2.mkdir()

        tool_file = dir2 / "mytool.py"
        tool_file.write_text("""
from nodupe.core.tool_system.base import Tool

class MyTool(Tool):
    name = "MyTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "My tool"
""")

        # First directory is empty
        dir1 = tmp_path / "dir1"
        dir1.mkdir()

        tool_class = loader.load_tool_by_name("mytool", [dir1, dir2])

        assert tool_class is not None


class TestInstantiateTool:
    """Test instantiate_tool method."""

    def test_instantiate_tool_success(self):
        """Test successfully instantiating a tool."""
        loader = ToolLoader()

        instance = loader.instantiate_tool(MockTool)

        assert isinstance(instance, MockTool)
        assert instance.name == "MockTool"

    def test_instantiate_tool_with_args(self):
        """Test instantiating tool with arguments."""
        loader = ToolLoader()

        instance = loader.instantiate_tool(MockTool, "CustomName", "2.0.0", ["dep1"])

        assert isinstance(instance, MockTool)
        assert instance.name == "CustomName"
        assert instance.version == "2.0.0"
        assert instance.dependencies == ["dep1"]

    def test_instantiate_tool_with_kwargs(self):
        """Test instantiating tool with keyword arguments."""
        loader = ToolLoader()

        instance = loader.instantiate_tool(MockTool, name="KwargsTool", version="3.0.0")

        assert isinstance(instance, MockTool)
        assert instance.name == "KwargsTool"
        assert instance.version == "3.0.0"

    def test_instantiate_tool_failure(self):
        """Test instantiating tool that fails."""
        loader = ToolLoader()

        class FailingTool:
            """Tool that fails on instantiation."""
            def __init__(self):
                """Initialize failing tool."""
                raise Exception("Instantiation failed")

        with pytest.raises(ToolLoaderError) as exc_info:
            loader.instantiate_tool(FailingTool)

        assert "Failed to instantiate" in str(exc_info.value)


class TestRegisterLoadedTool:
    """Test register_loaded_tool method."""

    def test_register_loaded_tool_success(self):
        """Test successfully registering a loaded tool."""
        loader = ToolLoader()
        tool = MockTool()

        loader.register_loaded_tool(tool)

        assert loader.registry.get_tool("MockTool") is tool

    def test_register_loaded_tool_with_path(self, tmp_path):
        """Test registering tool with path."""
        # Reset registry first
        ToolRegistry._reset_instance()

        loader = ToolLoader()
        tool = MockTool(name="UniqueToolWithPath")
        tool_path = tmp_path / "tool.py"

        loader.register_loaded_tool(tool, tool_path)

        assert loader.registry.get_tool("UniqueToolWithPath") is tool

    def test_register_loaded_tool_failure(self):
        """Test registering tool that fails."""
        loader = ToolLoader()
        tool = MockTool()

        # Mock registry to raise exception
        loader.registry.register = MagicMock(side_effect=Exception("Registration failed"))

        with pytest.raises(ToolLoaderError) as exc_info:
            loader.register_loaded_tool(tool)

        assert "Failed to register" in str(exc_info.value)


class TestUnloadTool:
    """Test unload_tool method."""

    def test_unload_tool_by_name(self):
        """Test unloading tool by name."""
        loader = ToolLoader()
        tool = MockTool()
        loader.load_tool(tool)

        result = loader.unload_tool("MockTool")

        assert result is True
        assert "MockTool" not in loader._loaded_tools

    def test_unload_tool_by_instance(self):
        """Test unloading tool by instance."""
        loader = ToolLoader()
        tool = MockTool()
        loader.load_tool(tool)

        result = loader.unload_tool(tool)

        assert result is True
        assert "MockTool" not in loader._loaded_tools

    def test_unload_tool_not_found(self):
        """Test unloading nonexistent tool."""
        loader = ToolLoader()

        result = loader.unload_tool("nonexistent")

        assert result is False

    def test_unload_tool_shutdown_error(self):
        """Test unloading tool that fails on shutdown."""
        loader = ToolLoader()

        class FailingShutdownTool(Tool):
            """Tool that fails on shutdown."""

            @property
            def name(self):
                """Get tool name."""
                return "FailingTool"

            @property
            def version(self):
                """Get tool version."""
                return "1.0.0"

            @property
            def dependencies(self):
                """Get tool dependencies."""
                return []

            def initialize(self, container):
                """Initialize the tool."""
                pass

            def shutdown(self):
                """Shutdown the tool."""
                raise Exception("Shutdown failed")

            def get_capabilities(self):
                """Get tool capabilities."""
                return {}

            @property
            def api_methods(self):
                """Get API methods."""
                return {}

            def run_standalone(self, args):
                """Run standalone."""
                return 0

            def describe_usage(self):
                """Describe usage."""
                return "Failing tool"

        tool = FailingShutdownTool()
        loader.load_tool(tool)

        # Should not raise, just print warning
        result = loader.unload_tool("FailingTool")

        assert result is True

    def test_unload_tool_removes_from_registry(self):
        """Test that unloading removes from registry."""
        # Reset registry first
        ToolRegistry._reset_instance()

        loader = ToolLoader()
        tool = MockTool(name="UnloadTestTool")
        loader.load_tool(tool)
        # Tool is already registered by load_tool, don't call register_loaded_tool again

        loader.unload_tool("UnloadTestTool")

        assert loader.registry.get_tool("UnloadTestTool") is None

    def test_unload_tool_removes_from_sys_modules(self):
        """Test that unloading removes from sys.modules."""
        loader = ToolLoader()
        tool = MockTool()
        tool.__module__ = "test_module_xyz"
        sys.modules["test_module_xyz"] = MagicMock()

        loader._loaded_tools["MockTool"] = tool

        loader.unload_tool("MockTool")

        assert "test_module_xyz" not in sys.modules


class TestGetLoadedTool:
    """Test get_loaded_tool method."""

    def test_get_loaded_tool_exists(self):
        """Test getting loaded tool that exists."""
        loader = ToolLoader()
        tool = MockTool()
        loader.load_tool(tool)

        result = loader.get_loaded_tool("MockTool")

        assert result is tool

    def test_get_loaded_tool_not_exists(self):
        """Test getting loaded tool that doesn't exist."""
        loader = ToolLoader()

        result = loader.get_loaded_tool("nonexistent")

        assert result is None


class TestGetAllLoadedTools:
    """Test get_all_loaded_tools method."""

    def test_get_all_loaded_tools_empty(self):
        """Test getting all loaded tools when empty."""
        loader = ToolLoader()

        result = loader.get_all_loaded_tools()

        assert result == {}

    def test_get_all_loaded_tools_with_tools(self):
        """Test getting all loaded tools."""
        loader = ToolLoader()
        tool1 = MockTool(name="Tool1")
        tool2 = MockTool(name="Tool2")
        loader.load_tool(tool1)
        loader.load_tool(tool2)

        result = loader.get_all_loaded_tools()

        assert len(result) == 2
        assert "Tool1" in result
        assert "Tool2" in result

    def test_get_all_loaded_tools_returns_copy(self):
        """Test that get_all_loaded_tools returns a copy."""
        loader = ToolLoader()
        tool = MockTool()
        loader.load_tool(tool)

        result = loader.get_all_loaded_tools()
        result["NewTool"] = MagicMock()

        assert "NewTool" not in loader._loaded_tools


class TestFindToolClass:
    """Test _find_tool_class method."""

    def test_find_tool_class_found(self, tmp_path):
        """Test finding tool class in module."""
        loader = ToolLoader()

        tool_file = tmp_path / "test_tool.py"
        tool_file.write_text("""
from nodupe.core.tool_system.base import Tool

class FoundTool(Tool):
    name = "FoundTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Found tool"

# Some other class
class NotATool:
    pass
""")

        module = loader.load_tool_from_file(tool_file)
        # Get the actual module from _tool_modules
        module_name = [k for k in loader._tool_modules.keys() if k == "FoundTool"][0]
        module = loader._tool_modules[module_name]

        tool_class = loader._find_tool_class(module)

        assert tool_class is not None
        assert tool_class.__name__ == "FoundTool"

    def test_find_tool_class_not_found(self, tmp_path):
        """Test finding tool class when not present."""
        loader = ToolLoader()

        # Create module without Tool subclass
        no_tool_file = tmp_path / "no_tool.py"
        no_tool_file.write_text("""
# Just a regular module
def some_function():
    return 42
""")

        spec = __import__('importlib.util').util.spec_from_file_location("no_tool", no_tool_file)
        module = __import__('importlib.util').util.module_from_spec(spec)
        spec.loader.exec_module(module)

        tool_class = loader._find_tool_class(module)

        assert tool_class is None

    def test_find_tool_class_excludes_base_tool(self, tmp_path):
        """Test that base Tool class is excluded."""
        loader = ToolLoader()

        # Create module with only base Tool import
        base_only_file = tmp_path / "base_only.py"
        base_only_file.write_text("""
from nodupe.core.tool_system.base import Tool

# Only import, no subclass
""")

        spec = __import__('importlib.util').util.spec_from_file_location("base_only", base_only_file)
        module = __import__('importlib.util').util.module_from_spec(spec)
        spec.loader.exec_module(module)

        tool_class = loader._find_tool_class(module)

        assert tool_class is None


class TestValidateToolClass:
    """Test _validate_tool_class method."""

    def test_validate_tool_class_valid(self, tmp_path):
        """Test validating valid tool class."""
        loader = ToolLoader()

        tool_file = tmp_path / "valid_tool.py"
        tool_file.write_text("""
from nodupe.core.tool_system.base import Tool

class ValidTool(Tool):
    name = "ValidTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Valid tool"
""")

        tool_class = loader.load_tool_from_file(tool_file)

        is_valid = loader._validate_tool_class(tool_class)

        assert is_valid is True

    def test_validate_tool_class_no_name(self, tmp_path):
        """Test validating tool class without name."""
        loader = ToolLoader()

        # Create a mock tool class without name
        class NoNameTool(Tool):
            """Tool without name attribute."""
            version = "1.0.0"
            dependencies = []

            def initialize(self, container):
                """Initialize the tool."""
                pass

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get capabilities."""
                return {}

            @property
            def api_methods(self):
                """Get API methods."""
                return {}

            def run_standalone(self, args):
                """Run standalone."""
                return 0

            def describe_usage(self):
                """Describe usage."""
                return "No name tool"

        is_valid = loader._validate_tool_class(NoNameTool)

        assert is_valid is False

    def test_validate_tool_class_empty_name(self, tmp_path):
        """Test validating tool class with empty name."""
        loader = ToolLoader()

        class EmptyNameTool(Tool):
            """Tool with empty name."""
            name = ""
            version = "1.0.0"
            dependencies = []

            def initialize(self, container):
                """Initialize the tool."""
                pass

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get capabilities."""
                return {}

            @property
            def api_methods(self):
                """Get API methods."""
                return {}

            def run_standalone(self, args):
                """Run standalone."""
                return 0

            def describe_usage(self):
                """Describe usage."""
                return "Empty name tool"

        is_valid = loader._validate_tool_class(EmptyNameTool)

        assert is_valid is False

    def test_validate_tool_class_whitespace_name(self, tmp_path):
        """Test validating tool class with whitespace-only name."""
        loader = ToolLoader()

        class WhitespaceNameTool(Tool):
            """Tool with whitespace name."""
            name = "   "
            version = "1.0.0"
            dependencies = []

            def initialize(self, container):
                """Initialize the tool."""
                pass

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get capabilities."""
                return {}

            @property
            def api_methods(self):
                """Get API methods."""
                return {}

            def run_standalone(self, args):
                """Run standalone."""
                return 0

            def describe_usage(self):
                """Describe usage."""
                return "Whitespace name tool"

        is_valid = loader._validate_tool_class(WhitespaceNameTool)

        assert is_valid is False

    def test_validate_tool_class_property_name(self, tmp_path):
        """Test validating tool class with property name."""
        loader = ToolLoader()

        tool_file = tmp_path / "property_name.py"
        tool_file.write_text("""
from nodupe.core.tool_system.base import Tool

class PropertyNameTool(Tool):
    _name = "PropertyNameTool"

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return "1.0.0"

    @property
    def dependencies(self):
        return []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Property name tool"
""")

        tool_class = loader.load_tool_from_file(tool_file)

        is_valid = loader._validate_tool_class(tool_class)

        assert is_valid is True

    def test_validate_tool_class_exception(self, tmp_path):
        """Test validating tool class that raises exception."""
        loader = ToolLoader()

        class ExceptionNameTool(Tool):
            """Tool whose name property raises exception."""

            @property
            def name(self):
                """Get name - raises exception."""
                raise Exception("Name error")

            @property
            def version(self):
                """Get version."""
                return "1.0.0"

            @property
            def dependencies(self):
                """Get dependencies."""
                return []

            def initialize(self, container):
                """Initialize the tool."""
                pass

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get capabilities."""
                return {}

            @property
            def api_methods(self):
                """Get API methods."""
                return {}

            def run_standalone(self, args):
                """Run standalone."""
                return 0

            def describe_usage(self):
                """Describe usage."""
                return "Exception name tool"

        is_valid = loader._validate_tool_class(ExceptionNameTool)

        assert is_valid is False


class TestToolLoaderEdgeCases:
    """Test edge cases in tool loading."""

    def test_load_tool_from_file_with_syntax_error(self, tmp_path):
        """Test loading file with syntax error."""
        loader = ToolLoader()

        bad_file = tmp_path / "bad_syntax.py"
        bad_file.write_text("def broken(")

        with pytest.raises(ToolLoaderError) as exc_info:
            loader.load_tool_from_file(bad_file)

        assert "Failed to load tool" in str(exc_info.value)

    def test_load_tool_from_file_with_import_error(self, tmp_path):
        """Test loading file with import error."""
        loader = ToolLoader()

        import_error_file = tmp_path / "import_error.py"
        import_error_file.write_text("""
import nonexistent_module_xyz

from nodupe.core.tool_system.base import Tool

class ImportErrorTool(Tool):
    name = "ImportErrorTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Import error tool"
""")

        with pytest.raises(ToolLoaderError):
            loader.load_tool_from_file(import_error_file)

    def test_multiple_tools_same_directory(self, tmp_path):
        """Test loading multiple tools from same directory."""
        loader = ToolLoader()

        # Create multiple tool files
        for i in range(5):
            tool_file = tmp_path / f"tool_{i}.py"
            tool_file.write_text(f"""
from nodupe.core.tool_system.base import Tool

class Tool{i}(Tool):
    name = "Tool{i}"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {{}}

    @property
    def api_methods(self):
        return {{}}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Tool {i}"
""")

        loaded_tools = loader.load_tool_from_directory(tmp_path)

        assert len(loaded_tools) == 5
        tool_names = [t.__name__ for t in loaded_tools]
        for i in range(5):
            assert f"Tool{i}" in tool_names

    def test_load_and_unload_cycle(self):
        """Test load/unload cycle."""
        loader = ToolLoader()
        tool = MockTool()

        # Load
        loader.load_tool(tool)
        assert "MockTool" in loader._loaded_tools

        # Unload
        loader.unload_tool("MockTool")
        assert "MockTool" not in loader._loaded_tools

        # Load again
        tool2 = MockTool()
        loader.load_tool(tool2)
        assert "MockTool" in loader._loaded_tools

    def test_load_tool_with_special_characters_in_path(self, tmp_path):
        """Test loading tool with special characters in path."""
        loader = ToolLoader()

        # Create directory with special characters
        special_dir = tmp_path / "tool-dir_test"
        special_dir.mkdir()

        tool_file = special_dir / "tool.py"
        tool_file.write_text("""
from nodupe.core.tool_system.base import Tool

class SpecialPathTool(Tool):
    name = "SpecialPathTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Special path tool"
""")

        tool_class = loader.load_tool_from_file(tool_file)

        assert tool_class is not None


class TestLoaderCoverageGaps:
    """Additional tests to cover remaining lines in loader.py."""

    def test_load_tool_from_file_spec_none(self, tmp_path):
        """Test load_tool_from_file when spec is None."""
        loader = ToolLoader()

        tool_file = tmp_path / "test.py"
        tool_file.write_text("# Test")

        # Mock spec_from_file_location to return None
        with patch('importlib.util.spec_from_file_location', return_value=None):
            with pytest.raises(ToolLoaderError) as exc_info:
                loader.load_tool_from_file(tool_file)

            assert "Could not create module spec" in str(exc_info.value)

    def test_load_tool_from_file_spec_loader_none(self, tmp_path):
        """Test load_tool_from_file when spec.loader is None."""
        loader = ToolLoader()

        tool_file = tmp_path / "test.py"
        tool_file.write_text("# Test")

        # Mock spec to have None loader
        mock_spec = MagicMock()
        mock_spec.loader = None
        with patch('importlib.util.spec_from_file_location', return_value=mock_spec):
            with pytest.raises(ToolLoaderError) as exc_info:
                loader.load_tool_from_file(tool_file)

            assert "Could not create module spec" in str(exc_info.value)

    def test_load_tool_from_directory_non_recursive(self, tmp_path):
        """Test load_tool_from_directory with recursive=False."""
        loader = ToolLoader()

        # Create subdirectory with tool
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        tool_file = subdir / "tool.py"
        tool_file.write_text("""
from nodupe.core.tool_system.base import Tool

class SubTool(Tool):
    name = "SubTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Sub tool"
""")

        # Non-recursive should not find the tool
        loaded_tools = loader.load_tool_from_directory(tmp_path, recursive=False)
        assert len(loaded_tools) == 0

    def test_load_tool_from_directory_exception_handling(self, tmp_path):
        """Test load_tool_from_directory exception handling."""
        loader = ToolLoader()

        # Mock glob to raise exception
        with patch.object(Path, 'glob', side_effect=Exception("Glob error")):
            with pytest.raises(ToolLoaderError) as exc_info:
                loader.load_tool_from_directory(tmp_path)

            assert "Failed to load tools" in str(exc_info.value)

    def test_validate_tool_class_property_name_exception(self):
        """Test _validate_tool_class when property getter raises exception."""
        loader = ToolLoader()

        class PropertyExceptionTool(Tool):
            """Tool with property that raises exception."""

            @property
            def name(self):
                """Get name - raises exception."""
                raise Exception("Property error")

            @property
            def version(self):
                """Get version."""
                return "1.0.0"

            @property
            def dependencies(self):
                """Get dependencies."""
                return []

            def initialize(self, container):
                """Initialize the tool."""
                pass

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get capabilities."""
                return {}

            @property
            def api_methods(self):
                """Get API methods."""
                return {}

            def run_standalone(self, args):
                """Run standalone."""
                return 0

            def describe_usage(self):
                """Describe usage."""
                return ""

        result = loader._validate_tool_class(PropertyExceptionTool)
        assert result is False

    def test_find_tool_class_with_multiple_attrs(self, tmp_path):
        """Test _find_tool_class with multiple attributes."""
        loader = ToolLoader()

        # Create a module with multiple classes
        tool_file = tmp_path / "multi.py"
        tool_file.write_text("""
from nodupe.core.tool_system.base import Tool

class NotATool:
    pass

class MyTool(Tool):
    name = "MyTool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return ""

def not_a_class():
    pass
""")

        # Load the module
        import importlib.util
        spec = importlib.util.spec_from_file_location("multi", tool_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        tool_class = loader._find_tool_class(module)
        assert tool_class is not None
        assert tool_class.__name__ == "MyTool"
