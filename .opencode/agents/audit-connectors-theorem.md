---
description: Audit the temporarily removed theorem in Connectors.lean. Use ONLY when asked to clean up Connectors.lean or evaluate quarantined proofs.
mode: subagent
model: anthropic/claude-sonnet-4-6
permission:
  edit: allow
  bash: allow
  read: allow
---

# Audit Connectors.lean

## Context

`Semantics/Connectors.lean:94` has:
```
-- TODO(lean-port): proof required - theorem temporarily removed
```

A theorem was removed and marked for later restoration. Determine whether it should be restored, replaced, or the comment removed.

## What to do

1. Read `Semantics/Connectors.lean` around line 90-100.
2. Read git history to find the removed theorem:
   ```bash
   git log -p --follow -S "TODO(lean-port): proof required" -- Semantics/Connectors.lean
   ```
3. Determine:
   - Was the theorem part of a larger proof chain that's now broken?
   - Does the theorem have any remaining callers or references?
   - Is the theorem still relevant given the current state of the module?
4. Either restore the theorem with a complete proof, or add a note that it was evaluated and the TODO is stale, then remove the TODO.
5. Run `lake build Compiler` to verify.
