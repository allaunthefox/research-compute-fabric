# 0-Core-Formalism

**Purpose:** Formal foundations for the entire Research Stack — Lean modules, bind primitive, Triumvirate consensus, core source.

**No external dependencies.** All other layers depend on this.

## Contents (Target)

| Source | Destination |
|--------|-------------|
| `0-Core-Formalism/lean/Semantics/` | `0-Core-Formalism/lean/Semantics/` |
| `core/` | `0-Core-Formalism/core/` |

## Concepts

- **bind** — State → (State → Action) → State
- **TriumvirateClock** — ternary consensus (ADD/PAUSE/SUBTRACT)
- **Builder/Judge/Warden** — roles mapped to hardware registers
- **OTOM** — Ordered Transformation & Orchestration Model

## Build

```bash
cd "0-Core-Formalism"
lake build
```
