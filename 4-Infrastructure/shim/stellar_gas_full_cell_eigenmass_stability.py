#!/usr/bin/env python3
"""Full-cell eigenmass stability and ablation controls.

This probe reuses the existing DESI epoviz to MaNGA population-cell join and
checks whether the 25-cell SMN/evidence-load eigenvector remains stable across
all joined cells, leave-one-cell-out slices, deterministic null shuffles, and
feature ablations.

Boundary: this is evidence-geometry quality control. It is not physical mass,
not gas density, not shock proof, and not cosmology.
"""

from __future__ import annotations

import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
JOIN_JSON = ROOT / "shared-data/data/stellar_gas_observation/desi_epoviz_manga_population_cell_join.json"
BASELINE_JSON = ROOT / "shared-data/data/stellar_gas_observation/stellar_gas_eigenvector_mass_probe.json"
OUT_DIR = ROOT / "shared-data/data/stellar_gas_observation"
DOCS_DIR = ROOT / "6-Documentation/docs"
TIDDLER_DIR = ROOT / "6-Documentation/tiddlywiki-local/wiki/tiddlers"

OUT_JSON = OUT_DIR / "stellar_gas_full_cell_eigenmass_stability.json"
RECEIPT_JSON = OUT_DIR / "stellar_gas_full_cell_eigenmass_stability_receipt.json"
DOC_MD = DOCS_DIR / "stellar_gas_full_cell_eigenmass_stability_2026-05-09.md"
TIDDLER = TIDDLER_DIR / "Stellar Gas Full Cell Eigenmass Stability.tid"

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

SHOCK_FEATURES = {"partial_full_shock_fraction", "shock_lier_fraction"}
TRACER_FEATURES = {"BGS_share", "ELG_share", "LRG_share", "QSO_share"}


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def norm(v: list[float]) -> float:
    return math.sqrt(dot(v, v))


def normalize(v: list[float]) -> list[float]:
    n = norm(v)
    if n == 0:
        return [0.0 for _ in v]
    return [x / n for x in v]


def cosine(a: list[float], b: list[float]) -> float:
    denom = norm(a) * norm(b)
    if denom == 0:
        return 0.0
    return dot(a, b) / denom


def transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [list(col) for col in zip(*matrix)]


def round9(value: float) -> float:
    return round(value, 9)


def jacobi_eigen_symmetric(matrix: list[list[float]], max_iter: int = 240, eps: float = 1e-12) -> tuple[list[float], list[list[float]], dict[str, Any]]:
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


def mat_vec(m: list[list[float]], v: list[float]) -> list[float]:
    return [dot(row, v) for row in m]


def eigen_residual(matrix: list[list[float]], eigenvalue: float, eigenvector: list[float]) -> float:
    av = mat_vec(matrix, eigenvector)
    residual = [av_i - eigenvalue * v_i for av_i, v_i in zip(av, eigenvector)]
    return norm(residual)


def zscore(rows: list[list[float]]) -> tuple[list[list[float]], list[float], list[float]]:
    cols = transpose(rows)
    means = [sum(col) / len(col) for col in cols]
    stds = []
    for col, mean in zip(cols, means):
        var = sum((x - mean) ** 2 for x in col) / len(col)
        std = math.sqrt(var)
        stds.append(std if std > 0 else 1.0)
    return [[(x - means[i]) / stds[i] for i, x in enumerate(row)] for row in rows], means, stds


def covariance(rows: list[list[float]]) -> list[list[float]]:
    n = len(rows)
    cols = len(rows[0])
    return [
        [sum(row[i] * row[j] for row in rows) / (n - 1) for j in range(cols)]
        for i in range(cols)
    ]


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def source_rows(join: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for cell in join["manga_join"]["top_joined_cells"]:
        mix = cell["desi_tracer_mix"]
        total = sum(float(v) for v in mix.values()) or 1.0
        rows.append(
            {
                "cell": cell["cell"],
                "payload": cell,
                "features": {
                    "log_desi_count": math.log1p(float(cell["desi_count"])),
                    "log_manga_count": math.log1p(float(cell["manga_count"])),
                    "partial_full_shock_fraction": float(cell.get("manga_partial_or_full_shock_fraction") or 0.0),
                    "shock_lier_fraction": float(cell.get("manga_shock_lier_fraction") or 0.0),
                    "BGS_share": float(mix.get("BGS", 0.0)) / total,
                    "ELG_share": float(mix.get("ELG", 0.0)) / total,
                    "LRG_share": float(mix.get("LRG", 0.0)) / total,
                    "QSO_share": float(mix.get("QSO", 0.0)) / total,
                },
            }
        )
    return rows


def permuted(values: list[Any], seed: int) -> list[Any]:
    out = values[:]
    random.Random(seed).shuffle(out)
    return out


def vector_for_features(row: dict[str, Any], features: list[str]) -> list[float]:
    return [float(row["features"][feature]) for feature in features]


def fit_eigenmass(rows: list[dict[str, Any]], features: list[str], baseline_vector: dict[str, float] | None = None) -> dict[str, Any]:
    labels = [row["cell"] for row in rows]
    raw_rows = [vector_for_features(row, features) for row in rows]
    scaled_rows, means, stds = zscore(raw_rows)
    cov = covariance(scaled_rows)
    values, vectors_as_columns, solver = jacobi_eigen_symmetric(cov)
    order = sorted(range(len(values)), key=lambda i: values[i], reverse=True)
    eigenvalues = [values[i] for i in order]
    dominant = normalize([vectors_as_columns[row][order[0]] for row in range(len(features))])

    if baseline_vector is None:
        if "partial_full_shock_fraction" in features:
            anchor = dominant[features.index("partial_full_shock_fraction")]
        else:
            anchor = sum(dominant)
        if anchor < 0:
            dominant = [-x for x in dominant]
    else:
        common = [feature for feature in features if feature in baseline_vector]
        candidate_common = [dominant[features.index(feature)] for feature in common]
        baseline_common = [baseline_vector[feature] for feature in common]
        if dot(candidate_common, baseline_common) < 0:
            dominant = [-x for x in dominant]
    residual = eigen_residual(cov, eigenvalues[0], dominant)

    scores = [dot(row, dominant) for row in scaled_rows]
    min_score = min(scores)
    shifted = [score - min_score for score in scores]
    total_shifted = sum(shifted)
    masses = [x / total_shifted if total_shifted > 0 else 1.0 / len(shifted) for x in shifted]
    cell_masses = [
        {
            "cell": label,
            "eigen_score": round(score, 6),
            "normalized_eigenvector_mass": round(mass, 6),
        }
        for label, score, mass in zip(labels, scores, masses)
    ]
    cell_masses.sort(key=lambda row: row["normalized_eigenvector_mass"], reverse=True)

    total_eigen = sum(x for x in eigenvalues if x > 0)
    explained = [(x / total_eigen if total_eigen > 0 else 0.0) for x in eigenvalues]
    return {
        "cell_count": len(rows),
        "feature_basis": features,
        "feature_means": {name: round9(means[i]) for i, name in enumerate(features)},
        "feature_stds": {name: round9(stds[i]) for i, name in enumerate(features)},
        "dominant_eigenvalue": round9(eigenvalues[0]),
        "dominant_explained_mass_share": round9(explained[0]),
        "eigensolver_diagnostics": {
            **solver,
            "dominant_residual_l2": round(residual, 12),
            "orthogonality_note": "Jacobi rotations return an orthonormal basis up to numeric roundoff; this receipt reports the dominant residual only.",
        },
        "dominant_eigenvector": {name: round9(dominant[i]) for i, name in enumerate(features)},
        "eigenvalues": [round9(x) for x in eigenvalues],
        "explained_mass_share": [round9(x) for x in explained],
        "top_cell_masses": cell_masses,
    }


def compare_to_baseline(candidate: dict[str, Any], baseline: dict[str, Any], top_n: int = 5) -> dict[str, Any]:
    common = [feature for feature in FEATURES if feature in candidate["dominant_eigenvector"] and feature in baseline["dominant_eigenvector"]]
    cand_vec = [candidate["dominant_eigenvector"][feature] for feature in common]
    base_vec = [baseline["dominant_eigenvector"][feature] for feature in common]
    base_top = {row["cell"] for row in baseline["top_cell_masses"][:top_n]}
    cand_top = {row["cell"] for row in candidate["top_cell_masses"][:top_n]}
    return {
        "common_feature_basis": common,
        "common_basis_cosine_to_original": round9(cosine(cand_vec, base_vec)),
        "dominant_explained_share_delta": round9(candidate["dominant_explained_mass_share"] - baseline["dominant_explained_mass_share"]),
        "top_cell_overlap_at_5": len(base_top & cand_top),
        "top_cell_overlap_fraction_at_5": round9(len(base_top & cand_top) / top_n),
    }


def summarize_leave_one_out(values: list[dict[str, Any]]) -> dict[str, Any]:
    cosines = sorted(row["common_basis_cosine_to_original"] for row in values)
    overlaps = [row["top_cell_overlap_fraction_at_5"] for row in values]
    return {
        "loo_count": len(values),
        "min_cosine_to_original": round9(cosines[0]),
        "median_cosine_to_original": round9(cosines[len(cosines) // 2]),
        "mean_cosine_to_original": round9(sum(cosines) / len(cosines)),
        "mean_top5_overlap_fraction": round9(sum(overlaps) / len(overlaps)),
    }


def with_shuffled_feature_columns(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    shuffled_columns = {
        feature: permuted([row["features"][feature] for row in rows], seed=2026050901 + idx)
        for idx, feature in enumerate(FEATURES)
    }
    out = []
    for idx, row in enumerate(rows):
        clone = {"cell": row["cell"], "payload": row["payload"], "features": dict(row["features"])}
        for feature in FEATURES:
            clone["features"][feature] = shuffled_columns[feature][idx]
        out.append(clone)
    return out


def with_shuffled_shocks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    partial = permuted([row["features"]["partial_full_shock_fraction"] for row in rows], seed=2026050902)
    lier = permuted([row["features"]["shock_lier_fraction"] for row in rows], seed=2026050903)
    out = []
    for idx, row in enumerate(rows):
        clone = {"cell": row["cell"], "payload": row["payload"], "features": dict(row["features"])}
        clone["features"]["partial_full_shock_fraction"] = partial[idx]
        clone["features"]["shock_lier_fraction"] = lier[idx]
        out.append(clone)
    return out


def control_result(name: str, rows: list[dict[str, Any]], features: list[str], baseline: dict[str, Any]) -> dict[str, Any]:
    fit = fit_eigenmass(rows, features, baseline["dominant_eigenvector"])
    return {
        "control": name,
        "cell_count": fit["cell_count"],
        "feature_basis": fit["feature_basis"],
        "dominant_eigenvalue": fit["dominant_eigenvalue"],
        "dominant_explained_mass_share": fit["dominant_explained_mass_share"],
        "dominant_eigenvector": fit["dominant_eigenvector"],
        "comparison_to_original": compare_to_baseline(fit, baseline),
        "top_cell_masses": fit["top_cell_masses"][:10],
    }


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    join = load_json(JOIN_JSON)
    stored = load_json(BASELINE_JSON)
    rows = source_rows(join)
    baseline = fit_eigenmass(rows, FEATURES)

    stored_compare = compare_to_baseline(baseline, stored, top_n=5)
    stored_vector_abs_delta = {
        feature: round9(abs(baseline["dominant_eigenvector"][feature] - stored["dominant_eigenvector"][feature]))
        for feature in FEATURES
    }

    loo_rows = []
    for cell in [row["cell"] for row in rows]:
        subset = [row for row in rows if row["cell"] != cell]
        fit = fit_eigenmass(subset, FEATURES, baseline["dominant_eigenvector"])
        comparison = compare_to_baseline(fit, baseline)
        loo_rows.append(
            {
                "held_out_cell": cell,
                "dominant_explained_mass_share": fit["dominant_explained_mass_share"],
                **comparison,
            }
        )

    controls = [
        control_result("shuffled_feature_columns", with_shuffled_feature_columns(rows), FEATURES, baseline),
        control_result("shuffled_shock_channels", with_shuffled_shocks(rows), FEATURES, baseline),
        control_result("desi_count_removed", rows, [feature for feature in FEATURES if feature != "log_desi_count"], baseline),
        control_result("shock_proxy_removed", rows, [feature for feature in FEATURES if feature not in SHOCK_FEATURES], baseline),
        control_result("tracer_mix_removed", rows, [feature for feature in FEATURES if feature not in TRACER_FEATURES], baseline),
    ]

    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result = {
        "schema": "stellar_gas_full_cell_eigenmass_stability_v0",
        "created": created,
        "decision": "REPORT_FULL_CELL_EIGENMASS_STABILITY_WITH_NULL_CONTROLS_HOLD_PHYSICAL_CLAIMS",
        "claim_boundary": (
            "Full-cell stability and ablation controls for the joined DESI/MaNGA "
            "SMN/evidence-load eigenvector. This does not promote physical mass, "
            "gas density, shock proof, or cosmology."
        ),
        "sources": {
            "join": str(JOIN_JSON.relative_to(ROOT)),
            "stored_25_cell_probe": str(BASELINE_JSON.relative_to(ROOT)),
        },
        "full_cell_baseline": baseline,
        "stored_25_cell_comparison": {
            "stored_cell_count": stored["cell_count"],
            "recomputed_cell_count": baseline["cell_count"],
            "common_basis_cosine_to_stored": stored_compare["common_basis_cosine_to_original"],
            "top_cell_overlap_at_5": stored_compare["top_cell_overlap_at_5"],
            "max_abs_eigenvector_component_delta": round9(max(stored_vector_abs_delta.values())),
            "abs_eigenvector_component_delta": stored_vector_abs_delta,
        },
        "leave_one_cell_out_stability": {
            "summary": summarize_leave_one_out(loo_rows),
            "rows": loo_rows,
        },
        "null_and_ablation_controls": controls,
        "holds": [
            "HOLD_PHYSICAL_MASS_INTERPRETATION",
            "HOLD_DIRECT_GAS_DENSITY_INFERENCE",
            "HOLD_SHOCK_PROOF",
            "HOLD_OBJECT_LEVEL_CROSSMATCH",
            "HOLD_SELECTION_FUNCTION_FIT",
            "HOLD_COSMOLOGY_FIT",
        ],
    }
    receipt = {
        "receipt_type": "stellar_gas_full_cell_eigenmass_stability_receipt",
        "created": created,
        "source_join": str(JOIN_JSON.relative_to(ROOT)),
        "stored_25_cell_probe": str(BASELINE_JSON.relative_to(ROOT)),
        "full_cell_count": baseline["cell_count"],
        "stored_25_cell_count": stored["cell_count"],
        "stored_comparison_cosine": result["stored_25_cell_comparison"]["common_basis_cosine_to_stored"],
        "leave_one_out_min_cosine": result["leave_one_cell_out_stability"]["summary"]["min_cosine_to_original"],
        "control_names": [control["control"] for control in controls],
        "eigensolver_diagnostics": baseline["eigensolver_diagnostics"],
        "decision": result["decision"],
        "validated_outputs": [
            str(OUT_JSON.relative_to(ROOT)),
            str(DOC_MD.relative_to(ROOT)),
            str(TIDDLER.relative_to(ROOT)),
        ],
    }
    return result, receipt


def write_docs(result: dict[str, Any]) -> None:
    baseline = result["full_cell_baseline"]
    stored = result["stored_25_cell_comparison"]
    loo = result["leave_one_cell_out_stability"]["summary"]
    controls = result["null_and_ablation_controls"]
    diag = baseline["eigensolver_diagnostics"]
    vector_lines = "\n".join(
        f"- `{name}`: {value}" for name, value in baseline["dominant_eigenvector"].items()
    )
    control_lines = "\n".join(
        "- `{control}`: cosine `{cosine}`, explained share `{share}`, top5 overlap `{overlap}`".format(
            control=control["control"],
            cosine=control["comparison_to_original"]["common_basis_cosine_to_original"],
            share=control["dominant_explained_mass_share"],
            overlap=control["comparison_to_original"]["top_cell_overlap_fraction_at_5"],
        )
        for control in controls
    )
    holds = "\n".join(f"- `{hold}`" for hold in result["holds"])

    DOC_MD.write_text(
        f"""# Stellar Gas Full Cell Eigenmass Stability

Status: `FULL_CELL_EIGENMASS_STABILITY`

Decision: `{result['decision']}`

This probe checks the 25-cell DESI/MaNGA joined-cell eigenmass against all
available joined cells, leave-one-cell-out slices, deterministic null shuffles,
and feature ablations.

Claim boundary: this is evidence-geometry quality control only. It does not
promote physical mass, gas density, shock proof, object-level crossmatch, or
cosmology.

## Full-Cell Baseline

Cell count: `{baseline['cell_count']}`

Dominant eigenvalue:

```text
{baseline['dominant_eigenvalue']}
```

Dominant explained mass share:

```text
{baseline['dominant_explained_mass_share']}
```

Dominant eigenvector:

{vector_lines}

## Stored 25-Cell Comparison

```text
common-basis cosine to stored probe: {stored['common_basis_cosine_to_stored']}
top-cell overlap at 5:              {stored['top_cell_overlap_at_5']}
max abs component delta:            {stored['max_abs_eigenvector_component_delta']}
```

## Eigensolver Diagnostics

```text
method:                 {diag['method']}
converged:              {diag['converged']}
iterations:             {diag['iterations']}
final max off-diagonal: {diag['final_max_offdiag']}
dominant residual L2:   {diag['dominant_residual_l2']}
```

## Leave-One-Cell-Out Stability

```text
loo count:                 {loo['loo_count']}
min cosine to original:    {loo['min_cosine_to_original']}
median cosine to original: {loo['median_cosine_to_original']}
mean cosine to original:   {loo['mean_cosine_to_original']}
mean top5 overlap:         {loo['mean_top5_overlap_fraction']}
```

## Null And Ablation Controls

{control_lines}

## Holds

{holds}
""",
        encoding="utf-8",
    )

    TIDDLER.write_text(
        f"""title: Stellar Gas Full Cell Eigenmass Stability
tags: StellarGasObservation DESI MaNGA Eigenvector Controls Receipts
type: text/vnd.tiddlywiki

Status: <<tag FULL_CELL_EIGENMASS_STABILITY>>

Decision: `{result['decision']}`

This tiddler records a full-cell stability and null-control check for the
DESI/MaNGA joined-cell SMN/evidence-load eigenvector.

Cell count: `{baseline['cell_count']}`

Stored 25-cell cosine:

```
{stored['common_basis_cosine_to_stored']}
```

Leave-one-cell-out minimum cosine:

```
{loo['min_cosine_to_original']}
```

Eigensolver:

```
converged={diag['converged']} iterations={diag['iterations']} residual_l2={diag['dominant_residual_l2']}
```

!! Original Dominant Eigenvector

{vector_lines}

!! Null And Ablation Controls

{control_lines}

!! Boundary

This is evidence-geometry quality control only. It is not physical mass, gas
density, shock proof, or cosmology.
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
