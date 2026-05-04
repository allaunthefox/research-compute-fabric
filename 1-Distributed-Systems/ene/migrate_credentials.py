#!/usr/bin/env python3
import sys
from pathlib import Path
import json

# Add infra to path
sys.path.insert(0, str(Path(__file__).parent.parent / "infra"))

from ene_api import ENEAPIHook, AccessLevel
from ene_cloud_credential_manager import ENECloudCredentialManager

def migrate():
    api = ENEAPIHook()
    mgr = ENECloudCredentialManager()
    
    # Migrate Linear
    print("Migrating Linear credentials...")
    res = api.retrieve_sensitive_data("credentials/linear", AccessLevel.SECRET)
    if res.get("success"):
        key = res["payload"]
        print(f"  Retrieved Linear key (len: {len(key)})")
        cred_id = mgr.store_credential(
            provider="linear",
            api_key=key,
            secret="",
            node_assignments=["mcp_server_node"]
        )
        print(f"  Stored in ENE: {cred_id}")
    else:
        print(f"  Failed to retrieve Linear: {res.get('error')}")
        
    # Migrate Notion
    print("\nMigrating Notion credentials...")
    res = api.retrieve_sensitive_data("credentials/notion", AccessLevel.SECRET)
    if res.get("success"):
        key = res["payload"]
        print(f"  Retrieved Notion key (len: {len(key)})")
        
        # Get database ID if available
        db_res = api.retrieve_sensitive_data("credentials/notion_database_id", AccessLevel.SECRET)
        db_id = db_res.get("payload", "") if db_res.get("success") else ""
        
        cred_id = mgr.store_credential(
            provider="notion",
            api_key=key,
            secret=json.dumps({"database_id": db_id}),
            node_assignments=["mcp_server_node"]
        )
        print(f"  Stored in ENE: {cred_id}")
    else:
        print(f"  Failed to retrieve Notion: {res.get('error')}")

if __name__ == "__main__":
    migrate()
