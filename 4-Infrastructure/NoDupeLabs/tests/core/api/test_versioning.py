# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Comprehensive tests for the versioning module."""

import warnings

import pytest

from nodupe.core.api.versioning import (
    APIVersion,
    VersionedFunction,
    get_api_version,
    is_api_deprecated,
    versioned,
)


class TestVersionedFunction:
    """Test VersionedFunction dataclass."""

    def test_versioned_function_creation(self):
        """Test VersionedFunction creation."""
        def my_func():
            """Test function for VersionedFunction."""
            pass

        vf = VersionedFunction(func=my_func, version="v1")
        assert vf.func is my_func
        assert vf.version == "v1"
        assert vf.deprecated is False
        assert vf.deprecation_message is None

    def test_versioned_function_with_deprecation(self):
        """Test VersionedFunction with deprecation."""
        def my_func():
            """Test function for VersionedFunction."""
            pass

        vf = VersionedFunction(
            func=my_func,
            version="v1",
            deprecated=True,
            deprecation_message="Use v2 instead"
        )
        assert vf.deprecated is True
        assert vf.deprecation_message == "Use v2 instead"


class TestAPIVersionInitialization:
    """Test APIVersion initialization."""

    def test_init_default(self):
        """Test API version initialization with default."""
        api = APIVersion()
        assert api.current_version == "v1"
        assert "v1" in api.supported_versions

    def test_init_custom_version(self):
        """Test API version initialization with custom version."""
        api = APIVersion(default_version="v2")
        assert api.current_version == "v2"
        assert "v2" in api.supported_versions


class TestAPIVersionRegisterVersion:
    """Test APIVersion register_version method."""

    def test_register_version(self):
        """Test registering a new version."""
        api = APIVersion()
        api.register_version("v2")
        assert "v2" in api.supported_versions

    def test_register_multiple_versions(self):
        """Test registering multiple versions."""
        api = APIVersion()
        api.register_version("v2")
        api.register_version("v3")
        api.register_version("v4")
        assert "v2" in api.supported_versions
        assert "v3" in api.supported_versions
        assert "v4" in api.supported_versions

    def test_register_duplicate_version(self):
        """Test registering duplicate version (should be idempotent)."""
        api = APIVersion()
        api.register_version("v1")  # Already exists
        # Sets don't allow duplicates, so count is always 1
        assert "v1" in api.supported_versions
        # Verify it's still just one entry (set property)
        assert len([v for v in api.supported_versions if v == "v1"]) == 1


class TestAPIVersionSetCurrentVersion:
    """Test APIVersion set_current_version method."""

    def test_set_current_version(self):
        """Test setting current version."""
        api = APIVersion()
        api.register_version("v2")
        api.set_current_version("v2")
        assert api.current_version == "v2"

    def test_set_current_version_same(self):
        """Test setting current version to same version."""
        api = APIVersion()
        api.set_current_version("v1")
        assert api.current_version == "v1"

    def test_set_current_version_invalid(self):
        """Test setting invalid version raises error."""
        api = APIVersion()
        with pytest.raises(ValueError, match="Version v999 not registered"):
            api.set_current_version("v999")

    def test_set_current_version_unregistered(self):
        """Test setting unregistered version raises error."""
        api = APIVersion()
        with pytest.raises(ValueError):
            api.set_current_version("v3")


class TestAPIVersionDeprecateVersion:
    """Test APIVersion deprecate_version method."""

    def test_deprecate_version(self):
        """Test deprecating a version."""
        api = APIVersion()
        api.deprecate_version("v1", "v2")
        assert api.is_version_deprecated("v1")

    def test_deprecate_version_without_replacement(self):
        """Test deprecating a version without specifying replacement."""
        api = APIVersion()
        api.deprecate_version("v1")
        assert api.is_version_deprecated("v1")

    def test_deprecate_nonexistent_version(self):
        """Test deprecating a version that doesn't exist."""
        api = APIVersion()
        # Should not raise, just silently do nothing
        api.deprecate_version("v999")
        assert not api.is_version_deprecated("v999")

    def test_deprecate_multiple_versions(self):
        """Test deprecating multiple versions."""
        api = APIVersion()
        api.register_version("v2")
        api.register_version("v3")
        api.deprecate_version("v1", "v2")
        api.deprecate_version("v2", "v3")
        assert api.is_version_deprecated("v1")
        assert api.is_version_deprecated("v2")


class TestAPIVersionIsVersionSupported:
    """Test APIVersion is_version_supported method."""

    def test_is_version_supported_true(self):
        """Test checking supported version."""
        api = APIVersion()
        assert api.is_version_supported("v1") is True

    def test_is_version_supported_false(self):
        """Test checking unsupported version."""
        api = APIVersion()
        assert api.is_version_supported("v999") is False

    def test_is_version_supported_after_register(self):
        """Test checking version after registration."""
        api = APIVersion()
        api.register_version("v2")
        assert api.is_version_supported("v2") is True


class TestAPIVersionIsVersionDeprecated:
    """Test APIVersion is_version_deprecated method."""

    def test_is_version_deprecated_true(self):
        """Test checking deprecated version."""
        api = APIVersion()
        api.deprecate_version("v1", "v2")
        assert api.is_version_deprecated("v1") is True

    def test_is_version_deprecated_false(self):
        """Test checking non-deprecated version."""
        api = APIVersion()
        assert api.is_version_deprecated("v1") is False

    def test_is_version_deprecated_nonexistent(self):
        """Test checking non-existent version."""
        api = APIVersion()
        assert api.is_version_deprecated("v999") is False


class TestAPIVersionGetDeprecationMessage:
    """Test APIVersion get_deprecation_message method."""

    def test_get_deprecation_message_with_replacement(self):
        """Test getting deprecation message with replacement."""
        api = APIVersion()
        api.deprecate_version("v1", "v2")
        msg = api.get_deprecation_message("v1")
        assert "v1" in msg
        assert "v2" in msg
        assert "deprecated" in msg.lower()

    def test_get_deprecation_message_without_replacement(self):
        """Test getting deprecation message without replacement."""
        api = APIVersion()
        api.deprecate_version("v1")
        msg = api.get_deprecation_message("v1")
        assert "v1" in msg
        assert "deprecated" in msg.lower()

    def test_get_deprecation_message_non_deprecated(self):
        """Test getting deprecation message for non-deprecated version."""
        api = APIVersion()
        msg = api.get_deprecation_message("v1")
        # Should still return a message with default replacement
        assert "v1" in msg


class TestVersionedDecorator:
    """Test versioned decorator."""

    def test_decorator_basic(self):
        """Test basic decorator functionality."""
        @versioned("v1")
        def test_func():
            """Test function for versioned decorator."""
            return "success"

        result = test_func()
        assert result == "success"
        assert test_func._api_version == "v1"
        assert test_func._api_deprecated is False

    def test_decorator_with_deprecation(self):
        """Test decorator with deprecation."""
        @versioned("v1", deprecated=True)
        def test_func():
            """Test function for versioned decorator."""
            return "success"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = test_func()
            assert result == "success"
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "v1" in str(w[0].message)

        assert test_func._api_version == "v1"
        assert test_func._api_deprecated is True

    def test_decorator_preserves_function_name(self):
        """Test decorator preserves function name."""
        @versioned("v1")
        def my_versioned_function():
            """Versioned function for name test."""
            return "success"

        assert my_versioned_function.__name__ == "my_versioned_function"

    def test_decorator_preserves_docstring(self):
        """Test decorator preserves docstring."""
        @versioned("v1")
        def my_versioned_function():
            """Versioned function with docstring."""
            """This is a versioned function."""
            return "success"

        assert my_versioned_function.__doc__ == "This is a versioned function."

    def test_decorator_with_args(self):
        """Test decorator with function arguments."""
        @versioned("v1")
        def test_func(a, b):
            """Test function with arguments."""
            return a + b

        result = test_func(1, 2)
        assert result == 3

    def test_decorator_with_kwargs(self):
        """Test decorator with keyword arguments."""
        @versioned("v1")
        def test_func(a, b=10):
            """Test function with keyword arguments."""
            return a + b

        result = test_func(1, b=20)
        assert result == 21

    def test_decorator_custom_version(self):
        """Test decorator with custom version."""
        @versioned("v3.5.2")
        def test_func():
            """Test function for versioned decorator."""
            return "success"

        assert test_func._api_version == "v3.5.2"


class TestGetApiVersion:
    """Test get_api_version function."""

    def test_get_api_version_with_decorator(self):
        """Test getting API version from decorated function."""
        @versioned("v2")
        def test_func():
            """Test function for get_api_version."""
            return "success"

        version = get_api_version(test_func)
        assert version == "v2"

    def test_get_api_version_without_decorator(self):
        """Test getting API version from non-decorated function."""
        def test_func():
            """Test function without decorator."""
            return "success"

        version = get_api_version(test_func)
        assert version is None

    def test_get_api_version_none(self):
        """Test getting API version from None."""
        version = get_api_version(None)
        assert version is None


class TestIsApiDeprecated:
    """Test is_api_deprecated function."""

    def test_is_api_deprecated_true(self):
        """Test checking deprecated function."""
        @versioned("v1", deprecated=True)
        def test_func():
            """Test function for is_api_deprecated."""
            return "success"

        assert is_api_deprecated(test_func) is True

    def test_is_api_deprecated_false(self):
        """Test checking non-deprecated function."""
        @versioned("v1")
        def test_func():
            """Test function for is_api_deprecated."""
            return "success"

        assert is_api_deprecated(test_func) is False

    def test_is_api_deprecated_no_decorator(self):
        """Test checking function without decorator."""
        def test_func():
            """Test function without decorator."""
            return "success"

        assert is_api_deprecated(test_func) is False

    def test_is_api_deprecated_none(self):
        """Test checking None."""
        assert is_api_deprecated(None) is False


class TestAPIVersionIntegration:
    """Test APIVersion integration scenarios."""

    def test_complete_versioning_workflow(self):
        """Test complete API versioning workflow."""
        api = APIVersion()

        # Register versions
        api.register_version("v1")
        api.register_version("v2")
        api.register_version("v3")

        # Set current
        api.set_current_version("v2")

        # Deprecate old
        api.deprecate_version("v1", "v2")

        # Verify
        assert api.is_version_supported("v1")
        assert api.is_version_supported("v2")
        assert api.is_version_supported("v3")
        assert api.is_version_deprecated("v1")
        assert not api.is_version_deprecated("v2")
        assert api.get_deprecation_message("v1") != ""

    def test_version_lifecycle(self):
        """Test version lifecycle."""
        api = APIVersion(default_version="v1")

        # Initial state
        assert api.current_version == "v1"
        assert api.is_version_supported("v1")
        assert not api.is_version_deprecated("v1")

        # Add new version
        api.register_version("v2")
        assert api.is_version_supported("v2")

        # Switch to new version
        api.set_current_version("v2")
        assert api.current_version == "v2"

        # Deprecate old version
        api.deprecate_version("v1", "v2")
        assert api.is_version_deprecated("v1")

        # Get deprecation message
        msg = api.get_deprecation_message("v1")
        assert "v1" in msg
        assert "v2" in msg


class TestVersioningEdgeCases:
    """Test versioning edge cases."""

    def test_empty_version_string(self):
        """Test with empty version string."""
        api = APIVersion()
        api.register_version("")
        assert "" in api.supported_versions

    def test_special_version_strings(self):
        """Test with special version strings."""
        api = APIVersion()
        api.register_version("v1.0.0-beta")
        api.register_version("v1.0.0-rc1")
        api.register_version("v1.0.0+build.123")
        assert "v1.0.0-beta" in api.supported_versions
        assert "v1.0.0-rc1" in api.supported_versions
        assert "v1.0.0+build.123" in api.supported_versions

    def test_deprecate_current_version(self):
        """Test deprecating the current version."""
        api = APIVersion()
        api.register_version("v2")
        api.set_current_version("v1")
        api.deprecate_version("v1", "v2")
        # Current version can be deprecated
        assert api.is_version_deprecated("v1")
        assert api.current_version == "v1"  # But still current

    def test_multiple_deprecations_same_version(self):
        """Test deprecating same version multiple times."""
        api = APIVersion()
        api.deprecate_version("v1", "v2")
        api.deprecate_version("v1", "v3")  # Should overwrite
        msg = api.get_deprecation_message("v1")
        assert "v3" in msg

    def test_versioned_decorator_multiple_functions(self):
        """Test versioned decorator on multiple functions."""
        @versioned("v1")
        def func1():
            """First test function."""
            return 1

        @versioned("v2")
        def func2():
            """Second test function."""
            return 2

        assert get_api_version(func1) == "v1"
        assert get_api_version(func2) == "v2"
        assert func1() == 1
        assert func2() == 2
