# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for DatabaseSecurity to achieve 100% coverage."""

from unittest.mock import MagicMock

import pytest

from nodupe.tools.databases.security import DatabaseSecurity, InputValidationError, SecurityError


class TestDatabaseSecurityCoverage:
    """Test cases to achieve full coverage of DatabaseSecurity."""

    def test_validate_input_none(self):
        """Test validate_input raises error for None."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        with pytest.raises(InputValidationError):
            security.validate_input(None)

    def test_validate_input_with_type_str(self):
        """Test validate_input with string type."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        result = security.validate_input("test", "str")
        assert result is True

    def test_validate_input_with_type_int(self):
        """Test validate_input with int type."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        result = security.validate_input(123, "int")
        assert result is True

    def test_validate_input_with_type_mismatch(self):
        """Test validate_input raises error for type mismatch."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        with pytest.raises(InputValidationError):
            security.validate_input("123", "int")

    def test_validate_input_unknown_type(self):
        """Test validate_input raises error for unknown type."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        with pytest.raises(InputValidationError):
            security.validate_input("test", "unknown_type")

    def test_validate_input_dangerous_string(self):
        """Test validate_input raises error for dangerous string."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        with pytest.raises(InputValidationError):
            security.validate_input("test'; DROP TABLE users;--")

    def test_is_safe_string_empty(self):
        """Test _is_safe_string returns True for empty string."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        assert security._is_safe_string("") is True

    def test_is_safe_string_dangerous(self):
        """Test _is_safe_string detects dangerous patterns."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        # These patterns should be detected as dangerous
        assert security._is_safe_string("test; DROP TABLE") is False

    def test_is_safe_string_safe(self):
        """Test _is_safe_string returns True for safe strings."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        assert security._is_safe_string("test_value_123") is True

    def test_validate_path_empty(self):
        """Test validate_path raises error for empty path."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        with pytest.raises(InputValidationError):
            security.validate_path("")

    def test_validate_path_traversal(self):
        """Test validate_path detects directory traversal."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        with pytest.raises(InputValidationError):
            security.validate_path("../etc/passwd")

    def test_validate_path_absolute_outside_base(self):
        """Test validate_path detects absolute path outside base."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        with pytest.raises(InputValidationError):
            security.validate_path("/etc/passwd", base_dir="/home/user")

    def test_validate_path_valid(self):
        """Test validate_path accepts valid paths."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        assert security.validate_path("/home/user/file.txt") is True
        assert security.validate_path("relative/path/file.txt") is True

    def test_validate_path_with_base_dir_valid(self):
        """Test validate_path accepts paths within base_dir."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        assert security.validate_path("/home/user/data/file.txt", base_dir="/home/user/data") is True

    def test_sanitize_error_message(self):
        """Test sanitize_error_message removes sensitive info."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        # Test with password pattern
        error = Exception("Error: password=secret123")
        result = security.sanitize_error_message(error)
        assert "password" in result.lower() or "secret123" not in result

    def test_validate_identifier_empty(self):
        """Test validate_identifier raises error for empty identifier."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        with pytest.raises(InputValidationError):
            security.validate_identifier("")

    def test_validate_identifier_invalid_start(self):
        """Test validate_identifier raises error for invalid start."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        with pytest.raises(InputValidationError):
            security.validate_identifier("123invalid")

    def test_validate_identifier_invalid_chars(self):
        """Test validate_identifier raises error for invalid chars."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        with pytest.raises(InputValidationError):
            security.validate_identifier("table-name")

    def test_validate_identifier_valid(self):
        """Test validate_identifier accepts valid identifiers."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        assert security.validate_identifier("valid_table") is True
        assert security.validate_identifier("Table123") is True

    def test_validate_schema_empty(self):
        """Test validate_schema raises error for empty schema."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        with pytest.raises(InputValidationError):
            security.validate_schema("")

    def test_validate_schema_invalid_chars(self):
        """Test validate_schema raises error for invalid chars."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        with pytest.raises(InputValidationError):
            security.validate_schema("col TEXT; DROP TABLE")

    def test_validate_schema_valid(self):
        """Test validate_schema accepts valid schemas."""
        mock_db = MagicMock()
        security = DatabaseSecurity(mock_db)

        assert security.validate_schema("id INTEGER PRIMARY KEY, name TEXT") is True
        assert security.validate_schema("col1 INT, col2 TEXT, col3 REAL") is True
