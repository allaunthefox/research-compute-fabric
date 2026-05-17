# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: OBSERVERLESS STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

# [WARDEN BOUNDARY ENFORCEMENT INJECTED]
import sys
import os
try:
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from io_harness_compat import spawn_isolated_process, fetch_network_resource

#!/usr/bin/env python3
# PTOS: LAYER=STORE / DOMAIN=DATA / CONDITION=EXPERIMENTAL / STAGE=ACTIVE / SOURCE=CODE
"""
Substrate Git Index — provider-driven source index.
===================================================

POSITION IN THE STACK
---------------------
This script is the database layer that bridges configured artifact sources
and the rest of the substrate:

  Hardware Platform  (KDA / RISC-V nodes / HDL)
      ↑
  GraphVM OS         (TSM opcodes, FOAM voxels, substrate ISA, omnitoken bus)
      ↑
  Source-backed SQL DB ← THIS FILE
      ├── configured source    VCS / ledger / toolbelt / filesystem reports
      ├── SQLite index         queryable PTOS-tagged package registry
      └── HTTP query API       substrate-facing query interface

CONCEPT
-------
Every `pkg/*` tag pushed to a configured git source carries a full PTOS
manifest in its annotation (written by metafoam_pkg.py).  This script can
intercept that push via a server-side post-receive hook, parse the JSON
annotation, and insert a row into a SQLite database whose schema maps 1-to-1
to the PTOS tag axes.

The result: any configured source can feed a custom SQL backend.  Git handles
durability and content-addressing for git sources; SQLite handles queryability;
PTOS tags are the schema.

  git object store  ≡  row storage (BLOB columns)
  annotated tag     ≡  typed SQL row
  PTOS manifest     ≡  column values
  depends[]         ≡  foreign key references
  sha256            ≡  primary content hash
  meta_capsule      ≡  compressed full-row backup

MODES
-----
This script runs in three distinct modes:

  1. hook   — post-receive stdin mode.
     Git calls this after a push.  Reads  <old> <new> <ref>  lines from
     stdin.  For each refs/tags/pkg/* ref, reads the tag annotation from
     the git object, parses the PTOS JSON, and indexes it into SQLite.
     Install it with the source-aware wrapper:
       python3 substrate_git_index.py install --repo <bare-git-repo> --source <source-name>

  2. serve  — HTTP query server daemon.
     Listens on a TCP port (default 7743).  Accepts JSON queries and
     returns package records.  Designed to be the substrate's "SQL
     endpoint" — any component can ask "give me all CRYSTALLINE packages"
     and get back git tag refs + metadata.

  3. CLI    — local admin commands (index, query, status, install).
     Direct SQLite interaction without the HTTP layer.

SQL SCHEMA
----------
The packages table maps directly to PTOS_TAG_SCHEMA axes.
Every column corresponds to a field in the tag annotation JSON.

  packages (
    pkg               TEXT     package name (from PACKAGES registry)
    version           TEXT     semver
    layer             TEXT     CORE | CARRY | RULE | STORE | EXTERNAL
    domain            TEXT     COMPUTE | TOKEN | RULE | STORE | …
    condition         TEXT     STABLE | EXPERIMENTAL | EXTREME | …
    stage             TEXT     ACTIVE | INTAKE | REVIEW | HOLD | ARCHIVED
    source            TEXT     CODE | SPEC | NOTE | DATA | …
    tier              TEXT     SINGULARITY | PLASMA | CRYSTALLINE | FOAM | …
    module            TEXT     uppercase module identifier
    archetype         TEXT     optional semantic archetype
    tags              TEXT     JSON array of string labels
    description       TEXT     human-readable summary
    files             TEXT     JSON array of repo-relative paths
    depends           TEXT     JSON array of dependency pkg/version strings
    foam_score        REAL     φ-ratio quality metric (higher = denser)
    nd_point          TEXT     JSON array of 14 f64 omnitoken axis values
    sha256            TEXT     SHA-256 of sorted file contents
    sealed_utc        TEXT     ISO8601Z build timestamp
    verification_basis TEXT    DECLARED | OBSERVED | CROSS_CHECKED | PHYSICS_BOUND
    visibility        TEXT     PRIVATE | INTERNAL | SELECTIVE | PUBLIC
    model_status      TEXT     CANONICAL | REFERENCE_ONLY | QUARANTINED | REJECTED
    taint_status      TEXT     CLEAN | SENSITIVE | CONTAMINATED | EXCLUDED
    meta_capsule      TEXT     base64url(zlib(json(manifest)))
    meta_capsule_hash TEXT     sha256 of meta_capsule string
    tag_name          TEXT     full git tag name, e.g. pkg/usc-audio/v1.0.0
    commit_hash       TEXT     git commit SHA the tag points to
    indexed_utc       TEXT     when this row was inserted by the hook
    idea_weights      TEXT     JSON dict: {"key insight": 0.0-1.0} (RESEARCH tier)
    extension_points  TEXT     JSON list of suggested extension targets
    session_id        TEXT     source LLM session identifier
    concept_vector    TEXT     JSON 14-float semantic embedding (direction = meaning)
    analog_map        TEXT     JSON dict: domain → nearest analog pkg
    concept_anchor    TEXT     JSON {domain, concept, resolution} — axis 5, PTOS schema
    spectral_band     TEXT     USC Spectral Band (e.g., X-RAY, OPTICAL)
    bekenstein_bound  REAL     Information capacity bound per N-space snag
    PRIMARY KEY (pkg, version)
  )

HTTP API
--------
The serve mode exposes a minimal JSON API on port 7743 (default):

  GET  /packages                       list all packages (summary)
  GET  /packages?<field>=<value>       filter by any PTOS field
  GET  /packages/<pkg>                 full record for latest version
  GET  /packages/<pkg>/<version>       full record for specific version
  POST /query   body: {"sql": "SELECT … WHERE …"}   raw SQL (SELECT only)
  GET  /health                         {"status":"ok","count":<n>}

All responses are JSON.  The SQL endpoint accepts arbitrary SELECT statements
against the packages table — the substrate can issue any query it needs.

INSTALL
-------
  # Install as post-receive hook for any bare git source
  python3 substrate_git_index.py install --repo /path/to/research-stack.git --source research-stack-bare-local

  # Start HTTP server (background)
  python3 substrate_git_index.py serve --port 7743 --db /var/lib/substrate/index.db &

  # Or install as systemd service
  python3 substrate_git_index.py install-service

Usage:
  python3 substrate_git_index.py hook                         post-receive mode (stdin)
  python3 substrate_git_index.py serve [--port N] [--db PATH] HTTP query server
  python3 substrate_git_index.py index <tag_name>             index one tag manually
  python3 substrate_git_index.py query "<WHERE clause>"       CLI SQL query
  python3 substrate_git_index.py status                       show indexed packages
  python3 substrate_git_index.py install --repo <path>        install as a git post-receive hook
  python3 substrate_git_index.py install-service              write systemd unit
  python3 substrate_git_index.py schema                       print CREATE TABLE
  python3 substrate_git_index.py drop <pkg> [version]         remove a record
"""

import base64
import hashlib
import http.server
import json
import os
import sqlite3
import subprocess
import sys
import urllib.parse
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / ".git").exists() or (parent / "AGENTS.md").exists():
            return parent
    return here.parents[3]


REPO_ROOT = _repo_root()


def _witness_config_path() -> Path:
    return Path(
        os.environ.get(
            "WITNESS_SOURCES_CONFIG",
            REPO_ROOT / "4-Infrastructure" / "witness" / "sources.json",
        )
    )


WITNESS_SOURCE = os.environ.get("WITNESS_SOURCE", "research-stack-github")


def _load_witness_sources(config_path: Path | None = None) -> dict[str, Any]:
    path = config_path or _witness_config_path()
    if not path.exists():
        return {"schema": "research_stack_witness_sources_v1", "sources": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _source_config(source_name: str = WITNESS_SOURCE) -> dict[str, Any]:
    data = _load_witness_sources()
    sources = data.get("sources", {})
    value = sources.get(source_name)
    if not isinstance(value, dict):
        return {}
    return value


def _file_url_to_path(url: str) -> Path | None:
    if url.startswith("file://"):
        return Path(urllib.parse.unquote(url[len("file://") :]))
    if "://" not in url and url:
        return Path(url)
    return None


def _repo_path_from_source(source_name: str = WITNESS_SOURCE) -> Path | None:
    source = _source_config(source_name)
    url = str(source.get("url", ""))
    return _file_url_to_path(url)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration — override via environment variables on the VPS
# ─────────────────────────────────────────────────────────────────────────────

# Path to the SQLite database file.
# On VPS: export SUBSTRATE_DB=/var/lib/substrate/index.db
DB_PATH = Path(
    os.environ.get("SUBSTRATE_DB", Path(__file__).parent.parent.parent / "substrate_index.db")
)

# Git repo to operate on (used by hook and index commands).
# The hook mode detects this automatically from GIT_DIR env var set by git.
REPO_PATH = Path(
    os.environ.get(
        "GIT_REPO_PATH",
        os.environ.get("SUBSTRATE_REPO", os.environ.get("GIT_DIR", Path(__file__).parent.parent)),
    )
)

# Default HTTP server port.
DEFAULT_PORT = int(os.environ.get("SUBSTRATE_PORT", "7743"))

# Tag prefix that identifies metafoam packages.
PKG_TAG_PREFIX = "refs/tags/pkg/"

# Bare git repo location (used by install command). Prefer an explicit
# GIT_REPO_PATH or a provider block in 4-Infrastructure/witness/sources.json.
DEFAULT_HOOK_REPO = (
    os.environ.get("GIT_REPO_PATH")
    or os.environ.get("SUBSTRATE_REPO")
    or (str(_repo_path_from_source()) if _repo_path_from_source() else "")
)


# ─────────────────────────────────────────────────────────────────────────────
# DB Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _upsert_package(db: sqlite3.Connection, row: dict) -> None:
    """Insert or replace a package record in the database."""
    cols = ", ".join(row.keys())
    placeholders = ", ".join(f":{k}" for k in row.keys())
    db.execute(
        f"INSERT OR REPLACE INTO packages ({cols}) VALUES ({placeholders})",
        row,
    )
    db.commit()

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS packages (
    pkg               TEXT NOT NULL,
    version           TEXT NOT NULL,
    layer             TEXT,
    domain            TEXT,
    condition         TEXT,
    stage             TEXT,
    source            TEXT,
    tier              TEXT,
    module            TEXT,
    archetype         TEXT,
    tags              TEXT,    -- JSON array
    description       TEXT,
    files             TEXT,    -- JSON array of repo-relative paths
    depends           TEXT,    -- JSON array of pkg/version dependency strings
    foam_score        REAL,
    nd_point          TEXT,    -- JSON array of 14 f64 values
    sha256            TEXT,
    sealed_utc        TEXT,
    verification_basis TEXT,
    visibility        TEXT,
    model_status      TEXT,
    taint_status      TEXT,
    meta_capsule      TEXT,
    meta_capsule_hash TEXT,
    tag_name          TEXT,
    commit_hash       TEXT,
    indexed_utc       TEXT,

    -- Semantic layer: idea weighting + metanarrative connection graph
    -- These fields are populated by RESEARCH-tier packages (chat sessions,
    -- research notes) and used by the connect / translate commands.

    idea_weights      TEXT,    -- JSON dict: {"key insight text": 0.0-1.0, …}
                               -- Higher weight = more conceptually dense moment
                               -- Used to prioritise which ideas to surface

    extension_points  TEXT,    -- JSON list of suggested extension targets
                               -- ["pkg/file:  what could be extended here", …]
                               -- Populated by the language miner or manually

    session_id        TEXT,    -- Source session identifier (LLM chat ID, doc ref)
                               -- Allows tracing a concept back to its origin

    concept_vector    TEXT,    -- JSON array of floats — richer semantic embedding
                               -- than nd_point (which is φ^-i positional).
                               -- Populated from idea_weights: each dimension is
                               -- the weight of a canonical concept cluster.
                               -- Used by cosine_similarity in cmd_connect().
                               -- Analogous to the engram pattern in hippocampal
                               -- semantic storage: direction encodes meaning, not
                               -- magnitude.  concept_anchor names the engram;
                               -- concept_vector is its activation pattern.

    analog_map        TEXT,    -- JSON dict: {"domain": "nearest pkg in that domain"}
                               -- Pre-computed local analog translations.
                               -- When a concept has no direct equivalent in a target
                               -- tier/domain, the nearest analog is cached here.
                               -- Same logic as best_domain_for_band() in the codec:
                               -- each concept finds its best carrier domain.

    concept_anchor    TEXT,    -- JSON object: concept lineage tag (axis 5 of PTOS schema)
                               -- Preserves metacontext that would otherwise be lost when
                               -- an artifact is compressed, encoded, or symbol-substituted.
                               -- Structure: {"domain": str, "concept": str, "resolution": str}
                               -- domain:     which knowledge domain the idea originated in
                               -- concept:    canonical snake_case identifier for the idea
                               -- resolution: settlement state — one of:
                               --   SEED        raw intuition, no defined edges
                               --   FORMING     actively developing, edges shifting
                               --   STABLE      well understood, not yet demonstrated
                               --   CRYSTALLIZED fully settled, compression-ready
                               --   COMPRESSED   has been encoded; tag is the decoder ring
                               --   RECOVERED    reconstructed from lineage after loss
                               -- Even after metatag recovery every other axis can be
                               -- reconstructed from content.  concept_anchor is the only
                               -- record of what the idea MEANT and how settled it WAS at
                               -- the time it was written — this is why it must survive
                               -- compression intact.

    PRIMARY KEY (pkg, version)
);
"""

# Full-text search virtual table over human-readable fields.
CREATE_FTS_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS packages_fts USING fts5(
    pkg, version, tier, domain, module, archetype, description, tags,
    content=packages, content_rowid=rowid
);
"""

CREATE_FTS_TRIGGER_INSERT = """
CREATE TRIGGER IF NOT EXISTS packages_fts_insert AFTER INSERT ON packages BEGIN
    INSERT INTO packages_fts(rowid, pkg, version, tier, domain, module,
                              archetype, description, tags)
    VALUES (new.rowid, new.pkg, new.version, new.tier, new.domain,
            new.module, new.archetype, new.description, new.tags);
END;
"""

CREATE_FTS_TRIGGER_DELETE = """
CREATE TRIGGER IF NOT EXISTS packages_fts_delete BEFORE DELETE ON packages BEGIN
    INSERT INTO packages_fts(packages_fts, rowid, pkg, version, tier, domain,
                              module, archetype, description, tags)
    VALUES ('delete', old.rowid, old.pkg, old.version, old.tier, old.domain,
            old.module, old.archetype, old.description, old.tags);
END;
"""


# ─────────────────────────────────────────────────────────────────────────────
# Database helpers
# ─────────────────────────────────────────────────────────────────────────────

# Columns added in the semantic layer (may not exist in older DBs).
_SEMANTIC_COLS = [
    "idea_weights", "extension_points", "session_id",
    "concept_vector", "analog_map", "concept_anchor",
    "attachment_meta", "ingest_profile",
]


def _open_db(path: Path = DB_PATH) -> sqlite3.Connection:
    """Open (or create) the SQLite database, apply schema if needed.

    # Why WAL mode?
    Write-Ahead Logging allows the HTTP server (reader) and the post-receive
    hook (writer) to run concurrently without blocking each other.  The hook
    fires during a git push; the HTTP server may be serving a query at the
    same time.  WAL eliminates the write-lock contention.

    # FTS5 virtual table
    Full-text search over pkg, module, description, tags — lets the substrate
    ask "find me everything related to 'soliton'" without needing to know the
    exact package name.

    # Schema migration
    Semantic layer columns (idea_weights, concept_vector, etc.) were added
    after the initial schema.  We ALTER TABLE to add them if missing so that
    existing DBs upgrade transparently without losing data.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(
        CREATE_TABLE_SQL
        + CREATE_FTS_SQL
        + CREATE_FTS_TRIGGER_INSERT
        + CREATE_FTS_TRIGGER_DELETE
    )
    # Migrate: add semantic columns to existing tables that predate them.
    existing = {
        row[1]
        for row in conn.execute("PRAGMA table_info(packages)").fetchall()
    }
    for col in _SEMANTIC_COLS:
        if col not in existing:
            conn.execute(f"ALTER TABLE packages ADD COLUMN {col} TEXT")
    conn.commit()
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict, parsing JSON columns."""
    d = dict(row)
    for col in ("tags", "files", "depends", "nd_point", "concept_anchor", "analog_map"):
        if d.get(col):
            try:
                d[col] = json.loads(d[col])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


# ─────────────────────────────────────────────────────────────────────────────
# Git helpers
# ─────────────────────────────────────────────────────────────────────────────

def _git(*args: str, repo: Path = REPO_PATH) -> str:
    """Run a git command in repo, return stdout stripped.

    # Bare repo awareness
    When called from a post-receive hook, GIT_DIR is set by git to the bare
    repo path.  We pass it explicitly in env so the command works whether
    called from a bare repo or a working-tree checkout.
    """
    env = os.environ.copy()
    # If repo is a bare repo (no .git subdir), set GIT_DIR directly.
    bare = repo / "HEAD"
    if bare.exists() and not (repo / ".git").exists():
        env["GIT_DIR"] = str(repo)
    result = subprocess.run(
        ["git"] + list(args),
        cwd=str(repo), capture_output=True, text=True,
        env=env, check=False,
    )
    return result.stdout.strip()


def _read_tag_annotation(tag_ref: str, repo: Path = REPO_PATH) -> str | None:
    """Read the annotation message from a git annotated tag.

    # How annotated tags work
    An annotated tag is a git object of type 'tag' (not 'commit').
    git cat-file tag <ref>  dumps the raw tag object, which ends with the
    annotation message after a blank line.

    For  refs/tags/pkg/usc-audio/v1.0.0  we need the short name
    pkg/usc-audio/v1.0.0  to pass to cat-file.
    """
    short = tag_ref.replace("refs/tags/", "")
    raw = _git("cat-file", "tag", short, repo=repo)
    if not raw:
        return None
    # Tag object format:
    #   object <sha>
    #   type commit
    #   tag <name>
    #   tagger ...
    #   <blank line>
    #   <annotation message — may be multi-line>
    parts = raw.split("\n\n", 1)
    if len(parts) < 2:
        return None
    return parts[1].strip()


def _resolve_commit(tag_ref: str, repo: Path = REPO_PATH) -> str:
    """Return the commit SHA that a tag points to (peeled through tag objects)."""
    short = tag_ref.replace("refs/tags/", "")
    return _git("rev-list", "-n1", short, repo=repo)


# ─────────────────────────────────────────────────────────────────────────────
# Professional Alignment Substrate
# ─────────────────────────────────────────────────────────────────────────────

# Heuristic mapping for PTOS Product Pillars (Synchronized with 8-Pillar Taxonomy)
PILLAR_MAP = {
    "core": {
        "product": "Sovereign Core (Production)",
        "goal": "Carrier Engine Execution & Substrate ISA",
        "tags": ["Core", "Carrier", "Production", "ISA"]
    },
    "docs": {
        "product": "Technical Specification (Docs)",
        "goal": "Formal Standards & Professional IP Alignment",
        "tags": ["Docs", "Spec", "IP", "Neutral"]
    },
    "roadmap": {
        "product": "Development Roadmap",
        "goal": "Integration & Convergence Planning",
        "tags": ["Roadmap", "Integration", "Convergence"]
    },
    "lab": {
        "product": "Research & Experiments (Lab)",
        "goal": "State-of-the-art Innovation & Performance Testing",
        "tags": ["Lab", "Research", "Experimental", "Vibrational"]
    },
    "tools": {
        "product": "Substrate Tooling",
        "goal": "Infrastructure Utilities & Indexer Integrity",
        "tags": ["Tools", "Utility", "Indexer", "Substrate"]
    },
    "infra": {
        "product": "System Infrastructure",
        "goal": "Pillar Definition & Environment Baseline",
        "tags": ["Infra", "System", "Config", "Warden"]
    },
    "data": {
        "product": "Permanent Archives",
        "goal": "Knowledge Preservation & Hutter Complexity Data",
        "tags": ["Data", "Archive", "Permanent", "Complexity"]
    },
    "audit": {
        "product": "Audit & Verification",
        "goal": "Technical Rigor & Professional Defensibility Results",
        "tags": ["Audit", "Verification", "Rigor", "Hardened"]
    }
}

def _professional_align(pkg_name: str, description: str, tags: list[str], 
                       idea_weights: dict[str, float]) -> tuple[str, list[str], dict[str, float]]:
    """Standardizes metadata with [Product]/[Goal] headers and aligns weights.
    
    This ensures that the 'Professional Alignment' is never a manual process.
    If a description already contains a [Product:] tag, it is preserved.
    """
    prefix = pkg_name.split("-")[0].lower()
    pillar = PILLAR_MAP.get(prefix)
    
    # 1. Smarter Pillar Identification (8-Pillar Taxonomy)
    if not pillar:
        # A. Keyword-based mapping
        keywords = {
            "core": ["isa", "engine", "carrier", "vrt", "annealer", "clock"],
            "docs": ["spec", "manifest", "alignment", "policy", "standard"],
            "roadmap": ["roadmap", "integration", "convergence", "phase"],
            "lab": ["research", "experimental", "hachimoji", "dna", "simulation", "test"],
            "tools": ["tool", "scripts", "utility", "indexer", "refactor"],
            "infra": ["infra", "config", "system", "warden", "platform", "kda"],
            "data": ["data", "archive", "enwik", "corpus", "patent", "store"],
            "audit": ["audit", "verification", "rigor", "assessment", "check", "governance"]
        }

        # Check name and tags for keywords
        search_str = (pkg_name + " " + " ".join(tags) + " " + description).lower()
        for p, kw_list in keywords.items():
            if any(kw in search_str for kw in kw_list):
                pillar = PILLAR_MAP[p]
                break
        
        # B. Fallback to path-based (package name as path)
        if not pillar:
            path = pkg_name.replace(".", "/").replace("-", "/")
            for p in PILLAR_MAP:
                if p in path:
                    pillar = PILLAR_MAP[p]
                    break
        
        # C. Absolute Fallback
        if not pillar:
            pillar = {
                "product": "General Substrate Node",
                "goal": "General Utility & Infrastructure",
                "tags": ["Infrastructure"]
            }

    # 2. Reformat Description
    # Only prepend if not already present
    if not description.startswith("[Product:"):
        new_desc = f"[Product: {pillar['product']}] [Goal: {pillar['goal']}] {description}"
    else:
        new_desc = description

    # 3. Synchronize Tags
    new_tags = list(set(tags) | set(pillar["tags"]))
    
    # 4. Align Weights for Cross-Referencing
    aligned_weights = dict(idea_weights)
    aligned_weights["product"] = max(aligned_weights.get("product", 0), 0.95)
    aligned_weights["goal"] = max(aligned_weights.get("goal", 0), 0.92)
    aligned_weights["explanation"] = max(aligned_weights.get("explanation", 0), 0.88)
    # Ensure the prefix itself is weighted if it's a pillar
    if prefix in PILLAR_MAP:
        aligned_weights[prefix.upper()] = 1.0

    return new_desc, new_tags, aligned_weights

# ─────────────────────────────────────────────────────────────────────────────
# Indexing
# ─────────────────────────────────────────────────────────────────────────────

def _index_tag(tag_ref: str, repo: Path = REPO_PATH,
               db: sqlite3.Connection | None = None) -> bool:
    """Parse one pkg/* tag annotation and upsert it into the SQLite index.

    # Why UPSERT (INSERT OR REPLACE)?
    The same tag may be rebuilt and re-pushed (metafoam_pkg.py build is
    idempotent).  We want the index to always reflect the latest build of
    a given (pkg, version) pair, not fail on duplicate primary key.

    # Parameters
      tag_ref : full ref name, e.g. refs/tags/pkg/usc-audio/v1.0.0
      repo    : path to git repo (working tree or bare)
      db      : open SQLite connection (if None, opens DB_PATH)

    # Returns
      True if indexing succeeded, False if the tag annotation is missing or
      not valid PTOS JSON.
    """
    annotation = _read_tag_annotation(tag_ref, repo)
    if not annotation:
        print(f"[index] WARN: no annotation for {tag_ref}", file=sys.stderr)
        return False

    try:
        manifest = json.loads(annotation)
    except json.JSONDecodeError as exc:
        print(f"[index] WARN: annotation not JSON for {tag_ref}: {exc}",
              file=sys.stderr)
        return False

    # Require the metafoam-pkg schema marker
    if manifest.get("schema") != "metafoam-pkg/v1":
        print(f"[index] skip {tag_ref}: schema={manifest.get('schema')!r}",
              file=sys.stderr)
        return False

    commit_hash = _resolve_commit(tag_ref, repo)
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _j(val: Any) -> str | None:
        """Serialise list/dict to JSON string; pass str/None through."""
        if val is None:
            return None
        if isinstance(val, (list, dict)):
            return json.dumps(val)
        return str(val)

    # ────────────────────────────────────────────────────────
    # Professional Alignment Step (Automated)
    # ────────────────────────────────────────────────────────
    pkg_name = manifest.get("pkg")
    raw_desc = manifest.get("description", "")
    raw_tags = manifest.get("tags", [])
    raw_weights = manifest.get("idea_weights", {})
    
    if not isinstance(raw_tags, list):
        raw_tags = []
    if not isinstance(raw_weights, dict):
        raw_weights = {}

    aligned_desc, aligned_tags, aligned_weights = _professional_align(
        pkg_name, raw_desc, raw_tags, raw_weights
    )

    row = {
        "pkg":               pkg_name,
        "version":           manifest.get("version"),
        "layer":             manifest.get("layer"),
        "domain":            manifest.get("domain"),
        "condition":         manifest.get("condition"),
        "stage":             manifest.get("stage"),
        "source":            manifest.get("source"),
        "tier":              manifest.get("tier"),
        "module":            manifest.get("module"),
        "archetype":         manifest.get("archetype"),
        "tags":              _j(aligned_tags),
        "description":       aligned_desc,
        "files":             _j(manifest.get("files")),
        "depends":           _j(manifest.get("depends")),
        "foam_score":        manifest.get("foam_score"),
        "nd_point":          _j(manifest.get("nd_point")),
        "sha256":            manifest.get("sha256"),
        "sealed_utc":        manifest.get("sealed_utc"),
        "verification_basis":manifest.get("verification_basis"),
        "visibility":        manifest.get("visibility"),
        "model_status":      manifest.get("model_status"),
        "taint_status":      manifest.get("taint_status"),
        "meta_capsule":      manifest.get("meta_capsule"),
        "meta_capsule_hash": manifest.get("meta_capsule_hash"),
        "tag_name":          tag_ref.replace("refs/tags/", ""),
        "commit_hash":       commit_hash,
        "indexed_utc":       now_utc,
        "idea_weights":      _j(aligned_weights),
        "concept_vector":    _j(_concept_vector_from_weights(aligned_weights))
    }

    close_after = db is None
    if db is None:
        db = _open_db()

    _upsert_package(db, row)

    if close_after:
        db.close()

    print(f"[index] {manifest.get('pkg')}/{manifest.get('version')} "
          f"tier={manifest.get('tier')} foam={manifest.get('foam_score')}")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Mode 1 — post-receive hook
# ─────────────────────────────────────────────────────────────────────────────

def cmd_hook() -> None:
    """Run as a git post-receive hook.

    # Invocation
    Git calls post-receive after updating all refs.  It passes one line per
    updated ref on stdin:
      <old-object-name> SP <new-object-name> SP <refname> LF

    We filter for refs/tags/pkg/* and index each one.

    # GIT_DIR
    When running as a server-side hook in a bare repo, GIT_DIR is set by git
    to the bare repo path.  _git() respects this automatically.

    # Bare repo path
    We use GIT_DIR if set (server-side hook), otherwise fall back to REPO_PATH
    (useful when testing locally in a working-tree checkout).
    """
    repo_path = Path(os.environ.get("GIT_DIR", str(REPO_PATH)))
    db = _open_db()

    indexed = 0
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 3:
            continue
        _old, _new, ref = parts
        if not ref.startswith(PKG_TAG_PREFIX):
            continue
        if _index_tag(ref, repo=repo_path, db=db):
            indexed += 1

    db.close()
    if indexed:
        print(f"[substrate] indexed {indexed} package tag(s) into {DB_PATH}")


# ─────────────────────────────────────────────────────────────────────────────
# Mode 2 — HTTP query server
# ─────────────────────────────────────────────────────────────────────────────

class _SubstrateHandler(http.server.BaseHTTPRequestHandler):
    """Minimal JSON HTTP handler for the substrate query API.

    # Endpoint summary
      GET  /health                       liveness check
      GET  /packages                     list all (summary fields only)
      GET  /packages?<field>=<value>     filter by PTOS field
      GET  /packages?search=<term>       full-text search via FTS5
      GET  /packages/<pkg>               latest version full record
      GET  /packages/<pkg>/<version>     specific version full record
      POST /query  {"sql": "SELECT …"}   raw SELECT against packages table

    # Security
    Only SELECT statements are accepted in /query.  INSERT, UPDATE, DELETE,
    DROP are rejected.  This is a substrate-internal service — it should not
    be exposed to the public internet.
    """

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: N802
        """Suppress default access log; substrate logging is in the caller."""

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, msg: str, status: int = 400) -> None:
        self._send_json({"error": msg}, status)

    def do_GET(self) -> None:  # noqa: N802
        """Handle GET requests."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = dict(urllib.parse.parse_qsl(parsed.query))

        conn = _open_db()

        if path == "/health":
            count = conn.execute("SELECT COUNT(*) FROM packages").fetchone()[0]
            self._send_json({"status": "ok", "packages": count,
                             "db": str(DB_PATH)})

        elif path == "/packages":
            self._handle_list(conn, params)

        elif path.startswith("/packages/"):
            parts = path[len("/packages/"):].split("/", 1)
            pkg = parts[0]
            version = parts[1] if len(parts) > 1 else None
            self._handle_get(conn, pkg, version)

        else:
            self._send_error("Not found", 404)

        conn.close()

    def do_POST(self) -> None:  # noqa: N802
        """Handle POST /query — raw SQL SELECT."""
        if self.path != "/query":
            self._send_error("Not found", 404)
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            req = json.loads(body)
        except json.JSONDecodeError:
            self._send_error("Invalid JSON body")
            return

        sql = req.get("sql", "").strip()
        if not sql.upper().startswith("SELECT"):
            self._send_error("Only SELECT statements are permitted")
            return

        conn = _open_db()
        try:
            rows = [_row_to_dict(r) for r in conn.execute(sql)]
            self._send_json({"rows": rows, "count": len(rows)})
        except sqlite3.Error as exc:
            self._send_error(str(exc))
        finally:
            conn.close()

    def _handle_list(self, conn: sqlite3.Connection, params: dict) -> None:
        """List packages, optionally filtered by PTOS field or FTS search."""
        SUMMARY_COLS = (
            "pkg, version, tier, domain, layer, module, archetype, "
            "foam_score, sealed_utc, visibility, taint_status"
        )

        search = params.pop("search", None)
        if search:
            # FTS5 search across pkg, module, description, tags
            rows = conn.execute(
                f"SELECT {SUMMARY_COLS} FROM packages WHERE rowid IN "
                f"(SELECT rowid FROM packages_fts WHERE packages_fts MATCH ?)",
                (search,),
            ).fetchall()
        elif params:
            # Filter by arbitrary PTOS field(s)
            # Only allow known column names to prevent injection
            SAFE_COLS = {
                "pkg", "version", "layer", "domain", "condition", "stage",
                "source", "tier", "module", "archetype", "visibility",
                "model_status", "taint_status", "verification_basis",
            }
            clauses = []
            values = []
            for col, val in params.items():
                if col in SAFE_COLS:
                    clauses.append(f"{col} = ?")
                    values.append(val)
            if not clauses:
                self._send_error("No valid filter fields provided")
                return
            where = " AND ".join(clauses)
            rows = conn.execute(
                f"SELECT {SUMMARY_COLS} FROM packages WHERE {where}",
                values,
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT {SUMMARY_COLS} FROM packages ORDER BY sealed_utc DESC"
            ).fetchall()

        self._send_json({"packages": [_row_to_dict(r) for r in rows],
                         "count": len(rows)})

    def _handle_get(self, conn: sqlite3.Connection,
                    pkg: str, version: str | None) -> None:
        """Return the full record for one package."""
        if version:
            row = conn.execute(
                "SELECT * FROM packages WHERE pkg=? AND version=?",
                (pkg, version),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM packages WHERE pkg=? ORDER BY sealed_utc DESC LIMIT 1",
                (pkg,),
            ).fetchone()

        if row is None:
            self._send_error(f"Package {pkg!r} not found", 404)
            return
        self._send_json(_row_to_dict(row))


def cmd_serve(port: int = DEFAULT_PORT) -> None:
    """Start the HTTP query server.

    # Binding
    Binds to 0.0.0.0 so both localhost (GraphVM OS) and the local network
    (other substrate nodes) can reach it.  For internet-facing deployments,
    put nginx in front and restrict to Tailnet / VPN.

    # Persistence
    The server is stateless — all state is in SQLite.  It can be restarted
    freely without losing data.  The WAL journal means in-progress queries
    are not affected by concurrent hook writes.
    """
    addr = ("0.0.0.0", port)
    server = http.server.HTTPServer(addr, _SubstrateHandler)
    print(f"[substrate] HTTP query server on port {port}")
    print(f"            DB: {DB_PATH}")
    print(f"            Endpoints: /health  /packages  /query")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[substrate] server stopped")


# ─────────────────────────────────────────────────────────────────────────────
# Mode 3 — CLI admin commands
# ─────────────────────────────────────────────────────────────────────────────

def cmd_index(tag_name: str) -> None:
    """Manually index one tag by name.

    # Use cases
    - Re-indexing after DB is wiped (disaster recovery)
    - Indexing tags that were pushed before the hook was installed
    - Testing the hook logic without a git push

    # Parameters
      tag_name : short tag name (e.g. pkg/usc-audio/v1.0.0) or full ref
    """
    ref = tag_name if tag_name.startswith("refs/") else f"refs/tags/{tag_name}"
    ok = _index_tag(ref)
    sys.exit(0 if ok else 1)


def cmd_reindex_all() -> None:
    """Re-index every pkg/* tag currently in the local git repo.

    # Use case: disaster recovery
    If the SQLite database is wiped, this reconstructs it entirely from the
    git object store.  Run this on the VPS after copying the bare repo.
    The git objects are the authoritative source; SQLite is derived.
    """
    out = _git("tag", "-l", "pkg/*")
    tags = [t.strip() for t in out.splitlines() if t.strip()]
    if not tags:
        print("[reindex] no pkg/* tags found")
        return

    db = _open_db()
    ok = sum(1 for t in tags if _index_tag(f"refs/tags/{t}", db=db))
    db.close()
    print(f"[reindex] {ok}/{len(tags)} tags indexed into {DB_PATH}")


def cmd_query(where: str) -> None:
    """Run a SQL SELECT query against the local index and print results.

    # Parameters
      where : SQL WHERE clause (e.g. "tier='CRYSTALLINE' AND domain='COMPUTE'")
              or a full SELECT statement
    """
    conn = _open_db()
    if where.strip().upper().startswith("SELECT"):
        sql = where
    else:
        sql = f"SELECT pkg, version, tier, domain, foam_score, sealed_utc FROM packages WHERE {where}"
    rows = conn.execute(sql).fetchall()
    conn.close()
    if not rows:
        print("(no results)")
        return
    for row in rows:
        print(json.dumps(_row_to_dict(row), indent=2))


def cmd_status() -> None:
    """Print a summary table of all indexed packages."""
    conn = _open_db()
    rows = conn.execute(
        "SELECT pkg, version, tier, domain, foam_score, taint_status, "
        "sealed_utc FROM packages ORDER BY tier, pkg"
    ).fetchall()
    conn.close()

    if not rows:
        print(f"(no packages indexed — DB: {DB_PATH})")
        return

    print(f"{'Package':<22} {'Ver':<8} {'Tier':<20} {'Domain':<10} "
          f"{'Foam':>6}  {'Taint':<12}  Sealed")
    print("-" * 100)
    for r in rows:
        pkg = r['pkg'] or ""
        ver = r['version'] or ""
        tier = r['tier'] or ""
        domain = r['domain'] or ""
        foam = r['foam_score'] if r['foam_score'] is not None else 0.0
        taint = r['taint_status'] or ""
        utc = r['sealed_utc'] or ""
        print(f"{pkg:<22} {ver:<8} {tier:<20} {domain:<10} "
              f"{foam:>6.2f}  {taint:<12}  {utc}")


def cmd_drop(pkg: str, version: str | None = None) -> None:
    """Remove a package record from the index (does not affect the git tag)."""
    conn = _open_db()
    if version:
        conn.execute("DELETE FROM packages WHERE pkg=? AND version=?",
                     (pkg, version))
        print(f"[drop] {pkg}/{version}")
    else:
        conn.execute("DELETE FROM packages WHERE pkg=?", (pkg,))
        print(f"[drop] all versions of {pkg}")
    conn.commit()
    conn.close()


def cmd_schema() -> None:
    """Print the CREATE TABLE statement (useful for schema documentation)."""
    print(CREATE_TABLE_SQL)


# ─────────────────────────────────────────────────────────────────────────────
# Semantic layer — metanarrative connection graph
#
# CONCEPT
# -------
# Every package has an nd_point (14-axis φ^-i positional vector) and,
# for RESEARCH-tier packages, a concept_vector (derived from idea_weights).
# Cosine similarity between vectors finds semantic neighbors.
#
# The metanarrative phase classifier maps similarity to action:
#
#   GROUNDED  (sim ≥ 0.85)  — you already know this connection.
#                              Surfaces it to confirm, not to surprise.
#   SEISMIC   (0.50–0.85)   — related but not immediately obvious.
#                              Worth investigating; may reveal refinements.
#   FLAME      (< 0.50)      — distant, non-obvious connection.
#                              The metanarrative found a bridge you missed.
#                              Highest value when confirmed; may be noise.
#
# The FLAME phase is the most important: these are the connections that
# prevent retreading existing thoughts and reveal where refinement is
# possible rather than reinvention.
#
# TRANSLATION / LOCAL ANALOG
# --------------------------
# When a concept has no direct equivalent in a target tier or domain,
# cmd_translate() finds the nearest package in that domain by nd_point
# cosine similarity.  This is the same logic as best_domain_for_band()
# in the USC codec: each concept finds its best carrier domain.
#
# This is grounded in the digital twin earth model: concepts were derived
# from the structures humanity built (minerals from architecture, not
# the reverse).  The metanarrative finds local analogs bottom-up, from
# what already exists in the semantic graph, not from literal intent.
#
# SIDECHANNEL TRANSLATION
# -----------------------
# When a "story" has no equivalent in the target domain, the system routes
# it through a sidechannel: the nearest analog in a different tier that
# shares semantic proximity.  The concept payload arrives intact even when
# the literal vocabulary does not map.  The analog IS the translation.
# ─────────────────────────────────────────────────────────────────────────────

# Metanarrative phase thresholds (mirrors soliton_factory.py phase gates)
_PHASE_GROUNDED = 0.85   # direct, known connection
_PHASE_SEISMIC  = 0.50   # related, worth investigating
# below SEISMIC threshold → FLAME phase (non-obvious, potentially breakthrough)

_PHI = (1 + 5 ** 0.5) / 2


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two equal-length float vectors.

    # Why cosine and not Euclidean?
    nd_point vectors encode direction in the 14-dimensional omnitoken space,
    not absolute position.  Two concepts at very different foam_scores may
    share the same semantic direction.  Cosine normalises out magnitude so
    only the angular relationship matters — same as how the codec normalises
    amplitude before comparing soliton phases.

    Returns a value in [-1, 1].  1.0 = identical direction, 0 = orthogonal.
    Negative values are possible but rare in this space (all axes ≥ 0).
    """
    if not a or not b or len(a) != len(b):
        return 0.0
    dot   = sum(x * y for x, y in zip(a, b))
    mag_a = sum(x ** 2 for x in a) ** 0.5
    mag_b = sum(x ** 2 for x in b) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _phase_classify(similarity: float) -> str:
    """Map a cosine similarity score to a metanarrative phase label.

    # Phase semantics in semantic space (mirrors soliton codec phases)
    GROUNDED  — you already know this; confirm rather than explore
    SEISMIC   — related but non-obvious; investigate for refinements
    FLAME      — distant; the bridge you missed; highest information value
    """
    if similarity >= _PHASE_GROUNDED:
        return "GROUNDED"
    if similarity >= _PHASE_SEISMIC:
        return "SEISMIC"
    return "FLAME"


def _concept_vector_from_weights(idea_weights: dict[str, float]) -> list[float]:
    """Derive a 14-axis concept_vector from an idea_weights dict.

    # Algorithm
    The 14 axes correspond to canonical concept clusters shared across the
    stack.  Each idea is mapped to its closest cluster by keyword matching,
    and the weight is accumulated.  The resulting vector is L2-normalised
    so cosine similarity is well-defined.

    # Concept cluster axes (matches omnitoken 14-axis surface bus)
    0   substrate / foam / universal computation
    1   compression / encoding / codec
    2   graph / dag / topology
    3   hardware / physical / isa
    4   time / planck / clock
    5   cryptography / hash / stark / zk
    6   database / sql / index / query
    7   semantic / language / translation / meaning
    8   physics / entropy / bekenstein / landauer
    9   security / isolation / sub-register / attestation
    10  os / kernel / vm / opcode
    11  research / discovery / idea / connection
    12  omnitoken / foam_score / nd_point / manifest
    13  identity / sovereignty / provenance / attestation
    """
    _CLUSTER_KEYWORDS: list[list[str]] = [
        ["substrate", "foam", "universal", "computation", "bits"],
        ["compression", "encoding", "codec", "soliton", "tse", "gamma"],
        ["graph", "dag", "node", "edge", "topology", "lut"],
        ["hardware", "physical", "isa", "risc", "kda", "hdl", "chip"],
        ["time", "planck", "clock", "tick", "temporal", "deterministic"],
        ["cryptography", "hash", "stark", "zk", "sha256", "proof"],
        ["database", "sql", "index", "query", "sqlite", "schema"],
        ["semantic", "language", "translation", "meaning", "concept", "analog"],
        ["physics", "entropy", "bekenstein", "landauer", "shannon", "thermodynamic"],
        ["security", "isolation", "register", "subregister", "attack", "boundary"],
        ["os", "kernel", "vm", "opcode", "tsm", "graphvm", "bytecode"],
        ["research", "discovery", "idea", "connection", "insight", "explore"],
        ["omnitoken", "foam_score", "nd_point", "manifest", "omni", "surface"],
        ["identity", "sovereignty", "provenance", "attestation", "prior", "legal"],
    ]

    vec = [0.0] * 14
    for idea, weight in idea_weights.items():
        tokens = set(idea.lower().replace('_', ' ').replace('-', ' ').split())  # EM-1 fix
        for axis, keywords in enumerate(_CLUSTER_KEYWORDS):
            if tokens & set(keywords):
                vec[axis] += weight

    # L2 normalise
    mag = sum(x ** 2 for x in vec) ** 0.5
    if mag > 0:
        vec = [x / mag for x in vec]
    return vec


def cmd_connect(pkg_name: str, version: str | None = None,
                min_phase: str = "SEISMIC") -> None:
    """Find semantic neighbors of a package via metanarrative phase classification.

    # What this does
    Computes cosine similarity between the target package's nd_point (or
    concept_vector for RESEARCH packages) and every other package in the
    index.  Results are phase-classified and filtered by min_phase.

    # Why this matters
    SEISMIC + FLAME connections are the ones you couldn't have found by
    grep or by memory.  They prevent retreading existing thoughts and
    reveal where refinement is possible rather than reinvention.

    # Parameters
      pkg_name  : package to connect from
      version   : specific version (default: latest)
      min_phase : minimum phase to show — "GROUNDED" shows all,
                  "SEISMIC" hides obvious matches, "FLAME" shows only
                  non-obvious connections (highest information value)
    """
    conn = _open_db()

    # Fetch target package
    if version:
        target = conn.execute(
            "SELECT * FROM packages WHERE pkg=? AND version=?",
            (pkg_name, version),
        ).fetchone()
    else:
        target = conn.execute(
            "SELECT * FROM packages WHERE pkg=? ORDER BY sealed_utc DESC LIMIT 1",
            (pkg_name,),
        ).fetchone()

    if target is None:
        print(f"[connect] package {pkg_name!r} not found")
        conn.close()
        return

    # Prefer concept_vector (richer) over nd_point (positional)
    target_vec = None
    if target["concept_vector"]:
        try:
            target_vec = json.loads(target["concept_vector"])
        except (json.JSONDecodeError, TypeError):
            pass
    if not target_vec and target["nd_point"]:
        try:
            target_vec = json.loads(target["nd_point"])
        except (json.JSONDecodeError, TypeError):
            pass
    if not target_vec:
        print(f"[connect] {pkg_name} has no vector — run ingest-session first")
        conn.close()
        return

    # Compare against all other packages
    others = conn.execute(
        "SELECT * FROM packages WHERE NOT (pkg=? AND version=?)",
        (target["pkg"], target["version"]),
    ).fetchall()
    conn.close()

    _PHASE_ORDER = {"GROUNDED": 0, "SEISMIC": 1, "FLAME": 2}
    min_idx = _PHASE_ORDER.get(min_phase, 1)

    results = []
    for row in others:
        vec = None
        if row["concept_vector"]:
            try:
                vec = json.loads(row["concept_vector"])
            except (json.JSONDecodeError, TypeError):
                pass
        if not vec and row["nd_point"]:
            try:
                vec = json.loads(row["nd_point"])
            except (json.JSONDecodeError, TypeError):
                pass
        if not vec:
            continue

        sim   = _cosine_similarity(target_vec, vec)
        phase = _phase_classify(sim)
        if _PHASE_ORDER[phase] >= min_idx:
            results.append((sim, phase, dict(row)))

    # Sort: FLAME first (highest information value), then SEISMIC, then GROUNDED
    # Within each phase, sort by similarity descending
    results.sort(key=lambda x: (-_PHASE_ORDER[x[1]], -x[0]))

    print(f"\n[connect] {pkg_name} → {len(results)} connection(s) "
          f"(min_phase={min_phase})\n")
    print(f"  {'Phase':<10} {'Sim':>5}  {'Package':<25} {'Tier':<14}  Insight")
    print("  " + "-" * 80)

    for sim, phase, row in results:
        # Summarise what the connection might mean
        target_tags = set(json.loads(target["tags"] or "[]"))
        other_tags  = set(json.loads(row["tags"] or "[]"))
        shared      = target_tags & other_tags
        novel       = other_tags - target_tags

        insight = ""
        if phase == "FLAME":
            insight = (
                f"non-obvious bridge — shared: {', '.join(list(shared)[:2]) or 'none'} "
                f"/ novel: {', '.join(list(novel)[:3]) or 'none'}"
            )
        elif phase == "SEISMIC":
            insight = f"refinement candidate — shared: {', '.join(list(shared)[:3]) or 'none'}"
        else:
            insight = f"known connection — {', '.join(list(shared)[:4]) or 'none'}"

        print(f"  {phase:<10} {sim:>5.3f}  {row['pkg']:<25} {row['tier'] or '':<14}  {insight}")

    if not results:
        print(f"  (no connections found at phase ≥ {min_phase})")


def cmd_translate(pkg_name: str, target_domain: str) -> None:
    """Find the local analog of a package in a target tier or domain.

    # The local analog principle
    When a concept has no direct equivalent in the target domain, the
    nearest semantic neighbor in that domain serves as the translation
    vehicle.  The concept payload arrives through the analog even when
    the literal vocabulary does not map — a sidechannel translation.

    # Basis: digital twin earth model
    Minerals and materials were refined from the structures humanity built,
    not defined first and then applied.  Concept translations here work the
    same way: the analog is derived bottom-up from what already exists in
    the semantic graph.

    # Parameters
      pkg_name      : source package to translate from
      target_domain : target tier (CRYSTALLINE, FOAM, …) or domain
                      (COMPUTE, TOKEN, STORE, …) to find the analog in
    """
    conn = _open_db()

    source = conn.execute(
        "SELECT * FROM packages WHERE pkg=? ORDER BY sealed_utc DESC LIMIT 1",
        (pkg_name,),
    ).fetchone()
    if source is None:
        print(f"[translate] package {pkg_name!r} not found")
        conn.close()
        return

    source_vec = None
    for field in ("concept_vector", "nd_point"):
        if source[field]:
            try:
                source_vec = json.loads(source[field])
                break
            except (json.JSONDecodeError, TypeError):
                pass

    if not source_vec:
        print(f"[translate] {pkg_name} has no vector")
        conn.close()
        return

    # Find nearest package in target tier or domain
    candidates = conn.execute(
        "SELECT * FROM packages WHERE tier=? OR domain=? AND pkg != ?",
        (target_domain, target_domain, pkg_name),
    ).fetchall()
    conn.close()

    if not candidates:
        print(f"[translate] no packages found in domain/tier {target_domain!r}")
        return

    best_sim  = -1.0
    best_row  = None
    for row in candidates:
        vec = None
        for field in ("concept_vector", "nd_point"):
            if row[field]:
                try:
                    vec = json.loads(row[field])
                    break
                except (json.JSONDecodeError, TypeError):
                    pass
        if not vec:
            continue
        sim = _cosine_similarity(source_vec, vec)
        if sim > best_sim:
            best_sim = sim
            best_row = dict(row)

    if best_row is None:
        print(f"[translate] no vectorised packages in {target_domain!r}")
        return

    phase = _phase_classify(best_sim)
    print(f"\n[translate] {pkg_name} → {target_domain}")
    print(f"  Local analog : {best_row['pkg']} / {best_row['version']}")
    print(f"  Phase        : {phase}  (sim={best_sim:.3f})")
    print(f"  Tier/Domain  : {best_row['tier']} / {best_row['domain']}")
    print(f"  Module       : {best_row['module']}")
    print(f"  Description  : {best_row['description']}")
    if phase == "FLAME":
        print(f"  Note: distant analog — concept will arrive via sidechannel.")
        print(f"        The analog IS the translation; literal mapping not available.")


def cmd_ingest_session(session_file: str) -> None:
    """Ingest a weighted LLM conversation session as a RESEARCH package.

    # Session file format (JSON)
    {
      "session_id":   "gemini-2026-03-25-substrate",
      "pkg":          "chat-substrate-design-20260325",
      "version":      "1.0.0",
      "description":  "Substrate stack design — GraphVM OS + git SQL DB",
      "tags":         ["substrate", "graphvm", "foam", "zk-stark", "planck"],
      "idea_weights": {
        "every hash has the schema embedded":       0.95,
        "sub-register per event prevents mixing":   0.91,
        "add/subtract only cpu with planck units":  0.88,
        "all data is foam, os reassembles bits":    0.94,
        "concept translates better than intent":    0.87,
        "local analog sidechannel translation":     0.90,
        "metanarrative finds connections you missed": 0.93
      },
      "extension_points": [
        "substrate_git_index.py: attest command for IP timeline",
        "metafoam_pkg.py: language miner integration",
        "soliton_factory.py: semantic domain routing via concept_vector"
      ]
    }

    # What happens
    1. Reads the JSON session file.
    2. Derives concept_vector from idea_weights using _concept_vector_from_weights().
    3. Inserts/replaces a row in packages with tier=RESEARCH, source=NOTE.
    4. Does NOT require a git tag — RESEARCH packages can be ingested directly.
    """
    p = Path(session_file)
    if not p.exists():
        print(f"[ingest] file not found: {session_file}")
        sys.exit(1)

    sess = json.loads(p.read_text())
    idea_weights = sess.get("idea_weights", {})
    concept_vec  = _concept_vector_from_weights(idea_weights)
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    conn = _open_db()
    concept_anchor = sess.get("concept_anchor")  # {"domain":…, "concept":…, "resolution":…}
    conn.execute(
        """INSERT OR REPLACE INTO packages
           (pkg, version, layer, domain, condition, stage, source,
            tier, module, archetype, tags, description,
            files, depends, foam_score, nd_point,
            sealed_utc, visibility, model_status, taint_status,
            session_id, idea_weights, extension_points, concept_vector,
            concept_anchor,
            indexed_utc)
           VALUES (?,?,?,?,?,?,?, ?,?,?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?, ?, ?)""",
        (
            sess.get("pkg", f"chat-{now_utc[:10]}"),
            sess.get("version", "1.0.0"),
            "RULE", "DATA", "EXPERIMENTAL", "ACTIVE", "NOTE",
            "RESEARCH",
            sess.get("module", "IDEA_CRYSTALLIZATION"),
            sess.get("archetype", "SEMANTIC_NODE"),
            json.dumps(sess.get("tags", [])),
            sess.get("description", ""),
            json.dumps([]),
            json.dumps([]),
            round(sum(idea_weights.values()) / max(len(idea_weights), 1) * _PHI, 6),
            json.dumps(concept_vec[:14]),
            now_utc,
            sess.get("visibility", "PRIVATE"),
            "CANONICAL", "CLEAN",
            sess.get("session_id", ""),
            json.dumps(idea_weights),
            json.dumps(sess.get("extension_points", [])),
            json.dumps(concept_vec),
            json.dumps(concept_anchor) if concept_anchor else None,
            now_utc,
        ),
    )
    conn.commit()
    conn.close()

    print(f"[ingest] {sess.get('pkg')} / {sess.get('version', '1.0.0')}")
    print(f"         ideas    : {len(idea_weights)}")
    print(f"         foam_score: {round(sum(idea_weights.values())/max(len(idea_weights),1)*_PHI, 4)}")
    print(f"         concept_vector axes with signal: "
          f"{sum(1 for x in concept_vec if x > 0.01)}/14")


# ─────────────────────────────────────────────────────────────────────────────
# Install helpers
# ─────────────────────────────────────────────────────────────────────────────

_SYSTEMD_UNIT = """\
[Unit]
Description=Substrate Git Index — HTTP query server
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 {script} serve --port {port} --db {db}
Restart=on-failure
RestartSec=5
Environment=SUBSTRATE_DB={db}
Environment=SUBSTRATE_PORT={port}
Environment=WITNESS_SOURCE={source}
Environment=WITNESS_SOURCES_CONFIG={config}

[Install]
WantedBy=multi-user.target
"""


def cmd_install(repo: str | None = None, source: str = WITNESS_SOURCE) -> None:
    """Install this script as the post-receive hook in a bare git repo.

    # What this does
    1. Writes a small provider-aware wrapper to <repo>/hooks/post-receive
    2. Makes it executable (chmod +x)
    3. Sets WITNESS_SOURCE, GIT_REPO_PATH, and SUBSTRATE_DB for the hook.

    # Parameters
      repo   : path to the bare git repo
      source : source block in 4-Infrastructure/witness/sources.json
    """
    source_repo = _repo_path_from_source(source)
    repo = repo or (str(source_repo) if source_repo else DEFAULT_HOOK_REPO)
    if not repo:
        print("[install] ERROR: no repo supplied and no local file:// source is configured.")
        print("          Use --repo <bare-git-repo> or set GIT_REPO_PATH.")
        sys.exit(1)

    hooks_dir = Path(repo) / "hooks"
    if not hooks_dir.exists():
        print(f"[install] ERROR: hooks dir not found: {hooks_dir}")
        sys.exit(1)

    dest = hooks_dir / "post-receive"
    script = Path(__file__).resolve()
    wrapper = f"""#!/usr/bin/env sh
export WITNESS_SOURCE={source!r}
export WITNESS_SOURCES_CONFIG={str(_witness_config_path())!r}
export GIT_REPO_PATH="${{GIT_DIR:-{str(Path(repo).resolve())}}}"
export SUBSTRATE_DB={str(DB_PATH)!r}
exec /usr/bin/python3 {str(script)!r} hook "$@"
"""
    dest.write_text(wrapper, encoding="utf-8")
    dest.chmod(0o755)
    print(f"[install] hook installed → {dest}")
    print(f"          Source: {source}")
    print(f"          DB will be written to: {DB_PATH}")
    print()
    print("  To change DB path, edit SUBSTRATE_DB in the hook or set env var.")
    print("  Start the query server:")
    print(f"    python3 {script} serve --port {DEFAULT_PORT} --db {DB_PATH}")


def cmd_install_service(port: int = DEFAULT_PORT, source: str = WITNESS_SOURCE) -> None:
    """Write a systemd unit file for the HTTP query server.

    Writes to /etc/systemd/system/substrate-git-index.service
    Then run:  systemctl enable --now substrate-git-index
    """
    unit = _SYSTEMD_UNIT.format(
        script=Path(__file__).resolve(),
        port=port,
        db=DB_PATH,
        source=source,
        config=_witness_config_path(),
    )
    dest = Path("/etc/systemd/system/substrate-git-index.service")
    try:
        dest.write_text(unit)
        print(f"[install-service] written → {dest}")
        print("  Enable:  systemctl enable --now substrate-git-index")
    except PermissionError:
        print(f"[install-service] writing to {dest} requires root.")
        print("  Unit file content:")
        print(unit)


# ─────────────────────────────────────────────────────────────────────────────
# CLI dispatch
# ─────────────────────────────────────────────────────────────────────────────

def _parse_kv_args(args: list[str]) -> tuple[dict[str, str], list[str]]:
    """Parse ``--key value`` pairs and preserve true positional arguments."""
    d: dict = {}
    positional: list[str] = []
    i = 0
    while i < len(args):
        if args[i].startswith("--"):
            key = args[i][2:]
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                d[key] = args[i + 1]
                i += 2
            else:
                d[key] = "true"
                i += 1
        else:
            positional.append(args[i])
            i += 1
    return d, positional


def main() -> None:
    """Parse argv and dispatch to the appropriate command function."""
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return

    cmd = args[0]
    opts, positional = _parse_kv_args(args[1:])

    # Apply --db and --port overrides globally
    global DB_PATH, DEFAULT_PORT
    if "db" in opts:
        DB_PATH = Path(opts["db"])
    if "port" in opts:
        DEFAULT_PORT = int(opts["port"])

    if cmd == "hook":
        cmd_hook()

    elif cmd == "serve":
        cmd_serve(DEFAULT_PORT)

    elif cmd == "index":
        if not positional:
            print("Usage: substrate_git_index.py index <tag_name>")
            sys.exit(1)
        cmd_index(positional[0])

    elif cmd == "reindex":
        cmd_reindex_all()

    elif cmd == "query":
        if not positional:
            print("Usage: substrate_git_index.py query \"<WHERE clause>\"")
            sys.exit(1)
        cmd_query(" ".join(positional))

    elif cmd == "status":
        cmd_status()

    elif cmd == "drop":
        if not positional:
            print("Usage: substrate_git_index.py drop <pkg> [version]")
            sys.exit(1)
        cmd_drop(positional[0], positional[1] if len(positional) > 1 else None)

    elif cmd == "schema":
        cmd_schema()

    elif cmd == "connect":
        if not positional:
            print("Usage: substrate_git_index.py connect <pkg> [--phase SEISMIC|FLAME|GROUNDED]")
            sys.exit(1)
        phase = opts.get("phase", "SEISMIC")
        cmd_connect(positional[0], version=opts.get("version"), min_phase=phase)

    elif cmd == "translate":
        if len(positional) < 2:
            print("Usage: substrate_git_index.py translate <pkg> <target_domain>")
            sys.exit(1)
        cmd_translate(positional[0], positional[1])

    elif cmd == "ingest-session":
        if not positional:
            print("Usage: substrate_git_index.py ingest-session <session.json>")
            sys.exit(1)
        cmd_ingest_session(positional[0])

    elif cmd == "install":
        repo = opts.get("repo") or (positional[0] if positional else None)
        cmd_install(repo, source=opts.get("source", WITNESS_SOURCE))

    elif cmd == "install-service":
        cmd_install_service(
            int(opts.get("port", str(DEFAULT_PORT))),
            source=opts.get("source", WITNESS_SOURCE),
        )

    elif cmd == "align":
        """Retroactively professionalize all nodes in the database."""
        conn = _open_db()
        rows = conn.execute("SELECT rowid, pkg, description, tags, idea_weights FROM packages").fetchall()
        updates = 0
        for row in rows:
            r_id, pkg, desc, tags_raw, weights_raw = row
            try:
                tags = json.loads(tags_raw) if tags_raw else []
                weights = json.loads(weights_raw) if weights_raw else {}
            except (json.JSONDecodeError, TypeError):
                tags, weights = [], {}

            new_desc, new_tags, new_weights = _professional_align(pkg, desc, tags, weights)
            
            if new_desc != desc or new_tags != tags or new_weights != weights:
                new_vec = _concept_vector_from_weights(new_weights)
                conn.execute("""
                    UPDATE packages SET 
                        description = ?, 
                        tags = ?, 
                        idea_weights = ?,
                        concept_vector = ?
                    WHERE rowid = ?
                """, (new_desc, json.dumps(new_tags), json.dumps(new_weights), json.dumps(new_vec), r_id))
                updates += 1
        conn.commit()
        conn.close()
        print(f"[align] professionalized {updates}/{len(rows)} nodes in {DB_PATH}")

    else:
        print(
            f"Unknown command: {cmd!r}\n"
            "Commands: hook | serve | index | reindex | query | status | "
            "drop | schema | install | install-service"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
