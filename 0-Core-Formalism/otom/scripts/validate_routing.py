#!/usr/bin/env python3
"""Validate Equation Forest routing registry and toy Goxel route requests.

Status: HOLD / workbench projection.

This script validates the machine-readable routing grammar. It does not prove
physics, topology, or semantic truth.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

REQUIRED_KERNEL_FIELDS = {
    "kernel_id",
    "domain_class",
    "display_equation",
    "variables",
    "bucket",
    "hyper_term",
    "functional_role",
    "claim_state",
    "authority_scope",
    "allowed_runtimes",
    "blocked_usages",
    "receipt_refs",
}

ALLOWED_BUCKETS = {"GEOMETRY", "FLUID", "NEURAL", "ENTROPY", "TOPOLOGY", "AUXILIARY"}

TOY_ROUTE_RULES = {
    "shockwave_goxel": {
        "required_buckets": {"FLUID", "ENTROPY"},
        "recommended_kernels": {
            "Burgers_Inviscid",
            "Burgers_Viscous",
            "Navier_Stokes_Incompressible",
            "Shannon_Entropy",
            "Landauer_Bound",
        },
        "description": "Shockwave Goxel should route through fluid dynamics plus entropy/cost gates.",
    },
    "near_miss_sidon_goxel": {
        "required_buckets": {"TOPOLOGY", "ENTROPY"},
        "recommended_kernels": {
            "RGFlow_Admissibility",
            "Genome18_Address",
            "Shannon_Entropy",
            "Landauer_Bound",
        },
        "description": "Near-miss Sidon Goxel should preserve collision metadata and route through topology plus entropy gates.",
    },
    "signal_surprise_goxel": {
        "required_buckets": {"NEURAL", "ENTROPY"},
        "recommended_kernels": {
            "NII_Surprise",
            "S3C_Codec",
            "Shannon_Entropy",
        },
        "description": "Signal-surprise Goxel should route through residual/signal and entropy accounting.",
    },
}


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    messages: list[str]


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit(f"Expected JSON object at root of {path}")
    return data


def validate_kernel_registry(registry: dict[str, Any]) -> ValidationResult:
    messages: list[str] = []
    kernels = registry.get("kernels")

    if not isinstance(kernels, list):
        return ValidationResult(False, ["registry.kernels must be a list"])

    seen: set[str] = set()
    bucket_counts: dict[str, int] = {bucket: 0 for bucket in ALLOWED_BUCKETS}

    for index, kernel in enumerate(kernels):
        if not isinstance(kernel, dict):
            messages.append(f"kernel[{index}] is not an object")
            continue

        missing = sorted(REQUIRED_KERNEL_FIELDS - set(kernel))
        if missing:
            messages.append(f"kernel[{index}] missing fields: {', '.join(missing)}")

        kernel_id = kernel.get("kernel_id")
        if not isinstance(kernel_id, str) or not kernel_id:
            messages.append(f"kernel[{index}] has invalid kernel_id")
        elif kernel_id in seen:
            messages.append(f"duplicate kernel_id: {kernel_id}")
        else:
            seen.add(kernel_id)

        bucket = kernel.get("bucket")
        if bucket not in ALLOWED_BUCKETS:
            messages.append(f"kernel {kernel_id!r} has invalid bucket: {bucket!r}")
        else:
            bucket_counts[bucket] += 1

        if kernel.get("claim_state") not in {"HOLD", "V_scope", "REVIEWED", "CANONICAL_LEAN", "QUARANTINE"}:
            messages.append(f"kernel {kernel_id!r} has invalid claim_state: {kernel.get('claim_state')!r}")

        if kernel.get("authority_scope") not in {
            "workbench_projection",
            "simulation_only",
            "receipt_backed",
            "canonical_lean",
            "external_source",
            "safety_policy",
        }:
            messages.append(f"kernel {kernel_id!r} has invalid authority_scope: {kernel.get('authority_scope')!r}")

    if len(seen) != 15:
        messages.append(f"expected 15 kernels, found {len(seen)}")

    for required_bucket in {"FLUID", "NEURAL", "ENTROPY", "TOPOLOGY"}:
        if bucket_counts[required_bucket] == 0:
            messages.append(f"required bucket has no kernels: {required_bucket}")

    if messages:
        return ValidationResult(False, messages)

    return ValidationResult(True, ["kernel registry passed structural validation"])


def kernel_index(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {kernel["kernel_id"]: kernel for kernel in registry.get("kernels", []) if isinstance(kernel, dict) and "kernel_id" in kernel}


def buckets_for_kernels(kernels: Iterable[str], index: dict[str, dict[str, Any]]) -> set[str]:
    buckets: set[str] = set()
    for kernel_id in kernels:
        kernel = index.get(kernel_id)
        if kernel:
            buckets.add(str(kernel.get("bucket")))
    return buckets


def validate_toy_route(registry: dict[str, Any], route_name: str, selected_kernels: list[str] | None) -> ValidationResult:
    messages: list[str] = []
    rules = TOY_ROUTE_RULES.get(route_name)
    if rules is None:
        valid = ", ".join(sorted(TOY_ROUTE_RULES))
        return ValidationResult(False, [f"unknown route {route_name!r}; valid routes: {valid}"])

    index = kernel_index(registry)
    selected = set(selected_kernels or rules["recommended_kernels"])

    unknown = sorted(kernel for kernel in selected if kernel not in index)
    if unknown:
        messages.append(f"unknown selected kernels: {', '.join(unknown)}")

    actual_buckets = buckets_for_kernels(selected, index)
    missing_buckets = set(rules["required_buckets"]) - actual_buckets
    if missing_buckets:
        messages.append(f"route {route_name} missing required buckets: {', '.join(sorted(missing_buckets))}")

    for kernel_id in sorted(selected):
        kernel = index.get(kernel_id)
        if not kernel:
            continue
        if "toy_route_validator" not in kernel.get("allowed_runtimes", []):
            messages.append(f"kernel {kernel_id} is not marked for toy_route_validator runtime")

    if messages:
        return ValidationResult(False, messages)

    return ValidationResult(True, [
        rules["description"],
        f"selected kernels: {', '.join(sorted(selected))}",
        f"covered buckets: {', '.join(sorted(actual_buckets))}",
        "route passed routing-grammar validation only; no physical/theorem claim is implied",
    ])


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate Equation Forest routing registry and toy routes.")
    parser.add_argument("--registry", type=Path, default=Path("registry/equation_forest_kernels.json"))
    parser.add_argument("--route", choices=sorted(TOY_ROUTE_RULES), help="Optional toy route to validate")
    parser.add_argument("--kernels", nargs="*", help="Optional explicit kernel IDs for route validation")
    args = parser.parse_args(argv)

    registry = load_json(args.registry)
    structural = validate_kernel_registry(registry)
    for message in structural.messages:
        print(message)
    if not structural.ok:
        return 1

    if args.route:
        route_result = validate_toy_route(registry, args.route, args.kernels)
        for message in route_result.messages:
            print(message)
        if not route_result.ok:
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
