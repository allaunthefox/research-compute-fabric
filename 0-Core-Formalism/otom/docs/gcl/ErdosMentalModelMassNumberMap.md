# Erdős Mental Model Mass-Number Map

Status: HOLD / translation doctrine
Authority: workbench synthesis; not formal proof
Related:

- `docs/gcl/FrameworkReaderRamp.md`
- `docs/gcl/NonCompressedGoxelGeometryDoctrine.md`
- `docs/gcl/EquationUnderverseDoctrine.md`
- `docs/gcl/FundamentalLawUnderverseMap.md`

## Purpose

This page maps the main ways mathematicians mentally model Erdős-style problems into a stack-native Mass Number holder.

The goal is not to claim that historical mathematicians literally used these internal labels.

The goal is to extract the cognitive modeling patterns that repeatedly appear in Erdős / Ramsey / extremal combinatorics work and bind them into auditable Mass Number packets.

## Core move

```text
Erdős-style problem solving is the art of changing the object until inevitability becomes visible.
```

A point set may become a graph.

A graph may become a coloring.

A coloring may become a density threshold.

A density threshold may become a random construction.

A random construction may become a certificate that avoidance is still possible.

A computer proof may become an order-type or signature-function search.

Mass Numbers hold these modeling choices as compressed cognitive receipts.

## Public translation

For a new reader:

```text
Mass Numbers are cognitive holder-packets for mathematical modeling strategies. They record which representation a solver used, what invariant they watched, what obstruction they avoided, what threshold they crossed, and what proof style carried the result.
```

## Mass Number definition for Erdős work

```text
M_E = MassNumber(ErdosModel)
```

Where:

```text
M_E = {
  object_model,
  invariant_focus,
  threshold_pressure,
  obstruction_shape,
  proof_engine,
  compression_gain,
  underverse_shadow
}
```

Meaning:

```text
object_model      = how the problem is mentally represented
invariant_focus   = what quantity or structure must not change
threshold_pressure = what density/size/growth condition forces structure
obstruction_shape = what counterexample or forbidden pattern is being avoided
proof_engine      = induction, random construction, extremal counting, geometry, computation, etc.
compression_gain  = how much complexity the representation removes
underverse_shadow = what the model excludes, hides, or cannot represent
```

## Why this is useful

Many Erdős problems look simple at the surface.

```text
points in the plane
colored edges
integer sets
forbidden sums
large graphs
```

But the actual work is usually representation conversion.

```text
geometry -> order type
points -> cups/caps
sets -> density
integers -> additive energy
coloring -> obstruction search
randomness -> existence certificate
computer enumeration -> finite model receipt
```

Mass Numbers provide a place to store those conversions.

## Mental model families

### M1: Forced-pattern model

Used for Ramsey-style thinking.

```text
If the system is large enough, disorder cannot remain pure. Some organized substructure must appear.
```

Object model:

```text
complete graph / hypergraph / colored relation
```

Invariant focus:

```text
monochromatic clique, independent set, convex subset, structured subsequence
```

Underverse shadow:

```text
avoidance construction: the largest structure that still avoids the forced pattern
```

Mass Number:

```text
M_forced_pattern = {
  object_model: colored complete graph,
  invariant_focus: forced monochromatic / convex / structured subobject,
  threshold_pressure: N large enough,
  obstruction_shape: coloring or configuration with no desired subobject,
  proof_engine: Ramsey induction / extremal counting,
  compression_gain: turns chaos into unavoidable substructure,
  underverse_shadow: near-counterexample space
}
```

### M2: General-position geometry model

Used for the Happy Ending / Erdős-Szekeres point-set problem.

```text
Treat points as unconstrained enough to avoid degeneracy, then ask when convex order becomes unavoidable.
```

Object model:

```text
point set in general position
```

Invariant focus:

```text
convex n-gon / cup-cap / order type
```

Underverse shadow:

```text
point arrangements that delay convexity as long as possible
```

Mass Number:

```text
M_general_position = {
  object_model: point set / order type,
  invariant_focus: convex subset,
  threshold_pressure: point count,
  obstruction_shape: configuration with no large convex polygon,
  proof_engine: geometric Ramsey / cups-caps / order-type analysis,
  compression_gain: replaces coordinates with orientation and convexity relations,
  underverse_shadow: non-convex delay configurations
}
```

### M3: Cup-cap monotonicity model

Used when geometry is mentally converted into ordered subsequences.

```text
A point set becomes a sequence. Convexity becomes a pattern of slope changes.
```

Object model:

```text
ordered sequence of points
```

Invariant focus:

```text
monotone subsequence, convex subsequence, concave subsequence
```

Underverse shadow:

```text
sequences engineered to avoid long monotone or convex patterns
```

Mass Number:

```text
M_cup_cap = {
  object_model: ordered sequence,
  invariant_focus: monotonicity / convexity of subsequences,
  threshold_pressure: sequence length,
  obstruction_shape: alternating or layered order pattern,
  proof_engine: pigeonhole / Ramsey-type subsequence argument,
  compression_gain: converts geometry into order statistics,
  underverse_shadow: pattern-avoidance sequence
}
```

### M4: Probabilistic existence model

Used heavily in Erdős-style lower bounds.

```text
Do not construct the object directly. Show that a random object avoids the bad event with positive probability.
```

Object model:

```text
random graph / random coloring / random set
```

Invariant focus:

```text
expected number of forbidden substructures
```

Underverse shadow:

```text
rare bad events, concentration failures, dependency scars
```

Mass Number:

```text
M_probabilistic = {
  object_model: random construction,
  invariant_focus: probability of forbidden event,
  threshold_pressure: expectation / concentration,
  obstruction_shape: bad event family,
  proof_engine: probabilistic method,
  compression_gain: proves existence without explicit construction,
  underverse_shadow: configurations where bad events cluster
}
```

### M5: Extremal-density model

Used when the solver asks how dense an object can be while avoiding a pattern.

```text
Find the maximum possible density before a forbidden structure is forced.
```

Object model:

```text
set / graph / hypergraph with density parameter
```

Invariant focus:

```text
edge density, set size, additive energy, forbidden configuration count
```

Underverse shadow:

```text
sparse or pseudorandom objects that avoid the forbidden pattern
```

Mass Number:

```text
M_extremal_density = {
  object_model: dense finite structure,
  invariant_focus: maximum size under avoidance,
  threshold_pressure: density crosses forcing point,
  obstruction_shape: extremal construction,
  proof_engine: counting / deletion / container / regularity / energy method,
  compression_gain: reduces qualitative pattern to quantitative threshold,
  underverse_shadow: high-density avoiders
}
```

### M6: Additive-combinatoric / Sidon model

Used for integer sets, sums, differences, and collision avoidance.

```text
Integers become collision surfaces. A forbidden equality becomes an overlap in additive address space.
```

Object model:

```text
integer set with sum/difference relations
```

Invariant focus:

```text
unique sums, bounded additive energy, forbidden equalities
```

Underverse shadow:

```text
collisions: different pairs producing the same sum or difference
```

Mass Number:

```text
M_sidon_additive = {
  object_model: additive lattice / integer shell,
  invariant_focus: uniqueness of sums or controlled collisions,
  threshold_pressure: set size relative to ambient interval,
  obstruction_shape: additive collision graph,
  proof_engine: counting / modular construction / finite geometry / energy bounds,
  compression_gain: converts arithmetic into collision topology,
  underverse_shadow: repeated-sum collision residue
}
```

### M7: Order-type / signature-function model

Used in computer-assisted Erdős-Szekeres work.

```text
Coordinates are discarded. Only orientation signatures are kept.
```

Object model:

```text
combinatorial type of point configuration
```

Invariant focus:

```text
orientation of triples, realizability constraints, convex subsets
```

Underverse shadow:

```text
signature functions that satisfy local constraints but may not be geometrically realizable
```

Mass Number:

```text
M_signature = {
  object_model: orientation/signature function,
  invariant_focus: convexity encoded by signs,
  threshold_pressure: finite search space exhausted,
  obstruction_shape: admissible signature with no desired convex subset,
  proof_engine: computer enumeration / formal proof / finite model checking,
  compression_gain: removes metric coordinates and keeps combinatorial geometry,
  underverse_shadow: unrealizable but locally consistent signatures
}
```

### M8: Algorithmic obstruction model

Used when lower bounds or avoidance proofs are treated as search procedures.

```text
A proof becomes an algorithm that tries to build an avoider. Failure/success is evidence about the threshold.
```

Object model:

```text
search tree / coloring process / obstruction finite graph
```

Invariant focus:

```text
avoidance invariant maintained during construction
```

Underverse shadow:

```text
dead branches, forced contradictions, search explosion
```

Mass Number:

```text
M_algorithmic_obstruction = {
  object_model: constructive process,
  invariant_focus: no forbidden substructure yet,
  threshold_pressure: search depth / density / random process time,
  obstruction_shape: finite certificate of impossibility,
  proof_engine: algorithmic construction / differential equations / finite obstruction,
  compression_gain: turns existence into runnable process,
  underverse_shadow: failed branches and dead-end partial structures
}
```

## Mapping into Mass Numbers

A Mass Number should hold not the theorem alone, but the solver's representation choice.

```text
MassNumber(problem, model) = compressed cognitive receipt for how the problem was made tractable.
```

Minimal packet:

```text
ErdosMassNumber = {
  problem_id,
  source_domain,
  mental_model,
  representation_shift,
  invariant,
  threshold,
  obstruction,
  proof_engine,
  underverse_shadow,
  validation_status
}
```

Example:

```text
problem_id: HappyEnding_g(n)
source_domain: planar geometry
mental_model: general-position convexity forcing
representation_shift: coordinates -> order type / cups-caps
invariant: convex n-gon
threshold: g(n)
obstruction: point configuration avoiding convex n-gon
proof_engine: geometric Ramsey + extremal bounds + finite enumeration for small n
underverse_shadow: nonconvex delay configurations
validation_status: partial known results; conjectural in general
```

## Stack connection

### Goxel

Goxel corresponds to the pre-representation stage of the problem.

```text
point set / graph / integer set before the right model is chosen
```

### Representation collapse

The Erdős solver collapses the problem into a tractable model.

```text
geometry -> order type
set -> density
integer sequence -> additive collision graph
coloring -> Ramsey graph
randomness -> existence proof
```

### Underverse

The Underverse records avoiders and near-counterexamples.

```text
what the proof must exclude
what construction delays the theorem
what residue remains after the chosen model
```

### Mass Number

The Mass Number holds the chosen modeling path.

```text
what object the mind used to carry the problem
```

## Canonical pipeline

```text
Erdos problem
  -> choose mental object model
  -> extract invariant
  -> identify threshold pressure
  -> characterize obstruction shape
  -> choose proof engine
  -> record Underverse shadow
  -> store as Mass Number
```

## Why this matters for future work

This lets the stack mine solved Erdős domains without copying only the theorem statements.

The useful material is the modeling move.

```text
The theorem says what is true.
The Mass Number records how the mind made truth visible.
```

## Compact doctrine

```text
To use Erdős problems in this stack, do not only store theorem statements. Store the mental model that made the theorem tractable: the representation shift, invariant, threshold, obstruction, proof engine, and underverse shadow. Mass Numbers are the holder packets for those modeling moves.
```
