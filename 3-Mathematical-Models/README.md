# 3-Mathematical-Models

**Purpose:** Central equation registry, proof tracking, and mathematical substrate index.

**Depends on:** `0-Core-Formalism`, `2-Search-Space`

## Contents (Target)

| Source | Destination |
|--------|-------------|
| `data/mathlib_database/` | `3-Mathematical-Models/database/` |
| `data/equation_extraction_*` | `3-Mathematical-Models/equations_*` |

## Registry Format

TSV-style with columns: `Model_Name | Family | Equation | Variables | Purpose | Location | Implemented | Status | Cross_Refs | Domain_Type | Bind_Class`

## Rule

**All new mathematical models MUST be added to the registry before creating separate documentation.**
