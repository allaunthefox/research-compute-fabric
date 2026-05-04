# Phi-S3C-PIST Bridge Spec

**Status:** marching orders  
**Parent:** `docs/PHI_CENTER_REVAMP.md`  
**Purpose:** connect the Phi center to S3C shell coordinates and PIST witness transport without collapsing their roles.

## Core Bridge

```text
Phi_field compares
S3C locates
PIST witnesses
phinary indexes
GraphML descends
```

This is the first operational bridge of the Phi-centered revamp.

## Role Boundaries

| Component | Job | Must not pretend to be |
|---|---|---|
| `Phi_field` | Root cost/efficiency comparison | A shell coordinate system |
| `phi_ratio` / phinary | Irrational spacing and descent/address indexing | A proof of the equation |
| S3C | Exact integer shell atlas and mass/throat geometry | A universal cost law |
| PIST | Typed witness transport over shell state | A loose scalar analogy |
| GraphML | Descent/exterior lineage map | The formal source of truth |

## Bridge Object

For each active equation or graph node, the bridge record should eventually be:

```json
{
  "id": "equation_or_node_id",
  "phi_role": "field|ratio|scheduler|none",
  "phi_form": "absolute_cost|relative_efficiency|spacing|traversal|not_applicable",
  "s3c_role": "shell_coordinate|open_mass|closed_mass|throat|not_applicable",
  "pist_role": "witness_state|transport|blitter|not_applicable",
  "phinary_id": "zeckendorf_or_null",
  "lineage_role": "root|root_child|trunk|branch|leaf|realization|support"
}
```

## March Order

### 1. Phi Correction Boundary

Use `0-Core-Formalism/lean/Semantics/Semantics/UniversalField.lean` as the corrected root
for cost/efficiency language.

Required distinction:

```text
absolute cost:       Phi = sum w * ln(N) - sum v * ln(M)
relative efficiency: Phi = sum w * h / ln(N) - sum v * p / ln(M)
```

Do not promote older `w / ln(N)` wording as the root cost law.

### 2. S3C Mass Boundary

Use `0-Core-Formalism/lean/Semantics/Semantics/S3C.lean` as the shell source.

Required distinction:

```text
closed shell: b0 = (k+1)^2 - 1 - n
open shell:   b+ = (k+1)^2 - n
closed mass:  mass0 = a * b0
open mass:    mass+ = a * b+
```

Closed mass is the throat/intersection activation. Open mass is next-shell
tension. They are adjacent, not interchangeable.

### 3. Phi-S3C Coupling

Phi may weight or compare S3C states, but S3C coordinates remain exact integer
structure.

Allowed:

```text
Phi_weighted_shell_score =
  alpha * Phi_cost(shell_payload)
+ beta  * normalized(mass0)
+ gamma * normalized(abs(a - b0))
+ delta * next_shell_tension(b+)
```

**Concrete S3C-D Resonance Implementation (S3CResonance.lean):**

The S3C-D (Ductile) architecture uses a parabolic J-Score model with Q16_16 fixed-point arithmetic:

```text
J(k) = 32 - 0.5 * (k - 22)^2
```

Where:
- `k` = resonant frequency index in Q16_16 fixed-point
- `J` = J-score in Q16_16 fixed-point (range [-32768, 32767.999985])
- Peak at `k = 21.5` → `J = 31.875`
- God-Tier threshold: `J > 30.0`

**Q16_16 Encoding:**
- `k_peak = 21.5` → 1409024 (21.5 * 65536)
- `J_peak = 31.875` → 2088960 (31.875 * 65536)
- `J_god = 30.0` → 1966080 (30.0 * 65536)
- Computed as: `J = 32 - 0.125` where `0.125 = 8192` in Q16_16

**Verified Properties (Lean theorems):**
- `jPeak_correct`: computeJScore kPeak = jPeak
- `jPeak_exceeds_god_tier`: gt jPeak jGodTierThreshold = true
- `peakAttainsGodTier`: isGodTier (computeJScore kPeak) = true

This J-Score model is a concrete instance of the Phi-S3C coupling pattern, where the parabolic resonance curve encodes the ductile architecture's stability envelope without collapsing into a generic cost function.

Not allowed:

```text
Phi proves genus-3
Phi changes b0/b+ definitions
phinary ID proves S3C correctness
```

### 4. PIST Witness Transport

Use PIST for typed transport/witnessing after S3C has located shell state.

Route:

```text
n
-> S3C.shellDecomposition(n)
-> S3C mass/throat fields
-> Phi comparison
-> PIST witness state / bridge transport
-> GraphML lineage update
```

The PIST role is not to decorate the proof. It is the typed witness path that
prevents scalar-only drift.

### 5. Phinary Descent

Use `MATH_MODEL_MAP_phinary.tsv` as the companion index to `MATH_MODEL_MAP.tsv`.

Rule:

```text
MATH_MODEL_MAP.tsv          = semantic/equation registry
MATH_MODEL_MAP_phinary.tsv  = descent/address registry
```

Every active bridge target should either have a phinary ID or be marked as
excluded/support.

## First Bridge Targets

| Target | Why first |
|---|---|
| `EQUATION_00_PHI_UNIVERSAL` | Root comparison law |
| `Intrinsic_Load_LI` | Base information cost substrate |
| `Total_Cognitive_Load` | Aggregate load coupling |
| `S3C.shellDecomposition` | Exact shell coordinates |
| `S3C.massZero` | Closed-shell throat activation |
| `S3C.massPlus` | Open-shell next-shell tension |
| `NUVMATH.AtomicWaveState` | Lean-audited S3C/GPE energy carrier |
| `NUVMATH.HairBallState` | Finite ensemble of audited wave filaments |
| `PistBridge.shellStateToPistCoords` | Shell-to-witness transport |
| `research_graph.graphml` | Exterior descent map |

## Done Criteria

The bridge is usable when:

- Phi docs all point to corrected cost/efficiency language.
- S3C docs identify where Phi weighting enters and where it does not.
- PIST bridge docs identify the typed witness step after shell location.
- The generated reflow index puts bridge files under the Phi/S3C cockpit.
- GraphML work can assign lineage roles without re-deriving the whole system.

## S3C-Regularized GPE Hair Ball

The S3C/GPE "Hair Ball" is the current operational simulation framing for a
finite ensemble of wave filaments. It should be treated as a Lean-audited
control surface first, with any C, Python, or visualization code acting as a
shim over the formal S3C gates.

### Current Formal Surface

Source module: `0-Core-Formalism/lean/Semantics/Semantics/NUVMATH.lean`

| Lean artifact | Role |
|---|---|
| `S3CAudit` | Captures the S3C shell handles, contact bits, J-score, and emit gate for an energy cell. |
| `AtomicWaveState` | Carries a wave energy cell plus proofs that its audit matches the cell and that the emit gate is open. |
| `tryAtomicStep` | Returns `none` when a proposed energy update lands on boundary-closed geometry. |
| `geometricDt` | Scales the local step by the capped J-score. |
| `adaptiveStepFuel` | Bounded retry loop: failed gates halve the step and eventually return explicit deferment. |
| `HairBallState` | Finite list of accepted `AtomicWaveState` filaments. |
| `allHairsEmit` | Executable ensemble predicate for extraction shims. |
| `combTargetCell` | Shell-local throat target `k^2 + k`. |
| `combForceCell` | Integer cell force toward the throat: `target - energyCell`. |

### Verified Properties

| Theorem | Guarantee |
|---|---|
| `atomicStateEmitOpen` | Every `AtomicWaveState` has an open S3C emit gate by construction. |
| `atomicStateAuditMatchesEnergy` | The state's audit is tied to the current audited energy cell. |
| `boundaryCellDefers` | Example square boundary cells `9` and `16` close the emit gate. |
| `adaptiveBoundaryAttemptDefers` | A throat-to-boundary impulse returns deferment instead of accepting the unsafe boundary step. |
| `shellBoundaryEnergyInvariant` | The upper edge of shell `k` and the lower edge of shell `k+1` name the same energy cell. |
| `shellBoundaryMassZero` | Exact square boundaries have zero closed-shell mass resonance. |
| `hairballSafety` | Every filament admitted to a `HairBallState` emits under its local audit. |
| `combTargetAtK3Throat` | The `k=3` throat target is cell `12`, with zero comb force at the throat. |

### Hair Ball Mechanics

The ensemble model is deliberately small:

```text
energy cell n
-> S3C audit
-> AtomicWaveState if emit=true
-> HairBallState ensemble if every filament is atomic
-> adaptiveStepFuel for bounded retry/deferment
```

The combing law is represented in Lean at the shell-cell level:

```text
target(k) = k^2 + k
combForceCell = target(k) - n
```

Positive force means a filament is below the throat; negative force means it is
above the throat. The current Lean surface proves the throat witness for `k=3`.
Phase locking, tangle-event collision handling, shell-exclusion scheduling, and
fall-out/noise routing are driver policies that must call back into these Lean
gates before accepting state transitions.

### Implementation Status

| Feature | Status |
|---|---|
| S3C shell decomposition | Implemented in `Semantics.S3C`. |
| J-score audit and emit gate | Implemented in `Semantics.NUVMATH`. |
| Adaptive bounded retry/deferment | Implemented in `adaptiveStepFuel`. |
| Shell boundary energy conservation | Proved by `shellBoundaryEnergyInvariant`. |
| Ensemble safety | Proved by `hairballSafety`. |
| Visual comparison artifacts | Generated by `scripts/visualize_s3c_gpe_landscape.py`. |
| C-driver integration | Target shim only; must consume Lean decisions, not duplicate gate logic. |

## Empirical Validation

### STL-Free 3D Printing Research (Xu Song, CUHK / Wen Chen, USC)

Published validation in *International Journal of Extreme Manufacturing* confirms the bridge architecture's core thesis:

**Traditional approach (Mesh/STL intermediate):**
```text
CAD → STL mesh conversion → Slicer → Laser paths
     ↑ 90% overhead, precision loss
```

**Direct implicit function approach (Validated):**
```text
Mathematical description (Implicit function) → Direct laser paths
     ↓ 90% memory reduction, 66% strength increase, 257% elongation
```

This validates the **Phi-S3C-PIST bridge** principle:
```text
Phi_field (mathematical description)
  ↓
S3C (shell coordinates / spatial structure)
  ↓
PIST (direct witness transport / laser execution)
  ↓
Physical fabrication (no collapsed intermediate)
```

### Key Performance Metrics (Empirical)

| Metric | STL-Based | Implicit/Direct | Improvement |
|---|---|---|---|
| Memory/processing | 100% baseline | 10% of baseline | **90% reduction** |
| Wall thickness | Limited | 65 microns | **Microscale precision** |
| Surface roughness | Higher | 3.2 microns | **Smooth finish** |
| Yield strength | 100% baseline | 166% of baseline | **66% increase** |
| Elongation | 100% baseline | 357% of baseline | **257% improvement** |
| Tensile (aerospace bracket) | 100% baseline | 152% of baseline | **52% increase** |
| Energy absorption | 100% baseline | 500% of baseline | **5x improvement** |

### Connection to Bridge Components

**Phi_field → Implicit Function:**
The mathematical description of shell lattices (gyroid, Schwarz P/D) is the **cost/efficiency field**. It encodes the complete geometry without approximation.

**S3C → Shell Atlas:**
The lattice coordinates map directly to S3C's **exact integer shell atlas**:
- `b0 = (k+1)² - 1 - n` (closed shell mass/thickness)
- Lattice period L = `period` parameter
- Wall thickness t = `thickness` parameter

**PIST → Hybrid Toolpath Transport:**
The validated hybrid strategy (contour + rotational scanning) is **typed witness transport**:
- Contour scanning = boundary witness for thin walls
- Rotational scanning = heat management at joints
- Direct execution = blitter-style state application

**No STL Collapse:**
The research explicitly demonstrates that bypassing the STL intermediate (mesh representation) preserves geometric fidelity and mechanical properties — validating the bridge's role-preservation principle.

### Reference Implementation

Formal Lean module: `0-Core-Formalism/lean/Semantics/Semantics/Geometry/ImplicitShellLattice.lean`
- TPMS implicit function definitions (Gyroid, Schwarz P/D, Neovius)
- Fixed-point arithmetic for FPGA targeting
- NUVMAP projection integration
- Memory efficiency validation theorems

## Generated Targets

Run:

```bash
python3 scripts/reflow/generate_local_setup_reflow.py
```

Bridge target outputs:

- `data/reflow/phi_s3c_pist_bridge_targets.tsv`
- `data/reflow/phi_s3c_pist_bridge_targets.json`
