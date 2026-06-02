#!/usr/bin/env python3
"""Targeted ingest for the Venice Research Stack conversation markdown."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shim.utils.hashing import sha256_text, sha256_bytes, sha256_path
from shim.utils.json_utils import stable_json


ROOT = Path("/home/allaun/Documents/Research Stack")
SOURCE = Path("/home/allaun/Documents/ingest/research stack conversation venice.md")
OUT_DIR = ROOT / "data" / "ingested" / "chatgpt"
WIKI_DIR = ROOT / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers"
DB = ROOT / "data" / "substrate_index.db"
MANIFEST = ROOT / "data" / "manifest.jsonl"
RECEIPT = ROOT / "4-Infrastructure" / "shim" / "venice_research_stack_conversation_ingest_receipt.json"


CONCEPT_TERMS = [
    "compression",
    "language",
    "thermodynamic",
    "Landauer",
    "eigenvector",
    "geodesic",
    "epigenetic",
    "cancer",
    "entropy",
    "binding site",
    "topology",
    "Hutter",
    "sidecar",
    "omindirection",
    "GCCL",
    "vectorless",
    "database",
    "agent",
]

EVIDENCE_PATTERNS = {
    "math_language_compression": "Math, at its most ripped apart core, is language",
    "genome_geodesic": "dna is employing a eigenvector math set",
    "landauer_gene_transfer": "i meant landuer limit sorry",
    "cancer_bad_compression": "what if the cancers that show entropy coding are bad compression",
    "binding_site_topology": "what topology does the binding sites encode for cancer drugs",
    "sidecar_plan": "Sidecar plan: it is now a structured correction stream",
    "omindirection_integration": "omindirection compiler actually call this substitution audit",
    "vectorless_database": "i need a vectorles approach with high token retension and external database stores",
    "topology_agents": "once we have agents that can point out where the topology fits",
}





def slugify(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")


def tiddler(title: str, tags: str, body: str) -> str:
    return (
        "created: 20260508000000000\n"
        "modified: 20260508000000000\n"
        f"tags: {tags}\n"
        f"title: {title}\n"
        "type: text/vnd.tiddlywiki\n\n"
        f"! {title}\n\n"
        f"{body.strip()}\n"
    )


def line_evidence(text: str) -> dict[str, dict[str, Any]]:
    lines = text.splitlines()
    evidence: dict[str, dict[str, Any]] = {}
    lower_lines = [line.lower() for line in lines]
    for key, pattern in EVIDENCE_PATTERNS.items():
        needle = pattern.lower()
        found = None
        for index, line in enumerate(lower_lines, start=1):
            if needle in line:
                found = index
                break
        if found is None:
            continue
        start = max(1, found - 1)
        end = min(len(lines), found + 2)
        evidence[key] = {
            "line": found,
            "excerpt": "\n".join(lines[start - 1 : end]).strip(),
        }
    return evidence


def term_counts(text: str) -> dict[str, int]:
    lower = text.lower()
    return {term: lower.count(term.lower()) for term in CONCEPT_TERMS if lower.count(term.lower())}


def manifest_entry(path: Path) -> dict[str, Any]:
    rel = path.relative_to(ROOT)
    stat = path.stat()
    concept = slugify(path.stem)
    return {
        "t": stat.st_mtime,
        "src": "ene",
        "id": f"ene:text/md/{concept}:{datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()}",
        "op": "upsert",
        "data": {
            "pkg": f"ene/text/md/{concept}",
            "version": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            "tier": "AUX",
            "domain": "compression",
            "archetype": "chatgpt_md",
            "concept_anchor": {
                "domain": "compression_biology",
                "concept": concept,
                "resolution": "FORMING",
            },
            "file_path": str(rel),
            "file_ext": ".md",
            "file_hash": f"sha256:{sha256_path(path)}",
            "byte_count": stat.st_size,
            "line_count": len(path.read_text(encoding="utf-8", errors="replace").splitlines()),
            "summary": "Venice conversation on math as compression, genomic geodesics, Landauer limits, cancer as a compression-explanation prior, and logogram sidecar compression.",
        },
        "genome": {"mu": 6, "rho": min(7, stat.st_size // 65536), "c": 4, "m": 4, "ne": 7, "sig": 0},
        "bind": {
            "lawful": True,
            "cost": 0x00010000,
            "invariant": "documentConsistency",
            "class": "informational_bind",
        },
        "provenance": {
            "node": "codex",
            "lake_seed": "venice_research_stack_conversation_ingest",
            "tailscale_ip": "127.0.0.1",
            "attestation_hash": f"sha256:{sha256_path(path)}",
            "prev_id": None,
        },
    }


def append_manifest_if_missing(entry: dict[str, Any]) -> bool:
    existing = set()
    if MANIFEST.exists():
        for line in MANIFEST.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                existing.add(json.loads(line).get("id"))
            except json.JSONDecodeError:
                pass
    if entry["id"] in existing:
        return False
    with MANIFEST.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return True


def ensure_package(title: str, body: str, tags: list[str], files: list[str], evidence: dict[str, Any]) -> dict[str, Any]:
    pkg = f"aiscroll/{slugify(title)}"
    sha = sha256_text(body)
    version = datetime.now(timezone.utc).isoformat().replace(":", "-").replace(".", "-")
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(DB)
    try:
        row = conn.execute(
            "select rowid, version from packages where pkg = ? and sha256 = ? order by rowid desc limit 1",
            (pkg, sha),
        ).fetchone()
        if row:
            return {"pkg": pkg, "rowid": row[0], "version": row[1], "sha256": sha, "reused": True}
        cur = conn.execute(
            """
            insert into packages (
              pkg, version, tier, domain, archetype, description, tags, source,
              session_id, sha256, indexed_utc, model_status, foam_score,
              verification_basis, idea_weights, extension_points, files,
              concept_vector, analog_map, concept_anchor, audit_rationale
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pkg,
                version,
                "RESEARCH",
                "compression_biology",
                "conversation_ingest_brief",
                body[:1200],
                json.dumps(tags, sort_keys=True),
                "Venice conversation markdown",
                str(SOURCE),
                sha,
                now,
                "INGESTED",
                0.0,
                sha,
                json.dumps(
                    {
                        "math_language_compression": 0.9,
                        "genome_geodesic": 0.9,
                        "landauer_biological_transfer": 0.85,
                        "cancer_bad_compression_explanation_prior": 0.75,
                        "vectorless_database_compression": 0.85,
                    },
                    sort_keys=True,
                ),
                json.dumps(
                    [
                        "Logogram sidecar dictionary table",
                        "Genome geodesic compression law surface",
                        "Cancer bad-compression explanation-prior card",
                    ],
                    sort_keys=True,
                ),
                json.dumps(files, sort_keys=True),
                json.dumps(tags, sort_keys=True),
                json.dumps(evidence, sort_keys=True),
                json.dumps(
                    {
                        "domain": "compression_biology",
                        "concept": "venice_research_stack_conversation",
                        "resolution": "FORMING",
                    },
                    sort_keys=True,
                ),
                json.dumps(evidence, sort_keys=True),
            ),
        )
        conn.commit()
        return {"pkg": pkg, "rowid": cur.lastrowid, "version": version, "sha256": sha, "reused": False}
    finally:
        conn.close()


def append_link_once(path: Path, heading: str, link: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if link in text:
        return False
    addition = f"\n{heading}\n\n* {link}\n"
    path.write_text(text.rstrip() + "\n" + addition, encoding="utf-8")
    return True


def build_graph_edges(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    edges = [
        ("math_language_compression", "grounds", "GCCL Encoding Contract"),
        ("genome_geodesic", "maps_to", "Genomic Data Compression Anchor"),
        ("genome_geodesic", "requires_boundary", "Claim Boundary"),
        ("landauer_gene_transfer", "bounds", "Landauer Compression"),
        ("cancer_bad_compression", "explains_as", "Compression Drift Boundary"),
        ("binding_site_topology", "suggests", "Topology-Aware Drug Binding Prior"),
        ("sidecar_plan", "implements", "Math Logogram Surface Compiler"),
        ("omindirection_integration", "feeds", "Omindirection Logogram Contract"),
        ("vectorless_database", "feeds", "Substrate FTS Query Surface"),
        ("topology_agents", "feeds", "Hutter Topology Agent Prior"),
    ]
    return [
        {"source": source, "predicate": predicate, "target": target, "line": evidence.get(source, {}).get("line")}
        for source, predicate, target in edges
        if source in evidence
    ]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WIKI_DIR.mkdir(parents=True, exist_ok=True)

    source_text = SOURCE.read_text(encoding="utf-8", errors="replace")
    source_hash = sha256_path(SOURCE)
    counts = term_counts(source_text)
    evidence = line_evidence(source_text)

    source_copy = OUT_DIR / "venice_research_stack_conversation_source.md"
    shutil.copyfile(SOURCE, source_copy)
    transcript = OUT_DIR / "venice_research_stack_conversation_transcript.md"
    transcript.write_text(source_text, encoding="utf-8")

    graph_edges = build_graph_edges(evidence)
    graph_path = OUT_DIR / "venice_research_stack_conversation_graph_edges.jsonl"
    graph_path.write_text("\n".join(stable_json(edge) for edge in graph_edges) + "\n", encoding="utf-8")

    brief = OUT_DIR / "venice_research_stack_conversation_ene_brief.md"
    brief_text = f"""# Venice Research Stack Conversation - ENE Brief

Source: `{SOURCE}`
Source SHA-256: `{source_hash}`
Transcript SHA-256: `{sha256_text(source_text)}`
Lines: {len(source_text.splitlines())}

## Core Read

This conversation is a concept-development source for compression biology,
GCCL/logogram sidecars, vectorless external-memory compression, and topology
agents. It should be treated as a research-prior source, not as external
scientific validation.

## Extracted Priors

1. Math/language/compression baseline: mathematics is treated as a precise
   language, and language is treated as a compression substrate.
2. Genome geodesic prior: DNA and epigenetics are framed as a dynamic
   eigen/geodesic system in an n-space expression manifold.
3. Landauer biological transfer prior: gene-group timing and expression
   decisions should be bounded by thermodynamic information cost.
4. Cancer bad-compression explanation prior: cancer is discussed as a possible
   compression/entropy-coding failure mode. The intended use is explanatory
   modeling and measurement, not treatment design.
5. Binding-site topology prior: drug binding is reframed as topology encoded
   by molecular pockets and thermodynamic correction paths.
6. Compression pipeline prior: logogram sidecars, omindirection atoms,
   vectorless high-retention stores, and topology agents are linked into one
   measurement-first Hutter/compression architecture.

## Evidence Lines

```json
{json.dumps(evidence, indent=2, sort_keys=True)}
```

## Term Counts

```json
{json.dumps(counts, indent=2, sort_keys=True)}
```

## Claim Boundary

This brief preserves the internal research conversation. It does not prove
biology, medicine, oncology, thermodynamics, compression competitiveness,
Hutter Prize standing, or drug efficacy. The cancer material is a
compression-based explanatory prior only. It must not be used as advice,
diagnosis, treatment guidance, or a treatment goal.
"""
    brief.write_text(brief_text, encoding="utf-8")

    files = [
        str(source_copy.relative_to(ROOT)),
        str(transcript.relative_to(ROOT)),
        str(brief.relative_to(ROOT)),
        str(graph_path.relative_to(ROOT)),
    ]
    tags = [
        "venice",
        "conversation-ingest",
        "compression-biology",
        "landauer",
        "genome-geodesic",
        "bad-compression-explanation",
        "logogram-sidecar",
        "vectorless-database",
        "topology-agents",
        "claim-boundary",
    ]
    package = ensure_package(
        "Venice Research Stack Conversation ENE Brief",
        brief_text,
        tags,
        files,
        evidence,
    )
    manifest_added = append_manifest_if_missing(manifest_entry(transcript))

    source_body = f"""
This tiddler records the targeted ingest of:

```
{SOURCE}
```

Transcript:

```
{transcript.relative_to(ROOT)}
```

ENE brief:

```
{brief.relative_to(ROOT)}
```

Graph edges:

```
{graph_path.relative_to(ROOT)}
```

Source SHA-256:

```
{source_hash}
```

ENE package:

```
{package["pkg"]}
rowid: {package["rowid"]}
```

!! Core Lanes

* [[Genome Geodesic Compression Prior]]
* [[Cancer Bad Compression Explanation Prior]]
* [[Math Logogram Surface Compiler]]
* [[Omindirection Logogram Contract]]
* [[Substrate FTS Query Surface]]

!! Claim Boundary

This is a conversation source. It preserves concept lineage and does not prove
external scientific, medical, compression, or hardware claims.
"""
    (WIKI_DIR / "Venice Research Stack Conversation.tid").write_text(
        tiddler(
            "Venice Research Stack Conversation",
            "ResearchStack Venice Conversation ENEIngest CompressionBiology ClaimBoundary",
            source_body,
        ),
        encoding="utf-8",
    )

    genome_body = f"""
Source: [[Venice Research Stack Conversation]]

Durable brief:

```
{brief.relative_to(ROOT)}
```

!! Prior

The conversation frames genome expression as a dynamic compression surface:

```
genome sequence
  -> eigen/geodesic expression manifold
  -> epigenetic curvature change
  -> thermodynamic information-cost bound
  -> emergent phenotype or held residual
```

This is useful as a GCCL research prior because it turns biological expression
into a receipt-bounded transition: baseline state, transformed state,
invariant, residual, cost, and claim boundary.

!! Evidence

* `genome_geodesic`: source line {evidence.get("genome_geodesic", {}).get("line", "missing")}
* `landauer_gene_transfer`: source line {evidence.get("landauer_gene_transfer", {}).get("line", "missing")}

!! Claim Boundary

This card is not a biological model, not a genetics claim, and not a medical
claim. It is a named hypothesis surface for future formalization and measurement.

!! Links

* [[GCCL Encoding Contract]]
* [[Genomic Data Compression Anchor]]
* [[Landauer Compression]]
* [[Omindirection Logogram Contract]]
"""
    (WIKI_DIR / "Genome Geodesic Compression Prior.tid").write_text(
        tiddler(
            "Genome Geodesic Compression Prior",
            "ResearchStack CompressionBiology Genome Geodesic Landauer ClaimBoundary",
            genome_body,
        ),
        encoding="utf-8",
    )

    cancer_body = f"""
Source: [[Venice Research Stack Conversation]]

Durable brief:

```
{brief.relative_to(ROOT)}
```

!! Compression Explanation Prior

The conversation preserves a speculative compression explanation:

```
cancer-like entropy coding signal
  -> possible biological codec failure
  -> inefficient residual/repair loop
  -> thermodynamic and topology measurements required
```

The usable research shape is not a treatment goal. It is a prompt for building
measurement receipts around entropy, topology, metabolic cost, state transition
reversibility, and sub-noticeable information drift.

The model is also not immune to the information-theoretic version of this
failure. Any GCCL, logogram, or omindirectional compression layer can accumulate
bit rot as residual creep: tiny unchecked substitutions, sidecar mismatches,
rounding losses, or topology-label drift that remain below ordinary notice until
they corrupt replay.

!! Evidence

* `cancer_bad_compression`: source line {evidence.get("cancer_bad_compression", {}).get("line", "missing")}
* `binding_site_topology`: source line {evidence.get("binding_site_topology", {}).get("line", "missing")}

!! Claim Boundary

This card is held as a compression-explanation prior. It is not medical advice,
not diagnosis, not therapy guidance, not a treatment goal, and not an oncology
claim. Any future biological use requires external biomedical sources, ethics
review where applicable, and independent measurement receipts.

!! Links

* [[Genome Geodesic Compression Prior]]
* [[Claim Boundary]]
* [[Semantic Topology Compression Regimes]]
"""
    (WIKI_DIR / "Cancer Bad Compression Explanation Prior.tid").write_text(
        tiddler(
            "Cancer Bad Compression Explanation Prior",
            "ResearchStack CompressionBiology Cancer CompressionExplanation ClaimBoundary Held",
            cancer_body,
        ),
        encoding="utf-8",
    )

    topology_agent_body = f"""
Source: [[Venice Research Stack Conversation]]

!! Prior

The conversation links Hutter/compression agents to topology detection:

```
topology agent
  -> fold / tear / boundary labels
  -> vectorless token-retention store
  -> sidecar dictionary optimization
  -> omindirectional atom decision
```

This is directly relevant to the current logogram sidecar work. The agent does
not replace receipts. It proposes candidate topology labels that must be
replayed through the substitution audit and omindirection compiler.

!! Evidence

* `vectorless_database`: source line {evidence.get("vectorless_database", {}).get("line", "missing")}
* `topology_agents`: source line {evidence.get("topology_agents", {}).get("line", "missing")}

!! Links

* [[Math Logogram Surface Compiler]]
* [[Omindirection Logogram Contract]]
* [[Substrate FTS Query Surface]]
* [[Hutter Prize Compression]]
"""
    (WIKI_DIR / "Hutter Topology Agent Prior.tid").write_text(
        tiddler(
            "Hutter Topology Agent Prior",
            "ResearchStack Hutter Compression Topology Agents VectorlessDatabase Sidecar",
            topology_agent_body,
        ),
        encoding="utf-8",
    )

    updated_indexes = {
        "Conversation Mining Source Map": append_link_once(
            WIKI_DIR / "Conversation Mining Source Map.tid",
            "!! Venice Conversation Ingest",
            "[[Venice Research Stack Conversation]]",
        ),
        "Mined Conversation Concepts": append_link_once(
            WIKI_DIR / "Mined Conversation Concepts.tid",
            "!! Venice Conversation Concepts",
            "[[Genome Geodesic Compression Prior]] / [[Cancer Bad Compression Explanation Prior]] / [[Hutter Topology Agent Prior]]",
        ),
        "Compression and Soliton Mining": append_link_once(
            WIKI_DIR / "Compression and Soliton Mining.tid",
            "!! Venice Compression Biology Batch",
            "[[Hutter Topology Agent Prior]]",
        ),
    }

    receipt = {
        "schema": "venice_research_stack_conversation_ingest_v1",
        "lawful": True,
        "source": str(SOURCE),
        "source_hash": source_hash,
        "source_copy": str(source_copy.relative_to(ROOT)),
        "source_copy_hash": sha256_path(source_copy),
        "transcript": str(transcript.relative_to(ROOT)),
        "transcript_hash": sha256_path(transcript),
        "brief": str(brief.relative_to(ROOT)),
        "brief_hash": sha256_path(brief),
        "graph_edges": str(graph_path.relative_to(ROOT)),
        "graph_edge_count": len(graph_edges),
        "manifest_added": manifest_added,
        "package": package,
        "wiki_tiddlers": [
            "6-Documentation/tiddlywiki-local/wiki/tiddlers/Venice Research Stack Conversation.tid",
            "6-Documentation/tiddlywiki-local/wiki/tiddlers/Genome Geodesic Compression Prior.tid",
            "6-Documentation/tiddlywiki-local/wiki/tiddlers/Cancer Bad Compression Explanation Prior.tid",
            "6-Documentation/tiddlywiki-local/wiki/tiddlers/Hutter Topology Agent Prior.tid",
        ],
        "updated_indexes": updated_indexes,
        "evidence": evidence,
        "term_counts": counts,
        "claim_boundary": "Conversation ingest only; compression-explanation prior, not treatment goal; no external science, medical, compression-win, or hardware proof claim.",
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
