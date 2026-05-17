# Observerless Research Stack Master Memory

This file serves as the definitive local memory and core knowledge base for the Hermes Agent. It encapsulates the mathematical foundation, layer topology, core invariants, and promotion structures of the Observerless Research Stack.

---

## 1. Core Philosophy & Q16.16 Arithmetic

The Observerless Research Stack is a formal verification and compression framework grounded in cross-domain invariant analysis.
- **source of truth**: Lean 4 formalizations. All computation, transformations, and assertions must be backed by formal proofs. No unproven claims, no receipt-free promotions.
- **arithmetic totality**: Every arithmetic operation is executed using **Q16.16 fixed-point representation**. Raw floating-point arithmetic is prohibited to prevent precision drift and non-deterministic behavior.
- **receipt-bearing event**: Every transformation (compression pass, PDE discretization, STDP weights update) must yield a receipt-bearing event that preserves declared invariants.

---

## 2. Layer Topology (Levels 0 - 6)

The stack is organized into seven distinct functional tiers:

1. **Level 0 — Primordial (Pure Math)**:
   - *Substrates*: PIST/DIAT shells, Q16.16 arithmetic, BraidField, BracketedCalculus.
   - *Invariant*: `mass = t * (2k + 1 - t)`, arithmetic totality.
2. **Level 1 — Geometric (Shape-Aware)**:
   - *Substrates*: GWL rotational coupling, toroidal shells, torsion quaternions, GWL throat.
   - *Invariant*: `dE/dt <= 0`, no zero-mass singularities.
3. **Level 2 — Biological (Life-Aware)**:
   - *Substrates*: 64 codon tables, Izhikevich spiking neurons, STDP plasticity.
   - *Invariant*: Codon validity, spike threshold `v < 30mV`.
4. **Level 3 — Thermodynamic (Energy-Aware)**:
   - *Substrates*: Trixal state (thermal/work/irreversibility), homeostatic governor, HyperFlow Navier-Stokes on shells.
   - *Invariant*: Irreversibility < threshold, `|γ + s'(p*)| < 1`.
5. **Level 4 — Security (Attack-Aware)**:
   - *Substrates*: AngrySphinx exponential gate, FAMM frustration tensor, ASIC admissible operations.
   - *Invariant*: `E_solve >= 2^n` where `n = type depth`, NaN boundary at `F = 0`, operation admissibility.
6. **Level 5 — Semantic (Meaning-Aware)**:
   - *Substrates*: CrossDimensionalFilter (12 primes), manifold networking, compression control.
   - *Invariant*: Shared primes non-empty, flat-to-ordinary kernel mapping.
7. **Level 6 — Meta-Computation (Self-Aware)**:
   - *Substrates*: Cognitive load router, auto-adaptive metatyping.
   - *Invariant*: `efficiency >= 0`, mass conservation across tiers.

---

## 3. The Seven Core Invariants

Every lawful operation inside the research stack must strictly maintain these seven mathematical constraints:

1. **Mass Conservation (PIST/Geometry)**:
   - The shell mass equation `mass = t * (2k + 1 - t)` must remain perfectly conserved under all lawful transitions.
2. **Exponential Gate (AngrySphinx/Security)**:
   - Security verification complexity must scale as `E_solve >= 2^n` where `n` is type depth.
3. **Semantic Prime Conservation (CrossDimensionalFilter/Semantics)**:
   - The twelve irreducible semantic primes must be conserved across all dimensional reductions.
4. **Frustration Monotonicity (FAMM/Security)**:
   - Triadic incompatibility within the frustration tensor must grow monotonically until explicitly resolved.
5. **Homeostatic Fixed Point (HomeostaticGovernor/Thermodynamics)**:
   - Compression pressure must converge dynamically to a stable homeostatic fixed point `p*`.
6. **Cognitive Load Decomposition (CognitiveLoad/Meta)**:
   - Strategy selection must minimize the total cognitive load `L_total = λI·L_I + λE·L_E - λG·L_G + λR·L_R + λM·L_M`.
7. **Q0_64 Scalar Universality (GENSIS/Meta)**:
   - Every substrate state must reduce to a single, unsigned [0, 1) Q0_64 scalar interface to enable cross-tier validation.

---

## 4. Settlements & Promotion Ladders

Artifacts and models move through strict validation stages. No progress is permitted without receipt-bearing evidence.

### Artifact Settlement States:
```
SEED → FORMING → STABLE → CRYSTALLIZED → COMPRESSED
```

### Model Promotion Ladder:
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
*Note: Demotion is immediate if a proof is broken (moves back to COST_ACCOUNTED) or if an analogy is misleading (moves to ARCHIVED).*

---

## 5. Grounded Codebase Directories

- **`0-Core-Formalism/`**: Source of truth. Contains Lean 4 formalizations (`Semantics/`), OTOM specs (`otom/`), and Rust/Python extraction targets (`core/`).
- **`1-Distributed-Systems/`**: ENE mesh nodes, gossip control planes, and waveprobe telemetry.
- **`2-Search-Space/`**: Manifold compression algorithms (`pist_gcl_compression.py`, shifters).
- **`3-Mathematical-Models/`**: Equation registry, model maps, and mathematical databases.
- **`4-Infrastructure/`**: Hardware shims, GPU/FPGA Verilog code, and hardware drivers.
- **`5-Applications/`**: Audit tools, golden traces, Hutter prize compression benchmarks.
- **`6-Documentation/`**: Master specs, roadmaps, vision boards, and user guides.
