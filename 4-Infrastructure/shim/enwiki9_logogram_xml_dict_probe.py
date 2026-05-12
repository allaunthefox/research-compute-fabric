#!/usr/bin/env python3
"""v2 fixed-tag dictionary probe for enwiki9/MediaWiki logogram targeting.

This is the deliberately boring next pass after the v1 targeter negative
control: promote repeated XML/MediaWiki scaffolding into fixed tag IDs and
measure whether the core delta flips positive on markup-heavy slices.
"""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import lzma
import re
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DEFAULT_BUNDLE_DEMO = REPO / "shared-data" / "data" / "enwiki9_logogram_targeter" / "demo"
DEFAULT_LOCAL_SAMPLE = Path("/home/allaun/Downloads/data/enwik9_data/1234567")
OUT_DIR = REPO / "shared-data" / "data" / "enwiki9_logogram_xml_dict_probe"
RECEIPT = OUT_DIR / "enwiki9_logogram_xml_dict_probe_receipt.json"
SUMMARY = OUT_DIR / "enwiki9_logogram_xml_dict_probe_receipt.md"
V1_RECEIPT = REPO / "shared-data" / "data" / "enwiki9_logogram_targeter" / "enwiki9_logogram_targeter_receipt.json"

OP_LIT = 0x00
OP_WLINK = 0x81
OP_TEMPLATE = 0x82
OP_REF = 0x83
OP_TABLE = 0x84
OP_MOTIF = 0x85
OP_FIXED_TAG = 0x90
OP_TAG_PAIR = 0x91
OP_TEXT_ATTR_PAIR = 0x92
OP_TAG_ATTR = 0x93

FIXED_TAGS = [
    b"<mediawiki",
    b"</mediawiki>",
    b"<siteinfo>",
    b"</siteinfo>",
    b"<namespaces>",
    b"</namespaces>",
    b"<page>",
    b"</page>",
    b"<revision>",
    b"</revision>",
    b"<contributor>",
    b"</contributor>",
    b"<minor />",
    b"</text>",
    b"<!DOCTYPE html>",
    b"<html",
    b"</html>",
    b"<head>",
    b"</head>",
    b"<body>",
    b"</body>",
    b"</script>",
    b"</style>",
    b"</div>",
    b"</span>",
]
TAG_TO_ID = {tag: index + 1 for index, tag in enumerate(FIXED_TAGS)}
ID_TO_TAG = {index + 1: tag for index, tag in enumerate(FIXED_TAGS)}

PAIR_TAGS = [
    b"title",
    b"id",
    b"timestamp",
    b"username",
    b"comment",
    b"sitename",
    b"base",
    b"generator",
    b"case",
    b"namespace",
    b"model",
    b"format",
]
PAIR_TO_ID = {tag: index + 1 for index, tag in enumerate(PAIR_TAGS)}
ID_TO_PAIR = {index + 1: tag for index, tag in enumerate(PAIR_TAGS)}

ATTR_TAGS = [
    b"mediawiki",
    b"text",
    b"html",
    b"meta",
    b"script",
    b"link",
    b"div",
    b"span",
    b"body",
]
ATTR_TO_ID = {tag: index + 1 for index, tag in enumerate(ATTR_TAGS)}
ID_TO_ATTR = {index + 1: tag for index, tag in enumerate(ATTR_TAGS)}

MOTIFS = [
    b" the ",
    b" and ",
    b" of ",
    b" in ",
    b" to ",
    b", the ",
    b". The ",
    b"#REDIRECT ",
    b" xml:space=\"preserve\"",
    b" xmlns=\"",
    b" http://",
]
MOTIF_TO_ID = {motif: index + 1 for index, motif in enumerate(MOTIFS)}
ID_TO_MOTIF = {index + 1: motif for index, motif in enumerate(MOTIFS)}

PAIR_RE = re.compile(
    rb"<(title|id|timestamp|username|comment|sitename|base|generator|case|namespace|model|format)(\s[^<>]*)?>(.*?)</\1>",
    re.DOTALL,
)
TEXT_ATTR_RE = re.compile(rb'<text xml:space="preserve">(.*?)</text>', re.DOTALL)
ATTR_TAG_RE = re.compile(rb"<(mediawiki|html|meta|script|link|div|span|body)(\s[^<>]*?)>", re.DOTALL)
WLINK_RE = re.compile(rb"\[\[([^\[\]\n]{1,4096})\]\]")
TEMPLATE_RE = re.compile(rb"\{\{([^\{\}\n]{1,8192})\}\}")
REF_RE = re.compile(rb"<ref([^<>]*?)(?:/|>(.*?)</ref>)", re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True)
class Atom:
    kind: str
    raw: bytes
    payload: bytes
    start: int
    end: int
    id_value: int = 0
    attrs: bytes = b""


def put_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("negative varint")
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        out.append(byte | 0x80 if value else byte)
        if not value:
            return bytes(out)


def read_varint(data: bytes, cursor: int) -> tuple[int, int]:
    shift = 0
    value = 0
    while True:
        if cursor >= len(data):
            raise ValueError("truncated varint")
        byte = data[cursor]
        cursor += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, cursor
        shift += 7


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


def emit_payload(opcode: int, payload: bytes) -> bytes:
    return bytes([opcode]) + put_varint(len(payload)) + payload


def atom_encoded(atom: Atom) -> bytes:
    if atom.kind == "LIT":
        return emit_payload(OP_LIT, atom.payload)
    if atom.kind == "WLINK":
        return emit_payload(OP_WLINK, atom.payload)
    if atom.kind == "TEMPLATE":
        return emit_payload(OP_TEMPLATE, atom.payload)
    if atom.kind == "REF":
        return emit_payload(OP_REF, atom.payload)
    if atom.kind == "TABLE":
        return emit_payload(OP_TABLE, atom.payload)
    if atom.kind == "MOTIF":
        return bytes([OP_MOTIF, atom.id_value])
    if atom.kind == "FIXED_TAG":
        return bytes([OP_FIXED_TAG, atom.id_value])
    if atom.kind == "TAG_PAIR":
        return bytes([OP_TAG_PAIR, atom.id_value]) + put_varint(len(atom.attrs)) + atom.attrs + put_varint(len(atom.payload)) + atom.payload
    if atom.kind == "TEXT_ATTR_PAIR":
        return bytes([OP_TEXT_ATTR_PAIR]) + put_varint(len(atom.payload)) + atom.payload
    if atom.kind == "TAG_ATTR":
        return bytes([OP_TAG_ATTR, atom.id_value]) + put_varint(len(atom.attrs)) + atom.attrs
    raise ValueError(f"unsupported atom kind {atom.kind}")


def decode_core(core: bytes) -> bytes:
    if not core.startswith(b"WLG2"):
        raise ValueError("bad core magic")
    cursor = 4
    out = bytearray()
    while cursor < len(core):
        opcode = core[cursor]
        cursor += 1
        if opcode == OP_FIXED_TAG:
            tag_id = core[cursor]
            cursor += 1
            out.extend(ID_TO_TAG[tag_id])
            continue
        if opcode == OP_MOTIF:
            motif_id = core[cursor]
            cursor += 1
            out.extend(ID_TO_MOTIF[motif_id])
            continue
        if opcode == OP_TAG_PAIR:
            tag_id = core[cursor]
            cursor += 1
            attr_len, cursor = read_varint(core, cursor)
            attrs = core[cursor : cursor + attr_len]
            cursor += attr_len
            payload_len, cursor = read_varint(core, cursor)
            payload = core[cursor : cursor + payload_len]
            cursor += payload_len
            tag = ID_TO_PAIR[tag_id]
            out.extend(b"<" + tag + attrs + b">" + payload + b"</" + tag + b">")
            continue
        if opcode == OP_TEXT_ATTR_PAIR:
            payload_len, cursor = read_varint(core, cursor)
            payload = core[cursor : cursor + payload_len]
            cursor += payload_len
            out.extend(b'<text xml:space="preserve">' + payload + b"</text>")
            continue
        if opcode == OP_TAG_ATTR:
            tag_id = core[cursor]
            cursor += 1
            attr_len, cursor = read_varint(core, cursor)
            attrs = core[cursor : cursor + attr_len]
            cursor += attr_len
            out.extend(b"<" + ID_TO_ATTR[tag_id] + attrs + b">")
            continue

        size, cursor = read_varint(core, cursor)
        payload = core[cursor : cursor + size]
        cursor += size
        if opcode == OP_LIT:
            out.extend(payload)
        elif opcode == OP_WLINK:
            out.extend(b"[[" + payload + b"]]")
        elif opcode == OP_TEMPLATE:
            out.extend(b"{{" + payload + b"}}")
        elif opcode == OP_REF:
            if payload.endswith(b"\0SELF"):
                out.extend(b"<ref" + payload[:-5] + b"/>")
            else:
                attrs, body = payload.split(b"\0", 1)
                out.extend(b"<ref" + attrs + b">" + body + b"</ref>")
        elif opcode == OP_TABLE:
            out.extend(payload)
        else:
            raise ValueError(f"bad opcode {opcode}")
    return bytes(out)


def match_atom(data: bytes, cursor: int) -> Atom | None:
    candidates: list[Atom] = []

    text_match = TEXT_ATTR_RE.match(data, cursor)
    if text_match:
        raw = text_match.group(0)
        candidates.append(Atom("TEXT_ATTR_PAIR", raw, text_match.group(1), cursor, cursor + len(raw)))

    pair_match = PAIR_RE.match(data, cursor)
    if pair_match:
        raw = pair_match.group(0)
        tag = pair_match.group(1)
        attrs = pair_match.group(2) or b""
        payload = pair_match.group(3)
        candidates.append(Atom("TAG_PAIR", raw, payload, cursor, cursor + len(raw), PAIR_TO_ID[tag], attrs))

    attr_match = ATTR_TAG_RE.match(data, cursor)
    if attr_match:
        raw = attr_match.group(0)
        tag = attr_match.group(1)
        attrs = attr_match.group(2) or b""
        candidates.append(Atom("TAG_ATTR", raw, b"", cursor, cursor + len(raw), ATTR_TO_ID[tag], attrs))

    for tag in sorted(FIXED_TAGS, key=len, reverse=True):
        if data.startswith(tag, cursor):
            candidates.append(Atom("FIXED_TAG", tag, b"", cursor, cursor + len(tag), TAG_TO_ID[tag]))
            break

    wlink = WLINK_RE.match(data, cursor)
    if wlink:
        raw = wlink.group(0)
        candidates.append(Atom("WLINK", raw, wlink.group(1), cursor, cursor + len(raw)))

    template = TEMPLATE_RE.match(data, cursor)
    if template:
        raw = template.group(0)
        candidates.append(Atom("TEMPLATE", raw, template.group(1), cursor, cursor + len(raw)))

    ref = REF_RE.match(data, cursor)
    if ref:
        raw = ref.group(0)
        if raw.endswith(b"/>"):
            payload = (ref.group(1) or b"") + b"\0SELF"
        else:
            payload = (ref.group(1) or b"") + b"\0" + (ref.group(2) or b"")
        candidates.append(Atom("REF", raw, payload, cursor, cursor + len(raw)))

    for token in (b"{|", b"|}", b"|-"):
        if data.startswith(token, cursor):
            candidates.append(Atom("TABLE", token, token, cursor, cursor + len(token)))

    for motif in sorted(MOTIFS, key=len, reverse=True):
        if data.startswith(motif, cursor):
            candidates.append(Atom("MOTIF", motif, b"", cursor, cursor + len(motif), MOTIF_TO_ID[motif]))
            break

    if not candidates:
        return None
    return min(candidates, key=lambda atom: len(atom_encoded(atom)) - len(atom.raw))


def encode(data: bytes) -> tuple[bytes, list[Atom]]:
    atoms: list[Atom] = []
    literal = bytearray()
    literal_start = 0
    cursor = 0

    def flush_literal(at: int) -> None:
        nonlocal literal, literal_start
        if literal:
            payload = bytes(literal)
            atoms.append(Atom("LIT", payload, payload, literal_start, at))
            literal = bytearray()

    while cursor < len(data):
        atom = match_atom(data, cursor)
        if atom is None:
            if not literal:
                literal_start = cursor
            literal.append(data[cursor])
            cursor += 1
            continue
        flush_literal(cursor)
        atoms.append(atom)
        cursor = atom.end

    flush_literal(cursor)
    return b"WLG2" + b"".join(atom_encoded(atom) for atom in atoms), atoms


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = {byte: data.count(byte) for byte in set(data)}
    n = len(data)
    return -sum((count / n) * __import__("math").log2(count / n) for count in counts.values())


def baselines(data: bytes) -> dict[str, int]:
    return {
        "zlib_9": len(zlib.compress(data, 9)),
        "bz2_9": len(bz2.compress(data, 9)),
        "lzma_9": len(lzma.compress(data, preset=9)),
    }


def run_slice(name: str, source_label: str, data: bytes, out_dir: Path) -> dict[str, Any]:
    core, atoms = encode(data)
    decoded = decode_core(core)
    core_path = out_dir / f"{name}.wlg2"
    core_path.write_bytes(core)
    atom_counts = {kind: sum(1 for atom in atoms if atom.kind == kind) for kind in sorted({atom.kind for atom in atoms})}
    header_bytes = 8
    receipt_stub_bytes = 4 * len(atoms)
    packet_estimate = len(core) + header_bytes + receipt_stub_bytes
    return {
        "name": name,
        "source": source_label,
        "raw_bytes": len(data),
        "core_bytes": len(core),
        "packet_estimate_bytes": packet_estimate,
        "delta_core": len(data) - len(core),
        "delta_packet": len(data) - packet_estimate,
        "exact_replay": decoded == data,
        "atom_count": len(atoms),
        "atom_counts": atom_counts,
        "raw_sha256": sha256_bytes(data),
        "core": rel(core_path),
        "core_sha256": sha256_bytes(core),
        "entropy_raw": entropy(data),
        "entropy_core": entropy(core),
        "baselines": baselines(data),
        "fixture_status": "ADMIT_FIXTURE" if decoded == data and len(data) > len(core) else "HOLD_DIAGNOSTIC",
    }


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


def aggregate(results: list[dict[str, Any]], dictionary_bytes: int) -> dict[str, Any]:
    raw = sum(item["raw_bytes"] for item in results)
    core = sum(item["core_bytes"] for item in results)
    packet = sum(item["packet_estimate_bytes"] for item in results)
    return {
        "slice_count": len(results),
        "all_exact_replay": all(item["exact_replay"] for item in results),
        "raw_bytes": raw,
        "core_bytes": core,
        "packet_estimate_bytes": packet,
        "delta_core": raw - core,
        "delta_packet": raw - packet,
        "dictionary_bytes": dictionary_bytes,
        "delta_global": raw - (packet + dictionary_bytes),
        "status_counts": {
            status: sum(1 for item in results if item["fixture_status"] == status)
            for status in sorted({item["fixture_status"] for item in results})
        },
    }


def prior_v1_totals() -> dict[str, Any] | None:
    if not V1_RECEIPT.exists():
        return None
    receipt = json.loads(V1_RECEIPT.read_text(encoding="utf-8"))
    out: dict[str, Any] = {}
    for key, run_key in [("demo", "demo"), ("local_sample", "sample_20532")]:
        payload = receipt.get("runs", {}).get(run_key, {}).get("summary_payload")
        if not payload:
            continue
        raw = int(payload["total_raw_len"])
        core = int(payload["total_core_len"])
        packet = int(payload["total_local_packet_estimate"])
        out[key] = {
            "raw_bytes": raw,
            "core_bytes": core,
            "packet_estimate_bytes": packet,
            "delta_core": raw - core,
            "delta_packet": raw - packet,
            "all_exact_replay": bool(payload["all_roundtrip_ok"]),
        }
    return out or None


def write_summary(receipt: dict[str, Any]) -> None:
    lines = [
        "# enwiki9 XML Dictionary Probe Receipt",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        receipt["claim_boundary"],
        "",
        "## Aggregate",
        "",
        "| Run | Slices | Exact replay | Raw | Core | Packet est. | Delta core | Delta packet | Delta global |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ["demo", "local_sample"]:
        agg = receipt["aggregates"].get(name)
        if not agg:
            continue
        lines.append(
            f"| {name} | {agg['slice_count']} | {agg['all_exact_replay']} | "
            f"{agg['raw_bytes']} | {agg['core_bytes']} | {agg['packet_estimate_bytes']} | "
            f"{agg['delta_core']} | {agg['delta_packet']} | {agg['delta_global']} |"
        )
    if receipt.get("prior_v1_totals"):
        lines.extend(["", "## v1 Comparison", ""])
        for name, totals in receipt["prior_v1_totals"].items():
            lines.append(
                f"- `{name}` v1 raw/core/packet: "
                f"`{totals['raw_bytes']} / {totals['core_bytes']} / {totals['packet_estimate_bytes']}`"
            )
    lines.extend(["", "## Dictionary", ""])
    lines.append(f"- Fixed tag entries: `{len(FIXED_TAGS)}`")
    lines.append(f"- Pair tag entries: `{len(PAIR_TAGS)}`")
    lines.append(f"- Attribute tag entries: `{len(ATTR_TAGS)}`")
    lines.append(f"- Motif entries: `{len(MOTIFS)}`")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_receipt(demo_dir: Path, sample: Path, slice_size: int, max_sample_slices: int) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    demo_results = [run_slice(name, source, data, OUT_DIR) for name, source, data in demo_slices(demo_dir)]
    sample_results = [run_slice(name, source, data, OUT_DIR) for name, source, data in sample_slices(sample, slice_size, max_sample_slices)]
    dictionary_bytes = len(stable_json({"fixed": [tag.hex() for tag in FIXED_TAGS], "pair": [tag.hex() for tag in PAIR_TAGS], "attr": [tag.hex() for tag in ATTR_TAGS], "motif": [tag.hex() for tag in MOTIFS]}).encode("utf-8"))
    receipt = {
        "schema": "enwiki9_logogram_xml_dict_probe_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dictionary": {
            "fixed_tags": [tag.decode("utf-8", errors="replace") for tag in FIXED_TAGS],
            "pair_tags": [tag.decode("ascii") for tag in PAIR_TAGS],
            "attribute_tags": [tag.decode("ascii") for tag in ATTR_TAGS],
            "motifs": [motif.decode("utf-8", errors="replace") for motif in MOTIFS],
        },
        "dictionary_bytes": dictionary_bytes,
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
        "prior_v1_totals": prior_v1_totals(),
        "decision": "HOLD",
        "claim_boundary": (
            "Fixed-tag dictionary probe only. Demo slices come from the uploaded "
            "targeter bundle; the local sample is a 20,532-byte noncanonical HTML "
            "file, not the 1,000,000,000-byte enwik9 corpus. Positive deltas are "
            "fixture evidence only and do not establish Hutter/LTCB performance."
        ),
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v2 fixed XML/MediaWiki tag dictionary probe.")
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
