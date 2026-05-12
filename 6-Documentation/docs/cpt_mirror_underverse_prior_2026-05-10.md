# CPT Mirror Underverse Prior

Status: `EXTERNAL_REFERENCE_PRIOR`

Claim boundary: this is a bounded external physics prior for Underverse
accounting. It does not prove a mirror universe, does not prove dark matter or
dark energy, does not promote a cosmology fit, and does not change the Lean
Underverse packet semantics. It only gives a useful symmetry-accounting pattern:
a globally conserved symmetry may appear locally broken when only one sector is
visible.

User seed:

```text
https://www.popularmechanics.com/space/deep-space/a71234773/mirror-universe-cpt/
```

Primary source for the seed article:

```text
M. M. Chaichian, M. Gogberashvili, M. N. Mnatsakanova, T. Tsiskaridze,
CPT Violation, Mirror World and Implications for Baryon Asymmetry,
European Physical Journal C 86, 425 (2026)
arXiv:2603.22381
DOI: 10.1140/epjc/s10052-026-15592-5
```

Precedent source:

```text
Latham Boyle, Kieran Finn, Neil Turok,
CPT-Symmetric Universe,
Physical Review Letters 121, 251301 (2018)
arXiv:1803.08928
DOI: 10.1103/PhysRevLett.121.251301
```

## Physics Kernel

The 2026 paper proposes a paired-universe model:

```text
visible sector
  + coordinate-reversed mirror sector
  -> globally CPT-symmetric system
  -> local CPT violation allowed inside each sector
  -> possible inflaton / anti-inflaton mass difference
  -> altered reheating temperatures
  -> baryon asymmetry in both sectors
```

The useful Research Stack reading is not "the mirror universe is true." The
useful reading is:

```text
local ledger imbalance may be the visible half of a larger symmetry account
```

That is Underverse-shaped.

## Minimal Equation Pack

CPT transform as a discrete account inversion:

```text
C: charge conjugation        q -> -q
P: parity / spatial mirror   x -> -x
T: time reversal             t -> -t

CPT: (q, x, t) -> (-q, -x, -t)
```

Paired-sector bookkeeping:

```text
U_total = U_visible + U_mirror

CPT_global(U_total) = U_total

CPT_local(U_visible) may fail while CPT_global still closes
```

Baryon-asymmetry observable:

```text
B_U = (n_b - n_bar_b) / s ~ 10^-10
```

Inflaton-field sketch from the 2026 paper:

```text
ddot(phi) + 2 (dot(a)/a) dot(phi)
  + (a^2 m^2 + ddot(a)/a) phi = 0
```

With:

```text
phi(t)  ~ t^(-3/2) exp(+i m t / c)
phi'(t) ~ t^(-3/2) exp(-i m t / c)
```

The mirror-sector field is treated as the coordinate-reversed companion needed
to keep the larger symmetry account coherent.

## Mapping To Underverse

| CPT/mirror concept | Underverse analogue |
|---|---|
| visible universe | promoted / positive equation surface |
| mirror universe | hidden complement / Underverse ledger |
| local CPT violation | local route appears imbalanced |
| global CPT conservation | full ledger closes across visible + hidden sectors |
| opposite chirality | route orientation/reflection bit |
| reversed microscopic time | inverse receipt direction / rollback lane |
| inflaton/anti-inflaton mass split | asymmetric cost or scalar-load split |
| baryon asymmetry | small visible residue after cancellation |

New Underverse variant:

```text
U_CPT_MIRROR
terminal: HOLD_CPT_MIRROR_ACCOUNTING
meaning: global symmetry may require a hidden mirror/complement ledger before
         local imbalance can be interpreted
promotion rule: hold until both visible and mirror-side accounting functions,
                transforms, and receipts are declared
```

## Stack Rule

```text
If a local equation appears to violate a conservation, symmetry, orientation, or
time-accounting law, do not immediately promote the violation as a discovery.
First ask whether the missing term belongs in the Underverse as a typed mirror
ledger.
```

This gives a cleaner split:

```text
positive equation surface:
  what was admitted and replayed

Underverse mirror ledger:
  what was excluded, reversed, unpaid, hidden, or required for global closure
```

## HOLD Boundaries

These remain HOLD:

```text
mirror universe as established fact
dark matter or dark energy explanation
baryogenesis proof
inflation model promotion
Research Stack cosmology fit
Lean theorem promotion
compression/Hutter claim
hardware/FPGA/ASIC claim
```

Allowed use:

```text
external CPT/mirror-world prior
Underverse complement-accounting analogy
chirality and time-reversal route warning
global-vs-local symmetry receipt pattern
```

## Next Local Fixture

A small local fixture can model this without cosmology:

```text
given a transition T with visible residual R_v:
  construct mirror candidate M(T)
  compute mirrored residual R_m
  check closure: R_v + R_m <= epsilon
  if missing mirror receipt: HOLD_CPT_MIRROR_ACCOUNTING
```

This is a receipt diagnostic, not a physics simulation.
