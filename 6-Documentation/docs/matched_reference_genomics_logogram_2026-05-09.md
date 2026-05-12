# Matched-Reference Genomics For Logogram Replay

**Date:** 2026-05-09

**Status:** `DESIGN_PRIOR_RECEIPT`

**Claim boundary:** this note uses matched-reference genomics as a design prior
for logogram replay and static decompressor surfaces. It does not claim a
biological codec implementation, clinical utility, or compression-ratio win.

## Source

Nature Communications published:

```text
Cell line-matched reference enables high-precision functional genomics
DOI: 10.1038/s41467-025-66155-3
Published: 2025-11-20
```

The paper's core result is that sequencing and functional-genomics analysis
improve when reads from a laboratory cell line are mapped against a reference
assembly from the same cell line, especially in divergent, repetitive,
haplotype-specific regions such as centromeres.

Useful source facts:

- A generic reference genome can introduce reference bias.
- The RPE-1 matched diploid reference improves DNA/RNA read mapping.
- The gain is strongest in divergent centromeric and pericentromeric loci.
- Haplotype-specific centromere organization matters for guide design,
  epigenetic peak calling, and kinetochore localization.

Source URL:

```text
https://www.nature.com/articles/s41467-025-66155-3
```

## Stack Translation

The useful abstraction is:

```text
payload should be decoded against the matching reference basis
```

For the Research Stack:

```text
generic reference      -> generic grammar / generic dictionary / generic route prior
cell-line reference    -> matched logogram basis / matched dictionary / matched route prior
reference bias         -> replay bias / residual inflation / false mismatch
haplotype-specificity  -> branch-specific receipt basis
centromere divergence  -> high-repetition, high-ambiguity logogram region
```

This gives a clean rule for the static decompressor:

```text
do not unspool against a universal reference if the payload declares
a more specific matched basis
```

## Isogenomic Replay Primitive

Define an `isogenomic replay basis` as a reference surface whose identity is
matched to the payload's declared substrate family.

Minimum fields:

```yaml
matched_reference_basis:
  basis_id:
  substrate_family:
  alphabet:
  haplotype_or_branch:
  source_hash:
  payload_hash:
  reference_hash:
  mismatch_policy:
  residual_policy:
```

Replay gate:

```text
if payload declares matched_reference_basis and basis is missing:
  HOLD_MISSING_MATCHED_REFERENCE
elif reference_hash mismatch:
  QUARANTINE_REFERENCE_BIAS
elif replay residual <= declared bound:
  ADMIT_MATCHED_REPLAY
else:
  HOLD_RESIDUAL_INFLATION
```

## Why This Helps The Decompressor

A static decompressor is intentionally dumb: it should not improvise a better
world model at decode time. The compressor must therefore emit enough reference
identity for the decompressor to replay the intended path.

Matched-reference genomics supports that design:

```text
the same observed symbols can map differently under a generic versus matched
reference, and the mismatch is most dangerous in repetitive divergent regions
```

For logogram / Hachimoji / OISC surfaces, those risky regions are:

- repeated symbols
- dense alphabets
- folded or mirrored branches
- branch-local dictionaries
- whitespace-zero grammar boundaries
- highly reused AMMR leaves

So the decompressor should prefer:

```text
payload + matched reference hash + residual
```

over:

```text
payload + generic global dictionary
```

## Relation To Existing Surfaces

This design prior attaches to:

- `6-Documentation/docs/specs/OMINDIRECTION_LOGOGRAM_DESIGN_AND_COMPILER.md`
- `4-Infrastructure/infra/embedded_surface/omni_lut/sequence_surface_lut.py`
- `5-Applications/compression-core/src/oisc.rs`
- `shared-data/data/stack_solidification/rust_oisc_decompressor_target_receipt.json`

It also sharpens the earlier hachimoji / sequence-surface split:

```text
Q4-ROISC       -> smaller carrier, simpler static unspooling
Hachimoji/BF   -> larger alphabet, richer command surface
matched basis  -> required whenever richer alphabets create replay ambiguity
```

## Decision

```text
ADMIT_AS_DESIGN_PRIOR
HOLD_FOR_IMPLEMENTATION
```

## Next Work

1. Add a `reference_hash` and `basis_id` field to the Rust OISC receipt shape.
2. Add a negative fixture where the payload decodes under a generic basis but
   fails under the declared matched basis.
3. Add a hachimoji/logogram replay fixture where branch-specific basis metadata
   lowers residual size without changing byte-exact output.
4. Keep any compression-efficiency claim HOLD until fixture and corpus receipts
   exist.
