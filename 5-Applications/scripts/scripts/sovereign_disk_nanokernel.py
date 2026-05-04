#!/usr/bin/env python3
"""
Sovereign Disk Nanokernel Simulator
Implements block-level GCL admission logic for disk controllers.
"""

import hashlib
import json
import time
import numpy as np
from typing import Dict, List, Tuple, Optional

class GCLAdmissionGate:
    """Simulates the hardware-level gate on the disk controller."""
    
    def __init__(self, trust_threshold=0.8):
        self.trust_threshold = trust_threshold
        self.admission_log = []
        self.active_policies = {
            "no_high_entropy": True,      # Reject encrypted blocks (ransomware defense)
            "require_gcl_signature": True, # Only accept writes with valid GCL tokens
            "structural_coherence": True  # Audit data structure via Metaprobe
        }

    def evaluate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of the block."""
        if not data: return 0.0
        counts = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256)
        probs = counts[counts > 0] / len(data)
        return -np.sum(probs * np.log2(probs))

    def metaprobe_audit(self, data: bytes) -> float:
        """
        Coarse Metaprobe sweep.
        In a real nanokernel, this would run on the 32-bit RISC core.
        Checks for 'Lawful' signal resonance.
        """
        # Simplified: Check for repeating patterns or known structural headers
        # High score for structured data (text, code), low for pure noise.
        entropy = self.evaluate_entropy(data)
        # Normalized score: high entropy (>7.5) is likely compressed or encrypted
        structure_score = 1.0 - (max(0, entropy - 4.0) / 4.0)
        return max(0.0, min(1.0, structure_score))

    def validate_gcl_token(self, data: bytes, token: str) -> bool:
        """Verify the GCL admission token."""
        # In a real system, this would check a HMAC or ZK-Proof
        expected = hashlib.sha256(data[:1024] + b"DISK_SECRET_KEY").hexdigest()[:16]
        return token == expected

    def handle_write_request(self, lba: int, data: bytes, token: Optional[str] = None) -> Dict:
        """Evaluates whether to admit the write to NAND."""
        start_time = time.time()
        
        # 1. Entropy Check
        entropy = self.evaluate_entropy(data)
        entropy_status = "PASS" if entropy < 7.8 else "FAIL (Suspected Ransomware/Encryption)"
        
        # 2. Metaprobe Structural Audit
        structure_score = self.metaprobe_audit(data)
        
        # 3. GCL Token Validation
        token_valid = False
        if self.active_policies["require_gcl_signature"]:
            if token:
                token_valid = self.validate_gcl_token(data, token)
            token_status = "VALID" if token_valid else "INVALID/MISSING"
        else:
            token_status = "BYPASSED"
            token_valid = True

        # Final Admission Decision
        admitted = (entropy < 7.9) and token_valid
        
        result = {
            "lba": lba,
            "size": len(data),
            "metrics": {
                "entropy": round(entropy, 4),
                "structure_score": round(structure_score, 4)
            },
            "status": {
                "entropy": entropy_status,
                "token": token_status
            },
            "decision": "ADMITTED" if admitted else "REJECTED (GCL Hardware Gate)",
            "latency_ms": round((time.time() - start_time) * 1000, 4)
        }
        
        self.admission_log.append(result)
        return result

def simulate_nanokernel():
    print("=" * 70)
    print("SOVEREIGN DISK NANOKERNEL SIMULATOR (CBM2199 Architecture)")
    print("=" * 70)
    
    kernel = GCLAdmissionGate()
    
    # Scenario 1: Valid GCL Write (System metadata)
    print("\n[*] Scenario 1: Lawful System Update...")
    valid_data = b"GCL_MANIFEST_VERSION_1.0\n" + b"A" * 4000
    token = hashlib.sha256(valid_data[:1024] + b"DISK_SECRET_KEY").hexdigest()[:16]
    res1 = kernel.handle_write_request(0, valid_data, token)
    print(json.dumps(res1, indent=2))
    
    # Scenario 2: High-Entropy Write (Suspected Ransomware)
    print("\n[*] Scenario 2: Unlawful High-Entropy Write (Encrypted Data)...")
    ransomware_payload = np.random.bytes(4096)
    res2 = kernel.handle_write_request(100, ransomware_payload, "FAKE_TOKEN")
    print(json.dumps(res2, indent=2))
    
    # Scenario 3: Unauthorized OS Write (No GCL Token)
    print("\n[*] Scenario 3: Unauthorized Rootkit Write (No Token)...")
    rootkit_data = b"malicious_code_v1.0"
    res3 = kernel.handle_write_request(500, rootkit_data, None)
    print(json.dumps(res3, indent=2))

    print("\n" + "=" * 70)
    print("NANOKERNEL SIMULATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    simulate_nanokernel()
