#!/usr/bin/env python3
"""Validate the Tammes-focused adversarial Hutter prior receipt.

This is a lightweight semantic test, not a compression benchmark.  It checks
that the prior stays in its intended role: route diversity, frontier focusing,
and adversarial stress before exact byte promotion.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
RECEIPT = SHIM / "tammes_focused_adversarial_hutter_prior_receipt.json"
TEST_OUT = SHIM / "tammes_focused_adversarial_hutter_prior_test_receipt.json"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(receipt: dict[str, Any]) -> str:
    preimage = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    return hashlib.sha256(stable_json(preimage).encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def check(condition: bool, test_id: str, detail: str) -> dict[str, Any]:
    return {
        "id": test_id,
        "passed": bool(condition),
        "detail": detail,
    }


def main() -> None:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))

    equations = {item["id"]: item["equation"] for item in receipt["equations"]}
    promotion_rules = set(receipt["promotion_rule"])
    failure_rules = set(receipt["failure_rule"])
    dd_edges = set(receipt["candidate_dd_edges"])
    source_receipts = receipt["source_receipts"]
    source_evidence = receipt["source_evidence"]
    context = receipt["current_hutter_context"]

    tests = [
        check(
            stable_hash(receipt) == receipt["receipt_hash"],
            "receipt_hash_recomputes",
            "The receipt hash matches the stable JSON preimage.",
        ),
        check(
            receipt["schema"] == "tammes_focused_adversarial_hutter_prior_v1",
            "schema_expected",
            "The receipt uses the expected schema.",
        ),
        check(
            len(equations) == 7
            and {"TFA1_tammes_diversity", "TFA2_composition_focus", "TFA4_adversarial_fragility", "TFA6_promotion"}
            <= set(equations),
            "equation_surface_complete",
            "Tammes, composition focus, adversarial fragility, and promotion equations are present.",
        ),
        check(
            "decoded_hash_matches_source_hash" in promotion_rules
            and "measured_total_bytes_beat_incumbent_under_explicit_ratio_schema"
            in promotion_rules,
            "promotion_requires_exact_bytes",
            "Promotion rules require hash match and measured byte improvement.",
        ),
        check(
            "stress_survivorship_used_as_byte_evidence -> diagnostic_only"
            in failure_rules,
            "stress_not_byte_evidence",
            "Adversarial stress survivorship cannot masquerade as compression proof.",
        ),
        check(
            "hash_route_glyph_for_adversarial_arena" in dd_edges
            and "run_adversarial_conway_stress_cases" in dd_edges
            and "close_with_byte_rehydration_hash" in dd_edges,
            "adversarial_edges_close_to_hash",
            "Adversarial glyph stress exists but still closes through byte rehydration hash.",
        ),
        check(
            all((REPO / record["path"]).exists() for record in source_receipts.values()),
            "source_receipts_resolve",
            "All local source receipt paths referenced by the prior exist.",
        ),
        check(
            source_evidence["adversarial_conway_prompt"]["claim_status"]
            == "community_prompt_not_peer_reviewed_source",
            "reddit_source_boundary",
            "The Reddit source is explicitly held as a prompt, not peer-reviewed evidence.",
        ),
        check(
            context["projected_enwik9_total_bytes"] > context["hard_target_bytes_enwik9"]
            and context["projected_gap_to_hard_target_bytes"] > 0,
            "hutter_gap_not_hidden",
            "The current projected Hutter gap is retained and positive.",
        ),
        check(
            (
                "does not prove compression" in receipt["claim_boundary"]
                or "do not prove compression" in receipt["claim_boundary"]
            )
            and "exact decode" in receipt["claim_boundary"],
            "claim_boundary_preserved",
            "The claim boundary explicitly denies compression proof and requires exact decode.",
        ),
    ]

    passed = sum(1 for test in tests if test["passed"])
    failed = len(tests) - passed
    test_receipt: dict[str, Any] = {
        "schema": "tammes_focused_adversarial_hutter_prior_test_v1",
        "tested_receipt": rel(RECEIPT),
        "tested_receipt_hash": receipt["receipt_hash"],
        "tests": tests,
        "summary": {
            "passed": passed,
            "failed": failed,
            "status": "pass" if failed == 0 else "fail",
        },
    }
    preimage = {key: value for key, value in test_receipt.items() if key != "receipt_hash"}
    test_receipt["receipt_hash"] = hashlib.sha256(
        stable_json(preimage).encode("utf-8")
    ).hexdigest()
    TEST_OUT.write_text(
        json.dumps(test_receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(test_receipt["summary"], indent=2, sort_keys=True))
    print(f"test_receipt: {rel(TEST_OUT)}")
    print(f"receipt_hash: {test_receipt['receipt_hash']}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
