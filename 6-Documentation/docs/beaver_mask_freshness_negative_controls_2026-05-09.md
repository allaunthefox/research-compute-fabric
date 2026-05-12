# Beaver Mask Freshness Negative Controls

**Date:** 2026-05-09

This closes one narrow shaky part: adaptive/topology-derived coefficients are not admitted as privacy-equivalent Beaver masks in the local Lean gate.

## Claim Boundary

Finite freshness/admission gate only. This rejects unsafe mask sources in the local model; it does not prove full MPC privacy, entropy quality, or adaptive Beaver security.

## Gate

- Lean module: `Semantics.BeaverMaskFreshness`
- Lean build: `PASS`
- Case status: `PASS_NEGATIVE_CONTROLS`
- Positive controls: `2`
- Negative controls: `4`
- Promotion effect: `PARTIAL_EVIDENCE_ONLY_SECURITY_HOLD_REMAINS`

## Cases

- `fresh_unused_admits`: expected `ADMIT`, observed `ADMIT`, Lean witness `freshUnusedAdmits`
- `distinct_fresh_sequence_admits`: expected `ADMIT`, observed `ADMIT`, Lean witness `distinctFreshSequenceAdmits`
- `reused_source_rejected`: expected `REJECT`, observed `REJECT`, Lean witness `reusedSourceRejected`
- `reused_mask_id_mislabeled_fresh_rejected`: expected `REJECT`, observed `REJECT`, Lean witness `reusedMaskIdRejected`
- `topology_derived_rejected`: expected `REJECT`, observed `REJECT`, Lean witness `topologyDerivedRejected`
- `adversarial_chosen_rejected`: expected `REJECT`, observed `REJECT`, Lean witness `adversarialChosenRejected`

## Remaining Security Debt

- This does not prove true randomness or independence of a deployed entropy source.
- This does not prove a full Beaver Triples privacy theorem.
- This does not admit topology-derived coefficients as masks; they remain useful routing coefficients only after separate receipt gates.

## Machine Receipt

- `shared-data/data/stack_solidification/beaver_mask_freshness_negative_controls.json`
