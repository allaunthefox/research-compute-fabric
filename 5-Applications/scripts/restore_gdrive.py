#!/usr/bin/env python3
"""
restore_gdrive.py — Restore Google Drive access and re-ingest into ENE.

Steps:
    1. Test current rclone Gdrive: remote
    2. If token is dead, print re-auth instructions
    3. If token works, extract credentials and re-ingest into ENE substrate
    4. Verify ENE can decrypt the new credentials

Usage:
    # If gdrive token is dead, re-auth first:
    rclone config reconnect Gdrive:
    
    # Then run:
    python3 5-Applications/scripts/restore_gdrive.py
"""

import sys
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime

# Load .env
project_root = Path(__file__).parent.parent.parent
try:
    from dotenv import load_dotenv
    if (project_root / ".env").exists():
        load_dotenv(project_root / ".env")
except ImportError:
    pass

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "4-Infrastructure" / "infra"))

from infra.ene_api import ENEAPIHook, AccessLevel

RCLONE_CONF = Path.home() / ".config" / "rclone" / "rclone.conf"


def test_rclone_gdrive() -> dict:
    """Test if rclone can list Gdrive root."""
    result = subprocess.run(
        ["rclone", "ls", "Gdrive:", "--max-depth", "1"],
        capture_output=True, text=True, timeout=60
    )
    return {
        "ok": result.returncode == 0,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "returncode": result.returncode
    }


def parse_rclone_token() -> dict:
    """Extract token JSON from rclone config."""
    if not RCLONE_CONF.exists():
        return {"error": f"rclone.conf not found at {RCLONE_CONF}"}
    
    in_gdrive = False
    token_line = None
    with open(RCLONE_CONF) as f:
        for line in f:
            line = line.strip()
            if line.startswith("[Gdrive]"):
                in_gdrive = True
            elif line.startswith("[") and line.endswith("]"):
                in_gdrive = False
            elif in_gdrive and line.startswith("token = "):
                token_line = line[len("token = "):]
                break
    
    if not token_line:
        return {"error": "No token found in [Gdrive] section"}
    
    try:
        token = json.loads(token_line)
        return {"ok": True, "token": token}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid token JSON: {e}"}


def update_rclone_config(new_token: dict) -> bool:
    """Update rclone.conf with new token JSON."""
    if not RCLONE_CONF.exists():
        return False
    
    lines = []
    in_gdrive = False
    replaced = False
    with open(RCLONE_CONF) as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("[Gdrive]"):
                in_gdrive = True
            elif stripped.startswith("[") and stripped.endswith("]"):
                in_gdrive = False
            
            if in_gdrive and stripped.startswith("token = ") and not replaced:
                lines.append(f"token = {json.dumps(new_token)}\n")
                replaced = True
                continue
            lines.append(line)
    
    with open(RCLONE_CONF, "w") as f:
        f.writelines(lines)
    
    return replaced


def ingest_gdrive_to_ene(token: dict, client_id: str, client_secret: str) -> dict:
    """Store gdrive credentials in ENE substrate."""
    api = ENEAPIHook()
    
    # Store the refresh token as the primary credential
    payload = json.dumps({
        "provider": "gdrive",
        "remote_name": "Gdrive",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": token.get("refresh_token", ""),
        "token_type": token.get("token_type", "Bearer"),
        "updated_at": datetime.utcnow().isoformat(),
    })
    
    result = api.store_sensitive_data(
        pkg="credentials/gdrive",
        payload=payload,
        classification=AccessLevel.SECRET
    )
    
    return result


def main():
    print("=" * 70)
    print("GDRIVE RESTORE")
    print("=" * 70)
    
    # 1. Test rclone
    print("\n[1] Testing rclone Gdrive: access...")
    test = test_rclone_gdrive()
    if test["ok"]:
        print("   ✅ Gdrive is accessible")
        print(f"   Listing: {test['stdout'][:200]}...")
    else:
        print("   ❌ Gdrive access failed")
        print(f"   Error: {test['stderr'][:200]}")
        
        if "invalid_grant" in test["stderr"] or "token expired" in test["stderr"]:
            print("\n   The refresh token is revoked or expired.")
            print("   You need to re-authenticate:")
            print("\n   ┌─────────────────────────────────────────────────────────────┐")
            print("   │  Run this command in your terminal:                       │")
            print("   │                                                             │")
            print("   │    rclone config reconnect Gdrive:                        │")
            print("   │                                                             │")
            print("   │  Then follow the browser prompt to authorize.             │")
            print("   │  After that, run this script again.                       │")
            print("   └─────────────────────────────────────────────────────────────┘")
            sys.exit(1)
    
    # 2. Parse token
    print("\n[2] Reading rclone token...")
    token_info = parse_rclone_token()
    if "error" in token_info:
        print(f"   ❌ {token_info['error']}")
        sys.exit(1)
    
    token = token_info["token"]
    refresh_token = token.get("refresh_token", "")
    if not refresh_token:
        print("   ❌ No refresh_token in rclone config. Re-authenticate with:")
        print("      rclone config reconnect Gdrive:")
        sys.exit(1)
    
    print(f"   ✅ Refresh token present ({len(refresh_token)} chars)")
    
    # 3. Read client_id/client_secret from rclone config
    client_id = None
    client_secret = None
    with open(RCLONE_CONF) as f:
        in_gdrive = False
        for line in f:
            line = line.strip()
            if line.startswith("[Gdrive]"):
                in_gdrive = True
            elif line.startswith("[") and line.endswith("]"):
                in_gdrive = False
            elif in_gdrive and line.startswith("client_id = "):
                client_id = line[len("client_id = "):]
            elif in_gdrive and line.startswith("client_secret = "):
                client_secret = line[len("client_secret = "):]
    
    # 4. Ingest into ENE
    print("\n[3] Ingesting gdrive credentials into ENE substrate...")
    ene_result = ingest_gdrive_to_ene(token, client_id, client_secret)
    if ene_result.get("success"):
        print(f"   ✅ Stored in ENE. ID: {ene_result['id']}")
    else:
        print(f"   ❌ ENE storage failed: {ene_result.get('error')}")
        sys.exit(1)
    
    # 5. Verify decryption
    print("\n[4] Verifying ENE decryption...")
    api = ENEAPIHook()
    verify = api.retrieve_sensitive_data("credentials/gdrive", AccessLevel.SECRET)
    if verify.get("success"):
        print("   ✅ Credentials decryptable")
        parsed = json.loads(verify["payload"])
        print(f"   Provider: {parsed.get('provider')}")
        print(f"   Remote: {parsed.get('remote_name')}")
        print(f"   Refresh token length: {len(parsed.get('refresh_token', ''))}")
    else:
        print(f"   ❌ Decryption failed: {verify.get('error')}")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("GDRIVE RESTORED")
    print("=" * 70)
    print("\nNext steps:")
    print("  - ENE substrate now holds the gdrive credential")
    print("  - rclone Gdrive: remote is working")
    print("  - Run 'rclone mount Gdrive: ~/Gdrive' to mount if desired")
    print("  - Run bridge/dump scripts to push gdrive metadata into Neo4j")


if __name__ == "__main__":
    main()
