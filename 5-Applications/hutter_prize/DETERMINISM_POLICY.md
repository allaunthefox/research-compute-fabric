# Determinism Policy

Public-facing builders should be deterministic unless they explicitly declare
otherwise.

For this repo, that means:

- rerunning the same public builder with the same inputs should produce the same bytes
- nonessential timestamps should be excluded from public manifests
- nonessential absolute paths should be excluded from public manifests
- deterministic fingerprints should be preferred over fresh run markers

## Why This Matters

This project leans heavily on one-way artifacts:

- hashes
- manifests
- review packets
- public prep bundles

If those drift without a good reason, trust drops fast.

## Current Scope

This policy currently applies most directly to:

- `scripts/build_review_packet.py`
- `scripts/prepare_public_artifact.py`

Those builders are expected to be byte-stable on rerun for the same inputs.

## Verification Tool

The reference verifier is:

- `scripts/verify_builder_determinism.py`

That script rebuilds a bundle twice in separate temporary directories and checks
whether the relative output files hash to the same values.

## Explicit Exceptions

Not every artifact in the repo is expected to be deterministic in this way.

Benchmark and experiment outputs may legitimately contain:

- timing measurements
- run stamps
- observation-time receipts

Those are observational artifacts, not stable publication bundles.

## Working Rule

If a builder is meant for public handoff or archival packaging, assume it should be
deterministic until proven otherwise.
