#!/usr/bin/env python3
"""Build a DESI EDR epoviz population seed and coarse MaNGA gas-cell join.

This is intentionally a coarse population prior, not an object-level crossmatch.
The DESI EDR epoviz VAC supplies sky position, redshift, rosette, and tracer
codes; the MaNGA gas grouping study supplies local gas/shock proxies.  The only
join key used here is a shared sky/redshift cell.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DESI_GZ = ROOT / "shared-data/artifacts/stellar_gas_observation/desi_epoviz/EDR-Viz-Outreach-VAC.csv.gz"
MANGA_STUDY = ROOT / "shared-data/data/stellar_gas_observation/stellar_gas_population_grouping_study.json"
OUT_DIR = ROOT / "shared-data/data/stellar_gas_observation"
DOCS_DIR = ROOT / "6-Documentation/docs"
TIDDLER_DIR = ROOT / "6-Documentation/tiddlywiki-local/wiki/tiddlers"

STUDY_JSON = OUT_DIR / "desi_epoviz_manga_population_cell_join.json"
RECEIPT_JSON = OUT_DIR / "desi_epoviz_manga_population_cell_join_receipt.json"
DOC_MD = DOCS_DIR / "desi_epoviz_manga_population_cell_join_2026-05-09.md"
TIDDLER = TIDDLER_DIR / "DESI Epoviz MaNGA Population Cell Join.tid"

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


def z_bin_local(z: float) -> str:
    if z < 0.02:
        return "z_000_002"
    if z < 0.04:
        return "z_002_004"
    if z < 0.06:
        return "z_004_006"
    if z < 0.08:
        return "z_006_008"
    return "z_008_plus"


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


def sky_bin(ra: float, dec: float) -> str:
    sector = int(ra // 60)
    if sector < 0:
        sector = 0
    if sector > 5:
        sector = 5
    hemi = "north" if dec >= 0 else "south"
    return f"ra{sector:02d}_{hemi}"


def round6(x: float | None) -> float | None:
    if x is None:
        return None
    return round(x, 6)


def summarize(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "max": None, "mean": None}
    return {
        "count": len(values),
        "min": round6(min(values)),
        "max": round6(max(values)),
        "mean": round6(sum(values) / len(values)),
    }


def counter_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def load_manga_cells() -> dict[str, dict[str, Any]]:
    with MANGA_STUDY.open() as f:
        data = json.load(f)
    cells = data["groups"]["by_sky_z_cell"]
    return {cell: payload for cell, payload in cells.items()}


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    if not DESI_GZ.exists():
        raise FileNotFoundError(f"missing DESI epoviz artifact: {DESI_GZ}")
    if not MANGA_STUDY.exists():
        raise FileNotFoundError(f"missing MaNGA grouping study: {MANGA_STUDY}")

    manga_cells = load_manga_cells()
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    source_hash = sha256_file(DESI_GZ)

    tracer_counts: Counter[str] = Counter()
    rosette_counts: Counter[str] = Counter()
    local_z_counts: Counter[str] = Counter()
    cosmic_z_counts: Counter[str] = Counter()
    sky_counts: Counter[str] = Counter()
    sky_z_counts: dict[str, Counter[str]] = defaultdict(Counter)
    z_by_tracer: dict[str, list[float]] = defaultdict(list)
    redshifts: list[float] = []
    row_count = 0

    with gzip.open(DESI_GZ, "rt", newline="") as f:
        reader = csv.DictReader(f)
        required = {"TARGETID", "RA", "DEC", "REDSHIFT", "ROSETTE", "TRACER"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing DESI epoviz columns: {sorted(missing)}")
        for row in reader:
            row_count += 1
            ra = float(row["RA"])
            dec = float(row["DEC"])
            z = float(row["REDSHIFT"])
            tracer_code = row["TRACER"]
            tracer = TRACERS.get(tracer_code, f"UNKNOWN_{tracer_code}")
            local_bin = z_bin_local(z)
            cosmic_bin = z_bin_cosmic(z)
            sky = sky_bin(ra, dec)
            cell = f"{sky}__{local_bin}"

            tracer_counts[tracer] += 1
            rosette_counts[row["ROSETTE"]] += 1
            local_z_counts[local_bin] += 1
            cosmic_z_counts[cosmic_bin] += 1
            sky_counts[sky] += 1
            sky_z_counts[cell]["count"] += 1
            sky_z_counts[cell][f"tracer_{tracer}"] += 1
            z_by_tracer[tracer].append(z)
            redshifts.append(z)

    joined_cells: list[dict[str, Any]] = []
    for cell, manga in manga_cells.items():
        desi = sky_z_counts.get(cell, Counter())
        if not desi:
            continue
        desi_count = desi["count"]
        tracer_mix = {
            key.removeprefix("tracer_"): value
            for key, value in sorted(desi.items())
            if key.startswith("tracer_")
        }
        joined_cells.append(
            {
                "cell": cell,
                "desi_count": desi_count,
                "desi_tracer_mix": tracer_mix,
                "manga_count": manga["count"],
                "manga_partial_or_full_shock_fraction": manga.get("partial_or_full_shock_fraction"),
                "manga_shock_lier_fraction": manga.get("shock_lier_fraction"),
                "join_status": "COARSE_SKY_REDSHIFT_CELL_OVERLAP",
            }
        )

    joined_cells.sort(
        key=lambda item: (
            item["desi_count"] * item["manga_count"],
            item["manga_partial_or_full_shock_fraction"] or 0,
        ),
        reverse=True,
    )

    desi_top_cells = []
    for cell, payload in sorted(sky_z_counts.items(), key=lambda kv: kv[1]["count"], reverse=True)[:25]:
        tracer_mix = {
            key.removeprefix("tracer_"): value
            for key, value in sorted(payload.items())
            if key.startswith("tracer_")
        }
        desi_top_cells.append(
            {
                "cell": cell,
                "count": payload["count"],
                "tracer_mix": tracer_mix,
            }
        )

    study = {
        "schema": "desi_epoviz_manga_population_cell_join_v0",
        "created": created,
        "decision": "ADMIT_COARSE_CELL_PRIOR_HOLD_OBJECT_CROSSMATCH",
        "claim_boundary": (
            "Uses DESI EDR epoviz as a population prior and joins to MaNGA only by "
            "coarse sky/redshift cells. This is not an object-level crossmatch, not "
            "a direct stellar gas map, and not a cosmology fit."
        ),
        "sources": {
            "desi_epoviz_csv_gz": str(DESI_GZ.relative_to(ROOT)),
            "desi_epoviz_sha256": source_hash,
            "desi_epoviz_doc": "https://data.desi.lbl.gov/doc/releases/edr/vac/epoviz/",
            "manga_population_study": str(MANGA_STUDY.relative_to(ROOT)),
        },
        "desi_population": {
            "row_count": row_count,
            "tracer_counts": counter_dict(tracer_counts),
            "local_redshift_bins": counter_dict(local_z_counts),
            "cosmic_redshift_bins": counter_dict(cosmic_z_counts),
            "sky_bins": counter_dict(sky_counts),
            "rosette_counts": counter_dict(rosette_counts),
            "redshift_summary": summarize(redshifts),
            "redshift_summary_by_tracer": {
                tracer: summarize(vals) for tracer, vals in sorted(z_by_tracer.items())
            },
            "top_sky_z_cells": desi_top_cells,
        },
        "manga_join": {
            "manga_cell_count": len(manga_cells),
            "joined_cell_count": len(joined_cells),
            "join_key": "sky_bin + local_redshift_bin",
            "join_key_shape": "raXX_north_or_south__z_000_002/z_002_004/z_004_006/z_006_008/z_008_plus",
            "top_joined_cells": joined_cells[:25],
        },
        "holds": [
            "HOLD_OBJECT_LEVEL_CROSSMATCH",
            "HOLD_DIRECT_GAS_DENSITY_INFERENCE",
            "HOLD_SELECTION_FUNCTION_FIT",
            "HOLD_COSMOLOGY_FIT",
        ],
    }

    receipt = {
        "receipt_type": "desi_epoviz_manga_population_cell_join_receipt",
        "created": created,
        "source_sha256": source_hash,
        "rows_seen": row_count,
        "joined_cell_count": len(joined_cells),
        "decision": study["decision"],
        "validated_outputs": [
            str(STUDY_JSON.relative_to(ROOT)),
            str(DOC_MD.relative_to(ROOT)),
            str(TIDDLER.relative_to(ROOT)),
        ],
    }
    return study, receipt


def write_docs(study: dict[str, Any]) -> None:
    pop = study["desi_population"]
    join = study["manga_join"]
    top_join = join["top_joined_cells"][:8]
    top_lines = "\n".join(
        f"- `{row['cell']}`: DESI {row['desi_count']}, MaNGA {row['manga_count']}, "
        f"shock proxy {row['manga_partial_or_full_shock_fraction']}"
        for row in top_join
    )
    tracer_lines = "\n".join(
        f"- `{name}`: {count}" for name, count in pop["tracer_counts"].items()
    )
    redshift_lines = "\n".join(
        f"- `{name}`: {count}" for name, count in pop["local_redshift_bins"].items()
    )

    DOC_MD.write_text(
        f"""# DESI Epoviz to MaNGA Population Cell Join

Status: `COARSE_CELL_PRIOR`

Decision: `{study['decision']}`

This note uses the DESI EDR epoviz visualization/outreach VAC as a lightweight
population prior and compares it with the local MaNGA stellar-gas grouping study
by shared sky/redshift cells.

Claim boundary: this is not an object-level crossmatch, not a direct gas-density
map, and not a cosmology fit. It is a population-shape prior for deciding where
the stellar-gas model has local support and where it should stay in `HOLD`.

## Source

- DESI EDR epoviz CSV: `{study['sources']['desi_epoviz_csv_gz']}`
- DESI source hash: `{study['sources']['desi_epoviz_sha256']}`
- DESI documentation: {study['sources']['desi_epoviz_doc']}
- MaNGA grouping study: `{study['sources']['manga_population_study']}`

## DESI Population

Rows read: `{pop['row_count']}`

Tracer counts:

{tracer_lines}

Local redshift bins used for MaNGA overlap:

{redshift_lines}

Redshift summary:

```json
{json.dumps(pop['redshift_summary'], indent=2)}
```

## Coarse Join

Join key:

```text
{join['join_key_shape']}
```

Joined cells: `{join['joined_cell_count']}` out of `{join['manga_cell_count']}` MaNGA cells.

Top joined cells:

{top_lines}

## Holds

{chr(10).join(f'- `{hold}`' for hold in study['holds'])}
""",
        encoding="utf-8",
    )

    TIDDLER.write_text(
        f"""title: DESI Epoviz MaNGA Population Cell Join
tags: StellarGasObservation DESI MaNGA SemanticMassNumbers Receipts
type: text/vnd.tiddlywiki

Status: <<tag COARSE_CELL_PRIOR>>

Decision: `{study['decision']}`

This tiddler records a coarse population overlap between the DESI EDR epoviz
catalog and the MaNGA stellar-gas grouping study.

It uses the shared key:

```
{join['join_key_shape']}
```

Rows read from DESI epoviz: `{pop['row_count']}`

Joined MaNGA cells: `{join['joined_cell_count']}` / `{join['manga_cell_count']}`

This is not an object-level crossmatch and not a direct stellar-gas density map.
It is a prior surface for deciding where the SMN / stellar-gas model has enough
population support to zoom in.

!! Tracer Counts

{tracer_lines}

!! Top Joined Cells

{top_lines}

!! Holds

{chr(10).join(f'* `{hold}`' for hold in study['holds'])}
""",
        encoding="utf-8",
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    TIDDLER_DIR.mkdir(parents=True, exist_ok=True)

    study, receipt = build()
    STUDY_JSON.write_text(json.dumps(study, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT_JSON.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_docs(study)

    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
