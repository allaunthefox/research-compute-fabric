# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""File repository for database operations.

This module provides file repository functionality for the database layer,
handling file metadata storage and retrieval.

Key Features:
    - File metadata CRUD operations
    - Duplicate detection
    - File indexing
    - Batch operations
    - Error handling

Dependencies:
    - sqlite3 (standard library only)
    - typing (standard library only)
"""

import re
from typing import Optional, List, Dict, Any, Tuple
import time
from .connection import DatabaseConnection


def _validate_identifier(identifier: str) -> str:
    """Validate SQL identifier to prevent SQL injection.

    Args:
        identifier: SQL identifier (column name)

    Returns:
        The validated identifier

    Raises:
        ValueError: If identifier contains invalid characters
    """
    if not identifier or not isinstance(identifier, str):
        raise ValueError("Identifier cannot be empty")

    # Only allow alphanumeric and underscore, must start with letter
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        raise ValueError(f"Invalid identifier: {identifier}")

    return identifier


def _row_to_dict(cursor: Any, row: Tuple) -> Dict[str, Any]:
    """Convert a database row to a dictionary using cursor description.

    This function is schema-agnostic and works with any number of columns.

    Args:
        cursor: Database cursor with description attribute
        row: Database row tuple

    Returns:
        Dictionary mapping column names to values
    """
    if row is None:
        return {}

    # Use cursor.description to get column names
    columns = [desc[0] for desc in cursor.description]
    return dict(zip(columns, row))


class FileRepository:
    """File repository for database operations.

    Responsibilities:
    - Manage file metadata in database
    - Handle file CRUD operations
    - Detect and manage duplicates
    - Provide file indexing
    - Support batch operations
    """

    # Column name mappings for schema-agnostic access
    # Maps column names to their typical positions in full schema
    COL_ID = 'id'
    COL_PATH = 'path'
    COL_SIZE = 'size'
    COL_MODIFIED_TIME = 'modified_time'
    COL_HASH = 'hash'
    COL_IS_DUPLICATE = 'is_duplicate'
    COL_DUPLICATE_OF = 'duplicate_of'

    def __init__(self, db_connection: DatabaseConnection):
        """Initialize file repository.

        Args:
            db_connection: Database connection instance
        """
        self.db = db_connection

    def _row_to_file_dict(self, cursor: Any, row: Tuple) -> Optional[Dict[str, Any]]:
        """Convert a database row to a file dictionary with standard fields.

        This method is schema-agnostic and only includes fields that exist
        in the schema, using column names instead of indices.

        Args:
            cursor: Database cursor with description attribute
            row: Database row tuple

        Returns:
            File dictionary with standard fields, or None if row is None
        """
        if row is None:
            return None

        # Get column names from cursor description
        columns = [desc[0] for desc in cursor.description]
        row_dict = dict(zip(columns, row))

        # Build result using column names, with defaults for missing columns
        result = {
            'id': row_dict.get('id'),
            'path': row_dict.get('path'),
            'size': row_dict.get('size'),
            'modified_time': row_dict.get('modified_time'),
        }

        # Add optional fields if they exist in the schema
        if 'hash' in row_dict:
            result['hash'] = row_dict.get('hash')
        if 'is_duplicate' in row_dict:
            result['is_duplicate'] = bool(row_dict.get('is_duplicate'))
        if 'duplicate_of' in row_dict:
            result['duplicate_of'] = row_dict.get('duplicate_of')

        return result

    def add_file(self, file_path: str, size: int, modified_time: int,
                 hash_value: Optional[str] = None) -> Optional[int]:
        """Add file to database.

        Args:
            file_path: Path to file
            size: File size in bytes
            modified_time: File modification time
            hash_value: Optional file hash

        Returns:
            File ID
        """
        try:
            current_time = int(time.monotonic())
            cursor = self.db.execute(
                '''
                INSERT INTO files (path, size, modified_time, hash, created_time, scanned_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (file_path, size, modified_time, hash_value, modified_time, current_time, current_time)
            )
            return cursor.lastrowid
        except Exception as e:
            print(f"[ERROR] Failed to add file: {e}")
            raise

    def get_file(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Get file by ID.

        Args:
            file_id: File ID

        Returns:
            File data or None if not found
        """
        try:
            cursor = self.db.execute(
                'SELECT * FROM files WHERE id = ?',
                (file_id,)
            )
            row = cursor.fetchone()
            return self._row_to_file_dict(cursor, row)
        except Exception as e:
            print(f"[ERROR] Failed to get file: {e}")
            raise

    def get_file_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file by path.

        Args:
            file_path: File path

        Returns:
            File data or None if not found
        """
        try:
            cursor = self.db.execute(
                'SELECT * FROM files WHERE path = ?',
                (file_path,)
            )
            row = cursor.fetchone()
            return self._row_to_file_dict(cursor, row)
        except Exception as e:
            print(f"[ERROR] Failed to get file by path: {e}")
            raise

    def update_file(self, file_id: int, **kwargs: Any) -> bool:
        """Update file data.

        Args:
            file_id: File ID
            **kwargs: File attributes to update

        Returns:
            True if updated, False if not found
        """
        if not kwargs:
            return False

        valid_fields = {'size', 'modified_time', 'hash', 'is_duplicate', 'duplicate_of'}
        update_fields = {k: v for k, v in kwargs.items() if k in valid_fields}

        if not update_fields:
            return False

        try:
            # Validate column names to prevent SQL injection
            for field in update_fields.keys():
                _validate_identifier(field)

            set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
            values = list(update_fields.values())
            values.append(file_id)

            query = f"UPDATE files SET {set_clause} WHERE id = ?"
            cursor = self.db.execute(query, tuple(values))

            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ERROR] Failed to update file: {e}")
            raise

    def mark_as_duplicate(self, file_id: int, duplicate_of: int) -> bool:
        """Mark file as duplicate.

        Args:
            file_id: File ID to mark as duplicate
            duplicate_of: ID of original file

        Returns:
            True if updated, False if not found
        """
        try:
            cursor = self.db.execute(
                'UPDATE files SET is_duplicate = TRUE, duplicate_of = ? WHERE id = ?',
                (duplicate_of, file_id)
            )
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ERROR] Failed to mark file as duplicate: {e}")
            raise

    def find_duplicates_by_hash(self, hash_value: str) -> List[Dict[str, Any]]:
        """Find files with same hash.

        Args:
            hash_value: Hash value to search for

        Returns:
            List of files with matching hash
        """
        try:
            cursor = self.db.execute(
                'SELECT * FROM files WHERE hash = ? ORDER BY path',
                (hash_value,)
            )
            return [self._row_to_file_dict(cursor, row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[ERROR] Failed to find duplicates by hash: {e}")
            raise

    def find_duplicates_by_size(self, size: int) -> List[Dict[str, Any]]:
        """Find files with same size.

        Args:
            size: File size to search for

        Returns:
            List of files with matching size
        """
        try:
            cursor = self.db.execute(
                'SELECT * FROM files WHERE size = ? ORDER BY path',
                (size,)
            )
            return [self._row_to_file_dict(cursor, row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[ERROR] Failed to find duplicates by size: {e}")
            raise

    def get_all_files(self) -> List[Dict[str, Any]]:
        """Get all files from database.

        Returns:
            List of all files
        """
        try:
            cursor = self.db.execute('SELECT * FROM files ORDER BY path')
            return [self._row_to_file_dict(cursor, row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[ERROR] Failed to get all files: {e}")
            raise

    def delete_file(self, file_id: int) -> bool:
        """Delete file from database.

        Args:
            file_id: File ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            cursor = self.db.execute(
                'DELETE FROM files WHERE id = ?',
                (file_id,)
            )
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ERROR] Failed to delete file: {e}")
            raise

    def get_duplicate_files(self) -> List[Dict[str, Any]]:
        """Get all duplicate files.

        Returns:
            List of duplicate files
        """
        try:
            cursor = self.db.execute(
                'SELECT * FROM files WHERE is_duplicate = TRUE ORDER BY path'
            )
            return [self._row_to_file_dict(cursor, row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[ERROR] Failed to get duplicate files: {e}")
            raise

    def get_original_files(self) -> List[Dict[str, Any]]:
        """Get all original files (not duplicates).

        Returns:
            List of original files
        """
        try:
            cursor = self.db.execute(
                'SELECT * FROM files WHERE is_duplicate = FALSE ORDER BY path'
            )
            return [self._row_to_file_dict(cursor, row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[ERROR] Failed to get original files: {e}")
            raise

    def count_files(self) -> int:
        """Count total files in database.

        Returns:
            Total file count
        """
        try:
            cursor = self.db.execute('SELECT COUNT(*) FROM files')
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"[ERROR] Failed to count files: {e}")
            raise

    def count_duplicates(self) -> int:
        """Count duplicate files in database.

        Returns:
            Duplicate file count
        """
        try:
            cursor = self.db.execute('SELECT COUNT(*) FROM files WHERE is_duplicate = TRUE')
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"[ERROR] Failed to count duplicates: {e}")
            raise

    def batch_add_files(self, files: List[Dict[str, Any]]) -> int:
        """Add multiple files in batch.

        Args:
            files: List of file data dictionaries

        Returns:
            Number of files added
        """
        if not files:
            return 0

        try:
            current_time = int(time.monotonic())
            data = [
                (
                    file_data['path'],
                    file_data['size'],
                    file_data['modified_time'],
                    file_data.get('hash'),
                    file_data.get('created_time', file_data['modified_time']),
                    current_time,
                    current_time
                )
                for file_data in files
            ]

            self.db.executemany(
                '''INSERT INTO files
                (path, size, modified_time, hash, created_time, scanned_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                data
            )
            return len(files)
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"[ERROR] Failed to batch add files: {e}")
            raise

    def clear_all_files(self) -> None:
        """Clear all files from database."""
        try:
            self.db.execute('DELETE FROM files')
            self.db.commit()
        except Exception as e:
            print(f"[ERROR] Failed to clear all files: {e}")
            raise


def get_file_repository(db_path: str = "output/index.db") -> FileRepository:
    """Get file repository instance.

    Args:
        db_path: Path to SQLite database file

    Returns:
        FileRepository instance
    """
    db_connection = DatabaseConnection.get_instance(db_path)
    return FileRepository(db_connection)
