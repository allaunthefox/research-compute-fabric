# Omnitoken GCL Redesign

**Version:** 0.1  
**Status:** Canonical redesign draft  
**Scope:** Omnitoken as an OMNIsurface language for GCL, JupiterBox, swarm transport, and embedded node surfaces  
**Design center:** Works on Racknerd-class nodes and degrades down toward 8 KB RAM targets
**GCL revision reference:** `docs/specs/GCL_TOPOLOGY_REVISION_SPEC.md`

---

## Thesis

Omnitoken should not be "JSON over a transport", "UDP packets", "onion
messages", or "metrics packets with tags." Those are shell appearances.
Omnitoken is an OMNIsurface: it takes the local shape of whatever substrate it
touches while preserving one internal scalar/LUT meaning.

The redesigned Omnitoken is:

```text
a scale-invariant 1D scalar -> compressed LUT -> lawful GCL codon
```

The GCL topology revision fixes the authority boundary around that codon:
Omnitoken can project a shell into a finite codon, but only the GCL gate can
admit it as state. Builder, Warden, and Judge appear as topology phases inside
the same surface rather than as separate runtime authorities.

The revised field-equation extension is defined in
`GCL_FIELD_EQUATIONS_SPEC.md`. In that extension, the middle step becomes a
field-selected LUT:

```text
scale-invariant scalar
  -> surface/motif/informaton field lookup
  -> RGFlow persistent intersection
  -> compressed LUT
  -> lawful GCL codon
```

It is not a network, a blockchain container, a metrics format, or a transport
packet by itself. If it bumps into UDP, the shell may read as UDP. If it moves
through an onion network, the shell may read as onion. If `IPv923U` exists in
the future, it becomes another shell. The internal object remains the same:
a scalar-indexed LUT entry admitted by GCL.

---

## Problems in the Old Shape

The existing Omnitoken work contains the right ingredients, but they are mixed
at the wrong layer.

Observed issues:

1. Operation names are often open strings.
2. Metrics, transport, routing, and execution containers share vocabulary but
   not one canonical frame.
3. CRC is treated as useful integrity, but not clearly separated from
   authentication or replay protection.
4. UDP-like carriers are tolerated, but ordering, loss, replay, and corruption
   are not made first-class protocol obligations.
5. JupiterBox is treated as a transport enhancement rather than the bounded
   carrier envelope for Omnitoken/GCL state.
6. Tiny targets cannot afford JSON, float64, variable dictionaries, or large tag
   blocks.
7. Large targets and tiny targets do not yet share the same operation language.

The redesign fixes this by making Omnitoken a layered codon protocol.

---

## Layer Model

```text
OT0  Codon vocabulary       finite ops, fields, status codes
OT1  Frame                  binary packet with sequence, window, crc
OT2  Fragment/manifest      bounded reassembly and payload hash
OT3  JupiterBox envelope    carrier box, mode, phase, route identity
OT4  Carrier binding        serial, TCP, WebSocket, Tailscale, I2P, ICMP, UDP
OT5  MNN routing            morphic adaptive routing based on goal, state, carrier
OT6  GCL dispatch           admit, attest, route, recover, execute/refuse
```

Only OT4 knows the substrate. OT0-OT3 must be portable across all carriers.

OT5 (MNN routing) is the Morphic Neural Network layer that adapts routing based on:
- Packet goal (health, attest, compress, route, recover)
- Local node state (memory, CPU, recovery mode, trust score)
- Carrier conditions (latency, loss rate, bandwidth)
- Historical outcomes (adaptive learning)

The MNN decides whether to execute locally, defer to the atlas, or reject the operation.

Hosted adapters that need JSON-L use `HUMAN_SURFACE_JSONL_SPEC.md` above this
layer. The JSON-L envelope is for human/tool surfaces; Omnitoken remains the
finite admitted projection.

---

## Design Invariants

Omnitoken MUST:

1. Use finite operation IDs, not open operation strings.
2. Treat carrier delivery as untrusted.
3. Include sequence and replay-window material in every nontrivial frame.
4. Separate accidental corruption checks from authentication.
5. Admit or reject work before expansion.
6. Support tiny targets without JSON, malloc, filesystem, or TCP/IP.
7. Support large targets through the same operation vocabulary.
8. Be routeable by GCL before shell-specific payload interpretation.
9. Fail closed on malformed, replayed, unordered-critical, or unauthenticated
   privileged frames.
10. Preserve recovery mode as a plain, minimal subset.

Omnitoken SHOULD:

1. Prefer compact fixed fields over variable maps.
2. Use manifests for large payloads.
3. Use JupiterBox for multiplexed and phase-aware transport.
4. Allow WebSocket only as a compatibility carrier, not as the inner protocol.
5. Maintain monotonic capability tiers.

---

## OMNI Core: Scale-Invariant Scalar LUT

The compressed internal form is a 1D scalar `s` plus a small context domain.
The scalar selects a LUT entry; the entry expands to a finite GCL codon.

```text
shell surface       local carrier appearance: udp, onion, serial, ipv923u
scalar s           scale-invariant 1D coordinate
domain d           finite context/LUT bank
lut[d][s]          compressed action entry
expanded codon     finite GCL/Omnitoken operation
```

Scale invariance means the shell can change resolution without changing
semantic identity. A 2-byte pulse, an 8-byte tiny frame, a WebSocket binary
message, and an onion payload may all project to the same `(d, s)` pair.
An IBM-II-class software Ethernet controller may also project the same pair
from an Ethernet-looking frame shell.

The shell is descriptive. The scalar/LUT pair is decisive.

```text
shell decides how it looks locally
scalar decides what it means internally
GCL decides whether it may become state
```

For tiny profiles, the preferred pulse is two bytes:

```text
u8 domain
u8 scalar
```

Example recovery pulse:

```text
domain = 0x0D  recovery bank
scalar = 0x01  recovery_subset_boot_ok
lut[0x0D][0x01] -> recover, recovery_allowed, admitted candidate
```

The 2-byte OISC is therefore not a carrier. It is an ultracompressed LUT
execution surface under Omnitoken.

### IBM-II Software Ethernet Intake

An early or intentionally tiny machine can host Omnitoken without a full network
stack by treating Ethernet as a shell around the scalar/LUT pair.

```text
Ethernet-looking frame
  -> shell validation: length, destination, EtherType, FCS
  -> payload[0..1]
  -> (domain, scalar)
  -> LUT admission
  -> GCL codon
```

The controller does not need to understand IP, UDP, TCP, onion routing, or
future `IPv923U`. It only needs to recognize the local shell boundary and pass
the two-byte OMNI core into the LUT. Hosted observers may wrap the admitted
result as JSON-L after the fact.

For an IBM-II-class target, the expected minimum shape is:

```text
RX ring          4 slots
RX slot budget   160 bytes
shell check      destination, EtherType, FCS
inner payload    u8 domain, u8 scalar
admission        finite LUT only
```

This proves the OMNI claim: Ethernet is just one appearance. The invariant
object is still the scale-invariant 1D scalar inside its LUT bank.

### AngrySphinx Default

The default dynamic LUT slot is `angry_sphinx`.

Unknown workloads, unknown shells, and unsafe AMMR routes MUST NOT expand into
large registries by default. They enter the AngrySphinx frustration range:

```text
unknown shell/workload
  -> AVMR mountain signal
  -> S3C partial-computation gate
  -> AMMR safety gate
  -> angry_sphinx slot
  -> proof-of-defense challenge or quarantine
```

This preserves the OMNI invariant while forcing reverse-engineering pressure to
pay solve cost before it can learn useful structure. Recovery remains the only
low-cost escape hatch.

### S3C Partial Computation

S3C is the partial-computation layer between mountain selection and LUT
expansion. A tiny node may not know enough to expand the full workload table, so
it evaluates only the shell coordinates of the proposed token:

```text
(lut_slot, domain, scalar)
  -> shell decomposition
  -> contact A / contact C
  -> bounded J-like score
  -> emit or fall back
```

If the S3C gate emits, AMMR may allow the slot to expand. If it does not emit,
the token SHOULD fall back to AngrySphinx unless it is already in the recovery
profile. This makes partial computation productive: the node spends just enough
work to choose a safe mountain range, not enough to reveal or load the whole
registry.

## OT0: Codon Vocabulary

The core operation table is one byte.

| ID | Op | Class | Meaning |
|----|----|-------|---------|
| 0x00 | `nop` | control | No operation / keepalive |
| 0x01 | `health` | control | Minimal liveness |
| 0x02 | `status` | control | Node state summary |
| 0x03 | `metrics` | control | Bounded telemetry |
| 0x04 | `attest` | trust | Hash/sign state |
| 0x05 | `admit` | gcl | RGFlow/admission check |
| 0x06 | `compress` | data | Compress or report method |
| 0x07 | `route` | gcl | Route or refuse |
| 0x08 | `manifest` | data | Fragment manifest |
| 0x09 | `fragment` | data | Fragment payload |
| 0x0A | `ack` | control | Acknowledge frame/window |
| 0x0B | `nack` | control | Reject/missing frame |
| 0x0C | `snapshot` | recovery | Persist tiny state |
| 0x0D | `recover` | recovery | Enter or operate recovery mode |
| 0x0E | `mark_good` | recovery | Mark image/state as good |
| 0x0F | `refuse` | gcl | Explicit lawful refusal |

Profile-specific operations start at `0x40`.

```text
0x40-0x5F swarm profile
0x60-0x7F storage profile
0x80-0x9F chain/container profile
0xA0-0xBF diagnostic profile
0xC0-0xEF experimental/private profile
0xF0-0xFF reserved
```

---

## OT1: Core Frame

The smallest standard frame is 16 bytes plus payload.

```text
u8    magic          0x4F
u8    version        0x01
u8    op             OT0 operation id
u8    flags          bitfield
u16le source_id      local or atlas-assigned short id
u16le route_id       route/window/domain id
u16le seq            sender sequence
u16le ack            receiver acknowledgment
u16le len            payload bytes
u16le crc16          frame header+payload corruption check
bytes payload        0..profile_max
```

Flag bits:

```text
0x01 payload_compressed
0x02 payload_authenticated
0x04 payload_fragmented
0x08 privileged
0x10 recovery_allowed
0x20 response_required
0x40 carrier_unreliable
0x80 reserved
```

CRC16 is for accidental corruption only. Authenticated profiles add MAC or
signature material in the payload or trailer.

Tiny profiles MAY use an 8-byte pulse frame for `health` only:

```text
u8 magic
u8 version
u8 op
u8 status
u16le source_id
u16le crc16
```

---

## OT2: Fragment and Manifest

UDP weakness research makes fragmentation explicit. No carrier fragment is
trusted as semantic state.

A manifest binds the payload:

```text
payload_hash      16 or 32 bytes
total_len         u32
fragment_count    u16
fragment_size     u16
codec             u8
admission_class   u8
route_hint        u16
```

Each fragment binds itself:

```text
manifest_id       16 bytes
fragment_index    u16
fragment_count    u16
offset            u32
chunk_hash        8 or 16 bytes
chunk_payload     bytes
```

Receiver rule:

```text
carrier arrival != state
valid fragment != state
complete manifest + hashes + replay check + GCL admission == candidate state
```

Reassembly MUST have a byte cap and timeout.

---

## OT3: JupiterBox Envelope

JupiterBox is the bounded carrier envelope. It supplies route identity, phase,
mode, and recovery metadata around Omnitoken frames.

```text
box_id            u16
mode              u8      0..13 for grounded phase
phase             u8      grounded, seismic, flame
priority          u8
ttl               u8
frame_count       u8
box_flags         u8
frames            Omnitoken frames
box_crc           u16
```

Phase behavior:

| Phase | Modes | Behavior |
|-------|-------|----------|
| grounded | 14 | Full multiplexing |
| seismic | 7 | Reduced multiplexing, prefer redundancy |
| flame | 1 or 0 | Do not rely on Jupiter-only path |

If phase is `flame`, GCL MUST either reject, route through a non-Jupiter
manifest shell, or require redundant carriers.

---

## OT4: Carrier Binding

Carriers are dumb pipes. Omnitoken must survive carrier differences.

| Carrier | Role | Rule |
|---------|------|------|
| serial | tiny/recovery | preferred for 8 KB targets |
| TCP | simple reliable carrier | still use Omnitoken seq/replay |
| WebSocket | compatibility | carries Omnitoken frames as binary |
| Tailscale | private mesh | normal large-node carrier |
| I2P | sovereign manifest path | prefer for manifest-heavy payloads |
| ICMP | ghost/sideband | heartbeat or small codon only |
| UDP | unreliable datagram | allowed only with OT2/OT3 protections |

UDP-specific rule:

```text
Raw UDP is never the protocol. It is only a carrier for Omnitoken frames.
```

Every UDP-carried frame MUST set `carrier_unreliable`.

---

## OT5: GCL Dispatch

GCL receives candidate Omnitoken frames and decides:

```text
drop
refuse
ack
nack
admit
route
execute local action
enter recovery
```

Dispatch order:

1. Parse fixed frame.
2. Check length and CRC.
3. Check replay window.
4. Check authentication if required.
5. Check operation privilege.
6. Run RGFlow/admission policy.
7. Expand/decompress only if admitted.
8. Execute or route.
9. Attest state transition.

No payload expansion before admission.

---

## Authentication and Replay

CRC is not security.

Security tiers:

| Tier | Name | Requirement |
|------|------|-------------|
| S0 | public pulse | CRC only, health/nop only |
| S1 | local trusted | CRC + replay window |
| S2 | peer trusted | MAC or keyed hash |
| S3 | atlas trusted | signature or attested session |
| S4 | recovery privileged | signature + physical/local policy |

Replay state for small nodes:

```text
source_id
last_seq
window_bitmap 16 or 32 bits
last_route_id
```

8 KB targets SHOULD use a 16-bit replay window. Larger targets SHOULD use 32 or
64 bits.

---

## Compression

Compression is an admission decision, not a default.

| Tier | RAM | Compression |
|------|-----|-------------|
| T0 | 2 KB | codon substitution only |
| T1 | 8 KB | RLE, tiny LZSS, static dictionary |
| T2 | 32 KB | larger LZSS/dictionary, fragments |
| T3 | 128 KB | stronger dictionary, object snapshots |
| T4 | 512 KB+ | zstd/lz4 profiles, WebSocket bridge |

Omnitoken frame headers are never compressed. Payloads may be compressed only
after admission policy says the CPU and memory trade is lawful.

---

## Capability Tiers

### T0: Pulse Node, about 2 KB RAM

Can:

```text
health
nop
refuse
recover-lite
```

Cannot:

```text
fragment
route tables
payload compression
dynamic peer state
```

### T1: GCL Nerve Ending, about 8 KB RAM

Can:

```text
health
status
attest-lite
admit
route-small
snapshot-small
recover
bounded replay
tiny compression
```

This is the reference minimum.

### T2: Embedded Node, about 32 KB RAM

Adds:

```text
fragment reassembly
small peer table
manifest verification
JupiterBox reduced mode
```

### T3: Rich Embedded Node, about 128 KB RAM

Adds:

```text
object spool
stronger hashes
better recovery shell
dictionary updates
```

### T4: Hosted Surface, 512 KB RAM and up

Adds:

```text
WebSocket carrier
JSON compatibility adapter
zstd/lz4
GDrive mount control
large-node swarm bridge
```

---

## Compatibility Adapters

Old packet styles should become adapters, not the core protocol.

### Metrics Adapter

Old:

```text
metric_name + float64 + timestamp + JSON tags + CRC32
```

New:

```text
OT1 op=metrics
payload = compact metric tuple or profile-specific metric block
```

### Transport Adapter

Old:

```text
transport action encoded as Omnitoken metric-like packet
```

New:

```text
OT1 op=route/admit/manifest
OT3 JupiterBox optional
OT4 carrier selected by MIMO
```

### Container Adapter

Old:

```text
OmniTokenAction container with idempotency, KOT cost, fragments, compliance
```

New:

```text
OT profile 0x80-0x9F
container_id -> manifest_id
idempotency -> replay/session field
compliance -> attestation payload
fragments -> OT2 fragments
```

---

## Failure Semantics

Omnitoken must have explicit failure language.

Refusal codes:

| Code | Meaning |
|------|---------|
| 0x00 | unknown |
| 0x01 | malformed |
| 0x02 | crc_failed |
| 0x03 | replay |
| 0x04 | auth_required |
| 0x05 | auth_failed |
| 0x06 | op_not_supported |
| 0x07 | privilege_required |
| 0x08 | admission_failed |
| 0x09 | route_unavailable |
| 0x0A | memory_budget_exceeded |
| 0x0B | fragment_timeout |
| 0x0C | manifest_hash_failed |
| 0x0D | jupiter_phase_flame |
| 0x0E | recovery_locked |
| 0x0F | carrier_untrusted |

Refusal is not failure if it preserves GCL invariants.

---

## Canonical Tiny Frame Example

A T1 health frame:

```text
4F 01 01 00  2A 00  01 00  10 00  0F 00  00 00  CRC CRC
```

Meaning:

```text
magic=0x4F
version=1
op=health
flags=0
source_id=42
route_id=1
seq=16
ack=15
len=0
crc16=...
```

No JSON. No strings. No heap.

---

## Redesign Migration Plan

1. Freeze this spec as Omnitoken v5 draft.
2. Keep old v4 metrics codec as `compat.metrics.v4`.
3. Implement a tiny reference codec in C or Rust with no allocation.
4. Implement a Python adapter for hosted nodes and Docker tests.
5. Replace open-string operations with OT0 IDs.
6. Route all old Omnitoken/MIMO/Jupiter paths through OT1/OT2/OT3.
7. Add Lean definitions for finite ops, frame validity, replay acceptance, and
   admission-before-expansion.
8. Only then deploy to Racknerd as a hosted carrier.

---

## The New Meaning of Omnitoken

Omnitoken is the language by which one observer chart asks another observer
chart to accept a lawful state transition.

Short form:

```text
Omnitoken = finite GCL codons + replay-aware frames + route-admissible state
```

It wants to be the invariant packet language of the atlas. This redesign makes
that explicit.
