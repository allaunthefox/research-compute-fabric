# Full-Stack Assumption DAG — 2026-05-13

**Files audited: 78** | **Assumptions identified: ~280** | **Build: 3529 jobs, zero errors**

---

## Physics/Lean (15 files)

| File | Grade | Isses |
|------|-------|-------|
| PIST.lean | ✅ Green | 17+ theorems with real proofs. Clean. |
| BraidedFieldPaths.lean | 🟡 Yellow | 2 theorems, structurally correct but claims in comments not proven |
| ThresholdVector.lean | 🟡 Yellow | 12 theorems, all native_decide — thresholds heuristic |
| LogogramRotationLoop.lean | 🟡 Yellow | Band-disjointness claim contradicted by its own test |
| BraidSerial.lean | 🟡 Yellow | Roundtrip on one hand-picked packet only |
| BraidCross.lean | 🔴 Red | Trivial zero-strand theorems only |
| Law19_VoidScar.lean | 🔴 Red | 0 theorems, all claims in comments |
| BoundaryEigenFire.lean | 🔴 Red | 0 theorems, 7 heuristic claims, arbitrary thresholds |
| HyperEigenSpectrum.lean | 🔴 Red | 0 theorems, arbitrary regime transitions |
| MengerSpongeFractalAddressing.lean | 🔴 Red | 4 theorems, 3 are empty placeholders |
| FAMM.lean | 🔴 Red | 2 theorems, both tautological |
| BraidBracket.lean | 🔴 Red | 0 theorems, placeholder constants |
| BraidStrand.lean | 🔴 Red | 0 theorems, lossy Float roundtrip |
| BraidField.lean | 🔴 Red | 0 theorems, RG claims in comments only |
| NBody.lean | 🔴 Red | 1 BROKEN theorem (references nonexistent lemma) |

## Infrastructure/Shim (33 files)

- **190+ heuristic assumptions** across ~22 receipt generators
- Dominant failure mode: metaphors written as equations (Kerr analogy, BodegaFlow, cognitive shell model)
- Multiple files claim `D_f = log(2)/log(Phi)` without derivation
- **Well-scoped exemplars**: buoyancy_added_mass, solids_physics, magnetic_derivative, alphafold_probe

## 5-Applications (30 files)

- **88 assumptions**, most in PIST compression scripts (27 assumptions, 3 files)
- PIST "compression" is coordinate remapping, not compression
- Multiple scripts import shock physics as metaphor for compression stages
- CAD harness, finance_manager, review_emitter: clean, no physics claims

---

## Action Items by Severity

**Critical (broken build):**
- NBody.lean:1395 — `verlet_preserves_energy_approximate` references nonexistent lemma

**High (placeholder theorems):**
- MengerSpongeFractalAddressing.lean:197,202,208 — 3 theorem bodies missing

**Medium (tautological/trivial theorems):**
- FAMM.lean:141,223 — both theorems are trivial identities
- BraidCross.lean:71,78 — zero-strand theorems only

**Low (heuristic but documented):**
- All HCMMR kernel thresholds, PIST compression claims, cognitive load parameters
- These are acknowledged as model-internal, not empirical claims
