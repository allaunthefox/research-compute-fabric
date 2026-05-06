"""Test Tool Compatibility Module.

Comprehensive tests for the compatibility checking system including:
- Python version compatibility checking
- Dependency version validation
- API compatibility verification
- Tool compatibility checking
- Version parsing and comparison
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from nodupe.core.tool_system.base import Tool
from nodupe.core.tool_system.compatibility import (
    CompatibilityChecker,
    ToolCompatibility,
    ToolCompatibilityError,
    create_compatibility_checker,
)


class MockTool(Tool):
    """Mock tool for testing."""

    def __init__(self, name="MockTool", version="1.0.0", dependencies=None):
        """Initialize MockTool with name, version, and dependencies."""
        self._name = name
        self._version = version
        self._dependencies = dependencies or []
        self._initialized = False

    @property
    def name(self):
        """Tool name property."""
        return self._name

    @property
    def version(self):
        """Tool version property."""
        return self._version

    @property
    def dependencies(self):
        """Tool dependencies property."""
        return self._dependencies

    def initialize(self, container):
        """Initialize the tool."""
        self._initialized = True

    def shutdown(self):
        """Shutdown the tool."""
        self._initialized = False

    def get_capabilities(self):
        """Get tool capabilities."""
        return {"test": "capability"}

    @property
    def api_methods(self):
        """API methods property."""
        return {}

    def run_standalone(self, args):
        """Run as standalone."""
        return 0

    def describe_usage(self):
        """Describe tool usage."""
        return "Mock tool usage"


class TestCompatibilityCheckerInit:
    """Test CompatibilityChecker initialization."""

    def test_compatibility_checker_init(self):
        """Test basic CompatibilityChecker initialization."""
        checker = CompatibilityChecker()

        assert checker._python_version == sys.version_info
        assert len(checker._supported_versions) > 0
        assert checker._api_versions == {}
        assert checker._dependency_constraints == {}

    def test_supported_versions(self):
        """Test that supported versions are properly defined."""
        checker = CompatibilityChecker()
        versions = checker.get_supported_python_versions()

        assert isinstance(versions, list)
        assert len(versions) > 0

    def test_create_compatibility_checker_factory(self):
        """Test the create_compatibility_checker factory function."""
        checker = create_compatibility_checker()

        assert isinstance(checker, CompatibilityChecker)


class TestPythonVersionCompatibility:
    """Test Python version compatibility checking."""

    def test_check_python_compatibility_current_version(self):
        """Test checking compatibility with current Python version."""
        checker = CompatibilityChecker()
        current = sys.version_info

        is_compat, msg = checker.check_python_compatibility(
            required_version=(current.major, current.minor)
        )

        assert is_compat is True
        assert "Compatible" in msg

    def test_check_python_compatibility_wrong_version(self):
        """Test checking compatibility with wrong Python version."""
        checker = CompatibilityChecker()

        wrong_version = (2, 7) if sys.version_info.major >= 3 else (3, 9)

        is_compat, msg = checker.check_python_compatibility(
            required_version=wrong_version
        )

        assert is_compat is False
        assert "Requires Python" in msg

    def test_check_python_compatibility_min_version_satisfied(self):
        """Test checking minimum version that is satisfied."""
        checker = CompatibilityChecker()
        current = sys.version_info

        min_version = (current.major, current.minor - 1) if current.minor > 0 else (current.major - 1, 9)

        is_compat, msg = checker.check_python_compatibility(
            min_version=min_version
        )

        assert is_compat is True

    def test_check_python_compatibility_min_version_not_satisfied(self):
        """Test checking minimum version that is not satisfied."""
        checker = CompatibilityChecker()

        current = sys.version_info
        future_version = (current.major + 10, 0)

        is_compat, msg = checker.check_python_compatibility(
            min_version=future_version
        )

        assert is_compat is False
        assert "Requires Python" in msg

    def test_check_python_compatibility_max_version_satisfied(self):
        """Test checking maximum version that is satisfied."""
        checker = CompatibilityChecker()
        current = sys.version_info

        max_version = (current.major + 10, 0)

        is_compat, msg = checker.check_python_compatibility(
            max_version=max_version
        )

        assert is_compat is True

    def test_check_python_compatibility_max_version_not_satisfied(self):
        """Test checking maximum version that is not satisfied."""
        checker = CompatibilityChecker()
        current = sys.version_info

        old_version = (2, 7) if current.major >= 3 else (current.major - 1, 0)

        is_compat, msg = checker.check_python_compatibility(
            max_version=old_version
        )

        assert is_compat is False
        assert "Maximum Python" in msg

    def test_check_python_compatibility_combined_checks(self):
        """Test checking with min and max version together."""
        checker = CompatibilityChecker()
        current = sys.version_info

        min_ver = (current.major, 0)
        max_ver = (current.major + 10, 0)

        is_compat, msg = checker.check_python_compatibility(
            min_version=min_ver,
            max_version=max_ver
        )

        assert is_compat is True

    def test_check_python_compatibility_no_constraints(self):
        """Test checking with no version constraints."""
        checker = CompatibilityChecker()

        is_compat, msg = checker.check_python_compatibility()

        assert is_compat is True
        assert "Compatible" in msg


class TestDependencyCompatibility:
    """Test dependency version compatibility checking."""

    def test_check_dependency_compatibility_installed_module(self):
        """Test checking compatibility with an installed module."""
        checker = CompatibilityChecker()

        is_compat, msg = checker.check_dependency_compatibility("sys")

        assert is_compat is True

    def test_check_dependency_compatibility_with_version(self):
        """Test checking compatibility with version constraint."""
        checker = CompatibilityChecker()

        is_compat, msg = checker.check_dependency_compatibility(
            "sys",
            min_version="3.0"
        )

        assert is_compat is True

    def test_check_dependency_compatibility_missing_module(self):
        """Test checking compatibility with missing module."""
        checker = CompatibilityChecker()

        is_compat, msg = checker.check_dependency_compatibility(
            "nonexistent_module_xyz"
        )

        assert is_compat is True

    def test_check_dependency_compatibility_required_missing(self):
        """Test checking compatibility with required missing module."""
        checker = CompatibilityChecker()

        is_compat, msg = checker.check_dependency_compatibility(
            "nonexistent_module_xyz",
            min_version="1.0"
        )

        assert is_compat is False
        assert "not installed" in msg

    def test_check_dependency_compatibility_version_mismatch(self):
        """Test checking compatibility with version mismatch."""
        checker = CompatibilityChecker()

        is_compat, msg = checker.check_dependency_compatibility(
            "sys",
            required_version="99.99.99"
        )

        assert is_compat is True

    def test_check_dependency_compatibility_min_version_fail(self):
        """Test checking compatibility with minimum version failure."""
        checker = CompatibilityChecker()

        is_compat, msg = checker.check_dependency_compatibility(
            "sys",
            min_version="99.0"
        )

        assert is_compat is True

    def test_check_dependency_compatibility_max_version_fail(self):
        """Test checking compatibility with maximum version failure."""
        checker = CompatibilityChecker()

        is_compat, msg = checker.check_dependency_compatibility(
            "sys",
            max_version="1.0"
        )

        assert is_compat is True


class TestAPICompatibility:
    """Test API compatibility checking."""

    def test_check_api_compatibility_same_version(self):
        """Test checking API compatibility with same version."""
        checker = CompatibilityChecker()

        is_compat, msg = checker.check_api_compatibility(
            "TestTool",
            "1.0.0",
            "1.0.0"
        )

        assert is_compat is True
        assert "API compatible" in msg

    def test_check_api_compatibility_same_major(self):
        """Test checking API compatibility with same major version."""
        checker = CompatibilityChecker()

        is_compat, msg = checker.check_api_compatibility(
            "TestTool",
            "1.0.0",
            "1.5.0"
        )

        assert is_compat is True

    def test_check_api_compatibility_different_major(self):
        """Test checking API compatibility with different major version."""
        checker = CompatibilityChecker()

        is_compat, msg = checker.check_api_compatibility(
            "TestTool",
            "2.0.0",
            "1.0.0"
        )

        assert is_compat is False
        assert "requires API" in msg

    def test_check_api_compatibility_patch_difference(self):
        """Test checking API compatibility with patch version difference."""
        checker = CompatibilityChecker()

        is_compat, msg = checker.check_api_compatibility(
            "TestTool",
            "1.0.0",
            "1.0.1"
        )

        assert is_compat is True


class TestToolCompatibility:
    """Test overall tool compatibility checking."""

    def test_check_tool_compatibility_valid_tool(self):
        """Test checking compatibility with a valid tool."""
        checker = CompatibilityChecker()
        current = sys.version_info

        tool_info = {
            "name": "TestTool",
            "python_version": f"{current.major}.{current.minor}",
            "dependencies": {},
            "api_version": "1.0.0",
            "current_api_version": "1.0.0"
        }

        is_compat, issues = checker.check_tool_compatibility(tool_info)

        assert is_compat is True
        assert issues == []

    def test_check_tool_compatibility_invalid_python_version(self):
        """Test checking compatibility with invalid Python version."""
        checker = CompatibilityChecker()

        tool_info = {
            "name": "TestTool",
            "python_version": "2.7",
            "dependencies": {},
            "api_version": "1.0.0",
            "current_api_version": "1.0.0"
        }

        is_compat, issues = checker.check_tool_compatibility(tool_info)

        assert is_compat is False
        assert len(issues) > 0

    def test_check_tool_compatibility_missing_dependency(self):
        """Test checking compatibility with missing dependency."""
        checker = CompatibilityChecker()
        current = sys.version_info

        tool_info = {
            "name": "TestTool",
            "python_version": f"{current.major}.{current.minor}",
            "dependencies": {
                "nonexistent_dep_xyz": ">=1.0"
            },
            "api_version": "1.0.0",
            "current_api_version": "1.0.0"
        }

        is_compat, issues = checker.check_tool_compatibility(tool_info)

        assert is_compat is False
        assert len(issues) > 0

    def test_check_tool_compatibility_api_mismatch(self):
        """Test checking compatibility with API version mismatch."""
        checker = CompatibilityChecker()
        current = sys.version_info

        tool_info = {
            "name": "TestTool",
            "python_version": f"{current.major}.{current.minor}",
            "dependencies": {},
            "api_version": "2.0.0",
            "current_api_version": "1.0.0"
        }

        is_compat, issues = checker.check_tool_compatibility(tool_info)

        assert is_compat is False
        assert len(issues) > 0

    def test_check_tool_compatibility_tuple_version(self):
        """Test checking compatibility with tuple version format."""
        checker = CompatibilityChecker()
        current = sys.version_info

        tool_info = {
            "name": "TestTool",
            "python_version": (current.major, current.minor),
            "dependencies": {},
            "api_version": "1.0.0",
            "current_api_version": "1.0.0"
        }

        is_compat, issues = checker.check_tool_compatibility(tool_info)

        assert is_compat is True

    def test_check_tool_compatibility_invalid_version_format(self):
        """Test checking compatibility with invalid version format."""
        checker = CompatibilityChecker()

        tool_info = {
            "name": "TestTool",
            "python_version": "invalid",
            "dependencies": {},
            "api_version": "1.0.0",
            "current_api_version": "1.0.0"
        }

        is_compat, issues = checker.check_tool_compatibility(tool_info)

        assert is_compat is False

    def test_check_tool_compatibility_min_constraint(self):
        """Test checking compatibility with >= constraint."""
        checker = CompatibilityChecker()
        current = sys.version_info

        tool_info = {
            "name": "TestTool",
            "python_version": f"{current.major}.{current.minor}",
            "dependencies": {
                "sys": ">=3.0"
            },
            "api_version": "1.0.0",
            "current_api_version": "1.0.0"
        }

        is_compat, issues = checker.check_tool_compatibility(tool_info)

        assert is_compat is True

    def test_check_tool_compatibility_max_constraint(self):
        """Test checking compatibility with <= constraint."""
        checker = CompatibilityChecker()
        current = sys.version_info

        tool_info = {
            "name": "TestTool",
            "python_version": f"{current.major}.{current.minor}",
            "dependencies": {
                "sys": "<=99.0"
            },
            "api_version": "1.0.0",
            "current_api_version": "1.0.0"
        }

        is_compat, issues = checker.check_tool_compatibility(tool_info)

        assert is_compat is True

    def test_check_tool_compatibility_exact_constraint(self):
        """Test checking compatibility with == constraint."""
        checker = CompatibilityChecker()
        current = sys.version_info

        tool_info = {
            "name": "TestTool",
            "python_version": f"{current.major}.{current.minor}",
            "dependencies": {
                "sys": "==99.0"
            },
            "api_version": "1.0.0",
            "current_api_version": "1.0.0"
        }

        is_compat, issues = checker.check_tool_compatibility(tool_info)

        assert is_compat is True

    def test_check_tool_compatibility_no_python_version(self):
        """Test checking compatibility without python_version key."""
        checker = CompatibilityChecker()

        tool_info = {
            "name": "TestTool",
            "dependencies": {},
            "api_version": "1.0.0",
            "current_api_version": "1.0.0"
        }

        is_compat, issues = checker.check_tool_compatibility(tool_info)

        assert is_compat is True

    def test_check_tool_compatibility_no_dependencies(self):
        """Test checking compatibility without dependencies key."""
        checker = CompatibilityChecker()
        current = sys.version_info

        tool_info = {
            "name": "TestTool",
            "python_version": f"{current.major}.{current.minor}",
            "api_version": "1.0.0",
            "current_api_version": "1.0.0"
        }

        is_compat, issues = checker.check_tool_compatibility(tool_info)

        assert is_compat is True

    def test_check_tool_compatibility_no_api_version(self):
        """Test checking compatibility without api_version key."""
        checker = CompatibilityChecker()
        current = sys.version_info

        tool_info = {
            "name": "TestTool",
            "python_version": f"{current.major}.{current.minor}",
            "dependencies": {}
        }

        is_compat, issues = checker.check_tool_compatibility(tool_info)

        assert is_compat is True


class TestVersionComparison:
    """Test version comparison methods."""

    def test_is_version_compatible_major(self):
        """Test version compatibility with major tolerance."""
        checker = CompatibilityChecker()

        assert checker.is_version_compatible("1.0.0", "1.5.0", "major") is True
        assert checker.is_version_compatible("1.0.0", "2.0.0", "major") is False

    def test_is_version_compatible_minor(self):
        """Test version compatibility with minor tolerance."""
        checker = CompatibilityChecker()

        assert checker.is_version_compatible("1.2.0", "1.2.5", "minor") is True
        assert checker.is_version_compatible("1.2.0", "1.3.0", "minor") is False

    def test_is_version_compatible_patch(self):
        """Test version compatibility with patch tolerance."""
        checker = CompatibilityChecker()

        assert checker.is_version_compatible("1.2.3", "1.2.3", "patch") is True
        assert checker.is_version_compatible("1.2.3", "1.2.4", "patch") is False

    def test_is_version_compatible_invalid_tolerance(self):
        """Test version compatibility with invalid tolerance."""
        checker = CompatibilityChecker()

        assert checker.is_version_compatible("1.0.0", "1.0.0", "invalid") is False

    def test_is_version_compatible_exception(self):
        """Test version compatibility with exception handling."""
        checker = CompatibilityChecker()

        assert checker.is_version_compatible("invalid", "version", "major") is False

    def test_version_matches_exact(self):
        """Test exact version matching."""
        checker = CompatibilityChecker()

        assert checker._version_matches("1.2.3", "1.2.3") is True
        assert checker._version_matches("1.2.3", "==1.2.3") is True
        assert checker._version_matches("1.2.4", "1.2.3") is False

    def test_version_satisfies_min(self):
        """Test minimum version satisfaction."""
        checker = CompatibilityChecker()

        assert checker._version_satisfies_min("1.2.3", "1.0.0") is True
        assert checker._version_satisfies_min("1.2.3", "1.2.3") is True
        assert checker._version_satisfies_min("1.2.3", "1.2.4") is False

    def test_version_satisfies_max(self):
        """Test maximum version satisfaction."""
        checker = CompatibilityChecker()

        assert checker._version_satisfies_max("1.2.3", "2.0.0") is True
        assert checker._version_satisfies_max("1.2.3", "1.2.3") is True
        assert checker._version_satisfies_max("1.2.3", "1.2.2") is False

    def test_api_version_compatible(self):
        """Test API version compatibility."""
        checker = CompatibilityChecker()

        assert checker._api_version_compatible("1.0.0", "1.5.0") is True
        assert checker._api_version_compatible("1.0.0", "2.0.0") is False

    def test_parse_version(self):
        """Test version string parsing."""
        checker = CompatibilityChecker()

        assert checker._parse_version("1.2.3") == [1, 2, 3]
        assert checker._parse_version("1.2") == [1, 2]
        assert checker._parse_version("1.2.3-beta") == [1, 2, 3]


class TestRegistryMethods:
    """Test API version and dependency constraint registration."""

    def test_register_api_version(self):
        """Test registering an API version."""
        checker = CompatibilityChecker()

        checker.register_api_version("TestTool", "1.0.0")

        assert checker._api_versions["TestTool"] == "1.0.0"

    def test_register_dependency_constraint(self):
        """Test registering a dependency constraint."""
        checker = CompatibilityChecker()

        checker.register_dependency_constraint("test_dep", ">=1.0")

        assert checker._dependency_constraints["test_dep"] == ">=1.0"

    def test_get_supported_python_versions(self):
        """Test getting supported Python versions."""
        checker = CompatibilityChecker()

        versions = checker.get_supported_python_versions()

        assert isinstance(versions, list)


class TestToolCompatibilityClass:
    """Test ToolCompatibility class."""

    def test_tool_compatibility_init(self):
        """Test ToolCompatibility initialization."""
        compat = ToolCompatibility()

        assert compat.container is None
        assert isinstance(compat._checker, CompatibilityChecker)

    def test_check_compatibility_valid_tool(self):
        """Test checking compatibility with a valid tool."""
        compat = ToolCompatibility()
        tool = MockTool()

        report = compat.check_compatibility(tool)

        assert report["compatible"] is True
        assert report["issues"] == []

    def test_check_compatibility_not_tool(self):
        """Test checking compatibility with non-tool object."""
        compat = ToolCompatibility()

        with pytest.raises(ToolCompatibilityError) as exc_info:
            compat.check_compatibility("not a tool")

        assert "Tool must inherit from Tool" in str(exc_info.value)

    def test_check_compatibility_no_name(self):
        """Test checking compatibility with tool without name."""
        compat = ToolCompatibility()

        class BadTool(Tool):
            """Tool with missing name for testing."""

            @property
            def name(self):
                """Tool name property."""
                return ""

            @property
            def version(self):
                """Tool version property."""

            @property
            def dependencies(self):
                """Tool dependencies property."""

            def initialize(self, container):
                """Initialize the tool."""

            def shutdown(self):
                """Shutdown the tool."""

            def get_capabilities(self):
                """Get tool capabilities."""

            @property
            def api_methods(self):
                """API methods property."""

            def run_standalone(self, args):
                """Run as standalone."""

            def describe_usage(self):
                """Describe tool usage."""

        tool = BadTool()

        with pytest.raises(ToolCompatibilityError) as exc_info:
            compat.check_compatibility(tool)

        assert "valid name" in str(exc_info.value)

    def test_check_compatibility_no_version(self):
        """Test checking compatibility with tool without version."""
        compat = ToolCompatibility()

        class BadTool(Tool):
            """Tool with missing version for testing."""

            @property
            def name(self):
                """Tool name property."""
                return "BadTool"
            @property
            def version(self):
                """Tool version property."""
                raise AttributeError("version")
            @property
            def dependencies(self):
                """Tool dependencies property."""
                return []
            def initialize(self, container):
                """Initialize the tool."""
                pass
            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get tool capabilities."""
                return {}

            @property
            def api_methods(self):
                """API methods property."""
                return {}

            def run_standalone(self, args):
                """Run as standalone."""
                return 0

            def describe_usage(self):
                """Describe tool usage."""
                return ""
        tool = BadTool()

        with pytest.raises(ToolCompatibilityError) as exc_info:
            compat.check_compatibility(tool)

        assert "version" in str(exc_info.value)

    def test_check_compatibility_no_dependencies(self):
        """Test checking compatibility with tool without dependencies."""
        compat = ToolCompatibility()

        class BadTool(Tool):
            """Tool with failing dependencies for testing."""

            @property
            def name(self):
                """Tool name property."""
                return "BadTool"

            @property
            def version(self):
                """Tool version property."""
                return "1.0.0"

            @property
            def dependencies(self):
                """Tool dependencies property."""
                raise AttributeError("dependencies")

            def initialize(self, container):
                """Initialize the tool."""
                pass

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get tool capabilities."""
                return {}

            @property
            def api_methods(self):
                """API methods property."""
                return {}

            def run_standalone(self, args):
                """Run as standalone."""
                return 0

            def describe_usage(self):
                """Describe tool usage."""
                return ""

        tool = BadTool()

        with pytest.raises(ToolCompatibilityError) as exc_info:
            compat.check_compatibility(tool)

        assert "dependencies" in str(exc_info.value)

    def test_check_compatibility_missing_methods(self):
        """Test checking compatibility with tool missing methods."""
        compat = ToolCompatibility()

        tool = MagicMock()
        tool.name = "BadTool"
        tool.version = "1.0.0"
        tool.dependencies = []

        with pytest.raises(ToolCompatibilityError) as exc_info:
            compat.check_compatibility(tool)

        assert "Tool must inherit from Tool" in str(exc_info.value)

    def test_get_compatibility_report_valid_tool(self):
        """Test getting compatibility report for valid tool."""
        compat = ToolCompatibility()
        tool = MockTool()

        report = compat.get_compatibility_report(tool)

        assert report["tool_name"] == "MockTool"
        assert report["tool_version"] == "1.0.0"
        assert report["compatibility_status"] == "compatible"

    def test_tool_compatibility_initialize(self):
        """Test ToolCompatibility initialize method."""
        compat = ToolCompatibility()
        container = MagicMock()

        compat.initialize(container)

        assert compat.container == container

    def test_tool_compatibility_shutdown(self):
        """Test ToolCompatibility shutdown method."""
        compat = ToolCompatibility()
        compat.container = MagicMock()

        compat.shutdown()

        assert compat.container is None


class TestCompatibilityCoverageGaps:
    """Additional tests to cover remaining lines in compatibility.py."""

    def test_check_dependency_compatibility_with_VERSION_attr(self):
        """Test dependency check when module has VERSION attribute."""
        checker = CompatibilityChecker()

        import types
        mock_module = types.ModuleType("mock_module")
        mock_module.VERSION = "1.0.0"

        with patch('builtins.__import__', return_value=mock_module):
            is_compat, msg = checker.check_dependency_compatibility("mock_module")
            assert is_compat is True

    def test_check_dependency_compatibility_required_with_version(self):
        """Test dependency check with required version that fails."""
        checker = CompatibilityChecker()

        import types
        mock_module = types.ModuleType("versioned_module")
        mock_module.__version__ = "1.0.0"

        with patch('builtins.__import__', return_value=mock_module):
            is_compat, msg = checker.check_dependency_compatibility(
                "versioned_module",
                required_version="2.0.0"
            )
            assert is_compat is False

    def test_check_dependency_compatibility_min_version_fail(self):
        """Test dependency check with minimum version that fails."""
        checker = CompatibilityChecker()

        import types
        mock_module = types.ModuleType("versioned_module")
        mock_module.__version__ = "1.0.0"

        with patch('builtins.__import__', return_value=mock_module):
            is_compat, msg = checker.check_dependency_compatibility(
                "versioned_module",
                min_version="2.0.0"
            )
            assert is_compat is False

    def test_check_dependency_compatibility_max_version_fail(self):
        """Test dependency check with maximum version that fails."""
        checker = CompatibilityChecker()

        import types
        mock_module = types.ModuleType("versioned_module")
        mock_module.__version__ = "2.0.0"

        with patch('builtins.__import__', return_value=mock_module):
            is_compat, msg = checker.check_dependency_compatibility(
                "versioned_module",
                max_version="1.0.0"
            )
            assert is_compat is False

    def test_check_tool_compatibility_no_current_api_version(self):
        """Test tool compatibility check without current_api_version."""
        checker = CompatibilityChecker()
        current = sys.version_info

        tool_info = {
            "name": "TestTool",
            "python_version": f"{current.major}.{current.minor}",
            "dependencies": {},
            "api_version": "1.0.0"
        }

        is_compat, issues = checker.check_tool_compatibility(tool_info)
        assert is_compat is True

    def test_check_tool_compatibility_deps_not_dict(self):
        """Test tool compatibility check when dependencies is not a dict."""
        checker = CompatibilityChecker()
        current = sys.version_info

        tool_info = {
            "name": "TestTool",
            "python_version": f"{current.major}.{current.minor}",
            "dependencies": ["dep1", "dep2"],
            "api_version": "1.0.0",
            "current_api_version": "1.0.0"
        }

        is_compat, issues = checker.check_tool_compatibility(tool_info)
        assert is_compat is True
