#!/usr/bin/env python3
"""
Swarm Review for PeptideMoE Lean Modules

Queries the swarm API to review the newly added PeptideMoE modules:
- PeptideMoE
- PeptideMoEExamples
- PeptideMoEFailure
- PeptideMoERepair
"""

import requests
import json
from lean_unified_shim import SwarmAPISystem, Any

# Swarm API endpoint
SWARM_API_URL = "http://127.0.0.1:8000"

def query_swarm(subjects: List[str], keywords: str = None, has_lean: bool = True) -> Dict[str, Any]:
    """Query the swarm API."""
    try:
        response = requests.post(
            f"{SWARM_API_URL}/query",
            json={
                "subjects": subjects,
                "keywords": keywords,
                "has_lean_formalization": has_lean,
                "limit": 20,
                "include_metadata": True
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to swarm API. Ensure it's running."}
    except Exception as e:
        return {"error": str(e)}

def main():
    """Main entry point."""
    print("=" * 70)
    print("SWARM REVIEW: PeptideMoE Lean Modules")
    print("=" * 70)
    
    # Query for PeptideMoE-related modules
    print("\nQuerying swarm for PeptideMoE modules...")
    result = query_swarm(
        subjects=["PeptideMoE"],
        keywords="PeptideMoE",
        has_lean=True
    )
    
    if "error" in result:
        print(f"\n[!] Error: {result['error']}")
        print("\nNote: To start the swarm API, run:")
        print("  cd /home/allaun/Documents/Research Stack/tools")
        print("  python swarm_api.py")
        return
    
    print(f"\nQuery Results:")
    print(f"  Success: {result.get('success', False)}")
    print(f"  Count: {result.get('count', 0)}")
    print(f"  Confidence: {result.get('confidence', 0):.3f}")
    print(f"  Query Time: {result.get('query_time_ms', 0):.2f}ms")
    
    print(f"\nResults:")
    for i, item in enumerate(result.get('results', []), 1):
        print(f"\n  {i}. {item.get('name', 'Unknown')}")
        print(f"     Subject: {item.get('subject', 'N/A')}")
        print(f"     Lean Module: {item.get('lean_module', 'N/A')}")
        print(f"     Formal Status: {item.get('formal_status', 'N/A')}")
        print(f"     Proof Status: {item.get('proof_status', 'N/A')}")
        if item.get('statement'):
            stmt = item['statement'][:100] + "..." if len(item['statement']) > 100 else item['statement']
            print(f"     Statement: {stmt}")
    
    print(f"\nSuggestions:")
    for suggestion in result.get('suggestions', []):
        print(f"  - {suggestion}")
    
    print(f"\nMetadata:")
    for key, value in result.get('metadata', {}).items():
        print(f"  {key}: {value}")
    
    # Check database stats
    print("\n" + "=" * 70)
    print("DATABASE STATISTICS")
    print("=" * 70)
    
    try:
        stats_response = requests.get(f"{SWARM_API_URL}/stats", timeout=10)
        stats_response.raise_for_status()
        stats = stats_response.json()
        
        print(f"\nTotal Entities: {stats.get('total_entities', 0)}")
        print(f"Lean Formalized: {stats.get('lean_formalized', 0)}")
        print(f"Subjects: {stats.get('subjects', 0)}")
        print(f"Timestamp: {stats.get('timestamp', 'N/A')}")
    except Exception as e:
        print(f"\n[!] Could not fetch stats: {e}")
    
    print("\n" + "=" * 70)
    
    # Save results
    output_file = "/home/allaun/Documents/Research Stack/data/swarm_peptide_moe_module_review.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
