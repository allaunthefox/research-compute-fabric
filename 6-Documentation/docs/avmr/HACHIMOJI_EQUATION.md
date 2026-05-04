# THE EQUATION — Hachimoji Extension

## From 4 Bases to 8: The Generalized Form

---

## The Generalized Equation

For a genetic alphabet of size N = 2^m bases:

```
encode?(n) = κ_A(n) ∧ κ_C(n) ∧ [J_m(n) > 0]
```

where:

```
n = k^m + a,    b = (k+1)^m - n,    k = ⌊n^(1/m)⌋
```

```
J_m(n) = Σᵢ₌₁^m aᵢ·bᵢ·F_{m,i}  +  Σᵢ₌₁^m (aᵢ-bᵢ)·F_{p,i}  +  ⟨χ, F_c⟩
```

The sum runs over the m base-pair types.

---

## DNA (m = 2, N = 4)

The original equation:

```
J₂(n) = a₁·b₁·F_{m,1} + a₂·b₂·F_{m,2}
      + (a₁-b₁)·F_{p,1} + (a₂-b₂)·F_{p,2}
      + ⟨χ, F_c⟩

a₁,b₁ = GC content     F_{m,1} = 3-H-bond field (~41 kJ/mol)
a₂,b₂ = AT content     F_{m,2} = 2-H-bond field (~27 kJ/mol)
```

---

## Hachimoji (m = 3, N = 8)

The extended equation:

```
J₃(n) = a₁·b₁·F_{m,1} + a₂·b₂·F_{m,2} + a₃·b₃·F_{m,3}
      + (a₁-b₁)·F_{p,1} + (a₂-b₂)·F_{p,2} + (a₃-b₃)·F_{p,3}
      + ⟨χ, F_c⟩

a₁,b₁ = GC content    F_{m,1} ~ 41 kJ/mol  (3 H-bonds)
a₂,b₂ = SB content    F_{m,2} ~ 43 kJ/mol  (3 H-bonds)
a₃,b₃ = AT+PZ content F_{m,3} ~ 28 kJ/mol  (2 H-bond average)

F_{p,1} = GC skew     (leading vs lagging strand)
F_{p,2} = SB skew     (replication-induced asymmetry)
F_{p,3} = (AT+PZ) skew
```

---

## What Changes

| Component | DNA (4 bases) | Hachimoji (8 bases) |
|-----------|--------------|---------------------|
| Shell | `n = k² + a` | `n = k³ + a` |
| Mass field | 2 parameters (GC, AT) | 3 parameters (GC, SB, AT+PZ) |
| H-bond energies | 2 types (2, 3) | 3 types (2, 3-strong, 3-weak) |
| Genetic code | 4³ = 64 codons | 8³ = 512 codons |
| codonLUT entries | 64 | 512 |
| Top handle count | 2 (GC, AT) | 3 (GC, SB, AT+PZ) |

## What Stays the Same

| Invariant | Reason |
|-----------|--------|
| 3-point contact | Physical B-DNA helix structure (3 recognition surfaces) |
| Gate logic κ_A ∧ κ_C ∧ J > 0 | Multi-layer consensus required |
| 1/n progressive binding | Topological entropy law |
| Score law ℓₜ structure | Thermodynamic cost structure |

---

## The Key Difference

In DNA, the interaction score J₂(n) = 0 defines a **curve** in the (a₁, a₂) plane — the set of positions where energy vanishes.

In hachimoji, J₃(n) = 0 defines a **surface** in the (a₁, a₂, a₃) volume — a 2D manifold embedded in 3D composition space.

This means:
- DNA has **1 throat dimension** (the GC-AT balance axis)
- Hachimoji has **2 throat dimensions** (a surface of stable configurations)

The hachimoji genome has MORE stable configurations — a larger "throat" — because the extra base pairs provide additional degrees of freedom for energy optimization.

---

## Thermodynamic Data (Kumawat & Sherrill 2023)

| Pair | H-bonds | Energy (kJ/mol) | S3C Classification |
|------|---------|-----------------|-------------------|
| G:C | 3 | ~41 | F_{m,1} — strong 3-bond |
| S:B | 3 | ~43 | F_{m,2} — strong 3-bond (slightly stronger) |
| A:T | 2 | ~27 | F_{m,3} — weak 2-bond |
| P:Z | 2 | ~29 | F_{m,3} — weak 2-bond (slightly stronger) |

The energy differences (~2 kJ/mol between GC and SB, ~2 kJ/mol between AT and PZ) are small but measurable, and they define the separate mass fields F_{m,1}, F_{m,2}, F_{m,3}.

---

## References

1. Hoshika S. et al. (2019). "Hachimoji DNA and RNA: A genetic system
   with eight building blocks." Science, 363, 884-887. (554 citations)

2. Kumawat A., Sherrill C.D. (2023). "Evaluating the hydrogen bonding
   of hachimoji base pairs." Physical Chemistry Chemical Physics, 25,
   22699-22711. (16 citations)

3. Negi S. et al. (2023). "Hachimoji DNA: Structure and its comparison
   with the four, six, and eight-lettered natural and unnatural genetic
   alphabets." International Journal of Molecular Sciences. (2 citations)

4. Eberlein C.K. et al. (2020). "Tautomeric equilibria in DNA: a study
   of hachimoji expanded alphabets." Chemical Science, 11, 12307.
   (45 citations)
