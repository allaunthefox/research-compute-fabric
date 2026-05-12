#!/usr/bin/env python3
"""Bounded decision-diagram probe for dimensional shell closure.

This runner does not recompress data.  It consumes the current reversible
projectable-geometry approach receipt and asks a narrower question:

If every non-raw route must carry a dimensional-shell closure witness, which
routes still beat the raw baseline, and which routes are pruned before any
recursive residual expansion can start?

The policy is intentionally conservative:

* no recursive residual subdivision
* no unresolved mass debt
* NaN0 fails closed
* candidate routes are compared against the best raw baseline per slice
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
APPROACH_RECEIPT = (
    REPO
    / "4-Infrastructure"
    / "shim"
    / "projectable_geometry_approach_tester_receipt.json"
)
RATIO_RECEIPT = (
    REPO
    / "4-Infrastructure"
    / "shim"
    / "compression_ratio_rederivation_receipt.json"
)
OUT = (
    REPO
    / "4-Infrastructure"
    / "shim"
    / "dimensional_shell_dd_probe_receipt.json"
)

HUTTER_TARGET_BYTES = 109_685_197
ENWIK9_BYTES = 1_000_000_000

SHELL_SEQUENCE = (12, 4, 3, 0)
MAX_PROJECTION_DEPTH = 3
DEFAULT_SHELL_WITNESS_BYTES = 16


@dataclass(frozen=True)
class ShellMass:
    visible_4d: Fraction
    shadow_3d: Fraction
    closure_0d: Fraction
    lawbound: Fraction
    unresolved: Fraction

    @property
    def total(self) -> Fraction:
        return (
            self.visible_4d
            + self.shadow_3d
            + self.closure_0d
            + self.lawbound
            + self.unresolved
        )


SHELL_MASS = ShellMass(
    visible_4d=Fraction(4, 12),
    shadow_3d=Fraction(3, 12),
    closure_0d=Fraction(1, 12),
    lawbound=Fraction(4, 12),
    unresolved=Fraction(0),
)


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fraction_str(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def fraction_json(value: Fraction) -> dict[str, Any]:
    return {
        "fraction": fraction_str(value),
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": float(value),
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def route_id(slice_name: str, transform: str, codec: str) -> str:
    return f"{slice_name}|{transform}|{codec}"


def shell_status(result: dict[str, Any]) -> dict[str, Any]:
    rehydrated_ok = bool(result.get("rehydrated_ok"))
    unresolved_ok = SHELL_MASS.unresolved == 0
    mass_ok = SHELL_MASS.total == 1
    depth_ok = MAX_PROJECTION_DEPTH == len(SHELL_SEQUENCE) - 1
    nan0 = not (rehydrated_ok and unresolved_ok and mass_ok and depth_ok)
    return {
        "closed": not nan0,
        "nan0": nan0,
        "rehydrated_ok": rehydrated_ok,
        "mass_total": fraction_json(SHELL_MASS.total),
        "mass_delta": fraction_json(SHELL_MASS.total - 1),
        "unresolved_mass": fraction_json(SHELL_MASS.unresolved),
        "depth_ok": depth_ok,
    }


def classify_route(
    slice_name: str,
    source_bytes: int,
    raw_baseline_bytes: int,
    result: dict[str, Any],
    shell_witness_bytes: int,
) -> dict[str, Any]:
    transform = result["transform"]
    codec = result["codec"]
    raw_route = transform == "raw"
    closure = shell_status(result)
    witness_bytes = 0 if raw_route else shell_witness_bytes
    adjusted_bytes = int(result["compressed_size"]) + witness_bytes
    raw_gap_bytes = raw_baseline_bytes - adjusted_bytes
    ratio = adjusted_bytes / source_bytes if source_bytes else 0.0
    projected_enwik9_total = int(ratio * ENWIK9_BYTES)

    if raw_route:
        decision = "raw_baseline"
        prune_reason = None
    elif closure["nan0"]:
        decision = "pruned"
        prune_reason = "nan0"
    elif adjusted_bytes >= raw_baseline_bytes:
        decision = "pruned"
        prune_reason = "lower_bound_exceeds_incumbent"
    else:
        decision = "promoted"
        prune_reason = None

    return {
        "route_id": route_id(slice_name, transform, codec),
        "slice": slice_name,
        "source_bytes": source_bytes,
        "transform": transform,
        "codec": codec,
        "raw_baseline_bytes": raw_baseline_bytes,
        "compressed_bytes": int(result["compressed_size"]),
        "encoded_bytes": int(result.get("encoded_size", result["compressed_size"])),
        "shell_witness_bytes": witness_bytes,
        "shell_adjusted_bytes": adjusted_bytes,
        "shell_adjusted_ratio": ratio,
        "projected_enwik9_total_bytes": projected_enwik9_total,
        "hutter_target_gap_bytes_projected_enwik9": projected_enwik9_total - HUTTER_TARGET_BYTES,
        "gain_vs_raw_after_shell_bytes": raw_gap_bytes,
        "overhead_budget_before_losing_raw": max(
            0,
            raw_baseline_bytes - int(result["compressed_size"]) - (1 if not raw_route else 0),
        ),
        "decision": decision,
        "prune_reason": prune_reason,
        "shell_status": closure,
    }


def slice_best(routes: list[dict[str, Any]]) -> dict[str, Any] | None:
    promoted = [route for route in routes if route["decision"] == "promoted"]
    if not promoted:
        return None
    return min(promoted, key=lambda item: item["shell_adjusted_bytes"])


def build_receipt(shell_witness_bytes: int) -> dict[str, Any]:
    approach = load_json(APPROACH_RECEIPT)
    ratio = load_json(RATIO_RECEIPT) if RATIO_RECEIPT.exists() else {}

    slices = []
    all_routes = []
    for item in approach.get("slices", []):
        slice_name = item["slice_name"]
        source_bytes = int(item["source_bytes"])
        raw_baseline_bytes = int(item["best_raw_baseline"]["compressed_size"])
        routes = [
            classify_route(
                slice_name,
                source_bytes,
                raw_baseline_bytes,
                result,
                shell_witness_bytes,
            )
            for result in item.get("results", [])
        ]
        best = slice_best(routes)
        all_routes.extend(routes)
        slices.append({
            "slice": slice_name,
            "source_bytes": source_bytes,
            "raw_baseline_bytes": raw_baseline_bytes,
            "route_count": len(routes),
            "promoted_route_count": sum(route["decision"] == "promoted" for route in routes),
            "pruned_route_count": sum(route["decision"] == "pruned" for route in routes),
            "nan0_route_count": sum(route["prune_reason"] == "nan0" for route in routes),
            "best_shell_adjusted": best,
            "routes": routes,
        })

    promoted = [route for route in all_routes if route["decision"] == "promoted"]
    pruned = [route for route in all_routes if route["decision"] == "pruned"]
    raw_baselines = [route for route in all_routes if route["decision"] == "raw_baseline"]
    best_overall = min(promoted, key=lambda item: item["shell_adjusted_ratio"]) if promoted else None

    receipt = {
        "schema": "dimensional_shell_dd_probe_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "dimensional_shell_dd_probe",
        "source_receipts": {
            "approach_receipt": str(APPROACH_RECEIPT.relative_to(REPO)),
            "approach_stable_hash_sha256": approach.get("stable_approach_hash_sha256"),
            "ratio_receipt": str(RATIO_RECEIPT.relative_to(REPO)),
            "ratio_stable_hash_sha256": ratio.get("stable_rederived_ratio_hash_sha256"),
        },
        "dimensional_shell": {
            "shell_sequence": list(SHELL_SEQUENCE),
            "max_projection_depth": MAX_PROJECTION_DEPTH,
            "mass_law": (
                "source_mass = visible_4d + shadow_3d + closure_0d + lawbound_mass; "
                "unresolved_mass must be zero."
            ),
            "mass": {
                "source": fraction_json(Fraction(1)),
                "visible_4d": fraction_json(SHELL_MASS.visible_4d),
                "shadow_3d": fraction_json(SHELL_MASS.shadow_3d),
                "closure_0d": fraction_json(SHELL_MASS.closure_0d),
                "lawbound": fraction_json(SHELL_MASS.lawbound),
                "unresolved": fraction_json(SHELL_MASS.unresolved),
                "total": fraction_json(SHELL_MASS.total),
            },
            "nan0_boundary": (
                "Any non-rehydrating route, unresolved mass debt, non-unit mass total, "
                "or projection deeper than 12->4->3->0 is NaN0 and fails closed."
            ),
        },
        "dd_policy": {
            "exponential_computation_permaban": True,
            "no_recursive_residual_subdivision": True,
            "branch_and_bound_incumbent": "best raw baseline per slice",
            "shell_witness_bytes_per_non_raw_route": shell_witness_bytes,
            "prune_rules": [
                "nan0",
                "lower_bound_exceeds_incumbent",
            ],
        },
        "summary": {
            "slice_count": len(slices),
            "route_count": len(all_routes),
            "raw_baseline_route_count": len(raw_baselines),
            "promoted_route_count": len(promoted),
            "pruned_route_count": len(pruned),
            "nan0_route_count": sum(route["prune_reason"] == "nan0" for route in all_routes),
            "lower_bound_pruned_count": sum(
                route["prune_reason"] == "lower_bound_exceeds_incumbent"
                for route in all_routes
            ),
            "best_shell_adjusted_overall": best_overall,
            "all_shell_closed": all(not route["shell_status"]["nan0"] for route in all_routes),
        },
        "slices": slices,
        "claim_boundary": (
            "This is a bounded decision-diagram pruning receipt over existing "
            "small-slice compression measurements. It is not a Hutter claim, "
            "optimality proof, physical-dimension claim, or new compression result."
        ),
        "lawful": True,
    }

    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "source_receipts": receipt["source_receipts"],
        "dimensional_shell": receipt["dimensional_shell"],
        "dd_policy": receipt["dd_policy"],
        "summary": receipt["summary"],
        "slices": receipt["slices"],
        "claim_boundary": receipt["claim_boundary"],
        "lawful": receipt["lawful"],
    }).encode("utf-8")
    receipt["stable_shell_dd_hash_sha256"] = sha256_bytes(stable_preimage)
    receipt["receipt_hash_preimage_sha256"] = sha256_bytes(stable_json(receipt).encode("utf-8"))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shell-witness-bytes", type=int, default=DEFAULT_SHELL_WITNESS_BYTES)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    if args.shell_witness_bytes < 0:
        raise ValueError("--shell-witness-bytes must be non-negative")

    receipt = build_receipt(args.shell_witness_bytes)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "lawful": receipt["lawful"],
        "stable_shell_dd_hash_sha256": receipt["stable_shell_dd_hash_sha256"],
        "summary": receipt["summary"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
