# False Vacuum Rydberg Bubble Nucleation Prior

Status: `EXTERNAL_REFERENCE_PRIOR`

Claim boundary: this is a bounded physics prior from a Rydberg atom analogue
simulation of false-vacuum decay and bubble nucleation. It is not evidence that
the experiment can trigger cosmological vacuum decay, not evidence that
spacetime is programmable, not a hardware-readiness claim, and not a replacement
for the Lean FSDU/FAMM surfaces.

Primary source:

```text
Yu-Xin Chao et al.,
Probing False Vacuum Decay and Bubble Nucleation in a Rydberg Atom Array,
Physical Review Letters 136, 120407 (2026)
arXiv:2512.04637
DOI: 10.1103/kqzq-fnr4
```

User seed:

```text
https://www.iflscience.com/giant-atoms-experiment-simulates-the-scariest-way-for-the-universe-to-end-83333
```

Accessible source used for extraction:

```text
https://phys.org/news/2026-04-tabletop-atoms-universe-doomsday-vacuum.html
https://arxiv.org/abs/2512.04637
```

## Stable Physics Kernel

The useful model is:

```text
metastable local minimum
  -> symmetry-breaking field
  -> tunneling / nucleation event
  -> true-vacuum bubble candidate
  -> growth only if the bubble clears an energy threshold
```

For Research Stack purposes, this is a controlled analogue of:

```text
false basin
  -> local perturbation
  -> bubble / scar nucleation
  -> thresholded propagation
  -> FAMM/FSDU gate
```

## Minimal Equation Pack

Generic field-theory energy landscape:

```text
V(phi) has at least two minima:

false vacuum: phi_f, local minimum
true vacuum:  phi_t, lower-energy minimum
DeltaV = V(phi_f) - V(phi_t) > 0
```

Bubble energy, thin-wall intuition:

```text
E(R) = surface_cost - volume_gain
     = 4 pi R^2 sigma - (4 pi / 3) R^3 DeltaV
```

Critical radius:

```text
R_c = 2 sigma / DeltaV
```

Interpretation:

```text
R < R_c  -> bubble collapses
R >= R_c -> bubble can expand
```

Quantum tunneling rate shape:

```text
Gamma / V approx A exp(-B / hbar)
```

Thin-wall bounce-action reference shape:

```text
B = 27 pi^2 sigma^4 / (2 DeltaV^3)
```

Rydberg atom-array analogue Hamiltonian shape:

```text
H = sum_i (Omega_i / 2) sigma_i^x
    - sum_i delta_i n_i
    + sum_{i<j} V_ij n_i n_j

V_ij = C6 / r_ij^6
```

In the cited experiment, individual site addressing and van der Waals
interactions allow a ring of Rydberg atoms to realize two competing alternating
spin-order patterns. A site-selective laser field breaks the symmetry, creating
an analogue false-vacuum / true-vacuum pair.

Observed scaling shape:

```text
Gamma(h) ~ exp(-kappa / h)
```

where `h` is the effective symmetry-breaking field. As the field grows, the
required critical bubble becomes smaller, so decay is easier to observe.

Discrete-system warning:

```text
resonant bubble nucleation can occur at specific field strengths
```

That resonance is useful to the stack as a warning: discrete lattices can have
field-strength bands where decay is enhanced beyond smooth-continuum intuition.

## Mapping To FAMM / FSDU

| Physics concept | Stack analogue |
|---|---|
| false vacuum | apparently stable local route/basin |
| true vacuum | lower-cost route/basin discovered after perturbation |
| symmetry-breaking field | probe pressure, heuristic bias, or external prior |
| bubble nucleation | local scar/component crossing threshold |
| critical radius | minimum evidence mass before propagation |
| domain wall tension `sigma` | boundary cost / receipt cost |
| energy gap `DeltaV` | cost improvement or residual release |
| decay rate `Gamma` | probability/rate of route switch |
| resonant bubble nucleation | discrete PIST/FAMM shell resonance warning |

FSDU guard form:

```text
commit allowed iff ||S_a - S_b|| <= epsilon
```

Bubble-nucleation guard form:

```text
promote bubble only if R >= R_c and receipt_cost <= released_residual
```

So the practical Research Stack primitive is:

```text
FalseVacuumPrior:
  do not erase metastable basins;
  probe them for thresholded scar nucleation;
  promote only when a replay receipt shows the bubble exceeds critical size.
```

## HOLD Boundaries

These remain HOLD or QUARANTINE:

```text
spacetime programmable from Rydberg arrays
cosmological false-vacuum hazard from the experiment
hardware control claim
universal physics claim
compression result
FSDU theorem promotion
```

Allowed use:

```text
metastable-state prior
bubble-threshold analogy
discrete resonance warning
FAMM/FSDU scar-nucleation heuristic
```

## Next Probe

The next useful local probe is a small deterministic threshold model:

```text
given cells with scar mass m_i and boundary cost sigma_i:
  bubble_gain = sum(m_i)
  wall_cost   = perimeter(component) * sigma
  admit iff bubble_gain > wall_cost and component hash replays
```

This should be treated as a receipt-bearing diagnostic, not a physics
simulation.
