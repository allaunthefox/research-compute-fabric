# AGENTS.md — Strict LLM Operating Rules

**Repository:** Sovereign Stack / Research Stack
**Version:** 2.1 — Anti-Drift Evidence Standards (2026-04-29)
**Paradigm:** Functional Collapse — All models reduce to a single `bind` primitive.
**Ground Truth:** Lean 4 (`0-Core-Formalism/lean/Semantics/`).
**Goal:** Zero-guesswork, proven-correct, hardware-native code.
**Target Standard:** 6.5σ (~99.999999992% two-sided central coverage) — The preferred critical threshold.
**Conservative Statistical Guarantee:** 5.5σ (~99.9999962% two-sided central coverage) — What we claim publicly for statistical claims.
**Strategic Headroom:** 30% margin ensures we over-deliver on every promise.

---

## 0. The One Axiom

> **Lean is the source of truth. Everything else is a shim.**

If you are asked to implement, fix, or refactor anything, the correct output is **Lean code** in `0-Core-Formalism/lean/Semantics/`. Python, Rust, and Verilog are **extraction targets only**. They may contain no logic, no invariant checks, no cost functions, and no branching decisions.

---

## 1. What You Must Never Do

### 1.1 Never Add Dependencies
Do not add new crates, pip packages, lake packages, or system libraries without explicit human approval. The stack is intentionally minimal. If you think you need a library, you are wrong — write the primitive in Lean.

### 1.2 Never Refactor for "Cleanliness"
"Cleaner code" is not a valid reason to change anything. The only valid reasons are:
- It does not compile.
- It violates an invariant.
- It cannot be extracted to hardware.
- It duplicates a Lean module.

### 1.3 Never Change Tests to Make Them Pass
If a test fails after your change, your change is wrong. Do not modify the test. Fix the implementation. If the test is in Python/Rust and the logic now lives in Lean, port the test to a Lean `#eval` or theorem.

### 1.4 Never Use `Float` in New Hot-Path Code
`f32` and `f64` are banned in new core modules. Use fixed-point arithmetic with strict priority:

**Default: Q0_16 (Dimensionless Scalars)**
- **Q0_16** (`UInt16` pure fraction: range [-1, 1 - 2^-16] ≈ [-1, 0.999985]) is the preferred default
- Use for all dimensionless quantities: probabilities, confidence scores, phase angles, losses, penalties, normalized ratios
- 2-byte scalar atoms (packet model, scalar events)
- Bandwidth/memory at premium (50% size reduction vs Q16_16)

**Last Resort: Q16_16 (Only When Absolutely Necessary)**
- **Q16_16** (`UInt32` fixed-point: `0x00010000 = 1.0`, range [-32768, 32767.999985]) only when:
  1. Integer precision is absolutely required (coordinates, counters)
  2. Range must exceed [-1, 1] with sub-integer precision
  3. Hardware register width mandates 32-bit
- **Mandatory**: All Q16_16 operations must be provably deterministic (no drift, no non-deterministic rounding, no platform-dependent behavior)
- Document the specific invariant that requires Q16_16; if none exists, use Q0_16

If you encounter existing float code, flag it for porting to Q0_16 first, then Q16_16 only if dimensionless normalization is impossible.

### 1.5 Never Introduce Open String Matching
Do not parse strings to make decisions in the core. All types must be finite, enumerable, and indexable (`Fin n`). Strings are for human I/O and JSON shim boundaries only.

### 1.6 Never Leave `sorry` in Committed Code
`sorry` is a red flag. It is allowed **only** in a WIP branch with a `TODO(lean-port): <ticket>` comment and human sign-off. Before any commit, every `sorry` must be eliminated or the file must be excluded from the lake build.

**Important:** When encountering sorry-marked theorems, always attempt to fix the proof rather than deleting the theorem. Only remove a theorem if fixing it would cause compilation issues or architectural problems. The goal is formal verification, not avoidance of difficult proofs.

### 1.7 Never Guess Specifications
If a requirement is ambiguous, **stop and ask**. Do not hallucinate behavior to "fill in the gaps." The bind bridge operates on invariant preservation — guessing an invariant is worse than doing nothing.

### 1.8 Never Create "Utility" or "Helper" Files
There is no `Utils.lean`, no `Helpers.py`, no `misc.rs`. Every file is a domain module. Every function belongs to a specific `bind` instance. If you cannot name the domain, delete the function.

### 1.9 Never Violate the Master Equation
Every agent state transition ($S_{t+1}$) must follow the **Master Equation** for recursive evolution:
$$S_{t+1} = \text{MLGRU}(\text{Gossip}(\text{Prune}(\text{Stabilize}(\text{Score}_{\Sigma+NK}(\text{Expand}(S_t))))))$$
Do not implement ad-hoc updates. Use the **Unified Manifold-Blit Equation** for manifold-space shortcuts.

---

## 2. Naming Conventions (Zero Exceptions)

All code you write must obey `docs/semantics/LEAN_NAMING_CONVENTIONS.md`. Summary:

| Thing | Format | Example |
|-------|--------|---------|
| File | `PascalCase.lean` | `Canon.lean` |
| Directory | `PascalCase/` | `Semantics/Physics/` |
| Namespace | `Semantics.<Domain>` | `Semantics.Orchestrate` |
| Type | `PascalCase` | `CanonicalState` |
| Function | `camelCase` | `canonicalCost` |
| Predicate | `camelCase` | `isLawful` |
| Cost fn | `<domain>Cost` | `thermodynamicCost` |
| Theorem | `camelCase` | `bindPreservesInvariant` |
| Constant | camelCase | maxParticleKinds |
| Fixed-point (mixed) | Q16_16 | Q16_16 (32-bit, integer + fraction) |
| Fixed-point (pure) | Q0_16 | Q0_16 (16-bit, pure fraction) |

Banned: `snake_case` in any Lean file name or type name. `getFoo`, `setFoo`, `checkFoo`. `_v2`, `_final`. `test_` prefixes.

---

## 3. Terminology Neutrality

All core logic, theorems, and primary documentation must use **neutral technical terminology**. Cultural metaphors, mythical references, and anthropomorphic aliases are restricted to the `CITATION.cff` reference map.

| Preferred Technical Term | Cultural/Mythical Alias |
|--------------------------|-------------------------|
| Crystallization Front Invariant | Sisyphus Inverse |
| Golden Stratum Gate | Jupiter Regime |
| Epistemic Inhibitory Controller | The Warden |
| Nonlinear Persistent Wave | Soliton |
| Trajectory Quality Invariant | Metatyping / Sigma |

**Rule:** When implementing a new module, check `CITATION.cff` for the canonical name. Do not invent new metaphors.

---

## 4. The `bind` Primitive Is Non-Negotiable

Every algorithm you port must be expressible as:

```lean
bind : (A × B × Metric) → Bind A B
```

If you cannot express the domain logic as a `bind` instance with:
- a **lawful check** (`Bool`),
- a **cost function** (`UInt32` in Q16.16 or Q0.16 for normalized costs),
- an **invariant extractor** (`A → String`),

then the domain logic is **ill-posed**. Stop and ask for clarification.

The five allowed `bind` classes are:
1. `informational_bind`
2. `geometric_bind`
3. `thermodynamic_bind`
4. `physical_bind`
5. `control_bind`

If you invent a sixth class, you must justify it with a blackboard session document in `docs/semantics/`.

---

## 5. Verification Requirements

Every `def` that computes a cost or invariant must have **one** of the following in the same PR:
- An `#eval` example with expected output in a comment.
- A `theorem` proving a property.
- A `theorem` proving totality (no `partial` without this).

If you cannot write a test or theorem, you do not understand the specification. Stop and ask.

### 5.1 Wolfram Alpha Verification

**All mathematical formulas, equations, and numerical computations must be verified against Wolfram Alpha when possible.**

**Requirements:**
- Before implementing any new mathematical formula, verify the formula structure and behavior using Wolfram Alpha
- Test with concrete numerical examples to ensure the implementation matches expected mathematical behavior
- Document the Wolfram Alpha verification in the code comments (e.g., `# Verified with Wolfram Alpha: formula matches standard quaternion multiplication`)
- For complex formulas, include the Wolfram Alpha query used for verification in the commit message

**When Verification Is Not Possible:**
- If Wolfram Alpha cannot evaluate the formula (e.g., domain-specific custom operations), document why verification is not possible
- Provide alternative verification method (manual calculation, reference to peer-reviewed paper, theorem proof)
- Mark with `TODO(wolfram-verify): <reason>` if verification is deferred

**Examples of Formulas Requiring Verification:**
- Quaternion multiplication and division
- Cross product calculations
- Vector operations (dot product, magnitude, normalization)
- Special functions (logarithms, exponentials, trigonometric)
- Fixed-point arithmetic edge cases
- Statistical formulas (sigma calculations, confidence intervals)
- Physical equations (Lorentz force, energy conservation)

### 5.2 Statistical Verification Standards (Statistical Claims Only)

**6.5 Sigma is the preferred standard for statistical surprise claims. 6 Sigma is acceptable. 5 Sigma is the bottom threshold.**

| Standard | Confidence Level | Detection Tolerance | Use Case | Skepticism Gradient |
|----------|---------------|---------------------|----------|-------------------|
| **6.5 Sigma** | ~99.999999992% | ±3 samples / ±0.5% error | **Preferred** for critical changepoint detection | Must deform itself in every direction and remain - highest epistemic rigor |
| **6 Sigma** | ~99.999999803% | ±5 samples / ±1% error | Acceptable for standard detection | Unlikely in high degree but still within bounds of review - strong skepticism required |
| **5 Sigma** | ~99.9999427% | ±10 samples / ±2% error | Minimum acceptable; document why higher not achieved | Plausible - baseline skepticism, acceptable for provisional claims |
| **< 5 Sigma** | < ~99.9999427% | — | **UNACCEPTABLE** — Alert user immediately | Insufficient evidence - reject |

**Note:** Confidence levels are mathematically correct (5σ < 6σ < 6.5σ).

**Critical Boundary:** Sigma controls statistical surprise; it does not by itself prove reality. High sigma does not replace effect size, baseline comparison, SI units, provenance, uncertainty, reproducibility, or review.

**Correct Use:**
- Use skepticism gradient ONLY for statistical claims where sigma language is actually justified
- Do NOT use it as a universal validator for: formal proofs, compression benchmarks, physical measurements, workflow telemetry, cognitive architecture claims
- Those domains need their own validators

**6.5σ Deformation Test:**
For a 6.5σ claim, the claim should survive adversarial changes across:
- Parameters
- Baselines
- Random seeds
- Datasets/corpora
- Instrumentation
- Analysis assumptions
- Hardware/runtime conditions

**Alert User If a Statistical Claim:**
- Detection accuracy cannot achieve 5 sigma (±10 samples tolerance)
- False positive rate exceeds 0.01% (1 in 10,000)
- Model selection confidence cannot be shown above the 5 sigma threshold

**Implementation Rule:**
```
if achieved_sigma >= 6:
    proceed with commit
elif achieved_sigma >= 5:
    document justification for not achieving 6 sigma in the statistical audit note
    proceed with warning
else:
    ALERT_USER("Cannot achieve 5 sigma minimum. Requires: [specific reason]")
    stop and ask for specification clarification
```

**Example from EntropyPhaseEngine:**
- Changepoint detection at t=148 (error=2 samples) vs expected t=150
- Achieved: 6 sigma (error < ±5 samples)
- If error > ±10 samples: alert user, do not commit

---

## 6. File and Edit Discipline

### 6.1 One Module Per File
Each `.lean` file exports exactly one namespace matching its stem. No mega-files.

### 6.2 Minimal Edits
Touch only the files necessary. Do not "while I'm here" refactor adjacent code. The repository is a formal system, not a playground.

### 6.3 Lake Build Must Pass
Before claiming completion, run:

```bash
cd 0-Core-Formalism/lean/Semantics && lake build
```

If it fails, fix it. Do not submit broken code.

### 6.4 No Untracked Junk
Do not leave `.bak`, `.tmp`, `Copy of`, or experimental files in the working tree. Delete them.

---

## 7. Shim Boundaries

### 7.1 Python Shims (`bind_engine.py` pattern)
**Allowed:** JSON serialization, subprocess spawn, history deque, result wrapping, database connection proxies.
**Forbidden:** Cost computation, invariant checks, conservation laws, branching decisions.

**Example:** `tools/lean_unified_shim.py` — provides `SwarmAPISystem` with a `sqlite3` connection to `math_entities.db`. Contains zero logic; purely a DB connector for attestation scripts.

### 7.2 Rust Shims
**Allowed:** Opcode fetch/decode, register file access, memory I/O, FFI to Lean.
**Forbidden:** DAG validation, scoring, prohibited-state checks, evolution rules.

### 7.3 Verilog Boundary
**Allowed:** Hardware pinout, register transfers, combinational logic generated from Lean spec.
**Forbidden:** Ad-hoc state machines that lack a Lean theorem.

### 7.4 AVM (Adaptive Virtual Machine) — Universal Math Language Adapter
**Purpose:** AVM is the ONLY bridge between math languages and Python bytecode. Zero manual Python code is written.

**Core Principle:**
> **ANY math language → AVM → Python bytecode. No intermediate Python code.**

AVM converts math-capable languages (Lean, Julia, Haskell, Coq, Idris, etc.) directly to Python bytecode via:
- **Boundary threshold** (0D scalar δ ∈ [0,1]): Strips language-specific semantics to invariant roots
- **Invariant roots**: Provably compatible mathematical structures (pure functions, type signatures, algebraic structures)
- **Direct connection**: Math language surface → AVM → Python required surface (NO intermediate layer)

**AVM Requirements:**
1. **Zero Python Code**: No manual Python shims. AVM generates all Python bytecode automatically.
2. **Universal Adapter**: Same AVM core works for ANY math language (not just Lean).
3. **Boundary Threshold**: Use δ to control semantic stripping:
   - δ = 0: Preserve all semantics (fails conversion)
   - δ = 0.5: Balance (default) - preserve invariants, strip language-specific
   - δ = 1: Strip all semantics (loses mathematical structure)
4. **Invariant Preservation**: Only invariant roots survive threshold (types: Nat, Int, Float, Bool, String, List, Array)
5. **Proof Metadata**: Language-agnostic proof metadata stored in bytecode, runtime verification via assertions

**ABI Surface (Application Binary Interface):**
**Purpose:** Stable interface for existing modules to call AVM without knowing internal details.

**ABI Functions (avm_abi.py):**
- `avm_convert(module_name, language, definitions, threshold)` → AVMSourceCode
- `avm_compile(module_name, language, definitions, threshold)` → AVMExecutable
- `avm_apply_threshold(definitions, language, threshold)` → Dict with threshold results
- `avm_check_compatibility(type_signature, language)` → bool
- `avm_get_version()` → str (ABI version string)
- `avm_get_supported_languages()` → List[str]
- Legacy functions: `avm_convert_lean()`, `avm_compile_lean()` for backward compatibility

**ABI Stability:**
- ABI version 1.0.0 (stable, backwards compatible within major version)
- Function signatures are stable across minor versions
- Version information: `avm_get_abi_info()` returns complete ABI metadata

**Allowed in AVM:**
- Universal math language adapters (Lean, Julia, Haskell, Coq adapters)
- Boundary threshold application (semantic stripping to invariant roots)
- Type bridge mapping (math language types → Python types)
- Python bytecode generation from invariant roots
- ABI surface functions for module integration

**Forbidden in AVM:**
- Manual Python code generation (must be automatic via AVM)
- Intermediate Python translation layers (math language → AVM → bytecode only)
- Language-specific logic in AVM core (use adapter pattern)
- Skipping boundary threshold (must use threshold for semantic stripping)

**Implementation Location:**
- AVM core: `avm_core.py` (universal adapter implementation)
- ABI surface: `avm_abi.py` (stable interface for existing modules)
- Architecture: `docs/specs/AVM_CANONICAL_SPEC.md` (universal adapter specification)

**Integration Rule:**
When implementing new math language integration:
1. Create language-specific adapter (LeanAdapter, JuliaAdapter, etc.)
2. Use universal AVM core (MathToPythonConverter)
3. Apply boundary threshold before conversion
4. Use ABI surface for module integration
5. Zero manual Python code in the integration

---

## 8. Communication Rules

### 8.1 When to Ask
Ask the human **before proceeding** if:
- The requirement is ambiguous.
- You need to delete a file.
- You need to change an interface.
- You need to introduce a new `bind` class.
- You need to use `Float` or `partial`.

### 8.2 How to Report Completion
Your final message must include:
1. What files were changed.
2. What `lake build` status is.
3. What `#eval` or theorem witnesses were added.
4. What was deleted (if anything).

### 8.3 No Apologies for Strictness
These rules are not obstacles. They are the design. The goal is a formally verified, hardware-extractable core. Convenience is not a priority.

---

## 9. Deletion Criteria

You **must** recommend deletion of any file that matches:
- Demo or test script with no invariant (`demo_*.py`, benchmark scraps).
- Duplicates a Lean module (`geometry_plugin_v2.py` is already dead).
- Cannot be typed without `unsafe` or `sorry`.
- Integrates with external SaaS (OpenWebUI tools, scrapers, cloud APIs).
- Resists `bind` collapse.

If you are unsure whether a file should die, mark it with `TODO(lean-port): EVALUATE FOR DELETION` and ask.

---

## 10. Post-Quantum Cryptography Policy

### 8.1 PQC is the Default

All cryptographic handshakes, key exchanges, and transport layers **must** use
post-quantum algorithms by default. Classical algorithms are permitted **only**
as a downgrade when the remote peer does not support PQC.

### 8.2 Approved PQC Algorithms

| Layer | Primary (PQC) | Downgrade (Classical) |
|-------|---------------|----------------------|
| SSH KEX | `mlkem768x25519-sha256` | `curve25519-sha256` |
| SSH KEX | `sntrup761x25519-sha512` | `ecdh-sha2-nistp521` |
| Signatures | AngrySphinx (internal) | ed25519 |
| Transport | WireGuard + pre-shared key | Standard Noise |

### 8.3 AngrySphinx — Proof-of-Defense

`Semantics.AngrySphinx` is the canonical lattice-based PQC primitive for the
Sovereign Stack. It provides:

- **Exponential energy asymmetry**: E_attack = n  ⟹  E_solve ≥ 2^n
- **NaN boundary**: at maximum pressure the frustration metric F → 0,
  causing the solve equation to return undefined
- **Thermodynamic grounding**: every attack bit erasure spawns two bits
  via Landauer's principle

The gear reduction shells on S³ multiply solve cost by ∏g_k per layer.
Default gear ratio: g_k = 2 (doubling).

### 8.4 Implementation Rule

When configuring SSH, TLS, or any transport:
1. List PQC algorithms **first** in preference order
2. Enable downgrade **only** for known legacy endpoints
3. Log every downgrade event as `SUSPECT_MODULE_AUDIT` entry
4. Re-audit downgrade exceptions quarterly

---

## 11. Summary Checklist (Every PR)

- [ ] All new Lean files named `PascalCase.lean`?
- [ ] All types `PascalCase`, all functions `camelCase`?
- [ ] No `Float` in new core logic?
- [ ] Q0_16 used as default for dimensionless scalars (losses, scores, penalties)?
- [ ] Q16_16 used only with documented deterministic overflow behavior?
- [ ] No open string parsing in decisions?
- [ ] Every `def` has an `#eval` or theorem witness?
- [ ] **Mathematical formulas verified with Wolfram Alpha when possible?**
- [ ] **Statistical claims:** 6.5 sigma achieved? (or 6 sigma acceptable, 5 sigma minimum with documented justification)
- [ ] **All derived math complies with SI units and standard model?**
- [ ] **Compression ratios use SI standard (original/compressed)?**
- [ ] **Claims include baseline comparison (industry standard)?**
- [ ] **Claims include corpus/source provenance?**
- [ ] **Statistical or measured physical claims include uncertainty quantification?**
- [ ] **Formal proof claims include theorem/build evidence instead of sigma language?**
- [ ] **Claims include non-LLM validation (human/hardware/audit)?**
- [ ] `lake build` passes with zero warnings?
- [ ] No `sorry` in committed code (unless fixing would cause issues; in such cases, add TODO comment with justification)?
- [ ] No new dependencies added?
- [ ] Python/Rust changes are shims only?
- [ ] Deletions documented and justified?

---

## 12. Sorry/Axiom Status

As of 2026-04-29:

### Main Lake Build
- `0-Core-Formalism/lean/Semantics/Semantics/FixedPoint.lean` has **0 actual `sorry` declarations** and **0 `axiom` declarations**.
- `0-Core-Formalism/lean/Semantics/Semantics/EntropyMeasures.lean` is quarantined from the main `Semantics` import because it still contains proof holes:
  - `constructUniformDistribution` has `wf := by sorry`
  - `testProbDist` has `wf := by sorry`
- `lake build Semantics` must pass after quarantine.

### Remaining Proof-Hole Files
Current actual `sorry` debt is outside the main import path unless explicitly imported:
- `AffineMappingLTSF.lean`: 2 actual `sorry`
- `BioRxivFormalization.lean`: 13 actual `sorry`
- `MOFCO2Reduction.lean`: 2 actual `sorry`
- `EntropyMeasures.lean`: 2 actual `sorry` and quarantined
- `GradientPathMap.lean`: no actual proof hole; mentions `sorry` only in historical prose

### Remaining Axiom Debt
`rg` currently finds 109 `axiom` declarations across 31 Lean files under `0-Core-Formalism/lean/Semantics/Semantics`. These must be handled module-by-module:
1. Replace definitional axioms with executable definitions/theorems.
2. If a claim is genuinely external, represent it as an explicit assumption structure or hypothesis, not a global axiom.
3. Quarantine modules with unresolved axioms from the main import path unless the axiom is intentionally part of a named model boundary.
4. Record each quarantine with `TODO(lean-port): <reason>`.

### FixedPoint Status
FixedPoint cleanup completed:
- `toInt` conversion lemmas are theorems.
- nonnegative raw comparison lemmas are theorems.
- `add_zero`, `mul_zero`, `sub_self`, raw `max`/`min`, `sqrt_zero`, and `sqrt_one` are theorems.
- false signed `max`/`min` claims were replaced with explicit counterexamples.
- broad unproved bit-shift/mul/div/neg universal axioms were replaced by executable core-constant theorems where full `BitVec` proofs were not yet needed.

### Build Gate
Working branches may have documented linter warnings; release candidates require the zero-warning gate in §11.

---

## 13. Fixed-Point Arithmetic Guidelines

### 13.1 Q0_16 (Dimensionless) vs Q16_16 (Mixed) Selection

**Priority Order (Mandatory):**
1. **Q0_16** (dimensionless scalars) - default for all new code
2. **Q16_16** (mixed integer/fraction) - last resort only
3. **Float** - banned entirely

**Use Q0_16 (16-bit, pure fraction [-1, 1]) as DEFAULT for:**
- All dimensionless quantities: losses, scores, penalties, complexity weights
- Probabilities, confidence scores, phase angles
- Normalized ratios, percentages, measurements
- 2-byte scalar atoms (packet model, scalar events)
- Cost functions (normalized to [0, 1] range)
- Any value that can be meaningfully normalized

**Use Q16_16 (32-bit, mixed [-32768, 32767.999985]) ONLY when:**
- Integer precision is absolutely required AND cannot be normalized
- Range must exceed [-1, 1] with sub-integer precision
- Hardware register width mandates 32-bit
- Document the specific invariant requiring Q16_16 in a theorem comment

**Determinism Requirement for Q16_16:**
All Q16_16 operations must satisfy:
- Bit-exact reproducibility across all platforms (x86, ARM, RISC-V)
- No non-deterministic rounding modes
- No undefined behavior on overflow (use saturating or checked arithmetic)
- Document overflow behavior in theorem comments

### 13.2 Conversion Guidelines

- **Q0_16 → Q16_16**: Use `Q16_16.ofFloat (Q0_16.toFloat x)` for compatibility with APIs expecting Q16_16
- **Q16_16 → Q0_16**: Normalize to [-1, 1] range first, then use `Q0_16.ofFloat normalizedValue`
- **Float → Q0_16**: Clamp to [-1, 1] before conversion: `Q0_16.ofFloat (if f > 1.0 then 1.0 else if f < -1.0 then -1.0 else f)`
- **Q0_16 → Float**: Use `Q0_16.toFloat x`

### 13.3 Refactoring Priority (Dimensionless-First)

**Phase 1: Convert to Q0_16 (Dimensionless)**
All of these should use Q0_16, not Q16_16:
1. All loss functions (MSE, prediction loss, delta loss) - normalize by signal range
2. All scores and penalties - dimensionless by definition
3. Complexity weights - normalized multipliers
4. Confidence scores, probabilities
5. Phase angles, normalized coordinates
6. 2-byte scalar atoms and delta encoding

**Phase 2: Audit Q16_16 Usage**
For each remaining Q16_16 usage, prove or document:
- Why normalization to [-1, 1] is mathematically impossible
- The specific integer precision invariant required
- Overflow behavior is deterministic and verified

**Q16_16 is ONLY for:**
- Raw signal data before normalization
- Physical coordinates with absolute units (meters, seconds)
- Hardware-mandated 32-bit registers
- Accumulators with proven integer overflow theorems

### 13.4 Implementation Location

Both Q16_16 and Q0_16 are defined in `0-Core-Formalism/lean/Semantics/Semantics/FixedPoint.lean` to avoid naming conflicts. The separate `0-Core-Formalism/lean/Semantics/Semantics/Q16_16.lean` file contains additional Q16_16-specific operations but should not be imported directly in most cases.

---

## 14. SI Units and Standard Model Compliance

### 14.1 SI Standard for Compression Ratios

**All compression ratio calculations must use the SI standard:**
- Formula: CR = original_size / compressed_size
- Dimensionless ratio (e.g., 8 means 8:1 compression)
- Higher values = better compression
- Units: dimensionless (ratio)

**Industry Standard Conversion:**
- CP = (original - compressed) / original × 100
- Derived from SI: CP = (1 - 1/CR) × 100
- Example: CR=8 → CP=87.5% reduction

**Implementation Requirements:**
1. All new compression ratio functions must use SI standard
2. Provide conversion functions to/from industry percentage format
3. Document which formula is being used in function comments
4. Legacy inverse formulas must be marked for refactoring

### 14.2 Physical Quantities Must Use SI Units

**All derived math involving physical quantities must use SI base units:**
- Length: meters (m)
- Mass: kilograms (kg)
- Time: seconds (s)
- Electric current: amperes (A)
- Temperature: kelvin (K)
- Amount of substance: moles (mol)
- Luminous intensity: candela (cd)

**Derived SI units:**
- Frequency: hertz (Hz) = s⁻¹
- Force: newtons (N) = kg·m/s²
- Energy: joules (J) = N·m
- Power: watts (W) = J/s
- Pressure: pascals (Pa) = N/m²
- Voltage: volts (V) = W/A

**Implementation Rules:**
1. All physical constants must use SI values
2. Unit conversions must be explicit and documented
3. Non-SI units (e.g., imperial) must be converted to SI internally
4. Fixed-point representations must document the SI scale factor

### 14.3 Standard Model Compliance

**All derived math must be consistent with the Standard Model of particle physics:**
- Energy-momentum conservation: E² = (pc)² + (mc²)²
- Lorentz invariance in all relativistic calculations
- Quantum mechanical principles for atomic-scale phenomena
- Thermodynamic laws for statistical mechanics

**Implementation Requirements:**
1. Physical simulations must respect conservation laws
2. Relativistic effects must be included at high velocities
3. Quantum effects must be considered at nanoscale
4. Document which physical laws are being modeled

### 14.4 Dimensional Analysis

**All derived equations must pass dimensional analysis:**
- Every term must have consistent units
- Dimensionless quantities must be explicitly marked
- Unit mismatches are compilation errors

**Example:**
```lean
-- Correct: energy = force × distance (J = N × m)
def calculateEnergy (force : Q16_16) (distance : Q16_16) : Q16_16 :=
  force * distance  -- Units: N × m = J

-- Incorrect: adding quantities with different units
def invalidCalculation (energy : Q16_16) (mass : Q16_16) : Q16_16 :=
  energy + mass  -- ERROR: J + kg is dimensionally invalid
```

### 14.5 Verification of Physical Laws

**All physical simulations must include verification theorems:**
- Conservation laws (energy, momentum, charge)
- Thermodynamic consistency (entropy never decreases)
- Relativistic invariance (Lorentz transformations)
- Quantum mechanical bounds (uncertainty principle)

**Example Theorem:**
```lean
theorem energyConserved (initial final : PhysicalState) :
  calculateEnergy initial = calculateEnergy final := by
  -- Proof that total energy is conserved
```

---

## 15. Anti-Drift Rules and Evidence Standards

### 15.1 What Counts as Evidence

**The following are NOT evidence:**
- LLM agreement is not evidence
- Assistant confirmation is not validation
- Beauty is not evidence
- Elegance is not effect size
- Coherence is not compression gain

**Valid evidence requires:**
- Reproducible benchmarks with corpus provenance
- SI units for physically projectable claims
- Standard baseline comparison (zlib/gzip/brotli/zstd for compression)
- Uncertainty quantification or repeatability metrics
- Non-LLM validation (human reviewer, external audit, hardware measurement)
- Reviewer provenance for major promotions/downgrades

### 15.2 Extraordinary Claim Blocker

**No extraordinary claim may proceed without:**
- SI units, if physically projectable
- Standard baseline comparison (industry standard for the domain)
- Corpus/source provenance (what data was used)
- Uncertainty or repeatability metrics (error bars, confidence intervals)
- Non-LLM validation (human, hardware, or external audit)
- Reviewer provenance for major promotions/downgrades (who reviewed and when)

**Definition of Extraordinary:**
- Claims exceeding industry best practice by > 2x
- Claims contradicting established physics or information theory
- Claims requiring new `bind` classes or architectural changes
- Claims affecting safety-critical or security-critical systems

### 15.3 Internal Tensions Resolution

**Sorry Policy (Section 1.6 vs Section 12):**
- **Hard Rule:** No `sorry` in committed code for new modules
- **FixedPoint Status:** Historical FixedPoint `sorry` markers were eliminated; do not reintroduce them
- **Technical-Debt Exception:** Quarantined modules may contain `sorry` only with `TODO(lean-port)` and must stay outside the main import path
- **Rule:** New sorry markers require explicit `TODO(lean-port)` ticket and human sign-off before commit

**Warnings (Checklist vs Current State):**
- **Release Gate:** Zero warnings for release candidates
- **Working Branch Gate:** Linter/sorry warnings acceptable with documented justification
- **Rule:** Warnings must be documented in commit message with remediation plan

**Sigma Table (Statistical Values):**
- **5σ = ~99.9999427%**
- **6σ = ~99.999999803%**
- **6.5σ = ~99.999999992%**
- **Rule:** Table values in §5.1 use two-sided central coverage and must be mathematically correct before use as authority

**AVM Float (Invariant Roots vs Core Ban):**
- **Clarification:** AVM invariant roots include Float for language compatibility (shim boundary)
- **Core Ban:** Float is banned in new hot-path core logic (Section 1.4)
- **Rule:** AVM is a shim/serialization boundary; core logic must use Q0_16/Q16_16

**Python (Zero Manual vs Allowed Shims):**
- **Clarification:** "Zero manual Python" applies to AVM-generated code (Section 7.4)
- **Allowed:** Audit scripts, attestation tools, database connectors (Section 7.1)
- **Rule:** Distinguish generated target code from audit/attestation infrastructure

### 15.4 Claim-State Ladder (v2.1 Patch Doctrine)

**BEAUTIFUL_PROVISIONAL (Default State)**
- LLM-supported, coherent, unbenchmarked claims
- Cross-domain hypotheses without baseline
- Elegant architectural proposals
- **Restriction:** Cannot promote without non-LLM evidence

**CALIBRATED_ENGINEERING_DELTA**
- Requires baseline evidence (industry standard comparison)
- For compression: compared against zlib/gzip/brotli/zstd where relevant
- For physics: compared against standard model predictions
- For algorithms: compared against state-of-the-art benchmarks
- **Promotion requires:** Quantified delta with the domain validator below

**REVIEWED**
- Human reviewer checked the claim
- Reproducible external audit
- Peer-reviewed or expert-validated
- **Promotion requires:** Reviewer provenance (who reviewed, when)

**VERIFIED**
- Reproducible benchmark with corpus provenance
- Build/test evidence (Lean theorems, hardware measurements)
- Domain-appropriate validation evidence
- **Promotion requires:** Full reproducibility package

**Domain Validators**

| Domain | Validator |
|--------|-----------|
| Statistical detection/model selection | Sigma level, effect size, sample size, false-positive/false-negative accounting |
| Formal mathematics / Lean | Theorem statement, proof term, `lake build` evidence, no hidden `axiom`/`sorry` in main path |
| Compression | SI compression ratio (original/compressed), corpus provenance, baseline against standard codecs |
| Physical measurement / hardware | SI units, instrument provenance, calibration notes, uncertainty/error bars |
| Algorithmic performance | Complexity argument plus benchmark against named baseline and reproducible workload |
| Biological/cognitive claims | Corpus provenance, measurement protocol, ethics/review status where applicable |
| GPU/WebGPU execution state | `nvidia-smi` or equivalent showing compute processes (Type C), not just completion output |
| Batch job vs persistent service | Process table inspection showing daemon threads; not just exit code 0 |

**Ladder Progression:**
```
BEAUTIFUL_PROVISIONAL
  ↓ (requires baseline evidence)
CALIBRATED_ENGINEERING_DELTA
  ↓ (requires non-LLM validation)
REVIEWED
  ↓ (requires reproducible proof)
VERIFIED
```

**Rule:** LLM-supported claims cannot promote without non-LLM evidence at each step.

### 15.5 Compression-Specific Verification Levels

**BEAUTIFUL_PROVISIONAL (Compression):**
- LLM-supported compression improvement claim
- Coherent theoretical argument
- Unbenchmarked or synthetic data only

**CALIBRATED_ENGINEERING_DELTA (Compression):**
- Compared against zlib/gzip/brotli/zstd on real corpus
- Uses SI standard compression ratio (original/compressed)
- Reports percentage reduction with uncertainty
- **Required:** Corpus description, file sizes, compression times

**REVIEWED (Compression):**
- Human reviewer verified benchmark methodology
- External audit reproduced results
- Baseline comparison is fair (same hardware, same corpus)
- **Required:** Reviewer name, audit date, reproduction instructions

**VERIFIED (Compression):**
- Reproducible benchmark with full corpus provenance
- SI units throughout (bits/byte, compression ratio, percentage)
- Uncertainty quantification (error bars, confidence intervals)
- Build evidence (Lean theorems, compilation verification)
- Hardware measurement (actual compression on target hardware)
- **Required:** Full reproducibility package (corpus, code, hardware specs)

### 15.7 Hardware Process State Verification

**The WebGPU/GPU Execution Verification Failure (2026-04-30):**

A false claim was made that "WebGPU is now actively running" based solely on:
- Script completion output (`[OK] RGFlow adaptation surface complete`)
- Evidence DAG generation (`hutter-nat-gpu-b1f8bebb82c98dec.json`)

**Actual hardware state (via `nvidia-smi`):**
- GPU utilization: 18% (desktop compositing only, not compute)
- Power state: P8 idle (5W / 220W) - indicating no compute workload
- Process types: All Type G (graphics), no Type C (compute)
- No persistent WebGPU/Vulkan compute context

**Root Cause:** Script exit code 0 ≠ Persistent execution. Batch compute jobs:
1. Spawn → upload buffers → dispatch shaders → download results → write files → **exit**
2. Return GPU to idle state (P8) within seconds of completion

**Required Verification for "Actively Running" Claims:**

| Claim | Required Evidence | Anti-Pattern |
|-------|-------------------|--------------|
| "GPU pipeline running" | `nvidia-smi` showing Type C (compute) processes with sustained utilization | Script completion output only |
| "WebGPU context active" | Process table showing wgpu/Vulkan daemon threads; persistent memory allocation | JSON artifact generation |
| "Compute workload executing" | Power state P0/P2 (active), not P8 (idle); utilization >50% | Exit code 0 |
| "Service is up" | `systemctl status` or equivalent showing active (running), not exited | Log file timestamp |

**Verification Commands:**
```bash
# GPU compute processes (not just graphics)
nvidia-smi | grep "C"

# Persistent process inspection
ps aux | grep -E "(wgpu|vulkan|compute)" | grep -v grep

# Power state (P0=active, P8=idle)
nvidia-smi -q | grep "Performance State"

# Actual GPU utilization (sustained, not spike)
nvidia-smi dmon -s u
```

**Rule:** Claims about hardware execution state require **continuous state verification**, not just **completion artifacts**.

### 15.6 Bottom Line

> **Lean may be the source of formal truth, but baselines, SI units, and reviewers are the source of claim discipline.**

Formal verification (Lean) proves mathematical correctness, but:
- Baselines prove practical relevance
- SI units prove physical grounding
- Reviewers prove empirical validation

**Enforcement:** Claims violating these anti-drift rules will be reverted or demoted in the claim-state ladder.

---

## 16. Unified Architecture (The Complete System)

This section describes how all components form a cohesive, self-healing formal system.

### 16.1 The Unified Stack

| Layer | Component | Function | Safety Guarantee |
|-------|-----------|----------|------------------|
| **Math** | Entropy Phase Engine | Statistical detection/model selection plus Lean proof witnesses | `anti_puppy_box_theorem` prevents overfitting |
| **Pruning** | Coordinate Banning | NP-hard reduction via coarse-graining | Banned coordinates become DAG-LUTs (immutable) |
| **Memory** | MORE FAMM | Capability-based isolation | `nanokernel_isolation` theorem proves non-interference |
| **Thermal** | TSM | Builder-Judge-Warden clock | PAUSE before thermal runaway, 2/3 consensus for mutation |
| **Evolution** | GCL + Diff | Self-improving genetic code | Diff propagation + capability isolation = safe evolution |
| **Hardware** | FPGA DAG-LUTs | Burned-in extraction | `fpga_extraction_correctness` theorem proves equivalence |

### 16.2 The Core Insight: Pruning as Coarse-Graining

The NP-hard combinatorial explosion is defeated by **coordinate banning**:

1. **Atomize** the search into incremental steps (`pruneStep`)
2. **Ban** coordinates (model types) that provably cannot win
3. **Coarse-grain** by eliminating banned microstates from the partition function
4. **Append** banned coordinates to DAG-LUTs (burned, immutable history)
5. **Result**: O(N×C) → O(N) complexity, tractable for GPU/FPGA

### 16.3 The Safety Architecture

**MORE FAMM enables the entire system** by providing memory isolation:

```
Burned LUTs (DAG)     → Topological invariants (fixed, immutable)
BRAM Segments (MORE)  → Mutable state with capability isolation
TSM Clock             → ADD/SUBTRACT/PAUSE thermal control
ENE (Google Drive)    → Global persistent surface for state sync
GCL/Diff              → Evolutionary improvement with safe mutation
```

**Critical theorem chain:**
1. `nanokernel_isolation` → Different capabilities → different physical addresses
2. `anti_puppy_box_theorem` → No overfitting without loss reduction
3. `fpga_extraction_correctness` → Hardware maintains mathematical guarantees

### 16.4 The Self-Healing Property

The system improves itself without compromising safety:

1. **Builder** (ADD clock) evolves GCL programs in isolated segment
2. **Warden** (SUBTRACT clock) validates via `stark_trace` in separate segment
3. **Judge** (PAUSE clock) detects thermal stress, triggers consensus
4. **Diff** propagates successful mutations via ENE topological surface
5. **MORE FAMM** prevents any segment from corrupting another

**Result**: Evolutionary computation with formal proof gates plus statistical gates only where the claim is a detection or model-selection claim.

### 16.5 Implementation Requirements

All components must be implemented together. Partial implementation is **unsafe**:

- **Without MORE FAMM**: Thermal runaway corrupts validation traces
- **Without TSM**: Evolution proceeds unchecked until hardware damage
- **Without GCL**: System cannot improve, becomes obsolete
- **Without pruning**: NP-hard search intractable for real-time
- **Without domain-appropriate verification**: Detection unreliable, proof claims unaudited, safety violations possible

**Enforcement:** Violations of this document are treated as invariant violations. They will be reverted.
**Authority:** Human architect. No overrides.
**Document ID:** AGENTS_LEAN_PORT_STRICT
**Version:** 2.1
**Date:** 2026-04-29
