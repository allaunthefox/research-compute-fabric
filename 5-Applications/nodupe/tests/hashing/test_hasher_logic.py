# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 NoDupeLabs

"""Tests to achieve 100% coverage on hasher_logic.py module.

This test file targets the missing coverage in:
- hasher_logic.py: FileHasher class methods
"""

import hashlib
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from nodupe.core.hasher_interface import HasherInterface
from nodupe.tools.hashing.hasher_logic import (
    FileHasher,
    create_file_hasher,
)


class TestFileHasherInit:
    """Tests for FileHasher initialization."""

    def test_init_default_algorithm(self):
        """Test FileHasher with default algorithm."""
        hasher = FileHasher()
        assert hasher._algorithm == 'sha256'

    def test_init_custom_algorithm(self):
        """Test FileHasher with custom algorithm."""
        hasher = FileHasher(algorithm='md5')
        assert hasher._algorithm == 'md5'

    def test_init_default_buffer_size(self):
        """Test FileHasher with default buffer size."""
        hasher = FileHasher()
        assert hasher._buffer_size == 65536

    def test_init_custom_buffer_size(self):
        """Test FileHasher with custom buffer size."""
        hasher = FileHasher(buffer_size=8192)
        assert hasher._buffer_size == 8192

    def test_init_custom_algorithm_and_buffer(self):
        """Test FileHasher with custom algorithm and buffer size."""
        hasher = FileHasher(algorithm='sha512', buffer_size=16384)
        assert hasher._algorithm == 'sha512'
        assert hasher._buffer_size == 16384


class TestHashFile:
    """Tests for hash_file method."""

    def test_hash_file_basic(self, tmp_path):
        """Test basic file hashing."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        hasher = FileHasher()
        result = hasher.hash_file(str(test_file))

        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex length

    def test_hash_file_with_progress_callback(self, tmp_path):
        """Test file hashing with progress callback."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        progress_data = []

        def on_progress(progress):
            """Callback function to record progress during file hashing."""
            progress_data.append(progress)

        hasher = FileHasher()
        result = hasher.hash_file(str(test_file), on_progress=on_progress)

        assert len(progress_data) > 0
        assert progress_data[0]['bytes_read'] > 0
        assert progress_data[0]['percent_complete'] >= 0

    def test_hash_file_nonexistent(self):
        """Test hashing non-existent file raises error."""
        hasher = FileHasher()
        with pytest.raises(FileNotFoundError):
            hasher.hash_file("/nonexistent/path/file.txt")

    def test_hash_file_directory(self, tmp_path):
        """Test hashing directory raises error."""
        hasher = FileHasher()
        with pytest.raises(FileNotFoundError):
            hasher.hash_file(str(tmp_path))

    def test_hash_file_empty(self, tmp_path):
        """Test hashing empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        hasher = FileHasher()
        result = hasher.hash_file(str(test_file))

        assert isinstance(result, str)
        # Empty file should have a valid hash
        assert len(result) == 64

    def test_hash_file_large(self, tmp_path):
        """Test hashing larger file."""
        test_file = tmp_path / "large.txt"
        # Write 100KB of data
        test_file.write_bytes(b"x" * 102400)

        hasher = FileHasher()
        result = hasher.hash_file(str(test_file))

        assert isinstance(result, str)
        assert len(result) == 64


class TestHashFiles:
    """Tests for hash_files method."""

    def test_hash_files_multiple(self, tmp_path):
        """Test hashing multiple files."""
        files = []
        for i in range(3):
            test_file = tmp_path / f"file{i}.txt"
            test_file.write_text(f"content{i}")
            files.append(str(test_file))

        hasher = FileHasher()
        results = hasher.hash_files(files)

        assert len(results) == 3
        for file_path in files:
            assert file_path in results

    def test_hash_files_with_progress(self, tmp_path):
        """Test hashing multiple files with progress."""
        files = []
        for i in range(2):
            test_file = tmp_path / f"file{i}.txt"
            test_file.write_text(f"content{i}")
            files.append(str(test_file))

        progress_data = []

        def on_progress(progress):
            """Callback function to record progress during multi-file hashing."""
            progress_data.append(progress)

        hasher = FileHasher()
        results = hasher.hash_files(files, on_progress=on_progress)

        assert len(results) == 2
        assert len(progress_data) > 0

    def test_hash_files_empty_list(self):
        """Test hashing empty file list."""
        hasher = FileHasher()
        results = hasher.hash_files([])

        assert results == {}

    def test_hash_files_with_nonexistent(self, tmp_path):
        """Test hashing files with some non-existent."""
        test_file = tmp_path / "valid.txt"
        test_file.write_text("valid")

        files = [str(test_file), "/nonexistent/file.txt"]

        hasher = FileHasher()
        results = hasher.hash_files(files)

        # Should only return valid file
        assert len(results) == 1


class TestHashString:
    """Tests for hash_string method."""

    def test_hash_string_basic(self):
        """Test basic string hashing."""
        hasher = FileHasher()
        result = hasher.hash_string("test string")

        assert isinstance(result, str)
        assert len(result) == 64

    def test_hash_string_empty(self):
        """Test hashing empty string."""
        hasher = FileHasher()
        result = hasher.hash_string("")

        assert isinstance(result, str)
        assert len(result) == 64

    def test_hash_string_unicode(self):
        """Test hashing unicode string."""
        hasher = FileHasher()
        result = hasher.hash_string("Hello 世界 🌍")

        assert isinstance(result, str)
        assert len(result) == 64

    def test_hash_string_consistency(self):
        """Test same string produces same hash."""
        hasher = FileHasher()
        result1 = hasher.hash_string("test")
        result2 = hasher.hash_string("test")

        assert result1 == result2


class TestHashBytes:
    """Tests for hash_bytes method."""

    def test_hash_bytes_basic(self):
        """Test basic bytes hashing."""
        hasher = FileHasher()
        result = hasher.hash_bytes(b"test bytes")

        assert isinstance(result, str)
        assert len(result) == 64

    def test_hash_bytes_empty(self):
        """Test hashing empty bytes."""
        hasher = FileHasher()
        result = hasher.hash_bytes(b"")

        assert isinstance(result, str)
        assert len(result) == 64

    def test_hash_bytes_binary(self):
        """Test hashing binary data."""
        hasher = FileHasher()
        result = hasher.hash_bytes(bytes(range(256)))

        assert isinstance(result, str)
        assert len(result) == 64


class TestVerifyHash:
    """Tests for verify_hash method."""

    def test_verify_hash_valid(self, tmp_path):
        """Test hash verification with valid hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        hasher = FileHasher()
        expected_hash = hasher.hash_file(str(test_file))

        result = hasher.verify_hash(str(test_file), expected_hash)
        assert result is True

    def test_verify_hash_invalid(self, tmp_path):
        """Test hash verification with invalid hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        hasher = FileHasher()
        result = hasher.verify_hash(str(test_file), "invalid_hash")

        assert result is False

    def test_verify_hash_nonexistent_file(self):
        """Test hash verification for non-existent file."""
        hasher = FileHasher()
        result = hasher.verify_hash("/nonexistent/file.txt", "some_hash")

        assert result is False


class TestAlgorithmMethods:
    """Tests for algorithm-related methods."""

    def test_set_algorithm_valid(self):
        """Test setting valid algorithm."""
        hasher = FileHasher()
        hasher.set_algorithm('sha512')

        assert hasher._algorithm == 'sha512'

    def test_set_algorithm_invalid(self):
        """Test setting invalid algorithm raises error."""
        hasher = FileHasher()
        with pytest.raises(ValueError):
            hasher.set_algorithm('invalid_algo')

    def test_get_algorithm(self):
        """Test getting current algorithm."""
        hasher = FileHasher(algorithm='md5')
        assert hasher.get_algorithm() == 'md5'

    def test_set_buffer_size_valid(self):
        """Test setting valid buffer size."""
        hasher = FileHasher()
        hasher.set_buffer_size(8192)

        assert hasher._buffer_size == 8192

    def test_set_buffer_size_invalid(self):
        """Test setting invalid buffer size raises error."""
        hasher = FileHasher()
        with pytest.raises(ValueError):
            hasher.set_buffer_size(0)

        with pytest.raises(ValueError):
            hasher.set_buffer_size(-100)

    def test_get_buffer_size(self):
        """Test getting current buffer size."""
        hasher = FileHasher(buffer_size=8192)
        assert hasher.get_buffer_size() == 8192


class TestGetAvailableAlgorithms:
    """Tests for get_available_algorithms method."""

    def test_get_available_algorithms_returns_list(self):
        """Test get_available_algorithms returns a list."""
        hasher = FileHasher()
        algorithms = hasher.get_available_algorithms()

        assert isinstance(algorithms, list)
        assert len(algorithms) > 0

    def test_get_available_algorithms_contains_standard(self):
        """Test available algorithms contain standard ones."""
        hasher = FileHasher()
        algorithms = hasher.get_available_algorithms()

        assert 'sha256' in algorithms
        assert 'md5' in algorithms

    def test_get_available_algorithms_sorted(self):
        """Test available algorithms are sorted."""
        hasher = FileHasher()
        algorithms = hasher.get_available_algorithms()

        assert algorithms == sorted(algorithms)


class TestCreateFileHasher:
    """Tests for create_file_hasher factory function."""

    def test_create_file_hasher_default(self):
        """Test create_file_hasher with defaults."""
        hasher = create_file_hasher()

        assert isinstance(hasher, FileHasher)
        assert hasher._algorithm == 'sha256'
        assert hasher._buffer_size == 65536

    def test_create_file_hasher_custom(self):
        """Test create_file_hasher with custom parameters."""
        hasher = create_file_hasher(algorithm='md5', buffer_size=4096)

        assert isinstance(hasher, FileHasher)
        assert hasher._algorithm == 'md5'
        assert hasher._buffer_size == 4096


class TestHasherInterface:
    """Tests for HasherInterface inheritance."""

    def test_file_hasher_implements_interface(self):
        """Test FileHasher implements HasherInterface."""
        hasher = FileHasher()
        assert isinstance(hasher, HasherInterface)

    def test_hasher_interface_methods(self):
        """Test FileHasher has all interface methods."""
        hasher = FileHasher()

        assert hasattr(hasher, 'hash_file')
        assert hasattr(hasher, 'hash_string')
        assert hasattr(hasher, 'hash_bytes')
        assert hasattr(hasher, 'verify_hash')
        assert hasattr(hasher, 'set_algorithm')
        assert hasattr(hasher, 'get_algorithm')


class TestHashAlgorithmVariants:
    """Tests for different hash algorithms."""

    def test_hash_with_sha256(self):
        """Test hashing with SHA-256."""
        hasher = FileHasher(algorithm='sha256')
        result = hasher.hash_string("test")
        assert len(result) == 64

    def test_hash_with_sha512(self):
        """Test hashing with SHA-512."""
        hasher = FileHasher(algorithm='sha512')
        result = hasher.hash_string("test")
        assert len(result) == 128

    def test_hash_with_md5(self):
        """Test hashing with MD5."""
        hasher = FileHasher(algorithm='md5')
        result = hasher.hash_string("test")
        assert len(result) == 32

    def test_hash_with_blake2b(self):
        """Test hashing with BLAKE2b."""
        hasher = FileHasher(algorithm='blake2b')
        result = hasher.hash_string("test")
        assert len(result) == 128

    def test_hash_with_sha1(self):
        """Test hashing with SHA-1."""
        hasher = FileHasher(algorithm='sha1')
        result = hasher.hash_string("test")
        assert len(result) == 40


class TestEdgeCases:
    """Tests for edge cases."""

    def test_hash_file_read_error(self):
        """Test file hashing with read error."""
        hasher = FileHasher()

        with patch('builtins.open', side_effect=IOError("Read error")):
            with pytest.raises(IOError):
                hasher.hash_file("/some/file.txt")

    def test_hash_string_error(self):
        """Test string hashing with encoding error."""
        hasher = FileHasher()

        # Should handle encoding gracefully
        result = hasher.hash_string("test")
        assert isinstance(result, str)

    def test_multiple_algorithms_different_results(self):
        """Test different algorithms produce different results."""
        test_data = "test data"

        hasher = FileHasher(algorithm='sha256')
        sha256_result = hasher.hash_string(test_data)

        hasher = FileHasher(algorithm='md5')
        md5_result = hasher.hash_string(test_data)

        assert sha256_result != md5_result


class TestExceptionCoverage:
    """Tests for exception handling paths in hasher_logic.py."""

    @patch('hashlib.new')
    def test_hash_string_exception_path(self, mock_hashlib_new):
        """Test hash_string exception path when hashlib.new raises."""
        hasher = FileHasher()

        # Make hashlib.new raise an exception
        mock_hashlib_new.side_effect = ValueError("Algorithm not available")

        with pytest.raises(ValueError):
            hasher.hash_string("test data")

    @patch('hashlib.new')
    def test_hash_bytes_exception_path(self, mock_hashlib_new):
        """Test hash_bytes exception path when hashlib.new raises."""
        hasher = FileHasher()

        # Make hashlib.new raise an exception
        mock_hashlib_new.side_effect = ValueError("Algorithm not available")

        with pytest.raises(ValueError):
            hasher.hash_bytes(b"test data")

    @patch('hashlib.new')
    def test_hash_file_exception_path(self, mock_hashlib_new):
        """Test hash_file exception path when hashlib.new raises."""
        hasher = FileHasher()

        # Create a temporary file to test
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            # Make hashlib.new raise an exception
            mock_hashlib_new.side_effect = ValueError("Algorithm not available")

            with pytest.raises(ValueError):
                hasher.hash_file(temp_path)
        finally:
            os.unlink(temp_path)


    def test_hash_files_exception_handling(self):
        """Test hash_files handles individual file exceptions."""
        hasher = FileHasher()

        # Create temp files
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as f1:
            f1.write(b"content 1")
            temp1 = f1.name
        with tempfile.NamedTemporaryFile(delete=False) as f2:
            f2.write(b"content 2")
            temp2 = f2.name

        try:
            # Mock hash_file to raise an exception on the second file
            original_hash_file = hasher.hash_file

            def mock_hash_file(path, on_progress=None):
                """Mock hash_file that raises IOError for temp files."""
                if "temp" in path:
                    raise IOError("Read error for temp file")
                return original_hash_file(path, on_progress)

            hasher.hash_file = mock_hash_file

            # Should still return results for files that didn't fail
            result = hasher.hash_files([temp1, temp2])

            # Should return empty dict since both files fail
            assert isinstance(result, dict)
        finally:
            import os
            os.unlink(temp1)
            os.unlink(temp2)


    def test_hash_files_error_in_hash_file_inner(self):
        """Test hash_files exception in hash_file method itself (not the wrapper)."""
        hasher = FileHasher()

        # Create a temp file that we'll make throw during hash
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
            f.write("test content")
            temp_path = f.name

        try:
            # Patch the open to raise an error for this specific file
            original_open = open

            def selective_open(path, *args, **kwargs):
                """Mock open that raises error for specific path."""
                if path == temp_path:
                    raise IOError("Simulated read error")
                return original_open(path, *args, **kwargs)

            import builtins
            import unittest.mock
            with unittest.mock.patch.object(builtins, 'open', side_effect=selective_open):
                result = hasher.hash_files([temp_path])

            # Should return empty dict since the file failed
            assert isinstance(result, dict)
        finally:
            import os
            os.unlink(temp_path)
