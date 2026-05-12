#!/usr/bin/env python3
"""Build a receipt-backed registry of Mass-Number-able transforms.

The registry captures equation families that can be represented by a bounded
contrast

    MN(a,b) = (a-b)/(a+b)

plus a small transform opcode. Exact rational identities are admitted as
kernel fixtures. Analytic transforms such as entropy are recorded as HOLD
until a numerical/error policy is declared.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "mass_number_transform_registry"
REGISTRY = OUT_DIR / "mass_number_transform_registry.json"
RECEIPT = OUT_DIR / "mass_number_transform_registry_receipt.json"
SUMMARY = OUT_DIR / "mass_number_transform_registry.md"

SOURCE_REFS = [
    REPO / "shared-data/data/foundation_forward_equation_compiler/foundation_forward_equation_compiler_receipt.json",
    REPO / "shared-data/data/buoyancy_added_mass_mobius/buoyancy_added_mass_mobius_receipt.json",
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


def frac_payload(value: Fraction | tuple[Fraction, ...]) -> Any:
    if isinstance(value, tuple):
        return [frac_payload(item) for item in value]
    return {"numerator": value.numerator, "denominator": value.denominator, "decimal": float(value)}


def mn(a: Fraction, b: Fraction) -> Fraction:
    return (a - b) / (a + b)


def ratio_from_mn(x: Fraction) -> Fraction:
    return (Fraction(1) + x) / (Fraction(1) - x)


def mobius_mn(x: Fraction, k: Fraction) -> Fraction:
    return Fraction(2) * x / ((Fraction(1) + k) + (Fraction(1) - k) * x)


def split_pair(total: Fraction, x: Fraction) -> tuple[Fraction, Fraction]:
    return total * (Fraction(1) + x) / 2, total * (Fraction(1) - x) / 2


def reduced_pair(total: Fraction, x: Fraction) -> Fraction:
    return total * (Fraction(1) - x * x) / 4


def pair_product(total: Fraction, x: Fraction) -> Fraction:
    return total * total * (Fraction(1) - x * x) / 4


def weighted_blend(x: Fraction, a_value: Fraction, b_value: Fraction) -> Fraction:
    return (a_value + b_value) / 2 + x * (a_value - b_value) / 2


def binary_p(x: Fraction) -> Fraction:
    return (Fraction(1) + x) / 2


def binary_q(x: Fraction) -> Fraction:
    return (Fraction(1) - x) / 2


def transmit_power(x: Fraction) -> Fraction:
    return Fraction(1) - x * x


def elastic_1d(x: Fraction, v1: Fraction, v2: Fraction) -> tuple[Fraction, Fraction]:
    return x * v1 + (Fraction(1) - x) * v2, (Fraction(1) + x) * v1 - x * v2


def direct_mobius(a: Fraction, b: Fraction, k: Fraction) -> Fraction:
    return (a - b) / (a + k * b)


def direct_reduced(a: Fraction, b: Fraction) -> Fraction:
    return a * b / (a + b)


def direct_product(a: Fraction, b: Fraction) -> Fraction:
    return a * b


def direct_weighted_blend(w1: Fraction, w2: Fraction, a_value: Fraction, b_value: Fraction) -> Fraction:
    return (w1 * a_value + w2 * b_value) / (w1 + w2)


def direct_elastic_1d(m1: Fraction, m2: Fraction, v1: Fraction, v2: Fraction) -> tuple[Fraction, Fraction]:
    total = m1 + m2
    return (
        ((m1 - m2) / total) * v1 + (2 * m2 / total) * v2,
        (2 * m1 / total) * v1 + ((m2 - m1) / total) * v2,
    )


def check_equal(name: str, compressed: Any, direct: Any) -> dict[str, Any]:
    return {
        "name": name,
        "compressed": frac_payload(compressed),
        "direct": frac_payload(direct),
        "pass": compressed == direct,
    }


def transform(
    *,
    transform_id: str,
    opcode: str,
    family: str,
    canonical_form: str,
    expanded_form: str,
    args_saved: list[str],
    domains: list[str],
    checks: list[dict[str, Any]],
    decision: str = "ACCEPT_KERNEL",
    residual_policy: str = "none for exact algebraic identity; domain restrictions still apply",
) -> dict[str, Any]:
    item = {
        "transform_id": transform_id,
        "opcode": opcode,
        "family": family,
        "canonical_form": canonical_form,
        "expanded_form": expanded_form,
        "args_saved": args_saved,
        "domains": domains,
        "checks": checks,
        "all_checks_pass": all(check.get("pass", False) for check in checks) if checks else None,
        "decision": decision,
        "residual_policy": residual_policy,
    }
    item["transform_hash"] = hash_obj({k: v for k, v in item.items() if k != "transform_hash"})
    return item


def build_registry() -> dict[str, Any]:
    a = Fraction(5)
    b = Fraction(3)
    x = mn(a, b)
    total = a + b
    k = Fraction(2, 3)
    w1, w2 = Fraction(7), Fraction(5)
    wx = mn(w1, w2)
    av, bv = Fraction(11), Fraction(2)
    m1, m2 = Fraction(5), Fraction(3)
    mx = mn(m1, m2)
    v1, v2 = Fraction(7), Fraction(-1)
    z2, z1 = Fraction(9), Fraction(4)
    zx = mn(z2, z1)

    transforms = [
        transform(
            transform_id="MN_contrast",
            opcode="MN",
            family="contrast",
            canonical_form="x = MN(a,b)",
            expanded_form="x = (a-b)/(a+b)",
            args_saved=["shared bounded contrast replaces repeated difference-over-sum forms"],
            domains=["positive_pair_ratios", "impedance_contrasts", "density_contrasts", "binary_weights"],
            checks=[check_equal("MN_5_3", x, Fraction(1, 4))],
        ),
        transform(
            transform_id="ratio_from_MN",
            opcode="MN_RATIO_INV",
            family="inverse_ratio",
            canonical_form="a/b = (1+x)/(1-x)",
            expanded_form="x = (a-b)/(a+b)",
            args_saved=["reconstructs raw ratio from one bounded scalar"],
            domains=["positive_pair_ratios", "rehydration"],
            checks=[check_equal("ratio_rehydrate_5_3", ratio_from_mn(x), a / b)],
        ),
        transform(
            transform_id="MN_mobius_load",
            opcode="MN_MOBIUS_LOAD",
            family="geometry_loaded_denominator",
            canonical_form="F_k(x) = 2x / ((1+k)+(1-k)x)",
            expanded_form="F_k(a,b) = (a-b)/(a+k*b)",
            args_saved=["replace a,b,k denominator family with x,k"],
            domains=["added_mass", "geometry_loaded_inertia", "interface_load_correction"],
            checks=[check_equal("mobius_5_3_k_2_3", mobius_mn(x, k), direct_mobius(a, b, k))],
        ),
        transform(
            transform_id="pair_split",
            opcode="MN_SPLIT",
            family="two_body_decomposition",
            canonical_form="a,b = S/2*(1+x), S/2*(1-x)",
            expanded_form="S=a+b; x=(a-b)/(a+b)",
            args_saved=["store total plus MN instead of two raw parts"],
            domains=["two_body_mass", "binary_weights", "mixture_components"],
            checks=[check_equal("split_5_3", split_pair(total, x), (a, b))],
        ),
        transform(
            transform_id="pair_reduced",
            opcode="MN_REDUCED",
            family="product_over_sum",
            canonical_form="ab/(a+b) = S/4*(1-x^2)",
            expanded_form="ab/(a+b)",
            args_saved=["reduced mass / parallel pair from total plus MN"],
            domains=["reduced_mass", "parallel_resistors", "harmonic_pair_reduction"],
            checks=[check_equal("reduced_5_3", reduced_pair(total, x), direct_reduced(a, b))],
        ),
        transform(
            transform_id="pair_product",
            opcode="MN_PAIR_PRODUCT",
            family="pair_product",
            canonical_form="ab = S^2/4*(1-x^2)",
            expanded_form="ab",
            args_saved=["pair product from total plus MN"],
            domains=["two_body_mass", "variance_like_pair_terms", "coupling_products"],
            checks=[check_equal("product_5_3", pair_product(total, x), direct_product(a, b))],
        ),
        transform(
            transform_id="weighted_blend",
            opcode="MN_BLEND",
            family="weighted_average",
            canonical_form="blend = mid(A,B) + x*halfdiff(A,B)",
            expanded_form="(w1*A+w2*B)/(w1+w2)",
            args_saved=["replace two weights with one bounded weight contrast"],
            domains=["center_of_mass", "expert_blend", "mixture_interpolation", "confidence_merge"],
            checks=[check_equal("blend_w7_5_A11_B2", weighted_blend(wx, av, bv), direct_weighted_blend(w1, w2, av, bv))],
        ),
        transform(
            transform_id="reflection",
            opcode="MN_REFLECT",
            family="boundary_reflection",
            canonical_form="Gamma = MN(Z2,Z1)",
            expanded_form="Gamma = (Z2-Z1)/(Z2+Z1)",
            args_saved=["one contrast scalar for impedance boundary"],
            domains=["acoustic_impedance", "transmission_lines", "elastic_waves", "normal_fresnel", "thermal_effusivity"],
            checks=[check_equal("reflect_9_4", zx, (z2 - z1) / (z2 + z1))],
        ),
        transform(
            transform_id="transmit_power",
            opcode="MN_TRANSMIT_POWER",
            family="boundary_transmission",
            canonical_form="T_power = 1 - x^2",
            expanded_form="1 - ((A-B)/(A+B))^2",
            args_saved=["power transmission from reflected MN scalar"],
            domains=["boundary_transmission", "impedance_matching", "binary_survival"],
            checks=[check_equal("transmit_9_4", transmit_power(zx), Fraction(1) - ((z2 - z1) / (z2 + z1)) ** 2)],
        ),
        transform(
            transform_id="binary_probability",
            opcode="MN_BINARY_P",
            family="binary_choice",
            canonical_form="P(a)= (1+x)/2; P(b)= (1-x)/2",
            expanded_form="P(a)=a/(a+b); P(b)=b/(a+b)",
            args_saved=["two-class normalized weights from one bounded scalar"],
            domains=["binary_classifier", "route_selection", "expert_choice", "accept_hold_competition"],
            checks=[
                check_equal("binary_p_5_3", binary_p(x), a / (a + b)),
                check_equal("binary_q_5_3", binary_q(x), b / (a + b)),
            ],
        ),
        transform(
            transform_id="elastic_collision_1d",
            opcode="MN_ELASTIC_1D",
            family="two_body_collision",
            canonical_form="v1'=x*v1+(1-x)*v2; v2'=(1+x)*v1-x*v2",
            expanded_form="standard 1D elastic collision using m1,m2",
            args_saved=["replace two mass coefficients with one mass contrast"],
            domains=["elastic_collision", "two_body_mechanics", "mass_weighted_exchange"],
            checks=[check_equal("elastic_m5_3_v7_neg1", elastic_1d(mx, v1, v2), direct_elastic_1d(m1, m2, v1, v2))],
        ),
        transform(
            transform_id="binary_entropy_MN",
            opcode="MN_BINARY_ENTROPY",
            family="information_measure",
            canonical_form="H2(x)=H2((1+x)/2)",
            expanded_form="-p*log2(p)-(1-p)*log2(1-p)",
            args_saved=["entropy over binary choice reuses MN scalar"],
            domains=["route_uncertainty", "expert_selection", "receipt_gain_scoring"],
            checks=[],
            decision="HOLD_ANALYTIC",
            residual_policy="requires log base, numeric precision, and approximation receipt before admission",
        ),
    ]
    return {
        "schema": "mass_number_transform_registry_v1",
        "claim_boundary": (
            "Registry of algebraic Mass-Number-able transform families. ACCEPT_KERNEL "
            "entries passed exact rational identity checks; HOLD_ANALYTIC entries are "
            "routing candidates only until numerical/error policies are receipted. "
            "This is a compression/logogram registry, not a physics theorem atlas."
        ),
        "canonical_statement": (
            "Mass-Number-able equations are equations whose apparent complexity is "
            "mostly a bounded contrast, weighted blend, pair reduction, reflection, "
            "binary choice, or geometry-loaded Mobius transform."
        ),
        "base_logogram": "MN(a,b) = (a-b)/(a+b)",
        "ratio_identity": "MN(a,b) = tanh(0.5*ln(a/b)) for positive a,b",
        "transforms": transforms,
        "transform_count": len(transforms),
        "status_counts": {
            status: sum(1 for item in transforms if item["decision"] == status)
            for status in sorted({item["decision"] for item in transforms})
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    all_accept_checks_pass = all(
        item["all_checks_pass"] is True
        for item in registry["transforms"]
        if item["decision"] == "ACCEPT_KERNEL"
    )
    receipt = {
        "schema": "mass_number_transform_registry_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry_path": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "transform_count": registry["transform_count"],
        "status_counts": registry["status_counts"],
        "all_accept_kernel_checks_pass": all_accept_checks_pass,
        "decision": "ACCEPT_REGISTRY_WITH_HOLD_ANALYTIC" if all_accept_checks_pass else "HOLD_DIAGNOSTIC",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Mass Number Transform Registry",
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
        registry["base_logogram"],
        registry["ratio_identity"],
        "```",
        "",
        "## Transform Table",
        "",
        "| Opcode | Family | Decision | Canonical form | Domains |",
        "|---|---|---|---|---|",
    ]
    for item in registry["transforms"]:
        lines.append(
            f"| `{item['opcode']}` | `{item['family']}` | `{item['decision']}` | "
            f"`{item['canonical_form']}` | {', '.join(item['domains'])} |"
        )
    lines.extend(["", "## Check Summary", "", "| Opcode | Checks | Pass |", "|---|---:|---:|"])
    for item in registry["transforms"]:
        lines.append(f"| `{item['opcode']}` | {len(item['checks'])} | {item['all_checks_pass']} |")
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
