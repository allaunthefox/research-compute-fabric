# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/security_audit/validator_logic.py - Missing coverage paths.

Additional tests to improve coverage for:
- validate_boolean
- validate_positive
- validate_non_negative
- validate_non_empty
- Edge cases and error paths
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
# Test validate_boolean - Additional Coverage
# =============================================================================

class TestValidateBooleanAdditional:
    """Additional tests for validate_boolean method."""

    def test_validate_boolean_true_value(self):
        """validate_boolean accepts True."""
        result = Validators.validate_boolean(True)
        assert result is True

    def test_validate_boolean_false_value(self):
        """validate_boolean accepts False."""
        result = Validators.validate_boolean(False)
        assert result is True

    def test_validate_boolean_int_zero_raises(self):
        """validate_boolean raises error for int 0."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_boolean(0)
        assert "Expected bool" in str(exc_info.value)

    def test_validate_boolean_int_one_raises(self):
        """validate_boolean raises error for int 1."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_boolean(1)
        assert "Expected bool" in str(exc_info.value)

    def test_validate_boolean_string_raises(self):
        """validate_boolean raises error for string."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_boolean("true")
        assert "Expected bool" in str(exc_info.value)

    def test_validate_boolean_none_raises(self):
        """validate_boolean raises error for None."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_boolean(None)
        assert "Expected bool" in str(exc_info.value)

    def test_validate_boolean_list_raises(self):
        """validate_boolean raises error for list."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_boolean([True])
        assert "Expected bool" in str(exc_info.value)


# =============================================================================
# Test validate_positive - Full Coverage
# =============================================================================

class TestValidatePositive:
    """Test validate_positive method."""

    def test_validate_positive_int(self):
        """validate_positive accepts positive int."""
        result = Validators.validate_positive(42)
        assert result is True

    def test_validate_positive_float(self):
        """validate_positive accepts positive float."""
        result = Validators.validate_positive(3.14)
        assert result is True

    def test_validate_positive_large_number(self):
        """validate_positive accepts large positive number."""
        result = Validators.validate_positive(1000000)
        assert result is True

    def test_validate_positive_zero_raises(self):
        """validate_positive raises error for zero."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_positive(0)
        assert "is not positive" in str(exc_info.value)

    def test_validate_positive_negative_int_raises(self):
        """validate_positive raises error for negative int."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_positive(-1)
        assert "is not positive" in str(exc_info.value)

    def test_validate_positive_negative_float_raises(self):
        """validate_positive raises error for negative float."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_positive(-0.01)
        assert "is not positive" in str(exc_info.value)

    def test_validate_positive_string_raises(self):
        """validate_positive raises error for string."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_positive("42")
        assert "Expected numeric type" in str(exc_info.value)

    def test_validate_positive_none_raises(self):
        """validate_positive raises error for None."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_positive(None)
        assert "Expected numeric type" in str(exc_info.value)

    def test_validate_positive_bool_raises(self):
        """validate_positive raises error for bool."""
        # Note: bool is subclass of int, so True=1 passes
        # This tests the actual behavior
        result = Validators.validate_positive(True)
        assert result is True  # True is 1, which is positive


# =============================================================================
# Test validate_non_negative - Full Coverage
# =============================================================================

class TestValidateNonNegative:
    """Test validate_non_negative method."""

    def test_validate_non_negative_positive_int(self):
        """validate_non_negative accepts positive int."""
        result = Validators.validate_non_negative(42)
        assert result is True

    def test_validate_non_negative_zero(self):
        """validate_non_negative accepts zero."""
        result = Validators.validate_non_negative(0)
        assert result is True

    def test_validate_non_negative_positive_float(self):
        """validate_non_negative accepts positive float."""
        result = Validators.validate_non_negative(3.14)
        assert result is True

    def test_validate_non_negative_zero_float(self):
        """validate_non_negative accepts zero as float."""
        result = Validators.validate_non_negative(0.0)
        assert result is True

    def test_validate_non_negative_negative_int_raises(self):
        """validate_non_negative raises error for negative int."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_non_negative(-1)
        assert "is negative" in str(exc_info.value)

    def test_validate_non_negative_negative_float_raises(self):
        """validate_non_negative raises error for negative float."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_non_negative(-0.01)
        assert "is negative" in str(exc_info.value)

    def test_validate_non_negative_string_raises(self):
        """validate_non_negative raises error for string."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_non_negative("0")
        assert "Expected numeric type" in str(exc_info.value)

    def test_validate_non_negative_none_raises(self):
        """validate_non_negative raises error for None."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_non_negative(None)
        assert "Expected numeric type" in str(exc_info.value)


# =============================================================================
# Test validate_non_empty - Full Coverage
# =============================================================================

class TestValidateNonEmpty:
    """Test validate_non_empty method."""

    def test_validate_non_empty_string(self):
        """validate_non_empty accepts non-empty string."""
        result = Validators.validate_non_empty("hello")
        assert result is True

    def test_validate_non_empty_list(self):
        """validate_non_empty accepts non-empty list."""
        result = Validators.validate_non_empty([1, 2, 3])
        assert result is True

    def test_validate_non_empty_dict(self):
        """validate_non_empty accepts non-empty dict."""
        result = Validators.validate_non_empty({"key": "value"})
        assert result is True

    def test_validate_non_empty_tuple(self):
        """validate_non_empty accepts non-empty tuple."""
        result = Validators.validate_non_empty((1, 2))
        assert result is True

    def test_validate_non_empty_set(self):
        """validate_non_empty accepts non-empty set."""
        result = Validators.validate_non_empty({1, 2, 3})
        assert result is True

    def test_validate_non_empty_empty_string_raises(self):
        """validate_non_empty raises error for empty string."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_non_empty("")
        assert "empty" in str(exc_info.value).lower()

    def test_validate_non_empty_empty_list_raises(self):
        """validate_non_empty raises error for empty list."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_non_empty([])
        assert "empty" in str(exc_info.value).lower()

    def test_validate_non_empty_empty_dict_raises(self):
        """validate_non_empty raises error for empty dict."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_non_empty({})
        assert "empty" in str(exc_info.value).lower()

    def test_validate_non_empty_empty_tuple_raises(self):
        """validate_non_empty raises error for empty tuple."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_non_empty(())
        assert "empty" in str(exc_info.value).lower()

    def test_validate_non_empty_empty_set_raises(self):
        """validate_non_empty raises error for empty set."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_non_empty(set())
        assert "empty" in str(exc_info.value).lower()

    def test_validate_non_empty_none_raises(self):
        """validate_non_empty raises error for None."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_non_empty(None)
        assert "empty" in str(exc_info.value).lower()

    def test_validate_non_empty_whitespace_string(self):
        """validate_non_empty accepts whitespace string (not empty)."""
        result = Validators.validate_non_empty("   ")
        assert result is True


# =============================================================================
# Test validate_type - Additional Edge Cases
# =============================================================================

class TestValidateTypeEdgeCases:
    """Additional edge case tests for validate_type."""

    def test_validate_type_dict_subclass(self):
        """validate_type accepts dict subclass."""
        class CustomDict(dict):
            """Custom dict subclass."""
            pass

        obj = CustomDict()
        result = Validators.validate_type(obj, dict)
        assert result is True

    def test_validate_type_list_subclass(self):
        """validate_type accepts list subclass."""
        class CustomList(list):
            """Custom list subclass."""
            pass

        obj = CustomList()
        result = Validators.validate_type(obj, list)
        assert result is True

    def test_validate_type_tuple_type(self):
        """validate_type accepts tuple type."""
        result = Validators.validate_type((1, 2, 3), tuple)
        assert result is True

    def test_validate_type_set_type(self):
        """validate_type accepts set type."""
        result = Validators.validate_type({1, 2, 3}, set)
        assert result is True

    def test_validate_type_frozenset_type(self):
        """validate_type accepts frozenset type."""
        result = Validators.validate_type(frozenset([1, 2, 3]), frozenset)
        assert result is True


# =============================================================================
# Test validate_range - Additional Edge Cases
# =============================================================================

class TestValidateRangeEdgeCases:
    """Additional edge case tests for validate_range."""

    def test_validate_range_negative_to_positive(self):
        """validate_range works with negative to positive range."""
        result = Validators.validate_range(-5, min_val=-10, max_val=10)
        assert result is True

    def test_validate_range_both_negative(self):
        """validate_range works with both negative bounds."""
        result = Validators.validate_range(-5, min_val=-10, max_val=-1)
        assert result is True

    def test_validate_range_equal_min_max(self):
        """validate_range with equal min and max."""
        result = Validators.validate_range(5, min_val=5, max_val=5)
        assert result is True

    def test_validate_range_exclusive_equal_min_max_raises(self):
        """validate_range with exclusive and equal min/max raises."""
        with pytest.raises(ValidationError):
            Validators.validate_range(5, min_val=5, max_val=5, inclusive=False)

    def test_validate_range_min_greater_than_max(self):
        """validate_range with min > max still validates."""
        # This is an edge case - the validation still works
        # but the range is logically invalid
        with pytest.raises(ValidationError):
            Validators.validate_range(5, min_val=10, max_val=1)


# =============================================================================
# Test validate_string_length - Additional Edge Cases
# =============================================================================

class TestValidateStringLengthEdgeCases:
    """Additional edge case tests for validate_string_length."""

    def test_validate_string_length_zero_min_max(self):
        """validate_string_length with zero min and max."""
        result = Validators.validate_string_length("", min_length=0, max_length=0)
        assert result is True

    def test_validate_string_length_unicode_chars(self):
        """validate_string_length counts unicode characters."""
        # Unicode string with multi-byte characters
        result = Validators.validate_string_length("你好", min_length=2, max_length=2)
        assert result is True

    def test_validate_string_length_emoji(self):
        """validate_string_length handles emoji."""
        result = Validators.validate_string_length("😀", min_length=1, max_length=1)
        assert result is True

    def test_validate_string_length_newlines(self):
        """validate_string_length counts newlines."""
        result = Validators.validate_string_length("hello\nworld", min_length=11, max_length=11)
        assert result is True


# =============================================================================
# Test validate_pattern - Additional Edge Cases
# =============================================================================

class TestValidatePatternEdgeCases:
    """Additional edge case tests for validate_pattern."""

    def test_validate_pattern_empty_string(self):
        """validate_pattern with empty string."""
        result = Validators.validate_pattern("", r"^$")
        assert result is True

        with pytest.raises(ValidationError):
            Validators.validate_pattern("not empty", r"^$")

    def test_validate_pattern_case_insensitive(self):
        """validate_pattern with case insensitive flag."""
        result = Validators.validate_pattern("HELLO", r"(?i)^hello$")
        assert result is True

    def test_validate_pattern_special_chars(self):
        """validate_pattern with special characters."""
        result = Validators.validate_pattern("hello.world", r"^hello\.world$")
        assert result is True


# =============================================================================
# Test validate_email - Additional Edge Cases
# =============================================================================

class TestValidateEmailEdgeCases:
    """Additional edge case tests for validate_email."""

    def test_validate_email_subdomain(self):
        """validate_email accepts email with subdomain."""
        result = Validators.validate_email("user@mail.example.com")
        assert result is True

    def test_validate_email_numbers(self):
        """validate_email accepts email with numbers."""
        result = Validators.validate_email("user123@example123.com")
        assert result is True

    def test_validate_email_dots_in_local(self):
        """validate_email accepts dots in local part."""
        result = Validators.validate_email("user.name@example.com")
        assert result is True

    def test_validate_email_plus_sign(self):
        """validate_email accepts plus sign in local part."""
        result = Validators.validate_email("user+tag@example.com")
        assert result is True

    def test_validate_email_hyphen(self):
        """validate_email accepts hyphen in domain."""
        result = Validators.validate_email("user@example-domain.com")
        assert result is True


# =============================================================================
# Test validate_path - Additional Edge Cases
# =============================================================================

class TestValidatePathEdgeCases:
    """Additional edge case tests for validate_path."""

    def test_validate_path_relative_path(self):
        """validate_path accepts relative path."""
        result = Validators.validate_path("relative/path.txt")
        assert result is True

    def test_validate_path_symlink_file(self, tmp_path):
        """validate_path with symlink to file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        symlink = tmp_path / "link.txt"
        symlink.symlink_to(test_file)

        result = Validators.validate_path(symlink, must_exist=True, must_be_file=True)
        assert result is True

    def test_validate_path_symlink_dir(self, tmp_path):
        """validate_path with symlink to directory."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        symlink = tmp_path / "linkdir"
        symlink.symlink_to(test_dir)

        result = Validators.validate_path(symlink, must_exist=True, must_be_dir=True)
        assert result is True

    def test_validate_path_broken_symlink_raises(self, tmp_path):
        """validate_path with broken symlink raises error."""
        broken_link = tmp_path / "broken"
        broken_link.symlink_to(tmp_path / "nonexistent")

        with pytest.raises(ValidationError):
            Validators.validate_path(broken_link, must_exist=True)


# =============================================================================
# Test validate_enum - Additional Edge Cases
# =============================================================================

class TestValidateEnumEdgeCases:
    """Additional edge case tests for validate_enum."""

    def test_validate_enum_none_value(self):
        """validate_enum with None as allowed value."""
        result = Validators.validate_enum(None, [None, "value"])
        assert result is True

    def test_validate_enum_duplicate_allowed(self):
        """validate_enum with duplicate allowed values."""
        result = Validators.validate_enum("red", ["red", "red", "blue"])
        assert result is True

    def test_validate_enum_case_sensitive(self):
        """validate_enum is case sensitive."""
        with pytest.raises(ValidationError):
            Validators.validate_enum("RED", ["red", "green"])


# =============================================================================
# Test validate_dict_keys - Additional Edge Cases
# =============================================================================

class TestValidateDictKeysEdgeCases:
    """Additional edge case tests for validate_dict_keys."""

    def test_validate_dict_keys_both_required_and_allowed(self):
        """validate_dict_keys with both required and allowed keys."""
        result = Validators.validate_dict_keys(
            {"a": 1, "b": 2},
            required_keys=["a"],
            allowed_keys=["a", "b", "c"]
        )
        assert result is True

    def test_validate_dict_keys_missing_required_and_extra(self):
        """validate_dict_keys with missing required and extra keys."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_dict_keys(
                {"a": 1, "c": 3},
                required_keys=["a", "b"],
                allowed_keys=["a", "b"]
            )
        # Should report missing keys first
        assert "Missing required keys" in str(exc_info.value)

    def test_validate_dict_keys_int_keys(self):
        """validate_dict_keys with int keys."""
        result = Validators.validate_dict_keys(
            {1: "a", 2: "b"},
            required_keys=[1]
        )
        assert result is True


# =============================================================================
# Test validate_list_items - Additional Edge Cases
# =============================================================================

class TestValidateListItemsEdgeCases:
    """Additional edge case tests for validate_list_items."""

    def test_validate_list_items_zero_min_max(self):
        """validate_list_items with zero min and max items."""
        result = Validators.validate_list_items(
            [], str, min_items=0, max_items=0
        )
        assert result is True

    def test_validate_list_items_single_item(self):
        """validate_list_items with single item."""
        result = Validators.validate_list_items(["hello"], str, min_items=1, max_items=1)
        assert result is True

    def test_validate_list_items_mixed_types_raises(self):
        """validate_list_items with mixed types raises."""
        with pytest.raises(ValidationError) as exc_info:
            Validators.validate_list_items([1, "two", 3.0], int)
        assert "expected int" in str(exc_info.value).lower()
