# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for simple core modules - errors and deps."""

import pytest

# Test core.errors module
from nodupe.core.errors import NoDupeError


class TestErrors:
    """Test error classes."""

    def test_nodupe_error(self):
        """Test NoDupeError."""
        error = NoDupeError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_nodupe_error_base(self):
        """Test NoDupeError as base for other errors."""
        class CustomError(NoDupeError):
            """Custom error class for testing NoDupeError as base."""
            pass
        error = CustomError("Custom error")
        assert str(error) == "Custom error"
        assert isinstance(error, NoDupeError)


# Test core.deps module
from nodupe.core.deps import DependencyManager, dep_manager


class TestDependencyManager:
    """Test DependencyManager class."""

    def test_singleton_exists(self):
        """Test dep_manager singleton exists."""
        assert dep_manager is not None
        assert isinstance(dep_manager, DependencyManager)


# Test core.hasher_interface module - it's an ABC so we just verify it exists
from nodupe.core.hasher_interface import HasherInterface


class TestHasherInterface:
    """Test HasherInterface class."""

    def test_is_abc(self):
        """Test HasherInterface is an abstract base class."""
        # HasherInterface is an ABC - we can check it has abstract methods
        import inspect
        abstract_methods = [name for name, method in inspect.getmembers(HasherInterface, predicate=inspect.isfunction)
                          if getattr(method, '__isabstractmethod__', False)]
        assert len(abstract_methods) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
