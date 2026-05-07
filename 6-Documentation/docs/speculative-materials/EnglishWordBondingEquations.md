# English Word Bonding Equations

Status: SPECULATIVE_MATERIALS_BRIDGE
Claim level: mnemonic/operator surface only
Implementation burden: graph model first; chemistry validation later
Safety posture: not a synthesis plan, recipe, or material claim

## Core Idea

Some English words can be useful as compact handles for bonding, routing, and
stability operators, but only if the word collapses into typed quantities.

The useful move is not:

```text
word -> real compound
```

The useful move is:

```text
word -> memorable operator name -> finite fields -> testable gate
```

That makes the playful layer pay rent without pretending that spelling creates
chemistry. Element-symbol parses such as `Co-U-C-H`, `CaFe`, `BaCoN`, or
`Si-Li-C-O-N` are search/mnemonic anchors only. They are not claims that those
assemblies are stable, synthesizable, safe, or relevant without real chemistry
evidence.

## Operator Set

| Word handle | Neutral operator | Bonding / graph role | Stack role |
|---|---|---|---|
| `CAGE` | Bounded coordination shell | A local neighborhood that shields a reactive or unstable center. | Quarantine, Tree Fiddy/BHOCS archive, Faraday-cage metaphor translation. |
| `BRIDGE` | Shared-edge coupling | A ligand, edge, or witness connects two sites while paying strain. | Route stitcher between concept clusters or hardware/GPU/FPGA surfaces. |
| `CHAIN` | Propagating bond path | Sequential bond/order transfer with bounded residue at each step. | Compression path, polymer-like route, search expansion control. |
| `SCAR` | Defect-memory residue | Failed or strained bond leaves a persistent negative prior. | FAMM scar memory and COUCH route pressure. |
| `SALT` | Charge-balanced pair/lattice | Opposite charges stabilize if lattice/strain budget passes. | Balance gate for promotion versus quarantine. |
| `RING` | Closed recurrence loop | Closed path whose recurrence can stabilize or amplify signal. | Loc Nes recurrence and loop-safe semantic search. |

## Minimal Equation Sketches

All quantities below are intended as integer or fixed-point fields in a future
Lean surface, not floating chemistry simulation.

```text
CAGE(x) =
  coordination_count(x)
+ shield_strength(x)
- leakage(x)
- cage_strain(x)
```

Promotion rule:

```text
cage_ok(x) := CAGE(x) >= cage_threshold
           && leakage(x) <= leakage_budget
```

```text
BRIDGE(a, b) =
  shared_ligand(a, b) * compatibility(a, b)
- strain(a, b)
- unpaired_residue(a, b)
```

Promotion rule:

```text
bridge_ok(a, b) := BRIDGE(a, b) >= bridge_threshold
                && strain(a, b) <= strain_budget
```

```text
CHAIN_{n+1} =
  propagate(CHAIN_n)
  subject to bond_order(n) <= bond_order_threshold
         and residue(n) <= residue_budget
```

```text
SCAR_{t+1} =
  scar_decay * SCAR_t
+ failed_route_receipt_t
+ strain_memory_t
- repair_credit_t
```

```text
SALT(A, B) :=
  charge(A) + charge(B) = 0
  and lattice_energy(A, B) <= lattice_budget
  and hydration_or_context_penalty(A, B) <= context_budget
```

```text
RING(path) :=
  closed(path)
  and recurrence_count(path) >= min_recurrence
  and ring_strain(path) <= ring_strain_budget
```

## Useful Word Candidates

| Word | Element-symbol mnemonic | Why it might be useful | Required guardrail |
|---|---|---|---|
| `CAGE` | `C-A-G-E` as letters, not all element symbols | Names bounded coordination and shielding. | Must produce a finite containment score, not vibes. |
| `BRIDGE` | letter handle | Names ligand/edge sharing between two surfaces. | Must include a strain penalty. |
| `CHAIN` | `C-H-A-I-N` mnemonic | Names sequential propagation and polymer-like routing. | Must track residue at each step. |
| `SCAR` | `S-C-Ar` mnemonic | Sulfur/carbon/argon-like parse is a joke surface; useful part is defect memory. | Must decay or repair; no permanent punishment without receipt. |
| `SALT` | chemistry-native word | Names charge balance and lattice stabilization. | Must check context; charge balance alone is not stability. |
| `RING` | chemistry-native topology word | Names closed recurrence and aromatic/loop-like stabilization. | Must check strain and false loops. |
| `COUCH` | `Co-U-C-H` mnemonic | Already maps to route pressure; can also name a caged cobalt/uranium joke surface. | Do not imply a real material. Use as COUCH gate alias only. |
| `HELLO` | operator joke | Already maps to harmonic/eigen node plus language lattice. | Keep as search-operator mnemonic, not chemistry. |
| `CaFe` | calcium/iron parse | Useful as a memorable "cage plus iron/ferrite" search hook. | Must not be confused with a recipe or phase claim. |
| `BaCoN` | barium/cobalt/nitrogen parse | Useful as a deliberately silly handle for charge/coordination checks. | Toxicity/material hazards mean documentation only. |
| `SiLiCON` | silicon/lithium/carbon/oxygen/nitrogen parse | Useful for substrate/electrolyte/lattice search routing. | Needs real materials references before any claim. |

## Stack Mapping

The intended Research Stack use is a graph/search and verification adapter:

```text
English word handle
-> operator family
-> finite fields
-> route gate
-> evidence receipt
```

Example mapping:

```text
COUCH
-> cage / route-pressure mnemonic
-> F_COUCH, U_rot, R_value
-> local / atlas / reject route gate
-> Lean witness in Semantics.CouchFilterNormalization
```

```text
Loc Nes / RING
-> hidden-basin recurrence loop
-> recurrence_count, leakage, scar_energy
-> archive / recur / quarantine gate
-> Semantics.LochMonsterFilter
```

```text
Tree Fiddy / CAGE
-> bounded archive shell
-> cage_score, leakage_budget, history_bound
-> BHOCS commit monster assignment
-> bounded receipt instead of active charge
```

## Claim Boundary

This note does not claim that English words produce real chemical bonding
equations. It claims that English words can be good mnemonic labels for typed
operators if each label is forced through:

1. a neutral mechanism,
2. finite fields,
3. an explicit gate,
4. a receipt surface,
5. a failure mode.

If a word cannot survive those five checks, it stays a joke and does not enter
the model.

## Failure Modes

- The word becomes decoration and stops mapping to fields.
- Element-symbol parses are mistaken for chemistry claims.
- A cute spelling overfits a route that does not generalize.
- Charge balance is treated as sufficient stability.
- Closed loops are mistaken for useful recurrence.
- Scar memory becomes permanent punishment instead of bounded evidence.
- Search ranking prefers memorable names over executable evidence.

## Promotion Path

The smallest useful next artifact is not a chemistry simulator. It is a finite
operator table:

```text
WordBondOperator :=
  cage | bridge | chain | scar | salt | ring
```

with integer fields for charge, strain, leakage, recurrence, residue, and
receipt status. Once that exists, the internal semantic search engine can index
the playful handles while ranking by neutral operator evidence.

## One-Line Summary

Use English words as memorable handles for typed bonding and routing operators,
then force every handle through finite gates so the joke surface either pays
for itself or stays quarantined.
