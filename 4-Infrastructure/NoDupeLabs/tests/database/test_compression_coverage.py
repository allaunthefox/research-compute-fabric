# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 NoDupeLabs

"""Tests to achieve 100% coverage on compression.py module.

This test file targets the missing coverage in:
- compression.py: zlib.error exception paths in compress_data and decompress_data
"""

import zlib
from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.databases.compression import DatabaseCompression


class TestDatabaseCompressionCoverage:
    """Tests for DatabaseCompression class to achieve 100% coverage."""

    def test_compress_data_zlib_error(self):
        """Test compress_data when zlib.compress raises zlib.error."""
        mock_conn = MagicMock()
        compression = DatabaseCompression(mock_conn, level=6)

        # Mock zlib.compress to raise zlib.error
        with patch('nodupe.tools.databases.compression.zlib.compress', side_effect=zlib.error("Compression failed")):
            with pytest.raises(ValueError, match="Compression failed"):
                compression.compress_data(b"test data")

    def test_compress_data_string_input(self):
        """Test compress_data with string input (UTF-8 encoding path)."""
        mock_conn = MagicMock()
        compression = DatabaseCompression(mock_conn, level=6)

        # String input should be encoded to UTF-8
        result = compression.compress_data("test string data")
        assert isinstance(result, bytes)

    def test_compress_data_zlib_error_string(self):
        """Test compress_data zlib.error path with string input."""
        mock_conn = MagicMock()
        compression = DatabaseCompression(mock_conn, level=6)

        with patch('nodupe.tools.databases.compression.zlib.compress', side_effect=zlib.error("Compression error")):
            with pytest.raises(ValueError, match="Compression failed"):
                compression.compress_data("test string")

    def test_decompress_data_zlib_error(self):
        """Test decompress_data when zlib.decompress raises zlib.error."""
        mock_conn = MagicMock()
        compression = DatabaseCompression(mock_conn, level=6)

        # Mock zlib.decompress to raise zlib.error
        with patch('nodupe.tools.databases.compression.zlib.decompress', side_effect=zlib.error("Decompression failed")):
            with pytest.raises(ValueError, match="Decompression failed"):
                compression.decompress_data(b"corrupted data")

    def test_decompress_data_unicode_decode_error(self):
        """Test decompress_data when UTF-8 decode fails (returns bytes)."""
        mock_conn = MagicMock()
        compression = DatabaseCompression(mock_conn, level=6)

        # Create compressed binary data that won't decode as UTF-8
        # Use raw binary bytes that are valid zlib but not valid UTF-8
        original_data = b"\x00\x01\x02\x03\xff\xfe\xfd"
        compressed = zlib.compress(original_data, level=6)

        result = compression.decompress_data(compressed)
        # Should return bytes since it can't decode as UTF-8
        assert isinstance(result, bytes)
        assert result == original_data

    def test_compress_safe_returns_empty_on_failure(self):
        """Test compress_safe returns empty bytes on failure."""
        mock_conn = MagicMock()
        compression = DatabaseCompression(mock_conn, level=6)

        with patch('nodupe.tools.databases.compression.zlib.compress', side_effect=zlib.error("Error")):
            result = compression.compress_safe("test data")
            assert result == b''

    def test_decompress_safe_returns_original_on_failure(self):
        """Test decompress_safe returns original data on failure."""
        mock_conn = MagicMock()
        compression = DatabaseCompression(mock_conn, level=6)

        corrupted_data = b"corrupted\x00\x01\x02"
        result = compression.decompress_safe(corrupted_data)
        assert result == corrupted_data

    def test_compression_level_clamping(self):
        """Test that compression level is clamped to 1-9 range."""
        mock_conn = MagicMock()

        # Level below 1 should be clamped to 1
        compression_low = DatabaseCompression(mock_conn, level=0)
        assert compression_low.level == 1

        # Level above 9 should be clamped to 9
        compression_high = DatabaseCompression(mock_conn, level=15)
        assert compression_high.level == 9

        # Normal level should stay as is
        compression_normal = DatabaseCompression(mock_conn, level=6)
        assert compression_normal.level == 6

    def test_compress_decompress_roundtrip_string(self):
        """Test compress and decompress roundtrip with string data."""
        mock_conn = MagicMock()
        compression = DatabaseCompression(mock_conn, level=6)

        original = "Hello, World! This is a test string."
        compressed = compression.compress_data(original)
        decompressed = compression.decompress_data(compressed)

        assert decompressed == original

    def test_compress_decompress_roundtrip_bytes(self):
        """Test compress and decompress roundtrip with bytes data."""
        mock_conn = MagicMock()
        compression = DatabaseCompression(mock_conn, level=6)

        original = b"Hello, World! This is test bytes data."
        compressed = compression.compress_data(original)
        decompressed = compression.decompress_data(compressed)

        # decompress_data returns string if UTF-8 decodable, otherwise bytes
        if isinstance(decompressed, str):
            assert decompressed == original.decode('utf-8')
        else:
            assert decompressed == original
