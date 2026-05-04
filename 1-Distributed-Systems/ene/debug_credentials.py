#!/usr/bin/env python3
import sys
from pathlib import Path
import json
import sqlite3

# Add infra to path
sys.path.insert(0, str(Path(__file__).parent.parent / "infra"))

from ene_api import ENEAPIHook, AccessLevel, SECRET_KEY, SALT

def debug_retrieve():
    api = ENEAPIHook()
    
    db_path = "/home/allaun/Documents/Research Stack/data/substrate_index.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    pkgs = ["credentials/linear", "credentials/notion", "credentials/notion_database_id"]
    
    for pkg in pkgs:
        print(f"\nChecking pkg: {pkg}")
        cursor.execute("SELECT id, encrypted_payload, nonce, classification FROM sensitive_data WHERE pkg = ?", (pkg,))
        rows = cursor.fetchall()
        if not rows:
            print(f"  No rows found for {pkg}")
            continue
        
        print(f"  Found {len(rows)} rows")
        for row in rows:
            data_id, payload, nonce, classification = row
            print(f"  ID: {data_id}, Classification: {classification}")
            
            # Try to decrypt
            try:
                res = api.retrieve_sensitive_data(pkg, AccessLevel.SECRET)
                if res.get("success"):
                    print(f"  Decryption SUCCESS: {res['payload'][:5]}...")
                else:
                    print(f"  Decryption FAILED: {res.get('error')}")
            except Exception as e:
                print(f"  Decryption ERROR: {str(e)}")

    conn.close()

if __name__ == "__main__":
    debug_retrieve()
