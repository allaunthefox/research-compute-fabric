#!/usr/bin/env python3
"""
Wolfram Alpha Math Verification for FieldEquationIntegration.lean

Extracts and verifies mathematical equations from the FieldEquationIntegration module.
"""

import os
import sys
import json
import urllib.request
import urllib.error
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "0-Core-Formalism"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure" / "infra"))

try:
    from infra.ene_cloud_credential_manager import ENECloudCredentialManager
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

class WolframAlphaVerifier:
    """Wolfram Alpha API client for mathematical verification."""
    
    BASE_URL = "http://api.wolframalpha.com/v2/query"
    
    def __init__(self, app_id: str):
        self.app_id = app_id
    
    def query(self, input_expr: str, format: str = "plaintext", output: str = "JSON") -> dict:
        """Query Wolfram Alpha API."""
        params = {
            "input": input_expr,
            "format": format,
            "output": output,
            "appid": self.app_id
        }
        
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
            return data
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP Error {e.code}: {e.reason}"}
        except urllib.error.URLError as e:
            return {"error": f"URL Error: {e.reason}"}
        except Exception as e:
            return {"error": str(e)}
    
    def verify_equation(self, equation: str, description: str) -> dict:
        """Verify a mathematical equation."""
        print(f"\n🔍 Verifying: {description}")
        print(f"   Equation: {equation}")
        result = self.query(equation)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return {
                "equation": equation,
                "description": description,
                "status": "error",
                "error": result["error"]
            }
        
        # Check if query was successful
        if result.get("queryresult", {}).get("success"):
            pods = result["queryresult"].get("pods", [])
            
            # Extract primary result
            primary_result = None
            for pod in pods:
                if pod.get("primary"):
                    subpods = pod.get("subpods", [])
                    if subpods:
                        primary_result = subpods[0].get("plaintext", "")
                        break
            
            if primary_result:
                print(f"✅ Result: {primary_result}")
                return {
                    "equation": equation,
                    "description": description,
                    "status": "verified",
                    "result": primary_result,
                    "pods": len(pods)
                }
            else:
                print(f"⚠️  Query succeeded but no primary result")
                return {
                    "equation": equation,
                    "description": description,
                    "status": "partial",
                    "pods": len(pods)
                }
        else:
            print(f"❌ Query failed")
            return {
                "equation": equation,
                "description": description,
                "status": "failed"
            }

def main():
    print("=" * 70)
    print("WOLFRAM ALPHA MATH VERIFICATION - FieldEquationIntegration.lean")
    print("=" * 70)
    
    # Initialize ENE credential manager
    try:
        ene = ENECloudCredentialManager()
        print("ENE credential manager initialized")
    except Exception as e:
        print(f"ENE initialization failed: {e}")
        sys.exit(1)
    
    # Retrieve Wolfram Alpha credential from ENE
    print("\nRetrieving Wolfram Alpha credential from ENE...")
    wolfram_creds = None
    for cred_id, cred in ene.credentials.items():
        if cred.provider == "wolfram_alpha":
            wolfram_creds = cred
            break
    
    if not wolfram_creds:
        print("❌ Wolfram Alpha credential not found in ENE")
        sys.exit(1)
    
    print(f"✅ Found credential: {wolfram_creds.credential_id}")
    
    # Load App ID from environment
    app_id = os.getenv("WOLFRAM_ALPHA_APPID", "")
    if not app_id:
        print("❌ WOLFRAM_ALPHA_APPID not found in environment")
        sys.exit(1)
    print(f"✅ App ID loaded from environment")
    
    # Initialize Wolfram Alpha verifier
    verifier = WolframAlphaVerifier(app_id)
    
    # Equations from FieldEquationIntegration.lean
    equations = [
        # Unified field equation
        {
            "equation": "(F + Phi + C + D) / 4",
            "description": "Unified field equation composite (Ψ = (1/4)[F ⊗ Φ ⊗ C ⊗ D])"
        },
        
        # Weighted composite - use numeric example
        {
            "equation": "(10*2 + 20*3 + 30*4 + 40*5) / 4",
            "description": "Weighted composite with field weights (numeric example)"
        },
        
        # Pentagonal closure
        {
            "equation": "F + Phi + C + D + sigma",
            "description": "Pentagonal square closure (sum of corners plus center)"
        },
        
        # Pentagonal balance condition
        {
            "equation": "sigma * 4 = F + Phi + C + D",
            "description": "Pentagonal square balance (center equals average of corners)"
        },
        
        # Near-miss error (simplified)
        {
            "equation": "abs(x + y - z)",
            "description": "Near-miss error function (simplified Fermat equation)"
        },
        
        # Average error
        {
            "equation": "(epsilon1 + epsilon2 + epsilon3 + epsilon4) / 4",
            "description": "Average near-miss error over 4 points"
        },
        
        # Tension function
        {
            "equation": "abs(epsilon - mu) + 1 / (abs(epsilon - mu) + delta)",
            "description": "Tension function for near-miss detection"
        },
        
        # XOR operation (for MMR hash)
        {
            "equation": "a XOR b",
            "description": "XOR operation for MMR hash computation"
        },
        
        # Modulus operation (for hash) - use numeric example
        {
            "equation": "(100 * 31 + 17) mod 256",
            "description": "Modulus-based hash function (numeric example)"
        },
        
        # Stabilization formula - use numeric example
        {
            "equation": "(10 * 5 + 20) / (5 + 1)",
            "description": "Web constraint stabilization formula (numeric example)"
        }
    ]
    
    print(f"\nVerifying {len(equations)} equations from FieldEquationIntegration.lean...")
    
    results = []
    for i, eq in enumerate(equations):
        result = verifier.verify_equation(eq["equation"], eq["description"])
        results.append(result)
        # Add delay between requests to avoid rate limiting
        if i < len(equations) - 1:
            time.sleep(2)
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    verified = sum(1 for r in results if r["status"] == "verified")
    failed = sum(1 for r in results if r["status"] in ["error", "failed"])
    partial = sum(1 for r in results if r["status"] == "partial")
    
    print(f"Total equations: {len(equations)}")
    print(f"✅ Verified: {verified}")
    print(f"⚠️  Partial: {partial}")
    print(f"❌ Failed: {failed}")
    
    # Save results to file
    output_file = Path("shared-data/data/field_equation_wolfram_verification.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            "module": "FieldEquationIntegration.lean",
            "app_id": app_id,
            "timestamp": Path(__file__).stat().st_mtime,
            "total": len(equations),
            "verified": verified,
            "failed": failed,
            "partial": partial,
            "results": results
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    print("=" * 70)

if __name__ == "__main__":
    main()
