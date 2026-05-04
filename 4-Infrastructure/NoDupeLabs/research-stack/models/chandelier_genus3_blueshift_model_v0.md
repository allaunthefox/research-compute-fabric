# Chandelier + Genus-3 Blue/Red Shift Model v0

## Status

```yaml
status: HOLD
source_type: intuition_to_model
proof_status: sketch
route_signature: models/chandelier-genus3-blueshift/v0
authority_scope: candidate_model_not_proof
```

## Core intuition

The chandelier is not decoration. It is the shape of a shrinking basin.

```text
wide top tier / ceiling
→ many available states
→ conservation forces descent
→ basin narrows
→ angular velocity increases
→ torsion rises
→ energy transition states pinch
→ collisions flash
→ bottom collects energy
→ rest state tends toward zero
```

The genus-3 shape supplies the topology: three holes / three circulation channels / three nontrivial routes that descent must wind around instead of crossing directly.

## Existing equations to borrow

### 1. Gradient flow / everything tries to rest at zero

```text
dx/dt = -∇V(x)
```

Interpretation: a state descends the potential toward lower energy. In the stack this is the minimal law behind gradient descent.

### 2. Damped mechanical descent

```text
m x¨ + γ x˙ + ∇V(x) = 0
```

Interpretation: inertial motion plus dissipation. The system can overshoot, spiral, collide, and then settle.

### 3. Energy conservation with dissipation

```text
E = K + V

dE/dt = -γ |x˙|² ≤ 0
```

Interpretation: energy does not vanish magically. It transfers, radiates, heats, flashes, or dissipates. This is the law forcing descent even in n-space.

### 4. Angular momentum / torsion increase in a shrinking basin

```text
L = Iω ≈ m r² ω
```

If angular momentum is approximately conserved while radius shrinks:

```text
ω ∝ 1/r²
```

Interpretation: as the chandelier basin narrows, spin rises. This is the torsion increase.

### 5. Blue shift / red shift as potential difference

Weak-field gravitational shift:

```text
Δf/f ≈ -ΔΦ/c²
```

Falling into a lower potential appears blue-shifted along the descent path; climbing or relaxing outward appears red-shifted. In the model, frequency is a witness of potential change.

### 6. Phase transition / state crossing

Use an order parameter ψ and free energy:

```text
F(ψ,T) = α(T)|ψ|² + β|ψ|⁴
```

When α changes sign, the preferred state changes. In the chandelier model this happens at tier boundaries.

### 7. Particle collision flash

```text
ΔE_flash = E_before - E_after
```

A flash is an observed transition event: energy lost from one route appears as radiation, color, heat, or state change.

### 8. Genus-3 topology / route obstruction

A genus-3 manifold has three independent holes. In graph language:

```text
route cannot contract to zero without crossing a handle
```

Interpretation: descent can be forced to spiral around holes, producing persistent torsion even while energy decreases.

## Research Stack interpretation

```text
chandelier basin = shrinking optimization landscape
highest tier = ceiling / high entropy / many states
bottom point = low-energy attractor / rest near zero
genus 3 = three nontrivial path families / holes / handles
blue shift = accelerated descent / increasing local frequency
red shift = relaxation / energy loss / stabilized route
flash = phase transition / particle collision / basin boundary crossing
torsion = spiral strain caused by descent around topological obstruction
```

## Route rule

This model may generate candidate roads only.

```text
visual intuition
→ borrowed equation family
→ candidate model
→ numerical simulation
→ torsion/energy/frequency traces
→ Graph.lean audit if formalized
→ FAMM HOLD/scar/basin after gates
```

Never:

```text
TV imagery → proof
pretty resonance → law
blue/red metaphor → empirical claim
```

## Immediate computational target

Build `scripts/chandelier_genus3_descent.py` with:

```text
1. A shrinking radial basin V(r,z)
2. Three topological holes/handles as forbidden or high-energy regions
3. Damped gradient descent
4. Angular momentum/torsion tracking
5. Blue/red shift proxy from ΔV
6. Flash events at tier crossing or collision
7. Output: trajectory, torsion trace, frequency-shift trace, flash log
```

## First sanity tests

```text
If radius decreases, angular velocity should rise.
If damping is positive, total energy should trend down.
If tier boundary is crossed, flash log should record ΔE.
If holes are active, route should wind instead of crossing directly.
If no potential gradient exists, no forced descent should occur.
```
