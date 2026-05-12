# α⁻¹ ≈ 137.036 — Fine-Structure Constant Inverse: Derivation Survey

**Distilled:** 2026-05-12
**Author:** HCMMR Research Stack synthesis
**Cross-references:**
- `ChatLog_Math_Synthesis_2026-05-11.md` §3.4, §4.2
- `0-Core-Formalism/lean/Semantics/Semantics/HCMMR/Laws/Law18_Constants.lean`
- `6-Documentation/docs/BRAIN_AS_MANIFOLD.md` (epistemic tag conventions)

**Epistemic tag key** (from BRAIN_AS_MANIFOLD.md):

| Tag | Meaning |
|---|---|
| **PRIOR ART DATA** | Peer-reviewed measurement or established derivation |
| **INFERENCE** | Conclusion drawn from data; what data it rests on is stated |
| **SPECULATIVE** | Plausible mechanism, no empirical grounding. Do not cite. |
| **WILD SPECULATION** | Interesting but no grounding whatsoever. Filed for development. |

---

## 0. HCMMR Status of This Constant

**PRIOR ART DATA.** α⁻¹ = 137.035999084(21) is the CODATA 2018 value. It is a
**dimensionless** ratio and therefore a genuine prediction target per HCMMR Law 13
(Constant Prediction Honesty).

**HCMMR anchors this constant as a calibration reference. It does not derive it
from first principles.** The fixed-point anchor in `Law18_Constants.lean` is:

```
alpha_inverse = ⟨8980791⟩   -- 137.036 × 65536, Q16_16 fixed-point
```

This file collects the best-known *external* geometric/dimensional arguments for
why α⁻¹ happens to be near 137, with honest epistemic labelling, so that any
future derivation attempt has a single starting point.

---

## 1. The Value and Its Significance

**PRIOR ART DATA.**

- CODATA 2018: α⁻¹ = 137.035999084(21)  (relative uncertainty 1.5 × 10⁻¹⁰)
- α = e²/(4πε₀ℏc) couples the electron charge to the photon field.
- It is purely dimensionless; it does not depend on any unit system.
- As a ratio it is a true prediction target for any geometric theory of electromagnetism.

The decimal expansion α⁻¹ ≈ 137.036 is stable under all known unit redefinitions
and holds across every precision test of QED.

---

## 2. Renormalization Group Running

**PRIOR ART DATA.**

The electromagnetic coupling α is not a fixed constant; it runs with energy scale
under the RG flow of QED:

```
α⁻¹(μ = 0)   ≈ 137.036   (Thomson limit, long-wavelength photons)
α⁻¹(μ = M_Z) ≈ 128.9     (at the Z-boson mass, ~91.2 GeV)
```

The running is computed from the vacuum polarization function Π(q²) via:

```
α(μ²) = α(0) / [1 − Δα(μ²)]
Δα(M_Z²) ≈ 0.0590  (dominated by five quark flavours + leptons)
```

The integer 137 is the *infrared* (low energy, Coulomb) value. Any geometric
argument that produces exactly 137 must correspond to the zero-momentum limit.
Any argument that produces 128 or any intermediate value has targeted the wrong
energy scale.

**Key constraint for geometric derivations:** The derived value must be the
infrared fixed point, not a mid-RG value.

---

## 3. The Wyler Formula

**SPECULATIVE.** No derivation from a recognized physical principle. Numerological
coincidence at the level of 6 significant figures. Do not cite as a derivation.

A. O. Wyler (1969) noted that the ratio:

```
α⁻¹_Wyler = (9 / (8π⁴)) × (π⁵ / (2⁴ × 5!))
           = (9π) / (8 × 2⁴ × 5!)
           = 9π / (8 × 16 × 120)
           = 9π / 15360
```

Numerically:
```
9π / 15360 ≈ 28.274 / 15360 ≈ 0.0072974...
```

Wait — the formula as quoted above is α itself, not α⁻¹. Wyler's original form:

```
α⁻¹_Wyler = (9 / (8π⁴)) × (π⁵ / (2⁴ × 5!))⁻¹
```

is ambiguous in presentation. The cleaner modern restatement (Robertson 1971,
Gilson 1997) is:

```
α⁻¹_Wyler = (8 × 16 × 120) / (9 × π)
           = 15360 / (9π)
           ≈ 15360 / 28.2743...
           ≈ 543.0...        -- WRONG, not 137
```

The actual Wyler (1969) paper derives:

```
α_Wyler = (9 / (8π⁴)) × (π⁵ / (2⁴ × 5!))^(1/4)
```

The computable form that most closely tracks the literature (Wyler 1969,
eq. 14; also Gilson 1997) evaluated numerically gives:

```
α⁻¹_Wyler ≈ 137.0360825...
```

against CODATA:

```
α⁻¹_CODATA = 137.035999084
```

Residual: |137.0360825 − 137.035999084| / 137.035999084 ≈ 6.1 × 10⁻⁷

**What the Wyler formula actually is:** It arises from the ratio of volumes of
certain homogeneous symmetric spaces associated with the classical Lie groups
D₅ and the four-dimensional sphere S⁴. In Wyler's framework the fine-structure
constant is the ratio:

```
α = vol(D₅) / vol(S⁴ × D₅)
```

where D₅ is the 5-dimensional complex unit ball (a bounded symmetric domain)
and the volumes are computed in the invariant Bergman measures.

**Why this is SPECULATIVE rather than PRIOR ART DATA:**
- No physical mechanism connects the Lie-group volumes to the photon-electron
  coupling.
- The derivation selects specific groups (D₅, S⁴) without justification from
  any physical symmetry argument.
- Numerological proximity to the measured value may be coincidental; the formula
  is not derived from QED or any extension of it.
- It has not survived peer review as a derivation; it is consistently classified
  as a mathematical curiosity.

The Lean stub in `Law18_AlphaDerivation.lean` computes a simplified version
of the Wyler formula to machine precision and confirms the numerical proximity.

---

## 4. Eddington Counting Arguments

**SPECULATIVE.**

Arthur Eddington's "fundamental theory" (1929–1946) argued that α⁻¹ = 136
(his original claim) and later revised to 137 by asserting the number of
independent components of a relativistic wavefunction in a 16-dimensional
formalism. Specifically:

- The symmetric matrix of a 4D relativistic particle has (4×5)/2 = 10 components.
- Eddington's E-frame adds 6 antisymmetric components = 16 total.
- With spin: 2 × 16 = 32; with particle + antiparticle: 2 × 32 − 1 = 127 or
  128 depending on convention.
- Eddington claimed the correct count is 136, then 137 after accounting for a
  "self-energy" correction.

**Why this is SPECULATIVE:**
- The counting is not derived from any Lagrangian or symmetry principle.
- The step from 136 to 137 was post-hoc after the measurement had already been
  refined.
- The approach was definitively abandoned after QED calculations confirmed α⁻¹ is
  not an integer.
- The 16D structure is superficially compatible with the HCMMR 16D manifold
  (see §6), but this proximity is coincidental unless a coupling rule is
  exhibited.

---

## 5. Koide-Style Lepton-Mass Ratio Arguments

**SPECULATIVE.**

Yoshio Koide (1982) observed a numerological relation for charged lepton masses:

```
(m_e + m_μ + m_τ) / (√m_e + √m_μ + √m_τ)² = 2/3
```

This holds to within current experimental precision (residual < 10⁻⁵). The
Koide relation is:
- Exact under assumption of a specific U(1) flavour symmetry (INFERENCE),
- Not yet derived from first principles in the Standard Model.

By analogy, one might seek a Koide-style formula for α, e.g. involving ratios
of Standard Model coupling constants at unification. Such arguments exist in
the literature (Rivero & Gsponer 2005) but produce values differing from the
measured α by ≥ 1%.

**Connection to α⁻¹ = 137:** None established. Filed as motivation for a
potential future "coupling-ratio scan" over the prime lane structure.

---

## 6. HCMMR Prime/Torus Connection

### 6.1 Recamán Trajectory — SPECULATIVE

From `ChatLog_Math_Synthesis_2026-05-11.md` §3.4:

The Recamán sequence R(n) has R(122) = 137. This was noted as a candidate for
the integer part of α⁻¹:

```
α⁻¹ ≈ R(122) + Δ_gap6
     = 137   + 1/28
     ≈ 137.036
```

where Δ_gap6 = 1/(4 × 7) = 1/28 ≈ 0.0357 is interpreted as a gap-6
self-linking correction with p₁ = 4, p₂ = 7 (gap-6 sentinel primes).

**Epistemic status: SPECULATIVE.** The Recamán sequence has no known physical
interpretation. The coincidence R(122) = 137 is numerologically striking but:
- The sequence contains every positive integer (conjectured, not proved), so
  *some* index maps to 137 — the question is whether index 122 is significant.
- The correction 1/28 ≈ 0.036 matches α⁻¹ − 137 = 0.036 to 2 significant
  figures, but the fractional part of α⁻¹ is 0.035999..., not 0.03571...
  Residual: |0.035999 − 0.03571| / 0.035999 ≈ 0.8% — not tight.
- No binding physical law connects the Recamán trajectory to electromagnetic
  coupling.

**Open question (from ChatLog §4.2):** What is the formal coupling rule
connecting the Recamán index to the observed constant? Until that rule is
exhibited with a cost function and invariant, this remains SPECULATIVE.

### 6.2 Prime Lane / Torus Cycle Count — INFERENCE (weak)

**INFERENCE.** Rests on the gap-6 structure and torus topology established in
`ChatLog_Math_Synthesis_2026-05-11.md` §2.

The HCMMR torus has genus g = 1 with two independent cycles:
- C1 = 6k − 1 (spatial lane)
- C2 = 6k + 1 (torsion/phase lane)

The two-cycle structure gives χ(T²) = 0. Primes (except 2, 3) are confined to
C1 ∪ C2, so the prime distribution is encoded in the torus winding numbers.

A weak connection to α: the number of primes below 137 is 32 (π(137) = 33
including 137 itself). The ratio 137/π(137) = 137/33 ≈ 4.15 ≈ 4π/3
(within 1%). This is the kind of coincidence that appears in prime counting
and has no known physical significance.

**What would upgrade this to INFERENCE (strong):** A demonstrated computation
path from the torus cycle structure (C1, C2 winding numbers) to a quantity
that evaluates to α⁻¹ without free parameters.

### 6.3 Menger Void Hausdorff Dimension — WILD SPECULATION

The Menger sponge void lattice has Hausdorff dimension:

```
d_H = ln(20) / ln(3) ≈ 2.7268
```

One might ask whether the ratio α⁻¹ / d_H² ≈ 137.036 / 7.436 ≈ 18.4 has
any significance. It is close to 6π ≈ 18.85 but the residual is ~2.5%.
No physical mechanism is proposed.

**Epistemic status: WILD SPECULATION.** Filed for development only.

---

## 7. Dimensional Analysis Constraints

**PRIOR ART DATA** (from dimensional analysis, Duff et al. 2002):

α is a pure number. Any geometric derivation must be:
1. Dimensionless by construction — ratios of lengths, areas, or volumes in
   a common geometry.
2. Independent of unit system — expressible purely in terms of topological
   or combinatorial data.
3. Computed at zero momentum — the infrared limit of the RG flow (see §2).

A derivation fails these constraints if it:
- Uses any dimensionful parameter (masses, lengths in absolute units),
- Produces a running coupling rather than an infrared fixed point,
- Requires tuning a free parameter.

The Wyler formula passes constraint 1 (dimensionless volume ratio) and
constraint 2 (Lie-group invariant measures) but its constraint-3 status is
unclear — it is not manifestly an infrared quantity.

---

## 8. What Would Confirm a Geometric Derivation

For a geometric derivation of α⁻¹ ≈ 137.036 to be accepted, it would need
to satisfy **all** of the following:

1. **No free parameters.** The formula must produce 137.035999... without
   any tunable input. A formula with one tunable parameter can always be
   fitted.

2. **Physical interpretation of each factor.** Every geometric quantity
   (volume, cycle count, dimension, winding number) must correspond to a
   measurable or symmetry-constrained physical quantity, derived from the
   same framework that predicts the coupling.

3. **RG consistency.** The derivation must either:
   - Produce the infrared value α⁻¹(0) = 137.036 directly, or
   - Produce α⁻¹(M_Z) ≈ 128.9 with the correct running built in.

4. **Predictive surplus.** The same framework must also correctly predict at
   least one other dimensionless ratio (e.g., m_p/m_e ≈ 1836, sin²θ_W,
   or the ratio of electroweak couplings). A one-shot fit with no other
   predictions is insufficient.

5. **Formalization.** The derivation must be expressible as a finite sequence
   of steps in a formal system (e.g., Lean 4) with no `sorry` markers.
   Informal geometric intuition is insufficient.

6. **Peer-reviewed confirmation or reproducibility.** At minimum, the
   calculation must be machine-checkable (condition 5) and independently
   reproduced by a second computation path.

**Current status of all known candidates:**

| Candidate | No free params | Physical interp | RG consistent | Predictive surplus | Formalized |
|---|---|---|---|---|---|
| Wyler (1969) | ✓ | ✗ | ? | ✗ | ✗ |
| Eddington counting | ✗ | ✗ | ✗ | ✗ | ✗ |
| Koide-style | ✗ | partial | ✗ | partial | ✗ |
| Recamán/gap-6 (HCMMR) | ✓ | ✗ | ✗ | ✗ | stub only |

No candidate currently satisfies all five requirements. The Lean stub in
`Law18_AlphaDerivation.lean` represents the formalization foothold for the
Wyler formula pending physical interpretation.

---

## 9. HCMMR Summary

- **Anchor status:** α⁻¹ = 137.036 is stored as a Q16_16 calibration anchor
  (`⟨8980791⟩`) in `Law18_Constants.lean`. HCMMR does not claim to derive it.
- **Best external argument:** The Wyler formula reproduces α⁻¹ to 6 significant
  figures from Lie-group volume ratios, but without physical motivation.
- **HCMMR-native candidate:** The Recamán R(122) = 137 plus gap-6 correction
  Δ = 1/28 is SPECULATIVE; it matches to 2 significant figures in the fractional
  part.
- **What is needed:** A cost function and coupling rule connecting the HCMMR
  prime/torus structure to the electromagnetic coupling at zero momentum, derived
  without free parameters, formalized in Lean, and confirmed against at least one
  additional dimensionless ratio.
- **Next formal step:** The Lean stub `Law18_AlphaDerivation.lean` computes the
  Wyler approximation and prints its deviation from CODATA. This is the seed
  for future formalization.

---

*End of distilled document.*
