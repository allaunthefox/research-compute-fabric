# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for DatabaseSerialization to achieve 100% coverage."""

from unittest.mock import MagicMock

import pytest

from nodupe.tools.databases.serialization import DatabaseSerialization


class TestDatabaseSerializationCoverage:
    """Test cases to achieve full coverage of DatabaseSerialization."""

    def test_serialize_dict(self):
        """Test serializing a dictionary."""
        mock_conn = MagicMock()
        serialization = DatabaseSerialization(mock_conn)
        
        result = serialization.serialize({"key": "value"})
        assert result == '{"key": "value"}'

    def test_serialize_list(self):
        """Test serializing a list."""
        mock_conn = MagicMock()
        serialization = DatabaseSerialization(mock_conn)
        
        result = serialization.serialize([1, 2, 3])
        assert result == "[1, 2, 3]"

    def test_serialize_unserializable(self):
        """Test serializing unserializable data raises ValueError."""
        mock_conn = MagicMock()
        serialization = DatabaseSerialization(mock_conn)
        
        # datetime objects are not JSON serializable by default
        from datetime import datetime
        with pytest.raises(ValueError):
            serialization.serialize({"date": datetime.now()})

    def test_deserialize_valid(self):
        """Test deserializing valid JSON."""
        mock_conn = MagicMock()
        serialization = DatabaseSerialization(mock_conn)
        
        result = serialization.deserialize('{"key": "value"}')
        assert result == {"key": "value"}

    def test_deserialize_invalid(self):
        """Test deserializing invalid JSON raises ValueError."""
        mock_conn = MagicMock()
        serialization = DatabaseSerialization(mock_conn)
        
        with pytest.raises(ValueError):
            serialization.deserialize("not valid json")

    def test_serialize_safe_with_invalid(self):
        """Test serialize_safe returns empty dict on failure."""
        mock_conn = MagicMock()
        serialization = DatabaseSerialization(mock_conn)
        
        from datetime import datetime
        result = serialization.serialize_safe({"date": datetime.now()})
        assert result == '{}'

    def test_deserialize_safe_with_invalid(self):
        """Test deserialize_safe returns original on failure."""
        mock_conn = MagicMock()
        serialization = DatabaseSerialization(mock_conn)
        
        original = "not valid json"
        result = serialization.deserialize_safe(original)
        assert result == original
