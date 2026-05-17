# Loki Milky Way Accretion Prior

Status: `EXTERNAL_REFERENCE_PRIOR`

Claim boundary: this is a bounded galactic-archaeology prior from an external
paper about a possible ancient accreted progenitor hidden in the Milky Way
plane. It does not prove a Research Stack physics model, does not infer gas
density, does not promote physical mass, and does not turn SMN/eigenmass into
stellar mass. It only adds a useful evidence pattern: old merger debris can
remain visible as a coherent chemo-dynamical fossil scar.

Primary source:

```text
Federico Sestito et al.,
An ancient system hidden in the Galactic plane?,
Monthly Notices of the Royal Astronomical Society 548, stag563 (2026)
arXiv:2409.13813
DOI: 10.1093/mnras/stag563
```

User seed:

```text
https://www.iflscience.com/meet-loki-a-new-lost-galaxy-that-might-have-been-cannibalized-by-the-milky-way-83442
```

Accessible sources used for extraction:

```text
https://phys.org/news/2026-04-lost-galaxy-loki-milky.html
https://arxiv.org/abs/2409.13813
https://academic.oup.com/mnras/article/548/2/stag563/8537783
```

## Stable Astronomy Kernel

The useful external kernel is:

```text
20 very metal-poor stars
  -> selected near the solar neighbourhood and on planar, high-eccentricity orbits
  -> 11 prograde and 9 retrograde
  -> similar chemical abundance patterns
  -> chemically distinct from much of the observed non-planar halo sample
  -> plausible early accreted dwarf-galaxy progenitor
  -> tentative name: Loki
```

The authors explicitly keep the claim tentative. The same broad population of
planar very metal-poor stars may include more than one accretion event.

## Minimal Equation Pack

Chemo-dynamical feature vector:

```text
x_i = [
  position_i,
  velocity_i,
  eccentricity_i,
  zmax_i,
  [Fe/H]_i,
  [Mg/Fe]_i,
  [Sr/Fe]_i,
  [Ba/Fe]_i,
  [Eu/Fe]_i,
  ... abundance channels
]
```

Orbital evidence surface:

```text
E_i = 0.5 * |v_i|^2 + Phi(r_i)

L_i = r_i cross v_i

prograde / retrograde split follows sign or orientation of angular momentum
relative to the Galactic disc.
```

Chemical-distance surface:

```text
d_chem(i, j) = sqrt( sum_k w_k * ([X_k/Fe]_i - [X_k/Fe]_j)^2 )
```

Closed-box chemical-evolution sketch:

```text
dM_gas/dt = -nu * M_gas

SFR(t) = nu * M_gas(t)

M_gas(t) = M_gas(0) * exp(-nu * t)
```

Tidal-remnant intuition:

```text
r_t approx R * (m_sat / (3 * M_host(R)))^(1/3)
```

where `r_t` is a tidal radius, `m_sat` is the progenitor satellite mass, and
`M_host(R)` is the host mass enclosed at orbital radius `R`. This is only a
structural analogy for when an accreted object becomes debris; it is not a mass
inference for the local stack.

## Mapping To Research Stack

| Astronomy concept | Stack analogue |
|---|---|
| accreted dwarf progenitor | older route/source merged into the current manifold |
| metal-poor planar stars | fossil witness particles left in the current plane |
| prograde and retrograde members | opposite traversal chirality from one parent source |
| shared abundance pattern | chemical receipt / common-origin witness |
| high orbital eccentricity | scarred trajectory with strong radial excursion |
| Loki as tentative single system | candidate hidden basin, not promoted truth |
| multiple possible accretions | forked source history / HOLD until larger survey |

The stack-side primitive is:

```text
FossilScarPrior:
  a present-day population can preserve enough local chemistry + dynamics
  to reconstruct an earlier merged source, but the reconstruction remains HOLD
  until sample size, selection function, and independent survey checks close.
```

## Eigenmass / SMN Implication

This helps the eigenmass work because it gives a grounded astronomy example of
how a hidden source can survive as a coherent direction in feature space:

```text
row features
  -> abundance / orbit / position channels
  -> principal direction or cluster
  -> candidate source-history witness
```

For Research Stack wording:

```text
allowed: hidden-source / fossil-scar prior
allowed: chemo-dynamical feature grouping prior
allowed: SMN evidence-load analogy

not allowed: physical mass promotion
not allowed: gas-density inference
not allowed: cosmology fit
not allowed: object-level DESI/MaNGA crossmatch claim
not allowed: Loki confirmed as a unique progenitor beyond the paper boundary
```

## How This Sharpens The Model

The prior says that a state space can contain old merger debris that is not
obvious from position alone. The useful fields are multi-channel:

```text
geometry + motion + chemistry + dispersion + survey selection
```

That directly supports the current Research Stack habit of refusing single-axis
promotion. A source-history claim should need both:

```text
feature-space coherence
and
receipt-bearing provenance
```

## HOLD Boundaries

These remain HOLD:

```text
Loki as confirmed unique progenitor
physical stellar mass inference from SMN/eigenmass
gas-density inference
dark-matter inference
cosmology fit
object-level DESI/MaNGA crossmatch
Research Stack theorem promotion
compression/Hutter transfer
hardware/FPGA/ASIC claim
```

Allowed use:

```text
external galactic-archaeology prior
hidden-source fossil-scar analogy
chemo-dynamical grouping receipt pattern
survey-scale caution for small samples
```

## Next Probe

The local, receipt-bearing next probe should be a tiny chemo-dynamical fixture:

```text
given rows with abundance vector a_i and kinematic vector k_i:
  hash the source rows
  normalize channels
  compute chemical-distance graph
  compute orbit/chirality labels
  emit connected components and residuals
  require null controls before source-history admission
```

Null controls:

```text
shuffle abundance channels
shuffle orbit labels
remove metallicity channel
remove chirality label
compare component stability
```

Decision vocabulary:

```text
ADMIT_EXTERNAL_PRIOR
HOLD_SAMPLE_TOO_SMALL
HOLD_SELECTION_FUNCTION
QUARANTINE_UNREPLAYABLE_SOURCE_HISTORY
```
