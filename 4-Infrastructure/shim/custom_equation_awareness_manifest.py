#!/usr/bin/env python3
"""Build a custom-equation awareness manifest for the local LLM.

This script inventories equation-bearing artifacts across the Research Stack and
turns them into compact curriculum records. The goal is awareness and routing,
not proof: every extracted equation keeps its source path, line/key, hash,
claim boundary, and primitive/bucket hints when available.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


DEFAULT_ROOTS = [
    Path("4-Infrastructure/shim"),
    Path("0-Core-Formalism/otom"),
    Path("0-Core-Formalism/lean/Semantics/Semantics"),
    Path("6-Documentation/tiddlywiki-local/wiki/tiddlers"),
    Path("6-Documentation/docs"),
    Path("6-Documentation/papers/OTOM"),
]

NAME_PATTERNS = [
    "*equation*",
    "*Equation*",
    "*SMN*",
    "*Semantic Mass*",
    "*4primitive*",
    "*MasterEquation*",
    "*EquationTranslation*",
    "*FieldEquation*",
    "*GCLField*",
    "*HachimojiEquation*",
    "*WitnessGrammar*",
    "*UnderversePacket*",
]

TEXT_SUFFIXES = {".md", ".tid", ".lean", ".tex", ".txt", ".mmd"}
JSON_SUFFIXES = {".json"}

LINE_RE = re.compile(
    r"(equation|formula|display|display_equation|master equation|semantic mass number|SMN|u_t|argmin|min_|def\s+|structure\s+|inductive\s+|abbrev\s+)",
    re.IGNORECASE,
)
SYMBOLIC_LINE_MARKERS = ("ρ(", "G =", "G=", "Γ", "C =", "C=", "AᵀA", "UΛUᵀ")

STOP_PATH_PARTS = {"__pycache__"}
GENERATED_NAME_MARKERS = (
    "_receipt.json",
    "_curriculum.jsonl",
    "_manifest.jsonl",
    "physics_math_llm_sft.jsonl",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_read(path: Path) -> bytes:
    return path.read_bytes()


def iter_candidate_files(roots: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    candidates: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for pattern in NAME_PATTERNS:
            for path in root.rglob(pattern):
                if not path.is_file():
                    continue
                if any(part in STOP_PATH_PARTS for part in path.parts):
                    continue
                if any(marker in path.name for marker in GENERATED_NAME_MARKERS):
                    continue
                if path.suffix not in TEXT_SUFFIXES | JSON_SUFFIXES:
                    continue
                if path not in seen:
                    seen.add(path)
                    candidates.append(path)
    return sorted(candidates)


def classify_text(text: str) -> str:
    lower = text.lower()
    stripped = lower.strip()
    if "semantic mass number" in lower or "smn" in lower:
        return "semantic_load"
    if stripped in {r"\begin{equation}", r"\end{equation}", "display_equation", "equation forest:"}:
        return "registry_schema"
    if any(term in lower for term in ["receipt:", "status:", "type ", "display_equation: string", "equation_id", "source_path", "durable source", "kernel id", "registry role"]):
        return "registry_schema"
    if lower.startswith(("# ", "## ", "### ", "!! ")) or lower.endswith(" equations") or lower.endswith(" equation"):
        return "heading_or_doc"
    if any(term in lower for term in ["equation sniffer", "sniffer", "scent", "witness grammar", "equation graphs", "probe candidate equation regions", "residual motifs", "adapter candidates"]):
        return "equation_sniffer"
    if any(term in lower for term in ["equation forest", "kernel registry", "kernelclass", "equationkernel", "kernelassignment", "fuse_existing_equation_kernels"]):
        return "equation_forest_control"
    if any(term in lower for term in ["equation type:", "geocognition", "publicclaim", "external validation gate", "quarantine bin", "confidence cap"]):
        return "equation_atlas"
    if any(term in lower for term in ["betti", "homology", "rank h_", "rank h", "hole", "loop", "cavity", "underverse", "complement-space", "forbidden", "excluded", "residual", "gamma(g)", "torsion", "curvature", "zeta(1/2"]):
        return "topology"
    if any(term in lower for term in ["u_t", "u_x", "u_xx", "navier", "stokes", "burgers", "viscous", "fluid", "laplacian", "partial", "gradient", "torque", "tau_", "theta", "wave equation"]):
        return "pde_dynamics"
    if any(term in lower for term in ["selector", "metamaterial", "polarization", "chirality", "spin", "material", "active", "phase circulation", "eta_thg", "psi_g", "gouy"]):
        return "material_selector"
    if any(term in lower for term in ["diat", "sidon", "shell", "k²", "sqrt", "floor", "a(n)", "b(n)", "genome18", "18-bit"]):
        return "integer_geometry"
    if any(term in lower for term in ["s(t)", "w_i", "h_i", "spiking", "neural", "activation", "surprise", "regret", "softmax"]):
        return "neural_signal"
    if any(term in lower for term in ["route", "routing", "warden", "promotion gate", "claim_boundary", "validation cap", "passes:", "fails:"]):
        return "routing_control"
    if any(term in lower for term in ["metadata_first", "preview", "learned shortcut", "king context", "retrieval", "adr-like", "search metadata"]):
        return "retrieval_control"
    if any(term in lower for term in ["qwen", "gemini", "kimi", "model indexing", "derived the equation", "requested synthesis"]):
        return "external_model_workbench"
    if any(term in lower for term in ["shannon", "entropy", "kolmogorov", "mdl", "zipf", "bwt", "hutter", "compression", "bits", "character"]):
        return "information_theory"
    if any(term in text for term in ["C_{ij}", "Λ", "UΛU", "lambda", "\\lambda", "eigen", "spectral", "zeta"]):
        return "spectral"
    if any(term in lower for term in ["ρ(", "density", "potential", "field", "manifold"]):
        return "field"
    if any(term in lower for term in ["g = a", "metric", "distance", "deformation", "shear", "a_{ij}"]):
        return "shear"
    if any(term in lower for term in ["γ", "packet", "codec", "encoding", "ans", "bitpack", "gcl"]):
        return "packet"
    if any(term in lower for term in ["basis", "qubo", "argmin"]):
        return "spectral"
    if any(term in lower for term in ["lean", "def ", "theorem", "lemma", "native_decide"]):
        return "formal"
    if "=" in text and any(marker in text for marker in ["\\", "_", "^", "sum", "Σ", "∑", "(", ")", "{", "}"]):
        return "math_kernel"
    return "sniffer_candidate"


def boundary_for(path: Path, text: str) -> str:
    lower = text.lower()
    if "hold" in lower or "blocked_usage" in lower or "blocked claim" in lower:
        return "hold-or-routing-prior"
    if path.suffix == ".lean":
        return "lean-source-prior; build required before proof promotion"
    if "conjecture" in lower:
        return "conjecture-prior-only"
    return "equation-awareness-prior-only"


def add_record(records: list[dict[str, Any]], *, source_path: Path, source_hash: str, kind: str, name: str, equation: str, locator: str, metadata: dict[str, Any] | None = None) -> None:
    equation = " ".join(str(equation).split())
    if not equation:
        return
    primitive_hint = classify_text(equation + " " + json.dumps(metadata or {}, ensure_ascii=False))
    record = {
        "id": f"{source_path}:{locator}:{name}",
        "source_path": str(source_path),
        "source_hash": source_hash,
        "kind": kind,
        "name": name[:160],
        "equation": equation[:2000],
        "equation_hash": hashlib.sha256(equation.encode("utf-8")).hexdigest(),
        "locator": locator,
        "primitive_hint": primitive_hint,
        "claim_boundary": boundary_for(source_path, equation + " " + json.dumps(metadata or {}, ensure_ascii=False)),
    }
    if metadata:
        record["metadata"] = metadata
    records.append(record)


def walk_json_equations(value: Any, path: list[str] | None = None) -> Iterable[tuple[list[str], str, Any]]:
    path = path or []
    if isinstance(value, dict):
        for key, child in value.items():
            lower = str(key).lower()
            if lower in {"equation", "formula", "display", "display_equation", "statement"} and isinstance(child, (str, int, float)):
                yield path + [str(key)], str(key), child
            elif lower in {"axioms", "unified_equations", "scientific_equations", "system_equations", "erdos_problems", "kernels", "primitives"}:
                yield from walk_json_equations(child, path + [str(key)])
            else:
                yield from walk_json_equations(child, path + [str(key)])
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            yield from walk_json_equations(child, path + [str(idx)])


def extract_json(path: Path, source_hash: str, records: list[dict[str, Any]]) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    for key_path, key, equation in walk_json_equations(data):
        parent = data
        for part in key_path[:-1]:
            try:
                parent = parent[int(part)] if isinstance(parent, list) else parent[part]
            except Exception:
                parent = {}
                break
        name = (
            parent.get("name")
            if isinstance(parent, dict)
            else None
        ) or (
            parent.get("kernel_id")
            if isinstance(parent, dict)
            else None
        ) or ".".join(key_path[-4:])
        metadata = {}
        if isinstance(parent, dict):
            for meta_key in (
                "primitive",
                "mapping",
                "domain",
                "domain_class",
                "bucket",
                "hyper_term",
                "claim_state",
                "authority_scope",
                "blocked_usage",
                "blocked_usages",
                "functional_role",
                "feasibility",
                "approach",
            ):
                if meta_key in parent:
                    metadata[meta_key] = parent[meta_key]
        add_record(
            records,
            source_path=path,
            source_hash=source_hash,
            kind="json_equation",
            name=str(name),
            equation=str(equation),
            locator=".".join(key_path),
            metadata=metadata,
        )


def extract_text(path: Path, source_hash: str, records: list[dict[str, Any]]) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or len(stripped) < 6:
            continue
        if path.suffix == ".tex" and (
            stripped.startswith("\\begin{")
            or stripped.startswith("\\end{")
            or stripped.startswith("\\label{")
            or stripped.startswith("\\title{")
            or stripped.startswith("\\section{")
            or stripped.startswith("\\subsection{")
        ):
            continue
        if not LINE_RE.search(stripped) and not any(marker in stripped for marker in SYMBOLIC_LINE_MARKERS):
            continue
        if stripped.startswith(("import ", "open ", "namespace ", "end ")):
            continue
        name = f"line_{line_no}"
        lean_match = re.match(r"(def|structure|inductive|abbrev|theorem|lemma)\s+([A-Za-z0-9_'.]+)", stripped)
        if lean_match:
            name = f"{lean_match.group(1)}_{lean_match.group(2)}"
        heading = re.match(r"^#+\s+(.+)$", stripped)
        if heading:
            name = heading.group(1)
        add_record(
            records,
            source_path=path,
            source_hash=source_hash,
            kind="text_equation_line",
            name=name,
            equation=stripped,
            locator=f"line:{line_no}",
            metadata={"line": line_no, "suffix": path.suffix},
        )


def curriculum_records(receipt: dict[str, Any], per_bucket_limit: int) -> list[dict[str, Any]]:
    system = "You are a custom-equation-aware routing model. Return compact JSON with source and claim boundaries."
    by_primitive: dict[str, list[dict[str, Any]]] = {}
    for record in receipt["equations"]:
        by_primitive.setdefault(record["primitive_hint"], []).append(record)
    selected: list[dict[str, Any]] = []
    low_value_limits = {"heading_or_doc": 12, "registry_schema": 16}
    for primitive, items in sorted(by_primitive.items()):
        selected.extend(items[: low_value_limits.get(primitive, per_bucket_limit)])
    records = []
    for item in selected:
        prompt = {
            "task": "route_custom_equation",
            "source_path": item["source_path"],
            "name": item["name"],
            "equation": item["equation"],
            "primitive_hint": item["primitive_hint"],
            "claim_boundary": item["claim_boundary"],
            "instruction": "Make the LLM aware of this local equation without overclaiming proof.",
        }
        answer = {
            "selected": True,
            "use_as": "custom_equation_awareness",
            "primitive_hint": item["primitive_hint"],
            "claim_boundary": item["claim_boundary"],
            "source_path": item["source_path"],
            "equation_hash": item["equation_hash"],
            "route_rule": "Use the equation as a local routing/canonicalization prior; require source/build/prover receipts before truth promotion.",
        }
        records.append(
            {
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                    {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
                ]
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, action="append")
    parser.add_argument("--receipt", type=Path, default=Path("4-Infrastructure/shim/custom_equation_awareness_manifest_receipt.json"))
    parser.add_argument("--manifest", type=Path, default=Path("4-Infrastructure/shim/custom_equation_awareness_manifest.jsonl"))
    parser.add_argument("--curriculum", type=Path, default=Path("4-Infrastructure/shim/custom_equation_awareness_curriculum.jsonl"))
    parser.add_argument("--per-bucket-limit", type=int, default=80)
    args = parser.parse_args()

    roots = args.root or DEFAULT_ROOTS
    files = iter_candidate_files(roots)
    equations: list[dict[str, Any]] = []
    source_summaries = []
    for path in files:
        try:
            raw = safe_read(path)
        except Exception:
            continue
        source_hash = sha256_bytes(raw)
        before = len(equations)
        if path.suffix in JSON_SUFFIXES:
            extract_json(path, source_hash, equations)
        elif path.suffix in TEXT_SUFFIXES:
            extract_text(path, source_hash, equations)
        count = len(equations) - before
        source_summaries.append(
            {
                "path": str(path),
                "sha256": source_hash,
                "suffix": path.suffix,
                "equations_extracted": count,
            }
        )

    primitive_counts: dict[str, int] = {}
    boundary_counts: dict[str, int] = {}
    for equation in equations:
        primitive_counts[equation["primitive_hint"]] = primitive_counts.get(equation["primitive_hint"], 0) + 1
        boundary_counts[equation["claim_boundary"]] = boundary_counts.get(equation["claim_boundary"], 0) + 1

    receipt = {
        "schema": "custom_equation_awareness_manifest_v1",
        "claim_boundary": "Equation awareness teaches local routing and recall; it does not prove or validate equations.",
        "roots": [str(root) for root in roots],
        "source_count": len(source_summaries),
        "equation_count": len(equations),
        "primitive_counts": primitive_counts,
        "boundary_counts": boundary_counts,
        "sources": source_summaries,
        "equations": equations,
        "lawful": bool(equations),
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.manifest.open("w", encoding="utf-8") as handle:
        for equation in equations:
            handle.write(json.dumps(equation, ensure_ascii=False) + "\n")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(receipt, args.per_bucket_limit):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps({k: receipt[k] for k in ("schema", "source_count", "equation_count", "primitive_counts", "boundary_counts", "lawful")}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
