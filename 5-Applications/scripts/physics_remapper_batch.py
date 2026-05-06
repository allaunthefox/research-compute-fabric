#!/usr/bin/env python3
"""
Batched Physics Equation Remapper — /dev/shm + GPU batching

Speedup: 1 LLM call per ~40 equations vs 1 per equation.
540 eqs → ~14 calls → ~2 minutes total.

Architecture:
  /dev/shm/physics_equations.db  →  read batch
  GPU batch prompt (40 eqs)     →  single LLM call
  /dev/shm/mapped.jsonl         →  write results
  flush to disk                 →  physics_eqs_mapped_batch.md
  metaprobe + compression       →  per-batch telemetry
"""

import ctypes
import json
import os
import re
import sqlite3
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

# Add extremophile prior system
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extremophile_priors import DeepExtremophilePrior, PriorResult

# ─── Config ─────────────────────────────────────────────────────────────────

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"
DB_PATH = "/dev/shm/physics_equations.db"
SHM_OUT = "/dev/shm/physics_mapped_batch.jsonl"
SHM_META = "/dev/shm/physics_metaprobe_batch.jsonl"
DISK_DIR = Path("/home/allaun/Documents/Research Stack/3-Mathematical-Models")
OUTPUT_MD = DISK_DIR / "physics_eqs_mapped_batch.md"
COMPRESSION_LOG = DISK_DIR / "physics_compression_batch.log"
LIBMOIRE_PATH = "/tmp/libmoire.so"
BATCH_SIZE = 10  # equations per LLM call


# ─── Moiré Decoder ──────────────────────────────────────────────────────────

class MoireDecoder:
    def __init__(self):
        self.lib = ctypes.CDLL(LIBMOIRE_PATH)
        self.lib.moire_encode.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                                          ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t]
        self.lib.moire_encode.restype = ctypes.c_int
        self.lib.moire_estimate_entropy.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t]
        self.lib.moire_estimate_entropy.restype = ctypes.c_double

    def entropy(self, data: bytes) -> float:
        src = (ctypes.c_uint8 * len(data))(*data)
        return self.lib.moire_estimate_entropy(src, len(data))

    def ratio(self, data: bytes) -> float:
        ent = self.entropy(data)
        return 8.0 / ent if ent > 0 else 1.0


# ─── Metaprobe ─────────────────────────────────────────────────────────────

@dataclass
class BatchProbe:
    batch_id: int
    eq_numbers: List[int]
    success_count: int
    fail_count: int
    latency_ms: float
    avg_confidence: float = 0.0
    avg_distortion: float = 0.0
    batch_entropy: float = 0.0
    timestamp: float = field(default_factory=time.time)


class MetaprobeLayer:
    def __init__(self, moire: MoireDecoder):
        self.moire = moire
        self.batches: List[BatchProbe] = []
        self.domain_stats: Dict[str, int] = {}
        self.total_success = 0
        self.total_fail = 0

    def record_batch(self, probe: BatchProbe):
        self.batches.append(probe)
        self.total_success += probe.success_count
        self.total_fail += probe.fail_count

    def flush(self):
        with open(SHM_META, "a", encoding="utf-8") as f:
            for p in self.batches:
                f.write(json.dumps({
                    'batch_id': p.batch_id,
                    'eq_numbers': p.eq_numbers,
                    'success': p.success_count,
                    'fail': p.fail_count,
                    'latency_ms': round(p.latency_ms, 1),
                    'avg_confidence': round(p.avg_confidence, 3),
                    'avg_distortion': round(p.avg_distortion, 3),
                    'batch_entropy': round(p.batch_entropy, 3),
                    'timestamp': p.timestamp,
                }) + "\n")
        self.batches.clear()

    def summary(self) -> str:
        lines = ["=== Metaprobe Summary ===", ""]
        lines.append(f"Total mapped: {self.total_success} | Failed: {self.total_fail}")
        lines.append(f"Batches: {len(self.batches) + sum(1 for _ in open(SHM_META)) if os.path.exists(SHM_META) else len(self.batches)}")
        lines.append("")
        if self.domain_stats:
            lines.append("Per-domain:")
            for dom, cnt in sorted(self.domain_stats.items(), key=lambda x: -x[1]):
                lines.append(f"  {dom:25s} | {cnt:3d}")
        return "\n".join(lines)


# ─── Physics Filter ────────────────────────────────────────────────────────

class PhysicsFilter:
    """
    Filter out equations that require physically unrealistic conditions.

    Rejects equation solutions that violate constraints from organisms
    that survived extreme conditions (pressure, energy, time, compressibility).

    Applied BEFORE LLM remapping to prune physically inadmissible branches.
    """

    def __init__(self):
        self.priors = DeepExtremophilePrior()
        self.rejection_log: List[Dict] = []

    def filter_batch(self, equations: List[Tuple[int, str, str, str]]) -> List[Tuple[int, str, str, str]]:
        """
        Filter equation batch before LLM remapping.

        Extracts physical parameters from equation descriptions and
        rejects those requiring unphysical conditions.
        """
        admissible = []

        for eq_num, title, domain, desc in equations:
            # Extract potential physical parameters from description
            params = self._extract_parameters(desc)

            if params:
                result = self.priors.unified_check(params)

                if result.admissible:
                    admissible.append((eq_num, title, domain, desc))
                else:
                    self._log_rejection(eq_num, title, result)
            else:
                # If no parameters extracted, pass through (can't filter)
                admissible.append((eq_num, title, domain, desc))

        return admissible

    def _extract_parameters(self, desc: str) -> Optional[Dict]:
        """Extract physical parameters from equation description."""
        import re
        params = {}

        # Pressure extraction (look for MPa, GPa, atm, bar)
        pressure_patterns = [
            r'(\d+\.?\d*)\s*MPa',
            r'(\d+\.?\d*)\s*GPa',
            r'(\d+\.?\d*)\s*atm',
            r'(\d+\.?\d*)\s*bar',
        ]
        for pattern in pressure_patterns:
            match = re.search(pattern, desc, re.IGNORECASE)
            if match:
                val = float(match.group(1))
                if 'MPa' in pattern:
                    params['pressure'] = val * 1e6
                elif 'GPa' in pattern:
                    params['pressure'] = val * 1e9
                elif 'atm' in pattern:
                    params['pressure'] = val * 101325
                elif 'bar' in pattern:
                    params['pressure'] = val * 1e5
                break

        # Temperature extraction
        temp_match = re.search(r'(\d+\.?\d*)\s*°?\s*(K|C|°C|°F)', desc)
        if temp_match:
            val = float(temp_match.group(1))
            unit = temp_match.group(2).upper()
            if unit == 'K':
                params['temperature'] = val
            elif unit in ['C', '°C']:
                params['temperature'] = val + 273.15
            elif unit == '°F':
                params['temperature'] = (val - 32) * 5/9 + 273.15

        # Energy/power extraction
        power_patterns = [
            r'(\d+\.?\d*)\s*W',
            r'(\d+\.?\d*)\s*kW',
            r'(\d+\.?\d*)\s*MW',
        ]
        for pattern in power_patterns:
            match = re.search(pattern, desc, re.IGNORECASE)
            if match:
                val = float(match.group(1))
                if 'kW' in pattern:
                    params['power'] = val * 1e3
                elif 'MW' in pattern:
                    params['power'] = val * 1e6
                else:
                    params['power'] = val
                break

        # Time scale extraction
        time_patterns = [
            r'(\d+\.?\d*)\s*yr',
            r'(\d+\.?\d*)\s*year',
            r'(\d+\.?\d*)\s*Myr',
            r'(\d+\.?\d*)\s*Gyr',
        ]
        for pattern in time_patterns:
            match = re.search(pattern, desc, re.IGNORECASE)
            if match:
                val = float(match.group(1))
                if 'Myr' in pattern:
                    params['time'] = val * 1e6 * 365.25 * 24 * 3600
                elif 'Gyr' in pattern:
                    params['time'] = val * 1e9 * 365.25 * 24 * 3600
                else:
                    params['time'] = val * 365.25 * 24 * 3600
                break

        # Default bits (large computation assumed)
        params['bits'] = 1e15

        return params if params else None

    def _log_rejection(self, eq_num: int, title: str, result: PriorResult):
        """Log rejected equations for analysis."""
        self.rejection_log.append({
            'eq_num': eq_num,
            'title': title,
            'violated_constraint': result.violated_constraint,
            'details': result.details,
        })

    def get_rejection_summary(self) -> str:
        """Return summary of rejected equations."""
        if not self.rejection_log:
            return "No equations rejected by physics filter."

        lines = ["=== Physics Filter Rejections ===", ""]
        lines.append(f"Total rejected: {len(self.rejection_log)}")
        lines.append("")

        # Group by violation type
        violations: Dict[str, int] = {}
        for rej in self.rejection_log:
            vtype = rej['violated_constraint'] or 'unknown'
            violations[vtype] = violations.get(vtype, 0) + 1

        lines.append("By violation type:")
        for vtype, count in sorted(violations.items(), key=lambda x: -x[1]):
            lines.append(f"  {vtype:40s} | {count:3d}")

        return "\n".join(lines)


# ─── LLM Batch Prompt ──────────────────────────────────────────────────────

BATCH_PROMPT_TEMPLATE = """You are a physics equation mapper. For EACH equation below, assign symbols from:
  Output = Operator [ Basis(Context) ⊗ Params(n, α) ] ⊕ Error(n, Context, α)

Definitions:
- Output: Observable output / predicted quantity
- Operator: Mechanism or underlying theory
- Basis: Conserved basis / fundamental component
- Params: Dynamic context / variable parameter
- Error: Residual error / noise / fundamental limit

For each equation, respond with ONE line of valid JSON in this exact format:
{{"eq": NUMBER, "Output": "...", "Operator": "...", "Basis": "...", "Params": "...", "Error": "..."}}

Use ≤15 words per value. Respond with exactly {count} JSON lines, one per equation.

--- EQUATIONS ---
{equations}
---
"""


def call_ollama_batch(batch: List[Tuple[int, str, str, str]], batch_id: int) -> List[Optional[Dict]]:
    """Send a batch of equations to LLM, get mappings back."""
    eq_texts = []
    for eq_num, title, domain, desc in batch:
        eq_texts.append(f"[{eq_num}] {title} ({domain}): {desc[:120]}")

    prompt = BATCH_PROMPT_TEMPLATE.format(
        count=len(batch),
        equations="\n".join(eq_texts)
    )

    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False,
                  "options": {"temperature": 0.1, "num_predict": 800}},
            timeout=300,
        )
        r.raise_for_status()
        content = r.json()["response"]

        # Parse each JSON line
        results = [None] * len(batch)
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('```') or line.startswith('//'):
                continue
            # Extract JSON objects
            for match in re.finditer(r'\{[^}]*"eq"\s*:\s*(\d+)[^}]*\}', line):
                try:
                    obj = json.loads(match.group(0))
                    eq_num = int(obj.get('eq', 0))
                    # Find position in batch
                    for i, (b_num, _, _, _) in enumerate(batch):
                        if b_num == eq_num:
                            results[i] = {
                                'Output': obj.get('Output', 'N/A'),
                                'Operator': obj.get('Operator', 'N/A'),
                                'Basis': obj.get('Basis', 'N/A'),
                                'Params': obj.get('Params', 'N/A'),
                                'Error': obj.get('Error', 'N/A'),
                            }
                            break
                except (json.JSONDecodeError, ValueError):
                    pass
        return results

    except Exception as e:
        print(f"  BATCH ERROR #{batch_id}: {e}", file=sys.stderr)
        return [None] * len(batch)


# ─── I/O ────────────────────────────────────────────────────────────────────

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


def append_jsonl(eq_num: int, title: str, domain: str, desc: str, mapping: Dict):
    with open(SHM_OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            'eq_number': eq_num,
            'title': title,
            'domain': domain,
            'description': desc[:200],
            'mapping': mapping,
        }) + "\n")


def flush_to_disk():
    """Convert /dev/shm JSONL to markdown on disk."""
    lines = [
        "# Physics Equations — Batched Mapped (RAM→GPU→SHM→Disk)\n",
        "**Equation:** Output = Operator [ Basis(Context) ⊗ Params(n, α) ] ⊕ Error(n, Context, α)\n\n",
        "---\n\n",
    ]
    with open(SHM_OUT, "r", encoding="utf-8") as f:
        for row in f:
            obj = json.loads(row)
            m = obj['mapping']
            lines.append(f"## Eq {obj['eq_number']}. {obj['title']}\n")
            lines.append(f"**Domain:** {obj['domain']}\n")
            lines.append(f"**Description:** {obj['description']}\n")
            lines.append("| Symbol | Mapping |\n")
            lines.append("|--------|---------|\n")
            for sym in ['Output', 'Operator', 'Basis', 'Params', 'Error']:
                lines.append(f"| {sym} | {m.get(sym, 'N/A')} |\n")
            lines.append("\n---\n\n")

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.writelines(lines)


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Batched Physics Remapper — /dev/shm → GPU → disk")
    print(f"Batch size: {BATCH_SIZE}")
    print("=" * 60)

    print("\n[1/5] Loading moiré decoder...")
    moire = MoireDecoder()
    probe = MetaprobeLayer(moire)

    print("\n[2/5] Reading equations from /dev/shm...")
    equations = load_equations()
    print(f"      → {len(equations)} equations loaded")

    # Chunk into batches
    batches = [equations[i:i+BATCH_SIZE] for i in range(0, len(equations), BATCH_SIZE)]
    print(f"      → {len(batches)} batches of ≤{BATCH_SIZE}")

    print("\n[3/5] Processing batches...")
    print("-" * 60)

    for batch_id, batch in enumerate(batches):
        t0 = time.time()
        results = call_ollama_batch(batch, batch_id)
        latency = (time.time() - t0) * 1000

        success = 0
        fail = 0
        confidences = []
        distortions = []

        for i, (eq_num, title, domain, desc) in enumerate(batch):
            mapping = results[i]
            if mapping:
                append_jsonl(eq_num, title, domain, desc, mapping)
                success += 1
                # Quick confidence heuristics
                vals = [v for v in mapping.values() if v not in {'N/A', ''}]
                avg_len = sum(len(v) for v in vals) / max(len(vals), 1)
                confidences.append(min(1.0, avg_len / 30.0))
                distortions.append(0.0)  # batched: assume ok unless empty
                probe.domain_stats[domain] = probe.domain_stats.get(domain, 0) + 1
            else:
                fail += 1

        # Batch-level compression: entropy of this batch's mappings
        batch_text = json.dumps([r for r in results if r]).encode()
        batch_entropy = moire.entropy(batch_text) if batch_text else 8.0

        bp = BatchProbe(
            batch_id=batch_id,
            eq_numbers=[b[0] for b in batch],
            success_count=success,
            fail_count=fail,
            latency_ms=latency,
            avg_confidence=sum(confidences)/max(len(confidences),1),
            avg_distortion=sum(distortions)/max(len(distortions),1),
            batch_entropy=batch_entropy,
        )
        probe.record_batch(bp)

        print(f"  Batch {batch_id+1:2d}/{len(batches):2d} | {success:2d} OK {fail:2d} FAIL | "
              f"{latency:6.0f}ms | conf={bp.avg_confidence:.2f} | ent={batch_entropy:.3f}")

    print("-" * 60)

    print("\n[4/5] Flushing metaprobe...")
    probe.flush()

    print("\n[5/5] Writing markdown to disk...")
    flush_to_disk()

    # Compression analysis of final output
    data = Path(OUTPUT_MD).read_bytes()
    ent = moire.entropy(data)
    ratio = moire.ratio(data)

    with open(COMPRESSION_LOG, "w") as f:
        f.write(f"file={OUTPUT_MD}\n")
        f.write(f"size_bytes={len(data)}\n")
        f.write(f"moire_entropy={ent:.6f}\n")
        f.write(f"theoretical_ratio={ratio:.6f}\n")
        f.write(f"total_mapped={probe.total_success}\n")
        f.write(f"total_failed={probe.total_fail}\n")
        f.write(f"batch_count={len(batches)}\n")

    print(f"\nDone.")
    print(f"  Mapped: {probe.total_success}/{len(equations)}")
    print(f"  Batches: {len(batches)}")
    print(f"  Output: {OUTPUT_MD} ({len(data):,} bytes)")
    print(f"  Moiré entropy: {ent:.4f} bits/byte")
    print(f"  Compression ratio: {ratio:.2f}x")
    print("")
    print(probe.summary())


if __name__ == "__main__":
    main()
