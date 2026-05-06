# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Coverage tests for nodupe/core/config.py."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from nodupe.core.config import ConfigManager, load_config


def test_config_manager_no_toml(capsys):
    """Test ConfigManager when toml is missing (lines 38-45)."""
    with patch("nodupe.core.config.toml", None):
        manager = ConfigManager()
        assert manager.config == {}
        captured = capsys.readouterr()
        assert "toml package not found" in captured.out

def test_config_manager_file_not_found():
    """Test ConfigManager when file is missing (lines 49-56)."""
    # Default path missing should be empty dict
    with patch("os.path.exists", return_value=False):
        manager = ConfigManager("pyproject.toml")
        assert manager.config == {}

    # Explicit path missing should raise
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            ConfigManager("missing.toml")

def test_config_manager_parsing_error():
    """Test ConfigManager parsing errors (lines 58-61)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as tf:
        tf.write("invalid = [toml")
        tf_path = tf.name

    try:
        with pytest.raises(ValueError, match="Error parsing TOML file"):
            ConfigManager(tf_path)
    finally:
        os.unlink(tf_path)

def test_config_manager_missing_section():
    """Test ConfigManager missing [tool.nodupe] section (lines 63-64)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as tf:
        tf.write("[other]\nkey = 'value'")
        tf_path = tf.name

    try:
        with pytest.raises(ValueError, match=r"missing \[tool.nodupe\] section"):
            ConfigManager(tf_path)
    finally:
        os.unlink(tf_path)

def test_config_getters():
    """Test all configuration getters (lines 69-92)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as tf:
        tf.write("""
[tool.nodupe]
version = "1.0.0"
[tool.nodupe.database]
path = "test.db"
[tool.nodupe.scan]
opt = 1
[tool.nodupe.similarity]
opt = 2
[tool.nodupe.performance]
opt = 3
[tool.nodupe.logging]
opt = 4
""")
        tf_path = tf.name

    try:
        manager = ConfigManager(tf_path)
        assert manager.get_database_config()["path"] == "test.db"
        assert manager.get_scan_config()["opt"] == 1
        assert manager.get_similarity_config()["opt"] == 2
        assert manager.get_performance_config()["opt"] == 3
        assert manager.get_logging_config()["opt"] == 4
        assert manager.get_config_value("database", "path") == "test.db"
        assert manager.get_config_value("none", "key", "def") == "def"

        # Test get_nodupe_config error handling (line 72)
        manager.config = None # Cause error
        assert manager.get_nodupe_config() == {}

    finally:
        os.unlink(tf_path)

def test_get_config_value_error():
    """Test get_config_value error handling (lines 105-108)."""
    manager = ConfigManager()
    manager.config = {"tool": {"nodupe": None}} # Cause TypeError in .get()
    assert manager.get_config_value("section", "key", "default") == "default"

def test_validate_config():
    """Test validate_config (lines 116-127)."""
    manager = ConfigManager()
    manager.config = {"tool": {"nodupe": {}}}
    assert manager.validate_config() is False # Missing sections

    manager.config["tool"]["nodupe"] = {
        "database": {}, "scan": {}, "similarity": {}, "performance": {}, "logging": {}
    }
    assert manager.validate_config() is True

def test_load_config_helper():
    """Test load_config helper function (line 139)."""
    with patch("os.path.exists", return_value=False):
        manager = load_config()
        assert isinstance(manager, ConfigManager)
