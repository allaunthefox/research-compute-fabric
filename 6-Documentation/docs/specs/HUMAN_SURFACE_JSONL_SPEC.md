# Human Surface JSON-L Spec

**Version:** 0.1  
**Status:** Draft surface envelope  
**Scope:** JSON-L event format for every human-facing surface that feeds Omnitoken, GCL, ENE, RGFlow, and embedded node surfaces  
**Depends on:** `docs/UNIFIED_JSONL_SCHEMA.md`, `docs/specs/OMNITOKEN_GCL_REDESIGN.md`, `docs/specs/EMBEDDED_NODE_SURFACE_SPEC.md`

---

## Thesis

The atlas needs one append-only language for human surfaces.

A human surface is any interface where a person, tool, model, device, or storage
substrate exposes state that a node may observe, route, compress, attest, or
recover.

Examples:

- Chat messages
- Documents
- Tasks
- Code changes
- Terminal sessions
- Browser/search traces
- Email and calendar events
- Files and mounted drives
- Images, audio, video, maps, sensors
- APIs, databases, ledgers, model outputs
- Recovery pulses and node health events

The surface layer is JSON-L because hosted nodes and human tools can inspect it.
Tiny nodes do not parse JSON-L directly. They receive the admitted result as
Omnitoken/GCL codons.

```text
human surface -> JSON-L envelope -> GCL admission -> Omnitoken frame
```

---

## Design Invariants

1. Every observed surface event MUST fit in one JSON object per line.
2. The line MUST be append-only. Corrections are new lines.
3. Decision fields MUST be finite enums.
4. Future surfaces MUST have a place to land without changing the core enum.
5. Raw adapter payloads MAY be preserved, but GCL MUST admit before expansion.
6. Large content SHOULD be referenced by hash or URI, not embedded.
7. Hosted JSON-L and tiny Omnitoken MUST share the same operation intent.
8. Unknown surfaces MUST be preservable and routeable as unknown, not discarded.
9. Privacy and patent-hold status MUST travel with the event.
10. Recovery mode MUST use the same envelope with a smaller required subset.

---

## Layer Position

```text
HS0  Surface classes       finite human/computational surface classes
HS1  JSON-L envelope       append-only hosted event line
HS2  Admission projection  finite op, caps, cost, privacy, genome
HS3  Omnitoken mapping     scalar/LUT, OT0 op id, flags, route id, manifest
HS4  Shell/storage         Ethernet, GDrive, disk, WS, serial, TCP, onion, future labels
```

`HS1` is intentionally richer than an embedded node can afford. `HS2` is the
projection boundary. Anything not admitted by `HS2` remains archived data, not
state.

Default unknown-shell behavior is AngrySphinx quarantine. Unknown surfaces are
preserved as archive data, but their Omnitoken projection SHOULD use the
`angry_sphinx` LUT slot until a hosted registry admits a more specific workload
profile.

Tiny projections MAY include S3C partial-computation metadata such as
`s3c_emit` and `s3c_score`. These fields describe whether the proposed
`(lut_slot, domain, scalar)` had enough shell contact to expand; they are not a
replacement for GCL admission.

---

## Mandatory Root Fields

| Field | Type | Meaning |
|-------|------|---------|
| `v` | String | Schema version, currently `hs-jsonl-0.1` |
| `id` | String | Stable event id |
| `t` | Number | Unix timestamp, seconds with optional fraction |
| `op` | Enum | Surface operation intent |
| `surface` | Object | Surface class, kind, instance, and capabilities |
| `actor` | Object | Human, agent, service, or node that caused the event |
| `object` | Object | Thing being observed or changed |
| `content` | Object | Hash, URI, MIME, text, or compact payload pointer |
| `gcl` | Object | Admission, lawful state, cost, refusal, and invariants |
| `omni` | Object | Omnitoken projection metadata |
| `provenance` | Object | Origin, chain, node, source time, and prior event |
| `privacy` | Object | Disclosure, retention, and patent-hold policy |

Optional root fields:

| Field | Type | Meaning |
|-------|------|---------|
| `genome` | Object | 6D RGFlow routing signature |
| `links` | Array | Typed edges to other events or objects |
| `storage` | Object | Local, GDrive, content-addressed, or remote storage pointer |
| `raw` | Object | Adapter-native payload preserved after admission boundary |
| `render` | Object | Human presentation hints, never decision-critical |

---

## Finite Operation Enum

`op` is a finite enum. Adapters MUST map their native actions into one of these
values.

| Op | Meaning | Typical OT0 Projection |
|----|---------|------------------------|
| `observe` | Read or witness state without claiming change | `status`, `metrics` |
| `assert` | Add or upsert a state claim | `admit` |
| `revise` | Correct or supersede a previous claim | `admit` |
| `delete` | Tombstone or remove availability | `admit` |
| `attest` | Hash, sign, or witness state | `attest` |
| `route` | Ask the atlas to move or locate state | `route` |
| `recover` | Enter or report recovery mode | `recover` |
| `snapshot` | Persist a compact state image | `snapshot` |
| `render` | Produce a human-viewable representation | profile op |
| `reply` | Respond to an interaction | profile op |
| `link` | Create an edge between objects | `admit` |
| `refuse` | Preserve a lawful refusal | `refuse` |

Profile-specific operations MAY appear in `raw.native_op`, but never in `op`.

---

## Surface Classification

The surface decision field is `surface.class`. It is finite.

| Class | Meaning |
|-------|---------|
| `chat` | Human or agent conversation |
| `doc` | Document, note, page, paper, wiki |
| `task` | Issue, ticket, todo, project state |
| `code` | Repository, diff, review, build artifact |
| `terminal` | Shell, command, log, process interaction |
| `file` | File object, mount object, object-store blob |
| `drive` | Mounted cloud or remote drive surface |
| `email` | Mail message or mailbox state |
| `calendar` | Calendar event, availability, schedule |
| `browser` | Web page, search result, bookmark, tab state |
| `api` | HTTP/RPC/tool call boundary |
| `db` | Database row, query, schema, materialized view |
| `sensor` | Hardware or environmental reading |
| `image` | Image or visual artifact |
| `audio` | Audio artifact or stream |
| `video` | Video artifact or stream |
| `map` | Geospatial object or route |
| `finance` | Price, trade, account, market observation |
| `chain` | Blockchain, ledger, proof, block, transaction |
| `model` | Model prompt, output, embedding, eval |
| `node` | Runtime, health, topology, recovery surface |
| `unknown` | Preserved unknown surface |

The open extension field is `surface.kind`, a namespaced string such as
`notion.page`, `linear.issue`, `gdrive.file`, `github.pull_request`,
`jupiterbox.pulse`, or `racknerd.health`.

The rule is:

```text
surface.class decides
surface.kind explains
raw preserves
```

---

## Surface Object

```json
{
  "class": "doc",
  "kind": "notion.page",
  "instance": "notion:workspace:research",
  "caps": ["read", "write", "link", "attest"],
  "adapter": "notion-v1",
  "adapter_version": "0.1"
}
```

`caps` is finite:

```text
read write delete link attest route recover render stream mount execute
```

Adapters MAY add human labels in `render`, but capability decisions use `caps`.

---

## Actor Object

```json
{
  "type": "agent",
  "id": "node:qfox",
  "display": "qfox",
  "authority": "local_admin"
}
```

`actor.type` is finite:

```text
human agent service node model device unknown
```

`authority` is finite:

```text
none local_user local_admin root service_token delegated recovery
```

---

## Object Object

```json
{
  "type": "page",
  "id": "notion:page:7a27bd85",
  "stable_id": "sha256:...",
  "parent": "notion:database:research-stack",
  "version": "2026-04-25T16:40:00Z"
}
```

`object.type` is adapter-specific descriptive text. It does not decide
admission. Admission uses `surface.class`, `op`, `caps`, `privacy`, and `gcl`.

---

## Content Object

The content object should prefer pointers over bulk payloads.

```json
{
  "mime": "text/markdown",
  "hash": "sha256:...",
  "size": 2048,
  "uri": "gdrive://research-stack/docs/specs/example.md",
  "summary": "Surface event for a reusable embedded node spec.",
  "text": "Optional short text payload."
}
```

Allowed fields:

| Field | Meaning |
|-------|---------|
| `mime` | Media type |
| `hash` | Content hash |
| `size` | Byte size before compression |
| `compressed_size` | Byte size after compression |
| `codec` | `none`, `zstd`, `brotli`, `gzip`, `heatshrink`, `lz4`, `custom` |
| `uri` | Storage or retrieval URI |
| `summary` | Short human summary |
| `text` | Small text payload |
| `bytes_b64` | Small binary payload only |
| `refs` | Content references |

Large payloads MUST become Omnitoken manifests or storage references before
transport to constrained nodes.

---

## GCL Object

```json
{
  "admission": "candidate",
  "lawful": true,
  "cost_q16_16": 65536,
  "invariant": "admission_before_expansion",
  "refusal_code": "none",
  "capability_tier": "T4"
}
```

`gcl.admission` is finite:

```text
unknown candidate admitted refused quarantined archived
```

`gcl.refusal_code` maps to the Omnitoken refusal table:

```text
none unknown malformed replay auth_required auth_failed op_not_supported
privilege_required admission_failed route_unavailable memory_budget_exceeded
fragment_timeout manifest_hash_failed recovery_locked carrier_untrusted
```

`capability_tier` is finite:

```text
T0_pulse T1_8kb T2_32kb T3_128kb T4_hosted T5_full
```

---

## Omnitoken Object

```json
{
  "op_id": "0x05",
  "source_id": 42,
  "route_id": 1,
  "seq": 16,
  "flags": ["response_required"],
  "manifest_id": null,
  "frame_profile": "OT1"
}
```

`omni.flags` is the symbolic form of OT1 flags:

```text
payload_compressed payload_authenticated payload_fragmented privileged
recovery_allowed response_required carrier_unreliable
```

Hosted JSON-L MAY omit `seq` before projection. Once projected to Omnitoken,
sequence and replay-window material are required for nontrivial frames.

---

## Provenance Object

```json
{
  "origin": "notion:workspace:research",
  "node": "qfox",
  "observed_t": "2026-04-25T16:40:00Z",
  "ingested_t": "2026-04-25T16:40:02Z",
  "prev_id": null,
  "attestation_hash": "sha256:..."
}
```

`prev_id` links corrections, replies, and causal chains. `attestation_hash`
SHOULD be the cumulative hash of the normalized event plus the previous
attestation hash.

---

## Privacy Object

```json
{
  "tier": "patent_hold",
  "retention": "archive",
  "export": "deny",
  "redaction": "none"
}
```

`privacy.tier` is finite:

```text
public internal private secret patent_hold local_only
```

`privacy.export` is finite:

```text
allow redact deny local_only
```

`privacy.retention` is finite:

```text
ephemeral cache archive legal_hold delete_requested
```

No adapter may downgrade privacy. A forwarded event may only keep or strengthen
the tier.

---

## Storage Object

```json
{
  "class": "drive",
  "uri": "gdrive://research-stack/surfaces/2026/04/event.jsonl",
  "mount": "/mnt/gdrive",
  "content_address": "sha256:...",
  "local_cache": "/var/lib/atlas/cache/sha256/..."
}
```

`storage.class` is finite:

```text
none local drive object_store db content_addressed remote ephemeral
```

For underpowered nodes, storage SHOULD be an external mount or content-addressed
cache. The node surface does not need a full application stack if a drive can
hold the heavy state.

---

## Links

```json
[
  {
    "rel": "supersedes",
    "target": "hs:old-event-id"
  },
  {
    "rel": "derived_from",
    "target": "gdrive://research-stack/raw/source.md"
  }
]
```

`rel` is finite:

```text
parent child supersedes corrects derived_from caused_by blocks blocked_by
mentions replies_to attests_to stores routes_to recovers_from mirrors
```

---

## Genome

The optional `genome` field is the same 6D quantized routing signature used by
the existing unified JSON-L schema.

```json
{
  "mu": 0,
  "rho": 0,
  "c": 0,
  "m": 0,
  "ne": 0,
  "sig": 0
}
```

The genome is not a hash. It is a lossy routing projection.

---

## Minimal Recovery Line

Recovery mode may emit only the required recovery subset:

```json
{
  "v": "hs-jsonl-0.1",
  "id": "node:racknerd-510bd9c:recover:0001",
  "t": 1777135200.0,
  "op": "recover",
  "surface": {
    "class": "node",
    "kind": "racknerd.health",
    "instance": "racknerd-510bd9c",
    "caps": ["read", "recover"],
    "adapter": "embedded-surface",
    "adapter_version": "0.1"
  },
  "actor": {
    "type": "node",
    "id": "node:racknerd-510bd9c",
    "display": "racknerd-510bd9c",
    "authority": "recovery"
  },
  "object": {
    "type": "runtime",
    "id": "node:racknerd-510bd9c",
    "stable_id": "node:racknerd-510bd9c",
    "parent": null,
    "version": "recovery"
  },
  "content": {
    "mime": "application/json",
    "hash": "sha256:...",
    "size": 64,
    "summary": "Recovery heartbeat."
  },
  "gcl": {
    "admission": "admitted",
    "lawful": true,
    "cost_q16_16": 1,
    "invariant": "recovery_subset",
    "refusal_code": "none",
    "capability_tier": "T1_8kb"
  },
  "omni": {
    "op_id": "0x0D",
    "source_id": 42,
    "route_id": 1,
    "seq": 1,
    "flags": ["recovery_allowed"],
    "manifest_id": null,
    "frame_profile": "OT1"
  },
  "provenance": {
    "origin": "node:racknerd-510bd9c",
    "node": "racknerd-510bd9c",
    "observed_t": "2026-04-25T16:40:00Z",
    "ingested_t": "2026-04-25T16:40:00Z",
    "prev_id": null,
    "attestation_hash": "sha256:..."
  },
  "privacy": {
    "tier": "internal",
    "retention": "cache",
    "export": "deny",
    "redaction": "none"
  }
}
```

---

## Example: Chat Surface

```json
{
  "v": "hs-jsonl-0.1",
  "id": "chat:research:2026-04-25:0001",
  "t": 1777135201.5,
  "op": "assert",
  "surface": {
    "class": "chat",
    "kind": "codex.session",
    "instance": "research-stack",
    "caps": ["read", "write", "link", "attest"],
    "adapter": "codex",
    "adapter_version": "0.1"
  },
  "actor": {
    "type": "human",
    "id": "human:allaun",
    "display": "allaun",
    "authority": "local_admin"
  },
  "object": {
    "type": "message",
    "id": "chat:research:msg:0001",
    "stable_id": "sha256:...",
    "parent": "chat:research",
    "version": "1"
  },
  "content": {
    "mime": "text/plain",
    "hash": "sha256:...",
    "size": 92,
    "summary": "Request for a JSON-L spec that can cover every human surface.",
    "text": "Use every human surface possible and have space for more."
  },
  "gcl": {
    "admission": "candidate",
    "lawful": true,
    "cost_q16_16": 65536,
    "invariant": "surface_event_append_only",
    "refusal_code": "none",
    "capability_tier": "T4_hosted"
  },
  "omni": {
    "op_id": "0x05",
    "source_id": 42,
    "route_id": 1,
    "seq": null,
    "flags": ["response_required"],
    "manifest_id": null,
    "frame_profile": "hosted-jsonl"
  },
  "provenance": {
    "origin": "codex:session",
    "node": "qfox",
    "observed_t": "2026-04-25T16:40:01.500Z",
    "ingested_t": "2026-04-25T16:40:02.000Z",
    "prev_id": null,
    "attestation_hash": "sha256:..."
  },
  "privacy": {
    "tier": "patent_hold",
    "retention": "archive",
    "export": "deny",
    "redaction": "none"
  }
}
```

---

## Example: GDrive Mounted File

```json
{
  "v": "hs-jsonl-0.1",
  "id": "gdrive:file:research-stack:spec:0001",
  "t": 1777135222.0,
  "op": "observe",
  "surface": {
    "class": "drive",
    "kind": "gdrive.file",
    "instance": "gdrive:research-stack",
    "caps": ["read", "write", "mount", "attest"],
    "adapter": "rclone",
    "adapter_version": "1"
  },
  "actor": {
    "type": "service",
    "id": "service:rclone",
    "display": "rclone",
    "authority": "service_token"
  },
  "object": {
    "type": "file",
    "id": "gdrive://research-stack/docs/specs/HUMAN_SURFACE_JSONL_SPEC.md",
    "stable_id": "sha256:...",
    "parent": "gdrive://research-stack/docs/specs",
    "version": "2026-04-25T16:40:22Z"
  },
  "content": {
    "mime": "text/markdown",
    "hash": "sha256:...",
    "size": 12000,
    "uri": "gdrive://research-stack/docs/specs/HUMAN_SURFACE_JSONL_SPEC.md",
    "summary": "Reusable human surface JSON-L envelope."
  },
  "storage": {
    "class": "drive",
    "uri": "gdrive://research-stack/docs/specs/HUMAN_SURFACE_JSONL_SPEC.md",
    "mount": "/mnt/gdrive",
    "content_address": "sha256:...",
    "local_cache": null
  },
  "gcl": {
    "admission": "candidate",
    "lawful": true,
    "cost_q16_16": 4096,
    "invariant": "external_storage_pointer",
    "refusal_code": "none",
    "capability_tier": "T4_hosted"
  },
  "omni": {
    "op_id": "0x08",
    "source_id": 42,
    "route_id": 2,
    "seq": null,
    "flags": ["payload_fragmented"],
    "manifest_id": "sha256:...",
    "frame_profile": "OT2"
  },
  "provenance": {
    "origin": "gdrive:research-stack",
    "node": "qfox",
    "observed_t": "2026-04-25T16:40:22Z",
    "ingested_t": "2026-04-25T16:40:23Z",
    "prev_id": null,
    "attestation_hash": "sha256:..."
  },
  "privacy": {
    "tier": "internal",
    "retention": "archive",
    "export": "redact",
    "redaction": "hash_only"
  }
}
```

---

## Example: Terminal Command Result

```json
{
  "v": "hs-jsonl-0.1",
  "id": "terminal:qfox:cmd:0001",
  "t": 1777135244.0,
  "op": "attest",
  "surface": {
    "class": "terminal",
    "kind": "bash.command",
    "instance": "qfox",
    "caps": ["read", "execute", "attest"],
    "adapter": "local-shell",
    "adapter_version": "0.1"
  },
  "actor": {
    "type": "agent",
    "id": "agent:codex",
    "display": "codex",
    "authority": "local_user"
  },
  "object": {
    "type": "command",
    "id": "terminal:qfox:cmd:0001",
    "stable_id": "sha256:...",
    "parent": "terminal:qfox",
    "version": "exit:0"
  },
  "content": {
    "mime": "text/plain",
    "hash": "sha256:...",
    "size": 128,
    "summary": "Command completed successfully."
  },
  "gcl": {
    "admission": "admitted",
    "lawful": true,
    "cost_q16_16": 1024,
    "invariant": "attested_command_result",
    "refusal_code": "none",
    "capability_tier": "T4_hosted"
  },
  "omni": {
    "op_id": "0x04",
    "source_id": 42,
    "route_id": 3,
    "seq": null,
    "flags": ["payload_authenticated"],
    "manifest_id": null,
    "frame_profile": "hosted-jsonl"
  },
  "provenance": {
    "origin": "terminal:qfox",
    "node": "qfox",
    "observed_t": "2026-04-25T16:40:44Z",
    "ingested_t": "2026-04-25T16:40:44Z",
    "prev_id": null,
    "attestation_hash": "sha256:..."
  },
  "privacy": {
    "tier": "private",
    "retention": "cache",
    "export": "deny",
    "redaction": "none"
  }
}
```

---

## Legacy Mapping

The existing `docs/UNIFIED_JSONL_SCHEMA.md` remains the ENE substrate ingestion
schema. This spec is the wider surface envelope.

Legacy `src` maps into `surface` as follows:

| Legacy `src` | Surface Class | Surface Kind |
|--------------|---------------|--------------|
| `notion` | `doc` | `notion.page` or `notion.database` |
| `linear` | `task` | `linear.issue` |
| `ene` | `db` | `ene.package` |
| `rgflow` | `chain` | `rgflow.block` |
| `swarm` | `node` | `swarm.topology` |

Legacy `op` maps as follows:

| Legacy `op` | Human Surface `op` |
|-------------|--------------------|
| `upsert` | `assert` |
| `delete` | `delete` |
| `snapshot` | `snapshot` |
| `correct` | `revise` |
| `attest` | `attest` |

---

## Admission Rules

1. Parse the JSON object.
2. Validate mandatory fields and finite enums.
3. Verify privacy cannot be downgraded.
4. Refuse privileged operations without authority.
5. Hash or manifest large content before payload expansion.
6. Compute or propagate `genome`.
7. Evaluate GCL admission and cost.
8. Project admitted intent to Omnitoken OT0.
9. Assign sequence/window state when sending over a carrier.
10. Archive refused lines with `op: "refuse"` or `gcl.admission: "refused"`.

The key rule is:

```text
archive can store arbitrary surface data
state can only contain admitted finite projections
```

---

## Tiny Target Projection

Tiny nodes do not implement this full JSON-L schema.

| Target | Receives |
|--------|----------|
| `T0_pulse` | Health/recovery pulse only |
| `T1_8kb` | OT1 frames, no JSON, tiny fixed buffers |
| `T2_32kb` | OT1 plus bounded manifests |
| `T3_128kb` | OT1/OT2 plus small dictionaries |
| `T4_hosted` | Full JSON-L envelope |
| `T5_full` | Full adapters, search, render, storage |

The JSON-L envelope is the human-readable front porch. Omnitoken is the nerve
signal.

---

## Future Surface Rule

When a new human surface appears:

1. Choose the nearest existing `surface.class`.
2. Add a namespaced `surface.kind`.
3. Preserve native fields under `raw`.
4. Map native operations into finite `op`.
5. Define capability and privacy behavior.
6. Define GCL admission behavior.
7. Define Omnitoken projection.

No core schema change is required unless the new surface cannot be truthfully
represented by any existing class.
