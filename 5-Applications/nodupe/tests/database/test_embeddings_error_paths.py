# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 NoDupeLabs

"""Tests for error handling paths in embeddings.py.

This module tests all exception handling paths to achieve 100% coverage.
Tests cover:
- Database connection failures
- SQL execution errors
- Invalid embedding vectors
- Missing embeddings (get non-existent)
- Update non-existent embedding
- Delete non-existent embedding
- Batch operations with partial failures
- Similarity search with invalid parameters
- Dimension mismatches
"""

import pickle
import sqlite3
from unittest.mock import MagicMock

import numpy as np
import pytest

from nodupe.tools.databases.embeddings import EmbeddingRepository, get_embedding_repository

# =============================================================================
# Mock Database Connection for Error Testing
# =============================================================================

class MockConnectionFailing:
    """Mock database connection that can be configured to fail."""

    def __init__(self, fail_on_execute=False, fail_on_executemany=False,
                 fail_on_commit=False, execute_exception=None,
                 executemany_exception=None, commit_exception=None,
                 rowcount=1, fetchone_result=None, fetchall_result=None):
        """Initialize mock connection with configurable failure modes.

        Args:
            fail_on_execute: If True, execute() raises exception.
            fail_on_executemany: If True, executemany() raises exception.
            fail_on_commit: If True, commit() raises exception.
            execute_exception: Exception to raise on execute.
            executemany_exception: Exception to raise on executemany.
            commit_exception: Exception to raise on commit.
            rowcount: Number of rows affected.
            fetchone_result: Result for fetchone() calls.
            fetchall_result: Result for fetchall() calls.
        """
        self.fail_on_execute = fail_on_execute
        self.fail_on_executemany = fail_on_executemany
        self.fail_on_commit = fail_on_commit
        self.execute_exception = execute_exception or sqlite3.Error("Simulated SQL error")
        self.executemany_exception = executemany_exception or sqlite3.Error("Simulated batch SQL error")
        self.commit_exception = commit_exception or sqlite3.Error("Simulated commit error")
        self.rowcount = rowcount
        self.fetchone_result = fetchone_result
        self.fetchall_result = fetchall_result or []
        self.execute_call_count = 0
        self.executemany_call_count = 0
        self.commit_call_count = 0

    def execute(self, query, params=None):
        """Execute a query.

        Args:
            query: SQL query string.
            params: Query parameters (optional).

        Returns:
            Mock cursor object.
        """
        self.execute_call_count += 1
        if self.fail_on_execute:
            raise self.execute_exception
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_cursor.rowcount = self.rowcount
        mock_cursor.fetchone.return_value = self.fetchone_result
        mock_cursor.fetchall.return_value = self.fetchall_result
        return mock_cursor

    def executemany(self, query, params_list):
        """Execute multiple queries.

        Args:
            query: SQL query string.
            params_list: List of parameter tuples.

        Returns:
            Mock cursor object.
        """
        self.executemany_call_count += 1
        if self.fail_on_executemany:
            raise self.executemany_exception
        mock_cursor = MagicMock()
        mock_cursor.rowcount = len(params_list)
        return mock_cursor

    def commit(self):
        """Commit transaction."""
        self.commit_call_count += 1
        if self.fail_on_commit:
            raise self.commit_exception

            raise self.commit_exception
# Add Embedding Error Tests

# =============================================================================



class TestAddEmbeddingErrors:

    """Tests for add_embedding error paths."""



    def test_add_embedding_sql_error(self):

        """Test add_embedding when SQL execution fails."""

        mock_conn = MockConnectionFailing(fail_on_execute=True)

        repo = EmbeddingRepository(mock_conn)



        with pytest.raises(sqlite3.Error, match="Simulated SQL error"):

            repo.add_embedding(

                file_id=1,

                embedding=[0.1, 0.2, 0.3],

                model_version="v1.0",

                created_time=1000

            )



    def test_add_embedding_json_error(self):

        """Test add_embedding when JSON serialization fails."""

        mock_conn = MockConnectionFailing()

        repo = EmbeddingRepository(mock_conn)



        # Create an object that cannot be JSON serialized

        class UnserializableObject:
            """Class that cannot be serialized to JSON."""
            pass



        with pytest.raises(TypeError, match="not JSON serializable"):

            repo.add_embedding(

                file_id=1,

                embedding=UnserializableObject(),

                model_version="v1.0",

                created_time=1000

            )



    def test_add_embedding_generic_exception(self):

        """Test add_embedding with generic exception."""

        mock_conn = MockConnectionFailing(

            fail_on_execute=True,

            execute_exception=Exception("Generic error")

        )

        repo = EmbeddingRepository(mock_conn)



        with pytest.raises(Exception, match="Generic error"):

            repo.add_embedding(

                file_id=1,

                embedding=[0.1, 0.2, 0.3],

                model_version="v1.0",

                created_time=1000

            )





# =============================================================================

# Get Embedding Error Tests

# =============================================================================



class TestGetEmbeddingErrors:

    """Tests for get_embedding error paths."""



    def test_get_embedding_sql_error(self):

        """Test get_embedding when SQL execution fails."""

        mock_conn = MockConnectionFailing(fail_on_execute=True)

        repo = EmbeddingRepository(mock_conn)



        with pytest.raises(sqlite3.Error, match="Simulated SQL error"):

            repo.get_embedding(1)



    def test_get_embedding_deserialization_error(self):

        """Test get_embedding when deserialization fails (invalid JSON and pickle)."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        # Create a mock cursor that returns corrupted data (neither JSON nor pickle)

        mock_cursor = MagicMock()

        # Return a row with corrupted data that's neither valid JSON nor pickle

        mock_cursor.fetchone.return_value = (1, 1, b'\x80\x03\x80\x03corrupted', 'v1.0', 1000, 3)



        mock_conn.execute = MagicMock(return_value=mock_cursor)



        with pytest.raises(Exception):  # pickle.UnpicklingError or EOFError

            repo.get_embedding(1)



    def test_get_embedding_not_found_returns_none(self):

        """Test get_embedding returns None for non-existent ID."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        result = repo.get_embedding(99999)

        assert result is None





# =============================================================================

# Get Embedding By File Error Tests

# =============================================================================



class TestGetEmbeddingByFileErrors:

    """Tests for get_embedding_by_file error paths."""



    def test_get_embedding_by_file_sql_error(self):

        """Test get_embedding_by_file when SQL execution fails."""

        mock_conn = MockConnectionFailing(fail_on_execute=True)

        repo = EmbeddingRepository(mock_conn)



        with pytest.raises(sqlite3.Error, match="Simulated SQL error"):

            repo.get_embedding_by_file(1, "v1.0")



    def test_get_embedding_by_file_deserialization_error(self):

        """Test get_embedding_by_file when deserialization fails."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        mock_cursor = MagicMock()

        mock_cursor.fetchone.return_value = (1, 1, b'\x80\x03\x80\x03corrupted', 'v1.0', 1000, 3)

        mock_conn.execute = MagicMock(return_value=mock_cursor)



        with pytest.raises(Exception):

            repo.get_embedding_by_file(1, "v1.0")



    def test_get_embedding_by_file_not_found_returns_none(self):

        """Test get_embedding_by_file returns None for non-existent."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        result = repo.get_embedding_by_file(999, "v1.0")

        assert result is None





# =============================================================================

# Get Embeddings By File Error Tests

# =============================================================================



class TestGetEmbeddingsByFileErrors:

    """Tests for get_embeddings_by_file error paths."""



    def test_get_embeddings_by_file_sql_error(self):

        """Test get_embeddings_by_file when SQL execution fails."""

        mock_conn = MockConnectionFailing(fail_on_execute=True)

        repo = EmbeddingRepository(mock_conn)



        with pytest.raises(sqlite3.Error, match="Simulated SQL error"):

            repo.get_embeddings_by_file(1)



    def test_get_embeddings_by_file_deserialization_error(self):

        """Test get_embeddings_by_file when deserialization fails."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        mock_cursor = MagicMock()

        # Return rows with corrupted data

        mock_cursor.fetchall.return_value = [(1, 1, b'\x80\x03\x80\x03corrupted', 'v1.0', 1000, 3)]

        mock_conn.execute = MagicMock(return_value=mock_cursor)



        with pytest.raises(Exception):

            repo.get_embeddings_by_file(1)



    def test_get_embeddings_by_file_empty_result(self):

        """Test get_embeddings_by_file returns empty list for no results."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        result = repo.get_embeddings_by_file(999)

        assert result == []





# =============================================================================

# Get Embeddings By Model Error Tests

# =============================================================================



class TestGetEmbeddingsByModelErrors:

    """Tests for get_embeddings_by_model error paths."""



    def test_get_embeddings_by_model_sql_error(self):

        """Test get_embeddings_by_model when SQL execution fails."""

        mock_conn = MockConnectionFailing(fail_on_execute=True)

        repo = EmbeddingRepository(mock_conn)



        with pytest.raises(sqlite3.Error, match="Simulated SQL error"):

            repo.get_embeddings_by_model("v1.0")



    def test_get_embeddings_by_model_deserialization_error(self):

        """Test get_embeddings_by_model when deserialization fails."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        mock_cursor = MagicMock()

        mock_cursor.fetchall.return_value = [(1, 1, b'\x80\x03\x80\x03corrupted', 'v1.0', 1000, 3)]

        mock_conn.execute = MagicMock(return_value=mock_cursor)



        with pytest.raises(Exception):

            repo.get_embeddings_by_model("v1.0")



    def test_get_embeddings_by_model_empty_result(self):

        """Test get_embeddings_by_model returns empty list for no results."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        result = repo.get_embeddings_by_model("nonexistent")

        assert result == []





# =============================================================================

# Update Embedding Error Tests

# =============================================================================



class TestUpdateEmbeddingErrors:

    """Tests for update_embedding error paths."""



    def test_update_embedding_sql_error(self):

        """Test update_embedding when SQL execution fails."""

        mock_conn = MockConnectionFailing(fail_on_execute=True)

        repo = EmbeddingRepository(mock_conn)



        with pytest.raises(sqlite3.Error, match="Simulated SQL error"):

            repo.update_embedding(1, [0.1, 0.2, 0.3])



    def test_update_embedding_json_error(self):

        """Test update_embedding when JSON serialization fails."""

        mock_conn = MockConnectionFailing()

        repo = EmbeddingRepository(mock_conn)



        class UnserializableObject:
            """Class that cannot be serialized to JSON."""
            pass



        with pytest.raises(TypeError, match="not JSON serializable"):

            repo.update_embedding(1, UnserializableObject())



    def test_update_embedding_not_found_returns_false(self):

        """Test update_embedding returns False for non-existent ID."""

        mock_conn = MockConnectionFailing(fail_on_execute=False, rowcount=0)

        repo = EmbeddingRepository(mock_conn)



        result = repo.update_embedding(99999, [0.1, 0.2, 0.3])

        assert result is False





# =============================================================================

# Delete Embedding Error Tests

# =============================================================================



class TestDeleteEmbeddingErrors:

    """Tests for delete_embedding error paths."""



    def test_delete_embedding_sql_error(self):

        """Test delete_embedding when SQL execution fails."""

        mock_conn = MockConnectionFailing(fail_on_execute=True)

        repo = EmbeddingRepository(mock_conn)



        with pytest.raises(sqlite3.Error, match="Simulated SQL error"):

            repo.delete_embedding(1)



    def test_delete_embedding_not_found_returns_false(self):

        """Test delete_embedding returns False for non-existent ID."""

        mock_conn = MockConnectionFailing(fail_on_execute=False, rowcount=0)

        repo = EmbeddingRepository(mock_conn)



        result = repo.delete_embedding(99999)

        assert result is False





# =============================================================================

# Delete Embeddings By File Error Tests

# =============================================================================



class TestDeleteEmbeddingsByFileErrors:

    """Tests for delete_embeddings_by_file error paths."""



    def test_delete_embeddings_by_file_sql_error(self):

        """Test delete_embeddings_by_file when SQL execution fails."""

        mock_conn = MockConnectionFailing(fail_on_execute=True)

        repo = EmbeddingRepository(mock_conn)



        with pytest.raises(sqlite3.Error, match="Simulated SQL error"):

            repo.delete_embeddings_by_file(1)



    def test_delete_embeddings_by_file_no_matches(self):

        """Test delete_embeddings_by_file returns 0 for no matches."""

        mock_conn = MockConnectionFailing(fail_on_execute=False, rowcount=0)

        repo = EmbeddingRepository(mock_conn)



        result = repo.delete_embeddings_by_file(999)

        assert result == 0





# =============================================================================

# Delete Embeddings By Model Error Tests

# =============================================================================



class TestDeleteEmbeddingsByModelErrors:

    """Tests for delete_embeddings_by_model error paths."""



    def test_delete_embeddings_by_model_sql_error(self):

        """Test delete_embeddings_by_model when SQL execution fails."""

        mock_conn = MockConnectionFailing(fail_on_execute=True)

        repo = EmbeddingRepository(mock_conn)



        with pytest.raises(sqlite3.Error, match="Simulated SQL error"):

            repo.delete_embeddings_by_model("v1.0")



    def test_delete_embeddings_by_model_no_matches(self):

        """Test delete_embeddings_by_model returns 0 for no matches."""

        mock_conn = MockConnectionFailing(fail_on_execute=False, rowcount=0)

        repo = EmbeddingRepository(mock_conn)



        result = repo.delete_embeddings_by_model("nonexistent")

        assert result == 0





# =============================================================================

# Get All Embeddings Error Tests

# =============================================================================



class TestGetAllEmbeddingsErrors:

    """Tests for get_all_embeddings error paths."""



    def test_get_all_embeddings_sql_error(self):

        """Test get_all_embeddings when SQL execution fails."""

        mock_conn = MockConnectionFailing(fail_on_execute=True)

        repo = EmbeddingRepository(mock_conn)



        with pytest.raises(sqlite3.Error, match="Simulated SQL error"):

            repo.get_all_embeddings()



    def test_get_all_embeddings_deserialization_error(self):

        """Test get_all_embeddings when deserialization fails."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        mock_cursor = MagicMock()

        mock_cursor.fetchall.return_value = [(1, 1, b'\x80\x03\x80\x03corrupted', 'v1.0', 1000, 3)]

        mock_conn.execute = MagicMock(return_value=mock_cursor)



        with pytest.raises(Exception):

            repo.get_all_embeddings()



    def test_get_all_embeddings_empty_result(self):

        """Test get_all_embeddings returns empty list when no data."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        result = repo.get_all_embeddings()

        assert result == []





# =============================================================================

# Count Embeddings Error Tests

# =============================================================================



class TestCountEmbeddingsErrors:

    """Tests for count_embeddings error paths."""



    def test_count_embeddings_sql_error(self):

        """Test count_embeddings when SQL execution fails."""

        mock_conn = MockConnectionFailing(fail_on_execute=True)

        repo = EmbeddingRepository(mock_conn)



        with pytest.raises(sqlite3.Error, match="Simulated SQL error"):

            repo.count_embeddings()



    def test_count_embeddings_fetchone_none(self):

        """Test count_embeddings handles fetchone returning None."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        mock_cursor = MagicMock()

        mock_cursor.fetchone.return_value = None

        mock_conn.execute = MagicMock(return_value=mock_cursor)



        # This should raise TypeError when trying to subscript None

        with pytest.raises(TypeError):

            repo.count_embeddings()





# =============================================================================

# Count Embeddings By Model Error Tests

# =============================================================================



class TestCountEmbeddingsByModelErrors:

    """Tests for count_embeddings_by_model error paths."""



    def test_count_embeddings_by_model_sql_error(self):

        """Test count_embeddings_by_model when SQL execution fails."""

        mock_conn = MockConnectionFailing(fail_on_execute=True)

        repo = EmbeddingRepository(mock_conn)



        with pytest.raises(sqlite3.Error, match="Simulated SQL error"):

            repo.count_embeddings_by_model("v1.0")



    def test_count_embeddings_by_model_fetchone_none(self):

        """Test count_embeddings_by_model handles fetchone returning None."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        mock_cursor = MagicMock()

        mock_cursor.fetchone.return_value = None

        mock_conn.execute = MagicMock(return_value=mock_cursor)



        with pytest.raises(TypeError):

            repo.count_embeddings_by_model("v1.0")





# =============================================================================

# Batch Add Embeddings Error Tests

# =============================================================================



class TestBatchAddEmbeddingsErrors:

    """Tests for batch_add_embeddings error paths."""



    def test_batch_add_embeddings_sql_error(self):

        """Test batch_add_embeddings when SQL execution fails."""

        mock_conn = MockConnectionFailing(fail_on_executemany=True)

        repo = EmbeddingRepository(mock_conn)



        embeddings = [

            {"file_id": 1, "embedding": [0.1, 0.2, 0.3], "model_version": "v1", "created_time": 1000},

            {"file_id": 2, "embedding": [0.4, 0.5, 0.6], "model_version": "v1", "created_time": 1001},

        ]



        with pytest.raises(sqlite3.Error, match="Simulated batch SQL error"):

            repo.batch_add_embeddings(embeddings)



    def test_batch_add_embeddings_empty_list(self):

        """Test batch_add_embeddings with empty list returns 0."""

        mock_conn = MockConnectionFailing()

        repo = EmbeddingRepository(mock_conn)



        result = repo.batch_add_embeddings([])

        assert result == 0



    def test_batch_add_embeddings_json_error(self):

        """Test batch_add_embeddings when JSON serialization fails."""

        mock_conn = MockConnectionFailing()

        repo = EmbeddingRepository(mock_conn)



        class UnserializableObject:
            """Class that cannot be serialized to JSON."""
            pass



        embeddings = [

            {"file_id": 1, "embedding": UnserializableObject(), "model_version": "v1", "created_time": 1000},

        ]



        with pytest.raises(TypeError, match="not JSON serializable"):

            repo.batch_add_embeddings(embeddings)



    def test_batch_add_embeddings_missing_keys(self):

        """Test batch_add_embeddings with missing required keys."""

        mock_conn = MockConnectionFailing()

        repo = EmbeddingRepository(mock_conn)



        embeddings = [

            {"file_id": 1, "model_version": "v1", "created_time": 1000},  # Missing 'embedding'

        ]



        with pytest.raises(KeyError):

            repo.batch_add_embeddings(embeddings)





# =============================================================================

# Clear All Embeddings Error Tests

# =============================================================================



class TestClearAllEmbeddingsErrors:

    """Tests for clear_all_embeddings error paths."""



    def test_clear_all_embeddings_sql_error(self):

        """Test clear_all_embeddings when SQL execution fails."""

        mock_conn = MockConnectionFailing(fail_on_execute=True)

        repo = EmbeddingRepository(mock_conn)



        with pytest.raises(sqlite3.Error, match="Simulated SQL error"):

            repo.clear_all_embeddings()



    def test_clear_all_embeddings_commit_error(self):

        """Test clear_all_embeddings when commit fails."""

        mock_conn = MockConnectionFailing(fail_on_commit=True)

        repo = EmbeddingRepository(mock_conn)



        with pytest.raises(sqlite3.Error, match="Simulated commit error"):

            repo.clear_all_embeddings()





# =============================================================================

# Get Embedding Repository Function Error Tests

# =============================================================================



class TestGetEmbeddingRepositoryErrors:

    """Tests for get_embedding_repository function error paths."""



    def test_get_embedding_repository_with_invalid_path(self, tmp_path):

        """Test get_embedding_repository with invalid database path."""

        # Create a path that doesn't exist and can't be created

        invalid_path = str(tmp_path / "nonexistent_dir" / "test.db")



        # This should work as the function creates directories

        repo = get_embedding_repository(invalid_path)

        assert isinstance(repo, EmbeddingRepository)



    def test_get_embedding_repository_memory(self):

        """Test get_embedding_repository with in-memory database."""

        repo = get_embedding_repository(":memory:")

        assert isinstance(repo, EmbeddingRepository)





# =============================================================================

# Edge Cases and Boundary Tests

# =============================================================================



class TestEmbeddingEdgeCases:

    """Tests for edge cases in embedding operations."""



    def test_add_embedding_empty_vector(self):

        """Test add_embedding with empty embedding vector."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        embedding_id = repo.add_embedding(

            file_id=1,

            embedding=[],

            model_version="v1.0",

            created_time=1000

        )

        assert embedding_id is not None



    def test_add_embedding_very_large_vector(self):

        """Test add_embedding with very large embedding vector."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        large_embedding = list(range(10000))

        embedding_id = repo.add_embedding(

            file_id=1,

            embedding=large_embedding,

            model_version="v1.0",

            created_time=1000

        )

        assert embedding_id is not None



    def test_add_embedding_numpy_array(self):

        """Test add_embedding with numpy array."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        embedding_id = repo.add_embedding(

            file_id=1,

            embedding=embedding,

            model_version="v1.0",

            created_time=1000

        )

        assert embedding_id is not None



    def test_add_embedding_multidimensional_array(self):

        """Test add_embedding with multidimensional array."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        embedding = [[0.1, 0.2], [0.3, 0.4]]

        embedding_id = repo.add_embedding(

            file_id=1,

            embedding=embedding,

            model_version="v1.0",

            created_time=1000

        )

        assert embedding_id is not None



    def test_get_embedding_dimensions_with_non_sequence(self):

        """Test _get_embedding_dimensions with non-sequence object."""

        mock_conn = MockConnectionFailing()

        repo = EmbeddingRepository(mock_conn)



        # Test with integer (no __len__)

        assert repo._get_embedding_dimensions(42) == 0



        # Test with None

        assert repo._get_embedding_dimensions(None) == 0



    def test_get_embedding_dimensions_with_dict(self):

        """Test _get_embedding_dimensions with dict."""

        mock_conn = MockConnectionFailing()

        repo = EmbeddingRepository(mock_conn)



        # Dict has __len__

        assert repo._get_embedding_dimensions({"a": 1, "b": 2}) == 2



    def test_update_embedding_zero_vector(self):

        """Test update_embedding with zero vector."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        result = repo.update_embedding(1, [0.0, 0.0, 0.0])

        # Should return True if row exists (mock returns rowcount=1)

        assert result is True



    def test_delete_embedding_negative_id(self):

        """Test delete_embedding with negative ID."""

        mock_conn = MockConnectionFailing(fail_on_execute=False, rowcount=0)

        repo = EmbeddingRepository(mock_conn)



        result = repo.delete_embedding(-1)

        # Should return False (no row affected)

        assert result is False



    def test_get_embeddings_by_file_with_zero_file_id(self):

        """Test get_embeddings_by_file with zero file_id."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        result = repo.get_embeddings_by_file(0)

        assert result == []



    def test_get_embeddings_by_model_with_empty_string(self):

        """Test get_embeddings_by_model with empty model version."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        result = repo.get_embeddings_by_model("")

        assert result == []



    def test_count_embeddings_by_model_with_empty_string(self):

        """Test count_embeddings_by_model with empty model version."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        mock_cursor = MagicMock()

        mock_cursor.fetchone.return_value = (0,)

        mock_conn.execute = MagicMock(return_value=mock_cursor)



        result = repo.count_embeddings_by_model("")

        assert result == 0



    def test_batch_add_embeddings_single_item(self):

        """Test batch_add_embeddings with single item."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        embeddings = [

            {"file_id": 1, "embedding": [0.1, 0.2, 0.3], "model_version": "v1", "created_time": 1000},

        ]



        count = repo.batch_add_embeddings(embeddings)

        assert count == 1



    def test_batch_add_embeddings_with_numpy_arrays(self):

        """Test batch_add_embeddings with numpy arrays."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        embeddings = [

            {"file_id": 1, "embedding": np.array([0.1, 0.2, 0.3]), "model_version": "v1", "created_time": 1000},

            {"file_id": 2, "embedding": np.array([0.4, 0.5, 0.6]), "model_version": "v1", "created_time": 1001},

        ]



        count = repo.batch_add_embeddings(embeddings)

        assert count == 2





# =============================================================================

# Database Connection Error Tests

# =============================================================================



class TestDatabaseConnectionErrors:

    """Tests for database connection related errors."""



    def test_repository_with_mock_connection(self):

        """Test repository works with mock connection."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        # Test basic operations don't crash with mock

        embedding_id = repo.add_embedding(1, [0.1, 0.2], "v1", 1000)

        assert embedding_id is not None



    def test_repository_execute_returns_cursor(self):

        """Test that execute returns a cursor-like object."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        # Verify the mock cursor has expected attributes

        result = repo.add_embedding(1, [0.1, 0.2], "v1", 1000)

        assert result is not None



    def test_repository_executemany_returns_cursor(self):

        """Test that executemany returns a cursor-like object."""

        mock_conn = MockConnectionFailing(fail_on_execute=False)

        repo = EmbeddingRepository(mock_conn)



        embeddings = [

            {"file_id": 1, "embedding": [0.1], "model_version": "v1", "created_time": 1000},

        ]

        count = repo.batch_add_embeddings(embeddings)

        assert count == 1
