# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Coverage tests for nodupe/core/api/versioning.py."""

import warnings

import pytest

from nodupe.core.api.versioning import (
    APIVersion,
    VersionedFunction,
    get_api_version,
    is_api_deprecated,
    versioned,
)


def test_api_version_manager():
    """Test APIVersion manager class."""
    manager = APIVersion(default_version="v1")
    assert manager.current_version == "v1"
    assert manager.is_version_supported("v1")
    assert not manager.is_version_deprecated("v1")
    
    # Register and set current
    manager.register_version("v2")
    assert manager.is_version_supported("v2")
    manager.set_current_version("v2")
    assert manager.current_version == "v2"
    
    # Set unregistered version
    with pytest.raises(ValueError, match="not registered"):
        manager.set_current_version("v3")
        
    # Deprecate
    manager.deprecate_version("v1", deprecated_by="v2")
    assert manager.is_version_deprecated("v1")
    assert "is deprecated. Please use v2" in manager.get_deprecation_message("v1")
    
    # Deprecate by future
    manager.register_version("v3")
    manager.deprecate_version("v3")
    assert "Please use future" in manager.get_deprecation_message("v3")

def test_versioned_decorator():
    """Test versioned decorator."""
    @versioned("v1")
    def func_v1():
        """Test function for v1 version."""
        return "v1"
        
    @versioned("v2", deprecated=True)
    def func_v2():
        """Test function for v2 version (deprecated)."""
        return "v2"
        
    assert get_api_version(func_v1) == "v1"
    assert not is_api_deprecated(func_v1)
    assert func_v1() == "v1"
    
    assert get_api_version(func_v2) == "v2"
    assert is_api_deprecated(func_v2)
    
    with pytest.warns(DeprecationWarning, match="v2 is deprecated"):
        assert func_v2() == "v2"

def test_versioned_function_dataclass():
    """Test VersionedFunction dataclass."""
    def sample():
        """Sample function for testing VersionedFunction dataclass."""
        pass
    vf = VersionedFunction(func=sample, version="v1", deprecated=True, deprecation_message="msg")
    assert vf.version == "v1"
    assert vf.deprecated is True
    assert vf.deprecation_message == "msg"
