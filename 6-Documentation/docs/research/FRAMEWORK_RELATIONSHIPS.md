# Framework Relationships — Sovereign Research Stack

**Status:** Authoritative — replaces scattered naming/scope discussions
**Claim state:** Architecture documentation
**Scope:** Explains how GCCL, MISC, GENSIS, and USTSM relate to each other

---

## 0. The One-Sentence Version

> **GCCL is the law, MISC is the engine, GENSIS is the n-D extension, USTSM is the substrate census.**

These four frameworks are not competitors. They are layers.

---

## 1. GCCL — The Law Stack

**Full expansion:** Geometric, Cognitive, and Compression Law
**Role:** The constitutional layer — what must be preserved

GCCL defines the **receipt-bounded framework** for validating transformations of structured information. It does not implement compression, routing, or encoding. It defines the **gates** that every implementation must satisfy.

GCCL asks six questions of every transition:

| Gate | Question |
|------|----------|
| **Geometry** | What state space, projection, topology, or shape is involved? |
| **Cognition** | What meaning, load, object identity, or interpretive constraint is preserved? |
| **Compression** | What representation gain, canonicalization, or delta reduction is claimed? |
| **Cost** | What KOT / compute / routing / memory budget was spent? |
| **Scale** | Over what λ-band is the transition valid? |
| **Receipt** | What witness makes the transition auditable? |

GCCL specifies the **universal model wrapper** `M = (S, T, I, R, K, P, Q, Λ)` — state space, transforms, invariants, residual, cost ledger, projection, quarantine rule, scale band. Every framework below instantiates some subset of this wrapper.

**What GCCL is NOT:** GCCL is not an implementation, not a compression codec, not a genetic encoding system, and not a substrate catalog. It does not run. It governs.

**Location:** `6-Documentation/docs/research/GCCL_THEORY_INTRO.md`

---

## 2. MISC — The Compression Engine

**Full expansion:** Manifold-Invariant Shell Compression
**Role:** The operational layer — how GCCL laws become executable

MISC is a **unified compression framework** that implements GCCL law gates. It was derived from structural invariants spanning 2,634 cross-domain equations. It replaces linear token prediction with geometric position inference on a Riemannian-like information manifold.

MISC provides the **pipeline** that GCCL governs:

```
Data → PIST/DIAT Shell Encoding → GWL Multi-Factor Coupling
    → Cognitive Load Router (strategy selection)
    → Thermodynamic Trixal Quality (verification gate)
    → Delta GCL Encoder (encoding substrate)
    → Homeostatic Governor (self-regulation)
    → Compressed Output
```

Each stage directly implements a GCCL gate:

| MISC Stage | GCCL Gate Satisfied |
|------------|-------------------|
| PIST/DIAT Shell Encoding | Geometric (state space, projection) |
| GWL Multi-Factor Coupling | Geometric (topology, distance) |
| Cognitive Load Router | Cognitive (meaning, load decomposition) |
| Trixal Quality | Cost (KOT accounting, budget) |
| Delta GCL Encoder | Compression (representation gain) |
| Homeostatic Governor | Scale (λ-band adaptation) |
| AMMR Commit | Receipt (witness, audit) |

**What MISC is NOT:** MISC is not the law. It obeys the law. It is also not n-dimensional — it is fundamentally 2D (PIST shell coordinates). GENSIS extends it.

**Location:** `6-Documentation/docs/research/MISC_THEORY.md`

---

## 3. GENSIS — The n-D Extension

**Full expansion:** Genetic N-Space Shell Encoding (no formal acronym expansion — it names the genetic/biological extension of MISC)
**Role:** The dimensional generalization layer

GENSIS extends MISC along two axes simultaneously:

### Axis 1: Biological Coding Systems
GENSIS incorporates **every known biological/genetic coding system** as encoding substrates:
- DNA/RNA codons (64 standard + 30+ variant tables)
- Amino acid encodings (20 + 2 special: selenocysteine, pyrrolysine)
- Epigenetic marks (methylation states: 5mC, 5hmC, 5fC, 5caC)
- Histone modifications (100+ chromatin marks)
- Transcription factor binding motifs (1,600+ human TFs)
- CRISPR PAM sequences, microRNA seeds, splice site variants
- Synthetic/expanded alphabets (hachimoji 8-symbol DNA)

### Axis 2: Dimensional Generalization
GENSIS generalizes the PIST/DIAT 2D shell (`k = floor(√n)`) to **n-dimensional hypercubic shells**:

```
k = floor(n^(1/d))           # shell index (d-th root)
remaining = n - k^d           # remaining after removing d-cube
t[i] = remaining % (k+1)     # decomposes into d coordinates
mass = Π t[i]·(k - t[i] + 1)  # d-dimensional hyperbola index
```

Dimensions and their genetic basis:

| d | Shape | Genetic Basis | Use Case |
|---|-------|---------------|----------|
| 1 | Linear | DNA primary sequence | Raw nucleotides |
| 2 | Square (PIST) | Base pairs (AT/CG) | Standard MISC encoding |
| 3 | Cubic | Codon space (4³=64) | Standard genetic code |
| 4 | Tesseract | tRNA wobble + codons | Mitochondrial codes |
| 5 | 5-cube | Amino acid + modifications | Protein space |
| 6 | 6-cube | CpG methylation states | Epigenetic encoding |
| 7 | 7-cube | Histone mark combinations | Chromatin codes |
| 8 | 8-cube | TF binding dynamics | Regulatory encoding |

**What GENSIS is NOT:** GENSIS is not a separate compression algorithm. It is MISC with more dimensions and more encoding strategies. It does not define new law gates — it inherits GCCL's. It does not define new substrates — it registers with USTSM's census.

**Location:** `6-Documentation/docs/research/MISC_GENETIC_NSPACE.md` (authoritative)
**Historical reference:** `6-Documentation/docs/research/GCCL_GENETIC_INFORMATION_MIXTURE_PRIMITIVES.md`

---

## 4. USTSM — The Substrate Census

**Full expansion:** Universal Substrate Topological State Machine
**Role:** The unification layer — cataloging and composing all substrates

USTSM is the **meta-framework** that sits above GCCL, MISC, and GENSIS. It defines:

1. **What a substrate is:** A mathematical layer with state space, metric, transition, invariant, and guard
2. **The complete census:** All 36 substrates found across the Research Stack
3. **The universal interface:** Every substrate reduces to a Q0_64 scalar ∈ [0,1)
4. **Composition rules:** How substrates compose hierarchically (PIST + AngrySphinx + Trixal)
5. **The transition kernel:** `scalar → gate → route → transition → assess → update → check`

The USTSM kernel is the **universal transition function** that every substrate transition must pass through. It enforces all 7 core invariants on every transition.

USTSM organizes substrates into 7 abstraction levels:

```
Level 0 — Primordial (Q16_16, Q0_64, PIST, BraidField)       [Implemented]
Level 1 — Geometric (GWL, TorsionalPIST, Torus, GWL Throat)   [Partial]
Level 2 — Biological (Genetic Code, Spiking, Codon Opt)       [Speculative]
Level 3 — Thermodynamic (Trixal, Homeostatic, HyperFlow)      [Speculative]
Level 4 — Security (AngrySphinx, FAMM, ASICTopology)          [Partial]
Level 5 — Semantic (CrossDimensional, ManifoldNetworking)     [Speculative]
Level 6 — Meta (Cognitive Load, Adaptation, DynamicCanal)     [Speculative]
```

**What USTSM is NOT:** USTSM is not a replacement for GCCL's law gates or MISC's compression pipeline. It is the census-taker and composition engine. It tells you what substrates exist, how they compose, and whether a transition across substrates preserves invariants — but it does not define what invariants count as lawful. That's GCCL's job.

**Location:** `docs/roadmaps/UNIVERSAL_SUBSTRATE_ROADMAP.md`

---

## 5. The Layering — Not Competition

```
┌──────────────────────────────────────────────────────────────┐
│ USTSM — Substrate Census & Composition (36 substrates)        │
│ "What can compute? What invariants does it preserve?"         │
├──────────────────────────────────────────────────────────────┤
│ GENSIS — n-D Extension of MISC                                │
│ "How many dimensions? Which genetic code table?"              │
├──────────────────────────────────────────────────────────────┤
│ MISC — Compression Engine                                     │
│ "What pipeline? What encoding strategy?"                      │
├──────────────────────────────────────────────────────────────┤
│ GCCL — Law Stack                                              │
│ "What must be preserved? What receipt proves it?"             │
└──────────────────────────────────────────────────────────────┘
```

Bottom-up: GCCL defines the rules. MISC builds an engine that follows them. GENSIS adds dimensions and genetic encoding diversity. USTSM catalogs everything, proves composition, and provides the universal Q0_64 scalar interface.

**When they appear to overlap:** They don't. An apparent overlap is always a category error. Example:

- *"MISC has invariants — isn't that GCCL's job?"* No. GCCL defines what counts as an invariant gate. MISC implements specific invariants derived from equation analysis (mass conservation, mirror symmetry, resonance). GCCL is the constitution; MISC is the statute.
- *"GENSIS has genetic codes — isn't that a substrate?"* No. Genetic codes are encoding strategies inside GENSIS. The Genetic Code *substrate* (#16 in USTSM) is the formal state machine that GENSIS's strategies operate on. GENSIS is the compiler; the substrate is the target.
- *"USTSM has invariants — isn't that GCCL?"* No. USTSM records which invariants each substrate preserves. GCCL defines whether those invariants are sufficient for lawfulness. USTSM is descriptive; GCCL is normative.

---

## 6. Component Matrix

| | GCCL | MISC | GENSIS | USTSM |
|---|------|------|--------|-------|
| **What it is** | Law stack | Compression engine | n-D generalization | Substrate census |
| **What it does** | Defines valid transitions | Implements encoding pipeline | Adds dimensions + genetic codes | Catalogs and composes 36 substrates |
| **Key primitive** | Receipt (`gccl_receipt`) | PIST shell coordinate | N-dimensional hyperbola index | Q0_64 scalar |
| **Main question** | "Is this transformation lawful?" | "How compressible is this data?" | "In how many dimensions?" | "Which substrate handles this?" |
| **Lean status** | Partial (theory docs, some structures) | Partial (PIST, DIAT, GWL theory) | Speculative (GENSIS spec exists) | Partial (substrate census exists, kernel spec exists) |
| **Imports/uses** | None (foundational) | GCCL (inherits law gates) | MISC (extends pipeline) | All (enumerates everything) |
| **Authority scope** | Constitutional | Operational | Dimensional | Census-level |

---

## 7. How They Plug Together — Complete Data Lifecycle

```
1. Raw Data arrives
   → USTSM identifies candidate substrates (#1 PIST, #2 GWL, #14 Cognitive)

2. GCCL Law Gates fire
   → Geometric: state space declared? ✓ (PIST shell)
   → Cognitive: meaning preserved? ✓ (Cognitive router)
   → Compression: representation gain? ✓ (Delta GCL)
   → Cost: KOT budget check ✓ (Trixal)
   → Scale: λ-band valid? ✓ (Homeostatic)
   → Receipt: witness emitted? ✓ (AMMR commit)

3. MISC Pipeline executes
   → PIST shell encoding → GWL coupling → Cognitive routing
   → Trixal assessment → Delta GCL → Homeostatic update

4. GENSIS Dimension Selection (optional, when benefit exists)
   → Data has codon-like structure? → d=3 cubic shell
   → Data has epigenetic markers? → d=6 6-cube shell
   → Standard byte stream? → d=2 square shell (default MISC)

5. USTSM Composition (if multiple substrates needed)
   → PIST shell + AngrySphinx gate + Trixal assess = composed block
   → Cross-substrate resonance check: mass_eq? entropy_eq? scalar_eq?

6. Output
   → Compressed bitstream with shell map, trixal stamp, AMMR receipt
   → Promotion: BEAUTIFUL_PROVISIONAL → CALIBRATED_DELTA → REVIEWED → VERIFIED
```

---

## 8. One-Sentence Per Framework

- **GCCL:** Geometric, Cognitive, and Compression Law — the receipt-bounded constitutional layer that defines what a lawful transformation must preserve.
- **MISC:** Manifold-Invariant Shell Compression — the 2D compression engine that implements GCCL gates via shell coordinates, multi-factor coupling, cognitive routing, and trixal quality.
- **GENSIS:** Genetic N-Space Shell Encoding — the n-dimensional generalization of MISC incorporating every known biological coding system as additional encoding dimensions.
- **USTSM:** Universal Substrate Topological State Machine — the complete 36-substrate census and composition engine, unified under the Q0_64 scalar.

---

*This document replaces ad-hoc comparisons across theory files. See `GCCL_THEORY_INTRO.md` for GCCL detail, `MISC_THEORY.md` for MISC detail, `MISC_GENETIC_NSPACE.md` for GENSIS detail, and `docs/roadmaps/UNIVERSAL_SUBSTRATE_ROADMAP.md` for the USTSM census.*
