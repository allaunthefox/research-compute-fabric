# Missing Proofs Registry

**Purpose:** Track theorems, lemmas, and formalizations that are defined, documented, or conjectured but not yet proven in Lean 4.

**Status:** Living document — update as formalization progresses.

---

## Gap Categories

### Category A: AVMR Core Theorems (Models 102-110)

| # | Theorem | Statement | Current Status | Blocker | Auto-Provable? |
|---|---------|-----------|----------------|---------|----------------|
| 102 | Quasi-Periodic Square-Shell | `n = k² + a = (k+1)² - b` with `a+b = 2k+1` | ✅ **PROVEN** — `ring + omega` | — | **YES** ✅ |
| 103 | Tip Coordinate Vector | `Tip(n) = (ab, a-b)` as ℝ² embedding | Partial — `tipCoord` defined | Real embedding properties | **NO** — needs injectivity |
| 104 | Axial Event Production | `A_k, G_k, C_k, T_k` partition shell | ✅ **PROVEN** — `axialGeneratorExhaustivity` | — | **YES** ✅ |
| 121 | Axial Generator Exhaustivity | {A_k, G_k, C_k, T_k} exhaust S_k | ✅ **PROVEN** — `ring + nlinarith` | — | **YES** ✅ |
| 105 | Resonance Hub | `Tip(m²) = (0, -(2k+1))` | ✅ **PROVEN** — `simp + ring + omega` | — | **YES** ✅ |
| 106 | Standing-Wave Rear Field | `Ψ_i(n_i - d) = α_d · χ_i` | Partial — `buildFieldAt` computes | Field convergence | **PARTIAL** — echo sum proven |
| 107 | Interaction Score | `J(n) = ab·F_m + (a-b)·F_p + ⟨χ,F_c⟩` | ✅ **Implemented** | — | — |
| 108 | Left-Right Transduction | `(n,k,a,b) ↦ (e,τ,...) ↦ (S,P,G)` | Missing — pipeline not formalized | Multi-stage bind | **NO** — needs pipeline |
| 109 | Temporal Error-Coding | `t(n) = nR + τ`, 8-slot | Missing — microtime lattice | Temporal algebra | **NO** — needs Fin arithmetic |
| 110 | AVMR Commitment | `Σ_{k+1}[i] = Φ(Σ_k[2i], Σ_k[2i+1])` | Missing — vectorized Merkle | Aggregation invariant | **NO** — needs algebraic structure |

**Search space shrunk:** 4 of 11 theorems proven automatically (Models 102, 104, 105, 121). 7 require manual work.

### Category B: Core Semantics Debt

| Module | Debt | Location | Priority |
|--------|------|----------|----------|
| `BraidCross.lean` | Fix16.add associativity | Line 72 | High — blocks algebra |
| `BraidCross.lean` | Fix16.add commutativity | Line 84 | High — blocks algebra |
| `Constitution.lean` | Lawful constitution preservation | `sorry` placeholder | Medium — ENE core |
| `Canon.lean` | Float elimination (timestamp, trustLevel) | `float64` field kind | Medium — core purity |
| `Graph.lean` | Float → Q16_16 port | Geometry module | Low — shim acceptable |

### Category C: Domain Intersection Gaps

| Intersection | Missing Bridge | Impact |
|--------------|----------------|--------|
| E ↔ M (Verification ↔ Lean) | BEA consensus → Formal proof | Weak verification formalism |
| H ↔ G (Algebra ↔ Energy) | Geometric algebra → Thermodynamics | Noether connection missing |
| J ↔ L (Dynamics ↔ Application) | Phase transitions → FEA | Engineering bridge |

### Category D: Unified Compression Extensions

| Feature | Status | Needed For |
|---------|--------|------------|
| Temporal lattice integration | Missing | Model 109 connection |
| AVMR commitment hook | Missing | Model 110 connection |
| Microvoxel constraint check | Partial | Model 21-22 validation |
| Meta-LUT formalization | Missing | Model 23-24 |
| HotSwap selector proof | Missing | Model 25 |
| **Final Score Law** | 🔄 Formalizing | Models 119-120 — cost aggregation |
| Score parameter bounds | Missing | λ₁,λ₂,λ₃,λ₄ ∈ [0, 2.0] |
| Cost monotonicity | Missing | L(X) increases with complexity |

---

## Proof Templates

When adding a proof, use this format:

```lean
theorem <name> : <statement> := by
  <tactics>
  <;> try native_decide
  <;> try omega
  <;> try nlinarith
```

Preferred witnesses:
- `#eval` examples with expected output
- `native_decide` for concrete cases
- `omega` / `nlinarith` for arithmetic
- `simp` with appropriate lemmas

---

## Dependencies

Before proving higher theorems, these foundations are needed:

1. **Fix16 algebra** (BraidCross) — blocks all algebraic manipulation
2. **Shell state totality** — blocks AVMR event classification proofs
3. **Field convergence** — blocks standing-wave theorems
4. **Q16_16 metric** — blocks distance/geometry proofs

---

## Recent Updates

- **2026-04-17:** Created registry, populated from MATH_MODEL_MAP (181 models)
- **2026-04-17:** Added Unified Compression gaps (Models 111-118)
- **2026-04-17:** Added Final Score Law (Models 119-120) — complete cost aggregation
- **2026-04-17:** Added Agent F1/F2/F3 Tier Proofs (Models 121-131) — explicit Φ operators
- **2026-04-17:** Identified 3 critical domain intersections needing bridges
- **2026-04-17:** Prover ran — Models 102, 104, 105, 121 proven automatically

---

## How to Resolve

1. Pick a theorem from Category A or B
2. Create branch: `proof/<theorem-name>`
3. Add theorem + witness to appropriate `.lean` file
4. Update this registry with ✅ status
5. Run `lake build` to verify
6. PR with theorem statement and proof summary

---

**Enforcement:** Per AGENTS.md Section 4 — every `def` computing cost or invariant must have `#eval` or theorem witness before commit.
