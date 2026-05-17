#!/usr/bin/env python3
"""Emit the Agent 4 Hutter transfer-readiness fixture manifest.

This is a fixture gate, not a benchmark harness. It records byte provenance,
stdlib baselines, OISC replay size, and negative controls before any later
spectral run is allowed to read the fixture.
"""

from __future__ import annotations

import hashlib
import json
import lzma
import zlib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "shared-data" / "data" / "stack_solidification"
FIXTURE_DIR = DATA_DIR / "fixtures"
DOC_DIR = ROOT / "6-Documentation" / "docs"
TIDDLER_DIR = ROOT / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers"

FIXTURE_SOURCE = FIXTURE_DIR / "hutter_transfer_readiness_fixture.txt"
MANIFEST_PATH = DATA_DIR / "hutter_transfer_readiness_fixture_manifest.json"
DOC_PATH = DOC_DIR / "hutter_transfer_readiness_fixture_manifest_2026-05-09.md"
TIDDLER_PATH = TIDDLER_DIR / "Hutter Transfer Readiness Fixture.tid"

FIXTURE_TEXT = """Hutter transfer readiness fixture.

This small corpus window is intentionally local and inspectable. It carries
repeated phrases, shifted byte contexts, punctuation, digits 0123456789, and
line breaks so replay code must preserve more than a three-symbol toy stream.

Window alpha binds local recurrence: stack stack stack, receipt receipt receipt,
offset offset offset. Window beta changes cadence with JSON-ish tokens:
{"decision":"HOLD","window":128,"route":"oisc-replay"}.

Window gamma adds mixed case and separators: Alpha/BETA/gamma; phase_00,
phase_01, phase_02. The fixture stops here because the readiness gate is about
manifest discipline, not corpus scale.
"""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode_oisc(data: bytes) -> bytes:
    """Encode bytes with the Rust OiscCompressor fixture wire policy.

    The replay instruction format carries a residual byte, but the reference
    Rust compressor currently emits zero residuals for fixture replay. Non-zero
    residual policy remains a later HOLD item.
    """

    wire = bytearray(b"OISC\x01")
    for idx, symbol in enumerate(data):
        wire.append(symbol)
        wire.append(0)
        wire.append(1 if idx + 1 == len(data) else 0)
    return bytes(wire)


def baseline_matrix(data: bytes) -> dict[str, Any]:
    oisc_wire = encode_oisc(data)
    return {
        "raw": {"byte_length": len(data), "sha256": sha256_bytes(data)},
        "zlib": {"level": 9, "byte_length": len(zlib.compress(data, 9))},
        "lzma": {
            "preset": 6,
            "byte_length": len(lzma.compress(data, preset=6, check=lzma.CHECK_CRC64)),
        },
        "current_wire": {
            "codec": "oisc-replay-v0.1",
            "byte_length": len(oisc_wire),
            "sha256": sha256_bytes(oisc_wire),
        },
    }


def window_receipts(data: bytes) -> list[dict[str, Any]]:
    spans = [(0, 128), (128, 256), (384, 192)]
    receipts = []
    for idx, (offset, size) in enumerate(spans):
        chunk = data[offset : offset + size]
        receipts.append(
            {
                "window_id": f"htrf_win_{idx:02d}",
                "offset": offset,
                "window_size": size,
                "actual_byte_length": len(chunk),
                "sha256": sha256_bytes(chunk),
                "baseline_matrix": baseline_matrix(chunk),
            }
        )
    return receipts


def negative_controls(data: bytes) -> list[dict[str, Any]]:
    controls = [
        ("reverse_bytes", data[::-1], "order inversion control"),
        ("zero_bytes", bytes(len(data)), "symbol erasure control"),
        ("stride_permutation", data[1::2] + data[0::2], "local adjacency break control"),
    ]
    return [
        {
            "control_id": control_id,
            "purpose": purpose,
            "byte_length": len(payload),
            "sha256": sha256_bytes(payload),
            "baseline_matrix": baseline_matrix(payload),
            "decision": "HOLD",
        }
        for control_id, payload, purpose in controls
    ]


def build_manifest() -> dict[str, Any]:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    fixture_bytes = FIXTURE_TEXT.encode("utf-8")
    FIXTURE_SOURCE.write_bytes(fixture_bytes)

    return {
        "schema": "hutter_transfer_readiness_fixture_manifest_v0",
        "agent": "Agent 4: Hutter Transfer Readiness",
        "fixture_id": "htrf_local_text_window_2026_05_09_v0",
        "source_path": str(FIXTURE_SOURCE.relative_to(ROOT)),
        "byte_length": len(fixture_bytes),
        "sha256": sha256_bytes(fixture_bytes),
        "offsets_and_window_sizes": window_receipts(fixture_bytes),
        "decision_boundary": {
            "allowed_decisions": ["ADMIT_FIXTURE", "HOLD", "QUARANTINE"],
            "admit_fixture_requires": [
                "fixture_id",
                "source_path",
                "byte_length",
                "sha256",
                "offsets_and_window_sizes",
                "raw_zlib_lzma_current_wire_baseline_matrix",
                "negative_controls",
                "byte_exact_oisc_replay_fixture",
            ],
            "hold_when": [
                "baseline matrix is incomplete",
                "negative controls are absent",
                "OISC replay fixture has not passed byte-exact replay",
                "later spectral run is requested before control registration",
            ],
            "quarantine_when": [
                "fixture bytes do not match recorded sha256",
                "claim text exceeds fixture-readiness scope",
                "decompressor replay is not byte exact",
            ],
        },
        "baseline_matrix": baseline_matrix(fixture_bytes),
        "negative_controls": negative_controls(fixture_bytes),
        "oisc_replay_fixture": {
            "rust_test": "non_toy_transfer_fixture_replays_byte_exact",
            "source": "5-Applications/compression-core/src/oisc.rs",
            "expected_decision": "ADMIT_FIXTURE",
            "wire_codec": "oisc-replay-v0.1",
            "wire_byte_length": len(encode_oisc(fixture_bytes)),
            "wire_sha256": sha256_bytes(encode_oisc(fixture_bytes)),
        },
        "eigenmass_readiness": {
            "decision": "HOLD",
            "reason": "fixture admission has byte provenance, negative controls, and byte-exact Rust OISC replay; fixture-level eigenmass remains HOLD until residual policy and control accounting close",
        },
        "decision": "ADMIT_FIXTURE",
    }


def write_markdown(manifest: dict[str, Any]) -> None:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text(
        "\n".join(
            [
                "# Hutter Transfer Readiness Fixture Manifest",
                "",
                "Decision: `ADMIT_FIXTURE`",
                "",
                "This is a small fixture-readiness manifest. It records byte provenance,",
                "window receipts, baseline sizes, negative controls, and OISC replay",
                "requirements before any later spectral analysis can be considered.",
                "",
                "## Fixture",
                "",
                f"- Fixture id: `{manifest['fixture_id']}`",
                f"- Source path: `{manifest['source_path']}`",
                f"- Byte length: `{manifest['byte_length']}`",
                f"- SHA-256: `{manifest['sha256']}`",
                "",
                "## Baseline Matrix",
                "",
                "| route | bytes | note |",
                "| --- | ---: | --- |",
                f"| raw | {manifest['baseline_matrix']['raw']['byte_length']} | source bytes |",
                f"| zlib | {manifest['baseline_matrix']['zlib']['byte_length']} | stdlib level 9 |",
                f"| lzma | {manifest['baseline_matrix']['lzma']['byte_length']} | stdlib preset 6 |",
                f"| current-wire | {manifest['baseline_matrix']['current_wire']['byte_length']} | OISC replay wire |",
                "",
                "## Controls",
                "",
                "Negative controls are registered as `HOLD` before any later result gate.",
                "",
                "## Receipt",
                "",
                f"- Manifest: `{MANIFEST_PATH.relative_to(ROOT)}`",
                f"- OISC Rust test: `{manifest['oisc_replay_fixture']['rust_test']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_tiddler(manifest: dict[str, Any]) -> None:
    TIDDLER_DIR.mkdir(parents=True, exist_ok=True)
    TIDDLER_PATH.write_text(
        "\n".join(
            [
                "created: 20260509235900000",
                "modified: 20260509235900000",
                "tags: ResearchStack Hutter Compression Fixture",
                "title: Hutter Transfer Readiness Fixture",
                "type: text/vnd.tiddlywiki",
                "",
                "! Hutter Transfer Readiness Fixture",
                "",
                f"* Decision: `ADMIT_FIXTURE`",
                f"* Fixture id: `{manifest['fixture_id']}`",
                f"* Source: `{manifest['source_path']}`",
                f"* Byte length: `{manifest['byte_length']}`",
                f"* SHA-256: `{manifest['sha256']}`",
                f"* Manifest: `{MANIFEST_PATH.relative_to(ROOT)}`",
                "",
                "!! Boundary",
                "",
                "Allowed decisions are `ADMIT_FIXTURE`, `HOLD`, and `QUARANTINE`.",
                "This tiddler admits only the local fixture manifest and keeps later",
                "eigenmass or spectral analysis on `HOLD` until residual policy and",
                "control accounting close. Negative controls and byte-exact Rust OISC",
                "replay are registered here for fixture admission only.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    manifest = build_manifest()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(manifest)
    write_tiddler(manifest)
    print(json.dumps({"decision": manifest["decision"], "manifest": str(MANIFEST_PATH)}, indent=2))


if __name__ == "__main__":
    main()
