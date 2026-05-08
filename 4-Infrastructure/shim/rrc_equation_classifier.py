#!/usr/bin/env python3
"""Project local equation surfaces through the Rainbow Raccoon Compiler.

This is a routing/projection pass, not a proof pass.  It converts equation
records into RRC objects and lets the existing manifold-indexed compiler select
a nearest lawful shape.  The important artifact is the coordinate/witness
surface, not a human taxonomy label.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
OUT = SHIM / "rrc_equation_classifier_receipt.json"
CURRICULUM = SHIM / "rrc_equation_classifier_curriculum.jsonl"
SUMMARY = REPO / "docs" / "rrc_equation_classification.md"
TABLE = SHIM / "rrc_equation_classifier_table.csv"


@dataclass(frozen=True)
class EquationRecord:
    equation_id: str
    name: str
    equation: str
    source_path: str
    family: str
    purpose: str = ""
    domain_type: str = ""
    bind_class: str = ""


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_rrc_module() -> Any:
    path = SHIM / "rainbow_raccoon_compiler.py"
    spec = importlib.util.spec_from_file_location("rainbow_raccoon_compiler", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load RRC module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def clean_text(value: Any) -> str:
    return str(value or "").replace("\x00", "").strip()


def read_math_model_map(limit: int | None) -> list[EquationRecord]:
    path = REPO / "3-Mathematical-Models" / "MATH_MODEL_MAP.tsv"
    if not path.exists():
        return []
    records: list[EquationRecord] = []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            if not row:
                continue
            name = clean_text(row.get("Model_Name")) or f"math_model_{len(records)}"
            equation = clean_text(row.get("Equation"))
            if not equation:
                continue
            records.append(
                EquationRecord(
                    equation_id=f"math_model_map:{clean_text(row.get('#')) or len(records)}",
                    name=name,
                    equation=equation,
                    source_path=rel(path),
                    family=clean_text(row.get("Family")),
                    purpose=clean_text(row.get("Purpose")),
                    domain_type=clean_text(row.get("Domain_Type")),
                    bind_class=clean_text(row.get("Bind_Class")),
                )
            )
            if limit is not None and len(records) >= limit:
                break
    return records


def read_equations_jsonl(path: Path, limit: int | None) -> list[EquationRecord]:
    if not path.exists():
        return []
    records: list[EquationRecord] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if limit is not None and len(records) >= limit:
                break
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            equation = clean_text(row.get("equation") or row.get("normalized"))
            if not equation:
                continue
            records.append(
                EquationRecord(
                    equation_id=clean_text(row.get("equation_id")) or f"{path.name}:{len(records)}",
                    name=clean_text(row.get("name")) or clean_text(row.get("source")) or "extracted_equation",
                    equation=equation,
                    source_path=rel(path),
                    family=clean_text(row.get("type")) or "extracted",
                    purpose=clean_text(row.get("source_type")),
                )
            )
    return records


def read_extracted_markdown(limit: int | None) -> list[EquationRecord]:
    path = REPO / "3-Mathematical-Models" / "extracted_equations.md"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    records: list[EquationRecord] = []
    for idx, match in enumerate(re.finditer(r"```(?:[A-Za-z0-9_+-]+)?\n(.*?)```", text, re.DOTALL)):
        equation = clean_text(match.group(1))
        if not equation or "\n" in equation and len(equation.splitlines()) > 6:
            continue
        records.append(
            EquationRecord(
                equation_id=f"extracted_md:{idx}",
                name=f"extracted_md_equation_{idx}",
                equation=equation,
                source_path=rel(path),
                family="markdown_extracted",
                purpose="fenced equation block",
            )
        )
        if limit is not None and len(records) >= limit:
            break
    return records


def read_recent_receipt_equations() -> list[EquationRecord]:
    receipt_paths = [
        SHIM / "connectome_protective_cognitive_load_reweighting_receipt.json",
        SHIM / "transfold_enwiki8_magnetic_domain_generator_receipt.json",
        SHIM / "transfold_couch_data_magnetic_domain_receipt.json",
        SHIM / "merkle_tensegrity_load_equation_receipt.json",
        SHIM / "hutter_equation_metastate_transfold_receipt.json",
    ]
    records: list[EquationRecord] = []
    for path in receipt_paths:
        if not path.exists():
            continue
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        candidate_maps = []
        for key in ("core_equations", "transfold_map", "hutter_transfold_equations"):
            value = receipt.get(key)
            if isinstance(value, dict):
                candidate_maps.append((key, value))
        if isinstance(receipt.get("transfold_map"), dict):
            core = receipt["transfold_map"].get("core_equations")
            if isinstance(core, dict):
                candidate_maps.append(("transfold_core_equations", core))
        for group, mapping in candidate_maps:
            for name, equation in mapping.items():
                if isinstance(equation, (dict, list)):
                    equation_text = stable_json(equation)
                else:
                    equation_text = clean_text(equation)
                if not equation_text:
                    continue
                records.append(
                    EquationRecord(
                        equation_id=f"{path.stem}:{group}:{name}",
                        name=name,
                        equation=equation_text,
                        source_path=rel(path),
                        family=clean_text(receipt.get("schema")) or "receipt_equation",
                        purpose=clean_text(receipt.get("purpose") or receipt.get("primary_read")),
                    )
                )
    return records


def route_hint(record: EquationRecord) -> str:
    """Non-authoritative hint used only to choose an initial RRC kind prior."""
    text = " ".join(
        [record.name, record.equation, record.family, record.purpose, record.domain_type, record.bind_class]
    ).lower()
    checks = [
        ("cognitive_load", ["cognitive", "load", "overflow", "emotional"]),
        ("magnetic_signal", ["magnetic", "magnetization", "susceptibility", "remanence", "h_field"]),
        ("compression_route", ["compression", "bytes", "bpb", "hutter", "codec", "decode"]),
        ("geometry_topology", ["geometry", "topology", "manifold", "geodesic", "metric", "curvature"]),
        ("cad_force", ["force", "stress", "tensegrity", "equilibrium", "stiffness", "load vector"]),
        ("thermodynamic_energy", ["thermo", "entropy", "energy", "heat", "temperature", "landauer"]),
        ("control_signal", ["control", "gate", "threshold", "risk", "feedback", "actuator"]),
        ("chaotic_couch", ["couch", "chaotic", "oscillator", "hysteresis", "kappa"]),
        ("electromagnetic_field", ["electromagnetic", "muon", "magnetic moment", "lorentz", "photon"]),
        ("transfold", ["transfold", "projection", "source_domain", "target_domain"]),
    ]
    scores = []
    for label, terms in checks:
        hits = sum(1 for term in terms if term in text)
        scores.append((hits, label))
    scores.sort(reverse=True)
    return scores[0][1] if scores and scores[0][0] > 0 else "unclassified_equation"


def rrc_kind_for_record(record: EquationRecord, hint: str) -> str:
    bind = record.bind_class.lower()
    domain = record.domain_type.lower()
    text = f"{record.name} {record.equation} {record.family} {record.purpose}".lower()
    if hint in {"compression_route", "magnetic_signal", "transfold"} or "compression" in domain:
        return "compression_route_prior"
    if hint in {"geometry_topology", "cad_force"} or "geometric" in bind:
        return "cad_force_receipt" if hint == "cad_force" else "geometry_topology_receipt"
    if hint == "cognitive_load":
        return "cognitive_field_receipt"
    if "receipt" in text or "hash" in text:
        return "logogram_projection"
    if hint == "unclassified_equation":
        return "negative_control"
    return "cognitive_field_receipt" if hint in {"control_signal", "thermodynamic_energy"} else "compression_route_prior"


def record_payload(record: EquationRecord, hint: str) -> str:
    payload = {
        "equation_id": record.equation_id,
        "name": record.name,
        "equation": record.equation,
        "family": record.family,
        "purpose": record.purpose,
        "domain_type": record.domain_type,
        "bind_class": record.bind_class,
        "route_hint_non_authoritative": hint,
        "projection": "equation_text_to_rrc_manifold_axes",
        "decoder": "source_path plus equation_id plus equation text",
        "witness": "rrc_equation_classifier_receipt",
        "scale_band": "bounded text equation sample; no proof claim",
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=True)


def project_records(records: list[EquationRecord], sample_limit: int | None) -> dict[str, Any]:
    rrc = load_rrc_module()
    if sample_limit is not None:
        records = records[:sample_limit]
    compiled = []
    for record in records:
        hint = route_hint(record)
        kind = rrc_kind_for_record(record, hint)
        obj = rrc.RRCObject(
            object_id=f"rrc_eq_{sha256_text(record.equation_id)[:16]}",
            label=record.name,
            kind=kind,
            payload=record_payload(record, hint),
            source_path=record.source_path,
        )
        item = rrc.compile_object(obj)
        coords = item["manifold_projection"]["coordinates"]
        ranked_axes = sorted(coords.items(), key=lambda kv: kv[1], reverse=True)
        item["equation_record"] = {
            "equation_id": record.equation_id,
            "name": record.name,
            "equation": record.equation,
            "source_path": record.source_path,
            "family": record.family,
            "purpose": record.purpose,
            "domain_type": record.domain_type,
            "bind_class": record.bind_class,
            "route_hint_non_authoritative": hint,
            "rrc_kind": kind,
            "projection_signature": {
                "top_axes": ranked_axes[:4],
                "weak_axes": [axis for axis, value in coords.items() if value < 0.35],
                "shape_distance": item["nearest_lawful_shape"]["distance"],
            },
        }
        item["invariant_receipt"]["receipt_hash"] = sha256_text(stable_json(item))
        compiled.append(item)
    return {
        "compiled_equations": compiled,
        "counts": summarize(compiled),
    }


def summarize(compiled: list[dict[str, Any]]) -> dict[str, Any]:
    by_shape: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_missing_axis: dict[str, int] = {}
    for item in compiled:
        shape = item["nearest_lawful_shape"]["shape"]
        status = item["type_witness"]["status"]
        by_shape[shape] = by_shape.get(shape, 0) + 1
        by_status[status] = by_status.get(status, 0) + 1
        for axis in item["type_witness"].get("missing_or_weak_axes", []):
            by_missing_axis[axis] = by_missing_axis.get(axis, 0) + 1
    return {
        "equation_count": len(compiled),
        "by_rrc_shape": dict(sorted(by_shape.items())),
        "by_status": dict(sorted(by_status.items())),
        "by_missing_axis": dict(sorted(by_missing_axis.items())),
    }


def build_records(args: argparse.Namespace) -> list[EquationRecord]:
    records: list[EquationRecord] = []
    records.extend(read_recent_receipt_equations())
    records.extend(read_math_model_map(args.math_map_limit))
    records.extend(read_extracted_markdown(args.markdown_limit))
    for path in args.jsonl:
        records.extend(read_equations_jsonl(Path(path), args.jsonl_limit))

    seen: set[str] = set()
    unique: list[EquationRecord] = []
    for record in records:
        key = sha256_text(record.equation + "|" + record.source_path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique


def write_curriculum(receipt: dict[str, Any]) -> None:
    rows = []
    for item in receipt["compiled_equations"]:
        rows.append(
            {
                "prompt": {
                    "task": "project_equation_via_rrc",
                    "equation_id": item["equation_record"]["equation_id"],
                    "equation": item["equation_record"]["equation"],
                },
                "completion": {
                    "rrc_shape": item["nearest_lawful_shape"]["shape"],
                    "status": item["type_witness"]["status"],
                    "projection_signature": item["equation_record"]["projection_signature"],
                    "receipt_hash": item["invariant_receipt"]["receipt_hash"],
                },
            }
        )
    CURRICULUM.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_summary(receipt: dict[str, Any]) -> None:
    counts = receipt["counts"]
    lines = [
        "# RRC Equation Projection",
        "",
        "This is a Rainbow Raccoon Compiler projection pass over local equation surfaces.",
        "It records nearest lawful shapes, projection axes, and admissibility holds; it is not a proof of the equations.",
        "",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        f"Equation count: `{counts['equation_count']}`",
        "",
        "## Counts By RRC Shape",
        "",
        "| RRC shape | Count |",
        "|---|---:|",
    ]
    for key, value in counts["by_rrc_shape"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(["", "## Missing Axes", "", "| Axis | Count |", "|---|---:|"])
    for key, value in counts["by_missing_axis"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(["", "## Sample Projections", "", "| Equation | RRC shape | Status | Top axes |", "|---|---|---|---|"])
    for item in receipt["compiled_equations"][:24]:
        record = item["equation_record"]
        name = record["name"].replace("|", "/")
        top_axes = ", ".join(axis for axis, _value in record["projection_signature"]["top_axes"])
        lines.append(
            f"| `{name}` | `{item['nearest_lawful_shape']['shape']}` | "
            f"`{item['type_witness']['status']}` | `{top_axes}` |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            receipt["claim_boundary"],
            "",
        ]
    )
    SUMMARY.write_text("\n".join(lines), encoding="utf-8")


def write_table(receipt: dict[str, Any]) -> None:
    with TABLE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "equation_id",
                "name",
                "rrc_shape",
                "status",
                "distance",
                "top_axes",
                "missing_or_weak_axes",
                "source_path",
                "domain_type",
                "bind_class",
                "equation",
            ],
        )
        writer.writeheader()
        for item in receipt["compiled_equations"]:
            record = item["equation_record"]
            writer.writerow(
                {
                    "equation_id": record["equation_id"],
                    "name": record["name"],
                    "rrc_shape": item["nearest_lawful_shape"]["shape"],
                    "status": item["type_witness"]["status"],
                    "distance": item["nearest_lawful_shape"]["distance"],
                    "top_axes": ";".join(
                        axis for axis, _value in record["projection_signature"]["top_axes"]
                    ),
                    "missing_or_weak_axes": ";".join(
                        item["type_witness"].get("missing_or_weak_axes", [])
                    ),
                    "source_path": record["source_path"],
                    "domain_type": record["domain_type"],
                    "bind_class": record["bind_class"],
                    "equation": record["equation"],
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--math-map-limit", type=int, default=120)
    parser.add_argument("--markdown-limit", type=int, default=40)
    parser.add_argument("--jsonl-limit", type=int, default=80)
    parser.add_argument("--sample-limit", type=int)
    parser.add_argument(
        "--jsonl",
        action="append",
        default=[str(REPO / "3-Mathematical-Models" / "equations_100" / "equations_database.jsonl")],
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = build_records(args)
    projected = project_records(records, args.sample_limit)
    receipt = {
        "schema": "rrc_equation_projector_v1",
        "runner": rel(Path(__file__).resolve()),
        "source_inputs": {
            "math_model_map_limit": args.math_map_limit,
            "markdown_limit": args.markdown_limit,
            "jsonl_limit": args.jsonl_limit,
            "sample_limit": args.sample_limit,
            "jsonl": [rel(Path(p)) for p in args.jsonl],
        },
        "counts": projected["counts"],
        "compiled_equations": projected["compiled_equations"],
        "claim_boundary": (
            "RRC equation projection is an admissibility and routing pass. Human labels "
            "are non-authoritative hints only; CANDIDATE means suitable for next-stage "
            "checking, not mathematically proved."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    write_curriculum(receipt)
    write_summary(receipt)
    write_table(receipt)
    print(
        json.dumps(
            {
                "receipt": rel(OUT),
                "summary": rel(SUMMARY),
                "curriculum": rel(CURRICULUM),
                "table": rel(TABLE),
                "receipt_hash": receipt["receipt_hash"],
                "counts": receipt["counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
