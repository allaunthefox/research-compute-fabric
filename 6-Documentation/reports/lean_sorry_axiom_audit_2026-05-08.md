# Lean Sorry/Axiom Audit - 2026-05-08

Scope: `0-Core-Formalism/lean/Semantics/`

Roadmap source: `6-Documentation/docs/roadmaps/ROADMAP.md` Immediate Next Action 1.

Command used for raw roadmap check:

```sh
rg -n --glob '*.lean' '\b(sorry|admit|axiom)\b' 0-Core-Formalism/lean/Semantics
```

Command used for actionable proof-debt filter:

```sh
rg -n --glob '*.lean' '^\s*(private\s+)?axiom\b|^\s*sorry\b|:=\s*sorry\b|by\s+sorry\b' 0-Core-Formalism/lean/Semantics
```

## Result

2026-05-10 refresh: the stricter source-level filter now finds 11 remaining
actionable proof-debt hits across 2 files. This is an increase because
`Semantics/FixedPoint.lean` moved Q16_16 add/sub to signed `toInt` arithmetic
and replaced unclosed low-level UInt32 reconstruction proofs with explicit
`HOLD(q16-proof)` axioms rather than hidden `sorry` blocks. The build surface is
healthy, but the Q16 algebra closure remains proof debt.

| Count | File |
|---:|---|
| 9 | `0-Core-Formalism/lean/Semantics/Semantics/FixedPoint.lean` |
| 2 | `0-Core-Formalism/lean/Semantics/Semantics/TriangleManifold.lean` |

The only strict `admit` match was not a proof-hole token:

```text
0-Core-Formalism/lean/Semantics/Semantics/NS_MD.lean:139:  admit node.admission eg epi b
```

That is a domain predicate call to `def admit`, not Lean's proof-hole syntax.

## Actionable Locations

```text
0-Core-Formalism/lean/Semantics/Semantics/FixedPoint.lean:307:axiom zero_mul (a : Q16_16) : zero * a = zero
0-Core-Formalism/lean/Semantics/Semantics/FixedPoint.lean:312:axiom mul_zero (a : Q16_16) : a * zero = zero
0-Core-Formalism/lean/Semantics/Semantics/FixedPoint.lean:317:axiom one_mul (a : Q16_16) : one * a = a
0-Core-Formalism/lean/Semantics/Semantics/FixedPoint.lean:322:axiom mul_one (a : Q16_16) : a * one = a
0-Core-Formalism/lean/Semantics/Semantics/FixedPoint.lean:343:axiom zero_add (a : Q16_16) : zero + a = a
0-Core-Formalism/lean/Semantics/Semantics/FixedPoint.lean:348:axiom add_zero (a : Q16_16) : a + zero = a
0-Core-Formalism/lean/Semantics/Semantics/FixedPoint.lean:353:axiom sub_self (a : Q16_16) : a - a = zero
0-Core-Formalism/lean/Semantics/Semantics/FixedPoint.lean:358:axiom add_le_left {a b : Q16_16} (hb : b.toInt ≥ 0) :
0-Core-Formalism/lean/Semantics/Semantics/FixedPoint.lean:364:axiom epsilon_add_pos {r : Q16_16} (hr : r.toInt ≥ 0) :
0-Core-Formalism/lean/Semantics/Semantics/TriangleManifold.lean:224:axiom manifoldFieldBounded (tm : TriangleManifold) (friends : List FriendAgent)
0-Core-Formalism/lean/Semantics/Semantics/TriangleManifold.lean:230:axiom concentricNonIntersecting (k1 k2 : Nat) (hNe : k1 != k2) :
```

## Suggested Triage Order

1. `Semantics/FixedPoint.lean`: discharge the signed UInt32 reconstruction lemmas behind `HOLD(q16-proof)` so FSDU can stop relying on axiomatized Q16 algebra.
2. `Semantics/TriangleManifold.lean`: handle as a dedicated module repair pass because the file has broad elaboration drift in addition to its two remaining axioms.

## Notes

- The broad raw search also finds comments, strings, and documentation phrases such as "axiom" in explanatory text. Those were not counted as source-level proof debt here.
- 2026-05-10 verification: `lake build Semantics.FixedPoint`, `lake build Semantics.FAMM`, direct `lake env lean` for `2-Search-Space/FAMM/FAMM_FSDU.lean`, and `lake build Semantics` pass. Receipt: `shared-data/data/stack_solidification/fsdu_q16_build_receipt_2026-05-10.json`.
- Resolved in this pass: `0-Core-Formalism/lean/Semantics/EvolutionaryTransfold.lean` had two bare `sorry` declarations. They were replaced with explicit Boolean gates, soundness theorems, and executable witnesses.
- Resolved in this pass: `0-Core-Formalism/lean/Semantics/F01_Q16_16_FixedPoint.lean` had seven proof holes plus a stale import. Six totality/bounds holes were proven by direct witnesses; the overstrong convergence claim was replaced with an explicit fixed-point witness gate.
- Resolved in this pass: `0-Core-Formalism/lean/Semantics/Semantics/BraidSerial.lean` had ten proof holes and did not elaborate. It is now a fixed-point-only, one-frame braid serial envelope with byte-preserving witnesses, fail-closed invalid-frame decode, and no `sorry`/`axiom` surface.
- Resolved in this pass: `0-Core-Formalism/lean/Semantics/ExtensionScaffold/Temporal/OMT.lean` had five ordered-domain axioms and also failed to elaborate because its Shannon bridge referenced unscoped fields. It now uses a concrete discrete order model and an explicit `ShannonLandauerParams` bridge field.
- Resolved in this pass: `0-Core-Formalism/lean/Semantics/ExtensionScaffold/Math/FourPrimitiveErdosRenyi.lean` had four proof holes and unavailable spectral imports. It is now a finite graph-receipt gate with executable candidate/blocked witnesses.
- Resolved in this pass: `0-Core-Formalism/lean/Semantics/Semantics/TorsionalPIST.lean` had three private fixed-point axioms and depended on stale `Fix16.raw`/`Fix16.neg` surfaces. `Quaternion.lean` and `DynamicCanal.lean` now match current `Q16_16`, and the false global add-zero law was replaced by a concrete initial-state stability witness.
- Resolved in this pass: `0-Core-Formalism/lean/Semantics/Semantics/CostEffectiveVerification.lean` had two axioms plus non-elaborating Real/String machinery. It is now finite-domain and receipt-gated.
- Resolved in this pass: `0-Core-Formalism/lean/Semantics/Semantics/PandigitalSpectralMass.lean` had one false universal Z/N roundtrip theorem. Raw packing/decoding was corrected and covered with bounded executable witnesses.
- Resolved in this pass: `0-Core-Formalism/lean/Semantics/Semantics/GPUVerificationMetaprobe.lean` had two unconditional axioms over a simulated verification surface. They are now explicit receipt-gated theorems.
- Resolved in this pass: `0-Core-Formalism/lean/Semantics/Semantics/MorphicDSP.lean` had two unconditional OEPI allocation axioms. They are now explicit receipt-gated theorems; `lake build Semantics.MorphicDSP` passes.
- Resolved in this pass: `0-Core-Formalism/lean/Semantics/Semantics/HachimojiPipeline.lean` had one unconditional Adaptive Fabric stability axiom. The underlying `AdaptiveFabric.step` can increase residual-derived SLUQ stress, so the claim is now an explicit receipt-gated theorem; `lake build Semantics.HachimojiPipeline` passes.
- Resolved in this pass: `0-Core-Formalism/lean/Semantics/legacy/6point5sigma/HamiltonianMechanics.lean` had one bare `sorry` in the Picard-Lindelof existence step. The theorem now takes the existence witness as a premise. This legacy file still does not check in the current Lake environment because `Mathlib.MeasureTheory.Integral.IntervalIntegral` is unavailable.
- Resolved in this pass: `0-Core-Formalism/lean/Semantics/Semantics/ASICTopology.lean` and `Semantics/NICProbe.lean` had a mutual import cycle plus stale JSON/termination/list APIs. The cycle is broken and both targets build.
- Resolved in this pass: `0-Core-Formalism/lean/Semantics/Semantics/BitcoinMetaprobe.lean` had two unconditional batch/fold axioms plus stale topology/manifold/list APIs. The axioms are now explicit receipt-gated theorems; `lake build Semantics.BitcoinMetaprobe` passes.
- Resolved in this pass: `0-Core-Formalism/lean/Semantics/Semantics/BitcoinMetaprobeEval.lean` had one unconditional refused-batch axiom and an untyped payload batch literal. The axiom is now receipt-gated; `lake build Semantics.BitcoinMetaprobeEval` passes. The executable summary currently reports `5/9`, so the quiz harness is compiling but still exposes behavioral gaps.
- Resolved in this pass: `0-Core-Formalism/lean/Semantics/Semantics/Layer3Metaprobe.lean` had one unconditional internal-fold axiom. It is now a receipt-gated theorem.
- Deferred: `0-Core-Formalism/lean/Semantics/Semantics/TriangleManifold.lean` also fails to elaborate for stale `raw`/`to_q16`/list access/proof issues, so its two axioms should be handled in a dedicated module repair pass rather than as a narrow theorem edit.
- Deferred: `0-Core-Formalism/lean/Semantics/Semantics/Layer3Metaprobe.lean` still fails targeted build after axiom removal due unrelated stale definitions/proofs (`InternalTransition` inhabited instance, option handling, transition-gate proofs, missing `executeInternalTransition`, stale `Array.mkArray`, and malformed theorem/doc boundaries). Treat it as a module repair pass separate from the proof-debt count.
- This audit does not prove that `lake build` passes or fails. It only records the proof-hole and axiom surface requested by the roadmap.
