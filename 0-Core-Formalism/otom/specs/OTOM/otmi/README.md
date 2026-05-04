# otmi/ - Ordered Transformation Model Interface

Core interface specifications for OTOM framework transformation protocols.

## Contents

- `protocol.lean` - Transformation protocol definitions
- `boundary.lean` - Domain boundary specifications  
- `convergence.lean` - Convergence criteria and theorems

## Design Principles

1. **Neutral Terminology**: All core logic uses technical terms only
2. **Q16.16 Fixed-Point**: Hardware-native numerical precision
3. **Theorem Witnesses**: Every def has #eval or theorem
4. **Minimal Dependencies**: No external crates/packages without approval

## Connection to Research Stack

OTMI specs bridge formal Lean modules with practical orchestration:
- `Semantics.lean` 88 modules → OTMI interface layer
- `SubagentOrchestrator` → OTMI implementation guide
