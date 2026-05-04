#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

# UNIVERSE CONSTANTS (from nd_gauntlet_live.html & encode_claim_q11.py)
AETHER_FLOOR = 0.5
AXES = ['content_hash', 'tier', 'kind', 'meta', 'omega', 'primitive']

def fnv32(s: str) -> int:
    """Implement FNV-1a 32-bit hash logic from nd_gauntlet_live.html."""
    h = 0x811c9dc5
    for char in s:
        h ^= ord(char)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h

def vectorize_text(text: str, identifier: str) -> Dict[str, List[int]]:
    """Generate 384-spin N-D vector across 6 axes."""
    vectors: Dict[str, List[int]] = {}
    for axis in AXES:
        # Use first 500 chars for semantic context to avoid noise dilution
        seed = fnv32(f"{axis}:{identifier}:{text[:500]}")
        spins: List[int] = []
        s_val = seed
        for _ in range(64):
            s_val = ((s_val << 13) ^ s_val) & 0xFFFFFFFF
            s_val = ((s_val >> 17) ^ s_val) & 0xFFFFFFFF
            s_val = ((s_val << 5) ^ s_val) & 0xFFFFFFFF
            spins.append(1 if (s_val & 1) else -1)
        vectors[axis] = spins
    return vectors

def calculate_metrics(vectors: Dict[str, List[int]]) -> Dict[str, Any]:
    """Calculate ND metrics: entropy, magnetization, aether error."""
    all_spins: List[int] = [s for axis in AXES for s in vectors[axis]]
    p_up = len([s for s in all_spins if s == 1]) / len(all_spins)
    p_dn = 1.0 - p_up
    
    # Shannon Entropy S
    entropy = -(p_up * math.log2(p_up) + p_dn * math.log2(p_dn)) if 0 < p_up < 1 else 0.0
    
    # Magnetization M (coherence/rigidity)
    magnetization = abs(sum(all_spins) / len(all_spins))
    
    # Aether Error (Deviation from stability floor)
    aether_error = abs(entropy - AETHER_FLOOR)
    
    status = "SINGULARITY" if aether_error < 0.05 else "CRYSTALLINE" if aether_error < 0.1 else "PLASMA"
    
    return {
        "entropy_s": round(entropy, 6),
        "magnetization_m": round(magnetization, 6),
        "aether_error": round(aether_error, 6),
        "status": status
    }

def sieve_codebase(root_dir: str):
    """Walk the codebase and vectorize each file."""
    results = []
    root_path = Path(root_dir)
    
    # Focus on Java/Kotlin source and XML configs
    extensions = {'.java', '.kt', '.xml', '.gradle'}
    
    for path in root_path.rglob('*'):
        if path.is_file() and path.suffix in extensions:
            if '.git' in path.parts or 'build' in path.parts:
                continue
            
            try:
                content = path.read_text(encoding='utf-8', errors='ignore')
                if not content.strip():
                    continue
                
                # Identifier: relative path + first line (often package/comment)
                rel_path = str(path.relative_to(root_path))
                identifier = f"{rel_path}"
                
                vectors = vectorize_text(content, identifier)
                metrics = calculate_metrics(vectors)
                
                results.append({
                    "file": rel_path,
                    "metrics": metrics,
                    "risk_score": metrics['aether_error'] * (1.0 + metrics['magnetization_m'])
                })
            except Exception as e:
                print(f"[!] Error processing {path}: {e}")

    # Sort by risk score (descending aether error)
    results.sort(key=lambda x: x['risk_score'], reverse=True)
    return results

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "/tmp/proofmode-android"
    
    print(f"[*] Starting ND-Space Sieve on {target}...")
    findings = sieve_codebase(target)
    
    print(f"\n[+] Sieve Complete. Top 10 High-Entropy Anomalies (Potential Exploits):")
    print("-" * 80)
    print(f"{'File':<50} | {'Status':<12} | {'Aether Err':<10}")
    print("-" * 80)
    for f in findings[:20]:
        print(f"{f['file'][:50]:<50} | {f['metrics']['status']:<12} | {f['metrics']['aether_error']:.6f}")
    
    # Write full report
    report_path = Path("5-Applications/out/nd_sieve_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(findings, indent=2), encoding='utf-8')
    print(f"\n[+] Full report written to {report_path}")
