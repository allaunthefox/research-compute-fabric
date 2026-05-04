#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
# PTOS: LAYER=CORE / DOMAIN=TEST / CONDITION=EXPERIMENTAL / STAGE=ACTIVE / SOURCE=CODE
"""
Math Check Package Layer
========================

Purpose
-------
Central registry for math-check backends used across the repo.

This layer answers three operational questions:

1. What symbolic / numeric / SMT / CAS backends do we know about?
2. Which of them are actually available in the current environment?
3. Given a verification task, which backend should we record or prefer?

It also carries a lightweight "math style" inference so metaphor-heavy or
patamathematical work can be routed toward cross-check-heavy verification
instead of being treated as ordinary formal derivation by default.

Usage
-----
  python3 5-Applications/scripts/math_check_packages.py list
  python3 5-Applications/scripts/math_check_packages.py select --require symbolic_simplify equation_solve
  python3 5-Applications/scripts/math_check_packages.py record --require symbolic_simplify equation_solve
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class MathCheckBackend:
    """Registry entry for one math-check backend."""

    name: str
    import_name: str | None
    command: str | None
    kind: str
    capabilities: tuple[str, ...]
    verification_method: str
    priority: int
    notes: str = ""

    def is_available(self) -> bool:
        if self.import_name and importlib.util.find_spec(self.import_name) is not None:
            return True
        if self.command and shutil.which(self.command):
            return True
        return False


_ALIASES = {
    "sympy": "sympy",
    "sympy symbolic": "sympy",
    "numpy": "numpy",
    "scipy": "scipy",
    "mpmath": "mpmath",
    "z3": "z3",
    "z3-solver": "z3",
    "sage": "sage",
    "sagemath": "sage",
    "maxima": "maxima",
    "wolfram": "wolframscript",
    "wolfram alpha": "wolframalpha",
    "wolframalpha": "wolframalpha",
    "wolfram script": "wolframscript",
    "wolframscript": "wolframscript",
    "wolfram client": "wolframclient",
    "wolframclient": "wolframclient",
    "mathematica": "wolframscript",
    "maple": "maple",
}

_PATAMATHEMATICS_MARKERS = {
    "patamathematics",
    "patamathematical",
    "pataphysics",
    "pataphysical",
    "metaphor translation",
    "metaphor-translation",
}


BACKENDS: dict[str, MathCheckBackend] = {
    "sympy": MathCheckBackend(
        name="sympy",
        import_name="sympy",
        command=None,
        kind="symbolic",
        capabilities=(
            "symbolic_simplify",
            "symbolic_expand",
            "equation_solve",
            "calculus",
            "matrix_algebra",
            "assumption_reasoning",
            "latex_bridge",
            "number_theory",
        ),
        verification_method="sympy",
        priority=100,
        notes="Best default local symbolic checker in the current stack.",
    ),
    "mpmath": MathCheckBackend(
        name="mpmath",
        import_name="mpmath",
        command=None,
        kind="numeric",
        capabilities=(
            "high_precision_numeric",
            "special_functions",
            "root_finding",
        ),
        verification_method="mpmath",
        priority=70,
        notes="Good for precision checks after symbolic normalization.",
    ),
    "numpy": MathCheckBackend(
        name="numpy",
        import_name="numpy",
        command=None,
        kind="numeric",
        capabilities=(
            "array_numeric",
            "linear_algebra",
            "fft",
        ),
        verification_method="numpy",
        priority=65,
        notes="Useful for vectorized numeric sanity checks and simulation.",
    ),
    "scipy": MathCheckBackend(
        name="scipy",
        import_name="scipy",
        command=None,
        kind="numeric",
        capabilities=(
            "numerical_optimize",
            "integrate",
            "statistics",
            "signal",
            "sparse_linear_algebra",
        ),
        verification_method="scipy",
        priority=75,
        notes="Numeric verification, optimization, integration, and signal checks.",
    ),
    "z3": MathCheckBackend(
        name="z3",
        import_name="z3",
        command=None,
        kind="smt",
        capabilities=(
            "constraint_solve",
            "smt_check",
            "satisfiability",
            "exact_logic",
        ),
        verification_method="z3",
        priority=80,
        notes="Use for satisfiability and constraint-heavy math checks.",
    ),
    "sage": MathCheckBackend(
        name="sage",
        import_name="sageall",
        command="sage",
        kind="cas",
        capabilities=(
            "symbolic_simplify",
            "equation_solve",
            "calculus",
            "matrix_algebra",
            "number_theory",
            "combinatorics",
        ),
        verification_method="sage",
        priority=90,
        notes="Large CAS surface; heavier than SymPy but broader.",
    ),
    "maxima": MathCheckBackend(
        name="maxima",
        import_name=None,
        command="maxima",
        kind="cas",
        capabilities=(
            "symbolic_simplify",
            "equation_solve",
            "calculus",
        ),
        verification_method="maxima",
        priority=60,
        notes="Classic local CAS fallback.",
    ),
    "maple": MathCheckBackend(
        name="maple",
        import_name=None,
        command="maple",
        kind="cas",
        capabilities=(
            "symbolic_simplify",
            "equation_solve",
            "calculus",
            "matrix_algebra",
        ),
        verification_method="maple",
        priority=85,
        notes="Commercial CAS backend when available.",
    ),
    "wolframscript": MathCheckBackend(
        name="wolframscript",
        import_name=None,
        command="wolframscript",
        kind="cas",
        capabilities=(
            "symbolic_simplify",
            "equation_solve",
            "calculus",
            "special_functions",
            "plotting",
        ),
        verification_method="wolframscript",
        priority=88,
        notes="Local Wolfram runtime bridge.",
    ),
    "wolframclient": MathCheckBackend(
        name="wolframclient",
        import_name="wolframclient",
        command=None,
        kind="bridge",
        capabilities=(
            "wolfram_api_bridge",
            "remote_cas",
        ),
        verification_method="wolframclient",
        priority=50,
        notes="Python bridge to external Wolfram infrastructure.",
    ),
    "wolframalpha": MathCheckBackend(
        name="wolframalpha",
        import_name="wolframalpha",
        command=None,
        kind="bridge",
        capabilities=(
            "remote_cas",
            "equation_query",
            "special_functions",
        ),
        verification_method="wolframalpha",
        priority=55,
        notes="External query interface rather than a local symbolic engine.",
    ),
}


def canonical_backend_name(name: str) -> str:
    """Normalize a backend label or alias to a canonical registry key."""
    key = " ".join(name.strip().lower().replace("_", " ").split())
    return _ALIASES.get(key, key)


def infer_math_style(text: str | Iterable[str] | None) -> str:
    """Classify math framing as FORMAL, PATAMATHEMATICAL, HYBRID, or UNSPECIFIED."""
    if text is None:
        return "UNSPECIFIED"
    if isinstance(text, str):
        haystack = text.lower()
    else:
        haystack = " ".join(str(x).lower() for x in text)

    has_pata = any(marker in haystack for marker in _PATAMATHEMATICS_MARKERS)
    has_formal = any(
        marker in haystack
        for marker in ("theorem", "lemma", "proof", "equation", "derivation", "symbolic")
    )
    if has_pata and has_formal:
        return "HYBRID"
    if has_pata:
        return "PATAMATHEMATICAL"
    if has_formal:
        return "FORMAL"
    return "UNSPECIFIED"


def list_backends(include_unavailable: bool = False) -> list[dict]:
    """Return backend records, optionally including unavailable ones."""
    rows: list[dict] = []
    for backend in sorted(BACKENDS.values(), key=lambda b: (-b.priority, b.name)):
        available = backend.is_available()
        if not include_unavailable and not available:
            continue
        row = asdict(backend)
        row["available"] = available
        rows.append(row)
    return rows


def select_backend(
    required_capabilities: Iterable[str],
    preferred: str | None = None,
    include_unavailable: bool = False,
) -> dict | None:
    """Choose the best backend that satisfies all required capabilities."""
    required = tuple(dict.fromkeys(required_capabilities))
    candidates: list[MathCheckBackend] = []
    for backend in BACKENDS.values():
        if not include_unavailable and not backend.is_available():
            continue
        if all(cap in backend.capabilities for cap in required):
            candidates.append(backend)
    if not candidates:
        return None

    if preferred:
        preferred_name = canonical_backend_name(preferred)
        for backend in candidates:
            if backend.name == preferred_name:
                return _backend_row(backend)

    candidates.sort(key=lambda b: (-b.priority, b.name))
    return _backend_row(candidates[0])


def build_verification_record(
    required_capabilities: Iterable[str],
    preferred: str | None = None,
    text: str | Iterable[str] | None = None,
    include_unavailable: bool = False,
) -> dict:
    """Build a schema-friendly verification record for a math-check task."""
    required = list(dict.fromkeys(required_capabilities))
    selected = select_backend(
        required_capabilities=required,
        preferred=preferred,
        include_unavailable=include_unavailable,
    )
    available_names = [row["name"] for row in list_backends(include_unavailable=False)]
    math_style = infer_math_style(text)
    notes: list[str] = []
    strategy = ["symbolic", "numeric"]
    if math_style in {"PATAMATHEMATICAL", "HYBRID"}:
        notes.append(
            "Metaphor-heavy math detected; prefer restatement to invariants plus cross-checks."
        )
        strategy = ["symbolic", "numeric", "manual-invariant-restatement"]

    record = {
        "verification_basis": "OBSERVED" if selected and selected["available"] else "DECLARED",
        "verification_method": selected["verification_method"] if selected else None,
        "required_capabilities": required,
        "selected_backend": selected["name"] if selected else None,
        "available_backends": available_names,
        "math_style": math_style,
        "recommended_strategy": strategy,
        "notes": notes,
    }
    if len(available_names) > 1 and selected:
        record["verification_basis"] = "CROSS_CHECKED"
    return record


def _backend_row(backend: MathCheckBackend) -> dict:
    row = asdict(backend)
    row["available"] = backend.is_available()
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description="Math-check backend registry layer")
    sub = parser.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list", help="List known math-check backends")
    p_list.add_argument("--all", action="store_true", help="Include unavailable backends")

    p_select = sub.add_parser("select", help="Choose a backend for required capabilities")
    p_select.add_argument("--require", nargs="+", required=True, metavar="CAPABILITY")
    p_select.add_argument("--prefer", help="Preferred backend name or alias")
    p_select.add_argument("--all", action="store_true", help="Allow unavailable candidates")

    p_record = sub.add_parser("record", help="Build a verification record")
    p_record.add_argument("--require", nargs="+", required=True, metavar="CAPABILITY")
    p_record.add_argument("--prefer", help="Preferred backend name or alias")
    p_record.add_argument("--text", help="Optional text/tags for math-style inference")
    p_record.add_argument("--all", action="store_true", help="Allow unavailable candidates")

    args = parser.parse_args()

    if args.cmd == "list":
        print(json.dumps(list_backends(include_unavailable=args.all), indent=2))
    elif args.cmd == "select":
        print(
            json.dumps(
                select_backend(
                    required_capabilities=args.require,
                    preferred=args.prefer,
                    include_unavailable=args.all,
                ),
                indent=2,
            )
        )
    elif args.cmd == "record":
        print(
            json.dumps(
                build_verification_record(
                    required_capabilities=args.require,
                    preferred=args.prefer,
                    text=args.text,
                    include_unavailable=args.all,
                ),
                indent=2,
            )
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
