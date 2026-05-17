#!/usr/bin/env python3
"""Registry of mathematical research databases as RRC quarry surfaces.

This stores source metadata, access boundaries, and density-marker roles for
math research databases.  It does not scrape full texts or bypass subscriptions.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "math_research_databases"
JSONL = OUT_DIR / "math_research_database_registry.jsonl"
CSV = OUT_DIR / "math_research_database_registry.csv"
MSC_JSONL = OUT_DIR / "msc2020_top_level_registry.jsonl"
MSC_CSV = OUT_DIR / "msc2020_top_level_registry.csv"
RECEIPT = OUT_DIR / "math_research_database_registry_receipt.json"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


DATABASES: list[dict[str, Any]] = [
    {
        "database_id": "MATHDB.REFERENCE.ZBMATH_OPEN.0001",
        "name": "zbMATH Open",
        "category": "primary_reference_database",
        "url": "https://zbmath.org/",
        "access_boundary": "Open bibliographic/review metadata; respect platform terms and robots.",
        "bulk_access_mode": "rest_api_terms_bound",
        "lawful_ingest_surface": "zbMATH Open API bibliographic/review/classification metadata under API terms; no unrestricted full-content mirror assumption.",
        "density_markers": [
            "msc_classification_graph",
            "msc2020_top_level_ladder",
            "api_metadata_surface",
            "review_metadata",
            "citation_linkage",
            "long_historical_coverage",
        ],
        "rrc_use": "authoritative math-literature routing and classification prior",
        "claim_boundary": "index/review metadata is not theorem verification",
        "status": "CANDIDATE",
    },
    {
        "database_id": "MATHDB.REFERENCE.MATHSCINET.0001",
        "name": "MathSciNet / Mathematical Reviews",
        "category": "primary_reference_database",
        "url": "https://mathscinet.ams.org/",
        "access_boundary": "Subscription database; store pointer and metadata role only.",
        "bulk_access_mode": "subscription_pointer_only",
        "lawful_ingest_surface": "No bulk ingest without explicit licensed access; store source pointer and review/citation role only.",
        "density_markers": [
            "expert_review_graph",
            "citation_linkage",
            "msc_classification_graph",
            "author_disambiguation",
        ],
        "rrc_use": "high-trust review/citation routing when user has lawful access",
        "claim_boundary": "subscription metadata pointer only; no scraping",
        "status": "HOLD",
    },
    {
        "database_id": "MATHDB.DML.EUDML.0001",
        "name": "EuDML",
        "category": "digital_mathematics_library",
        "url": "https://eudml.org/",
        "access_boundary": "Use open full-text and moving-wall metadata lawfully.",
        "bulk_access_mode": "oai_pmh_metadata_harvest",
        "lawful_ingest_surface": "OAI-PMH metadata harvesting plus open full-text pointers where rights permit.",
        "density_markers": [
            "validated_full_text",
            "moving_wall_access",
            "oai_pmh_metadata_surface",
            "journal_archive_federation",
            "historical_math_corpus",
        ],
        "rrc_use": "full-text source candidate for historical/modern math documents",
        "claim_boundary": "full text does not imply formal proof replay",
        "status": "CANDIDATE",
    },
    {
        "database_id": "MATHDB.DML.PROJECT_EUCLID.0001",
        "name": "Project Euclid",
        "category": "digital_mathematics_library",
        "url": "https://projecteuclid.org/",
        "access_boundary": "Mixed open/subscription access; store article pointers and open metadata only.",
        "bulk_access_mode": "mixed_access_metadata_pointer",
        "lawful_ingest_surface": "Article pointers, open metadata, and open full-text where licensed; no subscription bypass.",
        "density_markers": [
            "society_journal_hosting",
            "math_statistics_full_text",
            "article_metadata",
            "independent_journal_surface",
        ],
        "rrc_use": "math/statistics journal source routing",
        "claim_boundary": "respect access controls and article licenses",
        "status": "HOLD",
    },
    {
        "database_id": "MATHDB.PREPRINT.ARXIV_MATH.0001",
        "name": "arXiv Math",
        "category": "preprint_repository",
        "url": "https://arxiv.org/archive/math",
        "access_boundary": "Open preprint metadata and PDFs under arXiv terms.",
        "bulk_access_mode": "requester_pays_s3_and_metadata_mirror",
        "lawful_ingest_surface": "Requester-pays S3 bulk PDFs/source files, OAI-PMH/API metadata, and Kaggle metadata snapshot; link back to arXiv for downloads.",
        "density_markers": [
            "requester_pays_s3_bulk_text",
            "latex_source_archive",
            "kaggle_metadata_snapshot",
            "preprint_version_graph",
            "author_accepted_manuscript_surface",
            "subject_classification",
            "fast_modern_research_signal",
        ],
        "rrc_use": "modern math prior and versioned source surface",
        "claim_boundary": "preprint status is not peer-reviewed theorem validation",
        "status": "CANDIDATE",
    },
    {
        "database_id": "MATHDB.ARCHIVE.JSTOR.0001",
        "name": "JSTOR",
        "category": "historical_digital_library",
        "url": "https://www.jstor.org/",
        "access_boundary": "Mixed access; store source pointer and public metadata only unless user has lawful access.",
        "bulk_access_mode": "restricted_archive_pointer",
        "lawful_ingest_surface": "Public metadata/source pointer only unless a lawful text-and-data-mining or institutional access path is present.",
        "density_markers": [
            "historical_journal_archive",
            "foundational_paper_surface",
            "citation_context",
            "scan_to_text_boundary",
        ],
        "rrc_use": "historical provenance and old-theorem source routing",
        "claim_boundary": "do not ingest paywalled text without access",
        "status": "HOLD",
    },
    {
        "database_id": "MATHDB.ARCHIVE.GALLICA.0001",
        "name": "Gallica",
        "category": "historical_digital_library",
        "url": "https://gallica.bnf.fr/",
        "access_boundary": "Use public-domain/open archive material under Gallica terms.",
        "bulk_access_mode": "open_archive_pointer",
        "lawful_ingest_surface": "Public-domain/open scans and metadata under Gallica terms, with OCR residual tracking.",
        "density_markers": [
            "digital_incunable_surface",
            "historical_scan",
            "ocr_noise_residual",
            "foundational_math_source",
        ],
        "rrc_use": "public historical math source with OCR residual tracking",
        "claim_boundary": "OCR text needs residual/scan receipts",
        "status": "CANDIDATE",
    },
    {
        "database_id": "MATHDB.ARCHIVE.PROJECT_GUTENBERG.0001",
        "name": "Project Gutenberg",
        "category": "historical_digital_library",
        "url": "https://www.gutenberg.org/",
        "access_boundary": "Use public-domain/open texts under Project Gutenberg terms.",
        "bulk_access_mode": "open_public_domain_text_repository",
        "lawful_ingest_surface": "Public-domain text files and metadata for historical mathematics books where available.",
        "density_markers": [
            "public_domain_text_surface",
            "historical_book_corpus",
            "ocr_or_transcription_residual",
            "foundational_math_source",
        ],
        "rrc_use": "historical math prose and notation source routing",
        "claim_boundary": "public-domain text is source material, not proof replay",
        "status": "CANDIDATE",
    },
    {
        "database_id": "MATHDB.ARCHIVE.INTERNET_ARCHIVE.0001",
        "name": "Internet Archive",
        "category": "historical_digital_library",
        "url": "https://archive.org/",
        "access_boundary": "Use public-domain/open collections and item metadata under item-specific rights.",
        "bulk_access_mode": "open_archive_item_collections",
        "lawful_ingest_surface": "Open item metadata, scans, OCR, and community collections where rights permit; avoid unofficial copyright-risk mirrors.",
        "density_markers": [
            "public_domain_scan_surface",
            "community_collection_surface",
            "ocr_noise_residual",
            "historical_math_corpus",
        ],
        "rrc_use": "public historical scan/OCR source with residual receipts",
        "claim_boundary": "item-level rights and OCR quality must be receipted",
        "status": "CANDIDATE",
    },
    {
        "database_id": "MATHDB.DATA.MARDI.0001",
        "name": "MaRDI",
        "category": "mathematical_research_data_initiative",
        "url": "https://www.mardi4nfdi.de/",
        "access_boundary": "Use public metadata and open APIs/datasets only.",
        "bulk_access_mode": "fair_data_portal",
        "lawful_ingest_surface": "FAIR mathematical model, algorithm, and research-data metadata/datasets where openly licensed.",
        "density_markers": [
            "mathematical_model_database",
            "algorithm_database",
            "research_data_graph",
            "model_metadata_surface",
        ],
        "rrc_use": "MathModDB/MathAlgoDB-style model and algorithm routing",
        "claim_boundary": "model metadata is not validated implementation",
        "status": "CANDIDATE",
    },
    {
        "database_id": "MATHDB.CONJECTURE.BLOOM_ERDOS.0001",
        "name": "Bloom's Erdos Conjectures Database",
        "category": "specialized_conjecture_database",
        "url": "https://www.erdosproblems.com/",
        "access_boundary": "Use public problem metadata and cite source; do not overclaim solver status.",
        "bulk_access_mode": "public_problem_metadata",
        "lawful_ingest_surface": "Public conjecture/problem metadata and status pointers with HOLD-first benchmark handling.",
        "density_markers": [
            "open_problem_graph",
            "combinatorics_number_theory_surface",
            "benchmark_problem_set",
            "conjecture_status_marker",
        ],
        "rrc_use": "HOLD-first benchmark surface for autonomous math research agents",
        "claim_boundary": "open problem metadata is not proof or disproof",
        "status": "CANDIDATE",
    },
    {
        "database_id": "MATHDB.SEQUENCE.OEIS.0001",
        "name": "OEIS",
        "category": "specialized_sequence_database",
        "url": "https://oeis.org/",
        "access_boundary": "Respect OEIS terms; store sequence IDs and pattern metadata, not bulk copies.",
        "bulk_access_mode": "direct_bulk_download_and_git_mirror",
        "lawful_ingest_surface": "Official stripped.gz sequence data, names.gz descriptions, and oeisdata GitHub mirror under OEIS license terms.",
        "density_markers": [
            "direct_sequence_bulk_download",
            "git_sequence_mirror",
            "integer_sequence_identity",
            "pattern_recognition_surface",
            "formula_crosslink",
            "sequence_reference_graph",
        ],
        "rrc_use": "sequence/logogram pattern recognition and residual routing",
        "claim_boundary": "sequence match is a hypothesis, not theorem proof",
        "status": "CANDIDATE",
    },
]


MSC2020_TOP_LEVEL: list[tuple[str, str]] = [
    ("00", "General and overarching topics; collections"),
    ("01", "History and biography"),
    ("03", "Mathematical logic and foundations"),
    ("05", "Combinatorics"),
    ("06", "Order, lattices, ordered algebraic structures"),
    ("08", "General algebraic systems"),
    ("11", "Number theory"),
    ("12", "Field theory and polynomials"),
    ("13", "Commutative algebra"),
    ("14", "Algebraic geometry"),
    ("15", "Linear and multilinear algebra; matrix theory"),
    ("16", "Associative rings and algebras"),
    ("17", "Nonassociative rings and algebras"),
    ("18", "Category theory; homological algebra"),
    ("19", "K-theory"),
    ("20", "Group theory and generalizations"),
    ("22", "Topological groups, Lie groups"),
    ("26", "Real functions"),
    ("28", "Measure and integration"),
    ("30", "Functions of a complex variable"),
    ("31", "Potential theory"),
    ("32", "Several complex variables and analytic spaces"),
    ("33", "Special functions"),
    ("34", "Ordinary differential equations"),
    ("35", "Partial differential equations"),
    ("37", "Dynamical systems and ergodic theory"),
    ("39", "Difference and functional equations"),
    ("40", "Sequences, series, summability"),
    ("41", "Approximations and expansions"),
    ("42", "Harmonic analysis on Euclidean spaces"),
    ("43", "Abstract harmonic analysis"),
    ("44", "Integral transforms, operational calculus"),
    ("45", "Integral equations"),
    ("46", "Functional analysis"),
    ("47", "Operator theory"),
    ("49", "Calculus of variations and optimal control; optimization"),
    ("51", "Geometry"),
    ("52", "Convex and discrete geometry"),
    ("53", "Differential geometry"),
    ("54", "General topology"),
    ("55", "Algebraic topology"),
    ("57", "Manifolds and cell complexes"),
    ("58", "Global analysis, analysis on manifolds"),
    ("60", "Probability theory and stochastic processes"),
    ("62", "Statistics"),
    ("65", "Numerical analysis"),
    ("68", "Computer science"),
    ("70", "Mechanics of particles and systems"),
    ("74", "Mechanics of deformable solids"),
    ("76", "Fluid mechanics"),
    ("78", "Optics, electromagnetic theory"),
    ("80", "Classical thermodynamics, heat transfer"),
    ("81", "Quantum theory"),
    ("82", "Statistical mechanics, structure of matter"),
    ("83", "Relativity and gravitational theory"),
    ("85", "Astronomy and astrophysics"),
    ("86", "Geophysics"),
    ("90", "Operations research, mathematical programming"),
    ("91", "Game theory, economics, finance, and other social and behavioral sciences"),
    ("92", "Biology and other natural sciences"),
    ("93", "Systems theory; control"),
    ("94", "Information and communication theory, circuits"),
    ("97", "Mathematics education"),
]


def packetize(entry: dict[str, Any]) -> dict[str, Any]:
    packet = {
        "schema": "math_research_database_registry_v1",
        "rrc_shape_hint": "MathSourceDensityRegistry",
        **entry,
    }
    packet["packet_hash"] = sha256_text(stable_json(packet))
    return packet


def packetize_msc(code: str, label: str) -> dict[str, Any]:
    packet = {
        "schema": "msc2020_top_level_registry_v1",
        "classification_id": f"MSC2020.{code}",
        "code": code,
        "label": label,
        "source": "MSC2020 top-level classification list",
        "license_note": "MSC2020 is published by Mathematical Reviews and zbMATH Open under CC-BY-NC-SA; store code and label with attribution.",
        "rrc_shape_hint": "MSC2020ClassificationLadder",
        "density_markers": [
            "classification_axis",
            "math_domain_boundary",
            "literature_routing_prior",
            "source_density_marker",
        ],
        "status": "CANDIDATE",
        "claim_boundary": "Classification route only; not proof validation or full-text access.",
    }
    packet["packet_hash"] = sha256_text(stable_json(packet))
    return packet


def csv_escape(value: Any) -> str:
    text = str(value).replace('"', '""')
    return f'"{text}"'


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    packets = [packetize(entry) for entry in DATABASES]
    msc_packets = [packetize_msc(code, label) for code, label in MSC2020_TOP_LEVEL]
    JSONL.write_text("\n".join(stable_json(packet) for packet in packets) + "\n", encoding="utf-8")
    MSC_JSONL.write_text("\n".join(stable_json(packet) for packet in msc_packets) + "\n", encoding="utf-8")
    lines = [
        "database_id,name,category,status,bulk_access_mode,lawful_ingest_surface,density_markers,rrc_use,url,packet_hash"
    ]
    for packet in packets:
        lines.append(
            ",".join(
                [
                    csv_escape(packet["database_id"]),
                    csv_escape(packet["name"]),
                    csv_escape(packet["category"]),
                    csv_escape(packet["status"]),
                    csv_escape(packet["bulk_access_mode"]),
                    csv_escape(packet["lawful_ingest_surface"]),
                    csv_escape(";".join(packet["density_markers"])),
                    csv_escape(packet["rrc_use"]),
                    csv_escape(packet["url"]),
                    csv_escape(packet["packet_hash"]),
                ]
            )
        )
    CSV.write_text("\n".join(lines) + "\n", encoding="utf-8")
    msc_lines = ["classification_id,code,label,status,density_markers,packet_hash"]
    for packet in msc_packets:
        msc_lines.append(
            ",".join(
                [
                    csv_escape(packet["classification_id"]),
                    csv_escape(packet["code"]),
                    csv_escape(packet["label"]),
                    csv_escape(packet["status"]),
                    csv_escape(";".join(packet["density_markers"])),
                    csv_escape(packet["packet_hash"]),
                ]
            )
        )
    MSC_CSV.write_text("\n".join(msc_lines) + "\n", encoding="utf-8")
    status_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    for packet in packets:
        status_counts[packet["status"]] = status_counts.get(packet["status"], 0) + 1
        category_counts[packet["category"]] = category_counts.get(packet["category"], 0) + 1
    receipt = {
        "schema": "math_research_database_registry_receipt_v1",
        "claim_boundary": "Metadata-only source registry; no subscription bypass, no bulk scraping, and no proof claims.",
        "database_count": len(packets),
        "status_counts": status_counts,
        "category_counts": category_counts,
        "msc2020_top_level_count": len(msc_packets),
        "jsonl": str(JSONL.relative_to(REPO)),
        "csv": str(CSV.relative_to(REPO)),
        "msc_jsonl": str(MSC_JSONL.relative_to(REPO)),
        "msc_csv": str(MSC_CSV.relative_to(REPO)),
        "database_ids": [packet["database_id"] for packet in packets],
        "msc2020_codes": [packet["code"] for packet in msc_packets],
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
