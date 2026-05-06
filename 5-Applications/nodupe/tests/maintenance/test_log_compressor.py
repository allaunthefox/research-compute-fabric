"""Tests for log_compressor module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest


class TestLogCompressor:
    """Test LogCompressor class."""

    def test_generate_metadata(self, temp_dir):
        """Test metadata generation."""
        from nodupe.tools.maintenance.log_compressor import LogCompressor

        # Create a test file
        test_file = temp_dir / "test.log"
        test_file.write_text("test log content")

        metadata = LogCompressor._generate_metadata(test_file)

        assert "dc:identifier" in metadata
        assert "dc:title" in metadata
        assert "dc:format" in metadata
        assert "dc:date" in metadata
        assert "oais:package_type" in metadata
        assert "fixity" in metadata
        assert metadata["fixity"]["algorithm"] == "sha256"
        assert metadata["fixity"]["value"] is not None

    def test_compress_old_logs_no_directory(self):
        """Test compress_old_logs when directory doesn't exist."""
        from nodupe.tools.maintenance.log_compressor import LogCompressor

        result = LogCompressor.compress_old_logs("/nonexistent/path")

        assert result == []

    def test_compress_old_logs_no_archive_handler(self, temp_dir):
        """Test compress_old_logs when no archive handler is available."""
        from nodupe.core.container import container as global_container
        from nodupe.tools.maintenance.log_compressor import LogCompressor

        # Clear any existing service
        global_container.clear()

        result = LogCompressor.compress_old_logs(str(temp_dir))

        assert result == []

    @patch('nodupe.tools.maintenance.log_compressor.global_container')
    def test_compress_old_logs_success(self, mock_container, temp_dir):
        """Test successful log compression."""
        from nodupe.tools.maintenance.log_compressor import LogCompressor

        # Create mock archive handler
        mock_handler = MagicMock()
        mock_handler.create_archive = MagicMock()

        # Setup container mock
        mock_container.get_service.return_value = mock_handler

        # Create a log file to compress
        log_file = temp_dir / "test.log.1"
        log_file.write_text("old log content")

        result = LogCompressor.compress_old_logs(str(temp_dir))

        # Verify archive handler was called
        mock_handler.create_archive.assert_called_once()

        # Original file should be deleted
        assert not log_file.exists()

    @patch('nodupe.tools.maintenance.log_compressor.global_container')
    def test_compress_old_logs_skip_existing_zip(self, mock_container, temp_dir):
        """Test that .zip files are skipped."""
        from nodupe.tools.maintenance.log_compressor import LogCompressor

        # Create mock archive handler
        mock_handler = MagicMock()
        mock_container.get_service.return_value = mock_handler

        # Create a zip file (should be skipped)
        zip_file = temp_dir / "test.log.zip"
        zip_file.write_text("already compressed")

        result = LogCompressor.compress_old_logs(str(temp_dir))

        # Handler should not be called
        mock_handler.create_archive.assert_not_called()

        assert result == []

    @patch('nodupe.tools.maintenance.log_compressor.global_container')
    def test_compress_old_logs_handles_exception(self, mock_container, temp_dir):
        """Test that exceptions are handled gracefully."""
        from nodupe.tools.maintenance.log_compressor import LogCompressor

        # Create mock archive handler that raises exception
        mock_handler = MagicMock()
        mock_handler.create_archive.side_effect = Exception("Archive error")
        mock_container.get_service.return_value = mock_handler

        # Create a log file
        log_file = temp_dir / "test.log.1"
        log_file.write_text("old log content")

        result = LogCompressor.compress_old_logs(str(temp_dir))

        # Should return empty list and handle exception
        assert result == []
        assert log_file.exists()  # Original file should remain

    def test_recovery_manual_content(self):
        """Test that recovery manual contains expected content."""
        from nodupe.tools.maintenance.log_compressor import LogCompressor

        manual = LogCompressor.RECOVERY_MANUAL

        assert "ISO 14721" in manual
        assert "OAIS" in manual
        assert "METADATA.json" in manual
        assert "sha256sum" in manual
        assert "ISO 8601" in manual
        assert "RFC 3339" in manual
        assert "ISO/IEC 21320-1" in manual
