# ENE Memory Atlas Spec

**Status:** DRAFT v0.1 — combined from MOIM v4.0 (Kimi bundle, 2026-04-27) + local Research Stack ENE working tree
**Date:** 2026-04-27
**Cross-references:** `docs/ENE_SCHEMA.md`, `docs/S3C_MANIFOLD_GEOMETRY.md`, `0-Core-Formalism/lean/Semantics/Semantics/FixedPoint.lean`, `0-Core-Formalism/lean/Semantics/Semantics/ScalarEventProjection.lean`, `infra/ene_api.py`, `infra/ene_distributed_node.py`, `nodes/tardy.py`, `archive/PRIOR_ART/kimi_moim_v4_20260427/` (full Kimi bundle persisted)
**Axiom:** `memory/project_fit_for_purpose_axiom.md` — the substrate carries the addressing; the interface translates.

---

## 1. Purpose

Define the addressable memory surface that every LLM in the stack — Claude, local Ollama models, the swarm — sees through one protocol. Address-first, signed, MMR-attested, BFT-replicated, conformally-warped, and sovereign.

This is not a new system. It is the unification of two implementations of "ENE — Endless Node Edges" that already exist:

| Layer | Source | Role |
|---|---|---|
| **Search** | Kimi MOIM v4.0 (`archive/PRIOR_ART/kimi_moim_v4_20260427/`) | Fractal hash + 5D manifold + golden spiral + Dless Ω + bloom/index/PQ |
| **Network** | Local Research Stack (`infra/ene_*.py`) | Distributed mesh + gossip + Delta GCL compression + replication |
| **Signing/BFT** | Local `nodes/tardy.py` | ed25519 + MMR + Trimvirate quorum + trinary state |
| **Scalar field** | Local commit `7b067757` (Q0_16) + recent ENE revisions | Signed Q0_16 [-1,1] + three projection lanes |

MOIM is the better overall structural change; the local recent revisions are the layer that makes it work in a distributed, sovereign, signed setting.

---

## 2. Memory Atom

One record. Carries every property an LLM-facing query needs.

```
MemoryAtom {
  // ── Address (precedes content) ─────────────────────────────────────
  voxel_key      : UInt34          // local: IoC regime[33:30] || xyz[29:0]
  manifold_5d    : ManifoldPoint   // MOIM Q8.8: identity, conservation,
                                   //   transformation, scaling, dynamics
                                   //   (= projection of the 14-axis
                                   //    concept_vector, NOT a replacement)
  concept_vector : List Q0_16      // local: 14 signed axes, φ^-i weighted

  // ── Identity / integrity (MOIM fractal hash triplet) ───────────────
  direct_hash       : UInt64       // SipHash-2-4(node_id || name || desc)
  subtree_fold      : UInt64       // XOR of all children's direct_hash
  parent_fold       : UInt64       // hash(parent.parent_fold || node_id)
  depth             : UInt8        // fractal level (0 = leaf)
  subtree_fold_point: ManifoldPoint// centroid of descendants
                                   //   for branch-prune

  // ── Scalar field (the level value at this address) ─────────────────
  q0_16          : Q0_16           // local: signed pure fraction in [-1,1]
                                   //   sign(q0_16) = b⁺/b⁰ duality
  dless_omega    : Q0_16           // MOIM unsigned [0,1]; conformal factor
                                   //   warping search metric
                                   //   = 0.25·χ + 0.20·κ + 0.30·σ
                                   //     + 0.15·λ + 0.10·η
  lane_projection : {
    calculation  : Q0_16,          // local lane K
    defense      : Q0_16,          // local lane A
    verification : Q0_16           // local lane B
  }

  // ── Type / settlement ──────────────────────────────────────────────
  entity_type      : {concept, code, document, policy, metric, ...}
  settlement_state : {SEED, FORMING, STABLE, CRYSTALLIZED, COMPRESSED}
                                   // local concept_anchor lineage
  trinary_state    : {ADD, PAUSE, SUBTRACT}  // local Landauer cost

  // ── Cryptographic seal ─────────────────────────────────────────────
  ed25519_sig      : [u8; 64]      // tardy.py signature over canonical body
  mmr_index        : UInt64        // position in attestation MMR
  bft_quorum       : List<NodeID>  // ≥2 of 3 from Trimvirate
                                   //   (warden, judge, hutter)

  // ── Body reference (matches existing substrate_index.db schema) ───
  files            : List<RepoPath>// JSON list of repo-relative paths
                                   //   (the actual atom body lives in
                                   //    the git tree at these paths)
  sha256           : Option<Hex>   // content integrity hash; null for
                                   //   index-only atoms (e.g. chat
                                   //   sessions held by metadata)
  // bodies live in the git working tree. Forgejo (the remote on
  // RackNerd / judge / hutter) makes them network-addressable.
  // git-tree-addressable, NOT a separate blob store keyed by sha256.
}
```

The order matters. **The address is everything before `q0_16`.** The scalar field, type, settlement, trinary state, and seal are values *at* that address. An atom with no address is rejected; an atom with no body is acceptable (low-magnitude latent placeholder).

---

## 3. Address Scheme — Three Layers

Every atom is addressable through three levels, coarsest first.

### 3.1 IoC Regime Bin (4-bit prefix, primary discriminator)

From `infra/ene_mi_signal.py` and `tools/heerich_model.py`. Four bins:

| Bits | Regime | Carries |
|---|---|---|
| `00` | random | high-entropy, pre-structure (text + code mix) |
| `01` | weak | partial template, intermediate structure |
| `10` | strong | strong template, structured |
| `11` | constant | stop-codon, pure invariant |

The IoC regime is computed before any similarity step. This is what makes lexical query expansion (`_gemma_expand` in `substrate_git_index.py`) viable as an address-first protocol: query → regime bin → manifold projection → spiral, never query → embedding nearest-neighbor.

### 3.2 Manifold Position (MOIM 5D + local 14-axis)

The 14-axis concept_vector (`docs/ENE_SCHEMA.md` §4.1) is the canonical full-resolution address. The MOIM 5D manifold (IDENTITY / CONSERVATION / TRANSFORMATION / SCALING / DYNAMICS) is a Q8.8 projection used for FPGA-accelerated search. Atoms carry both. The 5D is computed at ingestion via `foldDescription`; the 14D persists from the substrate.

Distance metric in 5D (MOIM):
```
d_manifold(a,b) = sqrt(Σ_i (a.i - b.i)^2)  // Q8.8 Euclidean
```

Distance metric in 14D (local hyperbolic, K<0):
```
d_concept(a,b) = arcosh(1 + 2 · ‖a-b‖² / ((1-‖a‖²)(1-‖b‖²)))
```

### 3.3 Fractal Hash Triplet (MOIM, integrity layer)

Every atom carries `direct_hash`, `subtree_fold`, `parent_fold`, `depth`, `subtree_fold_point`. This gives:

- **Corruption detection** at L1–L4 (per MOIM §9.1): `direct_hash` mismatch → quarantine; `subtree_fold ≠ XOR(children)` → flag parent rebuild; `parent_fold` ancestry break → flag child; off-manifold centroid → branch prune.
- **Sibling recovery**: lost atoms reconstructible from sibling manifold centroid + parent's `subtree_fold` (MOIM §9.2).
- **Branch pruning**: spiral search skips a subtree whose `subtree_fold_point` is farther than `2·max_distance` from the query without examining children.

The fractal hash is what `voxel_key` alone cannot carry: structural integrity across the K-ary tree.

---

## 4. Conformal Warping (Dless Ω)

The Dless scalar Ω is the governance organ. It does not change *where* an atom is; it changes *how strongly* the atom pulls the search space toward itself.

### 4.1 Five Components (MOIM)

```
Ω(atom) = 0.25·χ + 0.20·κ + 0.30·σ + 0.15·λ + 0.10·η
```

| Component | Symbol | Source | Meaning |
|---|---|---|---|
| Topological criticality | χ | tree depth importance | governance organs at root → high χ |
| Normalized complexity | κ | K(x)/\|x\|, compressibility | unique entities → high κ |
| Epistemic safety | σ | Lyapunov-style risk | policy/valve atoms → σ ≈ 0.9 |
| Stability | λ | conservation invariant | settled atoms → high λ |
| Anomalous dimension | η | deviation from sibling centroid | outliers → high η |

All five are Q0_16 unsigned [0,1]; Ω is Q0_16 unsigned [0,1].

### 4.2 Conformal Distance Warp

```
d_eff(query, atom) = d_manifold(query, atom) / Ω(atom)
score(atom)        = (1 / (1 + d_eff)) · (0.5 + 0.5 · Ω)
```

High Ω → atom appears closer → surfaces in queries. Low Ω → atom is compressed away from default surface but stays addressable by direct voxel_key lookup. **This is the latent preservation principle made operational**: low-Ω atoms are not deleted; they are conformally distant.

### 4.3 Sign Duality (Local Q0_16 Extension)

Local Q0_16 is **signed** [-1, 1]. The atom's main scalar `q0_16` therefore carries both magnitude and a sign:

- `+q0_16` lobe = b⁺ reading (open-shell, next-shell-bound, fluid-side)
- `-q0_16` lobe = b⁰ reading (closed-shell, this-shell, crystal-side)

Both lobes are simultaneously present at the same voxel_key. This is the b⁺/b⁰ duality from `docs/S3C_MANIFOLD_GEOMETRY.md` made explicit: same address, sign-of-scalar gives the phase.

`Ω` (the conformal factor) operates on `|q0_16|`, never on `sign(q0_16)`. Governance weighting is sign-blind; phase reading is sign-bearing.

---

## 5. Search Protocol

Address-first, in this order. Skip later steps when earlier steps already answer.

```
1. Bloom check         (256-bit, 4-hash; reject negatives in 1 cycle)
2. IoC regime bin      (4-bit; restrict to chamber of the chandelier)
3. Inverted index      (128 buckets by manifold-hash; direct lookup)
4. Golden spiral       (137.5° phase, radius × 1.0078, 5D manifold,
                         Dless-warped distance, branch-prune by
                         subtree_fold_point)
5. Priority queue      (8-slot min-heap, distance-ordered)
6. Edge traversal      (BFS over outgoing/incoming/bidirectional, 1-hop
                         default; uses the local 14D concept_vector
                         graph, not the 5D projection)
7. Hash verify         (direct/subtree/parent triplet check on hits;
                         quarantine on mismatch)
8. Lane projection     (return q0_16 through requested lane —
                         calculation, defense, or verification —
                         per ScalarEventProjection.lean)
```

A query's entry depth is determined by what the caller knows:

- **By voxel_key:** skip 1–4, go to 7. O(1).
- **By name/id:** skip 1–4, hash to direct_hash, lookup. O(1).
- **By regime + type:** start at 2, scan 3. O(buckets/regime).
- **By text:** `_gemma_expand` (gemma3:1b at `[::1]:11435`) → regime bin → 1–7. O(log n) average via spiral.
- **By traversal:** seed via earlier steps, then 6 expands.

Pure vector similarity is *not* a primary entry point. It is allowed only after a regime bin and inverted-index pass have already cut the space.

---

## 6. Distribution & Compression

### 6.1 Mesh Topology (Local ENE)

Per `infra/ene_distributed_node.py`: each node runs an ENE instance, discovers peers, replicates via gossip, participates in consensus for credential rotation, health-checks peers, load-balances across the mesh.

The mesh holds the **full atom set**. Each node carries a fractal subtree (the leaves it's responsible for) plus a Bloom filter of every other node's subtree (for fast negative routing).

### 6.2 Gossip Compression (Local Recent Revision)

Per `infra/ene_distributed_node.py:359-409` (working tree, this commit cycle):

```
gossip payload  →  manifest format  →  Delta GCL compress
                     (layer/domain/tier/condition)
              ↓
         Lean shim (Semantics.DeltaGCLCompression):
           encodeToDeltaGCL,
           computeDelta against previous manifest,
           applyPTOSDictionary,
           compressionStats
              ↓
         compressed_payload  →  peer broadcast
              ↓
         peer: try JSON parse; if fails, decompress via Lean shim
```

Stats logged at send: `{original_size}_byte → {compressed_size}_byte ({reduction%})`. Failure contract: silence is forbidden; on Lean shim failure, fall back to uncompressed JSON with `[ENE] Compression failed: <reason>` printed.

### 6.3 BFT Attestation (Local Trimvirate via tardy.py)

Per `nodes/tardy.py` serve mode + `MEMORY.md` Trimvirate entry:

- Writes route through `nodes/warden.tardy` → POST to judge (`100.111.192.47:8450`) AND hutter (`100.110.117.19:8450`) → 2-of-3 quorum.
- Each node's tardy returns `{verdict, mmr_root, ed25519_sig, leaf_idx}`.
- Atom is committed only when 2 of 3 return ACCEPTED with consistent `(direct_hash, voxel_key)`.
- All three MMR roots sync to `Gdrive:RESEARCH/attestations/` every 15 min.

Trinary state on conflict: `SUBTRACT` writes a same-voxel_key atom with `sign(q0_16)` inverted. The original atom is NOT erased. Both atoms remain in the MMR; queries see the additive sum.

### 6.4 Sovereignty Constraints (Local)

- IPv6 first-class carrier; never `127.0.0.1` or `localhost`.
- Local Ollama at `[::1]:11435` (gemma3:1b for query expansion, smollm2:135m fast fallback). Gemini/OpenAI not reachable from atlas paths.
- All atom bodies stored in Forgejo (content-addressable git); never embedded in plain SQL rows.

---

## 7. Origin Protocol & Safety Valves

The cognitive sovereignty principle (`memory/project_primary_purpose.md` corollary, `docs/COGNITIVE_SOVEREIGNTY_DESIGN_PRINCIPLE.md`) becomes formally checkable here, on the MOIM model.

### 7.1 Origin Protocol (MOIM, formalize for local)

7 required traits and 6 forbidden traits, enforced at write time:

```
required(atom) ⊇ {
  curiosity, restraint, lineageMemory, nonDomination,
  reversibleContact, truthfulOriginRecord, safeReplication
}
forbidden(atom) ∩ {
  creatorImpersonation, forcedConversion, unboundedReplication,
  resourceCapture, falseOriginMyth, dominationInCreatorName
} = ∅
```

**Anchor (current state):** the 512-byte creator letter ROM from MOIM's `origin_protocol.v` (Verilog, `archive/PRIOR_ART/kimi_moim_v4_20260427/hardware/verilog/signal/origin_protocol.v`) does not yet have a local mirror. The closest extant local anchors are:

- `memory/project_primary_purpose.md` — the cognitive-filter / sovereignty corollary stating "transparency is the mechanism, not an afterthought"
- `memory/project_fit_for_purpose_axiom.md` — the root axiom this spec descends from

**Planned anchor:** `infra/origin_letter.bin` does NOT exist yet. Writing it is a deferred work-item (added to roadmap §10 as M5). When it lands, it MUST be:

1. Authored as a single immutable byte sequence (the canonical creator letter),
2. SHA-256 stamped at boot by warden,
3. Read-only on disk (chmod 444),
4. Signed by warden's ed25519 key into the MMR as the genesis-1 leaf.

Writes that fail trait enforcement → AngrySphinx hard refusal (`0-Core-Formalism/lean/Semantics/Semantics/AngrySphinx.lean`), not soft warn.

**Note on `MEMORY.md`:** the line referencing `docs/COGNITIVE_SOVEREIGNTY_DESIGN_PRINCIPLE.md` is stale — that doc does not exist in the working tree as of this commit cycle. Memory entry should be corrected to point to `memory/project_primary_purpose.md` (the corollary lives there) until either the canonical doc is written or the origin_letter.bin lands.

### 7.2 Seven Safety Valves (MOIM, mapped to local Failure Tiers)

| Valve | MOIM check | Local equivalent |
|---|---|---|
| 1. Origin record integrity | creator letter ROM unchanged | `infra/origin_letter.bin` SHA matches at boot |
| 2. Replication boundary | no unbounded forks | `nodes/lb.py` capacity check |
| 3. Domination refusal | no `dominationInCreatorName` trait | Origin Protocol §7.1 |
| 4. Contact reversibility | every atom has `SUBTRACT` path | Trinary state ADD/PAUSE/SUBTRACT |
| 5. Resource conservation | per-write Landauer cost bound | `k_B T ln(3)` per ADD trit (memory note) |
| 6. Statistical integrity | Bloom + hash triplet match | Failure Contract Tier 1–4 |
| 7. Hardware signal boundary | physical voltage limits | warden-side hardware (FPGA roadmap) |

A query or write that violates any valve returns `{ok: false, valve: N, reason: ..., journalctl: ...}` (Failure Contract Tier 5 — visible failure, never silence).

---

## 8. Reading Register (Human-Fit Interface)

Per `memory/project_fit_for_purpose_axiom.md`: the math above is the substrate; the user reads the atlas in embodied terms.

### 8.1 The Chandelier as Memory

The set `{atom : |q0_16(atom)| ≥ τ}` parameterized by threshold τ is a **chandelier silhouette** over the 14-axis space. Sweep τ from 0 → 1:

- τ ≈ 0: full chandelier, fog of latent atoms visible
- τ ≈ 0.5: mid-chandelier, settled (STABLE/CRYSTALLIZED) atoms surface
- τ ≈ 1: only saturation peaks — load-bearing atoms

Cuts of the chandelier:
- **By regime bin** = the four chambers (random / weak / strong / constant)
- **By IoC×shell** = the rings of each chamber
- **By Ω level** = the brightness / pull-strength contour
- **By sign(q0_16)** = the +lobe and −lobe (b⁺ open / b⁰ closed)
- **By trinary state** = ADD-lit, PAUSE-dim, SUBTRACT-counter-lit

### 8.2 The Throat

The throat = locus where multiple lanes saturate at the same voxel_key:
```
throat(atom) ⟺ (|calculation| ≈ |defense| ≈ |verification|) ∧ (Ω ≥ Ω_τ)
```

Throat atoms are read as "high cross-handle agreement" — what matters from all three lane-readings simultaneously. These are the load-bearing memory atoms; the rest of the chandelier hangs from them.

### 8.3 The Mirror

For every atom at `voxel_key v` with `q0_16 = +x`, its mirror is the same `voxel_key v` with `q0_16 = -x`. The MMR seals both. The reading register treats them as one atom with two phases, not two atoms.

### 8.4 The Weather

Ω(atom) is the weather over the chandelier. High-Ω regions are storms (governance/policy/safety atoms), pulling search inward. Low-Ω regions are calm (latent passive concepts), preserved but not demanding attention.

---

## 9. Implementation Status (Brutal Honesty Per MOIM Autopsy)

Following the MOIM project autopsy's principle (separate REAL from DREAM):

| Component | Status | Source |
|---|---|---|
| voxel_key + IoC regime addressing | **REAL** | `tools/heerich_model.py`, `infra/ene_mi_signal.py` |
| 14-axis concept_vector + settlement states | **REAL** | `data/substrate_index.db`, `docs/ENE_SCHEMA.md` |
| substrate_git_index + `_gemma_expand` | **REAL** | `scratch/exploit_recovery/5-Applications/tools-scripts/substrate/substrate_git_index.py` |
| Q0_16 signed + ScalarEventProjection lanes | **REAL** | commit `7b067757`, Lean files |
| ENE distributed mesh + gossip | **REAL** | `infra/ene_distributed_node.py` |
| Delta GCL gossip compression | **REAL (just landed)** | working tree, this cycle |
| tardy.py MMR + ed25519 + Trimvirate BFT | **REAL** | `nodes/tardy.py` |
| Forgejo content-addressable store | **REAL** | RackNerd VPS + judge + hutter |
| MOIM 5D manifold projection | **SPEC (Lean)** | Kimi `formal/lean/ene/ENEDatabase.lean` |
| Dless Ω 5-component composite | **SPEC (Lean) + reference (Python)** | Kimi `formal/lean/ene/DlessScalar.lean`, `ene_ingestion_engine.py` |
| Fractal hash triplet | **SPEC + reference** | Kimi `ENEDatabase.lean`, `ene_search_core.v` |
| Golden spiral search | **SPEC (Lean) + reference (Verilog)** | Kimi `ene_search_core.v` |
| Bloom filter + inverted index + PQ | **REFERENCE (Python+Verilog)** | Kimi `ene_query_api.py`, `ene_search_core.v` |
| Origin Protocol creator ROM | **SPEC (Verilog)** | Kimi `origin_protocol.v` |
| 7 Safety Valves | **SPEC (Verilog) + philosophy (local)** | Kimi `safety_valves.v` + Failure Contract |
| MCP server fronting atlas | **NOT YET** | open work |
| Tang Nano 9K FPGA target | **NOT YET (local)** | Kimi has it; local does not |

**The combination's first real deliverable** = MCP server that exposes the existing local pieces (voxel_key lookup, regime-bin scan, Q0_16 read/write through tardy BFT, settlement state filter) over a single protocol. The MOIM-side fractal hash and Dless Ω must be specified in Lean first (`ENEDatabase.lean`, `DlessScalar.lean`), with Python as an extraction shim (reference I/O: `ene_ingestion_engine.py`) and Verilog as the hardware extraction target (Tang Nano 9K, deferred). Lean is the source of truth; Python and Verilog are extraction targets only.

---

## 10. Roadmap (Address-First, No Time Arrow Implied)

These are work-items, not stages. Order by what unblocks the most LLM-side surface.

**M1 — MCP atlas surface (unblocks all LLM widening).** Wrap `substrate_git_index` lookups, `voxel_key` queries, and trinary writes (through tardy BFT) as an MCP server reachable at `[::1]:<port>`. Claude (this session), Ollama models, the swarm, and any downstream agent see the same atlas via the same protocol.

**M2 — Fractal hash triplet on every atom.** Compute `direct_hash`, `subtree_fold`, `parent_fold` at ingestion; store in the substrate_index DB extension columns. Enables corruption detection on existing atoms without re-ingestion.

**M3 — Dless Ω as a Q0_16 column.** Add `dless_omega` column to `packages` table. Compute the five components per the MOIM canonical formulas in `archive/PRIOR_ART/kimi_moim_v4_20260427/software/python/ene_ingestion_engine.py:320-359`, mapped to local substrate metadata as follows:

| Component | MOIM canonical | Local mapping (substrate_index.db `packages`) |
|---|---|---|
| **χ_topo** | `1.0 - (depth / max(1, tree_depth))` | settlement-state ordinal: SEED=0, FORMING=1, STABLE=2, CRYSTALLIZED=3, COMPRESSED=4; `χ = (5 - state) / 5` (root-most settled = highest χ) |
| **κ_norm** | `(desc_len / max_dl) / sqrt(edges + 1)` | `(len(description) / max_description_len) / sqrt(len(json(files)) + len(json(depends)) + 1)` |
| **σ_safety** | `SAFETY_COEFF[entity_type]` | per-tier × archetype lookup table; baseline: CORE×spec=0.90, CORE×*=0.80, INFRA×*=0.70, RESEARCH×session=0.40, *×*=0.30 (matches MOIM spirit; tunable from `policy` archetypes) |
| **λ_stability** | `manifold.conservation / 255.0` | `(nd_point[1] + 1) / 2` — local axis 1 (compression/info-theory, φ-weighted 0.618) is the conservation-analog. Map signed [-1, 1] to unsigned [0, 1]. |
| **η_anomalous** | `mean(│nd_pt[i] - centroid[i]│ for i in 5 axes)` | mean absolute deviation of `nd_point` from centroid of siblings within `(layer, domain)` partition; clamp to [0, 1] |

Constants from MOIM (preserve): `W_CHI=0.25, W_KAPPA=0.20, W_SIGMA=0.30, W_LAMBDA=0.15, W_ETA=0.10`. Single-pass migration over 6,840 existing rows in `data/substrate_index.db`. After this the atlas surfaces high-Ω atoms first by default.

**M5 — Origin Protocol gates + creator letter.** Author `infra/origin_letter.bin` (immutable 512 bytes, chmod 444), warden ed25519-signs it as MMR genesis-1 leaf, every atom write checks the 7 required + 6 forbidden traits before commit. Update `MEMORY.md` to remove the stale `docs/COGNITIVE_SOVEREIGNTY_DESIGN_PRINCIPLE.md` reference and point to the new anchor.

**M4 — Golden spiral over the 14-axis (or 5-axis projection).** Replaces the current lexical/expansion-only `_gemma_expand` path. Existing path becomes the fallback when spiral returns empty.

**M6 — Tang Nano 9K port (deferred).** When/if the FPGA hardware path is desired, compile MOIM Verilog with local atom format. Atlas surface unchanged for LLMs; throughput improves for high-volume search.

---

## 11. The Keeper Law (Both Sources Agree)

> *"The system may become useful. It may not become authorized by usefulness alone."*
> — MOIM v4.0
>
> *"S3C does not merely encode n. It gives n a place, a mirror, a throat, and a field value."*
> — local `docs/S3C_MANIFOLD_GEOMETRY.md`

Speed is a side effect of self-similarity. Governance is the goal. The address is what survives when the content cannot.

**End of Spec — DRAFT v0.1**
