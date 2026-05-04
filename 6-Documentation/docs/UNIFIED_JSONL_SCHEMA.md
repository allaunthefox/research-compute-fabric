# Unified JSON-L Schema Specification — Manifold Ingestion Stream

**Version:** 1.0  
**Status:** ACTIVE — replaces discrete Notion/Linear/ENE shims  
**Ground Truth:** `0-Core-Formalism/lean/Semantics/` (bind bridge invariant preservation)  
**Target:** `data/substrate_index.db` — unified ENE substrate  

---

## 1. Design Principles

1. **Single Source of Truth**: Every state change — whether from Notion, Linear, ENE, or the blockchain proxy — reduces to one JSON-L line. The ENE SQLite substrate is the manifold.
2. **Bind Bridge Compliance**: Every event carries a `bind` struct with `lawful` (Bool), `cost` (Q16_16 UInt32), and `invariant` (String). No Python/Rust shim may compute cost; it is extracted from Lean or propagated from upstream.
3. **Temporal Immutability**: `t` is the single time axis. Events are append-only. Corrections are new events with `op: "correct"` referencing `prev_id`.
4. **Genome Addressability**: Every event MAY carry a `genome` field. If present, it is a 6D quantized signature deterministically hashable to an 18-bit address (`address = genome.hash() & 0x3FFFF`). This allows the event to be routed into the same hierarchical multicast buckets as blockchain blocks.
5. **No Open Strings in Decisions**: The `src` field is `Fin 5` (notion, linear, ene, rgflow, swarm). The `op` field is `Fin 5` (upsert, delete, snapshot, correct, attest). All other categorical fields use finite enumerations.

---

## 2. Mandatory Root Fields

| Field | Type | Description |
|-------|------|-------------|
| `t` | `f64` | Unix timestamp with millisecond resolution. Monotonic within a single `src`. |
| `src` | `Fin 5` | Origin: `notion`, `linear`, `ene`, `rgflow`, `swarm`. |
| `id` | `String` | Unique within `src`. Format: `<src>:<uuid>` or deterministic hash. |
| `op` | `Fin 5` | `upsert` \| `delete` \| `snapshot` \| `correct` \| `attest`. |
| `data` | `Dict` | Source-specific payload. Schema varies by `src` (see §4). |
| `genome` | `Genome` *(optional)* | 6D quantized spectral signature for RGFlow routing. |
| `bind` | `Bind` *(optional)* | Cost, lawful check, invariant extractor. Required for CORE-tier events. |
| `provenance` | `Provenance` | Node, lake seed, and attestation chain. |

---

## 3. Common Sub-Structures

### 3.1 `Genome` — RGFlow Addressable Signature

```json
{
  "mu":   0,  // UInt8  — compression ratio bin (0..7)
  "rho":  0,  // UInt8  — information density bin (0..7)
  "c":    0,  // UInt8  — thermodynamic cost bin (0..7)
  "m":    0,  // UInt8  — manifold curvature bin (0..7)
  "ne":   0,  // UInt8  — negentropy flux bin (0..7)
  "sig":  0   // UInt8  — signal-to-noise bin (0..7)
}
```

- **Address**: `address = (mu << 15) | (rho << 12) | (c << 9) | (m << 6) | (ne << 3) | sig` → 18-bit value `0..262143`.
- **Bucket**: `bucket = address >> 15` → top 3 bits, `0..7`. Used for multicast routing.
- **Determinism**: Every `src` MUST define a pure function `event → Genome` with no randomness. The genome is a lossy projection of `data`, not a hash.

### 3.2 `Bind` — Invariant Preservation Witness

```json
{
  "lawful": true,           // Bool — does this event preserve all invariants?
  "cost": 65536,            // UInt32 Q16_16 — computational/thermodynamic cost
  "invariant": "bindPreservesState: t_k+1 > t_k => forwardBlit", // String
  "class": "informational_bind"  // Fin 5: informational | geometric | thermodynamic | physical | control
}
```

- **Cost computation**: For `rgflow` events, cost is the byte count of the compressed genome. For `ene` events, cost is the L2 norm of the concept vector scaled to Q16_16. For `notion`/`linear`, cost is fixed at `0x00010000` (1.0) until a Lean cost function is extracted.
- **Rule**: If `lawful == false`, the event is written to the substrate but flagged in `swarm_work_queue` for review. No downstream manifold blit occurs.

### 3.3 `Provenance` — Attestation Chain

```json
{
  "node": "qfox",              // String — hostname of originating node
  "lake_seed": "nnyyP7DoHS11CNTRL", // String — Tailscale stable node ID
  "tailscale_ip": "100.105.111.120", // String — for routing verification
  "attestation_hash": "sha256:...",  // String — cumulative hash of event + prev attestation
  "prev_id": null            // String or null — previous event in causal chain
}
```

- **Attestation**: Every event is attested by the node that generated it. The hash chain allows `back-trace re-sync` when out-of-order events are detected.
- **Swarm propagation**: When an event is pushed via `/sync/manifest`, the `provenance.node` field is updated to the forwarding node, preserving the original in a nested `origin` field.

---

## 4. Source-Specific `data` Schemas

### 4.1 `src: "notion"` — Document Hierarchy Event

```json
{
  "page_id": "7a27bd85-9ff0-44fe-b873-7bb90f2a91a0",
  "block_id": "...",
  "parent_id": "...",
  "title": "Quantum Hamiltonian Manifold",
  "content_hash": "b3f5...f6bf",
  "last_edited_time": "2026-04-24T13:42:00.000Z",
  "property_changes": {
    "Status": {"old": "Draft", "new": "Review"}
  }
}
```

- **Genome mapping**: `mu = len(title) % 8`, `rho = popcount(content_hash) % 8`, `c = property_changes.count % 8`, `m = 4` (stable document), `ne = 7` (high semantic density), `sig = tier_index("RESEARCH")`.
- **ENE mapping**: Upsert into `packages` table. `pkg = notion/<page_id>`, `archetype = "document"`, `concept_anchor.resolution = property_changes["Status"].new`.

### 4.2 `src: "linear"` — Causal Dependency Event

```json
{
  "issue_id": "RES-7",
  "linear_id": "d8f2c1b4-...",
  "title": "Implement bind bridge for Q16_16",
  "state": {"old": "Todo", "new": "In Progress"},
  "priority": {"old": 2, "new": 1},
  "assignee": {"old": null, "new": "allaun"},
  "blocked_by": ["RES-3", "RES-5"],
  "identifier": "RES-7"
}
```

- **Genome mapping**: `mu = priority.new % 8`, `rho = len(blocked_by) % 8`, `c = state_transition_cost(state.old, state.new)`, `m = 2` (forming), `ne = assignee.new ? 4 : 0`, `sig = 0`.
- **ENE mapping**: Upsert into `packages`. `pkg = linear/<issue_id>`, `archetype = "issue"`, `session_id = linear_id`. `concept_anchor.resolution` maps from Linear state: `Todo→SEED`, `In Progress→FORMING`, `Done→STABLE`, `Canceled→RECOVERED`.

### 4.3 `src: "ene"` — Substrate Atomic Ingestion

```json
{
  "pkg": "semantics/Adaptation",
  "version": "2026-04-24T12:00:00Z",
  "tier": "CORE",
  "domain": "formalization",
  "archetype": "lean_module",
  "concept_anchor": {
    "domain": "formalization",
    "concept": "flow_audit_loop",
    "resolution": "CRYSTALLIZED"
  },
  "concept_vector": [1.0, 0.618, 0.0, 0.0, 0.146, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
  "idea_weights": {"bind primitive": 0.95, "Q16_16": 0.88},
  "files": ["0-Core-Formalism/lean/Semantics/Adaptation.lean"],
  "depends": ["semantics/Q16_16/2026-04-20T00:00:00Z"]
}
```

- **Genome mapping**: Derived from `concept_vector` via axis quantization: each dimension is binned to 3 bits using `floor(dim * 8 / max_dim)`.
- **ENE mapping**: Direct upsert into `packages` table. All fields map 1:1.

### 4.4 `src: "rgflow"` — Blockchain Genome Event

```json
{
  "chain": "btc",
  "height": 548000,
  "block_hash": "0000000000000000000...",
  "timestamp": 1777031220,
  "genome": {"mu": 3, "rho": 7, "c": 2, "m": 5, "ne": 1, "sig": 6},
  "address": 262143,
  "bucket": 7,
  "raw": {"size": 1456234, "tx_count": 2847, "difficulty": 1.23e14}
}
```

- **Genome mapping**: Already computed by `bitcoin_block_to_genome()` / `ethereum_block_to_genome()` in `scripts/blockchain_rgflow_proxy.py`. Deterministic 6D quantization from block metadata.
- **ENE mapping**: Upsert into `swarm_manifest`. `t = timestamp`, `node = provenance.node`, `genome = json.dumps(genome)`.

### 4.5 `src: "swarm"` — Topology / Work Queue Event

```json
{
  "event_type": "topology_change",  // topology_change | task_complete | node_failure | sync_manifest
  "hostname": "architect",
  "tailscale_ip": "100.127.111.7",
  "status": "active",
  "latency_ms": 281.0,
  "load": 0.34,
  "manifest_inserted": 42  // only for sync_manifest events
}
```

- **Genome mapping**: `mu = latency_ms < 100 ? 0 : latency_ms < 300 ? 2 : 4`, `rho = load * 8 % 8`, `c = status == "active" ? 0 : 7`, `m = 4`, `ne = manifest_inserted > 0 ? 7 : 0`, `sig = 0`.
- **ENE mapping**: Upsert into `swarm_nodes` or `swarm_work_queue` depending on `event_type`.

---

## 5. Manifold Convergence Rules

### 5.1 Forward Blit (Normal Case)

For any source, if `Upsert(t_k)` is followed by `Upsert(t_{k+1})` where `t_{k+1} > t_k`:
- The event is **lawful by monotonicity**.
- The manifold state is updated via a forward blit: `state' = state ⊕ data`.
- The `bind.cost` is additive: `cost_total = cost_total + bind.cost`.

### 5.2 Back-Trace Re-Sync (Out-of-Order)

If an event arrives with `t_k < t_latest`:
1. The event is written to the substrate with `op: "correct"` and `prev_id` pointing to the event it supersedes.
2. A **back-trace** is initiated: the SRAM Scaffolding buffer (last 1024 events in `swarm_query_cache`) is replayed from `t_k` to `t_latest`.
3. Each replayed event is re-evaluated for `bind.lawful`. If any event becomes unlawful, the entire segment is quarantined in `swarm_work_queue` with `status: "failed"`.
4. The manifold is reconstructed from the quarantine boundary forward.

### 5.3 SRAM Scaffolding Buffer

The buffer is a circular log of the last 1024 JSON-L events, stored in `swarm_query_cache`:
- `query_hash = sha256(event.id + event.t)`
- `subjects = event.src`
- `results = json.dumps(event)`
- `semantic_vector = event.genome || event.data.concept_vector || zeros(14)`
- `ttl = 86400` (24 hours)

---

## 6. Ingestion Pipeline

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Notion    │   │   Linear    │   │    ENE      │   │   RGFlow    │
│   (pull)    │   │   (webhook) │   │   ( Lake )  │   │   (ZMQ/WS)  │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │                 │
       └─────────────────┴─────────────────┴─────────────────┘
                           │
                    ┌──────▼──────┐
                    │  JSON-L     │
                    │  Canonical  │
                    │  Converter  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Bind Bridge│
                    │  (Lean #eval│
                    │   or cached)│
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐ ┌───▼────┐ ┌────▼─────┐
       │  ENE SQLite │ │Swarm   │ │Multicast │
       │  substrate  │ │Surface │ │239.255.x │
       │  (master)   │ │(mesh)  │ │(buckets) │
       └─────────────┘ └────────┘ └──────────┘
```

### 6.1 SQLite Insert Paths

| `src` | Target Table | Unique Key | Conflict Resolution |
|-------|-------------|------------|---------------------|
| `notion` | `packages` | `pkg = notion/<page_id>` | REPLACE (newer `t` wins) |
| `linear` | `packages` | `pkg = linear/<issue_id>` | REPLACE |
| `ene` | `packages` | `(pkg, version)` | REPLACE |
| `rgflow` | `swarm_manifest` | `(chain, height)` | INSERT OR IGNORE |
| `swarm` | `swarm_nodes` / `swarm_work_queue` | `hostname` / `task_id` | REPLACE |

### 6.2 Swarm Surface Sync

After SQLite insertion on qfox:
1. The push loop (`_push_loop` in `swarm_surface.py`) broadcasts the new manifest entry to all `active` peers.
2. Peers receive via `/sync/manifest` and insert into their local ENE DB.
3. If a peer is `offline`, the entry remains in qfox's DB. When the peer comes back online, the pull loop (`_pull_loop`) catches up by querying `/manifest?limit=1000`.

---

## 7. Verification Requirements

Per `AGENTS.md` §4, every `def` that computes a cost or invariant must have a witness. The JSON-L schema enforces this via:

1. **Eval witness**: Every `src` converter script must include a `#eval`-style test block (in Lean) or a Python `assert` block with expected output in a comment.
2. **Theorem witness**: The `Bind` struct must satisfy `bindPreservesInvariant : ∀ e : Event, e.bind.lawful → invariant(e.data) = invariant(state')`.
3. **Totality**: No `partial` functions in the conversion pipeline. Every `event → Genome` mapping is total and deterministic.

---

## 8. Example Stream

```jsonl
{"t":1777042800.000,"src":"rgflow","id":"rgflow:btc:548000","op":"upsert","data":{"chain":"btc","height":548000,"block_hash":"0000...dead","timestamp":1777042800,"address":42,"bucket":5,"raw":{"size":1456234,"tx_count":2847}},"genome":{"mu":3,"rho":7,"c":2,"m":5,"ne":1,"sig":6},"bind":{"lawful":true,"cost":65536,"invariant":"blockHashConserved","class":"informational_bind"},"provenance":{"node":"qfox","lake_seed":"nnyyP7DoHS11CNTRL","tailscale_ip":"100.105.111.120","attestation_hash":"sha256:abc...","prev_id":null}}
{"t":1777042801.000,"src":"linear","id":"linear:RES-7","op":"upsert","data":{"issue_id":"RES-7","title":"Implement bind bridge","state":{"old":"Todo","new":"In Progress"},"priority":1,"assignee":"allaun","blocked_by":["RES-3"]},"genome":{"mu":1,"rho":1,"c":3,"m":2,"ne":4,"sig":0},"bind":{"lawful":true,"cost":65536,"invariant":"stateTransitionValid","class":"control_bind"},"provenance":{"node":"qfox","lake_seed":"nnyyP7DoHS11CNTRL","tailscale_ip":"100.105.111.120","attestation_hash":"sha256:def...","prev_id":null}}
{"t":1777042802.000,"src":"ene","id":"ene:semantics/Adaptation:2026-04-24T12:00:00Z","op":"upsert","data":{"pkg":"semantics/Adaptation","version":"2026-04-24T12:00:00Z","tier":"CORE","domain":"formalization","archetype":"lean_module","concept_anchor":{"domain":"formalization","concept":"flow_audit_loop","resolution":"CRYSTALLIZED"},"concept_vector":[1.0,0.618,0.0,0.0,0.146,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0],"files":["0-Core-Formalism/lean/Semantics/Adaptation.lean"]},"genome":{"mu":0,"rho":5,"c":0,"m":1,"ne":7,"sig":0},"bind":{"lawful":true,"cost":98304,"invariant":"theorem finalLawfulEqEventuallyLawful","class":"informational_bind"},"provenance":{"node":"qfox","lake_seed":"nnyyP7DoHS11CNTRL","tailscale_ip":"100.105.111.120","attestation_hash":"sha256:ghi...","prev_id":null}}
```

---

## 9. Migration Path

### Phase 1 — Shim Unification (Now)
- [x] `swarm_surface.py` exposes `/sync/manifest` and `/topology`
- [x] `blockchain_rgflow_proxy.py` writes to `swarm_manifest` directly
- [ ] `notion.js` → add JSON-L exporter feeding ENE `packages`
- [ ] `linear.js` → add JSON-L exporter feeding ENE `packages`

### Phase 2 — Lean Ground Truth
- [ ] Port `event → Genome` mappings to Lean 4 (`0-Core-Formalism/lean/Semantics/JsonL/Converter.lean`)
- [ ] Prove `bindPreservesInvariant` for each `src` class
- [ ] Extract cost functions to Q16_16 (no Float in hot path)

### Phase 3 — Hardware Extraction
- [ ] Verilog generator for JSON-L → genome address decoder
- [ ] FPGA Warden node runs bind bridge in hardware

---

*Document ID:* UNIFIED_JSONL_SCHEMA_v1  
*Authority:* Human architect  
*Date:* 2026-04-24
