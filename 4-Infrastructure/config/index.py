import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class Config:
    """Centralized configuration for Research Stack"""

    # Linear API
    linear_api_key: str
    linear_team_id: str = "3c8c51e6-3f24-4999-8fe6-3e097468bf6c"

    # Notion API
    notion_api_key: str
    notion_database_id: str

    # Environment
    node_env: str = "development"

    # ENE Security
    ene_secret_key: str
    ene_encryption_key: Optional[str] = None

    # Topological Engine (NoDupeLabs private connector)
    topological_engine_url: str = "http://localhost:3000"
    topological_engine_token: Optional[str] = None
    obsidian_vault_path: Optional[str] = None
    neo4j_uri: Optional[str] = None
    neo4j_user: Optional[str] = None
    neo4j_password: Optional[str] = None

    # Database paths
    substrate_index_db: str = "/home/allaun/Documents/Research Stack/data/substrate_index.db"
    math_entities_db: str = "/home/allaun/Documents/Research Stack/data/math_entities.db"

    @classmethod
    def load(cls) -> 'Config':
        """Load configuration from environment variables"""
        # Load .env file if it exists
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)

        # Required fields
        linear_api_key = os.getenv('LINEAR_API_KEY')
        if not linear_api_key:
            raise ValueError(
                "LINEAR_API_KEY is required. Set it in .env file.\n"
                "Copy .env.example to .env and add your API keys."
            )

        notion_api_key = os.getenv('NOTION_API_KEY')
        if not notion_api_key:
            raise ValueError(
                "NOTION_API_KEY is required. Set it in .env file.\n"
                "Copy .env.example to .env and add your API keys."
            )

        notion_database_id = os.getenv('NOTION_DATABASE_ID')
        if not notion_database_id:
            raise ValueError(
                "NOTION_DATABASE_ID is required. Set it in .env file.\n"
                "Copy .env.example to .env and add your API keys."
            )

        ene_secret_key = os.getenv('ENE_SECRET_KEY')
        if not ene_secret_key:
            raise ValueError(
                "ENE_SECRET_KEY is required. Set it in .env file.\n"
                "Copy .env.example to .env and add your API keys."
            )

        return cls(
            linear_api_key=linear_api_key,
            notion_api_key=notion_api_key,
            notion_database_id=notion_database_id,
            linear_team_id=os.getenv('LINEAR_TEAM_ID', '3c8c51e6-3f24-4999-8fe6-3e097468bf6c'),
            node_env=os.getenv('NODE_ENV', 'development'),
            ene_secret_key=ene_secret_key,
            ene_encryption_key=os.getenv('ENE_ENCRYPTION_KEY'),
            substrate_index_db=os.getenv('SUBSTRATE_INDEX_DB', '/home/allaun/Documents/Research Stack/data/substrate_index.db'),
            math_entities_db=os.getenv('MATH_ENTITIES_DB', '/home/allaun/Documents/Research Stack/data/math_entities.db'),
            topological_engine_url=os.getenv('TOPOLOGICAL_ENGINE_URL', 'http://localhost:3000'),
            topological_engine_token=os.getenv('TOPOLOGICAL_ENGINE_TOKEN'),
            obsidian_vault_path=os.getenv('OBSIDIAN_VAULT_PATH'),
            neo4j_uri=os.getenv('NEO4J_URI'),
            neo4j_user=os.getenv('NEO4J_USER'),
            neo4j_password=os.getenv('NEO4J_PASSWORD'),
        )

# Singleton instance
_config: Optional[Config] = None

def get_config() -> Config:
    """Get configuration singleton"""
    global _config
    if _config is None:
        _config = Config.load()
    return _config

def reload_config() -> Config:
    """Reload configuration (useful for testing)"""
    global _config
    _config = Config.load()
    return _config
