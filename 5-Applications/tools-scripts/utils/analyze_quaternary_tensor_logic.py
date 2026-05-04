#!/usr/bin/env python3
"""
Analyze quaternary logic gates applied to tensor data.
Explores how quaternary transformations affect tensor compressibility and structure.
"""

import numpy as np
import zlib
import math
from collections import Counter

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
    return quaternary[::-1]

def quaternary_to_byte(quad_digits):
    """Convert 4 quaternary digits back to a byte."""
    byte_val = 0
    for digit in quad_digits:
        byte_val = byte_val * 4 + digit
    return byte_val

def generate_synthetic_tensor(shape=(1000, 1000), pattern='structured'):
    """Generate synthetic tensor data for testing."""
    if pattern == 'structured':
        # Low-rank matrix with patterns
        U = np.random.randn(shape[0], 10)
        V = np.random.randn(10, shape[1])
        tensor = U @ V
        # Add some structure
        tensor += np.sin(np.arange(shape[1]) / 100) * 10
    elif pattern == 'sparse':
        # Sparse tensor
        tensor = np.zeros(shape)
        n_nonzero = int(shape[0] * shape[1] * 0.01)  # 1% nonzero
        for _ in range(n_nonzero):
            i, j = np.random.randint(0, shape[0]), np.random.randint(0, shape[1])
            tensor[i, j] = np.random.randn() * 100
    elif pattern == 'random':
        # Random tensor
        tensor = np.random.randn(*shape) * 100
    else:
        tensor = np.random.randn(*shape) * 100
    
    # Convert to Float16 and back to bytes for realistic representation
    tensor_f16 = tensor.astype(np.float16)
    return tensor_f16.tobytes()

def apply_quaternary_to_tensor(tensor_bytes, method='group'):
    """Apply quaternary logic to tensor byte representation."""
    tensor_array = np.frombuffer(tensor_bytes, dtype=np.float16)
    
    if method == 'group':
        # Group by quaternary digit position
        streams = [[], [], [], []]
        for byte_val in tensor_array.tobytes():
            quad = byte_to_quaternary(byte_val)
            for pos, digit in enumerate(quad):
                streams[pos].append(digit)
        
        # Pack back
        result = bytearray()
        for stream in streams:
            if len(stream) % 2 == 1:
                stream.append(0)
            for i in range(0, len(stream), 2):
                packed = stream[i] * 4 + stream[i+1]
                result.append(packed)
        return bytes(result)
    
    elif method == 'not':
        # Quaternary NOT
        result = bytearray()
        for byte_val in tensor_array.tobytes():
            quad = byte_to_quaternary(byte_val)
            transformed = [3 - d for d in quad]
            result.append(quaternary_to_byte(transformed))
        return bytes(result)
    
    elif method == 'cycle':
        # Cycle digits
        result = bytearray()
        for byte_val in tensor_array.tobytes():
            quad = byte_to_quaternary(byte_val)
            transformed = quad[1:] + [quad[0]]
            result.append(quaternary_to_byte(transformed))
        return bytes(result)
    
    elif method == 'smooth':
        # Smooth transitions
        tensor_bytes = tensor_array.tobytes()
        if len(tensor_bytes) < 2:
            return tensor_bytes
        
        result = bytearray()
        result.append(tensor_bytes[0])
        prev_quad = byte_to_quaternary(tensor_bytes[0])
        
        for byte_val in tensor_bytes[1:]:
            curr_quad = byte_to_quaternary(byte_val)
            smoothed_quad = []
            
            for i in range(4):
                diff = abs(curr_quad[i] - prev_quad[i])
                if diff > 1:
                    if curr_quad[i] > prev_quad[i]:
                        smoothed_quad.append(prev_quad[i] + 1)
                    else:
                        smoothed_quad.append(prev_quad[i] - 1)
                else:
                    smoothed_quad.append(curr_quad[i])
            
            smoothed_quad = [max(0, min(3, d)) for d in smoothed_quad]
            result.append(quaternary_to_byte(smoothed_quad))
            prev_quad = smoothed_quad
        
        return bytes(result)
    
    return tensor_bytes

def analyze_tensor_compression(tensor_bytes, method_name, preprocess_func):
    """Analyze compression of tensor data with quaternary preprocessing."""
    print(f"\n{'=' * 60}")
    print(f"Method: {method_name}")
    print(f"{'=' * 60}")
    
    # Apply preprocessing
    preprocessed = preprocess_func(tensor_bytes)
    
    # Calculate metrics
    original_entropy = calculate_entropy(tensor_bytes)
    preprocessed_entropy = calculate_entropy(preprocessed)
    
    # Compress both
    original_compressed = zlib.compress(tensor_bytes, level=9)
    preprocessed_compressed = zlib.compress(preprocessed, level=9)
    
    print(f"Original size: {len(tensor_bytes):,} bytes")
    print(f"Preprocessed size: {len(preprocessed):,} bytes")
    print(f"Size change: {len(preprocessed) / len(tensor_bytes):.4f}x")
    print(f"\nOriginal entropy: {original_entropy:.4f} bits/byte")
    print(f"Preprocessed entropy: {preprocessed_entropy:.4f} bits/byte")
    print(f"Entropy change: {preprocessed_entropy - original_entropy:+.4f}")
    print(f"\nOriginal compressed: {len(original_compressed):,} bytes ({len(original_compressed) / len(tensor_bytes):.4f}x)")
    print(f"Preprocessed compressed: {len(preprocessed_compressed):,} bytes ({len(preprocessed_compressed) / len(preprocessed):.4f}x)")
    print(f"Compression ratio change: {(len(preprocessed_compressed) / len(preprocessed)) / (len(original_compressed) / len(tensor_bytes)):+.4f}x")
    
    return {
        'method': method_name,
        'size_ratio': len(preprocessed) / len(tensor_bytes),
        'entropy_change': preprocessed_entropy - original_entropy,
        'compression_ratio_change': (len(preprocessed_compressed) / len(preprocessed)) / (len(original_compressed) / len(tensor_bytes))
    }

def main():
    print("=" * 60)
    print("Quaternary Logic Gates for Tensor Data")
    print("=" * 60)
    
    # Test on different tensor patterns
    patterns = ['structured', 'sparse', 'random']
    
    all_results = {}
    
    for pattern in patterns:
        print(f"\n{'=' * 60}")
        print(f"Testing on {pattern.upper()} tensor (1000x1000 Float16)")
        print(f"{'=' * 60}")
        
        # Generate tensor
        tensor_bytes = generate_synthetic_tensor(shape=(1000, 1000), pattern=pattern)
        print(f"Tensor size: {len(tensor_bytes):,} bytes ({len(tensor_bytes) / 1024 / 1024:.2f} MB)")
        
        # Test methods
        results = []
        
        # Method 1: Quaternary grouping
        results.append(analyze_tensor_compression(
            tensor_bytes,
            "Quaternary Grouping",
            lambda d: apply_quaternary_to_tensor(d, 'group')
        ))
        
        # Method 2: Quaternary NOT
        results.append(analyze_tensor_compression(
            tensor_bytes,
            "Quaternary NOT",
            lambda d: apply_quaternary_to_tensor(d, 'not')
        ))
        
        # Method 3: Quaternary Cycle
        results.append(analyze_tensor_compression(
            tensor_bytes,
            "Quaternary Cycle",
            lambda d: apply_quaternary_to_tensor(d, 'cycle')
        ))
        
        # Method 4: Quaternary Smoothing
        results.append(analyze_tensor_compression(
            tensor_bytes,
            "Quaternary Smoothing",
            lambda d: apply_quaternary_to_tensor(d, 'smooth')
        ))
        
        all_results[pattern] = results
        
        # Summary for this pattern
        print("\n" + "=" * 60)
        print("SUMMARY - {}".format(pattern.upper()))
        print("=" * 60)
        print("{:<40} {:<12} {:<12} {:<12}".format('Method', 'Size Ratio', 'Entropy Δ', 'Comp Δ'))
        print("-" * 76)
        
        for r in results:
            entropy_str = "{:+.4f}".format(r['entropy_change'])
            comp_str = "{:+.4f}".format(r['compression_ratio_change'])
            size_str = "{:.4f}".format(r['size_ratio'])
            print("{:<40} {:<12} {:<12} {:<12}".format(r['method'], size_str, entropy_str, comp_str))
    
    # Cross-pattern comparison
    print("\n" + "=" * 60)
    print("CROSS-PATTERN COMPARISON")
    print("=" * 60)
    
    methods = ['Quaternary Grouping', 'Quaternary NOT', 'Quaternary Cycle', 'Quaternary Smoothing']
    
    print("{:<40} {:<12} {:<12} {:<12}".format('Method', 'Structured', 'Sparse', 'Random'))
    print("-" * 76)
    
    for method in methods:
        structured = next(r['compression_ratio_change'] for r in all_results['structured'] if r['method'] == method)
        sparse = next(r['compression_ratio_change'] for r in all_results['sparse'] if r['method'] == method)
        random = next(r['compression_ratio_change'] for r in all_results['random'] if r['method'] == method)
        
        structured_str = "{:+.4f}".format(structured)
        sparse_str = "{:+.4f}".format(sparse)
        random_str = "{:+.4f}".format(random)
        print("{:<40} {:<12} {:<12} {:<12}".format(method, structured_str, sparse_str, random_str))
    
    print("\n" + "=" * 60)
    print("KEY INSIGHTS FOR TENSOR DATA")
    print("=" * 60)
    
    # Find best method for each pattern
    for pattern in patterns:
        best = min(all_results[pattern], key=lambda x: x['compression_ratio_change'])
        print("Best for {}: {} ({:+.4f}x)".format(pattern, best['method'], best['compression_ratio_change']))
    
    print("\n" + "=" * 60)
    print("QUATERNARY TENSOR THEORY")
    print("=" * 60)
    print("Tensor data has different structure than text:")
    print("- Structured tensors: Low-rank, smooth transitions")
    print("- Sparse tensors: Many zeros, few non-zero values")
    print("- Random tensors: High entropy, no patterns")
    print("\nQuaternary logic may help tensor data because:")
    print("- Bit plane separation reveals low-rank structure")
    print("- Smoothing preserves tensor smoothness")
    print("- Digit operations can exploit sparsity patterns")

if __name__ == "__main__":
    main()
