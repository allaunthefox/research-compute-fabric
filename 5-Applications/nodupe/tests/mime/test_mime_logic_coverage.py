"""Test MIME Logic Module - Coverage Completion.

Tests to achieve 100% coverage for mime_logic.py
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from nodupe.tools.mime.mime_logic import (
    MIMEDetection,
    MIMEDetectionError,
)


@pytest.fixture
def detector():
    """Create a MIMEDetection instance for tests."""
    return MIMEDetection()


class TestMIMEDetectionMagicNumbers:
    """Test MIME detection using magic numbers."""

    def test_detect_by_magic_jpeg(self, detector):
        """Test detecting JPEG by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'image/jpeg'

    def test_detect_by_magic_png(self, detector):
        """Test detecting PNG by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'image/png'

    def test_detect_by_magic_gif87a(self, detector):
        """Test detecting GIF87a by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'GIF87a')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'image/gif'

    def test_detect_by_magic_gif89a(self, detector):
        """Test detecting GIF89a by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'GIF89a')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'image/gif'

    def test_detect_by_magic_bmp(self, detector):
        """Test detecting BMP by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'BM')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'image/bmp'

    def test_detect_by_magic_tiff_little_endian(self, detector):
        """Test detecting TIFF (little-endian) by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'II*\x00')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'image/tiff'

    def test_detect_by_magic_tiff_big_endian(self, detector):
        """Test detecting TIFF (big-endian) by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'MM\x00*')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'image/tiff'

    def test_detect_by_magic_pdf(self, detector):
        """Test detecting PDF by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'%PDF-1.4')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'application/pdf'

    def test_detect_by_magic_zip(self, detector):
        """Test detecting ZIP by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'PK\x03\x04')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'application/zip'

    def test_detect_by_magic_doc(self, detector):
        """Test detecting DOC by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'application/msword'

    def test_detect_by_magic_mp3_id3(self, detector):
        """Test detecting MP3 (with ID3) by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'ID3')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'audio/mpeg'

    def test_detect_by_magic_mp3_frame(self, detector):
        """Test detecting MP3 (frame sync) by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'\xFF\xFB')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'audio/mpeg'

    def test_detect_by_magic_flac(self, detector):
        """Test detecting FLAC by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'fLaC')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'audio/flac'

    def test_detect_by_magic_ogg(self, detector):
        """Test detecting OGG by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'OggS')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'audio/ogg'

    def test_detect_by_magic_mp4(self, detector):
        """Test detecting MP4 by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'\x00\x00\x00\x18ftyp')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'video/mp4'

    def test_detect_by_magic_webm(self, detector):
        """Test detecting WebM by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'\x1A\x45\xDF\xA3')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'video/webm'

    def test_detect_by_magic_rar(self, detector):
        """Test detecting RAR by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'Rar!\x1A\x07')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'application/x-rar-compressed'

    def test_detect_by_magic_7z(self, detector):
        """Test detecting 7z by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'7z\xBC\xAF\x27\x1C')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'application/x-7z-compressed'

    def test_detect_by_magic_tar(self, detector):
        """Test detecting TAR by magic number (at offset 257)."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Write 257 bytes of padding then 'ustar'
            f.write(b'\x00' * 257 + b'ustar')
            f.flush()
            result = detector._detect_by_magic(Path(f.name), max_read=512)
            assert result == 'application/x-tar'

    def test_detect_by_magic_exe(self, detector):
        """Test detecting EXE by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'MZ')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'application/x-msdownload'

    def test_detect_by_magic_elf(self, detector):
        """Test detecting ELF by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'\x7FELF')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'application/x-executable'

    def test_detect_by_magic_wav(self, detector):
        """Test detecting WAV by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'RIFFxxxxWAVE')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'audio/wav'

    def test_detect_by_magic_webp(self, detector):
        """Test detecting WebP by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'RIFFxxxxWEBP')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'image/webp'

    def test_detect_by_magic_avi(self, detector):
        """Test detecting AVI by magic number."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'RIFFxxxxAVI ')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result == 'video/avi'

    def test_detect_by_magic_no_match(self, detector):
        """Test detecting file with no magic number match."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'random data with no magic')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result is None

    def test_detect_by_magic_file_read_error(self, detector):
        """Test detecting MIME when file read fails."""
        with patch('builtins.open', side_effect=IOError("Cannot read")):
            result = detector._detect_by_magic(Path("/test"))
            assert result is None

    def test_detect_by_magic_header_too_short(self, detector):
        """Test detecting MIME when header is too short."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'\xFF')  # Too short for JPEG detection
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            assert result is None


class TestMIMEDetectionDetectMimeType:
    """Test detect_mime_type method."""

    def test_detect_mime_type_path_object(self, detector):
        """Test detecting MIME type with Path object."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'test content')
            f.flush()
            result = detector.detect_mime_type(Path(f.name))
            assert 'text' in result or 'application' in result

    def test_detect_mime_type_use_magic_false(self, detector):
        """Test detecting MIME type without magic number detection."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'test content')
            f.flush()
            result = detector.detect_mime_type(Path(f.name), use_magic=False)
            assert result is not None

    def test_detect_mime_type_file_not_exists(self, detector):
        """Test detecting MIME type for nonexistent file."""
        result = detector.detect_mime_type("/nonexistent/file.x999")
        # Should return default octet-stream
        assert result == 'application/octet-stream'

    def test_detect_mime_type_unknown_extension(self, detector):
        """Test detecting MIME type for unknown extension."""
        with tempfile.NamedTemporaryFile(suffix='.xyz123', delete=False) as f:
            f.write(b'test')
            f.flush()
            result = detector.detect_mime_type(Path(f.name), use_magic=False)
            # Should return default
            assert result == 'application/octet-stream'

    def test_detect_mime_type_exception(self, detector):
        """Test detecting MIME type with exception."""
        with patch('pathlib.Path.exists', side_effect=Exception("Error")):
            with pytest.raises(MIMEDetectionError) as exc_info:
                detector.detect_mime_type("/test")
            assert "Failed to detect" in str(exc_info.value)


class TestMIMEDetectionGetExtensionForMime:
    """Test get_extension_for_mime method."""

    def test_get_extension_for_mime_known(self, detector):
        """Test getting extension for known MIME type."""
        result = detector.get_extension_for_mime('image/jpeg')
        assert result is not None
        assert '.jpg' in result or '.jpeg' in result

    def test_get_extension_for_mime_unknown(self, detector):
        """Test getting extension for unknown MIME type."""
        result = detector.get_extension_for_mime('application/unknown-xyz')
        # May return None or a default
        assert result is None or isinstance(result, str)

    def test_get_extension_for_mime_via_map(self, detector):
        """Test getting extension via extension map."""
        result = detector.get_extension_for_mime('text/x-python')
        assert result == '.py'


class TestMIMEDetectionIsText:
    """Test is_text method."""

    def test_is_text_text_plain(self, detector):
        """Test is_text with text/plain."""
        assert detector.is_text('text/plain') is True

    def test_is_text_text_html(self, detector):
        """Test is_text with text/html."""
        assert detector.is_text('text/html') is True

    def test_is_text_application_json(self, detector):
        """Test is_text with application/json."""
        assert detector.is_text('application/json') is True

    def test_is_text_application_xml(self, detector):
        """Test is_text with application/xml."""
        assert detector.is_text('application/xml') is True

    def test_is_text_application_javascript(self, detector):
        """Test is_text with application/javascript."""
        assert detector.is_text('application/javascript') is True

    def test_is_text_application_x_sh(self, detector):
        """Test is_text with application/x-sh."""
        assert detector.is_text('application/x-sh') is True

    def test_is_text_image(self, detector):
        """Test is_text with image MIME type."""
        assert detector.is_text('image/jpeg') is False

    def test_is_text_video(self, detector):
        """Test is_text with video MIME type."""
        assert detector.is_text('video/mp4') is False


class TestMIMEDetectionIsImage:
    """Test is_image method."""

    def test_is_image_jpeg(self, detector):
        """Test is_image with image/jpeg."""
        assert detector.is_image('image/jpeg') is True

    def test_is_image_png(self, detector):
        """Test is_image with image/png."""
        assert detector.is_image('image/png') is True

    def test_is_image_text(self, detector):
        """Test is_image with text MIME type."""
        assert detector.is_image('text/plain') is False


class TestMIMEDetectionIsAudio:
    """Test is_audio method."""

    def test_is_audio_mpeg(self, detector):
        """Test is_audio with audio/mpeg."""
        assert detector.is_audio('audio/mpeg') is True

    def test_is_audio_wav(self, detector):
        """Test is_audio with audio/wav."""
        assert detector.is_audio('audio/wav') is True

    def test_is_audio_text(self, detector):
        """Test is_audio with text MIME type."""
        assert detector.is_audio('text/plain') is False


class TestMIMEDetectionIsVideo:
    """Test is_video method."""

    def test_is_video_mp4(self, detector):
        """Test is_video with video/mp4."""
        assert detector.is_video('video/mp4') is True

    def test_is_video_webm(self, detector):
        """Test is_video with video/webm."""
        assert detector.is_video('video/webm') is True

    def test_is_video_text(self, detector):
        """Test is_video with text MIME type."""
        assert detector.is_video('text/plain') is False


class TestMIMEDetectionIsArchive:
    """Test is_archive method."""

    def test_is_archive_zip(self, detector):
        """Test is_archive with application/zip."""
        assert detector.is_archive('application/zip') is True

    def test_is_archive_rar(self, detector):
        """Test is_archive with application/x-rar-compressed."""
        assert detector.is_archive('application/x-rar-compressed') is True

    def test_is_archive_7z(self, detector):
        """Test is_archive with application/x-7z-compressed."""
        assert detector.is_archive('application/x-7z-compressed') is True

    def test_is_archive_tar(self, detector):
        """Test is_archive with application/x-tar."""
        assert detector.is_archive('application/x-tar') is True

    def test_is_archive_gzip(self, detector):
        """Test is_archive with application/gzip."""
        assert detector.is_archive('application/gzip') is True

    def test_is_archive_bzip2(self, detector):
        """Test is_archive with application/x-bzip2."""
        assert detector.is_archive('application/x-bzip2') is True

    def test_is_archive_xz(self, detector):
        """Test is_archive with application/x-xz."""
        assert detector.is_archive('application/x-xz') is True

    def test_is_archive_lzma(self, detector):
        """Test is_archive with application/x-lzma."""
        assert detector.is_archive('application/x-lzma') is True

    def test_is_archive_text(self, detector):
        """Test is_archive with text MIME type."""
        assert detector.is_archive('text/plain') is False


class TestMIMEDetectionError:
    """Test MIMEDetectionError exception."""

    def test_mime_detection_error_creation(self):
        """Test creating MIMEDetectionError."""
        error = MIMEDetectionError("Test error")
        assert str(error) == "Test error"

    def test_mime_detection_error_with_cause(self):
        """Test creating MIMEDetectionError with cause."""
        original_error = ValueError("Original error")
        error = MIMEDetectionError("MIME error")
        error.__cause__ = original_error
        assert error.__cause__ is not None


class TestMIMEDetectionMagicNumbersUncovered:
    """Test uncovered branches in magic number detection."""

    def test_detect_by_magic_riff_unknown_subtype(self, detector):
        """Test RIFF with unknown subtype (line 173)."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Write RIFF with unknown subtype (not WAVE, WEBP, or AVI)
            f.write(b'RIFFxxxxXXXX')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            # Should return None since subtype doesn't match known types
            assert result is None

    def test_detect_by_magic_riff_short_header(self, detector):
        """Test RIFF magic detection when header is too short (line 183)."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Write minimal content (less than 12 bytes so can't check RIFF subtype)
            f.write(b'RIFF')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            # Header too short to check subtype, returns default 'image/webp' for RIFF
            assert result == 'image/webp'

    def test_detect_by_magic_pk_extension(self, detector):
        """Test PK signature at different offsets."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'PK\x03\x04extra')
            f.flush()
            result = detector._detect_by_magic(Path(f.name))
            # Should return zip
            assert result == 'application/zip'

    def test_extension_map_odt(self, detector):
        """Test ODT extension mapping."""
        result = detector.get_extension_for_mime('application/vnd.oasis.opendocument.text')
        assert result == '.odt'

    def test_extension_map_rtf(self, detector):
        """Test RTF extension mapping."""
        result = detector.get_extension_for_mime('application/rtf')
        assert result == '.rtf'

    def test_extension_map_not_found(self, detector):
        """Test extension mapping when not found (line 255)."""
        # This should exercise the return None at the end of get_extension_for_mime
        # when neither mimetypes nor the reverse map finds anything
        result = detector.get_extension_for_mime('application/x-custom-unknown')
        # Should return None when no extension found
        assert result is None


class TestMIMEDetectionCoverage:
    """Test specific uncovered lines for coverage."""

    def test_detect_mime_type_with_extension_in_map(self, detector):
        """Test detect_mime_type when extension is in EXTENSION_MAP (line 183)."""
        # Create a file with an extension that's in our custom EXTENSION_MAP
        # .svg is in EXTENSION_MAP as 'image/svg+xml'
        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as f:
            f.write(b'<svg></svg>')
            f.flush()
            # Use magic=False to ensure we go through extension mapping path
            result = detector.detect_mime_type(Path(f.name), use_magic=False)
            # Should return image/svg+xml from our EXTENSION_MAP
            assert result == 'image/svg+xml'

    def test_detect_mime_type_magic_returns_value(self, detector):
        """Test detect_mime_type when magic detection returns a value (line 173)."""
        # Create a file with a magic number that will be detected
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Write JPEG magic bytes
            f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF')
            f.flush()
            # use_magic=True should detect and return 'image/jpeg'
            result = detector.detect_mime_type(Path(f.name), use_magic=True)
            assert result == 'image/jpeg'

    def test_get_extension_for_mime_reverse_lookup(self, detector):
        """Test get_extension_for_mime when reverse lookup finds extension (line 255)."""
        # Use a MIME type that's in our custom EXTENSION_MAP but not in mimetypes
        # .svg maps to 'image/svg+xml'
        result = detector.get_extension_for_mime('image/svg+xml')
        # Should find via reverse lookup
        assert result == '.svg'

    def test_detect_mime_type_ico_extension(self, detector):
        """Test detect_mime_type with .ico extension."""
        # .ico returns from mimetypes as 'image/vnd.microsoft.icon'
        with tempfile.NamedTemporaryFile(suffix='.ico', delete=False) as f:
            f.write(b'\x00\x00\x01\x00')
            f.flush()
            result = detector.detect_mime_type(Path(f.name), use_magic=False)
            # mimetypes returns 'image/vnd.microsoft.icon' for .ico
            assert result == 'image/vnd.microsoft.icon'

    def test_get_extension_for_mime_ico(self, detector):
        """Test get_extension_for_mime with image/x-icon."""
        result = detector.get_extension_for_mime('image/x-icon')
        assert result == '.ico'

    def test_detect_mime_type_gz_extension(self, detector):
        """Test detect_mime_type with .gz extension (not in mimetypes, in EXTENSION_MAP)."""
        # .gz is in EXTENSION_MAP but NOT in mimetypes
        with tempfile.NamedTemporaryFile(suffix='.gz', delete=False) as f:
            f.write(b'\x1f\x8b\x08')
            f.flush()
            result = detector.detect_mime_type(Path(f.name), use_magic=False)
            # Should use EXTENSION_MAP
            assert result == 'application/gzip'

    def test_detect_mime_type_bz2_extension(self, detector):
        """Test detect_mime_type with .bz2 extension (not in mimetypes, in EXTENSION_MAP)."""
        # .bz2 is in EXTENSION_MAP but NOT in mimetypes
        with tempfile.NamedTemporaryFile(suffix='.bz2', delete=False) as f:
            f.write(b'BZ')
            f.flush()
            result = detector.detect_mime_type(Path(f.name), use_magic=False)
            # Should use EXTENSION_MAP
            assert result == 'application/x-bzip2'
