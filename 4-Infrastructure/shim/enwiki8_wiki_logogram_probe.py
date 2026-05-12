#!/usr/bin/env python3
"""Encode a bounded enwik8 slice with wiki/logogram grammar atoms.

This is a no-training, no-benchmark probe. It tests whether a tiny
decoder-facing grammar for common MediaWiki/XML surfaces can replay a local
enwik8 slice byte-exactly with residual/receipt accounting.
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
DEFAULT_CORPUS = REPO / "shared-data" / "corpora" / "enwik8"
OUT_DIR = REPO / "shared-data" / "data" / "enwiki8_wiki_logogram_probe"
RECEIPT = OUT_DIR / "enwiki8_wiki_logogram_probe_receipt.json"
SUMMARY = OUT_DIR / "enwiki8_wiki_logogram_probe_receipt.md"
CORE = OUT_DIR / "enwiki8_wiki_logogram_probe_core.wlg1"

OP_LIT = 0x00
OP_WLINK = 0x81
OP_TEMPLATE = 0x82
OP_SECTION = 0x83
OP_TAG_PAIR = 0x84
OP_TAG_ATTR_PAIR = 0x85
OP_EMPTY_MINOR = 0x86

TAG_IDS = {
    "title": 1,
    "id": 2,
    "timestamp": 3,
    "username": 4,
    "comment": 5,
    "text": 6,
}
ID_TAGS = {value: key for key, value in TAG_IDS.items()}

TAG_PAIR_RE = re.compile(
    rb"<(title|id|timestamp|username|comment)>([^<]*)</\1>", re.DOTALL
)
TEXT_ATTR_RE = re.compile(rb'<text xml:space="preserve">([^<]*)</text>', re.DOTALL)
WLINK_RE = re.compile(rb"\[\[([^\[\]\n]{1,240})\]\]")
TEMPLATE_RE = re.compile(rb"\{\{([^\{\}\n]{1,240})\}\}")
SECTION_RE = re.compile(rb"==\s*([^=\n][^\n]{0,160}?)\s*==")


@dataclass(frozen=True)
class Atom:
    kind: str
    raw: bytes
    payload: bytes
    start: int
    end: int
    tag: str | None = None


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def put_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("negative varint")
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
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
        if shift > 28:
            raise ValueError("varint too long")


def emit_payload(opcode: int, payload: bytes) -> bytes:
    return bytes([opcode]) + put_varint(len(payload)) + payload


def atom_encoded(atom: Atom) -> bytes:
    if atom.kind == "LIT":
        return emit_payload(OP_LIT, atom.payload)
    if atom.kind == "WLINK":
        return emit_payload(OP_WLINK, atom.payload)
    if atom.kind == "TEMPLATE":
        return emit_payload(OP_TEMPLATE, atom.payload)
    if atom.kind == "SECTION":
        return emit_payload(OP_SECTION, atom.payload)
    if atom.kind == "TAG_PAIR":
        tag_id = TAG_IDS[atom.tag or ""]
        return bytes([OP_TAG_PAIR, tag_id]) + put_varint(len(atom.payload)) + atom.payload
    if atom.kind == "TAG_ATTR_PAIR":
        tag_id = TAG_IDS[atom.tag or ""]
        return bytes([OP_TAG_ATTR_PAIR, tag_id]) + put_varint(len(atom.payload)) + atom.payload
    if atom.kind == "EMPTY_MINOR":
        return bytes([OP_EMPTY_MINOR])
    raise ValueError(f"unsupported atom kind {atom.kind}")


def decode_core(core: bytes) -> bytes:
    if not core.startswith(b"WLG1"):
        raise ValueError("bad core magic")
    cursor = 4
    out = bytearray()
    while cursor < len(core):
        opcode = core[cursor]
        cursor += 1
        if opcode == OP_EMPTY_MINOR:
            out.extend(b"<minor />")
            continue
        if opcode in {OP_TAG_PAIR, OP_TAG_ATTR_PAIR}:
            tag_id = core[cursor]
            cursor += 1
            tag = ID_TAGS[tag_id]
            size, cursor = read_varint(core, cursor)
            payload = core[cursor : cursor + size]
            cursor += size
            if opcode == OP_TAG_PAIR:
                out.extend(b"<" + tag.encode("ascii") + b">" + payload + b"</" + tag.encode("ascii") + b">")
            else:
                if tag != "text":
                    raise ValueError("unsupported attr tag")
                out.extend(b'<text xml:space="preserve">' + payload + b"</text>")
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
        elif opcode == OP_SECTION:
            out.extend(b"== " + payload + b" ==")
        else:
            raise ValueError(f"bad opcode {opcode}")
    return bytes(out)


def best_match(slice_bytes: bytes, cursor: int) -> Atom | None:
    candidates: list[Atom] = []
    for regex, kind in [
        (TEXT_ATTR_RE, "TAG_ATTR_PAIR"),
        (TAG_PAIR_RE, "TAG_PAIR"),
        (WLINK_RE, "WLINK"),
        (TEMPLATE_RE, "TEMPLATE"),
        (SECTION_RE, "SECTION"),
    ]:
        match = regex.match(slice_bytes, cursor)
        if not match:
            continue
        raw = match.group(0)
        if kind == "TAG_PAIR":
            tag = match.group(1).decode("ascii")
            payload = match.group(2)
        elif kind == "TAG_ATTR_PAIR":
            tag = "text"
            payload = match.group(1)
        else:
            tag = None
            payload = match.group(1).strip() if kind == "SECTION" else match.group(1)
        atom = Atom(kind=kind, raw=raw, payload=payload, start=cursor, end=cursor + len(raw), tag=tag)
        if len(atom_encoded(atom)) < len(raw):
            candidates.append(atom)
    if slice_bytes.startswith(b"<minor />", cursor):
        atom = Atom(kind="EMPTY_MINOR", raw=b"<minor />", payload=b"", start=cursor, end=cursor + len(b"<minor />"))
        candidates.append(atom)
    if not candidates:
        return None
    return min(candidates, key=lambda atom: len(atom_encoded(atom)) - len(atom.raw))


def encode_slice(slice_bytes: bytes) -> tuple[bytes, list[Atom]]:
    atoms: list[Atom] = []
    literal = bytearray()
    literal_start = 0
    cursor = 0

    def flush_literal(at: int) -> None:
        nonlocal literal, literal_start
        if literal:
            payload = bytes(literal)
            atoms.append(Atom(kind="LIT", raw=payload, payload=payload, start=literal_start, end=at))
            literal = bytearray()

    while cursor < len(slice_bytes):
        atom = best_match(slice_bytes, cursor)
        if atom is None:
            if not literal:
                literal_start = cursor
            literal.append(slice_bytes[cursor])
            cursor += 1
            continue
        flush_literal(cursor)
        atoms.append(atom)
        cursor = atom.end
    flush_literal(cursor)
    core = b"WLG1" + b"".join(atom_encoded(atom) for atom in atoms)
    return core, atoms


def atom_receipt(atom: Atom, index: int) -> dict[str, Any]:
    encoded = atom_encoded(atom)
    return {
        "index": index,
        "kind": atom.kind,
        "tag": atom.tag,
        "start": atom.start,
        "end": atom.end,
        "raw_bytes": len(atom.raw),
        "encoded_bytes": len(encoded),
        "byte_gain": len(atom.raw) - len(encoded),
        "raw_hash": sha256_bytes(atom.raw),
        "encoded_hash": sha256_bytes(encoded),
        "decision": "ACCEPT",
        "residual_policy": "none",
    }


def compression_baselines(data: bytes) -> dict[str, int]:
    return {
        "zlib_9": len(zlib.compress(data, 9)),
        "bz2_9": len(bz2.compress(data, 9)),
        "lzma_9": len(lzma.compress(data, preset=9)),
    }


def write_summary(receipt: dict[str, Any]) -> None:
    lines = [
        "# enwiki8 Wiki Logogram Probe Receipt",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        receipt["claim_boundary"],
        "",
        "## Slice",
        "",
        f"- Corpus: `{receipt['corpus']}`",
        f"- Offset: `{receipt['offset']}`",
        f"- Length: `{receipt['slice_bytes']}`",
        f"- Slice hash: `{receipt['slice_sha256']}`",
        "",
        "## Accounting",
        "",
        "| Metric | Bytes |",
        "|---|---:|",
        f"| Raw slice | {receipt['raw_bytes']} |",
        f"| Encoded core | {receipt['core_bytes']} |",
        f"| Packet estimate | {receipt['packet_estimate_bytes']} |",
        f"| Full receipt JSON | {receipt['full_receipt_json_bytes']} |",
        "",
        "## Status",
        "",
        f"- Exact replay: `{receipt['exact_replay']}`",
        f"- Core byte gain: `{receipt['core_byte_gain']}`",
        f"- Packet byte gain estimate: `{receipt['packet_byte_gain_estimate']}`",
        f"- Atom count: `{receipt['atom_count']}`",
        "",
        "## Baselines",
        "",
    ]
    for name, value in receipt["baselines"].items():
        lines.append(f"- `{name}`: `{value}` bytes")
    lines.append("")
    SUMMARY.write_text("\n".join(lines), encoding="utf-8")


def build_receipt(corpus: Path, offset: int, length: int) -> dict[str, Any]:
    source = corpus.read_bytes()
    slice_bytes = source[offset : offset + length]
    core, atoms = encode_slice(slice_bytes)
    decoded = decode_core(core)
    receipts = [atom_receipt(atom, index) for index, atom in enumerate(atoms)]
    kind_counts = {kind: sum(1 for atom in atoms if atom.kind == kind) for kind in sorted({atom.kind for atom in atoms})}
    truncated_receipt_bytes = 4 * len(atoms)
    header_bytes = 8
    packet_estimate_bytes = len(core) + header_bytes + truncated_receipt_bytes
    core_path = CORE
    core_path.write_bytes(core)

    receipt = {
        "schema": "enwiki8_wiki_logogram_probe_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "corpus": rel(corpus) if corpus.is_relative_to(REPO) else str(corpus),
        "corpus_size": corpus.stat().st_size,
        "offset": offset,
        "slice_bytes": len(slice_bytes),
        "slice_sha256": sha256_bytes(slice_bytes),
        "core": rel(core_path),
        "core_sha256": sha256_bytes(core),
        "decoded_sha256": sha256_bytes(decoded),
        "exact_replay": decoded == slice_bytes,
        "atom_count": len(atoms),
        "kind_counts": kind_counts,
        "raw_bytes": len(slice_bytes),
        "core_bytes": len(core),
        "core_byte_gain": len(slice_bytes) - len(core),
        "header_bytes": header_bytes,
        "truncated_receipt_bytes": truncated_receipt_bytes,
        "packet_estimate_bytes": packet_estimate_bytes,
        "packet_byte_gain_estimate": len(slice_bytes) - packet_estimate_bytes,
        "baselines": compression_baselines(slice_bytes),
        "atom_receipts": receipts,
        "decision": "HOLD",
        "fixture_status": "ADMIT_FIXTURE" if decoded == slice_bytes and len(slice_bytes) > len(core) else "HOLD_DIAGNOSTIC",
        "claim_boundary": (
            "Bounded local enwiki8 slice probe only. This is not a Hutter Prize "
            "submission, not a full-corpus enwiki8 result, and not evidence of "
            "compression competitiveness. The packet estimate uses truncated "
            "per-atom receipt hashes; full JSON receipts are inspection material."
        ),
    }
    receipt["full_receipt_json_bytes"] = len(stable_json(receipt).encode("utf-8"))
    receipt["receipt_hash"] = sha256_bytes(
        stable_json(
            {
                key: value
                for key, value in receipt.items()
                if key not in {"receipt_hash", "generated_at_utc"}
            }
        ).encode("utf-8")
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a wiki-logogram encode probe on a local enwiki8 slice.")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--offset", type=int, default=1406)
    parser.add_argument("--length", type=int, default=4096)
    parser.add_argument("--receipt", type=Path, default=RECEIPT)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    receipt = build_receipt(args.corpus, args.offset, args.length)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(receipt)
    print(
        json.dumps(
            {
                "receipt": rel(args.receipt),
                "summary": rel(SUMMARY),
                "core": rel(CORE),
                "receipt_hash": receipt["receipt_hash"],
                "fixture_status": receipt["fixture_status"],
                "raw_bytes": receipt["raw_bytes"],
                "core_bytes": receipt["core_bytes"],
                "packet_estimate_bytes": receipt["packet_estimate_bytes"],
                "baselines": receipt["baselines"],
                "kind_counts": receipt["kind_counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
