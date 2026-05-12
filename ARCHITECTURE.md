# ARCHITECTURE.md — Observerless Research Stack

**The single-page map of the system. Read this first.**

---

## 1. Core Idea

The Observerless Research Stack is a formal verification and compression system grounded in cross-domain invariant analysis. Every transformation — whether a byte-compression pass, a PDE discretization step, or a spiking-neuron firing — is treated as a receipt-bearing event that must preserve declared invariants. Lean 4 is the source of truth. All computation uses Q16.16 fixed-point arithmetic. No floating-point, no unproven claims, no receipt-free promotions.

---

## 2. Layer Model

```
Level 6 — Meta-Computation       Cognitive Router │ Auto-Adaptive Metatyping
Level 5 — Semantic               12 Semantic Primes │ Cross-Dimensional Filter
Level 4 — Security               AngrySphinx Gate │ FAMM Frustration │ ASIC Topology
Level 3 — Thermodynamic          Trixal Quality │ Homeostatic Governor │ HyperFlow
Level 2 — Biological             Genetic Codes │ Spiking Neurons │ STDP Weights
Level 1 — Geometric              GWL 5-Factor Coupling │ Toroidal Shells │ Quaternion Torsion
Level 0 — Primordial             PIST/DIAT Shells │ Q16.16 Arithmetic │ BraidField
```

| Level | Domain | Key Substrates | Invariant |
|-------|--------|----------------|-----------|
| 0 (Primordial) | Pure math | PIST/DIAT shells, Q16.16, BraidField, BracketedCalculus | mass = t·(2k+1-t), arithmetic totality |
| 1 (Geometric) | Shape-aware | GWL rotational coupling, toroidal shells, torsion quaternions, GWL throat | dE/dt ≤ 0, no zero-mass singularities |
| 2 (Biological) | Life-aware | 64 codon tables, Izhikevich spiking neurons, STDP plasticity | codon validity, spike threshold v < 30mV |
| 3 (Thermodynamic) | Energy-aware | Trixal state (thermal/work/irreversibility), homeostatic governor, HyperFlow NS-on-shells | irreversibility < threshold, |γ+s'(p*)| < 1 |
| 4 (Security) | Attack-aware | AngrySphinx exponential gate, FAMM frustration tensor, ASIC admissible operations | E_solve ≥ 2^n, F > 0, operation admissibility |
| 5 (Semantic) | Meaning-aware | CrossDimensionalFilter (12 primes), manifold networking, compression control | shared primes non-empty, flat→ordinary kernel |
| 6 (Meta) | Self-aware | Cognitive load router, auto-adaptive metatyping (7 invariants), adaptation, SSMS_nD | efficiency ≥ 0, mass conservation across tiers |

---

## 3. Three-Axis Pipeline

```
Substrate (ENE) ←→ Surface (Notion) ←→ Intent (Linear)
         │              │              │
         └──────────────┼──────────────┘
                        ▼
                   Metatype
                 (Q0_64 scalar)
```

- **ENE (Substrate)**: Holds ground truth — the SQLite-backed package store with hyperbolic concept coordinates
- **Notion (Surface)**: Human-facing UI and research database
- **Linear (Intent)**: Issue tracking and work orchestration
- **Metatype**: The 1D Q0_64 scalar interface that every substrate reduces to, enabling cross-tier communication

---

## 4. Data Flow

```
Raw Data
  │
  ▼
┌──────────────────┐    PIST Remap: bytes → (shell, offset, mass) coordinates
│ PIST/DIAT Remap  │    Filter grounded bytes (mass=0), count seismic bytes
└────────┬─────────┘
         ▼
┌──────────────────┐    GWL Coupling: 5-factor similarity between token pairs
│ GWL Similarity   │    w_ij = cos(Δθ)·cos(Δφ)·(1-2|Δχ|)·exp(-|Δp|²/2σ²)
└────────┬─────────┘
         ▼
┌──────────────────┐    Cognitive Router: select optimal compression strategy
│ Cognitive Router │    L_total = λI·L_I + λE·L_E - λG·L_G + λR·L_R + λM·L_M
└────────┬─────────┘
         ▼
┌──────────────────┐    Delta GCL: variable-length delta encoding + PTOS dict + Huffman
│ Delta GCL Encode │    Q16.16 fixed-point arithmetic for all transforms
└────────┬─────────┘
         ▼
┌──────────────────┐    Trixal Verify: thermodynamic quality check
│ Trixal Verify    │    dS/dt ≤ 0, Landauer bound: W ≥ k_B·T·ln(2)
└────────┬─────────┘
         ▼
┌──────────────────┐    Homeostatic Update: surprise/regret → pressure → canal width
│ Homeostatic      │    p_{t+1} = γ·p_t + α·surprise + β·regret
└────────┬─────────┘
         ▼
   Compressed Output + Receipt
```

---

## 5. Seven Core Invariants

| # | Invariant | Source | Domain | Statement |
|---|-----------|--------|--------|-----------|
| 1 | Mass Conservation | PIST | Geometry | mass = t·(2k+1−t) is preserved under all lawful transitions |
| 2 | Exponential Gate | AngrySphinx | Security | E_solve ≥ 2^n where n = type depth; NaN boundary at F=0 |
| 3 | Semantic Prime Conservation | CrossDimensionalFilter | Semantics | 12 irreducible primes preserved across dimensional reduction |
| 4 | Frustration Monotonicity | FAMM | Security | Triadic incompatibility → frustration grows until resolved |
| 5 | Homeostatic Fixed Point | HomeostaticGovernor | Thermodynamics | Compression pressure converges to stable p* |
| 6 | Cognitive Load Decomposition | CognitiveLoad | Meta | Strategy selection minimizes total load across 5 components |
| 7 | Q0_64 Scalar Universality | GENSIS | Meta | Every substrate state reduces to a single unsigned [0,1) scalar |

---

## 6. Framework Hierarchy

```
GCCL = Law Stack (what must be preserved)
  │
  ├── MISC = Compression Engine (how it runs)
  │     Uses: PIST shells, GWL coupling, Cognitive Router, Trixal Verify
  │     │
  │     └── GENSIS = N-D Extension (genetic codes + hypercubic shells)
  │           Adds: 64 codon tables, Izhikevich neurons, STDP, XNA backbones
  │
  └── USTSM = Substrate Census (36 substrates under one Q0_64 scalar)
        Maps: every substrate → state/metric/transition/invariant/guard/scalar
```

---

## 7. Repository Structure

| Path | Purpose |
|------|---------|
| `0-Core-Formalism/lean/Semantics/` | Lean 4 source (truth), FixedPoint, PIST, GWL, AVMR, FAMM, etc. |
| `0-Core-Formalism/otom/` | One-Truth-Only-Model consolidated spec |
| `0-Core-Formalism/core/` | Rust/Python extraction targets |
| `1-Distributed-Systems/` | ENE mesh nodes, gossip, waveprobe |
| `2-Search-Space/manifold/` | Manifold compression algos (pist_gcl_compression.py, shifters/) |
| `3-Mathematical-Models/` | Equation registry, math databases, model maps |
| `4-Infrastructure/` | Shims, GPU, FPGA Verilog, drivers |
| `5-Applications/` | Scripts, tests, Hutter prize work, audit tools |
| `6-Documentation/docs/` | Main documentation tree |
| `docs/` | Research papers, specs, roadmaps (aliased into 6-Documentation) |
| `shared-data/` | Databases, golden traces, artifacts |
| `workspace-config/` | IDE and environment settings |
| `scratch/` | Experimental code |

---

## 8. Settlements & Promotion Ladder

**Settlement states** (every artifact lives in one):

```
SEED → FORMING → STABLE → CRYSTALLIZED → COMPRESSED
```

Progression requires receipt-bearing evidence at each transition.

**Promotion ladder** (for models, not artifacts):

```
RAW_IDEA
  → SANITIZED_METAPHOR
  → TOY_MODEL
  → TYPED_MODEL
  → RESIDUAL_TESTED
  → COST_ACCOUNTED
  → PROOF_CANDIDATE
  → CORE_MODULE
```

Demotion is equally important — a broken proof goes back to COST_ACCOUNTED. A misleading analogy goes to METAPHOR_ONLY / ARCHIVED.

---

## 9. The Bounded Lawful Surface

Raw GCCL may be extremely expressive. Lawful GCCL is receipt-bounded.

A transition enters the lawful surface only if it satisfies:

```
valid syntax
+ declared projection
+ round-trip or explicit loss policy
+ invariant preservation
+ residual bound
+ KOT/cost bound
+ receipt
+ scale validity
```

**No receipt, no promotion. No residual, no lawfulness claim.**

---

## 10. Further Reading

- `6-Documentation/docs/AGENTS.md` — Strict LLM operating rules (the constitution)
- `6-Documentation/docs/VISION_NORTH_STAR.md` — Philosophical compass
- `6-Documentation/docs/GLOSSARY.md` — Project-wide terminology
- `CONCEPTS.md` — Quick reference for core concepts
- `6-Documentation/docs/roadmaps/ROADMAP.md` — Master implementation timeline
- `6-Documentation/docs/research/FRAMEWORK_RELATIONSHIPS.md` — GCCL/MISC/GENSIS layering
- `GETTING_STARTED.md` — Practical setup guide

---

*Observerless Research Stack — Architecture v1.0 (2026-05-04)*
