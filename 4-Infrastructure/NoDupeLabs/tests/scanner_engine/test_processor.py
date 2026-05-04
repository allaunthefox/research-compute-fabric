"""Tests for file processor module."""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest


class TestFileProcessor:
    """Test FileProcessor class."""

    def test_processor_initialization(self):
        """Test processor initialization."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        processor = FileProcessor()
        
        assert processor._hash_algorithm == 'sha256'
        assert processor._hash_buffer_size == 65536

    def test_processor_with_custom_walker(self):
        """Test processor with custom file walker."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        from nodupe.tools.scanner_engine.walker import FileWalker
        
        mock_walker = MagicMock(spec=FileWalker)
        processor = FileProcessor(file_walker=mock_walker)
        
        assert processor.file_walker is mock_walker

    def test_processor_with_custom_hasher(self):
        """Test processor with custom hasher."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        mock_hasher = MagicMock()
        mock_hasher.hash_file.return_value = "abc123"
        mock_hasher.get_algorithm.return_value = "sha256"
        mock_hasher.set_algorithm = MagicMock()
        
        processor = FileProcessor(hasher=mock_hasher)
        
        assert processor._hasher is mock_hasher

    def test_processor_default_hasher(self):
        """Test processor uses default hasher when none provided."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        with patch('nodupe.tools.scanner_engine.processor.global_container') as mock_container:
            mock_container.get_service.return_value = None
            
            processor = FileProcessor()
            
            # Should create a default hasher
            assert processor._hasher is not None

    def test_process_single_file(self, temp_dir):
        """Test processing a single file."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        processor = FileProcessor()
        
        file_info = {
            'path': str(test_file),
            'name': 'test.txt',
            'extension': '.txt',
            'size': 12
        }
        
        result = processor._process_single_file(file_info)
        
        assert result is not None
        assert 'hash' in result
        assert 'hash_algorithm' in result
        assert result['is_duplicate'] is False
        assert result['duplicate_of'] is None

    def test_calculate_file_hash(self, temp_dir):
        """Test file hash calculation."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        processor = FileProcessor()
        
        hash_value = processor._calculate_file_hash(str(test_file))
        
        assert hash_value is not None
        assert len(hash_value) > 0

    def test_calculate_file_hash_error(self):
        """Test file hash calculation with error."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        processor = FileProcessor()
        
        with pytest.raises(Exception):
            processor._calculate_file_hash("/nonexistent/file.txt")

    def test_detect_duplicates_empty_list(self):
        """Test detect duplicates with empty list."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        processor = FileProcessor()
        
        result = processor.detect_duplicates([])
        
        assert result == []

    def test_detect_duplicates_no_duplicates(self):
        """Test detect duplicates with unique files."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        processor = FileProcessor()
        
        files = [
            {'path': '/file1.txt', 'hash': 'hash1', 'size': 100},
            {'path': '/file2.txt', 'hash': 'hash2', 'size': 200},
        ]
        
        result = processor.detect_duplicates(files)
        
        assert all(not f.get('is_duplicate', False) for f in result)

    def test_detect_duplicates_with_duplicates(self, temp_dir):
        """Test detect duplicates with duplicate files."""
        from nodupe.tools.scanner_engine.processor import FileProcessor

        # Create duplicate files
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("same content")
        file2.write_text("same content")
        
        processor = FileProcessor()
        
        files = [
            {'path': str(file1), 'hash': 'same_hash', 'size': 12},
            {'path': str(file2), 'hash': 'same_hash', 'size': 12},
        ]
        
        result = processor.detect_duplicates(files)
        
        # One should be marked as duplicate
        duplicates = [f for f in result if f.get('is_duplicate')]
        originals = [f for f in result if not f.get('is_duplicate')]
        
        assert len(duplicates) == 1
        assert len(originals) == 1

    def test_get_basic_file_info(self, temp_dir):
        """Test getting basic file info."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        processor = FileProcessor()
        
        info = processor._get_basic_file_info(str(test_file))
        
        assert 'path' in info
        assert 'name' in info
        assert 'extension' in info
        assert 'size' in info
        assert 'modified_time' in info
        assert 'created_time' in info
        assert info['is_file'] is True
        assert info['is_directory'] is False

    def test_get_basic_file_info_error(self):
        """Test getting basic file info for nonexistent file."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        processor = FileProcessor()
        
        with pytest.raises(Exception):
            processor._get_basic_file_info("/nonexistent/file.txt")

    def test_set_hash_algorithm(self):
        """Test setting hash algorithm."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        processor = FileProcessor()
        
        processor.set_hash_algorithm('md5')
        
        assert processor._hash_algorithm == 'md5'

    def test_set_hash_algorithm_invalid(self):
        """Test setting invalid hash algorithm."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        processor = FileProcessor()
        
        with pytest.raises(ValueError):
            processor.set_hash_algorithm('invalid_algorithm')

    def test_get_hash_algorithm(self):
        """Test getting hash algorithm."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        processor = FileProcessor()
        
        assert processor.get_hash_algorithm() == 'sha256'
        
        processor.set_hash_algorithm('md5')
        
        assert processor.get_hash_algorithm() == 'md5'

    def test_set_hash_buffer_size(self):
        """Test setting hash buffer size."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        processor = FileProcessor()
        
        processor.set_hash_buffer_size(32768)
        
        assert processor._hash_buffer_size == 32768

    def test_set_hash_buffer_size_invalid(self):
        """Test setting invalid buffer size."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        processor = FileProcessor()
        
        with pytest.raises(ValueError):
            processor.set_hash_buffer_size(0)
        
        with pytest.raises(ValueError):
            processor.set_hash_buffer_size(-1)

    def test_get_hash_buffer_size(self):
        """Test getting hash buffer size."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        processor = FileProcessor()
        
        assert processor.get_hash_buffer_size() == 65536
        
        processor.set_hash_buffer_size(32768)
        
        assert processor.get_hash_buffer_size() == 32768

    def test_process_files_empty_directory(self, temp_dir):
        """Test processing files in empty directory."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        
        processor = FileProcessor()
        
        result = processor.process_files(str(empty_dir))
        
        assert result == []

    def test_batch_process_files(self, temp_dir):
        """Test batch processing files."""
        from nodupe.tools.scanner_engine.processor import FileProcessor

        # Create test files
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")
        
        processor = FileProcessor()
        
        result = processor.batch_process_files([str(file1), str(file2)])
        
        assert len(result) == 2
        assert all('hash' in f for f in result)

    def test_batch_process_files_nonexistent(self):
        """Test batch processing with nonexistent files."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        processor = FileProcessor()
        
        result = processor.batch_process_files(['/nonexistent/file1.txt', '/nonexistent/file2.txt'])
        
        assert result == []

    def test_default_hasher_hash_string(self):
        """Test default hasher hash_string method."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        processor = FileProcessor()
        
        hash_value = processor._hasher.hash_string("test data")
        
        assert hash_value is not None
        assert len(hash_value) > 0

    def test_default_hasher_hash_bytes(self):
        """Test default hasher hash_bytes method."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        processor = FileProcessor()
        
        hash_value = processor._hasher.hash_bytes(b"test data")
        
        assert hash_value is not None
        assert len(hash_value) > 0

    def test_default_hasher_verify_hash(self, temp_dir):
        """Test default hasher verify_hash method."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        processor = FileProcessor()
        
        # Calculate hash
        expected_hash = processor._hasher.hash_file(str(test_file))
        
        # Verify correct hash
        assert processor._hasher.verify_hash(str(test_file), expected_hash) is True
        
        # Verify incorrect hash
        assert processor._hasher.verify_hash(str(test_file), "wrong_hash") is False

    def test_default_hasher_set_algorithm(self):
        """Test default hasher set_algorithm method."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        processor = FileProcessor()
        
        processor._hasher.set_algorithm('md5')
        
        assert processor._hasher.get_algorithm() == 'md5'

    def test_default_hasher_get_algorithm(self):
        """Test default hasher get_algorithm method."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        processor = FileProcessor()
        
        assert processor._hasher.get_algorithm() == 'sha256'

    def test_default_hasher_get_available_algorithms(self):
        """Test default hasher get_available_algorithms method."""
        from nodupe.tools.scanner_engine.processor import FileProcessor
        
        processor = FileProcessor()
        
        algorithms = processor._hasher.get_available_algorithms()

        assert 'sha256' in algorithms
        assert 'md5' in algorithms

    def test_detect_duplicates(self, temp_dir):
        """Test detect_duplicates method."""
        from nodupe.tools.scanner_engine.processor import FileProcessor

        processor = FileProcessor()

        # Create files with same content (duplicates)
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("same content")
        file2.write_text("same content")

        files = [
            {'path': str(file1), 'hash': 'abc123', 'size': 12},
            {'path': str(file2), 'hash': 'abc123', 'size': 12},
            {'path': str(temp_dir / "unique.txt"), 'hash': 'xyz789', 'size': 14},
        ]

        duplicates = processor.detect_duplicates(files)

        assert len(duplicates) > 0

    def test_batch_process_files_with_error(self, temp_dir):
        """Test batch_process_files handles errors gracefully."""
        from nodupe.tools.scanner_engine.processor import FileProcessor

        processor = FileProcessor()

        # Create a valid file
        valid_file = temp_dir / "valid.txt"
        valid_file.write_text("valid content")

        # Process with a non-existent file (should handle error)
        file_paths = [str(valid_file), str(temp_dir / "nonexistent.txt")]

        result = processor.batch_process_files(file_paths)

        # Should process valid file, skip invalid
        assert len(result) >= 1

    def test_process_files_with_on_progress_callback(self, temp_dir):
        """Test process_files calls on_progress callback."""
        from nodupe.tools.scanner_engine.processor import FileProcessor

        processor = FileProcessor()

        # Create multiple files
        for i in range(15):
            (temp_dir / f"file{i}.txt").write_text(f"content {i}")

        progress_calls = []

        def on_progress(progress):
            progress_calls.append(progress)

        result = processor.process_files(str(temp_dir), on_progress=on_progress)

        # Should have called progress callback
        assert len(progress_calls) > 0
        assert 'files_processed' in progress_calls[0]
        assert 'total_files' in progress_calls[0]


class TestCreateFileProcessor:
    """Test create_file_processor factory function."""

    def test_create_file_processor_default(self):
        """Test creating file processor with defaults."""
        from nodupe.tools.scanner_engine.processor import create_file_processor
        
        processor = create_file_processor()
        
        assert processor is not None
        # Default hasher should be an instance, not a class
        assert not isinstance(processor._hasher, type)

    def test_create_file_processor_with_walker(self):
        """Test creating file processor with custom walker."""
        from nodupe.tools.scanner_engine.processor import create_file_processor
        from nodupe.tools.scanner_engine.walker import FileWalker
        
        mock_walker = MagicMock(spec=FileWalker)
        processor = create_file_processor(mock_walker)
        
        assert processor.file_walker is mock_walker
