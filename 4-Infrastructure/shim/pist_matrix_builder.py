#!/usr/bin/env python3
"""pist_matrix_builder — reproducible 8×8 braid adjacency matrix from RRC equations.

Builds token→strand adjacency matrices.  This is a feature-extraction shim
only — it produces no classifier output and no Lean spectral analysis.
proxy_pred/exact_pred are left null for the Lean surface.

Output schema: rrc_pist_predictions_278_v1  (claim_boundary: matrix-only)
"""

import hashlib
import json
import os
import re
import sys
from collections import defaultdict

N_STRANDS = 8

RECEIPT_JSON = os.path.join(
    os.path.dirname(__file__), "../..",
    "archive/experimental-shim-probes/rrc_equation_classifier_receipt.json",
)
OUTPUT_FILE = os.path.join(
    os.path.dirname(__file__), "../..",
    "shared-data/rrc_pist_predictions_278_v1.json",
)


# ═══════════════════════════════════════════════════════════════════════
# §1  PARSING
# ═══════════════════════════════════════════════════════════════════════

def load_equations() -> tuple[list[dict], int]:
    """Load equations grouped by invariant_receipt.object_id.

    Returns:
        (equations, total_source_records)
            equations — one per unique object_id with provenance fields
            total_source_records — count of all compiled_equations entries

    Representative selection (deterministic):
        Within each object_id group, the record with the lexicographically
        smallest ``equation_record.equation_id`` supplies the name and
        equation text for tokenization.  All records are captured in
        ``source_records`` for auditability.
    """
    with open(RECEIPT_JSON) as f:
        d = json.load(f)
    raw = d.get("compiled_equations", [])

    groups = defaultdict(list)
    for idx, eq in enumerate(raw):
        er = eq.get("equation_record", {})
        ir = eq.get("invariant_receipt", {})
        oid = ir.get("object_id", "")
        if not oid:
            continue
        groups[oid].append({
            "index": idx,
            "equation_id": er.get("equation_id", ""),
            "name": er.get("name", ""),
            "equation_text": er.get("equation", ""),
            "shape": ir.get("shape", "HoldForUnlawfulOrUnderspecifiedShape"),
            "status": ir.get("status", "HOLD"),
        })

    equations = []
    for oid, records in sorted(groups.items()):
        # Deterministic representative: lexicographically smallest equation_id
        rep = min(records, key=lambda r: r["equation_id"])
        equations.append({
            "equation_id": oid,
            "name": rep["name"],
            "equation_text": rep["equation_text"],
            "shape": rep["shape"],
            "status": rep["status"],
            "source_records": [
                {"equation_id": r["equation_id"], "name": r["name"]}
                for r in sorted(records, key=lambda r: r["equation_id"])
            ],
        })

    return equations, len(raw)


def tokenize(text: str) -> list[str]:
    """Split text into tokens.

    Normalization rules (versioned, deterministic):
      1. Replace '-' with '_'
      2. Split on '_' and ':'
      3. Drop empty strings

    Token source: ``equation_record.name`` (the human-readable equation title).
    The full equation text is preserved in ``equation_record.equation`` but is
    not the tokenization source.
    """
    normalized = text.replace("-", "_")
    return [p for p in re.split(r"[_:]", normalized) if p]


# ═══════════════════════════════════════════════════════════════════════
# §2  VOCABULARY
# ═══════════════════════════════════════════════════════════════════════

def build_global_vocabulary(equations: list[dict]) -> dict[str, int]:
    """Build global token→index mapping (sorted, deterministic)."""
    all_tokens = set()
    for eq in equations:
        for t in tokenize(eq["name"]):
            all_tokens.add(t)
    sorted_tokens = sorted(all_tokens)
    return {t: i for i, t in enumerate(sorted_tokens)}


def global_vocab_hash(vocab: dict[str, int]) -> str:
    """SHA256 of ``|``-joined sorted vocabulary tokens."""
    joined = "|".join(vocab.keys())
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


# ═══════════════════════════════════════════════════════════════════════
# §3  STRAND ADJACENCY MATRIX
# ═══════════════════════════════════════════════════════════════════════

def strand_for_token(token: str, vocab: dict[str, int]) -> int:
    """Map token to strand index via global vocabulary position (mod 8)."""
    return vocab[token] % N_STRANDS


def build_adjacency_matrix(tokens: list[str], vocab: dict[str, int]) -> list[list[int]]:
    """Build 8×8 adjacency matrix from token ordering.

    For each adjacent pair (t_i, t_{i+1}) in the original token sequence,
    increment ``M[strand(t_i)][strand(t_{i+1})]`` by 1.

    No symmetrization, no operator projection, no diagonal self-crossings.
    """
    M = [[0] * N_STRANDS for _ in range(N_STRANDS)]
    strands = [strand_for_token(t, vocab) for t in tokens]
    for i in range(len(strands) - 1):
        s1, s2 = strands[i], strands[i + 1]
        M[s1][s2] += 1
    return M


# ═══════════════════════════════════════════════════════════════════════
# §4  HASHING
# ═══════════════════════════════════════════════════════════════════════

def canonical_matrix_json(M: list[list[int]]) -> str:
    """Row‑major JSON, integers only, no whitespace, fixed 8×8 nesting."""
    return json.dumps(M, separators=(",", ":"))


def matrix_hash(M: list[list[int]]) -> str:
    return hashlib.sha256(canonical_matrix_json(M).encode("utf-8")).hexdigest()


# ═══════════════════════════════════════════════════════════════════════
# §5  MAIN
# ═══════════════════════════════════════════════════════════════════════

def main() -> int:
    equations, total_source_records = load_equations()
    print(f"Loaded {len(equations)} unique equations "
          f"(from {total_source_records} source records)", flush=True)

    vocab = build_global_vocabulary(equations)
    gvh = global_vocab_hash(vocab)
    print(f"Global vocabulary: {len(vocab)} unique tokens  hash={gvh}", flush=True)

    predictions = []
    hash_counts = {}

    for eq in equations:
        tokens = tokenize(eq["name"])
        M = build_adjacency_matrix(tokens, vocab)
        mh = matrix_hash(M)
        hash_counts[mh] = hash_counts.get(mh, 0) + 1
        predictions.append({
            "equation_id": eq["equation_id"],
            "proxy_pred": None,
            "exact_pred": None,
            "matrix_hash": mh,
            "matrix_8x8": M,
            "source_records": eq["source_records"],
            "notes": "generated from equation_record.equation_id token adjacency; "
                     "representative chosen by lexicographically smallest equation_id",
        })

    n_unique = len(hash_counts)
    n_total = len(predictions)
    n_collisions = sum(1 for c in hash_counts.values() if c > 1)
    if n_collisions:
        print(f"Matrix hash collisions: {n_collisions} groups "
              f"({n_unique} unique / {n_total} total)", flush=True)
    else:
        print(f"All matrix hashes unique: {n_unique}/{n_total}", flush=True)

    artifact = {
        "schema": "rrc_pist_predictions_278_v1",
        "claim_boundary": "matrix-only;no-classifier;no-lean-spectral",
        "matrix_schema": "token_strand_adjacency_8x8_v1",
        "global_vocab_hash": gvh,
        "summary": {
            "total_source_records": total_source_records,
            "unique_equation_ids": n_total,
        },
        "predictions": predictions,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(artifact, f, indent=2, sort_keys=True)
    print(f"\nWrote {OUTPUT_FILE}", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
