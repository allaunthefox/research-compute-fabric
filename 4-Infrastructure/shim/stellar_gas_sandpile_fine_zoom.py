#!/usr/bin/env python3
"""Fine-zoom object examples under the stellar-gas sandpile candidates.

This script drills from the sandpile cell diagnostic down to MaNGA Plate-IFU
examples in the avalanche-candidate cells.  It keeps the same proxy boundary as
the population study: these are observable gas/shock routing candidates, not
proof of a physical shock mechanism.
"""

from __future__ import annotations

import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
POP_SCRIPT = ROOT / "4-Infrastructure/shim/stellar_gas_population_grouping_study.py"
SANDPILE_JSON = ROOT / "shared-data/data/stellar_gas_observation/stellar_gas_abelian_sandpile_probe.json"
OUT_DIR = ROOT / "shared-data/data/stellar_gas_observation"
DOCS_DIR = ROOT / "6-Documentation/docs"
TIDDLER_DIR = ROOT / "6-Documentation/tiddlywiki-local/wiki/tiddlers"

OUT_JSON = OUT_DIR / "stellar_gas_sandpile_fine_zoom.json"
RECEIPT_JSON = OUT_DIR / "stellar_gas_sandpile_fine_zoom_receipt.json"
DOC_MD = DOCS_DIR / "stellar_gas_sandpile_fine_zoom_2026-05-09.md"
TIDDLER = TIDDLER_DIR / "Stellar Gas Sandpile Fine Zoom.tid"

EXAMPLES_PER_CELL = 8


def load_population_module():
    spec = importlib.util.spec_from_file_location("stellar_gas_population_grouping_study", POP_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {POP_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def round6(value: float | None) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return round(value, 6)


def object_pressure(row: dict[str, Any]) -> float:
    gas_sigma = row.get("gas_sigma_1re_kms") or 0.0
    stellar_sigma = row.get("stellar_sigma_1re_kms") or 0.0
    snr = row.get("snr_mean") or 0.0
    pressure = float(row.get("shock_lier_score") or 0.0)
    pressure += min(float(gas_sigma) / 250.0, 2.0)
    pressure += min(float(stellar_sigma) / 250.0, 2.0) * 0.5
    pressure += min(max(float(snr), 0.0) / 50.0, 1.0) * 0.25
    if row.get("bpt_proxy_class") == "agn_liner_or_shock_proxy":
        pressure += 0.5
    if row.get("shock_lier_proxy_class") == "shock_lier_proxy":
        pressure += 0.5
    return pressure


def compact_row(row: dict[str, Any]) -> dict[str, Any]:
    ratios = row.get("line_ratios", {})
    return {
        "plateifu": row.get("plateifu"),
        "mangaid": row.get("mangaid"),
        "ra": round6(row.get("ra")),
        "dec": round6(row.get("dec")),
        "z": round6(row.get("z")),
        "sky_z_cell": row.get("sky_z_cell"),
        "bpt_proxy_class": row.get("bpt_proxy_class"),
        "shock_lier_proxy_class": row.get("shock_lier_proxy_class"),
        "shock_lier_score": round6(row.get("shock_lier_score")),
        "gas_sigma_1re_kms": round6(row.get("gas_sigma_1re_kms")),
        "stellar_sigma_1re_kms": round6(row.get("stellar_sigma_1re_kms")),
        "snr_mean": round6(row.get("snr_mean")),
        "object_pressure": round6(object_pressure(row)),
        "line_ratios": {key: round6(value) for key, value in ratios.items()},
    }


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    pop = load_population_module()
    sandpile = load_json(SANDPILE_JSON)
    candidate_cells = [
        row["cell"]
        for row in sandpile["top_cells"]
        if row["sandpile"]["state"] == "AVALANCHE_CANDIDATE"
    ]
    candidate_set = set(candidate_cells)

    channel_index = pop.load_channels()
    by_plateifu: dict[str, dict[str, Any]] = {}
    rows_seen = 0
    rows_in_candidate_cells = 0

    for _, _, _, fields in pop.iter_rows(pop.DEFAULT_FITS):
        rows_seen += 1
        payload = pop.row_payload(fields, channel_index)
        if not payload:
            continue
        daptype = str(payload.get("daptype") or "")
        plateifu = str(payload.get("plateifu") or "")
        current = by_plateifu.get(plateifu)
        if current is None or daptype == pop.PREFERRED_DAPTYPE:
            by_plateifu[plateifu] = payload

    examples_by_cell: dict[str, list[dict[str, Any]]] = {cell: [] for cell in candidate_cells}
    for row in by_plateifu.values():
        cell = row.get("sky_z_cell")
        if cell not in candidate_set:
            continue
        rows_in_candidate_cells += 1
        examples_by_cell[cell].append(row)

    output_cells = []
    for sand_row in sandpile["top_cells"]:
        cell = sand_row["cell"]
        if cell not in candidate_set:
            continue
        examples = sorted(
            examples_by_cell[cell],
            key=lambda row: object_pressure(row),
            reverse=True,
        )[:EXAMPLES_PER_CELL]
        output_cells.append(
            {
                "cell": cell,
                "sandpile": sand_row["sandpile"],
                "channel_summary": sand_row["channels"],
                "candidate_count": len(examples_by_cell[cell]),
                "top_examples": [compact_row(row) for row in examples],
            }
        )

    created = now_iso()
    result = {
        "schema": "stellar_gas_sandpile_fine_zoom_v0",
        "created": created,
        "decision": "ADMIT_FINE_ZOOM_OBJECT_EXAMPLES_HOLD_MECHANISM_PROOF",
        "claim_boundary": (
            "Fine-zoom object examples under sandpile avalanche-candidate cells. "
            "Proxy classes and object-pressure scores route follow-up; they do "
            "not prove physical shock, AGN, stellar mass, or gas mechanism."
        ),
        "sources": {
            "sandpile_probe": str(SANDPILE_JSON.relative_to(ROOT)),
            "manga_fits": str(pop.DEFAULT_FITS.relative_to(ROOT)),
            "population_script": str(POP_SCRIPT.relative_to(ROOT)),
        },
        "rows_seen_all_daptypes": rows_seen,
        "unique_plateifu_count": len(by_plateifu),
        "candidate_cell_count": len(candidate_cells),
        "rows_in_candidate_cells": rows_in_candidate_cells,
        "examples_per_cell": EXAMPLES_PER_CELL,
        "candidate_cells": output_cells,
        "holds": [
            "HOLD_PHYSICAL_SHOCK_PROOF",
            "HOLD_DIRECT_STELLAR_MASS",
            "HOLD_DIRECT_GAS_DENSITY_INFERENCE",
            "HOLD_OBJECT_LEVEL_DESI_CROSSMATCH",
            "HOLD_COSMOLOGY_FIT",
        ],
    }
    receipt = {
        "receipt_type": "stellar_gas_sandpile_fine_zoom_receipt",
        "created": created,
        "candidate_cell_count": len(candidate_cells),
        "rows_in_candidate_cells": rows_in_candidate_cells,
        "examples_written": sum(len(cell["top_examples"]) for cell in output_cells),
        "decision": result["decision"],
        "validated_outputs": [
            str(OUT_JSON.relative_to(ROOT)),
            str(DOC_MD.relative_to(ROOT)),
            str(TIDDLER.relative_to(ROOT)),
        ],
    }
    return result, receipt


def write_docs(result: dict[str, Any]) -> None:
    cell_lines = []
    for cell in result["candidate_cells"]:
        top = cell["top_examples"][0] if cell["top_examples"] else {}
        cell_lines.append(
            f"- `{cell['cell']}`: candidates `{cell['candidate_count']}`, "
            f"top `{top.get('plateifu')}`, pressure `{top.get('object_pressure')}`, "
            f"class `{top.get('shock_lier_proxy_class')}`"
        )
    holds = "\n".join(f"- `{hold}`" for hold in result["holds"])

    DOC_MD.write_text(
        f"""# Stellar Gas Sandpile Fine Zoom

Status: `FINE_ZOOM_OBJECT_EXAMPLES`

Decision: `{result['decision']}`

This fine-zoom pass drills from sandpile avalanche-candidate cells down to MaNGA
Plate-IFU examples. It is meant to show which concrete objects carry the
strongest local proxy pressure under the cell-level eigenmass surface.

Claim boundary: proxy classes and object-pressure scores route follow-up; they
do not prove physical shock, AGN, stellar mass, gas density, or cosmology.

## Summary

```text
candidate cells:          {result['candidate_cell_count']}
candidate-cell objects:   {result['rows_in_candidate_cells']}
examples per cell:        {result['examples_per_cell']}
```

## Top Object Per Candidate Cell

{chr(10).join(cell_lines)}

## Holds

{holds}
""",
        encoding="utf-8",
    )

    TIDDLER.write_text(
        f"""title: Stellar Gas Sandpile Fine Zoom
tags: StellarGasObservation MaNGA SemanticMassNumbers Sandpile Receipts
type: text/vnd.tiddlywiki

Status: <<tag FINE_ZOOM_OBJECT_EXAMPLES>>

Decision: `{result['decision']}`

This tiddler drills from the Abelian-sandpile candidate cells into MaNGA
Plate-IFU examples.

```
candidate cells:        {result['candidate_cell_count']}
candidate-cell objects: {result['rows_in_candidate_cells']}
examples per cell:      {result['examples_per_cell']}
```

!! Top Object Per Candidate Cell

{chr(10).join(cell_lines)}

!! Boundary

These are proxy-ranked follow-up candidates, not proof of physical shock, AGN,
stellar mass, gas density, or cosmology.
""",
        encoding="utf-8",
    )


def main() -> None:
    result, receipt = build()
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT_JSON.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_docs(result)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
