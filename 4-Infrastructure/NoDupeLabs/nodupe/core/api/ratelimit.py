# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Rate Limiting Module.

Provides rate limiting functionality using sliding window algorithm.
"""

from __future__ import annotations

import functools
import time
from collections import deque
from typing import Any, Callable, Deque, Dict, Optional


class RateLimiter:
    """Sliding Window Rate Limiter.

    Implements rate limiting using a sliding window algorithm to track
    request timestamps and enforce rate limits.
    """

    def __init__(self, requests_per_minute: int = 60) -> None:
        """Initialize rate limiter.

        Args:
            requests_per_minute: Maximum number of requests allowed per minute.
                                Default is 60 requests.
        """
        self.requests_per_minute = requests_per_minute
        self.window_size: float = 60.0
        self._requests: Dict[str, Deque[float]] = {}

    def check_rate_limit(self, client_id: Optional[str] = None) -> bool:
        """Check if request is within rate limit.

        Uses a sliding window algorithm to track request timestamps and
        determine if the current request should be allowed.

        Args:
            client_id: Optional client identifier for per-client rate limiting.
                       If None, uses a default key.

        Returns:
            True if the request is allowed, False if rate limit is exceeded.
        """
        key = client_id or "default"
        current_time = time.time()

        if key not in self._requests:
            self._requests[key] = deque()

        window_start = current_time - self.window_size
        while self._requests[key] and self._requests[key][0] <= window_start:
            self._requests[key].popleft()

        if len(self._requests[key]) < self.requests_per_minute:
            self._requests[key].append(current_time)
            return True

        return False

    def throttle(self, client_id: Optional[str] = None) -> float:
        """Get wait time until next request is allowed.

        Calculates how long a client must wait before their next request
        will be allowed under the rate limit.

        Args:
            client_id: Optional client identifier. If None, uses a default key.

        Returns:
            Time in seconds to wait before the next request is allowed.
            Returns 0.0 if no waiting is required.
        """
        key = client_id or "default"

        if key not in self._requests or not self._requests[key]:
            return 0.0

        oldest = self._requests[key][0]
        current_time = time.time()
        window_start = current_time - self.window_size

        if oldest < window_start:
            return 0.0

        return oldest + self.window_size - current_time + 0.1


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: float = 0.0) -> None:
        """Initialize rate limit exception.

        Args:
            message: Error message describing the rate limit violation.
            retry_after: Number of seconds the client should wait before retrying.
        """
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


def rate_limited(requests_per_minute: int = 60) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to apply rate limiting to a function.

    Wraps a function with rate limiting using the RateLimiter class.
    Raises RateLimitExceeded if the rate limit is exceeded.

    Args:
        requests_per_minute: Maximum number of requests allowed per minute.
                            Default is 60 requests.

    Returns:
        A decorator function that applies rate limiting to the wrapped function.

    Raises:
        RateLimitExceeded: If the rate limit is exceeded.
    """
    limiter = RateLimiter(requests_per_minute=requests_per_minute)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator that wraps a function with rate limiting.

        Args:
            func: The function to be wrapped with rate limiting.

        Returns:
            The wrapped function with rate limiting applied.
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function that enforces rate limiting.

            Checks the rate limit before calling the wrapped function.
            Raises RateLimitExceeded if the rate limit is exceeded.

            Args:
                *args: Positional arguments passed to the wrapped function.
                **kwargs: Keyword arguments passed to the wrapped function.

            Returns:
                The result of the wrapped function if rate limit is not exceeded.

            Raises:
                RateLimitExceeded: If the rate limit is exceeded.
            """
            if not limiter.check_rate_limit():
                wait_time = limiter.throttle()
                raise RateLimitExceeded(f"Rate limit exceeded. Try again in {wait_time:.1f} seconds.", retry_after=wait_time)
            return func(*args, **kwargs)
        return wrapper

    return decorator
