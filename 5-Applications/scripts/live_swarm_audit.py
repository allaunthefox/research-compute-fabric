import sys
import os
import json

# Add project root to path for infra import
sys.path.append('/home/allaun/Research Stack')

from infra.lean_unified_shim import SwarmAPISystem

def main():
    print("--- INITIATING AUTHENTIC SWARM API INTERFACE ---")
    swarm = SwarmAPISystem()
    
    # query metadata for PIST stability
    try:
        print("Querying Swarm for PIST stability invariants...")
        # swarm_query expects a dictionary aligned with Semantics.SwarmQueryAPI.SwarmQueryRequest
        request = {
            "subjects": ["PIST", "Manifold"],
            "keywords": ["stability", "invariant"],
            "formalStatus": None,
            "requireLeanFormalization": False,
            "limit": {"value": 5},
            "includeMetadata": False
        }
        result = swarm.swarm_query(request)
        
        print("\n[LIVE SWARM RESPONSE]")
        print(f"Success: {result.get('success', False)}")
        print(f"Count: {result.get('count', 0)}")
        print(f"Routed To: {result.get('routedTo', 'unknown')}")
        
        # confidence is Q16_16 structure { val : Nat }
        conf_val = result.get('confidence', {}).get('val', 0)
        print(f"Confidence: {conf_val / 65536.0:.4f}")
        
        for i, res in enumerate(result.get('results', [])):
            print(f"\nResult {i+1}:")
            print(f"  Name: {res.get('name')}")
            print(f"  Subject: {res.get('subject')}")
            print(f"  Statement: {res.get('statement')}")
            print(f"  Formal Status: {res.get('formalStatus')}")
            
        if result.get('suggestions'):
            print("\nSwarm Suggestions:")
            for sug in result['suggestions']:
                print(f"  - {sug}")
                
    except Exception as e:
        print(f"API Error: {e}")

if __name__ == "__main__":
    main()
