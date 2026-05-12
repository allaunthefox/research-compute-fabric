#!/usr/bin/env python3
"""v4 dictionary-amortization probe for the enwiki9 logogram ladder.

This pass freezes the v2 encoder and v3 slice receipt mode, then changes only
the accounting scope: sum packet deltas over many slices and subtract the fixed
dictionary once.
"""

from __future__ import annotations

import argparse
import bz2
import hashlib
import importlib.util
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
V3_SCRIPT = REPO / "4-Infrastructure" / "shim" / "enwiki9_logogram_receipt_aggregation_probe.py"
V3_RECEIPT = REPO / "shared-data" / "data" / "enwiki9_logogram_receipt_aggregation_probe" / "enwiki9_logogram_receipt_aggregation_probe_receipt.json"
OUT_DIR = REPO / "shared-data" / "data" / "enwiki9_logogram_dictionary_amortization_probe"
RECEIPT = OUT_DIR / "enwiki9_logogram_dictionary_amortization_probe_receipt.json"
SUMMARY = OUT_DIR / "enwiki9_logogram_dictionary_amortization_probe_receipt.md"

DEFAULT_LOCAL_HTML = Path("/home/allaun/Downloads/data/enwik9_data/1234567")
DEFAULT_MEDIAWIKI_FIXTURES = [
    Path("/home/allaun/Research Stack/fawiki.xml.bz2"),
    Path("/home/allaun/Research Stack/jawiki.xml.bz2"),
    Path("/home/allaun/Research Stack/viwiki.xml.bz2"),
]
DEFAULT_SLICE_SIZE = 4096
DEFAULT_BYTE_LIMIT = 131072
GENESIS_EVENT_HASH = "0" * 64


def load_v3_module() -> Any:
    spec = importlib.util.spec_from_file_location("enwiki9_logogram_receipt_aggregation_probe", V3_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load v3 script: {V3_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V3 = load_v3_module()


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_bytes(path: Path, byte_limit: int | None) -> bytes:
    if path.suffix == ".bz2":
        with bz2.open(path, "rb") as handle:
            return handle.read(byte_limit if byte_limit is not None else -1)
    data = path.read_bytes()
    return data[:byte_limit] if byte_limit is not None else data


def dictionary_payload() -> dict[str, list[str]]:
    return V3.dictionary_payload()


def dictionary_bytes_and_hash() -> tuple[int, str]:
    encoded = stable_json(dictionary_payload()).encode("utf-8")
    return len(encoded), sha256_bytes(encoded)


def protocol_hash() -> str:
    return sha256_bytes(
        stable_json(
            {
                "protocol_id": V3.PROTOCOL_ID,
                "encoder": rel(V3.V2_SCRIPT),
                "receipt_mode": V3.RECEIPT_MODE,
                "slice_receipt_root_bytes": V3.SLICE_RECEIPT_ROOT_BYTES,
                "protocol_id_bytes": V3.PROTOCOL_ID_BYTES,
                "gate": "dictionary_amortization_v1",
            }
        ).encode("utf-8")
    )


def event_hash(event: dict[str, Any]) -> str:
    return sha256_bytes(stable_json(event).encode("utf-8"))


def make_event(
    index: int,
    gate: str,
    previous_hash: str,
    input_payload: dict[str, Any],
    output_payload: dict[str, Any],
    delta_bytes: int,
    decision: str,
) -> dict[str, Any]:
    event = {
        "event_index": index,
        "gate": gate,
        "previous_event_hash": previous_hash,
        "input_hash": sha256_bytes(stable_json(input_payload).encode("utf-8")),
        "output_hash": sha256_bytes(stable_json(output_payload).encode("utf-8")),
        "delta_bytes": delta_bytes,
        "decision": decision,
        "clock_participates_in_hash": False,
    }
    event["event_hash"] = event_hash(event)
    return event


def verdict_for(all_exact: bool, delta_core: int, packet_delta: int, global_delta: int, canonical_status: str) -> str:
    if not all_exact:
        return "REJECT"
    if global_delta > 0 and canonical_status == "canonical_enwik9":
        return "LAWFUL_CANDIDATE"
    if global_delta > 0:
        return "ADMIT_FIXTURE"
    if packet_delta > 0:
        return "HOLD_GLOBAL"
    if delta_core > 0:
        return "HOLD_PACKET"
    return "HOLD_DIAGNOSTIC"


def four_gate_events(
    *,
    raw_bytes: int,
    core_bytes: int,
    packet_v3_bytes: int,
    dictionary_bytes: int,
    all_exact_replay: bool,
    dictionary_hash: str,
    protocol_sha: str,
    canonical_status: str,
) -> dict[str, Any]:
    pass_input = {
        "raw_bytes": raw_bytes,
        "core_bytes": core_bytes,
        "dictionary_sha256": dictionary_hash,
        "protocol_sha256": protocol_sha,
    }
    pass_output = {
        "exact_replay": all_exact_replay,
        "replay_law": "Decode(Gamma,Pi,R)==S",
    }
    pass_event = make_event(1, "PASS", GENESIS_EVENT_HASH, pass_input, pass_output, 0, "PASS" if all_exact_replay else "REJECT")

    add_input = pass_output
    add_output = {
        "packet_v3_bytes": packet_v3_bytes,
        "dictionary_bytes": dictionary_bytes,
        "global_cost_bytes": packet_v3_bytes + dictionary_bytes,
    }
    add_event = make_event(2, "ADD", pass_event["event_hash"], add_input, add_output, add_output["global_cost_bytes"], "COUNTED")

    pause_input = {
        "state_root": add_event["event_hash"],
        "event_index_before": add_event["event_index"],
    }
    pause_output = {
        "state_root": add_event["event_hash"],
        "event_index_after": 3,
        "clock_participates_in_hash": False,
    }
    pause_event = make_event(3, "PAUSE", add_event["event_hash"], pause_input, pause_output, 0, "FENCED")

    delta_core = raw_bytes - core_bytes
    delta_packet = raw_bytes - packet_v3_bytes
    delta_global = raw_bytes - (packet_v3_bytes + dictionary_bytes)
    verdict = verdict_for(all_exact_replay, delta_core, delta_packet, delta_global, canonical_status)
    subtract_input = pause_output | add_output | {"raw_bytes": raw_bytes, "core_bytes": core_bytes}
    subtract_output = {
        "delta_core": delta_core,
        "delta_packet": delta_packet,
        "delta_global": delta_global,
        "verdict": verdict,
    }
    subtract_event = make_event(4, "SUBTRACT", pause_event["event_hash"], subtract_input, subtract_output, delta_global, verdict)
    return {
        "protocol": "PASS_ADD_PAUSE_SUBTRACT_v1",
        "timestamp_role": "metadata_only",
        "included_in_receipt_hash": {
            "generated_at_utc": False,
            "event_order": True,
            "event_hashes": True,
        },
        "events": [pass_event, add_event, pause_event, subtract_event],
        "final_event_hash": subtract_event["event_hash"],
        "verdict": verdict,
    }


def classify_slice(data: bytes) -> str:
    xml = data.count(b"<") + data.count(b">")
    template = data.count(b"{{") + data.count(b"}}")
    link = data.count(b"[[") + data.count(b"]]")
    table = data.count(b"{|") + data.count(b"|-") + data.count(b"|}")
    ref = data.lower().count(b"<ref")
    if template >= max(link, xml // 8, 2):
        return "template_heavy"
    if link >= max(template, xml // 8, 2):
        return "link_heavy"
    if table >= 2:
        return "table_heavy"
    if ref >= 2:
        return "ref_heavy"
    if xml >= 24:
        return "xml_heavy"
    if xml >= 8 or template or link:
        return "mixed"
    return "prose_heavy"


def run_source(name: str, path: Path, data: bytes, slice_size: int, dictionary_hash: str, protocol_sha: str, compressed: bool) -> dict[str, Any]:
    source_dir = OUT_DIR / name
    source_dir.mkdir(parents=True, exist_ok=True)
    slices: list[dict[str, Any]] = []
    for index in range(0, len(data), slice_size):
        chunk = data[index : index + slice_size]
        if not chunk:
            continue
        slice_name = f"{name}_{index // slice_size:04d}"
        core, atoms = V3.V2.encode(chunk)
        decoded = V3.V2.decode_core(core)
        exact_replay = decoded == chunk
        core_path = source_dir / f"{slice_name}.wlg2"
        core_path.write_bytes(core)
        packet = len(core) + V3.SLICE_RECEIPT_ROOT_BYTES + V3.PROTOCOL_ID_BYTES
        delta_packet = len(chunk) - packet
        root = V3.slice_receipt_root(chunk, core, exact_replay, dictionary_hash, protocol_sha)
        slice_class = classify_slice(chunk)
        slices.append(
            {
                "name": slice_name,
                "slice_class": slice_class,
                "offset": index,
                "raw_bytes": len(chunk),
                "core_bytes": len(core),
                "packet_v3_bytes": packet,
                "delta_core": len(chunk) - len(core),
                "delta_packet_v3": delta_packet,
                "global_contribution": delta_packet,
                "exact_replay": exact_replay,
                "atom_count": len(atoms),
                "raw_sha256": sha256_bytes(chunk),
                "core": rel(core_path),
                "core_sha256": sha256_bytes(core),
                "slice_receipt_root": root,
                "fixture_status": "ADMIT_FIXTURE" if exact_replay and delta_packet > 0 else "HOLD_DIAGNOSTIC",
            }
        )

    raw = sum(item["raw_bytes"] for item in slices)
    core = sum(item["core_bytes"] for item in slices)
    packet = sum(item["packet_v3_bytes"] for item in slices)
    packet_delta = raw - packet
    dictionary_bytes = V3_dictionary_bytes
    global_delta = packet_delta - dictionary_bytes
    canonical_status = "noncanonical_fixture"
    source_verdict = verdict_for(all(item["exact_replay"] for item in slices), raw - core, packet_delta, global_delta, canonical_status)
    avg_positive_delta = packet_delta / len(slices) if slices else 0.0
    break_even_slices = math.ceil(dictionary_bytes / avg_positive_delta) if avg_positive_delta > 0 else None
    break_even_bytes = break_even_slices * slice_size if break_even_slices is not None else None
    class_totals: dict[str, dict[str, int]] = {}
    for item in slices:
        bucket = class_totals.setdefault(
            item["slice_class"],
            {"slice_count": 0, "raw_bytes": 0, "core_bytes": 0, "packet_v3_bytes": 0, "delta_packet_v3": 0},
        )
        bucket["slice_count"] += 1
        bucket["raw_bytes"] += item["raw_bytes"]
        bucket["core_bytes"] += item["core_bytes"]
        bucket["packet_v3_bytes"] += item["packet_v3_bytes"]
        bucket["delta_packet_v3"] += item["delta_packet_v3"]

    return {
        "name": name,
        "source": str(path),
        "source_sha256": sha256_bytes(path.read_bytes()) if path.exists() and path.stat().st_size <= 50_000_000 else None,
        "source_is_compressed": compressed,
        "read_bytes": len(data),
        "slice_count": len(slices),
        "slice_size": slice_size,
        "all_exact_replay": all(item["exact_replay"] for item in slices),
        "raw_bytes": raw,
        "core_bytes": core,
        "packet_v3_bytes": packet,
        "delta_core": raw - core,
        "packet_delta_total": packet_delta,
        "dictionary_bytes": dictionary_bytes,
        "global_delta": global_delta,
        "break_even_slice_count": break_even_slices,
        "observed_bytes_to_break_even": break_even_bytes,
        "canonical_status": canonical_status,
        "gate_protocol": four_gate_events(
            raw_bytes=raw,
            core_bytes=core,
            packet_v3_bytes=packet,
            dictionary_bytes=dictionary_bytes,
            all_exact_replay=all(item["exact_replay"] for item in slices),
            dictionary_hash=dictionary_hash,
            protocol_sha=protocol_sha,
            canonical_status=canonical_status,
        ),
        "class_totals": class_totals,
        "status_counts": {
            status: sum(1 for item in slices if item["fixture_status"] == status)
            for status in sorted({item["fixture_status"] for item in slices})
        },
        "aggregate_status": source_verdict,
        "slices": slices,
    }


def read_prior_v3() -> dict[str, Any] | None:
    if not V3_RECEIPT.exists():
        return None
    receipt = json.loads(V3_RECEIPT.read_text(encoding="utf-8"))
    return {
        "receipt": rel(V3_RECEIPT),
        "receipt_hash": receipt.get("receipt_hash"),
        "receipt_mode": receipt.get("receipt_mode"),
        "aggregates": receipt.get("aggregates"),
    }


def write_summary(receipt: dict[str, Any]) -> None:
    lines = [
        "# enwiki9 Dictionary Amortization Probe Receipt",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        receipt["claim_boundary"],
        "",
        "## Aggregate",
        "",
        "| Source | Slices | Exact replay | Raw | Core | v3 packet | Packet delta | Dictionary | Global delta | Aggregate status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for source in receipt["sources"]:
        lines.append(
            f"| {source['name']} | {source['slice_count']} | {source['all_exact_replay']} | "
            f"{source['raw_bytes']} | {source['core_bytes']} | {source['packet_v3_bytes']} | "
            f"{source['packet_delta_total']} | {source['dictionary_bytes']} | {source['global_delta']} | "
            f"{source['aggregate_status']} |"
        )
    lines.extend(
        [
            "",
            "## Break Even",
            "",
            "| Source | Packet delta total | Break-even slices | Observed bytes to break even |",
            "|---|---:|---:|---:|",
        ]
    )
    for source in receipt["sources"]:
        lines.append(
            f"| {source['name']} | {source['packet_delta_total']} | "
            f"{source['break_even_slice_count']} | {source['observed_bytes_to_break_even']} |"
        )
    lines.extend(["", "## Class Totals", ""])
    for source in receipt["sources"]:
        lines.append(f"### {source['name']}")
        lines.append("")
        lines.append("| Class | Slices | Raw | Core | v3 packet | Packet delta |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for class_name, totals in sorted(source["class_totals"].items()):
            lines.append(
                f"| {class_name} | {totals['slice_count']} | {totals['raw_bytes']} | "
                f"{totals['core_bytes']} | {totals['packet_v3_bytes']} | {totals['delta_packet_v3']} |"
            )
        lines.append("")
    SUMMARY.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_receipt(paths: list[Path], slice_size: int, byte_limit: int) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dictionary_bytes, dictionary_hash = dictionary_bytes_and_hash()
    protocol_sha = protocol_hash()
    sources: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        name = path.name.replace(".", "_").replace("-", "_")
        data = read_bytes(path, byte_limit)
        sources.append(run_source(name, path, data, slice_size, dictionary_hash, protocol_sha, path.suffix == ".bz2"))
    receipt = {
        "schema": "enwiki9_logogram_dictionary_amortization_probe_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate": "dictionary_amortization_v1",
        "gate_protocol": "PASS_ADD_PAUSE_SUBTRACT_v1",
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "encoder_frozen_from": rel(V3.V2_SCRIPT),
        "receipt_mode_frozen_from": rel(V3_SCRIPT),
        "slice_receipt_root_bytes": V3.SLICE_RECEIPT_ROOT_BYTES,
        "protocol_id_bytes": V3.PROTOCOL_ID_BYTES,
        "dictionary_bytes": dictionary_bytes,
        "dictionary_sha256": dictionary_hash,
        "protocol_sha256": protocol_sha,
        "slice_size": slice_size,
        "byte_limit_per_source": byte_limit,
        "sources": sources,
        "prior_v3": read_prior_v3(),
        "decision": "HOLD",
        "claim_boundary": (
            "Dictionary amortization probe only. It freezes the v2 encoder and "
            "v3 slice-root receipt mode, then changes only accounting scope. "
            "Sources are noncanonical local fixtures, including local MediaWiki "
            "XML dump heads and the existing local HTML sample; no source is the "
            "canonical 1,000,000,000-byte enwik9 corpus. Aggregate ADMIT_FIXTURE "
            "means a noncanonical fixture crossed the global-delta gate, not a "
            "Hutter/LTCB result, corpus admission, or baseline-compressor win."
        ),
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


V3_dictionary_bytes, _V3_dictionary_hash = dictionary_bytes_and_hash()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v4 dictionary-amortization probe.")
    parser.add_argument("--slice-size", type=int, default=DEFAULT_SLICE_SIZE)
    parser.add_argument("--byte-limit", type=int, default=DEFAULT_BYTE_LIMIT)
    parser.add_argument("--source", action="append", type=Path, help="Optional source path. May be repeated.")
    args = parser.parse_args()

    paths = args.source if args.source else [DEFAULT_LOCAL_HTML, *DEFAULT_MEDIAWIKI_FIXTURES]
    receipt = build_receipt(paths, args.slice_size, args.byte_limit)
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(receipt)
    print(
        json.dumps(
            {
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "receipt_hash": receipt["receipt_hash"],
                "sources": [
                    {
                        "name": source["name"],
                        "raw_bytes": source["raw_bytes"],
                        "packet_delta_total": source["packet_delta_total"],
                        "global_delta": source["global_delta"],
                        "aggregate_status": source["aggregate_status"],
                    }
                    for source in receipt["sources"]
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
