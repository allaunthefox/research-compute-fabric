#!/usr/bin/env python3
"""Probe optional science tools without requiring them.

The goal is not to make these tools part of the default stack. The goal is to
let agents and CI-adjacent smoke checks discover which reference solvers,
format adapters, and verification backends are available on the current host.

Exit code:
    0  probe completed; missing optional tools are reported in the payload.
    2  invalid CLI arguments or unable to write output.
"""
from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PythonTool:
    key: str
    domain: str
    module: str
    purpose: str


@dataclass(frozen=True)
class CommandTool:
    key: str
    domain: str
    command: str
    purpose: str
    version_args: tuple[str, ...] = ("--version",)


PYTHON_TOOLS: tuple[PythonTool, ...] = (
    PythonTool(
        "biopython",
        "genetics",
        "Bio",
        "FASTA/FASTQ/GenBank parsing and sequence manipulation",
    ),
    PythonTool("pysam", "genetics", "pysam", "SAM/BAM/CRAM/VCF access from Python"),
    PythonTool(
        "rdkit",
        "chemistry",
        "rdkit",
        "SMILES parsing, canonicalization, descriptors, fingerprints",
    ),
    PythonTool("z3-solver", "formal-methods", "z3", "SMT checks before Lean proof work"),
    PythonTool("cvc5", "formal-methods", "cvc5", "SMT checks and model finding"),
    PythonTool(
        "pycryptodome",
        "cryptography",
        "Crypto",
        "hash/signature/cipher reference primitives",
    ),
    PythonTool("galois", "cryptography", "galois", "finite-field arithmetic"),
    PythonTool(
        "networkx",
        "graph-theory",
        "networkx",
        "graph certificates and topology receipts",
    ),
    PythonTool(
        "pywavelets",
        "signal-processing",
        "pywt",
        "wavelet decompositions for spectral receipts",
    ),
    PythonTool(
        "zstandard",
        "compression",
        "zstandard",
        "zstd baseline and dictionary-training adapter",
    ),
    PythonTool("dedalus", "cfd-pde", "dedalus", "spectral PDE reference solver"),
    PythonTool(
        "liboqs-python",
        "cryptography",
        "oqs",
        "Open Quantum Safe KEM/signature reference adapter",
    ),
)

COMMAND_TOOLS: tuple[CommandTool, ...] = (
    CommandTool(
        "samtools",
        "genetics",
        "samtools",
        "SAM/BAM/CRAM command-line verification",
    ),
    CommandTool("bcftools", "genetics", "bcftools", "VCF/BCF command-line verification"),
    CommandTool("minimap2", "genetics", "minimap2", "sequence alignment smoke checks"),
    CommandTool(
        "sage",
        "algebra-crypto",
        "sage",
        "lattice, group, and symbolic mathematics",
        ("--version",),
    ),
    CommandTool("gap", "algebra", "gap", "computational group-theory checks", ("--version",)),
    CommandTool("z3", "formal-methods", "z3", "SMT solver CLI", ("--version",)),
    CommandTool("cvc5", "formal-methods", "cvc5", "SMT solver CLI", ("--version",)),
    CommandTool("zstd", "compression", "zstd", "compression baseline CLI", ("--version",)),
    CommandTool("dot", "graph-theory", "dot", "Graphviz graph rendering for witness diagrams", ("-V",)),
    CommandTool("obabel", "chemistry", "obabel", "Open Babel format conversion", ("-V",)),
    CommandTool("paraview", "cfd-pde", "paraview", "CFD/PDE visualization frontend", ("--version",)),
)


def _module_version(module: Any) -> str | None:
    for attr in ("__version__", "VERSION", "version"):
        value = getattr(module, attr, None)
        if value is None:
            continue
        if callable(value):
            try:
                value = value()
            except Exception:
                continue
        return str(value)
    return None


def _probe_python(tool: PythonTool) -> dict[str, Any]:
    try:
        module = importlib.import_module(tool.module)
    except Exception as exc:
        return {
            **asdict(tool),
            "available": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {
        **asdict(tool),
        "available": True,
        "version": _module_version(module),
        "path": getattr(module, "__file__", None),
    }


def _run_version(path: str, args: tuple[str, ...]) -> str | None:
    try:
        result = subprocess.run(
            [path, *args],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return None
    text = (result.stdout or result.stderr).strip()
    if not text:
        return None
    return text.splitlines()[0]


def _probe_command(tool: CommandTool) -> dict[str, Any]:
    path = shutil.which(tool.command)
    if path is None:
        return {
            **asdict(tool),
            "available": False,
        }
    return {
        **asdict(tool),
        "available": True,
        "path": path,
        "version": _run_version(path, tool.version_args),
    }


def build_report() -> dict[str, Any]:
    python_results = [_probe_python(tool) for tool in PYTHON_TOOLS]
    command_results = [_probe_command(tool) for tool in COMMAND_TOOLS]
    available = sum(1 for item in python_results + command_results if item["available"])
    total = len(python_results) + len(command_results)
    by_domain: dict[str, dict[str, int]] = {}
    for item in python_results + command_results:
        bucket = by_domain.setdefault(item["domain"], {"available": 0, "total": 0})
        bucket["total"] += 1
        if item["available"]:
            bucket["available"] += 1
    return {
        "schema": "research_stack_optional_science_toolbelt_probe_v1",
        "summary": {
            "available": available,
            "total": total,
            "by_domain": by_domain,
        },
        "python": python_results,
        "commands": command_results,
    }


def _print_text(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print(f"optional science toolbelt: {summary['available']}/{summary['total']} available")
    for section in ("python", "commands"):
        print(f"\n{section}:")
        for item in report[section]:
            mark = "OK" if item["available"] else "--"
            version = item.get("version")
            suffix = f" ({version})" if version else ""
            print(f"  {mark} {item['key']}: {item['purpose']}{suffix}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument("--out", type=Path, help="write the JSON report to this path")
    args = parser.parse_args(argv)

    report = build_report()
    if args.out:
        try:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            print(f"error: failed to write {args.out}: {exc}", file=sys.stderr)
            return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
