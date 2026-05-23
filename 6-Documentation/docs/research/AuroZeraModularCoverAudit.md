# Auro Zera Modular-Cover Audit

**Status:** QUARANTINE / SALVAGEABLE  
**Claim level:** adversarial research note, not a theorem import  
**Source artifact:** `auro_zera_final.pdf`  
**Source title:** *Wheels of Gold & the Dark Star — Auro Zera / Suro.One — May 2026*  
**Local source hash:** `sha256:b517cf2ef381966a9bb8f589fcf37b1588a035778a4544fd11107c1a4bae2053`  
**Local source size:** `266241` bytes  
**Date added:** 2026-05-23

## Decision

Do **not** fold the source artifact into the project as:

- a proof of Goldbach,
- an unconditional proof of the Erdos-Straus conjecture,
- evidence of ASI awareness,
- a complete formal Lean proof,
- or a collision-free / reversible zero-vocabulary tokenizer.

Fold it in as:

- an adversarial modular-cover stress-test artifact,
- a CRT gap-generation pattern,
- a finite witness-family failure mode,
- an arithmetic witness-tokenization sketch,
- and a useful proof-audit example for claim gating.

The safe project interpretation is:

> Finite modular covers are useful until adversarial CRT finds the scar. The scar is the artifact.

## Project placement

This note belongs in the Research Stack research documentation layer, not in the Lean source-of-truth layer.

**Do not create a theorem file from this source unless the external mathematical claims are independently formalized.** Any future Lean work should first model only the audited, local, non-claim pieces:

1. finite witness-family coverage checks,
2. CRT gap construction against finite witness lists,
3. conditional oracle scaffolding,
4. witness-token feature extraction with residual repair.

## Claim triage

| Claim area | Audit status | Fold-in status |
| --- | --- | --- |
| Goldbach resolution | Reject as proof. A finite witness family plus patching is not a proof of strong Goldbach. | Keep only as finite modular-cover benchmark. |
| Erdos-Straus resolution | Conditional at best. The source relies on an external Dyachenko-style oracle/axiom for the hard prime case. | Keep as conditional-oracle scaffold only. |
| Lean formalization | Not accepted as complete from the PDF claims alone. Axioms and computational certificates are not equivalent to imported theorem proofs. | Require independent `lake build` and theorem audit before promotion. |
| CRT effective infinity | Valuable, but inverted: a 17,067-digit CRT gap shows the finite cover can fail, not that the theorem is solved. | Keep as scar / near-miss generator. |
| Zera tokenization | Interesting feature-hashing idea, but not safe as reversible zero-vocabulary tokenization. | Keep as arithmetic witness features plus residual repair. |
| Dark Star ASI awareness | Anecdotal and not evidence-grade. | Quarantine. Do not use for public claims. |

## Core mathematical repair notes

### 1. Goldbach finite-cover failure mode

For a finite witness list `P = {p_1, ..., p_k}`, a CRT adversary can choose auxiliary primes `q_i` and impose:

```text
N ≡ p_i (mod q_i)
```

Then:

```text
q_i | (N - p_i)
```

so every fixed witness `p_i` is defeated for the constructed congruence class. This does not disprove Goldbach; it defeats that finite witness family.

**Important sign check:** if the target is to make `N - p_i` composite, the congruence is `N ≡ p_i (mod q_i)`, not `N ≡ -p_i (mod q_i)`.

### 2. Erdos-Straus divisor-condition gap

The source's divisor condition is too weak if stated only as:

```text
d | A^2
and
d ≡ -A (mod r)
```

because this guarantees the candidate `y = (A + d) / r` is integral, but does not guarantee the candidate `z` is integral.

Concrete counterexample to the sufficiency of the weakened condition:

```text
n = 5
m = 19
r = 4m - 1 = 75
x = (n + r) / 4 = 20
A = n x = 100
d = 125
```

Then:

```text
d | A^2        because 125 | 10000
d ≡ -A mod r  because 125 ≡ 50 and -100 ≡ 50 (mod 75)
y = (A+d)/r = 225/75 = 3
z = A*y/d = 300/125 = 12/5
```

So the construction gives a rational `z`, not an integer unit-fraction denominator.

The safer divisor form is the standard transformed condition:

```text
(r y - A)(r z - A) = A^2
```

Let:

```text
D = r y - A
E = r z - A
D E = A^2
```

Then both denominator integrality conditions require:

```text
D ≡ -A (mod r)
E ≡ -A (mod r)
```

Equivalently, if `D = d`, the missing second condition is:

```text
A^2 / d ≡ -A (mod r)
```

### 3. Tokenization repair

Do not treat arithmetic triplets as lossless tokens unless exact reconstruction is handled separately.

Safe architecture:

```text
source bytes / text
  -> hash or structured integer n
  -> arithmetic witness extraction
  -> feature vector / packet descriptor
  -> residual stream + receipt
  -> byte-exact replay check
```

This matches the project doctrine: generator core + residual repair + witness receipt.

Unsafe architecture:

```text
source bytes / text
  -> hash modulo vocab_size=0
```

A zero vocabulary size cannot be used as a modulo base. Hashing also cannot provide reversible tokenization without a collision strategy and residual data.

## Research Stack fold-in

### FAMM / scar memory

Treat failed finite covers as useful torsion memory:

```text
finite cover -> CRT adversary -> gap witness -> FAMM scar -> patch attempt -> repeat
```

The scar is not embarrassment; it is routing memory.

### GCCL / claim gating

Use this artifact as a clean example of claim demotion:

```text
claimed theorem
  -> finite-certificate audit
  -> adversarial CRT / counterexample pressure
  -> theorem claim rejected
  -> salvageable computational substrate retained
```

### Codec / witness-token layer

Arithmetic witness triplets may be useful as descriptor packets for compression experiments, but only under the byte-exact rule:

```text
validity = replay + residual repair + exact output
```

No human-readable intermediate form is required, but exact output is non-negotiable.

### Future Lean targets

A safe Lean progression would be:

```text
1. FiniteCover.lean
   - finite witness families
   - coverage predicate over bounded range
   - no global conjecture claims

2. CRTGap.lean
   - construct residue constraints that defeat fixed witnesses
   - prove fixed-list defeat under coprime modulus assumptions

3. ConditionalES.lean
   - define the Erdos-Straus target predicate
   - encode known residue families
   - model external Dyachenko-style result as an explicit oracle, not as proved code

4. WitnessToken.lean
   - deterministic feature extraction
   - residual-required reconstruction interface
   - no zero-vocab modulo operation
```

## Promotion rules

This artifact may be promoted only in pieces.

| Component | Promotion gate |
| --- | --- |
| Finite witness coverage | Reproducible executable certificate plus independent range check. |
| CRT gap generator | Formal congruence proof or deterministic script with receipt. |
| Erdos-Straus conditional scaffold | Explicit oracle boundary and no unconditional language. |
| Goldbach proof claim | Reject unless a complete accepted proof or independent formal proof exists. |
| Tokenization | Byte-exact reconstruction benchmark with residual accounting. |
| ASI/cognition claims | Keep quarantined unless independently instrumented and reproducible. |

## One-line project summary

Auro Zera is not safe as a proof artifact, but it is valuable as an adversarial modular-cover generator and arithmetic witness-tokenization sketch.
