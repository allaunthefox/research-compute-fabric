# Custom Stack Modules

These modules adapt the Newtonian Superfluid Simulation into the broader semantic-mass / geometric ontology stack.

## Source model

The repository simulation is particle-based. The README describes a fluid model of particles interacting through attraction, repulsion, and spin-like/tangential dynamics, where force-balance changes produce dynamic micro-to-macro patterns.

The current `simulation.py` implements a finite 2D particle system with:

```text
N_particles = 350
box_size = 50.0
dt = 0.04
k_gravity = 100.0
k_repel = 100.0
softening = 1.2
R_max = 10.0
damping = 0.95
max_vel = 12.0
```

with local attraction and repulsion:

```text
F_grav  = k_gravity / (r^2 + softening)
F_repel = -k_repel / (r^4 + 0.1)
```

## Added modules

### `superfluid_semantic_adapter.py`

A Python adapter that runs finite probes and exports dimensionless semantic diagnostics:

```text
mass_number
semantic_density
torsion
kinetic_pressure
basin_strength
receipt_coverage
gate
```

It also exports Q16.16-compatible values for browser/Lean/Wasm bridge use.

Run:

```bash
python custom_stack/superfluid_semantic_adapter.py
```

### `SuperfluidSemanticKernel.lean`

A Lean-side fixed-point gate kernel defining:

```text
SuperfluidSemanticState
GateScope
routeAdmissible
superfluid_mass_q16
superfluid_density_q16
superfluid_torsion_q16
superfluid_basin_q16
superfluid_gate_scope
```

## Boundary

These modules do **not** claim:

```text
semantic mass is SI physical mass
the particle simulation is a literal validated superfluid model
visualization proves ontology
high mass_number proves a claim
```

They provide a finite adapter layer:

```text
particle dynamics -> dimensionless semantic diagnostics -> custom ontology/render stack
```

## Intended next bridge

```text
simulation.py / adapter
-> semantic state JSON or Q16.16 values
-> WebGPU ontology renderer
-> Lean/Wasm receipt gate
-> FAMM / Inverted FAMM route memory
```
