# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for file repository schema compatibility.

This module tests that the FileRepository works correctly with both
the full 14-column schema and the fallback 7-column schema, ensuring
no IndexError exceptions occur due to row index mismatches.

Regression tests for P1 bug: row index mismatch between files.py
(assumes 14-column schema) and connection.py fallback (7-column schema).
"""

import tempfile

import pytest

from nodupe.tools.databases.connection import DatabaseConnection
from nodupe.tools.databases.files import FileRepository, _row_to_dict
from nodupe.tools.databases.schema import DatabaseSchema


def _init_full_schema(db: DatabaseConnection) -> None:
    """Helper to initialize the full 14-column schema."""
    schema = DatabaseSchema(db.get_connection())
    schema.create_schema()


def _init_fallback_schema(db: DatabaseConnection) -> None:
    """Helper to initialize the fallback 7-column schema.
    
    This mimics the fallback schema in connection.py initialize_database().
    """
    conn = db.get_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL UNIQUE,
            size INTEGER NOT NULL,
            modified_time INTEGER NOT NULL,
            hash TEXT,
            is_duplicate BOOLEAN DEFAULT FALSE,
            duplicate_of INTEGER,
            FOREIGN KEY (duplicate_of) REFERENCES files(id)
        )
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_files_path ON files(path)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_files_hash ON files(hash)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_files_size ON files(size)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_files_duplicate ON files(is_duplicate)')
    conn.commit()


class TestRowToDictHelper:
    """Tests for the _row_to_dict helper function."""

    def test_row_to_dict_with_full_schema(self):
        """Test _row_to_dict works with full schema columns."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_full_schema(db)
            
            # Insert a test row
            db.execute(
                '''INSERT INTO files 
                (path, size, modified_time, created_time, accessed_time, 
                 file_type, mime_type, hash, is_duplicate, duplicate_of, 
                 status, scanned_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                ("test.txt", 100, 12345, 12345, 12345, "txt", "text/plain",
                 "abc123", False, None, "active", 12345, 12345)
            )
            
            cursor = db.execute("SELECT * FROM files WHERE path = ?", ("test.txt",))
            row = cursor.fetchone()
            
            result = _row_to_dict(cursor, row)
            
            assert result['path'] == "test.txt"
            assert result['size'] == 100
            assert result['hash'] == "abc123"
            assert not result['is_duplicate']
            
            db.close()

    def test_row_to_dict_with_fallback_schema(self):
        """Test _row_to_dict works with fallback schema columns."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_fallback_schema(db)
            
            # Insert a test row
            db.execute(
                '''INSERT INTO files 
                (path, size, modified_time, hash, is_duplicate, duplicate_of)
                VALUES (?, ?, ?, ?, ?, ?)''',
                ("test.txt", 100, 12345, "abc123", False, None)
            )
            
            cursor = db.execute("SELECT * FROM files WHERE path = ?", ("test.txt",))
            row = cursor.fetchone()
            
            result = _row_to_dict(cursor, row)
            
            assert result['path'] == "test.txt"
            assert result['size'] == 100
            assert result['hash'] == "abc123"
            assert not result['is_duplicate']
            
            db.close()

    def test_row_to_dict_with_none_row(self):
        """Test _row_to_dict handles None row gracefully."""
        mock_cursor = type('MockCursor', (), {'description': [('id',), ('path',)]})()
        result = _row_to_dict(mock_cursor, None)
        assert result == {}


class TestFileRepositoryWithFullSchema:
    """Test FileRepository with full 14-column schema."""

    def test_get_file_with_full_schema(self):
        """Test get_file works with full schema - no IndexError."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_full_schema(db)
            repo = FileRepository(db)
            
            # Add a file
            file_id = repo.add_file("test.txt", 100, 12345, "abc123")
            assert file_id is not None
            
            # Get file should work without IndexError
            file_data = repo.get_file(file_id)
            assert file_data is not None
            assert file_data['path'] == "test.txt"
            assert file_data['size'] == 100
            assert file_data['hash'] == "abc123"
            assert file_data['is_duplicate'] is False
            
            db.close()

    def test_get_file_by_path_with_full_schema(self):
        """Test get_file_by_path works with full schema - no IndexError."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_full_schema(db)
            repo = FileRepository(db)
            
            file_id = repo.add_file("test.txt", 100, 12345, "abc123")
            assert file_id is not None
            
            file_data = repo.get_file_by_path("test.txt")
            assert file_data is not None
            assert file_data['id'] == file_id
            
            db.close()

    def test_find_duplicates_by_hash_with_full_schema(self):
        """Test find_duplicates_by_hash works with full schema."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_full_schema(db)
            repo = FileRepository(db)
            
            repo.add_file("file1.txt", 100, 12345, "samehash")
            repo.add_file("file2.txt", 100, 12346, "samehash")
            
            duplicates = repo.find_duplicates_by_hash("samehash")
            assert len(duplicates) == 2
            assert all(f['hash'] == "samehash" for f in duplicates)
            
            db.close()

    def test_find_duplicates_by_size_with_full_schema(self):
        """Test find_duplicates_by_size works with full schema."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_full_schema(db)
            repo = FileRepository(db)
            
            repo.add_file("file1.txt", 100, 12345, "hash1")
            repo.add_file("file2.txt", 100, 12346, "hash2")
            
            same_size = repo.find_duplicates_by_size(100)
            assert len(same_size) == 2
            
            db.close()

    def test_get_all_files_with_full_schema(self):
        """Test get_all_files works with full schema."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_full_schema(db)
            repo = FileRepository(db)
            
            repo.add_file("file1.txt", 100, 12345, "hash1")
            repo.add_file("file2.txt", 200, 12346, "hash2")
            
            all_files = repo.get_all_files()
            assert len(all_files) == 2
            assert all('path' in f for f in all_files)
            assert all('hash' in f for f in all_files)
            
            db.close()

    def test_get_duplicate_files_with_full_schema(self):
        """Test get_duplicate_files works with full schema."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_full_schema(db)
            repo = FileRepository(db)
            
            original_id = repo.add_file("original.txt", 100, 12345, "hash1")
            dup_id = repo.add_file("dup.txt", 100, 12346, "hash1")
            repo.mark_as_duplicate(dup_id, original_id)
            
            duplicates = repo.get_duplicate_files()
            assert len(duplicates) == 1
            assert duplicates[0]['is_duplicate'] is True
            
            db.close()

    def test_get_original_files_with_full_schema(self):
        """Test get_original_files works with full schema."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_full_schema(db)
            repo = FileRepository(db)
            
            original_id = repo.add_file("original.txt", 100, 12345, "hash1")
            dup_id = repo.add_file("dup.txt", 100, 12346, "hash1")
            repo.mark_as_duplicate(dup_id, original_id)
            
            originals = repo.get_original_files()
            assert len(originals) == 1
            assert originals[0]['id'] == original_id
            
            db.close()


class TestFileRepositoryWithFallbackSchema:
    """Test FileRepository with fallback 7-column schema.
    
    These tests verify the fix for the P1 bug where row index access
    caused IndexError with the fallback schema.
    """

    def test_get_file_with_fallback_schema_no_index_error(self):
        """Test get_file works with fallback schema - regression test for IndexError."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_fallback_schema(db)
            repo = FileRepository(db)
            
            # Add a file using direct SQL (fallback schema has fewer columns)
            db.execute(
                '''INSERT INTO files (path, size, modified_time, hash)
                VALUES (?, ?, ?, ?)''',
                ("test.txt", 100, 12345, "abc123")
            )
            
            # Get the file ID
            cursor = db.execute("SELECT id FROM files WHERE path = ?", ("test.txt",))
            file_id = cursor.fetchone()[0]
            
            # This should NOT raise IndexError anymore
            file_data = repo.get_file(file_id)
            assert file_data is not None
            assert file_data['path'] == "test.txt"
            assert file_data['size'] == 100
            assert file_data['hash'] == "abc123"
            assert file_data['is_duplicate'] is False
            
            db.close()

    def test_get_file_by_path_with_fallback_schema_no_index_error(self):
        """Test get_file_by_path works with fallback schema - no IndexError."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_fallback_schema(db)
            repo = FileRepository(db)
            
            db.execute(
                '''INSERT INTO files (path, size, modified_time, hash)
                VALUES (?, ?, ?, ?)''',
                ("test.txt", 100, 12345, "abc123")
            )
            
            # This should NOT raise IndexError
            file_data = repo.get_file_by_path("test.txt")
            assert file_data is not None
            assert file_data['path'] == "test.txt"
            
            db.close()

    def test_find_duplicates_by_hash_with_fallback_schema(self):
        """Test find_duplicates_by_hash works with fallback schema."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_fallback_schema(db)
            repo = FileRepository(db)
            
            db.execute(
                '''INSERT INTO files (path, size, modified_time, hash)
                VALUES (?, ?, ?, ?)''',
                ("file1.txt", 100, 12345, "samehash")
            )
            db.execute(
                '''INSERT INTO files (path, size, modified_time, hash)
                VALUES (?, ?, ?, ?)''',
                ("file2.txt", 100, 12346, "samehash")
            )
            
            # Should not raise IndexError
            duplicates = repo.find_duplicates_by_hash("samehash")
            assert len(duplicates) == 2
            assert all(f['hash'] == "samehash" for f in duplicates)
            
            db.close()

    def test_find_duplicates_by_size_with_fallback_schema(self):
        """Test find_duplicates_by_size works with fallback schema."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_fallback_schema(db)
            repo = FileRepository(db)
            
            db.execute(
                '''INSERT INTO files (path, size, modified_time, hash)
                VALUES (?, ?, ?, ?)''',
                ("file1.txt", 100, 12345, "hash1")
            )
            db.execute(
                '''INSERT INTO files (path, size, modified_time, hash)
                VALUES (?, ?, ?, ?)''',
                ("file2.txt", 100, 12346, "hash2")
            )
            
            # Should not raise IndexError
            same_size = repo.find_duplicates_by_size(100)
            assert len(same_size) == 2
            
            db.close()

    def test_get_all_files_with_fallback_schema(self):
        """Test get_all_files works with fallback schema."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_fallback_schema(db)
            repo = FileRepository(db)
            
            db.execute(
                '''INSERT INTO files (path, size, modified_time, hash)
                VALUES (?, ?, ?, ?)''',
                ("file1.txt", 100, 12345, "hash1")
            )
            db.execute(
                '''INSERT INTO files (path, size, modified_time, hash)
                VALUES (?, ?, ?, ?)''',
                ("file2.txt", 200, 12346, "hash2")
            )
            
            # Should not raise IndexError
            all_files = repo.get_all_files()
            assert len(all_files) == 2
            assert all('path' in f for f in all_files)
            
            db.close()

    def test_get_duplicate_files_with_fallback_schema(self):
        """Test get_duplicate_files works with fallback schema."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_fallback_schema(db)
            repo = FileRepository(db)
            
            db.execute(
                '''INSERT INTO files (path, size, modified_time, hash, is_duplicate, duplicate_of)
                VALUES (?, ?, ?, ?, ?, ?)''',
                ("original.txt", 100, 12345, "hash1", False, None)
            )
            db.execute(
                '''INSERT INTO files (path, size, modified_time, hash, is_duplicate, duplicate_of)
                VALUES (?, ?, ?, ?, ?, ?)''',
                ("dup.txt", 100, 12346, "hash1", True, 1)
            )
            
            # Should not raise IndexError
            duplicates = repo.get_duplicate_files()
            assert len(duplicates) == 1
            assert duplicates[0]['is_duplicate'] is True
            
            db.close()

    def test_get_original_files_with_fallback_schema(self):
        """Test get_original_files works with fallback schema."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_fallback_schema(db)
            repo = FileRepository(db)
            
            db.execute(
                '''INSERT INTO files (path, size, modified_time, hash, is_duplicate, duplicate_of)
                VALUES (?, ?, ?, ?, ?, ?)''',
                ("original.txt", 100, 12345, "hash1", False, None)
            )
            db.execute(
                '''INSERT INTO files (path, size, modified_time, hash, is_duplicate, duplicate_of)
                VALUES (?, ?, ?, ?, ?, ?)''',
                ("dup.txt", 100, 12346, "hash1", True, 1)
            )
            
            # Should not raise IndexError
            originals = repo.get_original_files()
            assert len(originals) == 1
            assert originals[0]['path'] == "original.txt"
            
            db.close()

    def test_update_file_with_fallback_schema(self):
        """Test update_file works with fallback schema."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_fallback_schema(db)
            repo = FileRepository(db)
            
            db.execute(
                '''INSERT INTO files (path, size, modified_time, hash)
                VALUES (?, ?, ?, ?)''',
                ("test.txt", 100, 12345, "abc123")
            )
            
            cursor = db.execute("SELECT id FROM files WHERE path = ?", ("test.txt",))
            file_id = cursor.fetchone()[0]
            
            # Update should work
            success = repo.update_file(file_id, size=200, hash="def456")
            assert success is True
            
            # Verify update
            file_data = repo.get_file(file_id)
            assert file_data['size'] == 200
            assert file_data['hash'] == "def456"
            
            db.close()

    def test_mark_as_duplicate_with_fallback_schema(self):
        """Test mark_as_duplicate works with fallback schema."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_fallback_schema(db)
            repo = FileRepository(db)
            
            db.execute(
                '''INSERT INTO files (path, size, modified_time, hash)
                VALUES (?, ?, ?, ?)''',
                ("original.txt", 100, 12345, "hash1")
            )
            db.execute(
                '''INSERT INTO files (path, size, modified_time, hash)
                VALUES (?, ?, ?, ?)''',
                ("dup.txt", 100, 12346, "hash1")
            )
            
            # Mark as duplicate should work
            success = repo.mark_as_duplicate(2, 1)
            assert success is True
            
            # Verify
            dup_data = repo.get_file(2)
            assert dup_data['is_duplicate'] is True
            assert dup_data['duplicate_of'] == 1
            
            db.close()


class TestSchemaCompatibilityEdgeCases:
    """Test edge cases for schema compatibility."""

    def test_missing_columns_return_none(self):
        """Test that missing columns in fallback schema return None."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_fallback_schema(db)
            repo = FileRepository(db)
            
            # Fallback schema doesn't have created_time, accessed_time, etc.
            db.execute(
                '''INSERT INTO files (path, size, modified_time, hash)
                VALUES (?, ?, ?, ?)''',
                ("test.txt", 100, 12345, "abc123")
            )
            
            cursor = db.execute("SELECT id FROM files WHERE path = ?", ("test.txt",))
            file_id = cursor.fetchone()[0]
            
            file_data = repo.get_file(file_id)
            
            # Core fields should be present
            assert file_data['id'] is not None
            assert file_data['path'] == "test.txt"
            assert file_data['size'] == 100
            
            db.close()

    def test_is_duplicate_defaults_to_false_when_null(self):
        """Test that is_duplicate defaults to False when NULL."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_fallback_schema(db)
            repo = FileRepository(db)
            
            db.execute(
                '''INSERT INTO files (path, size, modified_time, hash, is_duplicate)
                VALUES (?, ?, ?, ?, ?)''',
                ("test.txt", 100, 12345, "abc123", None)
            )
            
            cursor = db.execute("SELECT id FROM files WHERE path = ?", ("test.txt",))
            file_id = cursor.fetchone()[0]
            
            file_data = repo.get_file(file_id)
            # Should default to False, not raise error
            assert file_data['is_duplicate'] is False
            
            db.close()

    def test_empty_result_returns_none(self):
        """Test that empty query results return None."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            _init_full_schema(db)
            repo = FileRepository(db)
            
            # Query non-existent file
            file_data = repo.get_file(999)
            assert file_data is None
            
            file_data = repo.get_file_by_path("nonexistent.txt")
            assert file_data is None
            
            db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
