#!/usr/bin/env python3
"""
Parallel Physics Equation Remapper — 4-6 concurrent workers

Leverages RTX 4070 SUPER: 12GB VRAM, currently 19% utilized.
llama3.1:8b (~4.9GB) can run 2-3 concurrent streams.
With 4 workers: ~4x speedup vs sequential.

Flow:
  /dev/shm/physics_equations.db → read
  4-worker ThreadPoolExecutor → LLM calls
  /dev/shm/mapped.jsonl → write
  flush to disk + compression + metaprobe
"""

import ctypes
import json
import os
import re
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

# ─── Config ─────────────────────────────────────────────────────────────────

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"
DB_PATH = "/dev/shm/physics_equations.db"
SHM_OUT = "/dev/shm/physics_mapped_parallel.jsonl"
SHM_META = "/dev/shm/physics_metaprobe_parallel.jsonl"
DISK_DIR = Path("/home/allaun/Documents/Research Stack/3-Mathematical-Models")
OUTPUT_MD = DISK_DIR / "physics_eqs_mapped_parallel.md"
COMPRESSION_LOG = DISK_DIR / "physics_compression_parallel.log"
LIBMOIRE_PATH = "/tmp/libmoire.so"
MAX_WORKERS = 6  # local GPU: 6 concurrent streams


# ─── Moiré Decoder ──────────────────────────────────────────────────────────

class MoireDecoder:
    def __init__(self):
        self.lib = ctypes.CDLL(LIBMOIRE_PATH)
        self.lib.moire_estimate_entropy.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t]
        self.lib.moire_estimate_entropy.restype = ctypes.c_double

    def entropy(self, data: bytes) -> float:
        src = (ctypes.c_uint8 * len(data))(*data)
        return self.lib.moire_estimate_entropy(src, len(data))

    def ratio(self, data: bytes) -> float:
        ent = self.entropy(data)
        return 8.0 / ent if ent > 0 else 1.0


# ─── LLM Single Equation Call ───────────────────────────────────────────────

PROMPT_TEMPLATE = """Map this physics equation to five symbols from:
  Ω = Ψ [ B(θ) ⊗ C(n, α) ] ⊕ Δ(n, θ, α)

Equation: {title}
Domain: {domain}
Description: {description}

Definitions:
- Ω: Observable output / predicted quantity
- Ψ: Operator, mechanism, or underlying theory
- B: Conserved basis / fundamental component
- C: Dynamic context / variable parameter
- Δ: Residual error / noise / fundamental limit

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
        pass
    return None


# ─── Data Loading ───────────────────────────────────────────────────────────

def load_equations() -> List[Tuple[int, str, str, str]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT eq_number, title, domain_id, significance FROM equations ORDER BY eq_number")
    rows = cursor.fetchall()
    cursor.execute("SELECT id, name FROM domains")
    domains = {str(r[0]): r[1] for r in cursor.fetchall()}
    conn.close()
    return [(eq_num, title, domains.get(str(did), "Unknown"), desc or "")
            for eq_num, title, did, desc in rows]


# ─── Progress Tracking ──────────────────────────────────────────────────────

class ProgressTracker:
    def __init__(self, moire: MoireDecoder, total: int):
        self.moire = moire
        self.total = total
        self.success = 0
        self.fail = 0
        self.domain_stats: Dict[str, int] = {}
        self.entropies: List[float] = []
        self.latencies: List[float] = []

    def record(self, eq_num: int, title: str, domain: str, mapping: Dict, latency_ms: float):
        self.success += 1
        self.domain_stats[domain] = self.domain_stats.get(domain, 0) + 1
        self.latencies.append(latency_ms)
        # Entropy of this mapping
        mapping_text = json.dumps(mapping, sort_keys=True).encode()
        self.entropies.append(self.moire.entropy(mapping_text))

    def record_fail(self):
        self.fail += 1

    def summary(self) -> str:
        lines = ["=== Results ===", ""]
        lines.append(f"Total: {self.total} | Success: {self.success} | Fail: {self.fail}")
        if self.latencies:
            avg_lat = sum(self.latencies) / len(self.latencies)
            lines.append(f"Avg latency: {avg_lat:.0f}ms")
        if self.entropies:
            avg_ent = sum(self.entropies) / len(self.entropies)
            lines.append(f"Avg mapping entropy: {avg_ent:.3f} bits/byte")
        lines.append("")
        lines.append("Top domains:")
        for dom, cnt in sorted(self.domain_stats.items(), key=lambda x: -x[1])[:10]:
            lines.append(f"  {dom:25s} | {cnt:3d}")
        return "\n".join(lines)


# ─── Main Pipeline ──────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print(f"Parallel Physics Remapper — {MAX_WORKERS} workers")
    print("=" * 60)

    print("\n[1/4] Loading moiré decoder...")
    moire = MoireDecoder()

    print("\n[2/4] Reading equations from /dev/shm...")
    equations = load_equations()
    print(f"      → {len(equations)} equations")

    print(f"\n[3/4] Mapping with {MAX_WORKERS} concurrent workers...")
    print("-" * 60)

    tracker = ProgressTracker(moire, len(equations))

    # Open output file for incremental writes
    with open(SHM_OUT, "w", encoding="utf-8") as out_f:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}
            for eq_num, title, domain, desc in equations:
                future = executor.submit(call_ollama, title, domain, desc)
                futures[future] = (eq_num, title, domain, desc, time.time())

            for future in as_completed(futures):
                eq_num, title, domain, desc, t0 = futures[future]
                latency = (time.time() - t0) * 1000
                mapping = future.result()

                if mapping:
                    tracker.record(eq_num, title, domain, mapping, latency)
                    out_f.write(json.dumps({
                        'eq_number': eq_num,
                        'title': title,
                        'domain': domain,
                        'mapping': mapping,
                    }) + "\n")
                    out_f.flush()
                    print(f"  ✓ #{eq_num:3d} [{domain:22s}] lat={latency:5.0f}ms | {title[:40]}...")
                else:
                    tracker.record_fail()
                    print(f"  ✗ #{eq_num:3d} FAILED")

    print("-" * 60)

    print("\n[4/4] Writing markdown to disk...")
    lines = [
        "# Physics Equations — Parallel Mapped\n",
        f"**Workers:** {MAX_WORKERS} | **Equation:** Ω = Ψ [ B(θ) ⊗ C(n, α) ] ⊕ Δ(n, θ, α)\n\n",
        "---\n\n",
    ]
    with open(SHM_OUT, "r", encoding="utf-8") as f:
        for row in f:
            obj = json.loads(row)
            m = obj['mapping']
            lines.append(f"## Eq {obj['eq_number']}. {obj['title']}\n")
            lines.append(f"**Domain:** {obj['domain']}\n")
            lines.append("| Symbol | Mapping |\n")
            lines.append("|--------|---------|\n")
            for sym in ['Ω', 'Ψ', 'B', 'C', 'Δ']:
                lines.append(f"| {sym} | {m.get(sym, 'N/A')} |\n")
            lines.append("\n---\n\n")

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.writelines(lines)

    # Compression analysis
    data = Path(OUTPUT_MD).read_bytes()
    ent = moire.entropy(data)
    ratio = moire.ratio(data)

    with open(COMPRESSION_LOG, "w") as f:
        f.write(f"file={OUTPUT_MD}\n")
        f.write(f"size_bytes={len(data)}\n")
        f.write(f"moire_entropy={ent:.6f}\n")
        f.write(f"theoretical_ratio={ratio:.6f}\n")
        f.write(f"workers={MAX_WORKERS}\n")
        f.write(f"total_mapped={tracker.success}\n")
        f.write(f"total_failed={tracker.fail}\n")

    print(f"\nOutput: {OUTPUT_MD} ({len(data):,} bytes)")
    print(f"Moiré entropy: {ent:.4f} bits/byte")
    print(f"Compression ratio: {ratio:.2f}x")
    print("")
    print(tracker.summary())


if __name__ == "__main__":
    main()
