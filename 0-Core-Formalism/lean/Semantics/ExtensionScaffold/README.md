# ExtensionScaffold

**Pattern**: Research extensions that extend the core `Semantics` library.

**Rule**: Core (`Semantics/`) remains tight. Extensions live here until proven essential.

## Derivation Pipeline

```
Core (Semantics/)
├── Invariants          (surfaceInvariant, localExpansionInvariant)
├── Admissibility       (CausalStatus.admissible, SensorDetection.admissible)
└── Preservation/Collapse  (collapseProne, .collapsed variants across domains)

    ↓ (extends)

Extension Kernel
└── Temporal/TemporalVariantIndex.lean  (generic TVI framework — testing branch)

    ↓ (adapts)

Extension Adapters
└── Temporal/SpikeSync.lean             (neural spike network)
└── (planned: history/decoherence)

    ↗ (may promote if passes all 3 criteria)

Core (future — if irreducible, cross-domain, stable)
```

## Purpose

This scaffold holds:
- **Special regimes** — Unusual physical conditions not yet canonical
- **Experimental metaphors** — Productive analogies being tested
- **Domain-specific constructions** — Vertical applications
- **Candidate metrics** — Measures not yet fully stabilized
- **Rich examples** — Patterns that may later be promoted into core

## Structure

```
ExtensionScaffold/
├── Thermodynamics/         # Energy/entropy extensions
│   └── ThroatPhysics.lean  # Metastable wormhole maintenance
├── Topology/               # Geometric structure extensions
│   └── PlasmaTopology.lean # Regime classification for plasmas
├── Temporal/               # Time-variant systems
├── Decoherence/            # Branching histories alignment
├── Transmission/           # Horizon/boundary information flow
├── SemanticPrimes/         # Prime-based semantic encoding
├── Narrative/              # Graph OS ancestry structures
└── Dynamics/               # Special kernels, phonons, repair
```

## Promotion Criteria

An extension moves to core only when it passes **all three**:

### 1. Irreducibility
You cannot explain the rest of the model without it.

### 2. Cross-domain reuse
It appears in multiple unrelated cases, not just one favorite example.

### 3. Stability under revision
It survives multiple rewrites without changing its meaning much.

---
**Old criteria** (deprecated): Required by `bind`, hardware target needs it, cost function depends on it, build fails without it.

## Current Extensions

| Extension | Category | Status | TVI Kernel |
|-----------|----------|--------|------------|
| `Temporal/TemporalVariantIndex.lean` | Time-variant | **Base kernel** — generic TVI framework | — |
| `Decoherence/HistoryTvi.lean` | Branching histories | **Active** — decoherent history TVI adapter | ✅ Uses kernel |
| `Temporal/SpikeSync.lean` | Time-variant | **Active** — neural spike network TVI adapter | ✅ Uses kernel |
| `Thermodynamics/ThroatPhysics.lean` | Special regimes | Reference — metastable wormhole thermodynamics | ⏸️ Standalone |
| `Topology/PlasmaTopology.lean` | Domain-specific | Reference — plasma regime classification | ⏸️ Standalone |

## Architecture Boundaries

### ENE (Endless Node Edges) — What It Is NOT

To keep the architecture clean, **ENE does NOT**:

| Compute | Store |
|---------|-------|
| ❌ Compute TVI | ✅ Store TVI results |
| ❌ Perform spike syncing | ✅ Record sync outcomes |
| ❌ Perform temporal alignment | ✅ Document alignment |
| ❌ Decide system actions (PTOS) | ✅ Witness PTOS decisions |
| ❌ Act as driver | ✅ Maintain audit trail |

**ENE is the record, not the computation.**

### Stack Layering

```
┌─────────────────┐
│  Driver Layer   │  ExtensionScaffold/Temporal/SpikeSync.lean
│  (computes TVI, │  ExtensionScaffold/Decoherence/HistoryTvi.lean
│   sync, etc.)   │
└────────┬────────┘
         ↓
┌─────────────────┐
│      PTOS       │  Semantics/Prohibited.lean
│  (decides what  │  Semantics/Constitution.lean
│   to do)        │
└────────┬────────┘
         ↓
┌─────────────────┐
│      ENE        │  Semantics/Graph.lean
│  (records what  │  Semantics/Witness.lean
│   is true and   │  Semantics/Evolution.lean
│   how)          │
└─────────────────┘
```

### One-Line Definition

> **ENE is a typed, witness-backed semantic graph with enforced admissibility, lawful traversal, and fully auditable evolution.**

## Verification Results

**Core build:** 43 jobs, zero warnings

**TVI Kernel test:** Two independent domains (history + spikes) successfully:
- Import `TemporalVariantIndex` kernel
- Map domain objects to `TemporalProfile`
- Compute `TviVector` via `fromProfiles`
- Check admissibility via `admissible`
- Expose same 4 failure axes: timing, rate, pattern, collapse

**Kernel adapters:**
- `HistoryTvi.lean`: 2 theorems + 4 #eval witnesses
- `SpikeSync.lean`: 1 theorem + 4 #eval witnesses

## Planned Categories

| Category | Scope | Candidate Content |
|----------|-------|-------------------|
| `Temporal/` | Time-variant subclass systems | Temporal variants, clock domains |
| `Decoherence/` | Branching histories | Many-worlds alignment, collapse models |
| `Transmission/` | Horizon information flow | Boundary transmission, holographic principles |
| `SemanticPrimes/` | Prime-based encoding | Semantic primes, invariant roots |
| `Narrative/` | Graph OS structures | ENE layer, story graphs, ancestry |
| `Dynamics/` | Repair and phonons | Special kernels, phonon structures, repair dynamics |

## Rejected Approaches

| File | Reason | Location |
|------|--------|----------|
| `HumanManifold.lean` | Fatally flawed approach | `/data/archive/HumanManifold.lean.REJECTED_FATALLY_FLAWED` |

## Usage

Extensions are **not** imported by `Semantics.lean`. They may:
- Import from core
- Be imported by other extensions
- Be promoted individually

## Build

Extensions are **not** built by default:

```bash
# Build core only (default)
lake build

# Build with extensions (when needed)
lake build +ExtensionScaffold.Thermodynamics.ThroatPhysics
```

---
**Note**: Files here are preserved for reference. Promotion requires human sign-off per `AGENTS.md`.
