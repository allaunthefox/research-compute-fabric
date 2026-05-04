# FAMM — Stigmergic Route Memory

Status: RESEARCH_NOTE  
Claim level: architecture bridge / conceptual alignment  
Primary stack anchor: FAMM = frustration-aligned memory management  
Related concepts: stigmergy, slime-trail memory, basin memory, route scars, frustration timing, topology-aware scheduling

## Source Anchor

Current project status defines FAMM as frustration-aligned memory management: it stores failed, partial, and successful routes as basin/frustration signals that bias future search.

This note adds a cognition/biology bridge: stigmergic memory.

In stigmergy, agents do not need a central planner or complete internal map. They leave traces in a medium. Those traces alter the environment, and the altered environment biases later action.

FAMM is the computational analogue:

```text
route traversal -> trace / scar -> basin or frustration signal -> biased future search
```

## Core Definition

FAMM is frustration-aligned route memory.

It records successes, failures, partial traversals, torsion, basins, and phase deltas so that future search is biased away from bad routes and toward lawful attractors.

Compact form:

```text
FAMM = scars becoming navigation
```

or:

```text
FAMM = route outcomes encoded as future-routing pressure
```

## Stigmergic Bridge

The slime-trail model of memory is useful because it reframes memory as an environmental trace rather than a stored object.

A slime mold does not need a complete internal map if its trail changes the field of future traversal. The medium remembers by being changed.

FAMM performs the same move inside the research stack:

```text
failed route   -> avoid / penalize basin
partial route  -> preserve as near-miss / torsion signal
successful route -> reinforce basin / attractor
ambiguous route -> quarantine / uncertainty field
```

The important object is not only the trace. It is the route bias induced by the trace.

## Difference from AMMR / AVMR

FAMM should not be collapsed into AMMR or AVMR.

```text
AMMR = auditable append-only structured history / receipt chain
AVMR = hierarchical vector-state accumulation / merge history
FAMM = frustration-aligned routing bias derived from prior traversal outcomes
```

AMMR preserves what happened.  
AVMR aggregates vector state.  
FAMM changes where the system searches next.

## FAMM Load

Existing NII driver notes frame FAMM-aware scheduling through timing/load terms such as:

```text
L_famm = Sigma^2 + I_lock + Delta_phi
```

where the broad roles are:

- `Sigma^2` = torsional stress from manifold state
- `I_lock` = interlocking energy
- `Delta_phi` = phase delta / route mismatch pressure

A more implementation-facing sketch also represents FAMM timing as:

```lean
structure FAMMTiming where
  torsionalStress : Q16_16
  interlockingEnergy : Q16_16
  laplacianEnergy : Q16_16

def computeFAMMLoad (t : FAMMTiming) : Q16_16 :=
  t.torsionalStress + t.interlockingEnergy + t.laplacianEnergy
```

The exact implementation may vary by module, but the architectural point is stable:

```text
higher FAMM load = route history indicates stress, lock, torsion, or phase mismatch
```

## Scheduling Interpretation

FAMM-aware scheduling should route work according to historical scar geometry.

A scheduler should ask:

```text
Has this route failed before?
Did it partially work?
Did it produce torsion?
Did it land in a stable basin?
Did it create downstream regret or desync?
Does another route have lower frustration load?
```

This turns memory into routing pressure.

## Seven-Pattern Mapping

FAMM maps cleanly into the Unified Function Layer:

```text
CHAIN:
route attempt -> outcome -> scar -> future scheduling decision

FEEDBACK:
route outcomes change future route selection

GRADIENT:
frustration basins create search pressure fields

MASS:
accumulated route scars, basin weight, regret magnitude, load score

ENTROPY:
successful FAMM reduces blind search disorder; failed FAMM increases routing noise

COUPLING:
agent state couples to route history and basin geometry

SCALING:
route-memory pressure must remain tractable as corpus, graph, or agent count grows
```

## Use in Current Stack

FAMM belongs wherever the system has to learn from traversal, not merely store records.

Examples:

- equation-pattern classification unknown bucket review
- ENE artifact routing
- N-gate adversary traversal
- compression-chain selection
- Hutter/corpus stress testing
- Jupiter-box degraded-channel routing
- topology-aware scheduling
- FPGA/SRAM route and memory-bank decisions

## Guardrail

FAMM should not hallucinate certainty.

A scar is not proof. A basin is not truth. A successful route is not universal validity.

FAMM is a search-bias mechanism. It should preserve uncertainty, provenance, and receipt links so that route memory remains auditable.

## Best Line

```text
FAMM is the mathematics of scars becoming navigation.
```
