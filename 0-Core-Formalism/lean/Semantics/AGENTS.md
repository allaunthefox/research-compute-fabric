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

## Blessed Compiler Surface (as of 2026-05-26, commit `9928dd74`)

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

Full workspace build baseline: **3567 jobs, 0 errors** (commit `9928dd74`).

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

- `goldenContractionEnergyDecrease` in `Semantics/PistSimulation.lean`:
  theorem body present with `sorry`; marked `TODO(lean-port)`. Proof requires
  Jensen's inequality for discrete convex combinations on Q16_16. The theorem
  is positioned after `burgersPhiEnergyStep` (its dependencies are now in
  scope). Do not move or re-comment this theorem; fix the proof instead.

## Key API Notes (Lean 4.30 / this workspace)

- `Q16_16` is a Subtype `{ x : Int // q16MinRaw ≤ x ∧ x ≤ q16MaxRaw }`.
  Safe constructors: `Q16_16.ofRawInt (n : Int)`, `Q16_16.ofBits (u : UInt32)`,
  `Q16_16.ofNat`, `Q16_16.ofRatio`. No struct literals `{ val := N }`.
- `Q0_16` has `add`/`sub` (no `addSat`/`subSat`).
- `List.get?` does not exist — use `list[i]?` subscript syntax.
- `liftMetaM` is the correct combinator for `MetaM → TacticM` in `mapM`.
- `MVarId.toNat` does not exist — use `g.name.toString`.
- `List.size` → `.length`; `Json.num Nat` → `Json.num { mantissa := (n : Int), exponent := 0 }`.
