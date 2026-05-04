#!/usr/bin/env python3
"""
preprocess_algos_for_deepseek_v4.py — Algorithm Observation & Collapse Analysis Pipeline

Preprocesses all Research Stack algorithms into a structured observation state,
feeds them to DeepSeek-V4-Pro for definable improvement/collapse analysis,
and stores proposals for Lean formalization tracking.

Per AGENTS.md:
- Python is shim only; all logic conclusions must be ported to Lean
- Results feed into MATH_MODEL_MAP for equation registry tracking
- No new dependencies; uses existing deepseek_adapter.py
"""

import argparse
import ast
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict

# Step 0: Handle OLLAMA_HOST for IPv6 loopback compatibility
if "OLLAMA_HOST" not in os.environ:
    os.environ["OLLAMA_HOST"] = "[::1]:11434"

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from infra.deepseek_adapter import DeepSeekV4


# ═══════════════════════════════════════════════════════════════════════════
# GUARDRAIL: Secret Scrubber
# ═══════════════════════════════════════════════════════════════════════════

SECRET_PATTERNS: List[Tuple[str, str]] = [
    (r'(?i)(api[_-]?key\s*=\s*["\'])[a-zA-Z0-9_\-]{16,}["\']', r'\1<SECRET_SCRUBBED>"'),
    (r'(?i)(token\s*=\s*["\'])[a-zA-Z0-9_\-]{16,}["\']', r'\1<SECRET_SCRUBBED>"'),
    (r'(?i)(secret\s*=\s*["\'])[a-zA-Z0-9_\-]{8,}["\']', r'\1<SECRET_SCRUBBED>"'),
    (r'(?i)(password\s*=\s*["\'])[^"\']{4,}["\']', r'\1<SECRET_SCRUBBED>"'),
    (r'(?i)(bearer\s+)[a-zA-Z0-9_\-]{20,}', r'\1<SECRET_SCRUBBED>'),
    (r'(?i)(authorization[:\s]+)[a-zA-Z0-9_\-]{20,}', r'\1<SECRET_SCRUBBED>'),
    (r'(?i)(ssh[_-]?key\s*=\s*["\'])[^"\']+["\']', r'\1<SECRET_SCRUBBED>"'),
    (r'(?i)(private[_-]?key\s*=\s*["\'])[^"\']+["\']', r'\1<SECRET_SCRUBBED>"'),
    (r'(?i)(AKIA[0-9A-Z]{16})', r'<AWS_ACCESS_KEY_SCRUBBED>'),
    (r'(?i)(credential[s]?\s*=\s*["\'])[^"\']{8,}["\']', r'\1<SECRET_SCRUBBED>"'),
    (r'(http[s]?://(?:[0-9]{1,3}\.){3}[0-9]{1,3}[:/][^\s\")\]\']*)', r'<PRIVATE_ENDPOINT_SCRUBBED>'),
]


def scrub_secrets(text: str) -> str:
    """Remove or redact secrets, credentials, tokens, hostnames, and private endpoints."""
    for pattern, replacement in SECRET_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


# ═══════════════════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class AlgorithmObservation:
    """Structured observation of a single algorithm file."""
    file_path: str
    module_name: str
    docstring: str
    classes: List[Dict[str, Any]]
    functions: List[Dict[str, Any]]
    constants: List[Dict[str, Any]]
    imports: List[str]
    hash_sha256: str
    line_count: int
    complexity_score: int  # Rough proxy: number of branches + loops


@dataclass
class CollapseProposal:
    """Hardened proposal shape with Warden status and hold action."""
    proposal_id: str
    action: str  # "collapse" | "refactor" | "eliminate" | "hold"
    confidence: str  # "low" | "medium" | "high"
    files: List[str]
    shared_invariant: str
    behavior_to_preserve: str
    risk: str
    required_tests: List[str]
    lean_candidate: Optional[Dict[str, Any]]
    warden_status: str  # "DRAFT" | "HOLD" | "BLOCK" | "CANDIDATE"
    raw_description: str  # Original DeepSeek text for audit


@dataclass
class AnalysisResult:
    """Complete analysis result from DeepSeek-V4-Pro."""
    run_id: str
    timestamp: str
    model_used: str
    total_files_observed: int
    total_lines_observed: int
    observations: List[AlgorithmObservation]
    proposals: List[CollapseProposal]
    raw_response: str
    schema_valid: bool
    schema_errors: List[str]


# ═══════════════════════════════════════════════════════════════════════════
# Configuration & Caps
# ═══════════════════════════════════════════════════════════════════════════

MAX_FILES_PER_BUNDLE: int = 40
MAX_BUNDLE_TOKENS: int = 32000
MAX_PROMPT_TOKENS: int = 36000

# Directories to scan for algorithm files
ALGO_DIRS = [
    "infra",
    "scripts",
    "core",
]

# Exclude patterns
EXCLUDE_PATTERNS = [
    "venv",
    ".venv",
    ".lake",
    "__pycache__",
    "archive",
    "temp_junk",
    "node_modules",
    "scratch",
    "data",
    "out",
    "artifacts",
    "invention_record",
]


def should_include_file(file_path: Path) -> bool:
    """Check if a Python file should be included in observation."""
    path_str = str(file_path)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path_str:
            return False
    return file_path.suffix == ".py" and file_path.stat().st_size < 500_000  # Skip huge files


def extract_ast_observation(file_path: Path, source: str) -> AlgorithmObservation:
    """Extract structured observation from Python source via AST.

    IMPORTANT: source has ALREADY been scrubbed by scrub_secrets() before this
    function is called. The AST sees only redacted text.
    """
    tree = ast.parse(source)

    docstring = ast.get_docstring(tree) or ""
    classes: List[Dict[str, Any]] = []
    functions: List[Dict[str, Any]] = []
    constants: List[Dict[str, Any]] = []
    imports: List[str] = []
    complexity_score = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append({
                        "name": item.name,
                        "args": [arg.arg for arg in item.args.args],
                        "docstring": ast.get_docstring(item) or "",
                        "line_count": item.end_lineno - item.lineno if item.end_lineno else 0,
                    })
            classes.append({
                "name": node.name,
                "docstring": ast.get_docstring(node) or "",
                "bases": [base.id if isinstance(base, ast.Name) else str(type(base).__name__) for base in node.bases],
                "methods": methods,
                "line_count": node.end_lineno - node.lineno if node.end_lineno else 0,
            })

        elif isinstance(node, ast.FunctionDef) and not isinstance(
            getattr(node, "parent", None), ast.ClassDef
        ):
            func_doc = ast.get_docstring(node) or ""
            branches = sum(1 for n in ast.walk(node) if isinstance(n, (ast.If, ast.While, ast.For, ast.With)))
            complexity_score += branches

            functions.append({
                "name": node.name,
                "args": [arg.arg for arg in node.args.args],
                "docstring": func_doc[:500],
                "line_count": node.end_lineno - node.lineno if node.end_lineno else 0,
                "has_return": any(isinstance(n, ast.Return) for n in ast.walk(node)),
                "decorators": [d.id if isinstance(d, ast.Name) else str(type(d).__name__) for d in node.decorator_list],
            })

        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    constants.append({
                        "name": target.id,
                        "value_preview": "...",  # Never expose constant values
                    })

        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            else:
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")

    # Deterministic: deduplicate and sort imports
    imports = sorted(set(imports))[:50]

    return AlgorithmObservation(
        file_path=str(file_path.relative_to(project_root)),
        module_name=file_path.stem,
        docstring=docstring[:1000],
        classes=classes,
        functions=functions,
        constants=constants,
        imports=imports,
        hash_sha256=hashlib.sha256(source.encode()).hexdigest(),
        line_count=len(source.splitlines()),
        complexity_score=complexity_score,
    )


def gather_observations() -> Tuple[List[AlgorithmObservation], int, int]:
    """Gather observations from all algorithm files in Research Stack."""
    observations: List[AlgorithmObservation] = []
    total_lines = 0

    for dir_name in ALGO_DIRS:
        target_dir = project_root / dir_name
        if not target_dir.exists():
            continue

        # rglob order is filesystem-dependent; sort for determinism
        py_files = sorted(target_dir.rglob("*.py"), key=lambda p: str(p))

        for py_file in py_files:
            if not should_include_file(py_file):
                continue

            try:
                raw_source = py_file.read_text(encoding="utf-8", errors="replace")
                # GUARDRAIL: scrub secrets BEFORE any processing or AST parsing
                source = scrub_secrets(raw_source)
                obs = extract_ast_observation(py_file, source)
                observations.append(obs)
                total_lines += obs.line_count
            except SyntaxError:
                print(f"  [SKIP] Syntax error in {py_file}")
            except Exception as e:
                print(f"  [SKIP] Error reading {py_file}: {e}")

    # Sort by complexity score descending (most interesting first)
    observations.sort(key=lambda x: x.complexity_score, reverse=True)

    return observations, len(observations), total_lines


def build_observation_bundle(observations: List[AlgorithmObservation], max_files: int = MAX_FILES_PER_BUNDLE) -> str:
    """Build a structured text bundle for DeepSeek-V4-Pro consumption."""
    lines: List[str] = []
    lines.append("=" * 70)
    lines.append("RESEARCH STACK ALGORITHM OBSERVATION BUNDLE")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Total files observed: {len(observations)}")
    lines.append(f"Files included in bundle: {min(max_files, len(observations))}")
    lines.append("")
    lines.append("OBSERVATION PROTOCOL:")
    lines.append("- Each file is summarized by its AST structure")
    lines.append("- Classes, top-level functions, constants, and imports are extracted")
    lines.append("- Complexity score = branch/loop count (proxy for algorithmic density)")
    lines.append("- ALL SOURCE HAS BEEN PRE-SCRUBBED: no credentials, tokens, or private endpoints appear below")
    lines.append("")
    lines.append("=" * 70)
    lines.append("")

    for idx, obs in enumerate(observations[:max_files], 1):
        lines.append(f"--- FILE {idx}: {obs.file_path} ---")
        lines.append(f"Module: {obs.module_name}")
        lines.append(f"Lines: {obs.line_count} | Complexity: {obs.complexity_score}")
        lines.append(f"SHA256: {obs.hash_sha256[:16]}...")

        if obs.docstring:
            lines.append(f"Docstring: {obs.docstring[:300]}")

        if obs.classes:
            lines.append(f"Classes ({len(obs.classes)}):")
            for cls in obs.classes:
                lines.append(f"  - {cls['name']}({', '.join(cls['bases'])})")
                method_names = [m["name"] for m in cls["methods"]]
                lines.append(f"    Methods: {', '.join(method_names)}")

        if obs.functions:
            lines.append(f"Functions ({len(obs.functions)}):")
            for func in obs.functions:
                ret = " -> ..." if func["has_return"] else ""
                args = f"({', '.join(func['args'][:6])}{'...' if len(func['args']) > 6 else ''})"
                lines.append(f"  - {func['name']}{args}{ret}")
                if func["docstring"]:
                    lines.append(f"    Doc: {func['docstring'][:150]}")

        if obs.constants:
            lines.append(f"Constants: {', '.join(c['name'] for c in obs.constants[:8])}")

        lines.append("")

    lines.append("=" * 70)
    lines.append("END OF OBSERVATION BUNDLE")
    lines.append("=" * 70)

    return "\n".join(lines)


def build_collapse_prompt(bundle: str, total_files: int, total_lines: int) -> str:
    """Build the hardened prompt asking DeepSeek-V4-Pro for invariant-duplication analysis.

    The prompt does NOT ask "what should I delete?" It asks "where do invariants appear
    duplicated?" and forces every proposed collapse through justification gates.
    """
    return f"""You are an expert algorithmic analyst and formal systems architect. Your task is to analyze a collection of Python algorithm implementations from the Research Stack (OTOM framework) and identify where invariants appear duplicated across the codebase — not to recommend deletions unless rigorously justified.

## Context

The Research Stack follows these architectural principles:
- **OTOM** (Ordered Transformation & Orchestration Model): All work reduces to a single `bind` primitive with lawful checks, cost functions, and invariant extractors
- **Lean 4 is the source of truth**: Python is extraction/shim only; all core logic must be expressible in Lean
- **Five bind classes**: informational_bind, geometric_bind, thermodynamic_bind, physical_bind, control_bind
- **Fixed-point arithmetic**: Q0_16 for dimensionless scalars, Q16_16 only when absolutely necessary (no floats in hot paths)
- **No string parsing for decisions**: All types must be finite, enumerable, and indexable (Fin n)
- **Every def needs verification**: Either an #eval example, a theorem proving a property, or totality proof

## CRITICAL WARNINGS

1. **AST similarity is NOT semantic equivalence.** Two functions can look similar in AST structure but encode different safety boundaries, different invariants, or different bind classes. Never treat AST shape overlap as proof that two implementations are interchangeable.

2. **You are a proposal generator, not an authority.** Every proposal you make is a suspicion signal, not a command. The Warden (human reviewer) decides what is actually safe to collapse.

3. **Default to HOLD.** If you are uncertain whether two implementations share the same invariant, mark the proposal as `hold`, not `collapse`.

## Warden Rule — Mandatory for Every Deletion or Collapse

You may NOT recommend deleting or collapsing code unless you can name ALL of the following:
1. The duplicated invariant (specifically, what semantic property is preserved by both implementations)
2. The replacement abstraction (what single construct replaces them)
3. The preserved behavior (what exact behavior of each original must continue to work)
4. The test needed before migration (what test, benchmark, or theorem must pass)
5. The Lean module or theorem candidate, if applicable (which Lean file and what theorem)

If you cannot name all five, you MUST emit `action: "hold"`.

## Input: Algorithm Observation Bundle

The bundle below contains structured AST observations from {total_files} Python files ({total_lines} total lines). Each observation shows classes, functions, constants, and docstrings. ALL SOURCE HAS BEEN PRE-SCRUBBED of credentials, tokens, and private endpoints.

---

{bundle}

---

## Your Task

DO NOT ask "what should I delete?" Instead, answer: "Where do invariants appear duplicated?"

For each suspected duplication, force the proposal through the output classification below. Bias heavily toward `hold`.

### Output Classification (Every proposal MUST use this exact shape)

```json
{{
  "proposals": [
    {{
      "action": "collapse | refactor | eliminate | hold",
      "confidence": "low | medium | high",
      "files": ["4-Infrastructure/infra/file_a.py", "5-Applications/scripts/file_b.py"],
      "shared_invariant": "Describe the specific semantic invariant shared by these files.",
      "behavior_to_preserve": "List the exact behavior that must continue to work after any change.",
      "risk": "Describe what could break if this proposal is wrong.",
      "required_tests": ["Test name or theorem that must pass before migration"],
      "lean_candidate": {{
        "module": "PascalCase.lean",
        "theorems": ["theoremName1", "theoremName2"]
      }},
      "warden_status": "DRAFT | HOLD | BLOCK | CANDIDATE"
    }}
  ],
  "pattern_detection": [
    {{
      "pattern_name": "...",
      "files": ["..."],
      "description": "...",
      "suspicion_level": "low | medium | high"
    }}
  ],
  "lean_priorities": [
    {{
      "rank": 1,
      "module_name": "PascalCase.lean",
      "namespace": "Semantics.Domain",
      "bind_class": "informational_bind | geometric_bind | thermodynamic_bind | physical_bind | control_bind",
      "theorems": ["..."],
      "rationale": "..."
    }}
  ],
  "math_model_map_entries_draft": [
    {{
      "model_name": "...",
      "family": "...",
      "equation": "...",
      "variables": "...",
      "purpose": "...",
      "bind_class": "..."
    }}
  ],
  "summary": "One-paragraph executive summary. Include a count of how many proposals are hold vs collapse."
}}
```

### Rules for action values

- `collapse`: Only if you can name all 5 Warden items AND the invariant is provably identical.
- `refactor`: Improvement without deletion — e.g., porting logic to Lean, replacing float with Q0_16.
- `eliminate`: Only if the file is a pure shim with zero unique logic AND a Lean equivalent exists.
- `hold`: DEFAULT. Use when AST similarity is present but semantic equivalence is uncertain. Use when safety boundaries might differ. Use when you cannot name all 5 Warden items.

### Rules for warden_status

- `DRAFT`: Initial proposal, not yet reviewed.
- `HOLD`: Suspicion exists but not enough evidence to proceed. Human must inspect.
- `BLOCK`: Known unsafe — do not proceed without architectural review.
- `CANDIDATE`: Meets all Warden items and is ready for test-driven validation.

Return ONLY valid JSON. No markdown outside the JSON block."""


def validate_proposal_schema(proposal: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a single proposal against the hardened output schema."""
    errors: List[str] = []
    required_keys = {"action", "confidence", "files", "shared_invariant", "behavior_to_preserve", "risk", "required_tests", "warden_status"}
    missing = required_keys - set(proposal.keys())
    if missing:
        errors.append(f"Missing required keys: {missing}")

    action = proposal.get("action", "")
    if action not in {"collapse", "refactor", "eliminate", "hold"}:
        errors.append(f"Invalid action '{action}'; must be collapse|refactor|eliminate|hold")

    confidence = proposal.get("confidence", "")
    if confidence not in {"low", "medium", "high"}:
        errors.append(f"Invalid confidence '{confidence}'; must be low|medium|high")

    warden = proposal.get("warden_status", "")
    if warden not in {"DRAFT", "HOLD", "BLOCK", "CANDIDATE"}:
        errors.append(f"Invalid warden_status '{warden}'; must be DRAFT|HOLD|BLOCK|CANDIDATE")

    if action in {"collapse", "eliminate"}:
        if not proposal.get("shared_invariant", "").strip():
            errors.append("action=collapse|eliminate requires shared_invariant")
        if not proposal.get("behavior_to_preserve", "").strip():
            errors.append("action=collapse|eliminate requires behavior_to_preserve")
        if not proposal.get("risk", "").strip():
            errors.append("action=collapse|eliminate requires risk")
        if not proposal.get("required_tests"):
            errors.append("action=collapse|eliminate requires required_tests (non-empty list)")

    return len(errors) == 0, errors


def parse_proposals_from_response(response_text: str) -> Tuple[List[CollapseProposal], Optional[Dict], List[str]]:
    """Extract structured proposals from DeepSeek-V4-Pro response with schema validation."""
    proposals: List[CollapseProposal] = []
    schema_errors: List[str] = []

    json_start = response_text.find("```json")
    if json_start == -1:
        json_start = response_text.find("```")
    if json_start == -1:
        json_start = 0
        json_end = len(response_text)
    else:
        json_end = response_text.find("```", json_start + 3)
        if json_end == -1:
            json_end = len(response_text)

    if json_start != -1:
        json_str = response_text[json_start:json_end].replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            schema_errors.append(f"JSON decode error: {e}")
            return proposals, None, schema_errors
    else:
        schema_errors.append("No JSON block found in response")
        return proposals, None, schema_errors

    raw_proposals = data.get("proposals", [])
    for idx, p in enumerate(raw_proposals):
        valid, errors = validate_proposal_schema(p)
        if not valid:
            schema_errors.extend([f"Proposal {idx}: {e}" for e in errors])
            warden = "BLOCK"
            action = "hold"
        else:
            warden = p.get("warden_status", "DRAFT")
            action = p.get("action", "hold")

        proposals.append(CollapseProposal(
            proposal_id=f"proposal_{idx:03d}",
            action=action,
            confidence=p.get("confidence", "low"),
            files=p.get("files", []),
            shared_invariant=p.get("shared_invariant", ""),
            behavior_to_preserve=p.get("behavior_to_preserve", ""),
            risk=p.get("risk", ""),
            required_tests=p.get("required_tests", []),
            lean_candidate=p.get("lean_candidate"),
            warden_status=warden,
            raw_description=json.dumps(p, indent=2),
        ))

    return proposals, data, schema_errors


def save_observation_bundle(observations: List[AlgorithmObservation], output_dir: Path, run_id: str) -> Tuple[Path, Path]:
    """Save observation bundle in JSON and human-readable markdown (dry-run output)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%dT%H-%M-%S", time.gmtime())

    bundle_dict = {
        "run_id": run_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "total_files": len(observations),
        "observations": [asdict(obs) for obs in observations],
        "scrubbed": True,
        "manifest_hash": hashlib.sha256(
            json.dumps([asdict(obs) for obs in observations], sort_keys=True).encode()
        ).hexdigest(),
    }

    json_path = output_dir / f"observation_bundle_{timestamp}_{run_id[:8]}.json"
    json_path.write_text(
        json.dumps(bundle_dict, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    md_lines: List[str] = []
    md_lines.append("# Observation Bundle (Dry Run)")
    md_lines.append(f"- **Run ID:** {run_id}")
    md_lines.append(f"- **Timestamp:** {bundle_dict['timestamp']}")
    md_lines.append(f"- **Total files:** {bundle_dict['total_files']}")
    md_lines.append(f"- **Manifest hash:** {bundle_dict['manifest_hash']}")
    md_lines.append(f"- **Secrets scrubbed:** {bundle_dict['scrubbed']}")
    md_lines.append("")

    for obs in observations:
        md_lines.append(f"## {obs.file_path}")
        md_lines.append(f"- **Module:** {obs.module_name}")
        md_lines.append(f"- **Lines:** {obs.line_count} | **Complexity:** {obs.complexity_score}")
        md_lines.append(f"- **SHA256:** `{obs.hash_sha256}`")
        if obs.docstring:
            md_lines.append(f"- **Docstring:** {obs.docstring[:200]}...")
        if obs.classes:
            md_lines.append(f"- **Classes:** {', '.join(c['name'] for c in obs.classes)}")
        if obs.functions:
            md_lines.append(f"- **Functions:** {', '.join(f['name'] for f in obs.functions)}")
        md_lines.append("")

    md_path = output_dir / f"observation_bundle_{timestamp}_{run_id[:8]}.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    return json_path, md_path


def save_analysis_result(result: AnalysisResult, output_dir: Path) -> Path:
    """Save analysis result to structured JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = result.timestamp.replace(":", "-").replace("T", "_")
    output_path = output_dir / f"algo_collapse_analysis_{timestamp_str}.json"

    result_dict = {
        "run_id": result.run_id,
        "timestamp": result.timestamp,
        "model_used": result.model_used,
        "total_files_observed": result.total_files_observed,
        "total_lines_observed": result.total_lines_observed,
        "observations": [asdict(obs) for obs in result.observations],
        "proposals": [asdict(prop) for prop in result.proposals],
        "schema_valid": result.schema_valid,
        "schema_errors": result.schema_errors,
        "raw_response": result.raw_response,
    }

    output_path.write_text(
        json.dumps(result_dict, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return output_path


def emit_math_model_map_draft(parsed_data: Optional[Dict], output_dir: Path, run_id: str) -> Optional[Path]:
    """Emit MATH_MODEL_MAP entries as a DRAFT file — NEVER auto-write to the canonical TSV."""
    if not parsed_data:
        return None

    entries = parsed_data.get("math_model_map_entries_draft", parsed_data.get("math_model_map_entries", []))
    if not entries:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%dT%H-%M-%S", time.gmtime())
    draft_path = output_dir / f"math_model_map_entries_DRAFT_{timestamp}_{run_id[:8]}.tsv"

    header = "Model_Name\tFamily\tEquation\tVariables\tPurpose\tLocation\tImplemented\tStatus\tCross_Refs\tDomain_Type\tBind_Class\n"
    lines = [header]
    for entry in entries:
        line = "\t".join([
            entry.get("model_name", ""),
            entry.get("family", ""),
            entry.get("equation", ""),
            entry.get("variables", ""),
            entry.get("purpose", ""),
            entry.get("location", ""),
            entry.get("implemented", ""),
            entry.get("status", ""),
            entry.get("cross_refs", ""),
            entry.get("domain_type", ""),
            entry.get("bind_class", ""),
        ])
        lines.append(line)

    draft_path.write_text("\n".join(lines), encoding="utf-8")
    return draft_path


def main():
    parser = argparse.ArgumentParser(
        description="Algorithm Observation & Collapse Analysis Pipeline (DeepSeek-V4-Pro)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and save observation bundle only. Do NOT call DeepSeek API.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=MAX_FILES_PER_BUNDLE,
        help=f"Maximum files to include in bundle (default: {MAX_FILES_PER_BUNDLE})",
    )
    parser.add_argument("--max-tokens", type=int, default=36000, help="Maximum estimated prompt tokens allowed (default: 36000)")
    parser.add_argument("--output-dir", type=str, default="5-Applications/out/algo_collapse_analysis", help="Output directory for all artifacts")
    parser.add_argument("--model", type=str, default="deepseek-v4-pro", help="Model to use (e.g. deepseek-v4-pro, deepseek-v4-flash:cloud)")
    parser.add_argument("--local", action="store_true", help="Use local Ollama instance (or Ollama Cloud via local proxy)")
    args = parser.parse_args()

    print("=" * 70)
    print("ALGORITHM OBSERVATION & COLLAPSE ANALYSIS PIPELINE")
    print("DeepSeek-V4-Pro | OTOM Research Stack")
    if args.dry_run:
        print("MODE: DRY-RUN (no API call)")
    print("=" * 70)

    output_dir = Path(args.output_dir)

    # Step 1: Gather observations
    print("\n[1] Gathering algorithm observations...")
    observations, total_files, total_lines = gather_observations()
    print(f"  Files observed: {total_files}")
    print(f"  Total lines: {total_lines}")
    print(f"  Top 5 by complexity:")
    for obs in observations[:5]:
        print(f"    - {obs.file_path} (complexity={obs.complexity_score}, lines={obs.line_count})")

    # Step 2: Build observation bundle
    print("\n[2] Building observation bundle...")
    bundle = build_observation_bundle(observations, max_files=args.max_files)
    bundle_chars = len(bundle)
    bundle_tokens = bundle_chars // 4
    print(f"  Bundle size: {bundle_chars:,} characters")
    print(f"  Estimated tokens: ~{bundle_tokens:,}")

    if bundle_tokens > MAX_BUNDLE_TOKENS:
        print(f"  [WARNING] Bundle exceeds max cap ({MAX_BUNDLE_TOKENS}). Truncating file list...")
        # Rough heuristic: reduce max_files proportionally
        scale = MAX_BUNDLE_TOKENS / bundle_tokens
        reduced_max = max(1, int(args.max_files * scale * 0.9))
        bundle = build_observation_bundle(observations, max_files=reduced_max)
        bundle_chars = len(bundle)
        bundle_tokens = bundle_chars // 4
        print(f"  Reduced bundle: ~{bundle_tokens:,} tokens ({reduced_max} files)")

    # Deterministic run ID from scrubbed bundle hash
    run_id = hashlib.sha256(bundle.encode()).hexdigest()[:16]
    print(f"  Deterministic run ID: {run_id}")

    # Step 2.5: Dry-run — save bundle and exit
    if args.dry_run:
        print("\n[DRY-RUN] Saving observation bundle...")
        json_path, md_path = save_observation_bundle(observations, output_dir, run_id)
        print(f"  JSON: {json_path}")
        print(f"  Markdown: {md_path}")
        print("\n" + "=" * 70)
        print("DRY-RUN COMPLETE — no API call made")
        print("=" * 70)
        print("\nNext steps:")
        print(f"  1. Inspect bundle: {md_path}")
        print(f"  2. Verify secrets were scrubbed (search for '<SECRET_SCRUBBED>')")
        print(f"  3. If satisfied, run without --dry-run to call DeepSeek-V4-Pro")
        return

    # Step 3: Build prompt
    print("\n[3] Building collapse analysis prompt...")
    prompt = build_collapse_prompt(bundle, total_files, total_lines)
    prompt_chars = len(prompt)
    prompt_tokens = prompt_chars // 4
    print(f"  Prompt size: {prompt_chars:,} characters")
    print(f"  Estimated tokens: ~{prompt_tokens:,}")

    if prompt_tokens > args.max_tokens:
        print(f"  [ERROR] Prompt exceeds --max-tokens cap ({args.max_tokens}).")
        print(f"    Either increase --max-tokens or reduce --max-files.")
        sys.exit(1)

    # Step 4: Initialize DeepSeek-V4-Pro client
    print(f"\n[4] Initializing client (Mode: {'Local/Ollama' if args.local else 'DeepSeek API'})...")
    
    api_key = None
    if not args.local:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            print("  [ERROR] DEEPSEEK_API_KEY not found in environment!")
            print("  To use Ollama Cloud or local models, add the --local flag.")
            sys.exit(1)

    local_url = f"http://{os.environ['OLLAMA_HOST']}"
    client = DeepSeekV4(api_key=api_key, local_url=local_url, use_local=args.local)
    model = args.model

    if not args.local:
        print(f"  API key prefix: {api_key[:8]}...")
        print(f"  Target: https://api.deepseek.com/v1")
    else:
        print(f"  Local URL: {local_url}")
    
    print(f"  Model: {model}")

    # Step 5: Send to DeepSeek-V4-Pro
    print("\n[5] Sending observation bundle to DeepSeek-V4-Pro...")
    print(f"  This may take several minutes (prompt is ~{prompt_tokens:,} tokens)")
    start_time = time.time()

    try:
        messages = [{"role": "user", "content": prompt}]
        response = client.chat(messages, model=model, stream=False, max_tokens=8192)

        raw_response = response["choices"][0]["message"]["content"]
        elapsed = time.time() - start_time

        print(f"  Response received in {elapsed:.1f}s")
        print(f"  Response length: {len(raw_response):,} characters")

    except Exception as e:
        print(f"  [ERROR] API call failed: {e}")
        sys.exit(1)

    # Step 6: Parse proposals with schema validation
    print("\n[6] Parsing collapse proposals from response...")
    proposals, parsed_data, schema_errors = parse_proposals_from_response(raw_response)
    schema_valid = len(schema_errors) == 0
    print(f"  Schema valid: {schema_valid}")
    if not schema_valid:
        print(f"  Schema errors ({len(schema_errors)}):")
        for err in schema_errors[:5]:
            print(f"    - {err}")

    print(f"  Proposals extracted: {len(proposals)}")
    action_counts: Dict[str, int] = {}
    warden_counts: Dict[str, int] = {}
    for p in proposals:
        action_counts[p.action] = action_counts.get(p.action, 0) + 1
        warden_counts[p.warden_status] = warden_counts.get(p.warden_status, 0) + 1
    for action, count in sorted(action_counts.items()):
        print(f"    - {action}: {count}")
    print(f"  Warden status breakdown:")
    for status, count in sorted(warden_counts.items()):
        print(f"    - {status}: {count}")

    # Step 7: Emit MATH_MODEL_MAP draft (never auto-write canonical TSV)
    print("\n[7] Emitting MATH_MODEL_MAP draft entries...")
    draft_map_path = emit_math_model_map_draft(parsed_data, output_dir, run_id)
    if draft_map_path:
        print(f"  Draft emitted: {draft_map_path}")
        print(f"  [NOTICE] This is a DRAFT. Do NOT auto-commit to shared-data/data/MATH_MODEL_MAP.tsv.")
        print(f"  Review manually, then append if validated.")
    else:
        print("  No MATH_MODEL_MAP draft entries generated.")

    # Step 8: Save result
    print("\n[8] Saving analysis result...")
    result = AnalysisResult(
        run_id=run_id,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        model_used=model,
        total_files_observed=total_files,
        total_lines_observed=total_lines,
        observations=observations[:args.max_files],
        proposals=proposals,
        raw_response=raw_response,
        schema_valid=schema_valid,
        schema_errors=schema_errors,
    )

    output_path = save_analysis_result(result, output_dir)
    print(f"  Saved to: {output_path}")

    # Also save raw response separately for easy reading
    raw_path = output_dir / f"algo_collapse_raw_{result.run_id}.md"
    raw_path.write_text(raw_response, encoding="utf-8")
    print(f"  Raw response: {raw_path}")

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"\nNext steps:")
    print(f"  1. Review proposals: {output_path}")
    print(f"  2. Read raw response: {raw_path}")
    print(f"  3. Inspect schema_errors if any proposals were auto-BLOCKed")
    if draft_map_path:
        print(f"  4. Review MATH_MODEL_MAP draft: {draft_map_path}")
    print(f"  5. Promote HOLD/CANDIDATE proposals through tests and Lean formalization")


if __name__ == "__main__":
    main()
