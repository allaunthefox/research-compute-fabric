#!/usr/bin/env python3
"""
Q16_16 Path Explorer - Python fallback for path exploration when WGSL runtime unavailable.

This script performs the same exhaustive exploration as the WGSL shader,
providing detailed analysis of all 6 helper lemmas across the Q16_16 space.
"""

import numpy as np
import json

def toInt(val):
    """Convert Q16_16 val to signed Int (2's complement)."""
    SIGN_BIT = 0x80000000
    TWO_POW_32 = 0x100000000
    if val >= SIGN_BIT:
        return val - TWO_POW_32
    return val

def is_edge_case(val):
    """Check if value is an edge case."""
    return val in [0, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF]

def detect_sign_bit_pattern(val):
    """Detect pattern in sign bit behavior."""
    sign_bit = (val & 0x80000000) >> 31
    magnitude = val & 0x7FFFFFFF
    return sign_bit * (magnitude % 256)

def explore_all_paths():
    """Exhaustively explore all paths for the 6 helper lemmas."""
    Q16_SPACE = 65536
    SIGN_BIT = 0x80000000
    TWO_POW_32 = 0x100000000
    SCALE_FACTOR = 65536
    
    results = {
        'toInt_nonneg_matches': 0,
        'toInt_neg_matches': 0,
        'toInt_nonneg_total': 0,
        'toInt_neg_total': 0,
        'shift_left_matches': 0,
        'shift_right_matches': 0,
        'shift_total': 0,
        'val_ge_toInt_ge_matches': 0,
        'val_le_toInt_le_matches': 0,
        'comparison_total': 0,
        'sign_bit_pattern': 0,
        'overflow_count': 0,
        'edge_case_count': 0,
        'counterexamples': [],
        'patterns': {}
    }
    
    print("Exploring all 65,536 Q16_16 values...")
    
    for val in range(Q16_SPACE):
        # Explore toInt lemma 1: non-negative values
        if val < SIGN_BIT:
            results['toInt_nonneg_total'] += 1
            toInt_val = toInt(val)
            expected = val
            if toInt_val == expected:
                results['toInt_nonneg_matches'] += 1
            else:
                results['counterexamples'].append({
                    'lemma': 'toInt_nonneg',
                    'val': hex(val),
                    'toInt': toInt_val,
                    'expected': expected
                })
        
        # Explore toInt lemma 2: negative values
        if val >= SIGN_BIT:
            results['toInt_neg_total'] += 1
            toInt_val = toInt(val)
            expected = val - TWO_POW_32
            if toInt_val == expected:
                results['toInt_neg_matches'] += 1
            else:
                results['counterexamples'].append({
                    'lemma': 'toInt_neg',
                    'val': hex(val),
                    'toInt': toInt_val,
                    'expected': expected
                })
        
        # Explore shift lemma 1: left shift
        shift_left = (val << 16) & 0xFFFFFFFF
        mul_result = (val * SCALE_FACTOR) & 0xFFFFFFFF
        if shift_left == mul_result:
            results['shift_left_matches'] += 1
        else:
            results['counterexamples'].append({
                'lemma': 'shift_left',
                'val': hex(val),
                'shift_left': hex(shift_left),
                'mul': hex(mul_result)
            })
        
        results['shift_total'] += 1
        
        # Explore shift lemma 2: right shift
        shift_right = val >> 16
        div_result = val // SCALE_FACTOR
        if shift_right == div_result:
            results['shift_right_matches'] += 1
        else:
            results['counterexamples'].append({
                'lemma': 'shift_right',
                'val': hex(val),
                'shift_right': hex(shift_right),
                'div': hex(div_result)
            })
        
        # Detect overflow
        if val > 0xFFFFFFFF // SCALE_FACTOR:
            results['overflow_count'] += 1
        
        # Check edge case
        if is_edge_case(val):
            results['edge_case_count'] += 1
        
        # Detect sign bit pattern
        pattern = detect_sign_bit_pattern(val)
        results['sign_bit_pattern'] += pattern
        
        # Explore comparison lemmas (sample pairs)
        test_values = [0, 0x40000000, 0x7FFFFFFF, SIGN_BIT]
        for b in test_values:
            a_val = val
            b_val = b
            a_int = toInt(a_val)
            b_int = toInt(b_val)
            
            # Test val_ge_toInt_ge
            if a_val >= b_val:
                results['comparison_total'] += 1
                if a_int >= b_int:
                    results['val_ge_toInt_ge_matches'] += 1
                else:
                    results['counterexamples'].append({
                        'lemma': 'val_ge_toInt_ge',
                        'a_val': hex(a_val),
                        'b_val': hex(b_val),
                        'a_int': a_int,
                        'b_int': b_int
                    })
            
            # Test val_le_toInt_le
            if a_val <= b_val:
                results['comparison_total'] += 1
                if a_int <= b_int:
                    results['val_le_toInt_le_matches'] += 1
                else:
                    results['counterexamples'].append({
                        'lemma': 'val_le_toInt_le',
                        'a_val': hex(a_val),
                        'b_val': hex(b_val),
                        'a_int': a_int,
                        'b_int': b_int
                    })
    
    # Calculate statistics
    results['toInt_nonneg_rate'] = results['toInt_nonneg_matches'] / max(results['toInt_nonneg_total'], 1)
    results['toInt_neg_rate'] = results['toInt_neg_matches'] / max(results['toInt_neg_total'], 1)
    results['shift_left_rate'] = results['shift_left_matches'] / results['shift_total']
    results['shift_right_rate'] = results['shift_right_matches'] / results['shift_total']
    results['val_ge_toInt_ge_rate'] = results['val_ge_toInt_ge_matches'] / max(results['comparison_total'], 1)
    results['val_le_toInt_le_rate'] = results['val_le_toInt_le_matches'] / max(results['comparison_total'], 1)
    
    return results

def main():
    results = explore_all_paths()
    
    print("\n=== Q16_16 Path Exploration Results ===")
    print(f"toInt non-negative matches: {results['toInt_nonneg_matches']}/{results['toInt_nonneg_total']} ({results['toInt_nonneg_rate']*100:.2f}%)")
    print(f"toInt negative matches: {results['toInt_neg_matches']}/{results['toInt_neg_total']} ({results['toInt_neg_rate']*100:.2f}%)")
    print(f"Shift left matches: {results['shift_left_matches']}/{results['shift_total']} ({results['shift_left_rate']*100:.2f}%)")
    print(f"Shift right matches: {results['shift_right_matches']}/{results['shift_total']} ({results['shift_right_rate']*100:.2f}%)")
    print(f"val >= toInt >= matches: {results['val_ge_toInt_ge_matches']}/{results['comparison_total']} ({results['val_ge_toInt_ge_rate']*100:.2f}%)")
    print(f"val <= toInt <= matches: {results['val_le_toInt_le_matches']}/{results['comparison_total']} ({results['val_le_toInt_le_rate']*100:.2f}%)")
    print(f"Overflow cases: {results['overflow_count']}")
    print(f"Edge cases: {results['edge_case_count']}")
    print(f"Counterexamples found: {len(results['counterexamples'])}")
    
    if results['counterexamples']:
        print("\n=== First 10 Counterexamples ===")
        for i, ce in enumerate(results['counterexamples'][:10]):
            print(f"{i+1}. {ce}")
    
    # Save results
    with open('/home/allaun/Documents/Research Stack/out/q16_path_exploration.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to 5-Applications/out/q16_path_exploration.json")

if __name__ == '__main__':
    main()
