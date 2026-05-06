# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Compression Engine Module.

Compression and archive utilities using standard library only.

Key Features:
    - Data compression (gzip, bz2, lzma)
    - File compression and decompression
    - Archive creation and extraction (zip, tar, tar.gz, tar.bz2, tar.xz)
    - Path validation for security
    - Compression ratio estimation
    - Standard library only (no external dependencies)

Dependencies:
    - gzip (standard library)
    - bz2 (standard library)
    - lzma (standard library)
    - tarfile (standard library)
    - zipfile (standard library)
    - pathlib (standard library)
"""

from __future__ import annotations
import gzip
import bz2
import lzma
import tarfile
import zipfile
from pathlib import Path
from typing import Optional, List, Union


PathLike = Union[str, Path]


class CompressionError(Exception):
    """Exception raised for compression and archive operations.

    Attributes:
        message: Explanation of the error
    """
    pass


class Compression:
    """Compression and archive operations handler.

    Provides static methods for compressing/decompressing data and files,
    as well as creating and extracting archives in various formats.

    Attributes:
        DATA_FORMATS: List of supported compression formats
        EXTENSION_MAP: Mapping of file extensions to format names
        FORMAT_EXTENSION: Mapping of format names to file extensions
        TAR_MODE_MAP: Mapping of tar format names to tarfile modes
        COMPRESSION_RATIOS: Estimated compression ratios by format and data type
    """

    DATA_FORMATS = ['gzip', 'bz2', 'lzma']
    EXTENSION_MAP = {
        '.gz': 'gzip',
        '.bz2': 'bz2',
        '.xz': 'lzma',
        '.zip': 'zip'
    }

    FORMAT_EXTENSION = {
        'gzip': '.gz',
        'bz2': '.bz2',
        'lzma': '.xz',
        'zip': '.zip'
    }

    TAR_MODE_MAP = {
        'tar': 'w',
        'tar.gz': 'w:gz',
        'tar.bz2': 'w:bz2',
        'tar.xz': 'w:xz'
    }

    COMPRESSION_RATIOS = {
        'gzip': {'text': 0.3, 'binary': 0.6, 'image': 0.9, 'video': 0.95},
        'gz': {'text': 0.3, 'binary': 0.6, 'image': 0.9, 'video': 0.95},
        'bz2': {'text': 0.25, 'binary': 0.55, 'image': 0.9, 'video': 0.95},
        'lzma': {'text': 0.2, 'binary': 0.5, 'image': 0.9, 'video': 0.95},
        'xz': {'text': 0.2, 'binary': 0.5, 'image': 0.9, 'video': 0.95},
    }

    @staticmethod
    def _ensure_path(path: PathLike) -> Path:
        """Ensure path is a Path object.

        Args:
            path: Path as string or Path object

        Returns:
            Path object
        """
        return Path(path)

    @staticmethod
    def _validate_extraction_path(output_dir: Path, member_name: str) -> None:
        """Validate extraction path to prevent directory traversal attacks.

        Args:
            output_dir: Target extraction directory
            member_name: Name of archive member to extract

        Raises:
            CompressionError: If the extraction path is unsafe
        """
        member_path = (output_dir / member_name).resolve()
        output_dir_resolved = output_dir.resolve()
        try:
            member_path.relative_to(output_dir_resolved)
        except ValueError:
            raise CompressionError(
                f"Unsafe extraction path: {member_name}"
            )

    @staticmethod
    def _validate_format(format: str) -> None:
        """Validate that the format is supported.

        Args:
            format: Compression or archive format name

        Raises:
            CompressionError: If format is not supported
        """
        if format not in Compression.DATA_FORMATS and \
           format not in Compression.FORMAT_EXTENSION and \
           format not in Compression.TAR_MODE_MAP:
            raise CompressionError(f"Unsupported format: {format}")

    @staticmethod
    def compress_data(data: bytes, format: str = 'gzip', level: int = 6) -> bytes:
        """Compress raw bytes data.

        Args:
            data: Bytes to compress
            format: Compression format ('gzip', 'bz2', or 'lzma')
            level: Compression level (1-9 for gzip/bz2, 0-9 for lzma)

        Returns:
            Compressed bytes

        Raises:
            CompressionError: If compression fails or format is unsupported
        """
        Compression._validate_format(format)

        try:
            if format == 'gzip':
                return gzip.compress(data, compresslevel=level)
            if format == 'bz2':
                return bz2.compress(data, compresslevel=level)
            if format == 'lzma':
                return lzma.compress(data, preset=level)
        except Exception as e:
            raise CompressionError(f"Compression failed: {e}") from e

        raise CompressionError(f"Unsupported format: {format}")

    @staticmethod
    def decompress_data(data: bytes, format: str = 'gzip') -> bytes:
        """Decompress compressed bytes data.

        Args:
            data: Compressed bytes to decompress
            format: Compression format ('gzip', 'bz2', or 'lzma')

        Returns:
            Decompressed bytes

        Raises:
            CompressionError: If decompression fails or format is unsupported
        """
        Compression._validate_format(format)

        try:
            if format == 'gzip':
                return gzip.decompress(data)
            if format == 'bz2':
                return bz2.decompress(data)
            if format == 'lzma':
                return lzma.decompress(data)
        except Exception as e:
            raise CompressionError(f"Decompression failed: {e}") from e

        raise CompressionError(f"Unsupported format: {format}")

    @staticmethod
    def compress_file(
        input_path: PathLike,
        output_path: Optional[PathLike] = None,
        format: str = 'gzip',
        remove_original: bool = False
    ) -> Path:
        """Compress a file.

        Args:
            input_path: Path to the input file
            output_path: Path for the output compressed file (None = auto-generate)
            format: Compression format ('gzip', 'bz2', 'lzma', or 'zip')
            remove_original: Whether to remove the original file after compression

        Returns:
            Path to the compressed file

        Raises:
            CompressionError: If compression fails
        """
        input_path = Compression._ensure_path(input_path)
        if not input_path.exists():
            raise CompressionError("Input file does not exist")

        Compression._validate_format(format)

        if output_path is None:
            ext = Compression.FORMAT_EXTENSION.get(format, f'.{format}')
            output_path = input_path.with_suffix(input_path.suffix + ext)
        else:
            output_path = Compression._ensure_path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if format in Compression.DATA_FORMATS:
                with open(input_path, 'rb') as src:
                    data = src.read()
                compressed = Compression.compress_data(data, format)
                with open(output_path, 'wb') as dst:
                    dst.write(compressed)

            elif format == 'zip':
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(input_path, arcname=input_path.name)

            else:
                raise CompressionError(f"Unsupported format: {format}")

        except Exception as e:
            raise CompressionError(f"File compression failed: {e}") from e

        if remove_original:
            try:
                input_path.unlink()
            except Exception as e:
                raise CompressionError(f"Failed to remove original: {e}") from e

        return output_path

    @staticmethod
    def create_archive(
        files: List[PathLike],
        output_path: PathLike,
        format: str = 'zip'
    ) -> Path:
        """Create an archive from a list of files.

        Args:
            files: List of paths to files to include
            output_path: Path to the resulting archive
            format: Archive format ('zip', 'tar', 'tar.gz', etc.)

        Returns:
            Path to the created archive

        Raises:
            CompressionError: If archive creation fails
        """
        output_path = Compression._ensure_path(output_path)
        Compression._validate_format(format)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if format == 'zip':
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for f in files:
                        f = Compression._ensure_path(f)
                        if f.exists():
                            zf.write(f, arcname=f.name)
                        else:
                            raise CompressionError(f"File not found: {f}")

            elif format in Compression.TAR_MODE_MAP:
                mode = Compression.TAR_MODE_MAP[format]
                with tarfile.open(output_path, mode) as tf:
                    for f in files:
                        f = Compression._ensure_path(f)
                        if f.exists():
                            tf.add(f, arcname=f.name)
                        else:
                            raise CompressionError(f"File not found: {f}")
            else:
                raise CompressionError(f"Unsupported format: {format}")

            return output_path

        except Exception as e:
            if isinstance(e, CompressionError):
                raise
            raise CompressionError(f"Archive creation failed: {e}") from e

    @staticmethod
    def decompress_file(
        input_path: PathLike,
        output_path: Optional[PathLike] = None,
        format: Optional[str] = None,
        remove_compressed: bool = False
    ) -> Path:
        """Decompress a compressed file.

        Args:
            input_path: Path to the compressed file
            output_path: Path for the output decompressed file (None = auto-generate)
            format: Compression format (None = auto-detect from extension)
            remove_compressed: Whether to remove the compressed file after decompression

        Returns:
            Path to the decompressed file

        Raises:
            CompressionError: If decompression fails
        """
        input_path = Compression._ensure_path(input_path)
        if not input_path.exists():
            raise CompressionError("Input file does not exist")

        if format is None:
            format = Compression.EXTENSION_MAP.get(input_path.suffix.lower())
            if not format:
                raise CompressionError("Cannot auto-detect format")

        Compression._validate_format(format)

        if output_path is None:
            output_path = input_path.with_suffix('')
        else:
            output_path = Compression._ensure_path(output_path)

        try:
            if format in Compression.DATA_FORMATS:
                with open(input_path, 'rb') as src:
                    data = src.read()
                decompressed = Compression.decompress_data(data, format)
                with open(output_path, 'wb') as dst:
                    dst.write(decompressed)

            elif format == 'zip':
                with zipfile.ZipFile(input_path, 'r') as zf:
                    for name in zf.namelist():
                        Compression._validate_extraction_path(output_path.parent, name)
                    zf.extractall(output_path.parent)

            else:
                raise CompressionError(f"Unsupported format: {format}")

        except Exception as e:
            raise CompressionError(f"File decompression failed: {e}") from e

        if remove_compressed:
            input_path.unlink()

        return output_path

    @staticmethod
    def extract_archive(
        archive_path: PathLike,
        output_dir: PathLike,
        format: Optional[str] = None,
        PASSWORD_REMOVED: Optional[bytes] = None
    ) -> List[Path]:
        """Extract archive (zip, tar, tar.gz, tar.bz2, tar.xz) to output directory.

        Args:
            archive_path: Path to the archive file
            output_dir: Directory to extract to
            format: Optional format hint ('zip', 'tar', 'tar.gz', etc.)
            PASSWORD_REMOVED: Optional PASSWORD_REMOVED for encrypted archives

        Returns:
            List of extracted file paths

        Raises:
            CompressionError: If archive cannot be extracted
        """
        archive_path = Compression._ensure_path(archive_path)
        output_dir = Compression._ensure_path(output_dir)

        if not archive_path.exists():
            raise CompressionError("Archive not found")

        # Auto-detect format if not provided
        detected = format
        if detected is None:
            suffix = archive_path.suffix.lower()
            if suffix == '.zip':
                detected = 'zip'
            elif archive_path.name.endswith('.tar.gz'):
                detected = 'tar.gz'
            elif archive_path.name.endswith('.tar.bz2'):
                detected = 'tar.bz2'
            elif archive_path.name.endswith('.tar.xz'):
                detected = 'tar.xz'
            elif suffix == '.tar':
                detected = 'tar'
            else:
                raise CompressionError(f"Cannot auto-detect format for: {archive_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        extracted_files: List[Path] = []

        try:
            if detected == 'zip':
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    if PASSWORD_REMOVED:
                        zf.setPASSWORD_REMOVED(PASSWORD_REMOVED)
                    # Validate all paths before extracting
                    for name in zf.namelist():
                        Compression._validate_extraction_path(output_dir, name)
                    zf.extractall(output_dir)
                    extracted_files = [output_dir / name for name in zf.namelist()]

            elif detected in Compression.TAR_MODE_MAP:
                with tarfile.open(archive_path, 'r:*') as tf:
                    # Validate all paths before extracting
                    members = [m for m in tf.getmembers() if m.name not in ('.', './', '..', '../')]
                    for member in members:
                        Compression._validate_extraction_path(output_dir, member.name)
                    tf.extractall(output_dir, members=members)
                    extracted_files = [output_dir / member.name for member in members]
            else:
                raise CompressionError(f"Unsupported format: {detected}")

            return extracted_files

        except Exception as e:
            if isinstance(e, CompressionError):
                raise
            raise CompressionError(f"Archive extraction failed: {e}") from e

    @staticmethod
    def get_compression_ratio(original: int, compressed: int) -> float:
        """Calculate compression ratio.

        Args:
            original: Original (uncompressed) size in bytes
            compressed: Compressed size in bytes

        Returns:
            Compression ratio (original / compressed), or 0 if compressed is 0
        """
        return original / compressed if compressed else 0.0

    @staticmethod
    def estimate_compressed_size(
        size: int,
        format: str = 'gzip',
        data_type: str = 'text'
    ) -> int:
        """Estimate compressed size based on historical ratios.

        Args:
            size: Original size in bytes
            format: Compression format
            data_type: Type of data ('text', 'binary', 'image', or 'video')

        Returns:
            Estimated compressed size in bytes
        """
        format_key = format.replace('tar.', '')
        ratios = Compression.COMPRESSION_RATIOS.get(format_key)
        if ratios:
            ratio = ratios.get(data_type, 0.5)
        else:
            ratio = 0.5

        return int(size * ratio)
