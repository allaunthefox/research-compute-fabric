# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for DatabaseLogging to achieve 100% coverage."""

from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.databases.logging_ import DatabaseLogging


class TestDatabaseLoggingCoverage:
    """Test cases to achieve full coverage of DatabaseLogging."""

    def test_log_disabled(self):
        """Test logging does nothing when disabled."""
        mock_conn = MagicMock()
        logger = DatabaseLogging(mock_conn)
        logger.enabled = False
        
        # Should not raise and should not print
        logger.log("test message", "INFO")

    def test_log_enabled_no_db(self):
        """Test logging to console when enabled but log_to_db is False."""
        mock_conn = MagicMock()
        logger = DatabaseLogging(mock_conn)
        logger.enabled = True
        logger.log_to_db = False
        
        # Should not raise
        logger.log("test message", "INFO")

    def test_log_to_database_success(self):
        """Test logging to database when enabled."""
        mock_conn = MagicMock()
        mock_conn.get_connection.return_value = MagicMock()
        
        logger = DatabaseLogging(mock_conn)
        logger.enabled = True
        logger.log_to_db = True
        
        # Should not raise
        logger.log("test message", "INFO")

    def test_log_to_database_exception(self):
        """Test logging to database handles exceptions."""
        mock_conn = MagicMock()
        mock_conn.get_connection.side_effect = Exception("DB Error")
        
        logger = DatabaseLogging(mock_conn)
        logger.enabled = True
        logger.log_to_db = True
        
        # Should not raise even when DB fails
        logger.log("test message", "INFO")

    def test_set_enabled_true(self):
        """Test set_enabled with True."""
        mock_conn = MagicMock()
        logger = DatabaseLogging(mock_conn)
        
        logger.set_enabled(True)
        assert logger.enabled is True

    def test_set_enabled_false(self):
        """Test set_enabled with False."""
        mock_conn = MagicMock()
        logger = DatabaseLogging(mock_conn)
        
        logger.set_enabled(False)
        assert logger.enabled is False

    def test_set_log_to_db_true(self):
        """Test set_log_to_db with True."""
        mock_conn = MagicMock()
        logger = DatabaseLogging(mock_conn)
        
        logger.set_log_to_db(True)
        assert logger.log_to_db is True

    def test_set_log_to_db_false(self):
        """Test set_log_to_db with False."""
        mock_conn = MagicMock()
        logger = DatabaseLogging(mock_conn)
        
        logger.set_log_to_db(False)
        assert logger.log_to_db is False
