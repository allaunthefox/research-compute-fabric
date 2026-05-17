#!/usr/bin/env python3
"""Receipt-backed bibliographic event horizon probe.

The joke is useful: a heavily cited source can become a gravity well. Downstream
claims orbit the label instead of recompiling forward from evidence. This probe
turns that into a provenance diagnostic, not a truth claim.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "bibliographic_event_horizon"
REGISTRY = OUT_DIR / "bibliographic_event_horizon_registry.json"
RECEIPT = OUT_DIR / "bibliographic_event_horizon_receipt.json"
SUMMARY = OUT_DIR / "bibliographic_event_horizon.md"

TREE_FIDDY_CAGE_BOUNDARY_BYTES = 350
EVENT_HORIZON_PULL_THRESHOLD_MILLI = 3500
RECEIPT_THRUST_PER_FORWARD_DERIVATION_MILLI = 1200
RECEIPT_THRUST_PER_REPLAY_CHECK_MILLI = 900
RECEIPT_THRUST_PER_SOURCE_HASH_MILLI = 350

CITATIONS = [
    {
        "id": "immaterialscience_bibliographic_event_horizon",
        "title": "The Bibliographic Event Horizon: A Study on the Gravitational Pull of [1]",
        "url": "https://www.immaterialscience.org/2026/citations",
        "role": "source_prompt",
        "status": "satirical_source_used_as_real_diagnostic_prompt",
    },
    {
        "id": "reddit_discussion_wrapper",
        "title": "Reddit discussion wrapper for bibliographic event horizon prompt",
        "url": "https://www.reddit.com/r/ImmaterialScience/comments/1t7plf9/the_bibliographic_event_horizon_a_study_on_the/",
        "role": "discussion_pointer",
        "status": "metadata_only",
    },
    {
        "id": "forward_foundation_equation_compiler",
        "title": "Forward foundation equation compiler",
        "path": "6-Documentation/docs/specs/FORWARD_FOUNDATION_EQUATION_COMPILER.md",
        "role": "local_trust_boundary",
        "status": "labels_and_citations_are_routing_hints_only",
    },
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def source(
    *,
    source_id: str,
    title: str,
    inbound_citations: int,
    downstream_claims: int,
    label_authority_claims: int,
    forward_derivation_receipts: int,
    replay_checks: int,
    source_hashes: int,
) -> dict[str, Any]:
    citation_pull = inbound_citations * 1000 + downstream_claims * 700 + label_authority_claims * 1300
    receipt_thrust = (
        forward_derivation_receipts * RECEIPT_THRUST_PER_FORWARD_DERIVATION_MILLI
        + replay_checks * RECEIPT_THRUST_PER_REPLAY_CHECK_MILLI
        + source_hashes * RECEIPT_THRUST_PER_SOURCE_HASH_MILLI
    )
    net_pull = citation_pull - receipt_thrust
    horizon = net_pull >= EVENT_HORIZON_PULL_THRESHOLD_MILLI
    item = {
        "source_id": source_id,
        "title": title,
        "inbound_citations": inbound_citations,
        "downstream_claims": downstream_claims,
        "label_authority_claims": label_authority_claims,
        "forward_derivation_receipts": forward_derivation_receipts,
        "replay_checks": replay_checks,
        "source_hashes": source_hashes,
        "citation_pull_milli": citation_pull,
        "receipt_thrust_milli": receipt_thrust,
        "net_pull_milli": net_pull,
        "event_horizon": horizon,
        "decision": "HOLD_CITATION_GRAVITY" if horizon else "ADMIT_ROUTING_DIAGNOSTIC",
        "repair": (
            "compile forward from foundation/source evidence; add replay checks and source hashes"
            if horizon
            else "retain as low-risk bibliography routing context"
        ),
    }
    item["source_hash"] = hash_obj({k: v for k, v in item.items() if k != "source_hash"})
    return item


def build_registry() -> dict[str, Any]:
    sources = [
        source(
            source_id="root_label_001",
            title="Canonical source used as authority label",
            inbound_citations=4,
            downstream_claims=5,
            label_authority_claims=3,
            forward_derivation_receipts=0,
            replay_checks=0,
            source_hashes=1,
        ),
        source(
            source_id="forward_receipted_001",
            title="Same citation load but forward-derived locally",
            inbound_citations=4,
            downstream_claims=5,
            label_authority_claims=0,
            forward_derivation_receipts=4,
            replay_checks=3,
            source_hashes=4,
        ),
        source(
            source_id="fixture_note_001",
            title="Small note with source hash but no theorem authority",
            inbound_citations=1,
            downstream_claims=1,
            label_authority_claims=0,
            forward_derivation_receipts=0,
            replay_checks=1,
            source_hashes=1,
        ),
    ]
    horizon_count = sum(1 for item in sources if item["event_horizon"])
    archive_bytes = 32 + len(sources) * 48
    return {
        "schema": "bibliographic_event_horizon_registry_v1",
        "source_prompt": {
            "title": "The Bibliographic Event Horizon: A Study on the Gravitational Pull of [1]",
            "url": "https://www.immaterialscience.org/2026/citations",
            "reddit_url": "https://www.reddit.com/r/ImmaterialScience/comments/1t7plf9/the_bibliographic_event_horizon_a_study_on_the/",
            "author": "Gunther Schlonk",
            "published": "9 May",
            "source_type": "satirical_article_with_useful_provenance_model",
            "observed_abstract_claim": (
                "The first reference [1] functions as a gravitational singularity; "
                "as reference count increases, the probability of the author having "
                "opened the source material approaches the Planck length."
            ),
            "fetch_status": "public article page fetched; PDF fetch blocked by safe-open policy",
        },
        "citations": CITATIONS,
        "claim_boundary": (
            "Bibliographic event horizon is a citation-provenance diagnostic. It "
            "does not decide whether a source is true. It detects when citation "
            "gravity exceeds local receipt thrust, forcing HOLD until forward "
            "derivation, replay, or source-hash evidence is added."
        ),
        "equation": {
            "citation_pull_milli": "1000*inbound_citations + 700*downstream_claims + 1300*label_authority_claims",
            "receipt_thrust_milli": "1200*forward_derivation_receipts + 900*replay_checks + 350*source_hashes",
            "event_horizon": "citation_pull_milli - receipt_thrust_milli >= 3500",
        },
        "o_ammr_shadow_carrier": {
            "visible_shadow": "bibliography entry, citation number, reference label",
            "hidden_state": "source graph, dependency graph, claim fanout, receipt coverage, residual obligations",
            "chain": [
                "L16_source_ecology",
                "L12_claim_dependency_residual_plane",
                "L8_bibliography_adapter",
                "L4_citation_gravity_primitive",
                "Rg3_obligation_residual_boat",
                "L1_reference_label_shadow",
                "L0_forward_receipt_closure",
                "O_AMMR_root",
            ],
            "residual_handles": ["quote_packet", "dependency_shear", "claim_spectral_field"],
            "plain_merkle_role": "content hash only; not authority",
        },
        "tree_fiddy_guard": {
            "cage_boundary_bytes": TREE_FIDDY_CAGE_BOUNDARY_BYTES,
            "archive_bytes": archive_bytes,
            "archive_admissible": archive_bytes <= TREE_FIDDY_CAGE_BOUNDARY_BYTES,
            "active_pull_rule": "Q_active(i)=0 only after committed_or_shielded; event-horizon sources stay active HOLD",
        },
        "sources": sources,
        "aggregates": {
            "source_count": len(sources),
            "event_horizon_count": horizon_count,
            "admitted_routing_diagnostic_count": sum(1 for item in sources if item["decision"] == "ADMIT_ROUTING_DIAGNOSTIC"),
            "hold_citation_gravity_count": sum(1 for item in sources if item["decision"] == "HOLD_CITATION_GRAVITY"),
            "tree_fiddy_archive_bytes": archive_bytes,
            "tree_fiddy_cage_boundary_bytes": TREE_FIDDY_CAGE_BOUNDARY_BYTES,
            "tree_fiddy_archive_admissible": archive_bytes <= TREE_FIDDY_CAGE_BOUNDARY_BYTES,
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "bibliographic_event_horizon_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "citations": registry["citations"],
        "aggregates": registry["aggregates"],
        "decision": "ADMIT_CITATION_GRAVITY_DIAGNOSTIC_HOLD_FIRST",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Bibliographic Event Horizon Probe",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Equation",
        "",
        f"- Citation pull: `{registry['equation']['citation_pull_milli']}`",
        f"- Receipt thrust: `{registry['equation']['receipt_thrust_milli']}`",
        f"- Event horizon: `{registry['equation']['event_horizon']}`",
        "",
        "## Sources",
        "",
        "| Source | Pull | Thrust | Net | Horizon | Decision |",
        "|---|---:|---:|---:|---|---|",
    ]
    for item in registry["sources"]:
        lines.append(
            f"| `{item['source_id']}` | {item['citation_pull_milli']} | {item['receipt_thrust_milli']} | "
            f"{item['net_pull_milli']} | `{item['event_horizon']}` | `{item['decision']}` |"
        )
    lines.extend(
        [
            "",
            "## Tree Fiddy Guard",
            "",
            f"- Archive bytes: `{registry['aggregates']['tree_fiddy_archive_bytes']}` / `{registry['aggregates']['tree_fiddy_cage_boundary_bytes']}`",
            f"- Archive admissible: `{registry['aggregates']['tree_fiddy_archive_admissible']}`",
            "",
            "## Citations",
            "",
        ]
    )
    for citation in registry["citations"]:
        target = citation.get("url") or citation.get("path")
        lines.append(f"- `{citation['id']}`: {citation['title']} ({target}); role: `{citation['role']}`")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    registry = build_registry()
    receipt = build_receipt(registry)
    REGISTRY.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(registry, receipt)
    print(
        json.dumps(
            {
                "registry": rel(REGISTRY),
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "receipt_hash": receipt["receipt_hash"],
                "decision": receipt["decision"],
                "aggregates": registry["aggregates"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
