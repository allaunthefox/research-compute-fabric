#!/usr/bin/env python3
"""Existing GCL motif and informaton surface LUT.

These are not sequence alphabets. They are finite motifs already present in the
GCL/Omnitoken/JSON-L design: control pulses, admission gates, compression,
routing, recovery, manifests, attestations, and informatic bind/genome surfaces.
The possibility-space probe imports this table so biological substrates and GCL
motifs share one metaprobe/RGFlow selection path.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Iterable

try:
    from .sequence_surface_lut import (
        OP_MUTATE,
        OP_ROUTE,
        ROLE_ARCHIVAL,
        ROLE_CATALYTIC,
        ROLE_EXPANDED,
        ROLE_MESSENGER,
        ROLE_SYNTHETIC,
    )
except ImportError:
    from sequence_surface_lut import (
        OP_MUTATE,
        OP_ROUTE,
        ROLE_ARCHIVAL,
        ROLE_CATALYTIC,
        ROLE_EXPANDED,
        ROLE_MESSENGER,
        ROLE_SYNTHETIC,
    )


OP_CONTROL = 0x20
OP_ADMIT = 0x40
OP_ATTEST = 0x80

ROLE_CONTROL = ROLE_ARCHIVAL
ROLE_TRUST = ROLE_CATALYTIC
ROLE_DATA = ROLE_MESSENGER
ROLE_TOPOLOGY = ROLE_SYNTHETIC
ROLE_INFORMATON = ROLE_EXPANDED


@dataclass(frozen=True)
class GCLMotifSurface:
    name: str
    motif_id: int
    domain_id: int
    alphabet_size: int
    bits_per_symbol: int
    role_flags: int
    op_flags: int
    closure_kind: str
    description: str

    def token(self) -> bytes:
        return bytes([self.motif_id, self.domain_id, self.role_flags, self.op_flags & 0xFF])


MOTIFS: dict[str, GCLMotifSurface] = {
    "gcl_control": GCLMotifSurface(
        "gcl_control",
        0x20,
        0x01,
        16,
        4,
        ROLE_CONTROL,
        OP_CONTROL | OP_ROUTE,
        "finite_codon",
        "finite OT0 control codons: nop, health, status, metrics, ack, nack",
    ),
    "gcl_admission": GCLMotifSurface(
        "gcl_admission",
        0x21,
        0x05,
        8,
        3,
        ROLE_TOPOLOGY | ROLE_INFORMATON,
        OP_ADMIT | OP_ROUTE,
        "rgflow",
        "RGFlow admission/refusal motif before expansion",
    ),
    "gcl_compression": GCLMotifSurface(
        "gcl_compression",
        0x22,
        0x06,
        8,
        3,
        ROLE_DATA | ROLE_INFORMATON,
        OP_MUTATE | OP_ROUTE | OP_ADMIT,
        "codec_roundtrip",
        "Delta GCL, PTOS, and compressed manifest motif",
    ),
    "gcl_route": GCLMotifSurface(
        "gcl_route",
        0x23,
        0x07,
        16,
        4,
        ROLE_TOPOLOGY | ROLE_INFORMATON,
        OP_ROUTE | OP_ADMIT,
        "topology_route",
        "route/refuse motif for carrier-independent topology movement",
    ),
    "gcl_manifest": GCLMotifSurface(
        "gcl_manifest",
        0x24,
        0x08,
        16,
        4,
        ROLE_DATA | ROLE_ARCHIVAL,
        OP_ROUTE | OP_ATTEST,
        "hash_manifest",
        "manifest/fragment motif with payload hash conservation",
    ),
    "gcl_attest": GCLMotifSurface(
        "gcl_attest",
        0x25,
        0x04,
        8,
        3,
        ROLE_TRUST | ROLE_INFORMATON,
        OP_ATTEST | OP_ROUTE,
        "hash_chain",
        "attestation motif for state hash, provenance, and replay defense",
    ),
    "gcl_recovery": GCLMotifSurface(
        "gcl_recovery",
        0x26,
        0x0D,
        4,
        2,
        ROLE_CONTROL | ROLE_ARCHIVAL,
        OP_CONTROL | OP_ROUTE | OP_ADMIT,
        "last_good",
        "minimal recovery, snapshot, mark-good, and rollback motif",
    ),
    "informaton_genome": GCLMotifSurface(
        "informaton_genome",
        0x30,
        0x0E,
        8,
        3,
        ROLE_INFORMATON | ROLE_TOPOLOGY,
        OP_ROUTE | OP_ADMIT | OP_ATTEST,
        "rg_address",
        "6D quantized genome/informaton address surface",
    ),
    "informaton_bind": GCLMotifSurface(
        "informaton_bind",
        0x31,
        0x0F,
        5,
        3,
        ROLE_INFORMATON | ROLE_TRUST,
        OP_ATTEST | OP_ADMIT,
        "invariant_witness",
        "lawful/cost/invariant bind witness surface",
    ),
    "ms3c_reduction_gear": GCLMotifSurface(
        "ms3c_reduction_gear",
        0x32,
        0x32,
        16,
        4,
        ROLE_TOPOLOGY | ROLE_INFORMATON,
        OP_CONTROL | OP_ADMIT | OP_ROUTE | OP_ATTEST,
        "route_prior_geometry",
        "Matroska-S3C nested reduction gear route-prior surface",
    ),
}


def iter_motif_rows() -> Iterable[dict[str, object]]:
    for motif in MOTIFS.values():
        yield {
            "name": motif.name,
            "motif_id": f"0x{motif.motif_id:02X}",
            "domain_id": f"0x{motif.domain_id:02X}",
            "alphabet_size": motif.alphabet_size,
            "bits_per_symbol": motif.bits_per_symbol,
            "role_flags": f"0x{motif.role_flags:02X}",
            "op_flags": f"0x{motif.op_flags:02X}",
            "closure_kind": motif.closure_kind,
            "token_hex": motif.token().hex(),
            "description": motif.description,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl", action="store_true")
    args = parser.parse_args()
    rows = list(iter_motif_rows())
    if args.jsonl:
        for row in rows:
            print(json.dumps(row, separators=(",", ":")))
    else:
        print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
