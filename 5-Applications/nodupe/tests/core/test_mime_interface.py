"""Tests for the mime_interface module."""

from unittest.mock import Mock

import pytest

from nodupe.core.mime_interface import MIMEDetectionInterface


class ConcreteMIMEDetector(MIMEDetectionInterface):
    """Concrete implementation of MIMEDetectionInterface for testing."""

    def __init__(self):
        """Initialize the concrete MIME detector with default values."""
        self._mime_type_result = "application/octet-stream"
        self._extension_result = None
        self._is_text_result = False
        self._is_image_result = False
        self._is_audio_result = False
        self._is_video_result = False
        self._is_archive_result = False

    def detect_mime_type(self, file_path: str, use_magic: bool = True) -> str:
        """Detect MIME type for a given file path.

        Args:
            file_path: Path to the file to check.
            use_magic: Whether to use magic bytes detection.

        Returns:
            The detected MIME type string.
        """
        return self._mime_type_result

    def get_extension_for_mime(self, mime_type: str) -> str | None:
        """Get file extension for a given MIME type.

        Args:
            mime_type: The MIME type to look up.

        Returns:
            The file extension including the dot, or None if not found.
        """
        return self._extension_result

    def is_text(self, mime_type: str) -> bool:
        """Check if MIME type is a text type.

        Args:
            mime_type: The MIME type to check.

        Returns:
            True if the MIME type is text, False otherwise.
        """
        return self._is_text_result

    def is_image(self, mime_type: str) -> bool:
        """Check if MIME type is an image type.

        Args:
            mime_type: The MIME type to check.

        Returns:
            True if the MIME type is an image, False otherwise.
        """
        return self._is_image_result

    def is_audio(self, mime_type: str) -> bool:
        """Check if MIME type is an audio type.

        Args:
            mime_type: The MIME type to check.

        Returns:
            True if the MIME type is audio, False otherwise.
        """
        return self._is_audio_result

    def is_video(self, mime_type: str) -> bool:
        """Check if MIME type is a video type.

        Args:
            mime_type: The MIME type to check.

        Returns:
            True if the MIME type is video, False otherwise.
        """
        return self._is_video_result

    def is_archive(self, mime_type: str) -> bool:
        """Check if MIME type is an archive type.

        Args:
            mime_type: The MIME type to check.

        Returns:
            True if the MIME type is an archive, False otherwise.
        """
        return self._is_archive_result


class TestMIMEDetectionInterface:
    """Test MIMEDetectionInterface abstract base class."""

    def test_interface_cannot_be_instantiated(self):
        """Test that MIMEDetectionInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            MIMEDetectionInterface()

    def test_concrete_implementation_can_be_instantiated(self):
        """Test that a concrete implementation can be instantiated."""
        detector = ConcreteMIMEDetector()
        assert detector is not None

    def test_detect_mime_type_abstract_method(self):
        """Test detect_mime_type method signature."""
        detector = ConcreteMIMEDetector()
        detector._mime_type_result = "text/plain"
        result = detector.detect_mime_type("/path/to/file.txt")
        assert isinstance(result, str)

    def test_detect_mime_type_with_use_magic_true(self):
        """Test detect_mime_type with use_magic=True."""
        detector = ConcreteMIMEDetector()
        detector._mime_type_result = "text/plain"
        result = detector.detect_mime_type("/path/to/file.txt", use_magic=True)
        assert isinstance(result, str)

    def test_detect_mime_type_with_use_magic_false(self):
        """Test detect_mime_type with use_magic=False."""
        detector = ConcreteMIMEDetector()
        detector._mime_type_result = "text/plain"
        result = detector.detect_mime_type("/path/to/file.txt", use_magic=False)
        assert isinstance(result, str)

    def test_get_extension_for_mime_abstract_method(self):
        """Test get_extension_for_mime method signature."""
        detector = ConcreteMIMEDetector()
        detector._extension_result = ".txt"
        result = detector.get_extension_for_mime("text/plain")
        assert result == ".txt"

    def test_get_extension_for_mime_returns_none(self):
        """Test get_extension_for_mime returning None."""
        detector = ConcreteMIMEDetector()
        detector._extension_result = None
        result = detector.get_extension_for_mime("unknown/type")
        assert result is None

    def test_is_text_abstract_method(self):
        """Test is_text method signature."""
        detector = ConcreteMIMEDetector()
        detector._is_text_result = True
        result = detector.is_text("text/plain")
        assert isinstance(result, bool)

    def test_is_image_abstract_method(self):
        """Test is_image method signature."""
        detector = ConcreteMIMEDetector()
        detector._is_image_result = True
        result = detector.is_image("image/jpeg")
        assert isinstance(result, bool)

    def test_is_audio_abstract_method(self):
        """Test is_audio method signature."""
        detector = ConcreteMIMEDetector()
        detector._is_audio_result = True
        result = detector.is_audio("audio/mpeg")
        assert isinstance(result, bool)

    def test_is_video_abstract_method(self):
        """Test is_video method signature."""
        detector = ConcreteMIMEDetector()
        detector._is_video_result = True
        result = detector.is_video("video/mp4")
        assert isinstance(result, bool)

    def test_is_archive_abstract_method(self):
        """Test is_archive method signature."""
        detector = ConcreteMIMEDetector()
        detector._is_archive_result = True
        result = detector.is_archive("application/zip")
        assert isinstance(result, bool)


class TestMIMEDetectionInterfaceImplementation:
    """Test MIMEDetectionInterface with concrete implementations."""

    def test_detect_mime_type_various_paths(self):
        """Test detect_mime_type with various file paths."""
        detector = ConcreteMIMEDetector()
        detector._mime_type_result = "text/plain"

        assert detector.detect_mime_type("/absolute/path/file.txt") == "text/plain"
        assert detector.detect_mime_type("relative/path/file.txt") == "text/plain"
        assert detector.detect_mime_type("file.txt") == "text/plain"

    def test_detect_mime_type_various_types(self):
        """Test detect_mime_type with various MIME types."""
        detector = ConcreteMIMEDetector()

        detector._mime_type_result = "text/plain"
        assert detector.detect_mime_type("/file.txt") == "text/plain"

        detector._mime_type_result = "image/jpeg"
        assert detector.detect_mime_type("/file.jpg") == "image/jpeg"

        detector._mime_type_result = "application/pdf"
        assert detector.detect_mime_type("/file.pdf") == "application/pdf"

        detector._mime_type_result = "video/mp4"
        assert detector.detect_mime_type("/file.mp4") == "video/mp4"

    def test_get_extension_for_mime_various_types(self):
        """Test get_extension_for_mime with various MIME types."""
        detector = ConcreteMIMEDetector()

        detector._extension_result = ".txt"
        assert detector.get_extension_for_mime("text/plain") == ".txt"

        detector._extension_result = ".jpg"
        assert detector.get_extension_for_mime("image/jpeg") == ".jpg"

        detector._extension_result = ".pdf"
        assert detector.get_extension_for_mime("application/pdf") == ".pdf"

        detector._extension_result = ".mp4"
        assert detector.get_extension_for_mime("video/mp4") == ".mp4"

    def test_is_text_various_types(self):
        """Test is_text with various MIME types."""
        detector = ConcreteMIMEDetector()

        detector._is_text_result = True
        assert detector.is_text("text/plain") is True
        assert detector.is_text("text/html") is True
        assert detector.is_text("text/css") is True

        detector._is_text_result = False
        assert detector.is_text("image/jpeg") is False
        assert detector.is_text("application/pdf") is False

    def test_is_image_various_types(self):
        """Test is_image with various MIME types."""
        detector = ConcreteMIMEDetector()

        detector._is_image_result = True
        assert detector.is_image("image/jpeg") is True
        assert detector.is_image("image/png") is True
        assert detector.is_image("image/gif") is True

        detector._is_image_result = False
        assert detector.is_image("text/plain") is False
        assert detector.is_image("video/mp4") is False

    def test_is_audio_various_types(self):
        """Test is_audio with various MIME types."""
        detector = ConcreteMIMEDetector()

        detector._is_audio_result = True
        assert detector.is_audio("audio/mpeg") is True
        assert detector.is_audio("audio/wav") is True
        assert detector.is_audio("audio/ogg") is True

        detector._is_audio_result = False
        assert detector.is_audio("text/plain") is False
        assert detector.is_audio("video/mp4") is False

    def test_is_video_various_types(self):
        """Test is_video with various MIME types."""
        detector = ConcreteMIMEDetector()

        detector._is_video_result = True
        assert detector.is_video("video/mp4") is True
        assert detector.is_video("video/avi") is True
        assert detector.is_video("video/webm") is True

        detector._is_video_result = False
        assert detector.is_video("text/plain") is False
        assert detector.is_video("audio/mpeg") is False

    def test_is_archive_various_types(self):
        """Test is_archive with various MIME types."""
        detector = ConcreteMIMEDetector()

        detector._is_archive_result = True
        assert detector.is_archive("application/zip") is True
        assert detector.is_archive("application/x-tar") is True
        assert detector.is_archive("application/gzip") is True

        detector._is_archive_result = False
        assert detector.is_archive("text/plain") is False
        assert detector.is_archive("image/jpeg") is False


class TestMIMEDetectionInterfaceMock:
    """Test MIMEDetectionInterface with mock implementations."""

    def test_mock_implementation(self):
        """Test with mock implementation."""
        mock_detector = Mock(spec=MIMEDetectionInterface)
        mock_detector.detect_mime_type.return_value = "text/plain"
        mock_detector.get_extension_for_mime.return_value = ".txt"
        mock_detector.is_text.return_value = True
        mock_detector.is_image.return_value = False
        mock_detector.is_audio.return_value = False
        mock_detector.is_video.return_value = False
        mock_detector.is_archive.return_value = False

        assert mock_detector.detect_mime_type("/test.txt") == "text/plain"
        assert mock_detector.get_extension_for_mime("text/plain") == ".txt"
        assert mock_detector.is_text("text/plain") is True
        assert mock_detector.is_image("text/plain") is False
        assert mock_detector.is_audio("text/plain") is False
        assert mock_detector.is_video("text/plain") is False
        assert mock_detector.is_archive("text/plain") is False


class TestMIMEDetectionInterfaceEdgeCases:
    """Test edge cases for MIMEDetectionInterface."""

    def test_detect_mime_type_none_path(self):
        """Test detect_mime_type with None path."""
        detector = ConcreteMIMEDetector()
        detector._mime_type_result = "application/octet-stream"

        result = detector.detect_mime_type(None)  # type: ignore
        assert isinstance(result, str)

    def test_detect_mime_type_empty_path(self):
        """Test detect_mime_type with empty path."""
        detector = ConcreteMIMEDetector()
        detector._mime_type_result = "application/octet-stream"

        result = detector.detect_mime_type("")
        assert isinstance(result, str)

    def test_get_extension_for_mime_none_type(self):
        """Test get_extension_for_mime with None MIME type."""
        detector = ConcreteMIMEDetector()
        detector._extension_result = None

        result = detector.get_extension_for_mime(None)  # type: ignore
        assert result is None

    def test_get_extension_for_mime_empty_type(self):
        """Test get_extension_for_mime with empty MIME type."""
        detector = ConcreteMIMEDetector()
        detector._extension_result = None

        result = detector.get_extension_for_mime("")
        assert result is None

    def test_is_text_none_type(self):
        """Test is_text with None MIME type."""
        detector = ConcreteMIMEDetector()
        detector._is_text_result = False

        result = detector.is_text(None)  # type: ignore
        assert isinstance(result, bool)

    def test_is_image_none_type(self):
        """Test is_image with None MIME type."""
        detector = ConcreteMIMEDetector()
        detector._is_image_result = False

        result = detector.is_image(None)  # type: ignore
        assert isinstance(result, bool)

    def test_is_audio_none_type(self):
        """Test is_audio with None MIME type."""
        detector = ConcreteMIMEDetector()
        detector._is_audio_result = False

        result = detector.is_audio(None)  # type: ignore
        assert isinstance(result, bool)

    def test_is_video_none_type(self):
        """Test is_video with None MIME type."""
        detector = ConcreteMIMEDetector()
        detector._is_video_result = False

        result = detector.is_video(None)  # type: ignore
        assert isinstance(result, bool)

    def test_is_archive_none_type(self):
        """Test is_archive with None MIME type."""
        detector = ConcreteMIMEDetector()
        detector._is_archive_result = False

        result = detector.is_archive(None)  # type: ignore
        assert isinstance(result, bool)

    def test_interface_subclass_check(self):
        """Test that concrete implementation is recognized as subclass."""
        assert issubclass(ConcreteMIMEDetector, MIMEDetectionInterface)

    def test_instance_check(self):
        """Test that concrete instance is recognized as instance."""
        detector = ConcreteMIMEDetector()
        assert isinstance(detector, MIMEDetectionInterface)

    def test_detect_mime_type_default_use_magic(self):
        """Test detect_mime_type with default use_magic parameter."""
        detector = ConcreteMIMEDetector()
        detector._mime_type_result = "text/plain"

        # Should work without specifying use_magic
        result = detector.detect_mime_type("/file.txt")
        assert result == "text/plain"

    def test_get_extension_for_mime_unknown_type(self):
        """Test get_extension_for_mime with unknown MIME type."""
        detector = ConcreteMIMEDetector()
        detector._extension_result = None

        result = detector.get_extension_for_mime("unknown/unknown")
        assert result is None

    def test_all_type_checks_same_mime_type(self):
        """Test all type check methods with same MIME type."""
        detector = ConcreteMIMEDetector()

        # Set all to False
        detector._is_text_result = False
        detector._is_image_result = False
        detector._is_audio_result = False
        detector._is_video_result = False
        detector._is_archive_result = False

        mime_type = "application/octet-stream"

        assert detector.is_text(mime_type) is False
        assert detector.is_image(mime_type) is False
        assert detector.is_audio(mime_type) is False
        assert detector.is_video(mime_type) is False
        assert detector.is_archive(mime_type) is False

    def test_detect_mime_type_use_magic_parameter_variations(self):
        """Test detect_mime_type with various use_magic parameter values."""
        detector = ConcreteMIMEDetector()
        detector._mime_type_result = "text/plain"

        # Test with explicit True
        result_true = detector.detect_mime_type("/file.txt", use_magic=True)
        assert result_true == "text/plain"

        # Test with explicit False
        result_false = detector.detect_mime_type("/file.txt", use_magic=False)
        assert result_false == "text/plain"

        # Test with default (should use True)
        result_default = detector.detect_mime_type("/file.txt")
        assert result_default == "text/plain"
