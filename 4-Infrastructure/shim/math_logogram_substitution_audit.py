#!/usr/bin/env python3
"""Audit substitution reversibility for the math logogram surface compiler.

This is an acceptance harness, not the compiler itself.  It checks whether a
canonicalized expression can be reconstructed from the emitted glyph payload and
which residual sidecars are required to make that substitution lawful.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import math_logogram_surface_builder as surface


SCHEMA = "math_logogram_substitution_audit_v1"
DEFAULT_RECEIPT = Path(__file__).with_name(
    "math_logogram_substitution_audit_receipt.json"
)


FIXTURES: list[dict[str, Any]] = [
    {
        "id": "literal_atom",
        "kind": "symbolic_logogram",
        "source": "x",
        "expected_classes": ["single_char_literal"],
    },
    {
        "id": "known_command_short",
        "kind": "latex_math",
        "source": r"\frac{x}{y}",
        "expected_classes": [
            "known_command",
            "known_symbol",
            "single_char_literal",
            "known_symbol",
            "known_symbol",
            "single_char_literal",
            "known_symbol",
        ],
    },
    {
        "id": "unknown_multichar_identifier",
        "kind": "symbolic_logogram",
        "source": "alphaBeta + z",
        "expected_classes": [
            "hashed_multichar_residual",
            "known_symbol",
            "single_char_literal",
        ],
    },
    {
        "id": "long_truncation",
        "kind": "latex_math",
        "source": r"\partial_t u + u \partial_x u - \nu \partial_{xx} u = 0",
        "expected_classes_prefix": [
            "known_command",
            "known_symbol",
            "single_char_literal",
            "single_char_literal",
        ],
    },
    {
        "id": "semantic_tear",
        "kind": "symbolic_logogram",
        "source": r"torsion(A,B) > max \Rightarrow tear(A,B)",
        "expected_regime": "horrible_manifold_tearing",
    },
]


def glyph_candidate_map() -> dict[int, list[str]]:
    """Return every token spelling that can produce each glyph byte."""

    candidates: dict[int, set[str]] = {}

    def add(glyph: int, token: str) -> None:
        candidates.setdefault(glyph & 0xFF, set()).add(token)

    for token, glyph in surface.COMMAND_GLYPHS.items():
        add(glyph, token)
    for token, glyph in surface.SYMBOL_GLYPHS.items():
        add(glyph, token)
    for value in range(0x20, 0x7F):
        add(value, chr(value))
    return {glyph: sorted(tokens) for glyph, tokens in candidates.items()}


GLYPH_CANDIDATES = glyph_candidate_map()


def classify_token(token: str) -> str:
    if token in surface.COMMAND_GLYPHS:
        return "known_command"
    if token in surface.SYMBOL_GLYPHS:
        return "known_symbol"
    if len(token) == 1:
        return "single_char_literal"
    return "hashed_multichar_residual"


def canonical_token_string(cells: list[dict[str, Any]]) -> str:
    return " ".join(str(cell["token"]) for cell in cells)


def compression_ratio(raw_bytes: int, payload_bytes: int) -> float | None:
    if payload_bytes == 0:
        return None
    return raw_bytes / payload_bytes


def compact_json_bytes(value: Any) -> int:
    return len(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )


def packed_sidecar_estimate_bytes(entries: list[dict[str, Any]]) -> int:
    """Estimate a simple binary sidecar envelope.

    This is not a final codec.  It prices each correction as:
    opcode + token index + glyph/candidate metadata + optional token bytes.
    The JSON receipt stays verbose for inspection; this estimate is the
    hardware-packer target to beat.
    """

    total = 0
    for entry in entries:
        op = str(entry["op"])
        token = str(entry.get("token", ""))
        token_bytes = len(token.encode("utf-8"))
        if op == "select_candidate":
            total += 4
        elif op == "literal_token":
            total += 3 + token_bytes
        elif op == "append_truncated_cell":
            total += 5 + token_bytes
        else:
            total += 4 + token_bytes
    return total


def rehydrate_with_sidecar(
    payload_tokens: list[str], entries: list[dict[str, Any]]
) -> str:
    tokens = list(payload_tokens)
    for entry in sorted(entries, key=lambda item: int(item["index"])):
        index = int(entry["index"])
        op = str(entry["op"])
        token = str(entry.get("token", ""))
        if op in {"select_candidate", "literal_token"}:
            while len(tokens) <= index:
                tokens.append("<missing>")
            tokens[index] = token
        elif op == "append_truncated_cell":
            while len(tokens) < index:
                tokens.append("<missing>")
            if len(tokens) == index:
                tokens.append(token)
            else:
                tokens[index] = token
    return " ".join(tokens)


def audit_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    source_text = str(fixture["source"])
    canon = surface.canonicalize(source_text)
    cells = list(canon["cells"])
    payload = surface.pack_glyph_payload(cells)
    metrics = surface.compression_metrics(source_text, canon["canonical"], payload)
    semantic_regime = surface.classify_regime(canon["canonical"], cells)

    classifications: list[dict[str, Any]] = []
    residual_reasons: list[str] = []
    sidecar_entries: list[dict[str, Any]] = []
    payload_only_tokens: list[str] = []
    payload_only_exact = True

    for cell in cells:
        token = str(cell["token"])
        glyph = int(cell["glyph_id"]) & 0xFF
        substitution_class = classify_token(token)
        candidates = GLYPH_CANDIDATES.get(glyph, [])
        is_hashed = substitution_class == "hashed_multichar_residual"
        is_ambiguous = len(candidates) != 1 or token not in candidates

        if is_hashed:
            residual_reasons.append(f"hashed_multichar_token:{token}")
            sidecar_entries.append(
                {
                    "index": cell["index"],
                    "op": "literal_token",
                    "token": token,
                    "glyph_id": glyph,
                    "reason": "hashed_multichar_token",
                }
            )
            payload_only_exact = False
        elif is_ambiguous:
            residual_reasons.append(f"ambiguous_glyph:{glyph:02x}:{token}")
            sidecar_entries.append(
                {
                    "index": cell["index"],
                    "op": "select_candidate",
                    "token": token,
                    "glyph_id": glyph,
                    "candidates": candidates,
                    "reason": "ambiguous_glyph",
                }
            )
            payload_only_exact = False

        payload_only_tokens.append(candidates[0] if len(candidates) == 1 else "<residual>")
        classifications.append(
            {
                "index": cell["index"],
                "token": token,
                "glyph_id": glyph,
                "class": substitution_class,
                "payload_candidates": candidates,
                "payload_only_reversible": not is_hashed and not is_ambiguous,
            }
        )

    if len(cells) > len(payload):
        payload_only_exact = False
        residual_reasons.append(
            f"payload_truncated:{len(cells) - len(payload)}_tokens"
        )
        for cell in cells[len(payload) :]:
            sidecar_entries.append(
                {
                    "index": cell["index"],
                    "op": "append_truncated_cell",
                    "token": cell["token"],
                    "glyph_id": int(cell["glyph_id"]) & 0xFF,
                    "kind": cell["kind"],
                    "depth": cell["depth"],
                    "reason": "payload_truncated",
                }
            )

    sidecar_cells = cells[: len(payload)]
    payload_cell_tokens = [str(cell["token"]) for cell in sidecar_cells]
    sidecar_reconstructed = rehydrate_with_sidecar(
        payload_cell_tokens, sidecar_entries
    )
    payload_reconstructed = " ".join(payload_only_tokens[: len(payload)])
    canonical_round_trip_with_cells = sidecar_reconstructed == str(canon["canonical"])
    payload_only_round_trip = (
        payload_only_exact
        and not len(cells) > len(payload)
        and payload_reconstructed == str(canon["canonical"])
    )

    expected_failures: list[str] = []
    expected_classes = fixture.get("expected_classes")
    if expected_classes is not None:
        observed = [entry["class"] for entry in classifications]
        if observed != expected_classes:
            expected_failures.append(
                f"expected_classes mismatch: observed {observed}"
            )
    expected_prefix = fixture.get("expected_classes_prefix")
    if expected_prefix is not None:
        observed_prefix = [entry["class"] for entry in classifications[: len(expected_prefix)]]
        if observed_prefix != expected_prefix:
            expected_failures.append(
                f"expected_classes_prefix mismatch: observed {observed_prefix}"
            )
    expected_regime = fixture.get("expected_regime")
    if expected_regime is not None and semantic_regime != expected_regime:
        expected_failures.append(
            f"expected_regime mismatch: observed {semantic_regime}"
        )

    if semantic_regime == "horrible_manifold_tearing":
        decision = "QUARANTINE"
    elif payload_only_round_trip:
        decision = "ACCEPT"
    else:
        decision = "HOLD"

    substitution_counts = Counter(entry["class"] for entry in classifications)
    payload_bound = len(payload) <= 16
    residual = bool(residual_reasons)
    sidecar = {
        "schema": "math_logogram_sidecar_v1",
        "encoding": "structured_token_corrections",
        "rehydration_rule": (
            "Start from glyph payload; apply candidate selections, literal "
            "tokens, and truncated cell appends by token index to recover the "
            "canonical token string."
        ),
        "entries": sidecar_entries,
    }
    sidecar_bytes = compact_json_bytes(sidecar) if sidecar_entries else 0
    sidecar_packed_estimate = packed_sidecar_estimate_bytes(sidecar_entries)
    total_payload_bytes = len(payload) + sidecar_bytes
    total_packed_payload_bytes = len(payload) + sidecar_packed_estimate
    return {
        "id": fixture["id"],
        "kind": fixture["kind"],
        "source": source_text,
        "source_hash": surface.sha256_text(source_text),
        "canonical": canon["canonical"],
        "canonical_hash": canon["canonical_hash"],
        "token_count": canon["token_count"],
        "payload_hex": payload.hex(),
        "payload_len": len(payload),
        "payload_bound": payload_bound,
        "substitution_receipt": surface.substitution_receipt(payload),
        "substitution_counts": dict(sorted(substitution_counts.items())),
        "substitutions": classifications,
        "round_trip": {
            "scope": "canonical_token_string",
            "source_byte_exact": source_text == canon["canonical"],
            "payload_only": payload_only_round_trip,
            "with_display_cell_sidecar": canonical_round_trip_with_cells,
            "payload_only_reconstructed": payload_reconstructed,
            "sidecar_reconstructed": sidecar_reconstructed,
        },
        "compression": {
            **metrics,
            "compression_ratio_raw_to_payload": compression_ratio(
                int(metrics["raw_bytes"]), len(payload)
            ),
            "sidecar_bytes_json_compact": sidecar_bytes,
            "sidecar_bytes_packed_estimate": sidecar_packed_estimate,
            "payload_plus_sidecar_bytes": total_payload_bytes,
            "payload_plus_packed_sidecar_bytes": total_packed_payload_bytes,
            "compression_ratio_raw_to_payload_plus_sidecar": compression_ratio(
                int(metrics["raw_bytes"]), total_payload_bytes
            ),
            "compression_ratio_raw_to_payload_plus_packed_sidecar": compression_ratio(
                int(metrics["raw_bytes"]), total_packed_payload_bytes
            ),
        },
        "residual": residual,
        "residual_reasons": sorted(set(residual_reasons)),
        "residual_sidecar": sidecar if sidecar_entries else None,
        "semantic_regime": semantic_regime,
        "decision": decision,
        "gcc_receipt_shape": {
            "compression_ratio": compression_ratio(int(metrics["raw_bytes"]), len(payload)),
            "round_trip": payload_only_round_trip,
            "residual": sorted(set(residual_reasons)) or None,
        },
        "expectation_failures": expected_failures,
    }


def build_receipt() -> dict[str, Any]:
    tests = [audit_fixture(fixture) for fixture in FIXTURES]
    failures = [
        f"{test['id']}:{failure}"
        for test in tests
        for failure in test["expectation_failures"]
    ]
    accept_count = sum(1 for test in tests if test["decision"] == "ACCEPT")
    hold_count = sum(1 for test in tests if test["decision"] == "HOLD")
    quarantine_count = sum(1 for test in tests if test["decision"] == "QUARANTINE")
    payload_only_round_trip_count = sum(
        1 for test in tests if test["round_trip"]["payload_only"]
    )
    sidecar_round_trip_count = sum(
        1 for test in tests if test["round_trip"]["with_display_cell_sidecar"]
    )
    all_payload_only_round_trip = payload_only_round_trip_count == len(tests)
    raw_bytes = sum(int(test["compression"]["raw_bytes"]) for test in tests)
    payload_bytes = sum(
        int(test["compression"]["surface_payload_bytes"]) for test in tests
    )
    json_sidecar_bytes = sum(
        int(test["compression"]["sidecar_bytes_json_compact"]) for test in tests
    )
    packed_sidecar_estimate_bytes = sum(
        int(test["compression"]["sidecar_bytes_packed_estimate"]) for test in tests
    )
    return {
        "schema": SCHEMA,
        "claim_boundary": (
            "This audit proves detection of substitution residuals for the "
            "fixture set. It does not prove global losslessness for all math "
            "or chemistry strings."
        ),
        "compiler": "4-Infrastructure/shim/math_logogram_surface_builder.py",
        "summary": {
            "fixture_count": len(tests),
            "expectation_failures": failures,
            "payload_only_round_trip_count": payload_only_round_trip_count,
            "all_payload_only_round_trip": all_payload_only_round_trip,
            "sidecar_round_trip_count": sidecar_round_trip_count,
            "sidecar_required_count": len(tests) - payload_only_round_trip_count,
            "accept_count": accept_count,
            "hold_count": hold_count,
            "quarantine_count": quarantine_count,
            "raw_bytes": raw_bytes,
            "payload_bytes": payload_bytes,
            "json_sidecar_bytes": json_sidecar_bytes,
            "packed_sidecar_estimate_bytes": packed_sidecar_estimate_bytes,
            "compression_ratio_raw_to_payload": compression_ratio(
                raw_bytes, payload_bytes
            ),
            "compression_ratio_raw_to_payload_plus_json_sidecar": compression_ratio(
                raw_bytes, payload_bytes + json_sidecar_bytes
            ),
            "compression_ratio_raw_to_payload_plus_packed_sidecar_estimate": compression_ratio(
                raw_bytes, payload_bytes + packed_sidecar_estimate_bytes
            ),
            "audit_passed": not failures,
        },
        "tests": tests,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit math logogram substitution reversibility."
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        default=DEFAULT_RECEIPT,
        help="Path for the JSON audit receipt.",
    )
    args = parser.parse_args()

    receipt = build_receipt()
    args.receipt.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt["summary"], indent=2, sort_keys=True))
    return 0 if receipt["summary"]["audit_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
