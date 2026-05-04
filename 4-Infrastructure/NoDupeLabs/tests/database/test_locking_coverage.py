# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for DatabaseLocking to achieve 100% coverage."""

from unittest.mock import MagicMock

import pytest

from nodupe.tools.databases.locking import DatabaseLocking


class TestDatabaseLockingCoverage:
    """Test cases to achieve full coverage of DatabaseLocking."""

    def test_lock_acquire_and_release(self):
        """Test lock context manager acquires and releases."""
        mock_conn = MagicMock()
        locking = DatabaseLocking(mock_conn)
        
        with locking.lock("resource1"):
            assert locking.is_locked("resource1") is True
        
        assert locking.is_locked("resource1") is False

    def test_multiple_locks(self):
        """Test multiple locks can be held simultaneously."""
        mock_conn = MagicMock()
        locking = DatabaseLocking(mock_conn)
        
        with locking.lock("resource1"):
            assert locking.is_locked("resource1") is True
            with locking.lock("resource2"):
                assert locking.is_locked("resource2") is True
                assert locking.is_locked("resource1") is True
            
            assert locking.is_locked("resource2") is False
            assert locking.is_locked("resource1") is True
        
        assert locking.is_locked("resource1") is False

    def test_get_held_locks_empty(self):
        """Test get_held_locks returns empty set initially."""
        mock_conn = MagicMock()
        locking = DatabaseLocking(mock_conn)
        
        locks = locking.get_held_locks()
        assert locks == set()

    def test_get_held_locks_with_locks(self):
        """Test get_held_locks returns correct locks."""
        mock_conn = MagicMock()
        locking = DatabaseLocking(mock_conn)
        
        with locking.lock("resource1"):
            with locking.lock("resource2"):
                locks = locking.get_held_locks()
                assert "resource1" in locks
                assert "resource2" in locks
                assert len(locks) == 2

    def test_get_held_locks_returns_copy(self):
        """Test get_held_locks returns a copy, not the original."""
        mock_conn = MagicMock()
        locking = DatabaseLocking(mock_conn)
        
        locks = locking.get_held_locks()
        locks.add("fake_lock")  # Modify the returned set
        
        # Original should not be modified
        assert "fake_lock" not in locking.get_held_locks()
