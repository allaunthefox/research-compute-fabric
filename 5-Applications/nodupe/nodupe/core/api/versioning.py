# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""API Versioning Module.

Provides API versioning functionality with support for multiple API versions
and version-aware request handling.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, Dict, Optional, Set
from dataclasses import dataclass


@dataclass
class VersionedFunction:
    """Wrapper for a versioned function.

    Holds metadata about a function that has been decorated with version
    information, including the version string and deprecation status.

    Attributes:
        func: The wrapped callable function.
        version: The API version string (e.g., "v1", "v2").
        deprecated: Whether this version is deprecated. Default is False.
        deprecation_message: Optional message explaining the deprecation.
    """
    func: Callable[..., Any]
    version: str
    deprecated: bool = False
    deprecation_message: Optional[str] = None


class APIVersion:
    """API Version Manager.

    Manages API versions and provides version-aware routing for endpoints.
    Supports multiple API versions with deprecation warnings.
    """

    def __init__(self, default_version: str = "v1") -> None:
        """Initialize API version manager.

        Args:
            default_version: The default API version to use. Default is "v1".
        """
        self.current_version: str = default_version
        self.supported_versions: Set[str] = {default_version}
        self.versioned_functions: Dict[str, Dict[str, VersionedFunction]] = {}
        self._deprecated_versions: Dict[str, str] = {}

    def register_version(self, version: str) -> None:
        """Register a new API version.

        Adds a new version to the set of supported API versions.

        Args:
            version: The version string to register (e.g., "v2", "v3").
        """
        self.supported_versions.add(version)

    def set_current_version(self, version: str) -> None:
        """Set the current/default API version.

        Args:
            version: The version string to set as current.

        Raises:
            ValueError: If the version has not been registered.
        """
        if version not in self.supported_versions:
            raise ValueError(f"Version {version} not registered.")
        self.current_version = version

    def deprecate_version(self, version: str, deprecated_by: Optional[str] = None) -> None:
        """Mark an API version as deprecated.

        Args:
            version: The version string to deprecate.
            deprecated_by: The version that replaces this version. Default is "future".
        """
        if version in self.supported_versions:
            self._deprecated_versions[version] = deprecated_by or "future"

    def is_version_supported(self, version: str) -> bool:
        """Check if a version is supported.

        Args:
            version: The version string to check.

        Returns:
            True if the version is supported, False otherwise.
        """
        return version in self.supported_versions

    def is_version_deprecated(self, version: str) -> bool:
        """Check if a version is deprecated.

        Args:
            version: The version string to check.

        Returns:
            True if the version is deprecated, False otherwise.
        """
        return version in self._deprecated_versions

    def get_deprecation_message(self, version: str) -> str:
        """Get deprecation message for a version.

        Args:
            version: The version string to get the message for.

        Returns:
            A human-readable deprecation message.
        """
        replacement = self._deprecated_versions.get(version, "future")
        return f"API version {version} is deprecated. Please use {replacement}."


def versioned(version: str, deprecated: bool = False) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to mark a function with a specific API version.

    Attaches version metadata to a function and optionally emits deprecation
    warnings when the function is called.

    Args:
        version: The API version string (e.g., "v1", "v2").
        deprecated: If True, emits a DeprecationWarning when called. Default is False.

    Returns:
        A decorator function that marks the function with version information.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Inner decorator that attaches version metadata to the function.

        Args:
            func: The function to decorate with version information.

        Returns:
            The wrapped function with version metadata attached.
        """
        func._api_version = version
        func._api_deprecated = deprecated

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function that handles deprecation warnings.

            Calls the decorated function and emits a deprecation warning
            if the function is marked as deprecated.

            Args:
                *args: Positional arguments to pass to the decorated function.
                **kwargs: Keyword arguments to pass to the decorated function.

            Returns:
                The result of calling the decorated function.
            """
            if deprecated:
                import warnings
                warnings.warn(f"API version {version} is deprecated", DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        wrapper._api_version = version
        wrapper._api_deprecated = deprecated
        return wrapper

    return decorator


def get_api_version(func: Callable[..., Any]) -> Optional[str]:
    """Get the API version for a function.

    Args:
        func: The function to get the version from.

    Returns:
        The API version string if set, None otherwise.
    """
    return getattr(func, '_api_version', None)


def is_api_deprecated(func: Callable[..., Any]) -> bool:
    """Check if a function is marked as deprecated.

    Args:
        func: The function to check.

    Returns:
        True if the function is marked as deprecated, False otherwise.
    """
    return getattr(func, '_api_deprecated', False)
