"""Database Sharding Tool.

Provides database sharding functionality for horizontal data partitioning.

Key Features:
    - Horizontal data partitioning
    - Multiple shard management
    - SQLite-based shards

Dependencies:
    - sqlite3 (standard library)
    - os (standard library)
    - typing (standard library)
"""

import sqlite3
import os
from typing import List, Optional, Dict, Any
import re

from nodupe.core.tool_system import Tool, ToolMetadata


class DatabaseShardingTool(Tool):
    """Database sharding functionality tool.
    
    Provides horizontal data partitioning through database sharding,
    allowing data to be distributed across multiple database files.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the database sharding tool.
        
        Args:
            config: Configuration dictionary with optional 'db_path' key
        """
        super().__init__()
        self.config = config or {}
        self._shards = {}

    @property
    def name(self) -> str:
        """Get tool name.
        
        Returns:
            Tool name identifier
        """
        return "DatabaseSharding"

    @property
    def version(self) -> str:
        """Get tool version.
        
        Returns:
            Version string in semver format
        """
        return "1.0.0"

    @property
    def dependencies(self) -> List[str]:
        """Get tool dependencies.
        
        Returns:
            List of dependency names
        """
        return []

    def get_capabilities(self) -> Dict[str, Any]:
        """Get tool capabilities.
        
        Returns:
            Dictionary of capability flags
        """
        return {
            "sharding": True,
            "horizontal_partitioning": True,
            "create_shard": True,
        }

    @property
    def metadata(self) -> ToolMetadata:
        """Get tool metadata.

        Returns:
            ToolMetadata object with tool information
        """
        return ToolMetadata(
            name=self.name,
            version=self.version,
            software_id="org.nodupe.tool.database-sharding",
            description="Database sharding functionality for horizontal data partitioning",
            author="NoDupeLabs",
            license="Apache-2.0",
            dependencies=self.dependencies,
            tags=["database", "sharding", "partitioning"]
        )

    def create_shard(self, shard_name: str, db_path: Optional[str] = None) -> str:
        """Create a new database shard.
        
        Args:
            shard_name: Name for the new shard
            db_path: Optional path for the shard database file
            
        Returns:
            Path to the created shard database
            
        Raises:
            ValueError: If shard name is invalid
        """
        if not self._is_valid_identifier(shard_name):
            raise ValueError(f"Invalid shard name: {shard_name}")

        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(self.config.get('db_path', '.')), 
                f"{shard_name}.db"
            )

        shard_conn = sqlite3.connect(db_path)
        try:
            shard_conn.execute("""
                CREATE TABLE IF NOT EXISTS shard_data (
                    id INTEGER PRIMARY KEY,
                    key TEXT UNIQUE,
                    value BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            shard_conn.commit()
        finally:
            shard_conn.close()

        self._shards[shard_name] = db_path
        return db_path

    def _is_valid_identifier(self, name: str) -> bool:
        """Check if a name is a valid identifier.
        
        Args:
            name: Name to validate
            
        Returns:
            True if valid identifier, False otherwise
        """
        if not name or not isinstance(name, str):
            return False
        if name.startswith('_'):
            return False
        if len(name) > 64:
            return False
        # Restrict to ASCII letters, numbers, underscores and hyphens only
        return bool(re.match(r'^[A-Za-z0-9_-]+$', name))

    def list_shards(self) -> List[str]:
        """List all created shards.
        
        Returns:
            List of shard names
        """
        return list(self._shards.keys())

    def initialize(self, container: Any) -> None:
        """Initialize the tool and register services.

        Args:
            container: Service container to register with
        """
        pass

    def shutdown(self) -> None:
        """Shutdown the tool and cleanup resources."""
        pass

    @property
    def api_methods(self) -> Dict[str, Any]:
        """Dictionary of methods exposed via programmatic API."""
        return {
            'create_shard': self.create_shard,
            'list_shards': self.list_shards,
        }

    def run_standalone(self, args: list[str]) -> int:
        """Execute the tool in stand-alone mode without raising SystemExit.

        This avoids argparse.exit() during tests by handling args manually.
        """
        if not args:
            print("Usage: Database Sharding Tool - create <name> | list")
            return 1

        cmd = args[0]
        if cmd == 'list':
            shards = self.list_shards()
            print('\n'.join(shards) if shards else '')
            return 0

        if cmd == 'create':
            # Accept either `create <name>` or `create --name <name>`
            name = None
            if len(args) >= 2 and not args[1].startswith('-'):
                name = args[1]
            else:
                # parse flags manually
                for i, a in enumerate(args[1:], start=1):
                    if a in ('--name', '-n') and i + 1 < len(args):
                        name = args[i + 1]
                        break

            if not name:
                print("Usage: create <name>")
                return 1

            try:
                self.create_shard(name, None)
                print(f"Created shard: {name}")
                return 0
            except Exception as exc:
                print(str(exc))
                return 1

        print("Unknown command")
        return 1

    def describe_usage(self) -> str:
        """Return human-readable usage description."""
        return "Database Sharding Tool: Manages horizontal data partitioning across multiple SQLite databases. Use 'create --name <shard>' to create a new shard or 'list' to see existing shards."
