#!/usr/bin/env python3
"""
Receipt-first Erdős investigation with an audit DAG and FAMM memory.

This harness keeps the DAG/FAMM layer honest:
- DAG means the validation workflow, not a theorem result.
- FAMM means a finite associative memory matrix of packets, receipts, and anomalies.
- Conjecture-facing claims stay finite smoke tests unless a verifier packet says more.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from itertools import combinations
from math import lcm
from pathlib import Path
from statistics import mean, pvariance
from typing import Any, Callable


RESEARCH_STACK = Path(__file__).resolve().parents[2]
OUT_PATH = RESEARCH_STACK / "4-Infrastructure/shim/investigate_erdos_dag_famm_results.json"
CHECKPOINT_PATH = RESEARCH_STACK / "4-Infrastructure/shim/investigate_erdos_dag_famm_checkpoint.json"
FAMM_PACKAGES_PATH = RESEARCH_STACK / "4-Infrastructure/shim/investigate_erdos_dag_famm_packages.json"
CHECKPOINT_VERSION = 1


def stable_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


@dataclass
class DagNodeReceipt:
    node_id: str
    depends_on: list[str]
    status: str
    summary: dict[str, Any]
    receipt: str


@dataclass
class FammMemory:
    """Small finite associative memory matrix keyed by domain and status."""

    buckets: dict[str, dict[str, list[dict[str, Any]]]] = field(default_factory=dict)

    def observe(self, domain: str, status: str, packet: dict[str, Any]) -> None:
        slim_packet = {
            "packet_id": packet.get("packet_id"),
            "status": status,
            "receipt": packet.get("receipt"),
            "summary": packet.get("summary", {}),
        }
        self.buckets.setdefault(domain, {}).setdefault(status, []).append(slim_packet)

    def matrix(self) -> dict[str, dict[str, int]]:
        return {
            domain: {status: len(items) for status, items in statuses.items()}
            for domain, statuses in self.buckets.items()
        }


class AuditDag:
    def __init__(self) -> None:
        self.receipts: list[DagNodeReceipt] = []

    def run(
        self,
        node_id: str,
        depends_on: list[str],
        fn: Callable[[], dict[str, Any]],
    ) -> dict[str, Any]:
        result = fn()
        status = str(result.get("status", "unknown"))
        receipt = stable_sha256({"node_id": node_id, "depends_on": depends_on, "result": result})
        self.receipts.append(
            DagNodeReceipt(
                node_id=node_id,
                depends_on=depends_on,
                status=status,
                summary=result.get("summary", {}),
                receipt=receipt,
            )
        )
        return result


class CheckpointStore:
    """Durable packet checkpoint store for resumable finite investigations."""

    def __init__(self, path: Path, resume: bool = False) -> None:
        self.path = path
        self.resume = resume
        self.reused = 0
        self.written = 0
        self.misses = 0
        self.data: dict[str, Any] = {
            "schema": "erdos_dag_famm_checkpoint_v1",
            "version": CHECKPOINT_VERSION,
            "packets": {},
        }
        if resume and path.exists():
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if loaded.get("version") == CHECKPOINT_VERSION and isinstance(loaded.get("packets"), dict):
                self.data = loaded

    def get(self, key: str) -> dict[str, Any] | None:
        if not self.resume:
            self.misses += 1
            return None
        packet = self.data.get("packets", {}).get(key)
        if isinstance(packet, dict):
            self.reused += 1
            return packet
        self.misses += 1
        return None

    def put(self, key: str, packet: dict[str, Any]) -> None:
        self.data.setdefault("packets", {})[key] = packet
        self.data["updated_at"] = datetime.now().isoformat()
        self.written += 1
        self.flush()

    def cached_or_compute(self, key: str, fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        cached = self.get(key)
        if cached is not None:
            return cached
        packet = fn()
        self.put(key, packet)
        return packet

    def flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def summary(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "resume_enabled": self.resume,
            "packet_count": len(self.data.get("packets", {})),
            "reused": self.reused,
            "misses": self.misses,
            "written": self.written,
        }


def famm_delay_class(packet: dict[str, Any]) -> str:
    status = packet.get("status")
    if status in {"invalid_packet", "detector_anomaly"}:
        return "fast_reject"
    if status in {"candidate_requires_external_verify", "odd_covering_candidate_requires_external_verify", "triple_candidate_requires_external_verify"}:
        return "slow_verify"
    if status in {"verified_has_power_two_cycle", "finite_smoke_pass"}:
        return "warm_receipt"
    return "cold_unknown"


def famm_lane_hints(packet: dict[str, Any]) -> list[str]:
    domain = packet.get("domain")
    status = packet.get("status")
    lanes = ["lean_trust", "shm_control"]
    if domain == "erdos_gyarfas":
        lanes.append("vulkan_shader")
    if domain == "erdos_selfridge":
        lanes.extend(["vulkan_shader", "h264_transport"])
    if domain == "erdos_mollin_walsh":
        lanes.extend(["vulkan_shader", "audio_dsp", "h265_transport"])
    if status in {"invalid_packet", "detector_anomaly"}:
        lanes = ["lean_trust", "shm_control"]
    return lanes


DSP_MOTIF_CATALOG: dict[str, dict[str, Any]] = {
    "raw": {
        "role": "pass-through packet waveform",
        "source": "5-Applications/tools-scripts/audio/pipewire_dsp_workloads.py",
        "metrics": ["rms", "zero_crossing_rate"],
    },
    "spectral_focus": {
        "role": "FFT-weighted packet emphasis for density or gap spectra",
        "source": "5-Applications/tools-scripts/audio/pipewire_dsp_workloads.py",
        "metrics": ["spectral_centroid_hz", "spectral_flatness", "dominant_freq_hz"],
    },
    "transient_edge": {
        "role": "packet-boundary and anomaly edge detector",
        "source": "5-Applications/tools-scripts/audio/pipewire_dsp_workloads.py",
        "metrics": ["transient_ratio", "zero_crossing_rate"],
    },
    "hybrid": {
        "role": "blend of raw, spectral, and transient motifs",
        "source": "5-Applications/tools-scripts/audio/pipewire_dsp_workloads.py",
        "metrics": ["rms_ratio", "band_energy_low", "band_energy_mid", "band_energy_high"],
    },
    "palette_control": {
        "role": "map packet features into visual frame palette controls",
        "source": "5-Applications/scripts/palette_dsp_slave.py",
        "metrics": ["frequency", "amplitude", "duty_cycle"],
    },
    "braid_prior": {
        "role": "translate packet feature vectors into mode-bias priors",
        "source": "5-Applications/tools-scripts/braid/braid_dsp_bridge.py",
        "metrics": ["boundary_sensitive", "center_sensitive", "resonance_sensitive", "neutral_traversal"],
    },
    "mode_mux_dsp": {
        "role": "Tang-class DSP mode hint for multiply, accumulate, convolution, FIR, FFT butterfly, adaptive update",
        "source": "4-Infrastructure/hardware/mode_multiplexed_dsp_slice.v",
        "metrics": ["mode", "valid_in", "valid_out", "accumulator"],
    },
}


def dsp_motifs_for_packet(packet: dict[str, Any]) -> list[dict[str, Any]]:
    domain = packet.get("domain")
    status = packet.get("status")
    if status in {"invalid_packet", "detector_anomaly"}:
        motif_names = ["raw", "transient_edge"]
    elif domain == "erdos_gyarfas":
        motif_names = ["transient_edge", "spectral_focus", "mode_mux_dsp"]
    elif domain == "erdos_selfridge":
        motif_names = ["raw", "palette_control", "mode_mux_dsp"]
    elif domain == "erdos_mollin_walsh":
        motif_names = ["spectral_focus", "hybrid", "braid_prior", "mode_mux_dsp"]
    else:
        motif_names = ["raw"]

    motifs = []
    for name in motif_names:
        motif = dict(DSP_MOTIF_CATALOG[name])
        motif["name"] = name
        motif["trust_boundary"] = "DSP motif is a signal/transport hint, not proof-bearing"
        motifs.append(motif)
    return motifs


def preshape_famm_package(packet: dict[str, Any], resume_key: str | None = None) -> dict[str, Any]:
    """Shape a packet for finite associative memory before transport/compute."""

    summary = packet.get("summary", {})
    domain = str(packet.get("domain", "unknown"))
    status = str(packet.get("status", "unknown"))
    packet_id = str(packet.get("packet_id", "unknown"))
    receipt = str(packet.get("receipt", ""))
    package = {
        "schema": "erdos_famm_package_v1",
        "package_id": stable_sha256(
            {
                "domain": domain,
                "packet_id": packet_id,
                "status": status,
                "receipt": receipt,
            }
        ),
        "equation_family": domain,
        "packet_id": packet_id,
        "resume_key": resume_key or f"{domain}:{packet_id}",
        "status": status,
        "delay_class": famm_delay_class(packet),
        "lane_hints": famm_lane_hints(packet),
        "dsp_motifs": dsp_motifs_for_packet(packet),
        "trust_boundary": "transport/acceleration only; Lean/CPU receipt gate owns promotion",
        "summary": summary,
        "receipt": receipt,
        "receipt_short": receipt[:12],
        "shape": {
            "field_keys": sorted(packet.get("field", {}).keys()),
            "spectral_proxy_keys": sorted(packet.get("spectral_proxy", {}).keys()),
            "shear_keys": sorted(packet.get("shear", {}).keys()),
            "packet_keys": sorted(packet.get("packet", {}).keys()),
        },
    }
    package["package_receipt"] = stable_sha256(package)
    return package


def preshape_famm_packages(results: dict[str, Any]) -> list[dict[str, Any]]:
    packages: list[dict[str, Any]] = []
    for result in results.values():
        if not isinstance(result, dict):
            continue
        for packet in result.get("packets", []):
            if isinstance(packet, dict):
                packages.append(preshape_famm_package(packet))
    return packages


def famm_package_matrix(packages: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    matrix: dict[str, dict[str, int]] = {}
    for package in packages:
        domain = package["equation_family"]
        delay = package["delay_class"]
        matrix.setdefault(domain, {}).setdefault(delay, 0)
        matrix[domain][delay] += 1
    return matrix


def normalize_edges(edges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    normalized = []
    for u, v in edges:
        if u == v:
            normalized.append((u, v))
        else:
            normalized.append((min(u, v), max(u, v)))
    return sorted(set(normalized))


def circulant_graph(n: int, jumps: tuple[int, ...] = (1, 2)) -> list[tuple[int, int]]:
    edges: set[tuple[int, int]] = set()
    for i in range(n):
        for jump in jumps:
            j = (i + jump) % n
            edges.add((min(i, j), max(i, j)))
            j = (i - jump) % n
            edges.add((min(i, j), max(i, j)))
    return sorted(edges)


def degree_sequence(n: int, edges: list[tuple[int, int]]) -> list[int]:
    degrees = [0] * n
    for u, v in edges:
        if 0 <= u < n and 0 <= v < n and u != v:
            degrees[u] += 1
            degrees[v] += 1
    return degrees


def adjacency(n: int, edges: list[tuple[int, int]]) -> list[set[int]]:
    adj = [set() for _ in range(n)]
    for u, v in edges:
        if 0 <= u < n and 0 <= v < n and u != v:
            adj[u].add(v)
            adj[v].add(u)
    return adj


def canonical_cycle(cycle: list[int]) -> tuple[int, ...]:
    rotations = []
    m = len(cycle)
    for seq in (cycle, list(reversed(cycle))):
        for i in range(m):
            rotations.append(tuple(seq[i:] + seq[:i]))
    return min(rotations)


def simple_cycles_exact_length(
    n: int,
    edges: list[tuple[int, int]],
    length: int,
    witness_limit: int = 8,
) -> list[list[int]]:
    adj = adjacency(n, edges)
    found: set[tuple[int, ...]] = set()

    def dfs(start: int, current: int, path: list[int], seen: set[int]) -> None:
        if len(found) >= witness_limit:
            return
        if len(path) == length:
            if start in adj[current]:
                found.add(canonical_cycle(path))
            return
        for nxt in sorted(adj[current]):
            if nxt == start or nxt in seen:
                continue
            if nxt < start:
                continue
            dfs(start, nxt, path + [nxt], seen | {nxt})

    for start in range(n):
        dfs(start, start, [start], {start})
        if len(found) >= witness_limit:
            break
    return [list(cycle) for cycle in sorted(found)]


def power_two_lengths(n: int) -> list[int]:
    lengths = []
    k = 4
    while k <= n:
        lengths.append(k)
        k *= 2
    return lengths


def graph_packet(n: int, graph_id: str, edges: list[tuple[int, int]]) -> dict[str, Any]:
    norm_edges = normalize_edges(edges)
    degrees = degree_sequence(n, norm_edges)
    checked_lengths = power_two_lengths(n)
    cycles = {
        str(length): simple_cycles_exact_length(n, norm_edges, length)
        for length in checked_lengths
    }
    flat_cycle_count = sum(len(v) for v in cycles.values())
    invalid_edges = [
        [u, v]
        for u, v in edges
        if u == v or u < 0 or v < 0 or u >= n or v >= n
    ]
    duplicate_edges_removed = len(edges) != len(norm_edges)
    min_degree = min(degrees) if degrees else 0
    edge_receipt = stable_sha256(norm_edges)
    status = (
        "invalid_packet"
        if invalid_edges or duplicate_edges_removed or min_degree < 3
        else "verified_has_power_two_cycle"
        if flat_cycle_count > 0
        else "candidate_requires_external_verify"
    )

    field = {
        "edge_count": len(norm_edges),
        "edge_density": len(norm_edges) / (n * (n - 1) / 2),
        "min_degree": min_degree,
    }
    shear = {
        "degree_variance": pvariance(degrees) if len(degrees) > 1 else 0.0,
        "degree_sequence": degrees,
    }
    spectral_proxy = {
        "trace_A2": 2 * len(norm_edges),
        "max_degree_bound": max(degrees) if degrees else 0,
    }
    packet = {
        "checked_lengths": checked_lengths,
        "cycles_found_by_length": cycles,
        "independent_verifier": "bounded_exact_dfs_per_power_length",
        "edge_receipt": edge_receipt,
    }

    return {
        "packet_id": graph_id,
        "domain": "erdos_gyarfas",
        "status": status,
        "summary": {
            "n": n,
            "min_degree": min_degree,
            "checked_lengths": checked_lengths,
            "power_two_cycle_witness_count": flat_cycle_count,
        },
        "field": field,
        "spectral_proxy": spectral_proxy,
        "shear": shear,
        "packet": packet,
        "receipt": stable_sha256(
            {
                "graph_id": graph_id,
                "n": n,
                "edges": norm_edges,
                "cycles": cycles,
                "status": status,
            }
        ),
    }


def gyarfas_investigation(checkpoint: CheckpointStore | None = None) -> dict[str, Any]:
    def packet_for_n(n: int) -> dict[str, Any]:
        key = f"erdos_gyarfas:circulant_n{n}_jumps_1_2"
        compute = lambda: graph_packet(n, f"circulant_n{n}_jumps_1_2", circulant_graph(n))
        return checkpoint.cached_or_compute(key, compute) if checkpoint else compute()

    packets = [
        packet_for_n(n)
        for n in (8, 10, 12, 14, 16)
    ]
    statuses = {status: sum(1 for p in packets if p["status"] == status) for status in sorted({p["status"] for p in packets})}
    return {
        "status": "finite_smoke_complete",
        "summary": {
            "packets": len(packets),
            "statuses": statuses,
            "claim_boundary": "finite witness search; not a conjecture proof",
        },
        "packets": packets,
    }


def coverage_window(moduli_residues: list[tuple[int, int]], lcm_cap: int = 200_000) -> tuple[list[int], int, bool]:
    modulus_lcm = 1
    for modulus, _ in moduli_residues:
        modulus_lcm = lcm(modulus_lcm, modulus)
        if modulus_lcm > lcm_cap:
            modulus_lcm = lcm_cap
            break

    uncovered = []
    for x in range(modulus_lcm):
        if not any(x % modulus == residue for modulus, residue in moduli_residues):
            uncovered.append(x)
            if len(uncovered) >= 16:
                break
    return uncovered, modulus_lcm, len(uncovered) == 0


def covering_packet(candidate_id: str, moduli_residues: list[tuple[int, int]]) -> dict[str, Any]:
    moduli = [m for m, _ in moduli_residues]
    residues_valid = all(0 <= r < m for m, r in moduli_residues)
    distinct_moduli = len(set(moduli)) == len(moduli)
    all_odd = all(m % 2 == 1 for m in moduli)
    uncovered, window, covers_window = coverage_window(moduli_residues)
    status = (
        "invalid_packet"
        if not residues_valid or not distinct_moduli
        else "odd_covering_candidate_requires_external_verify"
        if all_odd and covers_window
        else "finite_smoke_pass"
    )
    density = sum(1 / m for m in moduli) if moduli else 0.0
    return {
        "packet_id": candidate_id,
        "domain": "erdos_selfridge",
        "status": status,
        "summary": {
            "moduli": moduli,
            "all_odd": all_odd,
            "coverage_window": window,
            "covers_window": covers_window,
            "uncovered_prefix": uncovered,
        },
        "field": {"coverage_density_sum": density},
        "spectral_proxy": {"overlap_pairs_checked": len(list(combinations(moduli_residues, 2)))},
        "shear": {
            "even_modulus_count": sum(1 for m in moduli if m % 2 == 0),
            "odd_modulus_count": sum(1 for m in moduli if m % 2 == 1),
        },
        "packet": {
            "moduli_residues": moduli_residues,
            "distinct_moduli": distinct_moduli,
            "residues_valid": residues_valid,
            "independent_verifier": "exact_lcm_window_when_under_cap",
        },
        "receipt": stable_sha256({"candidate_id": candidate_id, "moduli_residues": moduli_residues, "status": status}),
    }


def selfridge_investigation(checkpoint: CheckpointStore | None = None) -> dict[str, Any]:
    candidates = [
        ("known_even_covering_parity", [(2, 0), (2, 1)]),  # intentionally invalid: repeated modulus
        ("small_even_covering_distinct", [(2, 0), (4, 1), (4, 3)]),  # invalid repeated modulus
        ("odd_noncovering_sample_3_5_7", [(3, 0), (5, 1), (7, 2)]),
        ("mixed_distinct_sample", [(2, 0), (3, 1), (5, 2), (7, 3)]),
    ]
    packets = []
    for candidate_id, system in candidates:
        key = f"erdos_selfridge:{candidate_id}"
        compute = lambda candidate_id=candidate_id, system=system: covering_packet(candidate_id, system)
        packets.append(checkpoint.cached_or_compute(key, compute) if checkpoint else compute())
    statuses = {status: sum(1 for p in packets if p["status"] == status) for status in sorted({p["status"] for p in packets})}
    return {
        "status": "finite_smoke_complete",
        "summary": {
            "packets": len(packets),
            "statuses": statuses,
            "claim_boundary": "finite coverage windows only; not a proof",
        },
        "packets": packets,
    }


def is_powerful_number(n: int) -> bool:
    if n == 1:
        return True
    if n < 1:
        return False
    x = n
    p = 2
    while p * p <= x:
        exponent = 0
        while x % p == 0:
            x //= p
            exponent += 1
        if exponent == 1:
            return False
        p += 1 if p == 2 else 2
    return x == 1


def powerful_numbers(limit: int) -> list[int]:
    return [n for n in range(1, limit + 1) if is_powerful_number(n)]


def powerful_packet(limit: int) -> dict[str, Any]:
    nums = powerful_numbers(limit)
    triples = [
        [nums[i], nums[i + 1], nums[i + 2]]
        for i in range(len(nums) - 2)
        if nums[i + 1] == nums[i] + 1 and nums[i + 2] == nums[i] + 2
    ]
    gaps = [b - a for a, b in zip(nums, nums[1:])]
    status = "triple_candidate_requires_external_verify" if triples else "finite_smoke_pass"
    return {
        "packet_id": f"powerful_numbers_to_{limit}",
        "domain": "erdos_mollin_walsh",
        "status": status,
        "summary": {
            "limit": limit,
            "powerful_count": len(nums),
            "triple_count": len(triples),
            "first_triples": triples[:8],
        },
        "field": {
            "density": len(nums) / limit,
            "avg_gap": mean(gaps) if gaps else 0.0,
        },
        "spectral_proxy": {
            "divisibility_dag_edges": sum(1 for a, b in combinations(nums, 2) if b % a == 0),
        },
        "shear": {
            "gap_variance": pvariance(gaps) if len(gaps) > 1 else 0.0,
            "small_gap_count": sum(1 for gap in gaps if gap <= 2),
        },
        "packet": {
            "powerful_prefix": nums[:32],
            "independent_verifier": "trial_factorization_with_exponent_gate",
        },
        "receipt": stable_sha256({"limit": limit, "powerful_numbers": nums, "triples": triples, "status": status}),
    }


def mollin_walsh_investigation(max_limit: int, checkpoint: CheckpointStore | None = None) -> dict[str, Any]:
    limits = [100, 1000, max_limit]
    packets = []
    for limit in limits:
        key = f"erdos_mollin_walsh:powerful_numbers_to_{limit}"
        compute = lambda limit=limit: powerful_packet(limit)
        packets.append(checkpoint.cached_or_compute(key, compute) if checkpoint else compute())
    statuses = {status: sum(1 for p in packets if p["status"] == status) for status in sorted({p["status"] for p in packets})}
    return {
        "status": "finite_smoke_complete",
        "summary": {
            "packets": len(packets),
            "statuses": statuses,
            "claim_boundary": "finite search only; not a conjecture proof",
        },
        "packets": packets,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-powerful", type=int, default=5000)
    parser.add_argument("--output", type=Path, default=OUT_PATH)
    parser.add_argument("--famm-packages-output", type=Path, default=FAMM_PACKAGES_PATH)
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINT_PATH)
    parser.add_argument("--resume", action="store_true", help="Reuse packets from the checkpoint when keys match.")
    parser.add_argument("--clear-checkpoint", action="store_true", help="Delete the checkpoint before running.")
    args = parser.parse_args()

    if args.clear_checkpoint and args.checkpoint.exists():
        args.checkpoint.unlink()

    dag = AuditDag()
    famm = FammMemory()
    checkpoint = CheckpointStore(args.checkpoint, resume=args.resume)

    gyarfas = dag.run("gyarfas_packet_receipts", [], lambda: gyarfas_investigation(checkpoint))
    for packet in gyarfas["packets"]:
        famm.observe(packet["domain"], packet["status"], packet)

    selfridge = dag.run("selfridge_covering_receipts", [], lambda: selfridge_investigation(checkpoint))
    for packet in selfridge["packets"]:
        famm.observe(packet["domain"], packet["status"], packet)

    mollin = dag.run(
        "mollin_walsh_powerful_receipts",
        [],
        lambda: mollin_walsh_investigation(args.max_powerful, checkpoint),
    )
    for packet in mollin["packets"]:
        famm.observe(packet["domain"], packet["status"], packet)

    synthesis = dag.run(
        "dag_famm_synthesis",
        [
            "gyarfas_packet_receipts",
            "selfridge_covering_receipts",
            "mollin_walsh_powerful_receipts",
        ],
        lambda: {
            "status": "synthesis_complete",
            "summary": {
                "famm_matrix": famm.matrix(),
                "promotion_rule": "Only verified packets promote; finite smoke tests remain finite.",
            },
        },
    )

    domain_results = {
        "erdos_gyarfas": gyarfas,
        "erdos_selfridge": selfridge,
        "erdos_mollin_walsh": mollin,
    }
    famm_packages = preshape_famm_packages(domain_results)
    famm_packages_output = {
        "schema": "erdos_famm_packages_v1",
        "created_at": datetime.now().isoformat(),
        "source_results": str(args.output),
        "package_count": len(famm_packages),
        "package_matrix": famm_package_matrix(famm_packages),
        "packages": famm_packages,
    }

    output = {
        "test_info": {
            "timestamp": datetime.now().isoformat(),
            "harness": "receipt_first_erdos_dag_famm",
            "max_powerful": args.max_powerful,
            "checkpoint": checkpoint.summary(),
            "famm_packages_output": str(args.famm_packages_output),
        },
        "dag_receipts": [asdict(receipt) for receipt in dag.receipts],
        "famm_memory": famm.buckets,
        "famm_matrix": famm.matrix(),
        "famm_packages": {
            "schema": "erdos_famm_packages_v1",
            "package_count": len(famm_packages),
            "package_matrix": famm_package_matrix(famm_packages),
            "packages": famm_packages,
        },
        "results": {
            **domain_results,
            "synthesis": synthesis,
        },
        "validation": {
            "status": "FINITE_INVESTIGATION_COMPLETE",
            "claim_boundary": "No theorem-level claim is made. The harness emits receipts, smoke-test statuses, and verifier packets.",
            "resumability": "Packets are checkpointed by deterministic domain keys; --resume reuses matching packets.",
            "famm_package_shape": "Packages are pre-shaped with delay class, lane hints, resume key, and receipt before surface transport.",
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    args.famm_packages_output.parent.mkdir(parents=True, exist_ok=True)
    args.famm_packages_output.write_text(json.dumps(famm_packages_output, indent=2), encoding="utf-8")

    print("DAG receipts:")
    for receipt in dag.receipts:
        print(f"  {receipt.node_id}: {receipt.status} {receipt.receipt[:12]}")
    print("\nFAMM matrix:")
    print(json.dumps(famm.matrix(), indent=2))
    print("\nCheckpoint:")
    print(json.dumps(checkpoint.summary(), indent=2))
    print("\nFAMM packages:")
    print(json.dumps({"package_count": len(famm_packages), "package_matrix": famm_package_matrix(famm_packages)}, indent=2))
    print(f"\nWrote {args.output}")
    print(f"Wrote {args.famm_packages_output}")


if __name__ == "__main__":
    main()
