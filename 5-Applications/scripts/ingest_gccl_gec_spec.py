#!/usr/bin/env python3
"""
Ingest: GCCL-GEC Spec — Full Compression Architecture
======================================================
Geometric-Cognitive Compression Law / Glyph Eigen Codec
Byte-exact compression via lawful callable glyph kernels.
"""

import json, time
from pathlib import Path

RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")

GCCL_GEC = {
    "id": "gccl-gec-spec-v1",
    "source": "USER formal spec — complete compression architecture",
    "title": "GCCL-GEC: Geometric-Cognitive Compression Law / Glyph Eigen Codec — Full Specification",
    "date": "2026-05-07",

    "purpose": (
        "Compress a byte corpus by finding the smallest lawful executable "
        "glyph/eigen/manifold program that reconstructs the exact original bytes. "
        "Do not store the text. Store the cheapest lawful generator of the byte projection."
    ),

    "archive_structure": {
        "formula": "A = D ⊕ 𝔊 ⊕ Χ ⊕ Τ ⊕ 𝕌 ⊕ Γ ⊕ Θ ⊕ Ε ⊕ R",
        "components": {
            "D": {"name": "Deterministic Decompressor", "role": "Loads profile, interprets packets, emits exact bytes"},
            "𝔊": {"name": "GlyphBook", "role": "Maps printable codepoints to callable reconstruction kernels"},
            "Χ": {"name": "ChiralityBook", "role": "Maps chirality vectors to law-axes for each glyph"},
            "Τ": {"name": "TypeBook", "role": "Maps datatype witnesses to structural generative laws"},
            "𝕌": {"name": "EigenBook", "role": "Stores reusable eigenbasis/spectrum/coefficient descriptors"},
            "Γ": {"name": "Glyph Packet Stream", "role": "Atomic compression units — not characters, but kernel invocations"},
            "Θ": {"name": "Parameter Stream", "role": "Side-stream of integer/arithmetic-coded payload data"},
            "Ε": {"name": "Residual Stream", "role": "Exact byte repair — honesty layer where speculative compressors die"},
            "R": {"name": "Receipt/Checksum/Audit", "role": "SHA256 verification + audit trail"}
        },
        "compact_equation": "C = Π_B(Bind_GCCL(𝔊, Χ, Τ, 𝕌, Γ, Θ, Ε))",
        "compact_meaning": "Corpus = byte projection of GCCL-bound kernel composition"
    },

    "fundamental_packet": {
        "formula": "Γᵢ = γᵢ ⊗ χᵢ ⊗ κᵢ ⊗ τᵢ ⊗ UᵢΛᵢaᵢ ⊗ θᵢ ⊗ εᵢ",
        "fields": {
            "γᵢ": {"name": "visible_glyph", "domain": "emoji / math symbol / PUA codepoint / Unicode printable", "meaning": "Invokes a specific reconstruction kernel"},
            "χᵢ": {"name": "chirality_vector", "domain": "⟨G_geo, G_comp, G_load, G_spec, G_topo, G_arith⟩", "meaning": "Which law-axis the glyph operates on"},
            "κᵢ": {"name": "local_context / manifold_coordinate", "domain": "position in n-D semantic manifold", "meaning": "Where in the field this packet applies"},
            "τᵢ": {"name": "datatype_witness", "domain": "TypeBook entry", "meaning": "Structural law to import (biography, math article, citation graph...)"},
            "UᵢΛᵢaᵢ": {"name": "eigen_descriptor", "domain": "EigenBook entry", "meaning": "Reusable geometric basis + spectrum + sparse coefficients"},
            "θᵢ": {"name": "parameters", "domain": "side-stream encoded integers", "meaning": "Mode selectors, eigenbook indices, residual class tags"},
            "εᵢ": {"name": "residual", "domain": "byte repair data", "meaning": "Exact correction to generated prediction"}
        },
        "core_rule": "glyph ≠ symbol. glyph = callable compression kernel."
    },

    "chirality_book": {
        "description": "Same glyph means different lawful things depending on chirality vector.",
        "vector_axes": {
            "G_geo": "geometric primitive",
            "G_comp": "mathematics article/domain macro",
            "G_spec": "eigenbasis selector",
            "G_topo": "incidence/angle graph operator",
            "G_arith": "numeric constraint kernel",
            "G_load": "expensive/fallback region marker"
        },
        "example": {
            "📐_geo": "geometric primitive",
            "📐_comp": "mathematics article/domain macro",
            "📐_spec": "eigenbasis selector",
            "📐_topo": "incidence/angle graph operator",
            "📐_arith": "numeric constraint kernel",
            "📐_load": "expensive/fallback region marker"
        },
        "power": "Finite glyph set becomes combinatorially huge through chirality rotation"
    },

    "type_book": {
        "core_rule": "The datatype is the engine. UTF-8 is only the exhaust.",
        "example_types": [
            "WikiArticle<Mathematics>",
            "WikiArticle<Biography>",
            "WikiArticle<Geography>",
            "Infobox<Person>",
            "CitationGraph",
            "SectionTree",
            "HistoricalTimeline",
            "BranchTaxonomy",
            "TableMatrix",
            "SameReferentCluster",
            "FormulaRegion",
            "ListRegion",
            "MarkupRegion"
        ],
        "compression_mass": "WikiArticle<Biography> already implies title, lead, infobox, birth/death fields, occupation, chronology, categories, citation patterns, linking conventions. The datatype itself carries structure.",
        "value": "A type imports generative structure without storing every instance explicitly."
    },

    "eigen_book": {
        "formula": "Gᵢ = ⟨τᵢ, Uᵢ, Λᵢ, aᵢ, εᵢ⟩",
        "components": {
            "τᵢ": "manifold/type class",
            "Uᵢ": "eigenbasis / local frame (column vectors)",
            "Λᵢ": "eigenvalue spectrum / scale-pressure",
            "aᵢ": "sparse coefficients (activation weights)",
            "εᵢ": "residual bytes (perturbation from ideal eigenstate)"
        },
        "example_math_article": {
            "U": ["u_definition", "u_taxonomy", "u_history", "u_notation", "u_application", "u_philosophy", "u_reference"],
            "meaning": "A mathematics page ≈ sparse activation of these eigenmodes + residual repair"
        },
        "keeper": "A wiki page is a sparse eigenstate of a typed reconstruction manifold, plus apology bytes."
    },

    "parameter_encoding": {
        "channels": [
            "side streams",
            "variation selectors",
            "combining marks",
            "PUA suffixes",
            "integer-coded payloads",
            "arithmetic-coded payloads"
        ],
        "example": "📐︖︉︚ → MathDomainKernel(mode=22, eigenbook=9, residual_class=26)",
        "rule": "Decompressor reads codepoints, not what fonts display."
    },

    "residual_stream": {
        "role": "The most important honesty layer.",
        "core_rule": "Decode(generative_model) ⊕ ε = exact original bytes",
        "forms": [
            "literal patch",
            "XOR patch",
            "edit script",
            "structural diff",
            "entropy-coded correction",
            "markup repair",
            "serialization repair"
        ],
        "diagnostic": "ρ = |ε| / |raw_span|. ρ < 0.1 = excellent. ρ ≈ 0.5 = maybe useful. ρ ≈ 1.0 = generator failed."
    },

    "gccl_gain_test": {
        "formula": "ΔGCL(Γᵢ) = ΔG_geo + ΔG_comp + ΔG_spec + ΔG_topo + ΔG_arith - G_load - L(εᵢ) - L(θᵢ) - amortized_decoder_cost",
        "accept_rule": "ΔGCL(Γᵢ) > 0",
        "practical_form": "gain(Γᵢ) = literal_cost(span) - encoded_cost(γᵢ, χᵢ, κᵢ, τᵢ, UΛa, θᵢ, εᵢ)",
        "principle": "No vibes. No 'semantic compression' handwaving. Only: shorter, deterministic, byte-exact, auditable."
    },

    "decode_pipeline": [
        "Load decompressor profile D",
        "Load GlyphBook 𝔊",
        "Load ChiralityBook Χ",
        "Load TypeBook Τ",
        "Load EigenBook 𝕌",
        "Read region index I",
        "For each Γᵢ: resolve glyph γᵢ, chirality χᵢ, type τᵢ, eigen descriptor UᵢΛᵢaᵢ, parameters θᵢ",
        "Generate predicted byte span ŝᵢ",
        "Apply residual εᵢ",
        "Emit exact span sᵢ",
        "Concatenate spans",
        "Verify checksum / receipt"
    ],

    "encode_pipeline": [
        "Segment corpus into candidate spans (pages, sections, infoboxes, tables, citations, formulas, markup regions)",
        "Infer candidate types τ",
        "Fit candidate geometric model (choose U, Λ, a)",
        "Choose glyph kernel γ and chirality χ",
        "Generate predicted bytes",
        "Compute residual ε",
        "Score: gain = literal_cost - encoded_cost",
        "Keep candidates with gain > 0",
        "Solve covering problem: choose packet set Γ* covering C with minimum total cost",
        "Emit archive",
        "Decode immediately and verify exact byte equality"
    ],

    "model_families": {
        "A_Wiki_structural": {
            "kernels": ["WikiArticle", "Infobox", "SectionTree", "CitationGraph", "CategoryList", "InternalLinkGraph", "ReferenceList", "TableMatrix"],
            "value": "Highest practical value. Structural redundancy in encyclopedic corpora is massive."
        },
        "B_Same_referent": {
            "kernels": ["SameReferentVariation", "EntityAliasCluster", "PronounEpithetChain"],
            "value": "Handles elegant-variation / synonym-heavy text where literal repetition is low."
        },
        "C_Arithmetic_date": {
            "kernels": ["Year", "DateInterval", "Coordinate", "PopulationTable", "UnitExpression", "Ranking", "Ordinal"],
            "value": "Numbers are dense but highly structured. Very reliable wins."
        },
        "D_Fractal_generator": {
            "kernels": ["Mandelbrot", "L-system", "CellularAutomaton", "ProceduralImage", "ParametricCurve"],
            "value": "Only useful if byte projection matches generator closely. SVG serialization cost usually dominates."
        },
        "E_Eigenfield": {
            "kernels": ["ArticleEigenfield", "CitationEigenfield", "MarkupEigenfield", "SemanticDensityField"],
            "value": "Region-level reconstruction. Connects to density-field encoding theory."
        }
    },

    "stress_test_lesson": {
        "mandelbrot_svg": "generator cost ≈ tiny, serialized artifact cost ≈ huge",
        "conclusion": "z ↦ z² + c generates the image, but not the exact SVG file. Residual = ε_serialize.",
        "best_diagnostic": "ρ = |ε| / |raw_span|"
    },

    "implementation_phases": {
        "Phase_1": {
            "name": "Byte-exact toy codec",
            "scope": "GlyphBook + TypeBook + ResidualStream",
            "kernels": ["CitationGraphKernel", "InfoboxKernel", "SectionTreeKernel"],
            "goal": "generated_span + residual = original_span"
        },
        "Phase_2": {
            "name": "Add arithmetic/date kernels",
            "scope": "Years, dates, coordinates, measurements, rankings, table values",
            "value": "Reliable wins on dense numeric data"
        },
        "Phase_3": {
            "name": "Add same-referent variation",
            "scope": "EntityClusterKernel, AliasEmitter, CoreferenceSurfaceFormKernel",
            "value": "Attacks low-repetition text"
        },
        "Phase_4": {
            "name": "Add eigen descriptors",
            "scope": "UΛa for region classes",
            "caution": "Only after above works. Use as descriptor reuse, not magic semantic compression."
        },
        "Phase_5": {
            "name": "Add PUA glyph acceleration",
            "rule": "promotion_gain = repeated_invocation_savings - glyph_definition_cost. Promote only if positive."
        }
    },

    "prototype_archive": {
        "magic": "GEC1",
        "struct_fields": ["decoder_profile", "glyphbook", "typebook", "packets", "params", "residuals", "sha256"],
        "packet_fields": ["glyph_id: u32", "chirality: u8", "type_id: u16", "region_start: u64", "region_len: u32", "eigen_id: Option<u16>", "param_ref", "residual_ref"],
        "decode_invariant": "sha256(decode(archive)) == sha256(original)"
    },

    "stack_integration": {
        "density_field_encoding": {
            "role": "REGION-LEVEL MODEL FAMILY E. The density field IS an eigenfield kernel.",
            "mapping": "ρ(x⃗) = SemanticDensityField kernel. Topological skeleton = GlyphBook + EigenBook. Perturbation = ResidualStream."
        },
        "s3c_shells": {
            "role": "LOCAL COORDINATE κᵢ. Shell index k = semantic distance from peak (e.g., article title). a = intra-cluster angular position.",
            "mapping": "κᵢ encoded as S3C shell coordinates: cheap integer manifold position."
        },
        "oac": {
            "role": "GLYPH KERNEL LAZINESS. A glyph is a callable kernel stored in the OAC. It only materializes when touched by the decoder pipeline.",
            "mapping": "GlyphBook = library of OAC touch-manifestable kernels. Chirality = which touch interpretation."
        },
        "hypercube_rhomboid": {
            "role": "MANIFOLD GEOMETRY OF THE PACKET STREAM. UTF-8 is orthogonal hypercube (independent byte positions). GCCL-GEC is sheared hyper-rhomboid: each packet's meaning depends on neighboring packets through chirality and type context.",
            "mapping": "Shear matrix learned from corpus: eigenvectors = principal semantic directions. Packets lean into each other."
        },
        "famm_delay_lines": {
            "role": "TEMPORAL SEQUENCING OF PACKET STREAM. FAMM preshaped delays impose decode order through the packet stream.",
            "mapping": "Delay profile = path integral through packet dependencies. Fast regions = high structural redundancy (predictable). Slow regions = high residual density (needs more context)."
        },
        "erans_entropy": {
            "role": "RESIDUAL AND PARAMETER STREAM CODING. After glyph prediction, residual bytes and parameters are entropy-coded via enumerative rANS.",
            "mapping": "Histogram of residuals is exact; erans enumerative coding is optimal for exact histograms."
        },
        "radius_ratio_motif": {
            "role": "LOCAL ADMISSIBILITY QUANTIZER FOR PACKET SELECTION. Given a local feature ratio ρ, the radius-ratio rule selects the smallest stable coordination motif (kernel).",
            "mapping": "Local scale ratio → admissible kernel class (WikiArticle, Infobox, CitationGraph...) + residual. Same move: continuous witness → finite motif alphabet."
        }
    },

    "keeper_phrases": [
        "Do not store the text. Store the cheapest lawful generator of the byte projection.",
        "glyph ≠ symbol. glyph = callable compression kernel.",
        "The datatype is the engine. UTF-8 is only the exhaust.",
        "A wiki page is a sparse eigenstate of a typed reconstruction manifold, plus apology bytes.",
        "Never trust a glyph until the residual gets smaller.",
        "No vibes. No 'semantic compression' handwaving. Only: shorter, deterministic, byte-exact, auditable.",
        "ρ = |ε| / |raw_span|. This is the only number that matters.",
        "The decompressor reads codepoints, not what fonts display.",
        "A finite glyph set becomes combinatorially huge because each glyph can rotate through many law-axes.",
        "The Morse-Smale complex is the topological skeleton of meaning. GCCL-GEC is the lawful engine that navigates it."
    ],

    "metadata": {
        "ingested_at": time.time(),
        "tags": [
            "gccl-gec", "compression-architecture", "glyph-eigen-codec",
            "byte-exact-compression", "callable-kernel", "chirality-book",
            "type-book", "eigen-book", "residual-stream", "gain-test",
            "hutter-prize", "density-field", "s3c-shells", "oac",
            "hypercube-rhomboid", "famm", "erans", "radius-ratio",
            "geometric-compression"
        ]
    }
}


def ingest():
    germane_dir = RESEARCH_STACK / "shared-data/data/germane/research"
    germane_dir.mkdir(parents=True, exist_ok=True)

    out_path = germane_dir / "gccl_gec_spec_v1.json"
    with open(out_path, 'w') as f:
        json.dump(GCCL_GEC, f, indent=2)

    print(f"✓ Ingested: {out_path}")

    index_path = germane_dir / "research_ingestion_index.json"
    index = []
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)

    index.append({
        "id": GCCL_GEC["id"],
        "title": GCCL_GEC["title"],
        "date": GCCL_GEC["date"],
        "source": GCCL_GEC["source"],
        "ingested_at": GCCL_GEC["metadata"]["ingested_at"],
        "tags": GCCL_GEC["metadata"]["tags"],
    })

    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)

    print(f"✓ Index: {len(index)} entries")

    print(f"\nArchive components (9):")
    for k, v in GCCL_GEC["archive_structure"]["components"].items():
        print(f"  {k} = {v['name']}: {v['role'][:60]}...")

    print(f"\nPacket fields (7):")
    for field, props in GCCL_GEC["fundamental_packet"]["fields"].items():
        print(f"  {field} → {props['name']}: {props['meaning'][:50]}...")

    print(f"\nModel families (5):")
    for fam, data in GCCL_GEC["model_families"].items():
        print(f"  {fam}: {len(data['kernels'])} kernels — {data['value'][:50]}...")

    print(f"\nStack integration (7):")
    for module, mapping in GCCL_GEC["stack_integration"].items():
        print(f"  ↔ {module}: {mapping['role'][:65]}...")

    print(f"\nImplementation phases (5):")
    for phase, data in GCCL_GEC["implementation_phases"].items():
        print(f"  {phase}: {data['name']} — {data.get('goal', data.get('value', data.get('scope', '')))[:50]}...")

    print(f"\nKeeper phrases ({len(GCCL_GEC['keeper_phrases'])}):")
    for p in GCCL_GEC["keeper_phrases"]:
        print(f"  → {p}")


if __name__ == "__main__":
    ingest()
