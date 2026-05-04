#!/usr/bin/env python3
"""
Unified Math-First Tagger
Expands 7 domain-centric patterns into 9 math-centric patterns by adding
Inequalities & Constraints and Atomic Assignments.

Priority: specialized mathematical operators are checked BEFORE generic '='
to prevent assignment_boundary from swallowing differential equations,
coupling terms, etc.

Pipeline: equations_tagged.parquet + unknown_refined.parquet → unified 9-pattern parquet
"""

import pyarrow.parquet as pq
import pyarrow as pa
import pandas as pd
import re
import json
from collections import Counter
from datetime import datetime

BASE = "/home/allaun/Documents/Research Stack/3-Mathematical-Models/equations_parquet_tagged"
INPUT_TAGGED = f"{BASE}/equations_tagged_20260504_134248.parquet"
INPUT_REFINED = f"{BASE}/unknown_refined_20260504.parquet"
OUTPUT_FILE = f"{BASE}/equations_unified_9pattern.parquet"
SUMMARY_FILE = f"{BASE}/unified_9pattern_summary.json"

# ── 9 Math-First Patterns (priority order matters) ───────────────────────────

def classify_unified(eq: str) -> str:
    text = eq.strip()
    if not text:
        return "unknown"

    lowered = text.lower()

    # 1. GRADIENT — derivatives, flows, geodesics (check BEFORE generic '=')
    if re.search(r'[∂∇∆]|\\dot|\\ddot|\\frac\{d[^}]*\}\{d[^}]*\}', text):
        return "gradient"

    # 2. ENTROPY — information theory, logarithmic
    if re.search(r'\\log\b|log\s*\(|ln\s*\(|entropy|shannon|information\s+(?:theory|gain)|kl\s+divergence', lowered):
        return "entropy"

    # 3. COUPLING — interactions, oscillators, Dirac notation, plain trig
    if re.search(r'\\sin|\\cos|\\exp\b|\bsin\b|\bcos\b|\btan\b|\bexp\b|e\^|⟨|⟩|\\bra|\\ket|oscillator|interaction|coupling|phase|braid|knot', lowered):
        return "coupling"

    # 4. MASS — ratios, fractions, densities
    if re.search(r'\\frac|(?<=\w)/(?=\w)|density|ratio|mass\b|weight\b|percentage', lowered):
        return "mass"

    # 5. SCALING — power laws, exponents, allometry, approximations
    if re.search(r'\^|\\propto|∝|≈|∼|power\s+law|exponent|allometry|arrhenius|boltzmann|logistic|sigmoid|hill', lowered):
        return "scaling"

    # 6. FEEDBACK — recurrence, dynamical systems, control
    if re.search(r'_{t\+1}|_{n\+1}|_{k\+1}|_{i\+1}|_{t-1}|_{n-1}|_{k-1}|_{i-1}|iterate|recurrence|feedback|control|adaptive|regulate|update|dynamical|homeostasis|state\s+space', lowered):
        return "feedback"

    # 7. CHAIN — compositions, sequences, pipelines
    if re.search(r'\\circ|compose|sequence|pipeline|cascade|layer|encode.*decode|transform', lowered):
        return "chain"

    # 8. INEQUALITY_CONSTRAINT — bounds, constraints (no =, or inequality dominant)
    if re.search(r'[><≥≤]', text):
        # Only classify as inequality if there's no =, or inequality chars outnumber =
        if '=' not in text or len(re.findall(r'[><≥≤]', text)) > text.count('='):
            return "inequality_constraint"

    # 9. ASSIGNMENT_BOUNDARY — simple definitions, boundary conditions
    if '=' in text:
        # Must be a simple assignment: exactly one =, short, no complex operators,
        # and not a sentence fragment full of English words.
        if text.count('=') != 1:
            pass  # multiple = signs are not simple assignments
        elif len(text) > 60:
            pass  # too long to be a simple boundary condition
        else:
            # Exclude if it contains common English words (sentence fragments)
            common_words = {'the', 'and', 'for', 'with', 'where', 'which', 'that', 'from',
                            'this', 'these', 'there', 'then', 'than', 'when', 'what', 'how',
                            'who', 'why', 'how', 'are', 'was', 'were', 'been', 'have', 'has',
                            'had', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
                            'not', 'but', 'or', 'yet', 'so', 'if', 'because', 'since', 'until',
                            'while', 'although', 'though', 'unless', 'whether', 'either', 'neither',
                            'both', 'all', 'any', 'some', 'many', 'most', 'few', 'several',
                            'various', 'certain', 'other', 'another', 'such', 'same', 'different',
                            'scenario', 'component', 'annihilates', 'into', 'onto', 'upon'}
            words_found = set(re.findall(r'\b[a-z]+\b', lowered))
            if len(words_found & common_words) <= 1:
                # Also exclude complex math operators
                complex_ops = r'[∂∇∆∫∑∏±∓×÷√∧∨¬⇒⇔∀∃⟨⟩|∈∉⊂⊃⊆⊇∪∩→↦<>≥≤^\\]'
                if not re.search(complex_ops, text):
                    return "assignment_boundary"

    # Fallback for remaining equations with =
    if '=' in text:
        # Detect actual function composition / sequence structure for chain
        if re.search(r'\\to|→.*=|=.*→|\\mapsto|↦', text) or text.count('=') >= 3:
            return "chain"
        # Detect recurrence-like structure without explicit subscript
        if re.search(r'\b[a-z]_[a-z]\b|\b[a-z]_{\w+}\b', text) and re.search(r'\b[a-z]_[a-z]\b.*\b[a-z]_[a-z]\b', text):
            return "coupling"  # Two indexed variables interacting
        # Generic algebraic relation with = → coupling
        return "coupling"

    return "unknown"


def main():
    print("═" * 60)
    print("  Unified Math-First Tagger (9 Patterns)")
    print("═" * 60)

    # ── Load full tagged dataset (single source of truth) ──────────────────
    print(f"\nLoading full tagged dataset from {INPUT_TAGGED}...")
    df = pq.read_table(INPUT_TAGGED).to_pandas()
    print(f"  Loaded {len(df):,} equations")
    n_unknown = (df['pattern'] == 'unknown').sum()
    print(f"  Original unknowns: {n_unknown:,}")

    # ── Load refined text for unknown rows only ────────────────────────────
    print(f"\nLoading refined text for unknowns from {INPUT_REFINED}...")
    df_refined = pq.read_table(INPUT_REFINED).to_pandas()
    print(f"  Loaded {len(df_refined):,} refined rows")

    # Merge refined text into the main dataframe (left join on equation_id)
    if 'equation_id' in df_refined.columns:
        refined_map = df_refined.set_index('equation_id')['refined_equation'].to_dict()
        # Only apply refined text to originally-unknown rows
        mask = df['pattern'] == 'unknown'
        df.loc[mask, 'refined_equation'] = df.loc[mask, 'equation_id'].map(refined_map)
        n_merged = df.loc[mask, 'refined_equation'].notna().sum()
        print(f"  Merged refined text for {n_merged:,} unknown rows")
    else:
        print("  [!] No equation_id in refined file; using raw equation text for all")
        df['refined_equation'] = None

    # ── Choose text to classify ─────────────────────────────────────────────
    print("\nPreparing classification text (refined > raw)...")
    df['text_to_classify'] = df['refined_equation'].fillna(df['equation']).astype(str)
    n_refined = df['refined_equation'].notna().sum()
    print(f"  Using refined text for {n_refined:,} rows, raw for {len(df) - n_refined:,} rows")

    # ── Apply unified math-first classification ────────────────────────────
    print("\nApplying unified math-first classification...")
    df['unified_pattern'] = df['text_to_classify'].apply(classify_unified)

    # ── Report distribution ─────────────────────────────────────────────────
    counts = Counter(df['unified_pattern'])
    total = len(df)

    print("\n  Unified 9-Pattern Distribution:")
    print("  " + "-" * 50)
    for pat, cnt in counts.most_common():
        pct = cnt / total * 100
        bar = "█" * int(pct / 2)
        print(f"  {pat:25s}: {cnt:>9,} ({pct:5.1f}%) {bar}")
    print("  " + "-" * 50)
    print(f"  {'TOTAL':25s}: {total:>9,} (100.0%)")

    # Cross-tab: original pattern vs unified pattern (for non-unknowns)
    known_mask = df['pattern'] != 'unknown'
    if known_mask.sum() > 0:
        print("\n  Original → Unified mapping (non-unknown rows only):")
        crosstab = pd.crosstab(df.loc[known_mask, 'pattern'], df.loc[known_mask, 'unified_pattern'])
        print(crosstab.to_string())

    # ── Write unified parquet ────────────────────────────────────────────────
    print(f"\nWriting unified parquet to {OUTPUT_FILE}...")
    table = pa.Table.from_pandas(df)
    pq.write_table(table, OUTPUT_FILE, compression="zstd")
    print(f"  Done. Size: {OUTPUT_FILE}")

    # ── Write pattern-specific parquets ─────────────────────────────────────
    for pattern in counts:
        subset = df[df['unified_pattern'] == pattern]
        pat_file = f"{BASE}/{pattern}_equations_unified.parquet"
        pq.write_table(pa.Table.from_pandas(subset), pat_file, compression="zstd")
        print(f"  {pattern}: {len(subset):,} rows → {pat_file}")

    # ── Write summary JSON ─────────────────────────────────────────────────
    summary = {
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "total_equations": total,
        "pattern_counts": dict(counts.most_common()),
        "pattern_percentages": {k: round(v/total*100, 2) for k, v in counts.items()},
        "sources": [INPUT_TAGGED, INPUT_REFINED],
        "output_file": OUTPUT_FILE,
        "classifier": "unified_math_first",
        "num_patterns": 9,
        "patterns": [
            "assignment_boundary",
            "inequality_constraint",
            "gradient",
            "entropy",
            "coupling",
            "mass",
            "scaling",
            "feedback",
            "chain"
        ]
    }
    with open(SUMMARY_FILE, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary written to {SUMMARY_FILE}")

    # ── Extract samples for manual review ───────────────────────────────────
    samples = {}
    for pattern in counts:
        subset = df[df['unified_pattern'] == pattern]
        n = min(15, len(subset))
        if n > 0:
            samples[pattern] = subset['equation'].sample(n).tolist()

    sample_file = f"{BASE}/../unified_9pattern_samples.json"
    with open(sample_file, "w") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    print(f"Samples written to {sample_file}")

    print("\n" + "═" * 60)
    print("  UNIFIED MATH-FIRST TAGGING COMPLETE")
    print("═" * 60)


if __name__ == "__main__":
    main()
