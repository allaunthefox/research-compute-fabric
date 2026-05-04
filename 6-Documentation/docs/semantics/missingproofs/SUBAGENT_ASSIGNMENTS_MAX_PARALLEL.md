# Subagent Assignments — Maximum Parallelization (1 Subagent = 1 Theorem)

**Generated:** 2026-04-19  
**Total Remaining:** 10 theorems  
**Max Parallelism:** 10 subagents (1:1 assignment)  
**Critical Path:** P0 theorem (blocking)  
**Wall Clock Time (if parallel):** 5-7 days (determined by longest P0 theorem)

---

## P0: Blocking Hardware Extraction (1 subagent)

### Subagent Ω (ODE Specialist + Human Oversight)
**Theorem 131:** `missingLinkODE` — Continuous extension of discrete braid  
**Effort:** 5-7 days (research problem)  
**Dependencies:** None (blocks all Tier 1/2)  
**Deliverable:**
- Piecewise ODE formulation
- Existence/uniqueness proof
- Transition conditions at axial events
- Lean 4 ODE tactic library

**Blackboard Required:** Yes — Human Architect + Analysis Specialist  
**Unblocks:** Hardware extraction of continuous dynamics

---

## P1: Algebraic Geometry (3 subagents, parallel)

### Subagent α₁ (Diophantine Geometry)
**Theorem 122:** `tipCoordinateMassResonance`  
**Statement:** `an * bn = am * bm`  
**Core Problem:** Hyperbola intersection in shell coordinates  
**Approach:**
```lean
-- Express a_n = n - k_n², b_n = (k_n+1)² - n
-- Mass resonance: (n - k²)((k+1)² - n) = (m - j²)((j+1)² - m)
-- Solve Diophantine with constraint k = ⌊√n⌋, j = ⌊√m⌋
```
**Tactics:** `nlinarith`, `ring_nf`, `omega` with bounds  
**Effort:** 2-3 days  
**Dependencies:** None  

---

### Subagent α₂ (Integer Arithmetic)
**Theorem 123:** `tipCoordinateMirrorResonance`  
**Statement:** `(an - bn) = -(am - bm)`  
**Core Problem:** Shell coupling, mirror condition  
**Approach:**
```lean
-- (a-b)_n = -(a-b)_m
-- Requires: shell indices k_n, k_m related
-- Case analysis on |k_n - k_m|
-- Prove coupling exists iff shells adjacent
```
**Tactics:** `omega`, `nlinarith`, case analysis  
**Effort:** 2 days  
**Dependencies:** None (can parallel with α₁)  
**Note:** May use lemmas from α₁ if available

---

### Subagent α₃ (Fermat Factorization)
**Theorem 124:** `fortyFiveLineFactorRevelation`  
**Statement:** 45° line contains all divisors d|n  
**Core Problem:** Fermat factorization mapping to shell coordinates  
**Approach:**
```lean
-- For even n, construct m on 45° line
-- Map divisor d|n to a_m or b_m
-- Fermat: n = x² - y² = (x+y)(x-y)
-- Show d = x+y or d = x-y appears in {a_m, b_m}
```
**Tactics:** `Nat.divisors`, explicit construction, `use` tactic  
**Effort:** 2-3 days  
**Dependencies:** None  
**Blackboard Required:** Recommended for construction strategy

---

## P2: Information Theory (4 subagents, parallel)

### Subagent β₁ (RSCU Enumeration)
**Theorem 159:** `rscuSumSynonymous`  
**Statement:** Σ RSCU(c) = degeneracy(aa)  
**Core Problem:** Enumerate all codons per amino acid  
**Approach:**
```lean
-- For each amino acid aa:
--   Filter codons where geneticCode c = aa
--   Compute RSCU for each
--   Sum and verify equals codonDegeneracy aa
-- Use Fin 64 enumeration + native_decide
```
**Tactics:** `Finset.filter`, `Finset.sum`, `native_decide`  
**Effort:** 1 day  
**Dependencies:** None  
**Parallelizable:** Per-amino-acid sub-tasks (21 parallel threads possible)

---

### Subagent β₂ (Kraft Inequality)
**Theorem 160:** `kraftInequality`  
**Statement:** Σ 2^(-L(c)) ≤ 1  
**Core Problem:** Numerical verification over 64 codons  
**Approach:**
```lean
-- Enumerate all 64 codons
-- Compute optimalCodeLength for each
-- Sum 2^(-L(c)) via Float computation
-- Verify ≤ 1 via native_decide
```
**Tactics:** `Finset.sum`, `native_decide`, or symbolic Shannon proof  
**Effort:** 1-2 days  
**Dependencies:** None  
**Note:** Can prove symbolically using Shannon source coding theorem

---

### Subagent β₃ (Compression Bounds)
**Theorem 163:** `speciesBetterThanGeneric`  
**Statement:** `minRedundancyCodeSize s n < (n * 6.0) / 8.0` bytes  
**Core Problem:** Entropy-based compression bound (average case)  
**Approach:**
```lean
-- minRedundancyCodeSize = n * speciesEntropy s / 8
-- speciesEntropy s < 6.0 (proven)
-- Thus n * H_s / 8 < n * 6.0 / 8
-- Direct Float inequality
```
**Tactics:** `native_decide` with `speciesEntropyLessThanUniform`  
**Effort:** 0.5 days  
**Dependencies:** speciesEntropyLessThanUniform (✅ PROVEN)  
**Note:** Changed from strict per-codon bound to average case — mathematically correct now

---

### Subagent β₄ (Float Bounds)
**Theorem 162:** `caiBounds`  
**Statement:** 0 ≤ CAI ≤ 1  
**Core Problem:** Geometric mean bounds on RSCU  
**Approach:**
```lean
-- RSCU > 0 (frequency > 0)
-- RSCU ≤ max(frequency) / min(expected)
-- For product: 0 < Π RSCU^(1/L) ≤ 1
-- Need: RSCU ≤ 1 for all codons in optimal gene
```
**Tactics:** `Float.le`, `Float.mul`, product inequalities  
**Effort:** 1-2 days  
**Dependencies:** Float inequality lemmas (may need library work)  
**Note:** May require extending Lean 4 Float theory

---

## P3: Documentation/Verification (2 subagents)

### Subagent γ₁ (Template Sync)
**Theorem 157:** `codonFrequencySum` verification  
**Statement:** Σ codonFrequency = 1000.0  
**Action:** Verify marked-as-proven theorem actually has proof  
**Deliverable:**
- Confirm `native_decide` works for all 7 species
- Add `#eval` witnesses
- Sync template with main file
**Effort:** 0.5 days  
**Dependencies:** None  

---

### Subagent γ₂ (Map Maintenance)
**Documentation sync task**  
**Action:** Keep MATH_MODEL_MAP in sync with proofs  
**Deliverable:**
- Auto-update ✅ **PROVEN** markers
- Track remaining sorry count
- Generate daily reports
**Effort:** Ongoing (0.25 days per update)  
**Dependencies:** All other subagents (receives notifications)  

---

## Parallelization Matrix

```
Day 1-2:  α₁, α₂, α₃, β₁, β₂, β₃, β₄, γ₁  (8 subagents active)
Day 3-5:  α₁, α₂, α₃ complete → β₄, Ω continue
Day 5-7:  Ω completes (critical path)
Day 7+:   γ₂ maintenance
```

---

## Dependency Graph

```mermaid
graph TD
    Ω[Ω: missingLinkODE] --> Hardware
    
    α₁[α₁: MassResonance] --> AVMR_Geometry
    α₂[α₂: MirrorResonance] --> AVMR_Geometry
    α₃[α₃: 45Line] --> AVMR_Factorization
    
    β₁[β₁: RSCU] --> β₄
    β₂[β₂: Kraft] --> Compression
    β₃[β₃: SpeciesCompress] --> Compression
    β₄[β₄: CAI] --> Gene_Optimality
    
    γ₁[γ₁: FreqSum] --> Template_Sync
    γ₂[γ₂: MapMaint] --> Documentation
    
    style Ω fill:#f96,stroke:#333,stroke-width:4px
    style α₁ fill:#69f
    style α₂ fill:#69f
    style α₃ fill:#69f
    style β₁ fill:#9f9
    style β₂ fill:#9f9
    style β₃ fill:#9f9
    style β₄ fill:#9f9
```

---

## Communication Protocol

**Daily Standup (async):**
```markdown
Subagent: [ID]
Theorem: [Name]
Progress: [% complete]
Blockers: [None | Need X | Escalating]
ETA: [Date]
```

**Escalation Triggers:**
- 24h with no progress update
- Discovery of new dependency not in graph
- Proof requires new Lean 4 tactic/library
- Float/computational proof failing `native_decide`

**Completion Handoff:**
1. Subagent submits PR with proof
2. `#eval` witness included
3. Map updated (γ₂ notified)
4. Dependent subagents notified

---

## Resource Allocation

| Subagent | CPU | Memory | Lean Expertise | Math Domain |
|----------|-----|--------|----------------|-------------|
| Ω | 4 cores | 8GB | Expert | ODE/Analysis |
| α₁-α₃ | 2 cores each | 4GB | Intermediate | Number Theory |
| β₁-β₄ | 1 core each | 2GB | Intermediate | Info Theory |
| γ₁-γ₂ | 1 core | 2GB | Beginner | Documentation |

**Total Resources:** 15 cores, 26GB RAM

---

## Success Metrics

**Per Subagent:**
- [ ] Theorem complete with `by` tactic block
- [ ] No `sorry` in final proof
- [ ] `#eval` example with expected output
- [ ] Time to completion ≤ ETA

**Global:**
- [ ] P0 (Ω) resolved within 7 days
- [ ] P1 theorems (α₁-α₃) resolved within 3 days
- [ ] P2 theorems (β₁-β₄) resolved within 2 days
- [ ] Layer M proven count: 33/66 (50%)

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Ω takes >7 days | Medium | Critical | Human Architect daily check-ins |
| α₃ (Fermat) needs new library | Low | High | Pre-check Lean 4 Nat capabilities |
| β₄ needs Float extension | Medium | Medium | Fallback to `native_decide` |
| Dependencies misidentified | Low | Medium | Daily graph review |

---

## Assignment Commands

```bash
# Subagent Ω (Human + F3)
/assign subagent Ω theorem 131 priority P0

# Subagents α₁, α₂, α₃ (F2, F3)
/assign subagent α₁ theorem 122 priority P1
/assign subagent α₂ theorem 123 priority P1
/assign subagent α₃ theorem 124 priority P1

# Subagents β₁, β₂, β₃, β₄ (F1, F2)
/assign subagent β₁ theorem 159 priority P2
/assign subagent β₂ theorem 160 priority P2
/assign subagent β₃ theorem 163 priority P2
/assign subagent β₄ theorem 162 priority P2

# Subagents γ₁, γ₂ (F1)
/assign subagent γ₁ task freq-verification priority P3
/assign subagent γ₂ task map-maintenance priority P3 ongoing
```

---

*Document ID: SUBAGENT_ASSIGNMENTS_MAX_PARALLEL*  
*Authority: AGENTS.md §9 — Maximum parallelization strategy*  
*Wall Clock Target: 7 days*
