# SMN: Semantic Mass Numbers

Status: `CANONICAL_NAMING_BOUNDARY`

Claim boundary: SMN is a project-local semantic-load measure. It is not atomic
mass, not isotope mass number, not physical mass, and not a Mass Number
admissibility receipt by itself.

## Definition

```text
SMN(x) = semantic load carried by x inside the stack.
```

An SMN measures how much structured meaning, provenance, relation burden,
constraint burden, and decision burden a symbol, channel, ratio, or gate carries.

Keeper rule:

```text
SMN measures how heavy a symbol is inside the model.
```

## Non-Identities

```text
SMN != atomic mass number
SMN != isotope mass
SMN != SI mass
SMN != Mass Number admissibility packet
SMN != proof
SMN != truth
```

The older phrase "semantic mass number" should now be normalized to:

```text
SMN: Semantic Mass Number
```

## Relationship To Existing Terms

| Term | Meaning | Claim boundary |
|---|---|---|
| Semantic Mass | Dimensionless semantic/routing pressure or burden | raw load signal |
| SMN | Counted semantic-load index for a concrete object | measurable/codable load number |
| Mass Number | Admissibility packet with residual and boundary guard | receipt/gate surface |

So the pipeline is:

```text
semantic mass pressure
  -> SMN score
  -> optional Mass Number packet
  -> admissibility / residual / boundary receipt
```

Do not skip directly from SMN score to truth. SMN can route attention, but a
Mass Number receipt is still required for promotion.

## Minimal Formula

```text
SMN(x) =
  identity_load(x)
+ relation_load(x)
+ provenance_load(x)
+ constraint_load(x)
+ decision_load(x)
+ repair_load(x)
```

For compact receipts:

```text
SMN(x) = |bindings| + |relations| + |gates| + |receipts| + |residuals|
```

## Stellar Gas Example

Anonymous vector slot:

```text
EMLINE_GFLUX_1RE[16]
```

has low SMN because it is only a position.

Named channel:

```text
OIII-5008
```

has higher SMN because it binds:

```text
oxygen species
+ ionization state
+ wavelength
+ high-ionization role
+ MaNGA provenance
```

Diagnostic ratio:

```text
log(OIII-5008 / Hb-4862)
```

has still higher SMN because it adds a relation and a diagnostic gate.

BPT-style proxy class:

```text
OIII/Hb + NII/Ha -> star-forming / composite / AGN-LIER-shock proxy
```

has higher SMN again because it participates in a decision surface.

## Receipt Shape

```json
{
  "schema": "smn_semantic_mass_number_v0",
  "object_id": "OIII-5008",
  "object_kind": "emission_line_channel",
  "smn": 7,
  "components": {
    "identity_load": 2,
    "relation_load": 1,
    "provenance_load": 1,
    "constraint_load": 1,
    "decision_load": 2,
    "repair_load": 0
  },
  "boundary": "SMN is semantic load, not atomic mass and not proof."
}
```

## Working Rule

Use SMN to choose what deserves attention, not to claim correctness.

```text
high SMN + weak receipt coverage = audit priority
high SMN + strong receipt coverage = reusable route candidate
low SMN + strong evidence = useful primitive
low SMN + weak evidence = background noise
```
