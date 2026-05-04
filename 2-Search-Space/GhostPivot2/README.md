# Ghost Pivot 2 — Core Theory

This repository is the **core theory layer**.

Its purpose is to state and eventually prove the substrate-neutral framework:
- invariant-preserving dynamics
- latent load and boundary crossing
- routed multi-subsystem evolution
- bounded resource competition
- bounded memory and switching
- update regimes as general operators

This repo should remain as close as possible to the *minimal provable core*.

## What belongs here
- core definitions
- core theorems and conjectures
- proof-oriented notes
- minimal Lean formalization of the general system
- substrate-neutral math and notation

## What does *not* belong here
- FSC-specific apparatus
- story-derived case studies
- language-specific or biology-specific examples beyond tiny toy examples
- heavy application layers
- experimental manifold adapters that are not needed to state the theory itself

## Intended relationship to the extension repo
The extension repo contains **refinements, applications, and derived constructions**.

Core claim:
> the base theory should stand on its own.

Extension claim:
> FSC, Stable Islands, domain adapters, and story-derived systems are refinements or instantiations of the core, not the core itself.

## Proposed structure
- `docs/` — definitions, axioms, theorem statements, proof sketches
- `lean/` — minimal formal core
- `paper/` — main theory manuscript

## Initial split plan
### Core
- state / invariant / latent load / resource / routing / update rule / solver
- generic reward shaping and boundary functions
- substrate-neutral adapter interface

### Extensions (other repo)
- FSC
- StableIsland
- manifold competition built from FSC steps
- domain adapters
- social / biological / language case studies
- story-derived stress tests

## Guiding rule
If removing a module would leave the core theory intact, it belongs in the extension repo.
If removing a module would collapse the theory itself, it belongs here.
