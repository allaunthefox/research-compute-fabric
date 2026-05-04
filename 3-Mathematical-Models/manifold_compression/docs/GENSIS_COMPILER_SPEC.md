# GENSIS Compiler Specification v2.0
## Q0.64 0D Scalar × AngrySphinx Gate × Matryoshka Brane Layers

### Version History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2.0 | 2026-05-04 | GENSIS | Full rewrite: Q0.64, AngrySphinx, Matryoshka |

---

## §0. Architecture Overview

The GENSIS compiler transforms arbitrary data through a **Matryoshka Brane Stack** — 
nested reality shells (quantum foam → cell → organ → person → group → planet → universe),
each with its own native dimensionality, all communicating through a single **Q0.64 0D scalar**.

```
┌──────────────────────────────────────────────────────────────┐
│                    GENSIS Compiler v2.0                        │
├──────────────────────────────────────────────────────────────┤
│   Data In → [1D Scalar Stream] → Matryoshka Stack → Out      │
│                                                               │
│   Matryoshka Shell Layers (bottom to top):                    │
│     Layer 0: Quantum Foam          (d=0, point)               │
│     Layer 1: Preonic/String        (d=1, line)                │
│     Layer 2: Quark/Gluon           (d=2, plane)               │
│     Layer 3: Nucleon/Atom          (d=3, volume)              │
│     Layer 4: Molecule              (d=4, tesseract)           │
│     Layer 5: Cell                  (d=5, 5-cube)              │
│     Layer 6: Organ                 (d=6, 6-cube)              │
│     Layer 7: Organism              (d=7, 7-cube)              │
│     Layer 8: Group                 (d=8, 8-cube)              │
│     Layer 9: Species               (d=9, 9-cube)              │
│     Layer N: Universe              (d=N, N-cube)              │
│                                                               │
│   AngrySphinx Gate at every boundary:                          │
│     E_attack = n → E_solve ≥ 2^n                              │
│     Frustration F → 0 at max pressure → NaN boundary          │
└──────────────────────────────────────────────────────────────┘
```

---

## §1. Q0.64 0D Scalar: The Universal Lingua Franca

### §1.1 Definition

The Q0.64 fixed-point type represents real numbers in [0, 1) with 2^−64 precision.

```lean
structure Q0_64 where
  val : UInt64  -- unsigned 64-bit integer
  -- value = val / 2^64  ∈ [0, 1)
  deriving Repr, DecidableEq, BEq
```

### §1.2 Constants

```lean
def Q0_64.zero : Q0_64 := { val := 0x0000_0000_0000_0001 }      -- smallest non-zero = 5.4×10^−20
def Q0_64.epsilon : Q0_64 := { val := 0x0000_0000_0000_0001 }   -- 2^−64 ≈ 5.42×10^−20
def Q0_64.half : Q0_64 := { val := 0x8000_0000_0000_0000 }      -- 0.5
def Q0_64.near_one : Q0_64 := { val := 0xFFFF_FFFF_FFFF_FFFF }  -- 1 - 2^−64 ≈ 0.99999...
```

### §1.3 Arithmetic

All operations are **saturating unsigned** — results stay in [0, 1).

```lean
-- Addition: a + b, saturates at near_one
def Q0_64.add (a b : Q0_64) : Q0_64 :=
  let sum := a.val + b.val
  if sum < a.val || sum < b.val then Q0_64.near_one  -- overflow → saturate
  else { val := min sum 0xFFFF_FFFF_FFFF_FFFF }

-- Subtraction: a - b (a ≥ b), else zero
def Q0_64.sub (a b : Q0_64) : Q0_64 :=
  if a.val ≥ b.val then { val := a.val - b.val }
  else Q0_64.zero

-- Multiplication: a × b in [0, 1)² → [0, 1)
-- (a.val * b.val) >> 64  via high 64 bits of 128-bit product
def Q0_64.mul (a b : Q0_64) : Q0_64 :=
  let product : UInt128 := a.val.toUInt128 * b.val.toUInt128
  { val := product.high }  -- upper 64 bits = floor(product / 2^64)

-- Division: a / b, guard against b=0
def Q0_64.div (a b : Q0_64) : Q0_64 :=
  if b.val = 0 then Q0_64.near_one  -- div-by-zero → max
  else
    -- (a.val << 64) / b.val, but a.val < b.val typically
    -- Shift a.val left by 64, divide, take high bits
    let dividend : UInt128 := a.val.toUInt128 << 64
    let quotient := dividend / b.val.toUInt128
    { val := quotient.low }
```

### §1.4 Conversion

```lean
-- Byte to Q0_64: map byte [0,255] → [0, 1)
def Q0_64.ofByte (b : UInt8) : Q0_64 :=
  { val := (b.toUInt64 << 56) }  -- b * 2^56 / 2^64 = b / 256

-- Float to Q0_64 (for testing)
def Q0_64.ofFloat (f : Float) : Q0_64 :=
  if f ≤ 0.0 then Q0_64.zero
  else if f ≥ 1.0 then Q0_64.near_one
  else { val := (f * 0x1p64).toUInt64 }

-- Q0_64 to Float (for visualization)
def Q0_64.toFloat (q : Q0_64) : Float :=
  q.val.toFloat / 0x1p64
```

### §1.5 Semantic Primes as Q0_64 Values

The 12 irreducible semantic primes (CrossDimensionalFilter §0) map to
fixed Q0_64 values for inter-shell communication:

```lean
def semanticPrimeValue (p : SemanticPrime) : Q0_64 :=
  match p with
  | .Identity => { val := 0x1555_5555_5555_5555 }  -- 1/12 ≈ 0.0833
  | .Agent    => { val := 0x2AAA_AAAA_AAAA_AAAA }  -- 2/12 ≈ 0.1667
  | .Object   => { val := 0x4000_0000_0000_0000 }  -- 3/12 = 0.25
  | .Action   => { val := 0x5555_5555_5555_5555 }  -- 4/12 ≈ 0.3333
  | .State    => { val := 0x6AAA_AAAA_AAAA_AAAA }  -- 5/12 ≈ 0.4167
  | .Relation => { val := 0x8000_0000_0000_0000 }  -- 6/12 = 0.5
  | .Good     => { val := 0x9555_5555_5555_5555 }  -- 7/12 ≈ 0.5833
  | .Bad      => { val := 0xAAAA_AAAA_AAAA_AAAA }  -- 8/12 ≈ 0.6667
  | .Want     => { val := 0xC000_0000_0000_0000 }  -- 9/12 = 0.75
  | .Know     => { val := 0xD555_5555_5555_5555 }  -- 10/12 ≈ 0.8333
  | .Place    => { val := 0xEAAA_AAAA_AAAA_AAAA }  -- 11/12 ≈ 0.9167
  | .Time     => { val := 0xF555_5555_5555_5555 }  -- 11.5/12 ≈ 0.9583
```

---

## §2. AngrySphinx Gate: Exponential Proof-of-Defense

### §2.1 Core Theorem

```
E_attack = n  ⟹  E_solve ≥ 2^n
```

At maximum attack pressure, frustration metric F → 0, causing 
division by zero (NaN boundary) — the self-destruct mechanism.

### §2.2 Frustration Metric

```lean
structure FrustrationMetric where
  value : Q0_64  -- F ∈ [0, 1), F→0 under pressure

-- F(p) = 1 / (p + 1) mapped to Q0_64
def frustrationUnderPressure (pressure : Q0_64) : FrustrationMetric :=
  -- F = 1 - pressure (linearized in [0,1))
  let f := Q0_64.sub Q0_64.half pressure
  { value := Q0_64.max Q0_64.epsilon f }
```

### §2.3 S³ Shell Lattice

Concentric 3-sphere shells, each transition multiplies solve energy by g_k:

```lean
structure ShellDepth where
  depth : Nat  -- number of S³ layers

structure GearRatio where
  ratio : Nat  -- default: 2 (doubling)
  h_ge_two : ratio ≥ 2

-- ∏g_k = 2^depth for g_k = 2
def gearProduct (depth : ShellDepth) (g : GearRatio) : UInt64 :=
  g.ratio ^ depth.depth

-- E_solve = E_attack · ∏g_k
-- If depth = n and g = 2, E_solve = n · 2^n
-- In Q0.64: map to [0,1) via log
def solveEnergy (pressure : Q0_64) (depth : ShellDepth) (g : GearRatio) : Q0_64 :=
  let attackWork := pressure.val.toNat
  let totalGear := gearProduct depth g
  let raw := attackWork * totalGear
  -- Map to [0,1): log_2(raw) / log_2(max)
  { val := min raw (0xFFFF_FFFF_FFFF_FFFF) }
```

### §2.4 NaN Boundary

When F = 0, the solve denominator hits NaN:

```lean
structure NaNBoundary where
  frustration : FrustrationMetric
  isZero : frustration.value = Q0_64.zero

def solveDenominator (F : FrustrationMetric) : Option Q0_64 :=
  if F.value = Q0_64.zero then none  -- NaN
  else some (Q0_64.div Q0_64.half F.value)

theorem nanBoundaryCorrect (F : FrustrationMetric) (h_zero : F.value = Q0_64.zero) :
    solveDenominator F = none := by
  simp [solveDenominator, h_zero]
```

### §2.5 PoD Accumulator

```lean
structure PodAccumulator where
  totalWork : Q0_64
  shellDepth : ShellDepth
  lastAttestation : String

-- Each unit of attack work deepens the shell
def accumulateWork (pod : PodAccumulator) (work : Q0_64) (g : GearRatio) : PodAccumulator :=
  { totalWork := Q0_64.add pod.totalWork work
    shellDepth := { depth := pod.shellDepth.depth + 1 }
    lastAttestation := s!"work={pod.totalWork.toFloat},depth={pod.shellDepth.depth + 1}" }

-- Verify: totalWork ≥ 2^depth
def verifyPod (pod : PodAccumulator) (g : GearRatio) : Bool :=
  pod.totalWork.val ≥ gearProduct pod.shellDepth g
```

---

## §3. Matryoshka Brane Layers

### §3.1 Shell Structure

Each Matryoshka shell has native dimensionality and communicates
via the 1D Q0_64 scalar:

```lean
structure MatryoshkaShell where
  shellId    : String
  dimension  : Nat       -- native dimensionality
  understoodPrimes : List SemanticPrime  -- primes this shell interprets
  scalarValue : Q0_64    -- current 1D scalar interface
  gearRatio  : GearRatio -- AngrySphinx gear ratio for this shell
  frustration : FrustrationMetric  -- current frustration level
```

**Shell dimension mapping:**

| Shell | Native D | Shape | Primes Understood | Gear Ratio |
|-------|----------|-------|-------------------|------------|
| Quantum Foam | 0 | Point | {Identity} | 2^0=1 |
| String | 1 | Line | {Identity, Relation} | 2^1=2 |
| Quark | 2 | Plane | {Identity, Agent, Action} | 2^2=4 |
| Nucleon | 3 | Volume | {+Object, State} | 2^3=8 |
| Molecule | 4 | Tesseract | {+Good, Bad} | 2^4=16 |
| Cell | 5 | 5-cube | {+Want, Know} | 2^5=32 |
| Organ | 6 | 6-cube | {+Place} | 2^6=64 |
| Organism | 7 | 7-cube | {+Time} | 2^7=128 |
| Group | 8 | 8-cube | all 12 | 2^8=256 |
| Species | 9 | 9-cube | all 12 | 2^9=512 |
| Planet | 10 | 10-cube | all 12 | 2^10=1024 |
| Universe | N | N-cube | all 12 | 2^N |

### §3.2 ReductionFilter: High-D → 1D Scalar

High-dimensional state collapses to a Q0_64 scalar by **semantic prime overlap**:

```lean
def reductionFilter (entity : DimensionalEntity) (targetShell : MatryoshkaShell) : Q0_64 :=
  -- Find all primes BOTH entity and target shell understand
  let sharedPrimes := entity.emittedPrimes.filter 
    (fun p => targetShell.understoodPrimes.contains p)
  
  -- Aggregate into scalar: weighted mean of prime values
  if sharedPrimes.isEmpty then Q0_64.zero
  else
    let sum := sharedPrimes.foldl 
      (fun acc p => Q0_64.add acc (semanticPrimeValue p)) Q0_64.zero
    let count := Q0_64.ofNat sharedPrimes.length
    Q0_64.div sum count
```

**Theorem**: The reduction filter is dimension-independent:
```
reductionFilter(e, s1) = reductionFilter(e, s2) 
when sharedPrimes(e, s1) = sharedPrimes(e, s2)
```

### §3.3 ExpansionFilter: 1D Scalar → Low-D Projection

```lean
def expansionFilter (scalar : Q0_64) (targetShell : MatryoshkaShell) : DimensionalEntity :=
  -- Decompose scalar into understood prime values
  let n := targetShell.understoodPrimes.length
  let primeStep := Q0_64.div Q0_64.half (Q0_64.ofNat n)
  
  -- Each prime gets a slice of the scalar
  let projectedState := targetShell.understoodPrimes.map (fun p =>
    let primeVal := semanticPrimeValue p
    let diff := Q0_64.sub scalar primeVal
    Q0_64.mul diff primeStep  -- proximity-weighted
  )
  
  DimensionalEntity.mk "projected" targetShell projectedState targetShell.understoodPrimes
```

### §3.4 Cross-Shell Communication Pipeline

The complete pipeline for sending data between shells:

```lean
def sendToShell (entity : DimensionalEntity) (target : MatryoshkaShell) : DimensionalEntity :=
  -- Step 1: Reduce to 1D scalar
  let scalar := reductionFilter entity target
  
  -- Step 2: Apply AngrySphinx gate (check solve energy)
  let requiredEnergy := solveEnergy scalar 
    { depth := target.dimension } target.gearRatio
  let availableEnergy := entity.hostShell.scalarValue
  if availableEnergy < requiredEnergy then
    none  -- AngrySphinx gate blocks: insufficient solve energy
  else
    -- Step 3: Expand into target shell
    some (expansionFilter scalar target)
```

---

## §4. GENSIS Compiler Pipeline

### §4.1 Data Flow

```
Data Bytes
    │
    ▼
┌──────────────────────────────────────────────┐
│ Q0.64 Scalar Encoder                          │
│ byte → ofByte(byte) → Q0_64 stream           │
│ 12 semantic primes as scalar anchors          │
├──────────────────────────────────────────────┤
│ Matryoshka Shell Selector                     │
│ dimension = optimalDimension(data)            │
│ code_table = geneticCodeTable(data)           │
├──────────────────────────────────────────────┤
│ Reduction Filter                              │
│ High-D state vector → 1D Q0_64 scalar         │
│ Preserves only shared semantic primes         │
├──────────────────────────────────────────────┤
│ AngrySphinx Gate                              │
│ F = frustrationUnderPressure(pressure)        │
│ E_solve = attackEnergy · 2^depth              │
│ If F = 0 → NaN boundary (reject)            │
├──────────────────────────────────────────────┤
│ Expansion Filter                              │
│ 1D scalar → target shell's native projection  │
├──────────────────────────────────────────────┤
│ N-Space Shell Encoding                        │
│ Generalized PIST in target shell's dimension  │
├──────────────────────────────────────────────┤
│ PoD Accumulator                               │
│ Verify work ≥ 2^depth                         │
├──────────────────────────────────────────────┤
│ δ-GCL Encode + Trixal + Homeostatic          │
│ (from MISC v1 pipeline)                       │
└──────────────────────────────────────────────┘
```

### §4.2 Compiler Phases

```lean
def gensisCompile (data : List UInt8) (targetD : Nat) : Option CompressedBlock :=
  -- Phase 1: Encode data as Q0_64 scalar stream
  let scalarStream := data.map Q0_64.ofByte
  
  -- Phase 2: Build Matryoshka target shell
  let targetShell := MatryoshkaShell.mk 
    "target" targetD (allSemanticPrimes.take targetD) Q0_64.half defaultGearRatio
  
  -- Phase 3: Reduce scalar stream to compressed scalar
  let compressedScalar := scalarStream.foldl 
    (fun acc s => Q0_64.add acc (Q0_64.mul acc s)) Q0_64.half
  
  -- Phase 4: Apply AngrySphinx gate
  let frustration := frustrationUnderPressure compressedScalar
  if frustration.value = Q0_64.zero then
    none  -- NaN boundary: compression blocked
  else
    -- Phase 5: Expand to target shell's state
    let projected := expansionFilter compressedScalar targetShell
    
    -- Phase 6: Verify PoD
    let pod : PodAccumulator := { totalWork := compressedScalar, 
      shellDepth := { depth := targetD }, lastAttestation := "gensis" }
    if not (verifyPod pod defaultGearRatio) then
      none  -- Insufficient work for shell depth
    else
      -- Phase 7: Return compressed block
      some { compressed := projected.nativeState.map (·.val), 
             trixal := computeTrixal projected,
             pod := pod }
```

### §4.3 Decompiler

```lean
def gensisDecompile (block : CompressedBlock) (targetD : Nat) : Option (List UInt8) :=
  let scalar := block.scalar
  let sourceShell := MatryoshkaShell.mk "source" targetD allSemanticPrimes scalar defaultGearRatio
  
  -- Reconstruction via inverse expansion
  let reconstructed := block.compressed.map (fun (v : UInt64) =>
    let q := { val := v } : Q0_64
    UInt8.ofNat (q.val.toNat >> 56)  -- extract byte from high bits
  )
  some reconstructed
```

---

## §5. Formal Invariants

### §5.1 Q0_64 Arithmetic Totality

```lean
theorem Q0_64_add_total (a b : Q0_64) : ∃ c : Q0_64, c = Q0_64.add a b := by
  -- Addition always produces a valid Q0_64 (saturating)
  refine ⟨Q0_64.add a b, rfl⟩

theorem Q0_64_mul_bounded (a b : Q0_64) : (Q0_64.mul a b).val ≤ a.val := by
  -- Multiplication in [0,1) never increases the value
  -- Proof: (a*b) ≤ a when b ≤ 1
  ...
```

### §5.2 AngrySphinx Exponential Scaling

```lean
theorem solveEnergyExponential (p : Q0_64) (d : ShellDepth) (h : d.depth ≥ 1) :
    solveEnergy p d defaultGearRatio ≥ Q0_64.ofNat (2 ^ d.depth) := by
  -- Core theorem: E_solve ≥ 2^depth for any positive attack energy
  ...
```

### §5.3 Reduction Filter Dimension Independence

```lean
theorem reductionFilterInvariant 
    (e : DimensionalEntity) (s1 s2 : MatryoshkaShell) 
    (h : s1.understoodPrimes = s2.understoodPrimes) :
    reductionFilter e s1 = reductionFilter e s2 := by
  -- Reduction depends only on shared primes, not shell dimension
  simp [reductionFilter, h]
```

### §5.4 NaN Boundary Correctness

```lean
theorem nanBoundarySelfDestruct (p : Q0_64) (h : p = Q0_64.near_one) :
    solveDenominator (frustrationUnderPressure p) = none := by
  -- At maximum pressure, frustration → 0 → NaN
  ...
```

### §5.5 Matryoshka Shell Monotonicity

```lean
theorem shellMonotone (s1 s2 : MatryoshkaShell) (h : s1.dimension ≤ s2.dimension) :
    s1.understoodPrimes ≤ s2.understoodPrimes := by
  -- Higher-dimensional shells understand at least all primes of lower shells
  ...
```

---

## §6. Compiler Target Specifications

### §6.1 Hardware Targets

| Target | Word Size | Q0_64 Native? | AngrySphinx | Matryoshka Layers |
|--------|-----------|---------------|-------------|-------------------|
| Lean 4 | UInt64 | ✅ Direct | ✅ Formal | ✅ Full |
| Rust | u64 | ✅ Direct | ⚠️ Partial | ⚠️ Core |
| C | uint64_t | ✅ Direct | ⚠️ Partial | ⚠️ Core |
| RISC-V | 64-bit | ✅ Direct | ❌ External | ❌ External |
| Verilog | 64-bit reg | ✅ Direct | ❌ LUT | ❌ LUT |

### §6.2 Lean 4 Extraction (Primary Target)

```lean
-- Compile GENSIS to Lean 4
def gensisExtractLean (block : CompressedBlock) : String :=
  s!"def compressedBlock : List UInt64 := {block.compressed.map (·.val)}"
```

### §6.3 Rust Extraction

```rust
// Compile GENSIS to Rust
pub fn gensis_extract_rust(block: &CompressedBlock) -> String {
    format!("let compressed_block: Vec<u64> = vec!{:?};", 
        block.compressed.iter().map(|q| q.val).collect::<Vec<_>>())
}
```

### §6.4 Verilog Extraction

```verilog
// GENSIS compressed block as Verilog ROM
module gensis_rom #(parameter DEPTH = 64) (
    input  [5:0] addr,
    output [63:0] data
);
    reg [63:0] rom [0:DEPTH-1];
    assign data = rom[addr];
endmodule
```

---

## §7. Compiler Implementation Plan

### Phase 1: Core Q0_64 (Week 1)
- [ ] Implement `Q0_64` with all arithmetic in Lean 4
- [ ] Prove totality theorems for add/sub/mul/div
- [ ] Generate Rust/C extraction

### Phase 2: AngrySphinx Gate (Week 2)
- [ ] Implement `FrustrationMetric`, `ShellDepth`, `GearRatio`
- [ ] Prove `solveEnergyExponential` theorem
- [ ] Implement `NaNBoundary` and `PodAccumulator`

### Phase 3: Matryoshka Branes (Week 3)
- [ ] Implement `MatryoshkaShell` with all shell dimensions (0..N)
- [ ] Implement `reductionFilter` / `expansionFilter`
- [ ] Prove `reductionFilterInvariant`

### Phase 4: Full Pipeline (Week 4)
- [ ] Implement `gensisCompile` / `gensisDecompile`
- [ ] Implement semantic prime mapping
- [ ] Cross-shell communication test suite

### Phase 5: Extraction (Week 5)
- [ ] Lean 4 → Rust extraction
- [ ] Lean 4 → C extraction  
- [ ] Lean 4 → Verilog extraction
- [ ] Hardware benchmark suite

---

*GENSIS Compiler v2.0: Q0.64 0D Scalar × AngrySphinx Exponential Gate × Matryoshka Brane Layers.*
*Every shell communicates through the same 1D scalar interface. Every layer is AngrySphinx-gated.*
*The universe is a stack of nested shells, and data is the scalar that flows between them.*
