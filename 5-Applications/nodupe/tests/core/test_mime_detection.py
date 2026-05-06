"""Tests for MIME detection module."""

import pytest
from pathlib import Path
from nodupe.tools.mime.mime_logic import MIMEDetection, MIMEDetectionError


class TestMIMEDetection:
    """Test MIMEDetection class."""

    @pytest.fixture
    def detector(self):
        """Create a MIMEDetection instance for tests."""
        return MIMEDetection()

    def test_detect_mime_type_by_extension(self, tmp_path, detector):
        """Test MIME detection by file extension."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        mime = detector.detect_mime_type(str(test_file), use_magic=False)
        assert mime == "text/plain"

    def test_detect_mime_type_pdf(self, tmp_path, detector):
        """Test PDF MIME detection."""
        test_file = tmp_path / "test.pdf"
        # PDF magic number
        test_file.write_bytes(b"%PDF-1.4\n")

        mime = detector.detect_mime_type(str(test_file), use_magic=True)
        assert mime == "application/pdf"

    def test_detect_mime_type_jpeg(self, tmp_path, detector):
        """Test JPEG MIME detection."""
        test_file = tmp_path / "test.jpg"
        # JPEG magic number
        test_file.write_bytes(b"\xFF\xD8\xFF\xE0" + b"\x00" * 100)

        mime = detector.detect_mime_type(str(test_file), use_magic=True)
        assert mime == "image/jpeg"

    def test_detect_mime_type_png(self, tmp_path, detector):
        """Test PNG MIME detection."""
        test_file = tmp_path / "test.png"
        # PNG magic number
        test_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        mime = detector.detect_mime_type(str(test_file), use_magic=True)
        assert mime == "image/png"

    def test_detect_mime_type_unknown(self, tmp_path, detector):
        """Test unknown MIME type defaults to octet-stream."""
        test_file = tmp_path / "test.unknown"
        test_file.write_bytes(b"random data")

        mime = detector.detect_mime_type(str(test_file))
        assert mime == "application/octet-stream"

    def test_get_extension_for_mime(self, detector):
        """Test getting file extension for MIME type."""
        ext = detector.get_extension_for_mime("image/jpeg")
        assert ext in [".jpg", ".jpeg", ".jpe"]

        ext = detector.get_extension_for_mime("text/plain")
        assert ext == ".txt"

    def test_is_text(self, detector):
        """Test text MIME type detection."""
        assert detector.is_text("text/plain")
        assert detector.is_text("text/html")
        assert detector.is_text("application/json")
        assert detector.is_text("application/xml")
        assert not detector.is_text("image/jpeg")

    def test_is_image(self, detector):
        """Test image MIME type detection."""
        assert detector.is_image("image/jpeg")
        assert detector.is_image("image/png")
        assert not detector.is_image("text/plain")

    def test_is_audio(self, detector):
        """Test audio MIME type detection."""
        assert detector.is_audio("audio/mpeg")
        assert detector.is_audio("audio/wav")
        assert not detector.is_audio("video/mp4")

    def test_is_video(self, detector):
        """Test video MIME type detection."""
        assert detector.is_video("video/mp4")
        assert detector.is_video("video/avi")
        assert not detector.is_video("audio/mpeg")

    def test_is_archive(self, detector):
        """Test archive MIME type detection."""
        assert detector.is_archive("application/zip")
        assert detector.is_archive("application/x-tar")
        assert not detector.is_archive("text/plain")

    def test_extension_map_coverage(self, detector):
        """Test that extension map contains common formats."""
        assert ".jpg" in detector.EXTENSION_MAP
        assert ".png" in detector.EXTENSION_MAP
        assert ".pdf" in detector.EXTENSION_MAP
        assert ".mp3" in detector.EXTENSION_MAP
        assert ".mp4" in detector.EXTENSION_MAP
        assert ".zip" in detector.EXTENSION_MAP
