#!/usr/bin/env python3
"""
Linux Kernel RGFlow Audit
Converts kernel source to Unified Compression format and audits lawfulness.
"""

import os
import sys
import numpy as np
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "0-Core-Formalism"))

from scripts.commoncrawl_waveprobe_ingestion import UnifiedAdaptationEquation, AdaptationState, UnifiedCompressor

logging.basicConfig(level=logging.INFO, format='%(levelname)s:KernelAudit:%(message)s')
logger = logging.getLogger(__name__)

def audit_kernel_file(filepath: Path):
    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        return

    logger.info(f"Auditing Linux Kernel subsystem: {filepath.name}")
    
    with open(filepath, 'rb') as f:
        data = f.read()

    # 1. Convert to Unified Compression format
    compressor = UnifiedCompressor()
    compressed_bytes, ratio = compressor.compress_bytestream(data)
    logger.info(f"Unified Compression Ratio: {ratio:.3f}")

    # 2. Extract Adaptation State from the compressed "Genome"
    adaptation_eq = UnifiedAdaptationEquation()
    
    # Heuristic mapping for Kernel Code
    # Entropy of compressed data (information density)
    entropy = -np.sum(np.histogram(np.frombuffer(compressed_bytes, dtype=np.uint8), bins=256, density=True)[0] * np.log2(np.histogram(np.frombuffer(compressed_bytes, dtype=np.uint8), bins=256, density=True)[0] + 1e-9))
    norm_entropy = min(entropy / 8.0, 1.0)
    
    mu_q = 0.001  # Kernel code is extremely stable
    rho_q = 0.9   # High refresh (frequent patches)
    C_fac = 0.8   # High connectance (tightly coupled)
    M_fac = 0.7   # Modularity (subsystems)
    n_e = 1.0     # Maximum observer mass (millions of users/devs)
    sigma_q = 1.0 + norm_entropy  # SNR based on compressed info density
    
    state = AdaptationState(mu_q, rho_q, C_fac, M_fac, n_e, sigma_q)
    
    # 3. Evaluate RGFlow trajectory
    (lawful_now, lawful_under_flow, reaches_attractor, flows_to_noise, 
     flows_to_sabotage, cost, margin, rg_depth, attractor_id, failure_mask) = \
        adaptation_eq.evaluate_state(state)

    print("\n" + "="*80)
    print(f"Linux Kernel Audit Report: {filepath.name}")
    print("="*80)
    print(f"Status: {'✓ LAWFUL' if lawful_under_flow else '✗ NON-LAWFUL'}")
    print(f"RG Depth: {rg_depth}/10")
    print(f"Attractor: {attractor_id}")
    print(f"Stability Margin: {margin:.4f}")
    print(f"Compression Ratio: {ratio:.3f}")
    print("-" * 80)
    print(f"Genome Logic: mu={mu_q}, rho={rho_q}, C={C_fac}, M={M_fac}, ne={n_e}, sigma={sigma_q:.3f}")
    if not lawful_under_flow:
        print(f"Failure Mask: {failure_mask} (1:Drake, 2:Drift, 4:Error)")
    print("="*80 + "\n")

if __name__ == "__main__":
    # Targeting the core scheduler
    target = Path("/usr/src/linux-cachyos/kernel/sched/core.c")
    if not target.exists():
        # Fallback to any file in the kernel source if core.c is not specifically there
        sources = list(Path("/usr/src/linux-cachyos").rglob("*.c"))
        if sources:
            target = sources[0]
    
    audit_kernel_file(target)
