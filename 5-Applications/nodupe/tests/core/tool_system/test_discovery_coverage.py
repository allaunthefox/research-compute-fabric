"""Test tool discovery functionality.

This module tests the ToolDiscovery class which is responsible for finding,
validating, and parsing tool files in the filesystem.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from nodupe.core.tool_system.discovery import ToolDiscovery, ToolDiscoveryError, ToolInfo


class TestToolDiscovery(unittest.TestCase):
    """Tests for ToolDiscovery class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.discovery = ToolDiscovery()
        self.discovery.initialize(None)  # container not used yet

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
        self.discovery.shutdown()

    def create_file(self, path, content):
        """Create a test file with given content.

        Args:
            path: Relative path for the file.
            content: Content to write to the file.

        Returns:
            Path: Absolute path to the created file.
        """
        full_path = Path(self.test_dir) / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
        return full_path

    def test_discover_tools_in_directory_recursive(self):
        """Test discovering tools recursively in a directory."""
        # Create structure
        # root/
        #   tool_a.py
        #   subdir/
        #     tool_b.py
        #   ignored.txt
        #   __init__.py

        self.create_file("tool_a.py", """
__version__ = "1.0.0"
class ToolA:
    pass
""")
        self.create_file("subdir/tool_b.py", """
VERSION = '2.0.0'
def some_func():
    pass
""")
        self.create_file("ignored.txt", "not a python file")
        self.create_file("__init__.py", "")

        tools = self.discovery.discover_tools_in_directory(Path(self.test_dir))

        tool_names = {t.name for t in tools}
        self.assertIn("tool_a", tool_names)
        self.assertIn("tool_b", tool_names)
        self.assertNotIn("ignored", tool_names)
        self.assertNotIn("__init__", tool_names)

        # Verify metadata
        tool_a = next(t for t in tools if t.name == "tool_a")
        self.assertEqual(tool_a.version, "1.0.0")

    def test_metadata_parsing(self):
        """Test parsing metadata from tool files."""
        content = """
__name__ = "custom_name"
__version__ = "1.2.3"
dependencies = ['dep1', 'dep2']
capabilities = {'read': True}
class MyTool:
    pass
"""
        p = self.create_file("complex_tool.py", content)
        info = self.discovery._extract_tool_info(p)

        self.assertEqual(info.name, "custom_name")
        self.assertEqual(info.version, "1.2.3")
        self.assertEqual(info.dependencies, ['dep1', 'dep2'])
        self.assertEqual(info.capabilities, {'read': True})

    def test_metadata_parsing_variations(self):
        """Test parsing different metadata variations."""
        # Test distinct parsing branches
        content = """
VERSION = "3.3.3"
AUTHOR = 'John Doe'
DESCRIPTION = "A description"
TYPE = "utility"
# Comment line
class T: pass
"""
        p = self.create_file("vars.py", content)
        info = self.discovery._extract_tool_info(p)
        self.assertEqual(info.version, "3.3.3")

    def test_validate_tool_file(self):
        """Test validating tool files."""
        # Valid
        valid_p = self.create_file("valid.py", "class A: pass")
        self.assertTrue(self.discovery.validate_tool_file(valid_p))

        # Not a file (dir)
        dir_p = Path(self.test_dir) / "subdir"
        dir_p.mkdir()
        self.assertFalse(self.discovery.validate_tool_file(dir_p))

        # Wrong extension
        txt_p = self.create_file("test.txt", "content")
        self.assertFalse(self.discovery.validate_tool_file(txt_p))

        # Empty
        empty_p = self.create_file("empty.py", "")
        self.assertFalse(self.discovery.validate_tool_file(empty_p))

        # Syntax Error
        bad_p = self.create_file("bad.py", "class A: : :")
        self.assertFalse(self.discovery.validate_tool_file(bad_p))

        # Not tool-like (no class/def/import)
        not_tool_p = self.create_file("script.py", "x = 1")
        # _looks_like_tool logic: has import OR class OR def
        # x=1 has none
        self.assertFalse(self.discovery.validate_tool_file(not_tool_p))

    def test_find_tool_by_name(self):
        """Test finding tools by name."""
        self.create_file("target.py", "class Target: pass")

        # Pre-discovery find (using directories arg)
        found = self.discovery.find_tool_by_name("target", search_directories=[Path(self.test_dir)])
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "target")

        # Post-discovery find (from cache)
        self.discovery.discover_tools([Path(self.test_dir)])
        found_cache = self.discovery.find_tool_by_name("target")
        self.assertIsNotNone(found_cache)

        # Find tool as directory (package)
        pkg_dir = Path(self.test_dir) / "pkgtool"
        pkg_dir.mkdir()
        with open(pkg_dir / "__init__.py", "w") as f:
            f.write("class Pkg: pass")

        found_pkg = self.discovery.find_tool_by_name("pkgtool", search_directories=[Path(self.test_dir)])
        self.assertIsNotNone(found_pkg)
        self.assertEqual(found_pkg.name, "pkgtool")

    def test_accessibility_detection(self):
        """Test detection of accessibility features in tools."""
        # Matches logic in _extract_tool_info
        path = self.create_file("acc_tool.py", """
import accessible_base
class AccessTool(accessible_base.AccessibleTool):
    pass
""")
        with self.assertLogs(level='INFO') as cm:
            self.discovery._extract_tool_info(path)
            self.assertTrue(any("Discovered tool with accessibility features" in o for o in cm.output))

        path_no_acc = self.create_file("no_acc.py", "class Tool: pass")
        with self.assertLogs(level='INFO') as cm:
            self.discovery._extract_tool_info(path_no_acc)
            self.assertTrue(any("Discovered tool without accessibility features" in o for o in cm.output))

    def test_discovery_helpers(self):
        """Test helper methods for tool discovery."""
        self.create_file("t1.py", "class T1: pass")
        self.discovery.discover_tools([Path(self.test_dir)])

        self.assertTrue(self.discovery.is_tool_discovered("t1"))
        self.assertFalse(self.discovery.is_tool_discovered("t2"))

        self.assertIsNotNone(self.discovery.get_discovered_tool("t1"))
        self.assertIsNone(self.discovery.get_discovered_tool("t2"))

        self.discovery.refresh_discovery()
        self.assertEqual(len(self.discovery.get_discovered_tools()), 0)

    def test_exception_handling(self):
        """Test exception handling in tool discovery."""
        # discover_tools_in_directory handles OSError
        # We can simulate by passing a non-existent path
        res = self.discovery.discover_tools_in_directory(Path("/non/existent/path"))
        self.assertEqual(res, [])

    def test_parse_metadata_eval_errors(self):
        """Test handling of malformed metadata during parsing."""
        # Malformed list for dependencies should handle error gracefully
        content = """
dependencies = [malformed
class T: pass
"""
        metadata = self.discovery._parse_metadata(content)
        self.assertNotIn('dependencies', metadata)


# =============================================================================
# Additional Coverage Tests for discovery.py
# =============================================================================

class TestDiscoveryMissingCoverage(unittest.TestCase):
    """Additional tests to cover missing lines in discovery.py."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.discovery = ToolDiscovery()
        self.discovery.initialize(None)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
        self.discovery.shutdown()

    def create_file(self, path, content):
        """Create a test file with given content.

        Args:
            path: Relative path for the file.
            content: Content to write to the file.

        Returns:
            Path: Absolute path to the created file.
        """
        full_path = Path(self.test_dir) / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
        return full_path

    def test_tool_info_repr(self):
        """Test ToolInfo __repr__ method."""
        info = ToolInfo(
            name="test_tool",
            file_path=Path("/path/to/tool.py"),
            version="2.0.0"
        )
        repr_str = repr(info)
        self.assertIn("test_tool", repr_str)
        self.assertIn("2.0.0", repr_str)

    def test_tool_info_path_property(self):
        """Test ToolInfo path property."""
        path = Path("/path/to/tool.py")
        info = ToolInfo(name="test", file_path=path)
        self.assertEqual(info.path, path)

    def test_discover_tools_returns_cached_when_no_dirs(self):
        """Test discover_tools returns cached tools when directories is None."""
        self.create_file("cached.py", "class Cached: pass")
        self.discovery.discover_tools([Path(self.test_dir)])

        # Call with directories=None should return cached
        result = self.discovery.discover_tools(directories=None)
        self.assertEqual(len(result), 1)

    def test_discover_tools_in_directory_mock_handling(self):
        """Test discover_tools_in_directory handles mock objects."""
        # Create a mock that raises AttributeError on iterdir
        class MockDir:
            """Mock directory class for testing error handling.

            Simulates a directory that raises various exceptions when iterated.
            """

            def iterdir(self):
                """Raise AttributeError to simulate a directory without iterdir method."""
                raise AttributeError("Mock has no iterdir")

        result = self.discovery.discover_tools_in_directory(MockDir())
        self.assertEqual(result, [])

    def test_discover_tools_in_directory_permission_error(self):
        """Test discover_tools_in_directory handles PermissionError."""
        class MockDir:
            """Mock directory class for testing error handling.

            Simulates a directory that raises various exceptions when iterated.
            """

            def iterdir(self):
                """Raise PermissionError to simulate a permission denied directory."""
                raise PermissionError("No permission")

        result = self.discovery.discover_tools_in_directory(MockDir())
        self.assertEqual(result, [])

    def test_discover_tools_in_directory_file_not_found(self):
        """Test discover_tools_in_directory handles FileNotFoundError."""
        class MockDir:
            """Mock directory class for testing error handling.

            Simulates a directory that raises various exceptions when iterated.
            """

            def iterdir(self):
                """Raise FileNotFoundError to simulate a missing directory."""
                raise FileNotFoundError("Not found")

        result = self.discovery.discover_tools_in_directory(MockDir())
        self.assertEqual(result, [])

    def test_discover_tools_in_directory_os_error(self):
        """Test discover_tools_in_directory handles OSError."""
        class MockDir:
            """Mock directory class for testing error handling.

            Simulates a directory that raises various exceptions when iterated.
            """

            def iterdir(self):
                """Raise OSError to simulate a generic OS error."""
                raise OSError("OS error")

        result = self.discovery.discover_tools_in_directory(MockDir())
        self.assertEqual(result, [])

    def test_discover_tools_in_directory_item_is_file_attr_error(self):
        """Test handling when item.is_file() raises AttributeError."""
        class MockItem:
            """Mock item class for testing error handling.

            Simulates a file/directory item with various attribute access patterns.
            """

            suffix = '.py'
            name = 'test.py'

            def is_file(self):
                """Raise AttributeError to simulate an item without is_file method."""
                raise AttributeError("No is_file")

        class MockDir:
            """Mock directory class for testing error handling.

            Simulates a directory that raises various exceptions when iterated.
            """

            def iterdir(self):
                """Return a list containing a MockItem."""
                return [MockItem()]

        result = self.discovery.discover_tools_in_directory(MockDir())
        # Should handle gracefully and return something
        self.assertIsInstance(result, list)

    def test_discover_tools_in_directory_item_is_dir_attr_error(self):
        """Test handling when item.is_dir() raises AttributeError."""
        class MockItem:
            """Mock item class for testing error handling.

            Simulates a file/directory item with various attribute access patterns.
            """

            suffix = '.py'
            name = 'test.py'

            def is_file(self):
                """Return False to simulate a directory."""
                return False

            def is_dir(self):
                """Raise AttributeError to simulate an item without is_dir method."""
                raise AttributeError("No is_dir")

        class MockDir:
            """Mock directory class for testing error handling.

            Simulates a directory that raises various exceptions when iterated.
            """

            def iterdir(self):
                """Return a list containing a MockItem."""
                return [MockItem()]

        result = self.discovery.discover_tools_in_directory(MockDir(), recursive=True)
        self.assertIsInstance(result, list)

    def test_discover_tools_in_directories_continues_on_error(self):
        """Test discover_tools_in_directories continues on ToolDiscoveryError."""
        class MockDir:
            """Mock directory class for testing error handling.

            Simulates a directory that raises various exceptions when iterated.
            """

            def iterdir(self):
                """Raise Exception to simulate a general error."""
                raise Exception("Error")

        result = self.discovery.discover_tools_in_directories([MockDir()])
        self.assertEqual(result, [])

    def test_find_tool_by_name_search_directories_error(self):
        """Test find_tool_by_name handles errors in search directories."""
        class MockDir:
            """Mock directory class for testing error handling.

            Simulates a directory that raises various exceptions when iterated.
            """

            def __truediv__(self, other):
                """Raise ToolDiscoveryError to simulate a path operation error."""
                raise ToolDiscoveryError("Error")

        result = self.discovery.find_tool_by_name("test", search_directories=[MockDir()])
        self.assertIsNone(result)

    def test_extract_tool_info_file_read_error(self):
        """Test _extract_tool_info handles file read errors."""
        # Create a path that exists but can't be read
        path = Path(self.test_dir) / "unreadable.py"
        path.touch()

        # Mock open to raise exception
        import builtins
        original_open = builtins.open

        def mock_open(*args, **kwargs):
            """Mock open function for testing."""
            raise IOError("Cannot read")

        builtins.open = mock_open
        try:
            result = self.discovery._extract_tool_info(path)
            self.assertIsNone(result)
        finally:
            builtins.open = original_open

    def test_extract_tool_info_looks_like_tool_false(self):
        """Test _extract_tool_info returns None when not tool-like."""
        content = "x = 1  # No imports, classes, or defs"
        path = self.create_file("not_a_tool.py", content)

        # Mock _looks_like_tool to return False
        original_looks = self.discovery._looks_like_tool
        self.discovery._looks_like_tool = lambda c: False

        try:
            result = self.discovery._extract_tool_info(path)
            self.assertIsNone(result)
        finally:
            self.discovery._looks_like_tool = original_looks

    def test_parse_metadata_capabilities_eval_error(self):
        """Test _parse_metadata handles capabilities eval error."""
        content = """
capabilities = {malformed
class T: pass
"""
        metadata = self.discovery._parse_metadata(content)
        self.assertEqual(metadata.get('capabilities', 'not_set'), {})

    def test_parse_metadata_name_assignment(self):
        """Test _parse_metadata parses name assignment."""
        content = """
name = "my_tool"
class T: pass
"""
        metadata = self.discovery._parse_metadata(content)
        self.assertEqual(metadata.get('name'), 'my_tool')

    def test_parse_metadata_type_assignment(self):
        """Test _parse_metadata parses type assignment."""
        content = """
type = "utility"
class T: pass
"""
        metadata = self.discovery._parse_metadata(content)
        self.assertEqual(metadata.get('type'), 'utility')

    def test_parse_metadata_author_assignment(self):
        """Test _parse_metadata parses author assignment."""
        content = """
author = "John Doe"
class T: pass
"""
        metadata = self.discovery._parse_metadata(content)
        self.assertEqual(metadata.get('author'), 'John Doe')

    def test_parse_metadata_description_assignment(self):
        """Test _parse_metadata parses description assignment."""
        content = """
description = "A test tool"
class T: pass
"""
        metadata = self.discovery._parse_metadata(content)
        self.assertEqual(metadata.get('description'), 'A test tool')

    def test_parse_metadata_no_equals(self):
        """Test _parse_metadata handles lines without equals."""
        content = """
# Just a comment
class T: pass
some_function()
"""
        metadata = self.discovery._parse_metadata(content)
        self.assertEqual(metadata, {})

    def test_parse_metadata_single_part_line(self):
        """Test _parse_metadata handles lines with only one part."""
        content = """
just_one_part
class T: pass
"""
        metadata = self.discovery._parse_metadata(content)
        self.assertEqual(metadata, {})

    def test_looks_like_tool_has_imports(self):
        """Test _looks_like_tool returns True for files with imports."""
        content = "import os"
        self.assertTrue(self.discovery._looks_like_tool(content))

    def test_looks_like_tool_has_class(self):
        """Test _looks_like_tool returns True for files with class."""
        content = "class MyClass: pass"
        self.assertTrue(self.discovery._looks_like_tool(content))

    def test_looks_like_tool_has_def(self):
        """Test _looks_like_tool returns True for files with def."""
        content = "def my_func(): pass"
        self.assertTrue(self.discovery._looks_like_tool(content))

    def test_looks_like_tool_empty(self):
        """Test _looks_like_tool returns False for empty content."""
        content = ""
        self.assertFalse(self.discovery._looks_like_tool(content))

    def test_validate_tool_file_not_exists(self):
        """Test validate_tool_file returns False for non-existent file."""
        path = Path("/nonexistent/file.py")
        self.assertFalse(self.discovery.validate_tool_file(path))

    def test_validate_tool_file_is_dir(self):
        """Test validate_tool_file returns False for directory."""
        dir_path = Path(self.test_dir) / "tool_dir"
        dir_path.mkdir()
        self.assertFalse(self.discovery.validate_tool_file(dir_path))

    def test_validate_tool_file_exception(self):
        """Test validate_tool_file handles exceptions."""
        # Test with a path that doesn't exist to trigger exception handling
        path = Path("/nonexistent/path/file.py")

        result = self.discovery.validate_tool_file(path)
        self.assertFalse(result)

    def test_discover_tools_exception_handling(self):
        """Test discover_tools handles general exceptions."""
        class MockDir:
            """Mock directory class for testing error handling.

            Simulates a directory that raises various exceptions when iterated.
            """

            def iterdir(self):
                """Raise Exception to simulate a general error."""
                raise Exception("General error")

        result = self.discovery.discover_tools([MockDir()])
        self.assertEqual(result, [])

    def test_discover_tools_in_directory_tool_discovery_error_continue(self):
        """Test discover_tools_in_directory continues on ToolDiscoveryError."""
        # Create a file that will cause ToolDiscoveryError
        self.create_file("error_tool.py", "class T: pass")

        # Mock _extract_tool_info to raise ToolDiscoveryError
        original_extract = self.discovery._extract_tool_info
        call_count = [0]

        def mock_extract(fp):
            """Mock extract function for testing."""
            call_count[0] += 1
            if call_count[0] == 1:
                raise ToolDiscoveryError("Test error")
            return original_extract(fp)

        self.discovery._extract_tool_info = mock_extract

        try:
            result = self.discovery.discover_tools_in_directory(Path(self.test_dir))
            # Should continue and find other tools
            self.assertIsInstance(result, list)
        finally:
            self.discovery._extract_tool_info = original_extract

    def test_find_tool_by_name_not_in_cache(self):
        """Test find_tool_by_name returns None when not in cache."""
        # Don't discover any tools
        result = self.discovery.find_tool_by_name("nonexistent")
        self.assertIsNone(result)

    def test_get_discovered_tool_returns_none(self):
        """Test get_discovered_tool returns None for unknown tool."""
        result = self.discovery.get_discovered_tool("unknown")
        self.assertIsNone(result)

    def test_is_tool_discovered_empty(self):
        """Test is_tool_discovered returns False when no tools discovered."""
        result = self.discovery.is_tool_discovered("any_tool")
        self.assertFalse(result)

    def test_create_tool_discovery_function(self):
        """Test create_tool_discovery function."""
        from nodupe.core.tool_system.discovery import create_tool_discovery

        discovery = create_tool_discovery()
        self.assertIsInstance(discovery, ToolDiscovery)


if __name__ == '__main__':
    unittest.main()
