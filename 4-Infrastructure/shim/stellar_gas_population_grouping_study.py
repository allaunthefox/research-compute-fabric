#!/usr/bin/env python3
"""Population study for MaNGA stellar-gas groupings.

This is the first local population layer for the DESI -> environment prior ->
stellar-gas distribution bridge. It groups MaNGA DAPall galaxies by redshift,
sky cell, BPT proxy, shock/LIER proxy, gas sigma, and stellar sigma. DESI is
kept as a join target only: no direct DESI gas-map claim is made here.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SEED_SCRIPT = REPO / "4-Infrastructure/shim/sdss_manga_dapall_observation_seed.py"
DATA_DIR = REPO / "shared-data/data/stellar_gas_observation"
CHANNELS = DATA_DIR / "sdss_manga_dr17_emission_line_channels.json"
DEFAULT_FITS = REPO / "shared-data/artifacts/stellar_gas_observation/dapall-v3_1_1-3.1.0.fits"
DESTINATION = "Gdrive:topological_storage/research-stack/stellar-gas-observation/seed-2026-05-09"

OUT = DATA_DIR / "stellar_gas_population_grouping_study.json"
DOC = REPO / "6-Documentation/docs/stellar_gas_population_grouping_study_2026-05-09.md"
TIDDLER = REPO / "6-Documentation/tiddlywiki-local/wiki/tiddlers/Stellar Gas Population Grouping Study.tid"

PREFERRED_DAPTYPE = "HYB10-MILESHC-MASTARSSP"

TARGET_COLUMNS = [
    "PLATEIFU",
    "MANGAID",
    "DAPTYPE",
    "OBJRA",
    "OBJDEC",
    "Z",
    "BINSNR",
    "SNR_MED",
    "STELLAR_SIGMA_1RE",
    "HA_GSIGMA_1RE",
    "EMLINE_GFLUX_1RE",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_seed_module():
    spec = importlib.util.spec_from_file_location("sdss_manga_dapall_observation_seed", SEED_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SEED_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_channels() -> dict[str, int]:
    payload = json.loads(CHANNELS.read_text(encoding="utf-8"))
    return {row["label"]: row["index0"] for row in payload["channels"]}


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def rclone_copyto(local: Path, remote: str) -> tuple[bool, str]:
    proc = run(["rclone", "copyto", str(local), remote, "--checksum"])
    message = (proc.stderr or proc.stdout).decode(errors="replace").strip()
    return proc.returncode == 0, message


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value) and value > -900


def pos(value: Any) -> float | None:
    if finite(value) and value > 0:
        return float(value)
    return None


def scalar(value: Any) -> float | None:
    if finite(value):
        return float(value)
    return None


def mean_list(value: Any) -> float | None:
    if not isinstance(value, list):
        return None
    vals = [float(v) for v in value if finite(v)]
    return statistics.fmean(vals) if vals else None


def log_ratio(num: float | None, den: float | None) -> float | None:
    if num is None or den is None or num <= 0 or den <= 0:
        return None
    return math.log10(num / den)


def ratio(num: float | None, den: float | None) -> float | None:
    if num is None or den is None or den <= 0:
        return None
    return num / den


def classify_bpt(log_nii_ha: float | None, log_oiii_hb: float | None) -> str:
    if log_nii_ha is None or log_oiii_hb is None:
        return "unclassified"
    if log_nii_ha >= 0.47:
        return "agn_liner_or_shock_proxy"
    kewley = 0.61 / (log_nii_ha - 0.47) + 1.19
    kauffmann = 0.61 / (log_nii_ha - 0.05) + 1.3
    if log_oiii_hb > kewley:
        return "agn_liner_or_shock_proxy"
    if log_oiii_hb > kauffmann:
        return "composite_proxy"
    return "star_forming_proxy"


def classify_shock(log_sii_ha: float | None, log_oi_ha: float | None, gas_sigma: float | None) -> tuple[float, str]:
    score = 0.0
    if log_sii_ha is not None and log_sii_ha > -0.4:
        score += 0.35
    if log_oi_ha is not None and log_oi_ha > -1.1:
        score += 0.35
    if gas_sigma is not None and gas_sigma > 120:
        score += 0.30
    if score >= 0.65:
        return min(1.0, score), "shock_lier_proxy"
    if score > 0:
        return score, "partial_shock_proxy"
    return 0.0, "no_shock_proxy"


def z_bin(z: float | None) -> str:
    if z is None:
        return "z_missing"
    if z < 0.02:
        return "z_000_002"
    if z < 0.04:
        return "z_002_004"
    if z < 0.06:
        return "z_004_006"
    if z < 0.08:
        return "z_006_008"
    return "z_008_plus"


def sigma_bin(value: float | None, prefix: str) -> str:
    if value is None:
        return f"{prefix}_missing"
    if value < 50:
        return f"{prefix}_000_050"
    if value < 100:
        return f"{prefix}_050_100"
    if value < 150:
        return f"{prefix}_100_150"
    if value < 250:
        return f"{prefix}_150_250"
    return f"{prefix}_250_plus"


def sky_bin(ra: float | None, dec: float | None) -> str:
    if ra is None or dec is None:
        return "sky_missing"
    ra_bin = int(max(0, min(5, math.floor((ra % 360.0) / 60.0))))
    dec_band = "south" if dec < 0 else "north"
    return f"ra{ra_bin:02d}_{dec_band}"


def sky_z_cell(ra: float | None, dec: float | None, z: float | None) -> str:
    return f"{sky_bin(ra, dec)}__{z_bin(z)}"


def summarize(vals: list[float]) -> dict[str, Any]:
    values = sorted(v for v in vals if math.isfinite(v))
    if not values:
        return {"count": 0}
    return {
        "count": len(values),
        "min": round(values[0], 6),
        "max": round(values[-1], 6),
        "mean": round(statistics.fmean(values), 6),
        "median": round(statistics.median(values), 6),
        "p90": round(values[int(0.9 * (len(values) - 1))], 6),
    }


def iter_rows(fits_path: Path):
    seed = load_seed_module()
    with fits_path.open("rb") as f:
        hdu_index = 0
        while True:
            try:
                header, _ = seed.read_header(f)
            except EOFError:
                break
            data_start = f.tell()
            if str(header.get("XTENSION", "PRIMARY")) == "BINTABLE":
                row_len = int(header["NAXIS1"])
                row_count = int(header["NAXIS2"])
                pcount = int(header.get("PCOUNT", 0))
                columns = seed.build_columns(header)
                by_name = {col["name"]: col for col in columns}
                selected = [by_name[name] for name in TARGET_COLUMNS if name in by_name]
                hdu_name = str(header.get("EXTNAME", f"HDU{hdu_index}"))
                for row_idx in range(row_count):
                    f.seek(data_start + row_idx * row_len)
                    row = f.read(row_len)
                    fields: dict[str, Any] = {}
                    for col in selected:
                        raw = row[col["offset"] : col["offset"] + col["width"]]
                        value = seed.decode_value(raw, col)
                        if isinstance(value, str):
                            value = value.replace("\u0000", "").strip()
                        fields[col["name"]] = value
                    yield hdu_index, hdu_name, row_idx, fields
                f.seek(data_start + seed.padded_size(row_len * row_count + pcount))
            else:
                bitpix = int(header.get("BITPIX", 8))
                naxis = int(header.get("NAXIS", 0))
                data_size = 0
                if naxis:
                    pixels = 1
                    for axis in range(1, naxis + 1):
                        pixels *= int(header.get(f"NAXIS{axis}", 0))
                    data_size = abs(bitpix) // 8 * pixels
                f.seek(data_start + seed.padded_size(data_size))
            hdu_index += 1


def add_count(bucket: dict[str, int], key: str) -> None:
    bucket[key] = bucket.get(key, 0) + 1


def group_template() -> dict[str, Any]:
    return {
        "count": 0,
        "bpt_proxy_classes": {},
        "shock_lier_proxy_classes": {},
        "z_bins": {},
        "gas_sigma_bins": {},
        "stellar_sigma_bins": {},
        "sky_bins": {},
        "shock_scores": [],
        "gas_sigma_values": [],
        "stellar_sigma_values": [],
        "snr_values": [],
    }


def update_group(group: dict[str, Any], row: dict[str, Any]) -> None:
    group["count"] += 1
    add_count(group["bpt_proxy_classes"], row["bpt_proxy_class"])
    add_count(group["shock_lier_proxy_classes"], row["shock_lier_proxy_class"])
    add_count(group["z_bins"], row["z_bin"])
    add_count(group["gas_sigma_bins"], row["gas_sigma_bin"])
    add_count(group["stellar_sigma_bins"], row["stellar_sigma_bin"])
    add_count(group["sky_bins"], row["sky_bin"])
    group["shock_scores"].append(row["shock_lier_score"])
    if row["gas_sigma_1re_kms"] is not None:
        group["gas_sigma_values"].append(row["gas_sigma_1re_kms"])
    if row["stellar_sigma_1re_kms"] is not None:
        group["stellar_sigma_values"].append(row["stellar_sigma_1re_kms"])
    if row["snr_mean"] is not None:
        group["snr_values"].append(row["snr_mean"])


def finalize_group(group: dict[str, Any]) -> dict[str, Any]:
    count = group["count"] or 1
    shock = group["shock_lier_proxy_classes"]
    group["shock_lier_fraction"] = round(shock.get("shock_lier_proxy", 0) / count, 6)
    group["partial_or_full_shock_fraction"] = round(
        (shock.get("shock_lier_proxy", 0) + shock.get("partial_shock_proxy", 0)) / count,
        6,
    )
    group["shock_score_summary"] = summarize(group.pop("shock_scores"))
    group["gas_sigma_summary"] = summarize(group.pop("gas_sigma_values"))
    group["stellar_sigma_summary"] = summarize(group.pop("stellar_sigma_values"))
    group["snr_summary"] = summarize(group.pop("snr_values"))
    return group


def row_payload(fields: dict[str, Any], channel_index: dict[str, int]) -> dict[str, Any] | None:
    flux = fields.get("EMLINE_GFLUX_1RE")
    if not isinstance(flux, list) or len(flux) < 35:
        return None
    ha = pos(flux[channel_index["Ha-6564"]])
    hb = pos(flux[channel_index["Hb-4862"]])
    oiii = pos(flux[channel_index["OIII-5008"]])
    nii = pos(flux[channel_index["NII-6585"]])
    sii_1 = pos(flux[channel_index["SII-6718"]])
    sii_2 = pos(flux[channel_index["SII-6732"]])
    sii = sii_1 + sii_2 if sii_1 is not None and sii_2 is not None else None
    oi = pos(flux[channel_index["OI-6302"]])
    gas_sigma = pos(fields.get("HA_GSIGMA_1RE"))
    stellar_sigma = pos(fields.get("STELLAR_SIGMA_1RE"))
    z = scalar(fields.get("Z"))
    ra = scalar(fields.get("OBJRA"))
    dec = scalar(fields.get("OBJDEC"))
    log_nii_ha = log_ratio(nii, ha)
    log_sii_ha = log_ratio(sii, ha)
    log_oi_ha = log_ratio(oi, ha)
    log_oiii_hb = log_ratio(oiii, hb)
    balmer = ratio(ha, hb)
    shock_score, shock_class = classify_shock(log_sii_ha, log_oi_ha, gas_sigma)
    bpt = classify_bpt(log_nii_ha, log_oiii_hb)
    return {
        "plateifu": fields.get("PLATEIFU"),
        "mangaid": fields.get("MANGAID"),
        "daptype": fields.get("DAPTYPE"),
        "ra": ra,
        "dec": dec,
        "z": z,
        "z_bin": z_bin(z),
        "sky_bin": sky_bin(ra, dec),
        "sky_z_cell": sky_z_cell(ra, dec, z),
        "snr_mean": mean_list(fields.get("SNR_MED")) or scalar(fields.get("BINSNR")),
        "gas_sigma_1re_kms": gas_sigma,
        "stellar_sigma_1re_kms": stellar_sigma,
        "gas_sigma_bin": sigma_bin(gas_sigma, "gas_sigma"),
        "stellar_sigma_bin": sigma_bin(stellar_sigma, "stellar_sigma"),
        "line_ratios": {
            "log_NII6585_Ha": log_nii_ha,
            "log_SII6718_6732_Ha": log_sii_ha,
            "log_OI6302_Ha": log_oi_ha,
            "log_OIII5008_Hb": log_oiii_hb,
            "Ha_Hb": balmer,
        },
        "bpt_proxy_class": bpt,
        "shock_lier_proxy_class": shock_class,
        "shock_lier_score": shock_score,
    }


def build_population_study(fits_path: Path, preferred_daptype: str) -> dict[str, Any]:
    channel_index = load_channels()
    required = ["Ha-6564", "Hb-4862", "OIII-5008", "NII-6585", "SII-6718", "SII-6732", "OI-6302"]
    missing = [name for name in required if name not in channel_index]
    if missing:
        raise RuntimeError(f"missing channel labels: {missing}")

    all_rows = 0
    selected_rows: list[dict[str, Any]] = []
    by_plateifu: dict[str, dict[str, Any]] = {}
    daptype_counts: dict[str, int] = {}
    for _, _, _, fields in iter_rows(fits_path):
        all_rows += 1
        payload = row_payload(fields, channel_index)
        if not payload:
            continue
        daptype = str(payload.get("daptype") or "unknown")
        add_count(daptype_counts, daptype)
        plateifu = str(payload.get("plateifu") or "")
        current = by_plateifu.get(plateifu)
        if current is None or daptype == preferred_daptype:
            by_plateifu[plateifu] = payload

    selected_rows = list(by_plateifu.values())
    groups = {
        "by_bpt_proxy_class": {},
        "by_shock_lier_proxy_class": {},
        "by_redshift_bin": {},
        "by_sky_bin": {},
        "by_sky_z_cell": {},
        "by_gas_sigma_bin": {},
        "by_stellar_sigma_bin": {},
    }
    aggregate = group_template()
    for row in selected_rows:
        update_group(aggregate, row)
        for group_name, key_name in [
            ("by_bpt_proxy_class", "bpt_proxy_class"),
            ("by_shock_lier_proxy_class", "shock_lier_proxy_class"),
            ("by_redshift_bin", "z_bin"),
            ("by_sky_bin", "sky_bin"),
            ("by_sky_z_cell", "sky_z_cell"),
            ("by_gas_sigma_bin", "gas_sigma_bin"),
            ("by_stellar_sigma_bin", "stellar_sigma_bin"),
        ]:
            key = row[key_name]
            groups[group_name].setdefault(key, group_template())
            update_group(groups[group_name][key], row)

    finalized_groups = {
        group_name: {
            key: finalize_group(value)
            for key, value in sorted(group.items(), key=lambda item: (-item[1]["count"], item[0]))
        }
        for group_name, group in groups.items()
    }
    top_cells = [
        {"cell": key, **value}
        for key, value in list(finalized_groups["by_sky_z_cell"].items())[:20]
    ]
    examples = sorted(
        selected_rows,
        key=lambda row: (row["shock_lier_score"], row["gas_sigma_1re_kms"] or 0.0),
        reverse=True,
    )[:20]
    return {
        "schema": "stellar_gas_population_grouping_study_v1",
        "created": now_iso(),
        "decision": "ADMIT_POPULATION_GROUPING_SURFACE",
        "claim_boundary": "MaNGA stellar-gas population grouping only. A coarse DESI/MaNGA cell join exists; object-level crossmatch remains HOLD. Proxy classes do not prove physical shock, AGN, or gas mechanism.",
        "source_fits": str(fits_path.relative_to(REPO)) if fits_path.is_relative_to(REPO) else str(fits_path),
        "channel_map": str(CHANNELS.relative_to(REPO)),
        "preferred_daptype": preferred_daptype,
        "rows_seen_all_daptypes": all_rows,
        "daptype_counts": daptype_counts,
        "unique_plateifu_count": len(by_plateifu),
        "selected_population_count": len(selected_rows),
        "aggregate": finalize_group(aggregate),
        "groups": finalized_groups,
        "top_sky_z_cells_for_desi_join": top_cells,
        "top_shock_lier_examples": examples,
        "desi_bridge": {
            "status": "COARSE_CELL_JOIN_EXISTS_OBJECT_CROSSMATCH_HOLD",
            "source_prior": "shared-data/data/stack_solidification/desi_stellar_gas_distribution_prior.json",
            "join_key_shape": "coarse sky/redshift population cell; object-level cone/crossmatch remains HOLD",
            "required_fields": ["ra", "dec", "z", "tracer_type", "selection_flags"],
        },
    }


def write_doc(result: dict[str, Any]) -> None:
    agg = result["aggregate"]
    groups = result["groups"]
    lines = [
        "# Stellar Gas Population Grouping Study",
        "",
        "**Date:** 2026-05-09",
        "",
        f"**Decision:** `{result['decision']}`",
        "",
        "**Claim boundary:** MaNGA stellar-gas population grouping only. DESI",
        "environment inference remains a prior bridge until a DESI-MaNGA join",
        "receipt exists. Proxy classes do not prove physical shock, AGN, or gas",
        "mechanism.",
        "",
        "## Population Surface",
        "",
        "```text",
        f"rows seen, all DAP types: {result['rows_seen_all_daptypes']}",
        f"unique Plate-IFU count:   {result['unique_plateifu_count']}",
        f"selected population:      {result['selected_population_count']}",
        f"preferred DAPTYPE:        {result['preferred_daptype']}",
        "```",
        "",
        "## Aggregate",
        "",
        "```json",
        json.dumps(
            {
                "bpt_proxy_classes": agg["bpt_proxy_classes"],
                "shock_lier_proxy_classes": agg["shock_lier_proxy_classes"],
                "partial_or_full_shock_fraction": agg["partial_or_full_shock_fraction"],
                "gas_sigma_summary": agg["gas_sigma_summary"],
                "stellar_sigma_summary": agg["stellar_sigma_summary"],
            },
            indent=2,
        ),
        "```",
        "",
        "## Redshift Bins",
        "",
        "| Bin | Count | Shock+Partial Fraction | Gas Sigma Median | Stellar Sigma Median |",
        "|---|---:|---:|---:|---:|",
    ]
    for key, value in groups["by_redshift_bin"].items():
        lines.append(
            f"| `{key}` | {value['count']} | {value['partial_or_full_shock_fraction']} | "
            f"{value['gas_sigma_summary'].get('median', '')} | {value['stellar_sigma_summary'].get('median', '')} |"
        )
    lines += [
        "",
        "## DESI-Ready Sky/Redshift Cells",
        "",
        "These are population cells for a later DESI join. They are not DESI",
        "environment classes yet.",
        "",
        "| Cell | Count | Shock+Partial Fraction | Main BPT Counts |",
        "|---|---:|---:|---|",
    ]
    for row in result["top_sky_z_cells_for_desi_join"][:12]:
        lines.append(
            f"| `{row['cell']}` | {row['count']} | {row['partial_or_full_shock_fraction']} | "
            f"`{row['bpt_proxy_classes']}` |"
        )
    lines += [
        "",
        "## What This Gives Us",
        "",
        "- A population baseline over unique MaNGA Plate-IFU rows.",
        "- Grouped shock/LIER and BPT proxy counts by redshift and sky cell.",
        "- DESI-ready cells for a future sky-cone plus redshift-window join.",
        "- Residual target: cells whose local gas state diverges from later DESI environment priors.",
        "",
        "## Receipt",
        "",
        "`shared-data/data/stellar_gas_observation/stellar_gas_population_grouping_study_receipt_*.json`",
        "",
    ]
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(result: dict[str, Any]) -> None:
    agg = result["aggregate"]
    TIDDLER.write_text(
        f"""created: 20260509224000000
modified: 20260509224000000
tags: ResearchStack StellarGas MaNGA PopulationStudy DESI Calibration
title: Stellar Gas Population Grouping Study
type: text/vnd.tiddlywiki

! Stellar Gas Population Grouping Study

Status: `ADMIT_POPULATION_GROUPING_SURFACE`

This page records the first local population grouping pass over MaNGA DAPall
stellar-gas diagnostics.

```text
unique Plate-IFU count: {result['unique_plateifu_count']}
selected population:    {result['selected_population_count']}
preferred DAPTYPE:      {result['preferred_daptype']}
```

!! Aggregate

```json
{json.dumps({
    'bpt_proxy_classes': agg['bpt_proxy_classes'],
    'shock_lier_proxy_classes': agg['shock_lier_proxy_classes'],
    'partial_or_full_shock_fraction': agg['partial_or_full_shock_fraction'],
}, indent=2)}
```

!! DESI Bridge

The sky/redshift cells are DESI-ready join buckets, not DESI environment classes
yet.

```text
MaNGA population cell
  -> future DESI sky-cone/redshift join
  -> environment prior
  -> gas-state residual map
```

!! Boundary

Proxy classes do not prove physical shock, AGN, or gas mechanism. DESI
environment inference remains HOLD until the join receipt exists.
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fits", type=Path, default=DEFAULT_FITS)
    parser.add_argument("--preferred-daptype", default=PREFERRED_DAPTYPE)
    parser.add_argument("--destination", default=DESTINATION)
    parser.add_argument("--no-upload", action="store_true")
    args = parser.parse_args()

    result = build_population_study(args.fits, args.preferred_daptype)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_doc(result)
    write_tiddler(result)

    receipt_path = DATA_DIR / f"stellar_gas_population_grouping_study_receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    receipt: dict[str, Any] = {
        "schema": "stellar_gas_population_grouping_study_receipt_v1",
        "created": now_iso(),
        "claim_boundary": result["claim_boundary"],
        "study_file": str(OUT.relative_to(REPO)),
        "doc_file": str(DOC.relative_to(REPO)),
        "tiddler_file": str(TIDDLER.relative_to(REPO)),
        "source_fits": result["source_fits"],
        "decision": result["decision"],
        "summary": {
            "unique_plateifu_count": result["unique_plateifu_count"],
            "selected_population_count": result["selected_population_count"],
            "partial_or_full_shock_fraction": result["aggregate"]["partial_or_full_shock_fraction"],
            "desi_bridge_status": result["desi_bridge"]["status"],
        },
        "uploads": {},
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.no_upload:
        uploads = {
            "study": (OUT, f"{args.destination}/derived/{OUT.name}"),
            "doc": (DOC, f"{args.destination}/docs/{DOC.name}"),
            "tiddler": (TIDDLER, f"{args.destination}/docs/{TIDDLER.name.replace(' ', '_')}"),
            "receipt": (receipt_path, f"{args.destination}/receipts/{receipt_path.name}"),
        }
        for key, (local, remote) in uploads.items():
            ok, message = rclone_copyto(local, remote)
            receipt["uploads"][key] = {"drive_path": remote, "ok": ok, "message": message}
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if receipt["uploads"].get("receipt", {}).get("ok"):
            rclone_copyto(receipt_path, receipt["uploads"]["receipt"]["drive_path"])

    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
