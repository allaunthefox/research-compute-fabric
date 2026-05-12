#!/usr/bin/env python3
"""Math/logogram compression surface builder.

Surface-1 is the host-side bridge between:

  LaTeX / symbolic logogram strings
      -> canonical token/display cells
      -> compressed bank-local glyph payload
      -> Tang-compatible substitution receipt
      -> n-space/eigen/metaprobe curriculum rows

The canonicalizer is deliberately small and deterministic. RaTeX is recorded as
the preferred future Rust renderer/canonicalizer, but this script does not need
RaTeX checked out to produce receipts today.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zlib
from collections import Counter
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(
    r"(\\[A-Za-z]+|\\.|[A-Za-z]+|[0-9]+|[{}_^=+\-*/(),;:\[\]<>|]|[^\s])"
)

COMMAND_GLYPHS = {
    "\\frac": 0x21,
    "\\sqrt": 0x22,
    "\\int": 0x23,
    "\\sum": 0x24,
    "\\partial": 0x25,
    "\\nabla": 0x26,
    "\\Delta": 0x27,
    "\\in": 0x28,
    "\\Rightarrow": 0x29,
    "\\neg": 0x2A,
    "\\cap": 0x2B,
    "\\ce": 0x2C,
    "\\pu": 0x2D,
}

SYMBOL_GLYPHS = {
    "{": 0x30,
    "}": 0x31,
    "_": 0x32,
    "^": 0x33,
    "=": 0x34,
    "+": 0x35,
    "-": 0x36,
    "*": 0x37,
    "/": 0x38,
    "(": 0x39,
    ")": 0x3A,
    ",": 0x3B,
    ";": 0x3C,
    ":": 0x3D,
    "<": 0x3E,
    ">": 0x3F,
    "|": 0x40,
}


DEFAULT_SAMPLES = [
    {
        "id": "quadratic_formula",
        "kind": "latex_math",
        "source": r"\frac{-b \pm \sqrt{b^2-4ac}}{2a}",
    },
    {
        "id": "pde_residual",
        "kind": "latex_math",
        "source": r"\partial_t u + u \partial_x u - \nu \partial_{xx} u = 0",
    },
    {
        "id": "metaglyph_fold",
        "kind": "symbolic_logogram",
        "source": r"A \cap B \Rightarrow fold(A,B)",
    },
    {
        "id": "semantic_tear",
        "kind": "symbolic_logogram",
        "source": r"torsion(A,B) > max \Rightarrow tear(A,B)",
    },
    {
        "id": "mhchem_surface",
        "kind": "latex_chem",
        "source": r"\ce{H2SO4 + 2NaOH -> Na2SO4 + 2H2O}",
    },
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonicalize(source: str) -> dict[str, Any]:
    tokens = TOKEN_RE.findall(source)
    canonical = " ".join(tokens)
    cells = []
    stack_depth = 0
    for index, token in enumerate(tokens):
        if token == "{":
            stack_depth += 1
        elif token == "}":
            stack_depth = max(0, stack_depth - 1)
        if token.startswith("\\"):
            token_kind = "command"
        elif token.isalpha():
            token_kind = "identifier"
        elif token.isdigit():
            token_kind = "number"
        else:
            token_kind = "symbol"
        cells.append(
            {
                "index": index,
                "kind": token_kind,
                "token": token,
                "depth": stack_depth,
                "glyph_id": glyph_id(token),
            }
        )
    return {
        "canonical": canonical,
        "canonical_hash": sha256_text(canonical),
        "token_count": len(tokens),
        "cells": cells,
        "cell_hash": sha256_text(json.dumps(cells, sort_keys=True, ensure_ascii=False)),
    }


def glyph_id(token: str) -> int:
    if token in COMMAND_GLYPHS:
        return COMMAND_GLYPHS[token]
    if token in SYMBOL_GLYPHS:
        return SYMBOL_GLYPHS[token]
    if len(token) == 1:
        return ord(token) & 0x7F
    digest = hashlib.blake2s(token.encode("utf-8"), digest_size=1).digest()[0]
    return 0x80 | (digest & 0x7F)


def pack_glyph_payload(cells: list[dict[str, Any]], max_len: int = 16) -> bytes:
    return bytes(int(cell["glyph_id"]) & 0xFF for cell in cells[:max_len])


def substitution_receipt(payload: bytes) -> dict[str, Any]:
    # Same hot-path substitution model as tang9k_hutter_symbol_surface.py, kept
    # local to avoid import-path surprises in shim execution.
    table = {
        ord(" "): 0x0,
        ord("e"): 0x1,
        ord("E"): 0x1,
        ord("t"): 0x2,
        ord("T"): 0x2,
        ord("a"): 0x3,
        ord("A"): 0x3,
        ord("o"): 0x4,
        ord("O"): 0x4,
        ord("i"): 0x5,
        ord("I"): 0x5,
        ord("n"): 0x6,
        ord("N"): 0x6,
        ord("s"): 0x7,
        ord("S"): 0x7,
        ord("r"): 0x8,
        ord("R"): 0x8,
        ord("h"): 0x9,
        ord("H"): 0x9,
        ord("l"): 0xA,
        ord("L"): 0xA,
        ord("d"): 0xB,
        ord("c"): 0xC,
        ord("C"): 0xC,
        ord("u"): 0xD,
        ord("U"): 0xD,
        ord("F"): 0xE,
        ord("D"): 0xF,
    }
    rolling_hash = 0xACE1
    mapped = 0
    literal = 0
    for byte in payload:
        hit = byte in table
        code = table[byte] if hit else byte & 0x0F
        rolling_hash = (((rolling_hash << 1) & 0xFFFF) | (rolling_hash >> 15)) ^ (
            (0x10 if hit else 0x00) | code
        )
        mapped += 1 if hit else 0
        literal += 0 if hit else 1
    return {
        "schema": "surface1_substitution_receipt_v1",
        "hash16": rolling_hash,
        "mapped_count": mapped,
        "literal_count": literal,
    }


def classify_regime(canonical: str, cells: list[dict[str, Any]]) -> str:
    lowered = canonical.lower()
    if "tear" in lowered or "torsion" in lowered or "contradiction" in lowered:
        return "horrible_manifold_tearing"
    if "fold" in lowered or "\\cap" in lowered or "\\rightarrow" in lowered or "\\rightarrow" in lowered:
        return "beautiful_topological_folding"
    command_count = sum(1 for cell in cells if cell["kind"] == "command")
    if command_count >= 2 or len(cells) > 20:
        return "ugly_asymmetric_pruning"
    return "beautiful_topological_folding"


def compression_metrics(source: str, canonical: str, payload: bytes) -> dict[str, Any]:
    raw = source.encode("utf-8")
    canonical_bytes = canonical.encode("utf-8")
    z_raw = zlib.compress(raw, level=9)
    return {
        "raw_bytes": len(raw),
        "canonical_bytes": len(canonical_bytes),
        "surface_payload_bytes": len(payload),
        "zlib_raw_bytes": len(z_raw),
        "payload_over_raw": len(payload) / (len(raw) or 1),
        "payload_over_canonical": len(payload) / (len(canonical_bytes) or 1),
    }


def load_terms(path: Path) -> list[str]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [str(item.get("term")) for item in data.get("top_terms", [])[:16]]


def build_sample_record(sample: dict[str, str], eigen_terms: list[str]) -> dict[str, Any]:
    source = sample["source"]
    canon = canonicalize(source)
    payload = pack_glyph_payload(canon["cells"])
    metrics = compression_metrics(source, canon["canonical"], payload)
    token_counts = Counter(cell["kind"] for cell in canon["cells"])
    return {
        "id": sample["id"],
        "kind": sample["kind"],
        "source": source,
        "source_hash": sha256_text(source),
        "canonical": canon["canonical"],
        "canonical_hash": canon["canonical_hash"],
        "cell_hash": canon["cell_hash"],
        "token_count": canon["token_count"],
        "token_kind_counts": dict(token_counts),
        "display_cells": canon["cells"],
        "surface_payload_hex": payload.hex(),
        "surface_payload_len": len(payload),
        "substitution_receipt": substitution_receipt(payload),
        "compression_metrics": metrics,
        "semantic_regime": classify_regime(canon["canonical"], canon["cells"]),
        "route_terms": eigen_terms[:8],
    }


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = "You are a math/logogram surface compiler. Return compact JSON with receipt boundaries."
    records = []
    for sample in receipt["samples"]:
        prompt = {
            "task": "compile_math_logogram_surface",
            "id": sample["id"],
            "source": sample["source"],
            "route_terms": sample["route_terms"],
            "instruction": "Compile this into canonical cells, compressed payload, and semantic regime.",
        }
        answer = {
            "selected": True,
            "claim_boundary": "surface-compiler-receipt-only",
            "canonical_hash": sample["canonical_hash"],
            "cell_hash": sample["cell_hash"],
            "surface_payload_hex": sample["surface_payload_hex"],
            "semantic_regime": sample["semantic_regime"],
            "compression_metrics": sample["compression_metrics"],
            "receipt_hash16": sample["substitution_receipt"]["hash16"],
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


def load_samples(path: Path | None) -> list[dict[str, str]]:
    if not path:
        return DEFAULT_SAMPLES
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return data.get("samples", DEFAULT_SAMPLES)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=Path)
    parser.add_argument("--eigen", type=Path, default=Path("4-Infrastructure/shim/nspace_semantic_pde_eigenvectors.json"))
    parser.add_argument("--receipt", type=Path, default=Path("4-Infrastructure/shim/math_logogram_surface_receipt.json"))
    parser.add_argument("--curriculum", type=Path, default=Path("4-Infrastructure/shim/math_logogram_surface_curriculum.jsonl"))
    args = parser.parse_args()

    eigen_terms = load_terms(args.eigen)
    samples = [build_sample_record(sample, eigen_terms) for sample in load_samples(args.samples)]
    receipt = {
        "schema": "math_logogram_surface_receipt_v1",
        "claim_boundary": "Surface compiler canonicalizes and compresses symbolic strings; it does not prove math or chemistry claims.",
        "canonicalizer": "deterministic_python_surface1",
        "preferred_future_canonicalizer": "RaTeX Rust display-list core",
        "eigen_source": str(args.eigen),
        "sample_count": len(samples),
        "samples": samples,
        "lawful": all(sample["surface_payload_len"] <= 16 for sample in samples),
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(receipt):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
