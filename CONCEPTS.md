# Core Concepts — Quick Reference

This document contains essential architectural concepts for instant retrieval when describing the Research Stack system.

---

## FAMM — Frustration Aligned Memory Management

**Definition:** A route-memory layer that stores failed, partial, and successful paths as frustration/basin signals, then uses them to bias future search.

**Shorter:** FAMM manages memory by aligning search away from useless frustration and toward stable basins.

**Even shorter:** FAMM turns constraint pain into routing memory.

**Tagline:**
> I got you FAMM. Failed routes are not wasted.

### Two-Level Architecture

**FAMM = Memory Management Policy**
- Frustration Aligned Memory Management
- The architectural layer that manages routing memory

**Frustration-Manifold Torsion Memory = Physical/Mathematical Substrate**
- The physical theory and mathematical substrate behavior
- Stores route history as frustration/torsion patterns over a manifold

**Why this split:**
- "Frustration-Manifold Torsion Memory" sounds like the physical theory
- "Frustration Aligned Memory Management" sounds like the architecture that uses it

### Stack Placement

```
GWL  = topology/coupling geometry
FAMM = frustration-aligned memory policy
PIST = witness/audit surface
ISA  = executable control layer
FPGA = route search engine
Lean = proof filter
```

### Component Naming Convention

- **FAMM-Policy**: Memory management policy
- **FAMM-State**: Current memory state
- **FAMM-Update**: State update mechanism
- **FAMM-Prior**: Route bias generated from scars and basins
- **FAMM-Basin**: Remembered stable/accepted route neighborhood
- **FAMM-Scar**: Remembered failed route

### Core Principle: Geometry IS Memory

FAMM eliminates the traditional "RAM vs disk" separation. Instead of address-based memory cells, we use **positional geometry** as the storage medium.

**Fundamental shift:**
```
Traditional: address → data cell → value
FAMM approach: geometry position → physical property → value
```

From `BRAIN_AS_MANIFOLD.md`:
> "There is no 'RAM' vs 'disk' separation. The substrate shape IS the accumulated computation record. State is encoded in positional geometry (etch depth, surface topology), not in a separate metadata register."

### Implementation Layers

**Physical Substrate Layer:**
- **Crystal etch pattern** → Persistent state (physical alteration of surface)
- **Etch depth** → Encodes magnitude
- **Surface topology** → Encodes structure/relationships
- **Material composition** → Encodes type/category

**Access Mechanism:**
- **Photon pulses** → Active stream that reads/writes geometry
- **Total internal reflection path** → Depends on surface topology
- **Pulse modulation by mat** → Current state influence
- **Local etch chemistry trigger** → State update mechanism

**Key insight**: The pulse doesn't carry memory; it **traverses** it. The geometry modulates the pulse, and the pulse writes back to the geometry.

**Formal Substrate Operations (Substrate.lean):**
```lean
| substrateAlloc (size : UInt64)  -- Allocate substrate memory
| substrateFree (ptr : UInt64)    -- Free substrate memory
| substrateExec (id : UInt64)     -- Execute substrate computation
```

**Memory Access Burden Equation (F05):**
```
L_M(x) = log₂|E| + α·1[hit] + β + λ·|E|/|E_max|
```
- **|E|**: Engram store size (topological state space)
- **α**: Retrieval cost (geometry traversal)
- **β**: Update cost (etch chemistry)
- **λ**: Eviction pressure (substrate saturation)

### The "Weirdness" of Topological RAM

**Non-Euclidean Addressing:**
- Functional distance = optical path length through crystal
- NOT Euclidean spatial proximity
- Two cells on opposite crystal faces can be "closer" computationally than adjacent cells separated by opaque inclusion

**Zero Metadata Overhead:**
- Navigator spacing encodes state directly
- No separate metadata registers
- Etch pattern = state (isomorphic to engram overhead=0 design)

**Persistent + Ephemeral Fusion:**
- **Persistent**: Crystal etch pattern (long-term computation record)
- **Ephemeral**: Photon pulse pattern (active stream)
- **Fusion**: Running ratio Ñ_t = P/(ε_b·İ) between geometry and signal

**Substrate as Computation Medium:**
- Intelligence = topological tension
- Continuous pressure to minimize energy cost while maximizing substrate access
- Crystal manifold = computational medium itself

### Integration with Topology Equations

**Memory Access Burden (F05):**
Models the cost of storing/retrieving/updating routing memory in engram stores. This is the cognitive load equivalent of "RAM access time" in traditional systems, but applied to topological substrate traversal.

**Connection to GWL Topology:**
- **Spatial Proximity (F17)**: `h = exp(-|Δp|²/(2σ²))` → Distance decay on substrate
- **Rotational Alignment (F16)**: Frame orientation compatibility → Crystal facet alignment
- **Multi-Factor Coupling (F24)**: Complete 5-factor coupling including spatial proximity

**Substrate State in VM:**
```lean
structure VMState where
  stack : List UInt64
  memory : ByteArray
  pc : Nat
  gas : UInt64
  substrate : SubstrateState  -- ← Topological RAM component
```

### Advantages Over Traditional RAM

1. **No address translation overhead** - geometry IS the address
2. **Natural persistence** - crystal etch pattern survives power loss
3. **Parallel access** - multiple pulses can traverse different paths simultaneously
4. **Energy efficiency** - no refresh cycles, state maintained by physical structure
5. **Scalability** - substrate can grow fractally (fractal recursive quantum foam)

### Trade-offs

- **Access time** depends on optical path length, not clock cycle
- **Write speed** limited by etch chemistry kinetics
- **Read noise** from surface imperfections and photon scattering
- **Address space** limited by substrate surface area and resolution

---

## OTOM (Ordered Transformation & Orchestration Model)

**Full citation from OTOMOntology.lean:**
"OTOM (Ordered Transformation & Orchestration Model) — the unifying label for all Research Stack work."

**Domain breakdown:**
- **Ordered**: Formal structure, hierarchy, dependency chains
- **Transformation**: State transitions, bind primitive, evolution
- **Orchestration**: Multi-agent coordination, subsystems, convergence
- **Model**: 88+ Lean modules as unified formal system

**Repository:** github.com/allaun/OTOM  
**Version:** 2.0.0-Cambrian-Bind

---

## PIST (Perfectly Imperfect Square Theory)

**Correct meaning of the acronym in the OTOM framework.**

The "imperfect square" captures the essence of parallel non-orthogonal state exploration, while "perfectly" acknowledges the deliberate design of invariant-safe traversal.

This is the formal mathematical meaning used in papers and documentation. The blog post title "I Messed With Geometry and Now It's PIST" is an informal reference to this concept.

**Location:** Paper 12 in OTOM-papers repository, TTM Layer F (Control)

---

## ENE (Endless Node Edges)

ENE is a distributed, self-replicating credential and node management system.

**Architecture:**
- **Distributed:** ENE runs on every node (not centralized)
- **Self-Replicating:** ENE auto-replicates to new endpoints that don't have it
- **Gossip Protocol:** Nodes discover each other via gossip messages
- **Consensus-Based:** Credential rotation requires 2/3 node agreement
- **Local Storage:** Each node has SQLite DB with encrypted credential fragments

**Implementation:**
- File: `4-Infrastructure/infra/ene_distributed_node.py` (500+ lines)
- Classes: ENENodeIdentity, ENEGossipMessage, ENEDistributedNode, ENEMeshController
- Database: Per-node SQLite (ene_nodes/{node_id}.db)
- Replication: Automatic detection and propagation

**Key Points:**
- ENE is NOT centralized - it runs on every node
- New nodes automatically receive ENE via replication
- Credential fragments distributed across nodes (no single point of failure)
- Consensus required for sensitive operations
- Gossip protocol maintains mesh topology
- Self-replicating: ENE propagates itself to new infrastructure

---

## Topological Storage (Google Drive)

Google Drive is designated as the topological storage area for the Research Stack swarm system.

**Configuration:**
- Provider: Google Drive (Rclone)
- Mount Point: gdrive:topological_storage
- Status: Primary storage area

**Purpose:**
- Persistent storage of topological state
- Swarm state preservation
- Cross-session topology continuity
- Backup and recovery of manifold data

**Integration:**
- RcloneIntegration.lean formalizes this as TopologicalStorageArea structure
- All topological operations default to Google Drive storage
- Python Rclone integration configured for gdrive:topological_storage

**Architectural Decision:**
Google Drive was chosen as the topological storage area due to:
- Cloud accessibility from any swarm node
- Version history and recovery capabilities
- Large storage capacity for manifold data
- Integration with existing Rclone infrastructure

---

## Charged-Mass Braid Sieve

**Definition:** A mass-transfer primitive that routes unstable information through a path-sensitive braid field, separating its charge into stable signal, useful residue, scar memory, or dischargeable noise.

**One-line version:**
Charged-Mass Braid Sieve transfers unstable information through a path-sensitive braid field so its charge can be separated into stable signal, useful residue, scar memory, or dischargeable noise.

**Mechanism:**
1. Inject unstable information packet `x_i`.
2. Assign provisional charged mass `M_i`.
3. Rotate `x_i` through braid field `B`.
4. Let repeated braid interactions expose phase/charge instability.
5. Transfer mass from unstable packet into stable center if admissible.
6. Sieve remaining charge:
   - **coherent charge** → promote / basin
   - **partial charge** → hold / edge survivor
   - **unstable charge** → FAMM scar / quarantine
   - **incoherent charge** → discharge / ignore

**Formal Sketch:**
Let:
- `x_i` = unstable information carrier
- `q_i` = charge / domain coupling
- `M_i` = mass-number weight
- `B(t)` = braid state
- `C(t)` = emergent center
- `S(x_i)` = sieve decision
- `R_i` = residual instability

Then:
`M_i(t+1) = M_i(t) + Δadmissible(x_i, B, C) - Δrisk(x_i, B, C)`

The transfer rule is:
> Unstable charge becomes useful only if rotation lowers residual risk

**Relation to Mass Numbers:**
This is a physicalized version of the mass-number rule (`Mass Number = Admissible Reduction / Residual Risk`):
- charged mass field = mass-number field
- sieve charge = admissibility test
- unstable phase = residual / drift
- emergent center = stable basin
- anyon rotation = path-sensitive reweighting

**Architecture Placement:**
```yaml
name: Charged-Mass Braid Sieve
type: InteractionPhysics
domain: axis-11-geometry
secondary_domains:
  - axis-07-attestation
  - axis-01-compression
  - axis-06-safety
mass_kinds:
  - charged_route_mass
  - braid_phase_mass
  - admissibility_center_mass
  - residual_sieve_mass
settlement: FORMING
```

---

## Braid Eigensolid Compressor

**Definition:** A lossless compressor built on the 8-strand BraidStorm topology. The compressed state IS the receipt — not metadata around it.

**Key terms:**

- **Eigensolid:** The converged, stable state of a braid crossing loop. Detected when `crossStep(s) = s`. The DC baseline in the TNT BraidCarrier model.
- **BraidStorm:** The 8-strand braid topology. Strands cross pairwise; each crossing merges phase and produces a residual.
- **Sidon label:** An address from a set where all pairwise sums are unique. Canonical set for 8 strands: powers of 2 (1, 2, 4, 8, 16, 32, 64, 128).
- **Sidon slack:** `address budget − max label used`. Encodes capacity headroom as a receipt dimension.
- **Crossing matrix C:** Q0_2 crossing weights per strand pair. Contractiveness enforced: row sum < 65536.
- **Receipt dimensions:** `(C, σ, k, ε_seq, t, ∅_scars)` — together form the encoding of the compressed state.

**Two required Lean theorems:**
1. `eigensolid_convergence` — the braid crossing loop stabilizes. **Proven** (`EigensolidConvergence.lean`, commit `d84569a5`).
2. `receipt_invertible` — given the receipt, original state is reconstructible within bounded error. **Pending.**

**Float is forbidden.** All crossing weights and phase values use Q16_16 integer arithmetic. No substrate is privileged — the algorithm is identical on GPU (WGSL/wgpu), CPU (scalar), FPGA (Verilog), or storage (NVMe/BTRFS).

---

## Constrained Agent Framework

**Definition:** An execution framework that confines LLM/agent actions to a verifiable, bounded gate — the agent cannot act outside the declared action space.

**Three documented approaches (as of 2026-05-19):**
- **SmallCode gate** (`5-Applications/hutter_prize/SmallCode_constrained_agent_execution_gate.md`): The agent produces only syntactically valid, size-bounded code fragments. Gate rejects oversized or syntactically invalid outputs.
- **OR-Tools WASM constraint solver gate** (`5-Applications/hutter_prize/OR-Tools_WASM_constraint_solver_gate.md`): Uses OR-Tools compiled to WASM as the execution substrate. Agent actions must satisfy declarative constraint satisfaction; the solver is the arbiter.
- **GLIA** (Generic Lean Invariant Agent): Formal Lean invariants form the gate boundary. Any agent action that would violate a stated invariant is rejected at the Lean elaboration stage.

**Relation to FAMM:** Constrained agent execution is a special case of FAMM — failed/out-of-bounds agent outputs are scars; accepted outputs are basins. The frustration signal guides future generation toward lawful regions.

---

## Garage S3 Storage Stack

**Definition:** A self-hosted, S3-compatible object store running over a Tailscale mesh network, serving as the primary backend for the restic backup system.

**Implementation:** Garage v2.3.0 — single-binary, Dynamo-style S3-compatible store written in Rust. Replaces rclone serve s3.

**Topology:**

| Node | Tailscale IP | Role |
|------|-------------|------|
| qfox-1 | 100.88.57.96 | primary, S3 endpoint (1.8 TB NVMe) |
| cupfox-4gb-2cpu | 100.126.242.5 | storage node (planned) |
| nixos | 100.119.165.120 | storage node (planned) |
| microvm-racknerd | 100.101.247.127 | storage node VPS (planned) |

**Buckets:** `research-stack`, `db-scratch`, `rds-overflow`, `snap-zone`, `gdrive-mirror`.

**Storage agent** (`4-Infrastructure/storage/storage_agent.py`): observe→decide→act loop every 15 min. Q16_16 thresholds throughout. JSONL hash-chain receipts at `~/.cache/storage-agent.jsonl` and `s3://research-stack/agent-receipts/`.

---

## See Also

- `AGENTS.md` — Full operating rules and specifications (includes Topological RAM section 10)
- `BRAIN_AS_MANIFOLD.md` — Detailed brain-as-manifold theory
- `EQUATION_FOREST_INDEX.md` — Equation taxonomy and kernel IDs
- `MATH_MODEL_MAP.tsv` — Equation registry (source of truth)
- `4-Infrastructure/AGENTS.md` — Infrastructure operating contract (storage stack, ENE RDS, WGSL compute dispatch)
