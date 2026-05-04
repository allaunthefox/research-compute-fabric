# Subagent Assignments — Remaining AVMR Theorems

**Generated:** 2026-04-19  
**Total Remaining:** 10 theorems across 4 difficulty tiers  
**Priority:** P0 (blocking hardware extraction) → P3 (research enrichment)

---

## Tier 1: Algebraic Geometry (P1 — 3 theorems)

**Location:** `0-Core-Formalism/lean/Semantics/Semantics/AVMR.lean`  
**Domain:** Number theory, hyperbola intersection, shell geometry  
**Estimated Effort:** 2-3 days each

### Theorem 122: `tipCoordinateMassResonance`
**Statement:** `an * bn = am * bm` for resonance condition  
**Gap:** Requires solving hyperbola intersection equation  
**Mathematical Approach:**
- Express a_n, b_n in terms of n, k_n = ⌊√n⌋
- Mass resonance occurs when ab_i = ab_j
- This is a Diophantine equation on hyperbola branches
- Use `nlinarith` with proper bounds on a, b

**Subagent Assignment:**  
→ **Agent F2 (Algebra Specialist)**  
Required: Number theory, nonlinear arithmetic, `nlinarith` mastery  
Deliverable: Complete proof with explicit bounds extraction

---

### Theorem 123: `tipCoordinateMirrorResonance`
**Statement:** `(an : Int) - (bn : Int) = -((am : Int) - (bm : Int))`  
**Gap:** Shell coupling between different k values  
**Mathematical Approach:**
- Mirror resonance: (a-b)_i = -(a-b)_j
- Requires relating shells k_i and k_j
- Use `omega` for integer constraints
- May need case analysis on |k_i - k_j|

**Subagent Assignment:**  
→ **Agent F2 (Algebra Specialist)**  
Required: Integer arithmetic, case analysis, shell geometry  
Deliverable: Proof with coupling condition explicit

---

### Theorem 124: `fortyFiveLineFactorRevelation`
**Statement:** For even n, 45° line contains all divisors d|n in {a_m, b_m}  
**Gap:** Fermat factorization mapping  
**Mathematical Approach:**
- Fermat's factorization: n = x² - y² = (x+y)(x-y)
- Map to shell coordinates: a = x - k, b = k + 1 - x
- Requires constructing m for each divisor
- Use `Nat.divisors` and explicit construction

**Subagent Assignment:**  
→ **Agent F3 (Number Theory Specialist)**  
Required: Fermat factorization, divisor theory, explicit constructions  
Deliverable: Existence proof with constructive witness

---

## Tier 2: Information Theory (P2 — 4 theorems)

**Location:** `0-Core-Formalism/lean/Semantics/Semantics/AVMR.lean`  
Domain: Float computation, enumeration, summation  
**Estimated Effort:** 1-2 days each

### Theorem 159: `rscuSumSynonymous`
**Statement:** Σ_{c ∈ aa} RSCU(c) = d (degeneracy)  
**Gap:** Enumeration over all codons for an amino acid  
**Mathematical Approach:**
- Use `Fin 64` to enumerate all codons
- Filter by `geneticCode c = aa`
- Compute sum and prove equals `codonDegeneracy aa`
- Can use `native_decide` for each amino acid case

**Subagent Assignment:**  
→ **Agent F1 (Enumeration Specialist)**  
Required: Fintype, enumeration tactics, summation  
Deliverable: Proof by exhaustive check or symbolic sum

---

### Theorem 160: `kraftInequality`
**Statement:** Σ_{c: Codon} 2^(-L(c)) ≤ 1  
**Gap:** Computation over all 64 codons  
**Mathematical Approach:**
- Enumerate all 64 codons
- Compute `optimalCodeLength` for each
- Verify sum ≤ 1 via `native_decide`
- Or prove symbolically using Shannon's source coding

**Subagent Assignment:**  
→ **Agent F1 (Enumeration Specialist)**  
Required: Float computation, summation, `native_decide`  
Deliverable: Numerical verification proof

---

### Theorem 163: `speciesBetterThanGeneric`
**Statement:** `minRedundancyCodeSize s n < (n.toFloat * 6.0) / 8.0` (average case bound)  
**Gap:** Float inequality with entropy  
**Mathematical Approach:**
-- minRedundancyCodeSize = n * speciesEntropy s / 8
-- speciesEntropy s < 6.0 (proven)
-- Direct Float inequality: n * H_s / 8 < n * 6 / 8
**Note:** Changed from per-codon bound (false for rare codons) to average case
**Subagent Assignment:**  
→ **Agent F1 (Enumeration Specialist)**  
Required: Float inequalities, summation bounds  
Deliverable: Direct corollary of speciesEntropy theorem

---

### Theorem 162: `caiBounds`
**Statement:** `0.0 ≤ cai s gene ∧ cai s gene ≤ 1.0`  
**Gap:** Bounds on geometric mean of RSCU  
**Mathematical Approach:**
- RSCU > 0 by definition
- RSCU ≤ max frequency / min expected
- Use Float bounds and product inequalities
- May need `sorry` for Float inequality lemmas

**Subagent Assignment:**  
→ **Agent F2 (Algebra Specialist)**  
Required: Float arithmetic, geometric mean bounds  
Deliverable: Tight bounds proof

---

## Tier 3: Continuous Dynamics (P0 — 1 theorem)

**Location:** `0-Core-Formalism/lean/Semantics/Semantics/AVMR.lean`  
**Domain:** ODE/SDE, continuous extension  
**Estimated Effort:** 5-7 days (research problem)

### Theorem 131: `missingLinkODE`
**Statement:** Continuous limit: d/dt(a,b) = (1,-1) + ε·∇J  
**Gap:** Requires continuous extension of discrete braid dynamics  
**Mathematical Approach:**
- Between axial events: linear drift
- At events: gradient ascent on J
- Needs piecewise ODE formulation
- May require new Lean 4 tactics for ODEs

**Subagent Assignment:**  
→ **Agent F3 (Analysis Specialist) + Human Architect**  
Required: ODE theory, differential inclusions, continuous dynamics  
Deliverable: Formalized ODE system with existence proof  
**Note:** This is a genuine research gap, not just formalization

---

## Tier 4: Documentation (P3 — 2 theorems)

**Location:** `docs/semantics/missingproofs/AVMR_Theorems.lean`  
**Purpose:** Template completeness

### Theorem 157: `codonFrequencySum`
**Statement:** Σ codonFrequency = 1000.0  
**Status:** Marked PROVEN in template  
**Action:** Verify or implement `native_decide` proof  
**Subagent:** Agent F1 (quick verification)

### Theorem 160 (template): `kraftInequality_Missing`
**Status:** Duplicated in template  
**Action:** Sync with main file, mark appropriately  
**Subagent:** Agent F1 (documentation sync)

---

## Summary Matrix

| Tier | Priority | Count | Assignee | Domain | Effort |
|------|----------|-------|----------|--------|--------|
| 1 | P1 | 3 | Agent F2 + F3 | Algebraic Geometry | 6-9 days |
| 2 | P2 | 4 | Agent F1 | Information Theory | 4-8 days |
| 3 | P0 | 1 | Agent F3 + Human | ODE/Analysis | 5-7 days |
| 4 | P3 | 2 | Agent F1 | Documentation | 1 day |
| **Total** | — | **10** | — | — | **16-25 days** |

---

## Cross-Dependencies

```
missingLinkODE (P0)
    └── Depends on: tipCoordinateMassResonance (P1)
    └── Blocks: Hardware extraction of continuous dynamics

rscuSumSynonymous (P2)
    └── Enables: caiBounds proof
    └── Enables: kraftInequality proof

speciesBetterThanGeneric (P2)
    └── Depends on: speciesEntropyLessThanUniform (✅ PROVEN)
    └── Enables: Compression engine formalization
```

---

## Success Criteria

**Per Theorem:**
- [ ] `lake build` passes with zero errors
- [ ] `#eval` example with expected output
- [ ] No `sorry` or `admit` in proof term
- [ ] Reference in MATH_MODEL_MAP marked ✅ **PROVEN**

**Global:**
- [ ] Layer M proven count ≥ 30 (currently 23)
- [ ] P0 theorems resolved
- [ ] Hardware extraction unblocked

---

## Communication Protocol

1. **Claim:** Comment on this file with theorem ID + ETA
2. **Progress:** Daily updates in `#lean-semantics` channel
3. **Blockers:** Escalate to Human Architect after 2 days stuck
4. **Completion:** PR with proof + `#eval` witness + map update

**Blackboard Sessions Required For:**
- Theorem 131 (missingLinkODE)
- Theorem 124 (Fermat factorization)

---

*Document ID: SUBAGENT_ASSIGNMENTS_2026-04-19*  
*Authority: AGENTS.md §9 — Subagent delegation*
