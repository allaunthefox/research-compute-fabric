#!/usr/bin/env python3
"""
classify_domains.py — Add Domain_Type classification to MATH_MODEL_MAP.tsv

Domain taxonomy derived from the Topological Tape Machine specification:
  LAYER_A_COMPRESSION    — Representation selection, entropy, encoding, compression objectives
  LAYER_B_ROUTING        — Cognitive load, mixture-of-experts, predictor distribution, decision reweighting
  LAYER_C_TOPOLOGY       — Metric tensors, geodesics, manifolds, curvature, Christoffel, charts
  LAYER_C_BRAID          — Braid formation, witness traces, Merkle structures, raycasting, holonomy
  LAYER_D_INVARIANTS     — Invariant vectors, conservation laws, constraint systems, survival masks
  LAYER_E_VERIFICATION   — Acceptance predicates, attestation, BEA consensus, validation checks
  LAYER_F_CONTROL        — Homeostatic control, hysteresis, mode transitions, waveprobe risk, pressure dynamics
  LAYER_G_ENERGY         — Thermodynamics, Landauer, Carnot, phonon physics, QCL energy, hardware stress
  LAYER_H_ALGEBRA        — Geometric algebra, chirality, group theory, finite fields, semirings
  LAYER_I_ENCODING       — Voxel keys, microvoxel seeds, bit-packing, address schemes, quantization
  LAYER_J_DYNAMICS       — Time evolution, phase transitions, emergence, Langevin, deformation fields
  LAYER_K_SIGNAL         — DSP, FFT, wave propagation, scattering, Rayleigh, phased arrays
  LAYER_L_APPLICATION    — FEA, hormone mapping, semi-truck physics, engineering models

Each model is classified into exactly ONE primary domain.
"""

import csv
import sys

# Domain classification rules: (model_number_range_or_name_keywords, domain_type)
# Using model number ranges for bulk assignment, with keyword overrides.

DOMAIN_MAP = {
    # LAYER_A: Compression / Representation Selection (models 1-2, 6-10, 33, 44, 54, 71, 74, 102, 126)
    "1":  "LAYER_A_COMPRESSION",
    "2":  "LAYER_A_COMPRESSION",
    "6":  "LAYER_A_COMPRESSION",
    "7":  "LAYER_A_COMPRESSION",
    "8":  "LAYER_A_COMPRESSION",
    "9":  "LAYER_A_COMPRESSION",
    "10": "LAYER_A_COMPRESSION",
    "33": "LAYER_A_COMPRESSION",
    "44": "LAYER_A_COMPRESSION",
    "54": "LAYER_A_COMPRESSION",
    "71": "LAYER_A_COMPRESSION",
    "74": "LAYER_A_COMPRESSION",
    "102":"LAYER_A_COMPRESSION",
    "126":"LAYER_A_COMPRESSION",

    # LAYER_B: Routing / Cognitive Load (models 3-5, 32, 45, 48, 50, 72-73, 75, 95, 98-101, 120-121, 137)
    "3":  "LAYER_B_ROUTING",
    "4":  "LAYER_B_ROUTING",
    "5":  "LAYER_B_ROUTING",
    "32": "LAYER_B_ROUTING",
    "45": "LAYER_B_ROUTING",
    "48": "LAYER_B_ROUTING",
    "50": "LAYER_B_ROUTING",
    "72": "LAYER_B_ROUTING",
    "73": "LAYER_B_ROUTING",
    "75": "LAYER_B_ROUTING",
    "95": "LAYER_B_ROUTING",
    "98": "LAYER_B_ROUTING",
    "99": "LAYER_B_ROUTING",
    "100":"LAYER_B_ROUTING",
    "101":"LAYER_B_ROUTING",
    "120":"LAYER_B_ROUTING",
    "121":"LAYER_B_ROUTING",
    "137":"LAYER_B_ROUTING",

    # LAYER_C_TOPOLOGY: Metric tensors, geodesics, manifolds, curvature (models 16-18, 25, 34, 38, 46, 82-89, 96-97, 105-107, 115-117, 119, 135-136)
    "16": "LAYER_C_TOPOLOGY",
    "17": "LAYER_C_TOPOLOGY",
    "18": "LAYER_C_TOPOLOGY",
    "25": "LAYER_C_TOPOLOGY",
    "34": "LAYER_C_TOPOLOGY",
    "38": "LAYER_C_TOPOLOGY",
    "46": "LAYER_C_TOPOLOGY",
    "82": "LAYER_C_TOPOLOGY",
    "83": "LAYER_C_TOPOLOGY",
    "84": "LAYER_C_TOPOLOGY",
    "85": "LAYER_C_TOPOLOGY",
    "86": "LAYER_C_TOPOLOGY",
    "87": "LAYER_C_TOPOLOGY",
    "88": "LAYER_C_TOPOLOGY",
    "89": "LAYER_C_TOPOLOGY",
    "96": "LAYER_C_TOPOLOGY",
    "97": "LAYER_C_TOPOLOGY",
    "105":"LAYER_C_TOPOLOGY",
    "106":"LAYER_C_TOPOLOGY",
    "107":"LAYER_C_TOPOLOGY",
    "115":"LAYER_C_TOPOLOGY",
    "116":"LAYER_C_TOPOLOGY",
    "117":"LAYER_C_TOPOLOGY",
    "119":"LAYER_C_TOPOLOGY",
    "135":"LAYER_C_TOPOLOGY",
    "136":"LAYER_C_TOPOLOGY",

    # LAYER_C_BRAID: Braid formation, witnesses, raycasting, holonomy (models 35-37, 39, 76-78, 110-112, 130)
    "35": "LAYER_C_BRAID",
    "36": "LAYER_C_BRAID",
    "37": "LAYER_C_BRAID",
    "39": "LAYER_C_BRAID",
    "76": "LAYER_C_BRAID",
    "77": "LAYER_C_BRAID",
    "78": "LAYER_C_BRAID",
    "110":"LAYER_C_BRAID",
    "111":"LAYER_C_BRAID",
    "112":"LAYER_C_BRAID",
    "130":"LAYER_C_BRAID",

    # LAYER_D_INVARIANTS: Conservation laws, constraint systems (models 28, 30-31, 43, 56, 61-63, 111, 127-128)
    "28": "LAYER_D_INVARIANTS",
    "30": "LAYER_D_INVARIANTS",
    "31": "LAYER_D_INVARIANTS",
    "43": "LAYER_D_INVARIANTS",
    "56": "LAYER_D_INVARIANTS",
    "61": "LAYER_D_INVARIANTS",
    "62": "LAYER_D_INVARIANTS",
    "63": "LAYER_D_INVARIANTS",
    "127":"LAYER_D_INVARIANTS",
    "128":"LAYER_D_INVARIANTS",

    # LAYER_E_VERIFICATION: Acceptance, attestation, BEA, validation (models 11, 14-15, 55, 60, 94, 125, 138)
    "11": "LAYER_E_VERIFICATION",
    "14": "LAYER_E_VERIFICATION",
    "15": "LAYER_E_VERIFICATION",
    "55": "LAYER_E_VERIFICATION",
    "60": "LAYER_E_VERIFICATION",
    "94": "LAYER_E_VERIFICATION",
    "125":"LAYER_E_VERIFICATION",
    "138":"LAYER_E_VERIFICATION",

    # LAYER_F_CONTROL: Homeostatic, hysteresis, waveprobe, mode transitions (models 7, 12, 24, 26-29, 49, 88, 90-93, 131-134)
    "24": "LAYER_F_CONTROL",
    "26": "LAYER_F_CONTROL",
    "27": "LAYER_F_CONTROL",
    "29": "LAYER_F_CONTROL",
    "49": "LAYER_F_CONTROL",
    "90": "LAYER_F_CONTROL",
    "91": "LAYER_F_CONTROL",
    "92": "LAYER_F_CONTROL",
    "93": "LAYER_F_CONTROL",
    "131":"LAYER_F_CONTROL",
    "132":"LAYER_F_CONTROL",
    "133":"LAYER_F_CONTROL",
    "134":"LAYER_F_CONTROL",

    # LAYER_G_ENERGY: Thermodynamics, Landauer, phonon, QCL, hardware stress (models 13, 20-23, 39-42, 47, 51-53, 57-59, 64-70, 108-109, 113-114, 139-140)
    "13": "LAYER_G_ENERGY",
    "20": "LAYER_G_ENERGY",
    "21": "LAYER_G_ENERGY",
    "22": "LAYER_G_ENERGY",
    "23": "LAYER_G_ENERGY",
    "39": "LAYER_G_ENERGY",
    "40": "LAYER_G_ENERGY",
    "41": "LAYER_G_ENERGY",
    "42": "LAYER_G_ENERGY",
    "47": "LAYER_G_ENERGY",
    "51": "LAYER_G_ENERGY",
    "52": "LAYER_G_ENERGY",
    "53": "LAYER_G_ENERGY",
    "57": "LAYER_G_ENERGY",
    "58": "LAYER_G_ENERGY",
    "59": "LAYER_G_ENERGY",
    "64": "LAYER_G_ENERGY",
    "65": "LAYER_G_ENERGY",
    "66": "LAYER_G_ENERGY",
    "67": "LAYER_G_ENERGY",
    "68": "LAYER_G_ENERGY",
    "69": "LAYER_G_ENERGY",
    "70": "LAYER_G_ENERGY",
    "108":"LAYER_G_ENERGY",
    "109":"LAYER_G_ENERGY",
    "113":"LAYER_G_ENERGY",
    "114":"LAYER_G_ENERGY",
    "139":"LAYER_G_ENERGY",
    "140":"LAYER_G_ENERGY",

    # LAYER_H_ALGEBRA: Geometric algebra, chirality, group theory (models 19, 21-23, 43, 117-119)
    "19": "LAYER_H_ALGEBRA",
    "21": "LAYER_H_ALGEBRA",
    "22": "LAYER_H_ALGEBRA",
    "23": "LAYER_H_ALGEBRA",
    "43": "LAYER_H_ALGEBRA",
    "117":"LAYER_H_ALGEBRA",
    "118":"LAYER_H_ALGEBRA",
    "119":"LAYER_H_ALGEBRA",

    # LAYER_I_ENCODING: Voxel keys, microvoxel, bit-packing, address schemes (models 123-124, 129)
    "123":"LAYER_I_ENCODING",
    "124":"LAYER_I_ENCODING",
    "129":"LAYER_I_ENCODING",

    # LAYER_J_DYNAMICS: Time evolution, phase transitions, emergence, deformation (models 8-9, 33, 44, 56, 71, 74, 103-104, 131-132)
    "103":"LAYER_J_DYNAMICS",
    "104":"LAYER_J_DYNAMICS",

    # LAYER_K_SIGNAL: DSP, FFT, wave propagation, scattering (models 79-81, 113-114)
    "79": "LAYER_K_SIGNAL",
    "80": "LAYER_K_SIGNAL",
    "81": "LAYER_K_SIGNAL",

    # LAYER_L_APPLICATION: FEA, hormone mapping, engineering (models 45, 120-122, 137)
    "122":"LAYER_L_APPLICATION",
}


def classify_domain(model_num: str, model_name: str, family: str) -> str:
    """Classify a model into its TTM domain layer."""
    # Direct number lookup
    if model_num in DOMAIN_MAP:
        return DOMAIN_MAP[model_num]

    # Keyword fallbacks for unclassified models
    name_lower = (model_name + " " + family).lower()

    if any(k in name_lower for k in ["compression", "entropy", "shannon", "hutter", "shape", "mi ", "mutual information", "structure yield", "watanabe", "kolmogorov"]):
        return "LAYER_A_COMPRESSION"
    if any(k in name_lower for k in ["routing", "cognitive", "load", "homeostatic", "pressure", "canal", "reweight", "equilibrium", "logit", "hormone", "half life", "decay rate", "concentration"]):
        return "LAYER_B_ROUTING"
    if any(k in name_lower for k in ["metric", "geodesic", "manifold", "curvature", "christoffel", "chart", "stereographic", "phi", "phi-weighted", "hyperbolic", "mobius", "non-euclidean", "writhe", "parallel transport", "pga", "geometric algebra", "sine-gordon", "curvature-torsion", "constraint geometry", "universe type scoring", "mean curvature"]):
        return "LAYER_C_TOPOLOGY"
    if any(k in name_lower for k in ["braid", "raycast", "ray-cast", "mmr", "merkle", "holonomy", "algebraic", "rollup", "diat", "uvmap", "half-mobius closure"]):
        return "LAYER_C_BRAID"
    if any(k in name_lower for k in ["invariant", "constraint", "conservation", "exact", "narrowing", "precision", "latency table", "sieve", "relation", "proxy"]):
        return "LAYER_D_INVARIANTS"
    if any(k in name_lower for k in ["verification", "attestation", "bea", "witness", "acceptance", "q-factor", "landauer", "surprise", "regret", "blink", "ternary", "dcvn", "thermal finality"]):
        return "LAYER_E_VERIFICATION"
    if any(k in name_lower for k in ["control", "hysteresis", "waveprobe", "risk", "heat evolution", "mode transition", "binning", "lut policy", "regret field", "blink cycle", "phase transition", "emergence"]):
        return "LAYER_F_CONTROL"
    if any(k in name_lower for k in ["thermodynamic", "arrhenius", "black", "coffin-manson", "bit-flip", "qcl", "quantum cascade", "photon", "energy", "phonon", "boltzmann", "carnot", "heat engine", "entropy generation", "rul", "remaining useful", "alcubierre", "dyson", "langevin"]):
        return "LAYER_G_ENERGY"
    if any(k in name_lower for k in ["chirality", "cl(3,0,1)", "geometric product", "motor", "clifford"]):
        return "LAYER_H_ALGEBRA"
    if any(k in name_lower for k in ["voxel", "microvoxel", "encoding", "seed", "bit", "pack", "address", "seismic", "topological encoder"]):
        return "LAYER_I_ENCODING"
    if any(k in name_lower for k in ["deformation", "epoch", "sha256 field", "manifold delta"]):
        return "LAYER_J_DYNAMICS"
    if any(k in name_lower for k in ["bracket", "braid sb", "cosine similarity", "gradient alignment", "phase accumulation", "dsp", "fft"]):
        return "LAYER_K_SIGNAL"
    if any(k in name_lower for k in ["fea", "hormone", "semi-truck", "dynamic amplification", "engineering"]):
        return "LAYER_L_APPLICATION"

    return "UNCLASSIFIED"


def main():
    input_path = "6-Documentation/docs/MATH_MODEL_MAP.tsv"
    output_path = "6-Documentation/docs/MATH_MODEL_MAP_classified.tsv"

    with open(input_path, "r", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        rows = list(reader)

    # Find the comment line (starts with #)
    comment_lines = []
    data_rows = []
    for row in rows:
        if row and row[0].startswith("#"):
            comment_lines.append(row)
        else:
            data_rows.append(row)

    # Add Domain_Type column to header
    header.append("Domain_Type")

    # Classify each row
    classified = 0
    unclassified = 0
    domain_counts = {}
    for row in data_rows:
        model_num = row[0].strip() if row else ""
        model_name = row[1].strip() if len(row) > 1 else ""
        family = row[2].strip() if len(row) > 2 else ""

        domain = classify_domain(model_num, model_name, family)
        row.append(domain)

        if domain == "UNCLASSIFIED":
            unclassified += 1
        else:
            classified += 1
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

    # Write output
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        for cl in comment_lines:
            writer.writerow(cl)
        writer.writerow(header)
        for row in data_rows:
            writer.writerow(row)

    # Summary
    print(f"Classified {classified}/{classified + unclassified} models")
    if unclassified:
        print(f"WARNING: {unclassified} models UNCLASSIFIED")
    print()
    print("Domain distribution:")
    for domain in sorted(domain_counts.keys()):
        print(f"  {domain:30s} {domain_counts[domain]:3d}")

    print(f"\nOutput written to: {output_path}")


if __name__ == "__main__":
    main()
