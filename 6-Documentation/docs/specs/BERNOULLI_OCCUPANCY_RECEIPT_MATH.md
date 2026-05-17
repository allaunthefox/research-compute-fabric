# Bernoulli Occupancy Receipt Math

Status: `LEAN_GATE_SURFACE`

Claim boundary: this generalizes the birthday-problem/hash-collision math into
a reusable receipt primitive. It is not a compression-ratio claim. It only
defines how to estimate and receipt expected collisions, survivor buckets, and
candidate reuse across finite slots.

Lean surface:

```text
0-Core-Formalism/lean/Semantics/Semantics/BernoulliOccupancyShockbow.lean
```

Machine receipt:

```text
shared-data/data/stack_solidification/bernoulli_occupancy_shockbow_receipt.json
```

Seed source:

```text
0xkrt26, "When is your birthday? - The Math Behind Hash Collisions",
2026-05-08,
https://0xkrt26.github.io/math_behind_security/2026/05/08/birthday-problem.html
```

## Generic Occupancy Frame

Replace birthdays with a finite slot system:

```text
n = number of slots
k = number of throws / candidates / emitted symbols
s = target occupancy count
```

Examples:

| Birthday term | General term | Research Stack use |
|---|---|---|
| day | slot / bucket / route class | decompressor symbol bucket, FAMM basin, AMMR peak, CMR survivor class |
| person | throw / candidate / observation | vector candidate, token, route probe, residual fragment |
| shared birthday | collision / reuse / same-slot occupancy | repeated structure, reusable transform, scar convergence |
| at least one match | any qualifying bucket | any reusable survivor bucket |

The exact birthday insight is the shift from:

```text
specific preselected slot has s hits
```

to:

```text
any slot has s hits
```

That shift is why the math becomes useful for compression and receipt routing.

## Uniform Slot Formula

For uniform slots, the probability that one named slot has exactly `s` hits is:

```text
p_1(s; n, k) =
  C(k, s) * (1/n)^s * (1 - 1/n)^(k-s)
```

The expected number of slots with exactly `s` hits is:

```text
E[X_s] =
  n * C(k, s) * (1/n)^s * (1 - 1/n)^(k-s)
```

For at least `s` hits:

```text
E[X_>=s] =
  n * sum_{j=s..k} C(k, j) * (1/n)^j * (1 - 1/n)^(k-j)
```

Interpretation:

```text
E[X_s]      = expected number of reusable exact-s buckets
E[X_>=s]   = expected number of reusable buckets at or above threshold
```

## Nonuniform Slot Formula

Real systems rarely distribute candidates uniformly. For slot probabilities
`p_i`, with `sum_i p_i = 1`, the expected number of slots with exactly `s`
hits is:

```text
E[X_s] =
  sum_i C(k, s) * p_i^s * (1 - p_i)^(k-s)
```

For at least `s`:

```text
E[X_>=s] =
  sum_i sum_{j=s..k} C(k, j) * p_i^j * (1 - p_i)^(k-j)
```

This is the better form for Research Stack because slot probabilities can come
from vector scores, route priors, FAMM basin strength, symbol frequency, or
receipt confidence.

## BMVR / BVMR / CMR Use

The Bernoulli receipt family can use occupancy math as its expectation layer:

```text
BVMR:
  vector v_i -> probability p_i -> Bernoulli gate outcome b_i

BMVR:
  observed bit b_i -> explanatory vector/residual -> receipt

CMR:
  AVMR / BVMR = surviving vector-combination receipt
```

Occupancy math tells us how many survivor buckets we should expect before the
static decompressor has to replay them:

```text
expected_survivor_buckets = E[X_>=s]
```

If this value is too high, the compressor is emitting too many ambiguous
survivors. If it is too low, the compressor may be over-gating and losing
reusable structure.

## Static Decompressor Application

The compressor can spend compute on:

```text
candidate generation
vector scoring
Bernoulli/occupancy gates
AVMR composition
CMR emission
```

The static decompressor should only need:

```text
CMR survivor map
residual lane
Merkle/AMMR proof
fixed replay rule
fail-closed rejection
```

So the decompressor does not estimate probabilities at runtime. It verifies that
the compressor committed the survivor set and that replay closes.

## Shockbow Occupancy Map

The same slot math can be drawn as a 2D shockwave-bow field. In that view,
candidate flow enters a bounded replay region from many directions. Curved bow
fronts mark where the flow compresses, reflects, or deflects around a boundary.
Intersections between bows and slot regions are the places where occupancy
pressure becomes useful.

```text
incoming candidate flow
  -> shockbow fronts
  -> compression / deflection zones
  -> BVMR survivor channels
  -> CMR replay core
```

This is a geometry aid, not a new physics claim. The bowfront drawing helps
choose or explain the slot map:

| Shockbow feature | Occupancy meaning | Receipt role |
|---|---|---|
| incoming flow | candidate stream | compressor-side search pressure |
| bowfront | boundary where candidates compress or deflect | slot probability contour |
| bow intersection | high occupancy / collision event | BVMR gate candidate |
| survivor channel | admitted compressed path | AVMR composition input |
| central core | replay-only state | CMR / static decompressor target |
| reflected branch | rejected or ambiguous candidate | HOLD / QUARANTINE |

The rough angular thresholds in a 2D drawing can be treated as local gate
parameters:

```text
theta_in      = candidate approach angle
theta_bow     = bowfront normal angle
delta_theta   = abs(theta_in - theta_bow)
gate passes   if delta_theta is inside the admitted compression band
```

The useful connection is:

```text
Bernoulli occupancy tells us how often slots collide.
Shockbow geometry tells us where candidate pressure makes those collisions
structurally useful.
```

For a static decompressor, the shockbow map should never be replayed as a full
simulation. It is compressor-side evidence for why the emitted CMR survivor map
is bounded.

## Useful Slot Choices

This math can be reused beyond birthdays for:

| Slot system | Candidate throw | Useful collision meaning |
|---|---|---|
| hash table | hash output | collision or birthday attack surface |
| decompressor dictionary | token/logogram bucket | repeated recoverable structure |
| AMMR peak set | receipt leaf | peak reuse / shared proof path |
| FAMM basin map | route probe | scar convergence or stable basin |
| BVMR gate family | vector candidate | survivor class for CMR |
| shockbow angle bins | candidate flow ray | compressed survivor channel |
| grammar buckets | symbol class | whitespace-free structural reuse |
| FPGA/OISC replay table | instruction opcode/residual class | deterministic replay slot |

## Gate Rules

Minimum candidate gate:

```text
ADMIT if:
  expected_survivor_buckets is within replay capacity
  residual_size <= residual_budget
  Merkle/AMMR proof closes
  static decompressor can replay without search

HOLD if:
  expected_survivor_buckets is plausible but unreceipted
  nonuniform p_i priors are missing
  residual budget is unknown

QUARANTINE if:
  expected_survivor_buckets exceeds replay capacity
  collision rate implies ambiguous decode
  proof path or residual lane is missing
```

The Lean gate surface implements this as `decideGate` and proves native-decision
fixtures for:

```text
birthdayTripleAdmits
missingPriorHolds
overCapacityQuarantines
missingProofQuarantines
shockbowRejectQuarantines
birthdayTripleInvariant
```

## Minimal Receipt Shape

```json
{
  "protocol": "bernoulli_occupancy_receipt_math_v0",
  "slot_model": "uniform_or_nonuniform",
  "n_slots": 365,
  "k_candidates": 60,
  "threshold_s": 3,
  "shockbow_gate": {
    "theta_model": "optional_angle_bins",
    "admitted_band_degrees": "declared_band_or_null"
  },
  "expected_exact_s": "E[X_s]",
  "expected_at_least_s": "E[X_>=s]",
  "decompressor_capacity": "declared_capacity",
  "decision": "ADMIT_OR_HOLD_OR_QUARANTINE"
}
```

## Working Rule

The birthday problem is not just about birthdays. It is a reusable warning:

```text
specific collision can be rare
any collision can be common
```

For compression, that means the compressor should watch the whole slot field,
not only a preselected bucket. For static decompression, it means the replay
surface must only receive the committed survivors, not the whole search space.
