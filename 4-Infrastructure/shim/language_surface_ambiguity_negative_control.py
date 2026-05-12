#!/usr/bin/env python3
"""Language surface-ambiguity negative controls for reconstruction receipts.

These fixtures record why surface resemblance cannot promote a replay law:
1. A false algebraic derivation may accidentally land on the right word.
2. Repeated word surfaces, such as Buffalo instances, require typed roles.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "language_surface_ambiguity_negative_control"
RECEIPT = OUT_DIR / "language_surface_ambiguity_negative_control_receipt.json"
SUMMARY = OUT_DIR / "language_surface_ambiguity_negative_control_receipt.md"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def flown_by_cancellation_fixture() -> dict[str, Any]:
    raw = "grew/grown = flew/x; x = flew*grown/grew = flown"
    lexicon = {
        "grow": {"past": "grew", "past_participle": "grown"},
        "fly": {"past": "flew", "past_participle": "flown"},
    }
    analogy_output = "flown"
    lexicon_output = lexicon["fly"]["past_participle"]
    return {
        "id": "flown_by_cancellation",
        "surface": raw,
        "surface_sha256": sha256_bytes(raw.encode("utf-8")),
        "claimed_operator": "string_fraction_cancellation",
        "operator_lawful": False,
        "analogy_output": analogy_output,
        "lexicon_output": lexicon_output,
        "output_matches_lexicon": analogy_output == lexicon_output,
        "promotion_decision": "HOLD_DERIVATION",
        "reason": (
            "The output is lexically correct, but the derivation is not lawful. "
            "English morphology is not cancellative algebra over word strings."
        ),
    }


def buffalo_fixture() -> dict[str, Any]:
    sentence = "Buffalo buffalo Buffalo buffalo buffalo buffalo Buffalo buffalo"
    tokens = sentence.split()
    typed_roles = [
        {"index": 1, "surface": "Buffalo", "role": "city_modifier", "lemma": "Buffalo"},
        {"index": 2, "surface": "buffalo", "role": "plural_noun_subject", "lemma": "buffalo"},
        {"index": 3, "surface": "Buffalo", "role": "city_modifier", "lemma": "Buffalo"},
        {"index": 4, "surface": "buffalo", "role": "plural_noun_relative_subject", "lemma": "buffalo"},
        {"index": 5, "surface": "buffalo", "role": "transitive_verb_relative", "lemma": "buffalo"},
        {"index": 6, "surface": "buffalo", "role": "transitive_verb_main", "lemma": "buffalo"},
        {"index": 7, "surface": "Buffalo", "role": "city_modifier", "lemma": "Buffalo"},
        {"index": 8, "surface": "buffalo", "role": "plural_noun_object", "lemma": "buffalo"},
    ]
    replay = " ".join(item["surface"] for item in typed_roles)
    normalized_surfaces = {token.lower() for token in tokens}
    return {
        "id": "buffalo_surface_collision",
        "surface": sentence,
        "surface_sha256": sha256_bytes(sentence.encode("utf-8")),
        "surface_token_count": len(tokens),
        "case_sensitive_surface_count": len(set(tokens)),
        "case_folded_surface_count": len(normalized_surfaces),
        "typed_role_count": len({item["role"] for item in typed_roles}),
        "typed_roles": typed_roles,
        "typed_replay_exact": replay == sentence,
        "naive_surface_collapse_loses_roles": len(normalized_surfaces) < len({item["role"] for item in typed_roles}),
        "promotion_decision": "HOLD_SURFACE_COLLISION",
        "reason": (
            "The same visible word surface carries city-modifier, noun, and verb "
            "roles. A codec may reuse the surface token only if typed roles or "
            "residuals replay the original bytes exactly."
        ),
    }


def build_receipt() -> dict[str, Any]:
    fixtures = [flown_by_cancellation_fixture(), buffalo_fixture()]
    receipt = {
        "schema": "language_surface_ambiguity_negative_control_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "purpose": "negative controls for analogy leakage and same-surface role collision",
        "fixtures": fixtures,
        "decision": "HOLD",
        "claim_boundary": (
            "Language ambiguity negative-control receipt only. These fixtures do "
            "not define an English morphology model or a compression result. They "
            "record that analogy and surface reuse may propose candidates, but "
            "typed replay and byte-exact recovery are the trust boundary."
        ),
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(receipt: dict[str, Any]) -> None:
    lines = [
        "# Language Surface Ambiguity Negative-Control Receipt",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        receipt["claim_boundary"],
        "",
        "## Fixtures",
        "",
        "| Fixture | Decision | Replay / match | Reason |",
        "|---|---|---|---|",
    ]
    for fixture in receipt["fixtures"]:
        if fixture["id"] == "flown_by_cancellation":
            replay = f"output_matches_lexicon={fixture['output_matches_lexicon']}"
        else:
            replay = f"typed_replay_exact={fixture['typed_replay_exact']}"
        lines.append(
            f"| `{fixture['id']}` | `{fixture['promotion_decision']}` | `{replay}` | {fixture['reason']} |"
        )
    lines.extend(
        [
            "",
            "## Buffalo Handling",
            "",
            "Buffalo instances are handled as typed-role atoms, not as one reusable untyped token.",
            "The surface may be shared, but each occurrence must preserve role, position,",
            "case, and replay order or declare a residual.",
        ]
    )
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    receipt = build_receipt()
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(receipt)
    print(
        json.dumps(
            {
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "receipt_hash": receipt["receipt_hash"],
                "decision": receipt["decision"],
                "fixtures": [fixture["promotion_decision"] for fixture in receipt["fixtures"]],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
