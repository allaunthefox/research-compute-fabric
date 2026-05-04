#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Validate payout candidates against law registry requirements and gate predicates.

Inputs:
- global regulatory registry CSV
- jurisdiction-to-control mapping CSV
- payout candidates in CSV or JSONL

Output:
- JSONL with allow/block decision and machine-readable block reasons
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, cast

try:
    from zk_stark_spending_proof import (
        default_spending_constraint,
        generate_spending_proof,
        verify_spending_proof,
        aggregate_spending_proofs,
        verify_cumulative_spending,
    )
    ZK_STARK_AVAILABLE = True
except ImportError:
    ZK_STARK_AVAILABLE = False

REQUIRED_REGISTRY_COLUMNS = [
    "record_id",
    "jurisdiction",
    "instrument_name",
    "instrument_type",
    "citation",
    "source_url",
    "effective_or_status",
    "applies_to",
    "trigger_event",
    "required_control",
    "reporting_deadline",
    "retention_period",
    "sanctions_screen_required",
    "travel_rule_required",
    "transaction_generation_binding",
    "enforcement_mode",
    "source_confidence",
    "notes",
    "last_verified_utc",
]

REQUIRED_MAPPING_COLUMNS = [
    "mapping_id",
    "jurisdiction",
    "predicate_id",
    "registry_dependency",
    "candidate_field",
    "pass_values",
    "applies_when",
    "fail_reason_code",
    "fail_reason_template",
    "severity",
]

TRUTHY = {"1", "true", "yes", "y", "pass", "ok", "clear", "allowed", "present", "valid"}


def load_csv_rows(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        headers = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]
    return headers, rows


def validate_headers(headers: Iterable[str], required: List[str], label: str) -> None:
    header_set = set(headers)
    missing = [col for col in required if col not in header_set]
    if missing:
        raise SystemExit(f"{label} missing required columns: {', '.join(missing)}")


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def normalize_bool(value: Any) -> bool:
    return normalize_text(value).lower() in TRUTHY


def normalize_jurisdiction(value: str) -> str:
    raw = normalize_text(value).lower()
    aliases = {
        "us": "United States",
        "usa": "United States",
        "united states of america": "United States",
        "uk": "United Kingdom",
        "great britain": "United Kingdom",
        "eu": "European Union",
        "european union": "European Union",
        "ca": "Canada",
        "sg": "Singapore",
        "ch": "Switzerland",
        "au": "Australia",
    }
    if raw in aliases:
        return aliases[raw]
    return normalize_text(value)


def parse_pass_values(raw: str) -> List[str]:
    return [x.strip().lower() for x in raw.split("|") if x.strip()]


def load_candidates(path: Path) -> List[Dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        out: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if isinstance(obj, dict):
                    raw_obj = cast(Dict[Any, Any], obj)
                    out.append({str(k): raw_obj[k] for k in raw_obj})
        return out

    if path.suffix.lower() == ".csv":
        _, rows = load_csv_rows(path)
        return [{k: v for k, v in row.items()} for row in rows]

    raise SystemExit("Candidates file must be .csv or .jsonl")


def detect_duplicate_intents(candidates: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group candidates by payout_intent_id to detect duplicate submissions.
    
    Returns dict mapping payout_intent_id -> list of candidate dicts.
    Duplicates are when the same intent appears more than once.
    """
    by_intent: Dict[str, List[Dict[str, Any]]] = {}
    for candidate in candidates:
        intent_id = normalize_text(candidate.get("payout_intent_id") or candidate.get("candidate_id") or "")
        if not intent_id:
            continue
        by_intent.setdefault(intent_id, []).append(candidate)
    return by_intent


def build_idempotency_key(candidate: Dict[str, Any]) -> str:
    """Build idempotency key from OmniToken basis fields.
    
    Matches the idempotency_key_basis order from weld_omintoken_tailnet_surface.py:
    ["payout_intent_id", "recipient_id", "gross_amount_base", "currency"]
    """
    intent = normalize_text(candidate.get("payout_intent_id") or "")
    recipient = normalize_text(candidate.get("recipient_id") or "")
    amount = normalize_text(candidate.get("gross_amount_base") or "")
    currency = normalize_text(candidate.get("currency") or "")
    return f"{intent}|{recipient}|{amount}|{currency}"


def build_registry_context(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    by_jurisdiction: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        jurisdiction = normalize_jurisdiction(row.get("jurisdiction", ""))
        if not jurisdiction:
            continue
        ctx = by_jurisdiction.setdefault(
            jurisdiction,
            {
                "jurisdiction": jurisdiction,
                "records": [],
                "flags": {
                    "sanctions_screen_required": False,
                    "travel_rule_required": False,
                    "transaction_generation_binding": False,
                    "reporting_deadline": False,
                    "retention_period": False,
                },
            },
        )

        ctx["records"].append(row)
        flags = ctx["flags"]
        flags["sanctions_screen_required"] = flags["sanctions_screen_required"] or normalize_bool(
            row.get("sanctions_screen_required")
        )
        flags["travel_rule_required"] = flags["travel_rule_required"] or normalize_bool(
            row.get("travel_rule_required")
        )
        flags["transaction_generation_binding"] = flags["transaction_generation_binding"] or normalize_bool(
            row.get("transaction_generation_binding")
        )
        flags["reporting_deadline"] = flags["reporting_deadline"] or bool(normalize_text(row.get("reporting_deadline")))
        flags["retention_period"] = flags["retention_period"] or bool(normalize_text(row.get("retention_period")))

    return by_jurisdiction


def rule_applies(rule: Dict[str, str], candidate: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
    applies_when = normalize_text(rule.get("applies_when", "always")).lower()
    dep = normalize_text(rule.get("registry_dependency", "always"))
    flags = ctx.get("flags", {})

    if applies_when == "always":
        return True

    if applies_when == "entity_recipient":
        recipient_type = normalize_text(candidate.get("recipient_type", "individual")).lower()
        return recipient_type == "entity"

    if applies_when == "registry_flag_true":
        return bool(flags.get(dep, False))

    if applies_when == "registry_field_present":
        return bool(flags.get(dep, False))

    return True


def evaluate_rule(rule: Dict[str, str], candidate: Dict[str, Any], jurisdiction: str) -> Tuple[bool, Dict[str, Any]]:
    field = normalize_text(rule.get("candidate_field"))
    predicate_id = normalize_text(rule.get("predicate_id"))
    payout_intent_id = normalize_text(candidate.get("payout_intent_id") or candidate.get("candidate_id") or "unknown")

    value = candidate.get(field)
    pass_values = parse_pass_values(normalize_text(rule.get("pass_values")))

    passed = False
    if "__nonempty__" in pass_values:
        passed = bool(normalize_text(value))
    else:
        passed = normalize_text(value).lower() in pass_values

    reason = {
        "predicate_id": predicate_id,
        "reason_code": normalize_text(rule.get("fail_reason_code")),
        "severity": normalize_text(rule.get("severity")) or "high",
        "candidate_field": field,
        "actual_value": normalize_text(value),
        "expected": normalize_text(rule.get("pass_values")),
        "message": normalize_text(rule.get("fail_reason_template")).format(
            jurisdiction=jurisdiction,
            payout_intent_id=payout_intent_id,
        ),
    }
    return passed, reason


def evaluate_candidate(
    candidate: Dict[str, Any],
    registry_ctx: Dict[str, Dict[str, Any]],
    mapping_rows: List[Dict[str, str]],
) -> Dict[str, Any]:
    payout_intent_id = normalize_text(candidate.get("payout_intent_id") or candidate.get("candidate_id") or "unknown")
    jurisdiction_raw = normalize_text(candidate.get("recipient_jurisdiction") or candidate.get("jurisdiction"))
    jurisdiction = normalize_jurisdiction(jurisdiction_raw)

    block_reasons: List[Dict[str, Any]] = []

    if not jurisdiction:
        block_reasons.append(
            {
                "predicate_id": "INPUT_VALIDATION",
                "reason_code": "MISSING_JURISDICTION",
                "severity": "critical",
                "message": "Candidate is missing recipient_jurisdiction.",
            }
        )

    if not payout_intent_id:
        block_reasons.append(
            {
                "predicate_id": "INPUT_VALIDATION",
                "reason_code": "MISSING_PAYOUT_INTENT_ID",
                "severity": "high",
                "message": "Candidate is missing payout_intent_id.",
            }
        )

    if block_reasons:
        return {
            "payout_intent_id": payout_intent_id,
            "jurisdiction": jurisdiction,
            "allow": False,
            "block_reasons": block_reasons,
        }

    ctx = registry_ctx.get(jurisdiction)
    if ctx is None:
        return {
            "payout_intent_id": payout_intent_id,
            "jurisdiction": jurisdiction,
            "allow": False,
            "block_reasons": [
                {
                    "predicate_id": "JURISDICTION_POLICY_CHECK",
                    "reason_code": "UNKNOWN_JURISDICTION",
                    "severity": "critical",
                    "message": f"No registry records found for jurisdiction '{jurisdiction}'.",
                }
            ],
        }

    applicable_rules: List[Dict[str, str]] = []
    for row in mapping_rows:
        j = normalize_text(row.get("jurisdiction"))
        if j in {"Global", jurisdiction}:
            if rule_applies(row, candidate, ctx):
                applicable_rules.append(row)

    evaluated_predicates: List[Dict[str, Any]] = []
    for rule in applicable_rules:
        passed, reason = evaluate_rule(rule, candidate, jurisdiction)
        evaluated_predicates.append(
            {
                "predicate_id": normalize_text(rule.get("predicate_id")),
                "passed": passed,
                "candidate_field": normalize_text(rule.get("candidate_field")),
            }
        )
        if not passed:
            block_reasons.append(reason)

    result = {
        "payout_intent_id": payout_intent_id,
        "jurisdiction": jurisdiction,
        "allow": len(block_reasons) == 0,
        "block_reasons": block_reasons,
        "evaluated_predicates": evaluated_predicates,
        "registry_record_count": len(ctx.get("records", [])),
    }
    
    return result


def generate_zk_stark_proof_for_candidate(
    candidate: Dict[str, Any],
    result: Dict[str, Any],
) -> Dict[str, Any] | None:
    """Generate ZK-STARK spending proof for candidate if passing compliance.
    
    Only generates proofs for allowed candidates. Returns None if blocked.
    """
    if not ZK_STARK_AVAILABLE:
        return None
    
    if not result.get("allow", False):
        return None
    
    try:
        payout_intent_id = normalize_text(result.get("payout_intent_id", ""))
        amount_usd = float(candidate.get("gross_amount_base") or candidate.get("amount_usd") or 0.0)
        recipient_id = normalize_text(candidate.get("recipient_id", ""))
        
        if not payout_intent_id or amount_usd <= 0:
            return None
        
        constraint = default_spending_constraint()
        
        proof = generate_spending_proof(
            payout_intent_id=payout_intent_id,
            amount_usd=amount_usd,
            recipient_id=recipient_id,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            constraint=constraint,
        )
        
        # Verify the proof was correctly generated
        is_valid, reason = verify_spending_proof(proof, constraint)
        if not is_valid:
            return None
        
        return proof
    except (ValueError, KeyError, AttributeError):
        return None


def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", required=True, help="Path to payout candidates (.csv or .jsonl)")
    parser.add_argument(
        "--registry",
        default="data_baselines/global_regulatory_law_registry.csv",
        help="Path to regulatory registry CSV",
    )
    parser.add_argument(
        "--mapping",
        default="data_baselines/jurisdiction_control_mapping.csv",
        help="Path to jurisdiction-to-control mapping CSV",
    )
    parser.add_argument(
        "--output",
        default="5-Applications/out/payout_validation_results.jsonl",
        help="Output JSONL path",
    )
    parser.add_argument(
        "--proofs-output",
        default="5-Applications/out/payout_zk_stark_proofs.jsonl",
        help="Output JSONL path for ZK-STARK spending proofs",
    )
    parser.add_argument(
        "--aggregate-proofs",
        default="5-Applications/out/payout_zk_stark_aggregate.json",
        help="Output JSON path for aggregated ZK-STARK proof statistics",
    )
    parser.add_argument(
        "--fail-on-block",
        action="store_true",
        help="Exit with code 2 if any candidate is blocked",
    )
    args = parser.parse_args()

    registry_path = Path(args.registry)
    mapping_path = Path(args.mapping)
    candidates_path = Path(args.candidates)
    output_path = Path(args.output)
    proofs_output_path = Path(args.proofs_output) if ZK_STARK_AVAILABLE else None
    aggregate_output_path = Path(args.aggregate_proofs) if ZK_STARK_AVAILABLE else None

    reg_headers, registry_rows = load_csv_rows(registry_path)
    map_headers, mapping_rows = load_csv_rows(mapping_path)
    validate_headers(reg_headers, REQUIRED_REGISTRY_COLUMNS, "Registry")
    validate_headers(map_headers, REQUIRED_MAPPING_COLUMNS, "Mapping")

    candidates = load_candidates(candidates_path)
    registry_ctx = build_registry_context(registry_rows)

    # Detect duplicate payout intents (idempotency check).
    duplicates_by_intent = detect_duplicate_intents(candidates)
    seen_idem_keys: set[str] = set()
    results: List[Dict[str, Any]] = []
    proofs: List[Dict[str, Any]] = []

    for candidate in candidates:
        payout_intent_id = normalize_text(candidate.get("payout_intent_id") or candidate.get("candidate_id") or "unknown")
        idem_key = build_idempotency_key(candidate)

        # Check for duplicate submission on same intent.
        intent_duplicates = duplicates_by_intent.get(payout_intent_id, [])
        if len(intent_duplicates) > 1:
            # Mark all but first as duplicate block.
            is_first = candidate == intent_duplicates[0]
            if not is_first:
                results.append(
                    {
                        "payout_intent_id": payout_intent_id,
                        "jurisdiction": normalize_jurisdiction(candidate.get("recipient_jurisdiction", "")),
                        "allow": False,
                        "block_reasons": [
                            {
                                "predicate_id": "OMNITOKEN_IDEMPOTENCY_CHECK",
                                "reason_code": "DUPLICATE_PAYOUT_INTENT",
                                "severity": "critical",
                                "candidate_field": "payout_intent_id",
                                "actual_value": payout_intent_id,
                                "expected": "unique_per_submission_batch",
                                "message": f"Duplicate payout intent detected: {payout_intent_id} was already submitted in this batch. Double-spend attempt blocked.",
                            }
                        ],
                    }
                )
                continue

        # Check for duplicate idempotency key (same payout across different intent ids).
        if idem_key in seen_idem_keys:
            results.append(
                {
                    "payout_intent_id": payout_intent_id,
                    "jurisdiction": normalize_jurisdiction(candidate.get("recipient_jurisdiction", "")),
                    "allow": False,
                    "block_reasons": [
                        {
                            "predicate_id": "OMNITOKEN_IDEMPOTENCY_CHECK",
                            "reason_code": "DUPLICATE_IDEMPOTENCY_KEY",
                            "severity": "critical",
                            "candidate_field": "idempotency_key_basis",
                            "actual_value": idem_key,
                            "expected": "unique_idempotency_key",
                            "message": f"Idempotent duplicate detected: same recipient, amount, and currency were attempted multiple times. Corporate double-spend blocked.",
                        }
                    ],
                }
            )
            continue
        seen_idem_keys.add(idem_key)

        # Standard compliance evaluation.
        result = evaluate_candidate(candidate, registry_ctx, mapping_rows)
        results.append(result)
        
        # Generate ZK-STARK spending proof for allowed candidates.
        if ZK_STARK_AVAILABLE and result.get("allow"):
            proof = generate_zk_stark_proof_for_candidate(candidate, result)
            if proof:
                proofs.append(proof)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_path, results)

    # Write ZK-STARK proofs if available.
    if ZK_STARK_AVAILABLE and proofs and proofs_output_path:
        write_jsonl(proofs_output_path, proofs)
        
        # Generate and write aggregate proof statistics.
        if aggregate_output_path:
            aggregate = aggregate_spending_proofs(proofs)
            
            # Check cumulative spending against default constraints.
            max_daily_ceiling = 1000000.0
            max_weekly_ceiling = 5000000.0
            max_total_ceiling = 50000000.0
            
            is_within_bounds, violations = verify_cumulative_spending(
                aggregate,
                max_daily_ceiling=max_daily_ceiling,
                max_weekly_ceiling=max_weekly_ceiling,
                max_total_ceiling=max_total_ceiling,
            )
            
            aggregate["cumulative_check"] = {
                "within_bounds": is_within_bounds,
                "violations": violations,
                "max_daily_ceiling_usd": max_daily_ceiling,
                "max_weekly_ceiling_usd": max_weekly_ceiling,
                "max_total_ceiling_usd": max_total_ceiling,
            }
            
            aggregate_output_path.parent.mkdir(parents=True, exist_ok=True)
            with aggregate_output_path.open("w", encoding="utf-8") as fh:
                json.dump(aggregate, fh, indent=2)

    allow_count = sum(1 for r in results if r.get("allow"))
    block_count = len(results) - allow_count
    summary: Dict[str, Any] = {
        "total": len(results),
        "allowed": allow_count,
        "blocked": block_count,
        "output": str(output_path),
    }
    if ZK_STARK_AVAILABLE:
        summary["zk_stark_proofs_output"] = str(proofs_output_path)
        summary["zk_stark_aggregate_output"] = str(aggregate_output_path)
        summary["proofs_generated"] = len(proofs)
    
    print(json.dumps(summary, indent=2))

    if args.fail_on_block and block_count > 0:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
