# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Final coverage tests for validator_logic.py - targeting 100% coverage.

This file specifically targets the remaining partial branches:
- validate_range with inclusive=False where value passes (lines 90->94, 99->102)
"""

import os
import tempfile
from pathlib import Path

import pytest

from nodupe.tools.security_audit.validator_logic import (
    ValidationError,
    Validators,
)

# =============================================================================
# Test validate_range - Exclusive bounds success cases (missing branches)
# =============================================================================

class TestValidateRangeExclusiveSuccess:
    """Test validate_range with inclusive=False where values pass validation.
    
    These tests target the partial branches at lines 90->94 and 99->102.
    """

    def test_validate_range_exclusive_min_passes(self):
        """validate_range with inclusive=False passes when value > min_val.
        
        This covers the branch at line 90->94 where inclusive=False
        and value > min_val (passes the check).
        """
        # Value 6 is strictly greater than min_val 5 (exclusive)
        result = Validators.validate_range(6, min_val=5, inclusive=False)
        assert result is True

    def test_validate_range_exclusive_max_passes(self):
        """validate_range with inclusive=False passes when value < max_val.
        
        This covers the branch at line 99->102 where inclusive=False
        and value < max_val (passes the check).
        """
        # Value 4 is strictly less than max_val 5 (exclusive)
        result = Validators.validate_range(4, max_val=5, inclusive=False)
        assert result is True

    def test_validate_range_exclusive_both_bounds_passes(self):
        """validate_range with inclusive=False passes when value is strictly within bounds.
        
        This covers both branches 90->94 and 99->102 in a single test.
        """
        # Value 5 is strictly between 0 and 10 (exclusive on both ends)
        result = Validators.validate_range(5, min_val=0, max_val=10, inclusive=False)
        assert result is True

    def test_validate_range_exclusive_float_passes(self):
        """validate_range with inclusive=False passes for float values strictly within bounds."""
        # Float value strictly within exclusive bounds
        result = Validators.validate_range(5.5, min_val=5.0, max_val=6.0, inclusive=False)
        assert result is True

    def test_validate_range_exclusive_min_only_passes(self):
        """validate_range with inclusive=False and only min_val passes when value > min."""
        result = Validators.validate_range(10, min_val=5, inclusive=False)
        assert result is True

    def test_validate_range_exclusive_max_only_passes(self):
        """validate_range with inclusive=False and only max_val passes when value < max."""
        result = Validators.validate_range(-10, max_val=5, inclusive=False)
        assert result is True

    def test_validate_range_exclusive_negative_values_passes(self):
        """validate_range with inclusive=False passes for negative values within bounds."""
        # -5 is strictly between -10 and 0 (exclusive)
        result = Validators.validate_range(-5, min_val=-10, max_val=0, inclusive=False)
        assert result is True


# =============================================================================
# Additional edge cases for comprehensive coverage
# =============================================================================

class TestValidateRangeEdgeCases:
    """Additional edge cases for validate_range to ensure full coverage."""

    def test_validate_range_zero_min_exclusive_positive_value(self):
        """validate_range with min_val=0, inclusive=False, positive value passes."""
        result = Validators.validate_range(1, min_val=0, inclusive=False)
        assert result is True

    def test_validate_range_zero_max_exclusive_negative_value(self):
        """validate_range with max_val=0, inclusive=False, negative value passes."""
        result = Validators.validate_range(-1, max_val=0, inclusive=False)
        assert result is True

    def test_validate_range_very_close_to_exclusive_min(self):
        """validate_range with value very close to exclusive min passes."""
        result = Validators.validate_range(5.0001, min_val=5.0, inclusive=False)
        assert result is True

    def test_validate_range_very_close_to_exclusive_max(self):
        """validate_range with value very close to exclusive max passes."""
        result = Validators.validate_range(9.9999, max_val=10.0, inclusive=False)
        assert result is True


# =============================================================================
# Comprehensive tests for all validator methods - edge cases
# =============================================================================

class TestValidateTypeEdgeCases:
    """Edge cases for validate_type."""

    def test_validate_type_none_with_allow_none_default_false(self):
        """validate_type with None and default allow_none=False raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_type(None, str)
        assert "Expected type str, got NoneType" in str(exc_info.value)

    def test_validate_type_bytes(self):
        """validate_type works with bytes type."""
        assert Validators.validate_type(b"hello", bytes) is True

    def test_validate_type_tuple(self):
        """validate_type works with tuple type."""
        assert Validators.validate_type((1, 2, 3), tuple) is True

    def test_validate_type_set(self):
        """validate_type works with set type."""
        assert Validators.validate_type({1, 2, 3}, set) is True


class TestValidateStringLengthEdgeCases:
    """Edge cases for validate_string_length."""

    def test_validate_string_length_min_equals_max(self):
        """validate_string_length with min_length == max_length."""
        assert Validators.validate_string_length("abc", min_length=3, max_length=3) is True

        with pytest.raises(ValidationError):
            Validators.validate_string_length("ab", min_length=3, max_length=3)

        with pytest.raises(ValidationError):
            Validators.validate_string_length("abcd", min_length=3, max_length=3)

    def test_validate_string_length_zero_min(self):
        """validate_string_length with min_length=0."""
        assert Validators.validate_string_length("", min_length=0) is True
        assert Validators.validate_string_length("a", min_length=0) is True

    def test_validate_string_length_zero_max(self):
        """validate_string_length with max_length=0."""
        assert Validators.validate_string_length("", max_length=0) is True

        with pytest.raises(ValidationError):
            Validators.validate_string_length("a", max_length=0)


class TestValidatePatternEdgeCases:
    """Edge cases for validate_pattern."""

    def test_validate_pattern_empty_string(self):
        """validate_pattern with empty string."""
        # Empty pattern matches empty string
        assert Validators.validate_pattern("", r"^$") is True

        # Non-empty pattern doesn't match empty string
        with pytest.raises(ValidationError):
            Validators.validate_pattern("", r".+")

    def test_validate_pattern_whitespace(self):
        """validate_pattern with whitespace patterns."""
        assert Validators.validate_pattern("hello world", r"^hello\s+world$") is True

    def test_validate_pattern_multiline(self):
        """validate_pattern with multiline strings."""
        # match() only matches from start
        assert Validators.validate_pattern("line1\nline2", r"^line1") is True


class TestValidateEmailEdgeCases:
    """Edge cases for validate_email."""

    def test_validate_email_subdomain(self):
        """validate_email with subdomain."""
        assert Validators.validate_email("user@mail.example.com") is True

    def test_validate_email_numeric_domain(self):
        """validate_email with numeric-looking domain (valid)."""
        assert Validators.validate_email("user@123.com") is True

    def test_validate_email_hyphen_in_domain(self):
        """validate_email with hyphen in domain."""
        assert Validators.validate_email("user@my-domain.com") is True

    def test_validate_email_empty_string(self):
        """validate_email with empty string."""
        with pytest.raises(ValidationError):
            Validators.validate_email("")


class TestValidatePathEdgeCases:
    """Edge cases for validate_path."""

    def test_validate_path_relative_path(self):
        """validate_path with relative path string."""
        # Just verify it doesn't raise for valid path format
        # (existence not required unless must_exist=True)
        assert Validators.validate_path("relative/path/file.txt") is True

    def test_validate_path_dot_path(self):
        """validate_path with dot path."""
        assert Validators.validate_path(".") is True
        assert Validators.validate_path("./file.txt") is True

    def test_validate_path_double_dot_path(self):
        """validate_path with double dot path."""
        assert Validators.validate_path("..") is True

    def test_validate_path_empty_string(self):
        """validate_path with empty string."""
        # Empty path is technically a valid Path object
        assert Validators.validate_path("") is True


class TestValidateEnumEdgeCases:
    """Edge cases for validate_enum."""

    def test_validate_enum_boolean_values(self):
        """validate_enum with boolean values."""
        assert Validators.validate_enum(True, [True, False]) is True
        assert Validators.validate_enum(False, [True, False]) is True

        with pytest.raises(ValidationError):
            Validators.validate_enum(True, [False])

    def test_validate_enum_tuple_values(self):
        """validate_enum with tuple values."""
        allowed = [(1, 2), (3, 4)]
        assert Validators.validate_enum((1, 2), allowed) is True

        with pytest.raises(ValidationError):
            Validators.validate_enum((5, 6), allowed)

    def test_validate_enum_dict_in_list(self):
        """validate_enum with dict value in allowed list."""
        # Dict comparison works with 'in' operator
        allowed = [{"key": "value"}]
        assert Validators.validate_enum({"key": "value"}, allowed) is True

        with pytest.raises(ValidationError):
            Validators.validate_enum({"other": "value"}, allowed)


class TestValidateDictKeysEdgeCases:
    """Edge cases for validate_dict_keys."""

    def test_validate_dict_keys_both_required_and_allowed(self):
        """validate_dict_keys with both required_keys and allowed_keys."""
        assert Validators.validate_dict_keys(
            {"a": 1, "b": 2},
            required_keys=["a"],
            allowed_keys=["a", "b", "c"]
        ) is True

    def test_validate_dict_keys_required_not_in_allowed(self):
        """validate_dict_keys when required key not in allowed keys."""
        # This is a logic edge case - required key must be in allowed
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_dict_keys(
                {"a": 1, "b": 2},
                required_keys=["a", "c"],  # c is required but not allowed
                allowed_keys=["a", "b"]
            )
        # Should fail on missing required key first
        assert "Missing required keys" in str(exc_info.value)

    def test_validate_dict_keys_empty_required_list(self):
        """validate_dict_keys with empty required_keys list."""
        assert Validators.validate_dict_keys({"a": 1}, required_keys=[]) is True

    def test_validate_dict_keys_empty_allowed_list(self):
        """validate_dict_keys with empty allowed_keys list."""
        # Only empty dict should pass
        assert Validators.validate_dict_keys({}, allowed_keys=[]) is True

        with pytest.raises(ValidationError):
            Validators.validate_dict_keys({"a": 1}, allowed_keys=[])


class TestValidateListItemsEdgeCases:
    """Edge cases for validate_list_items."""

    def test_validate_list_items_both_min_and_max(self):
        """validate_list_items with both min_items and max_items."""
        assert Validators.validate_list_items([1, 2, 3], int, min_items=2, max_items=5) is True

        with pytest.raises(ValidationError):
            Validators.validate_list_items([1], int, min_items=2, max_items=5)

        with pytest.raises(ValidationError):
            Validators.validate_list_items([1, 2, 3, 4, 5, 6], int, min_items=2, max_items=5)

    def test_validate_list_items_min_equals_max(self):
        """validate_list_items with min_items == max_items."""
        assert Validators.validate_list_items([1, 2, 3], int, min_items=3, max_items=3) is True

        with pytest.raises(ValidationError):
            Validators.validate_list_items([1, 2], int, min_items=3, max_items=3)

    def test_validate_list_items_zero_min(self):
        """validate_list_items with min_items=0."""
        assert Validators.validate_list_items([], int, min_items=0) is True
        assert Validators.validate_list_items([1], int, min_items=0) is True

    def test_validate_list_items_single_item(self):
        """validate_list_items with single item list."""
        assert Validators.validate_list_items([42], int) is True

        with pytest.raises(ValidationError):
            Validators.validate_list_items([42], str)


class TestValidateBooleanEdgeCases:
    """Edge cases for validate_boolean."""

    def test_validate_boolean_none(self):
        """validate_boolean with None."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_boolean(None)
        assert "Expected bool" in str(exc_info.value)

    def test_validate_boolean_empty_string(self):
        """validate_boolean with empty string."""
        with pytest.raises(ValidationError):
            Validators.validate_boolean("")

    def test_validate_boolean_negative_int(self):
        """validate_boolean with negative integer."""
        with pytest.raises(ValidationError):
            Validators.validate_boolean(-1)


class TestValidatePositiveEdgeCases:
    """Edge cases for validate_positive."""

    def test_validate_positive_very_small_positive(self):
        """validate_positive with very small positive number."""
        assert Validators.validate_positive(0.0000001) is True

    def test_validate_positive_very_large_positive(self):
        """validate_positive with very large positive number."""
        assert Validators.validate_positive(1e100) is True


class TestValidateNonNegativeEdgeCases:
    """Edge cases for validate_non_negative."""

    def test_validate_non_negative_very_small_positive(self):
        """validate_non_negative with very small positive number."""
        assert Validators.validate_non_negative(0.0000001) is True

    def test_validate_non_negative_very_large_positive(self):
        """validate_non_negative with very large positive number."""
        assert Validators.validate_non_negative(1e100) is True


class TestValidateNonEmptyEdgeCases:
    """Edge cases for validate_non_empty."""

    def test_validate_non_empty_whitespace_string(self):
        """validate_non_empty with whitespace-only string."""
        # Whitespace string is not empty
        assert Validators.validate_non_empty("   ") is True

    def test_validate_non_empty_list_with_none(self):
        """validate_non_empty with list containing None."""
        assert Validators.validate_non_empty([None]) is True

    def validate_non_empty_dict_with_falsey_values(self):
        """validate_non_empty with dict containing falsey values."""
        assert Validators.validate_non_empty({"key": 0}) is True
        assert Validators.validate_non_empty({"key": ""}) is True
        assert Validators.validate_non_empty({"key": False}) is True


# =============================================================================
# Integration tests - combining multiple validators
# =============================================================================

class TestValidatorCombinations:
    """Tests combining multiple validators."""

    def test_validate_range_exclusive_with_type_check(self):
        """Combine validate_type and validate_range with exclusive bounds."""
        value = 5.5
        assert Validators.validate_type(value, float) is True
        assert Validators.validate_range(value, min_val=0.0, max_val=10.0, inclusive=False) is True

    def test_validate_string_with_pattern_and_length(self):
        """Combine validate_string_length and validate_pattern."""
        value = "hello123"
        assert Validators.validate_string_length(value, min_length=5, max_length=10) is True
        assert Validators.validate_pattern(value, r"^[a-z]+[0-9]+$") is True

    def test_validate_dict_with_list_values(self):
        """Combine validate_dict_keys and validate_list_items."""
        data = {"items": [1, 2, 3], "name": "test"}
        assert Validators.validate_dict_keys(data, required_keys=["items", "name"]) is True
        assert Validators.validate_list_items(data["items"], int, min_items=1) is True
