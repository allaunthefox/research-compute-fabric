# AGENTS.md Compliance Audit

**Date:** April 26, 2026  
**Auditor:** Cascade  
**Scope:** All Python scripts in `/scripts/`

---

## Violation Summary

According to AGENTS.md Section 6.1 (Python Shims):
- **Allowed:** JSON serialization, subprocess spawn, history deque, result wrapping
- **Forbidden:** Cost computation, invariant checks, conservation laws, branching decisions

According to AGENTS.md Section 8 (Deletion Criteria):
- Demo or test script with no invariant
- Duplicates a Lean module
- Cannot be typed without `unsafe` or `sorry`
- Integrates with external SaaS
- Resists `bind` collapse

---

## Scripts Requiring Deletion

The following scripts contain logic, cost computation, invariant checks, or branching decisions that violate AGENTS.md shim boundaries:

### Recently Created Scripts (Violations)

1. **`scripts/crypto_rfc_compliance_prober.py`**
   - **Violation:** Contains cost computation, invariant checks, branching decisions
   - **Reason:** Implements RFC compliance scoring logic in Python
   - **Action:** DELETE or port logic to Lean

2. **`scripts/pull_crypto_rfc_docs.py`**
   - **Violation:** Contains branching decisions, logic
   - **Reason:** Implements RFC extraction logic in Python
   - **Action:** DELETE or port logic to Lean

3. **`scripts/internet_waveform_atlas.py`**
   - **Violation:** Contains logic, branching decisions
   - **Reason:** Implements waveform probing logic in Python
   - **Action:** DELETE or port logic to Lean

4. **`scripts/archive_org_adapter.py`**
   - **Violation:** Contains logic, branching decisions
   - **Reason:** Implements adapter logic in Python
   - **Action:** DELETE or port logic to Lean

5. **`scripts/openworm_adapter.py`**
   - **Violation:** Contains logic, branching decisions
   - **Reason:** Implements adapter logic in Python
   - **Action:** DELETE or port logic to Lean

6. **`scripts/equation_extraction_pipeline.py`**
   - **Violation:** Contains logic, branching decisions
   - **Reason:** Implements equation extraction logic in Python
   - **Action:** DELETE or port logic to Lean

7. **`scripts/parallel_equation_extraction.py`**
   - **Violation:** Contains logic, branching decisions
   - **Reason:** Implements parallel extraction logic in Python
   - **Action:** DELETE or port logic to Lean

8. **`scripts/metaprobe_cross_domain_papers.py`**
   - **Violation:** Contains logic, branching decisions
   - **Reason:** Implements metaprobe logic in Python
   - **Action:** DELETE or port logic to Lean

9. **`scripts/genetic_codon_encoder.py`**
   - **Violation:** Contains cost computation, logic
   - **Reason:** Implements genetic encoding logic in Python
   - **Action:** DELETE or port logic to Lean

10. **`scripts/genetic_surface_compression.py`**
    - **Violation:** Contains cost computation, logic
    - **Reason:** Implements compression logic in Python
    - **Action:** DELETE or port logic to Lean

11. **`scripts/delta_gcl_encoder.py`**
    - **Violation:** Contains cost computation, logic
    - **Reason:** Implements Delta GCL encoding logic in Python
    - **Action:** DELETE or port logic to Lean

12. **`scripts/lean_delta_gcl_encoder.py`**
    - **Violation:** Contains cost computation, logic
    - **Reason:** Implements Delta GCL encoding logic in Python
    - **Action:** DELETE or port logic to Lean

13. **`scripts/sweep_lean_delta_gcl.py`**
    - **Violation:** Contains logic, branching decisions
    - **Reason:** Implements sweep logic in Python
    - **Action:** DELETE or port logic to Lean

14. **`scripts/batch_metafoam_papers.py`**
    - **Violation:** Contains logic, branching decisions
    - **Reason:** Implements batch processing logic in Python
    - **Action:** DELETE or port logic to Lean

15. **`scripts/waveprobe_metafoam_reader.py`**
    - **Violation:** Contains cost computation, logic
    - **Reason:** Implements metafoam reading logic in Python
    - **Action:** DELETE or port logic to Lean

16. **`scripts/compression_metafoam_adapter.py`**
    - **Violation:** Contains cost computation, logic
    - **Reason:** Implements compression adapter logic in Python
    - **Action:** DELETE or port logic to Lean

### Additional Scripts Requiring Audit

The following scripts also require audit for compliance:

- `scripts/financial_crash_audit.py`
- `scripts/cancer_godzilla_audit.py`
- `scripts/rgflow_network_filter.py`
- `scripts/genome_purification_stripper.py`
- `scripts/global_manifold_audit.py`
- `scripts/rgflow_enwik9_sweep.py`
- `scripts/hutter_full_purification.py`
- `scripts/rgflow_topology_filter.py`
- `scripts/hutter_rgflow_filter.py`
- `scripts/hep_event_benchmark.py`
- `scripts/connectome_lut_shim.py`
- `scripts/invention_plot.py`
- `scripts/rgflow_lean_filter.py`
- `scripts/rgflow_blind_detector.py`
- `scripts/killer_criterion_gen.py`
- `scripts/find_suspect_regions.py`
- `scripts/audit_linux_kernel.py`
- `scripts/rgflow_swarm_filter.py`
- `scripts/analyze_rgflow_noise_files.py`
- `scripts/kimi_waveprobe_rgflow.py`
- `scripts/rgflow_codebase_filter.py`
- `scripts/commoncrawl_waveprobe_ingestion.py`
- `scripts/merge_datasets.py`
- `scripts/lean_omnibus_total_recall.py`
- `scripts/lean_addons_to_parquet.py`
- `scripts/mathlib_to_parquet.py`
- `scripts/lean_to_parquet.py`
- `scripts/mathlib_ingestion_pipeline.py`
- `scripts/swarm_gpu_optimization_80_percent.py`
- `scripts/dump_notion_ene_jsonl.py`
- `scripts/generate_project_graph.py`
- `scripts/distributed_swarm_colonization.py`
- `scripts/virtual_gpu_workload_testbench.py`
- `scripts/virtual_gpu_topology_loader.py`
- `scripts/virtual_gpu_testbench.py`

---

## Files That Are Compliant

The following files are documentation and do not violate AGENTS.md:

- `docs/papers/CRYPTO_LAYER2_TOPOLOGY.md` - Documentation
- `docs/papers/NEURON_KERNEL_MAXIMAL_COMPRESSION.md` - Documentation
- `docs/papers/NEURON_AS_KERNEL_ENCODING.md` - Documentation
- `docs/papers/INTERNET_WAVEFORM_ATLAS.md` - Documentation
- `docs/papers/INTERNET_WAVEFORM_ATLAS_PAPER.md` - Documentation
- `docs/papers/METAPROBE_DUAL_FUNCTIONALITY.md` - Documentation

---

## Recommended Action

**DELETE** the 16 recently created scripts that violate AGENTS.md shim boundaries. These scripts contain domain logic that should be implemented in Lean, not Python.

**Total files to delete:** 16

---

**Status:** Awaiting user approval for deletion
