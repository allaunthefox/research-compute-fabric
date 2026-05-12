# Topological Soliton Raytrace Tessellation NUVMAP Protocol

Status: `CANDIDATE_PROTOCOL_WITH_HOLD_BOUNDARIES`

Seed phrase:

```text
Topological solitons > ray-traced tessellation > Tree Fiddy > NUVMAP results
```

Existing anchors:

- `6-Documentation/docs/topological_soliton_equation_pack_2026-05-09.md`
- `shared-data/data/stack_solidification/topological_soliton_equation_pack_receipt.json`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/Tessellated Triangle Flow Migration.tid`
- `6-Documentation/docs/MATH_MODEL_MAP.tsv`, row `Ray_Casting_Braid_Step`
- `6-Documentation/docs/GLOSSARY.md`, `NUVMAP`

## Core Move

The protocol treats a stable topological soliton as an identity-preserving
field object, then projects that object into an inspectable tessellated address
surface.

```text
topological soliton
  -> invariant field identity
  -> ray-traced local intersections
  -> tessellated cells
  -> Tree Fiddy bounded recursion
  -> NUVMAP address/projection result
  -> replay receipt
```

This is not a physics-device claim. It is a route/projection discipline:

```text
persistent topology becomes a bounded addressable map only if projection replay closes.
```

## Layer Roles

| Layer | Role |
|---|---|
| Topological soliton | Supplies persistent identity and invariant charge. |
| Ray trace | Samples field/ray intersections from observer/probe angles. |
| Tessellation | Converts continuous or dense projection into finite cells. |
| Tree Fiddy | Bounds recursion, refinement, and replay depth. |
| NUVMAP | Stores non-uniform variable/address projection. |
| Receipt | Proves projection, bound, and address replay agree. |

## Minimal Transform

Let:

```text
S = soliton state
I(S) = invariant receipt, e.g. charge/linking/wrapping class
R_i(S) = ray probe i through S
T(R_i) = tessellated cell hit set
B_350(T) = bounded refinement under Tree Fiddy
N(B_350) = NUVMAP address bundle
```

Then the candidate result is:

```text
NUVMAP_result(S) = N(B_350(T({R_i(S)})))
```

Admission requires:

```text
invariant_present(S)
projection_present(R_i)
tessellation_finite(T)
tree_fiddy_depth <= bound
nuvmap_address_valid(N)
replay_residual <= epsilon
```

## Receipt Shape

```json
{
  "protocol": "topological_soliton_raytrace_tessellation_nuvmap_v0",
  "soliton": {
    "invariant_kind": "hopfion|skyrmion|kink|other",
    "invariant_charge": "integer_or_declared_hold",
    "source_receipt": "topological_soliton_equation_pack_receipt"
  },
  "raytrace": {
    "ray_count": 0,
    "observer_basis_hash": "sha256:...",
    "hit_set_hash": "sha256:..."
  },
  "tessellation": {
    "cell_count": 0,
    "cell_adjacency_hash": "sha256:...",
    "cell_payload_hash": "sha256:..."
  },
  "tree_fiddy": {
    "max_depth": 350,
    "actual_depth": 0,
    "overflow": false
  },
  "nuvmap": {
    "address_count": 0,
    "address_hash": "sha256:...",
    "projection_hash": "sha256:..."
  },
  "gate": {
    "replay_residual_q0_16": 0,
    "residual_bound_q0_16": 0,
    "decision": "ADMIT_FIXTURE|HOLD|QUARANTINE"
  }
}
```

## Why This Solves A Real Stack Problem

Soliton equations are continuous or field-heavy. NUVMAP wants finite,
addressable projection. Ray-traced tessellation is the bridge:

```text
field identity
  -> sampled intersections
  -> finite cells
  -> bounded refinement
  -> addressable receipt
```

This gives the compiler a way to handle persistent topological objects without
pretending that a 2D/3D rendering is itself proof.

## HOLD Boundary

Allowed:

- Use topological soliton invariants as identity witnesses.
- Use ray tracing as an observation/projection operator.
- Use tessellation as finite address-cell construction.
- Use Tree Fiddy to bound recursive refinement.
- Use NUVMAP to store resulting addresses.

HOLD:

- Physical control of solitons.
- Device-readiness.
- Claim that ray rendering proves the topology.
- Infinite refinement.
- Unbounded recursion.
- Any NUVMAP address result without replay residual and hash receipts.

Decision:

```text
ADMIT_PROTOCOL_HOLD_FOR_EXECUTABLE_FIXTURE
```
