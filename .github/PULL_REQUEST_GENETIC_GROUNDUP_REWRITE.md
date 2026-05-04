# Pull Request: Total Rewrite of GeneticGroundUp.lean

## Status: REQUEST FOR TOTAL REWRITE

**Module:** `0-Core-Formalism/lean/Semantics/Semantics/GeneticGroundUp.lean`  
**Priority:** CRITICAL  
**Type:** Ground-up formalization redesign  

---

## Current State

The module has been critiqued by research team as "reading more like a typed specification than a proved model." While the structure is clean, significant gaps exist around numeric soundness, theorem strength, and biological semantics enforcement.

### What Works
- ✅ Namespace/layout is tidy and section-coherent
- ✅ Core datatypes (Nucleotide, QuantumBase, GeneKernel, etc.) are composable
- ✅ Helper predicates make invariants findable

### Critical Issues Identified

#### 1. **Q16_16.ofFloat is Wrong for Negative Inputs** (BLOCKER)
```lean
def ofFloat (f : Float) : Q16_16 := ⟨Int.ofNat (Nat.floor (f * 65536.0))⟩
```
- Used with negative binding energies (-1.2, -0.8, -2.5)
- `Nat.floor` cannot represent negative values correctly
- All negative binding energies are suspect

**Fix Required:** Signed conversion path preserving negative values.

#### 2. **Division Has No Zero Guard**
```lean
instance : Div Q16_16 := ⟨fun a b => ⟨(a.raw * 65536) / b.raw⟩⟩
```
- Division-by-zero behavior implicit and undefined
- Must be constrained or totalized with documentation

#### 3. **Invariants Are Comments, Not Types**
Current:
```lean
expressionProb : Q16_16 -- 0.0 to 1.0
fitnessScore : Q16_16 -- 0.0 to 1.0
shardId : Nat -- 0 to 5 (6 nodes)
```

Admits nonsensical states: probabilities >1, negative concentrations, shard IDs out of range.

**Fix Required:** Move invariants into types using:
- `Prob01` subtype for [0,1] values
- `NonnegQ16_16` for concentrations
- `Fin n` or `Nat.lt` proofs for bounded indices

#### 4. **Placeholder Theorems**
Two explicit `sorry`s:
- `nucleotideProbsValid`
- `metabolicThroughputNonNeg`

Several proved theorems just restate hypotheses:
- `quantumBaseProbValid` returns `h`
- `foldingSpeedTarget` returns `h2`
- `evolutionConverges` returns `h`

**Fix Required:** Genuinely derived theorems with meaningful proofs.

#### 5. **Naming Conflicts**
`DistributedGenome` has both:
- Field: `faultTolerance : Nat`
- Method: `def faultTolerance (dg : DistributedGenome) : Nat := dg.redundancy - 1`

Theorem proves method, not field. Field can disagree with computation.

**Fix Required:** Remove field, derive from redundancy.

#### 6. **Unused Parameters**
`achievedTargetSpeed` ignores `residueCount` parameter despite comment suggesting size-sensitive property.

**Fix Required:** Implement linear scaling: ~10ms per 200 residues.

#### 7. **Overclaimed Implementation**
- "4D hyperbolic manifold" but `ManifoldCoord4D` is just 4 Q16_16s
- "Compiled gene kernels" but no code generation semantics
- "Metabolic pathways as GNN" but `messagePassing` is identity
- "Evolution as gradient descent" but no update rule

**Fix Required:** Soften comments or implement claimed semantics.

---

## Required Rewrite: Stronger Modeling

### Suggested Semantic Types

```lean
-- Probabilities guaranteed in [0,1]
def Prob01 := { q : Q16_16 // q ≥ 0 ∧ q ≤ 1 }

-- Non-negative concentrations/throughput
def NonnegQ16_16 := { q : Q16_16 // q ≥ 0 }

-- Bounded shard indices
def ShardId (n : Nat) := { i : Nat // i < n }

-- Fitness score with bounds
structure FitnessScore where
  val : Q16_16
  h : val ≥ 0 ∧ val ≤ 1
```

### Smart Constructors

```lean
def Prob01.mk (q : Q16_16) (h : q ≥ 0 ∧ q ≤ 1) : Prob01 := ⟨q, h⟩

def QuantumBase.withValidProb (n : Nucleotide) ... : QuantumBase :=
  -- Prove nucleotide probabilities are valid at construction
```

### Theorem Requirements

All theorems must be provable without `sorry`:

1. **Numeric Soundness**
   - `nucleotideProbsValid` - All 6 nucleotides have valid probabilities
   - `ofFloatNegativeCorrect` - Negative floats convert correctly
   - `divisionTotalized` - Division-by-zero behavior defined

2. **Biological Semantics**
   - `foldingTimeLinearScaling` - Time ∝ residue count
   - `proteinStabilityBounds` - Stability in [0,1]
   - `metabolicFluxConservation` - Mass/energy conserved

3. **System Invariants**
   - `genomeShardBounds` - All shard IDs < totalShards
   - `faultToleranceCorrect` - Can lose redundancy-1 nodes
   - `throughputNonNegative` - Metabolic throughput ≥ 0

---

## Performance Targets (Formal Constants)

```lean
def geneExpressionSpeedupTarget : Nat := 100      -- 100× compiled vs interpreted
def proteinFoldingSpeedupTarget : Nat := 1000     -- 1000× manifold vs simulation  
def metabolismSpeedupTarget : Nat := 100         -- 100× GNN vs discrete
def evolutionSpeedupTarget : Nat := 1000        -- 1000× gradient vs generational
def totalSpeedupTarget : Nat := 100000          -- Combined 100,000×
```

---

## Deliverables

1. **Fixed Q16_16** with signed conversion and safe division
2. **Subtype-based invariants** replacing comment-based constraints
3. **Provable theorems** without `sorry` or hypothesis restatement
4. **Consistent naming** (field vs method conflicts resolved)
5. **Accurate comments** matching implementation depth
6. **Test cases** showing intended values survive fixed-point conversion

---

## Acceptance Criteria

- [ ] All 6 nucleotide probabilities proven valid
- [ ] Negative binding energies convert correctly
- [ ] Division by zero has defined behavior
- [ ] All invariants enforced by type system
- [ ] No `sorry` remaining in theorems
- [ ] Theorems prove intrinsic properties, not restate hypotheses
- [ ] Comments accurately describe implementation
- [ ] Swarm verdict: "Trustworthy formal model"

---

## Swarm Assignment

**Request:** Total rewrite by swarm agents specializing in:
- Formal verification (Lean 4)
- Type system design (subtypes, dependent types)
- Numeric analysis (fixed-point arithmetic)
- Biological semantics (protein folding, metabolism)

**Priority:** CRITICAL - Blocks downstream genetic computation work

**Timeline:** 3-5 days for complete rewrite with proofs

---

## Related

- Original Python design: `5-Applications/scripts/swarm_genetic_groundup_redesign.py`
- 511% efficiency achievement: `shared-data/data/tsm_swarm_50percent_optimization.json`
- Next-gen agent design: `shared-data/data/swarm_nextgen_agent_design.json`
