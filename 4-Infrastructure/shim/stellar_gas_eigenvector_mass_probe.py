#!/usr/bin/env python3
"""Infer an SMN/evidence eigenvector mass over DESI-MaNGA population cells.

This probe treats the coarse DESI epoviz to MaNGA cell join as an evidence
matrix.  It computes the dominant covariance eigenvector with deterministic
pure-Python Jacobi iteration, then emits a receipt-bearing semantic mass surface.

Boundary: this is not physical mass, not stellar mass, and not a cosmology fit.
It is a semantic/evidence-load direction over the current joined data surface.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
JOIN_JSON = ROOT / "shared-data/data/stellar_gas_observation/desi_epoviz_manga_population_cell_join.json"
OUT_DIR = ROOT / "shared-data/data/stellar_gas_observation"
DOCS_DIR = ROOT / "6-Documentation/docs"
TIDDLER_DIR = ROOT / "6-Documentation/tiddlywiki-local/wiki/tiddlers"

OUT_JSON = OUT_DIR / "stellar_gas_eigenvector_mass_probe.json"
RECEIPT_JSON = OUT_DIR / "stellar_gas_eigenvector_mass_probe_receipt.json"
DOC_MD = DOCS_DIR / "stellar_gas_eigenvector_mass_probe_2026-05-09.md"
TIDDLER = TIDDLER_DIR / "Stellar Gas Eigenvector Mass Probe.tid"

FEATURES = [
    "log_desi_count",
    "log_manga_count",
    "partial_full_shock_fraction",
    "shock_lier_fraction",
    "BGS_share",
    "ELG_share",
    "LRG_share",
    "QSO_share",
]


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def mat_vec(m: list[list[float]], v: list[float]) -> list[float]:
    return [dot(row, v) for row in m]


def norm(v: list[float]) -> float:
    return math.sqrt(dot(v, v))


def normalize(v: list[float]) -> list[float]:
    n = norm(v)
    if n == 0:
        return [0.0 for _ in v]
    return [x / n for x in v]


def transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [list(col) for col in zip(*matrix)]


def jacobi_eigen_symmetric(matrix: list[list[float]], max_iter: int = 200, eps: float = 1e-12) -> tuple[list[float], list[list[float]]]:
    """Return eigenvalues and eigenvectors for a small symmetric matrix.

    Eigenvectors are returned as columns in the second return value.
    """

    n = len(matrix)
    a = [row[:] for row in matrix]
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

    iterations = 0
    final_max_offdiag = 0.0
    converged = False
    for iteration in range(1, max_iter + 1):
        p, q = 0, 1
        max_off = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                val = abs(a[i][j])
                if val > max_off:
                    max_off = val
                    p, q = i, j
        iterations = iteration
        final_max_offdiag = max_off
        if max_off < eps:
            converged = True
            break

        if abs(a[p][p] - a[q][q]) < eps:
            angle = math.pi / 4
        else:
            angle = 0.5 * math.atan2(2.0 * a[p][q], a[q][q] - a[p][p])
        c = math.cos(angle)
        s = math.sin(angle)

        app = c * c * a[p][p] - 2.0 * s * c * a[p][q] + s * s * a[q][q]
        aqq = s * s * a[p][p] + 2.0 * s * c * a[p][q] + c * c * a[q][q]
        a[p][p] = app
        a[q][q] = aqq
        a[p][q] = 0.0
        a[q][p] = 0.0

        for k in range(n):
            if k == p or k == q:
                continue
            akp = c * a[k][p] - s * a[k][q]
            akq = s * a[k][p] + c * a[k][q]
            a[k][p] = akp
            a[p][k] = akp
            a[k][q] = akq
            a[q][k] = akq

        for k in range(n):
            vkp = c * v[k][p] - s * v[k][q]
            vkq = s * v[k][p] + c * v[k][q]
            v[k][p] = vkp
            v[k][q] = vkq

    eigenvalues = [a[i][i] for i in range(n)]
    return eigenvalues, v, {
        "method": "jacobi_symmetric",
        "max_iter": max_iter,
        "eps": eps,
        "iterations": iterations,
        "converged": converged,
        "final_max_offdiag": final_max_offdiag,
    }


def eigen_residual(matrix: list[list[float]], eigenvalue: float, eigenvector: list[float]) -> float:
    av = mat_vec(matrix, eigenvector)
    residual = [av_i - eigenvalue * v_i for av_i, v_i in zip(av, eigenvector)]
    return norm(residual)


def build_feature_rows(join: dict[str, Any]) -> tuple[list[str], list[list[float]], list[dict[str, Any]]]:
    labels: list[str] = []
    rows: list[list[float]] = []
    payloads: list[dict[str, Any]] = []
    for cell in join["manga_join"]["top_joined_cells"]:
        mix = cell["desi_tracer_mix"]
        total = sum(float(v) for v in mix.values()) or 1.0
        labels.append(cell["cell"])
        payloads.append(cell)
        rows.append(
            [
                math.log1p(float(cell["desi_count"])),
                math.log1p(float(cell["manga_count"])),
                float(cell.get("manga_partial_or_full_shock_fraction") or 0.0),
                float(cell.get("manga_shock_lier_fraction") or 0.0),
                float(mix.get("BGS", 0.0)) / total,
                float(mix.get("ELG", 0.0)) / total,
                float(mix.get("LRG", 0.0)) / total,
                float(mix.get("QSO", 0.0)) / total,
            ]
        )
    return labels, rows, payloads


def zscore(rows: list[list[float]]) -> tuple[list[list[float]], list[float], list[float]]:
    cols = transpose(rows)
    means = [sum(col) / len(col) for col in cols]
    stds = []
    for col, mean in zip(cols, means):
        var = sum((x - mean) ** 2 for x in col) / len(col)
        std = math.sqrt(var)
        stds.append(std if std > 0 else 1.0)
    scaled = [[(x - means[i]) / stds[i] for i, x in enumerate(row)] for row in rows]
    return scaled, means, stds


def covariance(rows: list[list[float]]) -> list[list[float]]:
    n = len(rows)
    cols = len(rows[0])
    return [
        [sum(row[i] * row[j] for row in rows) / (n - 1) for j in range(cols)]
        for i in range(cols)
    ]


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    with JOIN_JSON.open() as f:
        join = json.load(f)

    labels, raw_rows, payloads = build_feature_rows(join)
    scaled_rows, means, stds = zscore(raw_rows)
    cov = covariance(scaled_rows)
    values, vectors_as_columns, solver = jacobi_eigen_symmetric(cov)

    order = sorted(range(len(values)), key=lambda i: values[i], reverse=True)
    eigenvalues = [values[i] for i in order]
    eigenvectors_by_rank = [[vectors_as_columns[row][i] for row in range(len(FEATURES))] for i in order]
    dominant = normalize(eigenvectors_by_rank[0])

    shock_index = FEATURES.index("partial_full_shock_fraction")
    if dominant[shock_index] < 0:
        dominant = [-x for x in dominant]
    residual = eigen_residual(cov, eigenvalues[0], dominant)

    scores = [dot(row, dominant) for row in scaled_rows]
    min_score = min(scores)
    shifted = [score - min_score for score in scores]
    total_shifted = sum(shifted)
    masses = [x / total_shifted if total_shifted > 0 else 1.0 / len(shifted) for x in shifted]

    cell_masses = []
    for label, payload, score, mass in zip(labels, payloads, scores, masses):
        cell_masses.append(
            {
                "cell": label,
                "eigen_score": round(score, 6),
                "normalized_eigenvector_mass": round(mass, 6),
                "desi_count": payload["desi_count"],
                "manga_count": payload["manga_count"],
                "manga_partial_or_full_shock_fraction": payload.get("manga_partial_or_full_shock_fraction"),
                "manga_shock_lier_fraction": payload.get("manga_shock_lier_fraction"),
                "desi_tracer_mix": payload["desi_tracer_mix"],
            }
        )
    cell_masses.sort(key=lambda row: row["normalized_eigenvector_mass"], reverse=True)

    total_eigen = sum(x for x in eigenvalues if x > 0)
    explained = [(x / total_eigen if total_eigen > 0 else 0.0) for x in eigenvalues]
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")

    result = {
        "schema": "stellar_gas_eigenvector_mass_probe_v0",
        "created": created,
        "decision": "ADMIT_SMN_EIGENVECTOR_MASS_HOLD_PHYSICAL_MASS",
        "claim_boundary": (
            "Eigenvector mass is an SMN/evidence-load direction over the coarse "
            "DESI epoviz to MaNGA population-cell join. It is not physical mass, "
            "not stellar mass, not a gas-density map, and not a cosmology fit."
        ),
        "source_join": str(JOIN_JSON.relative_to(ROOT)),
        "feature_basis": FEATURES,
        "feature_means": {name: round(means[i], 9) for i, name in enumerate(FEATURES)},
        "feature_stds": {name: round(stds[i], 9) for i, name in enumerate(FEATURES)},
        "cell_count": len(labels),
        "eigenvalues": [round(x, 9) for x in eigenvalues],
        "explained_mass_share": [round(x, 9) for x in explained],
        "dominant_eigenvector": {name: round(dominant[i], 9) for i, name in enumerate(FEATURES)},
        "dominant_eigenvalue": round(eigenvalues[0], 9),
        "dominant_explained_mass_share": round(explained[0], 9),
        "eigensolver_diagnostics": {
            **solver,
            "dominant_residual_l2": round(residual, 12),
            "orthogonality_note": "Jacobi rotations return an orthonormal basis up to numeric roundoff; this receipt reports the dominant residual only.",
        },
        "top_cell_masses": cell_masses[:25],
        "holds": [
            "HOLD_PHYSICAL_MASS_INTERPRETATION",
            "HOLD_OBJECT_LEVEL_CROSSMATCH",
            "HOLD_DIRECT_GAS_DENSITY_INFERENCE",
            "HOLD_SELECTION_FUNCTION_FIT",
            "HOLD_COSMOLOGY_FIT",
        ],
    }

    receipt = {
        "receipt_type": "stellar_gas_eigenvector_mass_probe_receipt",
        "created": created,
        "source_join": str(JOIN_JSON.relative_to(ROOT)),
        "cell_count": len(labels),
        "dominant_eigenvalue": result["dominant_eigenvalue"],
        "dominant_explained_mass_share": result["dominant_explained_mass_share"],
        "eigensolver_diagnostics": result["eigensolver_diagnostics"],
        "decision": result["decision"],
        "validated_outputs": [
            str(OUT_JSON.relative_to(ROOT)),
            str(DOC_MD.relative_to(ROOT)),
            str(TIDDLER.relative_to(ROOT)),
        ],
    }
    return result, receipt


def write_docs(result: dict[str, Any]) -> None:
    vector_lines = "\n".join(
        f"- `{name}`: {value}" for name, value in result["dominant_eigenvector"].items()
    )
    cell_lines = "\n".join(
        f"- `{row['cell']}`: mass `{row['normalized_eigenvector_mass']}`, "
        f"score `{row['eigen_score']}`, DESI `{row['desi_count']}`, MaNGA `{row['manga_count']}`"
        for row in result["top_cell_masses"][:10]
    )
    holds = "\n".join(f"- `{hold}`" for hold in result["holds"])
    diag = result["eigensolver_diagnostics"]

    DOC_MD.write_text(
        f"""# Stellar Gas Eigenvector Mass Probe

Status: `SMN_EIGENVECTOR_MASS`

Decision: `{result['decision']}`

This probe computes the dominant covariance eigenvector over the coarse DESI
epoviz to MaNGA population-cell join. The output is an SMN/evidence-load mass
direction: it ranks the current coarse joined cells by this diagnostic score so
later zoom work can choose explicit follow-up targets.

Claim boundary: this is not physical mass, not stellar mass, not a direct gas
density map, and not a cosmology fit.

## Result

Dominant eigenvalue:

```text
{result['dominant_eigenvalue']}
```

Dominant explained mass share:

```text
{result['dominant_explained_mass_share']}
```

## Dominant Eigenvector

{vector_lines}

## Eigensolver Diagnostics

```text
method:                 {diag['method']}
converged:              {diag['converged']}
iterations:             {diag['iterations']}
final max off-diagonal: {diag['final_max_offdiag']}
dominant residual L2:   {diag['dominant_residual_l2']}
```

## Top Cell Masses

{cell_lines}

## Holds

{holds}
""",
        encoding="utf-8",
    )

    TIDDLER.write_text(
        f"""title: Stellar Gas Eigenvector Mass Probe
tags: StellarGasObservation SemanticMassNumbers DESI MaNGA Eigenvector Receipts
type: text/vnd.tiddlywiki

Status: <<tag SMN_EIGENVECTOR_MASS>>

Decision: `{result['decision']}`

The inferred eigenvector mass is the dominant SMN/evidence-load direction over
the coarse DESI epoviz to MaNGA population-cell join.

Dominant eigenvalue:

```
{result['dominant_eigenvalue']}
```

Dominant explained mass share:

```
{result['dominant_explained_mass_share']}
```

Eigensolver:

```
converged={diag['converged']} iterations={diag['iterations']} residual_l2={diag['dominant_residual_l2']}
```

!! Dominant Eigenvector

{vector_lines}

!! Top Cell Masses

{cell_lines}

!! Boundary

This is not physical mass, not stellar mass, not direct gas-density inference,
and not a cosmology fit.
""",
        encoding="utf-8",
    )


def main() -> None:
    result, receipt = build()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    TIDDLER_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT_JSON.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_docs(result)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
