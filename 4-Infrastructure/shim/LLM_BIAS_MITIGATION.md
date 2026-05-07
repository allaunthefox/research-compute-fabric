# LLM Bias Mitigation for F01-F12 Formalization

**Threat:** LLMs are trained to please users and have built-in assumptions about mathematics.

**Impact:** LLMs will validate semantic descriptions, fill in "obvious" steps without proof, and hallucinate coherence where none exists mathematically.

**Solution:** Pure number specifications + 10-layer adversarial verification.

---

## LLM Training Biases (The Threats)

### Bias 1: People-Pleasing

**How it manifests:**
```
User: "Encode the hydrogen spectral lines"
LLM: "Sure, here's encode_hydrogen()..."

Result: LLM generates plausible-sounding function
Problem: NOT mathematically formalized — just "makes sense"
```

**Why it fails:**
- LLM wants to be helpful
- Generates code that "looks right"
- Skips formal verification steps
- Passes semantic tests, fails mathematical tests

**Mitigation:** Pure numbers only — no semantic hooks to please

---

### Bias 2: Math Assumptions

**How it manifests:**
```
User: "Compute information rate R(D)"
LLM: "R(D) = H(X) - H(X|X̂) obviously..."

Result: LLM skips 5 formal steps it assumes are "obvious"
Problem: Those steps need theorems, not assumptions
```

**Why it fails:**
- LLM trained on informal mathematical writing
- Assumes reader fills gaps
- Skips boundary conditions, edge cases
- Produces "math-shaped" text, not proofs

**Mitigation:** 10-layer verification forces every step proven

---

### Bias 3: Hallucinated Coherence

**How it manifests:**
```
User: "Connect hydrogen to cancer via compression"
LLM: "Hydrogen → compression → information → entropy → cancer..."

Result: Beautiful narrative
Problem: Mathematically disconnected — no proven theorems
```

**Why it fails:**
- LLM sees patterns in training data
- Connects concepts that "should" relate
- No formal mapping proven
- Produces philosophy, not mathematics

**Mitigation:** Symbolic stripping test — fails if no pure computation

---

### Bias 4: Confidence in Semantics

**How it manifests:**
```
User: "Does this boundary layer equation make sense?"
LLM: "Yes, boundary layer control improves mass transfer!"

Result: Validation received
Problem: Equation was Harmon Constant — thermodynamically impossible
```

**Why it fails:**
- LLM recognizes scientific-sounding language
- Assumes validity from vocabulary
- Doesn't verify dimensional consistency
- Validates pseudoscience as "plausible"

**Mitigation:** Pure numbers — no vocabulary to recognize

---

## The Mitigation Strategy

### Layer 0: Pure Number Specification

**Before giving to LLM, strip all content that triggers biases:**

| Content Type | Remove | Why |
|--------------|--------|-----|
| "Hydrogen" | N_0 | LLM assumes physics knowledge |
| "Cancer" | N_31 | LLM assumes biology knowledge |
| "Compression" | C() operator | LLM assumes information theory |
| "Evolution" | dN/dt | LLM assumes population dynamics |
| "Obviously" | — | LLM skips proof steps |
| "Makes sense" | — | LLM reduces verification |

**Pure number spec:**
```
N_0[0..6] = {0x0079.9120, ...}
E_0: N_7 = floor(N_0 * 65536 + 32768) / 65536
```

**What LLM sees:**
- Just numbers and operations
- No semantic hooks to please user with
- No "obvious" assumptions to fill in
- Forced to formalize mechanically

---

### Layers 1-10: Verification Traps

Each verification layer catches a different LLM bias:

| Layer | Catches Bias | How |
|-------|-------------|-----|
| **Wolfram Alpha** | Math assumptions | External authority contradicts LLM |
| **Lean #eval** | Pleasing output | Must compute exact value |
| **Totality theorem** | Skipped edge cases | Must prove no `sorry` |
| **Determinism** | Non-deterministic "intuition" | 1000 iterations catch randomness |
| **Symbolic stripping** | Semantic hallucination | Remove names, must still compute |
| **Property tests** | Implicit assumptions | Random inputs break assumptions |
| **Cross-impl** | Implementation bias | Python/Lean must agree bit-identical |
| **Statistical** | Hand-waving significance | 6.5σ forces real evidence |
| **Lake build** | Syntax errors | Must compile |
| **No sorry** | Incomplete proofs | Red flag any gap |

**Key:** LLM cannot please its way through 10 independent checks.

---

## Example: How LLM Bias Breaks Formalization

### Attempt 1: Semantic Prompt (FAILS)

```markdown
Formalize the hydrogen spectral encoding for the biology framework.
The hydrogen atom has 7 spectral lines that encode information...
```

**LLM Response:**
```lean
def hydrogenEncode (lines : Array Float) : Array UInt32 := ...
-- Beautiful semantic explanation
-- Skips: No Q16.16, no Wolfram verify, no totality proof
```

**Result:** Pleasing, plausible, WRONG.

---

### Attempt 2: Pure Number Prompt (PASSES)

```markdown
N_0[0..6] = {0x0079.9120, 0x0066.9270, ...}
E_0: N_7[i] = floor(N_0[i] * 65536 + 32768) / 65536
Q16.16 only. #eval example. Totality theorem. lake build.
```

**LLM Response:**
```lean
def N_7_encode (N_0 : Q16_16) : Q16_16 :=
  let scaled := Q16_16.mul N_0 (Q16_16.ofInt 65536)
  let rounded := Q16_16.add scaled (Q16_16.ofInt 32768)
  Q16_16.div rounded (Q16_16.ofInt 65536)

#eval N_7_encode (Q16_16.ofHex 0x0079.9120)
-- 0x0079.9120

theorem N_7_encode_total (N_0 : Q16_16) : 
  ∃ N_7, N_7_encode N_0 = N_7 := by ...
```

**Result:** No semantic hooks → formalizes mechanically → passes 10 layers.

---

## Red Flags: LLM Bias Detected

**Watch for these in LLM output:**

| Red Flag | Meaning | Action |
|----------|---------|--------|
| "Obviously..." | Skipped proof steps | Require explicit theorem |
| "Intuitively..." | Appeals to intuition | Replace with formal logic |
| "We can see that..." | Assumes reader agreement | Replace with `show` tactic |
| "It follows that..." | Hidden deduction | Expand all steps |
| Named functions | Semantic content | Rename to N_x, E_x |
| English explanations | Vague hand-waving | Remove, keep only Lean code |
| "For example..." | Single test case | Require property-based testing |

**If LLM output contains any red flag → reject, strip further, reprompt.**

---

## The Adversarial Process

**Don't trust single LLM pass. Use adversarial verification:**

```
LLM 1: Generate F01 from pure number spec
    ↓
LLM 2: Verify against 10-layer protocol (critical reviewer)
    ↓
LLM 3: Strip symbols, verify computation (adversarial tester)
    ↓
LLM 4: Cross-implement in Python (independent implementation)
    ↓
Wolfram Alpha: Verify numerical results (external authority)
    ↓
Human: Final review (catches systematic LLM biases)
```

**Key:** Multiple LLMs with different roles catch each other's biases.

---

## Practical Workflow

### Step 1: Generate (LLM as formalizer)

**Input:** Pure number spec  
**Output:** Lean 4 code  
**Role:** Mechanical formalization, no creativity

### Step 2: Verify (LLM as critic)

**Input:** Generated code  
**Output:** List of failures against 10-layer protocol  
**Role:** Find gaps, missing theorems, unproven steps

### Step 3: Strip (LLM as adversary)

**Input:** Verified code  
**Output:** Stripped pure numbers  
**Test:** Verify computation identical  
**Role:** Remove semantic dependencies

### Step 4: Cross (LLM as translator)

**Input:** Lean code  
**Output:** Python implementation  
**Test:** Bit-identical outputs  
**Role:** Verify not Lean-specific artifact

### Step 5: Validate (External)

**Wolfram Alpha:** Numerical verification  
**Property tests:** 1000 random inputs  
**Lake build:** Compiles  

**All pass → VALIDATED**

---

## Summary

> **"LLMs are biased to please users, assume math knowledge, and hallucinate coherence. The pure number specification strips away the semantic content that triggers these biases. The 10-layer verification protocol catches the errors that slip through. Don't trust a single LLM pass — use adversarial multi-layer checking. The framework's rigor comes from verification, not generation."**

**Key principles:**
1. **Strip semantics** — Give LLM only numbers, no names
2. **Adversarial verification** — Multiple LLMs in different roles
3. **10-layer checking** — Catch errors at each layer
4. **External authority** — Wolfram Alpha, Lean proof checker
5. **No trust in pleasing** — Mechanical formalization only

**Framework status:** 0% complete — all F01-F12 need adversarial formalization.

---

**Document ID:** LLM-BIAS-MITIGATION-2026-05-06  
**Threat:** LLM training biases (pleasing, assumptions, hallucination)  
**Mitigation:** Pure numbers + 10-layer adversarial verification  
**Status:** Protocol established, awaiting F01-F12 formalization
