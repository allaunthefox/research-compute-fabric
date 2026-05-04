#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Batch-sweep IPv6 subnets through the HDC + HyperDAG simulator.

This helper loops over many child subnets, runs the simulation for each, appends
each result to the shared CSV ledger, and prints one grep-friendly line per run.
"""

from __future__ import annotations

import argparse
import ipaddress
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.simulate_ipv6_hdc_hyperdag import (
    DEFAULT_LEDGER_PATH,
    SimulationConfig,
    append_ledger_row,
    parse_ports,
    render_one_line_summary,
    run_simulation,
)


def utc_compact_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def iter_target_subnets(
    supernet: ipaddress.IPv6Network,
    target_prefix: int,
    start_index: int,
    limit: int,
) -> Iterator[ipaddress.IPv6Network]:
    produced = 0
    for idx, subnet in enumerate(supernet.subnets(new_prefix=target_prefix)):
        if idx < start_index:
            continue
        yield subnet
        produced += 1
        if produced >= limit:
            return


def build_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--supernet", default="2001:db8::/112", help="Parent IPv6 network to partition")
    ap.add_argument("--target-prefix", type=int, default=118, help="Prefix length for child sweep subnets")
    ap.add_argument("--start-index", type=int, default=0, help="Start child subnet offset")
    ap.add_argument("--limit", type=int, default=16, help="Number of child subnets to run")
    ap.add_argument("--ports", default="80,443", help="Comma-separated ports")
    ap.add_argument("--dims", type=int, default=4096, help="Hypervector dimensions")
    ap.add_argument("--max-samples", type=int, default=256, help="Max sampled IPs per subnet")
    ap.add_argument("--seed", type=int, default=42, help="Deterministic seed")
    ap.add_argument("--query-port", type=int, default=443, help="Query port used for lift calculations")
    ap.add_argument("--batch-label", default="sats_batch", help="Prefix for generated run labels")
    ap.add_argument("--one-line-delim", default=";", help="Delimiter for one-line stdout rows")
    ap.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH), help="CSV ledger path")
    ap.add_argument("--broadcast-bootstrap", action="store_true", help="Enable broadcast bootstrap analytics")
    ap.add_argument("--join-threshold", type=float, default=0.0, help="Join threshold for broadcast mode")
    ap.add_argument("--join-report-limit", type=int, default=16, help="Join-decision rows retained in JSON payload")
    return ap.parse_args()


def main() -> None:
    args = build_args()

    try:
        supernet = ipaddress.IPv6Network(str(args.supernet), strict=False)
    except ValueError as exc:
        raise SystemExit(f"invalid --supernet: {exc}") from exc

    target_prefix = int(args.target_prefix)
    if target_prefix < supernet.prefixlen or target_prefix > 128:
        raise SystemExit("invalid --target-prefix: must be between supernet prefix and 128")

    start_index = int(args.start_index)
    if start_index < 0:
        raise SystemExit("invalid --start-index: must be >= 0")

    limit = int(args.limit)
    if limit <= 0:
        raise SystemExit("invalid --limit: must be > 0")

    dims = int(args.dims)
    if dims <= 0:
        raise SystemExit("invalid --dims: must be > 0")

    max_samples = int(args.max_samples)
    if max_samples <= 0:
        raise SystemExit("invalid --max-samples: must be > 0")

    seed = int(args.seed)

    query_port = int(args.query_port)
    if query_port < 0 or query_port > 65535:
        raise SystemExit("invalid --query-port: must be 0..65535")

    if int(args.join_report_limit) < 0:
        raise SystemExit("invalid --join-report-limit: must be >= 0")

    try:
        ports: List[int] = parse_ports(str(args.ports))
    except ValueError as exc:
        raise SystemExit(f"invalid --ports: {exc}") from exc

    batch_stamp = utc_compact_now()
    ledger_path = Path(str(args.ledger_path))

    ran = 0
    for i, subnet in enumerate(iter_target_subnets(supernet, target_prefix, start_index, limit)):
        label = f"{args.batch_label}_{batch_stamp}_{i:04d}"
        cfg = SimulationConfig(
            subnet=subnet,
            ports=ports,
            dims=dims,
            max_samples=max_samples,
            seed=seed,
            query_ip=subnet.network_address,
            query_port=query_port,
            one_line=True,
            one_line_delim=str(args.one_line_delim),
            run_label=label,
            append_ledger=True,
            ledger_path=ledger_path,
            broadcast_bootstrap=bool(args.broadcast_bootstrap),
            join_threshold=float(args.join_threshold),
            join_report_limit=int(args.join_report_limit),
        )

        out = run_simulation(cfg)
        append_ledger_row(ledger_path, out)
        print(render_one_line_summary(out, delim=cfg.one_line_delim))
        ran += 1

    if ran == 0:
        raise SystemExit("no sweep runs executed; adjust --start-index/--limit")


if __name__ == "__main__":
    main()
