# Hutter Prize Lab

This workspace is a small, reproducible harness for compression experiments.

It does not claim to implement an official Hutter Prize submission flow yet.
It gives us a clean place to:

- run compressors against a fixed input
- measure compressed size and wall-clock time
- verify round-trip decompression when available
- save machine-readable results for later comparison

If you want the calmest entry point first, read `PLAIN_LANGUAGE_OVERVIEW.md` before the
rest of the repo.
If you are preparing a first outside handoff, use `REVIEW_PACKET_CHECKLIST.md`.

## Layout

- `PLAIN_LANGUAGE_OVERVIEW.md` - the shortest, calmest explanation of what this repo currently is
- `ARCHITECTURE.md` - current search / execution / audit split for the codec platform
- `ARCHIVAL_PUBLICATION_STRATEGY.md` - end-state plan for free public archival release
- `AUDITABILITY_IP_BOUNDARY.md` - disclosure ladder for what can be published now versus later
- `COMPRESSION_FIRST_APPLICATIONS.md` - why compression alone is already a useful and calmer first surface
- `DERIVATION_SPEC.md` - deterministic input-to-program derivation baseline
- `DETERMINISM_POLICY.md` - rules for byte-stable public builders and where timestamps are not allowed
- `EXECUTION_SUBSTRATE_STRATEGY.md` - multi-substrate plan for proving the path is not overfit to one executor
- `EXECUTION_TRUST_MODEL.md` - role split for physical execution, private search, and hosted witnessing
- `PUBLIC_SMOOTHING.md` - house-voice and metadata-smoothing policy for public artifacts
- `REVIEW_PACKET_CHECKLIST.md` - the smallest useful outside-review packet and the questions it should support
- `RELEASE_GATING.md` - staged release tiers from private work through public safe surface
- `TERNARY_VM_SPEC.md` - minimal deterministic VM contract for subregister-bounded execution
- `Containerfile` - minimal container substrate
- `components.lock.json` - SHA-256 lock manifest for tracked workspace files
- `scripts/benchmark.py` - generic compression benchmark harness
- `scripts/build_review_packet.py` - copies the default outside-review packet into one directory with a hash manifest
- `scripts/emit_build_manifest.py` - emits a machine-readable manifest of the build substrate
- `scripts/derive_trinary_program.py` - derives a deterministic VM program from an input file
- `scripts/trinary_vm.py` - tiny reference interpreter for the minimal trinary VM
- `scripts/ab_test.py` - runs two benchmark variants against the same input and emits a comparison report
- `scripts/run_matrix.py` - runs a config-defined experiment matrix and ranks variants
- `scripts/prepare_public_artifact.py` - bundles smoothing, receipts, and hashes for a public-facing artifact
- `scripts/validate_derivation.py` - checks that a claimed program matches the declared derivation rules
- `scripts/universal_smoother.py` - smooths public-facing text or JSON toward a low-distinctiveness house voice
- `scripts/verify_builder_determinism.py` - reruns public builders and fails if their output bytes drift
- `scripts/verify_components.py` - verifies tracked files against the lock manifest
- `experiments/` - reusable experiment definition files for A/B and multi-variant runs
- `results/` - JSON output from experiment runs

## Quick Start

Example with `xz`:

```bash
python3 scripts/benchmark.py \
  --input path/to/input.txt \
  --compress 'xz -9 -c {input} > {output}' \
  --decompress 'xz -d -c {input} > {output}' \
  --label xz-9
```

Example with a custom binary:

```bash
python3 scripts/benchmark.py \
  --input path/to/input.txt \
  --compress './mycodec encode {input} {output}' \
  --decompress './mycodec decode {input} {output}' \
  --label mycodec-v1
```

To include the deterministic baseline derivation artifacts in the same run:

```bash
python3 scripts/benchmark.py \
  --input path/to/input.txt \
  --compress 'xz -9 -c {input} > {output}' \
  --decompress 'xz -d -c {input} > {output}' \
  --label xz-9 \
  --derive-baseline
```

To bind a run to the single-lane execution contract and record the substrate:

```bash
python3 scripts/benchmark.py \
  --input path/to/input.txt \
  --compress 'xz -9 -c {input} > {output}' \
  --decompress 'xz -d -c {input} > {output}' \
  --label xz-9 \
  --single-lane \
  --execution-substrate risc64-emulated \
  --cpu-affinity 0
```

This clamps common thread-count environment variables to `1`, records the requested
execution substrate, and records any requested CPU-affinity wrapper in the run
artifacts.

The command templates must include:

- `{input}` for the source file
- `{output}` for the produced file

## A/B Comparison

To compare two variants on the same input:

```bash
python3 scripts/ab_test.py \
  --input path/to/input.txt \
  --label-a xz-6 \
  --compress-a 'xz -6 -c {input} > {output}' \
  --decompress-a 'xz -d -c {input} > {output}' \
  --label-b xz-9 \
  --compress-b 'xz -9 -c {input} > {output}' \
  --decompress-b 'xz -d -c {input} > {output}'
```

This writes the individual run artifacts plus a comparison JSON naming the smaller and
faster variant.
The same `--single-lane`, `--execution-substrate`, `--cpu-affinity`, and
`--thread-cap` flags may also be passed through to both variants.

## Config-Driven Matrix Runs

To run a named experiment definition:

```bash
python3 scripts/run_matrix.py \
  --config experiments/common_codecs_smoke.json \
  --input path/to/input.txt
```

That writes the per-variant bundles plus a matrix summary JSON ranking variants by size
and then speed.
The same execution-lane flags may be passed to matrix runs, and each variant summary
will retain the recorded substrate label.

## Deterministic Derivation

To derive a deterministic VM program from an input file:

```bash
python3 scripts/derive_trinary_program.py \
  --input path/to/input.bin \
  --output out/program.json
python3 scripts/trinary_vm.py --program out/program.json
python3 scripts/validate_derivation.py \
  --input path/to/input.bin \
  --program out/program.json \
  --report out/validation.json
```

The current derivation contract is documented in `DERIVATION_SPEC.md`.
That contract is intentionally minimalist so the baseline can be implemented and
reproduced in many environments, not just this repo's reference setup.
The validator gives reviewers a direct way to check whether a claimed derived program
actually matches the public rule set.
It can also emit a small JSON receipt for archival and review.

## Integrity Check

Before building or publishing, verify the tracked files:

```bash
python3 scripts/verify_components.py \
  --lock components.lock.json \
  --root .
```

The container build also runs this verification step so tracked files must match their
recorded SHA-256 values.

## Public Smoothing

To smooth a public-facing text artifact:

```bash
python3 scripts/universal_smoother.py \
  --input docs/draft.md \
  --output out/draft.public.md \
  --report out/draft.public.smoothing.json
```

To smooth JSON metadata into a stable low-distinctiveness form:

```bash
python3 scripts/universal_smoother.py \
  --input out/metadata.json \
  --output out/metadata.public.json \
  --mode json \
  --report out/metadata.public.smoothing.json
```

This is a stylometric and metadata-reduction step, not a claim of perfect anonymity.
The optional receipt gives a small machine-readable before-and-after record of the
reduction pass.

To prepare a full public-facing artifact bundle in one step:

```bash
python3 scripts/prepare_public_artifact.py \
  --input docs/draft.md \
  --out-dir out/public_bundle \
  --label draft
```

That writes:

- a smoothed public artifact
- a smoothing receipt
- a small manifest with SHA-256 hashes for both

## Review Packet Builder

To build the default first-review packet in one directory:

```bash
python3 scripts/build_review_packet.py \
  --root . \
  --out-dir out/review_packet
```

That writes:

- `out/review_packet/packet/` with the copied default review docs
- `out/review_packet/review_packet.manifest.json` with SHA-256 hashes and the default review questions

To verify that a public-facing builder is byte-stable across reruns:

```bash
python3 scripts/verify_builder_determinism.py \
  --builder review-packet \
  --root .
```

For the public artifact bundle path:

```bash
python3 scripts/verify_builder_determinism.py \
  --builder public-artifact \
  --input docs/draft.md \
  --label draft
```

## Reproducibility Posture

The current environment aims to be boring and auditable:

- base image pinned by digest
- minimal package set
- no `pip` layer
- no `git` requirement inside the image
- tracked workspace files verified by SHA-256 before the image is accepted
- build manifest emitted inside the image for later audit

The build manifest is written to:

- `/opt/hutter/build-manifest.json`

It records package inventory, key tool versions, and tracked file hashes as observed in
the built image.

## Architecture Direction

The current architecture direction is captured in `ARCHITECTURE.md`.

The short version is:

- private search is allowed
- deterministic execution is required
- audit should attach to the boring executable path, not the secret sauce
- each operation should have a subregister boundary so it can be replayed and verified

The current minimal execution contract is captured in `TERNARY_VM_SPEC.md`, with a
reference interpreter in `scripts/trinary_vm.py`.
The current input-to-program derivation baseline is captured in `DERIVATION_SPEC.md`,
with a reference implementation in `scripts/derive_trinary_program.py`.
The baseline is intentionally minimal so the software remains portable and
reimplementable outside this exact environment.
The intended multi-substrate execution strategy is captured in
`EXECUTION_SUBSTRATE_STRATEGY.md`.
The infrastructure role split for physical runs, private search, and hosted witnessing
is captured in `EXECUTION_TRUST_MODEL.md`.
Part of that strategy is pragmatic: legacy-core targets such as an SNES-family CPU path
provide an additional physical validation surface for reviewers who want something more
concrete than a modern emulator stack alone.
The publish-now versus hold-back boundary is captured in `AUDITABILITY_IP_BOUNDARY.md`.
The staged rollout logic is captured in `RELEASE_GATING.md`.
The standalone value of the compression layer is captured in
`COMPRESSION_FIRST_APPLICATIONS.md`.
The intended end-state public record is described in
`ARCHIVAL_PUBLICATION_STRATEGY.md`.

## Attribution Note

LLM assistance may be used in this workspace, but the human operator remains the
decision-maker for synthesis, boundary-setting, and release posture.
Part of that assistance may include helping bridge operator-side numeracy constraints in
number-dense work.
This should be read as an accessibility support measure, not as a laziness shortcut.
It should not prevent honest critique of the work itself.

## Hard Limits

This is strong, but not mathematically perfect.

What is pinned today:

- the base image digest
- the tracked project files in `components.lock.json`

What is still only partially pinned:

- Alpine package resolution inside `apk add`

If we want the environment to become even harder to impeach, the next step is to vendor
or explicitly fetch every non-base artifact by URL plus SHA-256, rather than trusting
package-manager resolution alone.

## Notes

- If no decompressor is provided, the harness will still report size and timing, but it
  will mark round-trip verification as skipped.
- Results are written into `results/` with timestamps so we can compare runs without
  losing history.
- With `--derive-baseline`, the benchmark also writes a derived program and validation
  receipt alongside the main result JSON.
- Each benchmark run now also writes a small manifest JSON linking the run's artifacts.
- Each benchmark run now also records an execution-contract receipt describing the
  declared lane, substrate, and thread-clamp settings.
- `ab_test.py` writes a comparison JSON on top of the two grouped run bundles.
- `run_matrix.py` writes a matrix summary on top of grouped per-variant runs.
- This is a lab harness, not an official score reporter.
- The Alpine base image is pinned by digest in `Containerfile`. Any future fetched
  artifacts should also be pinned and checksum-verified before they are trusted.
