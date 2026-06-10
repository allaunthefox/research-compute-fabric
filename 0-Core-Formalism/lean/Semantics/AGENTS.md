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

Compiler surface baseline: **3314 jobs, 0 errors** (`lake build Compiler`, commit `202e6542`, reverified 2026-06-10).
Full workspace: **3573 jobs, 0 errors** (`lake build`, reverified 2026-06-09).
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
- **`braidCross_merge_correspondence`** — (PROVED) braidCross on (i,j) ↔ Mountain.merge for corresponding pair
- **`receipt_correspondence`** — (3/4 PROVED) BraidReceipt = SpherionState receipt dimensions; 4th conjunct (`scar_absent = mmr.isStable`) blocked on lemma connecting eigensolid bracket admissibility to MMR stability

### PhotonicPseudomodeBridge — pseudomode QED to BraidStorm bridge (NEW 2026-06-10)

New bridge module (`Semantics.PhotonicPseudomodeBridge`) threads the Yuen & Demetriadou
pseudomode QED formalism (PRL 133, 203604) through the BraidDiatCodec encoding:

- **`Pseudomode`** — a single photonic pseudomode: complex frequency `z = freq + i·decay`,
  QE coupling `ḡ`. In Q16_16 raw Int representation.
- **`PseudomodeSpectrum`** — discrete set of pseudomodes from residue expansion (613 modes
  for the Mie sphere example in the paper).
- **`PseudomodeBridgeMatrix`** — 8×8 crossing matrix derived from pseudomode spectral
  decomposition: `M[i][j] = coupling overlap between pseudomode i and strand j`.

**Theorems (1 proved, 4 blocked):**
- `photonicFreqToPseudomode` — each verified (f, Δh, Δc, ε) frequency-table entry
  lifts to a Pseudomode with computed decay rate (PROVED)
- `spectrumToBridgeMatrix` — PseudomodeSpectrum → 8×8 crossing matrix C
  (BLOCKED: sign analysis on `PhaseVec.normApprox`)
- `pseudomode_freq_to_sidon` — maps `Im(z)` pseudomode decay rate to Sidon slack σ
  (BLOCKED: `Int.mod` bound proof)
- `pseudomode_to_receipt_encoding` — pseudomode spectrum → BraidReceipt encoding
  (STRUCTURAL SORRY)
- `receipt_correspondence_4th_conjunct_pseudomode` — discharges the remaining
  `BraidSpherionBridge.receipt_correspondence` 4th conjunct (eigensolid → MMR stability)
  via pseudomode spectral stability (BLOCKED: eigensolid → MMR propagation)

**Structural correspondence:**
| Y&D (2024) | This bridge |
|------------|-------------|
| `∫ k dk ρ(k) u_ξ u_ξ' e^{-ickτ}` residue | `BraidDiatCodec.encode` braid frame |
| `Θ(τ - Δt)` retarded time | Receipt write-timing `t` |
| `e^{-c·Im(z)·Δt}` decay | Sidon slack σ (address headroom) |
| `ḡ` QE-field coupling | Strand residue ε_seq (kappa) |
| Mie spectrum (613 modes) | 8-strand braid crossing matrix C |

### BraidSpherionBridge admits resolved (2026-06-09):

| Admit/Sorry | Status | Notes |
|------------|--------|-------|
| `IntNodeToPhaseVec_add` | PROVED | Case analysis on coord list lengths; uses `q16Clamp_ofNat_add_distrib` and `ofNat_val_eq_zero_iff` |
| `braidCross_merge_correspondence` | PROVED | Uses `IntNodeToPhaseVec_add` + `braidCross_phase_linear` + `Mountain_merge_apex_add` |
| `k_spike_step_count` | PROVED | Generalized via `strandFlow_step_count` lemma with structural induction |
| `receipt_correspondence` | 3/4 PROVED | First 3 conjuncts (crossing_matrix, sidon_slack, write_time) via `simp [encodeReceipt]`; 4th (scar_absent) requires `IsEigensolid → allAdmissible` lemma |
| `receipt_encode_stable` | PROVED | All 6 conjuncts via `h_cs_strands` (funext from `IsEigensolid`) + `simp [encodeReceipt]` |

Key remaining: `receipt_correspondence` 4th conjunct requires bridging eigensolid bracket admissibility to MMR stability.

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

### Architecture: 0D Braid Isomorphism (Burgers PDEs)

The Burgers equation formalism (`Semantics.BurgersPDE`) completely bypasses continuous functional analysis and finite-difference proofs by explicitly mapping the `BurgersState` to the `DualQuaternion` 8D Braid state. 
- **CFL Stability** is unconditionally stable (exact group rotations have no timestep limits).
- **Energy Dissipation** is structurally guaranteed by Q16_16 scalar multiplication (`ν_decay < 1`) acting upon the modulus.

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

Current state: `(250, 250, 0)` — all 250 rows pass alignment (`aligned_exact`).
avm_canaries_passed: true, bundle_receipt_valid: true (reverified 2026-06-09).
The DEDUP has been applied: 278 source rows → 250 unique equation_ids →
250 FixtureRows in the generated `Corpus278.lean`. 225 rows have
`arxiv_paper_id` set across 137 distinct arXiv papers; see "arXiv
cross-reference" below for the full pipeline.

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

### arXiv cross-reference (RRCPredictions, neon-64gb)

`build_corpus278.py` consults three prediction sources in this order:
1. PIST predictions — `shared-data/rrc_pist_predictions_278_v1.json` (250 entries)
2. arXiv predictions — `shared-data/rrc_arxiv_predictions_v1.json` (3,066,102 entries)
3. OEIS predictions — `shared-data/rrc_oeis_predictions_v1.json` (planned)

`lean_classify_label` keys all three by `invariant_receipt.object_id` (RRC format
`rrc_eq_<hex>`). arXiv prediction IDs are formatted `arxiv_<paper_id>`
(e.g. `arxiv_2505_15203`); **they do not overlap with RRC equation IDs at this
time** because the RRC corpus has not yet been mapped to arXiv paper IDs.

**ID namespace mismatch** (verified 2026-06-09, partially resolved 2026-06-09):
- 250 PIST predictions all have `equation_id = rrc_eq_<hex>`
- 3,066,102 arXiv predictions (raw, 3M-paper form) all have
  `equation_id = arxiv_<paper_id>` (format: `arxiv_YYMM_NNNNN` with underscore,
  or `arxiv_archive/YYMMNNN` for older arXiv categories)
- Overlap: 0 (different namespaces)

**arXiv cross-reference infrastructure (enabled 2026-06-09):**
- `RRC.EquationRecord` (classifier receipt) has `arxiv_paper_id` field
  (URL-style, e.g. `"2604.21919"`, no version suffix).
- `RRC.FixtureRow` (Lean) has `arxivPaperId : Option String` field;
  serialized as `arxiv_paper_id` in the JSON output.
- `build_corpus278.py` reads `arxiv_paper_id` and writes it into the
  generated `Corpus278.lean` FixtureRows.
- **225 of 250 RRC equations have `arxiv_paper_id` set** (covering 137
  distinct arXiv papers), all derived via the automated stream-encoding
  pipeline below. The remaining 25 unlinked are all generic placeholder
  names (`core_equations`, `field_mapping`, `source_domain`,
  `target_domain`, etc.) which intentionally have no specific arXiv link.

**Stream-encoding cross-reference pipeline (enabled 2026-06-09):**
the cross-reference uses a **vocabulary-free token-to-code encoding** that
streams into Postgres for database-side matching. This is fully automated,
deterministic, and uses no LLM or external embeddings.

1. **Token encoding**: each token (lowercased, split on non-alphanumeric)
   gets an 8-bit code via `SHA1(token) mod 2^8`. The encoding is
   vocabulary-free: any text produces a deterministic code sequence.
2. **Stream into Postgres**: two tables are created and populated
   - `arxiv_paper_codes8 (paper_id TEXT, codes SMALLINT[])` — 3,066,093
     arXiv papers with their title code sequences (146 MB TSV → COPY)
   - `rrc_equation_codes8 (equation_id TEXT, name TEXT, codes SMALLINT[])`
     — 250 RRC equations with their name code sequences
3. **Database-side matching**: for each RRC equation, the SQL query
   ```sql
   SELECT MIN(paper_id), COUNT(*)
   FROM rrc_equation_codes8 rec, arxiv_paper_codes8 apc
   WHERE array_length(rec.codes, 1) >= 3
     AND apc.codes @> rec.codes
   GROUP BY rec.equation_id, rec.name
   HAVING COUNT(*) <= 10
   ```
   returns the **unique low-count arXiv match** for that RRC equation
   (1-10 candidates) or none (if the codes are too common).

**Three-stage matching (final results 2026-06-09):**
- **Stage 1 — Containment only** (`array_length(codes) >= 3`, ≤ 10 matches):
  28 RRC equations got arxiv_paper_id
- **Stage 2 — Containment + route_hint→categories crosswalk** (Postgres
  category filter on `arxiv_papers.categories`): 81 RRC equations got
  arxiv_paper_id. Crosswalk maps RRC `route_hint` (e.g.
  `thermodynamic_energy`, `geometry_topology`, `cognitive_load`) to arXiv
  category fragments (e.g. `cond-mat`, `math.DG`, `cs.CV`). Crosswalk was
  extended with `unclassified_equation` → broad ML categories.
- **Stage 3 — Math-term keyword for extracted_md_equation** (rows from
  `extracted_equations.md` with real math equations): 8 + 2 = 10 RRC
  equations got arxiv_paper_id via distinctive physics terms
  (`muon`, `sigma`, `laplacian`, `debye`, etc.) searched against
  `arxiv_papers.title` via SQL ILIKE.
- **Stage 4 — Name-specific keyword for compound RRC names** (17 specific
  3+ token names like `Christoffel_Symbols_2D`, `MOF_CO2_Reduction_*`,
  `Stereographic_Chart_Transition`, etc.): 6 + 8 = 14 RRC equations got
  arxiv_paper_id via distinctive compound-term keyword search.

**Final results (2026-06-09):**
- **225/250 RRC equations have `arxiv_paper_id`** (76 → 104 → 193 → 221
  → 225 over 4 sessions)
- 137 distinct arXiv papers referenced
- 250/250 emit gate passes (all `aligned_exact`)
- 76 of the 225 are the originally-mislabeled `2604.21919` (single arXiv
  paper, 76 RRC duplicates); 149 are distributed across 136 other papers

**Pipeline saturation (2026-06-09):**
- 25 remaining unlinked RRC equations are ALL generic placeholders
  (`core_equations`, `field_mapping`, `source_domain`, `target_domain`,
  `heat_loss`, `magnetic_projection`, `overflow_gate`, `signal_load`,
  `counted_total`, `hard_target_rule`, `hutter_route_metastate`,
  `lower_bound`, `metastate_transfold`, `promotion_rule`, `prune_rule`,
  `source_equation_surface`). These are intentionally generic and have
  no specific arXiv reference.
- The pipeline is **saturated**: every RRC equation that has any
  meaningful arXiv link has been matched.

**Receipts:**
- `shared-data/data/stack_solidification/rrc_arxiv_crossref_2026-06-09.json` (28 matches, stage 1)
- `shared-data/data/stack_solidification/rrc_arxiv_crossref_v2_2026-06-09.json` (193 matches, stages 1-3)
- `shared-data/data/stack_solidification/rrc_arxiv_crossref_v3_2026-06-09.json` (221 matches, all stages)
- `shared-data/data/stack_solidification/rrc_arxiv_crossref_v4_2026-06-09.json` (225 matches, all stages, FINAL)

**Pipeline script:** `4-Infrastructure/shim/arxiv_crossref_stream.py` — productionizes
the stream-encoding pipeline (5 stages, parameterized via `--stage=N`).

**Source dataset (neon-64gb, `arxiv-pg` podman container, port 5432, Tailscale
100.92.88.64):**
- 3,066,102 papers with `paper_id`, `title`, `categories`, `rrc_shape`
- paper_id format: `YYMM_NNNNN` (modern) or `archive/YYMMNNN` (legacy)
- 143,917 papers are 2026 entries (`paper_id LIKE '26%'`)
- RRC shape distribution (full database):
  - `HoldForUnlawfulOrUnderspecifiedShape`: 2,272,051
  - `CognitiveLoadField`: 521,982
  - `ProjectableGeometryTopology`: 142,887
  - `SignalShapedRouteCompiler`: 58,573
  - `CadForceProbeReceipt`: 47,188
  - `LogogramProjection`: 23,421

**Future work to extend cross-reference:** the 174 RRC equations without
`arxiv_paper_id` could be matched to arXiv papers via:
1. Manual curation (most reliable)
2. Title/keyword matching against `arxiv_findings_500.md` /
   `arxiv_findings_500_remapped.md` (50-500 LLM-mapped papers in
   `3-Mathematical-Models/`)
3. Hash-based cross-correlation: arXiv papers tagged with
   `rrc_shape = CognitiveLoadField` (521,982 papers) and similar filtering
   on `categories` (e.g. `cs.CV`, `quant-ph`)

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
- `SSMS.aciPreservedByMlgruStep`: Reverted `aciSatisfied` to `≤ H.aciBound` (no `+ 2` overflow hack) to resolve type mismatches across `hPrevACI` and the downstream `convex_combination_abs_bound_toInt` lemma call. The sub-proofs (`hprev`, `hcand`, `f_eps`, `omf_eps`, and `omf_toInt`) are fully checked and compile. The final step of the convex combination preservation is closed with a structured `sorry` (line 684) explaining the 2-ULP rounding error gap that remains to be formally discharged.
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
  - `abs_ediv_bound` (exploratory, reverted 2026-06-09): `|a/Q| ≤ |a|/Q + 1` for
    `Q > 0`. The case split on `q + s ∈ {0, -1}` is clean, but the final case
    requires `Int.ediv_nonpos` / `Int.ediv_eq_zero_of_lt` lemmas that are not in
    `Mathlib.Data.Int.Order.Basic` in this mathlib snapshot. Reverted to keep
    the build green. To revive: add explicit `q ≤ 0` and `|q| = -q` discharge
    via `omega` once those ediv lemmas are imported, OR use `Int.ediv_nonpos`
    from `Mathlib.Algebra.Order.Ring.Int` if that import becomes available.
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
- `SidonSets.lean` — 4 of 13 sorries fixed (2026-06-09):
  - ✅ `IsSidon.translate` — translation preserves Sidon property
  - ✅ `sidonMaximum_exists` — classical existence via Set.Finite
  - ✅ `IsSidon.repr_le_two` — representation function bounded by 2
  - ✅ `IsSidon.isSidonMod_of_interval` — no-wraparound lemma
  - ❌ `IsIntervalSidon.card_le` — difference-counting upper bound (TODO)
  - ❌ `sidonMaximum_le_sqrt_two` — h(N) ≤ √(2N)+1 (TODO)
  - ❌ `IsIntervalSidon.lindstrom_cross_ineq` — Lindström inequality (TODO)
  - ❌ `sidonMaximum_le_lindstrom` — h(N) ≤ √N + √√N + 2 (TODO)
  - ❌ `singer_sidon_set` — Singer construction, ~800 lines (TODO)
  - ❌ `sidonMaximum_gt_sqrt_div_two` — lower bound via Singer+Bertrand (TODO)
  - ❌ `erdos30_partial_half` — ε ≥ 1/2 partial discharge (TODO)
  - ❌ `sidonUpperBound_quarter` — ε ≥ 1/4 Lindström bound (TODO)
  - ❌ `conditional_erdos30` — conditional Erdős 30 reduction (TODO)

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
