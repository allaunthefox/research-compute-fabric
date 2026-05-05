#!/usr/bin/env python3
"""Emit a provenance-bearing selection-metrics receipt.

Usage:
  python emit_selection_receipt.py \
    --fixture ../../data/fixtures/genetics/selection_metrics_fixture.json \
    --out ../../out/receipts/selection_metrics_demo_v0.receipt.json

The emitted receipt is suitable for plumbing tests only unless the fixture has
real-data provenance. Synthetic fixtures must never promote genetics claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from selection_metrics import (
    TajimasDInput,
    hudson_fst,
    mass_number_selection_pressure,
    tajimas_d,
)


RECEIPT_SCHEMA_VERSION = "selection-metrics-receipt/v0"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_fixture(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_text(encoding="utf-8")
    return json.loads(raw), sha256_text(raw)


def build_receipt(fixture: dict[str, Any], fixture_sha256: str, fixture_path: Path) -> dict[str, Any]:
    tajima_input = TajimasDInput(**fixture["tajimas_d_input"])
    fst_input = fixture["hudson_fst_input"]

    tajima = tajimas_d(tajima_input)
    fst = hudson_fst(
        within_pairwise_differences=fst_input["within_pairwise_differences"],
        between_pairwise_differences=fst_input["between_pairwise_differences"],
    )
    pressure = mass_number_selection_pressure(tajima, fst)

    provenance = fixture.get("provenance", {})
    promotion_policy = fixture.get("promotion_policy", {})
    synthetic = provenance.get("source") == "synthetic_fixture"
    may_promote = bool(promotion_policy.get("may_promote_claims", False)) and not synthetic

    receipt = {
        "schema": RECEIPT_SCHEMA_VERSION,
        "receipt_kind": "selection_metrics_engineering_scaffold",
        "claim_state": "ENGINEERING_SCAFFOLD",
        "fixture": {
            "path": str(fixture_path),
            "fixture_id": fixture.get("fixture_id"),
            "sha256": fixture_sha256,
            "provenance": provenance,
        },
        "inputs": {
            "tajimas_d_input": fixture["tajimas_d_input"],
            "hudson_fst_input": fst_input,
        },
        "results": {
            "tajimas_d": asdict(tajima),
            "hudson_fst": asdict(fst),
            "mass_number_selection_pressure_proxy": pressure,
        },
        "promotion": {
            "may_promote_claims": may_promote,
            "reason": (
                "Synthetic fixture; validates code path only."
                if synthetic
                else promotion_policy.get("reason", "Promotion requires external review.")
            ),
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    receipt["receipt_sha256"] = sha256_text(json.dumps(receipt, sort_keys=True))
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit selection metrics receipt JSON")
    parser.add_argument("--fixture", required=True, type=Path, help="Path to fixture JSON")
    parser.add_argument("--out", required=True, type=Path, help="Output receipt path")
    args = parser.parse_args()

    fixture, fixture_sha256 = load_fixture(args.fixture)
    receipt = build_receipt(fixture, fixture_sha256, args.fixture)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(args.out), "receipt_sha256": receipt["receipt_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
