#!/usr/bin/env python3
"""
Canonical Math Functions Reference Builder

Builds deterministic Wolfram Alpha query strings for all math functions,
maps them to Mathematica syntax and Lean/Mathlib equivalents.

Output: JSON + Markdown reference table
"""

import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Tuple

WOLFRAM_APP_ID = "HYJE3R3R63"
WOLFRAM_API_URL = "https://api.wolframalpha.com/v2/query"

# Canonical math function categories and test queries
MATH_FUNCTION_CATEGORIES = {
    "trigonometric": [
        ("sin(x)", "Sin[x]", "Real.sin"),
        ("cos(x)", "Cos[x]", "Real.cos"),
        ("tan(x)", "Tan[x]", "Real.tan"),
        ("asin(x)", "ArcSin[x]", "Real.arcsin"),
        ("acos(x)", "ArcCos[x]", "Real.arccos"),
        ("atan(x)", "ArcTan[x]", "Real.arctan"),
        ("sinh x", "Sinh[x]", "Real.sinh"),
        ("cosh(x)", "Cosh[x]", "Real.cosh"),
        ("tanh(x)", "Tanh[x]", "Real.tanh"),
    ],
    "logarithmic": [
        ("log(x)", "Log[x]", "Real.log"),
        ("log10(x)", "Log10[x]", "Real.log10"),
        ("log2(x)", "Log2[x]", "Real.logBase 2"),
        ("ln(x)", "Log[x]", "Real.log"),
    ],
    "exponential": [
        ("exp(x)", "Exp[x]", "Real.exp"),
        ("e^x", "E^x", "Real.exp"),
        ("2^x", "2^x", "HPow.hPow 2"),
        ("x squared", "x^2", "HPow.hPow x 2"),
    ],
    "calculus": [
        ("derivative of sin(x)", "D[Sin[x], x]", "deriv (fun x => Real.sin x)"),
        ("integrate x^2 dx", "Integrate[x^2, x]", "integral (fun x => x^2)"),
        ("integrate x^2 from 0 to 1", "integrate x^2 from 0 to 1", "intervalIntegral (fun x => x^2) 0 1"),
        ("limit as x->0 of sin(x)/x", "Limit[Sin[x]/x, x -> 0]", "limit (fun x => Real.sin x / x) 0"),
    ],
    "special_functions": [
        ("gamma(x)", "Gamma[x]", "Real.gamma"),
        ("Beta function", "Beta[x, y]", "Real.beta"),
        ("erf(x)", "Erf[x]", "Real.erf"),
        ("Riemann zeta", "Zeta[x]", "Real.zeta"),
    ],
    "statistics": [
        ("mean of 1,2,3", "Mean[{1, 2, 3}]", "List.mean [1,2,3]"),
        ("variance of 1,2,3", "Variance[{1, 2, 3}]", "List.variance [1,2,3]"),
        ("standard deviation of 1,2,3", "StandardDeviation[{1, 2, 3}]", "List.std [1,2,3]"),
    ],
    "number_theory": [
        ("gcd of 12 and 18", "GCD[12, 18]", "Nat.gcd 12 18"),
        ("lcm of 12 and 18", "LCM[12, 18]", "Nat.lcm 12 18"),
        ("prime numbers up to 10", "Prime[Range[10]]", "List.filter Nat.Prime (List.range 10)"),
        ("prime 7", "PrimeQ[7]", "Nat.Prime 7"),
    ],
    "linear_algebra": [
        ("det [[1,2],[3,4]]", "Det[{{1, 2}, {3, 4}}]", "Matrix.det !![[1,2],[3,4]]"),
        ("inverse of {{1,2},{3,4}}", "Inverse[{{1, 2}, {3, 4}}]", "Matrix.inv !![[1,2],[3,4]]"),
        ("eigenvalues of {{1,2},{3,4}}", "Eigenvalues[{{1, 2}, {3, 4}}]", "Matrix.eigenvalues !![[1,2],[3,4]]"),
    ],
    "combinatorics": [
        ("factorial of 5", "Factorial[5]", "Nat.factorial 5"),
        ("C(5,2)", "Binomial[5, 2]", "Nat.choose 5 2"),
        ("permutations of 3", "Permutations[3]", "List.permutations (List.range 3)"),
    ],
    "complex": [
        ("Re(3+4i)", "Re[3 + 4 I]", "Complex.re (3 + 4 * Complex.I)"),
        ("imaginary part of 3+4i", "Im[3 + 4 I]", "Complex.im (3 + 4 * Complex.I)"),
        ("absolute value of 3+4i", "Abs[3 + 4 I]", "Complex.abs (3 + 4 * Complex.I)"),
        ("argument of 3+4i", "Arg[3 + 4 I]", "Complex.arg (3 + 4 * Complex.I)"),
    ],
}


def query_wolfram(input_str: str) -> Tuple[bool, str]:
    """Query Wolfram Alpha and return success status and result."""
    params = {
        "appid": WOLFRAM_APP_ID,
        "input": input_str,
        "format": "plaintext",
    }
    
    try:
        response = requests.get(WOLFRAM_API_URL, params=params, timeout=10)
        response.raise_for_status()
        
        # Extract plaintext result
        import re
        plaintext_matches = re.findall(r'<plaintext>([^<]+)</plaintext>', response.text)
        
        if plaintext_matches:
            return True, plaintext_matches[0].strip()
        else:
            return False, "No plaintext result found"
            
    except Exception as e:
        return False, f"Error: {str(e)}"


def build_canonical_reference() -> Dict:
    """Build canonical reference table for all math functions."""
    canonical_ref = {
        "metadata": {
            "app_id": WOLFRAM_APP_ID,
            "timestamp": time.time(),
            "total_categories": len(MATH_FUNCTION_CATEGORIES),
            "total_functions": sum(len(funcs) for funcs in MATH_FUNCTION_CATEGORIES.values()),
        },
        "categories": {},
    }
    
    for category, functions in MATH_FUNCTION_CATEGORIES.items():
        canonical_ref["categories"][category] = []
        
        for wolfram_query, mathematica_syntax, lean_syntax in functions:
            print(f"Testing: {category} - {wolfram_query}")
            
            success, result = query_wolfram(wolfram_query)
            
            canonical_ref["categories"][category].append({
                "wolfram_query": wolfram_query,
                "mathematica_syntax": mathematica_syntax,
                "lean_syntax": lean_syntax,
                "wolfram_result": result if success else "FAILED",
                "status": "verified" if success else "failed",
            })
            
            time.sleep(1)  # Rate limiting
    
    return canonical_ref


def save_canonical_reference(reference: Dict):
    """Save canonical reference to JSON and Markdown files."""
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    # Save JSON
    json_path = output_dir / "canonical_math_functions.json"
    with open(json_path, "w") as f:
        json.dump(reference, f, indent=2)
    print(f"JSON saved to: {json_path}")
    
    # Save Markdown
    md_path = output_dir / "canonical_math_functions.md"
    with open(md_path, "w") as f:
        f.write("# Canonical Math Functions Reference\n\n")
        f.write(f"Generated: {time.ctime(reference['metadata']['timestamp'])}\n")
        f.write(f"Total Categories: {reference['metadata']['total_categories']}\n")
        f.write(f"Total Functions: {reference['metadata']['total_functions']}\n\n")
        
        for category, functions in reference["categories"].items():
            f.write(f"## {category.title()}\n\n")
            f.write(f"| Wolfram Query | Mathematica Syntax | Lean Syntax | Status |\n")
            f.write(f"|---|---|---|---|\n")
            
            for func in functions:
                status_emoji = "✅" if func["status"] == "verified" else "❌"
                f.write(f"| `{func['wolfram_query']}` | `{func['mathematica_syntax']}` | `{func['lean_syntax']}` | {status_emoji} |\n")
            
            f.write("\n")
    
    print(f"Markdown saved to: {md_path}")


def main():
    print("Building canonical math functions reference...")
    print("=" * 70)
    
    reference = build_canonical_reference()
    save_canonical_reference(reference)
    
    verified_count = sum(
        1 for cat in reference["categories"].values()
        for func in cat if func["status"] == "verified"
    )
    total_count = reference["metadata"]["total_functions"]
    
    print("=" * 70)
    print(f"Verification complete: {verified_count}/{total_count} functions verified")
    print(f"Pass rate: {verified_count/total_count*100:.1f}%")


if __name__ == "__main__":
    main()
