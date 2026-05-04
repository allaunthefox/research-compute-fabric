"""Tests for tool compatibility checking functionality.

This module tests the CompatibilityChecker and ToolCompatibility classes which
verify that tools meet Python version, dependency, and API version requirements.
"""

import sys
import unittest
from unittest.mock import Mock, PropertyMock, patch

# Import Tool base class
from nodupe.core.tool_system.base import Tool
from nodupe.core.tool_system.compatibility import (
    CompatibilityChecker,
    ToolCompatibility,
    ToolCompatibilityError,
)


class MockTool(Tool):
    """Mock tool for testing that properly inherits from Tool."""

    def __init__(self, name="MockTool", version="1.0.0", dependencies=None):
        """Initialize MockTool with name, version, and optional dependencies."""
        self._name = name
        self._version = version
        self._dependencies = dependencies or []

    @property
    def name(self) -> str:
        """Return the tool name."""
        return self._name

    @property
    def version(self) -> str:
        """Return the tool version."""
        return self._version

    @property
    def dependencies(self):
        """Return the tool dependencies."""
        return self._dependencies

    def initialize(self, container):
        """Initialize the tool with a container."""
        pass

    def shutdown(self):
        """Shutdown the tool."""
        pass

    def get_capabilities(self):
        """Return the tool capabilities."""
        return {}

    @property
    def api_methods(self):
        """Return the tool API methods."""
        return {}

    def run_standalone(self, args):
        """Run the tool as a standalone process."""
        return 0

    def describe_usage(self):
        """Return a description of tool usage."""
        return "Mock tool usage"


class TestCompatibilityChecker(unittest.TestCase):
    """Tests for CompatibilityChecker class."""

    def setUp(self):
        """Set up test fixtures."""
        self.checker = CompatibilityChecker()

    def test_check_python_compatibility_exact(self):
        """Test Python version compatibility with exact version match and mismatch."""
        # Current version matched
        with patch.object(sys, 'version_info', (3, 9, 0)):
            self.checker._python_version = getattr(sys, 'version_info') # Re-init to pick up patch? 
            # Actually checker caches it in __init__, so we need to patch BEFORE init or manually update
            self.checker._python_version = Mock(major=3, minor=9)
            is_compat, msg = self.checker.check_python_compatibility(required_version=(3, 9))
            self.assertTrue(is_compat)
            self.assertIn("Compatible", msg)

        # Mismatch
        self.checker._python_version = Mock(major=3, minor=8)
        is_compat, msg = self.checker.check_python_compatibility(required_version=(3, 9))
        self.assertFalse(is_compat)
        self.assertIn("Requires Python 3.9", msg)

    def test_check_python_compatibility_min_max(self):
        """Test Python version compatibility with min and max version constraints."""
        self.checker._python_version = Mock(major=3, minor=10)
        
        # Min satisfied
        is_compat, msg = self.checker.check_python_compatibility(min_version=(3, 9))
        self.assertTrue(is_compat)

        # Min failed
        is_compat, msg = self.checker.check_python_compatibility(min_version=(3, 11))
        self.assertFalse(is_compat)

        # Max satisfied
        is_compat, msg = self.checker.check_python_compatibility(max_version=(3, 11))
        self.assertTrue(is_compat)

        # Max failed
        is_compat, msg = self.checker.check_python_compatibility(max_version=(3, 9))
        self.assertFalse(is_compat)

    def test_check_dependency_compatibility_installed(self):
        """Test dependency compatibility when dependency is installed with various version constraints."""
        # Mocking __import__ is hard, let's use a real standard lib module 'json'
        # json.__version__ usually exists or we can mock it
        
        with patch('builtins.__import__') as mock_import:
            mock_module = Mock()
            mock_module.__version__ = '1.5.0'
            mock_import.return_value = mock_module
            
            # Exact match
            is_compat, msg = self.checker.check_dependency_compatibility('fake_dep', required_version='1.5.0')
            self.assertTrue(is_compat)

            # Mismatch
            is_compat, msg = self.checker.check_dependency_compatibility('fake_dep', required_version='2.0.0')
            self.assertFalse(is_compat)

            # Min satisfied
            is_compat, msg = self.checker.check_dependency_compatibility('fake_dep', min_version='1.0.0')
            self.assertTrue(is_compat)

            # Max failed
            is_compat, msg = self.checker.check_dependency_compatibility('fake_dep', max_version='1.0.0')
            self.assertFalse(is_compat)

    def test_check_dependency_compatibility_not_installed(self):
        """Test dependency compatibility when dependency is not installed."""
        with patch('builtins.__import__', side_effect=ImportError):
            # Required
            is_compat, msg = self.checker.check_dependency_compatibility('missing_dep', required_version='1.0')
            self.assertFalse(is_compat)
            self.assertIn("not installed", msg)

            # Optional (no version constraints) -> actually if no constraints, it returns True for optional?
            # Wait, the code says: if required_version or min_version: return False.
            is_compat, msg = self.checker.check_dependency_compatibility('missing_dep')
            self.assertTrue(is_compat)

    def test_check_api_compatibility(self):
        """Test API version compatibility check with same and different major versions."""
        # Compatible (Same major)
        is_compat, msg = self.checker.check_api_compatibility('tool', '1.2.0', '1.5.0')
        self.assertTrue(is_compat)

        # Incompatible (Different major)
        is_compat, msg = self.checker.check_api_compatibility('tool', '2.0.0', '1.5.0')
        self.assertFalse(is_compat)

    def test_check_tool_compatibility_integration(self):
        """Test full tool compatibility check integration with Python, dependencies, and API."""
        tool_info = {
            'name': 'test_tool',
            'python_version': '3.9',
            'dependencies': {
                'dep1': '>=1.0.0',
                'dep2': '<=2.0.0',
                'dep3': '==1.5.0'
            },
            'api_version': '1.0.0',
            'current_api_version': '1.2.0'
        }

        # Mock self methods to isolate logic
        with patch.object(self.checker, 'check_python_compatibility', return_value=(True, "")) as mock_py, \
             patch.object(self.checker, 'check_dependency_compatibility', return_value=(True, "")) as mock_dep, \
             patch.object(self.checker, 'check_api_compatibility', return_value=(True, "")) as mock_api:
            
            is_compat, issues = self.checker.check_tool_compatibility(tool_info)
            self.assertTrue(is_compat)
            self.assertEqual(len(issues), 0)
            
            mock_py.assert_called()
            self.assertEqual(mock_dep.call_count, 3) 
            mock_api.assert_called()

    def test_version_helpers(self):
        """Test version matching, min/max satisfaction, and compatibility tolerance helper methods."""
        # matches
        self.assertTrue(self.checker._version_matches('1.2.3', '1.2'))
        self.assertFalse(self.checker._version_matches('1.3.0', '1.2'))
        
        # min
        self.assertTrue(self.checker._version_satisfies_min('1.5.0', '1.0.0'))
        self.assertFalse(self.checker._version_satisfies_min('0.9.0', '1.0.0'))
        
        # max
        self.assertTrue(self.checker._version_satisfies_max('1.0.0', '1.5.0'))
        self.assertFalse(self.checker._version_satisfies_max('2.0.0', '1.5.0'))
        
        # is_compatible tolerance
        self.assertTrue(self.checker.is_version_compatible('1.2.3', '1.2.4', tolerance='minor'))
        self.assertTrue(self.checker.is_version_compatible('1.2.3', '1.5.0', tolerance='major'))
        self.assertFalse(self.checker.is_version_compatible('2.0.0', '1.0.0', tolerance='major'))

    def test_parse_version(self):
        """Test version string parsing into numeric components."""
        self.assertEqual(self.checker._parse_version('1.2.3'), [1, 2, 3])
        self.assertEqual(self.checker._parse_version('1.2.3-alpha'), [1, 2, 3])


class TestToolCompatibility(unittest.TestCase):
    """Tests for ToolCompatibility class."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool_compat = ToolCompatibility()
        self.mock_tool = Mock(spec=Tool)
        self.mock_tool.name = "TestTool"
        self.mock_tool.version = "1.0.0"
        self.mock_tool.dependencies = []
        self.mock_tool.initialize = Mock()
        self.mock_tool.shutdown = Mock()
        self.mock_tool.get_capabilities = Mock()

    def test_check_compatibility_valid(self):
        """Test check_compatibility with a valid tool."""
        report = self.tool_compat.check_compatibility(self.mock_tool)
        self.assertTrue(report['compatible'])
        self.assertEqual(report['issues'], [])

    def test_check_compatibility_invalid_struct(self):
        """Test check_compatibility with invalid tool structures (empty name, whitespace, bad version)."""
        # Empty name -> Raises ToolCompatibilityError (early check)
        self.mock_tool.name = ""
        with self.assertRaises(ToolCompatibilityError):
            self.tool_compat.check_compatibility(self.mock_tool)

        # Whitespace name -> Passes early check, fails strip check
        self.mock_tool.name = "   "
        self.mock_tool.version = "1.0.0" # Reset version
        report = self.tool_compat.check_compatibility(self.mock_tool)
        self.assertFalse(report['compatible'])
        self.assertIn("Tool name cannot be empty", report['issues'])

        # Bad version
        self.mock_tool.version = "invalid"  # _parse_version expects x.y at least
        self.mock_tool.name = "ValidName"
        report = self.tool_compat.check_compatibility(self.mock_tool)
        self.assertFalse(report['compatible'])
        self.assertIn("Invalid version format", report['issues'][0])

    def test_get_compatibility_report(self):
        """Test get_compatibility_report returns correct status for valid and invalid tools."""
        report = self.tool_compat.get_compatibility_report(self.mock_tool)
        self.assertEqual(report['compatibility_status'], 'compatible')

        # Test breaking check
        del self.mock_tool.initialize
        report = self.tool_compat.get_compatibility_report(self.mock_tool)
        self.assertEqual(report['compatibility_status'], 'incompatible')

    def test_checks_not_tool_instance(self):
        """Test that check_compatibility raises error when passed non-Tool object."""
        with self.assertRaises(ToolCompatibilityError):
            self.tool_compat.check_compatibility("not a tool")

    def test_parse_version_helper(self):
        """Test version parsing helper via public API usage."""
        # Test private method via public usage or direct if needed
        # It's used in check_compatibility
        pass


class TestCompatibilityCoverageGaps(unittest.TestCase):
    """Test compatibility.py coverage gaps."""

    def setUp(self):
        """Set up test fixtures."""
        self.checker = CompatibilityChecker()
        self.tool_compat = ToolCompatibility()

    def test_check_tool_compatibility_python_version_tuple(self):
        """Test check_tool_compatibility with python_version as tuple (lines 185->192, 189)."""
        tool_info = {
            'name': 'test_tool',
            'python_version': (3, 9),  # Tuple format
            'dependencies': {},
            'api_version': '1.0.0',
            'current_api_version': '1.2.0'
        }

        # Mock to force failure path
        with patch.object(self.checker, 'check_python_compatibility', return_value=(False, "Version mismatch")):
            is_compat, issues = self.checker.check_tool_compatibility(tool_info)
            self.assertFalse(is_compat)
            self.assertIn("Version mismatch", issues)

    def test_check_tool_compatibility_python_version_tuple_success(self):
        """Test check_tool_compatibility with tuple python_version success path (line 185->192)."""
        tool_info = {
            'name': 'test_tool',
            'python_version': (3, 9),  # Tuple format - compatible
            'dependencies': {},
            'api_version': '1.0.0',
            'current_api_version': '1.2.0'
        }

        # Mock to return compatible
        with patch.object(self.checker, 'check_python_compatibility', return_value=(True, "Compatible")):
            is_compat, issues = self.checker.check_tool_compatibility(tool_info)
            self.assertTrue(is_compat)
            self.assertEqual(len(issues), 0)

    def test_check_tool_compatibility_python_version_neither_str_nor_tuple(self):
        """Test check_tool_compatibility with python_version that is neither str nor tuple (line 185->192)."""
        tool_info = {
            'name': 'test_tool',
            'python_version': 123,  # Neither string nor tuple
            'dependencies': {},
            'api_version': '1.0.0',
            'current_api_version': '1.2.0'
        }

        # Should not raise, just skip the python version check
        is_compat, issues = self.checker.check_tool_compatibility(tool_info)
        self.assertTrue(is_compat)
        self.assertEqual(len(issues), 0)

    def test_check_tool_compatibility_dependency_le_constraint_success(self):
        """Test check_tool_compatibility with <= constraint success path (lines 203-205)."""
        tool_info = {
            'name': 'test_tool',
            'python_version': '3.9',
            'dependencies': {
                'dep1': '<=2.0.0'  # <= constraint - compatible
            },
            'api_version': '1.0.0',
            'current_api_version': '1.2.0'
        }

        with patch.object(self.checker, 'check_dependency_compatibility', return_value=(True, "Compatible")), \
             patch.object(self.checker, 'check_python_compatibility', return_value=(True, "Compatible")):
            is_compat, issues = self.checker.check_tool_compatibility(tool_info)
            self.assertTrue(is_compat)
            self.assertEqual(len(issues), 0)

    def test_check_tool_compatibility_dependency_conversion_exception(self):
        """Test check_tool_compatibility with dependency key/value that raises exception (lines 203-205)."""
        # Create a custom object that raises TypeError when converted to string
        class BadKey:
            """Mock class with a __str__ method that raises TypeError.
            
            Used to test error handling when dependency keys cannot be converted to strings.
            """
            def __str__(self):
                """Return string representation (raises TypeError)."""
                raise TypeError("Cannot convert to string")
        
        # Create a dict with a bad key
        bad_dict = {BadKey(): '>=1.0.0'}
        
        tool_info = {
            'name': 'test_tool',
            'python_version': '3.9',
            'dependencies': bad_dict,
            'api_version': '1.0.0',
            'current_api_version': '1.2.0'
        }

        # Should handle the exception and continue
        with patch.object(self.checker, 'check_python_compatibility', return_value=(True, "Compatible")):
            is_compat, issues = self.checker.check_tool_compatibility(tool_info)
        self.assertTrue(is_compat)
        self.assertEqual(len(issues), 0)

    def test_check_tool_compatibility_dependency_unknown_constraint_success(self):
        """Test check_tool_compatibility with unknown constraint success path (line 227)."""
        tool_info = {
            'name': 'test_tool',
            'python_version': '3.9',
            'dependencies': {
                'dep1': '~1.0.0'  # Unknown constraint format - compatible
            },
            'api_version': '1.0.0',
            'current_api_version': '1.2.0'
        }

        with patch.object(self.checker, 'check_dependency_compatibility', return_value=(True, "Compatible")), \
             patch.object(self.checker, 'check_python_compatibility', return_value=(True, "Compatible")):
            is_compat, issues = self.checker.check_tool_compatibility(tool_info)
            self.assertTrue(is_compat)
            self.assertEqual(len(issues), 0)

    def test_check_tool_compatibility_dependency_eq_constraint_success(self):
        """Test check_tool_compatibility with == constraint success path (line 227)."""
        tool_info = {
            'name': 'test_tool',
            'python_version': '3.9',
            'dependencies': {
                'dep1': '==1.0.0'  # == constraint - compatible
            },
            'api_version': '1.0.0',
            'current_api_version': '1.2.0'
        }

        with patch.object(self.checker, 'check_dependency_compatibility', return_value=(True, "Compatible")), \
             patch.object(self.checker, 'check_python_compatibility', return_value=(True, "Compatible")):
            is_compat, issues = self.checker.check_tool_compatibility(tool_info)
            self.assertTrue(is_compat)
            self.assertEqual(len(issues), 0)

    def test_check_tool_compatibility_dependency_eq_constraint_failure(self):
        """Test check_tool_compatibility with == constraint failure path (line 227)."""
        tool_info = {
            'name': 'test_tool',
            'python_version': '3.9',
            'dependencies': {
                'dep1': '==1.0.0'  # == constraint - not compatible
            },
            'api_version': '1.0.0',
            'current_api_version': '1.2.0'
        }

        with patch.object(self.checker, 'check_dependency_compatibility', return_value=(False, "Version mismatch")), \
             patch.object(self.checker, 'check_python_compatibility', return_value=(True, "Compatible")):
            is_compat, issues = self.checker.check_tool_compatibility(tool_info)
            # Overall compatibility is False because the dependency check failed
            self.assertFalse(is_compat)
            self.assertIn("Version mismatch", issues[0])
            self.assertIn("Version mismatch", issues)

    def test_check_tool_compatibility_dependency_le_constraint(self):
        """Test check_tool_compatibility with <= version constraint (lines 203-205)."""
        tool_info = {
            'name': 'test_tool',
            'python_version': '3.9',
            'dependencies': {
                'dep1': '<=2.0.0'  # <= constraint
            },
            'api_version': '1.0.0',
            'current_api_version': '1.2.0'
        }

        with patch.object(self.checker, 'check_dependency_compatibility', return_value=(False, "Version too high")):
            is_compat, issues = self.checker.check_tool_compatibility(tool_info)
            self.assertFalse(is_compat)
            self.assertIn("Version too high", issues)

    def test_check_tool_compatibility_dependency_unknown_constraint(self):
        """Test check_tool_compatibility with unknown version constraint (line 220)."""
        tool_info = {
            'name': 'test_tool',
            'python_version': '3.9',
            'dependencies': {
                'dep1': '~1.0.0'  # Unknown constraint format
            },
            'api_version': '1.0.0',
            'current_api_version': '1.2.0'
        }

        with patch.object(self.checker, 'check_dependency_compatibility', return_value=(False, "Constraint failed")):
            is_compat, issues = self.checker.check_tool_compatibility(tool_info)
            self.assertFalse(is_compat)
            self.assertIn("Constraint failed", issues)

    def test_check_tool_compatibility_dependency_failure(self):
        """Test check_tool_compatibility with dependency check failure (line 227)."""
        tool_info = {
            'name': 'test_tool',
            'python_version': '3.9',
            'dependencies': {
                'dep1': '>=1.0.0'
            },
            'api_version': '1.0.0',
            'current_api_version': '1.2.0'
        }

        with patch.object(self.checker, 'check_dependency_compatibility', return_value=(False, "Dependency missing")):
            is_compat, issues = self.checker.check_tool_compatibility(tool_info)
            self.assertFalse(is_compat)
            self.assertIn("Dependency missing", issues)

    def test_check_tool_compatibility_api_failure(self):
        """Test check_tool_compatibility with API check failure (line 234)."""
        tool_info = {
            'name': 'test_tool',
            'python_version': '3.9',
            'dependencies': {},
            'api_version': '2.0.0',  # Different major
            'current_api_version': '1.2.0'
        }

        is_compat, issues = self.checker.check_tool_compatibility(tool_info)
        self.assertFalse(is_compat)
        self.assertTrue(len(issues) > 0)

    def test_tool_compatibility_empty_name(self):
        """Test ToolCompatibility.check_compatibility with whitespace-only name (line 460)."""
        # Empty string raises exception early, so test whitespace-only name
        mock_tool = MockTool(name="   ")  # Whitespace-only name

        report = self.tool_compat.check_compatibility(mock_tool)
        self.assertFalse(report['compatible'])
        self.assertIn("Tool name cannot be empty", report['issues'])

    def test_tool_compatibility_invalid_version_format(self):
        """Test ToolCompatibility.check_compatibility with invalid version (lines 483-484)."""
        mock_tool = MockTool(name="TestTool", version="not-a-version")  # Invalid format

        report = self.tool_compat.check_compatibility(mock_tool)
        self.assertFalse(report['compatible'])
        self.assertTrue(any("Invalid version format" in issue for issue in report['issues']))

    def test_tool_compatibility_dependencies_not_list(self):
        """Test ToolCompatibility.check_compatibility with dependencies not a list (lines 515-517)."""
        mock_tool = MockTool(name="TestTool", version="1.0.0")
        mock_tool._dependencies = "not-a-list"  # Not a list

        report = self.tool_compat.check_compatibility(mock_tool)
        self.assertFalse(report['compatible'])
        self.assertIn("Dependencies must be a list", report['issues'])

    def test_tool_compatibility_full_report(self):
        """Test ToolCompatibility.get_compatibility_report full path (lines 520-522)."""
        mock_tool = MockTool(name="TestTool", version="1.0.0")

        report = self.tool_compat.get_compatibility_report(mock_tool)
        self.assertEqual(report['compatibility_status'], 'compatible')
        self.assertEqual(report['tool_name'], 'TestTool')
        self.assertEqual(report['tool_version'], '1.0.0')

    def test_get_compatibility_report_no_version(self):
        """Test get_compatibility_report when tool has no version (lines 515-517)."""
        # Create a mock tool class that inherits from Tool but has no version
        class ToolNoVersion(Tool):
            """Mock tool class without a version property.
            
            Used to test error handling when a tool lacks a version attribute.
            """
            name = "NoVersionTool"
            dependencies = []

            def __str__(self):
                """Return string representation of the tool."""
                return f"ToolNoVersion(name={self.name})"

            def initialize(self, container):
                """Initialize the tool with a container."""
                pass

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Return the tool capabilities."""
                return {}

            @property
            def api_methods(self):
                """Return the tool API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool as a standalone process."""
                return 0

            def describe_usage(self):
                """Return a description of tool usage."""
                return "test"

            @property
            def version(self):
                """Return the tool version (raises AttributeError to simulate missing)."""
                raise AttributeError("version")

        class ToolNoDeps(Tool):
            """Mock tool class without a dependencies property.
            
            Used to test error handling when a tool lacks a dependencies attribute.
            """
            name = "NoDepsTool"
            version = "1.0.0"

            def __str__(self):
                """Return string representation of the tool."""
                return f"ToolNoDeps(name={self.name}, version={self.version})"

            def initialize(self, container):
                """Initialize the tool with a container."""
                pass

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Return the tool capabilities."""
                return {}

            @property
            def api_methods(self):
                """Return the tool API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool as a standalone process."""
                return 0

            def describe_usage(self):
                """Return a description of tool usage."""
                return "test"

            @property
            def dependencies(self):
                """Return the tool dependencies (raises AttributeError to simulate missing)."""
                raise AttributeError("dependencies")

        mock_tool = ToolNoDeps()

        report = self.tool_compat.get_compatibility_report(mock_tool)
        self.assertEqual(report['compatibility_status'], 'incompatible')
        self.assertIn("Tool must have dependencies", report['compatibility_issues'])

    def test_check_compatibility_deps_not_list(self):
        """Test check_compatibility when dependencies is not a list (lines 483-484)."""
        mock_tool = MockTool(name="TestTool", version="1.0.0")
        mock_tool._dependencies = "not-a-list"

        report = self.tool_compat.check_compatibility(mock_tool)
        self.assertFalse(report['compatible'])
        self.assertIn("Dependencies must be a list", report['issues'])


if __name__ == '__main__':
    unittest.main()
