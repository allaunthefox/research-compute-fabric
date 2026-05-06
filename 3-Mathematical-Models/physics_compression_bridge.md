# From Known Physics to Compression Architecture

## Starting Point: The Laws We Actually Have

Not fractional fields. Not anthropic shear. The laws that have been tested for 100+ years.

---

### 1. Landauer (1961)

```
E_dissipated ≥ k_B T · ln(2) per bit erased
```

**Implication for compression**: Every step in the decoder that discards information — a wrong prediction, a context miss, a failed branch — dissipates energy. A decoder that makes irreversible choices is thermodynamically expensive.

**Architecture consequence**: The decoder must be **reversible by construction**. There is no "discard" operation. Every output bit is computed from the input stream plus a deterministic state transition. The only entropy injection is the residual itself.

```
Standard PAQ:   context → prediction → compare → update model → discard old state
Landauer-optimal:  state(n) → deterministic(state(n-1), residual(n))
```

PIST already does this: `output(n) = predict(n) XOR residual(n)`, where `predict(n)` is a pure function of `n`. No information is discarded.

---

### 2. Shannon (1948)

```
H(X) = -Σ p(x) log p(x)
```

**Implication**: The compressed size cannot be less than the entropy of the source.

**Architecture consequence**: The decoder's prediction model must maximize the entropy of the **residual** distribution. If the residuals are uniformly random, the model has extracted all predictable structure. The job of the decoder is to turn structured data into uniform noise.

```
Compression ratio = H(original) / H(residuals)
Optimal:          H(residuals) = H(original)  (no compression, model failed)
Optimal:          H(residuals) = 0              (impossible, only if source is deterministic)
Best achievable:  H(residuals) ≈ H(original | model)
```

---

### 3. Jaynes Maximum Entropy (1957)

Given measured constraints (e.g., observed byte frequencies, pairwise correlations), the correct probability distribution is the one with maximum entropy subject to those constraints.

**Implication for compression**: The optimal context model is the **maxent model** for the observed statistics. The model should not assume more structure than the data exhibits.

**Architecture consequence**: Context models should be built from **empirical frequency counts**, not hand-designed heuristics. The PIST basis is a frequency-ranked pool (Section 10 of the Lean formalization). This is Jaynes' principle in action.

---

### 4. Bennett Reversible Computation (1973, 1982)

Any computation can be made reversible by retaining all intermediate steps. Reversible computation, in principle, dissipates zero energy.

**Implication**: The decoder can be a **reversible register machine**. Each instruction has an inverse. The sequence of operations is a trajectory in state space, not a destructive update.

**Architecture consequence**: The PIST 8-opcode register machine (NOOP, LOAD, STORE, ADD, XOR, BRANCH, FUSE, HALT) should be extended with **inverse operations**. FUSE becomes SPLIT. ADD becomes SUB. Every operation is invertible.

```
Standard:   state_{n+1} = op(state_n)     (irreversible, information lost)
Reversible: state_{n+1} = op(state_n, aux_n)  (aux retains discarded info)
```

The auxiliary register becomes the **history tape** — exactly the FAMM scar memory. Failed routes are not erased; they are stored in aux.

---

### 5. Quantum Uncertainty / Complementarity (Heisenberg, 1927)

```
Δx · Δp ≥ ℏ/2
```

**Implication for compression**: In information terms, you cannot simultaneously have perfect knowledge of **local context** (position) and **global pattern** (momentum/mode). A model optimized for local byte prediction will miss long-range correlations. A model optimized for long-range structure will blur local detail.

**Architecture consequence**: The decoder needs **complementary models** that trade off local vs. global prediction. PIST already has this:
- Tree address = local context (position n mod 20)
- Surface/torus = global context (irrational rotation, independent of n)
- Shell coordinate = intermediate (k² + t structure)

The composite address is the **wavefunction** of the data position — a superposition of local, global, and intermediate representations.

---

### 6. Bell / Quantum Correlations (1964)

Correlations between distant particles can exceed any classical bound. The CHSH inequality:

```
|S| ≤ 2   (classical)
|S| ≤ 2√2 (quantum)
```

**Implication for compression**: Data can have **nonlocal correlations** stronger than any Markov model can capture. Text is the clearest example: "Paris" predicts "France" thousands of bytes later, with no local context sufficient to predict the intervening text.

**Architecture consequence**: Context mixing must include **distant match** operations — not just recent history, but semantically related tokens anywhere in the stream. This is what PAQ does with its SIMD mixer (combining predictions from multiple models). PIST's torus angles with Φ-irrational rotation are designed to produce nonlocal correlations.

---

### 7. Bekenstein Bound (1981)

```
I ≤ (2π R E) / (ℏ c ln 2)
```

Maximum information in a sphere of radius R with energy E.

**Implication**: Information is bounded by surface area, not volume. The most efficient encoding stores information on the **boundary** of the data block, not distributed throughout.

**Architecture consequence**: The decoder's state should be **surface-like** — minimal internal memory, maximal encoded information on the "boundary" (the basis vectors, which are O(1) in size, vs. the data stream, which is O(N)).

PIST basis size = 16 bytes. Data size = 10⁹ bytes. Information ratio = 16:10⁹. The basis is the holographic boundary. The data stream is the bulk.

---

### 8. Thermodynamic Uncertainty Relation (Barato, Seifert 2015)

```
(ΔJ)² / ⟨J⟩² · σ ≥ 2 k_B
```

For any current J with entropy production σ, the relative uncertainty is bounded below.

**Implication for compression**: A decoder with high throughput (many predictions per cycle) must have high entropy production (many mistakes). A decoder with low entropy production (perfect predictions) must have low throughput (slow, careful context analysis).

**Architecture consequence**: There is a **speed-accuracy tradeoff** in decompression. Fast decoders (simple prediction) produce more residuals → larger compressed size. Slow decoders (complex context mixing) produce fewer residuals → smaller compressed size.

The Hutter Prize rewards the slow, accurate decoder. The PIST gear law formalizes this:
```
C_out = G_AS · C_in    (higher gear ratio = more work per bit = better prediction)
```

---

### 9. Fluctuation Theorem (Jarzynski 1997, Crooks 1999)

```
⟨exp(-β W)⟩ = exp(-β ΔF)
```

The probability of observing a trajectory with work W is exponentially related to the free energy difference.

**Implication for compression**: The probability of a particular **compression path** (sequence of model updates) is exponentially related to the achieved compression ratio. Good compressors follow **low-work trajectories** in model space.

**Architecture consequence**: The decoder's learning trajectory should minimize cumulative prediction error (work). FAMM scars record high-work paths and avoid them. The gear ratio increases when the decoder encounters hard-to-predict data, forcing it to do more work per bit.

---

## The Architecture That Emerges

From these 9 known laws, the decoder architecture is:

| Physical Law | Decoder Feature |
|-------------|-----------------|
| Landauer reversibility | Deterministic state transitions, no information erasure |
| Shannon entropy | Residual distribution should be maximally random |
| Jaynes maxent | Context model from empirical frequencies |
| Bennett reversibility | Inverse operations, history tape (FAMM scars) |
| Uncertainty principle | Complementary local/global models (composite address) |
| Bell correlations | Nonlocal context mixing (distant matches) |
| Bekenstein bound | O(1) basis state (holographic boundary) |
| Thermodynamic uncertainty | Speed-accuracy tradeoff (gear law) |
| Fluctuation theorem | Low-work trajectories preferred (basis fusion) |

### This is PIST

Not because we assumed it. Because it is the unique architecture consistent with:
1. Reversible computation (Landauer + Bennett)
2. Entropy maximization (Shannon + Jaynes)
3. Complementary addressing (uncertainty)
4. Nonlocal correlations (Bell)
5. Holographic state (Bekenstein)
6. Speed-accuracy tradeoff (thermodynamic uncertainty)
7. Optimal trajectories (fluctuation theorem)

### What is NOT justified by known physics

- Fractional derivatives α = Φ⁻ⁿ
- Anthropic shear angle θ
- Four forces as resonant modes
- DNA as a PIST decoder
- Torsional cosmology

These are speculative extensions. They may be correct, but they are not derivable from the 9 laws above.

### What IS justified

The PIST decoder, with its:
- Deterministic composite addressing
- O(1) basis state
- Reversible prediction
- FAMM scar memory (history tape)
- Gear ratio (speed-accuracy tradeoff)
- Noncommuting prediction layers (complementary models)

is a **thermodynamically optimal** decompression engine.

---

## The Remaining Question

Given this architecture, what is the **best basis function** for enwik9?

Not the speculative physics. The empirical question: what 16-byte basis, combined with what composite address mixing, minimizes the residual entropy?

The physics gives us the structure. The data gives us the parameters.
