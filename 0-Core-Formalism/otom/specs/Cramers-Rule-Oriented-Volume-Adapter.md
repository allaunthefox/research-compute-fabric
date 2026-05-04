# Cramer's Rule as an Oriented-Volume Adapter

## Status

`BEAUTIFUL_PROVISIONAL`

Source pointer: <https://www.reddit.com/r/LinearAlgebra/comments/1t2vd4m/geometric_meaning_of_cramers_rule_for_a_33_system/>

The Reddit source was supplied by the project author as a public explanatory reference for the geometric interpretation of Cramer's rule. Live page details were not independently verified in this commit environment.

---

## One-sentence definition

```text
Cramer's rule extracts coordinates by comparing oriented volumes after replacing one basis column while holding the complementary reference face fixed.
```

---

## Algebraic form

Given a nonsingular system:

```math
A\vec{x}=\vec{b}
```

with column vectors:

```math
A=[\vec{a}_1\ \vec{a}_2\ \cdots\ \vec{a}_n]
```

Cramer's rule defines:

```math
x_k=\frac{\det(A_k)}{\det(A)}
```

where `A_k` is obtained by replacing the kth column of `A` with `b`:

```math
A_k=[\vec{a}_1\ \cdots\ \vec{a}_{k-1}\ \vec{b}\ \vec{a}_{k+1}\ \cdots\ \vec{a}_n]
```

---

## Oriented-volume interpretation

The determinant of `A` is the oriented n-volume of the basis cell:

```math
\det(A)=\operatorname{Vol}_{or}(\vec{a}_1,\ldots,\vec{a}_n)
```

The determinant of `A_k` is the oriented n-volume after replacing the kth basis vector by the target vector:

```math
\det(A_k)=\operatorname{Vol}_{or}(\vec{a}_1,\ldots,\vec{a}_{k-1},\vec{b},\vec{a}_{k+1},\ldots,\vec{a}_n)
```

Therefore:

```math
x_k=\frac{\operatorname{Vol}_{or}(A_k)}{\operatorname{Vol}_{or}(A)}
```

The sign of `x_k` records whether the replacement preserves or reverses orientation relative to the original basis cell.

---

## Shared reference-face cancellation

For each coordinate `x_k`, both `A` and `A_k` share the same complementary face:

```math
F_k=\operatorname{span}(\vec{a}_1,\ldots,\vec{a}_{k-1},\vec{a}_{k+1},\ldots,\vec{a}_n)
```

In three dimensions, for example:

| Coordinate | Shared face |
|---|---|
| `x_1` | face spanned by `a_2, a_3` |
| `x_2` | face spanned by `a_1, a_3` |
| `x_3` | face spanned by `a_1, a_2` |

Since oriented volume is base-face measure times signed perpendicular component:

```math
\operatorname{Vol}_{or}(A)=\operatorname{Area}_{or}(F_k)\,h_{a_k}
```

```math
\operatorname{Vol}_{or}(A_k)=\operatorname{Area}_{or}(F_k)\,h_b
```

then:

```math
x_k=\frac{h_b}{h_{a_k}}
```

So `x_k` is also the signed ratio of perpendicular components relative to the same reference face.

---

## Adapter interpretation

Define a Cramer adapter:

```math
\alpha_{Cramer}:(A,\vec{b},k)\rightarrow x_k
```

with:

```math
\alpha_{Cramer}(A,\vec{b},k)=\frac{\det(A_k)}{\det(A)}
```

Admissibility condition:

```math
\det(A)\neq 0
```

The adapter fails when the denominator cell has zero oriented volume:

```math
\det(A)=0\Rightarrow\text{basis cell is degenerate}
```

---

## OTOM interpretation

In OTOM terms:

| Linear algebra object | Geometric meaning | OTOM role |
|---|---|---|
| `A` | denominator basis cell | reference manifold cell |
| `det(A)` | oriented volume | denominator witness |
| `A_k` | replaced-column cell | translated candidate cell |
| `det(A_k)` | replacement volume | numerator witness |
| `F_k` | complementary shared face | invariant interface |
| `x_k` | signed volume ratio | coordinate extraction / translation coefficient |
| sign of `x_k` | orientation agreement/opposition | orientation-state witness |

Core claim:

```text
A coordinate is a signed volume ratio over a shared invariant reference face.
```

This makes Cramer's rule a small, exact example of a lawful manifold adapter.

---

## Relation to semantic basin shapers

Cramer's rule is a benign example of controlled basin shaping in mathematics:

```text
hold a reference face fixed
replace exactly one direction
measure the signed volume response
```

This prevents ambiguity because the comparison is not free-floating. It is anchored to a shared face.

In semantic terms:

```text
translation without a shared reference face is drift-prone
translation with a shared reference face is measurable
```

---

## Relation to SCW-8192

SCW-8192 uses salt domains and adapter digests as causal reference faces.

The analogy is bounded:

```text
Cramer's rule: shared geometric face stabilizes coordinate extraction.
SCW-8192: shared salt / schema / adapter context stabilizes interpretation extraction.
```

Forbidden overclaim:

```text
Cramer's rule proves SCW-8192.
```

Allowed use:

```text
Cramer's rule supplies a clean mathematical analogy for reference-face-bound translation.
```

---

## Failure modes

| Failure | Meaning |
|---|---|
| `det(A)=0` | degenerate basis; no unique coordinate extraction |
| wrong column replacement | coordinate index mismatch |
| sign ignored | orientation information lost |
| face not shared | ratio no longer measures the intended coordinate |
| determinant treated as scalar-only | geometric witness discarded |
| analogy overextended | mathematical result misused outside linear setting |

---

## Claim ladder

### `BEAUTIFUL_PROVISIONAL`

- Use as an analogy for reference-face-bound translation in OTOM.
- Use as a pedagogical model for signed-volume coordinate extraction.

### `CALIBRATED_ENGINEERING_DELTA`

- Use inside a implemented linear adapter where determinant ratios are computed and tested.
- Use in geometry/projection code with explicit degeneracy checks.

### `REVIEWED`

- Formalize determinant/oriented-volume statements in Lean or another proof assistant.
- Add tests proving coordinate reconstruction when `det(A) != 0`.

---

## Minimal implementation checklist

- [ ] Add determinant-ratio adapter type.
- [ ] Add degeneracy guard for `det(A)=0`.
- [ ] Add orientation-sign tests.
- [ ] Add reconstruction test: `A*x=b`.
- [ ] Add Lean theorem for Cramer's coordinate extraction.
- [ ] Add diagram reference as non-authoritative explanatory source.

---

## Summary

```text
Cramer's rule is coordinate extraction by oriented-volume replacement over a shared reference face.
```

That makes it a compact model for lawful translation: change one direction, preserve the reference interface, and measure the signed response.
