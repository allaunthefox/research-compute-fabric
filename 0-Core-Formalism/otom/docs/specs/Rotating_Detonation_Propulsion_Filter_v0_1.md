# Rotating Detonation Propulsion Filter v0.1

## Status

**Claim state:** `BEAUTIFUL_PROVISIONAL`

This is an OTOM/GCL propulsion-regime filter note. It interprets rotating detonation rocket engine reports as evidence for a transport/protocol pattern: a continuously sustained shock-front regime can act as a higher-efficiency propulsion operator when stability, duration, thrust, and mission scope are explicitly receipted.

## Source boundary

The user-provided Scientific American article reports Astrobotic hot-fire testing of Chakram rotating detonation rocket engines at NASA Marshall Space Flight Center, including more than 470 seconds total firing and a 300-second continuous burn. It also reports that each engine generated more than 4,000 pounds of thrust and that the technology is not yet launch-ready.

This spec treats the report as:

```text
engineering-progress evidence
not flight qualification
not proof of operational launch readiness
```

## Core thesis

A rotating detonation engine can be modeled as a propulsion protocol where the useful invariant is not merely combustion, but sustained cyclic shock-front organization.

In OTOM terms:

```text
propellant injection
→ detonation wave formation
→ annular shock-front circulation
→ sustained pressure gain
→ thrust output
→ thermal / structural / stability receipt
```

## GCL mapping

| RDRE event | GCL / OTOM interpretation |
|---|---|
| Fuel and oxidizer enter chamber | Source flow |
| Supersonic shock compresses and ignites mixture | Regime transition operator |
| Detonation wave rotates in chamber | Cyclic transport protocol |
| 300-second continuous burn | Stability / persistence receipt |
| >470 seconds total firing | Aggregate duration receipt |
| >4,000 lbf thrust per engine | Output-force receipt |
| Not yet launch-ready | Warden HOLD boundary |
| Cislunar / lunar lander target | λ-scale mission domain |

## Δφγλ reading

```text
Δ = instability, thermal loss, pressure oscillation, structural stress, incomplete burn, failed restart
φ = sustained detonation wave, useful thrust, stable chamber behavior, repeatable pressure-gain cycle
γ = combustion intensity / pressure-gain forcing / thrust demand
λ = engine test article, lander propulsion subsystem, cislunar transfer vehicle, not full launch stack
```

The important transport lesson is:

```text
shock-regime propulsion is lawful only when the detonation wave remains bounded, repeatable, and receipt-backed at the declared mission scale
```

## Warden gates

### Gate 1 — Test article versus launch system

Blocked claim:

```text
RDRE is launch-ready because a hot-fire test succeeded.
```

Allowed claim:

```text
The hot-fire test is a propulsion-regime stability receipt for a test article.
```

### Gate 2 — Duration is not mission qualification

Blocked claim:

```text
A 300-second burn proves mission readiness.
```

Allowed claim:

```text
A 300-second burn is a significant continuous-regime receipt that still requires restart, integration, environment, thermal, and flight tests.
```

### Gate 3 — Thrust-scale boundary

Blocked claim:

```text
RDRE replaces heavy-lift launch engines now.
```

Allowed claim:

```text
Current reported thrust supports subsystem or in-space propulsion discussions, not heavy-lift equivalence.
```

### Gate 4 — Cislunar transport framing

Allowed hypothesis:

```text
RDREs may be especially interesting for cislunar transfer, lander propulsion, orbital transfer vehicles, or staged transport nodes where efficiency and sustained burns matter.
```

Required receipts:

```text
hot-fire duration
thrust output
thermal stability
restart behavior
structural wear
propellant compatibility
vehicle integration
flight demonstration
```

## Relation to OTOM transport protocols

This belongs beside the market-filter and alphabet-reduction artifacts because it gives a physical transport instance of the same invariant grammar:

```text
input flow
→ constrained transformation
→ regime stabilization
→ output work
→ feedback / failure modes
→ scale-bounded receipt
```

Biology case:

```text
symbol alphabet → structural adapter → viable ribosomal subsystem
```

RDRE case:

```text
propellant flow → detonation adapter → stable thrust subsystem
```

Market case:

```text
asset flow → behavioral adapter → filterable regime match
```

The common invariant is not ontology. It is bounded transformation under a declared λ-scale.

## Non-goals

This spec does not claim:

```text
RDREs are ready for operational launch
RDREs outperform all conventional engines in all regimes
hot-fire duration alone proves reliability
reported thrust is equivalent to heavy-lift launch thrust
cislunar missions are guaranteed
```

## Strongest formulation

The useful claim is:

> A sustained RDRE burn is evidence that a detonation-front regime can be stabilized long enough to behave as a propulsion protocol, but promotion requires scale-specific engineering receipts.

That is the part OTOM should absorb.
