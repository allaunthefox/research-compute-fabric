#!/usr/bin/env python3
"""Treat stellar-gas eigenmass cells as an Abelian-sandpile-style diagnostic.

The metaphor is operationalized carefully:

* "grains" are normalized SMN/evidence eigenmass in a sky/redshift cell.
* "toppling pressure" is a standardized mix of gas/shock propagation channels.
* "avalanche candidates" are cells with both high eigenmass and high pressure.

Boundary: this is a routing/diagnostic model over observational proxies. It is
not a physical sandpile simulation, not stellar mass, and not cosmology.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MASS_JSON = ROOT / "shared-data/data/stellar_gas_observation/stellar_gas_eigenvector_mass_probe.json"
GROUP_JSON = ROOT / "shared-data/data/stellar_gas_observation/stellar_gas_population_grouping_study.json"
OUT_DIR = ROOT / "shared-data/data/stellar_gas_observation"
DOCS_DIR = ROOT / "6-Documentation/docs"
TIDDLER_DIR = ROOT / "6-Documentation/tiddlywiki-local/wiki/tiddlers"

OUT_JSON = OUT_DIR / "stellar_gas_abelian_sandpile_probe.json"
RECEIPT_JSON = OUT_DIR / "stellar_gas_abelian_sandpile_probe_receipt.json"
DOC_MD = DOCS_DIR / "stellar_gas_abelian_sandpile_probe_2026-05-09.md"
TIDDLER = TIDDLER_DIR / "Stellar Gas Abelian Sandpile Probe.tid"


CHANNELS = [
    "log_desi_count",
    "log_manga_count",
    "partial_full_shock_fraction",
    "shock_lier_fraction",
    "shock_score_mean",
    "gas_sigma_mean",
    "gas_sigma_p90",
    "stellar_sigma_mean",
    "snr_mean",
    "agn_liner_or_shock_fraction",
    "star_forming_fraction",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def pearson(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or len(a) < 2:
        return 0.0
    ma = sum(a) / len(a)
    mb = sum(b) / len(b)
    va = [x - ma for x in a]
    vb = [x - mb for x in b]
    den = math.sqrt(sum(x * x for x in va) * sum(y * y for y in vb))
    return sum(x * y for x, y in zip(va, vb)) / den if den else 0.0


def mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 1.0
    mean = sum(values) / len(values)
    var = sum((x - mean) ** 2 for x in values) / len(values)
    std = math.sqrt(var)
    return mean, std if std else 1.0


def zscore(values: list[float]) -> list[float]:
    mean, std = mean_std(values)
    return [(x - mean) / std for x in values]


def round9(x: float) -> float:
    return round(x, 9)


def cell_channels(mass_row: dict[str, Any], group_row: dict[str, Any]) -> dict[str, float]:
    count = float(group_row["count"])
    bpt = group_row.get("bpt_proxy_classes", {})
    gas = group_row.get("gas_sigma_summary", {})
    stellar = group_row.get("stellar_sigma_summary", {})
    snr = group_row.get("snr_summary", {})
    shock = group_row.get("shock_score_summary", {})
    return {
        "log_desi_count": math.log1p(float(mass_row["desi_count"])),
        "log_manga_count": math.log1p(float(mass_row["manga_count"])),
        "partial_full_shock_fraction": float(group_row.get("partial_or_full_shock_fraction") or 0.0),
        "shock_lier_fraction": float(group_row.get("shock_lier_fraction") or 0.0),
        "shock_score_mean": float(shock.get("mean") or 0.0),
        "gas_sigma_mean": float(gas.get("mean") or 0.0),
        "gas_sigma_p90": float(gas.get("p90") or 0.0),
        "stellar_sigma_mean": float(stellar.get("mean") or 0.0),
        "snr_mean": float(snr.get("mean") or 0.0),
        "agn_liner_or_shock_fraction": safe_div(float(bpt.get("agn_liner_or_shock_proxy", 0)), count),
        "star_forming_fraction": safe_div(float(bpt.get("star_forming_proxy", 0)), count),
    }


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    mass = load_json(MASS_JSON)
    groups = load_json(GROUP_JSON)["groups"]["by_sky_z_cell"]

    rows: list[dict[str, Any]] = []
    for mass_row in mass["top_cell_masses"]:
        cell = mass_row["cell"]
        if cell not in groups:
            continue
        channels = cell_channels(mass_row, groups[cell])
        rows.append(
            {
                "cell": cell,
                "eigenmass": float(mass_row["normalized_eigenvector_mass"]),
                "eigen_score": float(mass_row["eigen_score"]),
                "channels": channels,
            }
        )

    eigenmass_values = [row["eigenmass"] for row in rows]
    channel_values = {name: [row["channels"][name] for row in rows] for name in CHANNELS}
    channel_correlations = {
        name: round9(pearson(eigenmass_values, values))
        for name, values in channel_values.items()
    }

    pressure_components = [
        "partial_full_shock_fraction",
        "shock_lier_fraction",
        "shock_score_mean",
        "gas_sigma_mean",
        "gas_sigma_p90",
        "agn_liner_or_shock_fraction",
    ]
    z_components = {name: zscore(channel_values[name]) for name in pressure_components}
    mass_z = zscore(eigenmass_values)

    pressure_scores = []
    for i, row in enumerate(rows):
        pressure = sum(z_components[name][i] for name in pressure_components) / len(pressure_components)
        toppling_index = 0.5 * mass_z[i] + 0.5 * pressure
        pressure_scores.append(pressure)
        row["sandpile"] = {
            "grains": round9(row["eigenmass"]),
            "toppling_pressure": round9(pressure),
            "toppling_index": round9(toppling_index),
        }

    pressure_mean, pressure_std = mean_std(pressure_scores)
    index_values = [row["sandpile"]["toppling_index"] for row in rows]
    index_mean, index_std = mean_std(index_values)
    for row in rows:
        row["sandpile"]["state"] = (
            "AVALANCHE_CANDIDATE"
            if row["sandpile"]["toppling_index"] >= index_mean + index_std
            else "LOADED"
            if row["sandpile"]["toppling_index"] >= index_mean
            else "STABLE"
        )

    rows.sort(key=lambda item: item["sandpile"]["toppling_index"], reverse=True)
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result = {
        "schema": "stellar_gas_abelian_sandpile_probe_v0",
        "created": created,
        "decision": "ADMIT_SANDPILE_DIAGNOSTIC_HOLD_PHYSICAL_SANDPILE",
        "claim_boundary": (
            "Uses an Abelian-sandpile metaphor as a diagnostic over SMN/evidence "
            "mass and gas/shock observational proxies. It is not a physical "
            "sandpile simulation, not stellar mass, and not cosmology."
        ),
        "sources": {
            "eigenmass": str(MASS_JSON.relative_to(ROOT)),
            "population_groups": str(GROUP_JSON.relative_to(ROOT)),
        },
        "cell_count": len(rows),
        "channel_correlations_with_eigenmass": channel_correlations,
        "pressure_components": pressure_components,
        "pressure_summary": {
            "mean": round9(pressure_mean),
            "std": round9(pressure_std),
        },
        "toppling_index_summary": {
            "mean": round9(index_mean),
            "std": round9(index_std),
        },
        "top_cells": rows[:25],
        "interpretation": (
            "High eigenmass plus high gas/shock pressure marks cells that deserve "
            "fine-grained follow-up. Negative or weak channel correlation marks "
            "channels that may be less explanatory for the current eigenmass surface."
        ),
        "holds": [
            "HOLD_PHYSICAL_SANDPILE_SIMULATION",
            "HOLD_DIRECT_STELLAR_MASS",
            "HOLD_DIRECT_GAS_DENSITY_INFERENCE",
            "HOLD_OBJECT_LEVEL_CROSSMATCH",
            "HOLD_COSMOLOGY_FIT",
        ],
    }
    receipt = {
        "receipt_type": "stellar_gas_abelian_sandpile_probe_receipt",
        "created": created,
        "cell_count": len(rows),
        "avalanche_candidate_count": sum(1 for row in rows if row["sandpile"]["state"] == "AVALANCHE_CANDIDATE"),
        "decision": result["decision"],
        "validated_outputs": [
            str(OUT_JSON.relative_to(ROOT)),
            str(DOC_MD.relative_to(ROOT)),
            str(TIDDLER.relative_to(ROOT)),
        ],
    }
    return result, receipt


def write_docs(result: dict[str, Any]) -> None:
    corr_lines = "\n".join(
        f"- `{name}`: {value}"
        for name, value in sorted(
            result["channel_correlations_with_eigenmass"].items(),
            key=lambda item: abs(item[1]),
            reverse=True,
        )
    )
    top_lines = "\n".join(
        f"- `{row['cell']}`: state `{row['sandpile']['state']}`, grains `{row['sandpile']['grains']}`, "
        f"pressure `{row['sandpile']['toppling_pressure']}`, index `{row['sandpile']['toppling_index']}`"
        for row in result["top_cells"][:10]
    )
    holds = "\n".join(f"- `{hold}`" for hold in result["holds"])

    DOC_MD.write_text(
        f"""# Stellar Gas Abelian Sandpile Probe

Status: `SANDPILE_DIAGNOSTIC`

Decision: `{result['decision']}`

This probe treats the stellar-gas eigenmass surface as an Abelian-sandpile-style
diagnostic. Cells carry normalized eigenmass as "grains"; gas/shock observables
act as toppling pressure; high grain/high-pressure cells become avalanche
candidates for fine-grained follow-up.

Claim boundary: this is a metaphor-backed diagnostic over observational proxies.
It is not a physical sandpile simulation, not stellar mass, not direct gas
density inference, and not a cosmology fit.

## Channel Correlations With Eigenmass

{corr_lines}

## Toppling Candidates

{top_lines}

## Pressure Components

```json
{json.dumps(result['pressure_components'], indent=2)}
```

## Holds

{holds}
""",
        encoding="utf-8",
    )

    TIDDLER.write_text(
        f"""title: Stellar Gas Abelian Sandpile Probe
tags: StellarGasObservation SemanticMassNumbers Eigenvector Physics Sandpile Receipts
type: text/vnd.tiddlywiki

Status: <<tag SANDPILE_DIAGNOSTIC>>

Decision: `{result['decision']}`

This tiddler operationalizes the "stars as Abelian sand piles" metaphor as a
diagnostic over the stellar-gas eigenmass surface.

```
eigenmass grains + gas/shock pressure -> toppling candidates
```

!! Channel Correlations With Eigenmass

{corr_lines}

!! Toppling Candidates

{top_lines}

!! Boundary

This is not a physical sandpile simulation, not stellar mass, not direct gas
density inference, and not a cosmology fit.
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
