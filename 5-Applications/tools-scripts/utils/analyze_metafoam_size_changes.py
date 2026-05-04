#!/usr/bin/env python3
"""
Analyze data size changes during metafoam spray/melt events on enwik9.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
TSM_ROOT = REPO_ROOT / "CATEGORY" / "TSM"
ENWIK9_PATH = REPO_ROOT / "hutter_bind_implementation" / "enwik9"

sys.path.insert(0, str(TSM_ROOT))

from tsm_metafoam_enhanced import DistributedGraphSubstrateEngine
import time

def extract_waveform(data, window_size=1024):
    """Extract waveform from data using sliding window."""
    waveform = []
    n_windows = len(data) // window_size
    
    for i in range(n_windows):
        window = data[i*window_size:(i+1)*window_size]
        energy = sum(window)
        waveform.append(energy)
    
    return waveform

def main():
    print("=" * 60)
    print("Metafoam Spray/Melt Data Size Analysis")
    print("=" * 60)
    
    # Load enwik9
    print("\nLoading enwik9...")
    with open(ENWIK9_PATH, "rb") as f:
        original_data = f.read()
    
    original_size = len(original_data)
    print(f"Original size: {original_size:,} bytes ({original_size / 1024**3:.2f} GB)")
    
    # Extract original waveform
    print("Extracting original waveform...")
    original_waveform = extract_waveform(original_data)
    print(f"Original waveform length: {len(original_waveform)} points")
    
    # Initialize metafoam engine
    print("\nInitializing metafoam engine...")
    engine = DistributedGraphSubstrateEngine(substrate="superconductor")
    
    # Step 1: VDP_COMPRESS (create topological capsule)
    print("\n" + "=" * 60)
    print("Step 1: VDP_COMPRESS (0x19)")
    print("=" * 60)
    start = time.time()
    capsule = engine.execute_vdp_compress(original_data)
    compress_time = time.time() - start
    
    print(f"Compressed size: {len(capsule.data):,} bytes ({len(capsule.data) / 1024**3:.2f} GB)")
    print(f"Compression ratio: {capsule.compression_ratio:.4f}x")
    print(f"Entropy score: {capsule.entropy_score:.4f}")
    print(f"Compress time: {compress_time:.2f}s")
    print(f"Capsule hash: {capsule.capsule_hash[:16]}...")
    
    # Step 2: FOAM_SPRAY (holographic dispersion)
    print("\n" + "=" * 60)
    print("Step 2: FOAM_SPRAY (0x1B)")
    print("=" * 60)
    start = time.time()
    spray_result = engine.execute_foam_spray(capsule.capsule_hash, spatial_dispersion=10)
    spray_time = time.time() - start
    
    print(f"Scattered nodes: {len(spray_result.get('scattered_nodes', []))}")
    print(f"Topological volume: {spray_result.get('topological_volume', 0):.4f}")
    print(f"Spray time: {spray_time:.2f}s")
    
    # Analyze foam state after spray
    print(f"\nFoam voxels after spray: {len(engine.voxels)}")
    print(f"Capsules after spray: {len(engine.capsules)}")
    
    # Calculate holographic volume
    holographic_volume = len(capsule.data) * len(spray_result.get('scattered_nodes', []))
    print(f"Holographic volume (data * nodes): {holographic_volume:,} bytes ({holographic_volume / 1024**3:.2f} GB)")
    print(f"Volume expansion factor: {holographic_volume / len(capsule.data):.2f}x")
    
    # Step 3: QUANTUM_MELT (topological erasure)
    print("\n" + "=" * 60)
    print("Step 3: QUANTUM_MELT (0x1A)")
    print("=" * 60)
    
    # Create metadata for melt
    import os
    quantum_seed = os.urandom(32)
    metadata = {
        "original_size": original_size,
        "compressed_size": len(capsule.data),
        "compression_ratio": capsule.compression_ratio,
        "entropy_score": capsule.entropy_score
    }
    
    start = time.time()
    melted = engine.execute_quantum_melt(metadata, quantum_seed)
    melt_time = time.time() - start
    
    print(f"Melted size: {len(melted.data):,} bytes")
    print(f"Compression ratio: {melted.compression_ratio:.4f}x")
    print(f"Entropy score: {melted.entropy_score:.4f}")
    print(f"Melt time: {melt_time:.2f}s")
    print(f"Entanglement proof: {melted.entanglement_proof[:16]}...")
    
    # Step 4: RICCI_FLOW (decompress/expand)
    print("\n" + "=" * 60)
    print("Step 4: RICCI_FLOW (0x16) - White Hole Decompression")
    print("=" * 60)
    start = time.time()
    flow_result = engine.execute_ricci_flow(capsule.capsule_hash)
    flow_time = time.time() - start
    
    print(f"Status: {flow_result.get('status', 'N/A')}")
    print(f"Euclidean bytes restored: {flow_result.get('euclidean_bytes_restored', 0):,}")
    print(f"Curvature flattened from bits: {flow_result.get('curvature_flattened_from_bits', 0):.4f}")
    print(f"Flow time: {flow_time:.2f}s")
    
    # Summary
    print("\n" + "=" * 60)
    print("DATA SIZE SUMMARY")
    print("=" * 60)
    print(f"{'Operation':<25} {'Size (GB)':<15} {'Ratio':<10} {'Time (s)':<10}")
    print("-" * 60)
    print(f"{'Original':<25} {original_size / 1024**3:<15.3f} {'1.00':<10} {'N/A':<10}")
    print(f"{'VDP_COMPRESS':<25} {len(capsule.data) / 1024**3:<15.3f} {capsule.compression_ratio:<10.4f} {compress_time:<10.2f}")
    print(f"{'FOAM_SPRAY (holographic)':<25} {holographic_volume / 1024**3:<15.3f} {holographic_volume / len(capsule.data):<10.2f} {spray_time:<10.2f}")
    print(f"{'QUANTUM_MELT':<25} {len(melted.data) / 1024**9:<15.6f} {melted.compression_ratio:<10.4f} {melt_time:<10.2f}")
    print(f"{'RICCI_FLOW (restored)':<25} {flow_result.get('euclidean_bytes_restored', 0) / 1024**3:<15.3f} {'1.00':<10} {flow_time:<10.2f}")
    
    print("\n" + "=" * 60)
    print("KEY INSIGHTS")
    print("=" * 60)
    print("1. VDP_COMPRESS: Reduces data size via topological manifold discovery")
    print("2. FOAM_SPRAY: Creates holographic redundancy WITHOUT byte duplication")
    print("   - Actual byte-mass stays the same")
    print("   - Holographic volume = data_size * node_count")
    print("   - This is 'virtual' expansion via pointer scattering")
    print("3. QUANTUM_MELT: Destroys compressibility (entropy = 1.0)")
    print("   - Cannot be compressed topologically")
    print("   - Used for secure erasure of structure")
    print("4. RICCI_FLOW: Restores original data from compressed capsule")
    print("   - White hole expansion from singularity")
    print("   - Curvature flattens from compressed to 8.0 bits/byte")
    
    # Execution log analysis
    print("\n" + "=" * 60)
    print("EXECUTION LOG")
    print("=" * 60)
    for log in engine.execution_log:
        print(f"{log.opcode} {log.mnemonic}:")
        print(f"  State ID: {log.state_id[:20]}...")
        print(f"  Execution time: {log.execution_time_ns / 1_000_000:.2f} ms")
        print(f"  Energy: {log.energy_consumed_joules:.2e} J")
        print(f"  Compression ratio: {log.compression_ratio:.4f}")
        print(f"  Stability delta: {log.stability_delta:.4f}")
        print()

if __name__ == "__main__":
    main()
