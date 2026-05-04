# Public Smoothing

This note defines the public-facing smoothing posture for text and metadata that leave
the private workspace.

The aim is not deception.
The aim is to reduce unnecessary stylometric and metadata distinctiveness in public
artifacts.

In plain terms:

- make the language boring
- make the metadata boring
- make the formatting boring
- do not let personal fingerprints ride along when they are not needed for audit

## Why This Exists

Authorial fingerprinting does not depend on vocabulary alone.
It can also emerge through:

- spacing habits
- punctuation habits
- line-break rhythm
- casing quirks
- repeated idioms
- document-structure preferences
- metadata and timestamp patterns
- semantic tilt and preferred framing

The purpose of smoothing is to reduce that total signal before public release.

## Smoothing Target

The desired outcome is a low-distinctiveness house voice.

That means:

- neutral wording
- normalized spacing
- normalized punctuation
- consistent list style
- minimal expressive flourish
- stable metadata formatting

Public artifacts should read as disciplined and legible, not intensely personal.

## Scope

The smoothing pass is intended for:

- review packets
- public documentation
- challenge materials
- archival metadata
- any text that does not require raw private voice for evidentiary reasons

It should not silently rewrite artifacts whose original wording is itself the thing
being audited.

## Current Reference Tool

The current reference tool is `scripts/universal_smoother.py`.

The first implementation is intentionally modest.
It focuses on reducing obvious stylometric noise and normalizing JSON metadata shape.
It can also emit a machine-readable smoothing receipt so the before-and-after surface is
not purely subjective.

It is not a claim of perfect anonymity.
It is a precautionary reduction step.

For routine release work, the preferred wrapper is `scripts/prepare_public_artifact.py`.
That helper runs the smoother, writes a smoothing receipt, and emits a small manifest
with hashes so the bundle is easier to hand off or archive.

## House Rules

When a public artifact is smoothed, prefer:

- ASCII punctuation where reasonable
- single spaces between words
- no trailing whitespace
- bounded blank-line use
- sorted JSON keys
- stable indentation
- flattened repeated punctuation
- plain wording over signature phrasing

## Smoothing Receipt

Where practical, smoothing should emit a receipt.

That receipt may include:

- the smoothing mode
- basic before-and-after formatting metrics
- counts of repeated punctuation or spacing noise
- metadata normalization indicators

The point is not to claim a complete stylometric proof.
It is to leave behind a small factual record that a reduction pass actually happened.

## Audit Constraint

Smoothing must not undermine the public audit surface.

That means:

- hashes and manifests stay exact where exactness matters
- declared schemas stay intact
- derivation rules do not get blurred into vagueness
- validation receipts remain machine-readable

The goal is to remove unnecessary personal signal, not to weaken reproducibility.
