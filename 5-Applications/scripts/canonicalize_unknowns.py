#!/usr/bin/env python3
import re
from collections import Counter
import pyarrow.parquet as pq
import pandas as pd
import json

def canonicalize(eq):
    """
    Replace variables with placeholders to find structural duplicates.
    Example: 'a + b = c' -> 'v0 + v1 = v2'
    """
    # Replace common math operators with standard forms for matching
    eq = eq.replace('−', '-').replace('−', '-')
    
    # Identify variables (simple alphabetic letters or greek)
    # This is a heuristic first pass
    vars_found = []
    
    # Tokenize words that are likely variables (single letters or specific greek)
    # Exclude common math functions like sin, log, min
    funcs = {'sin', 'cos', 'tan', 'log', 'exp', 'min', 'max', 'poly', 'inf', 'sup', 'arcsinh', 'sinh'}
    
    tokens = re.split(r'(\W)', eq)
    canonical_tokens = []
    var_map = {}
    
    for t in tokens:
        if re.match(r'^[a-zA-Z\u0370-\u03ff]$', t): # Single letter or greek
            if t.lower() not in funcs:
                if t not in var_map:
                    var_map[t] = f"v{len(var_map)}"
                canonical_tokens.append(var_map[t])
            else:
                canonical_tokens.append(t)
        else:
            canonical_tokens.append(t)
            
    return "".join(canonical_tokens)

def main():
    INPUT_FILE = "3-Mathematical-Models/equations_parquet_tagged/unknown_equations_20260504_134248.parquet"
    print(f"Loading unknowns...")
    table = pq.read_table(INPUT_FILE)
    df = table.to_pandas()
    
    # Filter for things that look like math (missing_parser_rules subset)
    # For now, let's just sample all and see top structures
    sample = df.sample(min(50000, len(df)))
    
    print("Canonicalizing 50,000 samples...")
    sample['structure'] = sample['equation'].apply(canonicalize)
    
    struct_counts = Counter(sample['structure'])
    
    top_structures = struct_counts.most_common(50)
    
    print("\nTop 10 Structural Variants:")
    for struct, count in top_structures[:10]:
        print(f"  {count:5} : {struct}")
        
    # Find "True Unknowns" (structures that appear only once)
    uniques = [s for s, c in struct_counts.items() if c == 1]
    
    report = {
        "top_structures": [{"structure": s, "count": c} for s, c in top_structures],
        "unique_structures_count": len(uniques),
        "total_sample": len(sample)
    }
    
    with open("3-Mathematical-Models/structural_discovery.json", "w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    main()
