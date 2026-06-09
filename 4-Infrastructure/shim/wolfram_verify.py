#!/usr/bin/env python3
"""
wolfram_verify.py - Queries Wolfram Alpha API to verify algebraic and physical equations.
Saves the verification results as a receipt.
"""

import urllib.request
import urllib.parse
import json
import sys
import os

APPID = "HYJE3R3R63"

QUERIES = {
    "golden_ratio_conjugate": "solve x^2 + x - 1 = 0",
    "gaussian_diffusion_integral": "integrate exp(-x^2) from -infinity to infinity",
    "cramer_4x4_determinant": "determinant {{a, b, c, d}, {e, f, g, h}, {i, j, k, l}, {m, n, o, p}}"
}

def query_wolfram(query):
    encoded = urllib.parse.quote_plus(query)
    url = f"http://api.wolframalpha.com/v2/query?appid={APPID}&input={encoded}&format=plaintext&output=JSON"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except Exception as e:
        return {"error": str(e)}

def main():
    print("Initializing Wolfram Alpha Verification...")
    results = {}
    
    for name, query in QUERIES.items():
        print(f"Querying Wolfram for: '{query}'...")
        res = query_wolfram(query)
        
        # Parse out main text results from pods
        text_result = None
        if "queryresult" in res and "pods" in res["queryresult"]:
            for pod in res["queryresult"]["pods"]:
                if pod.get("primary", False) or pod.get("id") in ["Result", "Solution", "Value"]:
                    for subpod in pod.get("subpods", []):
                        if "plaintext" in subpod:
                            text_result = subpod["plaintext"]
                            break
        
        results[name] = {
            "query": query,
            "text_result": text_result,
            "raw_response": res
        }
        
    output_path = "shared-data/data/stack_solidification/wolfram_verification_receipt.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"\nVerification complete. Wolfram receipt written to {output_path}")
    print("Golden ratio conjugate result:", results["golden_ratio_conjugate"]["text_result"])
    print("Gaussian diffusion integral result:", results["gaussian_diffusion_integral"]["text_result"])

if __name__ == "__main__":
    main()
