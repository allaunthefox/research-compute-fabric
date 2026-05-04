import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from infra.ene_api import ENEAPIHook, AccessLevel

def _is_placeholder(value: str) -> bool:
    """Check if a value looks like a placeholder."""
    if not value:
        return True
    placeholders = ["your_", "change-me", "change_me", "placeholder", "example", "demo", "test", "fake"]
    lower = value.lower()
    return any(lower.startswith(p) or p in lower for p in placeholders)

def ingest_keys():
    print("🔒 Ingesting API keys from .env into ENE substrate...")

    # Load .env
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"   Loaded {env_file}")
    else:
        print(f"   No .env file found at {env_file}")

    notion_key = os.getenv("NOTION_API_KEY")
    linear_key = os.getenv("LINEAR_API_KEY")
    notion_db = os.getenv("NOTION_DATABASE_ID")
    ene_encryption_key = os.getenv("ENE_ENCRYPTION_KEY")

    warnings = []
    if not notion_key:
        warnings.append("NOTION_API_KEY is missing")
    elif _is_placeholder(notion_key):
        warnings.append(f"NOTION_API_KEY looks like a placeholder: {notion_key[:20]}...")

    if not linear_key:
        warnings.append("LINEAR_API_KEY is missing")
    elif _is_placeholder(linear_key):
        warnings.append(f"LINEAR_API_KEY looks like a placeholder: {linear_key[:20]}...")

    if not notion_db:
        warnings.append("NOTION_DATABASE_ID is missing")
    elif _is_placeholder(notion_db):
        warnings.append(f"NOTION_DATABASE_ID looks like a placeholder: {notion_db[:20]}...")

    if not ene_encryption_key:
        warnings.append("ENE_ENCRYPTION_KEY is missing (will derive from ENE_SECRET_KEY)")
    elif _is_placeholder(ene_encryption_key):
        warnings.append(f"ENE_ENCRYPTION_KEY looks like a placeholder: {ene_encryption_key[:20]}...")

    if warnings:
        print("\n⚠️  WARNINGS:")
        for w in warnings:
            print(f"   - {w}")
        print("   These placeholders will be encrypted and stored, but won't work with real APIs.")
        print("   Update .env with real values before ingesting if you need live API access.\n")

    if not (notion_key or linear_key):
        print("❌ Error: No API keys found in .env file.")
        return

    api = ENEAPIHook()

    # Securely store Notion key
    if notion_key:
        notion_result = api.store_sensitive_data(
            pkg="credentials/notion",
            payload=notion_key,
            classification=AccessLevel.SECRET
        )

        if notion_result.get("success"):
            print(f"✅ Notion API key securely anchored. ID: {notion_result['id']}")
        else:
            print(f"❌ Failed to anchor Notion key: {notion_result.get('error')}")

    # Securely store Linear key
    if linear_key:
        linear_result = api.store_sensitive_data(
            pkg="credentials/linear",
            payload=linear_key,
            classification=AccessLevel.SECRET
        )

        if linear_result.get("success"):
            print(f"✅ Linear API key securely anchored. ID: {linear_result['id']}")
        else:
            print(f"❌ Failed to anchor Linear key: {linear_result.get('error')}")

    # Securely store Notion DB ID as auxiliary data
    if notion_db:
        db_result = api.store_sensitive_data(
            pkg="credentials/notion_database_id",
            payload=notion_db,
            classification=AccessLevel.SECRET
        )
        if db_result.get("success"):
            print(f"✅ Notion database ID securely anchored. ID: {db_result['id']}")

    print("✅ ENE credential substrate hardened.")

if __name__ == "__main__":
    ingest_keys()
