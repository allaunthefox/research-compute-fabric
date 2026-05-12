# Stack Solidification Staging Manifest

**Date:** 2026-05-09

## Purpose

This manifest keeps the solidification slice scoped. The working tree is broad
and dirty, so do not stage a directory wholesale. The Google Drive receipt is a
curated safety snapshot; this staging manifest remains the full source list for
the slice.

## Stage Together

These files form the current stack-status and tri-cycle audit slice:

- `.gitignore`
- `AGENTS.md`
- `0-Core-Formalism/lean/Semantics/AGENTS.md`
- `4-Infrastructure/AGENTS.md`
- `4-Infrastructure/shim/stack_solidification_audit.py`
- `4-Infrastructure/shim/stack_fail_closure_register.py`
- `4-Infrastructure/shim/beaver_mask_freshness_negative_controls.py`
- `4-Infrastructure/shim/whitespace_zero_grammar_probe.py`
- `4-Infrastructure/shim/external_sem_entity_diff_probe.py`
- `4-Infrastructure/shim/network_topology_hold_manifests.py`
- `4-Infrastructure/shim/rrc_hold_closure_checklist.py`
- `4-Infrastructure/shim/tang9k_rrc_q16_virtual_serial_probe.py`
- `4-Infrastructure/shim/tang9k_uart_transport_router.py`
- `4-Infrastructure/shim/tang9k_uart_beacon_probe.py`
- `4-Infrastructure/shim/smn_tool_awareness_registry.py`
- `4-Infrastructure/shim/stellar_gas_population_grouping_study.py`
- `4-Infrastructure/shim/desi_epoviz_population_cell_join.py`
- `4-Infrastructure/shim/stellar_gas_eigenvector_mass_probe.py`
- `4-Infrastructure/shim/desi_epoviz_row_eigenmass_probe.py`
- `4-Infrastructure/shim/stellar_gas_multiscale_eigenmass_alignment.py`
- `4-Infrastructure/shim/hutter_eigenmass_transfer_plan.py`
- `4-Infrastructure/shim/stellar_gas_abelian_sandpile_probe.py`
- `4-Infrastructure/shim/stellar_gas_sandpile_fine_zoom.py`
- `4-Infrastructure/shim/stellar_gas_full_cell_eigenmass_stability.py`
- `4-Infrastructure/shim/stellar_gas_sandpile_graph_replay.py`
- `4-Infrastructure/shim/hutter_transfer_readiness_fixture.py`
- `4-Infrastructure/shim/custom_equation_awareness_manifest.py`
- `5-Applications/compression-core/src/oisc.rs`
- `shared-data/data/stack_solidification/stack_solidification_receipt.json`
- `shared-data/data/stack_solidification/stack_fail_closure_register.json`
- `shared-data/data/stack_solidification/beaver_mask_freshness_negative_controls.json`
- `shared-data/data/stack_solidification/whitespace_zero_grammar_probe.json`
- `shared-data/data/stack_solidification/tang9k_rrc_q16_virtual_serial_probe.json`
- `shared-data/data/stack_solidification/tang9k_uart_transport_routes.json`
- `shared-data/data/stack_solidification/external_sem_entity_diff_probe_receipt.json`
- `shared-data/data/stack_solidification/rrc_hold_closure_checklist.json`
- `shared-data/data/stack_solidification/network_topology_coefficient_calibration_manifest.json`
- `shared-data/data/stack_solidification/network_topology_prediction_hold_registry.json`
- `shared-data/data/stack_solidification/stack_solidification_kanban_cards.json`
- `shared-data/data/stack_solidification/stack_solidification_kanban_receipt.json`
- `shared-data/data/stack_solidification/shockwave_eigenvalue_comparison_receipt.json`
- `shared-data/data/stack_solidification/matched_reference_genomics_logogram_receipt.json`
- `shared-data/data/stack_solidification/underwater_shock_public_benchmark_receipt.json`
- `shared-data/data/stack_solidification/hopfion_topological_soliton_receipt.json`
- `shared-data/data/stack_solidification/topological_soliton_equation_pack_receipt.json`
- `shared-data/data/stack_solidification/palindrome_hex_symmetry_marker_receipt.json`
- `shared-data/data/stack_solidification/predictive_harmony_social_synchrony_receipt.json`
- `shared-data/data/stack_solidification/desi_noirlab2610_calibration_note_receipt.json`
- `shared-data/data/stack_solidification/desi_stellar_gas_distribution_prior.json`
- `shared-data/data/stack_solidification/desi_stellar_gas_distribution_prior_receipt.json`
- `shared-data/data/stack_solidification/smn_tool_awareness_registry.json`
- `shared-data/data/stack_solidification/smn_tool_awareness_receipt.json`
- `shared-data/data/stack_solidification/hutter_eigenmass_transfer_plan.json`
- `shared-data/data/stack_solidification/hutter_eigenmass_transfer_plan_receipt.json`
- `shared-data/data/stack_solidification/hutter_transfer_readiness_fixture_manifest.json`
- `shared-data/data/stack_solidification/eigenmass_stack_gdrive_sync_receipt_2026-05-09.json`
- `6-Documentation/docs/specs/SMN_SEMANTIC_MASS_NUMBERS.md`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/Semantic Mass Numbers.tid`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/Mass Number Theory.tid`
- `0-Core-Formalism/otom/docs/wiki/NotationNomenclatureRegistry.md`
- `shared-data/data/stellar_gas_observation/sdss_manga_dr17_emission_line_channels.json`
- `shared-data/data/stellar_gas_observation/smn_semantic_mass_number_boundary_receipt_20260509_215744.json`
- `shared-data/data/stellar_gas_observation/stellar_gas_population_grouping_study.json`
- `shared-data/data/stellar_gas_observation/stellar_gas_population_grouping_study_receipt_20260509_221815.json`
- `shared-data/data/stellar_gas_observation/desi_epoviz_manga_population_cell_join.json`
- `shared-data/data/stellar_gas_observation/desi_epoviz_manga_population_cell_join_receipt.json`
- `shared-data/data/stellar_gas_observation/stellar_gas_eigenvector_mass_probe.json`
- `shared-data/data/stellar_gas_observation/stellar_gas_eigenvector_mass_probe_receipt.json`
- `shared-data/data/stellar_gas_observation/desi_epoviz_row_eigenmass_probe.json`
- `shared-data/data/stellar_gas_observation/desi_epoviz_row_eigenmass_probe_receipt.json`
- `shared-data/data/stellar_gas_observation/stellar_gas_multiscale_eigenmass_alignment.json`
- `shared-data/data/stellar_gas_observation/stellar_gas_multiscale_eigenmass_alignment_receipt.json`
- `shared-data/data/stellar_gas_observation/stellar_gas_abelian_sandpile_probe.json`
- `shared-data/data/stellar_gas_observation/stellar_gas_abelian_sandpile_probe_receipt.json`
- `shared-data/data/stellar_gas_observation/stellar_gas_sandpile_fine_zoom.json`
- `shared-data/data/stellar_gas_observation/stellar_gas_sandpile_fine_zoom_receipt.json`
- `shared-data/data/stellar_gas_observation/stellar_gas_full_cell_eigenmass_stability.json`
- `shared-data/data/stellar_gas_observation/stellar_gas_full_cell_eigenmass_stability_receipt.json`
- `shared-data/data/stellar_gas_observation/stellar_gas_sandpile_graph_replay.json`
- `shared-data/data/stellar_gas_observation/stellar_gas_sandpile_graph_replay_receipt.json`
- `6-Documentation/docs/stack_solidification_status_2026-05-09.md`
- `6-Documentation/docs/stack_solidification_staging_manifest_2026-05-09.md`
- `6-Documentation/docs/stack_solidification_kanban_2026-05-09.md`
- `6-Documentation/docs/shockwave_eigenvalue_comparison_2026-05-09.md`
- `6-Documentation/docs/matched_reference_genomics_logogram_2026-05-09.md`
- `6-Documentation/docs/underwater_shock_public_benchmark_2026-05-09.md`
- `6-Documentation/docs/hopfion_topological_soliton_lane_2026-05-09.md`
- `6-Documentation/docs/topological_soliton_equation_pack_2026-05-09.md`
- `6-Documentation/docs/palindrome_hex_symmetry_markers_2026-05-09.md`
- `6-Documentation/docs/predictive_harmony_social_synchrony_2026-05-09.md`
- `6-Documentation/docs/desi_noirlab2610_calibration_note_2026-05-09.md`
- `6-Documentation/docs/desi_stellar_gas_distribution_prior_2026-05-09.md`
- `6-Documentation/docs/stellar_gas_population_grouping_study_2026-05-09.md`
- `6-Documentation/docs/desi_epoviz_manga_population_cell_join_2026-05-09.md`
- `6-Documentation/docs/stellar_gas_eigenvector_mass_probe_2026-05-09.md`
- `6-Documentation/docs/desi_epoviz_row_eigenmass_probe_2026-05-09.md`
- `6-Documentation/docs/stellar_gas_multiscale_eigenmass_alignment_2026-05-09.md`
- `6-Documentation/docs/hutter_eigenmass_transfer_plan_2026-05-09.md`
- `6-Documentation/docs/stellar_gas_abelian_sandpile_probe_2026-05-09.md`
- `6-Documentation/docs/stellar_gas_sandpile_fine_zoom_2026-05-09.md`
- `6-Documentation/docs/stellar_gas_full_cell_eigenmass_stability_2026-05-09.md`
- `6-Documentation/docs/stellar_gas_sandpile_graph_replay_2026-05-09.md`
- `6-Documentation/docs/hutter_transfer_readiness_fixture_manifest_2026-05-09.md`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/Palindrome Hex Symmetry Markers.tid`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/Predictive Harmony Social Synchrony.tid`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/DESI NOIRLab2610 Calibration Note.tid`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/DESI Stellar Gas Distribution Prior.tid`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/Stellar Gas Population Grouping Study.tid`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/DESI Epoviz MaNGA Population Cell Join.tid`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/Stellar Gas Eigenvector Mass Probe.tid`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/DESI Epoviz Row Eigenmass Probe.tid`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/Stellar Gas Multiscale Eigenmass Alignment.tid`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/Hutter Eigenmass Transfer Plan.tid`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/Stellar Gas Abelian Sandpile Probe.tid`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/Stellar Gas Sandpile Fine Zoom.tid`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/Stellar Gas Full Cell Eigenmass Stability.tid`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/Stellar Gas Sandpile Graph Replay.tid`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/Hutter Transfer Readiness Fixture.tid`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/Hutter Prize Next Roadmap.tid`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/Phonon Music Logogram Layer.tid`
- `6-Documentation/tiddlywiki-local/wiki/tiddlers/Remote Compression Test Ladder.tid`
- `6-Documentation/wiki/Glossary.md`
- `6-Documentation/wiki/Concept-Archive.md`
- `SIGNAL_THEORY_COMPENDIUM.md`
- `6-Documentation/docs/roadmaps/ROADMAP.md`
- `6-Documentation/docs/stack_fail_closure_register_2026-05-09.md`
- `6-Documentation/docs/beaver_mask_freshness_negative_controls_2026-05-09.md`
- `6-Documentation/docs/whitespace_zero_grammar_2026-05-09.md`
- `6-Documentation/docs/tang9k_rrc_q16_virtual_serial_probe_2026-05-09.md`
- `6-Documentation/docs/tang9k_uart_transport_routes_2026-05-09.md`
- `6-Documentation/docs/external_sem_entity_diff_probe_2026-05-09.md`
- `6-Documentation/docs/rrc_hold_closure_checklist_2026-05-09.md`
- `6-Documentation/docs/network_topology_hold_manifests_2026-05-09.md`
- `6-Documentation/docs/specs/OMINDIRECTION_LOGOGRAM_DESIGN_AND_COMPILER.md`
- `6-Documentation/docs/specs/LAW_GATED_RECONSTRUCTION_CORE_SHIFT.md`
- `4-Infrastructure/shim/rrc_tri_cycle_audit.py`
- `shared-data/data/rrc_tri_cycle_audit/rrc_tri_cycle_audit_receipt.json`
- `6-Documentation/docs/rrc_tri_cycle_audit_2026-05-09.md`
- `4-Infrastructure/hardware/tangnano9k_uart_beacon.v`
- `4-Infrastructure/hardware/build_uart_beacon.sh`
- `4-Infrastructure/hardware/tangnano9k_uart_swapped.cst`
- `4-Infrastructure/shim/tang9k_uart_beacon_probe_receipt.json`
- `4-Infrastructure/shim/tang9k_uart_beacon_swapped_probe_receipt.json`
- `4-Infrastructure/shim/tang9k_uart_loopback_after_jtag_clear_probe_receipt.json`
- `6-Documentation/docs/fpga_rrc_q16_accel_setup_2026-05-09.md`
- `6-Documentation/docs/fpga_uart_route_analysis_2026-05-09.md`
- `6-Documentation/docs/fpga_direct_probe_report_2026-05-09.md`
- `0-Core-Formalism/lean/Semantics/Semantics.lean`
- `0-Core-Formalism/lean/Semantics/Semantics/BeaverMaskFreshness.lean`
- `0-Core-Formalism/lean/Semantics/Semantics/WhitespaceFreeGrammar.lean`

## Optional Same-Slice Hardware Artifacts

These are generated bitstream/build products. Stage only if this repository wants
to preserve generated FPGA artifacts:

- `4-Infrastructure/hardware/tangnano9k_uart_beacon.fs`
- `4-Infrastructure/hardware/tangnano9k_uart_beacon.json`
- `4-Infrastructure/hardware/tangnano9k_uart_beacon_pnr.json`
- `4-Infrastructure/hardware/tangnano9k_rrc_q16_accel.fs`
- `4-Infrastructure/hardware/tangnano9k_rrc_q16_accel.json`
- `4-Infrastructure/hardware/tangnano9k_rrc_q16_accel_pnr.json`

## Do Not Sweep

Avoid broad commands such as:

```bash
git add 0-Core-Formalism 4-Infrastructure 6-Documentation shared-data
```

The current tree contains many unrelated generated probes, modified Lean
experiments, and documentation surfaces. Stage by explicit file path only.

## Current Evidence

- Full Lean/Semantics build: PASS
- JSON integrity gate: PASS
- Python shim compile gate: PASS
- Support receipt refresh gate: PASS
- Rainbow Raccoon compiler: PASS_WITH_HOLDS, 1 candidate and 6 HOLD
- Tri-cycle audit: PASS_WITH_BLOCKED_HARDWARE
- FPGA software witness: PASS
- FPGA hardware witness: FAIL
- UART beacon: no bytes observed on `/dev/ttyUSB0` or `/dev/ttyUSB1`
- Q16 virtual serial probe: PASS, proving host framing/parser and opcode semantics over a PTY-backed serial device
- UART transport routes: active non-hardware route is `virtual://q16-pty`; physical routes remain blocked or pending
- Forced JTAG clear: JTAG detect/reset and SRAM reload work; UART/fabric receipts still fail, with loopback-after-clear showing FTDI/MPSSE-style `faXX` bytes on `/dev/ttyUSB0`
- FPGA UART route analysis: onboard BL702 bridge route remains blocked; next live test uses external USB-UART on fabric pins 17/18
- Optional external `sem` entity-diff aid: ready from isolated `/tmp` binary; `/usr/bin/sem` is GNU Parallel
- Stack fail closure register: PASS_TICKETS_DECLARED, 7 tickets
- RRC HOLD closure checklist: 0 open documentation closures across 6 HOLD objects; compiler promotion rerun still pending
- Network topology HOLD manifests: 9 coefficient rows and 15 prediction rows separated from validation claims
- Beaver mask freshness controls: Lean-backed finite negative controls added; security HOLD remains partial
- Whitespace-zero grammar: canonical spaces derive from symbol count/order with zero stored whitespace codes; non-canonical spacing remains HOLD/residual
- Palindrome hex markers: deterministic mirror/frame markers added for zero-whitespace decompressor and remote/local replay packets; marker use is ADMIT only with namespace, payload hash, receipt hash, and replay agreement
- Predictive harmony social synchrony: structured chord progression plus live mutual-attention gate added as a neuroacoustic route prior; therapy and social-control claims remain HOLD/QUARANTINE
- DESI epoviz to MaNGA population-cell join: 669,377 DESI EDR epoviz rows joined to 25 MaNGA sky/redshift cells as a coarse population prior; object-level crossmatch and direct gas-density inference remain HOLD
- Stellar gas eigenvector mass: dominant SMN/evidence-load eigenvalue 4.872368819 over 25 DESI/MaNGA cells, explaining 58.4684258% of joined-cell variance; physical mass, gas density, and cosmology interpretations remain HOLD
- DESI row eigenmass: 669,377 DESI epoviz rows streamed into a row-level SMN/evidence-load eigenprobe; dominant eigenvalue 3.276998814 explains 32.7699881% of row-level geometry/tracer variance
- Multiscale eigenmass alignment: row-level DESI tracer eigenmass and DESI/MaNGA joined-cell tracer eigenmass align with cosine 0.702922832; MaNGA gas/shock overlap sharpens the dominant explained share by 1.784206501x
- Hutter eigenmass transfer: DESI multiscale eigenmass method ported into a Hutter tuning protocol with seven promotion gates; no Hutter compression-gain claim is made
- Stellar gas Abelian sandpile probe: eigenmass treated as grains and gas/shock channels as toppling pressure; 5 avalanche-candidate cells found, with eigenmass most correlated to DESI density, stellar sigma, and shock proxies
- Stellar gas sandpile fine zoom: 911 MaNGA objects found inside 5 avalanche-candidate cells; 40 object-level proxy examples emitted for follow-up while mechanism proof remains HOLD
- Stellar gas full-cell stability: all 25 joined cells checked against full-cell and null/ablation controls; stored 25-cell comparison cosine is 1.0 and leave-one-cell-out minimum cosine is 0.996495428
- Stellar gas sandpile graph replay: graph diagnostic emits 25 nodes, 45 edges, 5 seeded avalanche candidates, graph hash `fdfc686a022b726f550f73ad663cd9e222122a1048193dd22dafee0d891c62af`, and replay hash `95e938b7f6ed3a3c64af0fdaec45e9296316ae9e77b6b937aaa9ee16f7665393`
- Hutter transfer readiness fixture: 669-byte fixture `htrf_local_text_window_2026_05_09_v0`, SHA-256 `eacd7a17d3485ff0e9fd3ec19c3c2dfcc7419e906eafe18817b07596a99ad6e6`, raw/zlib/lzma/current-wire baseline matrix, negative controls, and Rust OISC byte-exact replay; no Hutter compression, full-corpus, FPGA, or ASIC claim
- Drive sync receipt: curated eigenmass-stack safety snapshot copied to `Gdrive:topological_storage/research-stack/eigenmass-stack-2026-05-09` with 36 remote entries observed after final sync; this manifest remains the full source list
- Agent routing files: repo root, Lean/Semantics, and Infrastructure contracts added
- Receipt visibility: stack solidification receipts and `shared-data/network_topology_database.json` are no longer hidden by broad `shared-data/` ignore rules
- Promotion decision: NO_PROMOTION
