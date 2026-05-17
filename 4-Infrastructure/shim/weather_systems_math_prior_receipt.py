#!/usr/bin/env python3
"""Receipt generator for weather-systems borrowed math.

This is a no-download, tiny-fixture prior for borrowing weather-system
mathematics into the reconstruction-core stack: conservative transport,
shallow-water/PV-style invariants, data-assimilation innovation, ensemble
spread, and forecast residual growth. It is not an NWP model, weather forecast,
ERA5 ingest, or benchmark result.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "weather_systems_math_prior"
RECEIPT = OUT_DIR / "weather_systems_math_prior_receipt.json"
TABLE = OUT_DIR / "weather_systems_math_prior_table.jsonl"
SUMMARY = OUT_DIR / "weather_systems_math_prior_receipt.md"
SOURCE_MANIFEST = REPO / "6-Documentation" / "docs" / "provenance" / "WEATHER_SYSTEMS_MATH_PRIOR_SOURCES.cff"


OBJECTIVE_PACKET = {
    "name": "Weather Systems Borrowed-Math Prior",
    "core_map": "weather_state -> transport/replay kernel + residual -> repaired state",
    "lossless_gate": "Repair(Replay(K,Theta,Pi),R) == S",
    "borrowed_math_surfaces": [
        "primitive-equation dynamics",
        "finite-volume conservative transport",
        "shallow-water layer invariants",
        "potential-vorticity-style route constraints",
        "data-assimilation innovation",
        "ensemble spread / forecast residual growth",
    ],
    "weather_codec_score": (
        "J_weather = |D|+|K|+|Theta|+|Pi|+|R|+|Receipts| "
        "+ lambda_m mass_drift + lambda_c CFL_excess + lambda_i innovation_norm "
        "+ lambda_e ensemble_spread + lambda_r residual_growth"
    ),
    "admission": "exact repair and positive byte law; weather terms are diagnostics unless normalized",
    "native_phrase": (
        "Weather math is useful as a replay-stability and residual-growth filter, "
        "not as a forecast or data-ingest claim."
    ),
}


SOURCE_SURFACES = [
    {
        "name": "ECMWF IFS documentation",
        "url": "https://www.ecmwf.int/en/publications/ifs-documentation",
        "role": "primitive equations, dynamics, and data-assimilation reference surface",
    },
    {
        "name": "ECMWF ERA5",
        "url": "https://www.ecmwf.int/en/forecasts/dataset/ecmwf-reanalysis-v5",
        "role": "reanalysis and assimilation route prior; no data vendored",
    },
    {
        "name": "NOAA NCEI Numerical Weather Prediction archive",
        "url": "https://www.ncei.noaa.gov/products/weather-climate-models/numerical-weather-prediction",
        "role": "NWP data-family route prior; no data vendored",
    },
    {
        "name": "NOAA/GFDL FV3 dynamical core",
        "url": "https://www.gfdl.noaa.gov/fv3",
        "role": "finite-volume cubed-sphere and shallow-water-layer route prior",
    },
    {
        "name": "NOAA/GFDL FV3 key components",
        "url": "https://www.gfdl.noaa.gov/fv3/fv3-key-components/",
        "role": "finite-volume conservation and layer dynamics reference surface",
    },
]


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    kind: str
    length: int
    theta: dict[str, Any]
    negative_control: bool
    notes: str


FIXTURES = [
    Fixture(
        fixture_id="periodic_transport_mass_admit",
        kind="periodic_transport",
        length=384,
        theta={"pattern": [1000, 1002, 1005, 1002], "shift": 1, "u": 0.25, "dx": 1.0, "dt": 1.0},
        negative_control=False,
        notes="Conservative periodic transport replays exactly and preserves total mass.",
    ),
    Fixture(
        fixture_id="wrong_boundary_residual_hold",
        kind="wrong_boundary_transport",
        length=384,
        theta={"pattern": [1000, 1002, 1005, 1002], "shift": 1, "u": 0.25, "dx": 1.0, "dt": 1.0},
        negative_control=True,
        notes="Wrong boundary condition creates a repairable but held residual surface.",
    ),
    Fixture(
        fixture_id="assimilation_innovation_hold",
        kind="assimilation_update",
        length=24,
        theta={"background": 1000.0, "observation": 1008.0, "gain": 0.25, "count": 24},
        negative_control=False,
        notes="A tiny innovation update is useful for routing, but not byte-useful compression.",
    ),
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def counted_size(obj: Any) -> int:
    return len(stable_json(obj).encode("utf-8"))


def source_state(fixture: Fixture) -> list[float]:
    if fixture.kind in {"periodic_transport", "wrong_boundary_transport"}:
        pattern = [float(value) for value in fixture.theta["pattern"]]
        return [pattern[index % len(pattern)] for index in range(fixture.length)]
    if fixture.kind == "assimilation_update":
        background = float(fixture.theta["background"])
        observation = float(fixture.theta["observation"])
        gain = float(fixture.theta["gain"])
        value = background + gain * (observation - background)
        return [value for _ in range(fixture.length)]
    raise ValueError(f"unsupported fixture kind {fixture.kind}")


def replay_state(fixture: Fixture) -> list[float]:
    source = source_state(fixture)
    if fixture.kind == "periodic_transport":
        shift = int(fixture.theta["shift"]) % len(source)
        return source[-shift:] + source[:-shift]
    if fixture.kind == "wrong_boundary_transport":
        shift = int(fixture.theta["shift"]) % len(source)
        shifted = [source[0] for _ in range(shift)] + source[:-shift]
        return shifted[: len(source)]
    if fixture.kind == "assimilation_update":
        # Replay the analysis state from background, observation, and gain.
        return source
    raise ValueError(f"unsupported fixture kind {fixture.kind}")


def target_state(fixture: Fixture) -> list[float]:
    if fixture.kind == "wrong_boundary_transport":
        correct = Fixture(
            fixture_id=fixture.fixture_id,
            kind="periodic_transport",
            length=fixture.length,
            theta=fixture.theta,
            negative_control=fixture.negative_control,
            notes=fixture.notes,
        )
        return replay_state(correct)
    return replay_state(fixture)


def residual_patch(source: list[float], candidate: list[float]) -> list[dict[str, float]]:
    patch: list[dict[str, float]] = []
    max_len = max(len(source), len(candidate))
    for index in range(max_len):
        actual = source[index] if index < len(source) else math.nan
        proposed = candidate[index] if index < len(candidate) else math.nan
        if actual != proposed:
            patch.append({"i": index, "actual": actual, "candidate": proposed})
    return patch


def apply_patch(candidate: list[float], patch: list[dict[str, float]], length: int) -> list[float]:
    repaired = list(candidate)
    for item in patch:
        index = int(item["i"])
        while index >= len(repaired):
            repaired.append(math.nan)
        repaired[index] = float(item["actual"])
    return repaired[:length]


def cfl(theta: dict[str, Any]) -> float:
    return abs(float(theta.get("u", 0.0))) * float(theta.get("dt", 1.0)) / max(float(theta.get("dx", 1.0)), 1e-12)


def innovation_norm(theta: dict[str, Any]) -> float:
    if "background" not in theta or "observation" not in theta:
        return 0.0
    return abs(float(theta["observation"]) - float(theta["background"]))


def ensemble_spread(state: list[float]) -> float:
    if not state:
        return 0.0
    mean = sum(state) / len(state)
    return math.sqrt(sum((value - mean) ** 2 for value in state) / len(state))


def run_fixture(fixture: Fixture) -> dict[str, Any]:
    target = target_state(fixture)
    candidate = replay_state(fixture)
    patch = residual_patch(target, candidate)
    repaired = apply_patch(candidate, patch, len(target))

    exact_without_residual = candidate == target
    exact_with_residual = repaired == target
    mass_target = sum(target)
    mass_candidate = sum(candidate)
    mass_repaired = sum(repaired)
    mass_drift_before_repair = abs(mass_target - mass_candidate)
    mass_drift_after_repair = abs(mass_target - mass_repaired)

    dictionary_payload = {
        "objective_hash": sha256_text(stable_json(OBJECTIVE_PACKET)),
        "source_manifest": rel(SOURCE_MANIFEST),
    }
    kernel_payload = {"kind": fixture.kind}
    theta_payload = fixture.theta
    protocol_payload = {"decoder": "weather_tiny_replay_v1", "repair": "patch_v1"}
    residual_payload = {"patch": patch}
    receipt_payload = {
        "target_hash": sha256_text(stable_json(target)),
        "candidate_hash": sha256_text(stable_json(candidate)),
        "repaired_hash": sha256_text(stable_json(repaired)),
    }

    raw_bytes = counted_size(target)
    dictionary_bytes = counted_size(dictionary_payload)
    kernel_bytes = counted_size(kernel_payload)
    theta_bytes = counted_size(theta_payload)
    protocol_bytes = counted_size(protocol_payload)
    residual_bytes = 0 if exact_without_residual else counted_size(residual_payload)
    receipt_bytes = counted_size(receipt_payload)
    counted_bytes = dictionary_bytes + kernel_bytes + theta_bytes + protocol_bytes + residual_bytes + receipt_bytes
    byte_gain = raw_bytes - counted_bytes
    positive_byte_law = byte_gain > 0
    cfl_number = cfl(fixture.theta)
    cfl_excess = max(0.0, cfl_number - 1.0)
    residual_growth = len(patch) / max(len(target), 1)

    if fixture.negative_control and exact_without_residual:
        status = "FAIL_NEGATIVE_CONTROL"
    elif fixture.negative_control:
        status = "HOLD_DIAGNOSTIC"
    elif exact_with_residual and positive_byte_law and mass_drift_after_repair == 0.0:
        status = "ADMIT_FIXTURE"
    else:
        status = "HOLD_DIAGNOSTIC"

    result = {
        "fixture_id": fixture.fixture_id,
        "kind": fixture.kind,
        "notes": fixture.notes,
        "negative_control": fixture.negative_control,
        "target_hash": receipt_payload["target_hash"],
        "candidate_hash": receipt_payload["candidate_hash"],
        "repaired_hash": receipt_payload["repaired_hash"],
        "objective_hash": sha256_text(stable_json(OBJECTIVE_PACKET)),
        "exact_replay_without_residual": exact_without_residual,
        "exact_replay_with_residual": exact_with_residual,
        "residual_declared": True,
        "raw_bytes": raw_bytes,
        "dictionary_bytes": dictionary_bytes,
        "kernel_bytes": kernel_bytes,
        "theta_bytes": theta_bytes,
        "protocol_bytes": protocol_bytes,
        "residual_bytes": residual_bytes,
        "receipt_bytes": receipt_bytes,
        "counted_bytes": counted_bytes,
        "byte_gain": byte_gain,
        "positive_byte_law": positive_byte_law,
        "mass_target": mass_target,
        "mass_candidate": mass_candidate,
        "mass_repaired": mass_repaired,
        "mass_drift_before_repair": mass_drift_before_repair,
        "mass_drift_after_repair": mass_drift_after_repair,
        "cfl_number": cfl_number,
        "cfl_excess": cfl_excess,
        "innovation_norm": innovation_norm(fixture.theta),
        "ensemble_spread": ensemble_spread(target),
        "residual_growth": residual_growth,
        "patch_count": len(patch),
        "counted_payload_hash": sha256_text(
            stable_json(
                {
                    "D": dictionary_payload,
                    "K": kernel_payload,
                    "Theta": theta_payload,
                    "Pi": protocol_payload,
                    "R": residual_payload,
                    "Receipts": receipt_payload,
                }
            )
        ),
        "status": status,
    }
    result["result_hash"] = sha256_text(stable_json({k: v for k, v in result.items() if k != "result_hash"}))
    return result


def write_summary(receipt: dict[str, Any], path: Path) -> None:
    lines = [
        "# Weather Systems Math Prior Receipt",
        "",
        f"Schema: `{receipt['schema']}`  ",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        receipt["claim_boundary"],
        "",
        "## Objective",
        "",
        f"`{OBJECTIVE_PACKET['core_map']}`",
        "",
        f"`{OBJECTIVE_PACKET['weather_codec_score']}`",
        "",
        "## Fixtures",
        "",
        "| Fixture | Status | Exact repair | Byte gain | Mass drift after repair | CFL | Residual growth |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for result in receipt["results"]:
        lines.append(
            f"| {result['fixture_id']} | {result['status']} | "
            f"{result['exact_replay_with_residual']} | {result['byte_gain']} | "
            f"{result['mass_drift_after_repair']:.6g} | {result['cfl_number']:.3f} | "
            f"{result['residual_growth']:.3f} |"
        )
    lines.extend(["", "## Source Surfaces", ""])
    for source in SOURCE_SURFACES:
        lines.append(f"- {source['name']}: {source['url']}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = [run_fixture(fixture) for fixture in FIXTURES]
    with TABLE.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result, sort_keys=True) + "\n")

    status_values = sorted({result["status"] for result in results})
    receipt = {
        "schema": "weather_systems_math_prior_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_packet": OBJECTIVE_PACKET,
        "objective_hash": sha256_text(stable_json(OBJECTIVE_PACKET)),
        "source_manifest": rel(SOURCE_MANIFEST),
        "source_surfaces": SOURCE_SURFACES,
        "fixture_count": len(results),
        "table": rel(TABLE),
        "summary": rel(SUMMARY),
        "status_counts": {
            status: sum(1 for result in results if result["status"] == status)
            for status in status_values
        },
        "results": results,
        "decision": "HOLD",
        "claim_boundary": (
            "Weather-systems borrowed-math prior only. It uses tiny synthetic "
            "fixtures for conservative transport, boundary-condition residuals, "
            "and data-assimilation innovation. It does not ingest ERA5/NWP data, "
            "does not forecast weather, does not validate an atmospheric model, "
            "and does not claim compression benchmark performance."
        ),
    }
    receipt["receipt_hash"] = sha256_text(
        stable_json(
            {
                k: v
                for k, v in receipt.items()
                if k not in {"receipt_hash", "generated_at_utc"}
            }
        )
    )
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(receipt, SUMMARY)
    print(
        json.dumps(
            {
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "table": rel(TABLE),
                "receipt_hash": receipt["receipt_hash"],
                "status_counts": receipt["status_counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
