# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 NoDupeLabs

"""Tests to achieve 100% coverage on database_tool.py module.

This test file targets the missing coverage in:
- database_tool.py: StandardDatabaseTool class methods
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.databases.database_tool import (
    StandardDatabaseTool,
    register_tool,
)


class TestStandardDatabaseToolInit:
    """Tests for StandardDatabaseTool initialization."""

    def test_init_creates_database(self):
        """Test initialization creates DatabaseConnection."""
        with patch('nodupe.tools.databases.database_tool.DatabaseConnection'):
            tool = StandardDatabaseTool()
            assert tool.db is not None


class TestToolProperties:
    """Tests for tool property attributes."""

    def test_name_property(self):
        """Test name property returns correct value."""
        with patch('nodupe.tools.databases.database_tool.DatabaseConnection'):
            tool = StandardDatabaseTool()
            assert tool.name == "database_standard"

    def test_version_property(self):
        """Test version property returns correct value."""
        with patch('nodupe.tools.databases.database_tool.DatabaseConnection'):
            tool = StandardDatabaseTool()
            assert tool.version == "1.0.0"

    def test_dependencies_property(self):
        """Test dependencies property returns empty list."""
        with patch('nodupe.tools.databases.database_tool.DatabaseConnection'):
            tool = StandardDatabaseTool()
            assert tool.dependencies == []
            assert isinstance(tool.dependencies, list)

    def test_metadata_property(self):
        """Test metadata property returns ToolMetadata."""
        with patch('nodupe.tools.databases.database_tool.DatabaseConnection'):
            tool = StandardDatabaseTool()
            metadata = tool.metadata

            assert metadata.name == "database_standard"
            assert metadata.version == "1.0.0"
            assert metadata.author == "NoDupeLabs"
            assert metadata.license == "Apache-2.0"
            assert "database" in metadata.tags
            assert "sqlite" in metadata.tags
            assert "storage" in metadata.tags

    def test_metadata_software_id(self):
        """Test metadata software_id format."""
        with patch('nodupe.tools.databases.database_tool.DatabaseConnection'):
            tool = StandardDatabaseTool()
            assert tool.metadata.software_id == "org.nodupe.tool.database_standard"


class TestApiMethods:
    """Tests for api_methods property."""

    def test_api_methods_returns_dict(self):
        """Test api_methods returns a dictionary."""
        with patch('nodupe.tools.databases.database_tool.DatabaseConnection'):
            tool = StandardDatabaseTool()
            api_methods = tool.api_methods

            assert isinstance(api_methods, dict)

    def test_api_methods_contains_initialize(self):
        """Test api_methods contains initialize."""
        with patch('nodupe.tools.databases.database_tool.DatabaseConnection'):
            tool = StandardDatabaseTool()
            assert 'initialize' in tool.api_methods
            assert callable(tool.api_methods['initialize'])

    def test_api_methods_contains_get_connection(self):
        """Test api_methods contains get_connection."""
        with patch('nodupe.tools.databases.database_tool.DatabaseConnection'):
            tool = StandardDatabaseTool()
            assert 'get_connection' in tool.api_methods

    def test_api_methods_contains_close(self):
        """Test api_methods contains close."""
        with patch('nodupe.tools.databases.database_tool.DatabaseConnection'):
            tool = StandardDatabaseTool()
            assert 'close' in tool.api_methods


class TestInitialize:
    """Tests for initialize method."""

    def test_initialize_success(self):
        """Test successful initialization."""
        mock_db = MagicMock()
        mock_container = MagicMock()

        with patch('nodupe.tools.databases.database_tool.DatabaseConnection', return_value=mock_db):
            tool = StandardDatabaseTool()
            tool.initialize(mock_container)

            mock_db.initialize_database.assert_called_once()
            mock_container.register_service.assert_called_once_with('database', mock_db)

    def test_initialize_handles_exception(self):
        """Test initialize handles exceptions gracefully."""
        mock_db = MagicMock()
        mock_db.initialize_database.side_effect = Exception("DB init error")
        mock_container = MagicMock()

        with patch('nodupe.tools.databases.database_tool.DatabaseConnection', return_value=mock_db):
            with patch('logging.getLogger'):
                tool = StandardDatabaseTool()
                # Should not raise
                tool.initialize(mock_container)


class TestShutdown:
    """Tests for shutdown method."""

    def test_shutdown_calls_close(self):
        """Test shutdown calls close on database."""
        mock_db = MagicMock()

        with patch('nodupe.tools.databases.database_tool.DatabaseConnection', return_value=mock_db):
            tool = StandardDatabaseTool()
            tool.shutdown()

            mock_db.close.assert_called_once()


class TestRunStandalone:
    """Tests for run_standalone method."""

    def test_run_standalone_success(self):
        """Test successful standalone run."""
        mock_db = MagicMock()

        with patch('nodupe.tools.databases.database_tool.DatabaseConnection', return_value=mock_db):
            tool = StandardDatabaseTool()
            result = tool.run_standalone([])

            mock_db.initialize_database.assert_called_once()

    def test_run_standalone_error(self):
        """Test standalone run with error."""
        mock_db = MagicMock()
        mock_db.initialize_database.side_effect = Exception("DB error")

        with patch('nodupe.tools.databases.database_tool.DatabaseConnection', return_value=mock_db):
            tool = StandardDatabaseTool()
            result = tool.run_standalone([])

            assert result == 1


class TestDescribeUsage:
    """Tests for describe_usage method."""

    def test_describe_usage_returns_string(self):
        """Test describe_usage returns a string."""
        with patch('nodupe.tools.databases.database_tool.DatabaseConnection'):
            tool = StandardDatabaseTool()
            description = tool.describe_usage()

            assert isinstance(description, str)
            assert len(description) > 0
            assert "library" in description.lower() or "filing" in description.lower()


class TestGetCapabilities:
    """Tests for get_capabilities method."""

    def test_get_capabilities_returns_dict(self):
        """Test get_capabilities returns a dictionary."""
        mock_db = MagicMock()
        mock_db.db_path = "/test/path"

        with patch('nodupe.tools.databases.database_tool.DatabaseConnection', return_value=mock_db):
            tool = StandardDatabaseTool()
            capabilities = tool.get_capabilities()

            assert isinstance(capabilities, dict)

    def test_get_capabilities_contains_engine(self):
        """Test get_capabilities contains engine."""
        mock_db = MagicMock()
        mock_db.db_path = "/test/path"

        with patch('nodupe.tools.databases.database_tool.DatabaseConnection', return_value=mock_db):
            tool = StandardDatabaseTool()
            capabilities = tool.get_capabilities()

            assert 'engine' in capabilities
            assert capabilities['engine'] == 'SQLite'

    def test_get_capabilities_contains_path(self):
        """Test get_capabilities contains path."""
        mock_db = MagicMock()
        mock_db.db_path = "/test/path"

        with patch('nodupe.tools.databases.database_tool.DatabaseConnection', return_value=mock_db):
            tool = StandardDatabaseTool()
            capabilities = tool.get_capabilities()

            assert 'path' in capabilities

    def test_get_capabilities_contains_features(self):
        """Test get_capabilities contains features."""
        mock_db = MagicMock()
        mock_db.db_path = "/test/path"

        with patch('nodupe.tools.databases.database_tool.DatabaseConnection', return_value=mock_db):
            tool = StandardDatabaseTool()
            capabilities = tool.get_capabilities()

            assert 'features' in capabilities
            assert isinstance(capabilities['features'], list)


class TestRegisterTool:
    """Tests for register_tool function."""

    def test_register_tool_returns_instance(self):
        """Test register_tool returns a StandardDatabaseTool instance."""
        with patch('nodupe.tools.databases.database_tool.DatabaseConnection'):
            result = register_tool()

            assert isinstance(result, StandardDatabaseTool)

    def test_register_tool_creates_new_instance(self):
        """Test register_tool creates a new instance each call."""
        with patch('nodupe.tools.databases.database_tool.DatabaseConnection'):
            result1 = register_tool()
            result2 = register_tool()

            assert result1 is not result2


class TestMainExecution:
    """Tests for main execution path."""

    def test_main_execution(self):
        """Test __main__ execution."""
        with patch('nodupe.tools.databases.database_tool.DatabaseConnection'):
            with patch.object(sys, 'argv', ['database_tool.py']):
                import nodupe.tools.databases.database_tool as database_tool_module

                # Just verify it imports correctly
                assert hasattr(database_tool_module, 'StandardDatabaseTool')
