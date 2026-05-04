#!/usr/bin/env python3
"""Derive a deterministic trinary VM program from an input file."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

WIDTH = 6
TRIT_MAP = {0: -1, 1: 0, 2: 1}
SCHEMA = "trinary_vm_derivation_v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def byte_to_trits(value: int) -> list[int]:
    digits = [0] * WIDTH
    remaining = value
    for index in range(WIDTH - 1, -1, -1):
        remaining, digit = divmod(remaining, 3)
        digits[index] = TRIT_MAP[digit]
    return digits


def derive_program_bytes(data: bytes) -> list[dict[str, object]]:
    program: list[dict[str, object]] = []
    for value in data:
        for index, trit in enumerate(byte_to_trits(value)):
            program.append(
                {
                    "op": "SET",
                    "target": "alpha",
                    "index": index,
                    "value": trit,
                }
            )
        program.append(
            {
                "op": "SHIFT",
                "target": "alpha",
                "direction": "right",
            }
        )
    return program


def derive_payload(input_path: Path) -> dict[str, object]:
    data = input_path.read_bytes()
    return {
        "schema": SCHEMA,
        "input_path": str(input_path),
        "input_size_bytes": len(data),
        "input_sha256": sha256_file(input_path),
        "subregisters": {
            "alpha": [0] * WIDTH,
            "beta": [0] * WIDTH,
        },
        "program": derive_program_bytes(data),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input file to derive from.")
    parser.add_argument("--output", required=True, help="Path to write the JSON program.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    payload = derive_payload(input_path)

    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote derived program to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
