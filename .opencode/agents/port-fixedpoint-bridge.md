---
description: Rewrite FixedPointBridge.lean conversions using pure integer arithmetic (remove Float dependency). Use ONLY when asked to port FixedPointBridge or eliminate Float from compute paths.
mode: subagent
model: anthropic/claude-sonnet-4-6
permission:
  edit: allow
  bash: allow
  read: allow
---

# Port FixedPointBridge

## Context

`Semantics/FixedPointBridge.lean:13` has:
```
TODO(lean-port): Rewrite conversions using pure integer arithmetic:
  - toFloat / fromFloat are used only at the external boundary
  - Internal compute should use ofNat / ofRatio / ofInt
```

Per root AGENTS.md: "Float (ofFloat) is forbidden in compute paths. Q16_16.ofNat and Q16_16.ofRatio are the canonical constructors."

## What to do

1. Read `Semantics/FixedPointBridge.lean` fully.
2. Identify every call to `ofFloat`, `toFloat`, or any Float-dependent conversion.
3. For each call, determine if it's:
   - An external boundary (JSON parsing, sensor input) → mark with a comment noting it's boundary-only.
   - An internal compute path → rewrite using `Q16_16.ofNat` / `Q16_16.ofRatio` / `Q16_16.ofInt`.
4. After rewriting, remove the `TODO(lean-port)` marker.
5. Run `lake build Compiler` and `lake build` to verify.
6. Run `grep -rn 'ofFloat\|toFloat' Semantics/ --include='*.lean' | grep -v lake-packages` to check for remaining Float usage.

## Constraints

- `ofFloat` is PERMITTED at the external boundary (JSON parsing, sensor input) but must be immediately bracketed with a comment.
- `ofFloat` is FORBIDDEN in internal compute paths.
- Do NOT change public API signatures unless necessary.
