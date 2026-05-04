# Mass Number Recursion Warning

Status: HOLD / safety doctrine
Authority: workbench warning; not formal proof
Related:

- `docs/gcl/MassNumberSurfaceTranslation.md`
- `docs/gcl/CognitiveProcessAdapter.md`
- `docs/gcl/SidonPhysicsNativeDeconstruction.md`
- `docs/gcl/EquationUnderverseDoctrine.md`
- `docs/gcl/FundamentalLawUnderverseMap.md`

## Purpose

This document adds a strong warning about recursion in Mass Number fields.

Mass Numbers are holder packets for modeling moves. They can store representation shifts, invariants, thresholds, obstructions, proof engines, Underverse shadows, and surface projections.

Because abstraction itself can become recursive, every Mass Number field that points to another abstraction must also define a reverse-collapse path.

```text
Forward abstraction without reverse collapse is unsafe.
```

## Core warning

```text
WARNING:
Do not allow Mass Number fields to recursively reference other Mass Numbers,
surfaces, adapters, or abstraction layers unless every recursive edge has:

1. a depth bound,
2. a type boundary,
3. a receipt hash,
4. a reverse-collapse target,
5. an Underverse failure packet,
6. a Warden stop condition.
```

## Why this matters

A Mass Number compresses process.

That compression is useful only if it can be unfolded safely.

If a Mass Number field recursively points to another Mass Number field, and that field points back into the first, the system can enter abstraction recursion:

```text
MassNumber
  -> Surface
  -> Adapter
  -> MassNumber
  -> Surface
  -> Adapter
  -> ...
```

This can look insightful while actually producing unbounded semantic expansion.

The danger is not only infinite recursion.

The danger is ungrounded abstraction that cannot return to a concrete surface, invariant, packet, or test.

## Reverse collapse

Every abstraction path must have a reverse-collapse path.

Forward path:

```text
raw object
  -> Mass Number
  -> Surface
  -> higher abstraction
```

Reverse-collapse path:

```text
higher abstraction
  -> Surface feature
  -> Mass Number field
  -> concrete object / example / invariant / test
```

If reverse collapse fails, the abstraction remains HOLD and must not be promoted.

## Definition

```text
Reverse collapse = the required operation that maps an abstract Mass Number field
back into a finite, inspectable, testable lower-level representation.
```

Reverse collapse can target:

```text
concrete example
surface feature
invariant
counterexample
packet schema
bounded metric
source artifact
Lean theorem
simulation trace
validation receipt
```

## Unsafe recursion patterns

### R1: Surface echo

```text
MassNumber.surface_projection -> Surface.source_mass_number_id -> same MassNumber
```

Risk:

```text
the surface explains itself by pointing to the Mass Number that created it
```

Required fix:

```text
surface must expose at least one concrete feature: ridge, hole, seam, basin,
flow line, scar field, rupture, or contour.
```

### R2: Adapter echo

```text
MassNumber.proof_engine -> CognitiveProcessAdapter -> MassNumber.proof_engine
```

Risk:

```text
the process adapter claims legitimacy by recursively citing its own abstraction
```

Required fix:

```text
adapter must cite a source artifact, proof structure, code trace, worked example,
or explicit inference label.
```

### R3: Underverse echo

```text
MassNumber.underverse_shadow -> UnderversePacket -> MassNumber.underverse_shadow
```

Risk:

```text
failure is explained only by more failure language
```

Required fix:

```text
Underverse packet must record finite residue: class, metric, forbidden tag,
failed representation tag, Warden status, and receipt hash.
```

### R4: Culture/math echo

```text
cultural form -> invariant -> Mass Number -> cultural form
```

Risk:

```text
interpretation becomes self-confirming
```

Required fix:

```text
state the invariant that survives transformation and at least one observed
carrier: body, rhythm, text, ritual, institution, symbol, artifact, or rule.
```

### R5: Physics-native echo

```text
physics metaphor -> surface -> Mass Number -> physics metaphor
```

Risk:

```text
fictional or metaphorical physics is promoted as real physics
```

Required fix:

```text
label as representation grammar, impossible-event adapter, toy model, or
physical claim. Physical claims require external evidence and SI accounting.
```

## Recursion safety packet

Every recursive Mass Number field must be accompanied by:

```text
RecursionSafetyPacket = {
  field_id,
  recursion_depth,
  max_depth,
  source_type,
  target_type,
  reverse_collapse_target,
  invariant_anchor,
  surface_anchor,
  underverse_failure_class,
  warden_stop_condition,
  receipt_hash
}
```

Hot-path numeric values must use fixed-point or integer-coded fields.

## Depth policy

Default depth policy:

```text
max_depth = 3
```

Recommended interpretation:

```text
Depth 0:
  concrete object / source artifact

Depth 1:
  Mass Number packet

Depth 2:
  Surface projection

Depth 3:
  higher abstraction / cross-domain adapter
```

Anything beyond depth 3 requires explicit Warden approval.

## Reverse-collapse test

A Mass Number recursion passes only if the system can answer:

```text
1. What did this abstraction come from?
2. What surface feature does it render as?
3. What invariant does it preserve?
4. What example or source artifact anchors it?
5. What would falsify or break it?
6. What Underverse packet is emitted if reverse collapse fails?
7. What stop condition prevents unbounded recursion?
```

If any answer is missing, do not promote.

## Warden rule

```text
if MassNumberField.references_abstraction == true
and reverse_collapse_target == null:
  emit UnderversePacket.recursive_abstraction_without_ground
  block promotion
```

```text
if recursion_depth > max_depth:
  emit UnderversePacket.recursion_depth_exceeded
  quarantine field
```

```text
if field resolves only to itself:
  emit UnderversePacket.self_referential_echo
  require concrete surface anchor
```

## Surface rule

Every recursive abstraction must eventually land on a surface.

```text
No surface, no promotion.
```

Valid surface anchors include:

```text
ridge
hole
wall
seam
basin
flow line
scar field
contour
rupture
NaN tear
threshold
forbidden region
```

## Underverse rule

If reverse collapse fails, do not leave the abstraction inside the active manifold.

```text
failed reverse collapse
  -> Underverse packet
  -> Warden review
  -> quarantine / snip / downgrade
```

## Compact doctrine

```text
Mass Numbers may recurse, but recursion must be bounded, typed, receipted, and
reversible. Every abstraction must support reverse collapse back into a concrete
surface feature, invariant, source artifact, packet, or test. If the abstraction
cannot reverse-collapse, it becomes an Underverse packet rather than an active
field.
```
