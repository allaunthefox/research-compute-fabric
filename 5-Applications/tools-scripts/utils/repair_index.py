#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
# PTOS: LAYER=RULE / DOMAIN=DATA / CONDITION=STABLE / STAGE=ACTIVE / SOURCE=CODE
"""
Substrate Index Repair Pass
===========================
Fixes several categories of data point mismatches:

  1. Backfill meta_capsule_hash  — 231 capsules without SHA256
  2. Derive missing idea_weights + concept_anchor + foam_score
     for nodes that have descriptions/tags but no semantic weights
  3. Backfill compression_ratio into waveprobe_sig dicts where derivable
  4. Audit tier/domain overload
  5. Reclassify legacy DATA or NULL PTOS domains when a deterministic
     operational-domain inference is confident enough

Does NOT promote RESEARCH → canonical tiers (that requires human review)
but it does repair operational-domain catch-alls so the backlog is smaller
and more queryable.

Usage:
    python3 5-Applications/scripts/repair_index.py [--dry-run]
"""

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from substrate_git_index import _open_db, _PHI, _concept_vector_from_weights

# ── helpers ──────────────────────────────────────────────────────────────────

_STOP = {"the","and","for","that","this","with","from","are","was","were",
         "have","been","will","would","could","should","which","their","there",
         "these","those","what","when","where","how","all","any","can","not",
         "but","also","its","into","over","each","more","other","used","using"}

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

_PTOS_DOMAIN_KEYWORDS: dict[str, set[str]] = {
    "COMPUTE": {
        "compute", "compression", "codec", "encode", "decode", "algorithm",
        "runtime", "kernel", "vm", "opcode", "instruction", "graph", "dag",
        "lut", "tsm", "substrate", "metafoam", "hutter", "script", "source",
        "interface", "executor", "smoother", "math", "mathematics",
        "geometry", "topology", "theorem", "proof", "equation", "invariant",
        "torsion", "mobius", "polytope", "patamathematics", "pataphysics",
    },
    "TOKEN": {
        "token", "omnitoken", "wallet", "mint", "burn", "settlement",
    },
    "RULE": {
        "rule", "govern", "legal", "ethic", "policy", "constraint", "audit",
        "patent", "license", "compliance", "safety", "protocol", "rights",
        "eula", "review",
    },
    "STORE": {
        "store", "storage", "archive", "manifest", "capsule", "vault",
        "database", "sqlite", "index", "query", "schema", "table", "row",
        "column", "persist", "metadata", "fingerprint", "build", "target",
    },
    "POWER": {
        "power", "energy", "thermal", "heat", "battery", "voltage", "current",
        "econom", "market", "incentive", "budget", "bom",
    },
    "COMMS": {
        "comms", "communic", "network", "protocol", "radio", "signal",
        "packet", "route", "mesh", "http", "api", "bridge", "bus", "ipc",
        "transport",
    },
    "MATERIAL": {
        "material", "chem", "molecule", "atomic", "atom", "orbital",
        "superconductor", "silicon", "wafer", "pcb", "hdl", "asic", "chip",
        "lithography", "nanowire", "qchem", "hardware", "risc", "kda",
    },
    "DATA": {
        "data", "dataset", "json", "csv", "session", "transcript",
        "document", "text", "note", "record", "corpus", "import", "chat",
        "summary",
    },
    "CLOCK": {
        "clock", "time", "timing", "tick", "latency", "temporal", "phase",
        "schedule",
    },
    "TEST": {
        "test", "tests", "testing", "validation", "verify", "verified",
        "benchmark", "assert", "rigor", "experiment", "ab_test", "run_matrix",
    },
}

_CONCEPT_TO_PTOS = {
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

_PTOS_HEADER_RE = re.compile(
    r"PTOS:\s*LAYER=\w+\s*/\s*DOMAIN=(?P<domain>\w+)",
    re.IGNORECASE,
)

def _extract_weights(text: str) -> dict:
    tokens = re.findall(r"\b[a-zA-Z][a-zA-Z_]{4,}\b", text.lower())
    counts = Counter(t for t in tokens if t not in _STOP)
    if not counts:
        return {}
    max_c = counts.most_common(1)[0][1]
    weights = {}
    for word, count in counts.most_common(25):
        score = min(1.0, (count / max_c) * 0.85)
        if score >= 0.10:
            weights[word] = round(score, 3)
    return weights


def _read_head(path: Path, limit: int = 8192) -> str:
    try:
        with open(path, "rb") as f:
            raw = f.read(limit)
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""


def _load_json(raw: str | None):
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _keyword_score(tokens: Counter[str], keywords: set[str]) -> float:
    score = 0.0
    for token, count in tokens.items():
        for keyword in keywords:
            if token.startswith(keyword):
                score += min(count, 6)
                break
    return score


def _infer_domain_from_row(
    pkg: str,
    module: str | None,
    archetype: str | None,
    description: str | None,
    tags_raw: str | None,
    files_raw: str | None,
    session_id: str | None,
    concept_anchor_raw: str | None,
) -> tuple[str, float]:
    """Infer a better PTOS domain for legacy DATA rows."""
    tags = _load_json(tags_raw) or []
    files = _load_json(files_raw) or []
    anchor = _load_json(concept_anchor_raw) or {}

    candidate_refs: list[str] = []
    if session_id:
        candidate_refs.append(session_id)
    candidate_refs.extend(str(f) for f in files[:8])

    resolved_paths: list[Path] = []
    seen: set[str] = set()
    for raw in candidate_refs:
        if not raw:
            continue
        p = Path(raw)
        probes = [p]
        if not p.is_absolute():
            probes.append(REPO / p)
        for probe in probes:
            try:
                rp = probe.resolve()
            except Exception:
                rp = probe
            key = str(rp)
            if key in seen:
                continue
            seen.add(key)
            if rp.exists():
                resolved_paths.append(rp)
                break

    header_domain = None
    content_snippets: list[str] = []
    for path in resolved_paths[:3]:
        head = _read_head(path)
        if head:
            content_snippets.append(head)
        if header_domain is None:
            m = _PTOS_HEADER_RE.search(head)
            if m:
                domain = m.group("domain").upper()
                if domain in _PTOS_DOMAINS:
                    header_domain = domain
    if header_domain is not None:
        return header_domain, 100.0

    path_hint_parts: list[str] = []
    for path in resolved_paths:
        if path.suffix == ".json" and path.name.endswith(".metadata.json"):
            continue
        try:
            rel = path.relative_to(REPO)
            path_hint_parts.append(str(rel))
        except Exception:
            path_hint_parts.append(str(path))
    path_hint = " ".join(path_hint_parts).lower()

    if any(part in path_hint for part in ("/target/", ".fingerprint/", "build-script", "run-build-script", ".rustc_info")):
        return "STORE", 12.0
    if any(part in path_hint for part in ("/src/", ".rs", ".py", ".c", ".sh")) and not any(
        part in path_hint for part in ("/tests/", "validation", "benchmark", "ab_test")
    ):
        # Source files default to COMPUTE unless strong test/rule cues override.
        early_compute = True
    else:
        early_compute = False

    if any(part in path_hint for part in ("validation", "verification", "/tests/", "benchmark", "ab_test", "run_matrix")):
        return "TEST", 11.0
    if any(part in path_hint for part in ("audit", "review", "policy", "legal", "ethic", "patent", "license", "safety_protocol", "safety")):
        return "RULE", 10.0
    if any(part in path_hint for part in ("bom", "pcb", "hdl", "asic", "chip", "wafer", "material", "qchem")):
        return "MATERIAL", 10.0
    if any(part in path_hint for part in ("manifest", "vault", "storage", "sqlite", "index", "archive_summary")):
        return "STORE", 10.0
    if early_compute:
        return "COMPUTE", 9.5

    text = " ".join(
        filter(
            None,
            [
                pkg,
                module or "",
                archetype or "",
                description or "",
                " ".join(map(str, tags)),
                str(anchor.get("domain", "")),
                path_hint,
                *content_snippets,
            ],
        )
    ).lower()
    tokens = Counter(re.findall(r"\b[a-zA-Z][a-zA-Z_]{2,}\b", text))
    weights = _extract_weights(text)

    scores = {domain: 0.0 for domain in _PTOS_DOMAINS}
    for domain, keywords in _PTOS_DOMAIN_KEYWORDS.items():
        scores[domain] += _keyword_score(tokens, keywords)
        for word, weight in weights.items():
            if any(word.startswith(keyword) for keyword in keywords):
                scores[domain] += 2.0 * float(weight)

    if early_compute:
        scores["COMPUTE"] += 4.0

    anchor_domain = str(anchor.get("domain", "")).lower()
    mapped = _CONCEPT_TO_PTOS.get(anchor_domain)
    if mapped:
        scores[mapped] += 3.0

    best = max(scores, key=lambda d: scores[d])
    if scores[best] <= 0.0:
        return "DATA", 0.0
    return best, scores[best]

def _detect_anchor(pkg: str, domain: str, description: str, tags_raw) -> dict:
    text = f"{pkg} {description or ''}".lower()
    tags = json.loads(tags_raw) if tags_raw else []
    tag_str = " ".join(tags).lower()

    if any(k in text+tag_str for k in ("hash","merkle","sha256","dag","crypto","attest")):
        dom = "compression"
    elif any(k in text+tag_str for k in ("hardware","kda","circuit","pcb","hdl","risc")):
        dom = "hardware"
    elif any(k in text+tag_str for k in ("hutter","enwik","compress","codec","lzma","entropy")):
        dom = "compression"
    elif any(k in text+tag_str for k in ("storage","store","archive","dedup","lut")):
        dom = "substrate"
    elif domain and domain != "DATA":
        dom = domain.lower()
    else:
        dom = "research"

    return {"domain": dom, "concept": re.sub(r"[^a-z0-9]+","_",pkg)[:60], "resolution": "FORMING"}


# ── repair passes ─────────────────────────────────────────────────────────────

def pass_capsule_hash(conn, dry_run: bool) -> int:
    """Compute SHA256 of meta_capsule string for all rows missing the hash."""
    rows = conn.execute(
        "SELECT rowid, pkg, meta_capsule FROM packages "
        "WHERE meta_capsule IS NOT NULL AND meta_capsule != '' "
        "AND (meta_capsule_hash IS NULL OR meta_capsule_hash = '')"
    ).fetchall()

    updated = 0
    for rowid, pkg, capsule in rows:
        h = hashlib.sha256(capsule.encode()).hexdigest()
        if not dry_run:
            conn.execute(
                "UPDATE packages SET meta_capsule_hash=? WHERE rowid=?", (h, rowid)
            )
        updated += 1

    if not dry_run:
        conn.commit()
    print(f"  capsule_hash: backfilled {updated} rows")
    return updated


def pass_compression_ratio(conn, dry_run: bool) -> int:
    """Derive compression_ratio = 8 / bpb_zlib and write back into meta_capsule JSON."""
    rows = conn.execute(
        "SELECT rowid, pkg, meta_capsule FROM packages "
        "WHERE meta_capsule LIKE '%waveprobe_sig%'"
    ).fetchall()

    updated = 0
    for rowid, pkg, capsule in rows:
        try:
            d = json.loads(capsule)
        except Exception:
            continue
        ws = d.get("waveprobe_sig", {})
        if ws.get("compression_ratio") is not None:
            continue
        bpb = ws.get("bpb_zlib")
        if not bpb or bpb <= 0:
            continue
        ws["compression_ratio"] = round(8.0 / bpb, 4)
        new_capsule = json.dumps(d)
        new_hash = hashlib.sha256(new_capsule.encode()).hexdigest()
        if not dry_run:
            conn.execute(
                "UPDATE packages SET meta_capsule=?, meta_capsule_hash=? WHERE rowid=?",
                (new_capsule, new_hash, rowid)
            )
        updated += 1

    if not dry_run:
        conn.commit()
    print(f"  compression_ratio: derived for {updated} rows")
    return updated


def pass_semantic_weights(conn, dry_run: bool) -> int:
    """Rebuild idea_weights + concept_anchor + foam_score for nodes missing them."""
    rows = conn.execute(
        "SELECT rowid, pkg, domain, description, tags, files "
        "FROM packages "
        "WHERE idea_weights IS NULL OR idea_weights = '' OR idea_weights = '{}'"
    ).fetchall()

    updated = 0
    for rowid, pkg, domain, description, tags_raw, files_raw in rows:
        # Build text signal from all available fields
        files = json.loads(files_raw) if files_raw else []
        file_stems = " ".join(Path(f).stem.replace("-","_").replace(" ","_")
                             for f in files)
        text = f"{pkg} {description or ''} {file_stems}"

        weights = _extract_weights(text)
        if not weights:
            # Minimal fallback from pkg name tokens
            weights = {t: 0.5 for t in re.findall(r"[a-z]{4,}", pkg.lower())[:5]}
        if not weights:
            print(f"    [skip] {pkg}: no extractable weights")
            continue

        vec = _concept_vector_from_weights(weights)
        anchor = _detect_anchor(pkg, domain, description or "", tags_raw)
        foam = round(sum(weights.values()) / max(len(weights), 1) * _PHI, 4)

        if not dry_run:
            conn.execute(
                "UPDATE packages SET idea_weights=?, concept_vector=?, "
                "concept_anchor=?, foam_score=? WHERE rowid=?",
                (json.dumps(weights), json.dumps(vec),
                 json.dumps(anchor), foam, rowid)
            )
        updated += 1
        print(f"    rebuilt: {pkg}  foam={foam:.3f}  "
              f"axes={sum(1 for x in vec if x > 0.01)}/14")

    if not dry_run:
        conn.commit()
    print(f"  semantic_weights: rebuilt for {updated} rows")
    return updated


def pass_tier_domain_audit(conn) -> None:
    """Report tier/domain overload — does not modify data."""
    total = conn.execute("SELECT COUNT(*) FROM packages").fetchone()[0]
    research = conn.execute(
        "SELECT COUNT(*) FROM packages WHERE tier='RESEARCH'"
    ).fetchone()[0]
    data_dom = conn.execute(
        "SELECT COUNT(*) FROM packages WHERE domain='DATA'"
    ).fetchone()[0]
    print(f"  RESEARCH tier: {research}/{total} "
          f"({100*research//total}%) — schema says transitional/intake only")
    print(f"  DATA domain:   {data_dom}/{total} "
          f"({100*data_dom//total}%) — schema expects domain-specific classification")
    print(f"  Action needed: human tier-promotion pass "
          f"(RESEARCH → SINGULARITY/PLASMA/CRYSTALLINE/FOAM/GOVERNANCE)")

    # Show canonical tier distribution for non-RESEARCH rows
    rows = conn.execute(
        "SELECT tier, COUNT(*) FROM packages WHERE tier != 'RESEARCH' "
        "GROUP BY tier ORDER BY 2 DESC"
    ).fetchall()
    print(f"  Promoted nodes already:")
    for tier, n in rows:
        print(f"    {tier}: {n}")


def pass_data_domain_reclassify(conn, dry_run: bool) -> int:
    """Promote legacy DATA/NULL rows to more specific PTOS domains when confident."""
    rows = conn.execute(
        "SELECT rowid, pkg, module, archetype, description, tags, files, "
        "session_id, concept_anchor "
        "FROM packages WHERE domain='DATA' OR domain IS NULL OR domain=''"
    ).fetchall()

    updated = 0
    for rowid, pkg, module, archetype, description, tags_raw, files_raw, session_id, concept_anchor_raw in rows:
        inferred, score = _infer_domain_from_row(
            pkg, module, archetype, description, tags_raw, files_raw, session_id, concept_anchor_raw
        )
        if inferred == "DATA":
            continue
        if score < 6.0:
            continue
        if not dry_run:
            conn.execute(
                "UPDATE packages SET domain=? WHERE rowid=?",
                (inferred, rowid),
            )
        updated += 1

    if not dry_run:
        conn.commit()
    print(f"  data_domain_reclassify: promoted {updated} rows")
    return updated


# ── main ─────────────────────────────────────────────────────────────────────

def run(dry_run: bool = False) -> None:
    conn = _open_db()

    print(f"Substrate Index Repair  {'[DRY RUN]' if dry_run else '[LIVE]'}")
    print(f"DB: {REPO / 'substrate_index.db'}")
    total = conn.execute("SELECT COUNT(*) FROM packages").fetchone()[0]
    print(f"Total rows: {total}\n")

    print("Pass 1: meta_capsule_hash backfill")
    pass_capsule_hash(conn, dry_run)

    print("\nPass 2: compression_ratio derivation")
    pass_compression_ratio(conn, dry_run)

    print("\nPass 3: semantic weights rebuild")
    pass_semantic_weights(conn, dry_run)

    print("\nPass 4: tier/domain overload audit")
    pass_tier_domain_audit(conn)

    print("\nPass 5: legacy DATA domain reclassification")
    pass_data_domain_reclassify(conn, dry_run)

    print("\nPost-pass audit")
    pass_tier_domain_audit(conn)

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    run(dry_run=args.dry_run)
