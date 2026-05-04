# Bind Migration Guide: Reengineering the Cells

**Date:** 2026-04-14  
**Status:** ACTIVE MIGRATION  
**Truth Seal:** `[ SSS-ENE-TRUTH-2026-04-14 ]`

---

## 1. The New Anatomy

Instead of 140+ isolated equations across 12 layers, the stack now has:

1. **One primitive:** `bind(left, right, metric_kind, history)`
2. **One formal spec:** `Semantics/Bind.lean`
3. **One runtime engine:** `infra/access_control/bind_engine.py`
4. **One invariant boundary:** `Semantics/Physics/*.lean`

Every existing module is being reengineered as a **cell type** — a differentiated instance of the same primitive.

---

## 2. What Exists Now

### 2.1 Formal Layer (Lean 4)

| File | Role | Status |
|---|---|---|
| `0-Core-Formalism/lean/Semantics/Semantics/Bind.lean` | Root primitive `Bind A B` | ✅ Compiles |
| `0-Core-Formalism/lean/Semantics/Semantics/Physics/BindPhysics.lean` | Proof-of-pattern: physical interactions as `bind` instances | ✅ Compiles |
| `0-Core-Formalism/lean/Semantics/Semantics.lean` | Updated to `version := "2.0.0-Cambrian-Bind"` | ✅ Compiles |

**Build verification:**
```bash
cd 0-Core-Formalism/lean/Semantics && lake build
# Build completed successfully (24 jobs)
```

### 2.2 Runtime Layer (Python)

| File | Role | Status |
|---|---|---|
| `infra/access_control/bind_engine.py` | Universal `BindEngine` with n-local metric computation | ✅ Runs |

**Runtime verification:**
```bash
python3 infra/access_control/bind_engine.py
# Physical bind: lawful=True, cost=0.000000
# Last geometric bind: metric.tensor=geometric, torsion=0.047790, history_len=4
```

### 2.3 Registry (TSV)

| File | Change | Status |
|---|---|---|
| `docs/MATH_MODEL_MAP.tsv` | Added `Bind_Class` column; every row classified | ✅ Updated |

---

## 3. Migration Map: Old File → New Cell

### 3.1 Production Pipeline (Priority 1)

| Old File | Old Role | New Cell | Action |
|---|---|---|---|
| `infra/access_control/geometry/geometry_plugin_v2.py` | Euclidean geometric preprocessor | `geometric_bind` via `BindEngine` | **Replace** with `bind_engine.geometric_bind()` |
| `tools/cache_sieve.py` | Raw manifold thresholding | `control_bind` via `BindEngine` | **Refactor** to consume `BindResult.cost` and `BindResult.metric.torsion` |
| `infra/access_control/pipeline/unified_pipeline.py` | Orchestrator with `TemporalBuffer` | `BindEngine` user | **Wire** `TemporalBuffer.history` into `BindEngine.bind(..., use_history=True)` |
| `tools/cache_sieve_exploration.py` | Relation sieve exploration | `control_bind` | **Port** 5-symbol sieve to use `bind()` with custom cost function |

### 3.2 Lean Formalisms (Priority 2)

| Old File | Old Role | New Cell | Action |
|---|---|---|---|
| `core/lean/geoweird/GWLKernel.lean` | Riemannian metric + geodesic integration | `geometric_bind` formal spec | **Port** `Metric2D`, `Christoffel2D`, `geodesicStep` into `Semantics/Bind.lean` metric instances |
| `core/lean/geoweird/WaveprobeKernel.lean` | Risk / heat / hysteresis control | `control_bind` formal spec | **Port** risk function and LUT policy into `Semantics/Bind.lean` control instances |
| `core/lean/geoweird/EmergenceSystem.lean` | Phase transition detection | `control_bind` | **Port** diminishing-ratio trigger into `Bind` cost function |
| `core/lean/geoweird/ConstraintGeometry.lean` | Constraint-to-curvature translator | `geometric_bind` | **Port** as metric initialization helper |

### 3.3 Thermodynamic & Stress Models (Priority 3)

| Old File | Old Role | New Cell | Action |
|---|---|---|---|
| `core/gwl-vm/src/thermo/entropy_engine.rs` | Shannon / Kolmogorov entropy | `informational_bind` | **Wrap** with `bind_engine.informational_bind()` or Rust equivalent |
| `core/gwl-vm/src/thermo/informatic_stress.rs` | Hardware stress / RUL / SEU | `thermodynamic_bind` | **Wrap** with `bind_engine.thermodynamic_bind()` |
| `core/gwl-vm/src/thermo/qcl_energy_model.rs` | QCL photon physics | `physical_bind` | **Wrap** with `bind_engine.physical_bind()` |
| `core/gwl-vm/src/thermo/bea_thermo_bridge.rs` | BEA consensus bridge | `thermodynamic_bind` | **Wrap** |

### 3.4 Compression & Signal (Priority 4)

| Old File | Old Role | New Cell | Action |
|---|---|---|---|
| `tools/geometry_bind.py` | PCA/HarfBuzz bind score | `informational_bind` | **Replace** with `bind_engine.informational_bind()` using KL cost on feature distributions |
| `core/intrinsic/formalisms/ene_mi_signal.py` | MI prediction / surprise | `informational_bind` | **Replace** |
| `scripts/soliton_factory.py` | PHI proximity, foam score | `geometric_bind` | **Replace** `phi_prox` with `bind_engine.bind(..., metric_kind="geometric")` |
| `tools/geometry_noneuclidean.py` | Log-PHI / logit / writhe | `geometric_bind` | **Absorb** into `bind_engine.py` as subroutines |

### 3.5 Verilog / Hardware (No Change Needed)

| Old File | Old Role | New Cell | Action |
|---|---|---|---|
| `core/src/tsm_perpetual_manifold.v` | Hardware substrate | Consumer of `bind` output | **None** — it receives field states, doesn't compute geometry |

---

## 4. Step-by-Step Migration Sequence

### Phase 1: Kill the Euclidean Assumption (This Week)

**Goal:** Replace `geometry_plugin_v2.py` with `bind_engine.py` in the live pipeline.

1. **In `infra/access_control/pipeline/unified_pipeline.py`:**
   ```python
   from bind_engine import BindEngine, geometric_bind

   self.bind_engine = BindEngine()
   ```

2. **Replace `GeometricBridgePlugin.transform()` calls:**
   ```python
   # OLD
   geom = self._geometry_plugin.transform(manifold)

   # NEW
   result = geometric_bind(
       state_a={"state_vector": prev_state},
       state_b={"state_vector": current_state},
       engine=self.bind_engine,
   )
   cost = result.cost
   torsion = result.metric.torsion
   ```

3. **Verify:** Run `test_compliance_fixes.py` and confirm no regression.

### Phase 2: Reorganize `cache_sieve.py` (Next Week)

**Goal:** Stop using raw manifold proxies; use bind-derived geometric features.

1. **Replace input mapping:**
   ```python
   # OLD
   inputs = [
       int(phi_corr * 255) & 0xFF,
       int(sum(tau_samples[:32]) * 10) & 0xFF,
       ...
   ]

   # NEW
   bind_result = self.bind_engine.bind(
       left=manifold_prev,
       right=manifold_curr,
       metric_kind="geometric",
       use_history=True,
   )
   inputs = encode_bind_features(bind_result)
   ```

2. **Add custom cost function for sieve:**
   ```python
   def sieve_cost(left, right, metric):
       return _geodesic_cost(left, right, metric) + metric.torsion * 10.0
   ```

### Phase 3: Port Lean Geometric Formalisms (Ongoing)

**Goal:** Make `GWLKernel.lean` a formal instance of `Bind`.

1. **In `Semantics/Bind.lean`, add metric constructors:**
   ```lean
   def Metric.riemannian (g_tt g_tp g_pp : Float) : Metric := { ... }
   def Metric.fromChristoffel (Γ : Christoffel2D) : Metric := { ... }
   ```

2. **In `Semantics/Geometry/BindGeodesic.lean`:**
   ```lean
   def geodesicBind (x v : Rat × Rat) (Γ : Christoffel2D) : Bind (Rat×Rat) (Rat×Rat) :=
     bind (x, v) (geodesicStep (x, v) Γ dt) metric geodesicCost invariant invariant
   ```

### Phase 4: Collapse Rust Thermodynamics (After Python Stabilizes)

**Goal:** Wrap Rust thermo modules with a thin `bind` interface.

1. Add `bind_thermodynamic(state, equilibrium)` to `core/gwl-vm/src/thermo/mod.rs`
2. Ensure it calls the same entropy / stress / QCL functions, but framed as `bind`.

---

## 5. What to Delete

The following concepts are **deprecated** by the collapse:

| Deprecated Concept | Reason |
|---|---|
| `LAYER_A` through `LAYER_L` | Replaced by 5 `Bind_Class` instances |
| `phi_prox = max(0, 1 - abs(r - PHI)/PHI)` | Replaced by `geometric_bind` with log-PHI metric |
| `GeometricBridgePlugin` (Euclidean version) | Replaced by `BindEngine` with n-local metric |
| `CacheSieve` raw input scaling | Replaced by `bind`-derived encoded features |
| `CHATGPT_EXTRACTION_GAP_ANALYSIS` action items for isolated patches | Superseded by unified `bind` engine plan |

---

## 6. Verification Checklist

- [x] Lean `Bind.lean` compiles
- [x] Python `bind_engine.py` runs
- [x] `MATH_MODEL_MAP.tsv` updated with `Bind_Class`
- [ ] `geometry_plugin_v2.py` replaced by `bind_engine` in pipeline
- [ ] `cache_sieve.py` refactored to use `BindResult`
- [ ] `test_compliance_fixes.py` passes after migration
- [ ] `GWLKernel.lean` formulas ported to `Bind` metric instances
- [ ] Rust thermo modules wrapped with `bind` interface

---

## 7. One-Liner Summary

> **There is no stack. There is `bind`. We are reengineering every cell to express itself through that one primitive.**
