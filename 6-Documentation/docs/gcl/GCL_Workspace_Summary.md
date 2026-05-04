# GCL Workspace Summary

**Date**: 2026-05-01  
**Status**: Active Implementation  
**Version**: 3.0-Delta-Q0_64

---

## What Was Built

### 1. Three-Layer Type System (Lean)

**Location**: `SyntheticGeneticCoding.lean`, `GeometricCompressionWorkspace.lean`

| Layer | Type | Range | Purpose |
|-------|------|-------|---------|
| **Source** | `BioParamQ` | Q16_16 [-32768, 32767] | Raw measurements (2.2 nm, 65°C, -1.0 charge) |
| **Coding** | `CodingQ` | Q0_64 [-1, 1) | ALL canonical coding atoms |
| **Projection** | `BioCodingProjection` | struct | Source→Coding with receipt |

**Key Rule**: No field marked `coding_atom` can be raw physical measurement. Must be `CodingQ`.

### 2. Four-Zone Workspace (Lean)

**Location**: `GeometricCompressionWorkspace.lean`

```
Source-Space          →    Coding-Space         →    Geometry-Space        →    Receipt-Space
(BioParamQ)                (CodingQ Q0_64)            (Surfaces/Operators)       (Δφγλ Audit)
    |                          |                           |                           |
    | Project                  | Embed                     | Collapse                  | Validate
    v                          v                           v                           v
Raw measurements         Normalized atoms           Geometric surface          Audit results
2.2 nm diameter          0.55 normalized            Low-rank perturbations     Phi/Delta/Gamma/Lambda
65°C Tm                  0.999 reliability          Structured basis           Warden emissions
```

### 3. Rational Constructors (No Float)

**Location**: `FixedPoint.lean`

```lean
-- WRONG (Float in canonical)
Q0_64.ofFloat 0.55

-- CORRECT (Rational)
Q0_64.ofRatio 55 100      -- 0.55
Q16_16.ofRatio 22 10      -- 2.2
Q0_64.ofRatio 3 8          -- 0.375 (log2(8)/8)
```

### 4. N-Voxel Geometry (Lean)

**Location**: `GeometricCompressionWorkspace.lean`

**Hierarchy** (v5 terminology, `hoxel` deprecated):
```
Goxel    -> pre-compression / shape-agnostic manifold primitive
Voxel    -> compressed 3D cell  
n-voxel  -> compressed n-dimensional cell (dimension is parameter)
Surface  -> rendered projection (phenotype, not proof)
```

**Lean Structures**:
- `NVoxel (n : Nat)` — dimension-parameterized with proof
- `Voxel3D` — specialized 3D voxel
- `voxel3DToNVoxel` — conversion function

### 5. Autopoietic Monitor Level 1 (Lean)

**Location**: `GeometricCompressionWorkspace.lean`

**Doctrine**: Bounded self-maintenance, not self-replication.

**Key Structures**:
- `FailurePattern` — 11 recognized failure modes
- `RepairProposal` — HOLD-state repair candidates
- `WorkspaceAutopoiesis` — failure observation + proposal generation
- `proposeRepairForPattern` — maps failures to repairs

**Warden Rule**: Autopoietic repairs must never self-promote.

### 5.5 Adversarial Trial — Process/Receipt Layer (Lean)

**Location**: `GeometricCompressionWorkspace.lean`

**Doctrine**: Dynamic trial execution as object of audit. Not operator mutation authority.

**Pipeline**:
```
CollapseOperator -> FailurePattern -> AdversarialTrial
  -> surviving φ / Δ residue -> RepairProposal -> WardenStatus
```

**Key Structures**:
- `WardenStatus` — HOLD / REVIEWED / BLOCKED / CANDIDATE
- `AdversarialTrial` — thesis vs contra operator test
- `hasProofReceipt` — delegates to ReceiptCore gate (real, not placeholder)
- `promoteTrial` — promotes CANDIDATE → REVIEWED only with valid receipts
- `promoteTrial_preserves_receipt_gate` — **theorem (proven)** — REVIEWED implies hasProofReceipt
- `ReceiptLedger` (ReceiptCore) — persistent receipt store per target
- `promoteTrialLedger` — promotion via ledger lookup
- `promoteTrialLedger_preserves_invariant` — **theorem (proven)** — ledger invariant
- `runAdversarialTrial` — executes trial, emits audit receipt

**Non-Negotiable**: 
> The workspace may generate counter-surfaces against its own operators, but it may not rewrite those operators without an external repair receipt.

### 6. External Source Anchors (Markdown)

**Location**: `GeometricCompressionWorkspace.md`

| Source | Key Insight | GCL Binding |
|--------|-------------|-------------|
| **Wang et al. (Science 2026)** | 20 AA → 19 AA compression in ribosomal proteins (Ec19 strain); AI-guided redesign maintains >90% fitness | Alphabet compression validated: collapse operator can reduce symbols while preserving phi if structural compensation applied |
| **MIT PlanetWaves** (2026) | Same forcing → different medium → different surface | Medium must be declared for compression claims |
| **Salimans ES (2017)** | ES scales with common random numbers | Mutation-search over coded surfaces |
| **ES at Scale (2025)** | Billion-parameter LLM fine-tuning with ES | Structured search without backprop |
| **EGGROLL/Hyperscale ES (2025)** | Structured low-rank perturbations | Geometric perturbation basis along invariant-preserving directions |

### 7. The Testable Claim

> **Geometry helps compression when it makes invariant structure cheaper to preserve than raw symbolic encoding does, measured by Delta-Phi-Gamma-Lambda across lambda under gamma.**

---

## The LLM Search Contract

**What DeepSeek/LLM Must Propose**:

1. **Input type** — What source objects are being compressed
2. **Q0_64 coding projection** — How source maps to normalized atoms
3. **Geometric embedding** — How atoms become surface coordinates
4. **Compression/collapse operator** — The transform function
5. **Preserved Phi** — What invariant must survive
6. **Residual Delta** — What distortion is acceptable
7. **Gamma pressure** — How aggressive is the collapse
8. **Lambda scale** — What scale band is being compared
9. **Reverse-collapse path** — Can we recover the original
10. **Alias/collision policy** — How to handle degeneracy
11. **Warden failure mode** — What happens if it fails

**Attack Surfaces** (What LLM should challenge):

1. Does Q0_64 lose too much source information?
2. Are normalization maps arbitrary?
3. Does geometric embedding preserve real invariants?
4. Does surface collapse create hidden aliases?
5. Does reverse-collapse recover useful structure?
6. Does operator beat ordinary compression baselines?
7. Does DeltaPhi have measurable proxies?
8. Are biological analogies smuggled as evidence?
9. Are render surfaces mistaken for proof?
10. Are fixed-point constraints obeyed end-to-end?

---

## Build Status

```bash
cd 0-Core-Formalism/lean/Semantics && lake build

✅ Semantics.FixedPoint — 724 jobs
✅ Semantics.SyntheticGeneticCoding — 845 jobs  
✅ Semantics.GeometricCompressionWorkspace — 725 jobs
```

---

## Key Documents

| File | Purpose |
|------|---------|
| `FixedPoint.lean` | Q0_64, Q16_16, Q0_16 with `ofRatio` constructors |
| `SyntheticGeneticCoding.lean` | 0D(n) coding objects, bio-param projection |
| `GeometricCompressionWorkspace.lean` | Four-zone workspace, n-voxel, autopoiesis, adversarial trial, collapse operators, Δφγλ audit |
| `ReceiptCore.lean` | Proof receipt infrastructure: kinds, validation gates, promotion boundary |
| `GeometricCompressionWorkspace.md` | Full doctrine, external anchors, LLM contract |

---

## The One Sentence

> If geometry is the proposed solution to compression, then GCL must provide the workspace where source objects become Q0_64 coding atoms, coding atoms become surfaces, surfaces undergo collapse, and every lost or preserved invariant is audited by Delta-Phi-Gamma-Lambda.

---

## Next Steps for LLM Review

1. **Review the workspace structures** — Are they usable for proposing operators?
2. **Test the Δφγλ audit** — Can meaningful metrics be extracted?
3. **Challenge the low-rank hypothesis** — Is structured perturbation actually better?
4. **Propose a concrete operator** — Fill in the 11-field contract
5. **Benchmark against baseline** — Symbolic encoding vs geometric surface collapse

The workspace is ready for pressure, not praise.
