# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Database Logging Module.

This module provides database logging functionality for tracking operations,
queries, and events within the database layer.

Classes:
    DatabaseLogging: Handles logging of database operations.

Example:
    >>> from nodupe.core.database import Database
    >>> db = Database("/path/to/db.db")
    >>> db.logging.log("Operation completed", "INFO")
"""

from __future__ import annotations

from typing import Any
import sqlite3


class DatabaseLogging:
    """Database logging functionality.

    Provides methods for logging database operations, queries, and events
    to both console and database storage.

    Attributes:
        enabled: Whether logging is enabled.
        log_to_db: Whether to store logs in the database.

    Example:
        >>> logger = DatabaseLogging(connection)
        >>> logger.log("Query executed", "INFO")
    """

    def __init__(self, connection: Any) -> None:
        """Initialize database logging.

        Args:
            connection: Database connection instance.
        """
        self.connection = connection
        self.enabled = True
        self.log_to_db = False

    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message.

        Args:
            message: The message to log.
            level: The log level (INFO, WARNING, ERROR, DEBUG).

        Example:
            >>> logger.log("Database operation", "INFO")
        """
        if not self.enabled:
            return

        # Simple console logging for now
        print(f"[{level}] {message}")

        if self.log_to_db:
            self._log_to_database(message, level)

    def _log_to_database(self, message: str, level: str) -> None:
        """Log to database table.

        Args:
            message: The message to log.
            level: The log level.
        """
        conn = None
        opened_conn = False
        try:
            if hasattr(self.connection, "get_connection"):
                conn = self.connection.get_connection()
            elif hasattr(self.connection, "execute"):
                conn = self.connection
            elif isinstance(self.connection, str):
                # Treat as DB path
                conn = sqlite3.connect(self.connection)
                opened_conn = True

            if conn is None:
                return

            conn.execute(
                "CREATE TABLE IF NOT EXISTS db_logs ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "timestamp DEFAULT CURRENT_TIMESTAMP, "
                "level TEXT, "
                "message TEXT"
                ")"
            )
            conn.execute(
                "INSERT INTO db_logs (level, message) VALUES (?, ?)",
                (level, message)
            )
            if opened_conn:
                conn.commit()
                conn.close()
            else:
                try:
                    conn.commit()
                except Exception:
                    # Some mock connections may not implement commit
                    pass
        except Exception:
            # Silently fail if logging table creation or insert fails
            try:
                if opened_conn and conn is not None:
                    conn.close()
            except Exception:
                pass

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable logging.

        Args:
            enabled: Whether to enable logging.

        Example:
            >>> logger.set_enabled(False)
        """
        self.enabled = enabled

    def set_log_to_db(self, log_to_db: bool) -> None:
        """Enable or disable database logging.

        Args:
            log_to_db: Whether to log to database.

        Example:
            >>> logger.set_log_to_db(True)
        """
        self.log_to_db = log_to_db
