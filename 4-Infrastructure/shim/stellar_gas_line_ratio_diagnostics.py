#!/usr/bin/env python3
"""Compute MaNGA emission-line ratio diagnostics from DAPall arrays."""

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


REPO = Path(__file__).resolve().parents[2]
SEED_SCRIPT = REPO / "4-Infrastructure/shim/sdss_manga_dapall_observation_seed.py"
DATA_DIR = REPO / "shared-data/data/stellar_gas_observation"
CHANNELS = DATA_DIR / "sdss_manga_dr17_emission_line_channels.json"
DEFAULT_FITS = REPO / "shared-data/artifacts/stellar_gas_observation/dapall-v3_1_1-3.1.0.fits"
DESTINATION = "Gdrive:topological_storage/research-stack/stellar-gas-observation/seed-2026-05-09"
DOC = REPO / "6-Documentation/docs/stellar_gas_line_ratio_diagnostics_2026-05-09.md"


TARGET_COLUMNS = [
    "PLATEIFU",
    "MANGAID",
    "DAPTYPE",
    "Z",
    "HA_GSIGMA_1RE",
    "HA_GSIGMA_HI_CLIP",
    "EMLINE_GFLUX_1RE",
    "EMLINE_GFLUX_TOT",
    "EMLINE_GEW_1RE",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def load_seed_module():
    spec = importlib.util.spec_from_file_location("sdss_manga_dapall_observation_seed", SEED_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SEED_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def rclone_copyto(local: Path, remote: str) -> tuple[bool, str]:
    proc = run(["rclone", "copyto", str(local), remote, "--checksum"])
    message = (proc.stderr or proc.stdout).decode(errors="replace").strip()
    return proc.returncode == 0, message


def finite(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value) and value > -900


def pos(value) -> float | None:
    if finite(value) and value > 0:
        return float(value)
    return None


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
    # Common demarcation curves. This is a diagnostic proxy only.
    if log_nii_ha >= 0.47:
        return "agn_liner_or_shock_proxy"
    kewley = 0.61 / (log_nii_ha - 0.47) + 1.19
    kauffmann = 0.61 / (log_nii_ha - 0.05) + 1.3
    if log_oiii_hb > kewley:
        return "agn_liner_or_shock_proxy"
    if log_oiii_hb > kauffmann:
        return "composite_proxy"
    return "star_forming_proxy"


def classify_shock(log_sii_ha, log_oi_ha, gas_sigma):
    score = 0.0
    reasons = []
    if log_sii_ha is not None and log_sii_ha > -0.4:
        score += 0.35
        reasons.append("elevated_sii_ha")
    if log_oi_ha is not None and log_oi_ha > -1.1:
        score += 0.35
        reasons.append("elevated_oi_ha")
    if gas_sigma is not None and gas_sigma > 120:
        score += 0.30
        reasons.append("broad_halpha_sigma")
    if score >= 0.65:
        label = "shock_lier_proxy"
    elif score > 0:
        label = "partial_shock_proxy"
    else:
        label = "no_shock_proxy"
    return min(1.0, score), label, reasons


def summarize(vals: list[float]) -> dict:
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
                    fields = {}
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
                if naxis == 0:
                    data_size = 0
                else:
                    pixels = 1
                    for axis in range(1, naxis + 1):
                        pixels *= int(header.get(f"NAXIS{axis}", 0))
                    data_size = abs(bitpix) // 8 * pixels
                f.seek(data_start + seed.padded_size(data_size))
            hdu_index += 1


def build_diagnostics(fits_path: Path) -> dict:
    channel_payload = load_json(CHANNELS)
    index = {c["label"]: c["index0"] for c in channel_payload["channels"]}
    required = ["Ha-6564", "Hb-4862", "OIII-5008", "NII-6585", "SII-6718", "SII-6732", "OI-6302"]
    missing = [name for name in required if name not in index]
    if missing:
        raise RuntimeError(f"missing channel labels: {missing}")

    summaries = {
        "log_nii_ha": [],
        "log_sii_ha": [],
        "log_oi_ha": [],
        "log_oiii_hb": [],
        "balmer_decrement": [],
        "gas_sigma_1re_kms": [],
        "shock_lier_score": [],
    }
    classes: dict[str, int] = {}
    shock_classes: dict[str, int] = {}
    examples = []
    total = 0
    valid_ratio_rows = 0
    for hdu_index, hdu_name, row_idx, fields in iter_rows(fits_path):
        total += 1
        flux = fields.get("EMLINE_GFLUX_1RE")
        if not isinstance(flux, list) or len(flux) < 35:
            continue
        ha = pos(flux[index["Ha-6564"]])
        hb = pos(flux[index["Hb-4862"]])
        oiii = pos(flux[index["OIII-5008"]])
        nii = pos(flux[index["NII-6585"]])
        sii = None
        sii_1 = pos(flux[index["SII-6718"]])
        sii_2 = pos(flux[index["SII-6732"]])
        if sii_1 is not None and sii_2 is not None:
            sii = sii_1 + sii_2
        oi = pos(flux[index["OI-6302"]])
        gas_sigma = pos(fields.get("HA_GSIGMA_1RE"))

        log_nii_ha = log_ratio(nii, ha)
        log_sii_ha = log_ratio(sii, ha)
        log_oi_ha = log_ratio(oi, ha)
        log_oiii_hb = log_ratio(oiii, hb)
        balmer = ratio(ha, hb)
        if any(v is not None for v in [log_nii_ha, log_sii_ha, log_oi_ha, log_oiii_hb]):
            valid_ratio_rows += 1

        bpt = classify_bpt(log_nii_ha, log_oiii_hb)
        classes[bpt] = classes.get(bpt, 0) + 1
        shock_score, shock_label, reasons = classify_shock(log_sii_ha, log_oi_ha, gas_sigma)
        shock_classes[shock_label] = shock_classes.get(shock_label, 0) + 1

        for key, value in [
            ("log_nii_ha", log_nii_ha),
            ("log_sii_ha", log_sii_ha),
            ("log_oi_ha", log_oi_ha),
            ("log_oiii_hb", log_oiii_hb),
            ("balmer_decrement", balmer),
            ("gas_sigma_1re_kms", gas_sigma),
            ("shock_lier_score", shock_score),
        ]:
            if value is not None and math.isfinite(value):
                summaries[key].append(float(value))

        if len(examples) < 20 and shock_score >= 0.65:
            examples.append(
                {
                    "hdu_name": hdu_name,
                    "row_index": row_idx,
                    "plateifu": fields.get("PLATEIFU"),
                    "mangaid": fields.get("MANGAID"),
                    "z": fields.get("Z"),
                    "line_ratios": {
                        "log_NII6585_Ha": log_nii_ha,
                        "log_SII6718_6732_Ha": log_sii_ha,
                        "log_OI6302_Ha": log_oi_ha,
                        "log_OIII5008_Hb": log_oiii_hb,
                        "Ha_Hb": balmer,
                    },
                    "gas_sigma_1re_kms": gas_sigma,
                    "bpt_proxy_class": bpt,
                    "shock_lier_proxy": shock_label,
                    "shock_reasons": reasons,
                    "shock_lier_score": shock_score,
                }
            )

    shock_fraction = (
        (shock_classes.get("shock_lier_proxy", 0) + 0.5 * shock_classes.get("partial_shock_proxy", 0))
        / total
        if total
        else 0.0
    )
    return {
        "schema": "stellar_gas_line_ratio_diagnostics_v0",
        "created": now_iso(),
        "claim_boundary": "Line-ratio diagnostics from MaNGA DAPall integrated Gaussian flux arrays. These are proxy classifications; they do not prove a physical shock, AGN, or ionization mechanism.",
        "source_fits": str(fits_path.relative_to(REPO)) if fits_path.is_relative_to(REPO) else str(fits_path),
        "channel_map": str(CHANNELS.relative_to(REPO)),
        "rows_seen": total,
        "valid_ratio_rows": valid_ratio_rows,
        "bpt_proxy_classes": classes,
        "shock_lier_proxy_classes": shock_classes,
        "aggregate_ratios": {k: summarize(v) for k, v in summaries.items()},
        "shock_lier_support": {
            "fractional_proxy_support": round(shock_fraction, 6),
            "gate": "ADMIT_LINE_RATIO_SHOCK_PROXY_SUPPORT" if shock_fraction > 0 else "HOLD_NO_LINE_RATIO_SUPPORT",
        },
        "example_shock_lier_rows": examples,
        "model_refinement": {
            "saha_ionization": "line ratios now present; still HOLD for electron density and temperature",
            "radiative_transfer": "Balmer decrement and flux lanes now named; still HOLD for attenuation model",
            "shock_excitation": "SII/Ha, OI/Ha, OIII/Hb, NII/Ha, and H-alpha sigma now form a proxy gate",
        },
        "decision": "ADMIT_LINE_RATIO_DIAGNOSTIC_SURFACE",
    }


def write_doc(result: dict, path: Path) -> None:
    support = result["shock_lier_support"]
    agg = result["aggregate_ratios"]
    lines = [
        "# Stellar Gas Line Ratio Diagnostics",
        "",
        "**Date:** 2026-05-09",
        "",
        f"**Decision:** `{result['decision']}`",
        "",
        "**Claim boundary:** line-ratio proxy only. This does not prove a",
        "physical shock, AGN, stellar breakout, or ionization mechanism.",
        "",
        "## What Changed",
        "",
        "The 35-element MaNGA emission-line arrays now have named channels, so",
        "physics can propagate through line ratios instead of anonymous vector",
        "positions.",
        "",
        "```text",
        f"rows seen:             {result['rows_seen']}",
        f"valid ratio rows:      {result['valid_ratio_rows']}",
        f"shock proxy support:   {support['fractional_proxy_support']}",
        f"shock proxy gate:      {support['gate']}",
        "```",
        "",
        "## Aggregate Ratios",
        "",
        "| Ratio | Count | Mean | Median | P90 |",
        "|---|---:|---:|---:|---:|",
    ]
    for key in [
        "log_nii_ha",
        "log_sii_ha",
        "log_oi_ha",
        "log_oiii_hb",
        "balmer_decrement",
        "gas_sigma_1re_kms",
        "shock_lier_score",
    ]:
        s = agg[key]
        lines.append(
            f"| `{key}` | {s.get('count', 0)} | {s.get('mean', '')} | "
            f"{s.get('median', '')} | {s.get('p90', '')} |"
        )
    lines += [
        "",
        "## Proxy Classes",
        "",
        "```json",
        json.dumps(
            {
                "bpt_proxy_classes": result["bpt_proxy_classes"],
                "shock_lier_proxy_classes": result["shock_lier_proxy_classes"],
            },
            indent=2,
        ),
        "```",
        "",
        "## Physics Propagation",
        "",
        "- Saha/ionization now has line-ratio support, but still needs electron density and temperature.",
        "- Radiative transfer now has named flux and Balmer-decrement lanes, but still needs an attenuation model.",
        "- Shock excitation now has SII/Ha, OI/Ha, OIII/Hb, NII/Ha, and H-alpha sigma proxy support.",
        "",
    ]
    path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fits", type=Path, default=DEFAULT_FITS)
    parser.add_argument("--destination", default=DESTINATION)
    args = parser.parse_args()
    result = build_diagnostics(args.fits)
    out = DATA_DIR / "stellar_gas_line_ratio_diagnostics.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    write_doc(result, DOC)

    receipt_path = DATA_DIR / f"stellar_gas_line_ratio_diagnostics_receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    receipt = {
        "schema": "stellar_gas_line_ratio_diagnostics_receipt_v0",
        "created": now_iso(),
        "claim_boundary": result["claim_boundary"],
        "channel_map": str(CHANNELS.relative_to(REPO)),
        "diagnostics_file": str(out.relative_to(REPO)),
        "doc_file": str(DOC.relative_to(REPO)),
        "decision": result["decision"],
        "shock_lier_support": result["shock_lier_support"],
        "uploads": {},
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    uploads = {
        "channel_map": (CHANNELS, f"{args.destination}/derived/{CHANNELS.name}"),
        "diagnostics": (out, f"{args.destination}/derived/{out.name}"),
        "doc": (DOC, f"{args.destination}/docs/{DOC.name}"),
        "receipt": (receipt_path, f"{args.destination}/receipts/{receipt_path.name}"),
    }
    for key, (local, remote) in uploads.items():
        ok, message = rclone_copyto(local, remote)
        receipt["uploads"][key] = {"drive_path": remote, "ok": ok, "message": message}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    if receipt["uploads"]["receipt"]["ok"]:
        rclone_copyto(receipt_path, receipt["uploads"]["receipt"]["drive_path"])
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
