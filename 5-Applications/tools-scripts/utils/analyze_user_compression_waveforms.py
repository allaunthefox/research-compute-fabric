#!/usr/bin/env python3
"""
Analyze waveform differences from user's compression approaches.
"""

import os
import numpy as np
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

# Configuration
ENWIK9_PATH = REPO_ROOT / "hutter_bind_implementation" / "enwik9"
OUTPUT_DIR = REPO_ROOT / "compression_comparison"
USER_COMPRESSION_DIR = REPO_ROOT
WINDOW_SIZE = 1024

def extract_waveform(data, window_size=WINDOW_SIZE):
    """Extract waveform from data using sliding window."""
    waveform = []
    n_windows = len(data) // window_size
    
    for i in range(n_windows):
        window = data[i*window_size:(i+1)*window_size]
        energy = sum(window)
        waveform.append(energy)
    
    return np.array(waveform, dtype=np.float64)

def load_user_compressed_data(compressed_path, metadata_path):
    """Load and reconstruct data from user's compressed format."""
    # Read compressed data
    with open(compressed_path, 'rb') as f:
        compressed_data = f.read()
    
    # Read metadata to understand format
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    print(f"Metadata: {metadata}")
    
    # Try to reconstruct based on metadata
    # This depends on the specific compression format
    
    return compressed_data, metadata

def main():
    """Analyze user compression waveform differences."""
    print("=" * 60)
    print("User Compression Waveform Analysis")
    print("=" * 60)
    
    # Load original waveform
    print("\nLoading original waveform...")
    with open(ENWIK9_PATH, 'rb') as f:
        original_data = f.read()
    
    original_waveform = extract_waveform(original_data)
    print(f"Original waveform length: {len(original_waveform)} points")
    
    # Load original waveform from numpy if exists
    original_waveform_path = OUTPUT_DIR / "waveform_original.npy"
    if original_waveform_path.exists():
        original_waveform = np.load(original_waveform_path)
        print(f"Loaded from: {original_waveform_path}")
    
    # User compression approaches
    user_approaches = {
        'zero_spike_uvmap': {
            'compressed': USER_COMPRESSION_DIR / 'enwik9_zero_spike_uvmap_compressed.bin',
            'metadata': USER_COMPRESSION_DIR / 'enwik9_zero_spike_uvmap_metadata.txt'
        },
        'sparse_zero_spike': {
            'compressed': USER_COMPRESSION_DIR / 'enwik9_sparse_zero_spike_compressed.bin',
            'metadata': USER_COMPRESSION_DIR / 'enwik9_sparse_zero_spike_metadata.txt'
        },
        'hybrid_dyson_swarm': {
            'compressed': USER_COMPRESSION_DIR / 'enwik9_hybrid_dyson_swarm_compressed.bin',
            'metadata': USER_COMPRESSION_DIR / 'enwik9_hybrid_dyson_swarm_metadata.txt'
        },
        'irreducible_surface': {
            'compressed': USER_COMPRESSION_DIR / 'enwik9_irreducible_surface_compressed.bin',
            'metadata': USER_COMPRESSION_DIR / 'enwik9_irreducible_surface_metadata.txt'
        }
    }
    
    # Analyze each approach
    results = {}
    
    for approach_name, paths in user_approaches.items():
        print(f"\n{'=' * 60}")
        print(f"Analyzing: {approach_name.upper()}")
        print('=' * 60)
        
        if not paths['compressed'].exists():
            print(f"✗ Compressed file not found: {paths['compressed']}")
            continue
        
        if not paths['metadata'].exists():
            print(f"✗ Metadata file not found: {paths['metadata']}")
            continue
        
        try:
            # Read compressed data
            with open(paths['compressed'], 'rb') as f:
                compressed_data = f.read()
            
            compressed_size = len(compressed_data)
            print(f"Compressed size: {compressed_size:,} bytes ({compressed_size / 1024**3:.2f} GB)")
            
            # Read metadata
            with open(paths['metadata'], 'r') as f:
                metadata_content = f.read()
            
            print(f"Metadata preview (first 500 chars):")
            print(metadata_content[:500])
            
            # Try to parse as JSON
            try:
                metadata = json.loads(metadata_content)
                print(f"\nParsed metadata keys: {metadata.keys()}")
                
                # Check if there's reconstructed data info
                if 'reconstructed_size' in metadata:
                    print(f"Reconstructed size: {metadata['reconstructed_size']:,} bytes")
                
                if 'compression_ratio' in metadata:
                    print(f"Compression ratio: {metadata['compression_ratio']:.2f}x")
                
            except json.JSONDecodeError:
                print("Metadata is not JSON format")
            
            # For now, we can't reconstruct without the decompression code
            # But we can analyze the compressed data structure
            print(f"\nCompressed data statistics:")
            print(f"  Min byte: {min(compressed_data)}")
            print(f"  Max byte: {max(compressed_data)}")
            print(f"  Unique bytes: {len(set(compressed_data))}")
            
            # Try to extract waveform from compressed data directly
            # (this won't match original, but shows what the compressed representation looks like)
            compressed_waveform = extract_waveform(compressed_data)
            
            # Compare to original (will be very different)
            waveform_diff = np.abs(original_waveform[:len(compressed_waveform)] - compressed_waveform)
            max_diff = np.max(waveform_diff)
            mean_diff = np.mean(waveform_diff)
            
            print(f"\nCompressed waveform (direct from compressed data):")
            print(f"  Length: {len(compressed_waveform)} points")
            print(f"  Max diff from original: {max_diff:.2f}")
            print(f"  Mean diff from original: {mean_diff:.2f}")
            
            results[approach_name] = {
                'compressed_size': compressed_size,
                'metadata': metadata_content,
                'compressed_waveform': compressed_waveform,
                'max_diff': max_diff,
                'mean_diff': mean_diff
            }
            
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Save results
    results_path = os.path.join(OUTPUT_DIR, "user_compression_analysis.json")
    with open(results_path, 'w') as f:
        # Convert numpy arrays to lists for JSON serialization
        json_results = {}
        for key, value in results.items():
            json_results[key] = {
                'compressed_size': value['compressed_size'],
                'metadata_preview': value['metadata'][:1000],
                'max_diff': float(value['max_diff']),
                'mean_diff': float(value['mean_diff'])
            }
        json.dump(json_results, f, indent=2)
    
    print(f"\nResults saved to: {results_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{'Approach':<25} {'Size (GB)':<12} {'Max Diff':<12} {'Mean Diff':<12}")
    print("-" * 60)
    
    for approach_name, result in results.items():
        size_gb = result['compressed_size'] / 1024**3
        print(f"{approach_name:<25} {size_gb:<12.3f} {result['max_diff']:<12.2f} {result['mean_diff']:<12.2f}")
    
    print("\n" + "=" * 60)
    print("IMPORTANT NOTE")
    print("=" * 60)
    print("To properly compare waveforms, we need to:")
    print("1. Decompress/reconstruct the data using your decompression code")
    print("2. Extract waveform from the RECONSTRUCTED data")
    print("3. Compare reconstructed waveform to original waveform")
    print("\nCurrently, we're comparing the compressed binary directly to original,")
    print("which shows structural differences but not the actual compression effect.")
    print("\nPlease provide the decompression/reconstruction code for each approach")
    print("so we can properly analyze the waveform differences.")

if __name__ == "__main__":
    main()
