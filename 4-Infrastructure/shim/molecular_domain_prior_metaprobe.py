#!/usr/bin/env python3
"""Molecular-domain metaprobe for the physics/math router.

This promotes chemistry from a generic Hugging Face registry tag into a
concrete computational surface: molecular graphs, bond matrices, spectra,
properties, units, provenance, and receipts. It deliberately avoids claiming
wet-lab validity from model/dataset priors.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REGISTRY = Path("shared-data/artifacts/chemical_bond_matrix_registry.md")
LOCAL_CHEMISTRY_DIR = Path("5-Applications/tools-scripts/chemistry")


MOLECULAR_AXES = [
    {
        "axis": "molecular_graph",
        "payload": ["atom_types", "bond_order", "formal_charge", "aromaticity", "stereochemistry"],
        "router_use": "graph_topology_and_symbolic_compression",
        "receipt_rule": "preserve canonical representation hash and source provenance",
    },
    {
        "axis": "bond_matrix",
        "payload": ["bond_length", "bond_angle", "dihedral", "force_constant", "coordinate_frame"],
        "router_use": "field/shear primitive over molecular geometry",
        "receipt_rule": "preserve units, method, basis/force-field name, and source database",
    },
    {
        "axis": "spectral_property",
        "payload": ["energy", "frequency", "dipole", "polarizability", "orbital_or_band_feature"],
        "router_use": "spectral primitive and eigen-prior selection",
        "receipt_rule": "separate experimental, calculated, and model-predicted values",
    },
    {
        "axis": "dataset_provenance",
        "payload": ["source", "license", "version", "modality", "schema", "contamination_check"],
        "router_use": "admissibility and sampling gate",
        "receipt_rule": "do not train/ingest without source/license/schema receipt",
    },
]


HF_CHEMISTRY_PRIORS = [
    {
        "id": "jablonkagroup/ChemBench",
        "role": "chemistry_benchmark_prior",
        "boundary": "benchmark-prior-only",
        "use_as": "chemistry_reasoning_eval_axis",
    },
    {
        "id": "eve-bio/drug-target-activity",
        "role": "bioactivity_table_prior",
        "boundary": "dataset-prior-only",
        "use_as": "molecule_target_property_schema_axis",
    },
    {
        "id": "lisn519010/QM9",
        "role": "quantum_chemistry_small_molecule_prior",
        "boundary": "dataset-prior-only",
        "use_as": "small_molecule_property_and_geometry_axis",
    },
    {
        "id": "jglaser/binding_affinity",
        "role": "protein_ligand_affinity_prior",
        "boundary": "dataset-prior-only",
        "use_as": "binding_property_schema_axis",
    },
    {
        "id": "LeMaterial/LeMat-Traj",
        "role": "material_trajectory_prior",
        "boundary": "dataset-prior-only",
        "use_as": "molecular_or_material_dynamics_axis",
    },
]


def extract_registry_sections(text: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in text.splitlines():
        heading = re.match(r"^###\s+\d+\.\s+(.+)$", line)
        if heading:
            if current:
                sections.append(current)
            current = {"name": heading.group(1).strip(), "lines": []}
            continue
        if current is not None:
            current["lines"].append(line)
    if current:
        sections.append(current)

    compact = []
    for section in sections:
        body = "\n".join(section["lines"])
        compact.append(
            {
                "name": section["name"],
                "source": first_match(body, r"\*\*Source:\*\*\s*(.+)") or first_match(body, r"\*\*URL:\*\*\s*(.+)"),
                "license": first_match(body, r"\*\*License:\*\*\s*(.+)"),
                "entries": first_match(body, r"\*\*Entries:\*\*\s*(.+)") or first_match(body, r"\*\*Species:\*\*\s*(.+)"),
                "integration_value": first_match(body, r"\*\*Integration Value:\*\*\s*(.+)"),
                "bond_matrix_mentions": count_terms(body, ["bond", "angle", "dihedral", "coordinate", "force"]),
            }
        )
    return compact


def first_match(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None


def count_terms(text: str, terms: list[str]) -> int:
    lowered = text.lower()
    return sum(lowered.count(term) for term in terms)


def local_script_summary(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lowered = text.lower()
    speculative_markers = [
        "element 229",
        "superconductor",
        "stabilized into a molecular cluster",
        "calibrated",
        "final collapse",
    ]
    return {
        "path": str(path),
        "lines": text.count("\n") + 1,
        "functions": re.findall(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)", text, flags=re.MULTILINE),
        "claim_boundary": "hypothesis_or_demo_only" if any(marker in lowered for marker in speculative_markers) else "utility_script",
        "contains_randomness": "random" in lowered,
    }


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = "You are a molecular physics/math router. Return compact JSON with evidence boundaries."
    records = []
    for axis in receipt["molecular_axes"]:
        prompt = {
            "task": "route_molecular_axis",
            "axis": axis["axis"],
            "payload": axis["payload"],
            "instruction": "Choose how this molecular axis should enter the physics-math compression router.",
        }
        answer = {
            "selected": True,
            "use_as": axis["router_use"],
            "claim_boundary": "computational-chemistry-prior-only",
            "surface_payload_hint": axis["axis"][:16].upper(),
            "receipt_rule": axis["receipt_rule"],
        }
        records.append(chat_record(system, prompt, answer))
    for prior in receipt["hf_chemistry_priors"]:
        prompt = {
            "task": "use_hf_chemistry_prior",
            "dataset": prior["id"],
            "role": prior["role"],
            "instruction": "Explain how to sample this chemistry dataset family without overclaiming.",
        }
        answer = {
            "selected": True,
            "use_as": prior["use_as"],
            "claim_boundary": prior["boundary"],
            "sampling_rule": "sample small, preserve schema/source/license/units, and keep experimental/calculated/predicted labels distinct",
        }
        records.append(chat_record(system, prompt, answer))
    return records


def chat_record(system: str, prompt: dict[str, Any], answer: dict[str, Any]) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--chemistry-dir", type=Path, default=LOCAL_CHEMISTRY_DIR)
    parser.add_argument("--receipt", type=Path, default=Path("4-Infrastructure/shim/molecular_domain_prior_receipt.json"))
    parser.add_argument("--curriculum", type=Path, default=Path("4-Infrastructure/shim/molecular_domain_prior_curriculum.jsonl"))
    args = parser.parse_args()

    registry_text = args.registry.read_text(encoding="utf-8", errors="replace") if args.registry.exists() else ""
    local_scripts = [
        local_script_summary(path)
        for path in sorted(args.chemistry_dir.glob("*.py"))
    ] if args.chemistry_dir.exists() else []
    receipt = {
        "schema": "molecular_domain_prior_receipt_v1",
        "claim_boundary": "Molecular priors support computational routing, not wet-lab validity or synthesis claims.",
        "registry": str(args.registry),
        "registry_sections": extract_registry_sections(registry_text),
        "molecular_axes": MOLECULAR_AXES,
        "hf_chemistry_priors": HF_CHEMISTRY_PRIORS,
        "local_scripts": local_scripts,
        "lawful": bool(registry_text) and bool(MOLECULAR_AXES),
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
