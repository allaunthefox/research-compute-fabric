#!/usr/bin/env python3
"""Seed an observation-backed stellar gas table from SDSS MaNGA DAPall.

This intentionally avoids astropy/fitsio so the stack can run on a bare Python
environment. It implements only the bounded FITS binary-table parsing needed for
route receipts and small sample extraction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


REPO = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO / "shared-data/artifacts/stellar_gas_observation"
DATA_DIR = REPO / "shared-data/data/stellar_gas_observation"
FITS_URL = (
    "https://data.sdss.org/sas/dr17/manga/spectro/analysis/"
    "v3_1_1/3.1.0/dapall-v3_1_1-3.1.0.fits"
)
FITS_NAME = "dapall-v3_1_1-3.1.0.fits"
DESTINATION = "Gdrive:topological_storage/research-stack/stellar-gas-observation/seed-2026-05-09"


TFORM_RE = re.compile(r"^(?P<repeat>\d*)(?P<code>[A-Z])")
BYTE_SIZES = {
    "L": 1,
    "A": 1,
    "B": 1,
    "I": 2,
    "J": 4,
    "K": 8,
    "E": 4,
    "D": 8,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def rclone_copyto(local: Path, remote: str) -> tuple[bool, str]:
    proc = run(["rclone", "copyto", str(local), remote, "--checksum"])
    message = (proc.stderr or proc.stdout).decode(errors="replace").strip()
    return proc.returncode == 0, message


def download(url: str, target: Path, timeout: int) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_suffix(target.suffix + ".part")
    req = Request(url, headers={"User-Agent": "ResearchStack-DAPallSeed/0"})
    with urlopen(req, timeout=timeout) as response, part.open("wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
    part.replace(target)


def card_value(card: str):
    if len(card) < 10 or card[8] != "=":
        return None
    raw = card[10:80].split("/", 1)[0].strip()
    if raw.startswith("'"):
        end = raw.rfind("'")
        return raw[1:end].strip() if end > 0 else raw.strip("'").strip()
    if raw in {"T", "F"}:
        return raw == "T"
    try:
        return int(raw)
    except ValueError:
        try:
            return float(raw.replace("D", "E"))
        except ValueError:
            return raw


def read_header(f) -> tuple[dict, int]:
    cards: list[str] = []
    bytes_read = 0
    while True:
        block = f.read(2880)
        if not block:
            raise EOFError("unexpected EOF while reading FITS header")
        bytes_read += len(block)
        for i in range(0, len(block), 80):
            card = block[i : i + 80].decode("ascii", errors="replace")
            cards.append(card)
            if card.startswith("END"):
                header: dict[str, object] = {}
                for item in cards:
                    key = item[:8].strip()
                    if not key:
                        continue
                    value = card_value(item)
                    if value is not None:
                        header[key] = value
                return header, bytes_read


def padded_size(size: int) -> int:
    return int(math.ceil(size / 2880.0) * 2880)


def parse_tform(value: str) -> tuple[int, str, int]:
    match = TFORM_RE.match(value.strip())
    if not match:
        raise ValueError(f"unsupported TFORM {value!r}")
    repeat = int(match.group("repeat") or "1")
    code = match.group("code")
    if code == "X":
        # FITS bit arrays are counted in bits.
        width = int(math.ceil(repeat / 8))
    else:
        width = repeat * BYTE_SIZES.get(code, 0)
    if width <= 0:
        raise ValueError(f"unsupported TFORM {value!r}")
    return repeat, code, width


def build_columns(header: dict) -> list[dict]:
    cols = []
    offset = 0
    tfields = int(header.get("TFIELDS", 0))
    for idx in range(1, tfields + 1):
        name = str(header.get(f"TTYPE{idx}", f"COL{idx}")).strip()
        form = str(header.get(f"TFORM{idx}", "")).strip()
        repeat, code, width = parse_tform(form)
        cols.append(
            {
                "idx": idx,
                "name": name,
                "form": form,
                "repeat": repeat,
                "code": code,
                "width": width,
                "offset": offset,
            }
        )
        offset += width
    return cols


def decode_value(raw: bytes, col: dict):
    repeat = col["repeat"]
    code = col["code"]
    if code == "A":
        return raw.decode("ascii", errors="replace").strip()
    if code == "L":
        vals = [bytes([b]).decode("ascii", errors="replace") == "T" for b in raw[:repeat]]
        return vals[0] if repeat == 1 else vals
    if code == "B":
        vals = list(raw[:repeat])
        return vals[0] if repeat == 1 else vals
    fmt = {
        "I": ">h",
        "J": ">i",
        "K": ">q",
        "E": ">f",
        "D": ">d",
    }.get(code)
    if not fmt:
        return None
    size = struct.calcsize(fmt)
    vals = [
        struct.unpack(fmt, raw[i * size : (i + 1) * size])[0]
        for i in range(repeat)
    ]
    vals = [None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v for v in vals]
    return vals[0] if repeat == 1 else vals


def interesting_columns(columns: list[dict]) -> list[dict]:
    patterns = [
        "plateifu",
        "mangaid",
        "objra",
        "objdec",
        "nsa_z",
        "z",
        "emline",
        "ha_",
        "hb_",
        "oiii",
        "nii",
        "sii",
        "sigma",
        "vel",
        "snr",
        "daptype",
    ]
    selected = []
    for col in columns:
        lname = col["name"].lower()
        if any(pattern in lname for pattern in patterns):
            selected.append(col)
    # Keep identifiers even if a future naming change misses them.
    selected = selected[:80]
    return selected


def classify_column(name: str) -> str:
    lname = name.lower()
    if lname in {"plateifu", "mangaid", "daptype"}:
        return "identifier"
    if "emline" in lname or any(line in lname for line in ["ha_", "hb_", "oiii", "nii", "sii"]):
        return "gas_emission_line_or_fit"
    if "sigma" in lname or "vel" in lname:
        return "shock_or_velocity_proxy"
    if lname in {"objra", "objdec", "nsa_z", "z"} or lname.endswith("_z"):
        return "position_or_redshift_context"
    if "snr" in lname:
        return "quality_or_uncertainty_proxy"
    return "context"


def scan_fits(path: Path, sample_rows: int) -> dict:
    hdus = []
    samples = []
    with path.open("rb") as f:
        hdu_index = 0
        while True:
            start = f.tell()
            try:
                header, header_bytes = read_header(f)
            except EOFError:
                break
            data_start = f.tell()
            xtension = str(header.get("XTENSION", "PRIMARY"))
            bitpix = int(header.get("BITPIX", 8))
            naxis = int(header.get("NAXIS", 0))
            if xtension == "BINTABLE":
                row_len = int(header["NAXIS1"])
                row_count = int(header["NAXIS2"])
                pcount = int(header.get("PCOUNT", 0))
                data_size = row_len * row_count + pcount
                columns = build_columns(header)
                selected = interesting_columns(columns)
                hdu_info = {
                    "hdu_index": hdu_index,
                    "name": header.get("EXTNAME", f"HDU{hdu_index}"),
                    "xtension": xtension,
                    "row_count": row_count,
                    "row_len": row_len,
                    "column_count": len(columns),
                    "selected_column_count": len(selected),
                    "selected_columns": [
                        {
                            "name": col["name"],
                            "form": col["form"],
                            "semantic_role": classify_column(col["name"]),
                        }
                        for col in selected
                    ],
                }
                hdus.append(hdu_info)
                if selected and len(samples) < sample_rows:
                    rows_to_read = min(sample_rows - len(samples), row_count)
                    for row_idx in range(rows_to_read):
                        f.seek(data_start + row_idx * row_len)
                        row = f.read(row_len)
                        record = {
                            "hdu_index": hdu_index,
                            "row_index": row_idx,
                            "source_catalog": "SDSS_DR17_MaNGA_DAPall",
                            "model_family": "stellar_gas_observation_seed",
                            "gate_decision": "ADMIT_OBSERVATION_SAMPLE",
                            "fields": {},
                            "semantic_roles": {},
                        }
                        for col in selected:
                            raw = row[col["offset"] : col["offset"] + col["width"]]
                            value = decode_value(raw, col)
                            # Keep JSON compact for large vector columns.
                            if isinstance(value, list) and len(value) > 8:
                                value = {
                                    "length": len(value),
                                    "head": value[:4],
                                    "tail": value[-4:],
                                }
                            record["fields"][col["name"]] = value
                            record["semantic_roles"][col["name"]] = classify_column(col["name"])
                        samples.append(record)
                f.seek(data_start + padded_size(data_size))
            else:
                # Generic IMAGE/PRIMARY skip.
                if naxis == 0:
                    data_size = 0
                else:
                    pixels = 1
                    for axis in range(1, naxis + 1):
                        pixels *= int(header.get(f"NAXIS{axis}", 0))
                    data_size = abs(bitpix) // 8 * pixels
                hdus.append(
                    {
                        "hdu_index": hdu_index,
                        "name": header.get("EXTNAME", "PRIMARY" if hdu_index == 0 else f"HDU{hdu_index}"),
                        "xtension": xtension,
                        "naxis": naxis,
                    }
                )
                f.seek(data_start + padded_size(data_size))
            if f.tell() <= start:
                raise RuntimeError("FITS scanner did not advance")
            hdu_index += 1
    return {"hdus": hdus, "samples": samples}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=ARTIFACT_DIR / FITS_NAME)
    parser.add_argument("--destination", default=DESTINATION)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--sample-rows", type=int, default=5)
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--skip-upload-raw", action="store_true")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    downloaded = False
    if not args.cache.exists() and not args.skip_download:
        download(FITS_URL, args.cache, args.timeout)
        downloaded = True
    if not args.cache.exists():
        raise FileNotFoundError(args.cache)

    fits_sha = sha256_file(args.cache)
    fits_size = args.cache.stat().st_size
    scan = scan_fits(args.cache, args.sample_rows)

    sample_path = DATA_DIR / "sdss_manga_dapall_observation_sample.json"
    sample_payload = {
        "schema": "sdss_manga_dapall_observation_sample_v0",
        "created": now_iso(),
        "claim_boundary": "Bounded sample extracted from SDSS DR17 MaNGA DAPall FITS. This is not the full observation database; it is the first observation-backed schema seed.",
        "source_url": FITS_URL,
        "source_file_sha256": fits_sha,
        "source_file_bytes": fits_size,
        "sample_rows": scan["samples"],
    }
    sample_path.write_text(json.dumps(sample_payload, indent=2) + "\n")

    column_path = DATA_DIR / "sdss_manga_dapall_column_map.json"
    column_payload = {
        "schema": "sdss_manga_dapall_column_map_v0",
        "created": now_iso(),
        "source_url": FITS_URL,
        "source_file_sha256": fits_sha,
        "source_file_bytes": fits_size,
        "hdu_count": len(scan["hdus"]),
        "hdus": scan["hdus"],
    }
    column_path.write_text(json.dumps(column_payload, indent=2) + "\n")

    raw_remote = f"{args.destination.rstrip('/')}/raw/{FITS_NAME}"
    sample_remote = f"{args.destination.rstrip('/')}/derived/{sample_path.name}"
    column_remote = f"{args.destination.rstrip('/')}/derived/{column_path.name}"

    raw_upload = {"drive_path": raw_remote, "ok": False, "message": "skipped"}
    if not args.skip_upload_raw:
        ok, msg = rclone_copyto(args.cache, raw_remote)
        raw_upload = {"drive_path": raw_remote, "ok": ok, "message": msg}

    sample_ok, sample_msg = rclone_copyto(sample_path, sample_remote)
    column_ok, column_msg = rclone_copyto(column_path, column_remote)

    receipt_path = DATA_DIR / f"sdss_manga_dapall_observation_seed_receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    receipt = {
        "schema": "sdss_manga_dapall_observation_seed_receipt_v0",
        "created": now_iso(),
        "claim_boundary": "Promotes one public SDSS MaNGA catalog from route-only to observation-backed seed. Full FITS is cached under shared-data/artifacts and copied to Drive; tracked repo files are column map, sample, and receipt JSON.",
        "source_url": FITS_URL,
        "local_cache": str(args.cache.relative_to(REPO)) if args.cache.is_relative_to(REPO) else str(args.cache),
        "downloaded_this_run": downloaded,
        "fits_sha256": fits_sha,
        "fits_bytes": fits_size,
        "sample_file": str(sample_path.relative_to(REPO)),
        "column_map_file": str(column_path.relative_to(REPO)),
        "gdrive_uploads": {
            "raw_fits": raw_upload,
            "sample": {"drive_path": sample_remote, "ok": sample_ok, "message": sample_msg},
            "column_map": {"drive_path": column_remote, "ok": column_ok, "message": column_msg},
        },
        "parse_summary": {
            "hdu_count": len(scan["hdus"]),
            "sample_count": len(scan["samples"]),
            "bintable_hdus": [h for h in scan["hdus"] if h.get("xtension") == "BINTABLE"],
        },
        "model_refinement": {
            "new_boundary": "route_only_to_observation_sample",
            "observable_lanes": [
                "emission-line gas diagnostics",
                "velocity or velocity-dispersion shock proxies",
                "redshift and sky-position context",
                "quality or uncertainty proxies",
            ],
            "next_gate": "fit selected gas/shock columns against local shock eigen axes",
        },
        "decision": "ADMIT_OBSERVATION_BACKED_STELLAR_GAS_SEED"
        if raw_upload["ok"] and sample_ok and column_ok and scan["samples"]
        else "HOLD_PARTIAL_OBSERVATION_SEED",
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    receipt_remote = f"{args.destination.rstrip('/')}/receipts/{receipt_path.name}"
    receipt_ok, receipt_msg = rclone_copyto(receipt_path, receipt_remote)
    receipt["gdrive_uploads"]["receipt"] = {
        "drive_path": receipt_remote,
        "ok": receipt_ok,
        "message": receipt_msg,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    if receipt_ok:
        rclone_copyto(receipt_path, receipt_remote)
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["decision"].startswith("ADMIT") else 1


if __name__ == "__main__":
    sys.exit(main())
