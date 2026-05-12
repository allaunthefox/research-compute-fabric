#!/usr/bin/env python3
"""v3 slice-receipt aggregation probe for enwiki9 logogram targeting.

This pass keeps the v2 fixed XML/MediaWiki dictionary encoder unchanged and
tests the next accounting hypothesis: replace per-atom receipt stubs with one
slice-level replay receipt root.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
V2_SCRIPT = REPO / "4-Infrastructure" / "shim" / "enwiki9_logogram_xml_dict_probe.py"
V2_RECEIPT = REPO / "shared-data" / "data" / "enwiki9_logogram_xml_dict_probe" / "enwiki9_logogram_xml_dict_probe_receipt.json"
DEFAULT_BUNDLE_DEMO = REPO / "shared-data" / "data" / "enwiki9_logogram_targeter" / "demo"
DEFAULT_LOCAL_SAMPLE = Path("/home/allaun/Downloads/data/enwik9_data/1234567")
OUT_DIR = REPO / "shared-data" / "data" / "enwiki9_logogram_receipt_aggregation_probe"
RECEIPT = OUT_DIR / "enwiki9_logogram_receipt_aggregation_probe_receipt.json"
SUMMARY = OUT_DIR / "enwiki9_logogram_receipt_aggregation_probe_receipt.md"

SLICE_RECEIPT_ROOT_BYTES = 32
PROTOCOL_ID_BYTES = 4
RECEIPT_MODE = "slice_root_v1"
PROTOCOL_ID = "WLG2"


def load_v2_module() -> Any:
    spec = importlib.util.spec_from_file_location("enwiki9_logogram_xml_dict_probe", V2_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load v2 script: {V2_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V2 = load_v2_module()


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_prior_v2() -> dict[str, Any] | None:
    if not V2_RECEIPT.exists():
        return None
    receipt = json.loads(V2_RECEIPT.read_text(encoding="utf-8"))
    out: dict[str, Any] = {
        "receipt": rel(V2_RECEIPT),
        "receipt_hash": receipt.get("receipt_hash"),
        "dictionary_bytes": receipt.get("dictionary_bytes"),
        "aggregates": {},
    }
    for name in ["demo", "local_sample"]:
        agg = receipt.get("aggregates", {}).get(name)
        if agg:
            out["aggregates"][name] = {
                "raw_bytes": agg.get("raw_bytes"),
                "core_bytes": agg.get("core_bytes"),
                "packet_estimate_bytes": agg.get("packet_estimate_bytes"),
                "delta_core": agg.get("delta_core"),
                "delta_packet": agg.get("delta_packet"),
                "delta_global": agg.get("delta_global"),
                "all_exact_replay": agg.get("all_exact_replay"),
            }
    return out


def demo_slices(demo_dir: Path) -> list[tuple[str, str, bytes]]:
    out: list[tuple[str, str, bytes]] = []
    if demo_dir.exists():
        for path in sorted(demo_dir.glob("*.raw")):
            out.append((path.stem, rel(path), path.read_bytes()))
    return out


def sample_slices(sample: Path, slice_size: int, max_slices: int) -> list[tuple[str, str, bytes]]:
    if not sample.exists():
        return []
    data = sample.read_bytes()
    return [
        (f"local_sample_{index:04d}", str(sample), data[index * slice_size : (index + 1) * slice_size])
        for index in range(min(max_slices, (len(data) + slice_size - 1) // slice_size))
        if data[index * slice_size : (index + 1) * slice_size]
    ]


def slice_receipt_root(raw: bytes, core: bytes, exact_replay: bool, dictionary_hash: str, protocol_hash: str) -> str:
    payload = {
        "raw_sha256": sha256_bytes(raw),
        "core_sha256": sha256_bytes(core),
        "dictionary_sha256": dictionary_hash,
        "protocol_sha256": protocol_hash,
        "exact_replay": exact_replay,
        "receipt_mode": RECEIPT_MODE,
    }
    return sha256_bytes(stable_json(payload).encode("utf-8"))


def run_slice(name: str, source_label: str, data: bytes, dictionary_hash: str, protocol_hash: str) -> dict[str, Any]:
    core, atoms = V2.encode(data)
    decoded = V2.decode_core(core)
    exact_replay = decoded == data
    core_path = OUT_DIR / f"{name}.wlg2"
    core_path.write_bytes(core)
    packet_v3 = len(core) + SLICE_RECEIPT_ROOT_BYTES + PROTOCOL_ID_BYTES
    root = slice_receipt_root(data, core, exact_replay, dictionary_hash, protocol_hash)
    atom_counts = {kind: sum(1 for atom in atoms if atom.kind == kind) for kind in sorted({atom.kind for atom in atoms})}
    return {
        "name": name,
        "source": source_label,
        "raw_bytes": len(data),
        "core_bytes": len(core),
        "packet_v3_bytes": packet_v3,
        "delta_core": len(data) - len(core),
        "delta_packet_v3": len(data) - packet_v3,
        "exact_replay": exact_replay,
        "atom_count": len(atoms),
        "atom_counts": atom_counts,
        "raw_sha256": sha256_bytes(data),
        "core": rel(core_path),
        "core_sha256": sha256_bytes(core),
        "slice_receipt_root": root,
        "slice_receipt_root_bytes": SLICE_RECEIPT_ROOT_BYTES,
        "protocol_id_bytes": PROTOCOL_ID_BYTES,
        "fixture_status": "ADMIT_FIXTURE" if exact_replay and len(data) > packet_v3 else "HOLD_DIAGNOSTIC",
    }


def aggregate(results: list[dict[str, Any]], dictionary_bytes: int) -> dict[str, Any]:
    raw = sum(item["raw_bytes"] for item in results)
    core = sum(item["core_bytes"] for item in results)
    packet = sum(item["packet_v3_bytes"] for item in results)
    return {
        "slice_count": len(results),
        "all_exact_replay": all(item["exact_replay"] for item in results),
        "raw_bytes": raw,
        "core_bytes": core,
        "packet_v3_bytes": packet,
        "delta_core": raw - core,
        "delta_packet_v3": raw - packet,
        "dictionary_bytes": dictionary_bytes,
        "delta_global_v3": raw - (packet + dictionary_bytes),
        "slice_receipt_root_bytes_total": SLICE_RECEIPT_ROOT_BYTES * len(results),
        "protocol_id_bytes_total": PROTOCOL_ID_BYTES * len(results),
        "status_counts": {
            status: sum(1 for item in results if item["fixture_status"] == status)
            for status in sorted({item["fixture_status"] for item in results})
        },
    }


def dictionary_payload() -> dict[str, list[str]]:
    return {
        "fixed": [tag.hex() for tag in V2.FIXED_TAGS],
        "pair": [tag.hex() for tag in V2.PAIR_TAGS],
        "attr": [tag.hex() for tag in V2.ATTR_TAGS],
        "motif": [tag.hex() for tag in V2.MOTIFS],
    }


def write_summary(receipt: dict[str, Any]) -> None:
    lines = [
        "# enwiki9 Receipt Aggregation Probe Receipt",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        receipt["claim_boundary"],
        "",
        "## Aggregate",
        "",
        "| Run | Slices | Exact replay | Raw | Core | v3 packet | Delta core | Delta packet v3 | Delta global v3 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ["demo", "local_sample"]:
        agg = receipt["aggregates"].get(name)
        if not agg:
            continue
        lines.append(
            f"| {name} | {agg['slice_count']} | {agg['all_exact_replay']} | "
            f"{agg['raw_bytes']} | {agg['core_bytes']} | {agg['packet_v3_bytes']} | "
            f"{agg['delta_core']} | {agg['delta_packet_v3']} | {agg['delta_global_v3']} |"
        )
    lines.extend(
        [
            "",
            "## v2 Comparison",
            "",
            "| Run | v2 packet delta | v3 packet delta | v2 global delta | v3 global delta |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    prior = receipt.get("prior_v2")
    if prior:
        for name in ["demo", "local_sample"]:
            v2 = prior.get("aggregates", {}).get(name)
            v3 = receipt["aggregates"].get(name)
            if not v2 or not v3:
                continue
            lines.append(
                f"| {name} | {v2['delta_packet']} | {v3['delta_packet_v3']} | "
                f"{v2['delta_global']} | {v3['delta_global_v3']} |"
            )
    lines.extend(
        [
            "",
            "## Receipt Mode",
            "",
            f"- Receipt mode: `{RECEIPT_MODE}`",
            f"- Slice receipt root bytes: `{SLICE_RECEIPT_ROOT_BYTES}`",
            f"- Protocol ID bytes per slice: `{PROTOCOL_ID_BYTES}`",
            f"- Dictionary bytes still counted globally: `{receipt['dictionary_bytes']}`",
        ]
    )
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_receipt(demo_dir: Path, sample: Path, slice_size: int, max_sample_slices: int) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dictionary_json = stable_json(dictionary_payload()).encode("utf-8")
    dictionary_bytes = len(dictionary_json)
    dictionary_hash = sha256_bytes(dictionary_json)
    protocol_hash = sha256_bytes(
        stable_json(
            {
                "protocol_id": PROTOCOL_ID,
                "encoder": rel(V2_SCRIPT),
                "receipt_mode": RECEIPT_MODE,
                "slice_receipt_root_bytes": SLICE_RECEIPT_ROOT_BYTES,
                "protocol_id_bytes": PROTOCOL_ID_BYTES,
            }
        ).encode("utf-8")
    )

    demo_results = [
        run_slice(name, source, data, dictionary_hash, protocol_hash)
        for name, source, data in demo_slices(demo_dir)
    ]
    sample_results = [
        run_slice(name, source, data, dictionary_hash, protocol_hash)
        for name, source, data in sample_slices(sample, slice_size, max_sample_slices)
    ]
    receipt = {
        "schema": "enwiki9_logogram_receipt_aggregation_probe_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "receipt_mode": RECEIPT_MODE,
        "slice_receipt_root_bytes": SLICE_RECEIPT_ROOT_BYTES,
        "protocol_id": PROTOCOL_ID,
        "protocol_id_bytes": PROTOCOL_ID_BYTES,
        "protocol_sha256": protocol_hash,
        "dictionary_bytes": dictionary_bytes,
        "dictionary_sha256": dictionary_hash,
        "dictionary_source": rel(V2_SCRIPT),
        "inputs": {
            "demo_dir": rel(demo_dir),
            "local_sample": str(sample),
            "local_sample_bytes": sample.stat().st_size if sample.exists() else None,
            "local_sample_sha256": sha256_file(sample) if sample.exists() else None,
            "local_sample_claim": "noncanonical local HTML sample; not enwik9",
        },
        "runs": {
            "demo": demo_results,
            "local_sample": sample_results,
        },
        "aggregates": {
            "demo": aggregate(demo_results, dictionary_bytes),
            "local_sample": aggregate(sample_results, dictionary_bytes),
        },
        "prior_v2": read_prior_v2(),
        "decision": "HOLD",
        "claim_boundary": (
            "Receipt aggregation probe only. It reuses the v2 fixed XML/MediaWiki "
            "dictionary encoder and replaces per-atom receipt stubs with one "
            "slice-level replay receipt root. Demo slices come from the uploaded "
            "targeter bundle; the local sample is a 20,532-byte noncanonical HTML "
            "file, not the 1,000,000,000-byte enwik9 corpus. Positive packet "
            "deltas are fixture evidence only; global admission remains HOLD "
            "until dictionary/protocol bytes are amortized over a canonical corpus "
            "run and baseline comparisons are counted."
        ),
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v3 slice receipt aggregation probe.")
    parser.add_argument("--demo-dir", type=Path, default=DEFAULT_BUNDLE_DEMO)
    parser.add_argument("--sample", type=Path, default=DEFAULT_LOCAL_SAMPLE)
    parser.add_argument("--slice-size", type=int, default=4096)
    parser.add_argument("--max-sample-slices", type=int, default=4)
    args = parser.parse_args()

    receipt = build_receipt(args.demo_dir, args.sample, args.slice_size, args.max_sample_slices)
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(receipt)
    print(
        json.dumps(
            {
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "receipt_hash": receipt["receipt_hash"],
                "demo": receipt["aggregates"]["demo"],
                "local_sample": receipt["aggregates"]["local_sample"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
