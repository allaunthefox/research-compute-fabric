#!/usr/bin/env python3
"""
Store Wolfram Alpha credential in ENE
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "0-Core-Formalism"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure" / "infra"))

try:
    from infra.ene_cloud_credential_manager import ENECloudCredentialManager
    from ene_api import AccessLevel
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def main():
    print("=" * 70)
    print("STORING WOLFRAM ALPHA CREDENTIAL IN ENE")
    print("=" * 70)
    
    # Initialize ENE credential manager
    try:
        ene = ENECloudCredentialManager()
        print("ENE credential manager initialized")
    except Exception as e:
        print(f"ENE initialization failed: {e}")
        sys.exit(1)
    
    # Store Wolfram Alpha credential
    wolfram_app_id = os.environ.get("WOLFRAM_ALPHA_APPID", "")
    
    print(f"\nStoring Wolfram Alpha App ID: {wolfram_app_id}")
    
    try:
        cred_id = ene.store_credential(
            provider="wolfram_alpha",
            api_key=wolfram_app_id,
            secret="",  # No additional secret needed for App ID
            node_assignments=["node_1", "node_2", "node_3"],
            access_level=AccessLevel.RESTRICTED
        )
        
        print(f"\n✅ Credential stored successfully!")
        print(f"   Credential ID: {cred_id}")
        print(f"   Provider: wolfram_alpha")
        print(f"   Node assignments: node_1, node_2, node_3")
        print(f"   Access level: RESTRICTED")
        
        # Verify storage
        print(f"\nVerifying storage...")
        creds = ene.credentials
        if cred_id in creds:
            print(f"✅ Credential verified in ENE database")
            print(f"   Health score: {creds[cred_id].health_score}")
            print(f"   Usage count: {creds[cred_id].usage_count}")
        else:
            print(f"❌ Credential not found in database")
        
    except Exception as e:
        print(f"\n❌ Failed to store credential: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
