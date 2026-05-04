"""Test MMAP Handler Module - Coverage Completion.

Tests to achieve 100% coverage for mmap_handler.py
"""

import mmap
import tempfile
from pathlib import Path

import pytest

from nodupe.tools.os_filesystem.mmap_handler import MMAPHandler


class TestMMAPHandlerCreateMmap:
    """Test create_mmap method."""

    def test_create_mmap_default_access(self):
        """Test creating mmap with default access mode."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test content for mmap')
            f.flush()
            mapped = MMAPHandler.create_mmap(f.name)
            try:
                assert mapped is not None
                assert len(mapped) > 0
            finally:
                mapped.close()

    def test_create_mmap_read_access(self):
        """Test creating mmap with read access."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test content')
            f.flush()
            mapped = MMAPHandler.create_mmap(f.name, access_mode=mmap.ACCESS_READ)
            try:
                content = mapped.read(10)
                assert content == b'test conte'
            finally:
                mapped.close()

    def test_create_mmap_empty_file(self):
        """Test creating mmap for empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Empty file
            f.flush()
            mapped = MMAPHandler.create_mmap(f.name)
            try:
                # Should create anonymous mapping for empty file
                assert mapped is not None
                assert len(mapped) == 1
            finally:
                mapped.close()

    def test_create_mmap_path_object(self):
        """Test creating mmap with Path object."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test content')
            f.flush()
            mapped = MMAPHandler.create_mmap(Path(f.name))
            try:
                assert mapped is not None
            finally:
                mapped.close()


class TestMMAPHandlerMmapContext:
    """Test mmap_context method."""

    def test_mmap_context_success(self):
        """Test mmap context manager success."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test content for context')
            f.flush()
            with MMAPHandler.mmap_context(f.name) as mapped:
                assert mapped is not None
                content = mapped.read(10)
                assert content == b'test conte'
            # Context manager should close the mapping

    def test_mmap_context_exception_cleanup(self):
        """Test mmap context manager cleans up on exception."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test content')
            f.flush()
            try:
                with MMAPHandler.mmap_context(f.name):
                    raise ValueError("Test exception")
            except ValueError:
                pass
            # Mapping should be closed even after exception

    def test_mmap_context_custom_access(self):
        """Test mmap context manager with custom access mode."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test content')
            f.flush()
            with MMAPHandler.mmap_context(f.name, access_mode=mmap.ACCESS_READ) as mapped:
                assert mapped is not None


class TestMMAPHandlerReadChunk:
    """Test read_chunk method."""

    def test_read_chunk_basic(self):
        """Test reading chunk from mmap."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'0123456789abcdef')
            f.flush()
            with MMAPHandler.mmap_context(f.name) as mapped:
                chunk = MMAPHandler.read_chunk(mapped, 0, 5)
                assert chunk == b'01234'

    def test_read_chunk_offset(self):
        """Test reading chunk with offset."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'0123456789abcdef')
            f.flush()
            with MMAPHandler.mmap_context(f.name) as mapped:
                chunk = MMAPHandler.read_chunk(mapped, 5, 5)
                assert chunk == b'56789'

    def test_read_chunk_restores_position(self):
        """Test that read_chunk restores original position."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'0123456789abcdef')
            f.flush()
            with MMAPHandler.mmap_context(f.name) as mapped:
                # Move to position 10
                mapped.seek(10)
                # Read chunk from position 0
                chunk = MMAPHandler.read_chunk(mapped, 0, 5)
                assert chunk == b'01234'
                # Position should be restored to 10
                assert mapped.tell() == 10


class TestMMAPHandlerGetFileSize:
    """Test get_file_size method."""

    def test_get_file_size_basic(self):
        """Test getting file size from mmap."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            content = b'test content for size check'
            f.write(content)
            f.flush()
            with MMAPHandler.mmap_context(f.name) as mapped:
                size = MMAPHandler.get_file_size(mapped)
                assert size == len(content)

    def test_get_file_size_empty(self):
        """Test getting file size for empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Empty file
            f.flush()
            with MMAPHandler.mmap_context(f.name) as mapped:
                size = MMAPHandler.get_file_size(mapped)
                # Anonymous mapping for empty file has size 1
                assert size == 1


class TestMMAPHandlerEdgeCases:
    """Test edge cases."""

    def test_create_mmap_large_file(self):
        """Test creating mmap for large file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Write 1MB of data
            f.write(b'x' * (1024 * 1024))
            f.flush()
            mapped = MMAPHandler.create_mmap(f.name)
            try:
                assert len(mapped) == 1024 * 1024
            finally:
                mapped.close()

    def test_read_chunk_beyond_end(self):
        """Test reading chunk beyond file end."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'short')
            f.flush()
            with MMAPHandler.mmap_context(f.name) as mapped:
                # Try to read beyond end
                chunk = MMAPHandler.read_chunk(mapped, 0, 100)
                # Should return what's available
                assert chunk == b'short'

    def test_mmap_context_file_not_exists(self):
        """Test mmap context with nonexistent file."""
        with pytest.raises(FileNotFoundError):
            with MMAPHandler.mmap_context("/nonexistent/file.txt"):
                pass
