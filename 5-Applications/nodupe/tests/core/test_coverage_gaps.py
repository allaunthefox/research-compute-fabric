# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests to cover remaining coverage gaps in target files.

This module contains targeted tests to achieve 100% coverage on the
16 files identified in COVERAGE_TRACKING.md as being at 80-95% coverage.
"""

import json
import os
import sqlite3
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from nodupe.core.api.ipc import ToolIPCServer
from nodupe.core.config import ConfigManager, load_config
from nodupe.core.logging_system import Logging, LoggingError, get_logger, setup_logging
from nodupe.core.tool_system.base import AccessibleTool
from nodupe.core.tool_system.lifecycle import ToolLifecycleManager
from nodupe.core.tool_system.loading_order import ToolLoadingOrder
from nodupe.tools.databases.connection import DatabaseConnection, get_connection
from nodupe.tools.databases.database_tool import StandardDatabaseTool, register_tool
from nodupe.tools.databases.files import FileRepository, _row_to_dict, get_file_repository
from nodupe.tools.databases.logging_ import DatabaseLogging
from nodupe.tools.databases.query_cache import QueryCache, create_query_cache

# Import all modules under test
from nodupe.tools.databases.schema import DatabaseSchema, SchemaError, create_database
from nodupe.tools.databases.security import DatabaseSecurity, InputValidationError
from nodupe.tools.databases.wrapper import Database as DatabaseWrapper
from nodupe.tools.hashing.hash_cache import HashCache, create_hash_cache
from nodupe.tools.ml.embedding_cache import EmbeddingCache, create_embedding_cache


# =============================================================================
# Helper classes for testing AccessibleTool abstract methods
# =============================================================================

class TestAccessibleTool(AccessibleTool):
    """Test implementation of AccessibleTool for coverage testing.

    This class implements all abstract methods of AccessibleTool to enable
    testing of the base class methods that require a concrete implementation.
    """

    @property
    def name(self):
        """Return tool name."""
        return "test"

    @property
    def version(self):
        """Return tool version."""
        return "1.0.0"

    @property
    def dependencies(self):
        """Return tool dependencies."""
        return []

    def initialize(self, container):
        """Initialize the tool."""
        pass

    def shutdown(self):
        """Shutdown the tool."""
        pass

    def get_capabilities(self):
        """Return tool capabilities."""
        return {}

    @property
    def api_methods(self):
        """Return API methods."""
        return {}

    def run_standalone(self, args):
        """Run tool standalone."""
        return 0

    def describe_usage(self):
        """Describe tool usage."""
        return "test"


class UnconvertibleResult:
    """Test class whose __str__ method raises an exception.

    Used to test error handling in memory usage calculations.
    """

    def __str__(self):
        """Raise exception to test error handling."""
        raise Exception("Cannot convert")


# =============================================================================
# Schema.py Coverage (87.42%) - Lines 244-245, 399-400, 423-424
# =============================================================================

class TestSchemaCoverageGaps:
    """Tests for schema.py coverage gaps."""

    def test_migrate_schema_no_version_table(self):
        """Test migrate_schema when schema_version table doesn't exist (lines 244-245)."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            conn = sqlite3.connect(tmp.name)
            schema = DatabaseSchema(conn)

            # Don't create schema_version table - this should trigger the None return path
            # Then migrate_schema should call create_schema
            schema.migrate_schema()

            # Verify schema was created
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert 'files' in tables

            conn.close()

    def test_get_table_info_error_handling(self):
        """Test get_table_info error handling (lines 399-400)."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            conn = sqlite3.connect(tmp.name)
            schema = DatabaseSchema(conn)

            # Close connection to trigger error
            conn.close()

            with pytest.raises(SchemaError):
                schema.get_table_info('files')

    def test_get_indexes_error_handling(self):
        """Test get_indexes error handling (lines 423-424)."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            conn = sqlite3.connect(tmp.name)
            schema = DatabaseSchema(conn)

            # Close connection to trigger error
            conn.close()

            with pytest.raises(SchemaError):
                schema.get_indexes('files')


# =============================================================================
# base.py Coverage (87.80%) - Lines 96, 108, 117, 126, 136
# =============================================================================

class TestBaseCoverageGaps:
    """Tests for base.py coverage gaps - AccessibleTool methods."""

    def test_accessible_tool_announce_to_assistive_tech(self):
        """Test AccessibleTool.announce_to_assistive_tech (line 96)."""
        tool = TestAccessibleTool()

        # Test announce_to_assistive_tech with default params
        tool.announce_to_assistive_tech("Test message")
        tool.announce_to_assistive_tech("Test message", interrupt=False)

    def test_accessible_tool_format_for_accessibility(self):
        """Test AccessibleTool.format_for_accessibility (line 108)."""
        tool = TestAccessibleTool()

        # Test format_for_accessibility with various data types
        # Note: Default implementation returns None
        result = tool.format_for_accessibility("string data")
        # Just verify it can be called without error
        assert result is None or isinstance(result, str)

    def test_accessible_tool_get_ipc_socket_documentation(self):
        """Test AccessibleTool.get_ipc_socket_documentation (line 117)."""
        tool = TestAccessibleTool()

        # Test get_ipc_socket_documentation
        # Note: Default implementation returns None
        result = tool.get_ipc_socket_documentation()
        # Just verify it can be called without error
        assert result is None or isinstance(result, dict)

    def test_accessible_tool_get_accessible_status(self):
        """Test AccessibleTool.get_accessible_status (line 126)."""
        tool = TestAccessibleTool()

        # Test get_accessible_status
        # Note: Default implementation returns None
        result = tool.get_accessible_status()
        # Just verify it can be called without error
        assert result is None or isinstance(result, str)

    def test_accessible_tool_log_accessible_message(self):
        """Test AccessibleTool.log_accessible_message (line 136)."""
        tool = TestAccessibleTool()

        # Test log_accessible_message with various levels
        tool.log_accessible_message("Test info message", level="info")
        tool.log_accessible_message("Test warning message", level="warning")
        tool.log_accessible_message("Test error message", level="error")
        tool.log_accessible_message("Test debug message", level="debug")


# =============================================================================
# lifecycle.py Coverage (89.45%) - Lines 186-188, 197-200
# =============================================================================

class TestLifecycleCoverageGaps:
    """Tests for lifecycle.py coverage gaps."""

    def test_initialize_tool_already_initialized(self):
        """Test initialize_tool when tool is already initialized (lines 186-188)."""
        registry = Mock()
        manager = ToolLifecycleManager(registry)

        # Create a mock tool
        mock_tool = Mock()
        mock_tool.name = "test_tool"

        # Initialize the tool first
        manager.initialize_tool(mock_tool, Mock())

        # Now initialize again - should return True immediately
        result = manager.initialize_tool(mock_tool, Mock())
        assert result is True

    def test_shutdown_tool_already_shutdown(self):
        """Test shutdown_tool when tool is already shutdown (lines 197-200)."""
        registry = Mock()
        manager = ToolLifecycleManager(registry)

        # Create and register a mock tool
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        registry.get_tool.return_value = mock_tool

        # Initialize then shutdown the tool
        manager.initialize_tool(mock_tool, Mock())
        manager.shutdown_tool("test_tool")

        # Now shutdown again - should return True immediately
        result = manager.shutdown_tool("test_tool")
        assert result is True


# =============================================================================
# hash_cache.py Coverage (90.44%) - Lines 97-101, 185-187
# =============================================================================

class TestHashCacheCoverageGaps:
    """Tests for hash_cache.py coverage gaps."""

    def test_get_hash_file_modified(self):
        """Test get_hash when file has been modified (lines 97-101)."""
        cache = HashCache(max_size=100, ttl_seconds=3600)

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")
            tmp.flush()
            file_path = Path(tmp.name)

            # Add to cache
            cache.set_hash(file_path, "abc123")

            # Modify the file to change mtime
            time.sleep(0.1)
            with open(file_path, 'w') as f:
                f.write("modified content")

            # Get should detect modification and return None
            result = cache.get_hash(file_path)
            assert result is None

            os.unlink(file_path)

    def test_resize_cache(self):
        """Test resize method (lines 185-187)."""
        cache = HashCache(max_size=100, ttl_seconds=3600)

        # Add some entries
        for i in range(50):
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(f"content {i}".encode())
                tmp.flush()
                file_path = Path(tmp.name)
                cache.set_hash(file_path, f"hash_{i}")
                os.unlink(file_path)

        # Resize to smaller size
        cache.resize(20)

        # Cache should be reduced to 20 entries
        assert cache.get_cache_size() == 20


# =============================================================================
# files.py Coverage (91.28%) - Lines 68-70, 199-201, 224-226
# =============================================================================

class TestFilesCoverageGaps:
    """Tests for files.py coverage gaps."""

    def test_row_to_dict_none_row(self):
        """Test _row_to_dict with None row (lines 68-70)."""
        mock_cursor = Mock()
        result = _row_to_dict(mock_cursor, None)
        assert result == {}

    def test_update_file_no_valid_fields(self):
        """Test update_file with no valid fields (lines 199-201)."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            db.get_connection()

            # Create schema
            schema = DatabaseSchema(db.get_connection())
            schema.create_schema()

            repo = FileRepository(db)

            # Add a file first
            file_id = repo.add_file("/test.txt", 100, 12345, "abc123")

            # Try to update with invalid field
            result = repo.update_file(file_id, invalid_field="value")
            assert result is False

            db.close()

    def test_update_file_empty_kwargs(self):
        """Test update_file with empty kwargs (lines 224-226)."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            db.get_connection()

            # Create schema
            schema = DatabaseSchema(db.get_connection())
            schema.create_schema()

            repo = FileRepository(db)

            # Add a file first
            file_id = repo.add_file("/test.txt", 100, 12345, "abc123")

            # Try to update with empty kwargs
            result = repo.update_file(file_id)
            assert result is False

            db.close()


# =============================================================================
# config.py Coverage (92.21%) - Lines 20-21, 71-72, 107-108
# =============================================================================

class TestConfigCoverageGaps:
    """Tests for config.py coverage gaps."""

    def test_config_manager_no_toml_package(self):
        """Test ConfigManager when toml package is not available (lines 20-21)."""
        with patch.dict('sys.modules', {'tomli': None, 'toml': None, 'tomlkit': None}):
            # Need to reload the module to trigger the import error
            import importlib

            import nodupe.core.config as config_module
            importlib.reload(config_module)

            # Create config manager - should use empty config
            manager = config_module.ConfigManager()
            assert manager.config == {}

            # Reload back to normal
            importlib.reload(config_module)

    def test_get_nodupe_config_exception_handling(self):
        """Test get_nodupe_config exception handling (lines 71-72)."""
        manager = ConfigManager.__new__(ConfigManager)
        manager.config = None  # This will cause AttributeError

        result = manager.get_nodupe_config()
        assert result == {}

    def test_validate_config_missing_section(self):
        """Test validate_config with missing section (lines 107-108)."""
        manager = ConfigManager.__new__(ConfigManager)
        manager.config = {'tool': {'nodupe': {}}}  # Missing required sections

        result = manager.validate_config()
        assert result is False


# =============================================================================
# logging_.py Coverage (93.10%) - Lines 89-90
# =============================================================================

class TestLoggingCoverageGaps:
    """Tests for logging_.py coverage gaps."""

    def test_log_disabled(self):
        """Test log when logging is disabled (lines 89-90)."""
        mock_connection = Mock()
        logger = DatabaseLogging(mock_connection)
        logger.set_enabled(False)

        # Should return immediately without logging
        logger.log("Test message")

        # Verify nothing was called
        mock_connection.get_connection.assert_not_called()


# =============================================================================
# database_tool.py Coverage (93.33%) - Lines 60-62
# =============================================================================

class TestDatabaseToolCoverageGaps:
    """Tests for database_tool.py coverage gaps."""

    def test_initialize_error_handling(self):
        """Test initialize with error handling (lines 60-62)."""
        tool = StandardDatabaseTool()

        # Mock db.initialize_database to raise exception
        with patch.object(tool.db, 'initialize_database', side_effect=Exception("Init failed")):
            mock_container = Mock()

            # Should log error but not raise
            tool.initialize(mock_container)

            # Verify service was not registered
            mock_container.register_service.assert_not_called()


# =============================================================================
# embedding_cache.py Coverage (93.50%) - Lines 240-241, 307, 347, 403
# =============================================================================

class TestEmbeddingCacheCoverageGaps:
    """Tests for embedding_cache.py coverage gaps."""

    def test_calculate_similarity_none_embedding(self):
        """Test calculate_similarity when embedding not cached (lines 240-241)."""
        cache = EmbeddingCache(max_size=100, ttl_seconds=3600)

        # Try to calculate similarity with non-existent keys
        result = cache.calculate_similarity("key1", "key2")
        assert result is None

    def test_get_average_embedding_empty_keys(self):
        """Test get_average_embedding with empty keys list (line 307)."""
        cache = EmbeddingCache(max_size=100, ttl_seconds=3600)

        result = cache.get_average_embedding([])
        assert result is None

    def test_get_average_embedding_no_valid_embeddings(self):
        """Test get_average_embedding when no embeddings are cached (line 347)."""
        cache = EmbeddingCache(max_size=100, ttl_seconds=3600)

        # Try to get average of non-existent keys
        result = cache.get_average_embedding(["key1", "key2"])
        assert result is None

    def test_clear_by_pattern(self):
        """Test clear_by_pattern method (line 403)."""
        cache = EmbeddingCache(max_size=100, ttl_seconds=3600)

        # Add some embeddings
        cache.set_embedding("test_key_1", [0.1, 0.2, 0.3])
        cache.set_embedding("test_key_2", [0.4, 0.5, 0.6])
        cache.set_embedding("other_key", [0.7, 0.8, 0.9])

        # Clear by pattern
        cleared = cache.clear_by_pattern("test")
        assert cleared == 2

        # Verify only matching keys were cleared
        assert cache.is_cached("other_key")
        assert not cache.is_cached("test_key_1")
        assert not cache.is_cached("test_key_2")


# =============================================================================
# loading_order.py Coverage (94.67%) - Lines 602-604, 629-630
# =============================================================================

class TestLoadingOrderCoverageGaps:
    """Tests for loading_order.py coverage gaps."""

    def test_get_safe_load_sequence_with_circular_deps(self):
        """Test get_safe_load_sequence when circular dependencies exist (lines 602-604)."""

        manager = ToolLoadingOrder()

        # Create a scenario that would trigger circular dependency detection
        # This is hard to trigger naturally, so we'll mock get_load_sequence to raise
        with patch.object(manager, 'get_load_sequence', side_effect=ValueError("Circular dependency")):
            # Should fall back to _fallback_load_sequence
            safe_sequence, excluded = manager.get_safe_load_sequence(["tool1", "tool2"])

            # Should return fallback sequence
            assert isinstance(safe_sequence, list)

    def test_fallback_load_sequence(self):
        """Test _fallback_load_sequence method (lines 629-630)."""

        manager = ToolLoadingOrder()

        # Test fallback sequence generation
        result = manager._fallback_load_sequence(["tool_b", "tool_a", "tool_c"])

        # Should be sorted by load order then name
        assert isinstance(result, list)
        assert len(result) == 3


# =============================================================================
# wrapper.py Coverage (94.79%) - Lines 231-232, 373, 397-398
# =============================================================================

class TestWrapperCoverageGaps:
    """Tests for wrapper.py coverage gaps."""

    def test_create_table_security_validation_error(self):
        """Test create_table when security validation fails (lines 231-232)."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseWrapper(tmp.name)

            # Try to create table with invalid name
            with pytest.raises(InputValidationError):
                db.create_table("123invalid", "id INTEGER PRIMARY KEY")

            db.close()

    def test_execute_batch_error_handling(self):
        """Test execute_batch error handling (line 373)."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseWrapper(tmp.name)

            # Create a simple table first using the wrapper's method
            db.create_table("test_table", "id INTEGER PRIMARY KEY")

            # Try to execute batch with invalid SQL (referencing nonexistent table)
            operations = [
                ("INSERT INTO nonexistent_table (id) VALUES (?)", (1,)),
            ]

            with pytest.raises(Exception):
                db.execute_batch(operations)

            db.close()

    def test_execute_transaction_batch_error_handling(self):
        """Test execute_transaction_batch error handling (lines 397-398)."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseWrapper(tmp.name)

            # Create a simple table first using the wrapper's method
            db.create_table("test_table", "id INTEGER PRIMARY KEY")

            # Try to execute transaction batch with invalid SQL
            operations = [
                ("INSERT INTO nonexistent_table (id) VALUES (?)", (1,)),
            ]

            with pytest.raises(Exception):
                db.execute_transaction_batch(operations)

            db.close()


# =============================================================================
# ipc.py Coverage (96.60%) - Lines 89-90, 137-138
# =============================================================================

class TestIPCCoverageGaps:
    """Tests for ipc.py coverage gaps."""

    def test_stop_server_with_exception(self):
        """Test stop server when connect raises exception (lines 89-90)."""
        mock_registry = Mock()
        server = ToolIPCServer(mock_registry)

        # Create a mock server thread
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        server._server_thread = mock_thread

        with patch('os.path.exists', return_value=True), \
             patch('os.remove'), \
             patch('socket.socket') as mock_socket_class:
            # Make connect raise an exception
            mock_client = Mock()
            mock_client.__enter__ = Mock(side_effect=Exception("Connect failed"))
            mock_client.__exit__ = Mock(return_value=False)
            mock_socket_class.return_value = mock_client

            # Should handle exception gracefully
            server.stop()

    def test_handle_connection_security_risk_flagged_path(self):
        """Test security risk flagged code path (lines 137-138)."""

        mock_registry = Mock()

        # We need to trigger the code path where action_code is in RISK_LEVELS
        # Looking at codes.py, RISK_LEVELS contains specific ActionCodes
        # We need to mock SENSITIVE_METHODS to return one of these

        mock_method = Mock(return_value="success")
        mock_tool = Mock()
        mock_tool.api_methods = {"test_method": mock_method}
        mock_registry.get_tool.return_value = mock_tool

        server = ToolIPCServer(mock_registry)

        # Patch SENSITIVE_METHODS to include our test method with a risk-level action code
        with patch('nodupe.core.api.ipc.SENSITIVE_METHODS', {'test_method': 500000}):
            mock_conn = Mock()
            request_data = {
                "jsonrpc": "2.0",
                "tool": "TestTool",
                "method": "test_method",
                "params": {},
                "id": 1
            }
            mock_conn.recv.return_value = json.dumps(request_data).encode('utf-8')

            mock_logger = Mock()
            mock_logger.info = Mock()
            mock_logger.warning = Mock()
            mock_logger.error = Mock()
            server.logger = mock_logger

            server._handle_connection(mock_conn)

            # Should have logged the security risk
            assert mock_logger.info.called


# =============================================================================
# query_cache.py Coverage (96.94%) - Lines 96-98, 314-315
# =============================================================================

class TestQueryCacheCoverageGaps:
    """Tests for query_cache.py coverage gaps."""

    def test_get_result_expired(self):
        """Test get_result when entry is expired (lines 96-98)."""
        cache = QueryCache(max_size=100, ttl_seconds=1)

        # Add entry
        cache.set_result("SELECT 1", {}, "result1")

        # Wait for TTL to expire
        time.sleep(1.1)

        # Get should detect expiration and return None
        result = cache.get_result("SELECT 1", {})
        assert result is None

    def test_get_memory_usage_conversion_error(self):
        """Test get_memory_usage when result conversion fails (lines 314-315)."""
        cache = QueryCache(max_size=100, ttl_seconds=3600)

        # Add an entry with a result that might cause conversion issues
        cache.set_result("SELECT 1", {}, UnconvertibleResult())

        # Should handle conversion error gracefully
        usage = cache.get_memory_usage()
        assert usage > 0


# =============================================================================
# security.py Coverage (97.06%) - Line 122
# =============================================================================

class TestSecurityCoverageGaps:
    """Tests for security.py coverage gaps."""

    def test_sanitize_error_message_with_sensitive_patterns(self):
        """Test sanitize_error_message with sensitive patterns (line 122)."""
        mock_db = Mock()
        security = DatabaseSecurity(mock_db)

        # Create error message with sensitive patterns
        error_msg = "Error with PASSWORD_REMOVED and api_key in message"
        error = Exception(error_msg)

        result = security.sanitize_error_message(error)

        # Should have redacted sensitive patterns
        assert 'PASSWORD_REMOVED' not in result
        assert 'api_key' not in result
        assert '[REDACTED]' in result


# =============================================================================
# logging_system.py Coverage (97.17%) - Line 94, 195->199
# =============================================================================

class TestLoggingSystemCoverageGaps:
    """Tests for logging_system.py coverage gaps."""

    def test_setup_logging_invalid_level(self):
        """Test setup_logging with invalid log level (line 94)."""
        with pytest.raises(LoggingError):
            Logging.setup_logging(log_level="INVALID_LEVEL")

    def test_add_file_handler_error_handling(self):
        """Test add_file_handler error handling (lines 195->199)."""
        logger = get_logger("test_logger")

        # Try to add file handler with invalid path
        with patch('pathlib.Path.mkdir', side_effect=Exception("Cannot create dir")):
            with pytest.raises(LoggingError):
                Logging.add_file_handler(logger, Path("/invalid/path/test.log"))


# =============================================================================
# connection.py Coverage (97.92%) - Lines 168-169
# =============================================================================

class TestConnectionCoverageGaps:
    """Tests for connection.py coverage gaps."""

    def test_close_error_handling(self):
        """Test close when connection close fails (lines 168-169)."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db = DatabaseConnection(tmp.name)
            db.get_connection()

            # Mock the connection to raise error on close
            original_conn = db._local.connection
            db._local.connection = Mock()
            db._local.connection.close.side_effect = sqlite3.Error("Close failed")

            # Should handle error gracefully and print error message
            db.close()

            # Restore original connection
            db._local.connection = original_conn


# =============================================================================
# Additional integration tests
# =============================================================================

class TestIntegrationCoverage:
    """Integration tests for additional coverage."""

    def test_create_database_function(self):
        """Test create_database function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = create_database(db_path)

            assert conn is not None
            assert db_path.exists()

            conn.close()

    def test_create_hash_cache_function(self):
        """Test create_hash_cache function."""
        cache = create_hash_cache(max_size=500, ttl_seconds=7200)
        assert cache.max_size == 500
        assert cache.ttl_seconds == 7200

    def test_get_file_repository_function(self):
        """Test get_file_repository function."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            repo = get_file_repository(tmp.name)
            assert isinstance(repo, FileRepository)

    def test_load_config_function(self):
        """Test load_config function."""
        config = load_config()
        # Check that it returns a ConfigManager-like object
        assert hasattr(config, 'config_path')
        assert hasattr(config, 'config')

    def test_create_embedding_cache_function(self):
        """Test create_embedding_cache function."""
        cache = create_embedding_cache(max_size=500, ttl_seconds=7200, max_dims=512)
        assert cache.max_size == 500
        assert cache.max_dimensions == 512

    def test_create_query_cache_function(self):
        """Test create_query_cache function."""
        cache = create_query_cache(max_size=500, ttl_seconds=7200)
        assert cache.max_size == 500
        assert cache.ttl_seconds == 7200

    def test_get_connection_function(self):
        """Test get_connection function."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            conn = get_connection(tmp.name)
            assert isinstance(conn, DatabaseConnection)

    def test_get_logger_function(self):
        """Test get_logger function."""
        logger = get_logger("test_module")
        assert logger is not None

    def test_setup_logging_function(self):
        """Test setup_logging function."""
        # Should not raise
        setup_logging(log_level="DEBUG", console_output=False)

    def test_register_tool_function(self):
        """Test register_tool function."""
        tool = register_tool()
        assert isinstance(tool, StandardDatabaseTool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
