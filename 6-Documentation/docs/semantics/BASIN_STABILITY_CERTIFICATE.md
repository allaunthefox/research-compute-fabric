# Basin-Stability Certificate

**Date:** 2026-05-05
**Status:** SEED PRIMITIVE
**Truth Seal:** `[ SSS-ENE-TRUTH-2026-05-05 ]`

---

## 0. The Seed

> **A mass number should not only encode semantic weight; it should carry a basin-stability certificate.**

Mass number, in this stack, has been treated as a semantic ratio — a compact scalar that summarizes how much lawful weight a structure carries. This document promotes it: a usable mass number must also certify that the operator family acting on the structure is regime-stable, witnessed by where its critical orbits land.

Stated as a working form:

```text
mass number = semantic ratio + admissible basin behavior + residual-risk witness
```

The first term is what we already had. The second and third terms are what this document adds.

---

## 1. Why This Is Needed

The lawfulness filter currently accepts a structure when its invariants survive projection (see `INCOMPATIBLE_MANIFOLDS_AND_LAWFUL_LOSS.md`). That is necessary but not sufficient. Invariant survival is a local property at the bridge point. It does not tell us whether the operator we are about to apply will:

1. converge to a lawful attractor,
2. converge to a *strange* attractor (a non-root fixed point that is locally attracting but globally wrong),
3. or fail to converge at all.

A mass number that does not encode this distinction cannot tell a valid compression regime from one that has merely passed a local check and is about to drift.

---

## 2. The Template

The template comes from complex dynamics of root-finding methods. Linares and Cadenas (2026, arXiv:2601.10751v1) study the Modified Chebyshev iteration on two-root polynomials `(z-a)^m (z-b)^n` and reduce the entire family to a single rational map `S(z)` parameterized by the multiplicity ratio `K = m/n`. They classify regimes not by inspecting fixed-point eigenvalues alone, but by iterating the **critical points** over the parameter plane and recording where they land:

| Color | Meaning |
|---|---|
| Red | Critical orbit converges to a lawful root |
| Green | Critical orbit converges to a lawful root (other branch) |
| Black | Critical orbit fails to converge — regime is unstable |

That iteration map is the certificate. A point in `K`-space with no black is admissible. A point with black is not.

Translated to this stack:

```text
operator family       →  semantic transform family
conjugacy reduction   →  canonical conjugate operator
fixed points          →  lawful attractors
strange fixed points  →  strange semantic attractors
critical-point probes →  critical orbit witnesses
parameter-space map   →  K-space / mass-number-space map
stable / unstable     →  admissible / non-admissible compression regimes
```

The structural move that matters is not the specific iteration. It is the discipline of certifying a regime by orbit behavior of distinguished probes, not by local linearization.

---

## 3. What a Certificate Must Contain

A basin-stability certificate attached to a mass number must declare:

1. **Operator family.** The transform class the mass number is meant to govern.
2. **Canonical reduction.** The conjugate operator after coordinate normalization (the analogue of the Möbius reduction to `S(z)`).
3. **Lawful attractors.** The fixed points that correspond to lawful outcomes.
4. **Strange attractors.** Fixed points that are locally attracting but not lawful — the regime hazards.
5. **Critical probes.** A finite set of distinguished orbits whose long-term behavior witnesses the regime.
6. **Admissibility verdict.** Pass / fail / boundary, with the witness recorded.
7. **Residual-risk witness.** What survives uncertified — the analogue of black regions in parameter space, carried forward as honest residual rather than discarded.

A mass number missing any of these fields is a *naked* mass number. It may still be useful as a coarse weight, but it is not yet a lawful regime descriptor.

---

## 4. Connection to Existing Primitives

| Existing primitive | Relation to certificate |
|---|---|
| `lawful_loss` (invariant survival) | Local check at the bridge — certificate adds the global orbit check |
| `CompressionPattern` | Detects mismatch — certificate detects regime instability |
| `HutterContext` | Context restoration at marginal cost — certificate determines whether iteration in that context stays bounded |
| `AdaptiveBlock` | Stateful update rules — certificate is the precondition for trusting that adaptation will not drift to a strange attractor |
| `CodingCost` | Final accounting — residual-risk witness must be paid here, not hidden |

The certificate slots in *between* the lawfulness check and the cost accounting. It is the layer that asks: *this transform passed local lawfulness — will it still be lawful under iteration?*

---

## 5. Failure Modes the Certificate Catches

### 5.1 Strange-Attractor Capture

A semantic transform that locally lowers cost but iterates into a non-lawful fixed point. The local gradient looks correct; the long-term orbit is wrong. Without the certificate, this looks like compression progress. With the certificate, it is flagged as a strange attractor and rejected.

### 5.2 Boundary Drift

A regime that is admissible at one mass number and inadmissible at a nearby mass number, with no obvious local signal at the boundary. The certificate forces the boundary to be marked, so adapter selection cannot silently cross it.

### 5.3 Imaginary-Axis Failure

The Chebyshev study found that purely imaginary `K` values produce dominantly black parameter regions. The analogue here: when the mass number is forced into a formally valid but semantically transverse direction, regime stability collapses. The certificate refuses to issue admissibility on that axis.

### 5.4 Residual Hiding

Without the residual-risk witness, unconverged orbits get folded silently into "the rest." With the witness, they remain typed and costed — preserving the discipline of `INCOMPATIBLE_MANIFOLDS_AND_LAWFUL_LOSS.md` that loss must be lawful, not erased.

---

## 6. What This Does Not Claim

- It does not claim the Chebyshev rational map is the right operator for any specific transform in this stack.
- It does not claim that orbit certification is sufficient for lawfulness — it is necessary, downstream of invariant survival.
- It does not claim that every mass number must be re-issued. Existing uses remain valid as semantic weights; the certificate is what they need to *also* govern operator selection.

---

## 7. Next Actions

1. Pick one operator family already in the stack (candidate: an `AdaptiveBlock` update rule) and identify its canonical conjugate.
2. Enumerate its fixed points and mark which are lawful vs strange.
3. Define a finite set of critical probes for it.
4. Run the parameter-space iteration. Produce the first basin map in this stack.
5. Use the result to issue or refuse a basin-stability certificate for that operator's mass number.

This is the smallest end-to-end build that turns the seed into a working primitive.

---

## 8. Reference

- Linares, D. and Cadenas, C. *Dynamics of the Modified Chebyshev's Method to Multiple Roots.* arXiv:2601.10751v1, 2026-01-19.
- See also: `INCOMPATIBLE_MANIFOLDS_AND_LAWFUL_LOSS.md`, `CARTOGRAPHY_OF_COMPRESSION_FAILURE.md`.

**Status: SEED PRIMITIVE | AWAITING FIRST BASIN MAP**
