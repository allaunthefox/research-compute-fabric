# Reconstruction Core Math Review

Status: Review v0.1
Date: 2026-05-09
Scope: stage-by-stage math consistency review after the law-gated reconstruction-core shift
Claim state: internal consistency review; not a compression benchmark, proof result, biological model, quantum-compression result, or corpus coverage claim

## Summary

The shift is mathematically coherent if the stack keeps three separations:

```text
counted byte law != auxiliary route score
ADMIT_FIXTURE != ADMIT
glyph/proposal/prior != payload truth
```

The core equation still holds:

```text
S -> (K, Theta, R, Pi, Receipts) -> S_hat
Repair(Replay(K, Theta, Pi), R) == S
epsilon_byte = 0
```

The counted compression gate is still the only compression admission:

```text
|D| + |K| + |Theta| + |Pi| + |R| + |Receipts| < |S|
```

All other terms are candidate-ranking or safety diagnostics unless normalized
and receipted.

## Stage Review

| Stage | Math status | Review |
|---|---|---|
| Route prior | Coherent | A prior has no truth force. It can only create a fixture target. |
| Reconstruction kernel | Coherent | `K` must be replayable. Readability is irrelevant. |
| Parameters / basis | Coherent with caveat | `Theta` must be counted. A basis choice that makes residual cheap but costs more than raw stays `HOLD`. |
| Protocol | Coherent | `Pi` is decoder instruction material and must be counted. |
| Residual repair | Coherent | Residual is a proofreading channel, not a failure. Silent residual is invalid. |
| Byte law | Coherent | The only compression gate is counted bytes against raw bytes. |
| Auxiliary scores | Coherent after clarification | Motif gain, binding analogues, replay curvature, entropy, cognitive burden, and mutation pressure are diagnostics unless normalized. |
| enwiki8 wiki-logogram probe | Coherent with caveat | MediaWiki/XML atoms can replay a bounded slice byte-exactly, but ordinary compressors remain much smaller. |
| enwiki9 logogram targeter | Coherent with caveat | The imported targeter finds slice classes and replays demo/sample slices exactly, but the current grammar expands both runs. |
| enwiki9 XML dictionary probe | Coherent with caveat | Fixed tag IDs flip `delta_core` positive, but packet/global deltas remain negative after receipt and dictionary costs. |
| enwiki9 receipt aggregation probe | Coherent with caveat | Slice-level replay receipts flip `delta_packet` positive on fixtures, but global deltas remain negative until dictionary amortization. |
| enwiki9 dictionary amortization probe | Coherent with caveat | PASS/ADD/PAUSE/SUBTRACT event gates show one noncanonical XML fixture flips `delta_global` positive, while other fixtures remain HOLD. |
| Language surface ambiguity negative control | Coherent | Same-surface word reuse and accidental correct analogy outputs stay HOLD unless typed replay or residuals preserve the byte path. |
| Reconstruction core ladder memory | Coherent | Project-memory pointer records receipt paths, hashes, statuses, guardrails, claim boundary, and next action without promoting compression claims. |
| Weather-system borrowed math | Coherent with caveat | Conservation, CFL, innovation, ensemble spread, and residual growth can rank field replay routes, but do not prove forecast skill or compression. |
| Fixture admission | Coherent after clarification | `ADMIT_FIXTURE` means tiny local fixture pass. It is not top-level `ADMIT`. |
| Control filters | Incomplete | Most tiny receipts do not yet record LoC/NES, FYC, COUCH, Tree Fiddy, or BHOCS fields. They must remain top-level `HOLD`. |
| Lean proof boundary | Coherent | External proof corpora route obligations only. Local Lean replay is the proof boundary. |

## Equation Checks

### 1. Reconstruction Equation

The reconstruction equation:

```text
S_hat = Repair(Replay(K, Theta, Pi), R)
```

is valid as a lossless-codec interface. `R` must be interpreted as a repair
stream over a deterministic candidate reconstruction, not as a subtraction over
arbitrary semantic objects.

Required receipt fields:

```text
raw_hash
kernel_hash
theta_hash
protocol_hash
residual_hash
repaired_hash
exact_replay
```

### 2. Byte Law

The counted objective:

```text
J_count = |D| + |K| + |Theta| + |Pi| + |R| + |Receipts|
```

is dimensionally sound because all terms are bytes.

The admission inequality:

```text
J_count < |S|
```

is the only compression claim. If an auxiliary score says a transform is
beautiful but `J_count >= |S|`, the transform is not compression-useful.

### 3. Quantum Basis Objective

The quantum-basis form remains coherent when treated as basis selection:

```text
G_Q = |S| - (|D| + |K_Q| + |Theta_Q| + |R_Q| + |Pi_Q|)
```

The Pauli/transfold terms should not be added directly to byte counts unless
converted into counted protocol, kernel, parameter, or residual bytes. Terms
such as noncommutativity, entanglement, and replay depth are route costs or
candidate penalties, not byte savings by themselves.

### 4. enwiki8 Wiki-Logogram Probe

The enwiki8 wiki-logogram probe is coherent as a grammar-substitution fixture:

```text
Decode(wiki_logogram_core) == enwiki8_slice
```

The current bounded slice records:

```text
raw slice: 4096 bytes
encoded core: 3453 bytes
packet estimate: 4025 bytes
zlib-9 baseline: 1365 bytes
bz2-9 baseline: 1469 bytes
lzma-9 baseline: 1420 bytes
```

This means the local grammar transform passes exact replay and shows a positive
packet estimate only under truncated per-atom receipt hashes. It is not
competitive with ordinary compressors on the slice and must stay benchmark-HOLD.

The math remains valid because the fixture separates:

```text
core byte gain
packet estimate gain
full inspection receipt cost
baseline compressor comparison
```

The next mathematical risk is amortization drift: a dictionary or receipt scheme
may look cheap on a tiny slice only because global tables are undercounted. Any
larger run must count grammar tables, protocol bytes, residual bytes, receipt
bytes, and baseline comparisons in one objective.

### 5. enwiki9 Logogram Targeter

The imported enwiki9 targeter is coherent as a slice-class selector and replay
harness:

```text
selected slice -> logogram core -> decoded bytes
Decode(core) == selected slice
```

The current receipt records:

```text
demo raw/core/packet: 948 / 1115 / 1491 bytes
sample raw/core/packet: 16384 / 17290 / 18678 bytes
```

Both demo and local sample runs replay byte-exactly, but both expand. Therefore
the targeter is useful for finding slice classes and atom-family failures, not
for compression admission.

The math review conclusion is:

```text
slice targeting != corpus compression
roundtrip pass != byte-law pass
local sample != canonical enwik9 benchmark
```

The next valid move is dictionary promotion for fixed XML/MediaWiki scaffold
atoms, followed by rerunning the same target classes with counted dictionary,
protocol, residual, and receipt bytes.

### 6. enwiki9 XML Dictionary Probe

The v2 fixed XML/MediaWiki dictionary probe is mathematically coherent as the
next promotion test:

```text
raw grammar span -> fixed tag ID + payload/residual -> exact replay
```

It records the three deltas separately:

```text
delta_core = |S| - |Gamma|
delta_packet = |S| - (|Gamma| + |rho| + |Pi|)
delta_global = |S| - (|Gamma| + |rho| + |Pi| + |D|)
```

Current receipt:

```text
demo raw/core/packet: 948 / 767 / 1011 bytes
demo delta_core/delta_packet/delta_global: 181 / -63 / -1127 bytes

local sample raw/core/packet: 16384 / 16177 / 17141 bytes
local sample delta_core/delta_packet/delta_global: 207 / -757 / -1821 bytes
```

This fixes the previous failure mode only at the core layer:

```text
v1 demo delta_core: -167
v2 demo delta_core: 181

v1 local-sample delta_core: -906
v2 local-sample delta_core: 207
```

The result must remain `HOLD` because dictionary cost and receipt stubs still
erase the gain, and the local sample is a noncanonical HTML file rather than the
canonical 1,000,000,000-byte `enwik9` corpus.

### 7. enwiki9 Receipt Aggregation Probe

The v3 receipt-aggregation probe is mathematically coherent as a packet-layer
test because it changes only the receipt accounting mode, not the replay
grammar:

```text
rho_slice = H(H(S_raw) || H(Gamma) || H(D) || H(Pi) || exact_replay)
P_v3 = |Gamma| + |rho_slice| + |Pi_id|
```

The current receipt counts:

```text
|rho_slice| = 32 bytes
|Pi_id| = 4 bytes per slice
|D| = 1064 bytes
```

Current receipt:

```text
demo raw/core/v3-packet: 948 / 767 / 875 bytes
demo delta_core/delta_packet_v3/delta_global_v3: 181 / 73 / -991 bytes

local sample raw/core/v3-packet: 16384 / 16177 / 16321 bytes
local sample delta_core/delta_packet_v3/delta_global_v3: 207 / 63 / -1001 bytes
```

This fixes the v2 packet-overhead failure on the fixture aggregates:

```text
demo packet delta: -63 -> 73
local-sample packet delta: -757 -> 63
```

The result must still remain top-level `HOLD` because the dictionary is not yet
amortized, the local sample is noncanonical HTML rather than `enwik9`, and no
baseline compressor comparison is beaten. The coherent next gate is global
dictionary amortization:

```text
sum_j delta_packet_j > |D| + |Pi|
```

### 8. enwiki9 Dictionary Amortization Probe

The v4 dictionary-amortization probe is mathematically coherent because it
keeps the replay transform and receipt mode fixed, then changes only accounting
scope:

```text
delta_global = sum_j delta_packet_j - |D|
```

It also introduces the clockless four-gate event protocol:

```text
PASS -> ADD -> PAUSE -> SUBTRACT => verdict
```

`PASS` verifies byte-exact replay. `ADD` computes deterministic packet and
global costs. `PAUSE` is a zero-delta state fence whose event hash advances by
logical order, not wall time. `SUBTRACT` computes deltas and emits the verdict.
Wall-clock timestamps are metadata only and are excluded from receipt hashes.

Current receipt:

```text
1234567 local HTML:
  raw/core/v3-packet/global-delta:
    20532 / 20282 / 20498 / -1030 bytes
  verdict: HOLD_GLOBAL

fawiki XML head:
  raw/core/v3-packet/global-delta:
    131072 / 125732 / 126884 / 3124 bytes
  verdict: ADMIT_FIXTURE

jawiki XML head:
  raw/core/v3-packet/global-delta:
    131072 / 130700 / 131852 / -1844 bytes
  verdict: HOLD_PACKET

viwiki XML head:
  raw/core/v3-packet/global-delta:
    131072 / 130152 / 131304 / -1296 bytes
  verdict: HOLD_PACKET
```

This is the first global-positive fixture in the ladder, but only as
`ADMIT_FIXTURE`: the source is noncanonical, no baseline compressor is beaten,
and no full `enwik9` or Hutter/LTCB accounting is claimed. The important result
is causal, not benchmark-level:

```text
v2 dictionary + v3 slice receipts + enough matching XML scaffold
  can overcome |D| on a local fixture
```

### 9. DNA Codec Filter

The DNA-style equation remains coherent as an analogy-bound filter:

```text
S = Repair_R(Regulate_B_DeltaG(Replay(K, Theta, Pi)))
```

The following terms are diagnostics, not counted bytes:

```text
R_motif
DeltaG_codec
U_route
E_mutation
C_regulatory
```

Correction applied:

```text
p_decode_fail_proxy = p_kernel * p_basis * p_replay * p_repair
```

was too optimistic for a layered verifier. The receipt generator now uses a
conservative union-bound proxy:

```text
p_decode_fail_union_bound <= p_kernel + p_basis + p_replay + p_repair
```

For a byte-exact archive:

```text
epsilon_archive = 0
```

so mutation/error terms can only describe receipt budget pressure. They cannot
permit nonzero output error.

### 10. Logogram-DNA Codec

The logogram-DNA equation remains coherent:

```text
S = Repair_R(Regulate_B_DeltaG(Replay_Pi(Gamma)))
```

provided:

```text
payload != glyph != rendered layout
```

and:

```text
Recover(g_i, r_i, rho_i) == p_i
```

The atom gate is logically sound:

```text
Adm(a_i) =
  F_payload
  and F_direction
  and F_chirality_phase
  and F_placement
  and F_residual
  and F_receipt
  and F_adapter
```

The current receipt correctly routes:

```text
auto direction -> HOLD
semantic tear / missing receipt / adapter mutation -> QUARANTINE_DIAGNOSTIC
```

The remaining caveat is that `Gamma` currently carries synthetic long repeated
payloads. This is a valid fixture, but not evidence of corpus-level logogram
compression.

### 11. Weather Systems Math Prior

The weather-systems borrowed-math equation is coherent as a field-dynamics
route filter:

```text
weather_state -> transport/replay kernel + residual -> repaired state
Repair(Replay(K, Theta, Pi), R) == S
```

The counted objective remains byte-dimensional:

```text
J_count = |D| + |K| + |Theta| + |Pi| + |R| + |Receipts|
```

The weather terms:

```text
mass_drift
CFL_excess
innovation_norm
ensemble_spread
residual_growth
```

are diagnostics unless normalized and receipted. They may reject or rank a
candidate replay route, but they do not add byte savings by themselves.

The tiny receipt is internally consistent because the exact periodic transport
fixture preserves mass and has `CFL <= 1`, the wrong-boundary fixture stays
`HOLD_DIAGNOSTIC`, and the assimilation fixture stays diagnostic when it is not
byte-useful. This does not imply NWP forecast skill, ERA5 ingest, atmospheric
model validation, or a weather compression benchmark.

### 12. Proof Replay

The Lean proof replay stage is coherent because it keeps proof promotion local:

```text
external corpus -> obligation route
local Lean replay -> proof-state promotion
```

The current fixture proves only its local admission predicates. It does not
prove the full reconstruction stack, external theorem validity, or mathlib
coverage.

## Required Fixes Applied

1. Clarified that `ADMIT_FIXTURE` is not top-level `ADMIT`.
2. Clarified that auxiliary route scores are diagnostics unless normalized and
   receipted.
3. Replaced the DNA receipt's layered failure product with a conservative
   union-bound failure proxy.
4. Made the new DNA and logogram-DNA receipt hashes stable over reruns by
   excluding `generated_at_utc` from the hash payload.
5. Regenerated the DNA codec filter and logogram-DNA codec receipts.

## Remaining HOLD Conditions

The stack should remain HOLD-grade until these are added:

1. A single admission index over all receipts.
2. Explicit control-filter result fields for LoC/NES, FYC, COUCH, Tree Fiddy,
   and BHOCS.
3. A common status schema:

```text
decision: HOLD | ADMIT | QUARANTINE
fixture_status: ADMIT_FIXTURE | HOLD_DIAGNOSTIC | QUARANTINE_DIAGNOSTIC
```

4. Normalization metadata for non-byte route terms:

```text
term
unit
scale
lambda
conversion_to_cost_or_rank
```

5. Lean mirrors for the stable gates:

```text
exactReplay
residualDeclared
byteGainPositive
receiptComplete
atomGatePass
```

## Verdict

The shifted math still makes sense if kept in this form:

```text
byte law is admission
auxiliary scores are routing
receipts are trust boundary
fixtures are not global claims
```

The main risk is not mathematical contradiction. The main risk is status drift:
letting `ADMIT_FIXTURE`, pretty glyphs, biological analogy, quantum notation, or
external corpora read like full promotion. The current review patches that
boundary back into the docs and receipt math.
