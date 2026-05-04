#!/usr/bin/env python3
import pyarrow.parquet as pq
import pandas as pd
import re
import json
from collections import Counter

# Unicode mapping for visual math reconstruction (common LaTeX-to-Unicode artifacts)
UNICODE_RECOVERY = {
    '\uf8eb': '(', # top left bracket
    '\uf8ed': '(', # bottom left
    '\uf8ec': '|', # middle left
    '\uf8f6': ')', # top right
    '\uf8f8': ')', # bottom right
    '\uf8f7': '|', # middle right
    '\u2212': '-', # minus
    '\u2217': '*', # asterisk
    '\u2216': '\\', # backslash
}

def refine_equation(eq):
    if not isinstance(eq, str): return ""
    
    # 1. Unicode Recovery
    for k, v in UNICODE_RECOVERY.items():
        eq = eq.replace(k, v)
    
    # 2. Strip obvious citation/metadata fragments
    eq = re.sub(r'arXiv:\d+\.\d+v\d+', '', eq)
    eq = re.sub(r'\(\d+\)', '', eq) # Eq numbers like (7)
    
    # 3. Clean whitespace
    eq = re.sub(r'\s+', ' ', eq).strip()
    
    return eq

def is_math_dense(eq):
    # A heuristic: must have at least one operator and not too many common words
    operators = r'[=><≥≤≈∼∇∂∫∑∏±∓×÷√]'
    common_words = {'the', 'and', 'is', 'where', 'which', 'that', 'with'}
    
    if not re.search(operators, eq): return False
    
    words = re.findall(r'\b\w+\b', eq.lower())
    if len(words) > 15: # Too wordy, likely text with a bit of math
        math_score = len(re.findall(operators, eq))
        word_score = sum(1 for w in words if w in common_words)
        if word_score > math_score * 2:
            return False
            
    return True

def main():
    INPUT_FILE = "3-Mathematical-Models/equations_parquet_tagged/unknown_equations_20260504_134248.parquet"
    OUTPUT_FILE = "3-Mathematical-Models/equations_parquet_tagged/unknown_refined_20260504.parquet"
    
    print(f"Loading {INPUT_FILE}...")
    df = pq.read_table(INPUT_FILE).to_pandas()
    
    print("Refining equations...")
    df['refined_equation'] = df['equation'].apply(refine_equation)
    
    print("Filtering noise...")
    df['is_math'] = df['refined_equation'].apply(is_math_dense)
    
    math_df = df[df['is_math']].copy()
    noise_df = df[~df['is_math']].copy()
    
    print(f"Refinement Summary:")
    print(f"  Total: {len(df)}")
    print(f"  Math Dense: {len(math_df)} ({len(math_df)/len(df)*100:.1f}%)")
    print(f"  Noise/Text: {len(noise_df)} ({len(noise_df)/len(df)*100:.1f}%)")
    
    # Save refined math to a new parquet
    import pyarrow as pa
    table = pa.Table.from_pandas(math_df)
    pq.write_table(table, OUTPUT_FILE)
    print(f"Saved refined math to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
