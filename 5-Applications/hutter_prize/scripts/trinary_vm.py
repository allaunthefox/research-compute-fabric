#!/usr/bin/env python3
"""Minimal deterministic trinary VM with subregister-bounded operations."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path

TRITS = (-1, 0, 1)


def clamp_trit(value: int) -> int:
    if value < -1:
        return -1
    if value > 1:
        return 1
    return value


def require_trit(value: int, *, field: str) -> int:
    if value not in TRITS:
        raise ValueError(f"{field} must be one of {TRITS}, got {value}")
    return value


class TrinaryVM:
    def __init__(self, subregisters: dict[str, list[int]]):
        self.state: dict[str, list[int]] = {}
        for name, cells in subregisters.items():
            self.state[name] = [require_trit(value, field=f"{name} cell") for value in cells]
        self.trace: list[dict[str, object]] = []

    def require_target(self, name: str) -> list[int]:
        if name not in self.state:
            raise KeyError(f"Unknown subregister: {name}")
        return self.state[name]

    def execute(self, instruction: dict[str, object], *, step: int) -> None:
        op = str(instruction["op"]).upper()
        target_name = str(instruction["target"])
        target = self.require_target(target_name)
        before = deepcopy(target)

        if op == "SET":
            index = int(instruction["index"])
            value = require_trit(int(instruction["value"]), field="value")
            target[index] = value
        elif op == "ADD":
            index = int(instruction["index"])
            value = require_trit(int(instruction["value"]), field="value")
            target[index] = clamp_trit(target[index] + value)
        elif op == "SUB":
            index = int(instruction["index"])
            value = require_trit(int(instruction["value"]), field="value")
            target[index] = clamp_trit(target[index] - value)
        elif op == "SHIFT":
            direction = str(instruction["direction"]).lower()
            if not target:
                raise ValueError(f"Cannot shift empty subregister: {target_name}")
            if direction == "left":
                rotated = target[1:] + target[:1]
            elif direction == "right":
                rotated = target[-1:] + target[:-1]
            else:
                raise ValueError(f"Invalid shift direction: {direction}")
            target[:] = rotated
        elif op == "MERGE":
            source_name = str(instruction["source"])
            source = self.require_target(source_name)
            if len(source) != len(target):
                raise ValueError("MERGE requires equal-width subregisters")
            for idx, source_value in enumerate(source):
                target[idx] = clamp_trit(target[idx] + source_value)
        elif op == "PROJECT":
            source_name = str(instruction["source"])
            source = self.require_target(source_name)
            start = int(instruction["source_start"])
            length = int(instruction["length"])
            target_start = int(instruction["target_start"])
            segment = source[start : start + length]
            if len(segment) != length:
                raise ValueError("PROJECT source slice is out of range")
            end = target_start + length
            if end > len(target):
                raise ValueError("PROJECT target slice is out of range")
            target[target_start:end] = segment
        elif op == "W":
            index = int(instruction["index"])
            weight = int(instruction["weight"])
            target[index] = clamp_trit(target[index] * weight)
        else:
            raise ValueError(f"Unsupported operation: {op}")

        self.trace.append(
            {
                "step": step,
                "op": op,
                "target": target_name,
                "args": {
                    key: value
                    for key, value in instruction.items()
                    if key not in {"op", "target"}
                },
                "before": before,
                "after": deepcopy(target),
            }
        )

    def run(self, program: list[dict[str, object]]) -> dict[str, object]:
        for step, instruction in enumerate(program):
            self.execute(instruction, step=step)
        return {
            "final_state": self.state,
            "trace": self.trace,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program", required=True, help="Path to a JSON program document.")
    parser.add_argument(
        "--output",
        help="Optional path to write the resulting JSON trace. Defaults to stdout only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    program_path = Path(args.program).resolve()
    payload = json.loads(program_path.read_text(encoding="utf-8"))
    vm = TrinaryVM(payload["subregisters"])
    result = vm.run(payload["program"])
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        Path(args.output).resolve().write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
