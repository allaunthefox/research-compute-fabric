# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for DatabaseSession to achieve 100% coverage."""

from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.databases.session import DatabaseSession


class TestDatabaseSessionCoverage:
    """Test cases to achieve full coverage of DatabaseSession."""

    def test_session_initialization(self):
        """Test session initialization."""
        mock_conn = MagicMock()
        session = DatabaseSession(mock_conn)
        assert session.connection is mock_conn
        assert session.is_active is False

    def test_begin_session_success(self):
        """Test beginning a session successfully."""
        mock_conn = MagicMock()
        mock_connection = MagicMock()
        mock_conn.get_connection.return_value = mock_connection
        
        session = DatabaseSession(mock_conn)
        
        with session.begin() as conn:
            assert conn is mock_connection
            assert session.is_active is True
        
        assert session.is_active is False
        mock_connection.commit.assert_called()

    def test_begin_session_rollback_on_error(self):
        """Test session rolls back on error."""
        mock_conn = MagicMock()
        mock_connection = MagicMock()
        mock_conn.get_connection.return_value = mock_connection
        
        session = DatabaseSession(mock_conn)
        
        with pytest.raises(ValueError):
            with session.begin() as conn:
                raise ValueError("Test error")
        
        assert session.is_active is False
        mock_connection.rollback.assert_called()

    def test_is_active_property(self):
        """Test is_active property."""
        mock_conn = MagicMock()
        session = DatabaseSession(mock_conn)
        
        assert session.is_active is False
        
        session._active = True
        assert session.is_active is True
