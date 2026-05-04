#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Attachment collection helpers for ingestion flows.

The goal is to preserve the widest useful source context in `packages.files`
without hardcoding one-off logic in every ingestor.
"""

from __future__ import annotations

from pathlib import Path


ATTACHMENT_LIMIT = 4096

# Common asset folders found in exported chat bundles and similar archives.
CHAT_EXPORT_ASSET_DIRS = frozenset({
    "css",
    "js",
    "images",
    "stickers",
    "files",
    "audio",
    "video",
    "videos",
    "photos",
    "voice",
    "voice_messages",
    "documents",
})

SIDECAR_EXTENSIONS = frozenset({
    ".json",
    ".jsonl",
    ".md",
    ".txt",
    ".pdf",
    ".html",
    ".htm",
    ".xml",
    ".rss",
    ".atom",
    ".bib",
    ".bibtex",
    ".dot",
    ".gv",
    ".graphml",
    ".csv",
    ".tsv",
    ".tex",
    ".yaml",
    ".yml",
    ".toml",
})

RESONANT_EXTENSIONS = frozenset({
    ".md",
    ".txt",
    ".py",
    ".v",
    ".lean",
    ".hdl",
    ".c",
    ".cpp",
    ".h",
    ".json",
})

RESONANT_EXTENSIONS = frozenset({
    ".md",
    ".txt",
    ".py",
    ".v",
    ".lean",
    ".hdl",
    ".c",
    ".cpp",
    ".h",
    ".json",
})


def _repo_rel(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo))
    except ValueError:
        return str(path)


def _resolve_ref(raw: str, *, repo: Path, base: Path) -> Path | None:
    raw = raw.strip()
    if not raw:
        return None

    candidate = Path(raw)
    probes = []
    if candidate.is_absolute():
        probes.append(candidate)
    else:
        probes.append((base / candidate).resolve())
        probes.append((repo / candidate).resolve())
        probes.append(candidate.resolve())

    seen: set[Path] = set()
    for probe in probes:
        if probe in seen:
            continue
        seen.add(probe)
        if probe.exists():
            return probe
    return None


def _append_path(paths: list[Path], seen: set[str], path: Path, repo: Path) -> None:
    if not path.exists() or not path.is_file():
        return
    key = _repo_rel(path, repo)
    if key in seen:
        return
    seen.add(key)
    paths.append(path)


def _same_stem_sidecars(source: Path) -> list[Path]:
    out: list[Path] = []
    parent = source.parent
    for sibling in sorted(parent.iterdir()):
        if sibling == source or not sibling.is_file():
            continue
        if sibling.suffix.lower() not in SIDECAR_EXTENSIONS:
            continue
        if sibling.stem == source.stem:
            out.append(sibling)
    return out


def _html_bundle_attachments(source: Path) -> list[Path]:
    out: list[Path] = []
    parent = source.parent

    for sibling in sorted(parent.iterdir()):
        if sibling == source:
            continue
        if sibling.is_file() and sibling.suffix.lower() in {".html", ".htm"}:
            out.append(sibling)

    for child in sorted(parent.iterdir()):
        if not child.is_dir() or child.name.lower() not in CHAT_EXPORT_ASSET_DIRS:
            continue
        for asset in sorted(p for p in child.rglob("*") if p.is_file()):
            out.append(asset)

    return out


def _collect_resonant_attachments(
    source: Path,
    *,
    repo: Path,
    keywords: list[str] | None = None,
    limit: int = 5,
    threshold: float = 0.6,
) -> list[Path]:
    """Use SeismicSearchEngine to discover conceptually relevant attachments."""
    try:
        # Import dynamically to avoid circular dependencies if any
        # Assuming seismic_search.py is in the same directory or sibling
        import sys
        
        script_dir = Path(__file__).parent
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
            
        from seismic_search import SeismicSearchEngine
    except ImportError:
        return []

    if not keywords:
        # Fallback: extract simple keywords from source head if not provided
        try:
            with open(source, "r", encoding="utf-8", errors="ignore") as f:
                head = f.read(16384)
                keywords = re.findall(r"\b[a-zA-Z]{5,}\b", head)[:10]
        except Exception:
            return []

    if not keywords:
        return []

    query = " ".join(keywords)
    engine = SeismicSearchEngine(phi=0.0) # Default phi for ingestion
    
    # Target search directories
    search_dirs = [repo / "docs", repo / "core"]
    indexed = 0
    for d in search_dirs:
        if d.exists():
            engine.build_index(d)
            indexed += engine.doc_count
    
    if indexed == 0:
        return []

    results = engine.search(query, limit=limit * 2) # Get more to filter extensions
    
    resonant_paths: list[Path] = []
    for r in results:
        p = Path(r["path"])
        if p.resolve() == source.resolve():
            continue
        if p.suffix.lower() not in RESONANT_EXTENSIONS:
            continue
        if r["score"] < threshold:
            continue
        resonant_paths.append(p)
        if len(resonant_paths) >= limit:
            break
            
    return resonant_paths


def collect_auto_attachments(
    source: Path,
    *,
    repo: Path,
    mode: str = "full",
    limit: int = ATTACHMENT_LIMIT,
    keywords: list[str] | None = None,
) -> tuple[list[str], dict]:
    """Collect source attachments and return repo-relative file refs plus metadata.

    Modes:
    - `full`: source file plus known sidecars/bundles
    - `auto`: alias for `full` (backward compatibility)
    - `resonant`: full + conceptually relevant files via search
    - `source-only`: only the source file itself
    """
    source = source.resolve()
    mode = mode.lower()
    if mode == "auto":
        mode = "full"
    if mode not in {"full", "resonant", "source-only"}:
        raise ValueError(f"unknown attachment mode: {mode}")

    paths: list[Path] = []
    seen: set[str] = set()
    policies = ["source"]
    _append_path(paths, seen, source, repo)

    if mode == "full":
        for sidecar in _same_stem_sidecars(source):
            _append_path(paths, seen, sidecar, repo)
        if len(paths) > 1:
            policies.append("same-stem-sidecars")

        if source.suffix.lower() in {".html", ".htm"}:
            before = len(paths)
            for related in _html_bundle_attachments(source):
                _append_path(paths, seen, related, repo)
            if len(paths) > before:
                policies.append("html-bundle")

    if mode == "resonant":
        # Note: if keywords are needed but not passed, _collect_resonant_attachments
        # will try to derive them from the source file head.
        # In practice, ingestors like ingest_large_file.py should pass them.
        resonant = _collect_resonant_attachments(source, repo=repo, keywords=keywords)
        for res_path in resonant:
            _append_path(paths, seen, res_path, repo)
        if len(resonant) > 0:
            policies.append("conceptual-resonance")

    truncated = False
    if len(paths) > limit:
        paths = paths[:limit]
        truncated = True

    return (
        [_repo_rel(path, repo) for path in paths],
        {
            "attachment_mode": mode,
            "attachment_count": len(paths),
            "attachment_policies": policies,
            "attachment_truncated": truncated,
        },
    )


def collect_session_attachments(
    session_file: Path,
    payload: dict,
    *,
    repo: Path,
    auto_mode: str = "full",
    limit: int = ATTACHMENT_LIMIT,
) -> tuple[list[str], dict]:
    """Collect attachments for a structured session JSON.

    Supports explicit additions:
    - `files`: direct file refs
    - `attachments`: extra file refs
    - `attachment_dirs`: directories whose file trees should be attached
    """
    session_file = session_file.resolve()
    base = session_file.parent

    mode = str(payload.get("attachment_mode", auto_mode or "full")).lower()
    
    # If conceptual resonance is supported, we might have keywords in the payload
    # ingest_attachments itself doesn't know idea_weights yet, but we can pass them
    # if we refactor collect_auto_attachments further. 
    # For now, we'll let it derive them or rely on collect_auto_attachments expansion.
    
    refs, meta = collect_auto_attachments(
        session_file, repo=repo, mode=mode, limit=limit
    )

    paths = [(_resolve_ref(ref, repo=repo, base=base)) for ref in refs]
    paths = [p for p in paths if p is not None]
    seen = {_repo_rel(p, repo) for p in paths}

    explicit_refs = list(payload.get("files", [])) + list(payload.get("attachments", []))
    for raw in explicit_refs:
        resolved = _resolve_ref(str(raw), repo=repo, base=base)
        if resolved is not None:
            _append_path(paths, seen, resolved, repo)

    for raw_dir in payload.get("attachment_dirs", []):
        resolved_dir = _resolve_ref(str(raw_dir), repo=repo, base=base)
        if resolved_dir is None or not resolved_dir.is_dir():
            continue
        for child in sorted(p for p in resolved_dir.rglob("*") if p.is_file()):
            _append_path(paths, seen, child, repo)

    truncated = False
    if len(paths) > limit:
        paths = paths[:limit]
        truncated = True

    meta["attachment_count"] = len(paths)
    meta["attachment_truncated"] = truncated
    return [_repo_rel(p, repo) for p in paths], meta
