# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Embedding repository for database operations.

This module provides embedding repository functionality for the database layer,
handling file embedding storage and retrieval.

Key Features:
    - Embedding CRUD operations
    - Model version management
    - Batch operations
    - Error handling

Dependencies:
    - sqlite3 (standard library only)
    - typing (standard library only)
"""

import json
from typing import Optional, List, Dict, Any
from .connection import DatabaseConnection


def _serialize_embedding(embedding: Any) -> str:
    """Serialize embedding to JSON string.
    
    Args:
        embedding: Embedding data (list, dict, or numpy array-like)
        
    Returns:
        JSON string representation
    """
    # Handle numpy arrays and other array-like objects
    if hasattr(embedding, 'tolist'):
        embedding = embedding.tolist()
    elif hasattr(embedding, '__iter__') and not isinstance(embedding, (str, bytes)):
        embedding = list(embedding)
    
    return json.dumps(embedding)


def _deserialize_embedding(data: str) -> Any:
    """Deserialize embedding from JSON string.
    
    Args:
        data: JSON string representation
        
    Returns:
        Deserialized embedding data
    """
    if isinstance(data, (bytes, bytearray)):
        try:
            data = data.decode('utf-8')
        except Exception:
            data = data.decode('latin-1')
    return json.loads(data)


class EmbeddingRepository:
    """Embedding repository for database operations.

    Responsibilities:
    - Manage file embeddings in database
    - Handle embedding CRUD operations
    - Manage model versions
    - Support batch operations
    """

    def __init__(self, db_connection: DatabaseConnection):
        """Initialize embedding repository.

        Args:
            db_connection: Database connection instance
        """
        self.db = db_connection

    def _get_embedding_dimensions(self, embedding: Any) -> int:
        """Return the number of dimensions for an embedding. Non-sequences -> 0."""
        try:
            if hasattr(embedding, 'shape'):
                return int(getattr(embedding, 'shape')[-1])
            if hasattr(embedding, '__len__') and not isinstance(embedding, (str, bytes)):
                return len(embedding)
        except Exception:
            return 0
        return 0

    def add_embedding(self, file_id: int, embedding: Any, model_version: str, created_time: int) -> Optional[int]:
        """Add embedding to database.

        Args:
            file_id: File ID
            embedding: Embedding data
            model_version: Model version
            created_time: Creation timestamp

        Returns:
            Embedding ID
        """
        try:
            # Compute embedding dimensions before serialization
            try:
                if hasattr(embedding, 'shape'):
                    # numpy-like
                    dims = int(getattr(embedding, 'shape')[-1])
                elif hasattr(embedding, '__len__') and not isinstance(embedding, (str, bytes)):
                    dims = len(embedding)
                else:
                    dims = 0
            except Exception:
                dims = 0

            # Serialize embedding to JSON string (safer than pickle)
            embedding_str = _serialize_embedding(embedding)

            cursor = self.db.execute(
                '''
                INSERT INTO embeddings (file_id, embedding, model_version, created_time, dimensions)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (file_id, embedding_str.encode('utf-8'), model_version, created_time, dims)
            )
            return cursor.lastrowid
        except Exception as e:
            print(f"[ERROR] Failed to add embedding: {e}")
            raise

    def get_embedding(self, embedding_id: int) -> Optional[Dict[str, Any]]:
        """Get embedding by ID.

        Args:
            embedding_id: Embedding ID

        Returns:
            Embedding data or None if not found
        """
        try:
            cursor = self.db.execute(
                'SELECT * FROM embeddings WHERE id = ?',
                (embedding_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'file_id': row[1],
                    'embedding': _deserialize_embedding(row[2]),
                    'model_version': row[3],
                    'created_time': row[4],
                    'dimensions': row[5] if len(row) > 5 else None
                }
            return None
        except Exception as e:
            print(f"[ERROR] Failed to get embedding: {e}")
            raise

    def get_embedding_by_file(self, file_id: int, model_version: str) -> Optional[Dict[str, Any]]:
        """Get embedding by file ID and model version.

        Args:
            file_id: File ID
            model_version: Model version

        Returns:
            Embedding data or None if not found
        """
        try:
            cursor = self.db.execute(
                'SELECT * FROM embeddings WHERE file_id = ? AND model_version = ?',
                (file_id, model_version)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'file_id': row[1],
                    'embedding': _deserialize_embedding(row[2]),
                    'model_version': row[3],
                    'created_time': row[4],
                    'dimensions': row[5] if len(row) > 5 else None
                }
            return None
        except Exception as e:
            print(f"[ERROR] Failed to get embedding by file: {e}")
            raise

    def get_embeddings_by_file(self, file_id: int) -> List[Dict[str, Any]]:
        """Get all embeddings for a file.

        Args:
            file_id: File ID

        Returns:
            List of embeddings for the file
        """
        try:
            cursor = self.db.execute(
                'SELECT * FROM embeddings WHERE file_id = ? ORDER BY model_version',
                (file_id,)
            )
            return [
                {
                    'id': row[0],
                    'file_id': row[1],
                    'embedding': _deserialize_embedding(row[2]),
                    'model_version': row[3],
                    'created_time': row[4],
                    'dimensions': row[5] if len(row) > 5 else None
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"[ERROR] Failed to get embeddings by file: {e}")
            raise

    def get_embeddings_by_model(self, model_version: str) -> List[Dict[str, Any]]:
        """Get all embeddings for a model version.

        Args:
            model_version: Model version

        Returns:
            List of embeddings for the model
        """
        try:
            cursor = self.db.execute(
                'SELECT * FROM embeddings WHERE model_version = ? ORDER BY file_id',
                (model_version,)
            )
            return [
                {
                    'id': row[0],
                    'file_id': row[1],
                    'embedding': _deserialize_embedding(row[2]),
                    'model_version': row[3],
                    'created_time': row[4],
                    'dimensions': row[5] if len(row) > 5 else None
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"[ERROR] Failed to get embeddings by model: {e}")
            raise

    def update_embedding(self, embedding_id: int, embedding: Any) -> bool:
        """Update embedding data.

        Args:
            embedding_id: Embedding ID
            embedding: New embedding data

        Returns:
            True if updated, False if not found
        """
        try:
            # Compute new dimensions and serialize
            try:
                if hasattr(embedding, 'shape'):
                    dims = int(getattr(embedding, 'shape')[-1])
                elif hasattr(embedding, '__len__') and not isinstance(embedding, (str, bytes)):
                    dims = len(embedding)
                else:
                    dims = 0
            except Exception:
                dims = 0

            embedding_str = _serialize_embedding(embedding)

            cursor = self.db.execute(
                'UPDATE embeddings SET embedding = ?, dimensions = ? WHERE id = ?',
                (embedding_str.encode('utf-8'), dims, embedding_id)
            )
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ERROR] Failed to update embedding: {e}")
            raise

    def delete_embedding(self, embedding_id: int) -> bool:
        """Delete embedding from database.

        Args:
            embedding_id: Embedding ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            cursor = self.db.execute(
                'DELETE FROM embeddings WHERE id = ?',
                (embedding_id,)
            )
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ERROR] Failed to delete embedding: {e}")
            raise

    def delete_embeddings_by_file(self, file_id: int) -> int:
        """Delete all embeddings for a file.

        Args:
            file_id: File ID

        Returns:
            Number of embeddings deleted
        """
        try:
            cursor = self.db.execute(
                'DELETE FROM embeddings WHERE file_id = ?',
                (file_id,)
            )
            return cursor.rowcount
        except Exception as e:
            print(f"[ERROR] Failed to delete embeddings by file: {e}")
            raise

    def delete_embeddings_by_model(self, model_version: str) -> int:
        """Delete all embeddings for a model version.

        Args:
            model_version: Model version

        Returns:
            Number of embeddings deleted
        """
        try:
            cursor = self.db.execute(
                'DELETE FROM embeddings WHERE model_version = ?',
                (model_version,)
            )
            return cursor.rowcount
        except Exception as e:
            print(f"[ERROR] Failed to delete embeddings by model: {e}")
            raise

    def get_all_embeddings(self) -> List[Dict[str, Any]]:
        """Get all embeddings from database.

        Returns:
            List of all embeddings
        """
        try:
            cursor = self.db.execute('SELECT * FROM embeddings ORDER BY file_id, model_version')
            return [
                {
                    'id': row[0],
                    'file_id': row[1],
                    'embedding': _deserialize_embedding(row[2]),
                    'model_version': row[3],
                    'created_time': row[4],
                    'dimensions': row[5] if len(row) > 5 else None
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"[ERROR] Failed to get all embeddings: {e}")
            raise

    def count_embeddings(self) -> int:
        """Count total embeddings in database.

        Returns:
            Total embedding count
        """
        try:
            cursor = self.db.execute('SELECT COUNT(*) FROM embeddings')
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"[ERROR] Failed to count embeddings: {e}")
            raise

    def count_embeddings_by_model(self, model_version: str) -> int:
        """Count embeddings for a model version.

        Args:
            model_version: Model version

        Returns:
            Embedding count for the model
        """
        try:
            cursor = self.db.execute(
                'SELECT COUNT(*) FROM embeddings WHERE model_version = ?',
                (model_version,)
            )
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"[ERROR] Failed to count embeddings by model: {e}")
            raise

    def batch_add_embeddings(self, embeddings: List[Dict[str, Any]]) -> int:
        """Add multiple embeddings in batch.

        Args:
            embeddings: List of embedding data dictionaries

        Returns:
            Number of embeddings added
        """
        if not embeddings:
            return 0

        try:
            data = []
            for emb_data in embeddings:
                emb = emb_data['embedding']
                try:
                    if hasattr(emb, 'shape'):
                        d = int(getattr(emb, 'shape')[-1])
                    elif hasattr(emb, '__len__') and not isinstance(emb, (str, bytes)):
                        d = len(emb)
                    else:
                        d = 0
                except Exception:
                    d = 0

                data.append((
                    emb_data['file_id'],
                    _serialize_embedding(emb).encode('utf-8'),
                    emb_data['model_version'],
                    emb_data['created_time'],
                    d
                ))

            self.db.executemany(
                '''INSERT INTO embeddings
                (file_id, embedding, model_version, created_time, dimensions)
                VALUES (?, ?, ?, ?, ?)''',
                [tuple(item) for item in data]
            )
            return len(embeddings)
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"[ERROR] Failed to batch add embeddings: {e}")
            raise

    def clear_all_embeddings(self) -> None:
        """Clear all embeddings from database."""
        try:
            self.db.execute('DELETE FROM embeddings')
            self.db.commit()
        except Exception as e:
            print(f"[ERROR] Failed to clear all embeddings: {e}")
            raise


def get_embedding_repository(db_path: str = "output/index.db") -> EmbeddingRepository:
    """Get embedding repository instance.

    Args:
        db_path: Path to SQLite database file

    Returns:
        EmbeddingRepository instance
    """
    db_connection = DatabaseConnection.get_instance(db_path)
    return EmbeddingRepository(db_connection)
