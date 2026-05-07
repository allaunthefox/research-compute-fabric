#!/usr/bin/env python3
"""
Ingest: erans — enumerative rANS (reference only, NO CODE COPIED)
==================================================================
izabera/erans is a streamable single-pass rANS variant.
NO LICENSE — algorithmic notes only, zero code incorporated.
"""

import json, time
from pathlib import Path

RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")

ERANS_REF = {
    "id": "erans-enumerative-rans-reference",
    "source": "https://github.com/izabera/erans",
    "title": "erans: Enumerative rANS — Algorithmic Reference (No Code)",
    "date": "2026-05-07",
    "license": "NONE SPECIFIED — DO NOT INCORPORATE CODE",
    "status": "REFERENCE ONLY — algorithmic ideas, zero lines copied",

    "what_it_is": (
        "A streamable, single-pass, adaptive rANS variant that encodes "
        "the exact histogram + permutation index of a multiset. Achieves "
        "the enumerative coding bound: compressed size approaches log of "
        "the multinomial coefficient, strictly less than Shannon entropy "
        "for the same data (by ~((K-1)/2)log2(N) bits)."
    ),

    "key_algorithmic_ideas": {
        "single_pass_adaptive": {
            "concept": "Encode each symbol against running counts INCLUDING current position. No pre-pass for histogram.",
            "why_it_works": "c_i(s) = count of s up to position i (including i). p_i(s) = c_i(s)/i. Encoder bumps count BEFORE computing CDF so decoder sees same prefix counts walking backward.",
            "our_take": "Maps to PIST streaming encode where shell mass accumulates online. The 'include current position' trick avoids zero-probability symbols."
        },
        "enumerative_bound": {
            "concept": "log2(M) = NH - ((K-1)/2)log2(N) + O(1) where M is multinomial coefficient, H is empirical entropy, K=256",
            "significance": "Beats Shannon entropy by ~1018 bits for N=2^24, K=256. The gain is from NOT quantizing frequencies to powers of 2.",
            "our_take": "This is the geometric compression gain from exact histogram — analogous to storing the exact shear matrix rather than a quantized approximation."
        },
        "shrub_data_structure": {
            "concept": "2-level tree, branching factor 16, for O(1) branchless CDF updates. Bottom: 16 groups of 16 counters. Top: 16 group sums.",
            "operations": "inc/dec: masked add to group + top. sym→cdf: top[byte>>4] + bottom[byte&0xf]. cdf→sym: vector compare for monotonic scan.",
            "isa_note": "erans uses AVX-512 masked adds. Scalar equivalent works at ~2x cycles. Algorithmic structure is ISA-agnostic.",
            "our_take": "Fenwick tree alternative. The 16×16 split is natural for byte alphabet. Could map to Q0_16 accumulators for fixed-point probability tracking."
        },
        "streaming_renorm": {
            "concept": "State kept in [M, 256*M). Overflow bytes emitted when state >= 256*f. No length prefix needed — decoder pulls until state >= M_final.",
            "boundary_case": "When f=M (all symbols same so far), state stays at 1, renorm never fires — degenerates to no-op. Clean.",
            "our_take": "FAMM preshaped renorm: the renorm threshold shifts with M. Could preshape the threshold per shell class for structured data."
        },
        "histogram_encoding": {
            "concept": "Rice coding: split each count into lower B bits (binary) + upper part (unary). B = max(0, ceil(log2(M))-8).",
            "overhead": "At most 576 bytes for N=2^24. Theoretical lower bound ~555 bytes.",
            "our_take": "S3C shell coordinates could encode histogram more compactly — counts are shell populations, naturally structured."
        }
    },

    "hutter_prize_relevance": {
        "entropy_coder": "erans is a candidate entropy coding backend. Beats standard rANS by ~0.004% on large blocks — small but real.",
        "streaming": "Single-pass streaming matches our PIST-S3C-FAMM pipeline architecture. No pre-pass needed.",
        "block_size": "Implementation limit 2^24 (16MiB). Algorithm has no inherent limit. enwik8 = 100M, enwik9 = 1G — need larger blocks or chaining.",
        "comparison_to_fse": "FSE (tANS) decodes in ~5-10 cycles/byte. erans is slower but produces smaller output. For Hutter, size matters more than speed.",
        "adaptation_limitation": "erans is NOT locally adaptive — uses global histogram. For varying distributions, block-splitting needed. Our S3C shell batching naturally provides block boundaries."
    },

    "why_separate": [
        "NO LICENSE — cannot incorporate any code",
        "Algorithmic ideas are public domain (math), implementation is not",
        "Our shrub-equivalent should be written from scratch in Lean + extraction target",
        "ISA-agnostic by design: no AVX-512 dependency, scalar fallback always"
    ],

    "design_rules_added": {
        "isa_agnostic": "Never assume any instruction set is available. SIMD is opportunistic, never structural. All hot paths must have scalar fallback.",
        "license_gate": "No code enters the stack without a compatible license. Algorithmic ideas from unlicensed repos are noted as reference only.",
        "separation": "Reference implementations live in design notes, never in the source tree."
    },

    "metadata": {
        "ingested_at": time.time(),
        "tags": ["entropy-coding", "rans", "enumerative-coding", "reference-only",
                 "no-license", "streaming", "hutter-prize", "entropy", "shrub"]
    }
}


def ingest():
    germane_dir = RESEARCH_STACK / "shared-data/data/germane/research"
    germane_dir.mkdir(parents=True, exist_ok=True)

    out_path = germane_dir / "erans_enumerative_rans_reference.json"
    with open(out_path, 'w') as f:
        json.dump(ERANS_REF, f, indent=2)

    print(f"✓ Ingested: {out_path}")

    index_path = germane_dir / "research_ingestion_index.json"
    index = []
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)

    index.append({
        "id": ERANS_REF["id"],
        "title": ERANS_REF["title"],
        "date": ERANS_REF["date"],
        "source": ERANS_REF["source"],
        "ingested_at": ERANS_REF["metadata"]["ingested_at"],
        "tags": ERANS_REF["metadata"]["tags"],
    })

    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)

    print(f"✓ Index: {len(index)} entries")

    print(f"\nAlgorithmic ideas captured (no code):")
    for name, idea in ERANS_REF["key_algorithmic_ideas"].items():
        print(f"  • {name}: {idea['concept'][:80]}...")

    print(f"\n⚠ LICENSE: {ERANS_REF['license']}")
    print(f"⚠ {ERANS_REF['why_separate'][0]}")
    print(f"⚠ {ERANS_REF['why_separate'][1]}")

    print(f"\nDesign rules:")
    for rule, text in ERANS_REF["design_rules_added"].items():
        print(f"  + {rule}: {text[:80]}...")


if __name__ == "__main__":
    ingest()
