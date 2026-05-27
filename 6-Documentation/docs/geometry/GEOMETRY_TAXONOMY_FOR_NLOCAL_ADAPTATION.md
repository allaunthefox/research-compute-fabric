# Geometry Taxonomy: Mapping All Repository Formats to N-Local Topology

**Date:** 2026-04-14  
**Status:** ACTIVE INVENTORY  
**Purpose:** Decide how every existing geometry format in the repo fits (or conflicts with) the n-local topology / Physical Semantics paradigm.

---

## 1. The Classification Axes

We classify each geometry format on two independent axes:

### Axis A: Geometric Regime (what kind of space is assumed?)
| Level | Name | Key Property |
|---|---|---|
| 0 | **Euclidean** | Global identity metric `G = I`, no curvature |
| 1 | **Non-Euclidean Global** | Curvature is constant or globally defined (spherical, hyperbolic) |
| 2 | **Riemannian** | Metric tensor `G(p)` varies with position `p` |
| 3 | **Cartan / Torsion** | Metric + torsion `T^k_ij` that depends on path/trajectory |
| 4 | **N-Local** | Metric, torsion, and phase discriminator are all local and history-dependent |

### Axis B: Implementation Status (how real is it?)
| Status | Meaning |
|---|---|
| ✅ **Production** | Running in live pipeline, tested, maintained |
| 🔧 **Implemented** | Code exists, may not be wired to production |
| ⚠️ **Stub / Partial** | Scaffold or proof-of-concept |
| 📝 **Documented Only** | Spec exists, no code |
| ❌ **Deprecated** | Known wrong, superseded |

---

## 2. The Full Inventory

### 2.1 Euclidean / Global Metric

#### `infra/access_control/geometry/geometry_plugin_v2.py` — `GeometricBridgePlugin`
- **Regime:** Euclidean (Level 0)
- **Status:** ✅ Production
- **Evidence:** Computes `angular_drift = acos(phi_clamped)`, Euclidean norm `norm()`, and linear coherence `1.0 / (1.0 + angular_drift * curvature)`. Has **no trajectory memory**.
- **NSPACE_COORDINATOR_VERDICT:** "The axes are nearly perpendicular to the surface they are meant to describe. Projection onto current axes retains ~17% of the real signal."
- **ADAPTATION:** This is the highest-priority target. Must evolve to Level 4 (N-Local) by adding trajectory history and replacing Euclidean formulas with anisotropic-metric versions.

#### `tools/cache_sieve.py` — `CacheSieve`
- **Regime:** Euclidean (Level 0)
- **Status:** ✅ Production
- **Evidence:** Maps raw manifold signals (`phi_corr`, `torsion_gradient`, `radius`) directly to SLUQ inputs with linear scaling (`* 255`, `* 10`, `* 100`). No geometric preprocessing.
- **ADAPTATION:** Should consume outputs from the evolved `geometry_plugin_v2.py` rather than raw manifold values.

#### `scripts/soliton_factory.py` (phi_proximity)
- **Regime:** Euclidean (Level 0) — **flagged as wrong**
- **Status:** ❌ Deprecated by `tools/geometry_noneuclidean.py`
- **Evidence:** `EUCLIDEAN_ASSUMPTION_AUDIT.md` Finding #1: `phi_prox = max(0, 1 - abs(r - PHI) / PHI)` treats a multiplicative (Möbius) ratio in linear additive space.
- **ADAPTATION:** Replace with `log_phi_proximity()` from `geometry_noneuclidean.py`.

---

### 2.2 Non-Euclidean Global

#### `tools/geometry_noneuclidean.py`
- **Regime:** Non-Euclidean Global (Level 1)
- **Status:** 🔧 Implemented, not wired to production
- **Evidence:** Provides `log_phi_proximity` (projective line distance), `logit_z` (bounded [0,1] → (-∞,+∞)), oblique projection `_proj_oblique_ne`, and PHI-geometric orbit decay `_PHI_NEG_POW16`.
- **Key insight:** Corrects the *global* geometry (projective/Möbius instead of linear) but still has **no local metric tensor or torsion**.
- **ADAPTATION:** Wire this into `ward_compute` after calibration (`calibrate_geometry.py`). It fixes the Euclidean error but is still only Level 1. To reach Level 4, it needs path-history dependence.

#### `audit/benchmarks/benchmark_hutter_geometric.rs`
- **Regime:** Non-Euclidean Global (Level 1)
- **Status:** ⚠️ Stub / Benchmark
- **Evidence:** `NonEuclideanSpace` with global `curvature: f64` (positive = spherical, negative = hyperbolic). Distorts coordinates by a global curvature factor.
- **ADAPTATION:** This is a compression benchmark, not a pipeline component. Can serve as a test harness for global non-Euclidean distance functions, but does not implement local metrics.

#### `audit/benchmarks/benchmark_nspace_entropy.rs`
- **Regime:** Non-Euclidean Global (Level 1) — vector-space phase geometry
- **Status:** ⚠️ Stub / Benchmark
- **Evidence:** `NoiseVector` with `magnitude()`, `direction_entropy()`, and `combined_entropy()`. Treats n-space as a vector space with angle-based entropy.
- **ADAPTATION:** The `direction_entropy` formula is useful for measuring informatic torsion between trajectory segments. Can be extracted and used in the Level 4 plugin.

---

### 2.3 Riemannian / Metric Tensor

#### `core/lean/geoweird/GWLKernel.lean` — `Metric2D`
- **Regime:** Riemannian (Level 2)
- **Status:** 🔧 Implemented in Lean, not extracted to runtime
- **Evidence:** Defines `Metric2D { g_tt, g_tp, g_pp }`, `lineElement`, `metricFromCircumferences`, `Christoffel2D`, and `geodesicStep`.
- **Key insight:** This is a genuine 2D Riemannian metric with Christoffel symbols and geodesic integration.
- **ADAPTATION:** The FFI gap blocks direct use. However, the **formulas** can be ported to Python/Rust for the geometry plugin. The `geodesicStep` symplectic Euler integrator is exactly what's needed for trajectory propagation in n-local topology.

#### `core/lean/geoweird/Manifold.lean`
- **Regime:** Riemannian (Level 2) with topological classification
- **Status:** 🔧 Implemented in Lean
- **Evidence:** `Manifold` has `dimension`, `curvature`, `volume`, `metric : MetricTensor`, and `GeodesicPath`. `TopologicalType` adds sphere/hyperbolic/flat/torus/custom labels.
- **ADAPTATION:** Serves as the formal specification for what a manifold *is* in this system. The `MetricTensor` structure should inform the Python `GeometricBridgePlugin` refactor.

#### `5-Applications/tools-scripts/demo/gwl_earth_riemannian_conversion.py`
- **Regime:** Riemannian (Level 2)
- **Status:** ⚠️ Demo script
- **Evidence:** Converts Earth coordinates (lat/lon/alt) using oblate spheroid metrics similar to `metricFromCircumferences`.
- **ADAPTATION:** Reference implementation for `metricFromCircumferences`. Can be reused for any application that needs geodesic distances on an ellipsoid.

---

### 2.4 Cartan / Informatic Torsion

#### `docs/gwl/GWL_ROTATIONAL_VALUES_AND_TORSION_FORMALISM_V1.md`
- **Regime:** Cartan / Torsion (Level 3)
- **Status:** 📝 Documented Only
- **Evidence:** Defines π field as "informatic torsion" `T(π) = rotation_matrix(π × 22.5°)`. Torsion affects "how Δp is interpreted" and "how neighboring μ-seeds couple." Chirality (D/L) flips torsion sign.
- **Key insight:** Torsion is encoded in the μ-seed state itself, not computed from trajectory history.
- **ADAPTATION:** This is a **stateful torsion** model (encoded in data) rather than a **dynamical torsion** model (computed from path history). To reach true Level 4, we need both: π as seed-encoded torsion + trajectory curvature as dynamical torsion.

#### `docs/pipeline/NSPACE_COORDINATOR_SPEC.md` — Informatic Torsion Section
- **Regime:** Cartan / Torsion (Level 3)
- **Status:** 📝 Documented Only (but referenced by production code)
- **Evidence:** `T^k_ij = Γ^k_ij - Γ^k_ji ≠ 0`. "Torsion is sourced by spin density — the path history through the manifold." Stokes theorem: `∮ T^k_ij dS^ij = 0`.
- **Key insight:** This document **explicitly requires** trajectory-dependent torsion, but no code implements it.
- **ADAPTATION:** This is the **design target**. The evolved `geometry_plugin_v2.py` should implement this exact formula using trajectory history.

#### `data/germane/research/chat-soliton-nspace-path-trace-20260404.md`
- **Regime:** Cartan / Torsion (Level 3) → N-Local (Level 4) aspiration
- **Status:** 📝 Documented Only
- **Evidence:** Soliton map as "path trace in n-space that leads to replayable actions." STOP codons = topological changes (different vacuum). KdV soliton preserves shape under nonlinear interaction.
- **ADAPTATION:** The soliton map is the **narrative** for what Level 4 geometry should feel like: localized, stable, time-reversible paths. It doesn't provide executable formulas but sets the behavioral specification.

---

### 2.5 Topological / Discrete

#### `infra/access_control/topological_tape_machine.py`
- **Regime:** Topological / Discrete
- **Status:** 🔧 Implemented (reference implementation)
- **Evidence:** `InvariantSurvivalMask`, `InvariantVector`, braid formation, morphism survival, Warden two-stage validation. No metric; only adjacency/occupancy/path/trust bits.
- **ADAPTATION:** This operates at a **higher abstraction layer** than geometry. It doesn't need a metric — it needs the geometry layer to provide a faithful `ProjectionCollapse`. The TTM is the **consumer**, not the producer, of n-local geometry.

#### `tools/topological_encoder.py`
- **Regime:** Topological / Discrete
- **Status:** 🔧 Implemented
- **Evidence:** Encodes data into topological invariants (braids, knots, links).
- **ADAPTATION:** Independent module. Can be used to encode n-local trajectory histories as topological braids for the TTM layer.

#### `core/lean/geoweird/ConstraintGeometry.lean`
- **Regime:** Topological / Discrete + Riemannian hybrid
- **Status:** 🔧 Implemented in Lean
- **Evidence:** Extracts `ConstraintFeatures` from domain constraints: curvature, symmetry, compactness, fundamental group rank. Uses combinatorial constraint types (temporal, spatial, cyclic, hierarchical) to infer geometric properties.
- **ADAPTATION:** This is a **constraint-to-geometry translator**. It can be used to initialize the metric tensor for a new manifold sheet given a set of domain constraints.

#### `core/src/tsm_perpetual_manifold.v` (Verilog)
- **Regime:** Topological / Discrete (hardware state machine)
- **Status:** 🔧 Implemented in RTL
- **Evidence:** 128-bit `field_resonance`, 256 `memistor_weights`, thermal energy recycling. Opcodes: INGEST, TSM_XOR, TSM_XAND, RESONATE, BALANCE, FREEZE. No coordinates, no metric — purely field-combinatorial.
- **ADAPTATION:** This is the **hardware substrate**. The n-local geometry layer (software) must emit opcodes and state vectors that this module can consume. The Verilog does not need to understand Riemannian geometry; it needs well-formed field states.

---

### 2.6 N-Local / Trajectory-Dependent (The Target)

#### `docs/gwl/GWL_MANIFOLD_INTERSECTION_JOIN_AND_TOPOLOGICAL_ADDRESSING_V1.md`
- **Regime:** N-Local (Level 4)
- **Status:** 📝 Documented Only
- **Evidence:** Defines `p_N = (p_E, M_i, M_j, γ, σ, Σ_topo)`. Non-Euclidean position includes Euclidean coordinate, manifold memberships, transport/path class, seam/projection state, and topological relation class.
- **Key insight:** Same Euclidean coordinate can have multiple distinct addresses depending on path history and manifold context.
- **ADAPTATION:** This is the **addressing layer** of the Level 4 target. Any evolved geometry plugin must produce `p_N` addresses for routing decisions.

#### `docs/pipeline/NSPACE_COORDINATOR_SPEC.md` — Phase Discriminator
- **Regime:** N-Local (Level 4)
- **Status:** 📝 Documented Only
- **Evidence:** `phase(p) = Φ(κ(p), T^k_ij(p), ρ(p))`. Phase discriminator selects the UV seam cut based on local curvature, torsion orientation, and information density.
- **ADAPTATION:** This is the **operational definition** of the Level 4 geometry plugin. `GeometricBridgePlugin.transform()` should compute exactly these three quantities from trajectory history.

#### `infra/access_control/pipeline/unified_pipeline.py` — `TemporalBuffer`
- **Regime:** N-Local (Level 4) — **has the data, doesn't use it for geometry**
- **Status:** ✅ Production
- **Evidence:** Maintains `history: deque[CanonicalState]`, `prev_delta`, `prev_phi`, `prev2_phi`. Computes reliable derivatives and gamma.
- **ADAPTATION:** This buffer already stores the trajectory history needed for Level 4 torsion computation. The missing link is piping this history into the geometry plugin.

---

### 2.7 Physical / Standard Model Boundary (New Paradigm)

#### `0-Core-Formalism/lean/Semantics/Semantics/Physics/*.lean`
- **Regime:** Physical / Standard Model (observational boundary)
- **Status:** ✅ Implemented, compiles, verified
- **Evidence:** `ParticleKind`, `QuantityKind`, `Interaction`, `PhysicalPath`, `Measurement`. Proves conservation laws (charge, lepton number) for e⁻e⁺ annihilation.
- **ADAPTATION:** This is the **bottom boundary** of the entire stack. N-local geometry must respect the conservation laws encoded here. Any physical realization of the manifold (e.g. field states in `tsm_perpetual_manifold.v`) must be accountable to these invariants.

---

## 3. Conflict Matrix: Which Formats Are Compatible?

| Format | Compatible With | Conflicts With |
|---|---|---|
| `geometry_plugin_v2.py` (Euclidean) | `cache_sieve.py`, `TemporalBuffer` | `NSPACE_COORDINATOR_SPEC.md`, `GWL_MANIFOLD_INTERSECTION_JOIN` |
| `geometry_noneuclidean.py` (Level 1) | `geometry_plugin_v2.py` (replacement) | `NSPACE_COORDINATOR_SPEC.md` (still insufficient) |
| `GWLKernel.lean` (Level 2) | `Manifold.lean`, `ConstraintGeometry.lean` | `geometry_plugin_v2.py` (no metric tensor) |
| `GWL_ROTATIONAL_VALUES_AND_TORSION_FORMALISM` (Level 3) | `GWLKernel.lean`, `topological_tape_machine.py` | `geometry_plugin_v2.py` (no torsion) |
| `NSPACE_COORDINATOR_SPEC.md` (Level 4) | `soliton_map`, `TemporalBuffer`, `Physics/*.lean` | `geometry_plugin_v2.py` (wrong metric) |
| `tsm_perpetual_manifold.v` (Topological) | All layers above it (as consumer) | None (it's the substrate) |
| `Physics/*.lean` (Boundary) | All layers above it | Any claim that violates charge/baryon/lepton conservation |

---

## 4. The Adaptation Decision

### What must change:
1. **`geometry_plugin_v2.py`** — evolve from Euclidean (Level 0) to N-Local (Level 4).
2. **`cache_sieve.py`** — stop consuming raw manifold values; consume N-local geometric features.
3. **`unified_pipeline.py`** — wire `TemporalBuffer` history into the geometry plugin.

### What can be wired as-is:
1. **`geometry_noneuclidean.py`** — its log-PHI and logit functions become subroutines in the Level 4 plugin.
2. **`GWLKernel.lean`** — its metric tensor and geodesic step formulas are the source of truth; Python is an extraction shim against this spec.
3. **`topological_tape_machine.py`** — operates at a higher layer; unchanged interface.
4. **`tsm_perpetual_manifold.v`** — unchanged; the geometry layer feeds it, it doesn't compute geometry.
5. **`Physics/*.lean`** — unchanged; serves as the invariant boundary.

### What is documentation-only and needs code:
1. `NSPACE_COORDINATOR_SPEC.md` — the Phase Discriminator needs a Python/Rust implementation.
2. `GWL_MANIFOLD_INTERSECTION_JOIN_AND_TOPOLOGICAL_ADDRESSING_V1.md` — `p_N` addressing needs a Python addressing module.
3. `GWL_ROTATIONAL_VALUES_AND_TORSION_FORMALISM_V1.md` — π-field torsion needs to be integrated into trajectory curvature computation.

---

## 5. Recommended Implementation Sequence

**Phase 1 (Immediate):** Refactor `geometry_plugin_v2.py` to use `TemporalBuffer` trajectory history and compute:
- Local metric tensor `G(p)` from trajectory covariance
- Geodesic angle under `G(p)` (replacing Euclidean `angular_drift`)
- Informatic torsion `T(p)` from trajectory curvature (path-history derivative)
- Phase discriminator `Φ(κ, T, ρ)` (stub, to be hardened)

**Phase 2 (Short-term):** Update `cache_sieve.py` to consume the new geometric features, and verify against existing tests.

**Phase 3 (Medium-term):** Port the verified Python formulas to Rust (or extract from Lean once FFI is fixed) for performance-critical paths.

**Phase 4 (Ongoing):** Maintain `Physics/*.lean` as the invariant oracle; any new geometric claim must be checked against conservation laws.

---

**Status:** INVENTORY COMPLETE | DECISION FRAMEWORK ESTABLISHED
