#!/usr/bin/env python3
"""TranscriptFormer evolutionary prior probe.

This records TranscriptFormer as an external HOLD prior for learning conserved
organization across evolutionary distance. It uses metadata from DOI/Crossref
and the public czi-ai/transcriptformer repository. It does not download model
weights, run biological inference, or validate biological claims.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "transcriptformer_evolutionary_prior"
PAYLOAD_JSON = OUT_DIR / "transcriptformer_evolutionary_prior.json"
SUMMARY = OUT_DIR / "transcriptformer_evolutionary_prior.md"
RECEIPT = OUT_DIR / "transcriptformer_evolutionary_prior_receipt.json"
TIDDLER = (
    REPO
    / "6-Documentation"
    / "tiddlywiki-local"
    / "wiki"
    / "tiddlers"
    / "TranscriptFormer Evolutionary Prior.tid"
)

REMOTE_SOURCES = [
    {
        "name": "crossref_science_article",
        "url": "https://api.crossref.org/works/10.1126/science.aec8514",
    },
    {
        "name": "openalex_science_article",
        "url": "https://api.openalex.org/works/doi:10.1126/science.aec8514",
    },
    {
        "name": "transcriptformer_readme",
        "url": "https://raw.githubusercontent.com/czi-ai/transcriptformer/main/README.md",
    },
    {
        "name": "transcriptformer_pyproject",
        "url": "https://raw.githubusercontent.com/czi-ai/transcriptformer/main/pyproject.toml",
    },
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def fetch(source: dict[str, str]) -> dict[str, Any]:
    try:
        request = urllib.request.Request(
            source["url"],
            headers={"User-Agent": "ResearchStack-transcriptformer-prior/1.0"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read()
        return {
            **source,
            "fetched": True,
            "fetch_error": None,
            "bytes": len(data),
            "sha256": sha256_bytes(data),
            "text": data.decode("utf-8", errors="replace"),
        }
    except Exception as exc:  # pragma: no cover - receipt captures network failures.
        return {
            **source,
            "fetched": False,
            "fetch_error": f"{type(exc).__name__}: {exc}",
            "bytes": 0,
            "sha256": None,
            "text": "",
        }


def clean_abstract(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_crossref(ref: dict[str, Any]) -> dict[str, Any]:
    if not ref["fetched"]:
        return {}
    data = json.loads(ref["text"])
    msg = data["message"]
    return {
        "title": (msg.get("title") or [""])[0],
        "doi": msg.get("DOI"),
        "published_online": msg.get("published-online"),
        "journal": (msg.get("container-title") or [""])[0],
        "abstract": clean_abstract(msg.get("abstract", "")),
    }


def extract_openalex(ref: dict[str, Any]) -> dict[str, Any]:
    if not ref["fetched"]:
        return {}
    data = json.loads(ref["text"])
    return {
        "title": data.get("title"),
        "publication_date": data.get("publication_date"),
        "ids": data.get("ids"),
        "open_access": data.get("open_access"),
    }


def build_payload() -> dict[str, Any]:
    refs = [fetch(source) for source in REMOTE_SOURCES]
    by_name = {ref["name"]: ref for ref in refs}
    crossref = extract_crossref(by_name["crossref_science_article"])
    openalex = extract_openalex(by_name["openalex_science_article"])
    payload = {
        "schema": "transcriptformer_evolutionary_prior_v1",
        "claim_boundary": (
            "External biology/foundation-model prior only. This records a model-card "
            "and DOI metadata surface for cross-species conserved-organization learning; "
            "it does not validate biological predictions, disease claims, or local model execution."
        ),
        "source_refs": [
            {k: ref[k] for k in ["name", "url", "fetched", "fetch_error", "bytes", "sha256"]}
            for ref in refs
        ],
        "article": {
            "crossref": crossref,
            "openalex": openalex,
        },
        "prior_statement": (
            "TranscriptFormer is a useful HOLD prior because it attempts to learn "
            "conserved cell-state organization from evolutionary breadth: up to 112M "
            "cells, 12 species, and 1.53B years of evolutionary distance, with emergent "
            "developmental, phylogenetic, and cellular hierarchies reported in learned representations."
        ),
        "candidate_equations": [
            {
                "equation_id": "evolutionary_breadth_representation_prior",
                "equation": "Z_cell=f_theta(gene_identity,expression_count,species_embedding,evolutionary_context)",
                "decision": "HOLD_EVOLUTIONARY_REPRESENTATION_PRIOR",
                "use_as": "external prior for conserved organization learned across evolutionary distance",
            },
            {
                "equation_id": "conserved_structure_emergence_gate",
                "equation": "G_conserved=1[hierarchy_emerges]*1[zero_shot_transfer]*1[negative_controls_pass]",
                "decision": "HOLD_CONSERVED_STRUCTURE_GATE",
                "use_as": "gate before using emergent hierarchy claims as topology evidence",
            },
            {
                "equation_id": "homology_leakage_caveat",
                "equation": "Risk_leak=homology_overlap+species_signal_dominance+annotation_reuse+benchmark_pseudoreplication",
                "decision": "HOLD_LEAKAGE_CAVEAT",
                "use_as": "caveat lane for cross-species model validation and generalization claims",
            },
            {
                "equation_id": "universal_organization_adapter",
                "equation": "P_universal(X)=conserved_signal(X)-leakage_risk(X)-species_confound(X)",
                "decision": "HOLD_UNIVERSAL_ORGANIZATION_ADAPTER",
                "use_as": "adapter from biological conserved organization to topology/engineering fitness priors",
            },
            {
                "equation_id": "logogram_species_code_adapter",
                "equation": "L_species=encode(conserved_tokens,lineage_markers,mutation_residuals,phenotype_closure)",
                "decision": "HOLD_LOGOGRAM_SPECIES_CODE_ADAPTER",
                "use_as": "treat the logogram as a species-code-like symbolic compression layer with lineage and residual lanes",
            },
            {
                "equation_id": "logogram_genotype_phenotype_closure",
                "equation": "G_logogram=1[decode(L)->phenotype_readout]*1[lineage_consistent]*1[residual_bounded]",
                "decision": "HOLD_LOGOGRAM_PHENOTYPE_CLOSURE",
                "use_as": "gate before a logogram code is treated as carrying conserved species-level structure",
            },
        ],
        "adapter_shape": {
            "to_network_topology": "supports the idea that conserved organization can emerge under shared constraints across distant substrates",
            "to_engineering_fitness": "evolutionary breadth acts like a natural negative-control surface for distinguishing conserved function from local artifact",
            "to_rainbow_raccoon": "treat learned representations as guess surfaces with residual/leakage gates before promotion",
            "to_logogram": "treat logogram tokens as symbolic species-code carriers only when conserved tokens, lineage markers, mutation residuals, and phenotype/readout closure are explicit",
            "caveat": "closed-access Science article metadata plus public repo README are not enough for local validation; no biological claim is promoted",
        },
        "decision": "ADMIT_TRANSCRIPTFORMER_AS_HOLD_EVOLUTIONARY_PRIOR",
    }
    payload["aggregates"] = {
        "remote_source_count": len(refs),
        "remote_fetched_count": sum(1 for ref in refs if ref["fetched"]),
        "candidate_count": len(payload["candidate_equations"]),
    }
    payload["payload_hash"] = hash_obj({k: v for k, v in payload.items() if k != "payload_hash"})
    return payload


def build_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "transcriptformer_evolutionary_prior_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "payload_hash": payload["payload_hash"],
        "aggregates": payload["aggregates"],
        "source_hashes": {ref["name"]: ref["sha256"] for ref in payload["source_refs"]},
        "decision": payload["decision"],
        "claim_boundary": payload["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(payload: dict[str, Any], receipt: dict[str, Any]) -> None:
    article = payload["article"]["crossref"]
    lines = [
        "# TranscriptFormer Evolutionary Prior",
        "",
        f"Decision: `{payload['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        payload["claim_boundary"],
        "",
        "## Article",
        "",
        f"- Title: {article.get('title')}",
        f"- DOI: `{article.get('doi')}`",
        f"- Published online: `{article.get('published_online')}`",
        "",
        "## Prior Statement",
        "",
        payload["prior_statement"],
        "",
        "## Candidate Equations",
        "",
        "| Candidate | Equation | Decision | Use as |",
        "|---|---|---|---|",
    ]
    for item in payload["candidate_equations"]:
        lines.append(f"| {item['equation_id']} | `{item['equation']}` | {item['decision']} | {item['use_as']} |")
    lines.extend(["", "## Caveat", "", payload["adapter_shape"]["caveat"], "", "## Sources", ""])
    for ref in payload["source_refs"]:
        status = "ok" if ref["fetched"] else "missing"
        lines.append(f"- `{ref['name']}`: {status} - {ref['url']}")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(payload: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "title: TranscriptFormer Evolutionary Prior",
        "tags: TranscriptFormer EvolutionaryPrior FoundationModel Biology HOLD Receipt",
        "type: text/vnd.tiddlywiki",
        "",
        "! TranscriptFormer Evolutionary Prior",
        "",
        f"Decision: `{payload['decision']}`",
        "",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        "!! Prior",
        "",
        payload["prior_statement"],
        "",
        "!! Candidate Equations",
        "",
        "| Candidate | Decision |h",
    ]
    for item in payload["candidate_equations"]:
        lines.append(f"| {item['equation_id']} | {item['decision']} |")
    lines.extend(
        [
            "",
            "!! Boundary",
            "",
            payload["claim_boundary"],
            "",
            f"Receipt: `shared-data/data/transcriptformer_evolutionary_prior/transcriptformer_evolutionary_prior_receipt.json`",
            "",
            "!! Links",
            "",
            "* [[Engineering Fitness Topology Trait]]",
            "* [[Combined Approach Equation Surface]]",
        ]
    )
    TIDDLER.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TIDDLER.parent.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    receipt = build_receipt(payload)
    PAYLOAD_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    write_summary(payload, receipt)
    write_tiddler(payload, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
