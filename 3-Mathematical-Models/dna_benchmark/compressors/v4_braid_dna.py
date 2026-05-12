#!/usr/bin/env python3
"""
V4 DNA Braid/Rope Compressor — Cayley Fibergraph Encoding
===========================================================

Every DNA base → Klein four-group V4 element.
Every transition → braid crossing action.
Every complement → involution in the group.
Every storage address → NUVMAP projection from group coordinates.

Encoding:  store (g_0, a_0, a_1, ..., a_{n-1}) NOT (s_0, s_1, ..., s_{n-1})
          g_{i+1} = a_i · g_i  (Cayley table lookup)

When the group matches the data's latent symmetry:
  H(action_stream) < H(symbol_stream) → compression

V4 = {e, a, b, c}  where a² = b² = c² = e, ab = c, ba = c, etc.
Mapping: A→a, C→b, G→c, T→abc
Complement: a↔abc (A↔T), b↔c (C↔G) — all involutions
"""

import struct, math, sys, os, time, json, tempfile, subprocess
import hashlib
from typing import Dict, List, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass

# ── V4 Group Algebra ──

# V4 elements: e=0, a=1, b=2, c=3
V4_E, V4_A, V4_B, V4_C = 0, 1, 2, 3

# Cayley table: T[x][y] = x·y
V4_CAYLEY = [
    [0, 1, 2, 3],  # e·e=e, e·a=a, e·b=b, e·c=c
    [1, 0, 3, 2],  # a·e=a, a·a=e, a·b=c, a·c=b
    [2, 3, 0, 1],  # b·e=b, b·a=c, b·b=e, b·c=a
    [3, 2, 1, 0],  # c·e=c, c·a=b, c·b=a, c·c=e
]

# DNA base → V4 element
BASE_TO_V4 = {"A": V4_A, "C": V4_B, "G": V4_C, "T": 3}  # T = abc = a·b·c = V4_C·V4_B
V4_TO_BASE = {0: "?", 1: "A", 2: "C", 3: "G"}

# T = abc = a·b·c. In V4: a·b = c, so abc = c·c = e. Wait, that's wrong.
# V4: a·a=e, b·b=e, c·c=e.
# a·b = c  (from Cayley: T[1][2]=3)
# a·c = b  (T[1][3]=2)
# b·c = a  (T[2][3]=1)
# a·b·c = (a·b)·c = c·c = e.
# T is NOT abc. Let me fix: T should map to (1,1,1) which is a·b·c in the group.
# But we only have 4 elements. T must be one of them.
# Actually: use V4 as direct product Z2×Z2. Elements as bit pairs:
# e=(0,0), a=(1,0), b=(0,1), c=(1,1)
# Then T = a·b = c since (1,0)+(0,1) = (1,1) = c.
# Wait no. Let me redo with the correct encoding:

# Better mapping: use Z2×Z2 additive notation
# elements as 2-bit: e=(0,0), a=(1,0), b=(0,1), c=(1,1)
# operation is XOR: (x1,y1)+(x2,y2) = (x1⊕x2, y1⊕y2)
# Then: a+b = (1,0)+(0,1) = (1,1) = c ✓

# DNA mapping: A=(1,0), C=(0,1), G=(1,1), T=(0,0) or similar
# Actually let me use a better encoding that makes complement natural:
# Complement A↔T: if A=(1,0), let T=(1,1). Differs by (0,1) = b
# Complement C↔G: if C=(0,1), let G=(1,1). Differs by (1,0) = a
# Hmm, not clean. Let me just use a fixed mapping:

# Use complement as a specific group action:
# complement_action = (1,1) = c
# A = (0,0) = e   → A↔T: T = c·e = (1,1) = c
# C = (1,0) = a   → C↔G: G = c·a = (1,1)+(1,0) = (0,1) = b ?
# Actually c·a in XOR: (1,1)⊕(1,0) = (0,1). So G = b. Hmm.
# That means A=e→T=c, C=a→G=b. Not great for readability.

# Actually: define complement as swap of x-bit = a-action
# A=(0,0)=e, T=(1,0)=a: differ by (1,0)
# C=(0,1)=b, G=(1,1)=c: differ by (1,0)
# This makes complement = (1,0) shift = a-action on x-bit.
# That's clean! complement = a, self-complement = a²=e.

# Final mapping:
# A = (0,0) = e    → complement = a → T = (1,0) = V4_A
# C = (0,1) = b    → complement = a → G = (1,1) = V4_C  (in our enum)
# G = V4_C (3)     → complement = a → C = V4_B (2)
# T = V4_A (1)     → complement = a → A = V4_E (0)

# So: BASE_TO_V4 = {"A": 0, "T": 1, "C": 2, "G": 3}
# Complement action = multiply by V4_A (1)
# T[1][0] = 1 = T ✓ (from Cayley, T[1][0]=1 means a·e=a, so complement of A=e is a=T ✓)
# T[1][2] = 3 = G ✓ (from Cayley, T[1][2]=3 means a·b=c, so complement of C=b is c=G ✓)

# This is clean. Let me redefine:

BASE_TO_V4 = {"A": V4_E, "T": V4_A, "C": V4_B, "G": V4_C}
V4_TO_BASE = {V4_E: "A", V4_A: "T", V4_B: "C", V4_C: "G"}
COMPLEMENT_ACTION = V4_A  # multiply by 'a' gives complement

# Validate:
# A→T: T[COMPLEMENT_ACTION][V4_E] = T[1][0] = 1 = V4_A = T ✓
# C→G: T[COMPLEMENT_ACTION][V4_B] = T[1][2] = 3 = V4_C = G ✓
# T→A: T[COMPLEMENT_ACTION][V4_A] = T[1][1] = 0 = V4_E = A ✓
# G→C: T[COMPLEMENT_ACTION][V4_C] = T[1][3] = 2 = V4_B = C ✓
# All correct.

# Braid crossing actions:
# σ_forward  = V4_B  (b-action, rotates A→C, C→A, G↔T swap)
# σ_reverse  = V4_B  (same, since b²=e in V4, forward=reverse=involution)
# Actually in V4 every non-id element is order-2, so forward=reverse always.
# Braid relations are trivially satisfied. V4 is abelian, so σ_i σ_j = σ_j σ_i always.

ACTION_NAMES = {V4_A: "σ_cmp", V4_B: "σ_trans", V4_C: "σ_twist", V4_E: "I"}


class V4BraidEncoder:
    """
    V4 DNA Braid/Rope encoder.

    Encode:  DNA strand → V4 element stream → action delta stream
    Decode:  action delta stream → V4 element stream → DNA strand
    """

    def __init__(self):
        self.cayley = V4_CAYLEY

    def _action(self, from_elem: int, to_elem: int) -> int:
        """Find the group action that takes from_elem to to_elem: to = a · from"""
        for a in range(4):
            if self.cayley[a][from_elem] == to_elem:
                return a
        return 0  # identity as fallback

    def encode(self, dna: str, encode_verbatim: bool = False) -> Tuple[bytes, Dict]:
        """
        Encode DNA sequence as V4 action stream.

        If encode_verbatim: output 2 bits per base (identity stream).
        If not: output first base (2 bits) + action delta stream.

        Returns (encoded_bytes, metadata_dict).
        """
        if not dna:
            return b"", {"length": 0}

        # Convert to V4 elements
        elements = [BASE_TO_V4.get(b, 0) for b in dna.upper()]
        n = len(elements)

        # Encode: [first_element:2bits] [action_0:2bits] [action_1:2bits] ...
        # 2 bits per element, but actions may have lower entropy
        bits = []

        # First element: 2 bits
        bits.extend([(elements[0] >> 1) & 1, elements[0] & 1])

        # Action stream
        actions = []
        for i in range(1, n):
            a = self._action(elements[i-1], elements[i])
            actions.append(a)
            bits.extend([(a >> 1) & 1, a & 1])

        # Pack bits into bytes
        packed = bytearray()
        for j in range(0, len(bits), 8):
            byte = 0
            for b in range(8):
                if j + b < len(bits):
                    byte |= bits[j + b] << (7 - b)  # MSB first
            packed.append(byte)

        compressed = bytes(packed)

        # Compute action entropy
        action_counter = Counter(actions)
        total = len(actions)
        action_entropy = -sum((c/total) * math.log2(c/total)
                             for c in action_counter.values()) if total > 0 else 0.0

        return compressed, {
            "length": n,
            "compressed_bytes": len(compressed),
            "raw_bits": n * 2,
            "action_entropy": round(action_entropy, 4),
            "idle_fraction": round(action_counter.get(V4_E, 0) / max(total, 1), 4),
            "complement_fraction": round(action_counter.get(V4_A, 0) / max(total, 1), 4),
            "transition_fraction": round(action_counter.get(V4_B, 0) / max(total, 1), 4),
            "twist_fraction": round(action_counter.get(V4_C, 0) / max(total, 1), 4),
            "most_common_action": action_counter.most_common(1)[0] if action_counter else None,
            "action_distribution": dict(action_counter),
            "group": "V4",
            "sha256": hashlib.sha256(dna.encode()).hexdigest(),
        }

    def decode(self, compressed: bytes, length: int) -> str:
        """Decode V4 action stream back to DNA sequence."""
        if length == 0:
            return ""

        # Unpack bits (MSB first)
        bits = []
        for byte in compressed:
            for b in range(8):
                bits.append((byte >> (7 - b)) & 1)

        # First element
        elem = (bits[0] << 1) | bits[1]
        result = [V4_TO_BASE.get(elem, "N")]

        # Action stream: decode each action and apply
        bit_pos = 2
        for i in range(1, length):
            if bit_pos + 1 >= len(bits):
                break
            action = (bits[bit_pos] << 1) | bits[bit_pos + 1]
            bit_pos += 2
            elem = self.cayley[action][elem]
            result.append(V4_TO_BASE.get(elem, "N"))

        return "".join(result)

    def roundtrip(self, dna: str) -> Tuple[bool, int, int]:
        """Test encode/decode cycle."""
        compressed, meta = self.encode(dna)
        decoded = self.decode(compressed, len(dna))
        ok = dna.upper() == decoded.upper()
        return ok, len(compressed), len(dna)

    # ── PIST integration ──

    def to_pist_coords(self, dna: str) -> List[Tuple[int, int]]:
        """Convert DNA to PIST shell coordinates via V4 elements."""
        if "pist_encode" not in globals():
            from pist_biological_polymorphic_shifter_v3_complete import pist_encode
        else:
            pist_encode = globals().get("pist_encode")

        coords = []
        for base in dna.upper():
            g = BASE_TO_V4.get(base, 0)
            # g ∈ [0,3], use as PIST input
            k, t = pist_encode(g)
            coords.append((k, t))
        return coords

    def nu_vmap_coords(self, dna: str) -> List[Dict]:
        """Compute NUVMAP texel coordinates for DNA sequence."""
        coords = self.to_pist_coords(dna)
        result = []
        for i, (k, t) in enumerate(coords):
            g = BASE_TO_V4.get(dna[i].upper(), 0)
            result.append({
                "position": i,
                "base": dna[i],
                "V4_element": g,
                "pist_shell": k,
                "pist_offset": t,
                "pist_mass": t * (2*k + 1 - t),
                "is_complement_target": g in (V4_A, V4_C),  # T and G
                "orbit": [V4_CAYLEY[x][g] for x in range(4)],  # action orbit
        })
        return result

    # ── Braid/rope analysis ──

    def braid_analysis(self, dna: str) -> Dict:
        """Analyze DNA as braid word with V4 strand operators."""
        elements = [BASE_TO_V4.get(b, 0) for b in dna.upper()]
        actions = [self._action(elements[i-1], elements[i]) for i in range(1, len(elements))]

        # Braid word length (in Artin generators)
        braid_word = []
        for a in actions:
            if a == V4_A:
                braid_word.append("c")  # complement crossing
            elif a == V4_B:
                braid_word.append("s")  # transition crossing
            elif a == V4_C:
                braid_word.append("t")  # twist crossing
            else:
                braid_word.append("1")  # identity

        # Simplify by canceling adjacent inverses (all are involutions in V4)
        simplified = []
        for op in braid_word:
            if simplified and simplified[-1] == op:
                simplified.pop()  # σ² = e in V4
            else:
                simplified.append(op)

        # Run-length compress the simplified word
        runs = []
        if braid_word:
            current = braid_word[0]; count = 1
            for op in braid_word[1:]:
                if op == current:
                    count += 1
                else:
                    runs.append((current, count))
                    current = op; count = 1
            runs.append((current, count))

        return {
            "original_length": len(elements),
            "braid_word_length": len(braid_word),
            "simplified_length": len(simplified),
            "compression_ratio": len(simplified) / max(len(braid_word), 1),
            "runs": runs,
            "num_runs": len(runs),
            "unique_actions": len(set(braid_word)),
            "identity_fraction": braid_word.count("1") / max(len(braid_word), 1),
        }


# ── Benchmark ──

def benchmark_v4_vs_all(dna: str, label: str,
                         brotli_lvl: int = 11, zstd_lvl: int = 19,
                         xz_lvl: int = 9) -> Dict:
    """Benchmark V4 braid encoder against system compressors."""
    encoder = V4BraidEncoder()

    results = []

    # V4 encoder
    t0 = time.time()
    comp, meta = encoder.encode(dna)
    v4_time = time.time() - t0

    t0 = time.time()
    dec = encoder.decode(comp, len(dna))
    v4_dec_time = time.time() - t0

    ok = dna.upper() == dec.upper()
    bpb = (len(comp) * 8) / max(len(dna), 1)

    results.append({
        "algo": "V4-braid",
        "label": label,
        "lossless": ok,
        "original": len(dna),
        "compressed": len(comp),
        "bpb": round(bpb, 3),
        "ratio": round(len(comp) / max(len(dna), 1), 4),
        "time_s": round(v4_time, 3),
        "dec_time_s": round(v4_dec_time, 3),
        "action_entropy": meta.get("action_entropy", 0),
        "idle_fraction": meta.get("idle_fraction", 0),
    })

    # System compressors
    dna_bytes = dna.encode()
    for algo, compress_cb, lvl, ext in [
        ("brotli", lambda d: subprocess.run(["brotli","-q",str(brotli_lvl),"-f","-c"],input=d,capture_output=True).stdout, brotli_lvl, ".br"),
        ("zstd", lambda d: subprocess.run(["zstd","-"+str(zstd_lvl),"-q","-f","-c"],input=d,capture_output=True).stdout, zstd_lvl, ".zst"),
        ("xz", lambda d: subprocess.run(["xz","-"+str(xz_lvl),"-f","-c","-z"],input=d,capture_output=True).stdout, xz_lvl, ".xz"),
        ("gzip", lambda d: subprocess.run(["gzip","-9","-f","-c"],input=d,capture_output=True).stdout, 9, ".gz"),
    ]:
        t0 = time.time()
        try:
            out = compress_cb(dna_bytes)
            ct = time.time() - t0
            if out:
                results.append({
                    "algo": algo,
                    "label": label,
                    "original": len(dna),
                    "compressed": len(out),
                    "bpb": round(len(out)*8/max(len(dna),1), 3),
                    "ratio": round(len(out)/max(len(dna),1), 4),
                    "time_s": round(ct, 3),
                })
        except: pass

    return results


def main():
    """Run demo and benchmark."""
    encoder = V4BraidEncoder()

    # Test sequences
    tests = [
        ("ACGT" * 50, "simple_repeat"),
        ("A" * 500, "polyA"),
        ("ATCG" * 50, "alternating"),
    ]

    # Load real data
    import gzip
    try:
        with gzip.open("/home/allaun/dna_benchmark/data/ecoli.fna.gz", "rt") as f:
            ecoli = "".join(line.strip() for line in f if not line.startswith(">"))
        tests.append((ecoli[:10000], "ecoli_10k"))
    except: pass

    print("=" * 64)
    print("V4 BRAID/ROPE DNA COMPRESSOR")
    print("=" * 64)
    print(f"\n  Group: V4 (Klein four-group, Z2×Z2)")
    print(f"  A={V4_TO_BASE[0]} T={V4_TO_BASE[1]} C={V4_TO_BASE[2]} G={V4_TO_BASE[3]}")
    print(f"  Complement action: a·g  (complement pairs: A↔T, C↔G)")
    print(f"  All non-identity actions are involutions (σ² = e)")

    for dna, label in tests:
        print(f"\n{'─' * 64}")
        print(f"  [{label}]  {len(dna)} bases")

        # Roundtrip
        ok, cs, os = encoder.roundtrip(dna)
        print(f"  Roundtrip: {'PASS' if ok else 'FAIL'}  {os}→{cs} bytes ({cs*8/os:.2f} bpb)")

        # Action analysis
        analysis = encoder.braid_analysis(dna)
        print(f"  Braid word: {analysis['braid_word_length']} ops → {analysis['simplified_length']} simplified "
              f"({analysis['num_runs']} runs, {analysis['unique_actions']} unique)")
        print(f"  Identity fraction: {analysis['identity_fraction']:.1%}")

        # Benchmarks
        bench = benchmark_v4_vs_all(dna, label)
        print(f"  {'Algo':12s} {'BPB':>7s} {'Ratio':>7s} {'Time':>7s} {'Size':>7s}")
        for r in sorted(bench, key=lambda x: x.get("bpb", 999)):
            bpb = r.get("bpb", "--")
            ratio = r.get("ratio", "--")
            ts = r.get("time_s", "--")
            sz = r.get("compressed", 0)
            print(f"  {r['algo']:12s} {str(bpb):>7s} {str(ratio):>7s} {str(ts):>7s} {sz:>6,}B")

if __name__ == "__main__":
    main()
