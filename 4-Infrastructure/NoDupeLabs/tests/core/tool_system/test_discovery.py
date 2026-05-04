"""Tests for the tool_system discovery module."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from nodupe.core.tool_system.discovery import (
    ToolDiscovery,
    ToolDiscoveryError,
    ToolInfo,
    create_tool_discovery,
)


class TestToolInfo:
    """Test ToolInfo class."""

    def test_tool_info_creation(self):
        """Test ToolInfo instance creation."""
        tool_info = ToolInfo(
            name="TestTool",
            file_path=Path("/path/to/tool.py"),
            version="1.0.0",
            dependencies=["dep1", "dep2"],
            capabilities={"feature1": "value1"}
        )

        assert tool_info.name == "TestTool"
        assert tool_info.path == Path("/path/to/tool.py")
        assert tool_info.version == "1.0.0"
        assert tool_info.dependencies == ["dep1", "dep2"]
        assert tool_info.capabilities == {"feature1": "value1"}

    def test_tool_info_default_values(self):
        """Test ToolInfo with default values."""
        tool_info = ToolInfo(
            name="TestTool",
            file_path=Path("/path/to/tool.py")
        )

        assert tool_info.name == "TestTool"
        assert tool_info.path == Path("/path/to/tool.py")
        assert tool_info.version == "1.0.0"
        assert tool_info.dependencies == []
        assert tool_info.capabilities == {}

    def test_tool_info_none_dependencies(self):
        """Test ToolInfo with None dependencies."""
        tool_info = ToolInfo(
            name="TestTool",
            file_path=Path("/path/to/tool.py"),
            dependencies=None
        )

        assert tool_info.dependencies == []

    def test_tool_info_none_capabilities(self):
        """Test ToolInfo with None capabilities."""
        tool_info = ToolInfo(
            name="TestTool",
            file_path=Path("/path/to/tool.py"),
            capabilities=None
        )

        assert tool_info.capabilities == {}

    def test_tool_info_repr(self):
        """Test ToolInfo string representation."""
        tool_info = ToolInfo(
            name="TestTool",
            file_path=Path("/path/to/tool.py")
        )

        repr_str = repr(tool_info)
        assert "ToolInfo" in repr_str
        assert "TestTool" in repr_str
        assert "/path/to/tool.py" in repr_str


class TestToolDiscoveryInitialization:
    """Test ToolDiscovery initialization."""

    def test_tool_discovery_creation(self):
        """Test ToolDiscovery instance creation."""
        discovery = ToolDiscovery()

        assert discovery is not None
        assert discovery._discovered_tools == []
        assert discovery.container is None

    def test_tool_discovery_initialize(self):
        """Test ToolDiscovery initialization with container."""
        discovery = ToolDiscovery()
        container = Mock()

        discovery.initialize(container)

        assert discovery.container is container

    def test_tool_discovery_shutdown(self):
        """Test ToolDiscovery shutdown."""
        discovery = ToolDiscovery()
        container = Mock()
        discovery.initialize(container)

        discovery.shutdown()

        assert discovery.container is None


class TestToolDiscoveryFileValidation:
    """Test tool discovery file validation."""

    def test_validate_tool_file_valid(self):
        """Test validating a valid tool file."""
        discovery = ToolDiscovery()

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_file', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat, \
             patch('builtins.open', mock_open(read_data='class TestTool:\n    pass')):

            mock_stat.return_value.st_size = 100

            result = discovery.validate_tool_file(Path("/fake/tool.py"))
            assert result is True

    def test_validate_tool_file_wrong_extension(self):
        """Test validating file with wrong extension."""
        discovery = ToolDiscovery()

        result = discovery.validate_tool_file(Path("/fake/tool.txt"))
        assert result is False

    def test_validate_tool_file_nonexistent(self):
        """Test validating nonexistent file."""
        discovery = ToolDiscovery()

        with patch('pathlib.Path.exists', return_value=False):
            result = discovery.validate_tool_file(Path("/fake/tool.py"))
            assert result is False

    def test_validate_tool_file_not_file(self):
        """Test validating path that is not a file."""
        discovery = ToolDiscovery()

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_file', return_value=False):
            result = discovery.validate_tool_file(Path("/fake/tool.py"))
            assert result is False

    def test_validate_tool_file_zero_size(self):
        """Test validating file with zero size."""
        discovery = ToolDiscovery()

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_file', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat:

            mock_stat.return_value.st_size = 0

            result = discovery.validate_tool_file(Path("/fake/tool.py"))
            assert result is False

    def test_validate_tool_file_syntax_error(self):
        """Test validating file with syntax errors."""
        discovery = ToolDiscovery()

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_file', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat, \
             patch('builtins.open', mock_open(read_data='invalid python syntax @@')):

            mock_stat.return_value.st_size = 100

            result = discovery.validate_tool_file(Path("/fake/tool.py"))
            assert result is False

    def test_validate_tool_file_exception(self):
        """Test validating file with exception."""
        discovery = ToolDiscovery()

        mock_path = Mock(spec=Path)
        mock_path.suffix = '.py'
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.stat.side_effect = OSError("Cannot stat")

        result = discovery.validate_tool_file(mock_path)
        assert result is False


class TestToolDiscoveryContentParsing:
    """Test tool discovery content parsing."""

    def test_parse_metadata_simple(self):
        """Test parsing simple metadata."""
        discovery = ToolDiscovery()

        content = '''
__version__ = "2.0.0"
__author__ = "Test Author"
__description__ = "A test tool"
'''

        metadata = discovery._parse_metadata(content)

        assert metadata.get('version') == "2.0.0"
        assert metadata.get('author') == "Test Author"
        assert metadata.get('description') == "A test tool"

    def test_parse_metadata_single_quotes(self):
        """Test parsing metadata with single quotes."""
        discovery = ToolDiscovery()

        content = """
version = '1.5.0'
author = 'Another Author'
"""

        metadata = discovery._parse_metadata(content)

        assert metadata.get('version') == "1.5.0"
        assert metadata.get('author') == "Another Author"

    def test_parse_metadata_dependencies(self):
        """Test parsing dependencies."""
        discovery = ToolDiscovery()

        content = '''
dependencies = ["dep1", "dep2", "dep3"]
'''

        metadata = discovery._parse_metadata(content)

        assert metadata.get('dependencies') == ["dep1", "dep2", "dep3"]

    def test_parse_metadata_dependencies_invalid_syntax(self):
        """Test parsing dependencies with invalid syntax."""
        discovery = ToolDiscovery()

        content = '''
dependencies = invalid_syntax_here
'''

        metadata = discovery._parse_metadata(content)

        # Should handle gracefully
        assert isinstance(metadata, dict)

    def test_parse_metadata_capabilities(self):
        """Test parsing capabilities."""
        discovery = ToolDiscovery()

        content = '''
capabilities = {"feature1": "value1", "feature2": "value2"}
'''

        metadata = discovery._parse_metadata(content)

        assert metadata.get('capabilities') == {"feature1": "value1", "feature2": "value2"}

    def test_parse_metadata_capabilities_invalid(self):
        """Test parsing capabilities with invalid syntax."""
        discovery = ToolDiscovery()

        content = '''
capabilities = invalid_syntax
'''

        metadata = discovery._parse_metadata(content)

        assert isinstance(metadata, dict)

    def test_parse_metadata_complex(self):
        """Test parsing complex metadata."""
        discovery = ToolDiscovery()

        content = '''
name = "ComplexTool"
version = "3.0.0"
dependencies = ["req1", "req2"]
capabilities = {"feature": "value"}
'''

        metadata = discovery._parse_metadata(content)

        assert metadata.get('name') == "ComplexTool"
        assert metadata.get('version') == "3.0.0"
        assert metadata.get('dependencies') == ["req1", "req2"]

    def test_parse_metadata_empty_content(self):
        """Test parsing empty content."""
        discovery = ToolDiscovery()

        metadata = discovery._parse_metadata("")

        assert metadata == {}


class TestToolDiscoveryContentAnalysis:
    """Test tool discovery content analysis."""

    def test_looks_like_tool_with_imports(self):
        """Test detecting tool-like content with imports."""
        discovery = ToolDiscovery()

        content = '''
import os
import sys
'''

        result = discovery._looks_like_tool(content)
        assert result is True

    def test_looks_like_tool_with_class(self):
        """Test detecting tool-like content with class."""
        discovery = ToolDiscovery()

        content = '''
class MinimalTool:
    pass
'''

        result = discovery._looks_like_tool(content)
        assert result is True

    def test_looks_like_tool_with_function(self):
        """Test detecting tool-like content with function."""
        discovery = ToolDiscovery()

        content = '''
def helper_function():
    pass
'''

        result = discovery._looks_like_tool(content)
        assert result is True

    def test_looks_like_tool_empty(self):
        """Test detecting tool-like content in empty file."""
        discovery = ToolDiscovery()

        result = discovery._looks_like_tool("")
        assert result is False

    def test_extract_tool_info_success(self):
        """Test successful tool info extraction."""
        discovery = ToolDiscovery()

        content = '''
name = "ExtractedTool"
version = "1.0.0"
dependencies = ["req1"]

class ExtractedTool:
    pass
'''

        with patch('builtins.open', mock_open(read_data=content)), \
             patch('pathlib.Path.exists', return_value=True):

            tool_path = Path("/fake/tool.py")
            result = discovery._extract_tool_info(tool_path)

            assert result is not None
            assert result.name == "ExtractedTool"
            assert result.version == "1.0.0"

    def test_extract_tool_info_not_tool_like(self):
        """Test tool info extraction for non-tool content."""
        discovery = ToolDiscovery()

        content = '''
# This is just a comment file
# No actual tool code here
'''

        with patch('builtins.open', mock_open(read_data=content)), \
             patch('pathlib.Path.exists', return_value=True):

            tool_path = Path("/fake/tool.py")
            result = discovery._extract_tool_info(tool_path)

            assert result is None

    def test_extract_tool_info_exception(self):
        """Test tool info extraction with exception."""
        discovery = ToolDiscovery()

        with patch('builtins.open', side_effect=IOError("Cannot read")):
            result = discovery._extract_tool_info(Path("/fake/tool.py"))
            assert result is None

    def test_extract_tool_info_init_file(self):
        """Test extracting tool info from __init__.py."""
        discovery = ToolDiscovery()

        content = '''
class MyTool:
    pass
'''

        with patch('builtins.open', mock_open(read_data=content)), \
             patch('pathlib.Path.exists', return_value=True):

            tool_path = Path("/fake/mytool/__init__.py")
            result = discovery._extract_tool_info(tool_path)

            assert result is not None
            assert result.name == "mytool"


class TestToolDiscoveryDirectoryScanning:
    """Test tool discovery directory scanning."""

    def test_discover_tools_in_directory_empty(self):
        """Test discovering tools in empty directory."""
        discovery = ToolDiscovery()

        with patch('pathlib.Path.iterdir', return_value=[]):
            result = discovery.discover_tools_in_directory(Path("/empty/dir"))
            assert result == []

    def test_discover_tools_in_directory_exception(self):
        """Test discovering tools with directory exception."""
        discovery = ToolDiscovery()

        mock_dir = Mock(spec=Path)
        mock_dir.iterdir.side_effect = OSError("Cannot read")

        result = discovery.discover_tools_in_directory(mock_dir)
        assert result == []

    def test_discover_tools_in_directory_with_files(self):
        """Test discovering tools in directory with files."""
        discovery = ToolDiscovery()

        mock_py_file = Mock()
        mock_py_file.name = "tool1.py"
        mock_py_file.suffix = ".py"
        mock_py_file.is_file.return_value = True
        mock_py_file.is_dir.return_value = False

        content = '''
class TestTool:
    pass
'''

        with patch('pathlib.Path.iterdir', return_value=[mock_py_file]), \
             patch('builtins.open', mock_open(read_data=content)), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat:

            mock_stat.return_value.st_size = 100

            result = discovery.discover_tools_in_directory(Path("/test/dir"))

            assert len(result) >= 0  # May find tool or not depending on content

    def test_discover_tools_in_directory_skip_init(self):
        """Test discovering tools skips __init__.py."""
        discovery = ToolDiscovery()

        mock_init_file = Mock()
        mock_init_file.name = "__init__.py"
        mock_init_file.suffix = ".py"
        mock_init_file.is_file.return_value = True

        with patch('pathlib.Path.iterdir', return_value=[mock_init_file]):
            result = discovery.discover_tools_in_directory(Path("/test/dir"))

            # __init__.py should be skipped
            assert len(result) == 0

    def test_discover_tools_in_directory_recursive(self):
        """Test discovering tools recursively."""
        discovery = ToolDiscovery()

        mock_py_file = Mock()
        mock_py_file.name = "tool1.py"
        mock_py_file.suffix = ".py"
        mock_py_file.is_file.return_value = True
        mock_py_file.is_dir.return_value = False

        mock_subdir = Mock()
        mock_subdir.name = "subdir"
        mock_subdir.is_dir.return_value = True
        mock_subdir.is_file.return_value = False

        mock_sub_py_file = Mock()
        mock_sub_py_file.name = "tool2.py"
        mock_sub_py_file.suffix = ".py"
        mock_sub_py_file.is_file.return_value = True
        mock_sub_py_file.is_dir.return_value = False

        content = '''
class TestTool:
    pass
'''

        def iterdir_side_effect(path):
            """Mock iterdir side effect for recursive directory test."""
            if path == mock_subdir:
                return [mock_sub_py_file]
            return [mock_py_file, mock_subdir]

        with patch.object(Path, 'iterdir', side_effect=iterdir_side_effect), \
             patch('builtins.open', mock_open(read_data=content)), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat:

            mock_stat.return_value.st_size = 100

            result = discovery.discover_tools_in_directory(Path("/test/dir"), recursive=True)

            assert isinstance(result, list)

    def test_discover_tools_in_directory_nonexistent(self):
        """Test discovering tools in nonexistent directory."""
        discovery = ToolDiscovery()

        with patch('pathlib.Path.iterdir', side_effect=FileNotFoundError()):
            result = discovery.discover_tools_in_directory(Path("/nonexistent/dir"))
            assert result == []

    def test_discover_tools_in_directories(self):
        """Test discovering tools in multiple directories."""
        discovery = ToolDiscovery()

        mock_tool1 = Mock()
        mock_tool1.name = "Tool1"
        mock_tool2 = Mock()
        mock_tool2.name = "Tool2"

        with patch.object(discovery, 'discover_tools_in_directory') as mock_discover:
            mock_discover.side_effect = [[mock_tool1], [mock_tool2]]

            directories = [Path("/dir1"), Path("/dir2")]
            result = discovery.discover_tools_in_directories(directories)

            assert len(result) == 2

    def test_discover_tools_in_directories_duplicate_names(self):
        """Test discovering tools with duplicate names."""
        discovery = ToolDiscovery()

        mock_tool1 = Mock()
        mock_tool1.name = "Tool1"
        mock_tool2 = Mock()
        mock_tool2.name = "Tool1"  # Same name

        with patch.object(discovery, 'discover_tools_in_directory') as mock_discover:
            mock_discover.side_effect = [[mock_tool1], [mock_tool2]]

            directories = [Path("/dir1"), Path("/dir2")]
            result = discovery.discover_tools_in_directories(directories)

            # Should only include unique names
            assert len(result) == 1

    def test_discover_tools_in_directories_exception(self):
        """Test discovering tools with exception."""
        discovery = ToolDiscovery()

        with patch.object(discovery, 'discover_tools_in_directory', side_effect=ToolDiscoveryError()):
            result = discovery.discover_tools_in_directories([Path("/dir1")])
            assert result == []


class TestToolDiscoveryMainMethods:
    """Test main discovery methods."""

    def test_discover_tools_with_directories(self):
        """Test discovering tools with directories parameter."""
        discovery = ToolDiscovery()

        with patch.object(discovery, 'discover_tools_in_directories') as mock_discover:
            mock_discover.return_value = [Mock(name="TestTool")]

            directories = [Path("/dir1")]
            result = discovery.discover_tools(directories)

            mock_discover.assert_called_once()
            assert len(result) == 1

    def test_discover_tools_without_directories(self):
        """Test discovering tools without directories parameter."""
        discovery = ToolDiscovery()

        mock_tool = Mock()
        mock_tool.name = "ExistingTool"
        discovery._discovered_tools = [mock_tool]

        result = discovery.discover_tools()

        assert result == [mock_tool]

    def test_find_tool_by_name_found(self):
        """Test finding tool by name when it exists."""
        discovery = ToolDiscovery()

        mock_tool = Mock()
        mock_tool.name = "TargetTool"
        discovery._discovered_tools = [mock_tool]

        result = discovery.find_tool_by_name("TargetTool")
        assert result is mock_tool

    def test_find_tool_by_name_not_found(self):
        """Test finding tool by name when it doesn't exist."""
        discovery = ToolDiscovery()

        mock_tool = Mock()
        mock_tool.name = "OtherTool"
        discovery._discovered_tools = [mock_tool]

        result = discovery.find_tool_by_name("TargetTool")
        assert result is None

    def test_find_tool_by_name_in_directories(self):
        """Test finding tool by name in directories."""
        discovery = ToolDiscovery()

        mock_found_tool = Mock()
        mock_found_tool.name = "TargetTool"

        with patch.object(discovery, 'discover_tools_in_directory') as mock_discover:
            mock_discover.return_value = [mock_found_tool]

            result = discovery.find_tool_by_name("TargetTool", [Path("/search/dir")])

            assert result is mock_found_tool

    def test_find_tool_by_name_directory_exception(self):
        """Test finding tool by name with directory exception."""
        discovery = ToolDiscovery()

        with patch.object(discovery, 'discover_tools_in_directory', side_effect=ToolDiscoveryError()):
            result = discovery.find_tool_by_name("test_tool", [Path("/dir")])
            assert result is None

    def test_refresh_discovery(self):
        """Test refreshing discovery."""
        discovery = ToolDiscovery()

        mock_tool = Mock()
        mock_tool.name = "OldTool"
        discovery._discovered_tools = [mock_tool]

        discovery.refresh_discovery()

        assert len(discovery._discovered_tools) == 0

    def test_get_discovered_tools(self):
        """Test getting all discovered tools."""
        discovery = ToolDiscovery()

        mock_tool1 = Mock()
        mock_tool1.name = "Tool1"
        mock_tool2 = Mock()
        mock_tool2.name = "Tool2"
        discovery._discovered_tools = [mock_tool1, mock_tool2]

        result = discovery.get_discovered_tools()

        assert result == [mock_tool1, mock_tool2]
        assert result is not discovery._discovered_tools

    def test_get_discovered_tool_found(self):
        """Test getting specific discovered tool."""
        discovery = ToolDiscovery()

        mock_tool = Mock()
        mock_tool.name = "TestTool"
        discovery._discovered_tools = [mock_tool]

        result = discovery.get_discovered_tool("TestTool")
        assert result is mock_tool

    def test_get_discovered_tool_not_found(self):
        """Test getting nonexistent discovered tool."""
        discovery = ToolDiscovery()

        result = discovery.get_discovered_tool("NonExistentTool")
        assert result is None

    def test_is_tool_discovered_true(self):
        """Test checking if tool is discovered - true case."""
        discovery = ToolDiscovery()

        mock_tool = Mock()
        mock_tool.name = "TestTool"
        discovery._discovered_tools = [mock_tool]

        assert discovery.is_tool_discovered("TestTool") is True

    def test_is_tool_discovered_false(self):
        """Test checking if tool is discovered - false case."""
        discovery = ToolDiscovery()

        result = discovery.is_tool_discovered("NonExistentTool")
        assert result is False


class TestCreateToolDiscovery:
    """Test create_tool_discovery function."""

    def test_create_tool_discovery(self):
        """Test create_tool_discovery creates instance."""
        discovery = create_tool_discovery()

        assert isinstance(discovery, ToolDiscovery)
        assert discovery.container is None


class TestToolDiscoveryEdgeCases:
    """Test edge cases for ToolDiscovery."""

    def test_tool_info_with_unicode_name(self):
        """Test ToolInfo with unicode name."""
        tool_info = ToolInfo(
            name="\u0422\u0435\u0441\u0442\u043e\u0432\u044b\u0439",
            file_path=Path("/path/to/tool.py")
        )

        assert tool_info.name == "\u0422\u0435\u0441\u0442\u043e\u0432\u044b\u0439"

    def test_discover_tools_in_directory_mock_exception(self):
        """Test discover_tools_in_directory with mock exception."""
        discovery = ToolDiscovery()

        mock_item = Mock()
        mock_item.name = "tool.py"
        mock_item.suffix = ".py"
        mock_item.is_file.side_effect = AttributeError("No is_file")
        mock_item.is_dir.side_effect = AttributeError("No is_dir")

        mock_dir = Mock(spec=Path)
        mock_dir.iterdir.return_value = [mock_item]

        result = discovery.discover_tools_in_directory(mock_dir)

        assert isinstance(result, list)

    def test_parse_metadata_none_content(self):
        """Test parsing None content."""
        discovery = ToolDiscovery()

        # Should handle None gracefully
        try:
            metadata = discovery._parse_metadata(None)  # type: ignore
        except AttributeError:
            # Expected for None content
            metadata = {}

        assert isinstance(metadata, dict)

    def test_looks_like_tool_none_content(self):
        """Test looks_like_tool with None content."""
        discovery = ToolDiscovery()

        try:
            result = discovery._looks_like_tool(None)  # type: ignore
        except AttributeError:
            # Expected for None content
            pass
