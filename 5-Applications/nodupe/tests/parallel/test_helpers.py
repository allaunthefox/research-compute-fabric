# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Pickle-safe helper functions for parallel processing tests.

This module provides functions that can be pickled and sent to worker processes.
These are used to test ProcessPoolExecutor code paths that lambdas cannot test.

See: https://docs.python.org/3/library/pickle.html#what-can-be-pickled
"""

from typing import List, Tuple, Any, Optional
import time


def square_number(x: int) -> int:
    """Square a number - pickle-safe for process testing.

    Args:
        x: Number to square

    Returns:
        x squared
    """
    return x * x


def double_number(x: int) -> int:
    """Double a number - pickle-safe.

    Args:
        x: Number to double

    Returns:
        x doubled
    """
    return x + x


def is_even(x: int) -> bool:
    """Check if number is even - pickle-safe.

    Args:
        x: Number to check

    Returns:
        True if x is even, False otherwise
    """
    return x % 2 == 0


def add_numbers(a: int, b: int) -> int:
    """Add two numbers - pickle-safe for starmap testing.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b


def multiply_numbers(a: int, b: int) -> int:
    """Multiply two numbers - pickle-safe.

    Args:
        a: First number
        b: Second number

    Returns:
        Product of a and b
    """
    return a * b


def identity(x: Any) -> Any:
    """Return input unchanged - pickle-safe.

    Args:
        x: Any value

    Returns:
        The same value
    """
    return x


def add_one(x: int) -> int:
    """Add one to number - pickle-safe.

    Args:
        x: Number to increment

    Returns:
        x + 1
    """
    return x + 1


def slow_square(x: int, delay: float = 0.1) -> int:
    """Square with delay - for testing timeouts and progress.

    Args:
        x: Number to square
        delay: Delay in seconds

    Returns:
        x squared
    """
    time.sleep(delay)
    return x * x


def count_letters(text: str) -> int:
    """Count letters in string - pickle-safe.

    Args:
        text: String to count

    Returns:
        Number of characters
    """
    return len(text)


def to_uppercase(text: str) -> str:
    """Convert to uppercase - pickle-safe.

    Args:
        text: String to convert

    Returns:
        Uppercase string
    """
    return text.upper()


def filter_positive(x: int) -> bool:
    """Check if number is positive - pickle-safe.

    Args:
        x: Number to check

    Returns:
        True if x > 0
    """
    return x > 0


def sum_list(numbers: List[int]) -> int:
    """Sum a list of numbers - pickle-safe for reduce operations.

    Args:
        numbers: List of numbers

    Returns:
        Sum of all numbers
    """
    return sum(numbers)


def concat_strings(a: str, b: str) -> str:
    """Concatenate two strings - pickle-safe.

    Args:
        a: First string
        b: Second string

    Returns:
        Concatenated string
    """
    return a + b


def create_pair(x: int) -> Tuple[int, int]:
    """Create a pair from number - pickle-safe.

    Args:
        x: Number

    Returns:
        Tuple of (x, x*2)
    """
    return (x, x * 2)


def unpack_and_add(pair: Tuple[int, int]) -> int:
    """Unpack pair and add - pickle-safe.

    Args:
        pair: Tuple of two numbers

    Returns:
        Sum of the pair
    """
    return pair[0] + pair[1]


def maybe_raise(x: int) -> int:
    """Raise error for specific value - for testing error handling.

    Args:
        x: Number to process

    Returns:
        x squared

    Raises:
        ValueError: If x is -1
    """
    if x == -1:
        raise ValueError("Error for value -1")
    return x * x


def slow_operation(x: int, delay: float = 0.5) -> int:
    """Slow operation for timeout testing.

    Args:
        x: Number to square
        delay: Delay in seconds

    Returns:
        x squared
    """
    time.sleep(delay)
    return x * x


def track_calls(x: int, call_tracker: Optional[List] = None) -> int:
    """Track function calls - for testing call verification.

    Note: call_tracker must be passed explicitly as default args are evaluated once.

    Args:
        x: Number to process
        call_tracker: Optional list to track calls

    Returns:
        x squared
    """
    if call_tracker is not None:
        call_tracker.append(x)
    return x * 2


class PicklableCounter:
    """Picklable counter for testing stateful operations.

    This class is picklable and can be used in multiprocessing tests.
    """

    def __init__(self, start: int = 0):
        """Initialize counter.

        Args:
            start: Starting value
        """
        self.count = start

    def increment(self, value: int) -> int:
        """Increment and return new value.

        Args:
            value: Value to add

        Returns:
            New count value
        """
        self.count += value
        return self.count

    def get_count(self) -> int:
        """Get current count.

        Returns:
            Current count value
        """
        return self.count

    def __call__(self, x: int) -> int:
        """Call interface - add x to count.

        Args:
            x: Value to add

        Returns:
            New count value
        """
        return self.increment(x)


def reducer_add(a: int, b: int) -> int:
    """Reducer function for add operations.

    Args:
        a: Accumulator
        b: Next value

    Returns:
        Sum of a and b
    """
    return a + b


def reducer_multiply(a: int, b: int) -> int:
    """Reducer function for multiply operations.

    Args:
        a: Accumulator
        b: Next value

    Returns:
        Product of a and b
    """
    return a * b


def reducer_max(a: int, b: int) -> int:
    """Reducer function for max operations.

    Args:
        a: Current max
        b: Next value

    Returns:
        Maximum of a and b
    """
    return max(a, b)


# Predefined test data sets
SMALL_INT_RANGE = list(range(10))
MEDIUM_INT_RANGE = list(range(100))
LARGE_INT_RANGE = list(range(1000))

SMALL_STRINGS = ["a", "b", "c", "d", "e"]
MIXED_NUMBERS = [-5, -2, 0, 1, 3, 7, 10]
POSITIVE_NUMBERS = [1, 2, 3, 4, 5]
NEGATIVE_NUMBERS = [-5, -4, -3, -2, -1]
