# AGENTS.md - Lean/Semantics

Scope: `0-Core-Formalism/lean/Semantics/`

The strict operating rules live in `../../../6-Documentation/docs/AGENTS.md`.
Follow those rules for all Lean, proof, fixed-point, hardware-extraction, and
shim-boundary work.

## Local Rules

- Keep module names aligned with file names and namespaces.
- Prefer small domain modules over utility files.
- Every new computational gate needs an executable witness: theorem, `#eval`,
  or native-decision proof.
- Run the narrow build target first, for example:

```bash
lake build Semantics.BeaverMaskFreshness
```

- Run the broader build before claiming a stable Lean surface:

```bash
lake build
```

- Do not delete difficult theorems to make builds pass. Fix proofs or quarantine
  with an explicit `TODO(lean-port): ...` boundary.
- Treat generated Python, Rust, Verilog, and JSON as shims or receipts, not as
  the formal source of truth.
- Float (`Q16_16.ofFloat`, `Q0_16.ofFloat`, `Q0_64.ofFloat`) is forbidden in
  compute-path code. Use `Q16_16.ofNat`, `Q16_16.ofRatio`, or `Q16_16.ofInt`
  instead. The historical 5 contamination sites in `BraidCross.lean:49,50,84`
  and `BraidStrand.lean:57,71` are the canonical fixed-point constructor
  template.
- Every new compressor theorem pair MUST provide both `eigensolid_convergence`
  and `receipt_invertible`. The convergence theorem proves the crossing loop
  stabilizes; the invertibility theorem proves the receipt bijectively encodes
  the original state including zero/gap/timing/absence dimensions.
- The BraidEigensolid module (`Semantics.BraidEigensolid`) is the canonical
  compressor target (planned, not yet written): 10 sections covering Q0_2
  crossing matrix, Sidon labels (powers of 2), golden centering (φ⁻¹ = 0x9E70),
  eigensolid convergence, receipt invertibility, and Anti-BraidStorm adversarial
  check. The fixed-point constructor patterns in `BraidCross` and `BraidStrand`
  must compile first.
- Receipt invertibility is a stronger theorem than convergence. Convergence says
  `crossStep(crossStep(s)) = crossStep(s)`. Invertibility says the full receipt
  `(C, sidon, k, ε_seq, t, ∅_scars)` bijectively reconstructs `s` and that
  `decode(encode(s)) = s` holds for all valid inputs.
- enwik9 is the end-to-end test vector. The hierarchical compressor
  (bytes→chunks→banks→file) must prove `decode(encode(enwik9)) = enwik9` byte-
  for-byte via a Lean execution witness.

## Current Stack-Solidification Anchors

- `Semantics.BeaverMaskFreshness` is a finite admission gate for Beaver-mask
  freshness negative controls.
- `Semantics.HCMMR.Kernels.EntropyCollapseDetector` is the finite arithmetic
  receipt for the corrected entropy-collapse detector. It intentionally keeps
  logarithmic/Hurst quantities as scaled receipt constants and proves the
  dense-rank crossing count, D2 numerator, and Kendall tail values with
  executable Lean checks.
- Stack status receipts live under `shared-data/data/stack_solidification/`.
- The canonical arithmetic note is
  `../../../6-Documentation/docs/distilled/ArithmeticSpec_Corrected_2026-05-11.md`.
  Treat `sigma_q` on `n=8` as a deterministic window feature, not as a robust
  Hurst estimator.
- The K=21 prime-gap rerun receipt is
  `../../../shared-data/data/stack_solidification/prime_gap_k21_rerun_receipt_2026-05-11.md`.
  Its conclusion is deliberately bounded: rare surviving windows are candidate
  motifs, not a general prime-gap collapse theorem.
- Historical staged slices are documented in
  `../../../6-Documentation/docs/stack_solidification_staging_manifest_2026-05-09.md`
  and
  `../../../6-Documentation/docs/stack_solidification_staging_manifest_2026-05-10.md`.

## Local Quarantine Boundaries

- The root `.gitignore` excludes known local formal scratch/WIP such as
  `2-Search-Space/FAMM/FAMM_FSDU.lean` and `4-Infrastructure/hardware/test.lean`.
  Do not revive ignored Lean files into the clean build surface without first
  making them compile under a narrow target.
- Generated `*_tb.v` and `*_test_vectors.json` files are build artifacts unless
  a task explicitly promotes one as a hardware receipt.

## Blessed Compiler Surface (as of 2026-05-30, commit `b7f3d1a9`)

The `Compiler` lean_lib in `lakefile.toml` gates the promoted API surface.
Only the following roots are blessed for downstream import and receipt emission:

| Root | Purpose |
|------|---------|
| `Semantics.RRC.Emit` | Alignment classifier; `emitCorpus` generic entry point |
| `Semantics.AVMIsa.Emit` | **Sole output boundary** — AVM canaries + stamps all receipts |
| `Semantics.RRC.Corpus278` | 278-equation raw feature list (Python-supplied, Lean-gated) |

Build the narrow surface with:

```bash
lake build Compiler
```

Build the full workspace with:

```bash
lake build
```

Compiler surface baseline: **3313 jobs, 0 errors** (`lake build Compiler`, commit `859d8726`, reverified 2026-05-28).
Full workspace: **3573 jobs, 0 errors** (`lake build`, reverified 2026-06-08).
PistSimulation: **3309 jobs, 0 errors** (`lake build Semantics.PistSimulation`, commit `778b78d3`, reverified 2026-05-27).
EmergencyBoot: **3302 jobs, 0 errors** (`lake build Semantics.Hardware.EmergencyBootTypes Semantics.Hardware.EmergencyBootState Semantics.Hardware.EmergencyBootShell`, reverified 2026-05-27).

### BraidDiatCodec — chirality/MMR/braid residual codec

New codec module (`Semantics.BraidDiatCodec`) layers the mountains-on-mountain stack into a compact binary format:

- **Layer 1** — `ChiralityDIAT`: 2-bit chirality + 62-bit DIAT slot address. Encode: `(Chirality × UInt32) → ChiralityDIAT`. Decode roundtrip proven (`encode_decode_roundtrip`).
- **Layer 2** — `MountainPacked`: height(8) + apex(48) + base_count(8) + base coords. Lossless `fromMountain` / `toMountain` with inner MMR preserved recursively.
- **Layer 3** — `BraidResidualPacked`: 5 Q0_2 fields × 2 bits = 10 bits per crossing residual. Q0_2 roundtrip proven (`bracket_roundtrip`).
- **Layer 4** — `BraidDiatFrame`: 256-bit fixed header + variable mountain list. Full `encode` / `decode` between `SpherionState × BraidReceipt` and frame.

Key invariants: DIAT mass (`a + b = 2k + 1`), MMR strictly decreasing heights, Q0_2 4-state packing.

### BraidSpherionBridge — SpherionState ↔ BraidState equivalence

New bridge module (`Semantics.BraidSpherionBridge`) wires the mountains-on-mountain formalism to the braid strand formalism:

- **`SpherionSpike`** — `spike(m : Mountain, crossPair : Fin 4)` ties a Mountain to which braid pair fires
- **`spikeToStrandUpdate`** — applies a spike's crossing to a `BraidState` via `braidCross`
- **`strandFlow`** — iterates `spikeToStrandUpdate` over a spike train
- **`braidCross_merge_correspondence`** — (admit) braidCross on (i,j) ↔ Mountain.merge for corresponding pair
- **`receipt_correspondence`** — (admit) BraidReceipt = SpherionState receipt dimensions

Key remaining admits: `IntNodeToPhaseVec` linearity (`IntNode.add ↔ PhaseVec.add`), step count accumulation, full receipt dimension mapping.

### goldenContractionEnergyDecrease — proof status

**Statement:** For Burgers fields with non-negative `u` and pointwise contraction `u'[i] ≤ u[i]`, the golden-contraction dissipation step reduces kinetic energy.

**Status:** Formal proof complete. The proof lifts pointwise square inequalities
through a `List.Forall₂` fold induction and uses `Array.foldl_toList` only to
connect the array energy definition to the list proof.

**Current theorem hypotheses:** `h_u_nonneg`, `h_u'_nonneg`, `h_pt`
(pointwise `u'[i] ≤ u[i]`), `h_size`, `hN`. Convexity is not part of this
theorem; it belongs in a separate premise-discharge lemma for `h_pt` and
`h_u'_nonneg`.

### Architecture: AVM is the sole output boundary

```
RRC.Corpus278   — 278 FixtureRows, raw features only (no decisions)
      ↓ emitCorpus
RRC.Emit        — alignment gate (missingPrediction / alignedExact / etc.)
      ↓ emitRrcCorpus278
AVMIsa.Emit     — AVM canaries must pass; stamps avm.rrc_corpus278.bundle
                  emits final JSON; SOLE output boundary
```

**Rule:** Nothing outside `AVMIsa.Emit` may emit a top-level receipt JSON.
`RRC.Emit` is a classifier that feeds it. `RRC.Corpus278` supplies raw features.

### Goal A canary receipt (AVMIsa.Emit §1–6)

Three passing canaries: `avm.canary.not`, `avm.canary.and`, `avm.canary.or`.
Expected `#eval emit.json` shape:

```json
{
  "schema": "avm_canary_emit_v1",
  "all_canaries_passed": true,
  "receipts": [...],
  "rrc_logogram": { "shape": "logogramProjection", ... },
  "projection_passed": true
}
```

### 278-equation corpus (AVMIsa.Emit §7 / RRC.Corpus278)

`emitRrcCorpus278` classifies all 278 rows and stamps the bundle.
Expected `#eval` corpus summary: `(278, <passed>, 278 - <passed>)`.

Current state: `(278, 0, 278)` — all held, no PIST labels present yet.
This is **correct and honest** — the gate reports exactly what it sees.

The PIST predictions merge pipeline:
  `pist_matrix_builder.py` → `rrc_pist_predictions_278_v1.json` → `build_corpus278.py` reads it
  and populates `pistProxyLabel`/`pistExactLabel` in generated `Corpus278.lean`.
  The merge is keyed by `invariant_receipt.object_id` (equation_id = `rrc_eq_<hex>`).
  When the predictions artifact has non-null labels, regenerating Corpus278.lean
  via `python3 4-Infrastructure/shim/build_corpus278.py` will automatically flow them
  into `determineAlignment` — no Lean emit logic changes needed.

Each row carries 5 generator fields for EN9wiki page generation:
- `operatorTokens` — domain/operator token list (from route_hint + rrc_kind)
- `invariantsDeclared` — declared invariant family (from domain_type)
- `boundaryConds` — binding class (from bind_class)
- `templateKey` — page-generator template (`definition`/`master_equation`/`gate`/`receipt`/`hold`)
- `templateParams` — compact rendering parameter string

To regenerate `Corpus278.lean` from source:

```bash
python3 4-Infrastructure/shim/build_corpus278.py
```

Python's role: raw feature extraction only. Lean's role: all gating decisions.

## Quarantined Modules (not in build surface)

| Module | File | Reason |
|--------|------|--------|
| `PIST.HybridTSMPISTTorus` | `2-Search-Space/PIST/HybridTSMPISTTorus.lean` | 2 sorry-related errors; no importers |

Quarantined files are excluded from `lakefile.toml` PIST roots. Revive only
after narrowly compiling the file under a scratch target.

## Pending Proof Work

- `goldenContractionEnergyDecrease` is discharged. Remaining follow-up is a
  separate premise-discharge lemma showing when the Burgers golden-contraction
  step satisfies `h_pt` and `h_u'_nonneg`.
- `HyperbolicStateSurface.ko_preserves_hyperbola_approx`: former sorry replaced
  by explicit premise `onHyperbolaApprox (forwardStep s Δu) Q16_16.epsilon` (line 69).
  Remaining: `TODO(lean-port)` discharge that premise from a formal `Q16_16.sqrt`
  error-bound lemma.
- `SSMS.aciPreservedByMlgruStep`: theorem signature updated with
  `h_ft_range : ∀ i, (fT i).toInt ≥ 0 ∧ (fT i).toInt ≤ FixedPoint.q16Scale`
  (line 546). The `hprev` and `hcand` sub-proofs use `abs_sub_comm` with correct
  argument ordering (lines 559–571). The `f_eps` and `omf_eps` sub-lemmas are
  proved via `mul_mono_left` + `one_mul` (PROVED, lines 605–607, 611–614).
  The `omf_toInt` equality is proved via `q16Clamp_id_of_inRange` (lines 575–599).
  The remaining `admit` (line 619) is the full mlgruStep preservation chain.
  **STATUS (2026-06-01): BLOCKED** — The proof requires a Q16_16 distributivity
  lemma (sub/add/mul) plus a floor-division error analysis. Without these,
  the convexity chain cannot be completed. Furthermore, `abs_triangle` is
  FALSE for Q16_16 saturating arithmetic (counterexample: a=3, b=-3 gives
  |a-b|=0 ≠ |a|+|b|=6), so a standard triangle inequality is unavailable.
  **Required infrastructure (to be developed as a new module):**
  1. `Q16_16.add_toInt_of_no_sat` — when no saturation, add is exact at toInt
  2. `Q16_16.sub_toInt_of_no_sat` — when no saturation, sub is exact at toInt
  3. `Q16_16.mul_floor_le` — `(mul a b).toInt ≤ a.toInt * b.toInt / q16Scale`
  4. `Q16_16.mul_floor_ge` — `(mul a b).toInt ≥ a.toInt * b.toInt / q16Scale - 1`
  5. Convex combination bound: `|f·x + (1-f)·y - f·x' - (1-f)·y'| ≤ f·|x-x'| + (1-f)·|y-y'| + 2`
     (the +2 absorbs the 2-ULP floor-division rounding error)
- `FixedPoint.lean` Q16_16 lemma library (lines 617–695):
  - `mul_mono_left/right` ✅ PROVED — `Int.ediv_le_ediv hpos hmul` pattern works
    with explicit `hpos : 0 < q16Scale` proof
  - `abs_sub_comm` ✅ PROVED — three-case split on `d := a.val - b.val` relative to
    `q16MinRaw`/`q16MaxRaw` bounds
  - `add_le_add` ✅ PROVED — `add_nonneg_monotone` + `q16Clamp_monotone`
  - `abs_nonneg` ✅ PROVED — `q16Clamp_nonneg_of_nonneg` for neg case
  - `abs_mul_le` ❌ REMOVED — was provably FALSE (counterexample: a=3, b=-1)
  - `abs_triangle` ❌ REMOVED — was provably FALSE (counterexample: a=3, b=-3)
  - `sub_eq_add_neg` (line 620): admit, unused
  - **MISSING for SSMS** (to be added):
    - `add_toInt_of_no_sat`, `sub_toInt_of_no_sat` (PROVED in FixedPoint.lean)
    - `mul_floor_le`, `mul_floor_ge` (PROVED in FixedPoint.lean)
    - Convex combination bound (Q16_16-specific)
- `EmergencyBootTypes.lean` — 6502 design philosophy hardware types (graphene memristor,
  optical fiber hot/cold paths, voltage differential computation). All structures compile;
  remaining formal work: `eigensolid_convergence` for optical delay-line memory,
  `receipt_invertible` for geometric seed extraction.
- `EmergencyBootState.lean` — power failure detection, seed assembly, self-sufficiency
  checks. Verified: `utilizationWithinBounds` (FPGA resource limits), `powerFailureMonotonic`
  (bridge isolation implies no false detection).
- `EmergencyBootShell.lean` — Tiny IP command interface (BOOT, SCAN, STATUS, EXIT, etc.).
  Verified: `commandOpcode_roundTrip` (opcode parsing correctness).
  TODO(lean-port): status byte round-trip theorem, phase-disjointness for command gating.

## Key API Notes (Lean 4.30 / this workspace)

- `Q16_16` is a Subtype `{ x : Int // q16MinRaw ≤ x ∧ x ≤ q16MaxRaw }`.
  Safe constructors: `Q16_16.ofRawInt (n : Int)`, `Q16_16.ofBits (u : UInt32)`,
  `Q16_16.ofNat`, `Q16_16.ofRatio`. No struct literals `{ val := N }`.
- `Q0_16` has `add`/`sub` (no `addSat`/`subSat`).
- `List.get?` does not exist — use `list[i]?` subscript syntax.
- `liftMetaM` is the correct combinator for `MetaM → TacticM` in `mapM`.
- `MVarId.toNat` does not exist — use `g.name.toString`.
- `List.size` → `.length`; `Json.num Nat` → `Json.num { mantissa := (n : Int), exponent := 0 }`.

## Cross-References

See root `AGENTS.md` for:
- **Post-Interaction Workflow** (mandatory 5-step session-end procedure)
- **Programming Choice Flow** (Lean owns decisions; Python owns I/O)
- **Do Not Sweep** rules (no broad `git add .`)
- **Git Remote Hygiene**
