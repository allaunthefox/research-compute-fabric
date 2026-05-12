# DESI Menger Probe Result

**Authored:** 2026-05-11
**Status:** Distilled synthesis — working scaffold, not a design claim
**Epistemic framework:** Tags from `6-Documentation/docs/BRAIN_AS_MANIFOLD.md`

---

## Epistemic Tag Legend

| Tag | Meaning |
|---|---|
| **PRIOR ART DATA** | Peer-reviewed measurement. Applies only to what those papers actually measured. |
| **PROJECT DATA** | Directly computed or observed from this project's code/data. |
| **INFERENCE** | Conclusion drawn from data. Followed by what data it rests on and what would break it. |
| **SPECULATIVE** | Plausible mechanism with no empirical grounding. Do not cite. |
| **WILD SPECULATION** | Interesting but no grounding whatsoever. Filed for development. |

---

## 1. What Was Probed

**PROJECT DATA.** The project's Menger void QR state machine (MATH_MODEL_MAP formalism `0.4.9`) is a computational architecture built on the 3D Menger sponge fractal geometry embedded in the project's 16D manifold.

### The lattice

The project's 16D packet vector is:

```
V₁₆(k) = q_void(k) ⊕ q_orbit(k) ⊕ q_braid(k) ⊕ η_observer(k)
```

The `q_void` block `(horizon_id, void_depth, area_class, skip_mass_class)` is the **Menger void component**. It carries the 3D Menger sponge geometry as a subspace of the full manifold.

The Lean-specified lattice (`MengerSpongeFractalAddressing.lean`) defines:

| Parameter | Value | Source |
|---|---|---|
| Hausdorff dimension d_H | ln(20)/ln(3) ≈ 2.7268 (Q16_16: `⟨17910⟩`) | `MengerSpongeFractalAddressing.lean` §0 |
| Addressing rule | `address(x,y,z) = mengerHash(x,y,z) ⊕ fractalOffset` | Lean spec §1 |
| Occupancy formula | `\|P_occ\| = ρ_occ · N^{d_H}` | Lean spec §2 |
| Active positions (N=64, ρ_occ=1) | ~84,000 of 262,144 (68% reduction) | Python shim computation |
| Void count at iteration n | `n_void = 20^n` (each iteration removes 20 of 27 cubes) | Fractal definition |

### The QR state machine equations

From the swarm request (`shared-data/data/swarm_requests/swarm_menger_void_qr_state_machine.json`, 2026-04-23):

```
V_void      = {v_i | v_i ∈ MS_removed}          (void set: removed positions)
S_state     = QR_encode(V_void, n_iter)           (void pattern → state encoding)
δ_transition = QR_decode(S_state, position)        (state → transition rule)
Φ_QR        = Σ_i v_i · 2^{-i}                   (state capacity)
τ_QR        = log₂(n_void) · log₂(d_H)            (transition time scaling)
```

### What the scripts actually ran

**PROJECT DATA.** Three artifacts exist:

1. `ask_swarm_menger_void_qr_state_machine.py` — generates a structured JSON query packet; saves it to `shared-data/data/swarm_requests/`. **Does not call any external service.** This is a query formulation tool, not an execution tool.

2. `execute_swarm_menger_void_qr_state_machine.py` — generates a synthetic swarm response **inline in Python** (the `generate_swarm_response` function produces a hardcoded dict). **No external LLM, no network call, no real swarm.** The "response" (confidence 0.87, agreement 0.84 across 6 participants) is a self-contained template.

3. `menger_sponge_fractal_addressing.py` — Python shim implementing the Lean-specified functions: `mengerHash`, `fractalOffset`, `mengerAddress`, `fractalOccupancy`, `mengerBind`. Contains real arithmetic. The `mengerBind` function executes the addressing pipeline.

**Honesty note:** The "swarm" is simulated. No actual distributed agents participated. The response document is the project's own self-assessment of the formalism, not an independent evaluation.

---

## 2. DESI Observational Result (Prior Art Context)

**PRIOR ART DATA.** The following is the real-world observational context that motivated calling this probe "DESI-relevant."

### DESI DR1 2024 — BAO measurement

**Citation:** DESI Collaboration, *DESI 2024 VI: Cosmological Constraints from the Measurements of Baryon Acoustic Oscillations* (arXiv:2404.03002, 2024). See also arXiv:2404.03000 (Overview), 2404.03001 (galaxy samples).

**What DESI measured:**
- Baryon Acoustic Oscillation (BAO) standard ruler across 6 galaxy tracers spanning redshifts 0.1 < z < 4.2 (including BGS, LRG, ELG, QSO, Ly-α forest)
- The BAO scale D_H/r_d and D_M/r_d at multiple redshifts, where r_d ≈ 147 Mpc is the sound horizon at drag epoch

**Key tension with ΛCDM:**
- When combined with CMB (Planck 2018) + SNIa, DESI DR1 finds the dark energy equation of state:
  ```
  w₀ = -0.827 ± 0.063   (vs. ΛCDM prediction w₀ = -1)
  w_a = -0.75 ± 0.29    (vs. ΛCDM prediction w_a = 0)
  ```
- The combination w₀ > -1, w_a < 0 — called "thawing quintessence" — deviates from ΛCDM at ~2.5–3σ significance
- If confirmed, this means dark energy is NOT a cosmological constant: it was stronger in the past and is evolving toward -1

**What cosmic voids have to do with DESI:**
- DESI measures large-scale structure via galaxy clustering. Cosmic voids (underdense regions ~10–100 Mpc scale) are a complementary probe
- Void statistics (void size function, void-galaxy cross-correlation, Alcock-Paczyński test in voids) are known to be sensitive to w₀w_a cosmology
- Ongoing analyses use DESI DR1 void catalogues to constrain dark energy independently of galaxy 2-point functions

---

## 3. Manifold Connection

**INFERENCE / SPECULATIVE.** This section draws an analogy between the project's Menger void geometry and cosmic void statistics. The connection is structural/mathematical, not observational.

### Scale mismatch (critical caveat first)

**The project's Menger sponge operates at a computational abstraction level — it is a state-space topology for a 16D information manifold, not a model of physical spacetime.** The void positions are lattice coordinates in an N=64 discrete grid; they have no assigned physical length scale. Cosmic voids are objects of 10–100 Mpc physical scale governed by gravitational dynamics in an expanding universe.

These two "void" concepts share a name and a fractal/hierarchical structure but are **not the same thing.** Any connection is analogical.

### Structural parallel: void statistics

**SPECULATIVE.** Both the Menger sponge and the cosmic web void hierarchy share a common property: **self-similar void nesting**. In both cases:

- Voids are the "removed" or "underdense" regions left over after a recursive selection process
- The remaining (occupied) structure has a Hausdorff dimension strictly less than 3
- The void-size distribution follows a power law controlled by the fractal dimension

In the project:
```
n_void at iteration n = 20^n            (Menger: 20 voids removed per 27 cubes)
d_H = ln(20)/ln(3) ≈ 2.727             (Hausdorff dimension of solid remainder)
active positions ≈ ρ_occ · N^{2.727}   (for N=64: ~84k of 262k)
```

In large-scale structure:
```
Cosmic void number function ~ V^{-α}    (power-law void size distribution)
Matter power spectrum has fractal correlation dimension D₂ ≈ 1.7–2.2 at small scales
Void hierarchy: supervoids > voids > voidlets (self-similar nesting)
```

The Menger d_H ≈ 2.727 is **higher** than the matter correlation dimension observed in the cosmic web (~1.7–2.2 at sub-100 Mpc scales), which suggests the Menger geometry models a **denser** fractal than the actual cosmic web. This is a structural mismatch if one were to claim direct correspondence.

### Dark energy connection (torsional cosmology thread)

**SPECULATIVE.** The project's `torsional_cosmology_spin.md` (in `3-Mathematical-Models/`) makes an independent prediction about dark energy:

```
dw/da = +2/a · (θ_obs/θ_max) · (1 - θ_obs/θ_max)   [torsional cosmology]
```

This predicts w evolves **above** -1 at late times — qualitatively consistent with the DESI DR1 tension (w₀ ≈ -0.83 > -1). **However:**
- This prediction is from a completely separate theoretical thread (torsional cosmology)
- It is not derived from the Menger void geometry
- The agreement with DESI is a qualitative directional match, not a quantitative prediction
- The torsional model also admits w ≈ -1 + ε barely distinguishable from ΛCDM

### The 16D manifold q_void block and void statistics

**WILD SPECULATION.** If the q_void block `(horizon_id, void_depth, area_class, skip_mass_class)` is interpreted as parametrizing cosmological voids:
- `void_depth` → underdensity δ_v < 0
- `area_class` → void radius bin
- `skip_mass_class` → wall galaxy mass threshold

…then the Menger fractal addressing could in principle provide a **compressed coordinate system** for void catalogues, exploiting the fractal void hierarchy to reduce catalogue storage from O(N³) to O(N^{2.727}). For N=64 redshift-position cells, this is a 68% storage reduction.

**This is speculative**. No void catalogue has been run through this addressing scheme. The reduction ratio is a property of the Menger sponge abstraction, not a tested property of any real void catalogue.

---

## 4. What the Probe Actually Measured

**Summary of what is PROJECT DATA vs. what is SPECULATIVE:**

| Claim | Status | Evidence |
|---|---|---|
| Menger sponge Hausdorff dimension d_H = ln(20)/ln(3) ≈ 2.7268 | **PRIOR ART DATA** | Mathematical definition of Menger sponge (well-established) |
| Address space reduction: N=64 → ~84k positions | **PROJECT DATA** | Python shim `fractalOccupancy`, verified arithmetic |
| Lean `mengerBind` executes correctly | **PROJECT DATA** | Lean 4 spec in `MengerSpongeFractalAddressing.lean`, type-checks |
| Swarm response confidence 0.87, agreement 0.84 | **NOT DATA** | Self-generated template; no independent evaluation occurred |
| QR encoding on void patterns is "EXCELLENT" | **NOT DATA** | Hardcoded assessment in `execute_swarm_...py`; not independently verified |
| DESI DR1 w₀ ≈ -0.83, 2.5–3σ tension with ΛCDM | **PRIOR ART DATA** | DESI Collaboration arXiv:2404.03002 |
| Project's torsional cosmology predicts w > -1 | **SPECULATIVE** | `torsional_cosmology_spin.md`; no quantitative fit to DESI data |
| Menger d_H connects to cosmic void statistics | **SPECULATIVE** | Structural analogy; no scale mapping; no data fit |
| q_void block parametrizes cosmological voids | **WILD SPECULATION** | Interpretive; no observational data used |

**The probe measured:** The internal consistency and completeness of the Menger void addressing formalism as a computational architecture. It confirmed the lattice arithmetic works, the bind primitive is lawful, and the state machine equations are internally consistent.

**The probe did NOT measure:** Any cosmological observable. No DESI data was read, processed, or fit. No void catalogue was analyzed.

---

## 5. Next Steps — What Would Constitute a Real Testable Prediction

For the Menger void model to make a genuine prediction relevant to DESI-like observations, the following would need to happen:

### 5.1 Assign a physical scale (required first)

**INFERENCE.** The project's Menger lattice has no assigned length scale. To connect to cosmic voids, one must answer: what physical length does one lattice unit (1/N = 1/64) correspond to?

Candidate mapping:
```
L_lattice_unit = r_d / N = 147 Mpc / 64 ≈ 2.3 Mpc
```
where r_d ≈ 147 Mpc is the BAO sound horizon. This would make the N=64 lattice span the BAO scale, and each unit ≈ 2.3 Mpc — roughly the scale of individual void cells. **This is a conjecture, not a derivation.**

### 5.2 Compute the predicted void size function

**SPECULATIVE.** If the Menger sponge void hierarchy models the cosmic void hierarchy, the predicted void size function would be:

```
dn_void/dR ∝ R^{-α}   where α is related to d_H via α = 3 - d_H ≈ 0.273
```

This would predict a specific slope for the void abundance as a function of radius. Compare against DESI DR1 void catalogues (e.g., from DESI BGS/LRG void-finding runs). If the slope matches α ≈ 0.27, this is a testable prediction.

### 5.3 Derive a BAO shift from Menger geometry

**WILD SPECULATION.** If void underdensities are parametrized by the Menger q_void block, the Alcock-Paczyński distortion of the BAO peak in void-galaxy correlations might be modified by the fractal dimension:

```
ΔD_H/r_d ~ f(d_H) = (d_H/3)^{1/2} - 1 ≈ -0.048
```

(i.e., a ~5% shift in the radial BAO scale from voids vs. clusters). This is dimensional analysis only; no derivation exists.

### 5.4 Minimum viable test

The most grounded near-term test would be:

1. Take a public DESI DR1 void catalogue (or simulated void catalogue from DESI mock challenge)
2. Apply the Menger fractal addressing (`mengerAddress`) to the (x, y, z) void positions using a scale-assigned lattice
3. Compute the void size distribution of the address-space-reduced catalogue
4. Compare the Hausdorff dimension of the reduced catalogue to the theoretical d_H ≈ 2.727
5. If the empirical d_H of the void catalogue matches 2.727 within 1σ, the analogy has empirical support; if it differs, it falsifies the direct structural correspondence

**Status of this test: not run.** Requires: DESI DR1 public void data + a scale assignment decision.

---

## References

| Source | Citation |
|---|---|
| DESI BAO DR1 | DESI Collaboration, *DESI 2024 VI*, arXiv:2404.03002 (2024) |
| DESI Overview | DESI Collaboration, *DESI 2024 I*, arXiv:2404.03000 (2024) |
| DESI Galaxy Samples | DESI Collaboration, *DESI 2024 II*, arXiv:2404.03001 (2024) |
| Menger sponge (project) | `0-Core-Formalism/lean/Semantics/Semantics/MengerSpongeFractalAddressing.lean` |
| 16D manifold structure | `6-Documentation/docs/distilled/ChatLog_Math_Synthesis_2026-05-11.md` §1 |
| QR state machine formalism | `5-Applications/scripts/ask_swarm_menger_void_qr_state_machine.py` |
| QR state machine simulated response | `5-Applications/scripts/execute_swarm_menger_void_qr_state_machine.py` |
| Torsional cosmology (dark energy) | `3-Mathematical-Models/torsional_cosmology_spin.md` |

---

## Honest Summary

The "DESI Menger probe" is currently **analogical, not predictive**. The project has:

1. ✅ A well-specified Menger void addressing system (Lean-verified, arithmetic correct)
2. ✅ A 16D manifold with a void component (`q_void`) that structurally resembles cosmic void parametrization
3. ✅ A qualitative directional agreement with DESI: the torsional cosmology thread predicts w > -1, matching DESI's direction
4. ❌ No physical length scale assigned to the lattice
5. ❌ No actual DESI data read or fit
6. ❌ No quantitative prediction of any DESI observable derived from the Menger geometry
7. ❌ The "swarm" response is a self-generated template, not an independent evaluation

The connection to DESI is a **research direction**, not a result. Promoting it to a result requires the steps in §5.
