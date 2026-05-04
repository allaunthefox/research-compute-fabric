#!/usr/bin/env python3
"""
Fundamental Math Verification for Research Stack — Drift-Prevention Net

Verifies a wide net of independent mathematical anchors so theory drift is caught
fast. Each anchor pairs a query with an expected substring; verification only
counts when Wolfram's output (whitespace + comma stripped, case-insensitive)
contains that substring.

All physical instances use SI-exact constants (post-2019 redefinition):
  c   = 299792458 m/s            (defined exact)
  h   = 6.62607015×10⁻³⁴ J·s    (defined exact)
  k_B = 1.380649×10⁻²³ J/K      (defined exact)
  N_A = 6.02214076×10²³ /mol    (defined exact)
  e   = 1.602176634×10⁻¹⁹ C    (defined exact)
  R   = N_A·k_B = 8.31446261815324 J/(mol·K)  (exact derived)

Reports pass_rate. Sigma is NOT computed here — claiming a sigma value from a
fixed test list is dimensionally wrong (Six Sigma 6.5σ ≈ 3.4 DPMO, requiring
~3M samples). Sigma claims belong with the GPU population sweeps in
FixedPoint.lean.
"""

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


class WolframAlphaVerifier:
    """Wolfram Alpha API client for mathematical verification."""

    BASE_URL = "https://api.wolframalpha.com/v2/query"

    def __init__(self, app_id: str):
        self.app_id = app_id

    def query(self, input_expr: str) -> dict:
        params = {
            "input": input_expr,
            "format": "plaintext",
            "output": "JSON",
            "appid": self.app_id,
        }
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def _norm(s: str) -> str:
        # Strip whitespace AND commas (Wolfram inserts thousands separators)
        return "".join(s.split()).lower().replace(",", "")

    def verify(self, equation: str, description: str, expected: str) -> dict:
        print(f"\n🔍 {description}")
        print(f"   Equation: {equation}")
        print(f"   Expected: {expected}")
        result = self.query(equation)

        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return {"equation": equation, "description": description,
                    "expected": expected, "status": "error", "error": result["error"]}

        qr = result.get("queryresult", {})
        if not qr.get("success"):
            print("❌ Query failed")
            return {"equation": equation, "description": description,
                    "expected": expected, "status": "failed"}

        pods = qr.get("pods", [])
        all_texts = []
        primary_text = None
        for pod in pods:
            for sub in pod.get("subpods", []):
                txt = sub.get("plaintext", "")
                if not isinstance(txt, str):
                    continue
                if txt:
                    all_texts.append(txt)
                    if pod.get("primary") and primary_text is None:
                        primary_text = txt

        expected_n = self._norm(expected)
        haystack = self._norm(" ".join(all_texts))
        matched = expected_n in haystack
        observed = primary_text or (all_texts[0] if all_texts else "")

        if matched:
            print(f"✅ Result: {observed[:100]}")
            return {"equation": equation, "description": description,
                    "expected": expected, "observed": observed, "status": "verified"}
        else:
            print(f"❌ MISMATCH — got: {observed[:100]}")
            return {"equation": equation, "description": description,
                    "expected": expected, "observed": observed,
                    "status": "mismatch", "all_pods": all_texts}


def main():
    print("=" * 70)
    print("FUNDAMENTAL MATH VERIFICATION — DRIFT-PREVENTION ANCHOR NET")
    print("=" * 70)

    app_id = "HYJE3R3R63"
    verifier = WolframAlphaVerifier(app_id)

    # (equation, description, expected_substring)
    fundamental_math = [
        # ─────────────────────────────────────────────────────────────
        # GROUP A — Calculus foundations (AnalysisFoundations.lean)
        # ─────────────────────────────────────────────────────────────
        ("limit h->0 (f(x+h)-f(x))/h",
         "Derivative definition (AnalysisFoundations.lean)", "f'(x)"),
        ("integral x^2 from 0 to 1",
         "∫₀¹ x² dx = 1/3 (AnalysisFoundations.lean)", "1/3"),
        ("d/dx (x^2)",
         "d/dx(x²) = 2x (AnalysisFoundations.lean)", "2 x"),
        ("limit of x^2 as x approaches 0",
         "lim x→0 x² = 0 (AnalysisFoundations.lean continuity)", "= 0"),
        ("integral sin(x) from 0 to pi",
         "∫₀^π sin(x) dx = 2", "2"),
        ("integral 1/x from 1 to e",
         "∫₁^e dx/x = 1", "1"),
        ("d/dx (sin(x))",
         "d/dx(sin(x)) = cos(x)", "cos(x)"),
        ("d/dx (e^x)",
         "d/dx(eˣ) = eˣ", "e^x"),
        ("d/dx (ln(x))",
         "d/dx(ln(x)) = 1/x", "1/x"),
        ("integral e^(-x^2) from -infinity to infinity",
         "Gaussian: ∫ e^(-x²) dx = √π", "sqrt(π)"),

        # ─────────────────────────────────────────────────────────────
        # GROUP B — Fixed-point arithmetic (FixedPoint.lean)
        # ─────────────────────────────────────────────────────────────
        ("65536 / 65536", "Q16_16 scale factor = 1", "1"),
        ("2^16", "Q0_16 precision = 65536", "65536"),
        ("2^32", "Q16_16 range = 4294967296", "4294967296"),
        ("2^31 - 1", "Q16_16 max signed = 2147483647", "2147483647"),
        ("2^15", "Q0_15 boundary = 32768", "32768"),

        # ─────────────────────────────────────────────────────────────
        # GROUP C — Forest/sum sanity (GradientPathMap.lean)
        # ─────────────────────────────────────────────────────────────
        ("sum [150, 250, 300, 200]",
         "Gradient path cost = 900 (GradientPathMap.lean)", "900"),

        # ─────────────────────────────────────────────────────────────
        # GROUP D — Information theory / Shannon entropy
        # ─────────────────────────────────────────────────────────────
        ("-0.5*log2(0.5) - 0.5*log2(0.5)",
         "H(½,½) = 1 bit (binary uniform)", "1"),
        ("-8*(1/8)*log2(1/8)",
         "H(uniform-8) = 3 bits", "3"),
        ("log2(6)",
         "H(fair die) ≈ 2.5849625 bits", "2.5849625"),
        ("log2(10)",
         "H(decimal digit) ≈ 3.3219280 bits", "3.3219280"),
        ("log2(256)",
         "H(byte) = 8 bits", "8"),
        ("log2(27)",
         "H(BASE-27 / K=3 ternary triplet) ≈ 4.7548875 bits", "4.7548875"),

        # ─────────────────────────────────────────────────────────────
        # GROUP E — SI defining constants (post-2019 redefinition).
        #   Verified by reverse-conversion: assert the SI-exact integer
        #   value converts back to "1 <unit>" — only matches if Wolfram
        #   recognizes the exact defined number.
        # ─────────────────────────────────────────────────────────────
        ("299792458 m/s in c",
         "c = 299792458 m/s (exact, SI defined) ⇒ 1 c", "1 c"),
        ("6.62607015*10^-34 J s in Planck constants",
         "h = 6.62607015×10⁻³⁴ J·s (exact, SI defined) ⇒ 1 ℏ",
         "1 h"),
        ("1.380649*10^-23 J/K in Boltzmann constants",
         "k_B = 1.380649×10⁻²³ J/K (exact, SI defined) ⇒ 1 k_B",
         "1 k"),
        ("6.02214076*10^23 in Avogadro number",
         "N_A = 6.02214076×10²³ /mol (exact, SI defined) ⇒ 1 N_A",
         "1 n"),
        ("1.602176634*10^-19 C in elementary charge",
         "e = 1.602176634×10⁻¹⁹ C (exact, SI defined) ⇒ 1 e",
         "1 e"),

        # ─────────────────────────────────────────────────────────────
        # GROUP F — Derived SI-exact constants (no measurement uncertainty)
        # ─────────────────────────────────────────────────────────────
        ("6.02214076*10^23 * 1.380649*10^-23",
         "R = N_A·k_B = 8.31446261815324 J/(mol·K)", "8.31446261815324"),
        ("6.02214076*10^23 * 1.602176634*10^-19",
         "Faraday F = N_A·e = 96485.33212... C/mol", "96485.33212"),

        # ─────────────────────────────────────────────────────────────
        # GROUP G — Mathematical constants at extreme precision
        # ─────────────────────────────────────────────────────────────
        ("N[Pi, 30]",
         "π to 28 digits (anchored prefix; Wolfram rounds 30th)",
         "3.141592653589793238462643383"),
        ("N[E, 30]",
         "e to 28 digits", "2.718281828459045235360287471"),
        ("N[GoldenRatio, 30]",
         "φ = (1+√5)/2 to 28 digits (PHI-axis hardware)",
         "1.618033988749894848204586834"),
        ("N[EulerGamma, 20]",
         "γ (Euler-Mascheroni) to 19 digits",
         "0.5772156649015328606"),
        ("N[Sqrt[2], 30]",
         "√2 to 28 digits",
         "1.414213562373095048801688724"),
        ("N[Sqrt[3], 30]",
         "√3 to 28 digits",
         "1.732050807568877293527446341"),
        ("N[Log[2], 30]",
         "ln(2) to 30 digits", "0.693147180559945309417232121458"),
        ("N[Log[10], 30]",
         "ln(10) to 30 digits", "2.30258509299404568401799145468"),

        # ─────────────────────────────────────────────────────────────
        # GROUP H — Trig exact values (no rounding)
        # ─────────────────────────────────────────────────────────────
        ("sin(30 degrees)", "sin(30°) = 1/2 (exact)", "1/2"),
        ("cos(60 degrees)", "cos(60°) = 1/2 (exact)", "1/2"),
        ("tan(45 degrees)", "tan(45°) = 1 (exact)", "1"),
        ("sin(pi/4)", "sin(π/4) = 1/√2 (exact)", "1/sqrt(2)"),
        ("cos(pi/3)", "cos(π/3) = 1/2 (exact)", "1/2"),

        # ─────────────────────────────────────────────────────────────
        # GROUP I — Physical-law specific instances at SI precision
        # ─────────────────────────────────────────────────────────────
        ("0.001 * 299792458^2",
         "E=mc² for 1 g = 8.9875517873681764×10¹³ J (c exact)",
         "8.9875517873681764"),
        ("8.31446261815324 * 273.15 / 101325",
         "PV=nRT: 1 mol IUPAC STP → V = 0.022413969545014… m³",
         "0.022413969545014"),
        ("100/300 - 100/400",
         "δS > 0: 100J heat 400K→300K → ΔS = 1/12 J/K (exact)",
         "1/12"),
        ("1 - 300/400",
         "Carnot η at T_c=300K, T_h=400K = 1/4 (exact)",
         "1/4"),
        ("2.897771955*10^-3 / 5778",
         "Wien displacement for Sun (T=5778K) → λ_max ≈ 5.01518×10⁻⁷ m (501.5 nm)",
         "5.01518"),
        ("Bohr radius",
         "a₀ = 5.29177211×10⁻¹¹ m (Wolfram CODATA precision)", "5.29177211"),
        ("Rydberg energy in eV",
         "E₁(H) = Ry = 13.605693123 eV (Rydberg, exact)", "13.605693123"),
        ("inverse fine structure constant",
         "1/α = 137.035999 (Sommerfeld, electromagnetic coupling)",
         "137.035999"),
        ("9.80665 m/s^2 in g",
         "g₀ = 9.80665 m/s² ≡ 1 standard gravity (defined exact, CGPM 1901)",
         "1 g"),

        # ─────────────────────────────────────────────────────────────
        # GROUP J — Astronomical constants (verified by reverse-conversion
        #   to canonical units, so the full defined integer is checked)
        # ─────────────────────────────────────────────────────────────
        ("149597870700 meters in AU",
         "AU = 149597870700 m exact (IAU 2012) ⇒ converts to 1 au",
         "1 au"),
        ("9460730472580800 meters in light years",
         "ly = 9460730472580800 m exact (c × Julian year) ⇒ 1 ly",
         "1 ly"),

        # ─────────────────────────────────────────────────────────────
        # GROUP K — Stack-specific anchors (PHI, BASE-27, K=3, k=7, Q16.16)
        # ─────────────────────────────────────────────────────────────
        ("(1 + sqrt(5)) / 2",
         "φ = (1+√5)/2 (PHI-axis hardware, golden ratio)",
         "1.61803398874"),
        ("3^3", "BASE-27 = 3³ = 27 (K=3 ternary triplet)", "27"),
        ("isprime(7)", "k=7 prime (coprime traversal)", "prime number"),
        ("round(0.5 * 65536)",
         "500ms anchor in Q16.16 raw = 32768",
         "32768"),
        ("round(0.7 * 65536)",
         "700ms anchor in Q16.16 raw = 45875",
         "45875"),
        ("round(0.8 * 65536)",
         "0.8 in Q16.16 raw = 52429 (corrected from 52428)",
         "52429"),
        ("round(0.150 * 65536)",
         "150ms in Q16.16 raw = 9830",
         "9830"),

        # ─────────────────────────────────────────────────────────────
        # GROUP L — Master equation / asymptotic
        # ─────────────────────────────────────────────────────────────
        ("limit n->infinity (1 + 1/n)^n",
         "lim (1+1/n)^n = e (compounding limit)", "e"),
        ("sum 1/n^2 from n=1 to infinity",
         "Basel problem: Σ 1/n² = π²/6", "π^2/6"),
        ("sum 1/2^n from n=1 to infinity",
         "Geometric series Σ (½)ⁿ = 1", "1"),
    ]

    print(f"\nVerifying {len(fundamental_math)} fundamental anchors...")

    results = [verifier.verify(eq, desc, exp) for eq, desc, exp in fundamental_math]

    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    verified = sum(1 for r in results if r["status"] == "verified")
    mismatch = sum(1 for r in results if r["status"] == "mismatch")
    failed = sum(1 for r in results if r["status"] in ("error", "failed"))
    total = len(results)
    pass_rate = verified / total if total else 0.0

    print(f"Total anchors: {total}")
    print(f"✅ Verified:   {verified}")
    print(f"⚠️  Mismatch:  {mismatch}")
    print(f"❌ Failed:     {failed}")
    print(f"\nPass rate: {pass_rate:.1%}")

    if mismatch:
        print("\n--- MISMATCHES (these are the drift-detection signals) ---")
        for r in results:
            if r["status"] == "mismatch":
                print(f"  • {r['description']}")
                print(f"    expected: {r['expected']}")
                print(f"    got:      {r.get('observed', '')[:120]}")

    if failed:
        print("\n--- FAILED (transient API or syntax) ---")
        for r in results:
            if r["status"] in ("error", "failed"):
                print(f"  • {r['description']}: {r.get('error', 'no result')}")

    print("\nNote: pass_rate is NOT a sigma. Real sigma claims need population")
    print("sweeps (see FixedPoint.lean's 65,536-value GPU verification).")

    output_file = Path("shared-data/data/fundamental_math_verification.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump({
            "app_id": app_id,
            "timestamp": time.time(),
            "total": total,
            "verified": verified,
            "mismatch": mismatch,
            "failed": failed,
            "pass_rate": pass_rate,
            "results": results,
        }, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
