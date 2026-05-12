#!/usr/bin/env python3
"""Stream the DESI EDR epoviz rows into a row-level eigenmass receipt.

This is a literal-data stress pass over the 669k-row DESI epoviz CSV.  It avoids
holding every row in memory by accumulating feature means and covariance with a
streaming Welford update, then computes a small symmetric eigendecomposition.

Boundary: this is an SMN/evidence-load mass direction over DESI epoviz rows. It
is not physical mass, not dark-energy inference, and not a gas-density map.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DESI_GZ = ROOT / "shared-data/artifacts/stellar_gas_observation/desi_epoviz/EDR-Viz-Outreach-VAC.csv.gz"
OUT_DIR = ROOT / "shared-data/data/stellar_gas_observation"
DOCS_DIR = ROOT / "6-Documentation/docs"
TIDDLER_DIR = ROOT / "6-Documentation/tiddlywiki-local/wiki/tiddlers"

OUT_JSON = OUT_DIR / "desi_epoviz_row_eigenmass_probe.json"
RECEIPT_JSON = OUT_DIR / "desi_epoviz_row_eigenmass_probe_receipt.json"
DOC_MD = DOCS_DIR / "desi_epoviz_row_eigenmass_probe_2026-05-09.md"
TIDDLER = TIDDLER_DIR / "DESI Epoviz Row Eigenmass Probe.tid"

FEATURES = [
    "x_glyr",
    "y_glyr",
    "z_glyr",
    "redshift",
    "rosette_sin",
    "rosette_cos",
    "tracer_QSO",
    "tracer_ELG",
    "tracer_LRG",
    "tracer_BGS",
]

TRACERS = {
    "0": "QSO",
    "1": "ELG",
    "2": "LRG",
    "3": "BGS",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def jacobi_eigen_symmetric(matrix: list[list[float]], max_iter: int = 300, eps: float = 1e-12) -> tuple[list[float], list[list[float]], dict[str, Any]]:
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
            angle = math.pi / 4.0
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

    return [a[i][i] for i in range(n)], v, {
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


def feature_row(row: dict[str, str]) -> list[float]:
    rosette = int(row["ROSETTE"])
    angle = 2.0 * math.pi * (rosette % 20) / 20.0
    tracer = TRACERS.get(row["TRACER"], "UNKNOWN")
    return [
        float(row["X"]),
        float(row["Y"]),
        float(row["Z"]),
        float(row["REDSHIFT"]),
        math.sin(angle),
        math.cos(angle),
        1.0 if tracer == "QSO" else 0.0,
        1.0 if tracer == "ELG" else 0.0,
        1.0 if tracer == "LRG" else 0.0,
        1.0 if tracer == "BGS" else 0.0,
    ]


def z_bin_cosmic(z: float) -> str:
    if z < 0.1:
        return "z_0_0p1"
    if z < 0.5:
        return "z_0p1_0p5"
    if z < 1.0:
        return "z_0p5_1"
    if z < 2.0:
        return "z_1_2"
    return "z_2_plus"


def round_float(x: float) -> float:
    return round(x, 9)


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    if not DESI_GZ.exists():
        raise FileNotFoundError(DESI_GZ)

    n = 0
    d = len(FEATURES)
    means = [0.0] * d
    m2 = [[0.0] * d for _ in range(d)]
    tracer_counts: Counter[str] = Counter()
    z_counts: Counter[str] = Counter()
    rosette_counts: Counter[str] = Counter()
    redshift_min = math.inf
    redshift_max = -math.inf

    with gzip.open(DESI_GZ, "rt", newline="") as f:
        reader = csv.DictReader(f)
        required = {"TARGETID", "REDSHIFT", "ROSETTE", "TRACER", "X", "Y", "Z"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing columns: {sorted(missing)}")
        for row in reader:
            x = feature_row(row)
            n += 1
            delta = [x[i] - means[i] for i in range(d)]
            for i in range(d):
                means[i] += delta[i] / n
            delta2 = [x[i] - means[i] for i in range(d)]
            for i in range(d):
                for j in range(i, d):
                    m2[i][j] += delta[i] * delta2[j]

            tracer = TRACERS.get(row["TRACER"], f"UNKNOWN_{row['TRACER']}")
            z = float(row["REDSHIFT"])
            tracer_counts[tracer] += 1
            z_counts[z_bin_cosmic(z)] += 1
            rosette_counts[row["ROSETTE"]] += 1
            redshift_min = min(redshift_min, z)
            redshift_max = max(redshift_max, z)

    cov = [[0.0] * d for _ in range(d)]
    for i in range(d):
        for j in range(i, d):
            val = m2[i][j] / (n - 1)
            cov[i][j] = val
            cov[j][i] = val

    stds = [math.sqrt(max(cov[i][i], 0.0)) or 1.0 for i in range(d)]
    corr = [[cov[i][j] / (stds[i] * stds[j]) for j in range(d)] for i in range(d)]
    values, vectors_as_columns, solver = jacobi_eigen_symmetric(corr)
    order = sorted(range(d), key=lambda i: values[i], reverse=True)
    eigenvalues = [values[i] for i in order]
    dominant = normalize([vectors_as_columns[row][order[0]] for row in range(d)])

    # Keep the direction readable: positive redshift and ELG/LRG direction.
    sign_anchor = dominant[FEATURES.index("redshift")] + dominant[FEATURES.index("tracer_ELG")] + dominant[FEATURES.index("tracer_LRG")]
    if sign_anchor < 0:
        dominant = [-x for x in dominant]
    residual = eigen_residual(corr, eigenvalues[0], dominant)

    total_positive = sum(x for x in eigenvalues if x > 0)
    explained = [x / total_positive if total_positive > 0 else 0.0 for x in eigenvalues]
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    source_hash = sha256_file(DESI_GZ)

    result = {
        "schema": "desi_epoviz_row_eigenmass_probe_v0",
        "created": created,
        "decision": "ADMIT_DESI_ROW_EIGENMASS_HOLD_PHYSICAL_MASS",
        "claim_boundary": (
            "Row eigenmass is an SMN/evidence-load direction over DESI EDR "
            "epoviz rows. It is not physical mass, not stellar mass, not a "
            "gas-density map, and not a cosmology fit."
        ),
        "source": {
            "csv_gz": str(DESI_GZ.relative_to(ROOT)),
            "sha256": source_hash,
            "doc": "https://data.desi.lbl.gov/doc/releases/edr/vac/epoviz/",
        },
        "row_count": n,
        "feature_basis": FEATURES,
        "feature_means": {name: round_float(means[i]) for i, name in enumerate(FEATURES)},
        "feature_stds": {name: round_float(stds[i]) for i, name in enumerate(FEATURES)},
        "dominant_eigenvalue": round_float(eigenvalues[0]),
        "dominant_explained_mass_share": round_float(explained[0]),
        "eigensolver_diagnostics": {
            **solver,
            "dominant_residual_l2": round(residual, 12),
            "orthogonality_note": "Jacobi rotations return an orthonormal basis up to numeric roundoff; this receipt reports the dominant residual only.",
        },
        "dominant_eigenvector": {name: round_float(dominant[i]) for i, name in enumerate(FEATURES)},
        "eigenvalues": [round_float(x) for x in eigenvalues],
        "explained_mass_share": [round_float(x) for x in explained],
        "population_counts": {
            "tracers": {k: tracer_counts[k] for k in sorted(tracer_counts)},
            "cosmic_redshift_bins": {k: z_counts[k] for k in sorted(z_counts)},
            "rosettes": {k: rosette_counts[k] for k in sorted(rosette_counts, key=lambda x: int(x))},
            "redshift_min": round_float(redshift_min),
            "redshift_max": round_float(redshift_max),
        },
        "holds": [
            "HOLD_PHYSICAL_MASS_INTERPRETATION",
            "HOLD_DIRECT_STELLAR_GAS_INFERENCE",
            "HOLD_OBJECT_LEVEL_MANGA_CROSSMATCH",
            "HOLD_SELECTION_FUNCTION_FIT",
            "HOLD_COSMOLOGY_FIT",
        ],
    }

    receipt = {
        "receipt_type": "desi_epoviz_row_eigenmass_probe_receipt",
        "created": created,
        "source_sha256": source_hash,
        "row_count": n,
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
    tracer_lines = "\n".join(
        f"- `{name}`: {value}" for name, value in result["population_counts"]["tracers"].items()
    )
    z_lines = "\n".join(
        f"- `{name}`: {value}" for name, value in result["population_counts"]["cosmic_redshift_bins"].items()
    )
    holds = "\n".join(f"- `{hold}`" for hold in result["holds"])
    diag = result["eigensolver_diagnostics"]

    DOC_MD.write_text(
        f"""# DESI Epoviz Row Eigenmass Probe

Status: `DESI_ROW_EIGENMASS`

Decision: `{result['decision']}`

This probe streams the DESI EDR epoviz CSV row-by-row and computes the dominant
correlation eigenvector over geometry, redshift, rosette phase, and tracer
identity. It is a literal-data stress pass over the DESI epoviz surface.

Claim boundary: this is SMN/evidence-load mass, not physical mass, not stellar
mass, not gas-density inference, and not a cosmology fit.

## Result

Rows read: `{result['row_count']}`

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

## Population Counts

Tracer counts:

{tracer_lines}

Cosmic redshift bins:

{z_lines}

## Holds

{holds}
""",
        encoding="utf-8",
    )

    TIDDLER.write_text(
        f"""title: DESI Epoviz Row Eigenmass Probe
tags: StellarGasObservation DESI SemanticMassNumbers Eigenvector Receipts
type: text/vnd.tiddlywiki

Status: <<tag DESI_ROW_EIGENMASS>>

Decision: `{result['decision']}`

This probe streams the DESI EDR epoviz rows directly and computes the dominant
SMN/evidence-load eigenvector over geometry, redshift, rosette phase, and tracer
identity.

Rows read: `{result['row_count']}`

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
