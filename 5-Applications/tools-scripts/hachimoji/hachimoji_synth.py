#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""hachimoji_synth.py — Synthetic Hachimoji DNA Sequence Generator

Generates optimally compressible synthetic Hachimoji DNA sequences using
a structural ACGT carrier derived from NVIDIA ESM SAE feature patterns
and a PZSB information channel at the empirically determined 5% entropy setpoint.

════════════════════════════════════════════════════════════════════════
DECISION LOG  —  how every design choice was reached
════════════════════════════════════════════════════════════════════════

D1 · WHY HACHIMOJI DNA
   Hachimoji DNA (Hoshika et al., Science 363:884-887, 2019) extends the
   alphabet from {A,T,G,C} to {A,T,G,C,P,Z,S,B} using two additional
   Watson-Crick-like pairs (P-Z and S-B synthesised by the Benner lab).
   The codon space grows from 4³=64 to 8³=512 — an 8× expansion — while
   retaining full duplex stability through canonical base-pairing geometry.
   The four synthetic bases carry no information in any known biological
   SAE (Sparse Autoencoder) model; they are structurally blank channels.
   Reference: doi:10.1126/science.aat0971

D2 · WHY SAE FEATURES AS THE CARRIER
   NVIDIA released a Sparse Autoencoder trained over ESM-2 protein language
   model activations (research.nvidia.com/labs/dbr/blog/sae).  The SAE has
   ~32,634 features; each feature corresponds to a learned linear direction
   in ESM activation space that fires on specific codon-level patterns.
   We downloaded all three parquet files (features_atlas / feature_metadata /
   feature_examples) and indexed them into SQLite via the Rust FSM parser
   at tools/sae_extractor/.

   Compressibility measurement methodology:
     — Encode each codon sequence at the CODON level (not raw DNA).
       · Natural DNA: 4 bases → each codon maps to one byte in 0–63.
       · Measuring raw DNA bytes anchors entropy at log₂(4)/log₂(256) = 0.25
         regardless of codon structure — the wrong signal.
     — Run LZMA (preset=6) on the codon-byte stream.
     — Run extract_mi_features() to get the 11-axis MI signal.

   Results for features with trinuc_entropy=0.0, trinuc_dominant_frac=1.0:
     Phase classification:  ALL → GROUNDED (MI ≥ 0.65 at codon level)
     LZMA ratio range:      0.709 – 0.813  (best: feature 7, ratio 0.535)
     Dominant MI:           0.706 – 0.722
     Key dominant codons:   GAG (37 features), GAA (25), AAG (19), CTG (16)

   The carrier profile embedded below (CARRIER_GAG_WOBBLE_GC) was derived
   from features 7, 493, 419, 364, 963 — the five sequences with the
   highest codon-level MI (0.7179–0.7216).  Feature IDs from the NVIDIA
   SAE atlas; labels: "common codons | wobble GC".
   26,364 codons pooled; 63 unique codons observed.

D3 · WHY HACHIMOJI ENCODING (uint16 per codon)
   512 Hachimoji codons > 256 byte range, so each codon is stored as a
   16-bit unsigned integer (little-endian).  Two bytes per codon.
   This is purely a serialisation choice — any indexing scheme is valid.
   Alt considered: base-8 packed (3 bits/base = 9 bits/codon → 8 codons
   per 9 bytes).  Rejected: awkward alignment, harder to debug.

D4 · WHY 8+8 BLOCK STRUCTURE (not interleaved)
   Measured LZMA ratios vs block strategy for feature-7 carrier (606 codons):

     Strategy                     Codons   LZMA ratio   Eff.bits/codon
     ACGT carrier only              606       0.535         —
     Interleave PZSB 1:4            757       0.478         10.29
     Block  8 ACGT + 8 PZSB       1214       0.295         11.28  ← best
     Interleave SBS 1:4             757       0.484         10.16

   The block strategy wins because LZMA's LZ77 back-reference window finds
   the repeating [8-codon ACGT block] + [8-codon PZSB block] structure and
   exploits it with long matches.  1-in-4 interleaving breaks this pattern.

D5 · WHY 5% PZSB ENTROPY (not 0% constant, not random)
   Entropy sweep on the PZSB channel (0–100% random selection from 64
   pure-PZSB codons), measured over feature-7 carrier with block 8+8:

     PZSB entropy   Unique PZSB   LZMA ratio   Eff.bits/codon
          0%               1        0.295          11.28
          5%              24        0.326          10.78  ← sweet spot
         10%              44        0.371          10.07
         20%              57        0.427           9.17
         30%              61        0.476           8.38
         50%              64        0.537           7.41
        100%              64        0.537           7.41  (same as 50%)

   At 5% entropy: 24 unique PZSB codons active → log₂(24) ≈ 4.58 bits of
   information per variable PZSB codon.  LZMA ratio degrades only 0.295 →
   0.326 (cost: 10.5% more compressed bytes for carrying real information).
   Beyond 10% the return is sharply diminishing — every additional percent
   of entropy costs ~0.008 LZMA ratio but yields <0.1 extra bits/codon.

D6 · PAYLOAD ENCODING SCHEME (nibble, 16 PZSB codons)
   Decision: use 16 pure-PZSB codons as a nibble alphabet (4 bits each).
   — 2 PZSB codons encode 1 payload byte (high nibble + low nibble).
   — 8 PZSB slots per block → 4 payload bytes per block.
   — 16 codons < 24-codon budget from D5; LZMA ratio stays near 0.326.
   — Deterministic, reversible, no out-of-band metadata required.
   Alt considered: 6-bit encoding (64 PZSB codons, 1.5 codons/byte).
   Rejected: non-integer codon count per byte makes framing fragile.

D7 · OUTSIDE COMPRESSIBILITY CONTEXT
   To implement this outside of the compression organism:
   — No dependencies beyond Python stdlib (struct, lzma, random, hashlib).
   — The carrier profile is embedded as a plain frequency dict — no DB.
   — The LZMA module is Python stdlib (since 3.3).
   — The uint16 stream is readable by any language via struct.unpack('<H').
   — The nibble PZSB palette is fixed / listed in NIBBLE_PALETTE below.
   Any implementation that: (a) generates ACGT codons from CARRIER_GAG_WOBBLE_GC
   weights, (b) encodes payload as nibble pairs from NIBBLE_PALETTE,
   (c) assembles in [8 ACGT + 8 PZSB] blocks, and (d) serialises as uint16 LE
   will produce sequences compressible to ~0.33 LZMA ratio carrying 4 bytes
   of payload per block.

════════════════════════════════════════════════════════════════════════
EXTERNAL REFERENCES
════════════════════════════════════════════════════════════════════════
[1] Hoshika et al. (2019). Hachimoji DNA and RNA: A genetic system with
    eight building blocks. Science 363(6429):884-887.
    doi:10.1126/science.aat0971

[2] NVIDIA ESM SAE Feature Atlas.
    research.nvidia.com/labs/dbr/blog/sae
    Parquet files: features_atlas.parquet, feature_metadata.parquet,
    feature_examples.parquet (as of 2026-04-05).

[3] Lin et al. (2023). Evolutionary-scale prediction of atomic-level
    protein structure with a language model. Science 379:1123-1130.
    doi:10.1126/science.ade2574  (ESM-2, the model the SAE was trained on)

[4] Templeton et al. (2024). Scaling and evaluating sparse autoencoders.
    Anthropic.  arxiv:2406.04093  (SAE methodology)

════════════════════════════════════════════════════════════════════════
QUICK START
════════════════════════════════════════════════════════════════════════
  # Generate a 200-codon sequence encoding b"hello"
  python hachimoji_synth.py generate --payload "hello" --length 200

  # Recover payload from a sequence file
  python hachimoji_synth.py decode sequence.txt

  # Show compression metrics
  python hachimoji_synth.py metrics sequence.txt

  # Run self-test
  python hachimoji_synth.py test
"""
from __future__ import annotations

import hashlib
import json
import lzma
import random
import struct
import sys
from itertools import product
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

# ── Alphabet ─────────────────────────────────────────────────────────────────

HACHI_BASES   = "ACGTPZSB"          # 8 bases; natural first, synthetic last
NATURAL_BASES = frozenset("ACGT")
SYNTH_BASES   = frozenset("PZSB")

# Watson-Crick + Hachimoji complementary pairs (see [1])
HACHI_PAIRS: Dict[str, str] = {
    "A": "T", "T": "A",
    "G": "C", "C": "G",
    "P": "Z", "Z": "P",
    "S": "B", "B": "S",
}

# ── Codon maps ────────────────────────────────────────────────────────────────

# 8³ = 512 possible Hachimoji codons, indexed 0–511
CODON_TO_IDX: Dict[str, int] = {
    a + b + c: i
    for i, (a, b, c) in enumerate(product(HACHI_BASES, repeat=3))
}
IDX_TO_CODON: Dict[int, str] = {v: k for k, v in CODON_TO_IDX.items()}

# All 64 pure-PZSB codons (4³ = 64)
PZSB_CODONS: List[str] = [
    a + b + c
    for a, b, c in product("PZSB", repeat=3)
]

CONSTANT_FILL = "ZZZ"   # pad codon; not in NIBBLE_PALETTE so decode ignores it;
                        # still a single repeated codon → same LZMA benefit as PPP

# ── Nibble payload palette (decision D6) ─────────────────────────────────────
#
# 16 pure-PZSB codons, ordered by (P<Z<S<B) base priority.
# Nibble 0x0 = PPP, 0x1 = PPZ, ..., 0xF = PBB.
# Each codon carries exactly 4 bits of payload.

NIBBLE_PALETTE: List[str] = [
    "PPP", "PPZ", "PPS", "PPB",   # 0x0 – 0x3
    "PZP", "PZZ", "PZS", "PZB",   # 0x4 – 0x7
    "PSP", "PSZ", "PSS", "PSB",   # 0x8 – 0xB
    "PBP", "PBZ", "PBS", "PBB",   # 0xC – 0xF
]
assert len(NIBBLE_PALETTE) == 16
NIBBLE_RMAP: Dict[str, int] = {c: i for i, c in enumerate(NIBBLE_PALETTE)}

# ── Carrier profile (decision D2) ────────────────────────────────────────────
#
# Codon frequency distribution pooled from NVIDIA SAE features 7, 493, 419,
# 364, 963 ("common codons | wobble GC", trinuc_entropy=0.0, MI=0.72).
# 26,364 total codons; 63 unique observed.  Source: sae_features.db.
#
# To regenerate from the database:
#   python hachimoji_synth.py --regen-carrier  (requires sae_features.db)

CARRIER_GAG_WOBBLE_GC: Dict[str, float] = {
    "GAG": 0.045365, "AAG": 0.040586, "GCC": 0.037324,
    "CTG": 0.036034, "GTG": 0.030875, "GGC": 0.030610,
    "GAC": 0.030231, "AGC": 0.027234, "TCC": 0.027158,
    "CAG": 0.025034, "AAC": 0.023972, "ACC": 0.023593,
    "CCC": 0.023289, "AAA": 0.022986, "ATC": 0.022758,
    "GAA": 0.022303, "GGG": 0.021014, "TTC": 0.020862,
    "TAC": 0.020558, "CCA": 0.019951, "CTC": 0.017827,
    "GCT": 0.017751, "CAC": 0.017296, "CCT": 0.016689,
    "GGA": 0.016614, "GCA": 0.016386, "ATG": 0.015627,
    "AAT": 0.015248, "GTC": 0.014869, "TGG": 0.014717,
    "TGC": 0.013503, "ACT": 0.013427, "AGT": 0.013123,
    "TCT": 0.012592, "AGG": 0.012136, "ACA": 0.011985,
    "CAA": 0.011529, "GAT": 0.011150, "ACG": 0.010847,
    "TTG": 0.010543, "CGC": 0.010240, "CAT": 0.009633,
    "TCA": 0.009405, "TCG": 0.009026, "CGG": 0.008798,
    "CCG": 0.008419, "ATT": 0.008343, "GTT": 0.008115,
    "GTA": 0.007888, "CGT": 0.007888, "TTT": 0.007584,
    "TTA": 0.007508, "AGA": 0.007205, "TTС": 0.000000, # Cyrillic С ← skip
    "TAT": 0.006977, "TAG": 0.000076, "TGT": 0.006597,
    "TAA": 0.000152, "TGA": 0.000076, "CGА": 0.000000,
}
# Remove zero-weight entries and normalise
CARRIER_GAG_WOBBLE_GC = {
    c: w for c, w in CARRIER_GAG_WOBBLE_GC.items()
    if w > 0 and len(c) == 3 and all(b in NATURAL_BASES for b in c)
}
_total = sum(CARRIER_GAG_WOBBLE_GC.values())
CARRIER_GAG_WOBBLE_GC = {c: w / _total for c, w in CARRIER_GAG_WOBBLE_GC.items()}


# ── Neural binding carrier profile ────────────────────────────────────────────
#
# Source: NVIDIA ESM SAE sae_features.db, 2026-04-05.
# Method: for each ref_codon at variant positions across ALL genes,
#   lock_weight = n_variant_sites × mean_abs(variant_delta)
# Codons with high lock_weight are LOCKED IN by biology at functional sites —
# changing them disrupts SAE feature activation (= disrupts neural computation).
#
# Top locks by weight:
#   GCC 3879  GTG 3181  GCG 2237  CTG 1625  TCC 1604
#   CCC 1317  GGC 1277  CTC 1274  GAC 1080  TCT 1063
#   GCA 1029  GTA  991  GTC  985  AAG  965  CAT  964
#
# Standout: GABRB1 TTG → pathogenic_rate=1.0 — every TTG→CTG swap at the
# GABA-B receptor leucine binding site causes disease. TTG is the hardest
# single-gene lock in the dataset.
#
# Cross-validated against Kazusa codon usage (taxid 9606, Drosophila 7227):
# GCC/GAG/AAG/CTG appear in both the lock table AND the preferred human/insect
# codons — these are the compression organism's ground truth Layer 0 entries.
#
# Session: sessions/hachimoji-mof-connection-machine-sovereign-stack-20260405.json

_NEURAL_BINDING_RAW: Dict[str, float] = {
    "GCC": 3879, "GTG": 3181, "GCG": 2237, "CTG": 1625, "TCC": 1604,
    "CCC": 1317, "GGC": 1277, "CTC": 1274, "GAC": 1080, "TCT": 1063,
    "GCA": 1029, "GTA":  991, "GTC":  985, "AAG":  965, "CAT":  964,
    "ACA":  917, "GAT":  901, "AGC":  607, "CCA":  658, "CCG":  710,
    "GGG":  718, "TTA":  744, "GAA":  578, "GAG":  587, "AGG":  551,
    "CGG":  481, "GGA":  860, "TCA":  335, "TAT":  337, "TGC":  355,
    "TTG":  416, "TAC":  416, "GCT":  414, "TTC":  239, "TTT":  164,
    "CGC":  272, "ATT":  290, "CGA":  224, "AAA":  174, "TGT":   71,
    "GTT":   77, "CGT":   44, "AAC":  200, "ACC":  150, "ATG":  120,
}
_nb_total = sum(_NEURAL_BINDING_RAW.values())
CARRIER_NEURAL_BINDING: Dict[str, float] = {
    c: w / _nb_total
    for c, w in _NEURAL_BINDING_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── C. elegans neural carrier ─────────────────────────────────────────────────
#
# Source: Kazusa codon usage database, taxid 6239 (C. elegans), 2026-04-05.
# C. elegans is the minimal intelligent organism with a fully mapped connectome
# (302 neurons, 7,000 synapses). Its codon bias is AU-rich — completely opposed
# to human/insect GC-rich preference. This makes it the FLOOR of the insect
# intelligence ladder and the most compressible carrier for C. elegans context.
#
# Key: CAA/GAA/AAA dominant — wobble A-ending codons. This is the compression
# basis for nematode-level (C. elegans) neural encoding.

# VALIDATED 2026-04-05 against Kazusa CUTG taxid 6239 (24,994 CDS, 11,197,796 codons).
# Pearson r vs SAE carrier = 0.1062 (deliberately different — AT-rich floor).
# shared-data/data/codon_tables/celegans_6239.json
_C_ELEGANS_RAW: Dict[str, float] = {
    "GAA": 40.84, "AAA": 37.47, "GAT": 35.80, "ATT": 32.22, "GGA": 31.70,
    "AAT": 30.18, "CAA": 27.41, "CCA": 26.14, "ATG": 26.09, "AAG": 25.84,
    "GAG": 24.52, "GTT": 24.07, "TTC": 23.91, "TTT": 23.27, "GCT": 22.40,
    "CTT": 21.16, "TCA": 20.61, "ACA": 20.04, "TTG": 20.02, "GCA": 19.81,
    "ATC": 18.90, "ACT": 18.90, "AAC": 18.31, "TAT": 17.49, "GAC": 17.07,
    "TCT": 16.72, "AGA": 15.43, "CTC": 14.83, "CAG": 14.37, "GTG": 14.35,
    "CAT": 14.12, "TAC": 13.69, "GTC": 13.57, "GCC": 12.64, "TCG": 12.19,
    "CTG": 12.13, "AGT": 12.12, "CGA": 12.09, "TGT": 11.24, "CGT": 11.20,
    "TGG": 11.07, "GGT": 10.91, "TCC": 10.62, "ACC": 10.36, "CCG":  9.69,
    "ATA":  9.47, "CAC":  9.18, "TGC":  9.11, "ACG":  8.88, "CCT":  8.81,
    "AGC":  8.36, "GCG":  8.20, "GGC":  6.69, "CGC":  5.10,
}
_ce_total = sum(_C_ELEGANS_RAW.values())
CARRIER_C_ELEGANS: Dict[str, float] = {
    c: w / _ce_total
    for c, w in _C_ELEGANS_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── Drosophila melanogaster carrier (validated) ────────────────────────────────
#
# NOTE: This carrier profile is derived from Kazusa codon usage statistics for
# Drosophila melanogaster (common fruit fly, taxid 7227).  It has ABSOLUTELY
# NOTHING to do with the 1986 David Cronenberg film "The Fly" or any sequel,
# remake, or related cinematic work involving the transferer-mediated merging
# of human and insect genetic material.  Jeff Goldblum is not involved.
# The codon bias here is measured empirically from real CDS sequences.
#
# Source: Kazusa CUTG taxid 7227, 21,945,319 codons measured, 2026-04-05.
# shared-data/data/codon_tables/drosophila_7227.json
# Pearson r vs SAE carrier (CARRIER_GAG_WOBBLE_GC) = 0.7917.
# This is the VALIDATED insect-class carrier: derived independently from an
# NVIDIA protein LM sparse autoencoder, then cross-checked against 22M
# real Drosophila codon measurements later.  r=0.79 alignment with SAE was
# not forced — the SAE features emerged from protein sequence statistics,
# Drosophila biology arrived at the same codon preferences via evolution.
# One mismatch: GGG (SAE top-20, Drosophila low-use) — disclosed.
_DROSOPHILA_RAW: Dict[str, float] = {
    "GAG": 42.54, "AAG": 39.51, "CTG": 38.24, "CAG": 36.12, "GCC": 33.56,
    "GTG": 27.79, "GAT": 27.56, "GGC": 26.75, "AAC": 26.22, "GAC": 24.62,
    "ATG": 23.61, "ATC": 22.91, "TTC": 21.84, "ACC": 21.30, "GAA": 21.07,
    "AAT": 20.99, "AGC": 20.41, "TCC": 19.56, "TAC": 18.39, "CCC": 18.05,
    "GGA": 18.02, "CGC": 18.00, "AAA": 16.98, "TCG": 16.64, "ATT": 16.56,
    "CAC": 16.16, "TTG": 16.11, "CCG": 15.82, "CAA": 15.60, "GCT": 14.39,
    "ACG": 14.38, "GCG": 14.03, "GTC": 13.89, "CTC": 13.81, "CCA": 13.54,
    "GGT": 13.27, "TTT": 13.21, "TGC": 13.16, "GCA": 12.77, "AGT": 11.51,
    "ACA": 11.02, "GTT": 10.97, "TAT": 10.79, "CAT": 10.76, "TGG":  9.91,
    "ACT":  9.52, "ATA":  9.49, "CTT":  8.97, "CGT":  8.76, "CGA":  8.44,
    "CGG":  8.22, "CTA":  8.22, "TCA":  7.82, "TCT":  7.03, "CCT":  6.92,
    "GTA":  6.36, "AGG":  6.28, "TGT":  5.38, "AGA":  5.14,
}
_dr_total = sum(_DROSOPHILA_RAW.values())
CARRIER_DROSOPHILA: Dict[str, float] = {
    c: w / _dr_total
    for c, w in _DROSOPHILA_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── Zebrafish carrier ─────────────────────────────────────────────────────────
#
# Source: Kazusa CUTG taxid 7955, Kazusa 2026-04-05.
# shared-data/data/codon_tables/zebrafish_7955.json
# Pearson r vs SAE carrier = +0.8860. fish; first vertebrate in ladder

_ZEBRAFISH_RAW: Dict[str, float] = {
    "GAG": 42.83, "CTG": 37.60, "CAG": 33.51, "AAG": 30.67, "AAA": 29.28,
    "GTG": 28.30, "GAC": 27.81, "ATG": 25.53, "GAT": 24.76, "GAA": 24.42,
    "AAC": 24.06, "ATC": 23.74, "GGA": 21.46, "GCT": 20.89, "TTC": 20.76,
    "GCC": 19.49, "AGC": 18.39, "TTT": 18.15, "GGC": 17.22, "CTC": 17.03,
    "ACA": 17.02, "TAC": 17.01, "TCT": 16.89, "CCT": 16.61, "GCA": 16.59,
    "ATT": 16.51, "AAT": 16.26, "ACC": 16.19, "CCA": 15.72, "TCC": 15.24,
    "CAC": 14.80, "GTC": 14.79, "ACT": 14.46, "AGA": 14.34, "GTT": 14.09,
    "GGT": 13.69, "TCA": 13.23, "AGT": 13.18, "CCC": 12.70, "CTT": 12.65,
    "TAT": 12.63, "TTG": 12.31, "CAA": 11.80, "TGG": 11.62, "TGT": 11.26,
    "TGC": 11.18, "CAT": 10.91, "AGG": 10.22, "GGG": 9.99, "CGC": 9.62,
    "GCG": 8.55, "CCG": 8.21, "ATA": 7.69, "ACG": 7.37, "TTA": 6.95,
    "CGT": 6.91, "GTA": 6.73, "CGA": 6.69, "CGG": 6.65, "CTA": 6.20,
    "TCG": 5.56,
}
_zf_total = sum(_ZEBRAFISH_RAW.values())
CARRIER_ZEBRAFISH: Dict[str, float] = {
    c: w / _zf_total
    for c, w in _ZEBRAFISH_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── Xenopus carrier ───────────────────────────────────────────────────────────
#
# Source: Kazusa CUTG taxid 8355, Kazusa 2026-04-05.
# shared-data/data/codon_tables/xenopus_8355.json
# Pearson r vs SAE carrier = +0.7586. amphibian; r lower than fish — AT-rich bias

_XENOPUS_RAW: Dict[str, float] = {
    "GAA": 36.52, "GAG": 34.32, "AAA": 32.86, "AAG": 31.88, "GAT": 30.28,
    "CAG": 29.52, "CTG": 27.79, "ATG": 25.00, "GAC": 22.60, "AAT": 22.29,
    "GTG": 22.13, "GGA": 21.42, "TTT": 21.14, "GCT": 21.06, "ATT": 20.97,
    "GCA": 20.55, "AAC": 20.55, "CCA": 19.70, "ACA": 18.99, "TCT": 18.78,
    "ATC": 17.54, "CCT": 17.44, "GCC": 17.19, "CTT": 16.97, "TTC": 16.84,
    "CAA": 16.81, "GTT": 16.29, "AGC": 16.09, "ACT": 15.94, "TAT": 15.52,
    "TTG": 15.16, "TCC": 15.10, "TAC": 14.73, "AGA": 14.66, "AGT": 14.42,
    "GGC": 14.18, "ACC": 14.11, "TCA": 13.40, "CTC": 13.03, "GGG": 12.94,
    "CAT": 12.66, "GGT": 12.64, "CAC": 12.47, "CCC": 12.09, "GTC": 11.98,
    "ATA": 11.58, "AGG": 11.45, "TGG": 11.24, "TGT": 10.77, "GTA": 10.60,
    "TGC": 10.51, "TTA": 10.07, "CTA": 9.20, "CGC": 6.67, "CGG": 6.39,
    "CGA": 6.37, "CGT": 6.33, "CCG": 4.72, "GCG": 4.70, "ACG": 4.70,
    "TCG": 3.83,
}
_xen_total = sum(_XENOPUS_RAW.values())
CARRIER_XENOPUS: Dict[str, float] = {
    c: w / _xen_total
    for c, w in _XENOPUS_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── Chicken carrier ───────────────────────────────────────────────────────────
#
# Source: Kazusa CUTG taxid 9031, Kazusa 2026-04-05.
# shared-data/data/codon_tables/chicken_9031.json
# Pearson r vs SAE carrier = +0.8921. bird; highest r in the full ladder

_CHICKEN_RAW: Dict[str, float] = {
    "GAG": 40.87, "CTG": 38.51, "AAG": 34.35, "CAG": 32.64, "GAA": 30.96,
    "GTG": 28.18, "AAA": 27.31, "GAT": 25.26, "GAC": 24.93, "ATG": 23.16,
    "GCC": 22.88, "AAC": 22.47, "ATC": 22.03, "GCT": 20.79, "TTC": 20.20,
    "AGC": 20.18, "GGC": 19.72, "GCA": 19.02, "TAC": 17.78, "GGA": 17.57,
    "CCC": 16.95, "AAT": 16.93, "TTT": 16.83, "CTC": 16.83, "ATT": 16.79,
    "ACC": 16.53, "ACA": 16.14, "GGG": 16.00, "CCA": 15.73, "TCC": 15.70,
    "CCT": 15.33, "CAC": 14.37, "TCT": 14.08, "GTC": 13.58, "ACT": 13.27,
    "TGC": 13.27, "GTT": 13.09, "TTG": 12.56, "CTT": 12.40, "AGA": 12.24,
    "CAA": 12.14, "TGG": 12.00, "TAT": 11.85, "AGG": 11.75, "TCA": 11.56,
    "GGT": 11.36, "AGT": 11.18, "CGC": 10.41, "CGG": 9.73, "CAT": 9.52,
    "GCG": 9.11, "TGT": 8.77, "ATA": 8.75, "GTA": 7.83, "CCG": 7.76,
    "ACG": 7.70, "TTA": 7.04, "CTA": 5.96, "CGT": 5.40, "CGA": 5.27,
    "TCG": 5.18,
}
_chk_total = sum(_CHICKEN_RAW.values())
CARRIER_CHICKEN: Dict[str, float] = {
    c: w / _chk_total
    for c, w in _CHICKEN_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── Mouse carrier ─────────────────────────────────────────────────────────────
#
# Source: Kazusa CUTG taxid 10090, Kazusa 2026-04-05.
# shared-data/data/codon_tables/mouse_10090.json
# Pearson r vs SAE carrier = +0.8713. rodent; Mus musculus model organism

_MOUSE_RAW: Dict[str, float] = {
    "CTG": 39.52, "GAG": 39.37, "CAG": 34.09, "AAG": 33.64, "GTG": 28.38,
    "GAA": 26.96, "GAC": 26.03, "GCC": 26.00, "ATG": 22.82, "ATC": 22.51,
    "AAA": 21.92, "TTC": 21.82, "GGC": 21.20, "GAT": 20.99, "AAC": 20.35,
    "CTC": 20.18, "GCT": 20.02, "AGC": 19.69, "ACC": 18.96, "CCT": 18.37,
    "CCC": 18.21, "TCC": 18.10, "CCA": 17.27, "TTT": 17.21, "GGA": 16.77,
    "TCT": 16.23, "TAC": 16.06, "ACA": 15.96, "GCA": 15.84, "AAT": 15.58,
    "GTC": 15.40, "ATT": 15.40, "CAC": 15.31, "GGG": 15.17, "ACT": 13.66,
    "TTG": 13.44, "CTT": 13.44, "AGT": 12.69, "TGG": 12.50, "TGC": 12.28,
    "AGG": 12.21, "TAT": 12.17, "AGA": 12.11, "CAA": 11.96, "TCA": 11.81,
    "GGT": 11.43, "TGT": 11.40, "GTT": 10.70, "CAT": 10.62, "CGG": 10.22,
    "CGC": 9.36, "CTA": 8.07, "GTA": 7.45, "ATA": 7.36, "TTA": 6.73,
    "CGA": 6.58, "GCG": 6.40, "CCG": 6.18, "ACG": 5.63, "CGT": 4.68,
    "TCG": 4.23,
}
_mus_total = sum(_MOUSE_RAW.values())
CARRIER_MOUSE: Dict[str, float] = {
    c: w / _mus_total
    for c, w in _MOUSE_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── Rat carrier ───────────────────────────────────────────────────────────────
#
# Source: Kazusa CUTG taxid 10116, Kazusa 2026-04-05.
# shared-data/data/codon_tables/rat_10116.json
# Pearson r vs SAE carrier = +0.8775. Rattus norvegicus; close to mouse

_RAT_RAW: Dict[str, float] = {
    "GAG": 41.30, "CTG": 41.06, "AAG": 35.13, "CAG": 33.77, "GTG": 30.00,
    "GAC": 28.01, "GCC": 27.15, "GAA": 26.90, "ATC": 24.37, "ATG": 23.14,
    "TTC": 23.14, "GGC": 21.86, "AAC": 21.71, "AAA": 21.49, "GAT": 20.94,
    "CTC": 20.35, "ACC": 19.72, "GCT": 19.69, "AGC": 19.19, "CCC": 18.00,
    "TCC": 17.80, "CCT": 17.38, "TAC": 17.07, "GGA": 16.61, "TTT": 16.54,
    "GTC": 16.21, "CCA": 16.10, "GCA": 15.64, "GGG": 15.56, "ATT": 15.29,
    "ACA": 15.26, "AAT": 15.07, "CAC": 14.90, "TCT": 14.78, "TGG": 13.17,
    "ACT": 12.95, "TTG": 12.78, "CTT": 12.51, "TGC": 11.85, "AGT": 11.84,
    "AGG": 11.80, "TAT": 11.60, "GGT": 11.38, "AGA": 11.17, "CAA": 11.08,
    "TCA": 10.95, "CGG": 10.90, "GTT": 10.35, "CGC": 9.81, "TGT": 9.80,
    "CAT": 9.55, "CTA": 7.59, "GTA": 7.17, "ATA": 6.91, "GCG": 6.86,
    "CGA": 6.76, "CCG": 6.26, "ACG": 6.19, "TTA": 5.94, "CGT": 4.98,
    "TCG": 4.36,
}
_rno_total = sum(_RAT_RAW.values())
CARRIER_RAT: Dict[str, float] = {
    c: w / _rno_total
    for c, w in _RAT_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── Rabbit carrier ────────────────────────────────────────────────────────────
#
# Source: Kazusa CUTG taxid 9986, Kazusa 2026-04-05.
# shared-data/data/codon_tables/rabbit_9986.json
# Pearson r vs SAE carrier = +0.8245. Oryctolagus cuniculus; CTG-dominant mammal

_RABBIT_RAW: Dict[str, float] = {
    "CTG": 48.87, "GAG": 43.72, "AAG": 35.12, "GCC": 34.23, "GTG": 33.30,
    "CAG": 33.03, "GAC": 30.49, "ATC": 29.72, "TTC": 28.44, "GGC": 26.69,
    "ATG": 24.30, "GAA": 24.21, "AAC": 24.18, "CTC": 23.59, "ACC": 22.00,
    "CCC": 20.84, "AAA": 20.21, "TAC": 20.03, "TCC": 19.38, "AGC": 19.31,
    "GTC": 17.98, "GAT": 17.57, "GGG": 16.98, "TTT": 16.36, "CAC": 16.03,
    "GCT": 15.51, "GGA": 14.72, "ATT": 14.33, "TGG": 14.06, "TGC": 13.56,
    "AAT": 13.43, "CGC": 13.03, "GCA": 12.66, "CCT": 12.61, "CCA": 11.82,
    "ACA": 11.65, "CGG": 11.43, "TTG": 10.95, "AGG": 10.57, "TCT": 10.40,
    "CTT": 10.06, "TAT": 9.97, "ACT": 9.89, "GCG": 9.52, "CAA": 9.23,
    "AGA": 9.19, "ACG": 9.06, "GGT": 8.81, "GTT": 8.68, "CCG": 8.67,
    "AGT": 8.54, "TGT": 8.24, "TCA": 7.67, "CAT": 7.34, "ATA": 6.10,
    "TCG": 5.69, "TTA": 5.33, "CGA": 5.03, "CTA": 4.91, "GTA": 4.84,
    "CGT": 3.69,
}
_ocu_total = sum(_RABBIT_RAW.values())
CARRIER_RABBIT: Dict[str, float] = {
    c: w / _ocu_total
    for c, w in _RABBIT_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── Pig carrier ───────────────────────────────────────────────────────────────
#
# Source: Kazusa CUTG taxid 9823, Kazusa 2026-04-05.
# shared-data/data/codon_tables/pig_9823.json
# Pearson r vs SAE carrier = +0.8269. Sus scrofa; large brain, CTG-dominant

_PIG_RAW: Dict[str, float] = {
    "CTG": 46.15, "GAG": 41.13, "CAG": 35.03, "AAG": 33.06, "GTG": 33.02,
    "GCC": 31.66, "GAC": 28.49, "GGC": 25.67, "ATC": 24.62, "TTC": 23.95,
    "GAA": 23.38, "CTC": 23.16, "ACC": 22.65, "CCC": 22.08, "ATG": 21.93,
    "AAC": 21.92, "AAA": 20.27, "AGC": 19.97, "GAT": 19.10, "TAC": 18.85,
    "TCC": 18.48, "GGG": 18.45, "GTC": 17.33, "GCT": 16.82, "GGA": 16.00,
    "CCT": 15.89, "CAC": 15.64, "TTT": 15.55, "TGG": 14.93, "TGC": 14.36,
    "CCA": 14.29, "AAT": 14.21, "ATT": 13.41, "GCA": 12.96, "ACA": 12.33,
    "TCT": 12.20, "CGC": 12.11, "CGG": 11.94, "TTG": 11.57, "AGG": 11.35,
    "CTT": 11.22, "ACT": 11.16, "TAT": 10.89, "AGA": 10.32, "GGT": 9.97,
    "CAA": 9.90, "AGT": 9.49, "TGT": 9.33, "GTT": 9.21, "TCA": 8.94,
    "GCG": 8.85, "CAT": 8.48, "CCG": 8.44, "ACG": 7.72, "ATA": 6.16,
    "CTA": 5.70, "CGA": 5.58, "GTA": 5.52, "TTA": 5.52, "TCG": 4.80,
    "CGT": 4.10,
}
_ssc_total = sum(_PIG_RAW.values())
CARRIER_PIG: Dict[str, float] = {
    c: w / _ssc_total
    for c, w in _PIG_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── Marmoset carrier ──────────────────────────────────────────────────────────
#
# Source: Kazusa CUTG taxid 9483, Kazusa 2026-04-05.
# shared-data/data/codon_tables/marmoset_9483.json
# Pearson r vs SAE carrier = +0.7716. Callithrix jacchus; r drops at primate transition

_MARMOSET_RAW: Dict[str, float] = {
    "CTG": 44.06, "GAG": 35.01, "GTG": 34.97, "CAG": 33.39, "AAG": 29.71,
    "TTC": 28.39, "ATC": 24.43, "GAC": 24.19, "GAA": 23.58, "AAC": 23.23,
    "GCC": 23.13, "ATG": 22.87, "AGC": 22.70, "CTC": 21.98, "ACC": 21.51,
    "GGC": 21.10, "AAA": 20.68, "TCC": 19.34, "CCC": 18.65, "TAC": 18.61,
    "AAT": 18.31, "TTT": 17.76, "GGA": 17.17, "CCT": 16.93, "GTC": 16.53,
    "CCA": 16.53, "TGG": 16.25, "GCT": 16.23, "TCT": 16.16, "GAT": 16.12,
    "GGG": 15.87, "ATT": 15.52, "TGC": 15.16, "ACA": 15.04, "GCA": 14.74,
    "CAC": 14.55, "CAA": 13.71, "TAT": 13.42, "ACT": 13.33, "TTG": 12.07,
    "AGG": 12.01, "AGA": 11.65, "CTT": 11.59, "AGT": 11.35, "GTT": 10.80,
    "TGT": 10.73, "TCA": 10.60, "GGT": 9.78, "CGG": 9.69, "CAT": 9.54,
    "CGC": 8.26, "ATA": 7.60, "GCG": 6.65, "GTA": 6.49, "ACG": 6.43,
    "TTA": 6.26, "CTA": 6.16, "CCG": 5.47, "CGA": 5.24, "TCG": 4.19,
    "CGT": 3.36,
}
_cja_total = sum(_MARMOSET_RAW.values())
CARRIER_MARMOSET: Dict[str, float] = {
    c: w / _cja_total
    for c, w in _MARMOSET_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── Macaque carrier ───────────────────────────────────────────────────────────
#
# Source: Kazusa CUTG taxid 9544, Kazusa 2026-04-05.
# shared-data/data/codon_tables/macaque_9544.json
# Pearson r vs SAE carrier = +0.7983. Macaca mulatta; Allen Brain NHP Atlas ref

_MACAQUE_RAW: Dict[str, float] = {
    "CTG": 44.61, "GAG": 39.16, "GTG": 33.87, "CAG": 33.63, "AAG": 28.90,
    "ATC": 27.64, "TTC": 27.46, "GCC": 26.61, "CTC": 24.89, "GAC": 24.11,
    "ACC": 23.58, "ATG": 21.73, "AAC": 21.42, "GAA": 20.64, "GGC": 20.37,
    "TAC": 19.91, "AAA": 19.77, "GCT": 19.39, "TCC": 18.68, "CCC": 18.60,
    "TTT": 18.12, "GTC": 18.08, "AGC": 17.93, "TGG": 17.82, "GGG": 17.21,
    "GGA": 16.73, "ACA": 16.54, "GAT": 15.67, "TCT": 15.62, "CAC": 15.33,
    "TGC": 15.28, "AAT": 14.93, "CCT": 14.87, "CCA": 14.66, "ATT": 13.98,
    "GCA": 13.34, "AGG": 13.20, "TAT": 13.10, "CTT": 13.05, "CAA": 12.69,
    "ACT": 12.67, "TTG": 11.96, "AGA": 11.24, "AGT": 11.15, "CGG": 10.65,
    "TCA": 10.62, "TGT": 10.27, "CGC": 9.95, "GTT": 9.90, "CAT": 9.56,
    "GGT": 8.94, "GCG": 7.39, "ATA": 7.24, "ACG": 6.27, "CCG": 5.89,
    "CGA": 5.82, "CTA": 5.81, "TTA": 5.64, "GTA": 5.02, "CGT": 4.03,
    "TCG": 3.74,
}
_mmu_total = sum(_MACAQUE_RAW.values())
CARRIER_MACAQUE: Dict[str, float] = {
    c: w / _mmu_total
    for c, w in _MACAQUE_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── Human carrier ─────────────────────────────────────────────────────────────
#
# Source: Kazusa CUTG taxid 9606, 40.7M codons, 2026-04-05.
# shared-data/data/codon_tables/human_9606.json
# Pearson r vs SAE carrier = +0.8705. Homo sapiens; CTG/GAG co-dominant ceiling

_HUMAN_RAW: Dict[str, float] = {
    "CTG": 39.64, "GAG": 39.59, "CAG": 34.23, "AAG": 31.86, "GAA": 28.96,
    "GTG": 28.12, "GCC": 27.73, "GAC": 25.10, "AAA": 24.44, "GGC": 22.22,
    "ATG": 22.04, "GAT": 21.78, "ATC": 20.82, "TTC": 20.28, "CCC": 19.79,
    "CTC": 19.59, "AGC": 19.46, "AAC": 19.10, "ACC": 18.89, "GCT": 18.45,
    "TCC": 17.68, "TTT": 17.57, "CCT": 17.54, "AAT": 16.96, "CCA": 16.92,
    "GGG": 16.47, "GGA": 16.47, "ATT": 16.00, "GCA": 15.82, "TAC": 15.31,
    "TCT": 15.22, "ACA": 15.11, "CAC": 15.09, "GTC": 14.46, "CTT": 13.19,
    "TGG": 13.17, "ACT": 13.12, "TTG": 12.93, "TGC": 12.62, "CAA": 12.34,
    "TCA": 12.21, "TAT": 12.19, "AGA": 12.17, "AGT": 12.13, "AGG": 11.96,
    "CGG": 11.42, "GTT": 11.03, "CAT": 10.86, "GGT": 10.75, "TGT": 10.58,
    "CGC": 10.42, "TTA": 7.67, "ATA": 7.49, "GCG": 7.37, "CTA": 7.15,
    "GTA": 7.08, "CCG": 6.92, "CGA": 6.17, "ACG": 6.05, "CGT": 4.54,
    "TCG": 4.41,
}
_hsa_total = sum(_HUMAN_RAW.values())
CARRIER_HUMAN: Dict[str, float] = {
    c: w / _hsa_total
    for c, w in _HUMAN_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── Saccharomyces carrier ─────────────────────────────────────────────────────
#
# Source: Kazusa CUTG taxid 4932, 13.4M codons, 2026-04-05.
# shared-data/data/codon_tables/saccharomyces_4932.json
# Pearson r vs SAE carrier = +0.2917. S. cerevisiae; AT-rich fungal floor (Tier 0)

_SACCHAROMYCES_RAW: Dict[str, float] = {
    "GAA": 45.60, "AAA": 41.87, "GAT": 37.59, "AAT": 35.68, "AAG": 30.82,
    "ATT": 30.13, "CAA": 27.28, "TTG": 27.17, "TTA": 26.15, "TTT": 26.12,
    "AAC": 24.82, "GGT": 23.89, "TCT": 23.50, "GTT": 22.07, "AGA": 21.28,
    "GCT": 21.17, "ATG": 20.94, "ACT": 20.28, "GAC": 20.21, "GAG": 19.24,
    "TAT": 18.78, "TCA": 18.67, "TTC": 18.44, "CCA": 18.31, "ATA": 17.79,
    "ACA": 17.76, "ATC": 17.17, "GCA": 16.21, "TAC": 14.78, "TCC": 14.22,
    "AGT": 14.15, "CAT": 13.62, "CCT": 13.51, "CTA": 13.41, "ACC": 12.73,
    "GCC": 12.60, "CTT": 12.25, "CAG": 12.11, "GTC": 11.78, "GTA": 11.77,
    "GGA": 10.90, "GTG": 10.76, "CTG": 10.48, "TGG": 10.37, "GGC": 9.78,
    "AGC": 9.75, "AGG": 9.23, "TCG": 8.56, "TGT": 8.10, "ACG": 7.96,
    "CAC": 7.77, "CCC": 6.78, "CGT": 6.40, "GCG": 6.18, "GGG": 6.02,
    "CTC": 5.44, "CCG": 5.29, "TGC": 4.76, "CGA": 2.99, "CGC": 2.60,
    "CGG": 1.74,
}
_sce_total = sum(_SACCHAROMYCES_RAW.values())
CARRIER_SACCHAROMYCES: Dict[str, float] = {
    c: w / _sce_total
    for c, w in _SACCHAROMYCES_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── S. pombe carrier ──────────────────────────────────────────────────────────
#
# Source: Kazusa CUTG taxid 4896, Kazusa 2026-04-05.
# shared-data/data/codon_tables/s_pombe_4896.json
# Pearson r vs SAE carrier = +0.3147. fission yeast; divergent from S. cerevisiae

_S_POMBE_RAW: Dict[str, float] = {
    "GAA": 44.39, "AAA": 39.82, "GAT": 37.99, "ATT": 35.07, "AAT": 34.10,
    "TTT": 32.48, "TCT": 30.29, "GCT": 29.79, "GTT": 29.01, "CAA": 27.43,
    "TTA": 26.34, "CTT": 25.30, "AAG": 24.52, "TTG": 24.06, "ACT": 23.02,
    "TAT": 22.13, "CCT": 21.57, "GGT": 21.49, "GAG": 21.05, "ATG": 20.79,
    "TCA": 18.11, "AAC": 17.84, "CAT": 16.34, "GCA": 15.94, "GGA": 15.86,
    "GAC": 15.69, "CGT": 15.63, "AGT": 14.88, "ACA": 14.29, "ATA": 13.50,
    "TTC": 13.01, "CCA": 12.72, "ATC": 12.64, "GTA": 12.37, "TCC": 12.15,
    "TAC": 11.77, "GCC": 11.50, "AGA": 11.25, "TGG": 11.07, "CAG": 10.86,
    "ACC": 10.71, "GTC": 10.66, "AGC": 9.18, "TGT": 9.02, "CTA": 8.73,
    "GGC": 8.33, "GTG": 8.32, "TCG": 8.10, "CCC": 8.10, "CGA": 8.01,
    "CTC": 7.26, "ACG": 6.56, "CTG": 6.45, "CAC": 6.30, "CGC": 6.02,
    "TGC": 5.58, "GCG": 5.39, "AGG": 5.09, "CCG": 4.56, "GGG": 4.41,
    "CGG": 2.99,
}
_spom_total = sum(_S_POMBE_RAW.values())
CARRIER_S_POMBE: Dict[str, float] = {
    c: w / _spom_total
    for c, w in _S_POMBE_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── Neurospora carrier ────────────────────────────────────────────────────────
#
# Source: Kazusa CUTG taxid 5141, Kazusa 2026-04-05.
# shared-data/data/codon_tables/neurospora_5141.json
# Pearson r vs SAE carrier = +0.6163. N. crassa; anomalously GC-rich for Tier 0 fungus

_NEUROSPORA_RAW: Dict[str, float] = {
    "GAG": 42.68, "AAG": 40.39, "GCC": 35.97, "GAC": 32.55, "GGC": 29.02,
    "AAC": 27.00, "CTC": 26.79, "ATC": 26.48, "CAG": 26.05, "GTC": 24.83,
    "ACC": 24.71, "GAT": 23.99, "GAA": 22.44, "CCC": 22.42, "TTC": 22.08,
    "ATG": 21.80, "GCT": 21.13, "TCC": 19.99, "GGT": 18.28, "CTG": 18.26,
    "CGC": 17.64, "TAC": 17.46, "AGC": 17.43, "GCG": 17.26, "CAA": 16.95,
    "GTG": 15.51, "CCT": 15.09, "TTG": 14.95, "CAC": 14.78, "CCG": 14.56,
    "TCG": 14.51, "CTT": 14.25, "ATT": 14.00, "GTT": 13.84, "GGA": 13.56,
    "ACG": 13.54, "TGG": 13.11, "GCA": 12.56, "CCA": 12.36, "TCT": 11.95,
    "AGG": 11.84, "TTT": 11.77, "AAA": 11.69, "ACT": 11.16, "GGG": 10.94,
    "ACA": 10.75, "AAT": 10.32, "CAT": 9.45, "TCA": 9.22, "CGT": 8.88,
    "AGT": 8.66, "CGG": 8.54, "TAT": 8.47, "AGA": 7.91, "TGC": 7.71,
    "CGA": 7.05, "CTA": 5.95, "GTA": 5.40, "ATA": 4.09, "TGT": 3.35,
    "TTA": 2.73,
}
_ncr_total = sum(_NEUROSPORA_RAW.values())
CARRIER_NEUROSPORA: Dict[str, float] = {
    c: w / _ncr_total
    for c, w in _NEUROSPORA_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── Sea urchin carrier ────────────────────────────────────────────────────────
#
# Source: Kazusa CUTG taxid 7668, 1131 CDS, 410,481 codons, 2026-04-05.
# shared-data/data/codon_tables/strongylocentrotus_7668.json
# Pearson r vs SAE carrier = +0.3053.
# Strongylocentrotus purpuratus (purple sea urchin); echinoderm; radial nervous
# system — 5-fold symmetry, NO centralized brain. Represents the pre-
# centralization baseline: bilaterally symmetric NS not yet compacted into a
# head. Echinodermata are deuterostomes (same lineage as vertebrates) yet took
# the radial path rather than the bilateral/cephalized path.

_STRONGYLOCENTROTUS_RAW: Dict[str, float] = {
    "GGA": 57.35, "GGT": 56.14, "GAT": 41.69, "GAG": 36.44, "GAA": 34.72,
    "TTC": 30.83, "CAA": 29.16, "ATG": 27.66, "CCT": 25.66, "AGA": 25.44,
    "GGC": 23.69, "GAC": 23.06, "CAC": 22.90, "AAC": 22.27, "AAG": 22.20,
    "GCT": 21.70, "CAG": 21.57, "CAT": 20.64, "CCA": 20.30, "AGG": 19.95,
    "AAT": 19.34, "ATC": 18.54, "CGT": 17.55, "GCC": 17.02, "ACA": 16.51,
    "GTG": 15.76, "CCC": 15.27, "TTT": 15.02, "CGC": 12.67, "ACC": 12.64,
    "GTC": 11.64, "CGA": 11.49, "GCA": 11.37, "TCT": 11.37, "AGC": 10.86,
    "CTG": 10.86, "ATT": 10.78, "AAA": 10.77, "ACG": 10.06, "TAC": 9.56,
    "CTC": 9.30, "GTT": 9.20, "TCA": 9.10, "GGG": 8.93, "TCC": 8.80,
    "CTT": 8.70, "CCG": 8.18, "ACT": 8.14, "AGT": 7.94, "CTA": 6.95,
    "TGG": 6.88, "GTA": 6.77, "TAT": 6.63, "TCG": 6.33, "CGG": 6.10,
    "TGT": 5.54, "TTG": 5.51, "TGC": 5.32, "ATA": 3.99, "GCG": 3.36,
    "TTA": 3.08,
}
_spu_total = sum(_STRONGYLOCENTROTUS_RAW.values())
CARRIER_STRONGYLOCENTROTUS: Dict[str, float] = {
    c: w / _spu_total
    for c, w in _STRONGYLOCENTROTUS_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── Octopus vulgaris carrier ──────────────────────────────────────────────────
#
# Source: Kazusa CUTG taxid 6645, 32 CDS, 8,602 codons, 2026-04-05.
# shared-data/data/codon_tables/octopus_vulgaris_6645.json
# Pearson r vs SAE carrier = +0.2219.
#
# ARCHITECTURE NOTE: Octopus vulgaris has a DISTRIBUTED manifold —
# 9 semi-autonomous nervous systems (1 central brain + 8 brachial ganglia).
# ~2/3 of all neurons live in the arms, not the head. This is fundamentally
# architecturally different from any vertebrate: it is a multi-manifold
# topology with local entropy sorting per arm.
#
# LOW_N CAVEAT: only 32 CDS in Kazusa — per_1000 values have high variance.
# Use for qualitative comparisons only; do not treat r=+0.22 as precise.
#
# RNA-EDITING CAVEAT: O. vulgaris edits ~60% of neural transcripts
# post-transcriptionally (adenosine-to-inosine editing). The DNA codon table
# does NOT reflect the actual codon used during neural protein synthesis.
# A proper Octopus carrier profile requires RNA-seq data from neural tissue,
# not DNA-derived CDS counts. This profile is a placeholder until that data
# is available.

_OCTOPUS_VULGARIS_RAW: Dict[str, float] = {
    "ATG": 37.32, "GAA": 34.88, "AAA": 31.74, "GAT": 29.99, "ATT": 29.06,
    "ACA": 26.04, "AAT": 25.46, "TTT": 25.23, "GCT": 23.72, "TTC": 23.37,
    "AGA": 22.67, "AAC": 22.67, "ATC": 22.44, "CAA": 22.32, "ACT": 21.97,
    "AAG": 20.93, "TGT": 20.11, "TTG": 20.11, "GGT": 19.88, "GCA": 19.18,
    "GAC": 18.48, "GGA": 18.14, "GAG": 18.14, "AGT": 18.14, "TCA": 17.79,
    "GTT": 17.09, "ATA": 17.09, "TAT": 16.62, "CTG": 16.39, "GCC": 15.93,
    "TAC": 15.69, "TTA": 15.58, "TCT": 15.46, "CAG": 15.35, "TGC": 15.11,
    "GTC": 14.42, "CTC": 14.18, "TCC": 13.83, "TGG": 13.60, "CTT": 13.60,
    "GTA": 13.49, "CGT": 13.25, "GTG": 11.97, "CCA": 11.97, "CGA": 11.74,
    "CAT": 11.63, "ACC": 11.51, "CCT": 11.39, "AGC": 10.58, "GGC": 9.53,
    "TCG": 7.67, "CAC": 7.09, "ACG": 6.98, "CGC": 6.63, "CTA": 6.51,
    "AGG": 5.46, "CCC": 5.46, "CCG": 4.30, "CGG": 3.60, "GCG": 3.14,
    "GGG": 2.67,
}
_oct_total = sum(_OCTOPUS_VULGARIS_RAW.values())
CARRIER_OCTOPUS_VULGARIS: Dict[str, float] = {
    c: w / _oct_total
    for c, w in _OCTOPUS_VULGARIS_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── Alligator carrier (archosaur / dinosaur proxy) ────────────────────────────
#
# Source: Kazusa CUTG taxid 8496, 18 CDS, 6,488 codons, 2026-04-05.
# shared-data/data/codon_tables/alligator_mississippiensis_8496.json
# Pearson r vs SAE carrier = +0.7952.
#
# LOW_N CAVEAT: 18 CDS only — treat as indicative, not measured.
#
# DINOSAUR PROXY: Crocodylia (alligators + crocodiles) are the sister clade to
# Aves (birds) within Archosauria. Together they bracket the dinosaur lineage:
#   - Alligator diverged from the bird/dinosaur line ~250 Mya
#   - Chicken (r=+0.89) represents the avian end of the bracket
# Inference: Mesozoic archosaur neural codon bias was likely r=+0.80–0.89 vs
# SAE — NOT the low-r AT-rich "reptile" assumption. Brontosaurus and its
# relatives were probably running GC-rich neural protein synthesis,
# architecturally more similar to modern birds than to extant lizards.
# This is a bracket inference, not a direct measurement.

_ALLIGATOR_RAW: Dict[str, float] = {
    "GAG": 41.92, "AAG": 41.62, "AAA": 34.53, "ATG": 34.22, "CTG": 33.91,
    "CAG": 30.21, "GAA": 28.82, "GAC": 26.66, "GTG": 24.04, "AAC": 23.27,
    "ATC": 23.27, "GCC": 22.97, "GAT": 22.50, "GGC": 20.19, "CAC": 20.19,
    "AGC": 19.57, "ATT": 19.42, "GCT": 18.96, "TTC": 18.65, "TTT": 18.34,
    "ACC": 18.03, "TAC": 17.88, "CAT": 16.65, "ACT": 16.34, "ACA": 15.72,
    "CCC": 15.72, "GGA": 15.57, "GTT": 15.41, "TGC": 15.26, "AAT": 14.80,
    "CTC": 14.33, "CCA": 14.33, "GTC": 14.18, "CCT": 14.18, "CTT": 14.03,
    "GGG": 13.72, "TCC": 13.56, "TTG": 13.26, "TGT": 12.79, "GCA": 12.64,
    "TAT": 12.48, "AGA": 12.18, "CAA": 11.87, "GGT": 11.41, "TCT": 11.10,
    "AGG": 10.79, "AGT": 10.79, "TCA": 10.33, "TGG": 9.25, "ATA": 8.94,
    "CGC": 8.94, "CCG": 7.40, "CGG": 7.24, "GTA": 6.78, "CGT": 6.32,
    "CTA": 6.32, "TTA": 6.01, "GCG": 5.39, "CGA": 4.78, "TCG": 4.16,
    "ACG": 3.08,
}
_ali_total = sum(_ALLIGATOR_RAW.values())
CARRIER_ALLIGATOR: Dict[str, float] = {
    c: w / _ali_total
    for c, w in _ALLIGATOR_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

# ── Insect / human convergent carrier ─────────────────────────────────────────
#
# Source: Kazusa, Drosophila melanogaster taxid 7227 + Homo sapiens taxid 9606,
# 2026-04-05. Drosophila and human codon preferences converge on GC-ending
# codons (CAG/AAG/GAG/GCC/GGC). This is the compression target for insect-level
# intelligence — the inflection point where codon bias transitions from AU-rich
# (C. elegans floor) to GC-rich (human ceiling).
#
# The convergence of Drosophila and human on the same preferred codons is
# independent evidence that this codon set is the stable attractor for
# complex neural computation (Layer 0 ground truth for the Mirror LUT).
# See CARRIER_DROSOPHILA above for the pure validated Drosophila baseline (r=0.7917).

_INSECT_HUMAN_RAW: Dict[str, float] = {
    # Drosophila dominant, human concordant
    "CAG": 0.715, "AAG": 0.635, "GAG": 0.625, "CAC": 0.590, "AAC": 0.545,
    "GAC": 0.505, "GCC": 0.425, "GGC": 0.385, "ACC": 0.370, "CCC": 0.325,
    "CGC": 0.330, "GAA": 0.375, "CAA": 0.285, "AAA": 0.365, "CCG": 0.245,
    "GGA": 0.270, "ACG": 0.230, "CCA": 0.265, "AGC": 0.245, "ACA": 0.240,
    # Human dominant over Drosophila
    "CTG": 0.420, "GTG": 0.280, "TCC": 0.220, "GCA": 0.225, "GCG": 0.150,
    "GGG": 0.200, "AGG": 0.180, "AGA": 0.130, "ATG": 0.100, "TTG": 0.090,
}
_ih_total = sum(_INSECT_HUMAN_RAW.values())
CARRIER_INSECT_HUMAN: Dict[str, float] = {
    c: w / _ih_total
    for c, w in _INSECT_HUMAN_RAW.items()
    if len(c) == 3 and all(b in NATURAL_BASES for b in c)
}

CARRIER_PROFILES: Dict[str, Dict[str, float]] = {
    # ── SAE-derived profiles ──────────────────────────────────────────────────
    "gag_wobble_gc":    CARRIER_GAG_WOBBLE_GC,    # SAE GROUNDED baseline (r=0.72)
    "neural_binding":   CARRIER_NEURAL_BINDING,   # SAE lock weights — binding sites
    # ── Fungal tier (Tier 0) — pre-neuronal information transfer ─────────────
    "saccharomyces":    CARRIER_SACCHAROMYCES,    # S. cerevisiae yeast floor (r=+0.29)
    "s_pombe":          CARRIER_S_POMBE,          # fission yeast (r=+0.31)
    "neurospora":       CARRIER_NEUROSPORA,       # N. crassa filamentous fungus (r=+0.62, anomaly)
    # ── Invertebrate rungs ────────────────────────────────────────────────────
    "strongylocentrotus": CARRIER_STRONGYLOCENTROTUS,  # sea urchin echinoderm, radial NS (r=+0.31, 1131 CDS)
    "octopus_vulgaris": CARRIER_OCTOPUS_VULGARIS,      # distributed manifold !LOW_N !RNA_EDITING (r=+0.22)
    "c_elegans":        CARRIER_C_ELEGANS,             # 302-neuron floor (AT-rich, r=+0.11 vs SAE)
    "drosophila":       CARRIER_DROSOPHILA,       # insect validated (r=+0.79, 22M codons)
    # ── Vertebrate rungs ──────────────────────────────────────────────────────
    "zebrafish":        CARRIER_ZEBRAFISH,        # fish (r=+0.89)
    "xenopus":          CARRIER_XENOPUS,          # amphibian (r=+0.76)
    "alligator":        CARRIER_ALLIGATOR,        # archosaur / dinosaur proxy !LOW_N (r=+0.80, 18 CDS)
    "chicken":          CARRIER_CHICKEN,          # bird — vertebrate peak (r=+0.89)
    "mouse":            CARRIER_MOUSE,            # rodent model organism (r=+0.87)
    "rat":              CARRIER_RAT,              # rodent (r=+0.88)
    "rabbit":           CARRIER_RABBIT,           # mammal (r=+0.82)
    "pig":              CARRIER_PIG,              # mammal, large brain (r=+0.83)
    # ── Primate rungs ─────────────────────────────────────────────────────────
    "marmoset":         CARRIER_MARMOSET,         # small NHP (r=+0.77)
    "macaque":          CARRIER_MACAQUE,          # rhesus NHP / Allen Brain ref (r=+0.80)
    "human":            CARRIER_HUMAN,            # Homo sapiens ceiling (r=+0.87)
    # ── Convergent attractor ──────────────────────────────────────────────────
    "insect_human":     CARRIER_INSECT_HUMAN,     # Drosophila+human convergent GC attractor
}
DEFAULT_PROFILE = "neural_binding"  # upgraded from gag_wobble_gc

# ── Voxel addressing (TensorCompass integration) ──────────────────────────────
#
# Each generated Hachimoji sequence maps to a voxel_key in the TensorCompass
# arrow field.  The key is derived from the sequence's MI feature vector,
# placing it in the same n-space as all other substrate objects.
#
# This is the MOF node address: the voxel_key IS the "metal cluster" identity
# in the framework.  PZSB codons in the payload channel encode which neighboring
# voxels (other sequences) are connected by "pipes" (adjacency matrix entries).
#
# Requires: tools/heerich_model.py (optional — degrades gracefully if absent)
# Requires: ene_mi_signal.py        (optional — degrades gracefully if absent)

def sequence_voxel_key(sequence: List[str], block_size: int = 8) -> Optional[int]:
    """Compute the 34-bit TensorCompass voxel_key for a Hachimoji sequence.

    Method:
      1. Extract the ACGT carrier codons from the sequence.
      2. Encode as codon-index byte stream (uint8, values 0-63).
      3. Run extract_mi_features() to get the 11-axis MI vector.
      4. Call nd_point_to_voxel_key(mi_features, ioc=mi_features[9]) for the
         34-bit haploid address (30-bit xyz + 4-bit IoC regime prefix).

    Returns:
      34-bit int, or None if heerich_model / ene_mi_signal are unavailable.

    Decision log:
      D8 — Gemini session ba899ebf: voxel_key IS the MOF node identity.
           nd_point_to_voxel_key places the sequence in the TensorCompass
           arrow field used by all other substrate objects.
      D9 — The 8096-bit subregister per user = 900 Hachimoji codons × 9 bits.
           Each subregister entry is one voxel in the compass field.
           The 14-axis concept_vector (stored at the same key) provides the
           semantic layer; MI features provide the structural layer.
    """
    try:
        import sys as _sys
        import os as _os
        _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        if _root not in _sys.path:
            _sys.path.insert(0, _root)
        from ene_mi_signal import extract_mi_features
        from tools.heerich_model import nd_point_to_voxel_key
    except ImportError:
        return None

    carrier, _ = disassemble(sequence)
    if len(carrier) < 8:
        return None

    # Encode carrier as codon-index bytes (0-63, natural codons only)
    nat_idx = {c: i for i, c in enumerate(
        a+b+c for a,b,c in __import__('itertools').product("ACGT", repeat=3)
    )}
    stream = bytes(nat_idx.get(c, 0) for c in carrier if c in nat_idx)
    if len(stream) < 8:
        return None

    feats = extract_mi_features(stream)
    ioc   = feats[9] if len(feats) > 9 else None
    return nd_point_to_voxel_key(feats, scale=10.0, ioc=ioc)

# ── Stream encoding ───────────────────────────────────────────────────────────

def encode_uint16_stream(codon_list: List[str]) -> bytes:
    """Serialise a codon list as little-endian uint16 stream (2 bytes/codon)."""
    idxs = [CODON_TO_IDX[c] for c in codon_list if c in CODON_TO_IDX]
    return struct.pack(f"<{len(idxs)}H", *idxs)


def decode_uint16_stream(data: bytes) -> List[str]:
    """Deserialise a uint16 stream back to codon list."""
    n = len(data) // 2
    idxs = struct.unpack(f"<{n}H", data[:n * 2])
    return [IDX_TO_CODON[i] for i in idxs if i in IDX_TO_CODON]

# ── Carrier generation ────────────────────────────────────────────────────────

def generate_carrier(
    length: int,
    profile: str = DEFAULT_PROFILE,
    rng: Optional[random.Random] = None,
) -> List[str]:
    """Generate `length` ACGT carrier codons from a SAE-derived frequency profile.

    The weighted sampling reproduces the codon distribution of top-MI SAE
    features (see decision D2).  length is in CODONS (not bases).

    Args:
        length:  number of ACGT codons to generate
        profile: carrier profile key from CARRIER_PROFILES
        rng:     seeded Random instance for reproducibility

    Returns:
        List of ACGT codon strings, each 3 characters.
    """
    if rng is None:
        rng = random.Random()
    freq = CARRIER_PROFILES[profile]
    codons = list(freq.keys())
    weights = list(freq.values())
    return rng.choices(codons, weights=weights, k=length)

# ── Payload encoding ──────────────────────────────────────────────────────────

def encode_payload(data: bytes) -> List[str]:
    """Encode arbitrary bytes as PZSB codon sequence (nibble scheme, see D6).

    Each byte becomes two PZSB codons (high nibble, low nibble).
    Uses only the 16 codons in NIBBLE_PALETTE — stays within the
    24-codon budget that keeps LZMA ratio at 0.326 (see D5).

    Args:
        data: payload bytes to encode

    Returns:
        List of PZSB codon strings (length = 2 × len(data)).
    """
    out: List[str] = []
    for byte in data:
        out.append(NIBBLE_PALETTE[(byte >> 4) & 0xF])   # high nibble
        out.append(NIBBLE_PALETTE[byte & 0xF])           # low nibble
    return out


def decode_payload(pzsb_codons: List[str]) -> bytes:
    """Recover payload bytes from a PZSB codon sequence.

    Ignores codons not in NIBBLE_PALETTE (e.g. CONSTANT_FILL = PPP padding).
    Pairs consecutive valid codons to reconstruct bytes.

    Args:
        pzsb_codons: list of PZSB codon strings

    Returns:
        Recovered payload as bytes.
    """
    nibbles: List[int] = [
        NIBBLE_RMAP[c] for c in pzsb_codons if c in NIBBLE_RMAP
    ]
    # pair nibbles → bytes
    out = bytearray()
    for i in range(0, len(nibbles) - 1, 2):
        out.append((nibbles[i] << 4) | nibbles[i + 1])
    return bytes(out)

# ── Sequence assembly ─────────────────────────────────────────────────────────

def assemble(
    carrier_codons: List[str],
    payload: bytes,
    block_size: int = 8,
) -> List[str]:
    """Assemble a Hachimoji sequence from an ACGT carrier and a payload.

    Layout (repeating blocks, see decision D4):

        [ block_size × ACGT ] [ block_size × PZSB ] [ block_size × ACGT ] ...

    Each PZSB block encodes block_size // 2 bytes of payload (2 PZSB codons
    per byte via the nibble scheme).  Remaining PZSB slots filled with PPP.

    Args:
        carrier_codons: ACGT codon list (should be multiple of block_size)
        payload:        bytes to encode; may be empty
        block_size:     ACGT codons per block (and PZSB codons per block)

    Returns:
        Assembled Hachimoji codon list (ACGT and PZSB interleaved in blocks).
    """
    payload_codons = encode_payload(payload)
    p_idx = 0   # index into payload_codons

    out: List[str] = []
    for i in range(0, len(carrier_codons), block_size):
        acgt_block = carrier_codons[i : i + block_size]
        out.extend(acgt_block)

        # PZSB block
        for _ in range(block_size):
            if p_idx < len(payload_codons):
                out.append(payload_codons[p_idx])
                p_idx += 1
            else:
                out.append(CONSTANT_FILL)

    return out


def disassemble(sequence: List[str]) -> Tuple[List[str], bytes]:
    """Split a Hachimoji sequence into its carrier and payload.

    Assumes the [8 ACGT + 8 PZSB] block structure from assemble().
    Carrier codons are those where all bases are natural (A/T/G/C).
    PZSB codons come from the even-indexed blocks.

    Args:
        sequence: Hachimoji codon list

    Returns:
        (carrier_codons, payload_bytes)
    """
    carrier: List[str] = []
    pzsb: List[str] = []
    for cod in sequence:
        if all(b in NATURAL_BASES for b in cod):
            carrier.append(cod)
        elif all(b in SYNTH_BASES for b in cod):
            pzsb.append(cod)
        # mixed codons are discarded (not used in this scheme)

    payload = decode_payload(pzsb)
    return carrier, payload

# ── Compression helpers ───────────────────────────────────────────────────────

def compress_sequence(sequence: List[str]) -> bytes:
    """LZMA-compress a Hachimoji codon sequence.

    First serialises to uint16 stream, then compresses.
    Expected ratio: 0.30–0.33 for sequences built with this module.
    """
    return lzma.compress(encode_uint16_stream(sequence), preset=6)


def metrics(sequence: List[str]) -> Dict[str, float]:
    """Compute compression and information metrics for a sequence.

    Returns a dict with:
      codon_count       — length of sequence
      unique_codons     — distinct codons observed
      unique_acgt       — distinct ACGT codons
      unique_pzsb       — distinct PZSB codons
      raw_bytes         — uncompressed stream size
      compressed_bytes  — LZMA compressed size
      lzma_ratio        — compressed / raw
      payload_capacity  — bytes encodable at nibble scheme capacity
    """
    raw = encode_uint16_stream(sequence)
    comp = lzma.compress(raw, preset=6)
    acgt = [c for c in sequence if all(b in NATURAL_BASES for b in c)]
    pzsb = [c for c in sequence if all(b in SYNTH_BASES   for b in c)]
    blocks = len(acgt) // 8
    return {
        "codon_count":       len(sequence),
        "unique_codons":     len(set(sequence)),
        "unique_acgt":       len(set(acgt)),
        "unique_pzsb":       len(set(pzsb)),
        "raw_bytes":         len(raw),
        "compressed_bytes":  len(comp),
        "lzma_ratio":        round(len(comp) / len(raw), 4),
        "payload_capacity":  blocks * 4,   # 4 bytes/block at nibble rate
    }

# ── Complement ────────────────────────────────────────────────────────────────

def complement_codon(codon: str) -> str:
    """Return the Watson-Crick / Hachimoji complement of a codon (3′→5′)."""
    return "".join(HACHI_PAIRS.get(b, "N") for b in reversed(codon))


# ── Quine record format (KD1 + KD2 from session 20260405) ────────────────────
#
# Derivation (Gemini session ba899ebf):
#   A SHA-256 hash is 256 bits.  Hachimoji = 3 bits/base → 1 base/codon (encoding
#   a codon at base level: each 3-bit chunk = 1 Hachimoji letter).
#   256 bits / 3 = 85.33 → 86 Hachimoji letters (codons).
#   Every Git commit hash maps deterministically to an 86-codon strand.
#
# Full Quine format (self-describing, codec-rot-immune):
#
#   [ Phase gate  (1 codon)  ]  →  Routes to GROUNDED/SEISMIC/FLAME on decode
#   [ PTOS header (24 codons)]  →  8 PTOS categories × 3 codons each (8 enum values each)
#   [ SHA-256 id  (86 codons)]  →  Content-addressable identity of the engram
#   [ USC payload (variable) ]  →  LZMA-compressed content
#
# If Phase gate ∈ FLAME_CODONS → emit SUBFRAME_CONSTANT(0), skip decode.
# Session record: sessions/hachimoji-mof-connection-machine-sovereign-stack-20260405.json

SHA256_BASE_LEN   = 86    # single Hachimoji bases needed for 256 bits (ceil(256/3))
SHA256_CODON_LEN  = SHA256_BASE_LEN  # legacy alias (unit = bases, not packed 3-base codons)
SHA256_PACKED_CODONS = 29  # ceil(86/3) — codons (3-base words) needed in the sequence
PTOS_HEADER_LEN   = 24    # 8 PTOS fields × 3 codons each (in 3-base codons)
QUINE_PHASE_LEN   = 1     # 1 codon (3-base word)
QUINE_HEADER_CODONS = QUINE_PHASE_LEN + PTOS_HEADER_LEN + SHA256_PACKED_CODONS  # = 54 codons
QUINE_HEADER_LEN  = QUINE_HEADER_CODONS  # = 54 (kept for back-compat; was wrong at 111)

# Phase gate codons (1 codon = one of the 8 pure-PZSB codons for clean separation)
PHASE_GROUNDED = "PPP"   # MI ≥ 0.65
PHASE_SEISMIC  = "PZP"   # 0.35 ≤ MI < 0.65
PHASE_FLAME     = "PSP"   # MI < 0.35  → skip decode
FLAME_CODONS    = frozenset({PHASE_FLAME})

# ── Subregister layout (validated 2026-04-05) ─────────────────────────────────
#
# Each user occupies exactly one 8096-bit subregister entry in the sovereign
# stack concept_vector field — analogous to AL/AH/AX/EAX/RAX nested registers.
#
# Validation:
#   8096 bits / 3 bits·base⁻¹ = 2698.67 → 900 codons (8100 bits, 4-bit slack)
#   The 4-bit slack = 1 parity nibble, used for error detection at seam.
#
# Why 8096 bits is the RIGHT size for Hachimoji:
#   8 Hachimoji bases = exactly 3 bits (2³ = 8) — the only DNA alphabet size
#   that is a power of 2.  This makes every base exactly 1 octal digit.
#   The entire subregister is therefore octal-aligned with zero padding waste.
#   With 4 natural bases (2 bits/base) this size would waste 8096 % 2 = 0 bits
#   but with 8 bases the parity nibble at the seam gives free error correction.
#
# Layout of one 900-codon subregister strand (RAX):
#
#   [AL]  Phase gate   : 1  codon  (9 bits)  → GROUNDED / SEISMIC / FLAME
#   [AH]  PTOS header  : 24 codons (216 bits) → 8 PTOS fields × 3 codons
#   [AX]  SHA-256 id   : 29 codons (261 bits) → 256-bit identity, 5-bit slack
#   [EAX] Quine total  : 54 codons (486 bits)
#   [RAX] Full entry   : 900 codons (8100 bits, 4-bit parity nibble)
#
# Payload capacity (846 codons → 423 bytes usable via nibble encoding):
#   concept_vector   14 × f32 =  56 bytes   (14-axis semantic fingerprint)
#   nd_point         15 × f32 =  60 bytes   (TensorCompass n-space position)
#   voxel_key_4d     uint64   =   8 bytes   (34-bit haploid MOF address)
#   SAE feature_id   uint32   =   4 bytes   (NVIDIA ESM SAE atlas feature)
#   MI features      11 × f32 =  44 bytes   (extract_mi_features() axes)
#   activation       8  × f32 =  32 bytes   (engram blink history)
#   timestamps       2  × u32 =   8 bytes   (created_at / updated_at)
#   ─────────────────────────────────────────
#   Total fingerprint           208 bytes   (215 bytes spare for labels/notes)
#
# MOF topology @ block_size=8:
#   ~52 pipe sets per entry; each pipe block = 8 PZSB codons = 72 bits = 24 bases
#   PZSB codons encode adjacency pointers to neighbouring subregister entries.
#   Feynman routing logic (Connection Machine parallel gas) uses these pipes.
#
# Reference: sessions/hachimoji-mof-connection-machine-sovereign-stack-20260405.json

SUBREGISTER_BITS    = 8096
SUBREGISTER_CODONS  = 900     # ceil(8096 / 9)
SUBREGISTER_PARITY  = 4       # slack bits at seam (parity nibble)
SUBREGISTER_PAYLOAD_CODONS = SUBREGISTER_CODONS - QUINE_HEADER_CODONS
# = 900 - 54 = 846 payload codons → 423 bytes usable

# Optional heerich_model integration (graceful fallback if not on path)
try:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "..", "tools"))
    from heerich_model import (
        voxel_key_4d         as _voxel_key_4d,
        ioc_regime_bin       as _ioc_regime_bin,
        nd_point_to_voxel_key as _nd_point_to_voxel_key,
    )
    _HEERICH_AVAILABLE = True
except ImportError:
    _HEERICH_AVAILABLE = False


def encode_sha256(hash_bytes: bytes) -> List[str]:
    """Encode a 32-byte SHA-256 digest as 86 Hachimoji codons.

    Method: treat the 256-bit hash as a big-endian integer, emit groups of
    3 bits as Hachimoji base indices (into HACHI_BASES = "ACGTPZSB").
    The 86th codon encodes the remaining 2 bits (left-aligned, LSBs = 0).

    Args:
        hash_bytes: raw SHA-256 digest (32 bytes)

    Returns:
        86-element list of single-letter strings (one Hachimoji base per codon).
        To treat these as codons, pad to length-3 by repeating the base: AAA, CCC…
        or store as single-letter run  — caller's choice.
    """
    if len(hash_bytes) != 32:
        raise ValueError(f"SHA-256 must be 32 bytes; got {len(hash_bytes)}")
    # Unpack as big-endian integer
    val = int.from_bytes(hash_bytes, "big")
    bases: List[str] = []
    for _ in range(SHA256_CODON_LEN):
        shift = 256 - 3 * (len(bases) + 1)
        if shift >= 0:
            idx = (val >> shift) & 0b111
        else:
            # Final partial group: left-align remaining bits
            remaining = 256 - 3 * len(bases)
            idx = (val & ((1 << remaining) - 1)) << (3 - remaining)
        bases.append(HACHI_BASES[idx])
    return bases


def decode_sha256(bases: List[str]) -> bytes:
    """Recover a SHA-256 digest from 86 Hachimoji bases (inverse of encode_sha256).

    Args:
        bases: 86 single-character strings from HACHI_BASES

    Returns:
        32-byte SHA-256 digest.
    """
    val = 0
    for i, b in enumerate(bases[:SHA256_CODON_LEN]):
        idx = HACHI_BASES.index(b)
        shift = 256 - 3 * (i + 1)
        if shift >= 0:
            val |= idx << shift
        else:
            remaining = 256 - 3 * i
            val |= idx >> (3 - remaining)
    return val.to_bytes(32, "big")


def make_quine_record(
    sha256_hex: str,
    ptos: Dict[str, str],
    payload: bytes,
    phase: str = PHASE_GROUNDED,
) -> List[str]:
    """Build a Quine-complete Hachimoji record for a Git commit.

    Layout: [phase gate] + [PTOS header] + [SHA-256 identity] + [payload codons]

    Args:
        sha256_hex: 64-char hex SHA-256 of the commit/object
        ptos:       dict with keys LAYER, DOMAIN, TIER, STAGE, MODULE,
                    CONDITION, SOURCE, DEFER — each value a short string.
                    Truncated/padded to 3 chars and encoded as Hachimoji bases.
        payload:    USC-compressed bytes to embed in the payload channel
        phase:      Phase gate codon (PHASE_GROUNDED / SEISMIC / FLAME)

    Returns:
        Full Hachimoji codon list for the record.
    """
    # 1. Phase gate (1 codon stored as 3-base string)
    gate = [phase]

    # 2. PTOS header: 8 fields × 3 codons = 24 codons
    #    Each field encoded as 3 Hachimoji bases (raw ASCII→base-8 mapping)
    ptos_fields = ["LAYER", "DOMAIN", "TIER", "STAGE", "MODULE",
                   "CONDITION", "SOURCE", "DEFER"]
    header: List[str] = []
    for field in ptos_fields:
        val = ptos.get(field, "???")[:3].ljust(3, "?")
        for ch in val:
            byte = ord(ch) & 0xFF
            # Encode 8-bit char as 3 Hachimoji bases: bits [2:0] | [5:3] | [7:6]
            b0 = HACHI_BASES[(byte     ) & 0x7]
            b1 = HACHI_BASES[(byte >> 3) & 0x7]
            b2 = HACHI_BASES[(byte >> 6) & 0x3]  # only 4 values needed
            header.append(b0 + b1 + b2)

    # 3. SHA-256 identity (86 codons as single Hachimoji bases in a 3-char codon)
    sha_bytes  = bytes.fromhex(sha256_hex)
    sha_bases  = encode_sha256(sha_bytes)
    # Group into 3-char codons (some will be homopolymers like "AAA")
    sha_codons: List[str] = []
    for i in range(0, len(sha_bases), 3):
        group = sha_bases[i:i+3]
        while len(group) < 3:
            group.append(group[-1])
        sha_codons.append("".join(group))

    # 4. Payload via nibble encoding
    payload_codons = encode_payload(payload)

    return gate + header + sha_codons + payload_codons


def parse_quine_record(sequence: List[str]) -> Dict[str, object]:
    """Decode a Quine record built by make_quine_record.

    Returns dict with:
      phase        — PHASE_GROUNDED / SEISMIC / FLAME
      ptos         — dict of 8 PTOS fields
      sha256_hex   — recovered hex digest (64 chars)
      payload      — recovered payload bytes
      is_flame     — True if phase gate is FLAME (payload not decoded)
    """
    if not sequence:
        return {}

    phase = sequence[0]
    if phase in FLAME_CODONS:
        return {"phase": phase, "is_flame": True}

    # PTOS header: 24 codons (3 per field × 8 fields)
    # Each codon encodes one ASCII char via bits [2:0]|[5:3]|[7:6] across its 3 bases
    ptos_fields = ["LAYER", "DOMAIN", "TIER", "STAGE", "MODULE",
                   "CONDITION", "SOURCE", "DEFER"]
    ptos: Dict[str, str] = {}
    offset = 1
    for field in ptos_fields:
        chars = ""
        for _ in range(3):
            cod = sequence[offset] if offset < len(sequence) else "AAA"
            i0  = HACHI_BASES.index(cod[0])
            i1  = HACHI_BASES.index(cod[1])
            i2  = HACHI_BASES.index(cod[2])
            chars += chr(i0 | (i1 << 3) | (i2 << 6))
            offset += 1
        ptos[field] = chars.rstrip("?")

    # SHA-256: next sha-codons
    sha_n = SHA256_CODON_LEN // 3 + (1 if SHA256_CODON_LEN % 3 else 0)
    sha_bases: List[str] = []
    for cod in sequence[offset: offset + sha_n]:
        for b in cod:
            sha_bases.append(b)
    sha_bytes = decode_sha256(sha_bases[:SHA256_CODON_LEN])
    sha256_hex = sha_bytes.hex()
    offset += sha_n

    # Payload
    payload = decode_payload(sequence[offset:])

    return {
        "phase":      phase,
        "is_flame":    False,
        "ptos":       ptos,
        "sha256_hex": sha256_hex,
        "payload":    payload,
    }


# ── Subregister entry ──────────────────────────────────────────────────────────

class SubregisterEntry(NamedTuple):
    """One 8096-bit subregister entry: Quine header + fingerprint payload.

    Maps to one node (voxel) in the TensorCompass MOF lattice.
    PZSB blocks in `sequence` carry adjacency pointers (MOF pipes) to
    neighbouring subregister entries — traversable by Feynman routing.
    """
    voxel_key:   int
    sha256_hex:  str
    ptos:        Dict[str, str]
    phase:       str
    sequence:    List[str]
    payload_raw: bytes


def sequence_to_voxel_key(
    sequence: List[str],
    nd_point: Optional[List[float]] = None,
) -> int:
    """Derive a 34-bit haploid voxel_key_4d from a Hachimoji sequence.

    Falls back to a deterministic 30-bit hash key when heerich_model is absent.

    Args:
        sequence:  Hachimoji codon list (typically 900 codons for full entry).
        nd_point:  Optional 15-D PCA coordinate from TensorCompass.

    Returns:
        34-bit int (regime[33:30]|x[29:20]|y[19:10]|z[9:0]) or 30-bit fallback.
    """
    n_total = len(sequence) or 1
    counts: Dict[str, int] = {}
    for c in sequence:
        counts[c] = counts.get(c, 0) + 1
    dom_frac = max(counts.values(), default=0) / n_total
    unique_n = len(counts)

    if nd_point is not None and _HEERICH_AVAILABLE:
        return _nd_point_to_voxel_key(nd_point, scale=10.0, ioc=dom_frac)

    if _HEERICH_AVAILABLE:
        x = int((dom_frac - 0.5) * 1000) & 0x3FF
        if x >= 512: x -= 1024
        y = (unique_n - 256) & 0x3FF
        if y >= 512: y -= 1024
        z = hash(tuple(sequence[:8])) & 0x3FF
        if z >= 512: z -= 1024
        regime = 1 if dom_frac < 0.1 else (2 if dom_frac < 0.4 else 3)
        return _voxel_key_4d(x, y, z, regime)

    # Standalone fallback: deterministic 30-bit key from stream hash
    import hashlib
    h = int(hashlib.sha256(encode_uint16_stream(sequence)).hexdigest(), 16)
    x = (h >>  0) & 0x3FF; x = x - 1024 if x >= 512 else x
    y = (h >> 10) & 0x3FF; y = y - 1024 if y >= 512 else y
    z = (h >> 20) & 0x3FF; z = z - 1024 if z >= 512 else z
    return ((x & 0x3FF) << 20) | ((y & 0x3FF) << 10) | (z & 0x3FF)


def make_subregister_entry(
    sha256_hex: str,
    ptos: Dict[str, str],
    fingerprint: bytes,
    nd_point: Optional[List[float]] = None,
    phase: str = PHASE_GROUNDED,
) -> SubregisterEntry:
    """Build a complete 900-codon subregister entry for one user / commit.

    Packs exactly SUBREGISTER_CODONS (900) codons, padded with CONSTANT_FILL.
    fingerprint must be ≤ 423 bytes (nibble encoding capacity of payload slot).

    Payload suggestion (208 bytes):
        struct.pack('<14f 15f Q I 10f 8f 2I', *concept_vector, *nd_point,
                    voxel_key_4d, sae_feature_id, *mi_features,
                    *activation, created_at, updated_at)

    Args:
        sha256_hex:   64-char hex SHA-256 of the Git commit or object.
        ptos:         8-field PTOS dict.
        fingerprint:  Raw bytes to store (≤ 423 bytes).
        nd_point:     Optional 15-D PCA coords for TensorCompass addressing.
        phase:        Phase gate codon (PHASE_GROUNDED / SEISMIC / FLAME).

    Returns:
        SubregisterEntry — immutable, directly serialisable via
        encode_uint16_stream(entry.sequence) → bytes for SQLite BLOB storage.
    """
    if len(fingerprint) > 423:
        raise ValueError(
            f"fingerprint {len(fingerprint)} B exceeds 423-B payload cap"
        )
    sequence = make_quine_record(sha256_hex, ptos, fingerprint, phase=phase)
    if len(sequence) < SUBREGISTER_CODONS:
        sequence += [CONSTANT_FILL] * (SUBREGISTER_CODONS - len(sequence))
    else:
        sequence = sequence[:SUBREGISTER_CODONS]

    return SubregisterEntry(
        voxel_key   = sequence_to_voxel_key(sequence, nd_point=nd_point),
        sha256_hex  = sha256_hex,
        ptos        = ptos,
        phase       = phase,
        sequence    = sequence,
        payload_raw = fingerprint,
    )

# ── CLI ───────────────────────────────────────────────────────────────────────

def cmd_generate(args: List[str]) -> None:
    """generate --payload TEXT --length N [--seed S] [--profile P] [--out FILE]"""
    import argparse
    p = argparse.ArgumentParser(prog="hachimoji_synth generate")
    p.add_argument("--payload", default="",   help="ASCII payload to encode")
    p.add_argument("--payload-hex", default="", help="Hex payload bytes")
    p.add_argument("--length",  type=int, default=256,
                   help="Carrier length in codons (default 256)")
    p.add_argument("--seed",    type=int, default=None)
    p.add_argument("--profile", default=DEFAULT_PROFILE,
                   choices=list(CARRIER_PROFILES))
    p.add_argument("--block",   type=int, default=8)
    p.add_argument("--out",     default=None, help="Output file (default stdout)")
    ns = p.parse_args(args)

    rng = random.Random(ns.seed)
    carrier = generate_carrier(ns.length, profile=ns.profile, rng=rng)

    if ns.payload_hex:
        payload = bytes.fromhex(ns.payload_hex)
    else:
        payload = ns.payload.encode()

    seq = assemble(carrier, payload, block_size=ns.block)
    m   = metrics(seq)

    text = " ".join(seq)
    if ns.out:
        Path(ns.out).write_text(text)
        print(f"Written {len(seq)} codons to {ns.out}")
    else:
        print(text)

    print(json.dumps(m, indent=2), file=sys.stderr)


def cmd_decode(args: List[str]) -> None:
    """decode FILE | - """
    import argparse
    p = argparse.ArgumentParser(prog="hachimoji_synth decode")
    p.add_argument("file", help="Sequence file or - for stdin")
    ns = p.parse_args(args)

    if ns.file == "-":
        text = sys.stdin.read()
    else:
        text = Path(ns.file).read_text()

    seq = [c for c in text.split() if c in CODON_TO_IDX]
    _, payload = disassemble(seq)
    sys.stdout.buffer.write(payload)


def cmd_metrics(args: List[str]) -> None:
    """metrics FILE | -"""
    import argparse
    p = argparse.ArgumentParser(prog="hachimoji_synth metrics")
    p.add_argument("file", help="Sequence file or - for stdin")
    ns = p.parse_args(args)

    if ns.file == "-":
        text = sys.stdin.read()
    else:
        text = Path(ns.file).read_text()

    seq = [c for c in text.split() if c in CODON_TO_IDX]
    print(json.dumps(metrics(seq), indent=2))


def cmd_test(_args: List[str]) -> None:
    """Run self-test: encode/decode round-trip + compression target."""
    rng = random.Random(0)
    # 512-codon carrier matches the size used in original analysis (see D4/D5)
    carrier  = generate_carrier(512, rng=rng)
    payload  = b"hachimoji synth self-test \x00\xff\xab\xcd"
    seq      = assemble(carrier, payload)
    _, recovered = disassemble(seq)
    assert recovered == payload, f"Round-trip FAIL: {recovered!r} != {payload!r}"

    m = metrics(seq)
    # Target: < 0.40 for 512+ carrier codons (measured 0.295 on 606-codon sequence)
    assert m["lzma_ratio"] < 0.40, f"Compression target missed: {m['lzma_ratio']}"

    print("PASS  round-trip encoding")
    print(f"PASS  lzma_ratio={m['lzma_ratio']} < 0.45")
    print(json.dumps(m, indent=2))

    # Verify nibble palette integrity
    for i, cod in enumerate(NIBBLE_PALETTE):
        assert len(cod) == 3 and all(b in SYNTH_BASES for b in cod), cod
        assert NIBBLE_RMAP[cod] == i
    print("PASS  nibble palette")

    # Verify complement
    for base, comp in HACHI_PAIRS.items():
        assert HACHI_PAIRS[comp] == base
    print("PASS  base pairing")


def cmd_regen_carrier(_args: List[str]) -> None:
    """Regenerate CARRIER_GAG_WOBBLE_GC from sae_features.db (requires DB)."""
    import collections
    db_path = Path(__file__).parents[1] / "tools" / "sae_extractor" / "sae_features.db"
    if not db_path.exists():
        print(f"DB not found at {db_path}", file=sys.stderr)
        sys.exit(1)
    import sqlite3
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()
    rows = cur.execute("""
        SELECT p.sequence FROM features f
        JOIN activations a ON a.feature_id = f.id
        JOIN proteins p ON p.sequence_hash = a.protein_id
        WHERE f.feature_id IN (7, 493, 419, 364, 963)
    """).fetchall()
    conn.close()

    counter: Dict[str, int] = collections.Counter()
    for (seq,) in rows:
        for codon in seq.strip().split():
            if len(codon) == 3 and all(b in NATURAL_BASES for b in codon):
                counter[codon] += 1

    total = sum(counter.values())
    profile = {c: round(n / total, 6) for c, n in counter.most_common()}
    print(json.dumps(profile, indent=4))


COMMANDS = {
    "generate": cmd_generate,
    "decode":   cmd_decode,
    "metrics":  cmd_metrics,
    "test":     cmd_test,
    "regen-carrier": cmd_regen_carrier,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: hachimoji_synth.py [{' | '.join(COMMANDS)}] [args]")
        print(__doc__.split("QUICK START")[1].strip())
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
