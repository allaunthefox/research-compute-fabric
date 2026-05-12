#!/usr/bin/env python3
"""Register cross-domain bulk datasets as n-space route candidates.

This is a metadata registry, not a downloader. It records large public dataset
surfaces that may produce useful density matrices or manifold graphs for RRC.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "nspace_bulk_routes"
PACKETS = OUT_DIR / "nspace_bulk_dataset_route_packets.jsonl"
TABLE_CSV = OUT_DIR / "nspace_bulk_dataset_route_table.csv"
RECEIPT = OUT_DIR / "nspace_bulk_dataset_route_receipt.json"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def packet(
    domain: str,
    dataset: str,
    source_urls: list[str],
    potential_nspace_application: str,
    density_markers: list[str],
    license_boundary: str,
    ingest_boundary: str,
) -> dict[str, Any]:
    obj = {
        "schema": "nspace_bulk_dataset_route_packet_v1",
        "domain": domain,
        "dataset": dataset,
        "source_urls": source_urls,
        "potential_nspace_application": potential_nspace_application,
        "density_markers": density_markers,
        "license_boundary": license_boundary,
        "ingest_boundary": ingest_boundary,
        "decision": "HOLD",
    }
    obj["packet_id"] = "NSPACE." + domain.upper().replace(" ", "_") + "." + dataset.upper().replace(" ", "_").replace("-", "_").replace("/", "_")
    obj["packet_hash"] = sha256_text(stable_json(obj))
    return obj


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    packets = [
        packet(
            domain="Astro",
            dataset="Gaia DR3",
            source_urls=["https://www.cosmos.esa.int/web/gaia/dr3"],
            potential_nspace_application="Galactic 5D/6D phase-space density matrix over position, parallax, proper motion, radial velocity, and photometry.",
            density_markers=[
                "astrometric_phase_space",
                "parallax_proper_motion_surface",
                "radial_velocity_subset",
                "photometric_density_channels",
                "billion_point_manifold",
            ],
            license_boundary="ESA/Gaia source terms and citation requirements must be checked before ingest.",
            ingest_boundary="Do not ingest full Gaia-scale tables without column partitioning, sky tiling, and receipt-backed storage budget.",
        ),
        packet(
            domain="Climate",
            dataset="ERA5",
            source_urls=["https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels"],
            potential_nspace_application="Spatio-temporal grid manifolds over latitude, longitude, vertical/variable axes, and time.",
            density_markers=[
                "spatiotemporal_grid",
                "reanalysis_variable_cube",
                "time_slice_projection",
                "region_tile_projection",
                "petabyte_scale_archive",
            ],
            license_boundary="Copernicus/ECMWF terms, attribution, and download rules must be checked before ingest.",
            ingest_boundary="Prefer variable/time/region subsets and derived density matrices before any petabyte-scale pull.",
        ),
        packet(
            domain="Semantic",
            dataset="LAION-5B",
            source_urls=["https://laion.ai/blog/laion-5b/"],
            potential_nspace_application="512D-1024D embedding-space density matrices, cluster manifolds, and modality-boundary probes.",
            density_markers=[
                "embedding_vector_surface",
                "image_text_pair_metadata",
                "high_dimensional_semantic_density",
                "cluster_eigenvector_probe",
                "license_and_safety_filter_gate",
            ],
            license_boundary="LAION metadata/source URLs and downstream content licenses/safety filters must be treated as source-specific.",
            ingest_boundary="Do not mirror raw media blindly; operate on metadata/embedding subsets and preserve safety/filter receipts.",
        ),
        packet(
            domain="Bio",
            dataset="AlphaFold",
            source_urls=["https://alphafold.ebi.ac.uk/download", "https://ftp.ebi.ac.uk/pub/databases/alphafold"],
            potential_nspace_application="3D geometric protein topology, contact-graph density matrices, confidence-weighted residue manifolds.",
            density_markers=[
                "protein_coordinate_topology",
                "plddt_confidence_surface",
                "species_structure_density",
                "fragment_boundary_lane",
                "cc_by_4_attribution_gate",
            ],
            license_boundary="AlphaFold DB data is listed as CC-BY-4.0 with required citations and nonclinical disclaimer.",
            ingest_boundary="Start with one small proteome archive and parse confidence/topology receipts before scaling.",
        ),
        packet(
            domain="Bio",
            dataset="NCBI ASN.1 / GenBank",
            source_urls=["https://ftp.ncbi.nlm.nih.gov/ncbi-asn1/", "https://ftp.ncbi.nlm.nih.gov/genbank/"],
            potential_nspace_application="Sequence record manifolds, divisional release matrices, daily-update delta lanes, CON scaffold reconstruction graphs.",
            density_markers=[
                "asn1_bioseq_set_carrier",
                "genbank_flatfile_carrier",
                "release_signal_files",
                "daily_incremental_update_lane",
                "division_code_partition",
                "con_scaffold_reassembly_graph",
                "wgs_project_tree",
                "protein_fasta_translation_surface",
            ],
            license_boundary="NCBI/GenBank public data has no NCBI restriction on use/distribution, but submitter records, citations, NLM/NCBI terms, and third-party caveats still need preservation.",
            ingest_boundary="ASN.1 and GenBank flatfiles are not equivalent record-for-record; never merge them without carrier-specific receipts.",
        ),
        packet(
            domain="Physics",
            dataset="The Well",
            source_urls=[
                "https://polymathic-ai.org/the_well/datasets_overview/",
                "https://polymathic-ai.org/the_well/data_format/",
                "https://polymathic-ai.org/the_well/benchmarks/",
            ],
            potential_nspace_application=(
                "Uniform-grid physics-dynamics route atlas over scalar, vector, and tensor fields; "
                "use as an external replay and residual benchmark prior for PIST/OMCF admission tests."
            ),
            density_markers=[
                "hdf5_uniform_grid_carrier",
                "constant_time_interval_trajectories",
                "scalar_vector_tensor_field_split",
                "cartesian_spherical_log_spherical_coordinate_systems",
                "fp32_state_variable_arrays",
                "physics_rollout_baseline_surface",
                "boundary_condition_receipt_surface",
            ],
            license_boundary=(
                "Polymathic AI / The Well dataset terms and per-dataset source terms must be verified "
                "before ingest; this registry does not vendor data."
            ),
            ingest_boundary=(
                "Start with metadata and tiny HDF5 slices only. Full corpus is multi-terabyte scale; "
                "use dataset/field/time/trajectory subsetting with receipt-backed storage budgets."
            ),
        ),
        packet(
            domain="Physics",
            dataset="PDEBench",
            source_urls=[
                "https://github.com/pdebench/PDEBench",
                "https://darus.uni-stuttgart.de/dataset.xhtml?persistentId=doi:10.18419/darus-2986",
                "https://arxiv.org/abs/2210.07182",
            ],
            potential_nspace_application=(
                "Canonical PDE-family replay layer for forward/inverse scientific-ML fixtures, "
                "baseline comparison, residual growth curves, and solver-family route selection."
            ),
            density_markers=[
                "canonical_pde_family_surface",
                "advection_burgers_diffusion_reaction_lane",
                "navier_stokes_darcy_shallow_water_lane",
                "forward_inverse_problem_split",
                "initial_boundary_condition_sweep",
                "ml_baseline_comparison_surface",
            ],
            license_boundary=(
                "PDEBench code, DaRUS datasets, pretrained models, and paper citation requirements "
                "must be checked separately before ingest or redistribution."
            ),
            ingest_boundary=(
                "Use small PDE shards and metadata first. Full benchmark pulls require PDE-family, "
                "resolution, parameter, and train/test split receipts."
            ),
        ),
        packet(
            domain="Physics",
            dataset="RealPDEBench",
            source_urls=[
                "https://huggingface.co/datasets/AI4Science-WestlakeU/RealPDEBench",
                "https://arxiv.org/abs/2601.01829",
                "https://realpdebench.github.io/",
            ],
            potential_nspace_application=(
                "Real-measurement residual calibration layer for sim-to-real gaps, modality masking, "
                "physical-parameter ranges, and witness drift between numerical and observed trajectories."
            ),
            density_markers=[
                "paired_real_simulated_trajectory",
                "piv_velocity_measurement_surface",
                "cfd_les_numerical_surface",
                "combustion_chemiluminescence_lane",
                "sim_to_real_gap_metric",
                "modality_masking_transfer_surface",
                "cc_by_nc_gate",
            ],
            license_boundary=(
                "RealPDEBench is listed on Hugging Face as CC-BY-NC-4.0; noncommercial terms, "
                "paper citation, and per-scenario source notes must be verified before ingest."
            ),
            ingest_boundary=(
                "Start with index files or one trajectory pair. Full release is hundreds of GB; "
                "do not ingest without scenario, modality, split, and storage-budget receipts."
            ),
        ),
        packet(
            domain="Mesh Physics",
            dataset="MeshGraphNets",
            source_urls=[
                "https://github.com/google-deepmind/deepmind-research/tree/master/meshgraphnets",
                "https://arxiv.org/abs/2010.03409",
            ],
            potential_nspace_application=(
                "Irregular mesh and goxel-topology substrate for graph route tests, remeshing witnesses, "
                "cloth/CFD rollouts, and non-grid residual behavior."
            ),
            density_markers=[
                "irregular_mesh_graph_carrier",
                "tfrecord_train_valid_test_splits",
                "cylinder_flow_cfd_domain",
                "flag_cloth_domain",
                "remeshing_sizing_field_lane",
                "rollout_trajectory_pickle_surface",
            ],
            license_boundary=(
                "DeepMind research repository license and dataset-specific availability terms must be "
                "checked before copying code or data."
            ),
            ingest_boundary=(
                "Use metadata and flag_minimal-style tiny domains first. Full mesh datasets require "
                "domain, split, mesh-field schema, and rollout receipt boundaries."
            ),
        ),
        packet(
            domain="Symbolic Regression",
            dataset="SRBench / ParFam",
            source_urls=[
                "https://cavalab.org/srbench/datasets/",
                "https://arxiv.org/html/2310.05537",
                "https://github.com/Philipp238/parfam",
            ],
            potential_nspace_application=(
                "Scientific-law reconstruction route prior over ground-truth formulas, black-box regression "
                "datasets, rational-function families, and basin-hopping candidate-law searches."
            ),
            density_markers=[
                "ground_truth_formula_surface",
                "feynman_symbolic_regression_law_set",
                "strogatz_ode_dynamics_set",
                "black_box_regression_negative_control",
                "rational_function_parametric_family",
                "continuous_global_optimization_route",
                "sparsity_regularized_candidate_law",
                "formula_reconstruction_receipt_surface",
            ],
            license_boundary=(
                "SRBench, PMLB, Feynman, Strogatz, and ParFam code/data licenses must be verified "
                "separately before copying, adapting, or redistributing artifacts."
            ),
            ingest_boundary=(
                "Use as benchmark metadata and tiny replay fixtures first. Ground-truth formulas may seed "
                "candidate-law tests; black-box problems remain negative controls unless exact replay and "
                "byte-accounted residuals pass."
            ),
        ),
        packet(
            domain="Symbolic Math",
            dataset="DLMF / Feynman Symbolic Regression",
            source_urls=[
                "https://dlmf.nist.gov/",
                "https://pmc.ncbi.nlm.nih.gov/articles/PMC7159912/",
                "https://space.mit.edu/home/tegmark/aifeynman.html",
            ],
            potential_nspace_application=(
                "Special-function and physics-equation glyph/eigen-codec prior for symbolic law recovery, "
                "formula canonicalization, and equation-family compression tests."
            ),
            density_markers=[
                "special_function_identity_surface",
                "dlmf_notation_reference_lane",
                "feynman_ground_truth_formula_set",
                "sympy_simplification_zero_check",
                "physics_equation_symbolic_regression_lane",
                "formula_glyph_codec_prior",
            ],
            license_boundary=(
                "DLMF/NIST terms and AI Feynman/FSReD dataset/code terms must be checked before "
                "vendoring formulas, tables, code, or generated data."
            ),
            ingest_boundary=(
                "Use equation identifiers, citations, and tiny replay samples first. Treat identities as "
                "reference priors until local symbolic replay and source-specific citation receipts exist."
            ),
        ),
        packet(
            domain="Formal Math",
            dataset="LeanDojo / mathlib",
            source_urls=[
                "https://leandojo.org/index.html",
                "https://leandojo.readthedocs.io/en/stable/",
                "https://github.com/leanprover-community/mathlib4",
            ],
            potential_nspace_application=(
                "Formal proof/tactic corpus for routing equation claims into Lean obligations, theorem "
                "dependency graphs, tactic-state replay, and proof-surface negative controls."
            ),
            density_markers=[
                "lean4_theorem_dependency_graph",
                "proof_state_tactic_trace",
                "mathlib_premise_selection_surface",
                "formal_obligation_routing",
                "source_of_truth_proof_gate",
                "reprover_retrieval_prior",
            ],
            license_boundary=(
                "LeanDojo, mathlib4, extracted benchmark datasets, and generated traces have separate "
                "licenses/citations that must be verified before vendoring or redistribution."
            ),
            ingest_boundary=(
                "Prefer local mathlib references and tiny traced theorem samples. Do not promote any "
                "equation route to proof status without actual Lean replay in the local toolchain."
            ),
        ),
        packet(
            domain="Math Reasoning",
            dataset="NuminaMath",
            source_urls=[
                "https://huggingface.co/collections/AI-MO/numinamath",
                "https://github.com/project-numina/aimo-progress-prize",
            ],
            potential_nspace_application=(
                "Broad mathematical reasoning pretraining prior for candidate generation, problem-style "
                "routing, and tool-integrated reasoning patterns before deterministic verification."
            ),
            density_markers=[
                "competition_math_problem_solution_pair",
                "chain_of_thought_reasoning_surface",
                "tool_integrated_reasoning_lane",
                "olympiad_metadata_prior",
                "reasoning_pretraining_not_formal_proof",
            ],
            license_boundary=(
                "Hugging Face dataset/model cards and Project Numina terms must be checked before "
                "download, training, redistribution, or derived dataset publication."
            ),
            ingest_boundary=(
                "Use only as proposal-generation and curriculum metadata unless answers are independently "
                "verified. This is not a formal proof corpus by itself."
            ),
        ),
    ]

    PACKETS.write_text("\n".join(stable_json(p) for p in packets) + "\n", encoding="utf-8")
    with TABLE_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Domain", "Dataset", "Potential n-Space Application", "Source URLs", "Decision"])
        writer.writeheader()
        for p in packets:
            writer.writerow(
                {
                    "Domain": p["domain"],
                    "Dataset": p["dataset"],
                    "Potential n-Space Application": p["potential_nspace_application"],
                    "Source URLs": " | ".join(p["source_urls"]),
                    "Decision": p["decision"],
                }
            )

    receipt = {
        "schema": "nspace_bulk_dataset_route_receipt_v1",
        "packet_count": len(packets),
        "packets": str(PACKETS.relative_to(REPO)),
        "sheets_ready_csv": str(TABLE_CSV.relative_to(REPO)),
        "domains": sorted({p["domain"] for p in packets}),
        "density_marker_total": sum(len(p["density_markers"]) for p in packets),
        "ncbi_boundary": (
            "NCBI ASN.1 files contain compressed binary Bioseq-set values. GenBank flatfiles "
            "are independent flatfile dumps. Similar filenames do not imply identical records."
        ),
        "claim_boundary": (
            "This is a route registry for n-space tooling. It does not download bulk archives, "
            "prove density matrices, or assert dataset-specific licenses beyond cited source notes."
        ),
        "decision": "HOLD",
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
