#!/usr/bin/env python3
"""
Convert Research Stack equation IDs to Phinary (Zeckendorf) representation.
Adapted from MOIM's phinary number system for equation indexing.
"""

import csv
from pathlib import Path
from typing import List, Tuple

def fib(n: int) -> int:
    """Compute nth Fibonacci number."""
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fib(n - 1) + fib(n - 2)

def find_largest_fib(n: int) -> int:
    """Find largest k such that fib(k+2) <= n."""
    k = 0
    while fib(k + 2) <= n:
        k += 1
    return k - 1

def nat_to_zeckendorf(n: int) -> List[int]:
    """Convert natural number to Zeckendorf representation (list of 0s and 1s)."""
    if n == 0:
        return [0]
    
    result = []
    remaining = n
    
    while remaining > 0:
        k = find_largest_fib(remaining)
        # Pad with zeros to reach position k
        while len(result) <= k:
            result.append(0)
        result[k] = 1
        remaining -= fib(k + 2)
    
    return result

def zeckendorf_to_nat(digits: List[int]) -> int:
    """Convert Zeckendorf digits back to natural number."""
    result = 0
    for idx, digit in enumerate(digits):
        result += digit * fib(idx + 2)
    return result

def valid_phinary_digits(digits: List[int]) -> bool:
    """Check if phinary digits satisfy Zeckendorf constraint (no adjacent 1s)."""
    for i in range(len(digits) - 1):
        if digits[i] == 1 and digits[i + 1] == 1:
            return False
    return True

def phinary_to_string(digits: List[int]) -> str:
    """Convert phinary digits to string representation."""
    return ''.join(str(d) for d in digits)

def equation_id_to_phinary(eq_id: int) -> Tuple[str, bool]:
    """Convert equation ID to phinary string representation."""
    digits = nat_to_zeckendorf(eq_id)
    valid = valid_phinary_digits(digits)
    return phinary_to_string(digits), valid

def process_math_model_map(input_path: str, output_path: str):
    """Process MATH_MODEL_MAP.tsv and add phinary representation."""
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find start of actual data (skip comment lines)
    start_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('1\t') or line.startswith('#\t'):
            start_idx = i
            break
    
    # Read header and data
    reader = csv.DictReader(lines[start_idx:], delimiter='\t')
    fieldnames = reader.fieldnames
    
    # Clean fieldnames (remove None values)
    fieldnames = [f for f in fieldnames if f is not None]
    
    # Add phinary column
    new_fieldnames = fieldnames + ['Phinary_ID', 'Phinary_Valid']
    
    with open(output_path, 'w', encoding='utf-8') as out:
        writer = csv.DictWriter(out, fieldnames=new_fieldnames, delimiter='\t')
        writer.writeheader()
        
        for row in reader:
            # Clean row dict (remove None keys)
            clean_row = {k: v for k, v in row.items() if k is not None}
            
            # Get equation ID
            eq_id_str = clean_row.get('#', clean_row.get('ID', '0'))
            try:
                eq_id = int(eq_id_str)
            except (ValueError, TypeError):
                eq_id = 0
            
            # Convert to phinary
            phinary_str, valid = equation_id_to_phinary(eq_id)
            
            # Add new columns
            clean_row['Phinary_ID'] = phinary_str
            clean_row['Phinary_Valid'] = 'TRUE' if valid else 'FALSE'
            
            writer.writerow(clean_row)
    
    print(f"✅ Converted equations to phinary representation")
    print(f"   Input:  {input_path}")
    print(f"   Output: {output_path}")

def analyze_phinary_distribution(input_path: str):
    """Analyze distribution of phinary representations."""
    phinary_lengths = {}
    valid_count = 0
    invalid_count = 0
    
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        for row in reader:
            phinary_id = row.get('Phinary_ID', '')
            is_valid = row.get('Phinary_Valid', 'FALSE') == 'TRUE'
            
            length = len(phinary_id)
            phinary_lengths[length] = phinary_lengths.get(length, 0) + 1
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
    
    print(f"\n📊 Phinary Distribution Analysis:")
    print(f"   Total equations: {valid_count + invalid_count}")
    print(f"   Valid phinary:   {valid_count}")
    print(f"   Invalid phinary: {invalid_count}")
    print(f"\n   Length distribution:")
    for length in sorted(phinary_lengths.keys()):
        print(f"   {length} digits: {phinary_lengths[length]} equations")

if __name__ == "__main__":
    base_path = Path(__file__).resolve().parent.parent.parent
    input_path = base_path / "3-Mathematical-Models" / "MATH_MODEL_MAP.tsv"
    output_path = base_path / "3-Mathematical-Models" / "MATH_MODEL_MAP_phinary.tsv"
    
    print("🔄 Converting equation IDs to phinary representation...")
    process_math_model_map(str(input_path), str(output_path))
    analyze_phinary_distribution(str(output_path))
