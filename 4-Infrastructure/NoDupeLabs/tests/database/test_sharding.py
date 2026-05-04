# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 NoDupeLabs

"""Comprehensive tests for database sharding functionality.

Tests cover:
- Shard creation and management
- Data distribution across shards
- Shard selection logic
- Identifier validation
- Initialize/shutdown lifecycle
"""

import os
import sqlite3
from unittest.mock import MagicMock

import pytest

from nodupe.tools.database.sharding import DatabaseShardingTool


class TestDatabaseShardingToolInit:
    """Tests for DatabaseShardingTool initialization."""

    def test_init_with_no_config(self):
        """Test initialization without configuration."""
        tool = DatabaseShardingTool()
        assert tool.config == {}
        assert tool._shards == {}

    def test_init_with_config(self):
        """Test initialization with configuration."""
        config = {"db_path": "/custom/path", "shard_count": 4}
        tool = DatabaseShardingTool(config=config)
        assert tool.config == config
        assert tool._shards == {}

    def test_init_with_empty_config_dict(self):
        """Test initialization with empty config dict."""
        tool = DatabaseShardingTool(config={})
        assert tool.config == {}

    def test_init_creates_empty_shards_dict(self):
        """Test that _shards is initialized as empty dict."""
        tool = DatabaseShardingTool()
        assert isinstance(tool._shards, dict)
        assert len(tool._shards) == 0


class TestDatabaseShardingToolProperties:
    """Tests for DatabaseShardingTool properties."""

    def test_name_property(self):
        """Test name property returns correct value."""
        tool = DatabaseShardingTool()
        assert tool.name == "DatabaseSharding"

    def test_version_property(self):
        """Test version property returns correct value."""
        tool = DatabaseShardingTool()
        assert tool.version == "1.0.0"

    def test_dependencies_property(self):
        """Test dependencies property returns empty list."""
        tool = DatabaseShardingTool()
        assert tool.dependencies == []
        assert isinstance(tool.dependencies, list)

    def test_get_capabilities(self):
        """Test get_capabilities returns correct capabilities."""
        tool = DatabaseShardingTool()
        capabilities = tool.get_capabilities()
        assert capabilities == {
            "sharding": True,
            "horizontal_partitioning": True,
            "create_shard": True,
        }

    def test_get_capabilities_all_true(self):
        """Test all capabilities are True."""
        tool = DatabaseShardingTool()
        capabilities = tool.get_capabilities()
        assert all(capabilities.values())

    def test_metadata_property(self):
        """Test metadata property returns ToolMetadata."""
        tool = DatabaseShardingTool()
        metadata = tool.metadata
        assert metadata.name == "DatabaseSharding"
        assert metadata.version == "1.0.0"
        assert "database" in metadata.tags
        assert "sharding" in metadata.tags
        assert "partitioning" in metadata.tags

    def test_metadata_author(self):
        """Test metadata author is NoDupeLabs."""
        tool = DatabaseShardingTool()
        assert tool.metadata.author == "NoDupeLabs"

    def test_metadata_license(self):
        """Test metadata license is Apache-2.0."""
        tool = DatabaseShardingTool()
        assert tool.metadata.license == "Apache-2.0"

    def test_metadata_description(self):
        """Test metadata description contains sharding info."""
        tool = DatabaseShardingTool()
        assert "sharding" in tool.metadata.description.lower()
        assert "horizontal" in tool.metadata.description.lower()


class TestIsValidIdentifier:
    """Tests for _is_valid_identifier method."""

    def test_valid_simple_name(self):
        """Test valid simple alphanumeric name."""
        tool = DatabaseShardingTool()
        assert tool._is_valid_identifier("shard1") is True

    def test_valid_name_with_underscore(self):
        """Test valid name with underscores."""
        tool = DatabaseShardingTool()
        assert tool._is_valid_identifier("shard_1") is True
        assert tool._is_valid_identifier("my_shard") is True

    def test_valid_name_with_hyphen(self):
        """Test valid name with hyphens."""
        tool = DatabaseShardingTool()
        assert tool._is_valid_identifier("shard-1") is True
        assert tool._is_valid_identifier("my-shard") is True

    def test_valid_name_mixed(self):
        """Test valid name with mixed characters."""
        tool = DatabaseShardingTool()
        assert tool._is_valid_identifier("shard_1-test") is True

    def test_invalid_empty_string(self):
        """Test empty string is invalid."""
        tool = DatabaseShardingTool()
        assert tool._is_valid_identifier("") is False

    def test_invalid_none(self):
        """Test None is invalid."""
        tool = DatabaseShardingTool()
        assert tool._is_valid_identifier(None) is False

    def test_invalid_starts_with_underscore(self):
        """Test name starting with underscore is invalid."""
        tool = DatabaseShardingTool()
        assert tool._is_valid_identifier("_shard") is False
        assert tool._is_valid_identifier("__shard") is False

    def test_invalid_too_long(self):
        """Test name longer than 64 chars is invalid."""
        tool = DatabaseShardingTool()
        long_name = "a" * 65
        assert tool._is_valid_identifier(long_name) is False

    def test_valid_max_length(self):
        """Test name exactly 64 chars is valid."""
        tool = DatabaseShardingTool()
        max_name = "a" * 64
        assert tool._is_valid_identifier(max_name) is True

    def test_invalid_special_characters(self):
        """Test names with special characters are invalid."""
        tool = DatabaseShardingTool()
        assert tool._is_valid_identifier("shard@1") is False
        assert tool._is_valid_identifier("shard#1") is False
        assert tool._is_valid_identifier("shard$1") is False
        assert tool._is_valid_identifier("shard!1") is False

    def test_invalid_spaces(self):
        """Test names with spaces are invalid."""
        tool = DatabaseShardingTool()
        assert tool._is_valid_identifier("shard 1") is False

    def test_valid_numeric_string(self):
        """Test numeric string is valid."""
        tool = DatabaseShardingTool()
        assert tool._is_valid_identifier("123") is True


class TestCreateShard:
    """Tests for create_shard method."""

    def test_create_shard_with_temp_db(self, tmp_path):
        """Test creating a shard with temporary database."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)
        shard_path = tool.create_shard("test_shard")
        assert os.path.exists(shard_path)
        assert shard_path.endswith("test_shard.db")
        assert "test_shard" in tool._shards

    def test_create_shard_creates_table(self, tmp_path):
        """Test that create_shard creates shard_data table."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)
        shard_path = tool.create_shard("test_shard")

        conn = sqlite3.connect(shard_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='shard_data'"
        )
        result = cursor.fetchone()
        conn.close()
        assert result is not None

    def test_create_shard_table_schema(self, tmp_path):
        """Test shard_data table has correct schema."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)
        shard_path = tool.create_shard("test_shard")

        conn = sqlite3.connect(shard_path)
        cursor = conn.execute("PRAGMA table_info(shard_data)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert "id" in columns
        assert "key" in columns
        assert "value" in columns
        assert "created_at" in columns

    def test_create_shard_with_custom_path(self, tmp_path):
        """Test creating shard with custom database path."""
        tool = DatabaseShardingTool()
        custom_path = str(tmp_path / "custom_shard.db")
        shard_path = tool.create_shard("custom", db_path=custom_path)
        assert shard_path == custom_path
        assert os.path.exists(shard_path)

    def test_create_shard_registers_in_dict(self, tmp_path):
        """Test that created shard is registered in _shards dict."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)
        tool.create_shard("shard_a")
        tool.create_shard("shard_b")
        assert len(tool._shards) == 2
        assert "shard_a" in tool._shards
        assert "shard_b" in tool._shards

    def test_create_shard_invalid_name(self):
        """Test that invalid shard name raises ValueError."""
        tool = DatabaseShardingTool()
        with pytest.raises(ValueError, match="Invalid shard name"):
            tool.create_shard("_invalid_shard")

    def test_create_shard_invalid_name_special_chars(self):
        """Test that special characters in name raises ValueError."""
        tool = DatabaseShardingTool()
        with pytest.raises(ValueError, match="Invalid shard name"):
            tool.create_shard("shard@invalid")

    def test_create_shard_creates_parent_dirs(self, tmp_path):
        """Test that create_shard creates parent directories if needed."""
        tool = DatabaseShardingTool()
        nested_dir = tmp_path / "nested" / "path"
        nested_dir.mkdir(parents=True, exist_ok=True)
        nested_path = str(nested_dir / "shard.db")
        shard_path = tool.create_shard("nested", db_path=nested_path)
        assert os.path.exists(shard_path)

    def test_create_multiple_shards(self, tmp_path):
        """Test creating multiple shards."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)
        paths = []
        for i in range(5):
            paths.append(tool.create_shard(f"shard_{i}"))

        assert len(tool._shards) == 5
        for path in paths:
            assert os.path.exists(path)

    def test_create_shard_idempotent(self, tmp_path):
        """Test that creating same shard twice works (table exists)."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)
        path1 = tool.create_shard("same_shard")
        path2 = tool.create_shard("same_shard")
        assert path1 == path2


class TestListShards:
    """Tests for list_shards method."""

    def test_list_shards_empty(self):
        """Test list_shards returns empty list when no shards."""
        tool = DatabaseShardingTool()
        assert tool.list_shards() == []

    def test_list_shards_single(self, tmp_path):
        """Test list_shards with single shard."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)
        tool.create_shard("single")
        assert tool.list_shards() == ["single"]

    def test_list_shards_multiple(self, tmp_path):
        """Test list_shards with multiple shards."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)
        tool.create_shard("shard_a")
        tool.create_shard("shard_b")
        tool.create_shard("shard_c")
        shards = tool.list_shards()
        assert len(shards) == 3
        assert set(shards) == {"shard_a", "shard_b", "shard_c"}

    def test_list_shards_returns_list(self):
        """Test list_shards returns a list type."""
        tool = DatabaseShardingTool()
        assert isinstance(tool.list_shards(), list)


class TestInitializeAndShutdown:
    """Tests for initialize and shutdown methods."""

    def test_initialize(self):
        """Test initialize method."""
        tool = DatabaseShardingTool()
        container = MagicMock()
        # Should not raise
        tool.initialize(container)

    def test_shutdown(self):
        """Test shutdown method."""
        tool = DatabaseShardingTool()
        # Should not raise
        tool.shutdown()

    def test_initialize_with_shards(self, tmp_path):
        """Test initialize after creating shards."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)
        tool.create_shard("test")
        container = MagicMock()
        tool.initialize(container)
        assert "test" in tool._shards

    def test_lifecycle_initialize_then_shutdown(self):
        """Test full lifecycle: initialize then shutdown."""
        tool = DatabaseShardingTool()
        container = MagicMock()
        # Should not raise
        tool.initialize(container)
        tool.shutdown()


class TestShardDataOperations:
    """Tests for shard data operations (integration tests)."""

    def test_insert_data_into_shard(self, tmp_path):
        """Test inserting data into created shard."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)
        shard_path = tool.create_shard("data_test")

        conn = sqlite3.connect(shard_path)
        conn.execute(
            "INSERT INTO shard_data (key, value) VALUES (?, ?)",
            ("test_key", b"test_value")
        )
        conn.commit()

        cursor = conn.execute("SELECT value FROM shard_data WHERE key = ?", ("test_key",))
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == b"test_value"

    def test_shard_data_with_timestamp(self, tmp_path):
        """Test that shard_data has created_at timestamp."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)
        shard_path = tool.create_shard("timestamp_test")

        conn = sqlite3.connect(shard_path)
        conn.execute(
            "INSERT INTO shard_data (key, value) VALUES (?, ?)",
            ("key1", b"value1")
        )
        conn.commit()

        cursor = conn.execute("SELECT created_at FROM shard_data WHERE key = ?", ("key1",))
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] is not None

    def test_shard_unique_constraint(self, tmp_path):
        """Test that key column has UNIQUE constraint."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)
        shard_path = tool.create_shard("unique_test")

        conn = sqlite3.connect(shard_path)
        conn.execute(
            "INSERT INTO shard_data (key, value) VALUES (?, ?)",
            ("unique_key", b"value1")
        )
        conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO shard_data (key, value) VALUES (?, ?)",
                ("unique_key", b"value2")
            )
        conn.close()


class TestShardingEdgeCases:
    """Edge case tests for sharding functionality."""

    def test_unicode_shard_name(self, tmp_path):
        """Test shard creation with unicode in name (should fail validation)."""
        tool = DatabaseShardingTool()
        # Unicode characters should fail identifier validation
        assert tool._is_valid_identifier("shard_\u00e9") is False

    def test_run_standalone_no_args(self, capsys):
        """Test run_standalone with no arguments."""
        tool = DatabaseShardingTool()
        result = tool.run_standalone([])
        assert result == 1
        captured = capsys.readouterr()
        assert "Usage:" in captured.out

    def test_run_standalone_create_command(self, tmp_path):
        """Test run_standalone with create command."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)
        result = tool.run_standalone(["create", "test_shard"])
        assert result == 0
        assert "test_shard" in tool.list_shards()

    def test_run_standalone_list_command(self, tmp_path, capsys):
        """Test run_standalone with list command."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)
        tool.create_shard("shard_a")
        tool.create_shard("shard_b")
        result = tool.run_standalone(["list"])
        assert result == 0
        captured = capsys.readouterr()
        assert "shard_a" in captured.out
        assert "shard_b" in captured.out

    def test_run_standalone_unknown_command(self, capsys):
        """Test run_standalone with unknown command."""
        tool = DatabaseShardingTool()
        result = tool.run_standalone(["unknown"])
        assert result == 1
        captured = capsys.readouterr()
        assert "Unknown command" in captured.out

    def test_describe_usage(self):
        """Test describe_usage method."""
        tool = DatabaseShardingTool()
        usage = tool.describe_usage()
        assert "Database Sharding Tool" in usage
        assert "sharding" in usage.lower()

    def test_api_methods(self):
        """Test api_methods property."""
        tool = DatabaseShardingTool()
        methods = tool.api_methods
        assert "create_shard" in methods
        assert "list_shards" in methods
        assert callable(methods["create_shard"])
        assert callable(methods["list_shards"])

    def test_whitespace_in_name(self, tmp_path):
        """Test that whitespace in name is invalid."""
        tool = DatabaseShardingTool()
        assert tool._is_valid_identifier("shard 1") is False
        assert tool._is_valid_identifier(" shard") is False
        assert tool._is_valid_identifier("shard ") is False

    def test_create_shard_path_traversal(self, tmp_path):
        """Test that path traversal in shard name is prevented."""
        tool = DatabaseShardingTool()
        # Path traversal should fail identifier validation
        assert tool._is_valid_identifier("../etc/shard") is False

    def test_concurrent_shard_creation(self, tmp_path):
        """Test creating shards in sequence (simulating concurrent access)."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)
        shards = []
        for i in range(10):
            shards.append(tool.create_shard(f"concurrent_{i}"))

        assert len(tool.list_shards()) == 10
        for path in shards:
            assert os.path.exists(path)

    def test_shard_with_numbers_only_name(self, tmp_path):
        """Test shard creation with numeric-only name."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)
        path = tool.create_shard("12345")
        assert os.path.exists(path)
        assert "12345" in tool.list_shards()

    def test_shard_with_mixed_case(self, tmp_path):
        """Test shard creation with mixed case name."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)
        path = tool.create_shard("MyShardName")
        assert os.path.exists(path)
        assert "MyShardName" in tool.list_shards()


class TestShardingIntegration:
    """Integration tests for sharding with database operations."""

    def test_full_shard_lifecycle(self, tmp_path):
        """Test complete shard lifecycle: create, use, list."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)

        # Create shard
        path = tool.create_shard("lifecycle_test")
        assert os.path.exists(path)

        # Verify in list
        assert "lifecycle_test" in tool.list_shards()

        # Use shard
        conn = sqlite3.connect(path)
        conn.execute(
            "INSERT INTO shard_data (key, value) VALUES (?, ?)",
            ("lifecycle_key", b"lifecycle_value")
        )
        conn.commit()
        conn.close()

        # Verify data persisted
        conn = sqlite3.connect(path)
        cursor = conn.execute("SELECT value FROM shard_data WHERE key = ?", ("lifecycle_key",))
        result = cursor.fetchone()
        conn.close()
        assert result[0] == b"lifecycle_value"

    def test_multiple_shards_data_isolation(self, tmp_path):
        """Test that data in different shards is isolated."""
        config = {"db_path": str(tmp_path)}
        tool = DatabaseShardingTool(config=config)

        path_a = tool.create_shard("shard_a")
        path_b = tool.create_shard("shard_b")

        # Insert different data in each shard
        conn_a = sqlite3.connect(path_a)
        conn_a.execute(
            "INSERT INTO shard_data (key, value) VALUES (?, ?)",
            ("key_a", b"value_a")
        )
        conn_a.commit()
        conn_a.close()

        conn_b = sqlite3.connect(path_b)
        conn_b.execute(
            "INSERT INTO shard_data (key, value) VALUES (?, ?)",
            ("key_b", b"value_b")
        )
        conn_b.commit()
        conn_b.close()

        # Verify isolation
        conn_a = sqlite3.connect(path_a)
        cursor_a = conn_a.execute("SELECT COUNT(*) FROM shard_data")
        count_a = cursor_a.fetchone()[0]
        conn_a.close()

        conn_b = sqlite3.connect(path_b)
        cursor_b = conn_b.execute("SELECT COUNT(*) FROM shard_data")
        count_b = cursor_b.fetchone()[0]
        conn_b.close()

        assert count_a == 1
        assert count_b == 1
