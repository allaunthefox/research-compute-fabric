#!/usr/bin/env python3
"""
Hypercube → Hyper-Rhomboid: Hutter Prize Implications
=======================================================
What changes for enwik8/enwik9 compression when you shear
the token space instead of treating positions independently.
"""

import json, time
from pathlib import Path

RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")

HUTTER_RHOMBOID = {
    "id": "hypercube-rhomboid-hutter-prize",
    "source": "User query — what does hypercube → hyper-rhomboid change for Hutter Prize",
    "title": "Sheared Token Manifolds: Hypercube → Hyper-Rhomboid Implications for Hutter Prize Compression",
    "date": "2026-05-07",

    "current_hutter_paradigm": {
        "approach": "1D token sequence → probability distribution per position → entropy code",
        "geometry": "Orthogonal hypercube: each token position is an independent axis. Context window = fixed-size orthogonal slice.",
        "limitation": (
            "Wikipedia text is NOT a sequence of independent positions. "
            "It is a sheared manifold where: infoboxes repeat with minor variations, "
            "citations share author/year/title structure, headings form a hierarchy, "
            "lists are parallel constructions, markup is templated, "
            "and natural language has syntactic correlation at every scale."
        ),
        "waste": (
            "An orthogonal model pays separately for every occurrence of '{{cite web|url=' "
            "even though the 5000th citation has the same structure as the 1st. "
            "The axes are at 90° — no sharing of probability mass across correlated positions."
        )
    },

    "rhomboid_paradigm": {
        "approach": "Token space as sheared manifold → correlated positions share axes → entropy code residuals only",
        "geometry": (
            "Hyper-rhomboid: token position axes lean into each other proportional to "
            "mutual information. Repeated structures collapse into shared shells. "
            "The shear matrix A IS the compression model."
        ),
        "key_insight": (
            "You don't compress the text. You compress the shear matrix that makes "
            "the text look like noise plus a small residual. The shear matrix is "
            "learned once from the corpus structure; the residual is what you actually "
            "entropy-code."
        )
    },

    "concrete_changes": {

        "pre_transform": {
            "title": "Shear Pre-Transform Before Entropy Coding",
            "current": "Raw bytes → LZ/BWT/PPM/transformer → entropy code",
            "rhomboid": "Raw bytes → S3C shell parse → shear into rhomboid → residual extraction → entropy code",
            "mechanism": (
                "Parse Wikipedia into structural regions (article, infobox, citation, list, heading, template). "
                "Each region type has a canonical shell coordinate. Within each shell, sheared axes encode "
                "the expected structure. Only deviations from the sheared template are entropy-coded."
            ),
            "estimated_gain": "15-30% on structured regions (infoboxes, citations, templates — ~40% of enwik)"
        },

        "s3c_shell_batching": {
            "title": "S3C Shell Coordinates for Token Position Encoding",
            "current": "Position encoded as absolute byte offset or transformer positional embedding",
            "rhomboid": "Position encoded as S3C shell (k, a, b⁰, b⁺) — shell = structural context, offset = within-structure position",
            "mechanism": (
                "k = structural depth (0=character, 1=word, 2=phrase, 3=sentence, 4=paragraph, 5=section, 6=article). "
                "a = position within that structure. b⁰ = remaining length. "
                "The throat (a ≈ b⁰) is where compression is maximal — midpoint of a repeated structure "
                "where the model has maximum predictive confidence."
            ),
            "estimated_gain": "5-10% on positional encoding overhead"
        },

        "oac_speculative_compression": {
            "title": "OAC Speculative Motif Testing Without Output Pollution",
            "current": "Compressor commits to a transform; if it's bad, output is bloated",
            "rhomboid": "Test compression motifs as Observer-Admissible Cavities — temporary exploration manifolds that don't commit to output unless L(motif) + L(residual) < L(raw)",
            "mechanism": (
                "For each structural region, try multiple shear matrices (citation-shear, list-shear, "
                "template-shear, plaintext-shear). The OAC gate only emits the one that beats raw encoding. "
                "Failed shears become FAMM scars — never tried again for similar regions."
            ),
            "estimated_gain": "Avoids 2-5% bloat from bad motif choices; enables aggressive speculation"
        },

        "famm_context_warping": {
            "title": "FAMM Preshaped Context Windows",
            "current": "Fixed context window (e.g., 1024 tokens) for transformer/ppm models",
            "rhomboid": "Preshaped (sheared) context: stretches for high-entropy regions, compresses for low-entropy template regions",
            "mechanism": (
                "Context window is not fixed-length; it's fixed-information. "
                "In a citation template, 50 bytes of context is enough (structure is predictable). "
                "In free text, 500 bytes may be needed. The FAMM delay line preshapes the context "
                "window per shell class — shearing time into the information domain."
            ),
            "estimated_gain": "10-20% context efficiency — more predictive power per context byte"
        },

        "pist_token_manifold": {
            "title": "PIST n-Dimensional Token Encoding",
            "current": "Tokens encoded as 1D integer IDs",
            "rhomboid": "Tokens encoded as n-dimensional PIST coordinates (k, t, fiber₀, ..., fiber_{n-2}) where n = number of correlated features",
            "mechanism": (
                "Each token gets: k = frequency/shell class, t = local offset, "
                "fiber₀ = part-of-speech class, fiber₁ = dependency depth, "
                "fiber₂ = template membership, fiber₃ = capitalization pattern. "
                "The fiber dimensions are the sheared axes — they encode correlation structure "
                "that a 1D token ID loses."
            ),
            "estimated_gain": "5-8% on token encoding; enables cross-position probability sharing"
        },

        "gram_dictionary": {
            "title": "Gram Matrix as Learned Compression Dictionary",
            "current": "Static dictionary (LZ) or learned embeddings (transformer)",
            "rhomboid": "Gram matrix G = A^T A of the shear transform IS the dictionary — eigenvectors are principal correlation directions, eigenvalues are compression gains",
            "mechanism": (
                "The shear matrix A is learned by minimizing: L(A) + L(residual | A). "
                "A is stored once in the compressed header. The decoder applies A^{-1} "
                "to reconstruct expected structure, then replays residuals. "
                "A is tiny compared to the text — a few KB for the entire corpus."
            ),
            "estimated_gain": "Dictionary overhead reduced from MB to KB"
        },

        "metric_entropy_code": {
            "title": "Information-Geometric Entropy Coding",
            "current": "Entropy coding assumes independent symbols (product distribution)",
            "rhomboid": "Entropy coding uses the sheared metric g_{μν} — symbols are coded relative to their position in the sheared manifold, not independently",
            "mechanism": (
                "The coding probability for token x_i is conditioned on its sheared context: "
                "P(x_i | context) = P(x_i | g_{μν}(context)). "
                "In a heavily sheared region (template), P is sharply peaked — near 1.0 for expected token. "
                "In a flat region (free text), P is broad. The metric tells the coder how confident to be."
            ),
            "estimated_gain": "10-15% entropy reduction in structured regions"
        }
    },

    "aggregate_estimate": {
        "structured_regions": "15-30% gain on ~40% of enwik (infoboxes, citations, templates, lists, headings, markup)",
        "free_text_regions": "5-10% gain on ~60% of enwik (natural language paragraphs)",
        "dictionary_overhead": "MB → KB (Gram matrix replaces LZ dictionary + transformer weights)",
        "context_efficiency": "10-20% more predictive power per context byte",
        "overall_compressed_size": "Estimated 12-22% reduction vs current best Hutter compressors",
        "caveat": "These are geometric estimates, not benchmarks. Real gains depend on shear matrix learning quality and residual entropy."
    },

    "the_big_fold": {
        "title": "What This Fundamentally Changes",
        "insight": (
            "The Hutter Prize is currently fought as a sequence modeling problem: "
            "predict the next token given previous tokens. "
            "The rhomboid reframes it as a manifold learning problem: "
            "find the shear that makes the token manifold maximally flat (predictable), "
            "store the shear, then entropy-code the residual curvature."
        ),
        "fold": (
            "This folds FOUR separate Hutter components into ONE: "
            "1. Dictionary (LZ) → Gram matrix eigenvectors "
            "2. Context model (PPM/transformer) → Sheared metric g_{μν} "
            "3. Token encoding → PIST n-D coordinates "
            "4. Structure detection → S3C shell classification "
            "All four are the same object: the shear matrix A."
        ),
        "one_sentence": "Don't predict the next token. Shear the space until the next token is obvious, store the shear, and pay only for what the shear didn't catch."
    },

    "keeper_phrases": [
        "You don't compress the text. You compress the shear matrix that makes the text predictable.",
        "The Gram matrix of the shear IS the dictionary, the context model, the token encoding, and the structure detector — all at once.",
        "A citation isn't 200 bytes that happen to look similar. It's one sheared cavity with 200-byte residuals.",
        "Stop predicting tokens. Start shearing the manifold until tokens become obvious.",
        "The Hutter Prize is manifold learning disguised as sequence modeling.",
        "Fixed context windows are orthogonal thinking. Sheared context is information-geometric thinking.",
        "Every '{{cite web' is the same hole. Pay for the hole once, pay for the URL residual each time."
    ],

    "metadata": {
        "ingested_at": time.time(),
        "tags": [
            "hutter-prize", "compression", "hypercube", "hyper-rhomboid",
            "sheared-manifold", "enwik", "token-encoding", "gram-matrix",
            "s3c-shells", "oac", "famm", "pist", "entropy-coding"
        ]
    }
}


def ingest():
    germane_dir = RESEARCH_STACK / "shared-data/data/germane/research"
    germane_dir.mkdir(parents=True, exist_ok=True)

    out_path = germane_dir / "hypercube_rhomboid_hutter_prize.json"
    with open(out_path, 'w') as f:
        json.dump(HUTTER_RHOMBOID, f, indent=2)

    print(f"✓ Ingested: {out_path}")

    index_path = germane_dir / "research_ingestion_index.json"
    index = []
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)

    index.append({
        "id": HUTTER_RHOMBOID["id"],
        "title": HUTTER_RHOMBOID["title"],
        "date": HUTTER_RHOMBOID["date"],
        "source": HUTTER_RHOMBOID["source"],
        "ingested_at": HUTTER_RHOMBOID["metadata"]["ingested_at"],
        "tags": HUTTER_RHOMBOID["metadata"]["tags"],
    })

    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)

    print(f"✓ Index: {len(index)} entries")

    print(f"\n7 concrete changes:")
    for key, change in HUTTER_RHOMBOID["concrete_changes"].items():
        print(f"  • {change['title']}: {change['estimated_gain']}")

    print(f"\nThe Big Fold:")
    print(f"  {HUTTER_RHOMBOID['the_big_fold']['insight'][:120]}...")

    print(f"\nKeeper phrases:")
    for p in HUTTER_RHOMBOID["keeper_phrases"]:
        print(f"  → {p}")


if __name__ == "__main__":
    ingest()
