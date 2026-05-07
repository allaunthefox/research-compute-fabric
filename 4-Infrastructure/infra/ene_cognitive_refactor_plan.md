# ENE Cognitive Refactoring Plan

**Date:** May 5, 2026 (restructured May 6, 2026)
**Domain:** ENE (Endless Node Edges) Infrastructure
**Purpose:** Integrate Cognitive Physics equations to enhance ENE performance, security, and semantic awareness using existing code as the foundation.

---

## Part I — Provable Components (Grounded in Existing Code)

Each component below maps to a specific file, function, or table in the repository. The "Action" column describes the concrete diff — what to add, change, or replace.

---

### 1. Cognitive Load Monitor (Eq 739)

**Equation:** `L_total = λ_I·l_I + λ_E·l_E − λ_G·l_G + λ_R·l_R + λ_M·l_M + λ_inv·l_inv + λ_traj·l_traj + λ_aci·l_aci` 

**Existing code to instrument:**

| File | Location | Metric |
|------|----------|--------|
| `4-Infrastructure/infra/ene_api.py:119-128` | `ENESecurityManager.encrypt_data()` | l_I: AES-256-GCM encrypt duration |
| `4-Infrastructure/infra/ene_api.py:130-140` | `ENESecurityManager.decrypt_data()` | l_I: AES-256-GCM decrypt duration |
| `4-Infrastructure/infra/ene_api.py:142-144` | `ENESecurityManager.check_access()` | l_aci: count of `False` returns per window |
| `4-Infrastructure/infra/swarm_ene_middleware.py:101-143` | `SwarmENEMiddleware.check_cache()` | l_R: count of `return None` (cache miss) per window |
| `4-Infrastructure/infra/swarm_ene_middleware.py:258-287` | `SwarmENEMiddleware.get_cache_statistics()` | l_M: `cache_count` + DB file size |
| `4-Infrastructure/infra/ene_wiki_layer.py:379-388` | revision number increment in `put_page()` | l_traj: revisions created per window |
| SQLite via `os.path.getsize(db_path)` | DB file size + `psutil.virtual_memory()` | l_M: storage footprint + RAM pressure |
| `4-Infrastructure/infra/ene_wiki_layer.py:360-370` | `admit_write()` rejections | l_E: rejected write attempts per window |
| `4-Infrastructure/infra/ene_api.py:316-318` | integrity check failure in `retrieve_sensitive_data()` | l_inv: count of integrity hash mismatches per window |
| N/A (negative contribution) | successful new category created or new link pattern discovered | l_G: estimated from `INSERT OR REPLACE INTO ene_wiki_categories` count + new `ene_wiki_links` target_slug discoveries per window |

The extraneous component (l_E) also tracks repeated identical queries by comparing `_compute_query_hash()` outputs over the window. The germane component (l_G) is a negative contribution: estimated from successful schema-learning events (new categories added, new link patterns discovered).

**Action:**

- Add an `ENELoadMonitor` class (new file `4-Infrastructure/infra/ene_load_monitor.py`) that:
  - Wraps calls to the above functions with timing/logging via decorators or context managers
  - Maintains a sliding window (60s default) of 8 load-component values
  - Exposes `compute_total_load(operation: str, context: dict) -> float`
  - The 8 λ coefficients start as equal weights (`1.0` for each, `-1.0` for germane) with defaults stored as a module-level dict `DEFAULT_LAMBDAS`
  - Calibration: after collecting (load, latency) pairs for 1 week, run `scipy.stats.linregress` or plain least-squares to adjust λ values. Until calibration data exists, use defaults.

**Testable outcome:** `L_total` correlates with measured p95 API latency on at least 100 samples (Pearson r > 0.7). Tracked via a CSV or SQLite log of `(timestamp, L_total, p95_latency_ms)` tuples written by a background collector.

**Test pattern to follow:** See `5-Applications/scripts/test_extremophile_constraints.py` — assert-based, self-contained functions, no framework dependency.

---

### 2. Gap-Adaptive Cache (Eq 745, 753)

**Equation:** `Gap = Gap_max · (1 - L_total / L_max)`

**Existing code to modify:**

| File | Location | What exists | What changes |
|------|----------|-------------|--------------|
| `4-Infrastructure/infra/swarm_ene_middleware.py:101-143` | `check_cache()` | Fixed TTL expiry check (`if now - created_at < ttl`) | Multiply TTL by gap factor from `ENELoadMonitor` |
| `4-Infrastructure/infra/swarm_ene_middleware.py:145-187` | `store_cache()` | Stores entries with `ttl` column as int seconds | TTL is now `int(base_ttl * gap)` |

**Database tables already in place:**
- `swarm_query_cache` — columns: `query_hash`, `subjects`, `keywords`, `formal_status`, `results`, `count`, `confidence`, `semantic_vector`, `created_at`, `ttl`, `hit_count`
- `swarm_api_audit` — columns: `id`, `operation`, `query_hash`, `parameters`, `result_cached`, `result_count`, `execution_time_ms`, `created_at`
- `swarm_semantic_index` — columns: `id`, `query_hash`, `semantic_vector`, `domain`, `created_at`

**Action:**

1. Add `self.gap: float = 1.0` and `self.load_monitor: ENELoadMonitor` to `SwarmENEMiddleware.__init__()`
2. Add `update_gap()` method: calls `self.load_monitor.compute_total_load()` and sets `self.gap = max(0.1, 1.0 - load / load_max)`
3. In `check_cache()` at line 127: replace `if now - created_at < ttl` with `if now - created_at < int(ttl * self.gap)`
4. In `store_cache()`: caller computes `gap_ttl = int(base_ttl * self.gap)` before passing `ttl`. Do NOT multiply inside `store_cache()` itself (that method just writes the value it receives)
5. In `get_cache_statistics()` (line 258): add `gap` to the return dict

**Testable outcome:** Write a test that stores a cache entry with `base_ttl=10` at gap=1.0, then sets gap=0.1, then sleeps 2 seconds before `check_cache()` — should return `None` (10 * 0.1 = 1s effective TTL < 2s elapsed). Conversely, store-before-sleep gap=1.0 should still hit. Test located in `swarm_ene_middleware.py` `__main__` block or a separate `test_ene_middleware.py`.

---

### 3. Semantic Compression for Wiki Storage (Eq 742, 746)

**Equation:** `Compressed(x) = Ψ_S [ Primes_64 × Context(L_total(x)) ] × Gap(L_total(x))`

**Existing code:**

| File | Location | What exists |
|------|----------|-------------|
| `4-Infrastructure/infra/ene_api.py:179-281` | `ENEAPIHook.store_sensitive_data()` | Already does: Metafoam compression → Delta GCL encoding → AES-256-GCM encryption. Has `use_metafoam` and `use_delta_gcl` flags (lines 181-182). Records `compression_stats` including `compression_ratio`, `field_phi`, `foam_score`, `rgflow_lawful`, `tags`, `gcl_encoding` |
| `4-Infrastructure/infra/ene_api.py:283-329` | `ENEAPIHook.retrieve_sensitive_data()` | Decrypts and verifies integrity. Returns `gcl_sequence` and `compression_stats` |
| `4-Infrastructure/infra/ene_api.py:190-225` | compression pipeline | Calls `MetafoamCompressionAdapter.compress_with_metafoam_metadata()` then `DeltaGCLEncoder.encode_to_delta_gcl()` |
| `4-Infrastructure/infra/ene_wiki_layer.py:150-182` | `make_archive_record()` | Creates `archive_id`, `content_hash`, `extracted_text` (truncated at 10k chars), `extraction_version` from `raw_content` dict (title, slug, revision, text, author, summary, links, categories) |
| `4-Infrastructure/infra/ene_wiki_layer.py:185-230` | `make_jsonl_event()` | Builds JSONL event with `concept_vector`, `genome` (from `genome_from_vector`), `bind` dict (lawful flag, cost as bytes-len << 16, invariant string), `provenance` with attestation_hash |

**Action:**

- In `store_sensitive_data()`, add a `fidelity: float = 0.5` parameter. High fidelity (near 1.0) = preserve more detail = less compression. Low fidelity (near 0.0) = aggressive compression.
- The fidelity value is derived from link depth: count rows in `ene_wiki_links` where `target_slug` matches the page's slug (i.e., inbound links). Pages with many inbound links are reference pages and need higher fidelity. Pages with zero inbound links are likely orphan/utility pages and can be compressed aggressively.
- Pass `fidelity` as a hint to the compression tier selection (if `MetafoamCompressionAdapter` supports it) or as a gating flag: `use_metafoam = fidelity > 0.3`.
- For wiki pages: `put_page()` at line 372 calls `make_archive_record()` then passes the result to `_upsert_package()`. Add a step between: query inbound link count, compute fidelity, store it in the archive record's metadata.

**Existing code that already works:** The `store_sensitive_data()` method already handles the full pipeline. The enhancement adds a fidelity parameter that gates or scales the compression level.

**Testable outcome:** Pages with 0 inbound links achieve >40% smaller stored representation compared to full-text storage. Pages with >5 inbound links decompress to byte-exact match (SHA-256 identical) with the original text. Both measured via the `compression_stats` dict already returned by `store_sensitive_data()` and the integrity hash check in `retrieve_sensitive_data()` (line 316-318).

---

### 4. Prime-Based Concept Vectors (Eq 748, 749)

**Equation:** `Vector(x) = M_P · p(x) · Gap` where `p(x)` is the 64-element structural prime activation vector.

**Existing code to replace:**

| File | Location | What exists | Problem |
|------|----------|-------------|---------|
| `4-Infrastructure/infra/ene_wiki_layer.py:113-131` | `concept_vector_for_wiki()` | 14D vector from keyword counting (counts of "topology", "hash", "receipt", "proof", "lean", etc.) | Heuristic, hardcoded keywords, no learning |
| `4-Infrastructure/infra/swarm_ene_middleware.py:77-93` | `_derive_semantic_vector()` | 14D from MD5 hashes of subjects | Nonsemantic — a hash is not a semantic representation |

**The 14-axis mapping (hardcoded in `concept_vector_for_wiki`):**

```
axes[2]  = topology/manifold/links count         (~ mathematical structure)
axes[5]  = hash/receipt/verify count              (~ integrity/cryptography)
axes[6]  = sqlite/schema/index count              (~ data architecture)
axes[7]  = unique word count / 500                (~ lexical diversity)
axes[11] = proof/lean/theorem count               (~ formal verification)
axes[12] = categories + archive + history count   (~ organizational metadata)
axes[13] = author/provenance/attest count         (~ attribution/trust)
```

(Axes 0, 1, 3, 4, 8, 9, 10 are always 0.0 — unused.)

**Action:**

1. Define 64 **structural primes** that map to computable features of a wiki page:
   - Content features: text length, unique word count, average sentence length, markup density
   - Link features: outbound link count, inbound (backlink) count, link-to-text ratio, category count
   - Revision features: revision count, edit velocity (revisions/day), time since last edit, author count
   - Semantic features: specific token presence (LaTeX math blocks, code blocks, tables), heading structure depth

2. Learn a 64×14 matrix `M_P` by:
   - Creating a labeled dataset of similar/dissimilar page pairs (e.g., pages that link to each other are "similar")
   - Using the existing link structure (`ene_wiki_links` table) as ground truth
   - Training via linear regression: for each linked pair (page A → page B), minimize `||M_P · p(A) - M_P · p(B)||²` where p(page) is the 64-prime activation vector

3. Replace the body of `concept_vector_for_wiki()` with:
   ```
   primes = compute_64_primes(title, text, links, categories)  # returns list[float] length 64
   return (M_P @ np.array(primes)).tolist()[:14]  # project to 14D
   ```

**Preserve backward compatibility:** The output format remains `list[float]` of length 14. All consumers (`make_jsonl_event`, the `packages` table, `swarm_semantic_index`) are unchanged.

**Testable outcome:** On a holdout set of 100 wiki page pairs (50 linked, 50 random), the cosine similarity of their concept vectors discriminates between linked and unlinked pairs with AUC > 0.80 (baseline with current keyword heuristic: TBD by running on existing wiki data).

---

### 5. Invariant Preservation for Security (Eq 750, 755)

**Equation:** `L_inv_active = Σ w_i · 𝟙[broken(i, x)] · severity(i) · 𝟙[active(p_i, Gap)]`

**Existing invariants to gate:**

| File | Location | Invariant | Severity | How to check |
|------|----------|-----------|----------|--------------|
| `4-Infrastructure/infra/ene_wiki_layer.py:85-97` | `write_receipt()` | Receipt chain integrity: each revision has valid SHA-256 receipt | CRITICAL | Compare stored receipt with recomputed `write_receipt(slug, revision, text, author, created_at)` |
| `4-Infrastructure/infra/ene_api.py:142-144` | `check_access()` | Access control: clearance ≥ classification | CRITICAL | Already enforced; add audit log of any DENY |
| `4-Infrastructure/infra/ene_api.py:146-148` | `compute_integrity_hash()` | Data integrity: stored hash matches computed hash | CRITICAL | Already checked in `retrieve_sensitive_data()` line 316-318 |
| `4-Infrastructure/infra/ene_api.py:96-116` | `derive_key_from_semantic()` | Key derivation: key derived from semantic vector has expected entropy | HIGH | Check that key has >128 bits of entropy (not all zeros/ones) |
| `4-Infrastructure/infra/ene_wiki_layer.py:360-370` | `admit_write()` | Content safety: no active scripts, text within size limits | HIGH | Already enforced; this is already an invariant gate |

**Action:**

1. Create `ENESecurityInvariants` class (new in `infra/`) that wraps the above checks
2. Each check returns `InvariantCheck(name, severity, passed, details)`
3. Critical invariants: always run, rejection = raise `ConstraintViolation` (from `extremophile_priors.py:29-32`)
4. High-severity: run when `gap > 0.2`
5. Integrate into `ENEAPIHook.store_sensitive_data()` and `retrieve_sensitive_data()` as pre/post conditions

**Testable outcome:** All existing tests pass (especially the access control test in `ene_api.py:348-349` which tests PUBLIC clearance rejection). Add invariant-specific tests following the pattern in `test_extremophile_constraints.py`.

---

### 6. HNSW Vector Search (Eq 780-782)

**Existing O(N) code to replace:**

| File | Location | What exists | Problem |
|------|----------|-------------|---------|
| `4-Infrastructure/infra/swarm_ene_middleware.py:224-240` | `semantic_search()` | Iterates over ALL rows in `swarm_semantic_index`, computes `_cosine_similarity()` for each | O(N) brute force — linear scan of entire index |
| `4-Infrastructure/infra/swarm_ene_middleware.py:242-249` | `_cosine_similarity()` | Pure Python dot product + norm | Correct but slow for large N |

**Existing data structure to index:**
- `swarm_semantic_index` table — each row has `query_hash`, `semantic_vector` (JSON list of 14 floats), `domain`, `created_at`

**Action:**

1. Implement `HNSWIndex` class with:
   - `add_vector(vector_id: str, vector: list[float])` — inserts into HNSW layers
   - `search(query: list[float], k: int = 10) -> list[tuple[str, float]]` — approximate nearest neighbors
   - Parameters: `M=16` (max connections), `ef_construction=200`, `ef_search=k`
   - Distance metric: cosine distance `1 - cos(v1, v2)` (reuse existing `_cosine_similarity`)

2. Add `self._hnsw_index: HNSWIndex` to `SwarmENEMiddleware.__init__()`
3. In `store_cache()`: after the `INSERT INTO swarm_semantic_index` block (lines 168-179), call `self._hnsw_index.add_vector(f"semantic_{query_hash}", semantic_vector)`
4. Rewrite `semantic_search()` to use `self._hnsw_index.search(query_vector, k=len(rows))` instead of linear scan
5. Fallback to brute force when HNSW index is empty (cold start)

**Testable outcome:** For 10,000 cached queries, `semantic_search(query_vector, threshold=0.7)` runs in <1ms (down from ~15ms brute force). Recall vs brute force at k=10: >95%.

---

### 7. Database Architecture — Concrete Cleanup

**Current issues to fix (no net-new equations, just engineering):**

| File | Issue | Fix |
|------|-------|-----|
| `4-Infrastructure/infra/ene_api.py:179-281` | `store_sensitive_data()` mixes Metafoam compression, GCL encoding, AES encryption, SQLite I/O, and schema migration (`ALTER TABLE` for missing columns) in one 100-line method | Extract: `_compress_payload()`, `_encrypt_payload()`, `_persist_sensitive()` |
| `4-Infrastructure/infra/ene_wiki_layer.py:372-453` | `put_page()` handles admission, revision computation, link extraction, archive creation, and 3 separate SQLite writes in one method | Extract data-access layer (`_insert_revision()`, `_update_page()`, `_upsert_package()`) — the `_upsert_package` method already exists at line 328 |
| `4-Infrastructure/infra/swarm_ene_middleware.py:41-67` | `_init_middleware_tables()` creates tables but has no version tracking | Add `schema_version` row to each table creation block |
| `4-Infrastructure/infra/ene_api.py:240-246` | Runtime `ALTER TABLE` for schema evolution | Move to a `_migrate_schema()` method called from `__init__()`, not from `store_sensitive_data()` |

**Note on SQLite concurrency:** `4-Infrastructure/infra/swarm_ene_middleware.py` already uses plain `sqlite3.connect()` (synchronous, one connection per call). This is correct for SQLite — do NOT add connection pooling or `aiosqlite`. SQLite serializes writes at the OS level; multiple concurrent connections add lock contention, not throughput.

---

### 8. AMVR Shell Partition (Eq 759-769)

**Equations mapped to PIST primitives:**

| Equation | PIST primitive (existing code) | Application to ENE |
|----------|-------------------------------|---------------------|
| Eq 759: `k = floor(sqrt(n))` | `pist_encode(n)` at `3-Mathematical-Models/pist_biological_polymorphic_shifter_v3_complete.py:159-166` returns `(shell, offset)` | Shell `k` is the complexity tier of a wiki page: `n` = page size in bytes. Small pages (k=0-2) = low complexity; large pages (k>10) = high complexity |
| Sorting within shell | `pist_decode(k, t)` at line 168-170 returns `n = k² + t` | Reversible: shell+offset ↔ page size. Not directly used for ranking, but ensures injectivity of (k, t) pairs |
| Eq 761: `J = m + p + s` | `pist_mass(k, t)` at line 172-174 = `t · (2k+1-t)` | Page "engagement mass": zero at shell edges (trivial/saturated pages), max at middle (substantive but not bloated). Use as a scoring boost for pages with mid-shell offset |
| Eq 769: RG flow preserves shells | `pist_mirror(k, t)` at line 180-182 = `(k, 2k+1-t)` | Eviction symmetry: `mass(k, t) = mass(mirror(k, t))`. Pages from each shell should be evicted in proportion to their shell width `2k+1` |

**Action:**

1. Add `shell_partition(page_size_bytes: int) -> tuple[int, int]` that wraps `pist_encode(page_size_bytes)` — returns `(shell, offset)`
2. In `ENEWikiLayer.put_page()` at line 372: after computing revision, call `shell, offset = shell_partition(len(text.encode('utf-8')))` and store as part of the archive record
3. In `SwarmENEMiddleware` eviction logic: when evicting cache entries, group by shell partition and evict proportionally (rather than FIFO-only, which the current `DELETE ... ORDER BY created_at ASC LIMIT ?` pattern does)

**Existing code to import from:** `sys.path.insert(0, ...)` pattern already used in `ene_api.py:35` to import from `scripts/` — same approach for PIST imports.

---

### 9. Extremophile Constraint Layer (Eq 829-840)

**Existing code — NO new implementation needed:**

| File | What exists |
|------|-------------|
| `5-Applications/scripts/extremophile_priors.py` (1089 lines) | Full implementation of all 12 extremophile priors with `PriorResult(admissible, violated_constraint, details)` |
| `5-Applications/scripts/extremophile_priors.py:550-699` | `DeepExtremophilePrior.unified_check(solution_params)` — runs all 12 tiers |
| `5-Applications/scripts/extremophile_priors.py:704-764` | `NavierStokesConstraints.check_solution()` — applies priors to PDE solutions |
| `5-Applications/scripts/extremophile_priors.py:767-1067` | `MissionCriticalReliability` — depth scoring and AngrySphinx adversarial defense |
| `5-Applications/scripts/test_extremophile_constraints.py` (175 lines) | 5 test functions validating constraint behavior |
| `5-Applications/scripts/extremophile_priors.py:29-32` | `ConstraintViolation` exception — already usable |

**Action:**

Wire the existing `DeepExtremophilePrior` into the ENE operation pipeline:

1. In `ENEAPIHook.__init__()` (line 153): add `self.extremophile = DeepExtremophilePrior()`
2. In `store_sensitive_data()` before encryption (line 231): call `self.extremophile.unified_check(params)` where params include:
   - `temperature`: hardware thermal reading (from `psutil.sensors_temperatures()` or env var)
   - `power`: estimated energy cost of the compression operation
   - `time`: expected operation duration
   - `bits`: payload size in bits
3. Reject operations that fail any constraint with `ConstraintViolation`
4. In `put_page()` (line 372): gate wiki writes through extremophile growth constraints (`TuringPatternPrior` — reject if wiki growth rate exceeds nutrient-like resource bounds)

**Test:**
```bash
python 5-Applications/scripts/test_extremophile_constraints.py
```
All 5 existing tests must pass. Add an ENE-specific test that verifies `store_sensitive_data()` rejects a payload requiring infinite energy.

---

### 10. Multi-Language Wiki Compression (Eq 757, 758)

**Existing code:**

| File | Location | What exists |
|------|----------|-------------|
| `4-Infrastructure/infra/ene_wiki_layer.py` | — | No language detection or language-aware compression. `concept_vector_for_wiki()` works on lowered text regardless of language |
| `4-Infrastructure/infra/ene_api.py:179-281` | `store_sensitive_data()` | Compression pipeline is language-agnostic |

**Action:**

1. Add `_detect_language(text: str) -> str` to `ene_wiki_layer.py`:
   - Use a simple `collections.Counter` of character n-grams and a frequency table for en/ru/zh/de/ja
   - Or import an existing library if available
2. In `store_sensitive_data()`: add `language` parameter. For morphologically complex languages (ru, de): use higher compression threshold. For CJK languages (zh, ja): use lower threshold (token boundary ambiguity limits safe compression)
3. In `make_archive_record()` at line 150: add `language` field

**Testable outcome:** Decompression error for Russian text is within 10% of English text error at the same compression ratio.

---

## Part II — Research Hypotheses

These sections from the original plan are retained as hypotheses for future investigation, NOT as implementation phases.

### What makes something "mushy" and why

The original plan's sections 14-19 (Shockwave/Phonon/Photon, GCCL, Mass Number, Archive Metaphors) share a pattern:

- They name-drop physics equations but provide no concrete mapping to system metrics
- The "implementations" are self-referential: they compare the system to itself with no external ground truth
- Several reduce to trivial operations wrapped in novel terminology:
  - "Rotational phase encoding" ≈ 4-bit integer with angular interpretation
  - "Temporal to genetic transduction" ≈ `hashlib.sha256(data).digest()`
  - "NaNMass detection" ≈ `numpy.isinf(value) or numpy.isnan(value)`
  - "Predictive coding" ≈ `prediction += learning_rate * error` (an EMA)
  - "Spike sync coarse-graining" ≈ `timestamp // bin_width`

These are not inherently wrong ideas, but they are not currently falsifiable. Each hypothesis below states what evidence would move it from the "mushy" column to the "provable" column.

### Hypothesis A: Cache Propagation via Lattice Metaphors
### Hypothesis B: Behavioral Routing via Fingerprint Matching
### Hypothesis C: Admissibility Gates for Operation Budgeting
### Hypothesis D: Genotype-Phenotype Split for Wiki Pages
### Hypothesis E: Time-Aware Semantic Encoding

*(Detailed hypothesis statements retained from v1 of this document.)*

---

## Part III — Implementation Plan

Phases are sequential but partially parallelizable within phase. Each phase modifies specific files.

### Phase 1: Instrumentation (Week 1-2)

**Files touched:**
- NEW `4-Infrastructure/infra/ene_load_monitor.py` — `ENELoadMonitor` class
- MODIFY `4-Infrastructure/infra/ene_api.py` — add timing hooks to `ENESecurityManager` methods
- MODIFY `4-Infrastructure/infra/swarm_ene_middleware.py` — add `gap` field to `SwarmENEMiddleware`

**Deliverable:**
```python
monitor = ENELoadMonitor()
load = monitor.compute_total_load("test_operation", {"size": 1024})
assert load >= 0.0, "load should be non-negative"
# load may exceed 100.0; load_max is a configurable threshold for gap calculation, not a hard bound
```

### Phase 2: Adaptive Cache (Week 3-4)

**Files touched:**
- MODIFY `4-Infrastructure/infra/swarm_ene_middleware.py` — gap-adaptive TTL in `check_cache()` and `store_cache()`

**Deliverable:** Cache hit rate under variable load improves >10% vs fixed TTL baseline.

### Phase 3: Semantic Compression (Week 5-6)

**Files touched:**
- MODIFY `4-Infrastructure/infra/ene_api.py` — fidelity-gated compression in `store_sensitive_data()`
- MODIFY `4-Infrastructure/infra/ene_wiki_layer.py` — pass link density as fidelity hint

**Deliverable:** >20% storage reduction for orphan pages, <5% decompression error for heavily-linked pages.

### Phase 4: Prime Concept Vectors (Week 7-8)

**Files touched:**
- NEW `4-Infrastructure/infra/ene_prime_vectors.py` — `PrimeConceptVector` class with 64×14 matrix
- MODIFY `4-Infrastructure/infra/ene_wiki_layer.py` — replace `concept_vector_for_wiki()` body

**Deliverable:** Semantic search with learned vectors beats keyword heuristic on labeled page-pair test set.

### Phase 5: Security Invariants (Week 9-10)

**Files touched:**
- NEW `4-Infrastructure/infra/ene_security_invariants.py` — `ENESecurityInvariants` class
- MODIFY `4-Infrastructure/infra/ene_api.py` — integrate invariant checks

**Deliverable:** Zero critical invariant violations. All existing `ene_api.py` tests pass.

### Phase 6: Vector Search & Shell Organization (Week 11-12)

**Files touched:**
- NEW `4-Infrastructure/infra/ene_hnsw_index.py` — `HNSWIndex` class
- MODIFY `4-Infrastructure/infra/swarm_ene_middleware.py` — replace `semantic_search()` linear scan
- NEW `4-Infrastructure/infra/ene_shell_partition.py` — wraps PIST functions for wiki page bucketing
- MODIFY `4-Infrastructure/infra/ene_wiki_layer.py` — tag pages with shell partition in archive records

**Deliverable:** `semantic_search()` on 10k+ vectors runs in <1ms. Cache eviction preserves shell proportions.

### Phase 7: Extremophile Constraints & Multi-Language (Week 13-14)

**Files touched:**
- MODIFY `4-Infrastructure/infra/ene_api.py` — wire `DeepExtremophilePrior` into operation gates
- MODIFY `4-Infrastructure/infra/ene_wiki_layer.py` — add language detection + language-aware compression

**Deliverable:** Operations violating extremophile priors are rejected with traceable reason codes. Cross-language compression within 10% variance.

---

## Part IV — Guardrails

### Things to NOT implement as originally described

1. **`asyncio.LRUCache`** — Does not exist in Python. The original plan used it in 5+ places. Replace with `collections.OrderedDict` with manual eviction, or `functools.lru_cache` for function-level caching.

2. **Do NOT add SQLite connection pooling.** The existing code uses plain `sqlite3.connect()` per operation, which is correct. SQLite serializes writes at the OS level. Multiple concurrent `aiosqlite` connections would add lock contention, not throughput.

3. **`physics_equations.db` does not exist** — The original plan references it as a source for equations 739-850, but no such file exists in the repository. The equations referenced in this plan are self-contained.

4. **Do NOT create 17 independent thread/process pools.** The original plan assigns `ThreadPoolExecutor(8)` and `ProcessPoolExecutor(4)` to each of 15+ classes, creating hundreds of idle threads. Use a single shared executor with semaphore-gated submission.

5. **Do NOT wrap sub-microsecond operations in `asyncio.to_thread()`.** Operations like `a * b`, `a - b`, or `hashlib.sha256(data).hexdigest()` complete in <1μs — thread dispatch overhead (~50μs) dominates the operation cost. Reserve thread dispatch for I/O or operations taking >1ms.

6. **The `QueryLanguage.CYpher` typo** (lowercase 'p' vs enum value `CYPHER`) would make graph queries silently fail. If implementing graph query support, fix this at implementation time.

---

## File Map

```
4-Infrastructure/infra/
├── ene_api.py                          [MODIFY Phases 1,3,5,7]  AES-GCM + compression
├── ene_wiki_layer.py                   [MODIFY Phases 3,4,6,7]  Wiki revisions + concept vectors
├── swarm_ene_middleware.py             [MODIFY Phases 1,2,6]    Cache + semantic search
├── ene_load_monitor.py                 [NEW Phase 1]            Cognitive load computation
├── ene_prime_vectors.py                [NEW Phase 4]            64×14 matrix learning
├── ene_hnsw_index.py                   [NEW Phase 6]            HNSW ANN search
├── ene_shell_partition.py              [NEW Phase 6]            PIST-based shell bucketing
├── ene_security_invariants.py          [NEW Phase 5]            Invariant checking + gating

5-Applications/scripts/
├── extremophile_priors.py              [USE AS-IS Phases 5,7]   12-tier constraint checking
├── test_extremophile_constraints.py    [REFERENCE for test patterns]

3-Mathematical-Models/
├── pist_biological_polymorphic_shifter_v3_complete.py  [IMPORT FROM Phase 6]  PIST encoding primitives
```
