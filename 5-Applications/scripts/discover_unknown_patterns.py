#!/usr/bin/env python3
import pyarrow.parquet as pq
import pandas as pd
import re
from collections import Counter
import json
import sys

INPUT_FILE = "3-Mathematical-Models/equations_parquet_tagged/unknown_equations_20260504_134248.parquet"
OUTPUT_REPORT = "3-Mathematical-Models/unknown_discovery_report.json"

COMMON_WORDS = {'the', 'and', 'is', 'where', 'which', 'this', 'that', 'with', 'for', 'holds', 'when', 'if', 'has', 'map'}
MATH_SYMBOLS = r'[=><≥≤≈∼∇∂∫∑∏⟨⟩|±∓×÷√∞∝∠∧∨∩∪⊂⊃⊆⊇∈∉∅∀∃∄]'
OCR_ARTIFACTS = r'[\uf800-\uf8ff]'

def classify(eq):
    if not isinstance(eq, str):
        return "malformed"
    
    # Check for OCR artifacts/malformed
    if re.search(OCR_ARTIFACTS, eq):
        return "malformed"
    
    # Check for natural language
    words = re.findall(r'\b\w+\b', eq.lower())
    if len(words) > 3:
        common_count = sum(1 for w in words if w in COMMON_WORDS)
        if common_count >= 2 or (len(words) > 10 and common_count >= 1):
            return "natural_language"
    
    # Check for math-like but unknown
    if re.search(MATH_SYMBOLS, eq):
        # Dirac notation?
        if '⟨' in eq or '⟩' in eq or '|' in eq:
            return "missing_parser_rules_dirac"
        # Big O?
        if re.search(r'\bO\(', eq):
            return "missing_parser_rules_bigo"
        # Generic missing rule
        return "missing_parser_rules_generic"

    # Metadata
    if re.search(r'\(\d+\)', eq) or 'Eq.' in eq:
        return "metadata_fragments"

    # Default
    return "undetermined"

def main():
    print(f"Reading {INPUT_FILE}...")
    table = pq.read_table(INPUT_FILE)
    df = table.to_pandas()
    
    print(f"Sampling 20,000 equations...")
    sample = df.sample(min(20000, len(df)))
    
    results = []
    counts = Counter()
    
    for _, row in sample.iterrows():
        eq = row['equation']
        cat = classify(eq)
        counts[cat] += 1
        results.append({
            'equation': eq,
            'category': cat,
            'id': row['equation_id'],
            'source': row['source']
        })
    
    report = {
        'total_rows': len(df),
        'sample_size': len(sample),
        'category_counts': dict(counts),
        'samples': {}
    }
    
    for cat in counts:
        report['samples'][cat] = [r['equation'] for r in results if r['category'] == cat][:10]

    with open(OUTPUT_REPORT, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Report written to {OUTPUT_REPORT}")
    for cat, count in counts.items():
        print(f"  {cat:30}: {count}")

if __name__ == "__main__":
    main()
