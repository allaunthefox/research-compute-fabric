#!/usr/bin/env python3
"""AlphaFold species-density eigen probe.

This is a metadata-only first pass. It uses AlphaFold DB download-page archive
metadata (predicted structure counts and archive sizes) to form a species x
density-feature matrix, then computes covariance eigenvectors and a normalized
positive semidefinite density matrix.

It does not download AlphaFold structure archives. Full protein-coordinate
eigenvectors require explicit archive ingest and pLDDT/contact/topology parsing.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "biological_structure_priors"
MATRIX_CSV = OUT_DIR / "alphafold_species_density_matrix.csv"
EIGEN_JSON = OUT_DIR / "alphafold_species_density_eigen_probe.json"
RECEIPT = OUT_DIR / "alphafold_species_density_eigen_probe_receipt.json"


SOURCE_URL = "https://alphafold.ebi.ac.uk/download"


SPECIES_ROWS = [
    # model organism proteomes
    ("model_organism", "Arabidopsis thaliana", "Arabidopsis", "UP000006548", 27402, 3698),
    ("model_organism", "Caenorhabditis elegans", "Nematode worm", "UP000001940", 19700, 2649),
    ("model_organism", "Candida albicans", "C. albicans", "UP000000559", 5973, 981),
    ("model_organism", "Danio rerio", "Zebrafish", "UP000000437", 26290, 4749),
    ("model_organism", "Dictyostelium discoideum", "Dictyostelium", "UP000002195", 12612, 2187),
    ("model_organism", "Drosophila melanogaster", "Fruit fly", "UP000000803", 13461, 2213),
    ("model_organism", "Escherichia coli", "E. coli", "UP000000625", 4370, 456),
    ("model_organism", "Glycine max", "Soybean", "UP000008827", 55796, 7264),
    ("model_organism", "Homo sapiens", "Human", "UP000005640", 23586, 4938),
    ("model_organism", "Methanocaldococcus jannaschii", "M. jannaschii", "UP000000805", 1773, 174),
    ("model_organism", "Mus musculus", "Mouse", "UP000000589", 21452, 3607),
    ("model_organism", "Oryza sativa", "Asian rice", "UP000059680", 43645, 4505),
    ("model_organism", "Rattus norvegicus", "Rat", "UP000002494", 22152, 3602),
    ("model_organism", "Saccharomyces cerevisiae", "Budding yeast", "UP000002311", 6055, 977),
    ("model_organism", "Schizosaccharomyces pombe", "Fission yeast", "UP000002485", 5196, 803),
    ("model_organism", "Zea mays", "Maize", "UP000007305", 39139, 4792),
    # global health proteomes
    ("global_health", "Ajellomyces capsulatus", "Ajellomyces capsulatus", "UP000001631", 9199, 1363),
    ("global_health", "Brugia malayi", "Brugia malayi", "UP000006672", 10972, 1635),
    ("global_health", "Campylobacter jejuni", "C. jejuni", "UP000000799", 1620, 175),
    ("global_health", "Cladophialophora carrionii", "Cladophialophora carrionii", "UP000094526", 11170, 1729),
    ("global_health", "Dracunculus medinensis", "Dracunculus medinensis", "UP000274756", 10834, 1364),
    ("global_health", "Fonsecaea pedrosoi", "Fonsecaea pedrosoi", "UP000053029", 12509, 2014),
    ("global_health", "Haemophilus influenzae", "H. influenzae", "UP000000579", 1660, 175),
    ("global_health", "Helicobacter pylori", "H. pylori", "UP000000429", 1540, 166),
    ("global_health", "Klebsiella pneumoniae", "K. pneumoniae", "UP000007841", 5727, 559),
    ("global_health", "Leishmania infantum", "L. infantum", "UP000008153", 7924, 1508),
    ("global_health", "Madurella mycetomatis", "Madurella mycetomatis", "UP000078237", 9561, 1537),
    ("global_health", "Mycobacterium leprae", "Mycobacterium leprae", "UP000000806", 1602, 177),
    ("global_health", "Mycobacterium tuberculosis", "M. tuberculosis", "UP000001584", 3991, 429),
    ("global_health", "Neisseria gonorrhoeae", "N. gonorrhoeae", "UP000000535", 2106, 195),
    ("global_health", "Nocardia brasiliensis", "Nocardia brasiliensis", "UP000006304", 8398, 873),
    ("global_health", "Onchocerca volvulus", "Onchocerca volvulus", "UP000024404", 12039, 1621),
    ("global_health", "Paracoccidioides lutzii", "Paracoccidioides lutzii", "UP000002059", 8794, 1294),
    ("global_health", "Plasmodium falciparum", "P. falciparum", "UP000001450", 5168, 1148),
    ("global_health", "Pseudomonas aeruginosa", "P. aeruginosa", "UP000002438", 5555, 613),
    ("global_health", "Salmonella typhimurium", "S. typhimurium", "UP000001014", 4526, 477),
    ("global_health", "Schistosoma mansoni", "Schistosoma mansoni", "UP000008854", 9735, 1802),
    ("global_health", "Shigella dysenteriae", "S. dysenteriae", "UP000002716", 3893, 373),
    ("global_health", "Sporothrix schenckii", "Sporothrix schenckii", "UP000018087", 8652, 1519),
    ("global_health", "Staphylococcus aureus", "S. aureus", "UP000008816", 2888, 274),
    ("global_health", "Streptococcus pneumoniae", "S. pneumoniae", "UP000000586", 2031, 202),
    ("global_health", "Strongyloides stercoralis", "Strongyloides stercoralis", "UP000035681", 15335, 2793),
    ("global_health", "Trichuris trichiura", "Trichuris trichiura", "UP000030665", 9563, 1362),
    ("global_health", "Trypanosoma brucei", "Trypanosoma brucei", "UP000008524", 8491, 1345),
    ("global_health", "Trypanosoma cruzi", "T. cruzi", "UP000002296", 19036, 2959),
    ("global_health", "Wuchereria bancrofti", "Wuchereria bancrofti", "UP000270924", 12725, 1418),
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def feature_row(row: tuple[str, str, str, str, int, int]) -> dict[str, Any]:
    category, species, common, proteome, predicted, archive_mb = row
    mb_per_structure = archive_mb / predicted
    structures_per_mb = predicted / archive_mb
    return {
        "category": category,
        "species": species,
        "common_name": common,
        "reference_proteome": proteome,
        "predicted_structures": predicted,
        "archive_mb": archive_mb,
        "mb_per_structure": mb_per_structure,
        "structures_per_mb": structures_per_mb,
        "log_predicted_structures": math.log1p(predicted),
        "log_archive_mb": math.log1p(archive_mb),
        "is_model_organism": 1.0 if category == "model_organism" else 0.0,
        "is_global_health": 1.0 if category == "global_health" else 0.0,
    }


def standardized_matrix(rows: list[dict[str, Any]], fields: list[str]) -> np.ndarray:
    matrix = np.array([[float(row[field]) for field in fields] for row in rows], dtype=float)
    mean = matrix.mean(axis=0)
    std = matrix.std(axis=0)
    std[std == 0] = 1.0
    return (matrix - mean) / std


def species_scores(z: np.ndarray, eigenvectors: np.ndarray, species: list[str], count: int = 8) -> list[dict[str, Any]]:
    scores = z @ eigenvectors[:, 0]
    order = np.argsort(np.abs(scores))[::-1][:count]
    return [{"species": species[i], "pc1_score": float(scores[i]), "abs_pc1_score": float(abs(scores[i]))} for i in order]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [feature_row(row) for row in SPECIES_ROWS]
    fields = [
        "log_predicted_structures",
        "log_archive_mb",
        "mb_per_structure",
        "structures_per_mb",
        "is_model_organism",
        "is_global_health",
    ]
    with MATRIX_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    z = standardized_matrix(rows, fields)
    covariance = (z.T @ z) / max(len(rows) - 1, 1)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    explained = eigenvalues / eigenvalues.sum()

    psd = covariance.copy()
    psd_trace = float(np.trace(psd))
    density_matrix = psd / psd_trace if psd_trace else psd
    purity = float(np.trace(density_matrix @ density_matrix))
    effective_rank = float(1.0 / purity) if purity else float("inf")

    eigen_probe = {
        "schema": "alphafold_species_density_eigen_probe_v1",
        "source_url": SOURCE_URL,
        "row_count": len(rows),
        "feature_fields": fields,
        "eigenvalues": [float(x) for x in eigenvalues],
        "explained_variance_ratio": [float(x) for x in explained],
        "principal_eigenvector": {field: float(eigenvectors[i, 0]) for i, field in enumerate(fields)},
        "density_matrix": density_matrix.tolist(),
        "density_matrix_trace": float(np.trace(density_matrix)),
        "density_matrix_purity": purity,
        "effective_rank": effective_rank,
        "top_pc1_species": species_scores(z, eigenvectors, [row["species"] for row in rows]),
        "claim_boundary": (
            "This is an archive-metadata eigen probe over species counts and compressed archive "
            "sizes, not a coordinate-structure eigensystem over AlphaFold models. Full species "
            "shape eigenvectors require explicit archive ingest and structure parsing."
        ),
        "decision": "HOLD",
    }
    eigen_probe["probe_hash"] = sha256_text(stable_json(eigen_probe))
    EIGEN_JSON.write_text(json.dumps(eigen_probe, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = {
        "schema": "alphafold_species_density_eigen_probe_receipt_v1",
        "source_url": SOURCE_URL,
        "matrix_csv": str(MATRIX_CSV.relative_to(REPO)),
        "eigen_json": str(EIGEN_JSON.relative_to(REPO)),
        "row_count": len(rows),
        "feature_count": len(fields),
        "dominant_explained_variance": float(explained[0]),
        "density_matrix_purity": purity,
        "effective_rank": effective_rank,
        "top_pc1_species": eigen_probe["top_pc1_species"],
        "claim_boundary": eigen_probe["claim_boundary"],
        "decision": "HOLD",
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
