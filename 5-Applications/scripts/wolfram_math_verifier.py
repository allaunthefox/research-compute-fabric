#!/usr/bin/env python3
"""
Wolfram Alpha Math Verifier for Research Stack

Queries Wolfram Alpha API to verify mathematical equations from the Research Stack,
including the equation forest and Wolfram Alpha input sheet.
"""

import os
import sys
import json
import urllib.request
import urllib.error
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
    
    def verify_equation(self, equation: str) -> dict:
        """Verify a mathematical equation."""
        print(f"\n🔍 Verifying: {equation}")
        result = self.query(equation)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return {"equation": equation, "status": "error", "error": result["error"]}
        
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
                    "status": "verified",
                    "result": primary_result,
                    "pods": len(pods)
                }
            else:
                print(f"⚠️  Query succeeded but no primary result")
                return {
                    "equation": equation,
                    "status": "partial",
                    "pods": len(pods)
                }
        else:
            print(f"❌ Query failed")
            return {
                "equation": equation,
                "status": "failed"
            }

def main():
    print("=" * 70)
    print("WOLFRAM ALPHA MATH VERIFICATION")
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
    
    # Equations to verify (from Wolfram Alpha input sheet)
    equations = [
        # AAS Compression & Entropy
        "2.0*10^6 / 3500",
        "-log2(3500 / 2000000)",
        "(1 - (3500 / 2000000)) * 100",
        
        # Sovereign Cement: Thermal & Kinetic
        "delta T = (1.2*10^6 J/kg) / (850 J/(kg*K))",
        "solve 1.2*10^6 = 0.95 * 5.67*10^-8 * 5.0 * T^4 for T",
        
        # Equation Forest examples
        "solve d/dx (x^2) = 0",
        "integrate x^2 from 0 to 1",
    ]
    
    print(f"\nVerifying {len(equations)} equations...")
    
    results = []
    for equation in equations:
        result = verifier.verify_equation(equation)
        results.append(result)
    
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
    output_file = Path("shared-data/data/wolfram_verification_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
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
