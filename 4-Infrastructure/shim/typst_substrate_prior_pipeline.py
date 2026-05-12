#!/usr/bin/env python3
"""Build a receipt-backed Typst report from recent substrate-prior tiddlers.

The pipeline always emits a `.typ` source and JSON receipt. If the `typst` CLI
is available, it also compiles a PDF and records the output hash. This keeps
the document surface useful even on machines where Typst is not installed yet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
WIKI = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers"
OUT_DIR = REPO / "6-Documentation" / "reports" / "typst"
LOCAL_TYPST = REPO / "5-Applications" / "tools-scripts" / "external" / "typst-cli" / "bin" / "typst"
SUPPORT_FILES = [
    OUT_DIR / "omindirection.typ",
    OUT_DIR / "logogram-bidi.typ",
    REPO / "typst" / "otom-style" / "finance-math.typ",
    REPO / "typst" / "otom-style" / "main.typ",
    REPO / "typst" / "registries" / "finance-registry.typ",
    REPO / "typst" / "registries" / "claim-taxonomy.typ",
    REPO / "typst" / "registries" / "debt-taxonomy.typ",
    REPO / "typst" / "registries" / "risk-taxonomy.typ",
    REPO / "typst" / "registries" / "accounting-taxonomy.typ",
    REPO / "typst" / "registries" / "monetary-taxonomy.typ",
    REPO / "typst" / "registries" / "symbology-typesetting-lut.typ",
]


DEFAULT_TIDDLERS = [
    "Erdos Four Primitive Diagnostics.tid",
    "Erdos DAG FAMM Investigation.tid",
    "Erdos DAG FAMM Historical Run Note.tid",
    "Four Primitive FPGA Acceleration Research.tid",
    "Quandela Noise Residual Shaver.tid",
    "Thermodynamic Computing Surface Prior.tid",
    "Biological Reservoir Surface Prior.tid",
    "Monocurl Interactive Math Animation Prior.tid",
    "Typst Math Typesetting Surface Prior.tid",
    "Typst Universe Useful Package Sweep.tid",
    "Typst Auto Bidi Dense Flow Prior.tid",
    "Typst Omindirection Plugin Surface.tid",
    "Typst Logogram Bidi Layer.tid",
    "Typst WUBRG Color Code Prior.tid",
    "Typst Unify Units Package Prior.tid",
    "Typst Universe Package Registry Prior.tid",
    "Typst Typshade Bioalignment Package Prior.tid",
    "Typst Alchemist Molecule Package Prior.tid",
    "OpenClaw Shared Bus Surface.tid",
    "OpenClaw Capability Surface.tid",
    "Epigenetic Go-Tile Meta-Manifold.tid",
    "Hutter Static Target Omindirection Prior.tid",
    "PAQ Style Compression Review.tid",
    "Rehydratable Non-Core Rounding Prior.tid",
    "Omindirection Compression Concept Ledger.tid",
    "MathXML Domain Graph Import.tid",
    "Finance Math OTOM Layer.tid",
    "Finance Claim LUT Compression Harness.tid",
    "Remote Compression Test Ladder.tid",
    "Virtual Baud Reconstruction Layer.tid",
    "Committee Jupyter Book Explanation Plan.tid",
    "Cursed Doom Goals.tid",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def parse_tiddler(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    header_text, _, body = text.partition("\n\n")
    fields = {}
    for line in header_text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    title = fields.get("title", path.stem)
    return {
        "path": str(path.relative_to(REPO)),
        "title": title,
        "tags": fields.get("tags", ""),
        "body": body.strip(),
        "sha256": file_hash(path),
    }


def strip_wiki_markup(text: str) -> str:
    text = text.replace("[[", "").replace("]]", "")
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text


def body_summary(body: str, limit: int = 1800) -> str:
    lines = []
    for raw in body.splitlines():
        line = raw.rstrip()
        if line.startswith("created:") or line.startswith("modified:"):
            continue
        lines.append(strip_wiki_markup(line))
    text = "\n".join(lines).strip()
    text = text.replace("```", "~~~")
    if len(text) <= limit:
        return text
    return text[:limit].rsplit("\n", 1)[0] + "\n..."


def typst_escape_text(text: str) -> str:
    replacements = {
        "\\": "\\\\",
        "#": "\\#",
        "$": "\\$",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def render_typst(tiddlers: list[dict[str, Any]], receipt_id: str) -> str:
    lines = [
        '#import "@preview/auto-bidi:0.1.0": *',
        '#import "@preview/unify:0.8.0": num, qty, numrange, qtyrange',
        '#import "omindirection.typ": omi-show, omi-atom, omi-flow, omi-mirror, omi-demo',
        '#import "logogram-bidi.typ": logogram-atom, logogram-flow, logogram-demo',
        '#set document(title: "Research Stack Substrate Prior Report")',
        '#set page(width: 8.5in, height: 11in, margin: 0.75in)',
        '#set text(size: 10pt)',
        '#set heading(numbering: "1.")',
        '#show: auto-dir.with(',
        '  detect-by: "auto",',
        '  hebrew-font: "Noto Sans Hebrew",',
        '  arab-font: "Noto Naskh Arabic",',
        '  english-font: ("New Computer Modern", "Libertinus Serif"),',
        '  base-font: "New Computer Modern",',
        ')',
        "",
        "= Research Stack Substrate Prior Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Receipt ID: `{receipt_id}`",
        "",
        "== Claim Boundary",
        "",
        "This report is a visualization and documentation artifact. It is not a theorem proof, solver certificate, hardware benchmark, QPU submission receipt, or biological-computing capability claim.",
        "",
        "== Source Tiddlers",
        "",
    ]
    for idx, item in enumerate(tiddlers, start=1):
        lines.append(f"{idx}. {typst_escape_text(item['title'])} -- `{item['sha256'][:16]}`")
    lines.extend(
        [
            "",
            "== Receipt Metrics",
            "",
            "These values are presentation examples copied from source notes or receipts; they are not new measurements.",
            "",
            "#table(",
            "  columns: (1fr, 1fr, 1fr),",
            "  [Metric], [Value], [Boundary],",
            "  [Historical FAMM engram strength], [$num(\"20.85\")$], [historical harness note],",
            "  [Historical FAMM delay diversity], [$num(\"3.00\")$], [historical harness note],",
            "  [Mollin-Walsh temporal density], [$qty(\"82.11\", \"percent\")$], [historical harness note],",
            "  [Quandela average noise shave score], [$num(\"0.6444444444444445\")$], [dry-run routing receipt],",
            "  [Conservative PCIe FPGA speedup], [$numrange(\"2\", \"20\")$], [hypothesis until measured],",
            ")",
            "",
            "== Omindirection Logogram Layer Smoke",
            "",
            "The following row is a presentation smoke for protected symbolic atoms under the repo-local `omindirection.typ` plugin surface.",
            "",
            "#omi-demo()",
            "",
            "== Notes",
            "",
        ]
    )
    for item in tiddlers:
        lines.extend(
            [
                f"=== {typst_escape_text(item['title'])}",
                "",
                f"Source: `{item['path']}`",
                "",
                f"Hash: `{item['sha256']}`",
                "",
                "```text",
                body_summary(item["body"]),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def find_typst() -> str | None:
    if LOCAL_TYPST.exists():
        return str(LOCAL_TYPST)
    return shutil.which("typst")


def run_typst(source: Path, pdf: Path) -> dict[str, Any]:
    typst = find_typst()
    if not typst:
        return {
            "compiled": False,
            "reason": "typst CLI not found on PATH",
            "typst_path": None,
            "typst_version": None,
            "pdf": str(pdf.relative_to(REPO)),
            "pdf_hash": None,
        }
    version_proc = subprocess.run([typst, "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    proc = subprocess.run([typst, "compile", str(source), str(pdf)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return {
        "compiled": proc.returncode == 0,
        "returncode": proc.returncode,
        "reason": None if proc.returncode == 0 else "typst compile failed",
        "typst_path": typst,
        "typst_version": version_proc.stdout.strip() or version_proc.stderr.strip(),
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:],
        "pdf": str(pdf.relative_to(REPO)),
        "pdf_hash": file_hash(pdf) if pdf.exists() and proc.returncode == 0 else None,
    }


def build_pipeline(tiddler_paths: list[Path], out_dir: Path) -> dict[str, Any]:
    tiddlers = [parse_tiddler(path) for path in tiddler_paths]
    source_hash_seed = json.dumps(
        [{"path": item["path"], "sha256": item["sha256"]} for item in tiddlers],
        sort_keys=True,
        ensure_ascii=False,
    )
    receipt_id = hashlib.sha256(source_hash_seed.encode("utf-8")).hexdigest()[:24]
    out_dir.mkdir(parents=True, exist_ok=True)
    typ_path = out_dir / "substrate_prior_report.typ"
    pdf_path = out_dir / "substrate_prior_report.pdf"
    typ_text = render_typst(tiddlers, receipt_id)
    typ_path.write_text(typ_text + "\n", encoding="utf-8")
    compile_result = run_typst(typ_path, pdf_path)
    return {
        "schema": "typst_substrate_prior_pipeline_receipt_v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "surface_id": "typst_substrate_prior_pipeline",
        "receipt_id": receipt_id,
        "source_tiddlers": [
            {"title": item["title"], "path": item["path"], "sha256": item["sha256"]}
            for item in tiddlers
        ],
        "source_count": len(tiddlers),
        "typst_support_files": [
            {"path": str(path.relative_to(REPO)), "sha256": file_hash(path)}
            for path in SUPPORT_FILES
            if path.exists()
        ],
        "typst_source": str(typ_path.relative_to(REPO)),
        "typst_source_hash": file_hash(typ_path),
        "compile": compile_result,
        "claim_boundary": (
            "Typst pipeline emits a documentation/report artifact only. It does not prove equations, "
            "validate hardware, submit jobs, or certify solver correctness."
        ),
        "lawful": True,
    }


def write_wiki(receipt: dict[str, Any], path: Path) -> None:
    lines = [
        "created: 20260507000000000",
        "modified: 20260507000000000",
        "tags: ResearchStack Typst Pipeline Reports SubstratePrior Receipts",
        "title: Substrate Prior Typst Pipeline",
        "type: text/vnd.tiddlywiki",
        "",
        "! Substrate Prior Typst Pipeline",
        "",
        "This tiddler records the pipeline that converts substrate-prior wiki cards into a receipt-backed Typst report source.",
        "",
        "Durable source: `4-Infrastructure/shim/typst_substrate_prior_pipeline.py`",
        "",
        f"Typst source: `{receipt['typst_source']}`",
        "",
        "Receipt: `4-Infrastructure/shim/typst_substrate_prior_pipeline_receipt.json`",
        "",
        "!! Compile Status",
        "",
        f"* Compiled: `{receipt['compile']['compiled']}`",
        f"* Reason: `{receipt['compile']['reason']}`",
        f"* Typst source hash: `{receipt['typst_source_hash']}`",
        f"* PDF hash: `{receipt['compile']['pdf_hash']}`",
        "",
        "!! Typst Support Files",
        "",
    ]
    for item in receipt.get("typst_support_files", []):
        lines.append(f"* `{item['path']}` -> `{item['sha256']}`")
    lines.extend([
        "!! Claim Boundary",
        "",
        receipt["claim_boundary"],
        "",
        "!! Sources",
        "",
    ])
    for item in receipt["source_tiddlers"]:
        lines.append(f"* [[{item['title']}]] -> `{item['sha256'][:16]}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = "You are a receipt-backed report router. Return compact JSON and never treat reports as proofs."
    prompt = {
        "task": "route_typst_report_surface",
        "surface_id": receipt["surface_id"],
        "source_count": receipt["source_count"],
        "typst_source": receipt["typst_source"],
        "compiled": receipt["compile"]["compiled"],
        "compile_reason": receipt["compile"]["reason"],
        "claim_boundary": receipt["claim_boundary"],
    }
    answer = {
        "selected": True,
        "use_as": "documentation_surface_prior",
        "surface_id": receipt["surface_id"],
        "typst_source": receipt["typst_source"],
        "typst_source_hash": receipt["typst_source_hash"],
        "compiled": receipt["compile"]["compiled"],
        "pdf_hash": receipt["compile"]["pdf_hash"],
        "claim_boundary": receipt["claim_boundary"],
        "receipt_rule": "Require source tiddler hashes, typst source hash, compile status, and PDF hash if compiled.",
    }
    return [
        {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
            ]
        }
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tiddler", type=Path, action="append")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--receipt", type=Path, default=SHIM / "typst_substrate_prior_pipeline_receipt.json")
    parser.add_argument("--curriculum", type=Path, default=SHIM / "typst_substrate_prior_pipeline_curriculum.jsonl")
    parser.add_argument("--wiki", type=Path, default=WIKI / "Substrate Prior Typst Pipeline.tid")
    args = parser.parse_args()

    tiddler_paths = args.tiddler or [WIKI / name for name in DEFAULT_TIDDLERS]
    missing = [str(path) for path in tiddler_paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing tiddlers: {missing}")

    receipt = build_pipeline(tiddler_paths, args.out_dir)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(receipt):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    write_wiki(receipt, args.wiki)
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
