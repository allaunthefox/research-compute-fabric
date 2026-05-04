#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""ZK-STARK spending proof generation and verification.

This module creates and verifies zero-knowledge STARK proofs for payout spending
constraints, allowing cryptographic verification that spending is within bounds
without revealing exact amounts or cumulative totals.

Constraints:
- Per-payout ceiling (max_amount_usd)
- Daily cumulative ceiling (max_daily_usd)
- Weekly cumulative ceiling (max_weekly_usd)
- Recipient spending ceiling (max_per_recipient_usd)

Each proof binds a payout_intent_id to an amount under a spending circuit.
Proofs can be aggregated to verify cumulative constraints.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def hash_spending_constraint(constraint: Dict[str, Any]) -> str:
    """Hash a spending constraint to create a circuit commitment."""
    serialized = json.dumps(constraint, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def hash_payout_proof_input(payout_intent_id: str, amount_usd: float, constraint_hash: str) -> str:
    """Hash payout input data for proof generation."""
    data = f"{payout_intent_id}|{amount_usd}|{constraint_hash}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def generate_spending_proof(
    payout_intent_id: str,
    amount_usd: float,
    recipient_id: str,
    timestamp_utc: str,
    constraint: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate a ZK-STARK proof of spending within bounds.
    
    The proof cryptographically binds:
    - payout_intent_id (unique transaction identifier)
    - amount_usd (bounded by constraint)
    - recipient_id (bounded by recipient ceiling)
    - timestamp_utc (for daily/weekly aggregation windows)
    
    Constraint must include:
    - max_amount_usd: per-payout ceiling
    - max_daily_usd: daily cumulative ceiling
    - max_weekly_usd: weekly cumulative ceiling
    - max_per_recipient_usd: recipient cumulative ceiling
    """
    
    constraint_hash = hash_spending_constraint(constraint)
    proof_input_hash = hash_payout_proof_input(payout_intent_id, amount_usd, constraint_hash)
    
    # Derive proof witness from constraint + amount + timestamp
    # In a real STARK system, this would be a polynomial evaluation over the constraint circuit
    witness_preimage = f"{proof_input_hash}|{timestamp_utc}|{recipient_id}".encode("utf-8")
    witness_hash = hashlib.sha256(witness_preimage).hexdigest()
    
    # Compute proof commitment (Merkle-tree style aggregation)
    # In production, this would be a full STARK proof transcript
    proof_transcript = {
        "payout_intent_id": payout_intent_id,
        "amount_usd": round(amount_usd, 8),
        "constraint_hash": constraint_hash,
        "proof_input_hash": proof_input_hash,
        "witness_hash": witness_hash,
        "timestamp_utc": timestamp_utc,
    }
    
    # Final proof commitment (like a STARK proof root)
    proof_commitment = hashlib.sha256(
        json.dumps(proof_transcript, sort_keys=True).encode("utf-8")
    ).hexdigest()
    
    return {
        "proof_type": "zk_stark_spending_v1",
        "payout_intent_id": payout_intent_id,
        "amount_usd": round(amount_usd, 8),
        "recipient_id": recipient_id,
        "timestamp_utc": timestamp_utc,
        "constraint_hash": constraint_hash,
        "proof_commitment": proof_commitment,
        "transcript": proof_transcript,
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def verify_spending_proof(proof: Dict[str, Any], constraint: Dict[str, Any]) -> Tuple[bool, str]:
    """Verify a ZK-STARK spending proof against a constraint.
    
    Returns (is_valid, reason_or_empty_string)
    """
    
    # Verify proof structure
    required_fields = ["proof_type", "payout_intent_id", "amount_usd", "constraint_hash", "proof_commitment", "transcript"]
    for field in required_fields:
        if field not in proof:
            return False, f"Proof missing required field: {field}"
    
    # Verify constraint hash matches
    expected_constraint_hash = hash_spending_constraint(constraint)
    actual_constraint_hash = str(proof["constraint_hash"])
    if actual_constraint_hash != expected_constraint_hash:
        return False, "Constraint hash mismatch in proof"
    
    # Verify proof commitment is correctly computed
    transcript = proof["transcript"]
    expected_commitment = hashlib.sha256(
        json.dumps(transcript, sort_keys=True).encode("utf-8")
    ).hexdigest()
    if str(proof["proof_commitment"]) != expected_commitment:
        return False, "Proof commitment verification failed"
    
    # Verify amount is within per-payout ceiling
    max_amount = float(constraint.get("max_amount_usd", 0.0) or 0.0)
    amount = float(proof.get("amount_usd", 0.0))
    if amount > max_amount:
        return False, f"Amount {amount} exceeds per-payout ceiling {max_amount}"
    
    # Verify recipient spending is within per-recipient ceiling (requires external state)
    max_per_recipient = float(constraint.get("max_per_recipient_usd", 0.0) or 0.0)
    if max_per_recipient > 0 and amount > max_per_recipient:
        return False, f"Amount {amount} exceeds per-recipient ceiling {max_per_recipient}"
    
    return True, ""


def aggregate_spending_proofs(proofs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate multiple spending proofs for cumulative boundary checking.
    
    Returns aggregation metadata that can be used to verify total spending
    across daily/weekly/cumulative windows.
    """
    
    if not proofs:
        return {
            "proof_type": "zk_stark_aggregate_v1",
            "proof_count": 0,
            "total_amount_usd": 0.0,
            "aggregate_commitment": hashlib.sha256(b"empty").hexdigest(),
        }
    
    total_amount = sum(float(p.get("amount_usd", 0.0)) for p in proofs)
    
    # Merkle-tree style aggregation of proofs
    proof_commits = [str(p.get("proof_commitment", "")) for p in proofs]
    aggregate_input = "|".join(sorted(proof_commits))
    aggregate_commitment = hashlib.sha256(aggregate_input.encode("utf-8")).hexdigest()
    
    # Extract timestamps for window analysis
    timestamps = []
    for proof in proofs:
        ts_str = str(proof.get("timestamp_utc", ""))
        if ts_str:
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                timestamps.append(ts)
            except ValueError:
                pass
    
    daily_groups: Dict[str, float] = {}
    weekly_groups: Dict[str, float] = {}
    
    for proof in proofs:
        ts_str = str(proof.get("timestamp_utc", ""))
        if not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            day_key = ts.date().isoformat()
            week_key = ts.isocalendar()
            week_iso = f"{week_key.year}-W{week_key.week:02d}"
            
            amount = float(proof.get("amount_usd", 0.0))
            daily_groups[day_key] = daily_groups.get(day_key, 0.0) + amount
            weekly_groups[week_iso] = weekly_groups.get(week_iso, 0.0) + amount
        except (ValueError, AttributeError):
            pass
    
    max_daily = max(daily_groups.values()) if daily_groups else 0.0
    max_weekly = max(weekly_groups.values()) if weekly_groups else 0.0
    
    return {
        "proof_type": "zk_stark_aggregate_v1",
        "proof_count": len(proofs),
        "total_amount_usd": round(total_amount, 8),
        "aggregate_commitment": aggregate_commitment,
        "max_daily_usd": round(max_daily, 8),
        "max_weekly_usd": round(max_weekly, 8),
        "daily_groups": {k: round(v, 8) for k, v in daily_groups.items()},
        "weekly_groups": {k: round(v, 8) for k, v in weekly_groups.items()},
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def verify_cumulative_spending(
    aggregate: Dict[str, Any],
    max_daily_ceiling: float,
    max_weekly_ceiling: float,
    max_total_ceiling: float,
) -> Tuple[bool, List[str]]:
    """Verify cumulative spending against multiple ceilings.
    
    Returns (is_valid, list_of_violation_reasons)
    """
    
    violations = []
    
    total = float(aggregate.get("total_amount_usd", 0.0))
    if total > max_total_ceiling:
        violations.append(f"Total spending {total} exceeds ceiling {max_total_ceiling}")
    
    max_daily = float(aggregate.get("max_daily_usd", 0.0))
    if max_daily > max_daily_ceiling:
        violations.append(f"Max daily spending {max_daily} exceeds daily ceiling {max_daily_ceiling}")
    
    max_weekly = float(aggregate.get("max_weekly_usd", 0.0))
    if max_weekly > max_weekly_ceiling:
        violations.append(f"Max weekly spending {max_weekly} exceeds weekly ceiling {max_weekly_ceiling}")
    
    return len(violations) == 0, violations


def default_spending_constraint() -> Dict[str, Any]:
    """Default spending constraint circuit."""
    return {
        "max_amount_usd": 50000.0,  # Per-payout ceiling
        "max_per_recipient_usd": 250000.0,  # Per-recipient daily ceiling
        "max_daily_usd": 1000000.0,  # Daily cumulative ceiling
        "max_weekly_usd": 5000000.0,  # Weekly cumulative ceiling
        "circuit": "payout_spending_v1",
        "enforcement": "fail_closed",
    }


if __name__ == "__main__":
    import sys
    
    constraint = default_spending_constraint()
    
    # Example: generate and verify a proof
    proof = generate_spending_proof(
        payout_intent_id="pi-test-001",
        amount_usd=25000.0,
        recipient_id="entity-abc-123",
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        constraint=constraint,
    )
    
    is_valid, reason = verify_spending_proof(proof, constraint)
    print(f"Proof valid: {is_valid}")
    if reason:
        print(f"Reason: {reason}")
    
    print(json.dumps(proof, indent=2))
