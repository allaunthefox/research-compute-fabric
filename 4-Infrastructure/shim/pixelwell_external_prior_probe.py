#!/usr/bin/env python3
"""PixelWell external-prior receipt for high-dimensional bump maps.

PixelWell maps bitmap intensity into a 2D Schrodinger potential and solves for
eigenstates. For this stack, that is useful as a conceptual seed for a higher
dimensional bump map: rendered glyphs, charts, molecule shadows, Hutter route
states, or torsion/chirality/orientation coordinates can become height fields,
potential wells, curvature fields, and spectral route hints. This probe records
the idea without vendoring the external code or promoting it beyond HOLD.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "pixelwell_external_prior"
REGISTRY = OUT_DIR / "pixelwell_external_prior_registry.json"
RECEIPT = OUT_DIR / "pixelwell_external_prior_receipt.json"
SUMMARY = OUT_DIR / "pixelwell_external_prior.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "PixelWell External Prior.tid"


EXTERNAL_REPO = "https://github.com/mrspinaz/PixelWell"
EXTERNAL_README = "https://raw.githubusercontent.com/mrspinaz/PixelWell/main/README.MD"
EXTERNAL_SCRIPT = "https://raw.githubusercontent.com/mrspinaz/PixelWell/main/pixelwell.py"
EIGEN3_URL = "https://eigen.tuxfamily.org/"
SPECTRA_URL = "https://spectralib.org/"


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


def build_registry() -> dict[str, Any]:
    external_summary = {
        "repo": EXTERNAL_REPO,
        "readme": EXTERNAL_README,
        "script": EXTERNAL_SCRIPT,
        "observed_status": "UNFINISHED",
        "observed_claim": "bitmap dark pixels become potential wells; solver finds quantum eigenstates",
        "observed_dependencies": [
            {"name": "Eigen3", "role": "sparse matrix support", "url": EIGEN3_URL},
            {"name": "Spectra", "role": "sparse eigenvalue solver", "url": SPECTRA_URL},
            {"name": "OpenMP", "role": "parallel solver support", "url": None},
            {"name": "numpy", "role": "array and binary buffer bridge", "url": None},
            {"name": "matplotlib", "role": "visualization", "url": None},
            {"name": "scikit-image", "role": "image loading, grayscale conversion, and downsampling", "url": None},
        ],
        "license_status": "unknown_from_observed_github_surface",
        "vendored": False,
    }
    projection = {
        "input_shadow": "bitmap_or_rendered_layout_intensity_field as the 2D chart of a higher-dimensional bump map",
        "high_dimensional_bump_map": "B(u_1,...,u_n) over byte, semantic, provenance, torsion, chirality, orientation, and observer coordinates",
        "potential": "V = adapter(B); local bumps/depressions act as wells, barriers, or curvature ridges",
        "spectral_output": "eigenstate/eigenmode basis over the well field",
        "hutter_analogy": "Hutter frame roots can sample bump-map slices; spectral wells are route hints, while byte-exact replay remains primary",
        "gaussian_splat_analogy": "splat fields can seed or approximate high-dimensional bumps before spectral projection",
        "sparse_operator_path": "B(u) -> sparse Hamiltonian/Laplacian-like operator -> Spectra-selected eigenmodes",
        "safety_boundary": "visual/eigenmode similarity is a routing hint only; exact replay, source bytes, and resource envelope still gate promotion",
    }
    dependency_priors = [
        {
            "dependency": "Eigen3",
            "stack_role": "sparse bump-map operator carrier",
            "candidate_use": "represent the discretized high-dimensional bump/potential operator without dense allocation",
            "decision": "ADMIT_DEPENDENCY_PRIOR_METADATA",
        },
        {
            "dependency": "Spectra",
            "stack_role": "sparse eigen-route extractor",
            "candidate_use": "extract a small set of eigenmodes from the sparse operator as route hints",
            "decision": "ADMIT_DEPENDENCY_PRIOR_METADATA",
        },
        {
            "dependency": "OpenMP",
            "stack_role": "parallel compute warning",
            "candidate_use": "may speed local experiments but cannot bypass Hutter single-core/no-GPU prize resource gate",
            "decision": "HOLD_RESOURCE_GATE_REQUIRED",
        },
    ]
    candidates = [
        {
            "candidate_id": "rendered_glyph_high_dimensional_bump",
            "input": "rendered symbol or page layout plus semantic/provenance axes",
            "possible_use": "derive spectral route priors for dense symbol/manifold regions",
            "decision": "HOLD_ADAPTER_REQUIRED",
            "reason": "needs deterministic renderer, reversible residual, and exact byte replay",
        },
        {
            "candidate_id": "hutter_route_bump_map",
            "input": "byte, semantic, provenance, torsion, chirality, orientation, and observer-chart axes",
            "possible_use": "turn multidimensional route pressure into a bump map and look for stable wells/ridges",
            "decision": "HOLD_EXPERIMENTAL_PRIOR",
            "reason": "spectral well stability is only a route hint until replay and resource gates close",
        },
        {
            "candidate_id": "molecule_shadow_well",
            "input": "MMFF/material geometry projection rendered as intensity or occupancy",
            "possible_use": "compare local spectral signatures of projected material shadows",
            "decision": "HOLD_DOMAIN_ADAPTER_REQUIRED",
            "reason": "quantum visual analogy is not chemical/material proof",
        },
        {
            "candidate_id": "gaussian_splat_to_well_field",
            "input": "torsion-indexed Gaussian witness splats",
            "possible_use": "collapse splat cloud into potential field and inspect eigenmode drift",
            "decision": "HOLD_EXPERIMENTAL_PRIOR",
            "reason": "must prove splat-to-well map preserves witness semantics",
        },
        {
            "candidate_id": "hutter_codec_training_source",
            "input": "external PixelWell code/content",
            "possible_use": "training or dictionary source",
            "decision": "QUARANTINE_LICENSE_UNVERIFIED_FOR_INGEST",
            "reason": "no license observed on GitHub surface; do not vendor or train on it",
        },
    ]
    return {
        "schema": "pixelwell_external_prior_registry_v1",
        "external_summary": external_summary,
        "projection_equation": {
            "shadow_to_potential": "image_intensity I(x,y) -> V(x,y)",
            "bump_map_generalization": "B(u_1,...,u_n) -> V_B(u) -> spectral_route_hints",
            "sparse_operator": "V_B plus adjacency/Laplacian stencil -> sparse operator M_B",
            "well_to_modes": "H(V) psi_n = E_n psi_n",
            "admission": "A=1[deterministic_renderer] * 1[adapter_receipt] * 1[residual_replay] * 1[resource_envelope_ok]",
        },
        "canonical_statement": (
            "PixelWell is useful as a spectral-potential projection prior for high "
            "dimensional bump maps: a 2D bitmap is the toy chart, while the stack "
            "generalizes the bump field over byte, semantic, provenance, torsion, "
            "chirality, orientation, and observer coordinates. Eigenmodes are route "
            "hints only, not byte-codec proof."
        ),
        "projection": projection,
        "dependency_priors": dependency_priors,
        "candidates": candidates,
        "aggregates": {
            "candidate_count": len(candidates),
            "dependency_prior_count": len(dependency_priors),
            "hold_count": sum(1 for item in candidates if item["decision"].startswith("HOLD")),
            "quarantine_count": sum(1 for item in candidates if item["decision"].startswith("QUARANTINE")),
            "admit_count": sum(1 for item in candidates if item["decision"].startswith("ADMIT")),
        },
        "decision": "HOLD_PIXELWELL_EXTERNAL_PRIOR",
        "claim_boundary": (
            "External-prior receipt only. No PixelWell code is vendored, copied, "
            "trained on, or promoted. License is unverified from the observed GitHub "
            "surface, so ingestion remains QUARANTINE until a license/adaptor receipt exists."
        ),
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "pixelwell_external_prior_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "external_repo": EXTERNAL_REPO,
        "decision": registry["decision"],
        "aggregates": registry["aggregates"],
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# PixelWell External Prior",
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
        "## Projection Equation",
        "",
    ]
    for key, value in registry["projection_equation"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Candidates", "", "| Candidate | Decision | Reason |", "|---|---|---|"])
    for item in registry["candidates"]:
        lines.append(f"| `{item['candidate_id']}` | `{item['decision']}` | {item['reason']} |")
    lines.extend(["", "## Dependency Priors", "", "| Dependency | Stack role | Decision |", "|---|---|---|"])
    for item in registry["dependency_priors"]:
        lines.append(f"| `{item['dependency']}` | {item['stack_role']} | `{item['decision']}` |")
    lines.extend(["", "## External Links", ""])
    for key in ["repo", "readme", "script"]:
        lines.append(f"- `{key}`: {registry['external_summary'][key]}")
    lines.append(f"- `Eigen3`: {EIGEN3_URL}")
    lines.append(f"- `Spectra`: {SPECTRA_URL}")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(receipt: dict[str, Any]) -> None:
    text = f"""created: 20260509000000000
modified: 20260509000000000
tags: ResearchStack ExternalPrior PixelWell SpectralProjection Hutter HOLD Receipt
title: PixelWell External Prior
type: text/vnd.tiddlywiki

! PixelWell External Prior

External repo:

```
{EXTERNAL_REPO}
```

Durable runner:

```
4-Infrastructure/shim/pixelwell_external_prior_probe.py
```

Receipt:

```
{rel(RECEIPT)}
```

Receipt hash:

```
{receipt['receipt_hash']}
```

!! Doctrine

PixelWell is useful as a spectral-potential projection prior: a bitmap shadow can
induce a well field whose eigenmodes may become route hints. Eigen3 and Spectra
make the sparse-operator path concrete, but this remains a prior, not a byte
codec, proof of semantic structure, or ingestible dependency without
license/adaptor/resource receipts.

!! Links

* [[Gaussian Splat Manifold Projection]]
* [[Torsion Interval Gaussian Splat Witness]]
* [[Godel Gauntlet Safety Condition Probe]]
"""
    TIDDLER.write_text(text, encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    registry = build_registry()
    receipt = build_receipt(registry)
    REGISTRY.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(registry, receipt)
    write_tiddler(receipt)
    print(
        json.dumps(
            {
                "registry": rel(REGISTRY),
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "tiddler": rel(TIDDLER),
                "receipt_hash": receipt["receipt_hash"],
                "decision": receipt["decision"],
                "aggregates": registry["aggregates"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
