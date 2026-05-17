#!/usr/bin/env python3
"""v5 canonical enwik9 slice and baseline probe.

This pass freezes the v4 codec/accounting path and adds only two outer gates:
PROVENANCE and BASELINE. It does not change the encoder. Non-1GB inputs are
automatically treated as fixtures, not canonical enwik9 evidence.
"""

from __future__ import annotations

import argparse
import bz2
import hashlib
import importlib.util
import json
import lzma
import shutil
import subprocess
import sys
import tempfile
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
V4_SCRIPT = REPO / "4-Infrastructure" / "shim" / "enwiki9_logogram_dictionary_amortization_probe.py"
V4_RECEIPT = REPO / "shared-data" / "data" / "enwiki9_logogram_dictionary_amortization_probe" / "enwiki9_logogram_dictionary_amortization_probe_receipt.json"
DEFAULT_INPUT = Path("/home/allaun/Downloads/data/enwik9_data/1234567")
OUT_DIR = REPO / "shared-data" / "data" / "enwiki9_logogram_canonical_baseline_probe"
RECEIPT = OUT_DIR / "enwiki9_logogram_canonical_baseline_probe_receipt.json"
SUMMARY = OUT_DIR / "enwiki9_logogram_canonical_baseline_probe_receipt.md"

CANONICAL_ENWIK9_SIZE = 1_000_000_000
DEFAULT_SLICE_SIZE = 65536
DEFAULT_SCAN_STRIDE = 1_048_576
GENESIS_EVENT_HASH = "0" * 64
FIXED_OFFSETS = [0, 1_000_000, 10_000_000, 100_000_000, 500_000_000, 900_000_000]
TARGET_CLASSES = [
    "xml_head",
    "link_heavy",
    "template_heavy",
    "ref_heavy",
    "category_file_heavy",
    "prose_heavy",
    "mixed_high_entropy",
]


def load_v4_module() -> Any:
    spec = importlib.util.spec_from_file_location("enwiki9_logogram_dictionary_amortization_probe", V4_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load v4 script: {V4_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V4 = load_v4_module()


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_prior_v4() -> dict[str, Any] | None:
    if not V4_RECEIPT.exists():
        return None
    receipt = json.loads(V4_RECEIPT.read_text(encoding="utf-8"))
    return {
        "receipt": rel(V4_RECEIPT),
        "receipt_hash": receipt.get("receipt_hash"),
        "gate_protocol": receipt.get("gate_protocol"),
        "encoder_frozen_from": receipt.get("encoder_frozen_from"),
        "receipt_mode_frozen_from": receipt.get("receipt_mode_frozen_from"),
        "dictionary_bytes": receipt.get("dictionary_bytes"),
    }


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


def classify_slice(data: bytes, offset: int) -> str:
    if offset == 0 and data.lstrip().startswith(b"<"):
        return "xml_head"
    lower = data.lower()
    template = data.count(b"{{") + data.count(b"}}")
    link = data.count(b"[[") + data.count(b"]]")
    category_file = lower.count(b"[[category:") + lower.count(b"[[file:") + lower.count(b"[[image:")
    ref = lower.count(b"<ref")
    table = data.count(b"{|") + data.count(b"|-") + data.count(b"|}")
    xml = data.count(b"<") + data.count(b">")
    entropyish = len(set(data)) + data.count(b"|") + data.count(b"{") + data.count(b"[")
    if category_file >= 2:
        return "category_file_heavy"
    if template >= max(link, 2):
        return "template_heavy"
    if ref >= 2:
        return "ref_heavy"
    if link >= 2:
        return "link_heavy"
    if table >= 2 or (xml >= 12 and entropyish >= 90):
        return "mixed_high_entropy"
    if xml >= 24:
        return "xml_head"
    return "prose_heavy"


def read_slice(path: Path, offset: int, length: int) -> bytes:
    with path.open("rb") as handle:
        handle.seek(offset)
        return handle.read(length)


def scan_for_class(path: Path, size: int, wanted: str, slice_size: int, stride: int) -> tuple[int, bytes, str] | None:
    best: tuple[int, bytes, str] | None = None
    best_score = -1
    with path.open("rb") as handle:
        for offset in range(0, max(size - 1, 0), stride):
            handle.seek(offset)
            data = handle.read(slice_size)
            if not data:
                break
            cls = classify_slice(data, offset)
            if cls == wanted:
                return offset, data, cls
            score = class_score(data, wanted, offset)
            if score > best_score:
                best_score = score
                best = (offset, data, cls)
    return best


def class_score(data: bytes, wanted: str, offset: int) -> int:
    lower = data.lower()
    if wanted == "xml_head":
        return (1000 if offset == 0 else 0) + data.count(b"<") + data.count(b">")
    if wanted == "link_heavy":
        return data.count(b"[[") + data.count(b"]]")
    if wanted == "template_heavy":
        return data.count(b"{{") + data.count(b"}}")
    if wanted == "ref_heavy":
        return lower.count(b"<ref")
    if wanted == "category_file_heavy":
        return lower.count(b"[[category:") + lower.count(b"[[file:") + lower.count(b"[[image:")
    if wanted == "mixed_high_entropy":
        return len(set(data)) + data.count(b"|") + data.count(b"{") + data.count(b"[") + data.count(b"<")
    return max(1, data.count(b" ")) - data.count(b"<") - data.count(b"{") - data.count(b"[")


def collect_slices(path: Path, size: int, slice_size: int, scan_stride: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen_offsets: set[int] = set()
    for offset in FIXED_OFFSETS:
        if offset >= size:
            continue
        data = read_slice(path, offset, slice_size)
        if not data:
            continue
        seen_offsets.add(offset)
        selected.append(
            {
                "name": f"offset_{offset}",
                "offset": offset,
                "length": len(data),
                "selection": "fixed_offset",
                "requested_class": None,
                "slice_class": classify_slice(data, offset),
                "data": data,
            }
        )
    for wanted in TARGET_CLASSES:
        found = scan_for_class(path, size, wanted, slice_size, scan_stride)
        if found is None:
            continue
        offset, data, cls = found
        if offset in seen_offsets:
            continue
        seen_offsets.add(offset)
        suffix = "exact" if cls == wanted else "best_available"
        name = f"{wanted}_{offset}_{suffix}"
        selected.append(
            {
                "name": name,
                "offset": offset,
                "length": len(data),
                "selection": "content_selected",
                "requested_class": wanted,
                "slice_class": cls,
                "content_match": cls == wanted,
                "data": data,
            }
        )
    return selected


def zstd_size(data: bytes) -> int | None:
    if shutil.which("zstd") is None:
        return None
    with tempfile.NamedTemporaryFile(suffix=".raw") as src, tempfile.NamedTemporaryFile(suffix=".zst") as dst:
        src.write(data)
        src.flush()
        subprocess.run(["zstd", "-19", "-q", "-f", src.name, "-o", dst.name], check=True)
        return Path(dst.name).stat().st_size


def baselines(data: bytes) -> dict[str, int | None]:
    return {
        "zlib_9": len(zlib.compress(data, 9)),
        "bz2_9": len(bz2.compress(data, 9)),
        "lzma_9": len(lzma.compress(data, preset=9)),
        "zstd_19_if_available": zstd_size(data),
    }


def run_slice(item: dict[str, Any], source_dir: Path, dictionary_hash: str, protocol_sha: str) -> dict[str, Any]:
    data = item.pop("data")
    core, atoms = V4.V3.V2.encode(data)
    decoded = V4.V3.V2.decode_core(core)
    exact_replay = decoded == data
    safe_name = item["name"].replace("/", "_")
    core_path = source_dir / f"{safe_name}.wlg2"
    core_path.write_bytes(core)
    packet = len(core) + V4.V3.SLICE_RECEIPT_ROOT_BYTES + V4.V3.PROTOCOL_ID_BYTES
    base = baselines(data)
    baseline_values = {k: v for k, v in base.items() if v is not None}
    best_name = min(baseline_values, key=lambda key: baseline_values[key]) if baseline_values else None
    best_size = baseline_values[best_name] if best_name else None
    return {
        **item,
        "raw_bytes": len(data),
        "core_bytes": len(core),
        "packet_bytes": packet,
        "delta_core": len(data) - len(core),
        "delta_packet": len(data) - packet,
        "exact_replay": exact_replay,
        "atom_count": len(atoms),
        "atom_counts": {kind: sum(1 for atom in atoms if atom.kind == kind) for kind in sorted({atom.kind for atom in atoms})},
        "raw_sha256": sha256_bytes(data),
        "core": rel(core_path),
        "core_sha256": sha256_bytes(core),
        "slice_receipt_root": V4.V3.slice_receipt_root(data, core, exact_replay, dictionary_hash, protocol_sha),
        "baseline": {
            **base,
            "best_baseline": best_name,
            "best_baseline_bytes": best_size,
            "delta_vs_best_baseline_packet": (best_size - packet) if best_size is not None else None,
        },
    }


def provenance_status(path: Path, size: int, claim: str) -> tuple[str, str]:
    if claim == "auto":
        claim = "canonical_enwik9" if size == CANONICAL_ENWIK9_SIZE else "fixture"
    if claim == "canonical_enwik9" and size != CANONICAL_ENWIK9_SIZE:
        return claim, "HOLD_PROVENANCE"
    if claim == "canonical_enwik9":
        return claim, "PASS"
    if claim in {"fixture", "unknown"}:
        return claim, "FIXTURE"
    return "unknown", "HOLD_PROVENANCE"


def aggregate(slices: list[dict[str, Any]], dictionary_bytes: int, canonical_claim: str, provenance_decision: str) -> dict[str, Any]:
    raw = sum(item["raw_bytes"] for item in slices)
    core = sum(item["core_bytes"] for item in slices)
    packet = sum(item["packet_bytes"] for item in slices)
    global_cost = packet + dictionary_bytes
    baseline_totals: dict[str, int | None] = {
        "zlib_9": sum_int_or_none(item["baseline"]["zlib_9"] for item in slices),
        "bz2_9": sum_int_or_none(item["baseline"]["bz2_9"] for item in slices),
        "lzma_9": sum_int_or_none(item["baseline"]["lzma_9"] for item in slices),
        "zstd_19_if_available": sum_int_or_none(item["baseline"]["zstd_19_if_available"] for item in slices),
    }
    numeric = {k: v for k, v in baseline_totals.items() if v is not None}
    best_name = min(numeric, key=lambda key: numeric[key]) if numeric else None
    best_size = numeric[best_name] if best_name else None
    decision = decide(
        all_exact=all(item["exact_replay"] for item in slices),
        provenance_decision=provenance_decision,
        canonical_claim=canonical_claim,
        delta_packet=raw - packet,
        delta_global=raw - global_cost,
        delta_vs_best=(best_size - global_cost) if best_size is not None else None,
    )
    return {
        "slice_count": len(slices),
        "all_exact_replay": all(item["exact_replay"] for item in slices),
        "raw_bytes": raw,
        "core_bytes": core,
        "packet_bytes": packet,
        "dictionary_bytes": dictionary_bytes,
        "global_cost_bytes": global_cost,
        "delta_core": raw - core,
        "delta_packet": raw - packet,
        "delta_global": raw - global_cost,
        "baseline": {
            **baseline_totals,
            "best_baseline": best_name,
            "best_baseline_bytes": best_size,
            "delta_vs_best_baseline": (best_size - global_cost) if best_size is not None else None,
        },
        "decision": decision,
    }


def sum_int_or_none(values: Any) -> int | None:
    total = 0
    for value in values:
        if value is None:
            return None
        total += int(value)
    return total


def decide(
    *,
    all_exact: bool,
    provenance_decision: str,
    canonical_claim: str,
    delta_packet: int,
    delta_global: int,
    delta_vs_best: int | None,
) -> str:
    if not all_exact:
        return "REJECT_REPLAY"
    if provenance_decision == "HOLD_PROVENANCE":
        return "HOLD_PROVENANCE"
    if delta_packet <= 0:
        return "HOLD_PACKET"
    if delta_global <= 0:
        return "HOLD_GLOBAL"
    if canonical_claim != "canonical_enwik9":
        return "ADMIT_FIXTURE"
    if delta_vs_best is not None and delta_vs_best > 0:
        return "BASELINE_CANDIDATE"
    return "ADMIT_CANONICAL_SLICE"


def build_gate_protocol(
    *,
    input_info: dict[str, Any],
    aggregates: dict[str, Any],
    dictionary_hash: str,
    protocol_sha: str,
) -> dict[str, Any]:
    provenance_output = {
        "canonical_claim": input_info["canonical_claim"],
        "provenance_decision": input_info["provenance_decision"],
        "size_requirement": CANONICAL_ENWIK9_SIZE,
    }
    provenance_event = make_event(1, "PROVENANCE", GENESIS_EVENT_HASH, input_info, provenance_output, 0, input_info["provenance_decision"])
    pass_output = {
        "exact_replay": aggregates["all_exact_replay"],
        "slice_count": aggregates["slice_count"],
        "replay_law": "Decode(Gamma,Pi,R)==S_slice",
    }
    pass_event = make_event(2, "PASS", provenance_event["event_hash"], provenance_output, pass_output, 0, "PASS" if aggregates["all_exact_replay"] else "REJECT_REPLAY")
    add_output = {
        "packet_bytes": aggregates["packet_bytes"],
        "dictionary_bytes": aggregates["dictionary_bytes"],
        "global_cost_bytes": aggregates["global_cost_bytes"],
        "dictionary_sha256": dictionary_hash,
        "protocol_sha256": protocol_sha,
    }
    add_event = make_event(3, "ADD", pass_event["event_hash"], pass_output, add_output, aggregates["global_cost_bytes"], "COUNTED")
    pause_output = {
        "state_root": add_event["event_hash"],
        "event_index_after": 4,
        "clock_participates_in_hash": False,
    }
    pause_event = make_event(4, "PAUSE", add_event["event_hash"], {"state_root": add_event["event_hash"]}, pause_output, 0, "FENCED")
    subtract_output = {
        "delta_core": aggregates["delta_core"],
        "delta_packet": aggregates["delta_packet"],
        "delta_global": aggregates["delta_global"],
    }
    subtract_event = make_event(5, "SUBTRACT", pause_event["event_hash"], pause_output | add_output, subtract_output, aggregates["delta_global"], "SUBTRACTED")
    baseline_output = aggregates["baseline"] | {"decision": aggregates["decision"]}
    baseline_event = make_event(6, "BASELINE", subtract_event["event_hash"], subtract_output, baseline_output, baseline_output.get("delta_vs_best_baseline") or 0, aggregates["decision"])
    return {
        "protocol": "PROVENANCE_PASS_ADD_PAUSE_SUBTRACT_BASELINE_v1",
        "clock_participates_in_hash": False,
        "events": [provenance_event, pass_event, add_event, pause_event, subtract_event, baseline_event],
        "final_event_hash": baseline_event["event_hash"],
    }


def write_summary(receipt: dict[str, Any]) -> None:
    agg = receipt["aggregate"]
    lines = [
        "# enwiki9 Canonical Slice Baseline Probe Receipt",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        receipt["claim_boundary"],
        "",
        "## Input",
        "",
        f"- Path: `{receipt['input']['path']}`",
        f"- Size bytes: `{receipt['input']['size_bytes']}`",
        f"- Canonical claim: `{receipt['input']['canonical_claim']}`",
        f"- Provenance decision: `{receipt['input']['provenance_decision']}`",
        "",
        "## Aggregate",
        "",
        "| Slices | Exact replay | Raw | Core | Packet | Dictionary | Delta core | Delta packet | Delta global | Best baseline | Delta vs best |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
        (
            f"| {agg['slice_count']} | {agg['all_exact_replay']} | {agg['raw_bytes']} | "
            f"{agg['core_bytes']} | {agg['packet_bytes']} | {agg['dictionary_bytes']} | "
            f"{agg['delta_core']} | {agg['delta_packet']} | {agg['delta_global']} | "
            f"{agg['baseline']['best_baseline']} | {agg['baseline']['delta_vs_best_baseline']} |"
        ),
        "",
        "## Slices",
        "",
        "| Name | Selection | Offset | Class | Raw | Core | Packet | Packet delta | Best baseline |",
        "|---|---|---:|---|---:|---:|---:|---:|---|",
    ]
    for item in receipt["slices"]:
        lines.append(
            f"| `{item['name']}` | `{item['selection']}` | {item['offset']} | `{item['slice_class']}` | "
            f"{item['raw_bytes']} | {item['core_bytes']} | {item['packet_bytes']} | "
            f"{item['delta_packet']} | `{item['baseline']['best_baseline']}` |"
        )
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_receipt(path: Path, slice_size: int, scan_stride: int, canonical_claim_arg: str) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source_dir = OUT_DIR / "cores"
    source_dir.mkdir(parents=True, exist_ok=True)
    size = path.stat().st_size if path.exists() else 0
    canonical_claim, provenance_decision = provenance_status(path, size, canonical_claim_arg)
    input_sha = sha256_file(path) if path.exists() else None
    dictionary_bytes, dictionary_hash = V4.dictionary_bytes_and_hash()
    protocol_sha = V4.protocol_hash()
    raw_slices = collect_slices(path, size, slice_size, scan_stride) if path.exists() else []
    slices = [run_slice(item, source_dir, dictionary_hash, protocol_sha) for item in raw_slices]
    agg = aggregate(slices, dictionary_bytes, canonical_claim, provenance_decision)
    input_info = {
        "path": str(path),
        "size_bytes": size,
        "sha256": input_sha,
        "canonical_claim": canonical_claim,
        "provenance_decision": provenance_decision,
    }
    receipt = {
        "schema": "enwiki9_canonical_slice_baseline_probe_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "codec_frozen_from": "v4",
        "encoder_changed": False,
        "encoder_frozen_from": rel(V4.V3.V2_SCRIPT),
        "receipt_mode_frozen_from": rel(V4.V3_SCRIPT),
        "v4_script": rel(V4_SCRIPT),
        "receipt_chain": ["PROVENANCE", "PASS", "ADD", "PAUSE", "SUBTRACT", "BASELINE"],
        "clock_participates_in_hash": False,
        "input": input_info,
        "slice_size": slice_size,
        "scan_stride": scan_stride,
        "fixed_offsets": FIXED_OFFSETS,
        "target_classes": TARGET_CLASSES,
        "dictionary_bytes": dictionary_bytes,
        "dictionary_sha256": dictionary_hash,
        "protocol_sha256": protocol_sha,
        "aggregate": agg,
        "slices": slices,
        "gate_protocol": build_gate_protocol(
            input_info=input_info,
            aggregates=agg,
            dictionary_hash=dictionary_hash,
            protocol_sha=protocol_sha,
        ),
        "prior_v4": read_prior_v4(),
        "decision": agg["decision"],
        "claim_boundary": (
            "Canonical slice baseline probe only. It freezes the v4 codec and "
            "accounting path, adds a provenance gate for canonical enwik9, and "
            "adds baseline comparisons against ordinary compressors. Inputs that "
            "are not exactly 1,000,000,000 bytes are fixture evidence only. This "
            "is not a Hutter/LTCB submission or corpus-scale result."
        ),
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v5 canonical enwik9 slice baseline probe.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--slice-size", type=int, default=DEFAULT_SLICE_SIZE)
    parser.add_argument("--scan-stride", type=int, default=DEFAULT_SCAN_STRIDE)
    parser.add_argument("--canonical-claim", choices=["auto", "canonical_enwik9", "fixture", "unknown"], default="auto")
    args = parser.parse_args()

    receipt = build_receipt(args.input, args.slice_size, args.scan_stride, args.canonical_claim)
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(receipt)
    print(
        json.dumps(
            {
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "receipt_hash": receipt["receipt_hash"],
                "decision": receipt["decision"],
                "input": receipt["input"],
                "aggregate": receipt["aggregate"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
