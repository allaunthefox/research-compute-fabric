#!/usr/bin/env python3
"""
Q16_16 LUT Generator - Python fallback for LUT generation when WGSL runtime unavailable.

This script computes all combinations of Q16_16 operations and generates a lookup table.
For each pair (a, b) in Q16_16 space (65,536² = 4,294,967,296 combinations), it computes:
  - add(a, b)
  - sub(a, b)
  - mul(a, b)
  - div(a, b) (when b != 0)
  - max(a, b)
  - min(a, b)
  - neg(a)
  - abs(a)

The output is a packed LUT that can be used for fast hardware implementation.
"""

import numpy as np
import json
from pathlib import Path

def q16_add(a, b):
    """Q16_16 addition (wrapping)."""
    return (a + b) & 0xFFFFFFFF

def q16_sub(a, b):
    """Q16_16 subtraction (wrapping)."""
    return (a - b) & 0xFFFFFFFF

def q16_mul(a, b):
    """Q16_16 multiplication (high 32 bits of 64-bit product)."""
    prod = (a * b) >> 16
    return prod & 0xFFFFFFFF

def q16_div(a, b):
    """Q16_16 division (with division by zero handling)."""
    if b == 0:
        return 0xFFFFFFFF  # Division by zero marker
    numerator = (a << 16) & 0xFFFFFFFFFFFFFFFF
    return (numerator // b) & 0xFFFFFFFF

def q16_max(a, b):
    """Q16_16 maximum (unsigned comparison)."""
    return a if a > b else b

def q16_min(a, b):
    """Q16_16 minimum (unsigned comparison)."""
    return a if a < b else b

def q16_neg(a):
    """Q16_16 negation (two's complement)."""
    return (-a) & 0xFFFFFFFF

def q16_abs(a):
    """Q16_16 absolute value (sign bit check)."""
    if a & 0x80000000:
        return q16_neg(a)
    return a

def generate_lut_sample():
    """Generate a sample LUT (not full 4.3B combinations due to memory constraints)."""
    Q16_SPACE = 65536
    SAMPLE_SIZE = 1000  # Sample size for demonstration
    
    print(f"Generating sample Q16_16 LUT ({SAMPLE_SIZE} combinations)...")
    print(f"Full LUT would require {Q16_SPACE * Q16_SPACE:,} combinations (4.3 billion)")
    print(f"Full LUT size: {(Q16_SPACE * Q16_SPACE * 32):,} bytes ({(Q16_SPACE * Q16_SPACE * 32 / (1024**3)):.2f} GB)")
    
    # Generate sample LUT
    lut = []
    for i in range(SAMPLE_SIZE):
        a = (i * 137) % Q16_SPACE  # Pseudo-random a
        b = (i * 251) % Q16_SPACE  # Pseudo-random b
        
        entry = {
            'a': a,
            'b': b,
            'add': q16_add(a, b),
            'sub': q16_sub(a, b),
            'mul': q16_mul(a, b),
            'div': q16_div(a, b),
            'max': q16_max(a, b),
            'min': q16_min(a, b),
            'neg': q16_neg(a),
            'abs': q16_abs(a)
        }
        lut.append(entry)
    
    # Save sample LUT
    output_path = Path('/home/allaun/Documents/Research Stack/out/q16_lut_sample.json')
    with open(output_path, 'w') as f:
        json.dump({
            'metadata': {
                'q16_space': Q16_SPACE,
                'total_combinations': Q16_SPACE * Q16_SPACE,
                'sample_size': SAMPLE_SIZE,
                'full_lut_size_bytes': Q16_SPACE * Q16_SPACE * 32,
                'full_lut_size_gb': (Q16_SPACE * Q16_SPACE * 32) / (1024**3)
            },
            'lut': lut
        }, f, indent=2)
    
    print(f"Sample LUT saved to {output_path}")
    print(f"Sample entries: {len(lut)}")
    
    # Statistics
    adds = [e['add'] for e in lut]
    muls = [e['mul'] for e in lut]
    divs = [e['div'] for e in lut]
    
    print(f"\nStatistics:")
    print(f"  Add range: [{min(adds)}, {max(adds)}]")
    print(f"  Mul range: [{min(muls)}, {max(muls)}]")
    print(f"  Div by zero: {divs.count(0xFFFFFFFF)}")
    
    return lut

def generate_full_lut_chunked():
    """
    Generate full LUT in chunks to avoid memory issues.
    This would generate the actual 4.3B combinations but is disabled by default.
    """
    Q16_SPACE = 65536
    CHUNK_SIZE = 10000  # Process in chunks
    
    print(f"Generating full Q16_16 LUT in chunks of {CHUNK_SIZE}...")
    print(f"Total combinations: {Q16_SPACE * Q16_SPACE:,}")
    
    output_dir = Path('/home/allaun/Documents/Research Stack/out/q16_lut_chunks')
    output_dir.mkdir(exist_ok=True)
    
    chunk_count = 0
    for chunk_start in range(0, Q16_SPACE * Q16_SPACE, CHUNK_SIZE):
        chunk_end = min(chunk_start + CHUNK_SIZE, Q16_SPACE * Q16_SPACE)
        
        lut_chunk = []
        for idx in range(chunk_start, chunk_end):
            a = idx // Q16_SPACE
            b = idx % Q16_SPACE
            
            entry = {
                'a': a,
                'b': b,
                'add': q16_add(a, b),
                'sub': q16_sub(a, b),
                'mul': q16_mul(a, b),
                'div': q16_div(a, b),
                'max': q16_max(a, b),
                'min': q16_min(a, b),
                'neg': q16_neg(a),
                'abs': q16_abs(a)
            }
            lut_chunk.append(entry)
        
        # Save chunk
        chunk_file = output_dir / f'chunk_{chunk_count:06d}.json'
        with open(chunk_file, 'w') as f:
            json.dump(lut_chunk, f)
        
        chunk_count += 1
        if chunk_count % 100 == 0:
            print(f"  Processed {chunk_end:,} / {Q16_SPACE * Q16_SPACE:,} combinations ({chunk_end / (Q16_SPACE * Q16_SPACE) * 100:.2f}%)")
    
    print(f"Full LUT saved to {output_dir} in {chunk_count} chunks")

def main():
    print("Q16_16 LUT Generator")
    print("=" * 50)
    
    # Generate sample LUT (for demonstration)
    generate_lut_sample()
    
    # Note: Full LUT generation is disabled by default due to memory constraints
    # To generate the full 4.3B combination LUT, uncomment the following line:
    # generate_full_lut_chunked()
    
    print("\nNote: Full LUT generation (4.3B combinations) requires ~137 GB of storage.")
    print("Use the WGSL shader (q16_lut_generator.wgsl) with GPU for full LUT generation.")

if __name__ == '__main__':
    main()
