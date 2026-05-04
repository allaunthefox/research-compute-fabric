#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
SHA256 Mathematical Derivation and Security Analysis
Educational derivation of SHA256 structure, security properties, and theoretical attack complexity

WARNING: This is for EDUCATIONAL PURPOSES ONLY
- SHA256 is cryptographically secure
- No practical attack exists with current technology
- Brute force requires 2^256 operations (physically impossible)
- This code demonstrates structure, NOT exploitation
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from math_harness_compat import xp, AnyArray
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import sys


# ============================================================================
# SHA256 CONSTANTS (First 32 bits of fractional parts of cube roots of primes)
# ============================================================================

SHA256_K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
]

# Initial hash values (First 32 bits of fractional parts of square roots of first 8 primes)
SHA256_H0 = [
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
]


# ============================================================================
# BITWISE OPERATIONS (SHA256 PRIMITIVES)
# ============================================================================

def rotr(x: int, n: int) -> int:
    """Right rotation for 32-bit integers"""
    return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF

def shr(x: int, n: int) -> int:
    """Right shift for 32-bit integers"""
    return x >> n

def ch(x: int, y: int, z: int) -> int:
    """Choice function: if x then y else z (bitwise)"""
    return (x & y) ^ (~x & z) & 0xFFFFFFFF

def maj(x: int, y: int, z: int) -> int:
    """Majority function: majority of bits in x, y, z"""
    return (x & y) ^ (x & z) ^ (y & z) & 0xFFFFFFFF

def sigma0(x: int) -> int:
    """Σ0 function for compression"""
    return rotr(x, 2) ^ rotr(x, 13) ^ rotr(x, 22)

def sigma1(x: int) -> int:
    """Σ1 function for compression"""
    return rotr(x, 6) ^ rotr(x, 11) ^ rotr(x, 25)

def gamma0(x: int) -> int:
    """σ0 function for message schedule"""
    return rotr(x, 7) ^ rotr(x, 18) ^ shr(x, 3)

def gamma1(x: int) -> int:
    """σ1 function for message schedule"""
    return rotr(x, 17) ^ rotr(x, 19) ^ shr(x, 10)


# ============================================================================
# SHA256 COMPRESSION FUNCTION (DERIVATION)
# ============================================================================

@dataclass
class SHA256State:
    """Represents the internal state of SHA256 during compression"""
    
    # Working variables (a-h)
    a: int = SHA256_H0[0]
    b: int = SHA256_H0[1]
    c: int = SHA256_H0[2]
    d: int = SHA256_H0[3]
    e: int = SHA256_H0[4]
    f: int = SHA256_H0[5]
    g: int = SHA256_H0[6]
    h: int = SHA256_H0[7]
    
    # Round number (0-63)
    round: int = 0
    
    # Message schedule word for current round
    w_t: int = 0
    
    # Intermediate values
    t1: int = 0
    t2: int = 0
    
    def to_list(self) -> List[int]:
        return [self.a, self.b, self.c, self.d, self.e, self.f, self.g, self.h]
    
    def copy(self) -> 'SHA256State':
        return SHA256State(
            a=self.a, b=self.b, c=self.c, d=self.d,
            e=self.e, f=self.f, g=self.g, h=self.h,
            round=self.round
        )


class SHA256Derivation:
    """
    Step-by-step SHA256 derivation with security analysis
    """
    
    def __init__(self):
        self.state = SHA256State()
        self.message_schedule: List[int] = []
        self.round_trace: List[SHA256State] = []
    
    def pad_message(self, message: bytes) -> bytes:
        """
        SHA256 padding:
        1. Append bit '1' to message
        2. Append k zeros where k is smallest non-negative solution to:
           (message_length + 1 + k) ≡ 448 (mod 512)
        3. Append original length in bits as 64-bit big-endian integer
        """
        msg_len = len(message)
        msg_bit_len = msg_len * 8
        
        # Append '1' bit (0x80 = 10000000)
        message += b'\x80'
        
        # Append zeros until length ≡ 448 (mod 512) bits = 56 (mod 64) bytes
        while (len(message) % 64) != 56:
            message += b'\x00'
        
        # Append original length as 64-bit big-endian
        message += msg_bit_len.to_bytes(8, 'big')
        
        return message
    
    def parse_message_blocks(self, padded_message: bytes) -> List[bytes]:
        """Parse padded message into 512-bit (64-byte) blocks"""
        return [padded_message[i:i+64] for i in range(0, len(padded_message), 64)]
    
    def compute_message_schedule(self, block: bytes) -> List[int]:
        """
        Compute message schedule W[0..63]
        
        For t = 0..15: W[t] = M[t] (direct from message block)
        For t = 16..63: W[t] = σ1(W[t-2]) + W[t-7] + σ0(W[t-15]) + W[t-16]
        
        This is where diffusion begins - each word depends on 4 previous words
        """
        W = []
        
        # First 16 words from message block (big-endian)
        for i in range(16):
            W.append(int.from_bytes(block[i*4:(i+1)*4], 'big'))
        
        # Extend to 64 words using message schedule expansion
        for t in range(16, 64):
            s0 = gamma0(W[t-15])
            s1 = gamma1(W[t-2])
            W.append((W[t-16] + s0 + W[t-7] + s1) & 0xFFFFFFFF)
        
        self.message_schedule = W
        return W
    
    def compression_round(self, t: int) -> SHA256State:
        """
        Perform one round of SHA256 compression
        
        T1 = h + Σ1(e) + Ch(e,f,g) + K[t] + W[t]
        T2 = Σ0(a) + Maj(a,b,c)
        
        h = g
        g = f
        f = e
        e = d + T1
        d = c
        c = b
        b = a
        a = T1 + T2
        
        All operations mod 2^32
        """
        state = self.state.copy()
        state.round = t
        
        # Get message schedule word
        W_t = self.message_schedule[t]
        state.w_t = W_t
        
        # Compute T1
        S1 = sigma1(state.e)
        ch_result = ch(state.e, state.f, state.g)
        state.t1 = (state.h + S1 + ch_result + SHA256_K[t] + W_t) & 0xFFFFFFFF
        
        # Compute T2
        S0 = sigma0(state.a)
        maj_result = maj(state.a, state.b, state.c)
        state.t2 = (S0 + maj_result) & 0xFFFFFFFF
        
        # Update working variables
        state.h = state.g
        state.g = state.f
        state.f = state.e
        state.e = (state.d + state.t1) & 0xFFFFFFFF
        state.d = state.c
        state.c = state.b
        state.b = state.a
        state.a = (state.t1 + state.t2) & 0xFFFFFFFF
        
        self.state = state
        self.round_trace.append(state.copy())
        
        return state
    
    def compress(self, block: bytes) -> SHA256State:
        """
        Full compression function for one 512-bit block
        
        This is the core one-way function - easy to compute forward,
        computationally infeasible to invert
        """
        # Reset state for new block
        self.state = SHA256State()
        self.round_trace = []
        
        # Compute message schedule
        self.compute_message_schedule(block)
        
        # Perform 64 rounds
        for t in range(64):
            self.compression_round(t)
        
        return self.state
    
    def final_hash(self, state: SHA256State) -> bytes:
        """
        Compute final hash by adding compressed state to initial values
        """
        h0 = (SHA256_H0[0] + state.a) & 0xFFFFFFFF
        h1 = (SHA256_H0[1] + state.b) & 0xFFFFFFFF
        h2 = (SHA256_H0[2] + state.c) & 0xFFFFFFFF
        h3 = (SHA256_H0[3] + state.d) & 0xFFFFFFFF
        h4 = (SHA256_H0[4] + state.e) & 0xFFFFFFFF
        h5 = (SHA256_H0[5] + state.f) & 0xFFFFFFFF
        h6 = (SHA256_H0[6] + state.g) & 0xFFFFFFFF
        h7 = (SHA256_H0[7] + state.h) & 0xFFFFFFFF
        
        return b''.join(h.to_bytes(4, 'big') for h in [h0, h1, h2, h3, h4, h5, h6, h7])
    
    def compute_full_sha256(self, message: bytes) -> Tuple[bytes, Dict]:
        """
        Compute complete SHA256 hash with derivation metadata
        """
        # Pad message
        padded = self.pad_message(message)
        
        # Parse into blocks
        blocks = self.parse_message_blocks(padded)
        
        # Process each block
        current_state = SHA256State()
        
        for i, block in enumerate(blocks):
            # Compute message schedule
            W = self.compute_message_schedule(block)
            
            # Set initial state (for first block) or use previous hash
            if i == 0:
                self.state = SHA256State()
            else:
                # Add previous hash to current state
                self.state.a = (self.state.a + current_state.a) & 0xFFFFFFFF
                self.state.b = (self.state.b + current_state.b) & 0xFFFFFFFF
                self.state.c = (self.state.c + current_state.c) & 0xFFFFFFFF
                self.state.d = (self.state.d + current_state.d) & 0xFFFFFFFF
                self.state.e = (self.state.e + current_state.e) & 0xFFFFFFFF
                self.state.f = (self.state.f + current_state.f) & 0xFFFFFFFF
                self.state.g = (self.state.g + current_state.g) & 0xFFFFFFFF
                self.state.h = (self.state.h + current_state.h) & 0xFFFFFFFF
            
            # Compress
            for t in range(64):
                self.compression_round(t)
            
            current_state = self.state.copy()
        
        # Final hash
        final_hash = self.final_hash(current_state)
        
        metadata = {
            "original_length": len(message),
            "padded_length": len(padded),
            "num_blocks": len(blocks),
            "total_rounds": len(blocks) * 64,
            "hash_hex": final_hash.hex()
        }
        
        return final_hash, metadata


# ============================================================================
# SECURITY ANALYSIS AND ATTACK COMPLEXITY
# ============================================================================

@dataclass
class SecurityAnalysis:
    """Analysis of SHA256 security properties and attack complexity"""
    
    # Hash output size
    output_bits: int = 256
    
    # Preimage resistance: Given h, find m such that H(m) = h
    preimage_complexity: int = 2**256
    
    # Second preimage resistance: Given m1, find m2 such that H(m1) = H(m2)
    second_preimage_complexity: int = 2**256
    
    # Collision resistance: Find any m1, m2 such that H(m1) = H(m2)
    # Birthday paradox: sqrt of search space
    collision_complexity: int = 2**128
    
    # Avalanche effect: Changing 1 bit changes ~50% of output
    avalanche_factor: float = 0.5
    
    def compute_attack_feasibility(self, attack_type: str) -> Dict:
        """
        Compute feasibility of various attack types
        """
        # Physical limits
        bremermann_limit = 1.36e50  # bits/sec/kg (maximum computational rate)
        earth_mass = 5.97e24  # kg
        age_of_universe_seconds = 4.35e17  # seconds (13.8 billion years)
        
        if attack_type == "brute_force_preimage":
            operations_needed = self.preimage_complexity
            time_on_earth_computer = operations_needed / (bremermann_limit * earth_mass)
            time_as_universe_age = time_on_earth_computer / age_of_universe_seconds
            
            return {
                "attack_type": "Brute Force Preimage Attack",
                "operations_needed": f"2^256 ≈ {operations_needed:.2e}",
                "time_on_planetary_computer": f"{time_on_earth_computer:.2e} seconds",
                "time_as_universe_ages": f"{time_as_universe_age:.2e} universe ages",
                "feasibility": "PHYSICALLY IMPOSSIBLE"
            }
        
        elif attack_type == "birthday_collision":
            operations_needed = self.collision_complexity
            time_on_earth_computer = operations_needed / (bremermann_limit * earth_mass)
            time_as_universe_age = time_on_earth_computer / age_of_universe_seconds
            
            return {
                "attack_type": "Birthday Collision Attack",
                "operations_needed": f"2^128 ≈ {operations_needed:.2e}",
                "time_on_planetary_computer": f"{time_on_earth_computer:.2e} seconds",
                "time_as_universe_ages": f"{time_as_universe_age:.2e} universe ages",
                "feasibility": "PHYSICALLY IMPOSSIBLE"
            }
        
        elif attack_type == "quantum_grover":
            # Grover's algorithm: sqrt of classical search
            operations_needed = 2**128  # Still 2^128 for 256-bit hash
            time_on_earth_computer = operations_needed / (bremermann_limit * earth_mass)
            
            return {
                "attack_type": "Quantum Attack (Grover's Algorithm)",
                "operations_needed": f"2^128 ≈ {operations_needed:.2e}",
                "note": "Grover provides quadratic speedup, but 2^128 is still infeasible",
                "feasibility": "PHYSICALLY IMPOSSIBLE with foreseeable technology"
            }
        
        elif attack_type == "differential_cryptanalysis":
            return {
                "attack_type": "Differential Cryptanalysis",
                "status": "No practical differential path found for full 64-round SHA256",
                "best_known_attack": "Reduced-round variants only (up to ~46 rounds)",
                "full_sha256_security": "256 bits (no known weakness)",
                "feasibility": "NO KNOWN PRACTICAL ATTACK"
            }
        
        return {"error": f"Unknown attack type: {attack_type}"}
    
    def analyze_avalanche_effect(self, message: bytes, deriv: SHA256Derivation) -> Dict:
        """
        Analyze avalanche effect - changing 1 bit should change ~50% of output
        """
        # Compute original hash
        original_hash, _ = deriv.compute_full_sha256(message)
        
        # Flip one bit
        message_bytes = bytearray(message)
        message_bytes[0] ^= 0x01  # Flip least significant bit of first byte
        modified_message = bytes(message_bytes)
        
        # Compute modified hash
        modified_hash, _ = deriv.compute_full_sha256(modified_message)
        
        # Count differing bits
        differing_bits = 0
        for i in range(len(original_hash)):
            xor = original_hash[i] ^ modified_hash[i]
            differing_bits += bin(xor).count('1')
        
        total_bits = len(original_hash) * 8
        avalanche_percentage = differing_bits / total_bits
        
        return {
            "original_hash": original_hash.hex(),
            "modified_hash": modified_hash.hex(),
            "bits_changed": differing_bits,
            "total_bits": total_bits,
            "avalanche_percentage": f"{avalanche_percentage*100:.1f}%",
            "ideal": "50%",
            "assessment": "EXCELLENT" if 0.45 <= avalanche_percentage <= 0.55 else "DEVIATION"
        }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Demonstrate SHA256 derivation and security analysis"""
    
    print("=" * 70)
    print("  SHA256 MATHEMATICAL DERIVATION AND SECURITY ANALYSIS")
    print("  Educational Derivation - NOT FOR EXPLOITATION")
    print("=" * 70)
    print()
    
    # Initialize derivation engine
    deriv = SHA256Derivation()
    security = SecurityAnalysis()
    
    # Test message
    test_message = b"Bitcoin block header data for SHA256 derivation analysis"
    
    print("[SECTION 1] SHA256 ALGORITHM DERIVATION")
    print()
    
    print("  Initial Hash Values (H0):")
    print("  (First 32 bits of fractional parts of square roots of first 8 primes)")
    for i, h in enumerate(SHA256_H0):
        prime = [2, 3, 5, 7, 11, 13, 17, 19][i]
        print(f"    H{chr(97+i)} = 0x{h:08x} ← √{prime}")
    print()
    
    print("  Round Constants (K):")
    print("  (First 32 bits of fractional parts of cube roots of first 64 primes)")
    print(f"    K[0..7] = {[f'0x{k:08x}' for k in SHA256_K[:8]]}")
    print(f"    ... (64 total constants)")
    print()
    
    print("  Compression Function:")
    print("    T1 = h + Σ1(e) + Ch(e,f,g) + K[t] + W[t]")
    print("    T2 = Σ0(a) + Maj(a,b,c)")
    print("    Where:")
    print("      Σ1(e) = ROTR⁶(e) ⊕ ROTR¹¹(e) ⊕ ROTR²⁵(e)")
    print("      Ch(e,f,g) = (e ∧ f) ⊕ (¬e ∧ g)")
    print("      Σ0(a) = ROTR²(a) ⊕ ROTR¹³(a) ⊕ ROTR²²(a)")
    print("      Maj(a,b,c) = (a ∧ b) ⊕ (a ∧ c) ⊕ (b ∧ c)")
    print()
    
    print("[SECTION 2] MESSAGE SCHEDULE EXPANSION")
    print()
    
    # Pad and parse message
    padded = deriv.pad_message(test_message)
    blocks = deriv.parse_message_blocks(padded)
    
    print(f"  Original message length: {len(test_message)} bytes")
    print(f"  Padded message length: {len(padded)} bytes")
    print(f"  Number of 512-bit blocks: {len(blocks)}")
    print()
    
    # Compute message schedule for first block
    W = deriv.compute_message_schedule(blocks[0])
    
    print("  Message Schedule W[0..15] (direct from message):")
    for i in range(16):
        print(f"    W[{i:2d}] = 0x{W[i]:08x}")
    print()
    
    print("  Message Schedule W[16..63] (expanded using σ0, σ1):")
    print("    W[t] = σ1(W[t-2]) + W[t-7] + σ0(W[t-15]) + W[t-16]")
    for i in range(16, 24):
        print(f"    W[{i:2d}] = 0x{W[i]:08x}")
    print("    ... (64 total words)")
    print()
    
    print("[SECTION 3] COMPRESSION ROUNDS (64 iterations)")
    print()
    
    # Run compression
    deriv.compress(blocks[0])
    
    print("  Round trace (first 8 rounds):")
    for i in range(min(8, len(deriv.round_trace))):
        trace = deriv.round_trace[i]
        print(f"    Round {i:2d}: a=0x{trace.a:08x} e=0x{trace.e:08x} T1=0x{trace.t1:08x}")
    print("    ... (64 rounds total)")
    print()
    
    print("[SECTION 4] FINAL HASH COMPUTATION")
    print()
    
    final_hash, metadata = deriv.compute_full_sha256(test_message)
    
    print(f"  Final SHA256 Hash: {final_hash.hex()}")
    print(f"  Metadata:")
    print(f"    Original length: {metadata['original_length']} bytes")
    print(f"    Padded length: {metadata['padded_length']} bytes")
    print(f"    Total rounds: {metadata['total_rounds']}")
    print()
    
    # Verify against standard library
    standard_hash = hashlib.sha256(test_message).hexdigest()
    match = "✓ MATCH" if final_hash.hex() == standard_hash else "✗ MISMATCH"
    print(f"  Verification against hashlib: {match}")
    print()
    
    print("[SECTION 5] AVALANCHE EFFECT ANALYSIS")
    print()
    
    avalanche = security.analyze_avalanche_effect(test_message, deriv)
    
    print(f"  Original:  {avalanche['original_hash']}")
    print(f"  Modified:  {avalanche['modified_hash']} (1 bit flipped)")
    print(f"  Bits changed: {avalanche['bits_changed']}/{avalanche['total_bits']}")
    print(f"  Avalanche: {avalanche['avalanche_percentage']} (ideal: 50%)")
    print(f"  Assessment: {avalanche['assessment']}")
    print()
    
    print("[SECTION 6] SECURITY ANALYSIS AND ATTACK COMPLEXITY")
    print()
    
    attacks = [
        "brute_force_preimage",
        "birthday_collision",
        "quantum_grover",
        "differential_cryptanalysis"
    ]
    
    for attack_type in attacks:
        result = security.compute_attack_feasibility(attack_type)
        print(f"  {result['attack_type']}:")
        if "operations_needed" in result:
            print(f"    Operations: {result['operations_needed']}")
        if "time_on_planetary_computer" in result:
            print(f"    Time: {result['time_on_planetary_computer']}")
        if "time_as_universe_ages" in result:
            print(f"    Universe ages: {result['time_as_universe_ages']}")
        if "status" in result:
            print(f"    Status: {result['status']}")
        if "feasibility" in result:
            print(f"    Feasibility: {result['feasibility']}")
        print()
    
    print("=" * 70)
    print("  CONCLUSION: SHA256 IS COMPUTATIONALLY SECURE")
    print("  No known practical attack exists for the full 64-round algorithm")
    print("  Brute force requires more energy than exists in the observable universe")
    print("=" * 70)
    
    # Save results
    results = {
        "derivation": {
            "initial_values": SHA256_H0,
            "round_constants_count": len(SHA256_K),
            "message_schedule_words": 64,
            "compression_rounds": 64
        },
        "test_hash": {
            "message": test_message.decode(),
            "hash": final_hash.hex(),
            "verification": "match" if final_hash.hex() == standard_hash else "mismatch"
        },
        "avalanche_effect": avalanche,
        "security_analysis": {
            "preimage_resistance": "2^256 operations",
            "collision_resistance": "2^128 operations (birthday bound)",
            "quantum_resistance": "2^128 operations (Grover's algorithm)",
            "best_known_attack": "None for full 64-round SHA256"
        },
        "timestamp": time.time()
    }
    
    output_path = Path(__file__).resolve().parent.parent / "out" / "sha256_derivation_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[+] Results saved to: {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
