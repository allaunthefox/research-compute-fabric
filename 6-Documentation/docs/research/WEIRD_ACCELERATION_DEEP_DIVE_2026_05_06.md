# Weird Acceleration Deep Dive - 2026-05-06

Status: research audit / promotion triage

This note reviews the recently added "weird" surfaces and asks a narrower
question: which ones can accelerate Research Stack work, and what gate keeps
them from turning into overclaimed math?

## Executive Read

The strongest acceleration path is not a single new compression shifter. It is
the pipeline shape that is emerging:

```text
semantic/eigen route discovery
  -> GPU/browser candidate generation
  -> FPGA/Lean receipt verification
  -> MassNumber / Underverse promotion or quarantine
  -> searchable concept graph
```

The most useful weird additions are therefore:

1. WebGPU Witness Kernel Pattern in `hdmi_computational_shell.py`
2. UnderversePacket as finite negative accounting
3. HELLO / Semantic Eigenvector Bundle as the search-routing model
4. Braid/rope geometry as a candidate route space, not yet as compression
5. 0D PIST scalar projections as cheap gates/classifiers, not codecs

## Evidence Checked

Commands run:

```bash
python -m py_compile 3-Mathematical-Models/pist_biological_polymorphic_shifter_v3_complete.py 5-Applications/scripts/hdmi_computational_shell.py
python 3-Mathematical-Models/pist_biological_polymorphic_shifter_v3_complete.py
python 5-Applications/scripts/hdmi_computational_shell.py
cd 0-Core-Formalism/lean/Semantics && lake build Semantics.Core.UnderversePacket
cd 0-Core-Formalism/lean/Semantics && lake build Semantics.Core.MassNumber
cd 0-Core-Formalism/lean/Semantics && lake build Semantics.MassNumberMetricClosure
```

Results:

- `hdmi_computational_shell.py` compiles and runs.
- `pist_biological_polymorphic_shifter_v3_complete.py` compiles and runs.
- `Semantics.Core.UnderversePacket` builds with one unused-variable warning.
- `Semantics.Core.MassNumber` does not build yet.
- `Semantics.MassNumberMetricClosure` does not build yet.

## Acceleration Candidate 1: WebGPU Witness Kernel Pattern

Surface:

- `5-Applications/scripts/hdmi_computational_shell.py`
- `WebGPU Geant4-DNA` external reference in `CITATION.cff` and
  `THIRD_PARTY_NOTICES.md`

What accelerates:

- The useful adaptation is architectural: many candidate events generated in a
  GPU/WebGPU/CUDA-style hot path, with a slower verifier/worker path for
  recovery and receipts.
- This maps directly onto the user's hardware framing: GPU does broad work,
  FPGA/Lean verifies selected witnesses.
- The newly added SSB/DSB-style route scoring is a good local invariant-break
  vocabulary:
  - SSB analogue: one local invariant or route break.
  - DSB analogue: paired/clustered break that threatens recovery.
  - DSB-like clusters should block promotion unless a receipt repairs them.

Evidence:

- The HDMI shell now emits `route_damage_score`, `validation_table`, and
  `shell_design.webgpu_witness_kernel_pattern`.
- Demo output recorded `2` SSB-like breaks, `1` DSB-like cluster, and
  `promotion_blocked=True`.

Promotion gate:

- Keep this as `ACTIVE/CANDIDATE` design infrastructure.
- Do not claim actual HDMI compute transport until a hardware smoke proves a
  real frame/packet path.
- Use this immediately for internal search and shifter candidate evaluation.

Next buildable primitive:

```text
candidate_route -> GPU score -> route_damage_score -> MassNumber/Underverse receipt
```

## Acceleration Candidate 2: UnderversePacket

Surface:

- `0-Core-Formalism/lean/Semantics/Semantics/Core/UnderversePacket.lean`

What accelerates:

- This is the missing negative ledger. It gives failed concepts, failed route
  bindings, forbidden paths, and unpromotable residuals a finite typed packet.
- That matters because the repo is full of high-energy candidate concepts. The
  Underverse makes failure searchable instead of letting it disappear or
  silently mutate into a later claim.

Evidence:

- `lake build Semantics.Core.UnderversePacket` succeeds.
- Warning only: unused variable in `isFixedPoint`.

Promotion gate:

- Promote as the receipt surface for failed shifter roundtrips, disconnected
  semantic graph components, and DSB-like route damage.
- Fix the unused-variable warning or make `isFixedPoint` inspect fields before
  commit.

Immediate use:

```text
lossy shifter -> UnderversePacket(absenceClass=Null6, failedRepTag=roundtrip)
DSB-like route cluster -> UnderversePacket(absenceClass=Null4 or Null6)
search miss/disconnected concept -> UnderversePacket(absenceClass=Null4)
```

## Acceleration Candidate 3: HELLO / Semantic Eigenvector Bundle

Surface:

- `6-Documentation/wiki/Concept-Archive.md`
- `6-Documentation/docs/WEIRD_CONCEPTS_GLOSSARY.md`
- Linear target `RES-2377`

What accelerates:

- This is not a theorem yet; it is a good search-engine design sketch.
- The serious interpretation is:

```text
E(H equiv N) + (L x L) -> O(n)
```

where harmonic/eigen structure aligns with graph nodes, so language-lattice
matching becomes route-based instead of full pairwise comparison.

Why it matters:

- It gives the internal search engine a concrete target:
  - literal symbol index
  - semantic eigenvector bundles
  - typed graph paths
  - MassNumber/Underverse admissibility receipts

Promotion gate:

- Keep `HELLO Transform` as `CANDIDATE`, joke provenance attached.
- Promote only after a local graph query demonstrates route compression:

```text
neighbors SemanticMass
path SemanticMass MassNumber
why hutter braid rope
```

## Acceleration Candidate 4: Braid/Rope Geometry

Surface:

- `3-Mathematical-Models/pist_biological_polymorphic_shifter_v3_complete.py`

Observed demo results:

```text
braid                 98 bytes, ratio=0.490, entropy=1.161
multicolor_rope      146 bytes, ratio=0.329, entropy=2.363
braid_rope_fusion    147 bytes, ratio=0.327, entropy=2.376
rope tension         0.107 demo / 0.116 full sample
```

Interpretation:

- These are not compression wins on the demo if ratio means
  `original_size / encoded_size`; ratios below 1 are expansion.
- They are still useful because they create structured route spaces with
  measurable entropy, tension, color entropy, and braid simplification.
- Braid entropy is low; rope tension is low. That is useful for routing and
  candidate sorting.

Acceleration path:

- Use braid/rope as a candidate topology generator, not as a final codec.
- Feed braid/rope metrics into MassNumber:

```text
admissible = reversible structure preserved or search work reduced
residual = roundtrip risk + expansion cost + tension
boundary = Hutter-safe threshold or discovery-only threshold
```

Promotion gate:

- A braid/rope chain cannot be Hutter-claim-safe until it round-trips and beats
  a baseline after overhead.
- Until then, archive as route-prior / discovery geometry.

## Acceleration Candidate 5: 0D and nD PIST

Surface:

- `pist_scalar_mass`
- `pist_scalar_tension`
- `pist_0d_degenerate`
- `pist_scalar_phase`
- `pist_nd_cartesian`
- `pist_nd_radial`
- `pist_nd_bundle`

Observed demo results:

```text
pist_scalar_phase    ratio=1.000, entropy=0.146
pist_0d_degenerate   ratio=1.000, entropy=2.052, irreversible
pist_nd_radial       9 bytes, ratio=5.333, entropy=2.419
pist_nd_cartesian    99 bytes, ratio=0.485
pist_nd_bundle       146 bytes, ratio=0.329
```

Interpretation:

- 0D scalar/phase surfaces are excellent gates and summaries.
- They are not codecs; the file correctly marks several as lossy or
  irreversible.
- `pist_nd_radial` is the most dangerous result: it looks like a major
  compression win, but its decode reconstructs repeated offsets, not the
  original bytes. Treat it as lossy unless a separate residual stream is added.

Acceleration path:

- Use 0D phase/mass as fast prefilters.
- Use nD radial as a sketch compressor / route candidate, then attach residual
  receipts.
- Use nD cartesian as the lossless baseline for dimensional PIST, despite
  expansion.

Promotion gate:

```text
0D phase -> CacheSieve / route class
nD radial -> Underverse or residual stream required
nD cartesian -> lossless reference path
```

## Acceleration Candidate 6: Display/Audio/FPGA Signal Architecture

Surface:

- `6-Documentation/docs/specs/UNIFIED_SIGNAL_ARCHITECTURE.md`
- `6-Documentation/docs/specs/DP_TEXEL_8K_ENCODING_SPEC.md`
- `5-Applications/scripts/hdmi_computational_shell.py`

What accelerates:

- The signal architecture gives a coherent hardware story:

```text
DP/HDMI texel stream -> audio/waveprobe side channel -> FPGA sampled witness
```

- The DP spec already admits a key reality: verifying every 8K texel on a
  27 MHz FPGA is not feasible; selected witness anchors are the sane route.

Promotion gate:

- Replace "verify all texels" language with "sampled anchor verification" in
  claims.
- Tie sampled anchors to route damage scoring and Underverse receipts.

Acceleration path:

```text
GPU emits many candidates
FPGA samples anchor loci
Lean/Underverse records failed closure
search graph links witness paths
```

## Formal Blockers

### `Semantics.Core.MassNumber`

Build fails. Main causes:

- `Q16_16.ofNat` proof assumes no UInt32 wraparound.
- Constants such as `Q16_16.epsilon_toInt_pos`, `Q16_16.zero_toInt`, and
  `Q16_16.zero_mul` are referenced but not present under those names.
- `MassLe` returns `Bool`, so theorem rewrites need to handle `decide`.
- `massLe_threshold_max_guardrail` currently proves a zero-threshold path, not
  a max-threshold property.

Acceleration implication:

- The conceptual fix is good: MassNumber theorems should require
  well-formedness instead of pretending arbitrary Q16_16 values are
  nonnegative.
- The Lean surface needs a smaller repair pass before it can guard anything.

### `Semantics.MassNumberMetricClosure`

Build fails. Main causes:

- Prop/Bool mismatch in `edgeAdmissible`.
- Path-reversal proof has unresolved induction goals and identifier drift.
- It references `Score.add_assoc`, but that theorem does not exist.
- Example `CandidateRecord` construction is out of date: fields like `name` and
  `mass` are no longer valid.
- There is at least one `sorry` warning in the path-reversal area.

Acceleration implication:

- The design is right: shortest-path closure + disconnected-component
  Underverse receipts.
- The file should be split into a tiny compiling graph kernel before trying to
  prove pseudometric closure.

## Recommended Next Moves

1. Make `UnderversePacket` warning-free and use it immediately as the failure
   ledger.
2. Add a small Python benchmark harness around shifters:
   - ratio
   - entropy
   - roundtrip bool
   - residual bytes required
   - MassNumber-ready packet
3. Classify every shifter output into:
   - Hutter-safe candidate
   - discovery-only route
   - lossy sketch
   - quarantine / Underverse packet
4. Repair `MassNumber.lean` before expanding `MassNumberMetricClosure.lean`.
5. Build the internal semantic graph with typed edges before adding a visual
   UI.

## High-Value Thesis

The weird additions do not currently say "new compressor solved." They say
something more useful:

```text
The repo is converging on a candidate-generation and receipt-verification
machine.
```

That can accelerate Hutter work if the rule stays strict:

```text
no roundtrip -> no codec claim
no receipt -> no promotion
no provenance -> no citation
no build -> no formal claim
```

