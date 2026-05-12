# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
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
# PTOS: LAYER=CORE / DOMAIN=STORE / CONDITION=EXPERIMENTAL / STAGE=ACTIVE / SOURCE=CODE
"""
MetaFoam Package Manager — git tag descriptor sidecar.
=======================================================

CONCEPT
-------
This tool treats the git repository as a substrate node registry — the same
semantic as the project's graph-SQL database, but using git's native object
model instead of SQL rows.

  Graph-SQL analogy:
    Table  row    ↔  git annotated tag
    Column values ↔  PTOS manifest fields in tag annotation
    Primary key   ↔  tag name  pkg/<name>/v<version>
    BLOB column   ↔  meta_capsule (zlib+base64 payload)
    Foreign key   ↔  depends[] list

A "pull" fetches only the tag's commit/tree/blobs — not the full repo history.
A "receive" unpacks exactly the files in that package to a target directory.
The result is a typed, versioned, self-describing deployment unit that travels
over git without carrying the whole repository.

HOW IT WORKS (git plumbing layer)
----------------------------------
Standard `git push` moves every commit in the branch history.  This tool uses
git's lower-level object model instead:

  1.  hash-object   — write each source file as a git blob object
  2.  update-index  — populate a *temporary* index (GIT_INDEX_FILE=/tmp/…)
                      so the real .git/index is never touched
  3.  write-tree    — turn the temp index into a tree object
  4.  commit-tree   — wrap the tree in a root/orphan commit (no parents)
  5.  tag -a        — annotate that commit with the full PTOS manifest JSON
  6.  push          — send only  refs/tags/pkg/<name>/v<ver>  to the remote
                      git transmits only the objects reachable from that tag

On the receiving node:
  git fetch  refs/tags/pkg/<name>/v<ver>
  git archive <tag> | tar -xC <target>

Nothing else crosses the wire.

TAG ANNOTATION SCHEMA  (PTOS_TAG_SCHEMA v1.0 — embedded for self-description)
-------------------------------------------------------------------------------
Every tag annotation is a valid JSON document conforming to PTOS_TAG_SCHEMA.md.
Fields below are the complete schema; all are written by cmd_build().

  PTOS Operational Axis:
    "layer"              CORE | CARRY | RULE | STORE | EXTERNAL
    "domain"             COMPUTE | TOKEN | RULE | STORE | POWER | COMMS |
                         MATERIAL | DATA | CLOCK | TEST
    "condition"          STABLE | EXPERIMENTAL | EXTREME | DRAFT |
                         ARCHIVED | STERILE
    "stage"              ACTIVE | INTAKE | REVIEW | HOLD | ARCHIVED
    "source"             CODE | SPEC | NOTE | DATA | PASTE | IMPORT |
                         MANIFEST | TEMPLATE

  Tier / Topology Axis:
    "tier"               SINGULARITY | PLASMA | CRYSTALLINE | FOAM |
                         GOVERNANCE | RESEARCH

  Semantic / Archetype Axis:
    "module"             <UPPERCASE_MODULE_ID>
    "archetype"          <OPTIONAL_ARCHETYPE>
    "tags"               ["<tag1>", ...]
    "manifold_id"        <optional substrate-addressable id>

  Package Identification:
    "schema"             "metafoam-pkg/v1"
    "pkg"                <name>
    "version"            <semver>
    "files"              ["<repo-relative path>", ...]
    "depends"            ["<pkg-name/version>", ...]
    "nd_point"           [<f64> × 14]   omnitoken 14-axis position (φ^-i)
    "foam_score"         <f64>          φ-ratio quality metric

  Provenance Axis:
    "sealed_utc"         <ISO8601Z>
    "sha256"             <hex>    SHA-256 of sorted file contents
    "verification_basis" DECLARED | OBSERVED | CROSS_CHECKED | PHYSICS_BOUND

  Privacy / Admissibility:
    "visibility"         PRIVATE | INTERNAL | SELECTIVE | PUBLIC
    "model_status"       CANONICAL | REFERENCE_ONLY | QUARANTINED | REJECTED
    "taint_status"       CLEAN | SENSITIVE | CONTAMINATED | EXCLUDED

  meta_capsule (compressed payload):
    "meta_capsule"       base64url(zlib(json(manifest_without_capsule_fields)))
    "meta_capsule_hash"  sha256(meta_capsule_string)
    Decode:  json.loads(zlib.decompress(base64.urlsafe_b64decode(c + padding)))

PACKAGE REGISTRY
----------------
The PACKAGES dict at the top of this file defines all deployable units.
Each entry gives the PTOS manifest fields + the list of files to include.
cmd_build() fills in the computed fields (nd_point, foam_score, sha256,
sealed_utc, meta_capsule) automatically.

To add a new package: copy an existing entry, change the name and files list,
adjust the PTOS fields, re-run `deploy <name>`.

AUTO-DEPLOY HOOK
----------------
`hook install` writes .git/hooks/post-commit to call this script after every
commit.  The hook diffs HEAD against the package file lists and redeploys any
package whose files were touched.  This is the "sidecar" behaviour: normal git
workflow continues unchanged; the hook fires in the background.

Usage:
  python metafoam_pkg.py list                    list defined packages
  python metafoam_pkg.py build  <pkg>            build orphan commit + tag
  python metafoam_pkg.py push   <pkg> [remote]   push tag to remote
  python metafoam_pkg.py deploy <pkg> [remote]   build + push in one step
  python metafoam_pkg.py deploy-all  [remote]    deploy every package
  python metafoam_pkg.py status [remote]         show pkg/* tags on remote
  python metafoam_pkg.py receive <pkg> [dir]     (VPS) fetch + unpack
  python metafoam_pkg.py decode <pkg>            pretty-print meta_capsule
  python metafoam_pkg.py hook install            install post-commit hook
  python metafoam_pkg.py hook remove             remove hook
  python metafoam_pkg.py hook run                run hook logic (called by git)
"""

import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zlib
from datetime import datetime, timezone
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
while not (REPO_ROOT / ".git").exists() and REPO_ROOT != REPO_ROOT.parent:
    REPO_ROOT = REPO_ROOT.parent
DEFAULT_REMOTE = os.environ.get("PTOS_REMOTE", "github")
_PHI = (1 + 5 ** 0.5) / 2  # golden ratio — used for nd_point and foam_score
SIDECAR_EXTENSIONS = frozenset({
    ".json",
    ".jsonl",
    ".md",
    ".txt",
    ".html",
    ".htm",
    ".csv",
})


# ─────────────────────────────────────────────────────────────────────────────
# Package Registry
#
# Each entry fully specifies a deployable unit:
#   • PTOS operational + tier + semantic tags (written verbatim to tag annotation)
#   • files: repo-relative paths included in the package tree
#   • depends: other packages this one requires (informational — not auto-fetched)
#
# Computed at build time (do not set here):
#   nd_point, foam_score, sha256, sealed_utc, meta_capsule, meta_capsule_hash
# ─────────────────────────────────────────────────────────────────────────────

PACKAGES: dict = {

    # ── USC Audio / Topological Soliton Codec ────────────────────────────────
    #
    # Five-physics model: gravity (Bekenstein snag) + Doppler + angular momentum
    # (Kerr) + conversion efficiency η + friction (Shakura-Sunyaev).
    # Gamma pattern principle: transmit index into shared physical basis, not
    # the value — pos_x/bandwidth/rate reconstructed at decode from band_idx.
    # Layer 1: 6-byte SolitonBox (4-byte label + f16 amplitude).
    # Layer 2: Jupiter φ-locked 14-mode residual (round-trip < 0.5% error).
    # Relativistic subregister: FLAME frames split 2×/4×/8× until resolved.
    # 23-domain basis registry (audio → radio → xray → exotic: monopole,
    #   kk_tower, regge, tachyon, octonion, axion, ads_cft, padic_2 …).
    # Streaming results: PURE TONE 45×, CHORD 40×, WHITE NOISE 42× (16 frames).
    "usc-audio": {
        "version":            "1.0.0",
        "layer":              "CORE",
        "domain":             "COMPUTE",
        "condition":          "EXPERIMENTAL",
        "stage":              "ACTIVE",
        "source":             "CODE",
        "tier":               "CRYSTALLINE",
        "module":             "USC_AUDIO_CODEC",
        "archetype":          "TOPOLOGICAL_SOLITON_ENCODER",
        "tags":               ["TSE", "soliton", "compression", "audio",
                               "gamma_pattern", "bekenstein", "jupiter"],
        "visibility":         "PUBLIC",
        "model_status":       "CANONICAL",
        "taint_status":       "CLEAN",
        "verification_basis": "PHYSICS_BOUND",
        "description": (
            "USC Topological Soliton Audio Codec — five-physics model, "
            "gamma pattern principle, relativistic subregister, "
            "omnitoken manifest, 23-domain basis registry"
        ),
        "files": [
            "5-Applications/scripts/soliton_factory.py",
            "5-Applications/scripts/audio_compression_sim.py",
            "5-Applications/scripts/usc_spectral_core.py",
            "5-Applications/scripts/video_compression_sim.py",
            "5-Applications/scripts/solidified_poc.py",
            "6-Documentation/docs/USC_AUDIO_CODEC_CHANGELOG.md",
            "USC_Topological_Soliton_Encoding_Spec.md",
        ],
        "depends": [],
    },

    # ── MetaFoam Rust Engine ─────────────────────────────────────────────────
    #
    # All TSM physics-gap opcodes closed with Landauer energy:
    #   WHITEHOLE_DECOMPRESS (0x63), FOAM_MAP (0x0E),
    #   VDP_COMPRESS_NSPACE (0x19), QUANTUM_MELT_NSPACE (0x1A).
    # FOAM_COLLAPSE / FOAM_FUSE / FOAM_MERGE → pdqsort neighbor lists.
    "metafoam-engine": {
        "version":            "1.0.0",
        "layer":              "CORE",
        "domain":             "COMPUTE",
        "condition":          "EXPERIMENTAL",
        "stage":              "ACTIVE",
        "source":             "CODE",
        "tier":               "CRYSTALLINE",
        "module":             "METAFOAM_ENGINE",
        "archetype":          "TSM_OPCODE_EXECUTOR",
        "tags":               ["TSM", "foam", "rust", "landauer", "opcodes", "pdqsort"],
        "visibility":         "PUBLIC",
        "model_status":       "CANONICAL",
        "taint_status":       "CLEAN",
        "verification_basis": "PHYSICS_BOUND",
        "description": (
            "MetaFoam Rust TSM engine — all Landauer opcodes closed, "
            "pdqsort neighbor lists, foam collapse/fuse/merge"
        ),
        "files": [
            "CATEGORY/TSM/tsm_foam_package/rust/metafoam_engine.rs",
            "CATEGORY/TSM/tsm_foam_package/rust/lib.rs",
            "CATEGORY/TSM/tsm_foam_package/rust/metafoam_opcodes_reference.json",
            "CATEGORY/TSM/tsm_foam_package/rust/metafoam_opcodes_reference.md",
            "CATEGORY/TSM/tsm_foam_package/rust/whitehole_opcode_reference_full.json",
        ],
        "depends": [],
    },

    # ── Omnitoken v3 Surface Bus ─────────────────────────────────────────────
    #
    # GraphVM preamble for the USC codec stream.
    # archive_compression domain activated.  14-axis nd_point = Jupiter mode
    # vector.  foam_score = φ-ratio = channel quality.
    # Register state machine: potential → candidate → collapsed → committed.
    "omnitoken": {
        "version":            "3.0.0",
        "layer":              "CARRY",
        "domain":             "TOKEN",
        "condition":          "STABLE",
        "stage":              "ACTIVE",
        "source":             "MANIFEST",
        "tier":               "FOAM",
        "module":             "OMNITOKEN_GRAPHVM",
        "archetype":          "PANSUBSTRATE_LOGIC_SURFACE",
        "tags":               ["omnitoken", "graphvm", "foam", "tunnel", "nd_point"],
        "visibility":         "INTERNAL",
        "model_status":       "CANONICAL",
        "taint_status":       "CLEAN",
        "verification_basis": "CROSS_CHECKED",
        "description": (
            "Omnitoken v3 GraphVM surface bus — archive_compression domain "
            "activated, 14-axis nd_point, foam_score, register state machine, "
            "I2P sovereign AI chat interface, sovereign_code clean-room CLI"
        ),
        "files": [
            "5-Applications/out/omnitoken_bridge/omnitoken_v3.json",
            "5-Applications/out/omnitoken_bridge/omnitoken_main.json",
            "i2p_openweb.py",
            "sovereign_code/__init__.py",
            "sovereign_code/__main__.py",
            "sovereign_code/core.py",
            "sovereign_code/tools.py",
            "sovereign_code/cli.py",
        ],
        "depends": [],
    },

    # ── Substrate ISA Spec ───────────────────────────────────────────────────
    #
    # Canonical tag schema and sovereign stack architecture.
    # This package is the schema authority — other packages reference it.
    "substrate-isa": {
        "version":            "1.0.0",
        "layer":              "RULE",
        "domain":             "COMPUTE",
        "condition":          "EXPERIMENTAL",
        "stage":              "ACTIVE",
        "source":             "SPEC",
        "tier":               "GOVERNANCE",
        "module":             "SUBSTRATE_ISA",
        "archetype":          "SOVEREIGN_DISCLOSURE",
        "tags":               ["ISA", "substrate", "spec", "ptos", "schema"],
        "visibility":         "PUBLIC",
        "model_status":       "CANONICAL",
        "taint_status":       "CLEAN",
        "verification_basis": "OBSERVED",
        "description":        "Substrate ISA specification and PTOS tag schema",
        "files": [
            "brain/substrate_isa_spec.md",
            "6-Documentation/docs/PTOS_TAG_SCHEMA.md",
            "6-Documentation/docs/SOVEREIGN_STACK_ARCHITECTURE.md",
            "6-Documentation/docs/TSM-AAC_v1_spec.md",
        ],
        "depends": [],
    },

    # ── Semantic Ingestion / Math Tooling ──────────────────────────────────
    #
    # PTOS-aware ingestion, LaTeX normalization, repair/reindex passes, and
    # math-check backend routing. This package exists so git-sidecar deploys
    # follow the same revisions that updated the local ingestion/search layer.
    "semantic-ingestion": {
        "version":            "1.0.0",
        "layer":              "STORE",
        "domain":             "COMPUTE",
        "condition":          "EXPERIMENTAL",
        "stage":              "ACTIVE",
        "source":             "CODE",
        "tier":               "GOVERNANCE",
        "module":             "SEMANTIC_INGESTION_PIPELINE",
        "archetype":          "PTOS_SYMBOLIC_ROUTER",
        "tags":               ["ingest", "ptos", "latex", "math-check",
                               "indexing", "repair", "sessions"],
        "visibility":         "INTERNAL",
        "model_status":       "CANONICAL",
        "taint_status":       "CLEAN",
        "verification_basis": "OBSERVED",
        "description": (
            "Semantic ingestion and math-routing toolchain — PTOS schema, "
            "LaTeX normalization, repair passes, backend registry, and "
            "session-aware index tooling"
        ),
        "files": [
            "6-Documentation/docs/PTOS_TAG_SCHEMA.md",
            "5-Applications/scripts/ingest_attachments.py",
            "5-Applications/scripts/ingest_archive.py",
            "5-Applications/scripts/ingest_large_file.py",
            "5-Applications/scripts/iso_pipeline.py",
            "5-Applications/scripts/iso_symbol_table.py",
            "5-Applications/scripts/math_check_packages.py",
            "5-Applications/scripts/repair_index.py",
            "5-Applications/scripts/stage0_classifier.py",
            "5-Applications/tools-scripts/substrate/substrate_git_index.py",
            "4-Infrastructure/witness/sources.json",
            "5-Applications/tests/test_iso_symbol_table.py",
            "5-Applications/tests/test_math_check_packages.py",
        ],
        "depends": ["substrate-isa/1.0.0"],
    },

    # ── Geometry / WaveProbe Research Sessions ──────────────────────────────
    #
    # Structured session captures for the 120-cell, WaveProbe, spoiler-game,
    # and math-ingestion throughline. Same-stem expansion picks up the paired
    # markdown notes automatically when the JSON session manifests are listed.
    "geometry-search-sessions": {
        "version":            "1.0.0",
        "layer":              "RULE",
        "domain":             "COMPUTE",
        "condition":          "EXPERIMENTAL",
        "stage":              "ACTIVE",
        "source":             "NOTE",
        "tier":               "RESEARCH",
        "module":             "GEOMETRIC_SEARCH_SESSION_CLUSTER",
        "archetype":          "CONCEPT_CONTINUATION",
        "tags":               ["sessions", "120-cell", "waveprobe",
                               "spoiler-game", "math-ingestion",
                               "geometric-search"],
        "visibility":         "PRIVATE",
        "model_status":       "CANONICAL",
        "taint_status":       "CLEAN",
        "verification_basis": "DECLARED",
        "description": (
            "Research-session cluster capturing the 120-cell geometric "
            "encoding bridge and its continuation into adversarial search, "
            "WaveProbe/QUBO, and symbol-terrain math ingestion"
        ),
        "files": [
            "sessions/chat-120cell-hachimoji-manifold-20260402.json",
            "sessions/chat-waveprobe-spoiler-math-ingestion-20260402.json",
        ],
        "depends": ["semantic-ingestion/1.0.0"],
    },

    # ── GeomTREE / KDA-16 Structural Attestation ────────────────────────────
    #
    # Baseline hardware-attestation docs for the jack / GeomTREE family plus
    # the verifier-side speculative MMR extension path. This keeps the
    # structural-attestation stack visible to the git sidecar instead of
    # leaving it only in loose docs and patent notes.
    "geomtree-jack": {
        "version":            "1.0.0",
        "layer":              "RULE",
        "domain":             "MATERIAL",
        "condition":          "EXPERIMENTAL",
        "stage":              "ACTIVE",
        "source":             "SPEC",
        "tier":               "SINGULARITY",
        "module":             "GEOMTREE_KDA16",
        "archetype":          "SELF_ATTESTING_STRUCTURAL_ELEMENT",
        "tags":               ["geomtree", "kda-16", "jack", "attestation",
                               "physical-merkle", "me-shunt", "mmr"],
        "visibility":         "INTERNAL",
        "model_status":       "CANONICAL",
        "taint_status":       "CLEAN",
        "verification_basis": "DECLARED",
        "description": (
            "GeomTREE / KDA-16 structural attestation docs — current "
            "incremental-Merkle baseline plus speculative MMR history path"
        ),
        "files": [
            "6-Documentation/docs/GEOMTREE_TECHNICAL_FACT_SHEET.md",
            "6-Documentation/docs/GEOMTREE_INTERVIEW_TALKING_POINTS.md",
            "GEOMETRIC_SECURITY_MAPPING.md",
            "RESEARCH_PORTFOLIO.md",
            "hutter/GEOMTREE_PITCH.md",
            "PATENT_APPLICATION/16_Semi_Jack_Self_Authenticating_Structural_Element.md",
            "6-Documentation/docs/roadmap/GEOMTREE_MMR_ATTESTATION_PATH.md",
        ],
        "depends": ["substrate-isa/1.0.0"],
    },

    # ── Deduplication + Deep Storage ─────────────────────────────────────────
    #
    # American Flag Sort (MSD radix, O(64n)) on 64-char hex hashes.
    # Batched LUT write: single JSON write replacing O(n) subprocess calls.
    "deep-storage": {
        "version":            "1.0.0",
        "layer":              "STORE",
        "domain":             "STORE",
        "condition":          "EXPERIMENTAL",
        "stage":              "ACTIVE",
        "source":             "CODE",
        "tier":               "FOAM",
        "module":             "DEEP_STORAGE_DEDUP",
        "archetype":          "TUNNEL_INGRESS",
        "tags":               ["dedup", "radix_sort", "american_flag", "lut"],
        "visibility":         "INTERNAL",
        "model_status":       "CANONICAL",
        "taint_status":       "CLEAN",
        "verification_basis": "OBSERVED",
        "description": (
            "Deduplication tools — American Flag Sort (O(64n)) on hex "
            "hashes, batched LUT write, deep-storage management"
        ),
        "files": [
            "dedupe_home_against_local.py",
            "dedupe_gdrive_against_local.py",
            "dedupe_to_devnull.py",
            "deep_storage_lut.py",
        ],
        "depends": [],
    },

    # ── Bind Bridge / Functional Collapse ────────────────────────────────────
    #
    # The Cambrian collapse: a single bind primitive replaces all previous
    # model families (informational, geometric, thermodynamic, physical,
    # control).  Lean 4 proves conservation laws; Q16.16 fixed-point enables
    # hardware-native execution; Python acts as a minimal history loader.
    # 105-kind bounded Standard Model particle address space.
    "bind-bridge": {
        "version":            "1.0.0",
        "layer":              "CORE",
        "domain":             "COMPUTE",
        "condition":          "EXPERIMENTAL",
        "stage":              "ACTIVE",
        "source":             "CODE",
        "tier":               "CRYSTALLINE",
        "module":             "BIND_BRIDGE",
        "archetype":          "UNIVERSAL_BIND_PRIMITIVE",
        "tags":               ["bind", "lean4", "q16_16", "physics",
                               "conservation", "cambrian", "collapse"],
        "visibility":         "PUBLIC",
        "model_status":       "CANONICAL",
        "taint_status":       "CLEAN",
        "verification_basis": "PHYSICS_BOUND",
        "description": (
            "Functional collapse to a single bind primitive — Lean 4 "
            "bindserver with Q16.16 fixed-point arithmetic, 105-kind "
            "particle domain, and minimal Python loader"
        ),
        "files": [
            "0-Core-Formalism/lean/Semantics/BindServer.lean",
            "0-Core-Formalism/lean/Semantics/lakefile.toml",
            "0-Core-Formalism/lean/Semantics/Semantics/Bind.lean",
            "0-Core-Formalism/lean/Semantics/Semantics/FixedPoint.lean",
            "0-Core-Formalism/lean/Semantics/Semantics/Physics.lean",
            "0-Core-Formalism/lean/Semantics/Semantics/Physics/BindPhysics.lean",
            "0-Core-Formalism/lean/Semantics/Semantics/Physics/Boundary.lean",
            "0-Core-Formalism/lean/Semantics/Semantics/Physics/Conservation.lean",
            "0-Core-Formalism/lean/Semantics/Semantics/Physics/Examples.lean",
            "0-Core-Formalism/lean/Semantics/Semantics/Physics/Interaction.lean",
            "0-Core-Formalism/lean/Semantics/Semantics/Physics/ParticleDomain.lean",
            "0-Core-Formalism/lean/Semantics/Semantics/Physics/Projection.lean",
            "0-Core-Formalism/lean/Semantics/Semantics/Physics/Tests.lean",
            "4-Infrastructure/infra/access_control/bind_engine.py",
            "6-Documentation/docs/VISION_NORTH_STAR.md",
            "6-Documentation/docs/geometry/FUNCTIONAL_COLLAPSE_PARADIGM.md",
            "6-Documentation/docs/geometry/BIND_MIGRATION_GUIDE.md",
            "6-Documentation/docs/semantics/INCOMPATIBLE_MANIFOLDS_AND_LAWFUL_LOSS.md",
            "6-Documentation/docs/semantics/BIND_BRIDGE_EQUATIONS.md",
            "6-Documentation/docs/physics/PHYSICAL_SEMANTICS_PARADIGM.md",
        ],
        "depends": ["substrate-isa/1.0.0"],
    },

}


# ─────────────────────────────────────────────────────────────────────────────
# Git plumbing helpers  (no working-tree modification)
# ─────────────────────────────────────────────────────────────────────────────

def _git(*args: str, stdin: str | None = None, check: bool = True) -> str:
    """Run a git plumbing subcommand in REPO_ROOT and return stdout stripped.

    # Why this wrapper exists
    All git calls are funnelled here so that:
      • cwd is always REPO_ROOT (not the CWD of whoever calls the script)
      • subprocess.run is always called with check=False (we raise our own
        RuntimeError with cleaned stderr instead of CalledProcessError)
      • stdin piping is handled in one place (needed by git mktree / commit-tree)

    # Parameters
      *args   : git subcommand + arguments, e.g. ("tag", "-a", name, "-m", msg)
      stdin   : optional string piped to git's stdin (None = no pipe)
      check   : if True, raise RuntimeError on non-zero exit code
                if False, return empty string on failure (caller decides)

    # Returns
      Stripped stdout string.  Empty string on failure when check=False.
    """
    cmd = ["git"] + list(args)
    result = subprocess.run(
        cmd, cwd=REPO_ROOT, capture_output=True, text=True,
        input=stdin, check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed:\n{result.stderr.strip()}"
        )
    return result.stdout.strip()


def _same_stem_sidecars(rel_path: str) -> list[str]:
    """Return repo-relative same-stem sidecars for a tracked package file.

    This mirrors the ingest-side attachment idea so package sidecars keep
    session json/md pairs and similar companion files together.
    """
    source = REPO_ROOT / rel_path
    if not source.exists() or not source.is_file():
        return []

    out: list[str] = []
    parent = source.parent
    for sibling in sorted(parent.iterdir()):
        if sibling == source or not sibling.is_file():
            continue
        if sibling.suffix.lower() not in SIDECAR_EXTENSIONS:
            continue
        if sibling.stem == source.stem:
            out.append(str(sibling.relative_to(REPO_ROOT)))
    return out


def _expand_package_files(files: list[str]) -> list[str]:
    """Expand a package file list to include same-stem sidecars once.

    The git sidecar still uses an explicit registry, but this keeps paired
    artifacts such as `session.json` + `session.md` or similar descriptor
    companions in sync without duplicating every sibling in PACKAGES.
    """
    expanded: list[str] = []
    seen: set[str] = set()
    for rel in files:
        norm = str(Path(rel))
        if norm not in seen:
            expanded.append(norm)
            seen.add(norm)
        for sidecar in _same_stem_sidecars(norm):
            if sidecar in seen:
                continue
            expanded.append(sidecar)
            seen.add(sidecar)
    return expanded


def _hash_file_contents(files: list[str]) -> str:
    """Return SHA-256 of sorted, concatenated file bytes.

    # Provenance anchor
    The hash travels in the tag annotation as the "sha256" provenance field
    (PTOS_TAG_SCHEMA provenance axis).  Sorting the file list before hashing
    makes the digest independent of insertion order — the same set of files
    always produces the same hash regardless of how the caller built the list.

    # Parameters
      files : list of repo-relative paths (missing files are skipped silently)

    # Returns
      64-character lowercase hex SHA-256 digest.
    """
    h = hashlib.sha256()
    for rel in sorted(_expand_package_files(files)):
        p = REPO_ROOT / rel
        if p.exists():
            h.update(p.read_bytes())
    return h.hexdigest()


def _build_tree(files: list[str]) -> tuple[str, list[str]]:
    """Build a git tree object from repo-relative paths without touching the
    working tree or .git/index.

    # Why not git mktree?
    git mktree only handles flat (single-level) trees.  Paths like
    "5-Applications/scripts/soliton_factory.py" contain a slash and cause a fatal error.
    The temporary-index approach handles arbitrary nesting.

    # Temporary index pattern (the key trick)
    git uses GIT_INDEX_FILE to redirect all index operations to a custom path.
    We:
      1. Generate a unique temp path via tempfile.NamedTemporaryFile.
      2. Immediately delete it — git treats a 0-byte file as a corrupt index
         and fails with "index file smaller than expected".  The path must not
         exist so git can create a fresh index on first update-index call.
      3. Set GIT_INDEX_FILE=<path> in the subprocess environment.
      4. Run git update-index --add --cacheinfo <mode>,<blob>,<path>  for
         each file.  This writes blobs into .git/objects and registers the
         path in the temp index.
      5. Run git write-tree to serialise the temp index as a tree object.
      6. Delete the temp index in the finally block.

    # File modes
      100644  regular file (non-executable)
      100755  executable file (checked via os.access)

    # Parameters
      files : list of repo-relative paths to include

    # Returns
      (tree_hash, included_files) where included_files omits any paths that
      did not exist on disk at build time.
    """
    included: list[str] = []
    blobs: list[tuple[str, str, str]] = []

    for rel in files:
        abs_path = REPO_ROOT / rel
        if not abs_path.exists():
            print(f"  [skip] {rel} — not found")
            continue
        blob = _git("hash-object", "-w", str(abs_path))
        mode = "100755" if os.access(abs_path, os.X_OK) else "100644"
        blobs.append((mode, blob, rel))
        included.append(rel)

    if not blobs:
        raise RuntimeError("No files found for package tree")

    # Obtain a unique temp path then delete it so git creates a fresh index.
    with tempfile.NamedTemporaryFile(prefix="metafoam_index_", delete=True) as tf:
        tmp_index = tf.name
    # tf.name is now deleted; git writes a valid index on first update-index.

    env = os.environ.copy()
    env["GIT_INDEX_FILE"] = tmp_index

    try:
        for mode, blob, rel in blobs:
            subprocess.run(
                ["git", "update-index", "--add", "--cacheinfo",
                 f"{mode},{blob},{rel}"],
                cwd=REPO_ROOT, env=env, check=True,
                capture_output=True,
            )
        result = subprocess.run(
            ["git", "write-tree"],
            cwd=REPO_ROOT, env=env, check=True,
            capture_output=True, text=True,
        )
        tree_hash = result.stdout.strip()
    finally:
        try:
            os.unlink(tmp_index)
        except OSError:
            pass

    return tree_hash, included


def _make_meta_capsule(payload: dict) -> tuple[str, str]:
    """Compress payload into a meta_capsule per PTOS_TAG_SCHEMA.md.

    # Encoding pipeline  (must be reproducible across Python versions)
      1. json.dumps(payload, sort_keys=True, separators=(",", ":"))
         → deterministic JSON bytes (no spaces, keys sorted)
      2. zlib.compress(raw, level=9)
         → deflate stream, maximum compression
      3. base64.urlsafe_b64encode(compressed).rstrip("=")
         → URL-safe base64 without padding (safe for git tag annotations
           which may be passed through shell variables)
      4. sha256(capsule_string)
         → integrity anchor stored alongside the capsule

    # Decoding (any language)
      padding = "=" * (-len(capsule) % 4)
      json.loads(zlib.decompress(base64.urlsafe_b64decode(capsule + padding)))

    # Why sort_keys?
    Determinism: the same logical payload always produces the same capsule
    regardless of Python dict insertion order.  This makes meta_capsule_hash
    a stable integrity anchor across rebuilds.

    # Parameters
      payload : dict to compress (should NOT yet contain meta_capsule /
                meta_capsule_hash fields — avoids circularity)

    # Returns
      (capsule_b64url_no_padding, sha256_hex_of_capsule_string)
    """
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    compressed = zlib.compress(raw, level=9)
    capsule = base64.urlsafe_b64encode(compressed).decode().rstrip("=")
    capsule_hash = hashlib.sha256(capsule.encode()).hexdigest()
    return capsule, capsule_hash


# ─────────────────────────────────────────────────────────────────────────────
# Core commands
# ─────────────────────────────────────────────────────────────────────────────

def cmd_build(pkg_name: str) -> str:
    """Build an orphan git commit + PTOS-annotated tag for a named package.

    # What this produces
    A git tag named  pkg/<name>/v<version>  that:
      • Points to an orphan commit (a root commit with no parents, so it
        carries ONLY the package files — no repo history).
      • Has a JSON annotation containing the full PTOS manifest, including
        nd_point, foam_score, sha256, sealed_utc, and a meta_capsule.

    Pushing just this tag to a remote transfers only the objects reachable
    from it (the orphan commit + its tree + its blobs).  Nothing else from
    the local repo history crosses the wire.

    # Build steps
      1. hash-object   Write each file into .git/objects as a blob.
      2. _build_tree   Assemble blobs into a tree via temp index
                       (see _build_tree docstring for the index trick).
      3. nd_point      14-axis omnitoken position: axis i = φ^(-i), rounded
                       to 6 decimal places.  Encodes the package's "location"
                       in the 14-dimensional omnitoken surface bus.
      4. foam_score    φ × (n_files / (n_deps + 1)).  Higher = more content
                       per dependency.  Mirrors the codec's foam_score metric.
      5. sha256        Sorted-concatenated file hash for provenance anchoring.
      6. manifest      Full PTOS-tagged dict (see TAG ANNOTATION SCHEMA in
                       module docstring).
      7. meta_capsule  zlib+base64 compressed manifest (without itself).
                       Stored alongside meta_capsule_hash for integrity.
      8. commit-tree   Creates a root commit from the tree + manifest message.
                       No -p flag → orphan (no parents).
      9. tag -a        Annotates the commit.  Rebuilding deletes the existing
                       local tag first (idempotent — safe to call repeatedly).

    # φ (golden ratio) = (1 + √5) / 2 ≈ 1.618033…
    Used in both the soliton codec (Jupiter layer φ-locking, foam_score) and
    here as the metric for package "information density".

    # Parameters
      pkg_name : key in PACKAGES dict

    # Returns
      Tag name string, e.g. "pkg/usc-audio/v1.0.0"

    # Errors
      KeyError   if pkg_name is not in PACKAGES
      RuntimeError if no files in the package exist on disk, or a git
                   plumbing call fails
    """
    if pkg_name not in PACKAGES:
        raise KeyError(
            f"Unknown package: {pkg_name!r}. Known: {sorted(PACKAGES)}"
        )

    spec = PACKAGES[pkg_name].copy()
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    package_files = _expand_package_files(spec["files"])
    tree_hash, included_files = _build_tree(package_files)

    # nd_point: 14-axis omnitoken position, φ^(-i) normalized
    nd_point = [round(_PHI ** (-i), 6) for i in range(min(14, len(included_files)))]
    while len(nd_point) < 14:
        nd_point.append(0.0)

    # foam_score: φ × (files / (deps + 1))  — higher = denser, fewer deps
    n_deps = len(spec.get("depends", []))
    foam_score = round(len(included_files) / (n_deps + 1) * _PHI, 6)

    content_sha256 = _hash_file_contents(included_files)

    manifest: dict = {
        "schema":             "metafoam-pkg/v1",
        "pkg":                pkg_name,
        "version":            spec["version"],
        "layer":              spec["layer"],
        "domain":             spec["domain"],
        "condition":          spec["condition"],
        "stage":              spec["stage"],
        "source":             spec["source"],
        "tier":               spec["tier"],
        "module":             spec["module"],
        "archetype":          spec.get("archetype", ""),
        "tags":               spec.get("tags", []),
        "description":        spec.get("description", ""),
        "files":              included_files,
        "depends":            spec.get("depends", []),
        "nd_point":           nd_point,
        "foam_score":         foam_score,
        "sealed_utc":         now_utc,
        "sha256":             content_sha256,
        "verification_basis": spec.get("verification_basis", "OBSERVED"),
        "visibility":         spec.get("visibility", "INTERNAL"),
        "model_status":       spec.get("model_status", "CANONICAL"),
        "taint_status":       spec.get("taint_status", "CLEAN"),
    }

    # meta_capsule is computed over the manifest sans itself (no circularity)
    capsule, capsule_hash = _make_meta_capsule(manifest)
    manifest["meta_capsule"] = capsule
    manifest["meta_capsule_hash"] = capsule_hash

    annotation = json.dumps(manifest, indent=2)

    # Orphan commit — no -p parent flags → root commit
    commit_hash = _git("commit-tree", tree_hash, "-m", annotation)

    tag_name = f"pkg/{pkg_name}/v{spec['version']}"

    # Delete existing local tag silently (idempotent rebuild)
    _git("tag", "-d", tag_name, check=False)
    _git("tag", "-a", tag_name, commit_hash, "-m", annotation)

    print(f"[build] {tag_name}")
    print(f"        commit    : {commit_hash[:16]}")
    print(f"        tree      : {tree_hash[:16]}")
    print(f"        files     : {len(included_files)}")
    print(f"        foam_score: {foam_score}")
    print(f"        sha256    : {content_sha256[:16]}…")
    print(f"        capsule   : {capsule[:32]}…")

    return tag_name


def cmd_push(pkg_name: str, remote: str = DEFAULT_REMOTE) -> None:
    """Push a package tag to a remote.

    Only the tag + its orphan commit/tree/blobs are transferred.
    The full repo history is not pushed.

    # Force-push behaviour
    Package tags are rebuilt deterministically (metafoam_pkg.py build is
    idempotent on content, but creates a new orphan commit each time).
    If the tag already exists on the remote, force-push replaces it.
    This is safe because package tags are not branch heads — they are
    typed deployment units that represent "the current build of package X",
    not a shared history anchor.
    """
    spec = PACKAGES[pkg_name]
    tag_name = f"pkg/{pkg_name}/v{spec['version']}"
    refspec = f"+refs/tags/{tag_name}:refs/tags/{tag_name}"  # + = force
    print(f"[push]  {tag_name} → {remote} …")
    _git("push", remote, refspec)
    print("[push]  done")


def cmd_deploy(pkg_name: str, remote: str = DEFAULT_REMOTE) -> None:
    """Build + push in one step (the normal operator workflow)."""
    cmd_build(pkg_name)
    cmd_push(pkg_name, remote)


def cmd_list() -> None:
    """Print a table of all defined packages."""
    header = (
        f"{'Package':<22} {'Ver':<8} {'Tier':<14} "
        f"{'Domain':<10} {'Files':<6}  Description"
    )
    print(header)
    print("-" * 100)
    for name, spec in sorted(PACKAGES.items()):
        n_files = len(spec["files"])
        desc = spec.get("description", "")[:50]
        print(
            f"{name:<22} {spec['version']:<8} {spec['tier']:<14} "
            f"{spec['domain']:<10} {n_files:<6}  {desc}"
        )


def cmd_status(remote: str = DEFAULT_REMOTE) -> None:
    """List all pkg/* annotated tags present on the remote."""
    print(f"[status] fetching tag list from {remote} …")
    out = _git("ls-remote", "--tags", remote, "refs/tags/pkg/*", check=False)
    if not out:
        print("  (no pkg/* tags found on remote)")
        return
    print(f"\n{'Commit':<12}  Tag")
    print("-" * 60)
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 2:
            commit, ref = parts
            tag = ref.replace("refs/tags/", "")
            print(f"{commit[:12]}  {tag}")


def cmd_receive(pkg_name: str, target_dir: str = ".") -> None:
    """Fetch a package tag from the remote and unpack it.

    Intended for use on a substrate node (VPS):
      1. git fetch  refs/tags/<tag>
      2. git archive <tag> | tar -xC <target_dir>

    Prints the manifest summary (foam_score, file count, sha256) after unpack.
    """
    if pkg_name not in PACKAGES:
        raise KeyError(f"Unknown package: {pkg_name!r}")

    spec = PACKAGES[pkg_name]
    tag_name = f"pkg/{pkg_name}/v{spec['version']}"
    refspec = f"refs/tags/{tag_name}:refs/tags/{tag_name}"

    print(f"[receive] fetching {tag_name} from {DEFAULT_REMOTE} …")
    _git("fetch", DEFAULT_REMOTE, refspec)

    target = Path(target_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)

    with subprocess.Popen(
        ["git", "archive", "--format=tar", tag_name],
        cwd=REPO_ROOT, stdout=subprocess.PIPE,
    ) as archive_proc:
        with subprocess.Popen(
            ["tar", "-xC", str(target)],
            stdin=archive_proc.stdout,
        ) as tar_proc:
            if archive_proc.stdout:
                archive_proc.stdout.close()
            tar_proc.wait()

    if archive_proc.returncode != 0 or tar_proc.returncode != 0:
        raise RuntimeError(f"receive failed for {tag_name}")

    print(f"[receive] unpacked {tag_name} → {target}")

    raw_ann = _git("tag", "-l", tag_name, "--format=%(contents)")
    try:
        manifest = json.loads(raw_ann)
        print(f"          foam_score : {manifest.get('foam_score')}")
        print(f"          files      : {len(manifest.get('files', []))}")
        print(f"          sealed_utc : {manifest.get('sealed_utc')}")
        print(f"          sha256     : {manifest.get('sha256', '')[:16]}…")
    except json.JSONDecodeError:
        pass


def cmd_decode(pkg_name: str) -> None:
    """Decode and pretty-print the meta_capsule from a locally built tag.

    Decode rule (per PTOS_TAG_SCHEMA.md):
      json.loads(zlib.decompress(base64.urlsafe_b64decode(capsule + padding)))
    """
    spec = PACKAGES.get(pkg_name)
    if not spec:
        raise KeyError(f"Unknown package: {pkg_name!r}")
    tag_name = f"pkg/{pkg_name}/v{spec['version']}"
    raw_ann = _git("tag", "-l", tag_name, "--format=%(contents)")
    manifest = json.loads(raw_ann)
    capsule = manifest.get("meta_capsule", "")
    padding = "=" * (-len(capsule) % 4)
    payload = json.loads(
        zlib.decompress(base64.urlsafe_b64decode(capsule + padding))
    )
    print(json.dumps(payload, indent=2))


# ─────────────────────────────────────────────────────────────────────────────
# Post-commit hook — automatic sidecar deploy
#
# The hook is the "automatic" part of the sidecar pattern:
#   • Normal git workflow is unchanged.
#   • After every commit, the hook checks which package files changed in HEAD.
#   • Any package with changed files is rebuilt and pushed automatically.
#   • Failures are printed as warnings but do not block the commit.
# ─────────────────────────────────────────────────────────────────────────────

HOOK_PATH = REPO_ROOT / ".git" / "hooks" / "post-commit"
_HOOK_SCRIPT = (
    "#!/bin/sh\n"
    "# MetaFoam auto-deploy hook — installed by metafoam_pkg.py\n"
    f'python3 "{Path(__file__).resolve()}" hook run\n'
)


def cmd_hook(action: str) -> None:
    """Manage the post-commit auto-deploy hook.

    # What the hook does
    After every `git commit`, git runs .git/hooks/post-commit.  The installed
    script calls `metafoam_pkg.py hook run`, which:
      1. Reads the list of files changed in HEAD via git diff-tree.
      2. Compares that list against every package's file list.
      3. For any package with changed files, calls cmd_deploy() automatically.

    This is the "sidecar" behaviour: normal git workflow is completely
    unchanged.  The hook fires in the background and keeps substrate-node
    deployments in sync with the repo without any manual step.

    # Failure behaviour
    Deploy failures inside the hook are caught and printed as warnings.  They
    do NOT block the commit or raise an exit code — the commit always succeeds.

    # Parameters
      action : "install" | "remove" | "run"
        install  Write .git/hooks/post-commit and chmod +x.
        remove   Delete the hook file (no-op if not present).
        run      Execute hook logic directly (called by git or by hand).
    """
    if action == "install":
        HOOK_PATH.write_text(_HOOK_SCRIPT)
        HOOK_PATH.chmod(0o755)
        print(f"[hook] installed → {HOOK_PATH}")
        print("       After each commit, changed packages auto-build and push.")
    elif action == "remove":
        if HOOK_PATH.exists():
            HOOK_PATH.unlink()
            print(f"[hook] removed {HOOK_PATH}")
        else:
            print("[hook] not installed")
    elif action == "run":
        _hook_run()
    else:
        print(f"Unknown hook action: {action!r}. Use: install | remove | run")


def _hook_run() -> None:
    """Find packages whose tracked files changed in HEAD and redeploy them.

    # Algorithm
      1. git diff-tree --no-commit-id -r --name-only HEAD
         → list of repo-relative paths modified by the most recent commit.
      2. For each package in PACKAGES: set(package.files) ∩ changed_files.
         If non-empty, the package is stale and needs redeployment.
      3. cmd_deploy() for each stale package (build + push).
         Errors are caught as warnings; the hook never blocks a commit.

    # Why diff-tree instead of diff-index?
    diff-tree compares the commit object to its parent — it sees exactly what
    the commit recorded, independent of current working-tree state.  This is
    correct even if the working tree has subsequent unstaged changes.

    # Safe to call manually
    Running `metafoam_pkg.py hook run` from the shell is identical to what
    git would run after a commit.  Useful for testing or forced sync.
    """
    changed_raw = _git(
        "diff-tree", "--no-commit-id", "-r", "--name-only", "HEAD",
        check=False,
    )
    changed = set(changed_raw.splitlines())
    if not changed:
        return

    deployed = []
    for pkg_name, spec in PACKAGES.items():
        if set(_expand_package_files(spec["files"])) & changed:
            print(f"[hook] {pkg_name} has changed files — deploying …")
            try:
                cmd_deploy(pkg_name)
                deployed.append(pkg_name)
            except (RuntimeError, subprocess.CalledProcessError) as exc:
                print(f"[hook] WARN: deploy {pkg_name} failed: {exc}")

    if not deployed:
        print("[hook] no package files changed — nothing to deploy")


# ─────────────────────────────────────────────────────────────────────────────
# CLI dispatch
# ─────────────────────────────────────────────────────────────────────────────

def _usage_error(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


def main() -> None:
    """Parse argv and dispatch to the appropriate command function."""
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return

    cmd = args[0]

    dispatch: dict[str, object] = {
        "list":       lambda: cmd_list(),
        "status":     lambda: cmd_status(args[1] if len(args) > 1 else DEFAULT_REMOTE),
        "decode":     lambda: (
            cmd_decode(args[1]) if len(args) > 1
            else _usage_error("Usage: metafoam_pkg.py decode <pkg>")
        ),
        "hook":       lambda: cmd_hook(args[1] if len(args) > 1 else "install"),
        "hook-run":   lambda: _hook_run(),
        "deploy-all": lambda: _cmd_deploy_all(
            args[1] if len(args) > 1 else DEFAULT_REMOTE
        ),
    }

    if cmd in dispatch:
        dispatch[cmd]()
        return

    # Commands that need at least one positional arg
    if len(args) < 2:
        _usage_error(
            f"Usage: metafoam_pkg.py {cmd} <pkg> [remote]\n"
            "Run with --help for full usage."
        )

    pkg = args[1]
    remote = args[2] if len(args) > 2 else DEFAULT_REMOTE

    if cmd == "build":
        cmd_build(pkg)
    elif cmd == "push":
        cmd_push(pkg, remote)
    elif cmd == "deploy":
        cmd_deploy(pkg, remote)
    elif cmd == "receive":
        cmd_receive(pkg, remote)  # remote arg doubles as target_dir here
    else:
        print(
            f"Unknown command: {cmd!r}\n"
            "Commands: list | build | push | deploy | deploy-all | "
            "status | receive | decode | hook"
        )
        sys.exit(1)


def _cmd_deploy_all(remote: str) -> None:
    """Deploy every registered package to remote."""
    for pkg_name in sorted(PACKAGES):
        print(f"\n{'=' * 60}")
        cmd_deploy(pkg_name, remote)


if __name__ == "__main__":
    main()
