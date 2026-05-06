# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/network/__init__.py - Network Backend implementations."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Import the network backend classes
from nodupe.tools.network import (
    LocalStorageBackend,
    NetworkManager,
    RemoteStorageBackend,
    S3StorageBackend,
    get_network_manager,
)


class TestRemoteStorageBackend:
    """Test abstract RemoteStorageBackend class."""

    def test_is_abstract(self):
        """RemoteStorageBackend cannot be instantiated directly."""
        with pytest.raises(TypeError):
            RemoteStorageBackend()


class TestLocalStorageBackend:
    """Test LocalStorageBackend class."""

    def test_local_storage_creation(self):
        """LocalStorageBackend can be created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LocalStorageBackend(base_dir=tmpdir)
            assert backend is not None

    def test_is_available(self):
        """LocalStorageBackend is always available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LocalStorageBackend(base_dir=tmpdir)
            assert backend.is_available() is True

    def test_upload_file(self):
        """LocalStorageBackend can upload files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LocalStorageBackend(base_dir=tmpdir)

            # Create a temp file to upload
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write("test content")
                temp_path = f.name

            try:
                result = backend.upload_file(temp_path, "test.txt")
                assert result is True

                # Check file exists
                assert (Path(tmpdir) / "test.txt").exists()
            finally:
                os.unlink(temp_path)

    def test_upload_file_not_found(self):
        """LocalStorageBackend handles missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LocalStorageBackend(base_dir=tmpdir)

            result = backend.upload_file("/nonexistent/file.txt", "test.txt")
            assert result is False

    def test_download_file(self):
        """LocalStorageBackend can download files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LocalStorageBackend(base_dir=tmpdir)

            # Create source file
            src_path = Path(tmpdir) / "source.txt"
            src_path.write_text("test content")

            # Download to temp location
            with tempfile.TemporaryDirectory() as download_dir:
                dst_path = os.path.join(download_dir, "downloaded.txt")
                result = backend.download_file("source.txt", dst_path)

                assert result is True
                assert Path(dst_path).read_text() == "test content"

    def test_download_file_not_found(self):
        """LocalStorageBackend handles missing remote file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LocalStorageBackend(base_dir=tmpdir)

            with tempfile.TemporaryDirectory() as download_dir:
                dst_path = os.path.join(download_dir, "test.txt")
                result = backend.download_file("nonexistent.txt", dst_path)
                assert result is False

    def test_list_files(self):
        """LocalStorageBackend can list files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LocalStorageBackend(base_dir=tmpdir)

            # Create some files
            (Path(tmpdir) / "file1.txt").write_text("content1")
            (Path(tmpdir) / "file2.txt").write_text("content2")
            (Path(tmpdir) / "subdir").mkdir()
            (Path(tmpdir) / "subdir" / "file3.txt").write_text("content3")

            files = backend.list_files()
            assert len(files) >= 2  # At least file1 and file2

    def test_list_files_with_prefix(self):
        """LocalStorageBackend can list files with prefix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LocalStorageBackend(base_dir=tmpdir)

            (Path(tmpdir) / "test1.txt").write_text("content")
            (Path(tmpdir) / "other.txt").write_text("content")

            files = backend.list_files(prefix="test")
            assert any("test1.txt" in f for f in files)

    def test_delete_file(self):
        """LocalStorageBackend can delete files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LocalStorageBackend(base_dir=tmpdir)

            # Create a file
            file_path = Path(tmpdir) / "to_delete.txt"
            file_path.write_text("content")

            result = backend.delete_file("to_delete.txt")
            assert result is True
            assert not file_path.exists()

    def test_delete_file_not_found(self):
        """LocalStorageBackend handles missing file deletion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LocalStorageBackend(base_dir=tmpdir)

            result = backend.delete_file("nonexistent.txt")
            assert result is False


class TestS3StorageBackend:
    """Test S3StorageBackend class."""

    def test_s3_backend_creation(self):
        """S3StorageBackend can be created."""
        backend = S3StorageBackend(bucket_name="test-bucket")
        assert backend is not None

    def test_s3_backend_availability(self):
        """S3StorageBackend availability check."""
        backend = S3StorageBackend(bucket_name="test-bucket")
        # Check that is_available returns a boolean
        result = backend.is_available()
        assert isinstance(result, bool)


class TestNetworkManager:
    """Test NetworkManager class."""

    def test_manager_creation(self):
        """NetworkManager can be created."""
        manager = NetworkManager()
        assert manager is not None

    def test_manager_has_storage_backend(self):
        """NetworkManager has a storage backend."""
        manager = NetworkManager()
        assert manager.storage_backend is not None

    def test_upload_file(self):
        """NetworkManager.upload_file returns bool."""
        manager = NetworkManager()
        # Test with non-existent file - should return False
        result = manager.upload_file('/nonexistent/file.txt', 'test.txt')
        assert result is False

    def test_download_file(self):
        """NetworkManager.download_file returns bool."""
        manager = NetworkManager()
        # Test with non-existent file - should return False
        result = manager.download_file('nonexistent.txt', '/tmp/test.txt')
        assert result is False

    def test_list_files(self):
        """NetworkManager can list files."""
        manager = NetworkManager()
        files = manager.list_files()
        assert isinstance(files, list)

    def test_delete_file(self):
        """NetworkManager.delete_file returns bool."""
        manager = NetworkManager()
        # Test with non-existent file - should return False
        result = manager.delete_file('nonexistent.txt')
        assert result is False


class TestGetNetworkManager:
    """Test get_network_manager function."""

    def test_get_manager_returns_manager(self):
        """get_network_manager returns NetworkManager."""
        manager = get_network_manager()
        assert isinstance(manager, NetworkManager)

    def test_get_manager_singleton(self):
        """get_network_manager returns the same instance."""
        manager1 = get_network_manager()
        manager2 = get_network_manager()
        assert manager1 is manager2
