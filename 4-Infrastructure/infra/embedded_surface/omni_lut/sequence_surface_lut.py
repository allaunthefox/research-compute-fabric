#!/usr/bin/env python3
"""Compact LUT for GCL sequence-substrate surface selection.

This module treats DNA, RNA, mRNA, XNA, and Hachimoji as related sequence
surfaces instead of separate codecs. The token is intentionally small:

    u8 surface_id
    u8 alphabet_id
    u8 role_flags
    u8 op_flags

The payload is packed by alphabet width. DNA/RNA/mRNA use 2 bits per symbol,
Hachimoji uses 3 bits per symbol, and generic XNA uses a conservative 4-bit
symbol lane. The point is not biochemical authority; it is a cheap first-pass
surface selector that reduces storage and dispatch area before richer GCL
admission or verification runs.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Iterable


ROLE_ARCHIVAL = 0x01
ROLE_CATALYTIC = 0x02
ROLE_MESSENGER = 0x04
ROLE_SYNTHETIC = 0x08
ROLE_EXPANDED = 0x10

OP_COMPLEMENT = 0x01
OP_TRANSCRIBE = 0x02
OP_TRANSLATE_HINT = 0x04
OP_MUTATE = 0x08
OP_ROUTE = 0x10


@dataclass(frozen=True)
class SequenceSurface:
    name: str
    surface_id: int
    alphabet_id: int
    symbols: str
    role_flags: int
    op_flags: int
    bits_per_symbol: int
    description: str

    def token(self) -> bytes:
        return bytes([self.surface_id, self.alphabet_id, self.role_flags, self.op_flags])

    @property
    def symbol_to_code(self) -> dict[str, int]:
        return {symbol: index for index, symbol in enumerate(self.symbols)}


SURFACES: dict[str, SequenceSurface] = {
    "dna": SequenceSurface(
        "dna",
        0x01,
        0x04,
        "ACGT",
        ROLE_ARCHIVAL,
        OP_COMPLEMENT | OP_TRANSCRIBE | OP_MUTATE | OP_ROUTE,
        2,
        "stable archival heredity surface",
    ),
    "rna": SequenceSurface(
        "rna",
        0x02,
        0x04,
        "ACGU",
        ROLE_CATALYTIC | ROLE_MESSENGER,
        OP_COMPLEMENT | OP_TRANSLATE_HINT | OP_MUTATE | OP_ROUTE,
        2,
        "flexible catalytic and regulatory surface",
    ),
    "mrna": SequenceSurface(
        "mrna",
        0x03,
        0x04,
        "ACGU",
        ROLE_MESSENGER,
        OP_TRANSLATE_HINT | OP_MUTATE | OP_ROUTE,
        2,
        "transient executable transcript surface",
    ),
    "hachimoji": SequenceSurface(
        "hachimoji",
        0x08,
        0x08,
        "ACGTZPSB",
        ROLE_ARCHIVAL | ROLE_EXPANDED | ROLE_SYNTHETIC,
        OP_COMPLEMENT | OP_TRANSCRIBE | OP_MUTATE | OP_ROUTE,
        3,
        "expanded eight-symbol hereditary surface",
    ),
    "xna": SequenceSurface(
        "xna",
        0x10,
        0x10,
        "0123456789ABCDEF",
        ROLE_SYNTHETIC | ROLE_EXPANDED,
        OP_COMPLEMENT | OP_MUTATE | OP_ROUTE,
        4,
        "generic synthetic backbone and expanded alphabet lane",
    ),
}


COMPLEMENT: dict[str, dict[str, str]] = {
    "dna": {"A": "T", "C": "G", "G": "C", "T": "A"},
    "rna": {"A": "U", "C": "G", "G": "C", "U": "A"},
    "mrna": {"A": "U", "C": "G", "G": "C", "U": "A"},
    "hachimoji": {
        "A": "T",
        "C": "G",
        "G": "C",
        "T": "A",
        "Z": "P",
        "P": "Z",
        "S": "B",
        "B": "S",
    },
}


def normalize_sequence(surface: SequenceSurface, sequence: str) -> str:
    clean = "".join(ch for ch in sequence.upper() if not ch.isspace())
    allowed = set(surface.symbols)
    bad = sorted({ch for ch in clean if ch not in allowed})
    if bad:
        raise ValueError(f"{surface.name} sequence contains unsupported symbols: {''.join(bad)}")
    return clean


def pack_sequence(surface: SequenceSurface, sequence: str) -> bytes:
    """Pack sequence symbols into the minimum whole-byte lane for the surface."""
    clean = normalize_sequence(surface, sequence)
    code = surface.symbol_to_code
    acc = 0
    width = 0
    out = bytearray()
    for symbol in clean:
        acc = (acc << surface.bits_per_symbol) | code[symbol]
        width += surface.bits_per_symbol
        while width >= 8:
            shift = width - 8
            out.append((acc >> shift) & 0xFF)
            acc &= (1 << shift) - 1
            width = shift
    if width:
        out.append((acc << (8 - width)) & 0xFF)
    return bytes(out)


def unpack_sequence(surface: SequenceSurface, packed: bytes, symbol_count: int) -> str:
    symbols = surface.symbols
    mask = (1 << surface.bits_per_symbol) - 1
    acc = 0
    width = 0
    out: list[str] = []
    for byte in packed:
        acc = (acc << 8) | byte
        width += 8
        while width >= surface.bits_per_symbol and len(out) < symbol_count:
            shift = width - surface.bits_per_symbol
            out.append(symbols[(acc >> shift) & mask])
            acc &= (1 << shift) - 1
            width = shift
    if len(out) != symbol_count:
        raise ValueError("packed payload ended before requested symbol count")
    return "".join(out)


def complement(surface: SequenceSurface, sequence: str) -> str:
    table = COMPLEMENT.get(surface.name)
    if table is None:
        raise ValueError(f"{surface.name} has no concrete complement table in this LUT")
    clean = normalize_sequence(surface, sequence)
    return "".join(table[symbol] for symbol in clean)


def compression_report(surface: SequenceSurface, sequence: str) -> dict[str, object]:
    clean = normalize_sequence(surface, sequence)
    packed = pack_sequence(surface, clean)
    token = surface.token()
    raw_ascii = len(clean)
    packed_bytes = len(token) + 2 + len(packed)
    reduction = 0.0 if raw_ascii == 0 else 1.0 - (packed_bytes / raw_ascii)
    return {
        "surface": surface.name,
        "token_hex": token.hex(),
        "symbols": len(clean),
        "bits_per_symbol": surface.bits_per_symbol,
        "raw_ascii_bytes": raw_ascii,
        "packed_payload_bytes": len(packed),
        "framed_bytes": packed_bytes,
        "reduction_percent_vs_ascii": round(reduction * 100, 2),
        "role_flags": f"0x{surface.role_flags:02X}",
        "op_flags": f"0x{surface.op_flags:02X}",
        "description": surface.description,
    }


def iter_surface_rows() -> Iterable[dict[str, object]]:
    for surface in SURFACES.values():
        yield {
            "name": surface.name,
            "surface_id": f"0x{surface.surface_id:02X}",
            "alphabet_id": f"0x{surface.alphabet_id:02X}",
            "symbols": surface.symbols,
            "bits_per_symbol": surface.bits_per_symbol,
            "role_flags": f"0x{surface.role_flags:02X}",
            "op_flags": f"0x{surface.op_flags:02X}",
            "token_hex": surface.token().hex(),
            "description": surface.description,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surface", choices=sorted(SURFACES), default="dna")
    parser.add_argument("--sequence", default="ACGTACGTACGTACGT")
    parser.add_argument("--complement", action="store_true")
    parser.add_argument("--table", action="store_true")
    args = parser.parse_args()

    if args.table:
        print(json.dumps(list(iter_surface_rows()), indent=2))
        return 0

    surface = SURFACES[args.surface]
    report = compression_report(surface, args.sequence)
    packed = pack_sequence(surface, args.sequence)
    report["packed_hex"] = packed.hex()
    report["roundtrip"] = unpack_sequence(surface, packed, len(normalize_sequence(surface, args.sequence)))
    if args.complement:
        report["complement"] = complement(surface, args.sequence)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
