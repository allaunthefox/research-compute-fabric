#!/usr/bin/env python3
"""
Analyze effects of quaternary logic gate preprocessing on enwik9.
Implements various quaternary transformations and measures impact on compressibility.
"""

import zlib
import math
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
ENWIK9_PATH = REPO_ROOT / "hutter_bind_implementation" / "enwik9"

def extract_waveform(data, window_size=1024):
    """Extract waveform from data using sliding window."""
    waveform = []
    n_windows = len(data) // window_size
    
    for i in range(n_windows):
        window = data[i*window_size:(i+1)*window_size]
        energy = sum(window)
        waveform.append(energy)
    
    return waveform

def calculate_entropy(data):
    """Calculate Shannon entropy of data."""
    if not data:
        return 0.0
    
    freq = Counter(data)
    total = len(data)
    entropy = 0.0
    
    for count in freq.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    
    return entropy

def byte_to_quaternary(byte_val):
    """Convert a byte (0-255) to 4 quaternary digits (base-4)."""
    quaternary = []
    for _ in range(4):
        quaternary.append(byte_val % 4)
        byte_val //= 4
    return quaternary[::-1]  # Most significant digit first

def quaternary_to_byte(quad_digits):
    """Convert 4 quaternary digits back to a byte."""
    byte_val = 0
    for digit in quad_digits:
        byte_val = byte_val * 4 + digit
    return byte_val

def preprocess_quaternary_group(data):
    """
    Preprocess: Convert bytes to quaternary digits, group by position.
    This separates the 4-bit planes into separate streams.
    """
    if not data:
        return b''
    
    # Separate into 4 streams (one for each quaternary position)
    streams = [[], [], [], []]
    
    for byte_val in data:
        quad = byte_to_quaternary(byte_val)
        for pos, digit in enumerate(quad):
            streams[pos].append(digit)
    
    # Re-encode: each stream becomes bytes (2 digits per byte)
    result = bytearray()
    for stream in streams:
        # Pad stream to even length
        if len(stream) % 2 == 1:
            stream.append(0)
        
        # Pack 2 quaternary digits per byte
        for i in range(0, len(stream), 2):
            packed = stream[i] * 4 + stream[i+1]
            result.append(packed)
    
    return bytes(result)

def preprocess_quaternary_transform(data, transform_type='identity'):
    """
    Apply quaternary logic gate transformations.
    transform_type: 'identity', 'not', 'cycle', 'invert_high'
    """
    if not data:
        return b''
    
    result = bytearray()
    
    for byte_val in data:
        quad = byte_to_quaternary(byte_val)
        
        if transform_type == 'identity':
            transformed = quad
        elif transform_type == 'not':
            # Invert each digit (3-x)
            transformed = [3 - d for d in quad]
        elif transform_type == 'cycle':
            # Cycle digits: [a,b,c,d] -> [b,c,d,a]
            transformed = quad[1:] + [quad[0]]
        elif transform_type == 'invert_high':
            # Invert only high-order digits
            transformed = [3 - d if i < 2 else d for i, d in enumerate(quad)]
        else:
            transformed = quad
        
        # Convert back to byte
        result.append(quaternary_to_byte(transformed))
    
    return bytes(result)

def preprocess_quaternary_smooth(data):
    """
    Smooth quaternary transitions by reducing high-frequency changes.
    If a digit differs from previous, interpolate or clamp.
    """
    if not data or len(data) < 2:
        return data
    
    result = bytearray()
    prev_quad = byte_to_quaternary(data[0])
    result.append(data[0])
    
    for byte_val in data[1:]:
        curr_quad = byte_to_quaternary(byte_val)
        smoothed_quad = []
        
        for i in range(4):
            diff = abs(curr_quad[i] - prev_quad[i])
            if diff > 1:
                # Clamp to reduce large transitions
                if curr_quad[i] > prev_quad[i]:
                    smoothed_quad.append(prev_quad[i] + 1)
                else:
                    smoothed_quad.append(prev_quad[i] - 1)
            else:
                smoothed_quad.append(curr_quad[i])
        
        # Clamp to valid range
        smoothed_quad = [max(0, min(3, d)) for d in smoothed_quad]
        result.append(quaternary_to_byte(smoothed_quad))
        prev_quad = smoothed_quad
    
    return bytes(result)

def analyze_preprocessing(data, method_name, preprocess_func):
    """Analyze the effect of a preprocessing method."""
    print(f"\n{'=' * 60}")
    print(f"Method: {method_name}")
    print(f"{'=' * 60}")
    
    # Apply preprocessing
    start = time.time()
    preprocessed = preprocess_func(data)
    preprocess_time = time.time() - start
    
    # Calculate metrics
    original_entropy = calculate_entropy(data)
    preprocessed_entropy = calculate_entropy(preprocessed)
    
    # Compress both
    original_compressed = zlib.compress(data, level=9)
    preprocessed_compressed = zlib.compress(preprocessed, level=9)
    
    # Extract waveforms
    original_waveform = extract_waveform(data)
    preprocessed_waveform = extract_waveform(preprocessed)
    
    # Calculate waveform difference
    if len(original_waveform) == len(preprocessed_waveform):
        waveform_diff = sum(abs(a - b) for a, b in zip(original_waveform, preprocessed_waveform))
        waveform_diff_norm = waveform_diff / len(original_waveform)
    else:
        waveform_diff = None
        waveform_diff_norm = None
    
    print(f"Original size: {len(data):,} bytes")
    print(f"Preprocessed size: {len(preprocessed):,} bytes")
    print(f"Size change: {len(preprocessed) / len(data):.4f}x")
    print(f"\nOriginal entropy: {original_entropy:.4f} bits/byte")
    print(f"Preprocessed entropy: {preprocessed_entropy:.4f} bits/byte")
    print(f"Entropy change: {preprocessed_entropy - original_entropy:+.4f}")
    print(f"\nOriginal compressed: {len(original_compressed):,} bytes ({len(original_compressed) / len(data):.4f}x)")
    print(f"Preprocessed compressed: {len(preprocessed_compressed):,} bytes ({len(preprocessed_compressed) / len(preprocessed):.4f}x)")
    print(f"Compression ratio change: {(len(preprocessed_compressed) / len(preprocessed)) / (len(original_compressed) / len(data)):+.4f}x")
    print(f"\nPreprocess time: {preprocess_time:.2f}s")
    print(f"Waveform difference: {waveform_diff_norm:.2f} avg energy per window" if waveform_diff_norm is not None else "Waveform difference: N/A (length mismatch)")
    
    return {
        'method': method_name,
        'preprocessed_size': len(preprocessed),
        'size_ratio': len(preprocessed) / len(data),
        'original_entropy': original_entropy,
        'preprocessed_entropy': preprocessed_entropy,
        'entropy_change': preprocessed_entropy - original_entropy,
        'original_compressed': len(original_compressed),
        'preprocessed_compressed': len(preprocessed_compressed),
        'compression_ratio_change': (len(preprocessed_compressed) / len(preprocessed)) / (len(original_compressed) / len(data)),
        'preprocess_time': preprocess_time,
        'waveform_diff_norm': waveform_diff_norm
    }

import time

def main():
    print("=" * 60)
    print("Quaternary Logic Gate Preprocessing Analysis")
    print("=" * 60)
    
    # Load enwik9 (sample first 10MB for faster analysis)
    print("\nLoading enwik9 (first 10MB)...")
    with open(ENWIK9_PATH, "rb") as f:
        data = f.read(10_000_000)  # 10MB sample
    
    print(f"Sample size: {len(data):,} bytes")
    
    # Test different preprocessing methods
    results = []
    
    # Method 1: Quaternary grouping (separate bit planes)
    results.append(analyze_preprocessing(
        data, 
        "Quaternary Grouping (Bit Plane Separation)",
        preprocess_quaternary_group
    ))
    
    # Method 2: Quaternary NOT gate
    results.append(analyze_preprocessing(
        data,
        "Quaternary NOT Gate (Digit Inversion)",
        lambda d: preprocess_quaternary_transform(d, 'not')
    ))
    
    # Method 3: Quaternary Cycle (rotate digits)
    results.append(analyze_preprocessing(
        data,
        "Quaternary Cycle (Digit Rotation)",
        lambda d: preprocess_quaternary_transform(d, 'cycle')
    ))
    
    # Method 4: Quaternary Invert High (invert high-order digits)
    results.append(analyze_preprocessing(
        data,
        "Quaternary Invert High (High-Order Inversion)",
        lambda d: preprocess_quaternary_transform(d, 'invert_high')
    ))
    
    # Method 5: Quaternary Smoothing (reduce high-frequency transitions)
    results.append(analyze_preprocessing(
        data,
        "Quaternary Smoothing (Transition Clamping)",
        preprocess_quaternary_smooth
    ))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("{:<40} {:<12} {:<12} {:<12} {:<12}".format('Method', 'Size Ratio', 'Entropy Δ', 'Comp Δ', 'Wave Δ'))
    print("-" * 88)
    
    for r in results:
        entropy_str = "{:+.4f}".format(r['entropy_change'])
        comp_str = "{:+.4f}".format(r['compression_ratio_change'])
        wave_str = "{:.2f}".format(r['waveform_diff_norm']) if r['waveform_diff_norm'] is not None else "N/A"
        print("{:<40} {:<12.4f} {:<12} {:<12} {:<12}".format(r['method'], r['size_ratio'], entropy_str, comp_str, wave_str))
    
    print("\n" + "=" * 60)
    print("KEY INSIGHTS")
    print("=" * 60)
    
    best_compression = min(results, key=lambda x: x['compression_ratio_change'])
    print(f"Best compression improvement: {best_compression['method']}")
    print(f"Compression ratio change: {best_compression['compression_ratio_change']:+.4f}x")
    
    best_entropy = min(results, key=lambda x: x['preprocessed_entropy'])
    print(f"\nLowest entropy: {best_entropy['method']}")
    print(f"Entropy: {best_entropy['preprocessed_entropy']:.4f} bits/byte (original: {results[0]['original_entropy']:.4f})")
    
    best_waveform = min(results, key=lambda x: x['waveform_diff_norm'] if x['waveform_diff_norm'] is not None else float('inf'))
    print(f"\nSmallest waveform change: {best_waveform['method']}")
    print(f"Waveform difference: {best_waveform['waveform_diff_norm']:.2f} avg energy")
    
    print("\n" + "=" * 60)
    print("QUATERNARY LOGIC THEORY")
    print("=" * 60)
    print("Quaternary logic uses 4 states (0, 1, 2, 3) instead of binary's 2.")
    print("Each byte (8 bits) can be represented as 4 quaternary digits (4^4 = 256).")
    print("\nPotential benefits for preprocessing:")
    print("1. Bit plane separation: Groups similar-position digits together")
    print("2. Smoothing: Reduces high-frequency transitions")
    print("3. Logic gates: Can create patterns exploitable by compressors")
    print("\nPotential drawbacks:")
    print("1. May increase entropy if transformation adds complexity")
    print("2. May not improve standard compression (gzip, etc.)")
    print("3. Requires inverse transformation for decompression")

if __name__ == "__main__":
    main()
