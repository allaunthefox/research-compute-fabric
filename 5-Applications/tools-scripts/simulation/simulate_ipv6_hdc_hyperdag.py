#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Simulate IPv6+port hypervector binding and DAG projection.

This script models endpoint coordinates (IP + port) as high-dimensional vectors,
binds them into a superposition wave, and projects sampled points into a prefix
DAG for fast topology-style inspection.

Notes:
- Full IPv6 space (2^128) is not enumerable. This uses deterministic sampling.
- Vectors are bipolar (+1/-1) and use hash-derived random indexing.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import ipaddress
import json
import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple, cast


DEFAULT_DIMS = 4096
DEFAULT_PORTS = "80,443"
DEFAULT_SUBNET = "2001:db8::/120"
DEFAULT_SAMPLES = 1024
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LEDGER_PATH = PROJECT_ROOT / "out" / "hdc_experiment_ledger.csv"


@dataclass
class SimulationConfig:
    subnet: ipaddress.IPv6Network
    ports: List[int]
    dims: int
    max_samples: int
    seed: int
    query_ip: ipaddress.IPv6Address
    query_port: int
    one_line: bool
    one_line_delim: str
    run_label: str
    append_ledger: bool
    ledger_path: Path
    broadcast_bootstrap: bool
    join_threshold: float
    join_report_limit: int


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_ports(value: str) -> List[int]:
    parts = [p.strip() for p in (value or "").split(",") if p.strip()]
    if not parts:
        raise ValueError("at least one port is required")
    out: List[int] = []
    for p in parts:
        try:
            v = int(p)
        except ValueError as exc:
            raise ValueError(f"invalid port: {p}") from exc
        if v < 0 or v > 65535:
            raise ValueError(f"port out of range: {p}")
        out.append(v)
    return sorted(set(out))


def expand_hash_stream(seed: bytes, needed_bits: int) -> bytes:
    chunks: List[bytes] = []
    counter = 0
    needed_bytes = (needed_bits + 7) // 8
    while sum(len(c) for c in chunks) < needed_bytes:
        h = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        chunks.append(h)
        counter += 1
    return b"".join(chunks)[:needed_bytes]


def bipolar_hv(key: str, dims: int) -> List[int]:
    raw = expand_hash_stream(key.encode("utf-8"), dims)
    out: List[int] = [0] * dims
    bit_i = 0
    for b in raw:
        for bit in range(8):
            if bit_i >= dims:
                return out
            out[bit_i] = 1 if ((b >> (7 - bit)) & 1) else -1
            bit_i += 1
    return out


def bind_bipolar(a: List[int], b: List[int]) -> List[int]:
    return [x * y for x, y in zip(a, b)]


def add_into(acc: List[int], v: List[int]) -> None:
    for i, x in enumerate(v):
        acc[i] += x


def sign_normalize(v: List[int]) -> List[int]:
    out: List[int] = [0] * len(v)
    for i, x in enumerate(v):
        out[i] = 1 if x >= 0 else -1
    return out


def dot(a: List[int], b: List[int]) -> int:
    return sum(x * y for x, y in zip(a, b))


def l2_norm(v: List[int]) -> float:
    return math.sqrt(float(sum(x * x for x in v)))


def cosine(a: List[int], b: List[int]) -> float:
    na = l2_norm(a)
    nb = l2_norm(b)
    if na <= 1e-12 or nb <= 1e-12:
        return 0.0
    return float(dot(a, b)) / (na * nb)


def sampled_ipv6_points(net: ipaddress.IPv6Network, max_samples: int, seed: int) -> List[ipaddress.IPv6Address]:
    total = int(net.num_addresses)
    n = max(1, min(max_samples, total))
    base = int(net.network_address)

    if total <= n:
        return [ipaddress.IPv6Address(base + i) for i in range(total)]

    rnd = random.Random(seed)
    offsets: Set[int] = set()
    while len(offsets) < n:
        offsets.add(rnd.randrange(0, total))
    return [ipaddress.IPv6Address(base + off) for off in sorted(offsets)]


def endpoint_hv(ip: ipaddress.IPv6Address, port: int, dims: int) -> List[int]:
    ip_vec = bipolar_hv(f"ip6:{ip.compressed}", dims)
    port_vec = bipolar_hv(f"port:{port}", dims)
    return bind_bipolar(ip_vec, port_vec)


def random_probe_hv(ip: ipaddress.IPv6Address, port: int, dims: int) -> List[int]:
    probe_ip = ipaddress.IPv6Address((int(ip) ^ 0xA5A5A5A5A5A5A5A5A5A5A5A5A5A5A5A5) & ((1 << 128) - 1))
    probe_port = (port + 7919) % 65536
    return endpoint_hv(probe_ip, probe_port, dims)


def combine_sign_vectors(a: List[int], b: List[int], gain: int = 1) -> List[int]:
    out: List[int] = [0] * len(a)
    for i, x in enumerate(a):
        out[i] = x + (gain * b[i])
    return sign_normalize(out)


def compute_query_lift(state_vec: List[int], ip: ipaddress.IPv6Address, port: int, dims: int) -> float:
    query = endpoint_hv(ip, port, dims)
    probe = random_probe_hv(ip, port, dims)
    return cosine(state_vec, query) - cosine(state_vec, probe)


def build_broadcast_payload(cfg: SimulationConfig) -> Dict[str, object]:
    payload_seed = "|".join([
        cfg.subnet.with_prefixlen,
        ",".join(str(p) for p in cfg.ports),
        str(cfg.dims),
        str(cfg.seed),
        cfg.run_label,
    ])
    payload_hash = hashlib.sha256(payload_seed.encode("utf-8")).hexdigest()
    return {
        "band": "s-band",
        "epoch_utc": utc_now(),
        "label": cfg.run_label,
        "subnet": cfg.subnet.with_prefixlen,
        "ports": cfg.ports,
        "dims": cfg.dims,
        "seed": cfg.seed,
        "policy_hash": payload_hash,
        "payload_bytes": len(payload_seed.encode("utf-8")),
    }


def evaluate_broadcast_bootstrap(
    cfg: SimulationConfig,
    sampled_ips: List[ipaddress.IPv6Address],
    psi: List[int],
) -> Dict[str, object]:
    payload = build_broadcast_payload(cfg)
    packet_vector = bipolar_hv(f"broadcast:{payload['policy_hash']}", cfg.dims)

    psi_post = combine_sign_vectors(psi, packet_vector, gain=1)

    base_lifts: List[float] = []
    post_lifts: List[float] = []
    join_rows: List[Dict[str, object]] = []
    joined_count = 0
    rejected_count = 0

    for ip in sampled_ips:
        base_lift = compute_query_lift(psi, ip, cfg.query_port, cfg.dims)
        post_lift = compute_query_lift(psi_post, ip, cfg.query_port, cfg.dims)
        base_lifts.append(base_lift)
        post_lifts.append(post_lift)

        join_score = cosine(packet_vector, endpoint_hv(ip, cfg.query_port, cfg.dims))
        joined = bool(join_score >= cfg.join_threshold)
        if joined:
            joined_count += 1
        else:
            rejected_count += 1

        if cfg.join_report_limit <= 0 or len(join_rows) < cfg.join_report_limit:
            join_rows.append({
                "node": ip.compressed,
                "join_score": round(join_score, 6),
                "decision": "join" if joined else "hold",
                "pre_lift": round(base_lift, 6),
                "post_lift": round(post_lift, 6),
                "lift_delta": round(post_lift - base_lift, 6),
            })

    mean_base = (sum(base_lifts) / len(base_lifts)) if base_lifts else 0.0
    mean_post = (sum(post_lifts) / len(post_lifts)) if post_lifts else 0.0

    return {
        "packet_payload": payload,
        "join_policy": {
            "join_threshold": cfg.join_threshold,
            "query_port": cfg.query_port,
            "report_limit": cfg.join_report_limit,
        },
        "join_summary": {
            "sampled_nodes": len(sampled_ips),
            "joined": joined_count,
            "held": rejected_count,
        },
        "join_decisions": join_rows,
        "query_lift_delta": {
            "mean_pre": round(mean_base, 6),
            "mean_post": round(mean_post, 6),
            "delta": round(mean_post - mean_base, 6),
        },
    }


def prefix_chain(ip: ipaddress.IPv6Address, root_prefix: int, levels: Iterable[int]) -> List[str]:
    chains: List[str] = []
    for p in levels:
        q = max(root_prefix, min(128, int(p)))
        net = ipaddress.IPv6Network(f"{ip}/{q}", strict=False)
        chains.append(net.with_prefixlen)
    return chains


def build_hyperdag(addresses: List[ipaddress.IPv6Address], root_prefix: int) -> Dict[str, object]:
    level_offsets = [0, 16, 32, 48, 64]
    levels = sorted({max(root_prefix, min(128, root_prefix + d)) for d in level_offsets})

    node_counts: Dict[str, int] = {}
    edge_counts: Dict[Tuple[str, str], int] = {}

    for ip in addresses:
        chain = prefix_chain(ip, root_prefix, levels)
        for node in chain:
            node_counts[node] = node_counts.get(node, 0) + 1
        for i in range(len(chain) - 1):
            e = (chain[i], chain[i + 1])
            edge_counts[e] = edge_counts.get(e, 0) + 1

    top_nodes = sorted(node_counts.items(), key=lambda kv: kv[1], reverse=True)[:12]
    top_edges = sorted(edge_counts.items(), key=lambda kv: kv[1], reverse=True)[:12]

    return {
        "levels": levels,
        "node_count": len(node_counts),
        "edge_count": len(edge_counts),
        "top_nodes": [{"node": k, "hits": v} for k, v in top_nodes],
        "top_edges": [{"from": a, "to": b, "hits": c} for (a, b), c in top_edges],
    }


def run_simulation(cfg: SimulationConfig) -> Dict[str, object]:
    sampled_ips = sampled_ipv6_points(cfg.subnet, cfg.max_samples, cfg.seed)
    total_points = len(sampled_ips) * len(cfg.ports)

    wave_sum = [0] * cfg.dims
    for ip in sampled_ips:
        for port in cfg.ports:
            add_into(wave_sum, endpoint_hv(ip, port, cfg.dims))

    psi = sign_normalize(wave_sum)

    query_vec = endpoint_hv(cfg.query_ip, cfg.query_port, cfg.dims)
    similarity = cosine(psi, query_vec)
    random_similarity = cosine(psi, random_probe_hv(cfg.query_ip, cfg.query_port, cfg.dims))

    entropy_bits_per_endpoint = 128 + 16

    dag = build_hyperdag(sampled_ips, cfg.subnet.prefixlen)

    nonzero = sum(1 for x in wave_sum if x != 0)
    density = float(nonzero) / float(cfg.dims)

    out: Dict[str, object] = {
        "generated_utc": utc_now(),
        "label": cfg.run_label,
        "config": {
            "subnet": cfg.subnet.with_prefixlen,
            "ports": cfg.ports,
            "dims": cfg.dims,
            "max_samples": cfg.max_samples,
            "seed": cfg.seed,
            "query": {"ip": cfg.query_ip.compressed, "port": cfg.query_port},
            "broadcast_bootstrap": cfg.broadcast_bootstrap,
        },
        "scale": {
            "sampled_addresses": len(sampled_ips),
            "sampled_endpoint_points": total_points,
            "theoretical_ipv6_port_space_bits": 144,
            "entropy_bits_per_endpoint": entropy_bits_per_endpoint,
            "vector_density": round(density, 6),
        },
        "wave": {
            "vector_type": "bipolar_sign_normalized",
            "dimensions": cfg.dims,
            "query_cosine": round(similarity, 6),
            "random_probe_cosine": round(random_similarity, 6),
            "query_lift": round(similarity - random_similarity, 6),
        },
        "hyperdag": dag,
    }

    if cfg.broadcast_bootstrap:
        out["broadcast_bootstrap"] = evaluate_broadcast_bootstrap(cfg, sampled_ips, psi)

    return out


def as_obj_dict(value: object) -> Dict[str, object]:
    return cast(Dict[str, object], value) if isinstance(value, dict) else {}


def as_obj_list(value: object) -> List[object]:
    return cast(List[object], value) if isinstance(value, list) else []


def render_one_line_summary(out: Dict[str, object], delim: str = "|") -> str:
    d = delim if delim else "|"
    config = as_obj_dict(out.get("config"))
    scale = as_obj_dict(out.get("scale"))
    wave = as_obj_dict(out.get("wave"))
    dag = as_obj_dict(out.get("hyperdag"))
    boot = as_obj_dict(out.get("broadcast_bootstrap"))
    boot_delta = as_obj_dict(boot.get("query_lift_delta"))
    query = as_obj_dict(config.get("query"))
    ports = as_obj_list(config.get("ports"))

    fields = [
        str(out.get("generated_utc") or ""),
        str(out.get("label") or ""),
        str(config.get("subnet") or ""),
        str(len(ports)),
        str(scale.get("sampled_addresses") or 0),
        str(scale.get("sampled_endpoint_points") or 0),
        str(config.get("dims") or 0),
        str(config.get("seed") or 0),
        str(query.get("ip") or ""),
        str(query.get("port") or 0),
        str(wave.get("query_cosine") or 0.0),
        str(wave.get("random_probe_cosine") or 0.0),
        str(wave.get("query_lift") or 0.0),
        str(scale.get("vector_density") or 0.0),
        str(dag.get("node_count") or 0),
        str(dag.get("edge_count") or 0),
        str(boot_delta.get("delta") or 0.0),
    ]
    return d.join(fields)


def append_ledger_row(ledger_path: Path, out: Dict[str, object]) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "generated_utc",
        "label",
        "subnet",
        "ports_count",
        "sampled_addresses",
        "sampled_endpoint_points",
        "dims",
        "seed",
        "query_ip",
        "query_port",
        "query_cosine",
        "random_probe_cosine",
        "query_lift",
        "vector_density",
        "dag_node_count",
        "dag_edge_count",
        "broadcast_delta",
    ]

    config = as_obj_dict(out.get("config"))
    scale = as_obj_dict(out.get("scale"))
    wave = as_obj_dict(out.get("wave"))
    dag = as_obj_dict(out.get("hyperdag"))
    query = as_obj_dict(config.get("query"))
    ports = as_obj_list(config.get("ports"))
    boot = as_obj_dict(out.get("broadcast_bootstrap"))
    boot_delta = as_obj_dict(boot.get("query_lift_delta"))

    row = {
        "generated_utc": str(out.get("generated_utc") or ""),
        "label": str(out.get("label") or ""),
        "subnet": str(config.get("subnet") or ""),
        "ports_count": str(len(ports)),
        "sampled_addresses": str(scale.get("sampled_addresses") or 0),
        "sampled_endpoint_points": str(scale.get("sampled_endpoint_points") or 0),
        "dims": str(config.get("dims") or 0),
        "seed": str(config.get("seed") or 0),
        "query_ip": str(query.get("ip") or ""),
        "query_port": str(query.get("port") or 0),
        "query_cosine": str(wave.get("query_cosine") or 0.0),
        "random_probe_cosine": str(wave.get("random_probe_cosine") or 0.0),
        "query_lift": str(wave.get("query_lift") or 0.0),
        "vector_density": str(scale.get("vector_density") or 0.0),
        "dag_node_count": str(dag.get("node_count") or 0),
        "dag_edge_count": str(dag.get("edge_count") or 0),
        "broadcast_delta": str(boot_delta.get("delta") or 0.0),
    }

    write_header = not ledger_path.exists()
    with ledger_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def build_config_from_args() -> SimulationConfig:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subnet", default=DEFAULT_SUBNET, help="IPv6 subnet to sample, e.g. 2001:db8::/64")
    ap.add_argument("--ports", default=DEFAULT_PORTS, help="Comma-separated ports, e.g. 80,443,8448")
    ap.add_argument("--dims", type=int, default=DEFAULT_DIMS, help="Hypervector dimensions")
    ap.add_argument("--max-samples", type=int, default=DEFAULT_SAMPLES, help="Max sampled IPs from subnet")
    ap.add_argument("--seed", type=int, default=42, help="Deterministic sampling seed")
    ap.add_argument("--query-ip", help="Optional query IPv6 address (defaults to first sampled IP)")
    ap.add_argument("--query-port", type=int, default=443, help="Query port for extraction test")
    ap.add_argument("--one-line", action="store_true", help="Emit a single delimiter-separated summary line for grep/awk batch sweeps")
    ap.add_argument("--one-line-delim", default="|", help="Delimiter for --one-line output (default: |)")
    ap.add_argument("--label", default="run", help="Short label written to one-line output and optional CSV ledger")
    ap.add_argument("--append-ledger", action="store_true", help="Append each run summary to a local CSV ledger")
    ap.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH), help="Path to CSV ledger for --append-ledger")
    ap.add_argument("--broadcast-bootstrap", action="store_true", help="Emit broadcast packet payload, join decisions, and query_lift delta")
    ap.add_argument("--join-threshold", type=float, default=0.0, help="Cosine threshold for broadcast join decisions")
    ap.add_argument("--join-report-limit", type=int, default=64, help="Max join-decision rows to include (<=0 means all)")
    args = ap.parse_args()

    try:
        subnet = ipaddress.IPv6Network(str(args.subnet), strict=False)
    except ValueError as exc:
        raise SystemExit(f"invalid --subnet: {exc}") from exc

    try:
        ports = parse_ports(str(args.ports))
    except ValueError as exc:
        raise SystemExit(f"invalid --ports: {exc}") from exc

    dims = int(args.dims)
    if dims <= 0:
        raise SystemExit("invalid --dims: must be > 0")

    max_samples = int(args.max_samples)
    if max_samples <= 0:
        raise SystemExit("invalid --max-samples: must be > 0")

    if args.query_ip:
        try:
            qip = ipaddress.IPv6Address(str(args.query_ip))
        except ValueError as exc:
            raise SystemExit(f"invalid --query-ip: {exc}") from exc
    else:
        qip = subnet.network_address

    qport = int(args.query_port)
    if qport < 0 or qport > 65535:
        raise SystemExit("invalid --query-port: must be 0..65535")

    if args.join_report_limit < 0:
        raise SystemExit("invalid --join-report-limit: must be >= 0")

    return SimulationConfig(
        subnet=subnet,
        ports=ports,
        dims=dims,
        max_samples=max_samples,
        seed=int(args.seed),
        query_ip=qip,
        query_port=qport,
        one_line=bool(args.one_line),
        one_line_delim=str(args.one_line_delim),
        run_label=str(args.label),
        append_ledger=bool(args.append_ledger),
        ledger_path=Path(str(args.ledger_path)),
        broadcast_bootstrap=bool(args.broadcast_bootstrap),
        join_threshold=float(args.join_threshold),
        join_report_limit=int(args.join_report_limit),
    )


def main() -> None:
    cfg = build_config_from_args()
    out = run_simulation(cfg)
    if cfg.append_ledger:
        append_ledger_row(cfg.ledger_path, out)
    if cfg.one_line:
        print(render_one_line_summary(out, delim=cfg.one_line_delim))
        return
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
