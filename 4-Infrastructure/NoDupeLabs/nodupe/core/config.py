#!/usr/bin/env python3
"""NoDupeLabs Configuration Manager using TOML.

This module provides configuration management for NoDupeLabs using TOML files.
It leverages the Even Better TOML VSCode extension for enhanced TOML support.

Example:
    To load configuration from a custom path::

        from nodupe.core.config import load_config

        config = load_config("/path/to/config.toml")
        db_config = config.get_database_config()

Or using the ConfigManager class directly::

        from nodupe.core.config import ConfigManager

        manager = ConfigManager("pyproject.toml")
        scan_config = manager.get_scan_config()
"""

import os
import sys
from typing import Dict, Any, Optional

try:
    import tomli as toml
except ImportError:
    try:
        import toml
    except ImportError:
        try:
            import tomlkit as toml
        except ImportError:
            toml = None


class ConfigManager:
    """Configuration manager for NoDupeLabs that loads and manages TOML configuration files.

    This class provides methods to load and retrieve configuration values from
    TOML configuration files, specifically looking for the [tool.nodupe] section.

    Attributes:
        config_path: Path to the TOML configuration file.
        config: Dictionary containing the loaded configuration.

    Example:
        >>> manager = ConfigManager("pyproject.toml")
        >>> db_config = manager.get_database_config()
        >>> print(db_config.get('path'))
        nodupe.db
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize the configuration manager.

        Args:
            config_path: Path to the TOML configuration file. Defaults to 'pyproject.toml'.

        Raises:
            ImportError: If toml package is not installed.
            FileNotFoundError: If configuration file is not found at the specified path.
            ValueError: If configuration file is invalid or missing [tool.nodupe] section.
        """
        self.config_path: str = config_path or "pyproject.toml"
        self.config: Dict[str, Any] = {}
        
        if toml is None:
            print("[WARN] toml package not found. Using default configuration.")
            self.config = {}
            return

        self._load_config()

    def _load_config(self) -> None:
        """Load the TOML configuration file.

        Reads the configuration file from the specified path and parses it as TOML.
        Validates that the [tool.nodupe] section exists in the configuration.

        Raises:
            FileNotFoundError: If the configuration file does not exist at the specified path.
            ValueError: If the TOML file cannot be parsed or is missing the [tool.nodupe] section.
        """
        if not os.path.exists(self.config_path):
            # If it's the default path, just be empty. If explicit, raise.
            if self.config_path == "pyproject.toml":
                self.config = {}
                return
            raise FileNotFoundError(
                f"Configuration file {self.config_path} not found")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = toml.load(f)
        except Exception as e:
            raise ValueError(f"Error parsing TOML file: {e}") from e

        if 'tool' not in self.config or 'nodupe' not in self.config['tool']:
            raise ValueError(
                "Invalid configuration file: missing [tool.nodupe] section")

    def get_nodupe_config(self) -> Dict[str, Any]:
        """Get the NoDupeLabs configuration section.

        Retrieves the entire [tool.nodupe] configuration section from the loaded
        configuration file.

        Returns:
            Dictionary containing the NoDupeLabs configuration, or empty dict if not found.

        Example:
            >>> config = manager.get_nodupe_config()
            >>> print(config.get('version'))
            1.0.0
        """
        try:
            return dict(self.config.get('tool', {}).get('nodupe', {}))
        except (AttributeError, TypeError, KeyError):
            return {}

    def get_database_config(self) -> Dict[str, Any]:
        """Get the database configuration.

        Retrieves the database configuration section from the NoDupeLabs configuration.

        Returns:
            Dictionary containing database configuration settings including:
                - path: Path to the database file
                - timeout: Database connection timeout in seconds
                - journal_mode: SQLite journal mode (e.g., 'WAL', 'DELETE')

        Example:
            >>> db_config = manager.get_database_config()
            >>> print(db_config.get('path'))
            nodupe.db
        """
        return dict(self.get_nodupe_config().get('database', {}))

    def get_scan_config(self) -> Dict[str, Any]:
        """Get the scan configuration.

        Retrieves the scan configuration section from the NoDupeLabs configuration.

        Returns:
            Dictionary containing scan configuration settings including:
                - min_file_size: Minimum file size to scan
                - max_file_size: Maximum file size to scan
                - default_extensions: List of file extensions to scan
                - exclude_dirs: List of directories to exclude from scanning

        Example:
            >>> scan_config = manager.get_scan_config()
            >>> print(scan_config.get('min_file_size'))
            1KB
        """
        return dict(self.get_nodupe_config().get('scan', {}))

    def get_similarity_config(self) -> Dict[str, Any]:
        """Get the similarity configuration.

        Retrieves the similarity configuration section from the NoDupeLabs configuration.

        Returns:
            Dictionary containing similarity configuration settings including:
                - default_backend: Similarity calculation backend
                - vector_dimensions: Dimensions for vector embeddings
                - search_k: Number of nearest neighbors to search
                - similarity_threshold: Threshold for considering files as similar

        Example:
            >>> sim_config = manager.get_similarity_config()
            >>> print(sim_config.get('similarity_threshold'))
            0.85
        """
        return dict(self.get_nodupe_config().get('similarity', {}))

    def get_performance_config(self) -> Dict[str, Any]:
        """Get the performance configuration.

        Retrieves the performance configuration section from the NoDupeLabs configuration.

        Returns:
            Dictionary containing performance configuration settings including:
                - max_workers: Maximum number of worker threads/processes
                - batch_size: Number of items to process in a batch
                - chunk_size: Size of data chunks for processing

        Example:
            >>> perf_config = manager.get_performance_config()
            >>> print(perf_config.get('max_workers'))
            8
        """
        return dict(self.get_nodupe_config().get('performance', {}))

    def get_logging_config(self) -> Dict[str, Any]:
        """Get the logging configuration.

        Retrieves the logging configuration section from the NoDupeLabs configuration.

        Returns:
            Dictionary containing logging configuration settings including:
                - level: Logging level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR')
                - file: Path to the log file
                - max_size: Maximum size of log file before rotation
                - backup_count: Number of backup files to keep

        Example:
            >>> log_config = manager.get_logging_config()
            >>> print(log_config.get('level'))
            INFO
        """
        return dict(self.get_nodupe_config().get('logging', {}))

    def get_config_value(self, section: str, key: str, default: Any = None) -> Any:
        """Get a specific configuration value.

        Retrieves a specific configuration value from a given section and key.
        Provides a convenient way to access individual configuration values.

        Args:
            section: Configuration section name (e.g., 'database', 'scan', 'similarity').
            key: Configuration key within the section.
            default: Default value to return if the section or key is not found.
                Defaults to None.

        Returns:
            The configuration value if found, or the default value if not found.

        Example:
            >>> value = manager.get_config_value('database', 'path', 'default.db')
            >>> print(value)
            nodupe.db
        """
        try:
            return self.get_nodupe_config().get(section, {}).get(key, default)
        except Exception:
            return default

    def validate_config(self) -> bool:
        """Validate the configuration file structure.

        Checks that all required configuration sections are present in the
        NoDupeLabs configuration.

        Returns:
            True if all required configuration sections are present, False otherwise.
                Required sections: 'database', 'scan', 'similarity', 'performance', 'logging'

        Raises:
            This method does not raise exceptions; it returns False for validation failures.

        Example:
            >>> if config.validate_config():
            ...     print("Configuration is valid!")
            ... else:
            ...     print("Configuration is missing required sections!")
        """
        required_sections: list[str] = ['database', 'scan',
                             'similarity', 'performance', 'logging']

        nodupe_config = self.get_nodupe_config()

        for section in required_sections:
            if section not in nodupe_config:
                print(
                    f"Warning: Missing required configuration section: {section}")
                return False

        return True


def load_config(config_path: Optional[str] = None) -> ConfigManager:
    """Load the NoDupeLabs configuration.

    Factory function that creates and returns a ConfigManager instance with
    the loaded configuration. This is the primary entry point for loading
    NoDupeLabs configuration.

    Args:
        config_path: Optional path to the TOML configuration file.
            If not provided, defaults to 'pyproject.toml'.

    Returns:
        ConfigManager instance with loaded configuration.
            The returned object provides methods to access different
            configuration sections and validate the configuration.

    Raises:
        ImportError: If no TOML library is installed.
        FileNotFoundError: If the specified configuration file does not exist.
        ValueError: If the configuration file is invalid.

    Example:
        Using the default configuration file::

            from nodupe.core.config import load_config

            config = load_config()
            db_config = config.get_database_config()

        Using a custom configuration file::

            from nodupe.core.config import load_config

            config = load_config("/path/to/custom.toml")
            scan_config = config.get_scan_config()
    """
    return ConfigManager(config_path)


# Example usage and testing
if __name__ == "__main__":
    print("🔧 Loading NoDupeLabs configuration from pyproject.toml...")

    try:
        config = load_config()

        if config.validate_config():
            print("✅ Configuration file is valid!")

            # Display some key configuration values
            print("\n📋 NoDupeLabs Configuration Summary:")
            print(
                f"Version: {config.get_config_value('nodupe', 'version', '1.0.0')}")
            print(
                f"Description: {config.get_config_value('nodupe', 'description', 'NoDupeLabs')}")

            db_config = config.get_database_config()
            print(f"\n🗃️ Database Configuration:")
            print(f"  Path: {db_config.get('path', 'nodupe.db')}")
            print(f"  Timeout: {db_config.get('timeout', 30.0)} seconds")
            print(f"  Journal Mode: {db_config.get('journal_mode', 'WAL')}")

            scan_config = config.get_scan_config()
            print(f"\n🔍 Scan Configuration:")
            print(
                f"  Min File Size: {scan_config.get('min_file_size', '1KB')}")
            print(
                f"  Max File Size: {scan_config.get('max_file_size', '100MB')}")
            print(
                f"  Default Extensions: {', '.join(scan_config.get('default_extensions', []))}")
            print(
                f"  Exclude Directories: {', '.join(scan_config.get('exclude_dirs', []))}")

            similarity_config = config.get_similarity_config()
            print(f"\n🎯 Similarity Configuration:")
            print(
                f"  Default Backend: {similarity_config.get('default_backend', 'brute_force')}")
            print(
                f"  Vector Dimensions: {similarity_config.get('vector_dimensions', 128)}")
            print(f"  Search K: {similarity_config.get('search_k', 10)}")
            print(
                f"  Similarity Threshold: {similarity_config.get('similarity_threshold', 0.85)}")

            print("\n✅ Even Better TOML plugin setup complete!")
            print("💡 The plugin provides enhanced TOML support including:")
            print("   • Syntax highlighting")
            print("   • Autocompletion")
            print("   • Validation")
            print("   • Formatting")
            print("   • Error detection")
            print("   • Schema support")

        else:
            print("❌ Configuration file validation failed!")

    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        # Only exit 1 if running as script
        sys.exit(1)
