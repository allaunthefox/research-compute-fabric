# Pulsar Genus-3 Two-Component Model v0

## Status

```yaml
status: HOLD
source_type: literature_aligned_candidate_model
proof_status: sketch
route_signature: models/pulsar-genus3-two-component/v0
authority_scope: candidate_model_not_proof
```

## Correction

There is no canonical vertical in n-space.

```text
"down" = direction of increasing torsion / decreasing accessible phase volume / decreasing free energy
```

So the chandelier is not a literal vertical object. It is a coordinate projection of a state-space descent.

## Physical mapping

```text
superfluid neutron vortices
= chandelier filaments

crustal nuclear lattice
= rigid outer shell / basin rim / pinning substrate

vortex unpinning avalanches
= phase-transition flashes

magnetic dipole braking
= damping / slow energy bleed

glitch spin-up
= sudden angular-momentum redistribution / flash

relativistic beaming
= blue/red shift from rotational velocity and viewing geometry

genus-3 topology
= three independent circulation cycles in magnetosphere or vortex-array domain
```

## Literature anchors

1. Vortex-avalanche theory is an existing explanation family for pulsar glitches and anti-glitches, where collectively unpinning vortices transfer angular momentum between the superfluid interior and crust.
2. Crust-only angular momentum reservoirs may be insufficient for large glitches when entrainment is included; core or deeper reservoir participation may be required.
3. Mutual friction, crust-core coupling, vortex pinning, vortex-flux-tube interactions, and magnetospheric changes are all active mechanisms in modern glitch modeling.

## Two-component dynamical skeleton

Let:

```text
Ω_c = crust / charged component angular velocity
Ω_s = neutron superfluid angular velocity
I_c = crust / charged component moment of inertia
I_s = superfluid moment of inertia
N_ext = external electromagnetic braking torque
N_int = internal mutual-friction / vortex-transfer torque
```

Core equations:

```text
I_c dΩ_c/dt = N_ext + N_int
I_s dΩ_s/dt = -N_int
```

Total angular momentum changes only through external torque:

```text
d/dt (I_c Ω_c + I_s Ω_s) = N_ext
```

If `N_ext = 0`, angular momentum is conserved internally.

## Magnetic dipole braking

A standard spin-down form:

```text
N_ext = -K Ω_c^n
```

For pure dipole braking, idealized braking index:

```text
n ≈ 3
```

But observed pulsars can differ because the magnetosphere, inclination angle, internal coupling, and field evolution are not frozen.

## Internal lag and pinning threshold

Define lag:

```text
ω_lag = Ω_s - Ω_c
```

Pinned vortices allow lag to accumulate. When lag exceeds a critical threshold:

```text
ω_lag ≥ ω_crit
```

an avalanche/unpinning event can occur.

## Glitch flash rule

During an avalanche, internal torque spikes:

```text
N_int(t) = N_creep(t) + N_flash(t)
```

with a short event window:

```text
N_flash(t) ∝ A_glitch exp(-(t-t_g)^2 / 2σ_g^2)
```

The observed glitch is:

```text
ΔΩ_c > 0
ΔΩ_s < 0
```

subject to angular momentum conservation over the short internal event:

```text
I_c ΔΩ_c + I_s ΔΩ_s ≈ 0
```

## Vortex count relation

For a rotating superfluid, vortex areal density follows Feynman relation:

```text
n_v = 2Ω_s / κ
```

where circulation quantum:

```text
κ = h / (2m_n)
```

Total vortex number in area A:

```text
N_v ≈ (2Ω_s A) / κ
```

A glitch corresponds to a rearrangement/unpinning flux:

```text
ΔN_v → ΔΩ_c
```

## Genus-3 topology interpretation

Use three noncontractible cycles as a modeling abstraction:

```text
cycle_1 = open field line / polar outflow route
cycle_2 = closed field line / trapped magnetospheric route
cycle_3 = return current sheet / reconnection route
```

or, inside the superfluid:

```text
cycle_1 = pinned vortex lattice channel
cycle_2 = mobile vortex creep channel
cycle_3 = avalanche front / turbulent reconnection channel
```

This does not claim the neutron star literally has genus 3. It says the reduced model has three independent circulation routes.

## Blue/red shift and beaming

Rotational Doppler factor for emission from a moving surface/beam element:

```text
D = 1 / (γ(1 - β cos θ_obs))
```

Observed frequency:

```text
ν_obs = D ν_emit
```

where:

```text
β = v/c
γ = 1 / sqrt(1-β²)
```

Use this as a trace, not as proof. A glitch can change Ω, beam geometry, or magnetospheric emission state, producing pulse-profile changes.

## Chandelier reinterpretation

The chandelier shape becomes:

```text
vortex bundle projection
+ pinning lattice shell
+ shrinking accessible phase volume
+ angular momentum transfer down the torsion gradient
```

The "flashes" are not decorations. They are modeled as:

```text
unpinning avalanche
→ angular momentum transfer
→ transient magnetospheric change
→ observable pulse/beam perturbation
```

## Simulation target

Build `scripts/pulsar_genus3_two_component.py`:

```text
1. Two angular velocities: Ω_c, Ω_s
2. External magnetic dipole braking
3. Internal mutual friction / creep
4. Pinning threshold and avalanche trigger
5. Conservation check: I_c ΔΩ_c + I_s ΔΩ_s ≈ 0 during flash
6. Vortex count proxy using n_v = 2Ω_s/κ
7. Genus-3 route weights for three circulation channels
8. Doppler beaming trace
9. Outputs: spin traces, lag trace, glitch log, angular momentum residual
```

## Acceptance tests

```text
with no external torque: total angular momentum conserved
with braking only: Ω_c slowly decreases
with pinning: lag accumulates
when lag crosses threshold: glitch flash occurs
at glitch: Ω_c jumps up and Ω_s drops
post-glitch: relaxation/coupling restores smoother evolution
if route weights are altered: glitch timing/size changes
```

## Safety boundary

```text
pulsar model = external-light-source physical analogy + candidate simulation
not proof of Research Stack
not direct basin
not solar-system validation
not empirical claim without data
```
