#!/usr/bin/env python3
"""Build a ranked replay-fixture queue from metaprobe receipts.

The queue is an execution planner, not a benchmark result. It ranks route
surfaces by local readiness, fixture size, verifier availability, and whether a
negative-control lane is already obvious.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DEFAULT_METAPROBE = (
    REPO
    / "4-Infrastructure"
    / "shim"
    / "parallel_metaprobe_runs"
    / "20260509T053755Z"
    / "parallel_metaprobe_launcher_receipt.json"
)
ROUTE_PACKETS = REPO / "shared-data" / "data" / "nspace_bulk_routes" / "nspace_bulk_dataset_route_packets.jsonl"
OUT_DIR = REPO / "shared-data" / "data" / "replay_fixture_queue"
QUEUE_JSON = OUT_DIR / "replay_fixture_queue_receipt.json"
QUEUE_MD = OUT_DIR / "replay_fixture_queue.md"


QUEUE_SHAPES = {
    "SRBench / ParFam": {
        "rank": 1,
        "readiness": 96,
        "first_fixture": "symbolic_law_replay_harness: feynman_newton_gravity",
        "negative_control": "mutated denominator exponent",
        "verifier": "deterministic numeric replay plus residual accounting",
        "reason": "smallest exact-law surface with obvious negative controls",
    },
    "DLMF / Feynman Symbolic Regression": {
        "rank": 2,
        "readiness": 94,
        "first_fixture": "symbolic_law_replay_harness: feynman_kinetic_energy",
        "negative_control": "operator or coefficient mutation",
        "verifier": "deterministic numeric replay plus formula/source hash",
        "reason": "equation/glyph prior is directly aligned with one-symbol law replay",
    },
    "PDEBench": {
        "rank": 3,
        "readiness": 78,
        "first_fixture": "pde_tiny_replay_harness: advection_periodic_exact_shift",
        "negative_control": "wrong boundary/viscosity metadata",
        "verifier": "deterministic local advection replay plus residual drift receipt",
        "reason": "canonical PDE families are clean and now have a no-download local micro-fixture",
    },
    "The Well": {
        "rank": 4,
        "readiness": 72,
        "first_fixture": "the_well_tiny_schema_probe: scalar/vector field schema",
        "negative_control": "field-rank or coordinate-system mismatch",
        "verifier": "field rank, axis, boundary, dtype, and residual schema receipt",
        "reason": "large and well-structured, now guarded by a metadata-only schema probe before data slices",
    },
    "LeanDojo / mathlib": {
        "rank": 5,
        "readiness": 70,
        "first_fixture": "lean_proof_replay_receipt: ExtensionScaffold.Compression.ProofReplay",
        "negative_control": "statement without local lake replay",
        "verifier": "targeted lake build plus #eval witness readback",
        "reason": "best proof boundary, now guarded by a tiny local Lean admission theorem fixture",
    },
    "MeshGraphNets": {
        "rank": 6,
        "readiness": 64,
        "first_fixture": "meshgraphnets_tiny_topology_probe: canonical mesh topology",
        "negative_control": "mesh topology/split mismatch",
        "verifier": "canonical edge, face, boundary, degree, and message-pass receipt",
        "reason": "important for goxel topology and now guarded by a no-download topology probe",
    },
    "RealPDEBench": {
        "rank": 7,
        "readiness": 58,
        "first_fixture": "one paired real/sim trajectory index",
        "negative_control": "sim-to-real modality mismatch",
        "verifier": "scenario, modality, split, and noncommercial license receipts",
        "reason": "valuable residual calibration, but license and data size raise friction",
    },
    "NuminaMath": {
        "rank": 8,
        "readiness": 52,
        "first_fixture": "proposal-only reasoning curriculum sample",
        "negative_control": "answer without independent verification",
        "verifier": "external answer check or local formal/numeric verifier",
        "reason": "useful for proposal generation, not enough for truth promotion",
    },
}


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_packets(path: Path) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            packets.append(json.loads(line))
    return packets


def build_queue(metaprobe_path: Path) -> dict[str, Any]:
    metaprobe = read_json(metaprobe_path)
    packets = read_packets(ROUTE_PACKETS)
    passed_lanes = {lane["name"] for lane in metaprobe.get("lanes", []) if lane.get("status") == "PASS"}

    queue = []
    for packet in packets:
        shape = QUEUE_SHAPES.get(packet["dataset"])
        if shape is None:
            continue
        queue.append(
            {
                "rank": shape["rank"],
                "readiness": shape["readiness"],
                "dataset": packet["dataset"],
                "domain": packet["domain"],
                "packet_id": packet["packet_id"],
                "packet_hash": packet["packet_hash"],
                "first_fixture": shape["first_fixture"],
                "negative_control": shape["negative_control"],
                "verifier": shape["verifier"],
                "reason": shape["reason"],
                "source_urls": packet["source_urls"],
                "ingest_boundary": packet["ingest_boundary"],
                "decision": "HOLD",
            }
        )
    queue.sort(key=lambda item: (item["rank"], -item["readiness"]))

    receipt = {
        "schema": "replay_fixture_queue_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "metaprobe_receipt": rel(metaprobe_path),
        "metaprobe_receipt_hash": metaprobe.get("receipt_hash"),
        "route_packets": rel(ROUTE_PACKETS),
        "route_packet_count": len(packets),
        "passed_metaprobe_lanes": sorted(passed_lanes),
        "queue_count": len(queue),
        "queue": queue,
        "next_action": "run lean_proof_replay_receipt.py before RealPDEBench calibration",
        "claim_boundary": (
            "Replay queue only. Ranking reflects local fixture readiness and receipt surface, "
            "not benchmark performance, proof status, or compression gain."
        ),
        "decision": "HOLD",
    }
    receipt["receipt_hash"] = sha256_text(stable_json({k: v for k, v in receipt.items() if k != "receipt_hash"}))
    return receipt


def write_markdown(receipt: dict[str, Any], path: Path) -> None:
    lines = [
        "# Replay Fixture Queue",
        "",
        f"Schema: `{receipt['schema']}`  ",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        receipt["claim_boundary"],
        "",
        "## Queue",
        "",
        "| Rank | Dataset | Readiness | First fixture | Negative control |",
        "|---:|---|---:|---|---|",
    ]
    for item in receipt["queue"]:
        lines.append(
            f"| {item['rank']} | {item['dataset']} | {item['readiness']} | "
            f"{item['first_fixture']} | {item['negative_control']} |"
        )
    lines.extend(
        [
            "",
            "## Next Action",
            "",
            f"`{receipt['next_action']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    receipt = build_queue(DEFAULT_METAPROBE)
    QUEUE_JSON.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(receipt, QUEUE_MD)
    print(json.dumps({"receipt": rel(QUEUE_JSON), "summary": rel(QUEUE_MD), "receipt_hash": receipt["receipt_hash"], "queue_count": receipt["queue_count"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
