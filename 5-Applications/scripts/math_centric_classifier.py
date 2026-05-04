#!/usr/bin/env python3
import pyarrow.parquet as pq
import pandas as pd
import re
import json
from collections import Counter
import pyarrow as pa

INPUT_FILE = "3-Mathematical-Models/equations_parquet_tagged/unknown_refined_20260504.parquet"
OUTPUT_FILE = "3-Mathematical-Models/equations_parquet_tagged/math_centric_categorization.parquet"

# Math Primitives
PATTERNS = {
    "inequality_constraint": r'[><≥≤]',
    "assignment_boundary": r'^[^=]+=[^=]+$', # Simple single equals
    "dirac_notation": r'[⟨⟩|]',
    "asymptotic_complexity": r'\b[Oo]\(|[∼≈≃]',
    "differential_calculus": r'[∂∇∆]|d/d|\\dot|\\ddot',
    "sum_prod_operators": r'[∑∏∫]',
    "set_transformation": r'[∈∉⊂⊃⊆⊇∪∩→↦]',
    "logical_boolean": r'[∀∃∄∧∨¬⇒⇔]',
    "matrix_tensor": r'[\uf8eb-\uf8ff]|\\pmatrix|\\matrix|\\begin\{matrix\}',
}

def classify_math(eq):
    categories = []
    for name, regex in PATTERNS.items():
        if re.search(regex, eq):
            categories.append(name)
    
    if not categories:
        return "algebraic_generic"
    # Return the first match or a compound name? 
    # For now, let's just take the primary (first in PATTERNS)
    return categories[0]

def main():
    print(f"Loading refined unknowns from {INPUT_FILE}...")
    df = pq.read_table(INPUT_FILE).to_pandas()
    
    print("Applying Math-First categorization...")
    # Use a subset of the column to save memory if needed, but 1.21M is manageable in pandas
    df['math_pattern'] = df['refined_equation'].apply(classify_math)
    
    counts = Counter(df['math_pattern'])
    print("\nCategorization Results:")
    for cat, count in counts.most_common():
        print(f"  {cat:25}: {count:8} ({count/len(df)*100:4.1f}%)")
        
    # Save the results
    print(f"Saving to {OUTPUT_FILE}...")
    table = pa.Table.from_pandas(df)
    pq.write_table(table, OUTPUT_FILE)
    
    # Export samples for review
    report = {}
    for cat in counts:
        report[cat] = df[df['math_pattern'] == cat]['refined_equation'].sample(min(20, counts[cat])).tolist()
        
    with open("3-Mathematical-Models/math_centric_samples.json", "w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    main()
