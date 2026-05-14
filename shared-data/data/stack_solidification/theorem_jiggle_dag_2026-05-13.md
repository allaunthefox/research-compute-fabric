# Theorem Jiggle DAG — 2026-05-13

**Build:** `lake build Semantics` — 3529 jobs, zero errors  
**Commit:** pending (jiggle fixes applied)

---

## Fixed Jiggles

| File | Issue | Fix |
|------|-------|-----|
| `PhotonTorsionProbe.lean:37` | Placeholder theorem proving `1 > 0` | Replaced with honest comment: effect underflows Q16_16 |
| `DESIInvariant.lean:208-221` | 4 vacuous theorems: `v - 3s <= v <= v + 3s` | Replaced with DR1 vs DR2 consistency checks via `absDiff` |
| `UniversalBridge.lean:261` | `.get!` at Re=3150 without `.isSome` guard | Added `intermittency_midpoint_some` companion theorem |

## Known Jiggles (acknowledged, not fixed)

| File | Issue | Status |
|------|-------|--------|
| `UniversalBridge.lean:8-9` | Hermite slopes m0, m1 from Moody chart, not first principles | **Heuristic — acceptable for engineering bridge** |
| `UniversalBridge.lean:22-23` | Q16_16 ±1 ULP truncation error | **Known, negligible for application** |
| `UniversalBridge.lean:150-161` | Laminar exit discontinuity (friction jumps at Re=2300) | **Physics discontinuity in Moody chart, not model error** |
| `DESIModelProjection.lean:68-72` | w0 calibrated to DESI DR1, not predicted | **Documented as calibration** |
| `DESIModelProjection.lean:82-85` | wa = -0.55 has no SM derivation | **Heuristic — largest open question** |
| `DESIModelProjection.lean:87-93` | Omega_m = 0.290 from void fraction calibration | **Heuristic — needs RG derivation** |
| `CouplingRotation.lean:15` | w0 projection formula is invented | **Self-acknowledged heuristic** |
| `TorsionWall.lean:10-12` | alpha = max|beta|/(4*pi) is invented formula | **Acknowledged as proposed relation** |
| `CMBTorsion.lean:60-66` | Q predicted 13x above measured, handwaved | **Factor 13 discrepancy not resolved** |
| `ClusterBHAnchors.lean:86` | M-sigma from fractal sum is post-hoc | **Geometric, not physical** |

## Verdict

| Metric | Value |
|--------|-------|
| Total theorems audited | 82 |
| Fixed jiggles | 3 |
| Known jiggles | 10 |
| Clean theorems | 69 (84%) |
| Build status | 3529 jobs, zero errors |
