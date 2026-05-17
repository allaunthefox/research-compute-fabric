#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
# PTOS: LAYER=STORE / DOMAIN=DATA / CONDITION=EXPERIMENTAL / STAGE=ACTIVE / SOURCE=CODE
"""
Archive Ingestor — Bulk tag every archived document into the substrate index.
=============================================================================

CONCEPT
-------
Every file in 6-Documentation/archive/ represents a research artifact — a spec, a session
note, a prior-art document, a design sketch. Most of them are invisible to
the metanarrative graph because they were never indexed.

This script walks the archive, extracts keyword signal from each file, and
ingests it as a lightweight RESEARCH-tier row in the SQLite index. After
running, cmd_connect() can find relationships between current work and
archived material — the "high speed connector."

WHAT IT DOES
------------
For each .md, .txt, .json, .py file in the archive (or a target directory):

  1. Read the file content (first 8KB — enough for keyword signal)
  2. Extract keyword frequencies using a domain-aware word scorer
  3. Map to the 14-axis concept_vector cluster vocabulary
  4. Auto-detect concept_anchor: domain from dominant keyword cluster,
     concept from file stem, resolution from PTOS CONDITION tag if present
  5. Write a row to the SQLite index via cmd_ingest_session() logic

The indexed rows are READ-ONLY references — the ingestor never modifies
the archive files. It just makes them queryable.

WHAT IT DOES NOT DO
-------------------
- Generate high-quality idea_weights (use cmd_ingest_session for that)
- Understand the content semantically (keyword frequency only)
- Replace manually crafted session JSON files
- Serve as the canonical home for curated session capsules, literature maps,
  or hand-authored relevance notes that already carry explicit semantic fields
- Index binary files, images, or large datasets

USAGE
-----
  # Index everything in 6-Documentation/archive/ (dry-run first)
  python3 5-Applications/scripts/ingest_archive.py --dry-run

  # Full run
  python3 5-Applications/scripts/ingest_archive.py

  # Index a specific subdirectory
  python3 5-Applications/scripts/ingest_archive.py --path 6-Documentation/archive/CATEGORY/TSM

  # Show what's already indexed
  python3 5-Applications/scripts/ingest_archive.py --status

  # Re-index (overwrite existing rows)
  python3 5-Applications/scripts/ingest_archive.py --force
"""

import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# ─── repo root ───────────────────────────────────────────────────────────────
REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "scripts"))

try:
    from substrate_git_index import (
        DB_PATH, _open_db, _concept_vector_from_weights, _upsert_package, _PHI,
    )
except ImportError as e:
    print(f"[error] cannot import substrate_git_index: {e}", file=sys.stderr)
    sys.exit(1)

try:
    from ingest_attachments import collect_auto_attachments
except ImportError as e:
    print(f"[error] cannot import ingest_attachments: {e}", file=sys.stderr)
    sys.exit(1)

try:
    from ingest_text_hygiene import derive_safe_description
except ImportError as e:
    print(f"[error] cannot import ingest_text_hygiene: {e}", file=sys.stderr)
    sys.exit(1)

# ─── configuration ────────────────────────────────────────────────────────────

ARCHIVE_ROOT = REPO / "archive"
SESSIONS_DIR = REPO / "sessions"

# File extensions to index
INDEXABLE = {".md", ".txt", ".rst", ".json", ".py", ".sh", ".rs", ".c"}

# Max bytes to read per file for keyword extraction
READ_LIMIT = 8192

# Skip files matching these patterns (noise, dependencies, license files)
SKIP_PATTERNS = [
    r"site-packages",
    r"__pycache__",
    r"\.git/",
    r"LICENSE",
    r"CHANGELOG",
    r"requirements\.txt",
    r"Cargo\.lock",
    r"package-lock",
]

# ─── keyword → concept cluster mapping ───────────────────────────────────────
# Same 14-axis vocabulary as substrate_git_index._concept_vector_from_weights
# Axis 0: substrate/foam
# Axis 1: compression/codec
# Axis 2: graph/dag
# Axis 3: hardware
# Axis 4: time/planck
# Axis 5: crypto/hash
# Axis 6: database
# Axis 7: semantic/language
# Axis 8: physics/entropy
# Axis 9: security
# Axis 10: os/vm
# Axis 11: research/discovery
# Axis 12: omnitoken
# Axis 13: identity

_CLUSTER_KEYWORDS: dict[int, set[str]] = {
    0:  {"substrate", "foam", "voxel", "node", "fabric", "manifold", "register",
         "soliton", "tsm", "metafoam", "capsule"},
    1:  {"compress", "compression", "codec", "encode", "decode", "entropy",
         "huffman", "soliton", "symbol", "iso", "lut", "lookup", "prepass",
         "dictionary", "alphabet", "phoneme", "substitution", "bandwidth"},
    2:  {"graph", "dag", "node", "edge", "tree", "merkle", "hash", "pointer",
         "traversal", "topology", "manifold", "fractal"},
    3:  {"hardware", "risc", "fpga", "hdl", "asic", "pcb", "circuit", "chip",
         "kda", "rad", "trace", "silicon", "lithography", "nanowire"},
    4:  {"time", "planck", "clock", "tick", "timing", "synchron", "latency",
         "quantum", "temporal", "duration", "schedule"},
    5:  {"crypto", "hash", "sha256", "merkle", "zk", "stark", "proof",
         "signature", "seal", "attest", "verify", "provenance"},
    6:  {"database", "sql", "sqlite", "index", "query", "schema", "table",
         "row", "column", "fts", "search", "source", "git"},
    7:  {"semantic", "language", "concept", "meaning", "vector", "embed",
         "nlp", "token", "word", "text", "notation", "symbol", "translate",
         "analog", "idea", "weight", "research"},
    8:  {"physics", "entropy", "energy", "wave", "frequency", "field",
         "quantum", "particle", "force", "mass", "density", "pressure",
         "temperature", "superconductor", "photon", "electron", "orbital"},
    9:  {"security", "attack", "exploit", "vuln", "threat", "encrypt",
         "defense", "audit", "taint", "isolat", "sandbox", "secret"},
    10: {"os", "kernel", "process", "memory", "virtual", "vm", "hypervisor",
         "syscall", "opcode", "instruction", "runtime", "executor"},
    11: {"research", "discover", "hypothes", "theory", "experiment", "paper",
         "result", "finding", "analysis", "study", "novel", "specul"},
    12: {"omnitoken", "token", "bridge", "surface", "bus", "ipc", "transport",
         "protocol", "route", "mesh", "omni"},
    13: {"identity", "sovereign", "manifest", "provenance", "attestation",
         "ownership", "claim", "ptos", "tag", "classify"},
}

_ALL_CLUSTER_WORDS: dict[str, int] = {
    word: axis
    for axis, words in _CLUSTER_KEYWORDS.items()
    for word in words
}

_PTOS_DOMAINS = (
    "COMPUTE",
    "TOKEN",
    "RULE",
    "STORE",
    "POWER",
    "COMMS",
    "MATERIAL",
    "DATA",
    "CLOCK",
    "TEST",
)

_PTOS_HEADER_RE = re.compile(
    r"PTOS:\s*LAYER=\w+\s*/\s*DOMAIN=(?P<domain>\w+)",
    re.IGNORECASE,
)

_PTOS_DOMAIN_KEYWORDS: dict[str, set[str]] = {
    "COMPUTE": {
        "compute", "compression", "codec", "encode", "decode", "algorithm",
        "solver", "runtime", "kernel", "vm", "opcode", "instruction",
        "graph", "dag", "lut", "tsm", "substrate", "metafoam", "hutter",
    },
    "TOKEN": {
        "token", "omnitoken", "wallet", "mint", "burn", "settlement",
        "bridge", "surface",
    },
    "RULE": {
        "rule", "govern", "legal", "ethic", "policy", "constraint", "audit",
        "patent", "license", "compliance", "attest", "proof", "verifier",
        "verification", "rights", "eula",
    },
    "STORE": {
        "store", "storage", "archive", "manifest", "capsule", "vault",
        "persist", "database", "sqlite", "index", "query", "schema",
        "table", "row", "column", "dedup",
    },
    "POWER": {
        "power", "energy", "thermal", "heat", "battery", "voltage", "current",
        "econom", "market", "incentive", "plasma",
    },
    "COMMS": {
        "comms", "communic", "network", "protocol", "radio", "signal",
        "packet", "route", "mesh", "http", "api", "lora", "ax25", "vlf",
        "channel", "transport", "carrier", "bus", "ipc",
    },
    "MATERIAL": {
        "material", "chem", "molecule", "atomic", "atom", "orbital",
        "superconductor", "silicon", "wafer", "pcb", "hdl", "asic", "chip",
        "lithography", "nanowire", "qchem", "fabrication",
    },
    "DATA": {
        "data", "dataset", "json", "csv", "session", "transcript",
        "document", "text", "note", "metadata", "record", "corpus", "import",
    },
    "CLOCK": {
        "clock", "time", "timing", "tick", "latency", "temporal", "synchron",
        "phase", "schedule", "planck",
    },
    "TEST": {
        "test", "tests", "testing", "validation", "verify", "verified",
        "benchmark", "assert", "rigor", "check",
    },
}

_CONCEPT_TO_PTOS: dict[str, str] = {
    "compression": "COMPUTE",
    "substrate": "COMPUTE",
    "mathematics": "COMPUTE",
    "computation": "COMPUTE",
    "governance": "RULE",
    "containment": "RULE",
    "cryptography": "RULE",
    "economics": "POWER",
    "physics": "MATERIAL",
    "chemistry": "MATERIAL",
    "biology": "MATERIAL",
    "hardware": "MATERIAL",
    "linguistics": "COMMS",
    "geography": "DATA",
    "music": "DATA",
    "neuroscience": "DATA",
    "research": "DATA",
}

_PTOS_PRIORITY = {
    domain: i for i, domain in enumerate(
        ["RULE", "TEST", "STORE", "POWER", "CLOCK",
         "COMMS", "TOKEN", "MATERIAL", "COMPUTE", "DATA"]
    )
}


# ─── helpers ──────────────────────────────────────────────────────────────────

def _should_skip(path: Path) -> bool:
    s = str(path)
    return any(re.search(p, s) for p in SKIP_PATTERNS)


def _read_head(path: Path) -> str:
    """Read up to READ_LIMIT bytes, decode leniently."""
    try:
        with open(path, "rb") as f:
            raw = f.read(READ_LIMIT)
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""


def _extract_keywords(text: str) -> dict[str, float]:
    """Extract a lightweight idea_weights dict from raw text.

    Tokenises by word boundary, counts frequency, normalises to 0–1 range.
    Only keeps tokens that appear in the cluster vocabulary or are long
    enough to be meaningful (≥6 chars, not stop words).
    """
    _STOP = {"the", "and", "for", "that", "this", "with", "from", "are",
             "was", "were", "have", "been", "will", "would", "could", "should",
             "which", "their", "there", "these", "those", "what", "when",
             "where", "how", "all", "any", "can", "not", "but", "also"}

    tokens = re.findall(r"\b[a-zA-Z][a-zA-Z_]{4,}\b", text.lower())
    counts = Counter(t for t in tokens if t not in _STOP)

    if not counts:
        return {}

    total = sum(counts.values())
    max_c = counts.most_common(1)[0][1]

    weights: dict[str, float] = {}
    for word, count in counts.most_common(30):
        # Boost words that appear in cluster vocabulary
        boost = 2.0 if word in _ALL_CLUSTER_WORDS else 1.0
        score = min(1.0, (count / max_c) * boost * 0.85)
        if score >= 0.10:
            weights[word] = round(score, 3)

    return weights


def _detect_concept_anchor(path: Path, text: str) -> dict:
    """Heuristically assign a concept_anchor from file path and content."""
    stem = path.stem.lower().replace("-", "_").replace(" ", "_")

    # Detect domain from path components and content
    path_str = str(path).lower()
    content_lower = text.lower()

    if any(k in path_str for k in ("tsm", "soliton", "metafoam", "substrate")):
        domain = "substrate"
    elif any(k in path_str for k in ("superconductor", "hodh", "material", "qchem")):
        domain = "physics"
    elif any(k in path_str for k in ("compress", "codec", "hutter", "iso", "lut")):
        domain = "compression"
    elif any(k in path_str for k in ("govern", "legal", "patent", "ethic")):
        domain = "governance"
    elif any(k in path_str for k in ("kda", "hardware", "pcb", "hdl", "risc")):
        domain = "hardware"
    elif "SPECULATIVE" in text or "specul" in content_lower:
        domain = "substrate"
    else:
        domain = "research"

    # Resolution from PTOS CONDITION tag if present
    m = re.search(r"CONDITION=(\w+)", text)
    condition = m.group(1) if m else None
    resolution = {
        "STABLE": "STABLE",
        "EXPERIMENTAL": "FORMING",
        "EXTREME": "FORMING",
        "DRAFT": "SEED",
        "ARCHIVED": "STABLE",
        "STERILE": "STABLE",
    }.get(condition, "FORMING")

    return {"domain": domain, "concept": stem[:60], "resolution": resolution}


def _declared_ptos_domain(text: str) -> str | None:
    """Return an explicit PTOS DOMAIN if the document declares one."""
    m = _PTOS_HEADER_RE.search(text)
    if not m:
        return None
    domain = m.group("domain").upper()
    if domain in _PTOS_DOMAINS:
        return domain
    return None


def _keyword_score(tokens: Counter[str], keywords: set[str]) -> float:
    score = 0.0
    for token, count in tokens.items():
        for keyword in keywords:
            if token.startswith(keyword):
                score += min(count, 6)
                break
    return score


def _detect_ptos_domain(
    path: Path,
    text: str,
    idea_weights: dict[str, float],
    concept_anchor: dict,
) -> str:
    """Infer the PTOS operational domain for an archived artifact."""
    declared = _declared_ptos_domain(text)
    if declared is not None:
        return declared

    path_str = str(path).lower()
    path_hint = " ".join(part.lower() for part in path.parts[1:]) or path.name.lower()
    if any(k in path_hint for k in ("validation", "verification", "test", "tests", "benchmark", "rigor")):
        return "TEST"
    if any(k in path_hint for k in ("audit", "review", "policy", "legal", "ethic",
                                   "patent", "license", "compliance")):
        return "RULE"
    if any(k in path_hint for k in ("bom", "pcb", "hdl", "asic", "chip", "wafer",
                                   "fabrication", "superconductor", "qchem", "material")):
        return "MATERIAL"
    if any(k in path_hint for k in ("manifest", "vault", "storage", "store", "index", "sqlite")):
        return "STORE"

    tokens = Counter(re.findall(r"\b[a-zA-Z][a-zA-Z_]{2,}\b", f"{path_hint} {text.lower()}"))
    scores = {domain: 0.0 for domain in _PTOS_DOMAINS}

    # Path hints are high-confidence because archive placement is often curated.
    for domain, keywords in _PTOS_DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            if keyword in path_hint:
                scores[domain] += 3.5

    # A few operational path cues deserve stronger nudges.
    suffix = path.suffix.lower()
    if suffix in {".py", ".rs", ".c", ".sh"}:
        scores["COMPUTE"] += 2.5
    if suffix in {".json", ".jsonl", ".csv"}:
        scores["DATA"] += 1.5
    if any(k in path_hint for k in ("test", "tests", "validation", "benchmark", "rigor")):
        scores["TEST"] += 4.0

    # Weighted content/profile hits.
    for domain, keywords in _PTOS_DOMAIN_KEYWORDS.items():
        scores[domain] += _keyword_score(tokens, keywords)
        for word, weight in idea_weights.items():
            if any(word.startswith(keyword) for keyword in keywords):
                scores[domain] += 2.0 * float(weight)

    # Concept-domain crosswalk is a semantic fallback, not the only driver.
    concept_domain = str(concept_anchor.get("domain", "")).lower()
    mapped = _CONCEPT_TO_PTOS.get(concept_domain)
    if mapped:
        scores[mapped] += 3.0

    # A STORE note that is also a test should stay TEST if the evidence is comparable.
    best = max(
        _PTOS_DOMAINS,
        key=lambda domain: (scores[domain], -_PTOS_PRIORITY[domain]),
    )

    if scores[best] <= 0.0:
        return "DATA"
    return best


def _pkg_name(path: Path) -> str:
    """Derive a stable, unique pkg identifier from the file path."""
    rel = path.relative_to(REPO)
    # e.g. 6-Documentation/archive/CATEGORY/TSM/INTRO_TO_METAFOAM.md → arc-tsm-intro_to_metafoam
    parts = [p.lower()[:8] for p in rel.parts[:-1] if p.lower() not in
             ("archive", "sort this", "category", "research documents")]
    stem = re.sub(r"[^a-z0-9]+", "_", path.stem.lower())[:40]
    prefix = "-".join(p for p in parts if p)[:20]
    tag = f"arc-{prefix}-{stem}" if prefix else f"arc-{stem}"
    return tag[:80]


# ─── main ingestor ────────────────────────────────────────────────────────────

def ingest_file(
    path: Path,
    conn: sqlite3.Connection,
    force: bool = False,
    dry_run: bool = False,
) -> str:
    """Index a single archive file. Returns status: 'indexed', 'skipped', 'exists'."""
    if _should_skip(path):
        return "skipped"

    pkg = _pkg_name(path)
    version = "1.0.0"

    if not force:
        row = conn.execute(
            "SELECT pkg FROM packages WHERE pkg=? AND version=?", (pkg, version)
        ).fetchone()
        if row:
            return "exists"

    text = _read_head(path)
    if not text.strip():
        return "skipped"

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sha256 = hashlib.sha256(path.name.encode()).hexdigest()[:16]

    idea_weights = _extract_keywords(text)
    if not idea_weights:
        return "skipped"

    concept_vec = _concept_vector_from_weights(idea_weights)
    concept_anchor = _detect_concept_anchor(path, text)
    ptos_domain = _detect_ptos_domain(path, text, idea_weights, concept_anchor)
    foam_score = round(
        sum(idea_weights.values()) / max(len(idea_weights), 1) * _PHI, 4
    )

    description = derive_safe_description(path, text, max_len=200)

    tags = [concept_anchor["domain"], "archive", path.suffix.lstrip(".")]

    if dry_run:
        print(f"  [dry] {pkg}")
        print(f"        concept_domain={concept_anchor['domain']}  "
              f"ptos_domain={ptos_domain}  "
              f"resolution={concept_anchor['resolution']}  "
              f"axes={sum(1 for x in concept_vec if x > 0.01)}/14  "
              f"foam={foam_score}")
        return "dry"

    attached_files, attachment_meta = collect_auto_attachments(
        path, repo=REPO, mode="full"
    )

    _upsert_package(conn, {
        "pkg": pkg,
        "version": version,
        "layer": "RULE",
        "domain": ptos_domain,
        "condition": "EXPERIMENTAL",
        "stage": "ARCHIVED",
        "source": "NOTE",
        "tier": "RESEARCH",
        "module": path.stem[:40].upper().replace(" ", "_").replace("-", "_"),
        "archetype": "ARCHIVE_NODE",
        "tags": json.dumps(tags),
        "description": description,
        "files": json.dumps(attached_files),
        "depends": json.dumps([]),
        "foam_score": foam_score,
        "nd_point": json.dumps(concept_vec[:14]),
        "sealed_utc": now_utc,
        "visibility": "PRIVATE",
        "model_status": "REFERENCE_ONLY",
        "taint_status": "CLEAN",
        "session_id": str(path.relative_to(REPO)),
        "idea_weights": json.dumps(idea_weights),
        "extension_points": json.dumps([]),
        "concept_vector": json.dumps(concept_vec),
        "analog_map": json.dumps({}),
        "concept_anchor": json.dumps(concept_anchor),
        "attachment_meta": json.dumps(attachment_meta),
        "ingest_profile": json.dumps({
            "ingestor": "archive",
            "suffix": path.suffix.lower(),
            "text_chars": len(text),
        }),
        "indexed_utc": now_utc,
    })
    return "indexed"


def run(
    target: Path = ARCHIVE_ROOT,
    dry_run: bool = False,
    force: bool = False,
    extensions: set[str] = INDEXABLE,
) -> None:
    conn = _open_db()
    counts = Counter()

    files = sorted(target.rglob("*"))
    total = sum(1 for f in files if f.is_file() and f.suffix in extensions)
    print(f"Scanning {target.relative_to(REPO)}  ({total} indexable files)")

    for i, path in enumerate(files):
        if not path.is_file():
            continue
        if path.suffix not in extensions:
            continue

        status = ingest_file(path, conn, force=force, dry_run=dry_run)
        counts[status] += 1

        if i % 50 == 0 and not dry_run:
            conn.commit()
            print(f"  {i+1}/{total}  indexed={counts['indexed']}  "
                  f"exists={counts['exists']}  skipped={counts['skipped']}")

    if not dry_run:
        conn.commit()

    conn.close()

    print(f"\nDone.")
    print(f"  indexed : {counts['indexed']:>5}")
    print(f"  exists  : {counts['exists']:>5}")
    print(f"  skipped : {counts['skipped']:>5}")
    if dry_run:
        print(f"  dry     : {counts['dry']:>5}")


def cmd_status() -> None:
    conn = _open_db()
    rows = conn.execute(
        "SELECT COUNT(*) FROM packages WHERE stage='ARCHIVED'"
    ).fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM packages").fetchone()[0]
    conn.close()
    print(f"Archive nodes in index : {rows}")
    print(f"Total nodes in index   : {total}")


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk-index archive files into substrate index")
    parser.add_argument("--path",     default=str(ARCHIVE_ROOT), help="Directory to scan")
    parser.add_argument("--dry-run",  action="store_true",       help="Show what would be indexed")
    parser.add_argument("--force",    action="store_true",       help="Re-index existing entries")
    parser.add_argument("--status",   action="store_true",       help="Show index counts and exit")
    args = parser.parse_args()

    if args.status:
        cmd_status()
    else:
        run(
            target=Path(args.path),
            dry_run=args.dry_run,
            force=args.force,
        )
