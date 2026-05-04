#!/usr/bin/env python3
"""
Execute Fundamental Topology Reinvention Using Real Swarm API

This script uses the real swarm API at http://127.0.0.1:8000 to execute the
fundamental topology reinvention query with actual time allocation (up to 1 hour).
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime

SWARM_API_URL = "http://127.0.0.1:8000"

def load_swarm_request(request_path):
    """Load the swarm request from file."""
    with open(request_path, 'r') as f:
        return json.load(f)

def execute_fundamental_reinvention_via_api():
    """Execute fundamental topology reinvention using real swarm API."""
    print("=" * 70)
    print("Executing Fundamental Topology Reinvention Using Real Swarm API")
    print("=" * 70)
    
    # Load the swarm request
    request_path = "shared-data/data/swarm_requests/swarm_fundamental_reinvention.json"
    print(f"\nLoading request from: {request_path}")
    request = load_swarm_request(request_path)
    
    print(f"Request ID: {request['request_id']}")
    print(f"Time Allocation: {request['time_allocation']}")
    print(f"Priority: {request['priority']}")
    
    # Convert the request to a format suitable for the swarm API
    # The swarm API expects subjects, keywords, formalStatus, requireLeanFormalization, limit, includeMetadata
    swarm_api_request = {
        "subjects": ["topology", "mathematics", "foundations", "novel_concept"],
        "keywords": "fundamental reinvention unprecedented mathematics topology",
        "formalStatus": "unknown",
        "requireLeanFormalization": False,
        "limit": 100,
        "includeMetadata": True
    }
    
    print(f"\nSending request to swarm API: {SWARM_API_URL}/query")
    print(f"Subjects: {swarm_api_request['subjects']}")
    print(f"Keywords: {swarm_api_request['keywords']}")
    
    start_time = time.time()
    
    try:
        # Execute the swarm query
        response = requests.post(
            f"{SWARM_API_URL}/query",
            json=swarm_api_request,
            timeout=3600  # 1 hour timeout
        )
        
        elapsed_time = time.time() - start_time
        
        response.raise_for_status()
        result = response.json()
        
        print(f"\nSwarm API response received in {elapsed_time:.2f} seconds")
        
        # Output results
        print("\n" + "=" * 70)
        print("Swarm API Results")
        print("=" * 70)
        print(f"Success: {result.get('success', False)}")
        print(f"Count: {result.get('count', 0)}")
        print(f"Confidence: {result.get('confidence', 0)}")
        print(f"Routed To: {result.get('routedTo', 'unknown')}")
        
        print(f"\nResults:")
        for i, entity in enumerate(result.get('results', [])[:10], 1):
            print(f"  {i}. {entity.get('name', 'Unknown')}")
            print(f"     Subject: {entity.get('subject', 'Unknown')}")
            print(f"     Statement: {entity.get('statement', 'No statement')[:100]}...")
        
        print(f"\nSuggestions:")
        for suggestion in result.get('suggestions', []):
            print(f"  - {suggestion}")
        
        # Save results
        output_path = f"shared-data/data/swarm_responses/swarm_response_fundamental_reinvention_real_api_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        result_data = {
            "response_id": f"swarm_response_real_api_{request['request_id'].replace('swarm_', '')}",
            "timestamp": datetime.now().isoformat(),
            "request_id": request['request_id'],
            "elapsed_time_seconds": elapsed_time,
            "swarm_api_result": result,
            "time_allocation_used": f"{elapsed_time:.2f} seconds out of {request['time_allocation']}"
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        print(f"\nResults saved to: {output_path}")
        print("=" * 70)
        
        return result_data
        
    except requests.exceptions.Timeout:
        print(f"\n❌ Timeout after 1 hour")
        return None
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Could not connect to swarm API at {SWARM_API_URL}")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = execute_fundamental_reinvention_via_api()
    if result:
        print("\n✅ Fundamental topology reinvention executed successfully using real swarm API")
    else:
        print("\n❌ Failed to execute fundamental topology reinvention via real swarm API")
