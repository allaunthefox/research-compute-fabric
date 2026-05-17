#!/usr/bin/env python3
"""Create a receipt-backed transfer plan for Hutter-style eigenmass tuning.

This does not run a Hutter benchmark.  It ports the successful DESI multiscale
eigenmass pattern into a compression/Hutter tuning protocol with explicit HOLDs.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ALIGNMENT_JSON = ROOT / "shared-data/data/stellar_gas_observation/stellar_gas_multiscale_eigenmass_alignment.json"
OISC_RECEIPT = ROOT / "shared-data/data/stack_solidification/rust_oisc_decompressor_target_receipt.json"
OUT_DIR = ROOT / "shared-data/data/stack_solidification"
DOCS_DIR = ROOT / "6-Documentation/docs"
TIDDLER_DIR = ROOT / "6-Documentation/tiddlywiki-local/wiki/tiddlers"

OUT_JSON = OUT_DIR / "hutter_eigenmass_transfer_plan.json"
RECEIPT_JSON = OUT_DIR / "hutter_eigenmass_transfer_plan_receipt.json"
DOC_MD = DOCS_DIR / "hutter_eigenmass_transfer_plan_2026-05-09.md"
TIDDLER = TIDDLER_DIR / "Hutter Eigenmass Transfer Plan.tid"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def maybe_load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return load_json(path)


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    alignment = load_json(ALIGNMENT_JSON)
    oisc = maybe_load_json(OISC_RECEIPT)
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")

    feature_basis = [
        "byte_offset_phase",
        "symbol_class",
        "local_context_hash_class",
        "long_range_recurrence_distance",
        "prediction_cache_hit",
        "ram_trace_reuse",
        "residual_entropy_proxy",
        "oisc_instruction_density",
        "ammr_receipt_depth",
        "replay_delta_cost",
    ]

    transfer_ladder = [
        {
            "desi_pattern": "literal row surface",
            "hutter_analog": "raw corpus windows",
            "gate": "WINDOW_FIXTURE_ONLY_UNTIL_CANONICAL_ENWIK9",
        },
        {
            "desi_pattern": "joined gas/shock constrained cells",
            "hutter_analog": "byte-exact replay fixtures constrained by Rust OISC closure",
            "gate": "LEAN_RUST_REPLAY_REQUIRED",
        },
        {
            "desi_pattern": "constraint sharpening factor",
            "hutter_analog": "compression candidate must sharpen prediction/replay axes without losing byte-exact closure",
            "gate": "SHARPENING_WITH_EXACT_REPLAY_ONLY",
        },
        {
            "desi_pattern": "multiscale cosine alignment",
            "hutter_analog": "candidate feature direction must align across raw windows, token/logogram windows, and OISC replay receipts",
            "gate": "MULTISCALE_ALIGNMENT_BEFORE_PROMOTION",
        },
    ]

    gates = [
        "canonical_enwik9_sha256_or_fixture_label_required",
        "raw_baseline_required",
        "candidate_wire_format_required",
        "byte_exact_decompressor_receipt_required",
        "negative_controls_required",
        "eigenmass_sharpening_required",
        "no_competitive_hutter_claim_without_full_prize_envelope",
    ]

    plan = {
        "schema": "hutter_eigenmass_transfer_plan_v0",
        "created": created,
        "decision": "ADMIT_TRANSFER_PROTOCOL_HOLD_HUTTER_CLAIM",
        "claim_boundary": (
            "Transfers the DESI multiscale eigenmass method into a Hutter-style "
            "compression tuning protocol. It does not run enwik9, does not claim "
            "compression gain, and does not claim Hutter Prize progress."
        ),
        "source_alignment": str(ALIGNMENT_JSON.relative_to(ROOT)),
        "source_oisc_receipt": str(OISC_RECEIPT.relative_to(ROOT)) if oisc else None,
        "imported_signal": {
            "desi_manga_tracer_cosine": alignment["alignment"]["tracer_subspace_cosine"],
            "desi_manga_constraint_sharpening_factor": alignment["alignment"]["constraint_sharpening_factor"],
            "analogy_boundary": "evidence sharpening pattern only; no astronomy data transfers into compression scores",
        },
        "hutter_feature_basis_after_tuning": feature_basis,
        "transfer_ladder": transfer_ladder,
        "minimum_receipt_shape": {
            "corpus_id": "canonical hash or fixture label",
            "window_id": "byte offset + length + hash",
            "baseline_sizes": "raw, zlib/lzma, current candidate if available",
            "candidate_features": feature_basis,
            "eigenmass": "dominant eigenvalue + explained share + feature vector",
            "replay": "input hash + output hash + instruction count + decision",
            "decision": "ADMIT_FIXTURE / HOLD / QUARANTINE",
        },
        "promotion_gates": gates,
        "hutter_holds": [
            "HOLD_CANONICAL_ENWIK9",
            "HOLD_FULL_CORPUS_RUN",
            "HOLD_COMPETITIVE_COMPRESSION_CLAIM",
            "HOLD_PRODUCTION_DECOMPRESSOR",
            "HOLD_FPGA_ASIC_PROMOTION",
        ],
        "next_executable_step": (
            "Run this protocol on a small fixed text fixture first, producing raw "
            "window eigenmass, OISC replay receipt, and a baseline size matrix."
        ),
    }

    receipt_payload = json.dumps(plan, sort_keys=True)
    receipt = {
        "receipt_type": "hutter_eigenmass_transfer_plan_receipt",
        "created": created,
        "plan_hash": sha256_text(receipt_payload),
        "decision": plan["decision"],
        "imported_sharpening_factor": plan["imported_signal"]["desi_manga_constraint_sharpening_factor"],
        "gate_count": len(gates),
        "validated_outputs": [
            str(OUT_JSON.relative_to(ROOT)),
            str(DOC_MD.relative_to(ROOT)),
            str(TIDDLER.relative_to(ROOT)),
        ],
    }
    return plan, receipt


def write_docs(plan: dict[str, Any], receipt: dict[str, Any]) -> None:
    basis = "\n".join(f"- `{item}`" for item in plan["hutter_feature_basis_after_tuning"])
    ladder = "\n".join(
        f"- DESI `{row['desi_pattern']}` -> Hutter `{row['hutter_analog']}`; gate `{row['gate']}`"
        for row in plan["transfer_ladder"]
    )
    gates = "\n".join(f"- `{gate}`" for gate in plan["promotion_gates"])
    holds = "\n".join(f"- `{hold}`" for hold in plan["hutter_holds"])

    DOC_MD.write_text(
        f"""# Hutter Eigenmass Transfer Plan

Status: `TRANSFER_PROTOCOL_HOLD_HUTTER_CLAIM`

Decision: `{plan['decision']}`

This document ports the DESI/MaNGA multiscale eigenmass pattern into the Hutter
compression lane as a tuning protocol. It is a method-transfer receipt, not a
compression benchmark.

Claim boundary: no enwik9 run, no compression-gain claim, no Hutter Prize claim,
and no FPGA/ASIC promotion is made here.

## Imported Signal

```text
DESI/MaNGA tracer cosine:       {plan['imported_signal']['desi_manga_tracer_cosine']}
DESI/MaNGA sharpening factor:   {plan['imported_signal']['desi_manga_constraint_sharpening_factor']}
```

Only the evidence-sharpening pattern transfers. Astronomy values do not become
compression scores.

## Hutter Feature Basis After Tuning

{basis}

## Transfer Ladder

{ladder}

## Minimum Receipt Shape

```json
{json.dumps(plan['minimum_receipt_shape'], indent=2)}
```

## Promotion Gates

{gates}

## Holds

{holds}

## Receipt

```text
plan hash: {receipt['plan_hash']}
```
""",
        encoding="utf-8",
    )

    TIDDLER.write_text(
        f"""title: Hutter Eigenmass Transfer Plan
tags: ResearchStack Hutter Compression SemanticMassNumbers Eigenvector Receipt HOLD
type: text/vnd.tiddlywiki

Status: <<tag TRANSFER_PROTOCOL_HOLD_HUTTER_CLAIM>>

Decision: `{plan['decision']}`

This tiddler records how the DESI/MaNGA multiscale eigenmass method transfers
into the Hutter compression lane after tuning.

Imported sharpening signal:

```
{plan['imported_signal']['desi_manga_constraint_sharpening_factor']}
```

Only the method transfers. Astronomy values do not become compression scores.

!! Feature Basis

{basis}

!! Transfer Ladder

{ladder}

!! Promotion Gates

{gates}

!! Holds

{holds}

!! Receipt

```
{receipt['plan_hash']}
```
""",
        encoding="utf-8",
    )


def main() -> None:
    plan, receipt = build()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    TIDDLER_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT_JSON.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_docs(plan, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
