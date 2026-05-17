#!/usr/bin/env python3
"""Eigenvector audit for major math/formalism repositories.

This is a lightweight structural pass, not a theorem checker.  It turns each
math-heavy repo/module into a feature vector, centers the matrix, and reports
the leading covariance eigenvectors as "math axes" for routing compression and
formalism work.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SHIM = ROOT / "4-Infrastructure" / "shim"
WIKI = ROOT / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers"
OUT_JSON = SHIM / "math_repository_eigenvector_audit.json"
OUT_JSONL = SHIM / "math_repository_eigenvector_audit_curriculum.jsonl"
OUT_TID = WIKI / "Math Repository Eigenvector Audit.tid"


REPO_CANDIDATES = [
    "0-Core-Formalism/lean/Semantics",
    "0-Core-Formalism/lean/LeanGPT",
    "0-Core-Formalism/otom/formal",
    "2-Search-Space/PIST",
    "2-Search-Space/FAMM",
    "2-Search-Space/tardygrada/proofs",
    "3-Mathematical-Models/AMMR",
    "3-Mathematical-Models/manifold_compression",
    "3-Mathematical-Models/hutter_manifold",
    "6-Documentation/docs/formal_verification",
    "6-Documentation/docs/semantics",
    "6-Documentation/invention_record",
    "ai-math-discovery-systems/AI-Feynman",
    "ai-math-discovery-systems/AI-Newton",
    "ai-math-discovery-systems/Goedel-Prover-V2",
    "ai-math-discovery-systems/PINNs",
    "ai-math-discovery-systems/alphageometry",
    "ai-math-discovery-systems/neural-conservation-law",
]

TEXT_EXTENSIONS = {
    ".lean",
    ".agda",
    ".v",
    ".thy",
    ".py",
    ".rs",
    ".jl",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
}

SKIP_DIRS = {
    ".git",
    ".lake",
    ".venv",
    "__pycache__",
    "node_modules",
    "build",
    "dist",
    "target",
    ".mypy_cache",
    ".pytest_cache",
}

FEATURES = [
    "file_count",
    "byte_count_log",
    "lean_files",
    "proof_files",
    "python_files",
    "markdown_files",
    "definitions",
    "theorems",
    "lemmas",
    "axioms",
    "imports",
    "evals",
    "sorry_markers",
    "admit_markers",
    "math_symbols",
    "unicode_symbols",
    "compression_terms",
    "geometry_terms",
    "spectrum_terms",
    "proof_terms",
    "model_terms",
    "hardware_terms",
    "dataset_terms",
    "avg_line_length",
]

TERM_PATTERNS = {
    "compression_terms": re.compile(r"\b(compress|codec|encode|decode|entropy|hutter|residual|packet|lut|dictionary)\b", re.I),
    "geometry_terms": re.compile(r"\b(manifold|topolog|braid|torsion|shear|field|metric|projection|eigen|vector|genus)\b", re.I),
    "spectrum_terms": re.compile(r"\b(spectrum|spectral|frequency|wave|phase|fourier|signal|eigenvalue)\b", re.I),
    "proof_terms": re.compile(r"\b(theorem|lemma|proof|axiom|decide|native_decide|invariant|lawful)\b", re.I),
    "model_terms": re.compile(r"\b(model|neural|pinn|feynman|newton|solver|optimizer|training|loss)\b", re.I),
    "hardware_terms": re.compile(r"\b(fpga|verilog|rtl|uart|bram|q16|fixed|silicon|hardware)\b", re.I),
    "dataset_terms": re.compile(r"\b(dataset|corpus|sample|benchmark|receipt|jsonl|manifest)\b", re.I),
}


@dataclass
class RepoVector:
    name: str
    path: str
    exists: bool
    features: dict[str, float]
    top_terms: list[tuple[str, int]]
    file_families: dict[str, int]
    content_hash: str | None


def iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS:
            files.append(path)
    return files


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def count_regex(pattern: str, text: str, flags: int = re.MULTILINE) -> int:
    return len(re.findall(pattern, text, flags))


def repo_vector(rel: str) -> RepoVector:
    path = ROOT / rel
    if not path.exists():
        return RepoVector(rel, rel, False, {key: 0.0 for key in FEATURES}, [], {}, None)

    files = iter_files(path)
    family_counter: Counter[str] = Counter()
    term_counter: Counter[str] = Counter()
    byte_count = 0
    line_count = 0
    line_length_sum = 0
    all_hash = hashlib.sha256()
    accum = {key: 0.0 for key in FEATURES}
    accum["file_count"] = float(len(files))

    for file_path in files:
        rel_file = file_path.relative_to(ROOT).as_posix()
        text = read_text(file_path)
        encoded = text.encode("utf-8", errors="ignore")
        all_hash.update(rel_file.encode("utf-8"))
        all_hash.update(b"\0")
        all_hash.update(hashlib.sha256(encoded).digest())
        byte_count += len(encoded)
        family_counter[file_path.suffix.lower() or "<none>"] += 1

        lines = text.splitlines()
        line_count += len(lines)
        line_length_sum += sum(len(line) for line in lines)

        suffix = file_path.suffix.lower()
        if suffix == ".lean":
            accum["lean_files"] += 1
        if suffix in {".lean", ".agda", ".v", ".thy"}:
            accum["proof_files"] += 1
        if suffix == ".py":
            accum["python_files"] += 1
        if suffix == ".md":
            accum["markdown_files"] += 1

        accum["definitions"] += count_regex(r"^\s*(def|abbrev|structure|inductive|class|instance|#let)\b", text)
        accum["theorems"] += count_regex(r"^\s*(theorem|example)\b", text)
        accum["lemmas"] += count_regex(r"^\s*lemma\b", text)
        accum["axioms"] += count_regex(r"^\s*(axiom|constant)\b", text)
        accum["imports"] += count_regex(r"^\s*(import|from\s+\S+\s+import|#import)\b", text)
        accum["evals"] += count_regex(r"^\s*(#eval|#check|native_decide)\b", text)
        accum["sorry_markers"] += len(re.findall(r"\bsorry\b", text))
        accum["admit_markers"] += len(re.findall(r"\badmit\b", text))
        accum["math_symbols"] += len(re.findall(r"[∀∃λΛΣΠα-ωΑ-Ω≤≥≠≈→←↔⊢⊨∂∇∑∏√∞]", text))
        accum["unicode_symbols"] += sum(1 for ch in text if ord(ch) > 127)
        for key, pattern in TERM_PATTERNS.items():
            hits = pattern.findall(text)
            accum[key] += len(hits)
            term_counter.update(str(hit).lower() for hit in hits)

    accum["byte_count_log"] = math.log2(byte_count + 1)
    accum["avg_line_length"] = line_length_sum / line_count if line_count else 0.0
    content_hash = all_hash.hexdigest() if files else hashlib.sha256(rel.encode("utf-8")).hexdigest()
    return RepoVector(
        name=rel.split("/")[-1] or rel,
        path=rel,
        exists=True,
        features=accum,
        top_terms=term_counter.most_common(12),
        file_families=dict(sorted(family_counter.items())),
        content_hash=content_hash,
    )


def zscore_matrix(vectors: list[RepoVector]) -> np.ndarray:
    matrix = np.array([[vec.features[key] for key in FEATURES] for vec in vectors], dtype=float)
    means = matrix.mean(axis=0)
    stds = matrix.std(axis=0)
    stds[stds == 0] = 1.0
    return (matrix - means) / stds


def eigen_audit(vectors: list[RepoVector]) -> dict[str, Any]:
    active = [vec for vec in vectors if vec.exists and vec.features["file_count"] > 0]
    if len(active) < 2:
        return {"axes": [], "repo_scores": []}

    zmat = zscore_matrix(active)
    cov = np.cov(zmat, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(cov)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    total = float(np.sum(np.maximum(eigenvalues, 0.0))) or 1.0

    axes = []
    repo_scores: dict[str, list[float]] = {vec.path: [] for vec in active}
    max_axes = min(6, eigenvectors.shape[1])
    projections = zmat @ eigenvectors[:, :max_axes]

    for axis_i in range(max_axes):
        weights = eigenvectors[:, axis_i]
        ranked = sorted(
            [(FEATURES[i], float(weights[i])) for i in range(len(FEATURES))],
            key=lambda item: abs(item[1]),
            reverse=True,
        )
        repo_rank = sorted(
            [(active[i].path, float(projections[i, axis_i])) for i in range(len(active))],
            key=lambda item: abs(item[1]),
            reverse=True,
        )
        axes.append(
            {
                "axis": axis_i + 1,
                "eigenvalue": float(eigenvalues[axis_i]),
                "explained_ratio": float(eigenvalues[axis_i] / total),
                "top_features": ranked[:8],
                "top_repositories": repo_rank[:8],
                "interpretation": interpret_axis(ranked[:8]),
            }
        )
        for repo_i, vec in enumerate(active):
            repo_scores[vec.path].append(float(projections[repo_i, axis_i]))

    return {"axes": axes, "repo_scores": repo_scores}


def interpret_axis(top_features: list[tuple[str, float]]) -> str:
    names = {name for name, _ in top_features[:5]}
    if {"proof_terms", "theorems", "lemmas"} & names:
        if {"sorry_markers", "admit_markers"} & names:
            return "proof-density vs proof-debt axis"
        return "formal proof-density axis"
    if {"model_terms", "python_files", "dataset_terms"} & names:
        return "empirical model/dataset axis"
    if {"compression_terms", "geometry_terms"} <= names or {"compression_terms", "spectrum_terms"} <= names:
        return "compression-geometry carrier axis"
    if {"hardware_terms", "evals"} & names:
        return "executable/hardware witness axis"
    if {"math_symbols", "unicode_symbols"} & names:
        return "symbolic notation density axis"
    return "mixed structural axis"


def stable_payload(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def write_jsonl(vectors: list[RepoVector], audit: dict[str, Any], receipt_hash: str) -> None:
    with OUT_JSONL.open("w", encoding="utf-8") as handle:
        for vec in vectors:
            record = {
                "task": "math_repository_eigenvector_audit",
                "repo": vec.path,
                "exists": vec.exists,
                "feature_vector": vec.features,
                "top_terms": vec.top_terms,
                "content_hash": vec.content_hash,
                "teaching_boundary": "Structural eigenvectors route repositories; they do not prove mathematical truth.",
            }
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
        handle.write(
            json.dumps(
                {
                    "task": "math_repository_eigenvector_axis_summary",
                    "axes": audit["axes"],
                    "receipt_hash": receipt_hash,
                    "teaching_boundary": "Use axes as compressor route priors, then require exact byte rehydration receipts.",
                },
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n"
        )


def format_feature_list(items: list[list[Any] | tuple[str, float]]) -> str:
    return ", ".join(f"{name}={value:.3f}" for name, value in items)


def write_tiddler(vectors: list[RepoVector], audit: dict[str, Any], receipt_hash: str) -> None:
    existing = [vec for vec in vectors if vec.exists and vec.features["file_count"] > 0]
    missing = [vec.path for vec in vectors if not vec.exists or vec.features["file_count"] == 0]
    axis_lines = []
    for axis in audit["axes"]:
        repos = ", ".join(f"{path} ({score:.2f})" for path, score in axis["top_repositories"][:5])
        axis_lines.append(
            "\n".join(
                [
                    f"!! Axis {axis['axis']}: {axis['interpretation']}",
                    f"* Explained ratio: {axis['explained_ratio']:.4f}",
                    f"* Top features: {format_feature_list(axis['top_features'][:6])}",
                    f"* Dominant repositories: {repos}",
                ]
            )
        )

    repo_lines = []
    scores = audit.get("repo_scores", {})
    for vec in existing:
        axis_score = scores.get(vec.path, [])
        score_text = ", ".join(f"a{i + 1}={score:.2f}" for i, score in enumerate(axis_score[:4]))
        repo_lines.append(
            f"|{vec.path}|{int(vec.features['file_count'])}|{int(vec.features['lean_files'])}|"
            f"{int(vec.features['proof_files'])}|{int(vec.features['python_files'])}|"
            f"{score_text}|{(vec.content_hash or '')[:16]}|"
        )

    text = f"""created: 20260507160000000
modified: 20260507160000000
tags: Compression Eigenvectors Formalism MathRepositories ProjectableGeometry
title: Math Repository Eigenvector Audit
type: text/vnd.tiddlywiki

This tiddler records the first structural eigenvector pass over the major math/formalism repositories in the stack.

The purpose is route selection, not truth promotion. A repository eigenvector says which mathematical surface a module resembles: proof-heavy, model-heavy, compression-geometric, symbolic, hardware-witness, or dataset/receipt oriented. Any compressor candidate still has to pass exact rehydration.

!! Scope

* Active repositories/modules scanned: {len(existing)}
* Missing or empty candidates: {len(missing)}
* Receipt: `4-Infrastructure/shim/math_repository_eigenvector_audit.json`
* Curriculum: `4-Infrastructure/shim/math_repository_eigenvector_audit_curriculum.jsonl`
* Receipt hash: `{receipt_hash}`

!! Eigen Axes

{chr(10).join(axis_lines)}

!! Repository Scores

|!Repository |!Files |!Lean |!Proof files |!Python |!Leading scores |!Content hash |
{chr(10).join(repo_lines)}

!! Compressor Tuning Implication

This fills a missing bucket in the projectable-geometry compressor. Before this pass, we had vectors for finance claims, genetics, molecular/PDE priors, and symbolic Standard Model reductions, but not for the math repositories themselves.

The immediate use is a route prior:

# Proof-dense repositories should feed theorem/witness tokenbooks and exact proof-state sidecars.
# Model/dataset repositories should feed numeric residual lanes and benchmark-corpus metadata.
# Compression-geometry repositories should feed carrier primitives, residual boat rules, and tokenbook transforms.
# Hardware-witness repositories should feed fixed-point and byte-lane constraints.

!! Boundary

This audit is lexical/structural. It does not certify that a theorem compiles, that an equation is correct, or that a repository is more important. It gives the compressor a coarse coordinate system for choosing which specialized route to try first.
"""
    OUT_TID.write_text(text, encoding="utf-8")


def main() -> None:
    vectors = [repo_vector(rel) for rel in REPO_CANDIDATES]
    audit = eigen_audit(vectors)
    body = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(ROOT),
        "feature_schema": FEATURES,
        "candidate_count": len(REPO_CANDIDATES),
        "active_count": sum(1 for vec in vectors if vec.exists and vec.features["file_count"] > 0),
        "vectors": [
            {
                "name": vec.name,
                "path": vec.path,
                "exists": vec.exists,
                "features": vec.features,
                "top_terms": vec.top_terms,
                "file_families": vec.file_families,
                "content_hash": vec.content_hash,
            }
            for vec in vectors
        ],
        "audit": audit,
        "claim_boundary": "Structural eigenvector audit only; compressor routing prior, not mathematical verification.",
    }
    receipt_hash = hashlib.sha256(stable_payload({k: v for k, v in body.items() if k != "generated_at"})).hexdigest()
    body["receipt_hash"] = receipt_hash
    OUT_JSON.write_text(json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    write_jsonl(vectors, audit, receipt_hash)
    write_tiddler(vectors, audit, receipt_hash)
    print(json.dumps({"active_count": body["active_count"], "axes": len(audit["axes"]), "receipt_hash": receipt_hash}, indent=2))


if __name__ == "__main__":
    main()
