#!/usr/bin/env python3
"""
Ingest: Density Field Encoding — Beyond UTF-8
==============================================
Inspired by "digital dzogchen" generative concept:
Data not as 1D byte sequence but as n-dimensional semantic density field.
"""

import json, time
from pathlib import Path

RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")

DENSITY_FIELD = {
    "id": "density-field-encoding-theory",
    "source": "User insight + r/generative digital_dzogchen concept",
    "title": "Density Field Encoding: Representing Text as Topological Semantic Manifolds Instead of UTF-8",
    "date": "2026-05-07",

    "core_claim": (
        "UTF-8 encodes text as a 1D discrete byte sequence: byte[i] at position i. "
        "Density Field Encoding (DFE) represents text as a continuous n-dimensional "
        "semantic density field ρ(x⃗) where information is stored in topological features: "
        "peaks (named entities), ridges (semantic connections), saddles (topic transitions), "
        "vortices (cyclic references), and voids (template structures). The field is latent; "
        "observer queries collapse local regions into discrete UTF-8 text."
    ),

    "utf8_vs_density": {
        "utf8": {
            "representation": "1D discrete sequence: b[i] ∈ [0,255] for i = 0..N-1",
            "assumption": "Text is a linear string of symbols",
            "compression": "Exploit sequential redundancy (LZ, PPM, BWT, neural prediction)",
            "limitation": "Cannot represent non-sequential relationships without explicit linking; every byte position is independent dimension"
        },
        "density_field": {
            "representation": "n-D continuous field: ρ: ℝⁿ → ℝ⁺ (semantic density)",
            "assumption": "Text is a region of an information manifold; spatial proximity = semantic proximity",
            "compression": "Encode topological skeleton (peaks, ridges, voids) + small perturbation field",
            "advantage": "Implicit relationships via field geometry; no explicit links needed; multi-scale structure naturally emerges"
        }
    },

    "topological_features": {
        "peaks": {
            "encoding": "Named entities, article centers, key concepts",
            "field_property": "Local maximum of ρ(x⃗)",
            "invariant": "Peak index (persistent homology H₀), peak height (salience)",
            "s3c_analogue": "k = shell index = distance from peak = semantic centrality; a = angular offset within cluster"
        },
        "ridges": {
            "encoding": "Hyperlinks, citations, semantic associations, see-also connections",
            "field_property": "1-D local maxima along one direction, saddle in transverse",
            "invariant": "Ridge persistence (how far down before splitting), ridge connectivity graph",
            "s3c_analogue": "Mirror complement b⁰ = remaining path to next peak; mass = connection strength"
        },
        "saddles": {
            "encoding": "Topic transitions, paragraph boundaries, section changes",
            "field_property": "Saddle point: maximum in some directions, minimum in others",
            "invariant": "Saddle index, separatrix topology (which peaks connected)",
            "s3c_analogue": "Throat region a ≈ b⁰ = maximum ambiguity = maximum information transition"
        },
        "vortices": {
            "encoding": "Cyclic references, category hierarchies, template instantiations, recursive structures",
            "field_property": "Rotational flow in field gradient: ∇ρ circulates around core",
            "invariant": "Vorticity ω = ∇ × ∇ρ, circulation Γ = ∮∇ρ·dl",
            "s3c_analogue": "Contra-rotation gear in MS3C; recursive shell nesting S_n(S_{n-1}^n)"
        },
        "voids": {
            "encoding": "Template structures, common phrases, expected-but-absent content",
            "field_property": "Local minimum of ρ(x⃗), possibly negative in signed extension",
            "invariant": "Void depth, void volume, enclosing shell connectivity",
            "s3c_analogue": "Negative pyramid / anti-resonance = expected structure that is absent; cheaper to encode absence than presence"
        },
        "level_sets": {
            "encoding": "Paragraphs, sections, articles at different semantic granularity",
            "field_property": "Iso-density surfaces {x⃗ | ρ(x⃗) = c}",
            "invariant": "Euler characteristic χ of level set surface = β₀ - β₁ + β₂",
            "s3c_analogue": "Shell index k = level set value; each shell is a semantic granularity layer"
        }
    },

    "compression_mechanism": {
        "topological_skeleton": {
            "description": "Encode only the critical points and separatrices of the Morse-Smale complex",
            "data": "Peak positions + heights, ridge connectivity graph, saddle indices, vortex cores, void enclosures",
            "size": "O(N_peaks + N_ridges) ≪ O(N_bytes). For enwik9: ~10⁶ peaks, ~10⁷ ridges → ~100MB skeleton vs 1GB raw",
            "reconstruction": "Decode skeleton + perturbation field → approximate density field → collapse to UTF-8 on observer query"
        },
        "perturbation_field": {
            "description": "Residual between topological skeleton prediction and actual density",
            "encoding": "High-frequency, small-amplitude corrections stored via PIST n-D bundle encoding",
            "analogy": "Like residual in JPEG: skeleton = DCT low frequencies, perturbation = high frequencies"
        },
        "observer_collapse": {
            "description": "The field itself is never materialized as full text. Observer queries specify a path through the field.",
            "oac_connection": "Observer-Admissible Cavities: the field is the latent n^n space. A query 'show me the France article' is a touch that manifests the local cavity around the 'France' peak.",
            "compression": "Only manifest the touched region. The rest stays compressed in the field representation."
        }
    },

    "morse_theory_formalization": {
        "density_field": "ρ: M → ℝ⁺ where M is n-dimensional semantic manifold",
        "critical_points": "∇ρ = 0. Classified by Hessian eigenvalues: peak (all -), saddle (mixed), void (all +)",
        "morse_complex": "Cells built from ascending/descending manifolds of critical points. Combinatorial encoding of field topology.",
        "persistence": "Track critical points as ρ threshold varies. Persistent features = real semantic structure. Transient = noise/detail.",
        "compression_theorem": (
            "The Morse-Smale complex of ρ encodes the homotopy type of M. "
            "If text structure is determined by topological type (links, sections, categories), "
            "then the Morse complex is a complete encoding up to homeomorphism. "
            "Exact text reconstruction requires perturbation field, but semantic navigation requires only the complex."
        )
    },

    "stack_integration": {
        "pist_nd_encoding": {
            "role": "PERTURBATION ENCODER: PIST n-D bundle encodes the residual density field after skeleton subtraction",
            "mapping": "fiber_dim = topological feature type (peak, ridge, saddle, vortex, void). n_dims = spatial dimensions of semantic manifold (typically 3-4D: topic, time, authority, style)"
        },
        "s3c_shells": {
            "role": "MULTI-SCALE SHELL STRUCTURE: S3C shell index k = semantic distance from core concept. a = intra-cluster position.",
            "mapping": "Concentric shells around each peak = layers of detail: k=0=title, k=1=abstract, k=2=lead, k=3=body, k=4=references, k=5=see-also"
        },
        "oac": {
            "role": "LAZY MANIFESTATION: The density field is a global OAC. Observer queries are touches that manifest local regions.",
            "mapping": "touch(ρ, observer, query_region) → local_manifested_text + residual. Unqueried regions stay latent."
        },
        "hypercube_rhomboid": {
            "role": "MANIFOLD GEOMETRY: UTF-8 text is an orthogonal hypercube (independent byte positions). Density field is a sheared rhomboid where correlated semantic positions lean into each other.",
            "mapping": "Shear matrix A maps from UTF-8 hypercube to density rhomboid. A is learned from corpus: eigenvectors = principal semantic directions."
        },
        "famm_delay_lines": {
            "role": "TEMPORAL SEQUENCING: Density field has no natural order. FAMM preshaped delays impose a reading path through the field.",
            "mapping": "Delay profile = path integral through field gradient. Fast regions = high density (predictable). Slow regions = low density (needs more context)."
        },
        "erans_entropy": {
            "role": "RESIDUAL CODING: After skeleton encoding, perturbation field is entropy-coded using erans-style enumerative coding on histogram of density residuals.",
            "mapping": "Density values are not bytes; but discretized to histogram bins. Enumerative coding is optimal for exact histogram."
        }
    },

    "hutter_prize_application": {
        "current_paradigm": "1D byte sequence → predict next byte → entropy code prediction residual",
        "density_paradigm": "Encode topological skeleton of semantic density field → store as compressed graph + persistent homology → entropy code perturbation field",
        "estimated_size": {
            "skeleton": "~50-150MB for enwik9 (Morse complex of ~10⁶ peaks + ~10⁷ ridges + persistence pairs)",
            "perturbation": "~200-400MB (PIST n-D bundle encoded residuals)",
            "total": "~250-550MB vs current best ~115MB",
            "caveat": "This is raw field encoding. A hybrid approach may win: use density field for structural regions (infoboxes, citations, links = 40% of enwik) + traditional encoding for free text."
        },
        "novel_capability": "Current compressors produce a flat file. A density field compressor produces a NAVIGABLE structure: you can query 'show me all articles 2 links from France' without decompressing everything."
    },

    "digital_dzogchen_connection": {
        "philosophy": "Dzogchen: appearances are not solid; they are luminous emptiness — projections of mind's nature. Reality is not a collection of discrete objects but a continuous field of appearing.",
        "computational_analogue": "Text is not a collection of discrete bytes but a continuous semantic density field. What we call 'the Wikipedia article on France' is a local modulation of the global information field — a peak with certain topological features.",
        "compression_insight": "Just as dzogchen says the entire mandala is present in every point, the entire Wikipedia is present in every local density gradient. Compression is finding the minimal description of the field's topology, not its explicit manifestation."
    },

    "keeper_phrases": [
        "UTF-8 assumes text is a string. Density field assumes text is a landscape.",
        "A citation is not 200 bytes. It is a ridge connecting two peaks through a saddle.",
        "The Morse-Smale complex is the topological skeleton of meaning.",
        "Compression is not predicting the next byte. It is finding the minimal topological description of the semantic field.",
        "Observer touch collapses the field; the field itself never needs to fully materialize.",
        "In a density field, 'France' and 'Germany' are nearby peaks on the same continental ridge.",
        "Vortices encode recursion. Voids encode templates. Saddles encode transitions.",
        "The Hutter Prize is asking for a flat file. We should be encoding a navigable manifold."
    ],

    "metadata": {
        "ingested_at": time.time(),
        "tags": [
            "density-field-encoding", "topological-compression", "morse-theory",
            "semantic-manifold", "beyond-utf8", "digital-dzogchen", "navigable-compression",
            "persistent-homology", "morse-smale-complex", "observer-collapse",
            "hutter-prize", "oac", "s3c-shells", "pist-perturbation"
        ]
    }
}


def ingest():
    germane_dir = RESEARCH_STACK / "shared-data/data/germane/research"
    germane_dir.mkdir(parents=True, exist_ok=True)

    out_path = germane_dir / "density_field_encoding_theory.json"
    with open(out_path, 'w') as f:
        json.dump(DENSITY_FIELD, f, indent=2)

    print(f"✓ Ingested: {out_path}")

    index_path = germane_dir / "research_ingestion_index.json"
    index = []
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)

    index.append({
        "id": DENSITY_FIELD["id"],
        "title": DENSITY_FIELD["title"],
        "date": DENSITY_FIELD["date"],
        "source": DENSITY_FIELD["source"],
        "ingested_at": DENSITY_FIELD["metadata"]["ingested_at"],
        "tags": DENSITY_FIELD["metadata"]["tags"],
    })

    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)

    print(f"✓ Index: {len(index)} entries")

    print(f"\nTopological features mapped:")
    for feat, props in DENSITY_FIELD["topological_features"].items():
        print(f"  • {feat}: {props['encoding']}")

    print(f"\nStack integration:")
    for module, mapping in DENSITY_FIELD["stack_integration"].items():
        print(f"  ↔ {module}: {mapping['role'][:70]}...")

    print(f"\nKeeper phrases ({len(DENSITY_FIELD['keeper_phrases'])}):")
    for p in DENSITY_FIELD["keeper_phrases"]:
        print(f"  → {p}")


if __name__ == "__main__":
    ingest()
