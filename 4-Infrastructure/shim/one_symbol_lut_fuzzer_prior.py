#!/usr/bin/env python3
"""Emit one-symbol LUT fuzzer generator priors.

The goal is not to claim compression. The goal is to preserve a finite catalog
of deterministic generator families that can fuzz a compression ratio by
collapsing a large explicit array into a small replay law plus residual.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "shared-data" / "data" / "one_symbol_lut_fuzzer"


@dataclass(frozen=True)
class GeneratorPrior:
    packet_id: str
    name: str
    family: str
    formula: str
    generating_function: str
    replay_law: str
    stress_role: str
    failure_mode: str
    sample: list[str]
    decision: str


def stable_hash(obj: object) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def fixed_blocks(values: list[int], width: int) -> list[str]:
    return [str(v).zfill(width)[-width:] for v in values]


def arithmetic_values(n: int) -> list[int]:
    return list(range(n))


def triangular_values(n: int) -> list[int]:
    return [i * (i + 1) // 2 for i in range(n)]


def square_values(n: int) -> list[int]:
    return [i * i for i in range(n)]


def cube_values(n: int) -> list[int]:
    return [i * i * i for i in range(n)]


def geometric_values(k: int, n: int) -> list[int]:
    v = 1
    out: list[int] = []
    for _ in range(n):
        out.append(v)
        v *= k
    return out


def fibonacci_values(n: int) -> list[int]:
    a, b = 1, 1
    out: list[int] = []
    for _ in range(n):
        out.append(a)
        a, b = b, a + b
    return out


def lucas_values(n: int) -> list[int]:
    a, b = 2, 1
    out: list[int] = []
    for _ in range(n):
        out.append(a)
        a, b = b, a + b
    return out


def repetend_digits(p: int, limit: int) -> str:
    seen: dict[int, int] = {}
    rem = 1 % p
    digits: list[str] = []
    while rem and rem not in seen and len(digits) < limit:
        seen[rem] = len(digits)
        rem *= 10
        digits.append(str(rem // p))
        rem %= p
    return "".join(digits)


def chunk_string(text: str, width: int, count: int) -> list[str]:
    padded = text + ("0" * width)
    return [padded[i : i + width].ljust(width, "0") for i in range(0, width * count, width)]


def champernowne_digits(limit: int) -> str:
    out = []
    i = 1
    while len("".join(out)) < limit:
        out.append(str(i))
        i += 1
    return "".join(out)[:limit]


def make_packet(
    packet_id: str,
    name: str,
    family: str,
    formula: str,
    generating_function: str,
    replay_law: str,
    stress_role: str,
    failure_mode: str,
    sample_builder: Callable[[], list[str]],
) -> GeneratorPrior:
    return GeneratorPrior(
        packet_id=packet_id,
        name=name,
        family=family,
        formula=formula,
        generating_function=generating_function,
        replay_law=replay_law,
        stress_role=stress_role,
        failure_mode=failure_mode,
        sample=sample_builder(),
        decision="HOLD",
    )


def build_packets() -> list[GeneratorPrior]:
    return [
        make_packet(
            "OSLF.PRIOR.ARITHMETIC_LADDER.0001",
            "Arithmetic progression ladder",
            "formal_power_series",
            "a_n = n",
            "x / (1 - x)^2",
            "emit start + n * stride in fixed-width slots",
            "boundary stressor for skipped/carry-swallowed coordinates",
            "carry propagation or wrap requires residual exceptions",
            lambda: fixed_blocks(arithmetic_values(16), 3),
        ),
        make_packet(
            "OSLF.PRIOR.TRIANGULAR.0001",
            "Triangular number ladder",
            "formal_power_series",
            "a_n = n(n+1)/2",
            "x / (1 - x)^3",
            "emit second-order cumulative count",
            "acceleration-density stressor for table and offset manifolds",
            "slot overflow creates overlapping blocks and residual debt",
            lambda: fixed_blocks(triangular_values(14), 4),
        ),
        make_packet(
            "OSLF.PRIOR.SQUARES.0001",
            "Square number ladder",
            "formal_power_series",
            "a_n = n^2",
            "x(1+x) / (1 - x)^3",
            "emit polynomial law value for index n",
            "curvature stressor for index surfaces and manifold-distance fields",
            "polynomial degree mismatch causes residual expansion",
            lambda: fixed_blocks(square_values(14), 4),
        ),
        make_packet(
            "OSLF.PRIOR.CUBES.0001",
            "Cube number ladder",
            "formal_power_series",
            "a_n = n^3",
            "x(1+4x+x^2) / (1 - x)^4",
            "emit third-order polynomial law value for index n",
            "higher-order density stressor for volume-like coordinate arrays",
            "slot overflow and degree overfit require explicit residuals",
            lambda: fixed_blocks(cube_values(12), 5),
        ),
        make_packet(
            "OSLF.PRIOR.GEOMETRIC_2.0001",
            "Power-of-two geometric generator",
            "geometric_series",
            "a_n = 2^n",
            "1 / (1 - 2x)",
            "multiply previous value by two",
            "exponential blowup stressor for slot overlap and entropy cliffs",
            "growth exceeds fixed slot width quickly and forces carry residuals",
            lambda: fixed_blocks(geometric_values(2, 12), 5),
        ),
        make_packet(
            "OSLF.PRIOR.FIBONACCI.0001",
            "Fibonacci recurrence generator",
            "linear_recurrence",
            "a_n = a_{n-1} + a_{n-2}",
            "x / (1 - x - x^2)",
            "emit recurrence with initial state 1,1",
            "state-transition stressor for biology-like branching and ratio drift",
            "wrong initial state or mutated coefficients produce Lucas-like residual",
            lambda: fixed_blocks(fibonacci_values(14), 4),
        ),
        make_packet(
            "OSLF.PRIOR.LUCAS_MUTATION.0001",
            "Lucas recurrence mutation generator",
            "linear_recurrence",
            "a_n = a_{n-1} + a_{n-2}, initial 2,1",
            "(2 - x) / (1 - x - x^2)",
            "emit Fibonacci-law recurrence with different initial state",
            "mutation basin test for recurrence classifier stability",
            "confusing Fibonacci and Lucas requires residual or distinct law ID",
            lambda: fixed_blocks(lucas_values(14), 4),
        ),
        make_packet(
            "OSLF.PRIOR.CYCLIC_PRIME_97.0001",
            "Prime reciprocal cyclic repetend",
            "cyclic_prime",
            "digits(1 / 97)",
            "1 / p where p has long decimal period",
            "emit repetend digits modulo period with rotation offset",
            "rotational-invariance stressor for LUT windows and FPGA O(1) paths",
            "non-full-period primes or wrong phase offsets require residual repair",
            lambda: chunk_string(repetend_digits(97, 96), 4, 12),
        ),
        make_packet(
            "OSLF.PRIOR.REPUNIT_REPEAT.0001",
            "Repunit repeat generator",
            "repunit",
            "block / (10^w - 1)",
            "c / (B - 1)",
            "repeat a fixed block indefinitely or for declared length",
            "header-tax baseline for obvious repetition",
            "not useful when explicit run-length coding is cheaper",
            lambda: ["123"] * 12,
        ),
        make_packet(
            "OSLF.PRIOR.CHAMPERNOWNE_DECOY.0001",
            "Champernowne-style counting-string decoy",
            "concatenation_law",
            "123456789101112...",
            "not rational in the simple finite recurrence sense",
            "concatenate positive integers in the declared radix",
            "pseudo-normal decoy: broad digit coverage from a tiny law",
            "normal-looking windows can defeat naive entropy heuristics",
            lambda: chunk_string(champernowne_digits(48), 4, 12),
        ),
    ]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    packets = build_packets()
    packet_dicts = [asdict(p) for p in packets]

    packets_path = OUT_DIR / "one_symbol_lut_fuzzer_packets.jsonl"
    table_path = OUT_DIR / "one_symbol_lut_fuzzer_table.csv"
    receipt_path = OUT_DIR / "one_symbol_lut_fuzzer_receipt.json"

    with packets_path.open("w", encoding="utf-8") as fh:
        for packet in packet_dicts:
            fh.write(json.dumps(packet, sort_keys=True) + "\n")

    with table_path.open("w", encoding="utf-8") as fh:
        fh.write("packet_id,name,family,generating_function,stress_role,decision\n")
        for packet in packets:
            fields = [
                packet.packet_id,
                packet.name,
                packet.family,
                packet.generating_function,
                packet.stress_role,
                packet.decision,
            ]
            fh.write(",".join('"' + f.replace('"', '""') + '"' for f in fields) + "\n")

    receipt = {
        "schema": "one_symbol_lut_fuzzer_receipt_v1",
        "packet_count": len(packets),
        "families": sorted({p.family for p in packets}),
        "decision": "HOLD",
        "packets_sha256": stable_hash(packet_dicts),
        "claim_boundary": (
            "Generator-law fuzzing prior only. One-symbol collapse promotes only "
            "when generator bytes plus residual and receipt beat the explicit array."
        ),
    }
    receipt["receipt_hash"] = stable_hash(receipt)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
