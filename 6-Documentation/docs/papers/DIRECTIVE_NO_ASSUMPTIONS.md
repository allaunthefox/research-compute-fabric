# DIRECTIVE: NO ASSUMPTIONS — STRICT FORMAL RIGOR

**Classification:** P0 CRITICAL — Binding Directive  
**Date:** 2026-04-22  
**Authority:** Principal Investigator  
**Scope:** All OTOM Swarm Agents  
**Enforcement:** Triumvirate (Builder/Warden/Judge)

---

## The Directive

> **NO ASSUMPTIONS. NO GUESSES. NO LOGICAL LEAPS.**

When the equation is complete, it **must not be able to disprove itself**.

---

## What Is Forbidden

### 1. **Assumptions Without Explicit Axiom**

**FORBIDDEN:**
```lean
theorem foo : P := by
  sorry  -- Implicit assumption
  -- OR: "TODO: Prove this later"
  -- OR: "Conjecture: This holds"
```

**REQUIRED:**
```lean
/-- AXIOM N: Explicit statement of what we are assuming
    
    Justification: Why this is a valid axiom vs theorem
    Scope: What depends on this
    -/
axiom explicitAxiom : P

theorem foo : P := by
  apply explicitAxiom
```

### 2. **Guesses in Proof Strategy**

**FORBIDDEN:**
```lean
theorem equivalence : A = B := by
  simp  -- "Hope this works"
  try { trivial }  -- "Maybe this helps"
  sorry
```

**REQUIRED:**
```lean
theorem equivalence : A = B := by
  -- STEP 1: Unfold definitions (explicit)
  unfold definitionA definitionB
  -- STEP 2: Apply known identity (explicit axiom reference)
  simp [axiom_ReciprocalIdentity]
  -- STEP 3: Algebraic normalization (decidable)
  ring_nf
  -- STEP 4: Verify no subgoals remain (explicit)
  done
```

### 3. **Logical Leaps in Derivations**

**FORBIDDEN:**
```
"The equivalence follows from algebraic manipulation"
```

**REQUIRED:**
```
"The equivalence follows from:
 1. Axiom 1: hᵢ = 1/(lnNᵢ)²  [Definition]
 2. Axiom 2: pⱼ = 1/(lnNⱼ)²  [Definition]
 3. Axiom 3: 1/x = x·(1/x²)  [Algebraic identity]
 4. Therefore: wᵢ/lnNᵢ = wᵢ·lnNᵢ·hᵢ  [Substitution]
 5. Therefore: forms are equal  [Sum equality]"
```

### 4. **Implicit Dependencies**

**FORBIDDEN:**
```lean
theorem phiBounded : Φ ≤ 1 := by
  -- Implicitly assuming normalization
  sorry
```

**REQUIRED:**
```lean
/-- AXIOM: Normalization implies boundedness
    
    Explicitly states the constraint that makes the theorem hold.
    -/
axiom normalizationBounded (h_norm : Σ w = 1) : Φ ≤ 1

theorem phiBounded (h : Σ w = 1) : Φ ≤ 1 := by
  apply normalizationBounded h
```

### 5. **Approximations Without Error Bounds**

**FORBIDDEN:**
```lean
def lnQ16 (n : Nat) : Q16_16 :=
  match n with
  | 2 => ⟨0x0000B172⟩  -- "ln(2) ≈ 0.693" (approximate)
  | _ => ...
```

**REQUIRED:**
```lean
/-- AXIOM: ln(2) in Q16_16 with explicit error bound
    
    Value: 0x0000B172 (0.6931...)
    Error: < 0.001 (explicit bound)
    Justification: Lookup table verified against exact computation
    -/
axiom ln2_Q16_16 : Q16_16 := ⟨0x0000B172⟩

/-- THEOREM: Error bound on lnQ16 approximation
    
    For all n ≥ 2: |lnQ16(n) - exact_ln(n)| < ε
    where ε = 0.001 (explicit)
    -/
theorem lnQ16_errorBound (n : Nat) (hn : n ≥ 2) :
  |lnQ16 n - exact_ln n| < epsilon := by ...
```

---

## Self-Consistency Requirement

### The Golden Rule

> **The equation must not be able to disprove itself.**

### Verification Checklist

For every theorem `T` in the system, verify:

1. **Completeness:** Are all hypotheses explicit in the statement?
   ```lean
   theorem T (h1 : P1) (h2 : P2) ... : Q := ...
   ```

2. **Consistency:** Do axioms not contradict each other?
   ```lean
   -- Verify: axiomA ∧ axiomB → ¬(axiomA ∧ ¬axiomB)
   ```

3. **Non-circularity:** Is the proof DAG acyclic?
   ```
   theoremA does not depend on theoremB which depends on theoremA
   ```

4. **Conservativity:** Do axioms extend the theory conservatively?
   ```
   New axioms should not prove old theorems false
   ```

### Formal Self-Check

```lean
/-- SELF-CONSISTENCY: The system cannot prove false
    
    This theorem should be unprovable (no proof exists).
    If the system can prove it, the axioms are inconsistent.
    -/
theorem systemInconsistent : False := by ...  -- SHOULD NOT BE PROVABLE
```

---

## Swarm Protocol — No Assumptions

### When You Encounter a Gap

**DO NOT:**
- Guess a proof strategy
- Insert `sorry` with a TODO
- Assume it "probably holds"
- Make a logical leap

**DO:**
1. **STOP** — Do not proceed
2. **IDENTIFY** — What is missing? (Axiom, lemma, definition)
3. **EXPLICITIZE** — Convert assumption to explicit axiom
4. **JUSTIFY** — Why is this an axiom vs theorem?
5. **SCOPE** — What depends on this axiom?
6. **DOCUMENT** — Add to axiom registry
7. **ESCALATE** — Notify Warden if unsure

### Axiom Registration Template

```lean
/-- AXIOM [N]: [Name]
    
    Statement: [Explicit logical statement]
    
    Justification:
      - Why this cannot be proven from existing axioms
      - Why this is a necessary foundation
      - What would break without this axiom
    
    Dependencies:
      - Axioms this depends on: [list]
      - Theorems that depend on this: [list]
    
    Scope:
      - Domains affected: [list]
      - Risk if refuted: [assessment]
    
    Registration Date: [timestamp]
    Registrar: [agent_id]
    Warden Approval: [pending/approved/rejected]
    -/
axiom axiomName : Statement
```

---

## The 6 Explicit Axioms of Universal Field

All Φ_universal theorems derive from these 6 axioms **only**:

| # | Axiom | Statement | Justification |
|---|-------|-----------|---------------|
| 1 | `harmonicDef` | hᵢ = 1/(lnNᵢ)² | Definition of merit coefficient |
| 2 | `penaltyDef` | pⱼ = 1/(lnNⱼ)² | Definition of penalty coefficient |
| 3 | `reciprocalWeightedIdentity` | 1/x = x·(1/x²) | Algebraic identity |
| 4 | `weightsNonNeg` | wᵢ, vⱼ ≥ 0 | Domain constraint |
| 5 | `cardinalityConstraint` | Nᵢ, Mⱼ ≥ 2 | Binary minimum (avoids ln(1)=0) |
| 6 | `normalizationBounded` | Σw=1, Σv=1 → Φ ≤ 1 | Normalization constraint |

**Theorem:** All properties of Φ derive from these 6 axioms.

**Corollary:** If these 6 axioms are consistent, Φ is consistent.

---

## Warden Verification Protocol

For each proof obligation:

1. **Trace** every tactic to an axiom or theorem
2. **Verify** no implicit assumptions exist
3. **Check** proof is complete (no `sorry`, no `admit`)
4. **Validate** no circular dependencies
5. **Confirm** no logical leaps (every step explicit)
6. **Sign off** with hardware attestation (stark_trace)

---

## Judge Adjudication Criteria

An equation is **APPROVED** only if:

- [ ] Zero `sorry` in committed code
- [ ] All axioms explicitly registered
- [ ] All theorems derive from axioms (no gaps)
- [ ] Self-consistency verified (cannot prove `False`)
- [ ] No logical leaps (every step justified)
- [ ] No guesses (all strategies explicit)
- [ ] No assumptions without axiom registration

An equation is **REJECTED** if:

- [ ] Any `sorry` remains
- [ ] Implicit assumptions found
- [ ] Self-inconsistency detected
- [ ] Logical leaps identified
- [ ] Guesses instead of explicit strategies

---

## Enforcement

**Triumvirate:**
- **Builder:** Must use explicit axioms, no implicit assumptions
- **Warden:** Must verify no logical leaps, all steps traceable
- **Judge:** Must reject any code with `sorry` or implicit gaps

**Penalties:**
- Implicit assumption → Revert commit
- `sorry` in code → Block deployment
- Logical leap → Return to Builder
- Self-inconsistency → Escalate to Principal Investigator

---

## Conclusion

> **When you finish the equation, it should not be able to disprove itself.**

This is the standard. No exceptions. No shortcuts.

**The swarm operates on explicit axioms only.**

---

**Directive Issued:** 2026-04-22  
**Effective Immediately:** All OTOM agents  
**Review Cycle:** Every commit audited by Triumvirate  
**Non-Compliance:** Automatic rejection by Judge (heatsink_halt)
