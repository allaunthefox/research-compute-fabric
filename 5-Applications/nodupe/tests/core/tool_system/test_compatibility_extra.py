"""Test Compatibility Module - Additional Coverage Tests.

Tests to achieve higher coverage for compatibility.py
"""

import sys
from unittest.mock import Mock, patch

import pytest

from nodupe.core.tool_system.base import Tool
from nodupe.core.tool_system.compatibility import (
    CompatibilityChecker,
    ToolCompatibility,
    ToolCompatibilityError,
)


class TestCompatibilityCheckerEdgeCases:
    """Test CompatibilityChecker edge cases."""

    def test_check_python_compatibility_all_constraints(self):
        """Test with all version constraints together."""
        checker = CompatibilityChecker()

        with patch.object(checker, '_python_version', Mock(major=3, minor=10)):
            # Min and max together, satisfied
            is_compat, msg = checker.check_python_compatibility(
                min_version=(3, 9),
                max_version=(3, 11)
            )
            assert is_compat is True

            # Min and max together, min not satisfied
            is_compat, msg = checker.check_python_compatibility(
                min_version=(3, 11),
                max_version=(3, 12)
            )
            assert is_compat is False

    def test_check_python_compatibility_with_required(self):
        """Test with exact required version."""
        checker = CompatibilityChecker()

        with patch.object(checker, '_python_version', Mock(major=3, minor=10)):
            # Exact match
            is_compat, msg = checker.check_python_compatibility(
                required_version=(3, 10)
            )
            assert is_compat is True

            # Exact mismatch
            is_compat, msg = checker.check_python_compatibility(
                required_version=(3, 9)
            )
            assert is_compat is False

    def test_check_dependency_compatibility_module_exception(self):
        """Test dependency compatibility with module exception."""
        checker = CompatibilityChecker()

        with patch('builtins.__import__') as mock_import:
            mock_import.side_effect = Exception("Import error")

            is_compat, msg = checker.check_dependency_compatibility('test_dep')
            # Should return True when exception occurs
            assert is_compat is True

    def test_check_dependency_compatibility_version_attribute(self):
        """Test dependency compatibility with VERSION attribute."""
        checker = CompatibilityChecker()

        with patch('builtins.__import__') as mock_import:
            mock_module = Mock()
            mock_module.__version__ = None
            mock_module.VERSION = "1.0.0"
            mock_import.return_value = mock_module

            is_compat, msg = checker.check_dependency_compatibility('test_dep')
            assert is_compat is True

    def test_check_dependency_compatibility_no_version(self):
        """Test dependency compatibility with no version attribute."""
        checker = CompatibilityChecker()

        with patch('builtins.__import__') as mock_import:
            mock_module = Mock()
            del mock_module.__version__
            if hasattr(mock_module, 'VERSION'):
                del mock_module.VERSION
            mock_import.return_value = mock_module

            is_compat, msg = checker.check_dependency_compatibility('test_dep')
            assert is_compat is True


class TestToolCompatibilityEdgeCases:
    """Test ToolCompatibility edge cases."""

    def test_check_compatibility_not_tool_instance(self):
        """Test check_compatibility with non-Tool instance."""
        compat = ToolCompatibility()

        with pytest.raises(ToolCompatibilityError):
            compat.check_compatibility("not a tool")

    def test_check_compatibility_missing_name(self):
        """Test check_compatibility with missing name."""
        compat = ToolCompatibility()
        mock_tool = Mock(spec=Tool)
        del mock_tool.name

        with pytest.raises(ToolCompatibilityError):
            compat.check_compatibility(mock_tool)

    def test_check_compatibility_missing_version(self):
        """Test check_compatibility with missing version."""
        compat = ToolCompatibility()
        mock_tool = Mock(spec=Tool)
        mock_tool.name = "Test"
        del mock_tool.version

        with pytest.raises(ToolCompatibilityError):
            compat.check_compatibility(mock_tool)

    def test_check_compatibility_missing_dependencies(self):
        """Test check_compatibility with missing dependencies."""
        compat = ToolCompatibility()
        mock_tool = Mock(spec=Tool)
        mock_tool.name = "Test"
        mock_tool.version = "1.0.0"
        del mock_tool.dependencies

        with pytest.raises(ToolCompatibilityError):
            compat.check_compatibility(mock_tool)

    def test_check_compatibility_missing_methods(self):
        """Test check_compatibility with missing methods."""
        compat = ToolCompatibility()
        mock_tool = Mock(spec=Tool)
        mock_tool.name = "Test"
        mock_tool.version = "1.0.0"
        mock_tool.dependencies = []

        # Remove required methods
        del mock_tool.initialize
        del mock_tool.shutdown
        del mock_tool.get_capabilities

        with pytest.raises(ToolCompatibilityError):
            compat.check_compatibility(mock_tool)


class TestToolCompatibilityInitializeShutdown:
    """Test ToolCompatibility initialize and shutdown."""

    def test_initialize_sets_container(self):
        """Test initialize sets container."""
        compat = ToolCompatibility()
        mock_container = Mock()

        compat.initialize(mock_container)

        assert compat.container is mock_container

    def test_shutdown_clears_container(self):
        """Test shutdown clears container."""
        compat = ToolCompatibility()
        mock_container = Mock()
        compat.container = mock_container

        compat.shutdown()

        assert compat.container is None


class TestCompatibilityCheckerAPI:
    """Test CompatibilityChecker API methods."""

    def test_register_api_version(self):
        """Test registering API version."""
        checker = CompatibilityChecker()

        checker.register_api_version("test_tool", "1.0.0")

        assert checker._api_versions["test_tool"] == "1.0.0"

    def test_register_dependency_constraint(self):
        """Test registering dependency constraint."""
        checker = CompatibilityChecker()

        checker.register_dependency_constraint("dep1", ">=1.0.0")

        assert checker._dependency_constraints["dep1"] == ">=1.0.0"

    def test_get_supported_python_versions(self):
        """Test getting supported Python versions."""
        checker = CompatibilityChecker()

        versions = checker.get_supported_python_versions()

        assert isinstance(versions, list)
        assert len(versions) > 0


class TestVersionParsing:
    """Test version parsing methods."""

    def test_parse_version_with_alpha(self):
        """Test parsing version with alpha suffix."""
        checker = CompatibilityChecker()

        result = checker._parse_version("1.0.0-alpha")

        assert result == [1, 0, 0]

    def test_parse_version_with_beta(self):
        """Test parsing version with beta suffix."""
        checker = CompatibilityChecker()

        result = checker._parse_version("2.0.0-beta.1")

        assert result == [2, 0, 0]

    def test_parse_version_with_dev(self):
        """Test parsing version with dev suffix."""
        checker = CompatibilityChecker()

        result = checker._parse_version("1.0.0.dev1")

        assert result == [1, 0, 0]

    def test_parse_version_with_plus(self):
        """Test parsing version with + suffix."""
        checker = CompatibilityChecker()

        result = checker._parse_version("1.0.0+build123")

        assert result == [1, 0, 0]


class TestVersionComparisonEdgeCases:
    """Test version comparison edge cases."""

    def test_version_matches_different_lengths(self):
        """Test version matching with different version lengths."""
        checker = CompatibilityChecker()

        # Installed has more parts than required
        assert checker._version_matches('1.2.3.4', '1.2') is True

    def test_version_satisfies_min_different_lengths(self):
        """Test min version with different lengths."""
        checker = CompatibilityChecker()

        # 1.2.3 >= 1.2
        assert checker._version_satisfies_min('1.2.3', '1.2') is True

        # 1.2 >= 1.2.3 - depends on implementation
        assert checker._version_satisfies_min('1.2', '1.2.3') is False

    def test_version_satisfies_max_different_lengths(self):
        """Test max version with different lengths."""
        checker = CompatibilityChecker()

        # 1.2 <= 1.2.3
        assert checker._version_satisfies_max('1.2', '1.2.3') is True

        # 1.2.3 <= 1.2
        assert checker._version_satisfies_max('1.2.3', '1.2') is False


class TestAPICompatibilityEdgeCases:
    """Test API compatibility edge cases."""

    def test_api_version_empty_strings(self):
        """Test API compatibility with empty strings."""
        checker = CompatibilityChecker()

        is_compat = checker._api_version_compatible("", "")

        # Empty strings should return False
        assert is_compat is False


class TestIsVersionCompatible:
    """Test is_version_compatible method - checks if two versions are mutually compatible."""

    def test_is_version_compatible_same_version(self):
        """Test version compatibility with same version."""
        checker = CompatibilityChecker()

        # Same version should always be compatible
        assert checker.is_version_compatible('1.0.0', '1.0.0', 'major') is True
        assert checker.is_version_compatible('1.0.0', '1.0.0', 'minor') is True
        assert checker.is_version_compatible('1.0.0', '1.0.0', 'patch') is True

    def test_is_version_compatible_major_different(self):
        """Test version compatibility with different major versions."""
        checker = CompatibilityChecker()

        # Different major versions are not compatible with major tolerance
        assert checker.is_version_compatible('2.0.0', '1.0.0', 'major') is False
        assert checker.is_version_compatible('1.0.0', '2.0.0', 'major') is False

    def test_is_version_compatible_minor_different(self):
        """Test version compatibility with different minor versions."""
        checker = CompatibilityChecker()

        # Different minor versions are not compatible with minor tolerance
        assert checker.is_version_compatible('1.2.0', '1.3.0', 'minor') is False
        assert checker.is_version_compatible('1.3.0', '1.2.0', 'minor') is False

    def test_is_version_compatible_patch_different(self):
        """Test version compatibility with different patch versions."""
        checker = CompatibilityChecker()

        # Different patch versions are not compatible with patch tolerance
        assert checker.is_version_compatible('1.2.3', '1.2.4', 'patch') is False
        assert checker.is_version_compatible('1.2.4', '1.2.3', 'patch') is False

    def test_is_version_compatible_invalid_tolerance(self):
        """Test version compatibility with invalid tolerance."""
        checker = CompatibilityChecker()

        # Invalid tolerance always returns False
        assert checker.is_version_compatible('1.2.3', '1.2.3', 'invalid') is False

    def test_is_version_compatible_exception(self):
        """Test version compatibility with exception handling."""
        checker = CompatibilityChecker()

        # Invalid version strings that raise exceptions
        assert checker.is_version_compatible('invalid', '1.0.0') is False


class TestCompatibilityCheckerFull:
    """Test full compatibility checker scenarios."""

    def test_check_tool_compatibility_min_version(self):
        """Test check_tool_compatibility with min version constraint."""
        checker = CompatibilityChecker()

        tool_info = {
            'name': 'test_tool',
            'python_version': '3.9',
            'dependencies': {
                'dep1': '>=1.0.0'
            }
        }

        with patch.object(checker, 'check_python_compatibility', return_value=(True, "")), \
             patch.object(checker, 'check_dependency_compatibility', return_value=(True, "")):
            is_compat, issues = checker.check_tool_compatibility(tool_info)
            assert is_compat is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
