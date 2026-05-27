---
description: Resolve the "implement or remove" TODO(lean-port) in CanonSerialization.lean. Use ONLY when asked to clean up CanonSerialization or resolve ambiguous TODO markers.
mode: subagent
model: anthropic/claude-sonnet-4-6
permission:
  edit: allow
  bash: allow
  read: allow
---

# Resolve CanonSerialization TODO

## Context

`Semantics/CanonSerialization.lean` has two `TODO(lean-port)` markers:

- Line 265: `TODO(lean-port): Implement canonicalize function or remove this theorem.`
- Line 327: `TODO(lean-port): Re-enable when proof is completed.`

## What to do

1. Read `Semantics/CanonSerialization.lean` fully.
2. For line 265: Determine whether `canonicalize` is needed or the theorem can be removed.
   - Check if any module imports or references `CanonSerialization` symbols.
   - If no callers exist and the function is not part of an active pipeline, remove the theorem and the TODO.
3. For line 327: Check if the proof blocker has been resolved. If not, add a specific description of what's needed.
4. Run `lake build Compiler` to verify no build breaks.
5. Run `lake build` to verify full workspace.
