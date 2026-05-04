# Deterministic Derivation Spec

This document defines the current minimum derivation path from an input file to a
trinary VM program.

It is intentionally simple.
The goal is not to be the final codec.
The goal is to prove that we can derive a replayable executable artifact from the input
using declared rules and no hidden choices.

## Goal

The derivation step should be:

- deterministic
- input-driven
- reproducible
- inspectable
- implementable anywhere

Two parties given the same input and the same derivation rules should produce the same
program document.

## Minimalist Portability Note

The software should be implementable anywhere the basic rules can be executed.

That means the reference path should prefer:

- simple data formats
- minimal dependencies
- obvious arithmetic rules
- small state surfaces

Minimalism is part of the reproducibility strategy.
The aim is not to prove the software only works in one privileged environment, but to
show that the same declared logic can be reimplemented across many environments without
changing the underlying derivation contract.

## Current Mapping

The current derivation path works byte-by-byte.

For each byte:

1. Split the byte into six base-3 digits.
2. Map each base-3 digit into one trinary value:
   - `0 -> -1`
   - `1 -> 0`
   - `2 -> +1`
3. Emit `SET` operations into a target subregister for those six trits.
4. Emit one `SHIFT right` after each encoded byte to make byte boundaries visible in the
   trace and avoid a completely static write pattern.

This produces a deterministic program over a fixed-width trinary subregister.

## Current Program Shape

The derived JSON payload includes:

- metadata about the input
- the input SHA-256
- one target subregister named `alpha`
- one helper subregister named `beta`
- a derived instruction stream

The helper subregister is currently inert.
It exists to keep the state shape stable as we experiment with richer derivation rules.

## Why This Matters

This spec gives us a public answer to:

- where did the program come from
- can someone else derive the same program
- did the executable path depend on hidden operator choices
- can the claimed program be validated against the declared derivation rules

That is the first step toward making the math, rather than the operator, the stable
reference point.

## Validation Path

The baseline derivation is intended to be self-checking.

Given:

- an input file
- a claimed derived program

a validator should be able to recompute the baseline payload and confirm whether the
claimed program matches the declared rule set.

That means the baseline is not only reproducible, but independently checkable.

The validator may also emit a machine-readable receipt containing:

- input hash
- program hash
- validation status
- any mismatch reasons

This gives experiments a small audit artifact that can be archived alongside the
derived program itself.

## Scope Limit

This is a baseline derivation contract, not a compression claim.

It proves determinism and auditability first.
Better transforms can be layered on later, but they should preserve the same public
discipline:

- declared rules
- stable derivation
- replayable outputs
