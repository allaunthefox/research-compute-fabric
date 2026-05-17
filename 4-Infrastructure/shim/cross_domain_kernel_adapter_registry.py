#!/usr/bin/env python3
"""Build a receipt-backed cross-domain kernel adapter registry.

Cross-domain compression is only lawful when a shared algebraic kernel is kept
separate from the domain adapter that interprets it. This registry records that
separation: exact Mass Number kernels may be reused, but domain analogies stay
HOLD unless adapter closure is receipted.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "cross_domain_kernel_adapters"
REGISTRY = OUT_DIR / "cross_domain_kernel_adapter_registry.json"
RECEIPT = OUT_DIR / "cross_domain_kernel_adapter_registry_receipt.json"
SUMMARY = OUT_DIR / "cross_domain_kernel_adapter_registry.md"

SOURCE_REFS = [
    REPO / "shared-data/data/mass_number_transform_registry/mass_number_transform_registry_receipt.json",
    REPO / "shared-data/data/buoyancy_added_mass_mobius/buoyancy_added_mass_mobius_receipt.json",
    REPO / "shared-data/data/foundation_forward_equation_compiler/foundation_forward_equation_compiler_receipt.json",
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def file_hash(path: Path) -> str | None:
    return sha256_bytes(path.read_bytes()) if path.exists() else None


def source_ref(path: Path) -> dict[str, Any]:
    return {"path": rel(path), "exists": path.exists(), "sha256": file_hash(path)}


def adapter(
    *,
    adapter_id: str,
    domain: str,
    kernel_opcode: str,
    adapter_role: str,
    compressed_form: str,
    expanded_form: str,
    required_receipt: str,
    decision: str,
    residual_policy: str,
    warning: str = "same algebraic skeleton does not imply same domain law",
) -> dict[str, Any]:
    item = {
        "adapter_id": adapter_id,
        "domain": domain,
        "kernel_opcode": kernel_opcode,
        "adapter_role": adapter_role,
        "compressed_form": compressed_form,
        "expanded_form": expanded_form,
        "required_receipt": required_receipt,
        "decision": decision,
        "residual_policy": residual_policy,
        "warning": warning,
    }
    item["adapter_hash"] = hash_obj({k: v for k, v in item.items() if k != "adapter_hash"})
    return item


def build_registry() -> dict[str, Any]:
    adapters = [
        adapter(
            adapter_id="fluid_added_mass_lambda_BAM",
            domain="fluid_mechanics",
            kernel_opcode="MN_MOBIUS_LOAD",
            adapter_role="density contrast plus added-mass geometry coefficient",
            compressed_form="lambda_BAM(MN(rho_o,rho_m), C)",
            expanded_form="a = g*(rho_o-rho_m)/(rho_o + C*rho_m)",
            required_receipt="shared-data/data/buoyancy_added_mass_mobius/buoyancy_added_mass_mobius_receipt.json",
            decision="ACCEPT_ADAPTER_FIXTURE",
            residual_policy="early-time ideal added-mass only; drag, vorticity, boundary effects remain residual lanes",
        ),
        adapter(
            adapter_id="impedance_boundary_reflection",
            domain="wave_boundaries",
            kernel_opcode="MN_REFLECT",
            adapter_role="two-impedance boundary contrast",
            compressed_form="Gamma = MN(Z2,Z1)",
            expanded_form="Gamma = (Z2-Z1)/(Z2+Z1)",
            required_receipt="shared-data/data/mass_number_transform_registry/mass_number_transform_registry_receipt.json",
            decision="ACCEPT_KERNEL_ADAPTER",
            residual_policy="domain source equation, sign convention, and loss model still required before physical promotion",
        ),
        adapter(
            adapter_id="binary_route_probability",
            domain="routing_probability",
            kernel_opcode="MN_BINARY_P",
            adapter_role="two-route normalized weight contrast",
            compressed_form="P(a)=(1+MN(a,b))/2",
            expanded_form="P(a)=a/(a+b)",
            required_receipt="shared-data/data/mass_number_transform_registry/mass_number_transform_registry_receipt.json",
            decision="ACCEPT_KERNEL_ADAPTER",
            residual_policy="requires nonnegative weights and explicit route prior source before use as decision evidence",
        ),
        adapter(
            adapter_id="mechanics_pair_reduction",
            domain="two_body_mechanics",
            kernel_opcode="MN_REDUCED",
            adapter_role="reduced mass / product-over-sum pair law",
            compressed_form="mu = S/4*(1-MN(m1,m2)^2)",
            expanded_form="mu = m1*m2/(m1+m2)",
            required_receipt="shared-data/data/mass_number_transform_registry/mass_number_transform_registry_receipt.json",
            decision="ACCEPT_KERNEL_ADAPTER",
            residual_policy="domain equations using reduced mass still require local source and closure receipts",
        ),
        adapter(
            adapter_id="weighted_expert_blend",
            domain="expert_routing",
            kernel_opcode="MN_BLEND",
            adapter_role="two-source confidence merge",
            compressed_form="blend = mid(A,B) + MN(w1,w2)*halfdiff(A,B)",
            expanded_form="blend = (w1*A+w2*B)/(w1+w2)",
            required_receipt="shared-data/data/mass_number_transform_registry/mass_number_transform_registry_receipt.json",
            decision="ACCEPT_KERNEL_ADAPTER",
            residual_policy="requires source weights, replayed decision path, and HOLD if weights are not lawful evidence",
        ),
        adapter(
            adapter_id="couch_contact_topology",
            domain="moving_sofa_contact_geometry",
            kernel_opcode="MN",
            adapter_role="bounded contact/clearance contrast between active constraints",
            compressed_form="MN_ij = (c_i-c_j)/(c_i+c_j+epsilon)",
            expanded_form="clearance/contact switching over corridor constraints",
            required_receipt="not yet available",
            decision="HOLD_CONTACT_TOPOLOGY",
            residual_policy="requires corridor model, signed-distance convention, motion path replay, collision closure, and area accounting",
        ),
        adapter(
            adapter_id="earth_core_boundary_witness",
            domain="seismic_horizon_inference",
            kernel_opcode="MN_REFLECT",
            adapter_role="boundary wave witness for inaccessible interior",
            compressed_form="interior_state := adapter(seismic boundary packets, residual model)",
            expanded_form="infer interior material state from wave travel/attenuation/aniso residuals",
            required_receipt="not yet available",
            decision="HOLD_BOUNDARY_WITNESS",
            residual_policy="boundary witnesses may route hypotheses; unresolved interior stays Underverse until source data and closure checks exist",
        ),
        adapter(
            adapter_id="binary_entropy_route_cost",
            domain="compression_routing",
            kernel_opcode="MN_BINARY_ENTROPY",
            adapter_role="route uncertainty over Mass Number contrast",
            compressed_form="H2_MN(x)",
            expanded_form="-p*log2(p)-(1-p)*log2(1-p), p=(1+x)/2",
            required_receipt="shared-data/data/mass_number_transform_registry/mass_number_transform_registry_receipt.json",
            decision="HOLD_ANALYTIC_ADAPTER",
            residual_policy="requires log base, numeric precision, approximation policy, and byte-cost receipt",
        ),
    ]
    return {
        "schema": "cross_domain_kernel_adapter_registry_v1",
        "claim_boundary": (
            "Cross-domain adapter registry only. It records reusable kernel shapes "
            "and domain adapters, not theorem promotion, physical equivalence, or "
            "benchmark evidence. Shared algebraic skeletons are not shared domain "
            "substance; adapters and residuals must close independently."
        ),
        "canonical_statement": (
            "Cross-domain compression stores reusable law-shapes once, then "
            "rehydrates them through domain adapters. Similarity without closure "
            "routes to HOLD, QUARANTINE, Underverse, or NaN0."
        ),
        "adapter_equation": "X_d = A_d[K_j(theta)] + R_d + chi0",
        "underverse_guardrail": "same shape does not imply same law",
        "adapters": adapters,
        "adapter_count": len(adapters),
        "status_counts": {
            status: sum(1 for item in adapters if item["decision"] == status)
            for status in sorted({item["decision"] for item in adapters})
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    source_refs = [source_ref(path) for path in SOURCE_REFS]
    accepted = sum(
        count
        for status, count in registry["status_counts"].items()
        if status in {"ACCEPT_ADAPTER_FIXTURE", "ACCEPT_KERNEL_ADAPTER"}
    )
    held = registry["adapter_count"] - accepted
    receipt = {
        "schema": "cross_domain_kernel_adapter_registry_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry_path": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "source_refs": source_refs,
        "adapter_count": registry["adapter_count"],
        "status_counts": registry["status_counts"],
        "accepted_adapter_count": accepted,
        "held_adapter_count": held,
        "decision": "HOLD_CROSS_DOMAIN_WITH_ACCEPTED_KERNEL_ADAPTERS",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Cross-Domain Kernel Adapter Registry",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Canonical Statement",
        "",
        registry["canonical_statement"],
        "",
        "```text",
        registry["adapter_equation"],
        registry["underverse_guardrail"],
        "```",
        "",
        "## Adapter Table",
        "",
        "| Adapter | Domain | Kernel | Decision | Role |",
        "|---|---|---|---|---|",
    ]
    for item in registry["adapters"]:
        lines.append(
            f"| `{item['adapter_id']}` | `{item['domain']}` | `{item['kernel_opcode']}` | "
            f"`{item['decision']}` | {item['adapter_role']} |"
        )
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            "Accepted kernel adapters admit algebraic reuse only. Domain-specific "
            "truth, physical interpretation, corpus compression, or geometry "
            "optimality still requires source equations, replay, residual policy, "
            "and closure receipts.",
        ]
    )
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    registry = build_registry()
    receipt = build_receipt(registry)
    REGISTRY.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(registry, receipt)
    print(
        json.dumps(
            {
                "registry": rel(REGISTRY),
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "receipt_hash": receipt["receipt_hash"],
                "decision": receipt["decision"],
                "status_counts": registry["status_counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
