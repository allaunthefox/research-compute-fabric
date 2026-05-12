# Underwater Shock Public Benchmark

**Date:** 2026-05-09

**Status:** `PUBLIC_HISTORY_MODELING_PRIOR`

**Claim boundary:** this note uses public historical underwater detonation
records as free modeling data for shock-front, acoustic, bubble-pulse,
reflection, and attenuation behavior. It is not a weapon-design document, not a
charge-sizing guide, not target-vulnerability analysis, and not an operational
placement model.

## Why Sea-Based Records Are Useful

Underwater detonations are over-documented historical events. Humans made an
enormous number of public visual, acoustic, radiological, naval, and historical
records around them. That makes them useful as a low-cost validation source for
general shock physics:

```text
impulsive source
-> compressive water shock
-> pressure-release surface interaction
-> gas / vapor bubble expansion
-> bubble collapse and pulse train
-> acoustic propagation and attenuation
-> sediment / boundary reflection
```

For this stack, the value is not the weapon. The value is the medium response:
water is dense, nearly incompressible, acoustically conductive, and creates a
clean separation between the first shock front and the slower bubble-pulse
sequence.

There is also a practical economic reason. A single serious underwater shock
test chamber campaign would be expensive enough to erase the available research
budget before the model had a chance to mature. Public historical records are
therefore not just convenient; they are the only sane first validation lane.
They let the stack fit waveform shape, timing, attenuation, and residuals
without pretending that a private chamber test is feasible.

The rule is:

```text
use public history to learn the medium response;
do not use the model to optimize destructive operation.
```

## Public Historical Source Class

Useful public source classes:

- official history pages and fact sheets for underwater tests such as
  Operation Crossroads BAKER;
- medical / environmental / historical reviews that describe the test context;
- public technical reports that summarize shock-wave and bubble-pulse signal
  characteristics;
- open acoustic literature on underwater explosion sound and bubble-pulse
  timing;
- generic bubble-dynamics literature using Rayleigh-Plesset-type equations.

Examples:

- Atomic Heritage Foundation / National Museum of Nuclear Science & History,
  Operation Crossroads overview:
  `https://ahf.nuclearmuseum.org/ahf/history/operation-crossroads`
- NCBI Bookshelf, "Mortality of Veteran Participants in the Crossroads Nuclear
  Test", historical description:
  `https://www.ncbi.nlm.nih.gov/books/NBK233207/`
- OSTI technical report, "Signal characteristics of an underwater explosive
  acoustic telemetry system":
  `https://www.osti.gov/biblio/6625697`
- Acoustics Today, "The Sound from Underwater Explosions":
  `https://acousticstoday.org/wp-content/uploads/2023/02/The-Sound-from-Underwater-Explosions-David-R.-DallOsto-Peter-H.-Dahl-and-N.-Ross-Chapman.pdf`

## Safe Modeling Variables

The benchmark lane should use observable signal variables:

```text
t_arrival       acoustic arrival time
p_peak_proxy    observed or normalized peak pressure proxy
tau_decay       shock decay time constant
t_bubble_1      first bubble pulse arrival
t_bubble_k      later bubble pulse arrivals
A_k             relative pulse amplitudes
alpha_water     fitted propagation attenuation
Gamma_surface   pressure-release reflection coefficient
Gamma_bottom    fitted seabed / boundary reflection coefficient
```

The benchmark lane must not optimize:

```text
charge mass
device design
placement depth
standoff distance
target damage
ship / hull response
casualty or infrastructure effects
```

Those fields are explicitly outside the modeling target.

## Equations For The Benchmark Lane

The first useful abstraction is a normalized waveform model:

```text
p_obs(t, r) =
  A_s(r) * exp(-(t - t_a) / tau_s) * H(t - t_a)
  + sum_k A_k(r) * B_k(t - t_b,k)
  + epsilon(t)
```

Where:

- `t_a = r / c_w` is acoustic arrival time in water.
- `A_s(r)` is a fitted initial shock-front amplitude proxy.
- `tau_s` is a fitted decay constant.
- `B_k` are bubble-pulse basis functions.
- `epsilon(t)` is residual sensor / environment error.

Attenuation can be tracked as:

```text
A_s(r) = A_0 * G(r) * exp(-alpha_water * r)
```

Where `G(r)` is a declared geometry-spreading term, not a weapon calibration.

The bubble-motion receipt can use the Rayleigh-Plesset shape as a qualitative
dynamics gate:

```text
rho * (R * R_ddot + 3/2 * R_dot^2)
  = p_b(t) - p_infty(t) - 2*sigma/R - 4*mu*R_dot/R
```

For stack use, this equation says:

```text
bubble pulse timing is a medium-response eigenmode,
not a second independent source event
```

Surface reflection can be modeled as a receipt gate:

```text
p_reflected = Gamma_boundary * p_incident
```

For a pressure-release surface, `Gamma_boundary` is expected to be negative in
the simplified acoustic model. The exact value remains a fitted receipt field.

## Eigenvalue Connection

This public benchmark should sharpen the physical-shock eigen gap found in:

```text
6-Documentation/docs/shockwave_eigenvalue_comparison_2026-05-09.md
```

Current repo state:

```text
shock alignment / relaxation exists as a local stack mode
classical hydrodynamic shock equations exist but have zero-strength support
```

The underwater benchmark can add a measured public-data bridge:

```text
Rankine-Hugoniot conservation
+ water acoustic attenuation
+ bubble-pulse eigenmode
+ boundary reflection
+ residual receipt
```

## Gate

Minimum gate:

```text
if source class is not public / archival:
  HOLD_SOURCE_PROVENANCE
elif requested variable is operational weapon design:
  QUARANTINE_OPERATIONAL_OPTIMIZATION
elif waveform lacks arrival/pulse/residual receipt:
  HOLD_SIGNAL_RECEIPT
elif fitted residual <= declared bound:
  ADMIT_PUBLIC_SHOCK_BENCHMARK
else:
  HOLD_RESIDUAL_TOO_LARGE
```

## Stack Interpretation

This is the clean bridge:

```text
stellar shock breakout:
  radiation escape through optical depth

underwater public shock:
  acoustic escape through dense medium + bubble pulse

rain/statolith shock:
  local displacement threshold in biological medium
```

All three share the same receipt grammar:

```text
impulse -> medium transfer -> boundary condition -> local witness -> residual
```

That gives the stack a free, public, non-operational benchmark for the physical
shock eigen lane.

## Next Work

1. Add a `PublicUnderwaterShockBenchmark` receipt surface.
2. Add an economic feasibility field that records why public data is the
   primary lane before any lab/chamber validation.
3. Use only normalized waveform fixtures at first: arrival, relative pulse
   intervals, attenuation fit, and residual.
4. Add negative controls for missing source provenance, operational-variable
   requests, missing residuals, and overfit waveforms.
5. Re-run the physics eigen remapper after the benchmark exists and check
   whether Detonics & Shock Physics gains a nonzero support lane.
