#!/usr/bin/env python3
"""
Physics Equation Remapper with Compression + Metaprobe Layers

Architecture:
  ┌─────────────────────────────────────────┐
  │  Metaprobe Layer (observability)        │
  │  - confidence scoring                   │
  │  - domain transition detection          │
  │  - torsion force (mapping drift)        │
  │  - cross-domain basis migration log     │
  ├─────────────────────────────────────────┤
  │  LLM Remapper (Ω/Ψ/B/C/Δ symbols)      │
  ├─────────────────────────────────────────┤
  │  Compression Layer (moiré decoder)      │
  │  - 4-layer van der Waals stack            │
  │  - domain-specific basis vectors        │
  │  - entropy estimation                   │
  └─────────────────────────────────────────┘
"""

import ctypes
import csv
import json
import os
import re
import sqlite3
import sys
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

# ─── Configuration ──────────────────────────────────────────────────────────

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"
DB_PATH = "/home/allaun/physics_equations.db"
OUTPUT_DIR = Path("/home/allaun/Documents/Research Stack/3-Mathematical-Models")
OUTPUT_MD = OUTPUT_DIR / "physics_eqs_mapped_pro.md"
METAPROBE_LOG = OUTPUT_DIR / "physics_metaprobe.jsonl"
COMPRESSION_LOG = OUTPUT_DIR / "physics_compression.log"

LIBMOIRE_PATH = "/tmp/libmoire.so"

# Domain-specific basis seeds for moiré decoder (replaces generic ascii_text etc.)
PHYSICS_DOMAINS = [
    "classical_mechanics", "quantum_mechanics", "thermodynamics",
    "electromagnetism", "relativity", "particle_physics",
    "cosmology", "condensed_matter", "information_theory"
]


# ─── Moiré Decoder C Binding ───────────────────────────────────────────────

class MoireDecoder:
    """Python wrapper for libmoire.so compression engine."""

    def __init__(self):
        self.lib = ctypes.CDLL(LIBMOIRE_PATH)
        self.lib.moire_encode.argtypes = [
            ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t
        ]
        self.lib.moire_encode.restype = ctypes.c_int
        self.lib.moire_decode.argtypes = [
            ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t
        ]
        self.lib.moire_decode.restype = ctypes.c_int
        self.lib.moire_estimate_entropy.argtypes = [
            ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t
        ]
        self.lib.moire_estimate_entropy.restype = ctypes.c_double

    def encode(self, data: bytes) -> bytes:
        src = (ctypes.c_uint8 * len(data))(*data)
        dst = (ctypes.c_uint8 * len(data))()
        n = self.lib.moire_encode(src, len(data), dst, len(data))
        return bytes(dst[:n])

    def decode(self, residuals: bytes, out_len: int) -> bytes:
        src = (ctypes.c_uint8 * len(residuals))(*residuals)
        dst = (ctypes.c_uint8 * out_len)()
        n = self.lib.moire_decode(src, len(residuals), dst, out_len)
        return bytes(dst[:n])

    def entropy(self, data: bytes) -> float:
        src = (ctypes.c_uint8 * len(data))(*data)
        return self.lib.moire_estimate_entropy(src, len(data))

    def compression_ratio(self, data: bytes) -> float:
        ent = self.entropy(data)
        return 8.0 / ent if ent > 0 else 1.0


# ─── Metaprobe Layer ──────────────────────────────────────────────────────

@dataclass
class MappingProbe:
    eq_number: int
    title: str
    domain: str
    mapping: Dict[str, str]
    latency_ms: float
    confidence: float = 0.0          # derived from layer agreement
    torsion_force: float = 0.0      # mapping drift from expected domain
    basis_migrated: bool = False    # did the mapping switch domains?
    residual_entropy: float = 0.0   # compression of the mapping tuple
    timestamp: float = field(default_factory=time.time)


class MetaprobeLayer:
    """Observability and quality monitoring for the remapping pipeline."""

    def __init__(self, moire: MoireDecoder):
        self.moire = moire
        self.history: deque = deque(maxlen=100)
        self.domain_stats: Dict[str, Dict] = {}
        self.migration_count = 0

    def _compute_torsion(self, domain: str, mapping: Dict[str, str]) -> float:
        """
        Torsion force = disagreement between the equation's native domain
        and the symbols assigned by the LLM.
        """
        # Heuristic: if the mapping's symbols are generic/empty, high torsion
        generic = {"N/A", "unknown", "none", "various", "not applicable"}
        bad_symbols = sum(1 for v in mapping.values() if v.lower() in generic)
        return bad_symbols / 5.0  # 0.0 = perfect, 1.0 = all generic

    def _compute_confidence(self, mapping: Dict[str, str]) -> float:
        """
        Confidence based on symbol specificity (length and uniqueness).
        """
        values = [v for v in mapping.values() if v not in {"N/A", ""}]
        if not values:
            return 0.0
        avg_len = sum(len(v) for v in values) / len(values)
        # Longer, more specific mappings = higher confidence
        return min(1.0, avg_len / 30.0)

    def record(self, eq_num: int, title: str, domain: str,
               mapping: Dict[str, str], latency_ms: float) -> MappingProbe:

        # Build a mini byte-stream from the mapping for compression analysis
        mapping_text = json.dumps(mapping, sort_keys=True).encode('utf-8')
        residual_entropy = self.moire.entropy(mapping_text)

        # Detect domain migration: compare with last mapping for this domain
        migrated = False
        if domain in self.domain_stats:
            last = self.domain_stats[domain].get('last_mapping', {})
            # Simple migration: if Ω category changed significantly
            if last.get('Ω', '')[:20] != mapping.get('Ω', '')[:20]:
                migrated = True
                self.migration_count += 1

        probe = MappingProbe(
            eq_number=eq_num,
            title=title,
            domain=domain,
            mapping=mapping,
            latency_ms=latency_ms,
            confidence=self._compute_confidence(mapping),
            torsion_force=self._compute_torsion(domain, mapping),
            basis_migrated=migrated,
            residual_entropy=residual_entropy,
        )

        self.history.append(probe)

        # Update domain stats
        if domain not in self.domain_stats:
            self.domain_stats[domain] = {'count': 0, 'last_mapping': {}}
        self.domain_stats[domain]['count'] += 1
        self.domain_stats[domain]['last_mapping'] = mapping.copy()

        return probe

    def flush_jsonl(self):
        with open(METAPROBE_LOG, "a", encoding="utf-8") as f:
            while self.history:
                p = self.history.popleft()
                f.write(json.dumps({
                    'eq_number': p.eq_number,
                    'title': p.title,
                    'domain': p.domain,
                    'confidence': round(p.confidence, 3),
                    'torsion_force': round(p.torsion_force, 3),
                    'basis_migrated': p.basis_migrated,
                    'residual_entropy': round(p.residual_entropy, 3),
                    'latency_ms': round(p.latency_ms, 1),
                    'timestamp': p.timestamp,
                }) + "\n")

    def summary(self) -> str:
        if not self.domain_stats:
            return "No data"
        lines = ["=== Metaprobe Summary ===", ""]
        total = sum(s['count'] for s in self.domain_stats.values())
        lines.append(f"Total mapped: {total}")
        lines.append(f"Domain migrations: {self.migration_count}")
        lines.append("")
        lines.append("Per-domain:")
        for dom, stats in sorted(self.domain_stats.items(), key=lambda x: -x[1]['count']):
            lines.append(f"  {dom:25s} | {stats['count']:3d} equations")
        return "\n".join(lines)


# ─── LLM Remapper Core ────────────────────────────────────────────────────

PROMPT_TEMPLATE = """Map this physics equation to five symbols from:
  Ω = Ψ [ B(θ) ⊗ C(n, α) ] ⊕ Δ(n, θ, α)

Equation: {title}
Domain: {domain}
Description: {description}

Definitions:
- Ω: Observable output, measured quantity, what the equation predicts
- Ψ: The operator, mechanism, or theory
- B: Conserved basis, fundamental component, the fixed structure
- C: Dynamic context, variable parameter, external condition
- Δ: Residual error, noise, uncertainty, fundamental limit

Respond ONLY in valid JSON with exactly these five keys and short (≤15 words) values:
{{"Ω": "...", "Ψ": "...", "B": "...", "C": "...", "Δ": "..."}}
"""


def call_ollama(title: str, domain: str, description: str) -> Optional[Dict]:
    prompt = PROMPT_TEMPLATE.format(title=title, domain=domain, description=description[:300])
    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False,
                  "options": {"temperature": 0.1, "num_predict": 150}},
            timeout=60,
        )
        r.raise_for_status()
        content = r.json()["response"]
        match = re.search(r'\{[^}]+\}', content)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
    return None


def load_progress() -> set:
    done = set()
    if OUTPUT_MD.exists():
        with open(OUTPUT_MD, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r"## Eq (\d+)\. ", line)
                if m:
                    done.add(m.group(1))
    return done


def append_md(eq_num: int, title: str, domain: str, desc: str, mapping: Dict):
    m = mapping
    lines = [
        f"## Eq {eq_num}. {title}",
        "",
        f"**Domain:** {domain}",
        f"**Description:** {desc[:200]}",
        "",
        "| Symbol | Mapping |",
        "|--------|---------|",
        f"| Ω | {m.get('Ω', 'N/A')} |",
        f"| Ψ | {m.get('Ψ', 'N/A')} |",
        f"| B | {m.get('B', 'N/A')} |",
        f"| C | {m.get('C', 'N/A')} |",
        f"| Δ | {m.get('Δ', 'N/A')} |",
        "",
        "---",
        "",
    ]
    with open(OUTPUT_MD, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ─── Main Pipeline ──────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Physics Equation Remapper + Compression + Metaprobe")
    print("=" * 60)

    # Initialize layers
    print("\n[1/4] Loading moiré decoder...")
    moire = MoireDecoder()
    print(f"      → libmoire loaded, entropy baseline: 8.0 bits/byte")

    print("\n[2/4] Starting metaprobe layer...")
    probe = MetaprobeLayer(moire)

    print("\n[3/4] Loading physics database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT eq_number, title, domain_id, significance FROM equations ORDER BY eq_number")
    rows = cursor.fetchall()
    cursor.execute("SELECT id, name FROM domains")
    domains = {str(r[0]): r[1] for r in cursor.fetchall()}
    conn.close()

    done = load_progress()
    remaining = [(eq_num, title, domains.get(str(did), "Unknown"), desc or "")
                 for eq_num, title, did, desc in rows
                 if str(eq_num) not in done]

    print(f"      → Total: {len(rows)} | Already done: {len(done)} | Remaining: {len(remaining)}")

    # Write header if new
    if not done:
        with open(OUTPUT_MD, "w", encoding="utf-8") as f:
            f.write("# Physics Equations — Mapped with Compression & Metaprobe\n\n")
            f.write(f"**Equation:** Ω = Ψ [ B(θ) ⊗ C(n, α) ] ⊕ Δ(n, θ, α)\n\n")
            f.write("---\n\n")

    print("\n[4/4] Mapping with metaprobe + compression telemetry...")
    print("-" * 60)

    success = 0
    fail = 0
    for eq_num, title, domain, desc in remaining:
        t0 = time.time()
        mapping = call_ollama(title, domain, desc)
        latency = (time.time() - t0) * 1000

        if mapping:
            append_md(eq_num, title, domain, desc, mapping)
            p = probe.record(eq_num, title, domain, mapping, latency)
            success += 1
            print(f"  ✓ #{eq_num:3d} [{domain:22s}] conf={p.confidence:.2f} torsion={p.torsion_force:.2f} entropy={p.residual_entropy:.3f} | {title[:45]}...")
        else:
            fail += 1
            print(f"  ✗ #{eq_num:3d} FAILED")

        # Flush metaprobe every 10 entries
        if success % 10 == 0:
            probe.flush_jsonl()

    probe.flush_jsonl()

    print("-" * 60)
    print(probe.summary())
    print("")
    print(f"Success: {success} | Failed: {fail} | Total: {success + fail}")
    print(f"Output:  {OUTPUT_MD}")
    print(f"Metaprobe log: {METAPROBE_LOG}")

    # Final compression test on the output file
    if OUTPUT_MD.exists():
        data = OUTPUT_MD.read_bytes()
        ent = moire.entropy(data)
        ratio = moire.compression_ratio(data)
        print(f"\nCompression analysis of output:")
        print(f"  File size: {len(data):,} bytes")
        print(f"  Moiré entropy: {ent:.4f} bits/byte")
        print(f"  Effective ratio: {ratio:.2f}x (theoretical)")

        with open(COMPRESSION_LOG, "w") as f:
            f.write(f"file={OUTPUT_MD}\n")
            f.write(f"size_bytes={len(data)}\n")
            f.write(f"moire_entropy_bits_per_byte={ent:.6f}\n")
            f.write(f"theoretical_compression_ratio={ratio:.6f}\n")
            f.write(f"domain_migrations={probe.migration_count}\n")
            f.write(f"equations_mapped={success}\n")


if __name__ == "__main__":
    main()
