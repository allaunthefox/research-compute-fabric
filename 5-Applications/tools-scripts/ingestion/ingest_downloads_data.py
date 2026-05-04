#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
# PTOS: LAYER=STORE / DOMAIN=DATA / CONDITION=STABLE / STAGE=ACTIVE / SOURCE=CODE
"""
Ingest the local downloads-data corpus into substrate_index.db.

Each subdir becomes one PTOS DATA package row so they show up in semantic_query.

Usage:
    python3 5-Applications/scripts/ingest_downloads_data.py [--dry-run]
"""
from __future__ import annotations

import json
import sqlite3
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

DATA_ROOT = Path(
    os.getenv("DOWNLOADS_DATA_ROOT") or Path.home() / "Downloads" / "data"
)
DB_PATH = Path(__file__).parent.parent / "substrate_index.db"

PACKAGES = [
    {
        "pkg": "downloads-data.literature",
        "version": "0.1.0",
        "layer": "STORE",
        "domain": "DATA",
        "condition": "STABLE",
        "stage": "INTAKE",
        "source": "DATA",
        "tier": "FOAM",
        "module": "DOWNLOADS_LITERATURE",
        "archetype": "paper-corpus",
        "description": (
            "Local research literature corpus: Nature/Springer DOI-named PDFs, "
            "PLOS Biology, SSRN preprints, NVIDIA Nemotron tech report, "
            "dark matter overview, ScienceDirect export, and unnamed downloads."
        ),
        "tags": json.dumps([
            "literature", "pdf", "nature", "springer", "preprint",
            "neuroscience", "biology", "ai", "physics", "data"
        ]),
        "subdir": "literature",
    },
    {
        "pkg": "downloads-data.facebook_pdfs",
        "version": "0.1.0",
        "layer": "STORE",
        "domain": "DATA",
        "condition": "STABLE",
        "stage": "INTAKE",
        "source": "IMPORT",
        "tier": "FOAM",
        "module": "DOWNLOADS_FACEBOOK",
        "archetype": "social-export",
        "description": (
            "PDFs downloaded from Facebook posts (numeric post-ID naming). "
            "17 files, mixed content."
        ),
        "tags": json.dumps(["facebook", "pdf", "social-media", "export"]),
        "subdir": "facebook_pdfs",
    },
    {
        "pkg": "downloads-data.feature_csvs",
        "version": "0.1.0",
        "layer": "STORE",
        "domain": "DATA",
        "condition": "STABLE",
        "stage": "INTAKE",
        "source": "DATA",
        "tier": "FOAM",
        "module": "DOWNLOADS_SAE_FEATURES",
        "archetype": "sae-feature-export",
        "description": (
            "Neuronpedia SAE feature exports — 26 CSV files covering alanine codon "
            "detection/preference/bias features and GC-rich region features. "
            "Exported from the NVIDIA SAE explorer session."
        ),
        "tags": json.dumps([
            "sae", "neuronpedia", "features", "alanine", "codon",
            "csv", "gc-rich", "sparse-autoencoder"
        ]),
        "subdir": "feature_csvs",
    },
    {
        "pkg": "downloads-data.media",
        "version": "0.1.0",
        "layer": "STORE",
        "domain": "DATA",
        "condition": "STABLE",
        "stage": "INTAKE",
        "source": "IMPORT",
        "tier": "FOAM",
        "module": "DOWNLOADS_MEDIA",
        "archetype": "media-capture",
        "description": (
            "Screenshots and subtitle transcripts: quantum mechanics linear algebra "
            "slides (5x WebP), BSDM lighting WebP, generic PNGs (5x), and YouTube "
            "auto-generated subtitles for NES RGB, NVIDIA, oil markets, and OpenAI IPO."
        ),
        "tags": json.dumps([
            "media", "screenshot", "webp", "png", "subtitle", "srt",
            "youtube", "quantum-mechanics", "linear-algebra"
        ]),
        "subdir": "media",
    },
    {
        "pkg": "downloads-data.nvidia-sae",
        "version": "0.1.0",
        "layer": "STORE",
        "domain": "DATA",
        "condition": "STABLE",
        "stage": "INTAKE",
        "source": "IMPORT",
        "tier": "FOAM",
        "module": "DOWNLOADS_NVIDIA_SAE",
        "archetype": "web-app-bundle",
        "description": (
            "Saved web-app bundle from the NVIDIA SAE explorer session: "
            "JS chunks + wasm binary. Captured alongside the feature CSV exports."
        ),
        "tags": json.dumps(["nvidia", "sae", "wasm", "javascript", "bundle"]),
        "subdir": "nvidia-sae",
    },
    {
        "pkg": "downloads-data.enwik9",
        "version": "0.1.0",
        "layer": "STORE",
        "domain": "DATA",
        "condition": "STABLE",
        "stage": "INTAKE",
        "source": "DATA",
        "tier": "FOAM",
        "module": "DOWNLOADS_ENWIK9",
        "archetype": "benchmark-data",
        "description": (
            "enwik9 benchmark data slice (21KB sample, file '1234567'). "
            "Reference corpus for compression benchmarking."
        ),
        "tags": json.dumps(["enwik9", "benchmark", "compression", "hutter-prize"]),
        "subdir": "enwik9_data",
    },
]


def collect_files(subdir: str) -> list[str]:
    d = DATA_ROOT / subdir
    if not d.exists():
        return []
    return sorted(str(p) for p in d.iterdir() if p.is_file())


def _upsert(db: sqlite3.Connection, row: dict) -> None:
    cols = list(row.keys())
    placeholders = ", ".join(f":{k}" for k in cols)
    update_cols = [c for c in cols if c not in ("pkg", "version")]
    update_sql = ", ".join(f"{c}=excluded.{c}" for c in update_cols)
    db.execute(
        f"INSERT INTO packages ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT(pkg, version) DO UPDATE SET {update_sql}",
        row,
    )


def main(dry_run: bool = False) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if dry_run:
        print("[dry-run] would insert:")

    db = None if dry_run else sqlite3.connect(DB_PATH)

    for spec in PACKAGES:
        subdir = spec.pop("subdir")
        files = collect_files(subdir)
        row = {
            **spec,
            "files": json.dumps(files),
            "indexed_utc": now,
        }

        if dry_run:
            print(f"  {row['pkg']} v{row['version']}  ({len(files)} files)")
            spec["subdir"] = subdir  # restore for reuse
            continue

        _upsert(db, row)
        print(f"  indexed {row['pkg']}  ({len(files)} files)")
        spec["subdir"] = subdir

    if db:
        # rebuild FTS so semantic_query picks up new rows
        db.execute("INSERT INTO packages_fts(packages_fts) VALUES ('rebuild')")
        db.execute("INSERT INTO packages_fts(packages_fts) VALUES ('optimize')")
        db.commit()
        db.close()
        print(f"done — substrate_index.db updated at {DB_PATH}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    main(dry_run)
