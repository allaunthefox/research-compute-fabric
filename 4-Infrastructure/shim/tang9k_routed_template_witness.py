#!/usr/bin/env python3
"""Witness routed math templates through the Tang9K symbol surface.

This converts top entries from eigen_solved_math_router.py into short
Surface-0 payloads. The FPGA still only witnesses substitution/hash/counts;
the host owns the full template ranking and codec logic.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


DEFAULT_ROUTER = Path("4-Infrastructure/shim/eigen_solved_math_router_compression.json")
SURFACE_PATH = Path("4-Infrastructure/shim/tang9k_hutter_symbol_surface.py")


def load_surface_module():
    spec = importlib.util.spec_from_file_location("tang9k_hutter_symbol_surface", SURFACE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SURFACE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def template_payload(entry: dict[str, Any], max_len: int = 16) -> bytes:
    name = str(entry.get("model_name") or entry.get("family") or "template")
    # Keep a readable bank-local token: uppercase, underscores become spaces,
    # punctuation drops. This intentionally targets the tiny hardware LUT.
    normalized = []
    for ch in name.upper().replace("_", " "):
        if ch.isalnum() or ch == " ":
            normalized.append(ch)
    token = "".join(normalized).strip() or "TEMPLATE"
    return token.encode("ascii", "ignore")[:max_len]


def witness_entry(surface, entry: dict[str, Any], seq: int, port: str | None, baud: int, retries: int) -> dict[str, Any]:
    payload = template_payload(entry)
    frame = surface.build_frame(seq, payload)
    expected = surface.receipt_for_payload(payload)
    result = {
        "schema": "tang9k_routed_template_witness_v1",
        "model_name": entry.get("model_name"),
        "family": entry.get("family"),
        "evidence_tier": entry.get("evidence_tier"),
        "routed_score": entry.get("routed_score"),
        "payload_ascii": payload.decode("ascii", "replace"),
        "payload_hex": payload.hex(),
        "frame_hex": frame.hex(),
        "expected": expected,
        "expected_led_reservoir": surface.led_reservoir_address(
            surface.pbacs_cmyk_state_for_payload(payload), expected["mapped_count"]
        ),
    }
    if port:
        raw = surface.send_serial(port, baud, frame, retries=retries)
        result["hardware_receipt_hex"] = raw.hex()
        if raw:
            try:
                parsed = surface.parse_receipt(raw)
                result["hardware_receipt"] = parsed
                result["hardware_led_reservoir"] = surface.led_reservoir_address(
                    surface.pbacs_cmyk_state_for_payload(payload), parsed["mapped_count"]
                )
                result["hardware_matches_expected"] = (
                    parsed["status"] == 0
                    and parsed["hash16"] == expected["hash16"]
                    and parsed["mapped_count"] == expected["mapped_count"]
                    and parsed["literal_count"] == expected["literal_count"]
                )
            except ValueError as exc:
                result["hardware_receipt"] = None
                result["hardware_matches_expected"] = False
                result["hardware_note"] = str(exc)
        else:
            result["hardware_receipt"] = None
            result["hardware_matches_expected"] = False
            result["hardware_note"] = "no UART receipt received"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--router-json", type=Path, default=DEFAULT_ROUTER)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--seq-base", type=lambda value: int(value, 0), default=0xE0)
    parser.add_argument("--port")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    router = json.loads(args.router_json.read_text(encoding="utf-8"))
    surface = load_surface_module()
    witnesses = []
    for index, entry in enumerate(router.get("entries", [])[: args.limit]):
        witnesses.append(
            witness_entry(
                surface=surface,
                entry=entry,
                seq=(args.seq_base + index) & 0xFF,
                port=args.port,
                baud=args.baud,
                retries=args.retries,
            )
        )
    bundle = {
        "schema": "tang9k_routed_template_witness_bundle_v1",
        "claim_boundary": "FPGA witnesses compact template tokens only; ranking and model validity remain host-side.",
        "router_json": str(args.router_json),
        "witness_count": len(witnesses),
        "hardware_count": sum(1 for item in witnesses if item.get("hardware_matches_expected")),
        "witnesses": witnesses,
    }
    text = json.dumps(bundle, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
