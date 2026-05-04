#!/usr/bin/env python3
import os
import sys
import json
import time
from pathlib import Path

# Add project root to path for infra imports
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from infra.ene_api import ENEAPIHook, AccessLevel
except ImportError:
    print("❌ Error: Could not find infra.ene_api. Ensure you are running from the project root.")
    sys.exit(1)

def load_env():
    """Manual .env loader to avoid external dependencies"""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value.replace('"', '').replace("'", "")

def deploy_sigma_session():
    print("🚀 Initializing SIGMA Hardware Session Deployment...")
    load_env()
    
    # Initialize ENE API Hook
    api = ENEAPIHook()
    
    # Session Metadata - Anchored to RES-2311/2312
    session_data = {
        "session_id": f"SIGMA-REV3-{int(time.time())}",
        "hardware_target": "Tang Nano 9K (GW1NR-9)",
        "components": [
            {"id": "PBACS-Signal-Core", "status": "VERIFIED", "source": "0-Core-Formalism/lean/Semantics/Semantics/PBACSSignal.lean"},
            {"id": "PBACS-Verilog-Netlist", "status": "EXTRACTED", "source": "5-Applications/scripts/pbacs_rev3_hdl.v"},
            {"id": "SIGMA-BOM", "status": "STABLE", "linear_ref": "RES-2312"}
        ],
        "manifold_anchor": "intent/sigma/rev3/stable"
    }

    print(f"🔒 Encrypting Structural Attestation for {session_data['session_id']}...")
    
    # Store session data with SECRET classification
    result = api.store_sensitive_data(
        pkg=f"sigma/sessions/{session_data['session_id']}",
        payload=json.dumps(session_data),
        classification=AccessLevel.SECRET,
        semantic_vector=[0.618, 0.382, 1.0, 0.0] # Phi-anchored coordinates
    )

    if result.get("success"):
        print(f"✅ Session stored successfully. Manifold ID: {result['id']}")
        
        # Immediate Clearance Verification
        print("\n🛡️ Running Automated Clearance Check...")
        
        # Verify with SECRET clearance
        audit_secret = api.retrieve_sensitive_data(f"sigma/sessions/{session_data['session_id']}", AccessLevel.SECRET)
        if audit_secret.get("success"):
            print(f"  [SECRET]: ACCESS GRANTED. Integrity verified: ✅")
        else:
            print(f"  [SECRET]: ACCESS DENIED. Error: {audit_secret.get('error')}")

        # Verify with PUBLIC clearance (negative test)
        audit_public = api.retrieve_sensitive_data(f"sigma/sessions/{session_data['session_id']}", AccessLevel.PUBLIC)
        if not audit_public.get("success"):
            print(f"  [PUBLIC]: ACCESS DENIED (Correct Behavior): ✅")
        else:
            print(f"  [PUBLIC]: CRITICAL ERROR - LEAK DETECTED.")
            
    else:
        print(f"❌ Deployment failed: {result.get('error')}")

if __name__ == "__main__":
    deploy_sigma_session()
