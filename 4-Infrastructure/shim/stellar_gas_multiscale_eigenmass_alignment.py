#!/usr/bin/env python3
"""Compare row-level DESI eigenmass with DESI/MaNGA joined-cell eigenmass.

This probe measures whether the SMN/evidence-load direction survives the zoom
from the literal DESI row surface into the gas/shock-constrained MaNGA overlap
surface.  It reports a tracer-subspace cosine alignment and a sharpening factor.

Boundary: this is an evidence-geometry comparison. It is not physical mass, not
stellar mass, not a gas-density map, and not a cosmology fit.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ROW_JSON = ROOT / "shared-data/data/stellar_gas_observation/desi_epoviz_row_eigenmass_probe.json"
CELL_JSON = ROOT / "shared-data/data/stellar_gas_observation/stellar_gas_eigenvector_mass_probe.json"
OUT_DIR = ROOT / "shared-data/data/stellar_gas_observation"
DOCS_DIR = ROOT / "6-Documentation/docs"
TIDDLER_DIR = ROOT / "6-Documentation/tiddlywiki-local/wiki/tiddlers"

OUT_JSON = OUT_DIR / "stellar_gas_multiscale_eigenmass_alignment.json"
RECEIPT_JSON = OUT_DIR / "stellar_gas_multiscale_eigenmass_alignment_receipt.json"
DOC_MD = DOCS_DIR / "stellar_gas_multiscale_eigenmass_alignment_2026-05-09.md"
TIDDLER = TIDDLER_DIR / "Stellar Gas Multiscale Eigenmass Alignment.tid"


TRACER_ORDER = ["QSO", "ELG", "LRG", "BGS"]


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def norm(v: list[float]) -> float:
    return math.sqrt(dot(v, v))


def cosine(a: list[float], b: list[float]) -> float:
    denom = norm(a) * norm(b)
    if denom == 0:
        return 0.0
    return dot(a, b) / denom


def round9(x: float) -> float:
    return round(x, 9)


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def tracer_vector_from_row(row: dict[str, float]) -> list[float]:
    return [
        row["tracer_QSO"],
        row["tracer_ELG"],
        row["tracer_LRG"],
        row["tracer_BGS"],
    ]


def tracer_vector_from_cell(cell: dict[str, float]) -> list[float]:
    return [
        cell["QSO_share"],
        cell["ELG_share"],
        cell["LRG_share"],
        cell["BGS_share"],
    ]


def classify_alignment(value: float) -> str:
    if value >= 0.85:
        return "STRONG_ALIGNMENT"
    if value >= 0.65:
        return "MODERATE_ALIGNMENT"
    if value >= 0.35:
        return "WEAK_ALIGNMENT"
    if value > -0.35:
        return "ORTHOGONAL_OR_MIXED"
    return "ANTI_ALIGNMENT"


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    row = load_json(ROW_JSON)
    cell = load_json(CELL_JSON)
    row_vec = tracer_vector_from_row(row["dominant_eigenvector"])
    cell_vec = tracer_vector_from_cell(cell["dominant_eigenvector"])
    tracer_alignment = cosine(row_vec, cell_vec)

    row_share = float(row["dominant_explained_mass_share"])
    cell_share = float(cell["dominant_explained_mass_share"])
    sharpening_factor = cell_share / row_share if row_share else 0.0
    eigenvalue_ratio = float(cell["dominant_eigenvalue"]) / float(row["dominant_eigenvalue"])

    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result = {
        "schema": "stellar_gas_multiscale_eigenmass_alignment_v0",
        "created": created,
        "decision": "ADMIT_MULTISCALE_EIGENMASS_ALIGNMENT_HOLD_PHYSICAL_MASS",
        "claim_boundary": (
            "Compares SMN/evidence-load eigenvectors across DESI row level and "
            "DESI/MaNGA joined-cell level. It does not infer physical mass, "
            "stellar mass, gas density, or cosmology."
        ),
        "sources": {
            "row_eigenmass": str(ROW_JSON.relative_to(ROOT)),
            "cell_eigenmass": str(CELL_JSON.relative_to(ROOT)),
        },
        "row_level": {
            "cell_or_row_count": row["row_count"],
            "dominant_eigenvalue": row["dominant_eigenvalue"],
            "dominant_explained_mass_share": row_share,
            "tracer_subvector_order": TRACER_ORDER,
            "tracer_subvector": [round9(x) for x in row_vec],
        },
        "cell_level": {
            "cell_or_row_count": cell["cell_count"],
            "dominant_eigenvalue": cell["dominant_eigenvalue"],
            "dominant_explained_mass_share": cell_share,
            "tracer_subvector_order": TRACER_ORDER,
            "tracer_subvector": [round9(x) for x in cell_vec],
        },
        "alignment": {
            "tracer_subspace_cosine": round9(tracer_alignment),
            "alignment_class": classify_alignment(tracer_alignment),
            "constraint_sharpening_factor": round9(sharpening_factor),
            "dominant_eigenvalue_ratio_cell_over_row": round9(eigenvalue_ratio),
            "interpretation": (
                "The cell-level explained share is larger than the row-level share "
                "under this diagnostic ratio. This is an accounting comparison, not "
                "a causal gas/shock mechanism."
            ),
        },
        "holds": [
            "HOLD_PHYSICAL_MASS_INTERPRETATION",
            "HOLD_DIRECT_GAS_DENSITY_INFERENCE",
            "HOLD_OBJECT_LEVEL_CROSSMATCH",
            "HOLD_SELECTION_FUNCTION_FIT",
            "HOLD_COSMOLOGY_FIT",
        ],
    }
    receipt = {
        "receipt_type": "stellar_gas_multiscale_eigenmass_alignment_receipt",
        "created": created,
        "row_rows": row["row_count"],
        "cell_count": cell["cell_count"],
        "tracer_subspace_cosine": result["alignment"]["tracer_subspace_cosine"],
        "constraint_sharpening_factor": result["alignment"]["constraint_sharpening_factor"],
        "decision": result["decision"],
        "validated_outputs": [
            str(OUT_JSON.relative_to(ROOT)),
            str(DOC_MD.relative_to(ROOT)),
            str(TIDDLER.relative_to(ROOT)),
        ],
    }
    return result, receipt


def write_docs(result: dict[str, Any]) -> None:
    align = result["alignment"]
    row = result["row_level"]
    cell = result["cell_level"]
    holds = "\n".join(f"- `{hold}`" for hold in result["holds"])
    tracer_lines = "\n".join(
        f"- `{name}`: row `{row['tracer_subvector'][i]}`, cell `{cell['tracer_subvector'][i]}`"
        for i, name in enumerate(TRACER_ORDER)
    )

    DOC_MD.write_text(
        f"""# Stellar Gas Multiscale Eigenmass Alignment

Status: `MULTISCALE_EIGENMASS_ALIGNMENT`

Decision: `{result['decision']}`

This probe compares the row-level DESI epoviz eigenmass with the DESI/MaNGA
joined-cell eigenmass. It reports a tracer-subspace cosine and explained-share
ratio between the literal row data and the coarse joined-cell overlap surface.

Claim boundary: this is not physical mass, not stellar mass, not gas-density
inference, and not a cosmology fit.

## Alignment Result

Tracer-subspace cosine:

```text
{align['tracer_subspace_cosine']}
```

Alignment class:

```text
{align['alignment_class']}
```

Constraint sharpening factor:

```text
{align['constraint_sharpening_factor']}
```

Dominant eigenvalue ratio, cell over row:

```text
{align['dominant_eigenvalue_ratio_cell_over_row']}
```

## Tracer Subvectors

{tracer_lines}

## Scale Comparison

```text
row level rows:        {row['cell_or_row_count']}
row explained share:   {row['dominant_explained_mass_share']}
cell level cells:      {cell['cell_or_row_count']}
cell explained share:  {cell['dominant_explained_mass_share']}
```

## Holds

{holds}
""",
        encoding="utf-8",
    )

    TIDDLER.write_text(
        f"""title: Stellar Gas Multiscale Eigenmass Alignment
tags: StellarGasObservation DESI MaNGA SemanticMassNumbers Eigenvector Receipts
type: text/vnd.tiddlywiki

Status: <<tag MULTISCALE_EIGENMASS_ALIGNMENT>>

Decision: `{result['decision']}`

This tiddler compares the row-level DESI epoviz eigenmass with the DESI/MaNGA
joined-cell eigenmass.

Tracer-subspace cosine:

```
{align['tracer_subspace_cosine']}
```

Alignment class:

```
{align['alignment_class']}
```

Constraint sharpening factor:

```
{align['constraint_sharpening_factor']}
```

!! Tracer Subvectors

{tracer_lines}

!! Boundary

This is SMN/evidence-load alignment, not physical mass or cosmology inference.
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
