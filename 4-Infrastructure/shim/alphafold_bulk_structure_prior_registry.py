#!/usr/bin/env python3
"""Register AlphaFold DB bulk downloads as a receipted biological structure prior.

This registry does not download AlphaFold archives. It records the external
download surface, license boundary, citation requirements, and Research Stack
route value for RRC/Omindirection as structured metadata.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "biological_structure_priors"
PACKETS = OUT_DIR / "alphafold_bulk_structure_prior_packets.jsonl"
RECEIPT = OUT_DIR / "alphafold_bulk_structure_prior_receipt.json"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def packet(packet_id: str, name: str, route: str, density_markers: list[str], claim_boundary: str) -> dict[str, Any]:
    obj = {
        "schema": "alphafold_bulk_structure_prior_packet_v1",
        "packet_id": packet_id,
        "name": name,
        "source_url": "https://alphafold.ebi.ac.uk/download",
        "ftp_url": "https://ftp.ebi.ac.uk/pub/databases/alphafold",
        "license": "CC-BY-4.0",
        "rrc_shape_hint": "PredictedProteinStructureCorpus",
        "route": route,
        "density_markers": density_markers,
        "claim_boundary": claim_boundary,
        "decision": "HOLD",
    }
    obj["packet_hash"] = sha256_text(stable_json(obj))
    return obj


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    packets = [
        packet(
            packet_id="ALPHAFOLD.BULK.MODEL_ORGANISM_PROTEOMES.0001",
            name="AlphaFold model-organism proteome archives",
            route=(
                "reference proteome -> compressed PDB/mmCIF archive -> confidence-bearing "
                "predicted structure graph -> domain/boundary/fragment route"
            ),
            density_markers=[
                "reference_proteome_archive",
                "compressed_pdb_mmcif_members",
                "per_residue_confidence_surface",
                "long_protein_fragmentation",
                "species_level_structure_corpus",
                "ftp_bulk_download_surface",
            ],
            claim_boundary=(
                "Prediction corpus only; structures are theoretical models and require confidence, "
                "metadata, and domain-specific validation before biological or compression claims."
            ),
        ),
        packet(
            packet_id="ALPHAFOLD.BULK.SWISSPROT.0001",
            name="AlphaFold Swiss-Prot bulk structure archives",
            route=(
                "Swiss-Prot sequence set -> predicted structure archive -> high-curation "
                "protein-shape dictionary -> residue/contact/topology prior"
            ),
            density_markers=[
                "swissprot_curated_sequence_anchor",
                "cif_archive_surface",
                "pdb_archive_surface",
                "protein_shape_dictionary",
                "sequence_to_structure_projection",
                "structure_metadata_citation_gate",
            ],
            claim_boundary=(
                "Useful as a curated structure prior; not a replacement for experimental structure "
                "or clinical evidence."
            ),
        ),
        packet(
            packet_id="ALPHAFOLD.BULK.COLLABORATOR_DATASETS.0001",
            name="AlphaFold collaborator dataset archives",
            route=(
                "collaborator dataset -> chunked coordinate archive / optional MSA archive "
                "-> dataset-specific structure prior -> source-specific citation gate"
            ),
            density_markers=[
                "collaborator_coordinate_chunks",
                "optional_msa_surface",
                "dataset_specific_availability",
                "third_party_copyright_boundary",
                "source_specific_citation_gate",
                "nonclinical_prediction_disclaimer",
            ],
            claim_boundary=(
                "Collaborator datasets have additional source-specific copyrights and metadata; "
                "local ingest must preserve those boundaries."
            ),
        ),
    ]

    PACKETS.write_text("\n".join(stable_json(p) for p in packets) + "\n", encoding="utf-8")
    receipt = {
        "schema": "alphafold_bulk_structure_prior_receipt_v1",
        "packet_count": len(packets),
        "density_marker_total": sum(len(p["density_markers"]) for p in packets),
        "packets": str(PACKETS.relative_to(REPO)),
        "source_url": "https://alphafold.ebi.ac.uk/download",
        "ftp_url": "https://ftp.ebi.ac.uk/pub/databases/alphafold",
        "license": "CC-BY-4.0",
        "license_boundary": (
            "AlphaFold DB data is listed as available for academic and commercial use under "
            "CC-BY-4.0. Use must preserve attribution, cite required papers, honor EMBL-EBI "
            "terms, and respect dataset-specific copyright notices."
        ),
        "disclaimer_boundary": (
            "AlphaFold and AlphaMissense data are predictions for theoretical modelling, provided "
            "as-is, not validated or approved for clinical use, and not a substitute for medical advice."
        ),
        "download_boundary": (
            "No bulk archives are downloaded by this registry. Archive ingest must be explicit, "
            "chunked, receipted, and storage-budgeted."
        ),
        "required_citation_gate": [
            "AlphaFold Protein Structure Database and 3D-Beacons: New Data and Capabilities",
            "Relevant structure publication or dataset metadata",
            "Jumper et al. AlphaFold Nature 2021 for UniProt predictions where applicable",
        ],
        "decision": "HOLD",
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
