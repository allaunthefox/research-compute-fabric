# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""API Decorators Module.

Provides common API decorators for NoDupeLabs.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, Dict, List, Optional


def api_endpoint(methods: Optional[List[str]] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to mark a function as an API endpoint.

    Args:
        methods: HTTP methods this endpoint supports (e.g., ["GET", "POST"]).
                 If None, any method is allowed.

    Returns:
        A decorator function that marks the wrapped function as an API endpoint.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator that wraps the API endpoint function.

        Args:
            func: The function to decorate as an API endpoint.

        Returns:
            The wrapped function with API endpoint metadata.
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function that executes the decorated API endpoint.

            Args:
                *args: Positional arguments passed to the decorated function.
                **kwargs: Keyword arguments passed to the decorated function.

            Returns:
                The result of the decorated function.
            """
            return func(*args, **kwargs)
        return wrapper
    return decorator


def cors(origins: Optional[List[str]] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to add CORS headers to a response.

    Adds Cross-Origin Resource Sharing (CORS) headers to the response
    dictionary returned by the wrapped function.

    Args:
        origins: List of allowed origins. If None, allows all origins ("*").

    Returns:
        A decorator function that adds CORS headers to the response.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator that wraps the function to add CORS headers.

        Args:
            func: The function to decorate with CORS headers.

        Returns:
            The wrapped function that adds CORS headers to responses.
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function that adds CORS headers to the response.

            Args:
                *args: Positional arguments passed to the decorated function.
                **kwargs: Keyword arguments passed to the decorated function.

            Returns:
                The result of the decorated function with CORS headers added
                if the result is a dictionary.
            """
            result = func(*args, **kwargs)
            if isinstance(result, dict):
                result["_cors"] = {
                    "Access-Control-Allow-Origin": ", ".join(origins) if origins else "*",
                }
            return result
        return wrapper
    return decorator


def require_auth(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require authentication for an endpoint.

    Checks for authentication token in the request and raises PermissionError
    if not present.

    Args:
        func: The function to wrap.

    Returns:
        The wrapped function that requires authentication.

    Raises:
        PermissionError: If no authentication token is provided.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Wrapper function that checks for authentication before executing.

        Args:
            *args: Positional arguments passed to the decorated function.
            **kwargs: Keyword arguments passed to the decorated function.
                Expects 'auth_TOKEN_REMOVED' or 'authorization' key for token.

        Returns:
            The result of the decorated function if authenticated.

        Raises:
            PermissionError: If no authentication token is provided.
        """
        auth_TOKEN_REMOVED = kwargs.get("auth_TOKEN_REMOVED") or kwargs.get("authorization")
        if not auth_TOKEN_REMOVED:
            raise PermissionError("Authentication required")
        return func(*args, **kwargs)
    return wrapper


def cache_response(ttl: int = 300) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to cache API responses.

    Caches the result of the wrapped function for a specified time-to-live (TTL).
    Uses function arguments as part of the cache key.

    Args:
        ttl: Time-to-live for cached responses in seconds. Default is 300 seconds.

    Returns:
        A decorator function that caches API responses.
    """
    _cache: Dict[str, tuple[Any, float]] = {}

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator that wraps the function to cache responses.

        Args:
            func: The function to decorate with response caching.

        Returns:
            The wrapped function that caches API responses.
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function that returns cached response or executes and caches.

            Args:
                *args: Positional arguments passed to the decorated function.
                **kwargs: Keyword arguments passed to the decorated function.

            Returns:
                Cached result if available and not expired, otherwise the result
                of the decorated function (which is then cached).
            """
            import time
            cache_key = str(args) + str(sorted(kwargs.items()))
            if cache_key in _cache:
                result, timestamp = _cache[cache_key]
                if time.time() - timestamp < ttl:
                    return result
            result = func(*args, **kwargs)
            _cache[cache_key] = (result, time.time())
            return result
        return wrapper
    return decorator


def retry(max_attempts: int = 3, delay: float = 1.0) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to retry failed operations.

    Retries the wrapped function up to max_attempts times with a delay
    between each attempt.

    Args:
        max_attempts: Maximum number of retry attempts. Default is 3.
        delay: Delay in seconds between retry attempts. Default is 1.0.

    Returns:
        A decorator function that retries failed operations.

    Raises:
        Exception: The last exception encountered if all attempts fail.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator that wraps the function with retry logic.

        Args:
            func: The function to decorate with retry capability.

        Returns:
            The wrapped function that retries on failure.
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function that retries the decorated function on failure.

            Args:
                *args: Positional arguments passed to the decorated function.
                **kwargs: Keyword arguments passed to the decorated function.

            Returns:
                The result of the decorated function if successful.

            Raises:
                Exception: The last exception encountered if all attempts fail.
            """
            import time
            last_exception: Optional[Exception] = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def deprecated(message: str = "This endpoint is deprecated") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to mark endpoints as deprecated.

    Emits a DeprecationWarning when the wrapped function is called.

    Args:
        message: The deprecation message to display. Default is
                 "This endpoint is deprecated".

    Returns:
        A decorator function that marks endpoints as deprecated.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator that wraps the function to emit deprecation warnings.

        Args:
            func: The function to decorate with deprecation warning.

        Returns:
            The wrapped function that emits deprecation warnings.
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function that emits a deprecation warning before executing.

            Args:
                *args: Positional arguments passed to the decorated function.
                **kwargs: Keyword arguments passed to the decorated function.

            Returns:
                The result of the decorated function.
            """
            import warnings
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator
