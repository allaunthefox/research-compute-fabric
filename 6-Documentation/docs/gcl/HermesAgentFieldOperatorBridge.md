# Hermes Agent — Field Operator Bridge for Research Stack

**Status**: Integration Proposal  
**Date**: 2026-05-02  
**Version**: 1.0.0-Phase0  
**Source**: https://github.com/allaunthefox/hermes-agent  
**Lean Module**: `0-Core-Formalism/lean/Semantics/Semantics/HermesAgentIntegration.lean`  

---

## Core Thesis

Hermes Agent is the **field-operator layer** for Research Stack: a messenger, scheduler, skill runtime, and subagent launcher that can perform repeatable GCL/Warden workflows while remaining subordinate to Lean, receipts, and Warden promotion gates.

**Hermes is not the brain.** The canonical model, lawfulness filter, and proof authority remain in OTOM/GCL/Lean. Hermes sits outside the proof core, executing tasks that Lean delegates but never verifying its own outputs as truth.

---

## Role Separation

| System | Role | Authority |
|--------|------|-----------|
| **Hermes** | Observes, routes, schedules, executes | Workflow layer only |
| **GCL** | Classifies, compresses, binds | Coding-space authority |
| **Lean** | Verifies, proves, is source of truth | Proof authority |
| **Warden** | Promotes, holds, blocks | Promotion gate |
| **ENE** | Persists, distributes, syncs | Swarm substrate |

---

## Warden-Safe Doctrine

```
Hermes may execute.
Hermes may remember.
Hermes may suggest.
Hermes may schedule.
Hermes may not promote without receipts.
```

### Critical Rules

1. **If Hermes skill writes or updates doctrine and no source/provenance/receipt boundary is emitted**: mark `HOLD`.

2. **If Hermes self-improvement modifies a skill used for promotion**: require `SkillMutationReceipt` + `AdversarialTrial`.

3. **All scheduled audit outputs default to `HOLD`** until external receipt validates them.

4. **Hermes is autopoietic at the workflow layer, not authoritative at the truth layer.**

---

## Integration Surfaces

| Hermes Feature | Research Stack Binding | Warden Boundary |
|----------------|------------------------|----------------|
| **Skills** | Repeatable GCL procedures | Skill mutation must be receipted |
| **Memory** | Project/user continuity | Memory is context, not evidence |
| **Cron** | Scheduled audits | Scheduled output defaults to `HOLD` |
| **Messaging Gateway** | Remote command interface | High-risk commands require confirmation |
| **Subagents** | Parallel review/search/build jobs | Subagent agreement is not evidence |
| **MCP** | Connectors/tools surface | Tool output needs provenance |
| **Terminal Backends** | Local/SSH/Docker/Modal execution | Command allowlist + sandbox receipts |
| **RL/Trajectories** | Training data for workflow agents | Trajectory compression is not proof |

---

## Command Surface

Hermes exposes these read-only and receipt-producing commands:

```
/run-gcl-audit          → GCL classification audit
/summarize-receipts    → Warden receipt ledger summary
/queue-deepseek-review → Adversarial review bundle assembler
/check-lean-sorries    → Lean sorry scan + classification
/search-provenance     → Provenance database search
/build-cff-entry      → CFF citation entry generator
/warden-status         → HOLD/BLOCK/CANDIDATE/REVIEWED report
/skill-run <name>      → Execute named skill with receipt emission
```

---

## Skill Specifications (Phase 1)

### `gcl-provenance-cff`
- **Task**: Ingest DOI / article / source → create CFF entry → add Warden boundary
- **Sources**: `doi`, `article_metadata`, `provenance_db`
- **Receipts Required**: `sourceAudit`, `humanReview`
- **Failure Modes**: `missing_doi`, `malformed_cff`, `no_provenance`

### `lean-sorry-audit`
- **Task**: Scan Lean files → list sorry locations → classify gaps
- **Sources**: `0-Core-Formalism/lean/Semantics`
- **Receipts Required**: `leanBuild`
- **Failure Modes**: `build_failure`, `sorry_increase`, `missing_todo_comment`

### `adapter-spec-writer`
- **Task**: Turn source cluster into GCL bridge doc
- **Sources**: `source_cluster`, `gcl_schema`
- **Receipts Required**: `humanReview`, `deltaPhiAudit`
- **Failure Modes**: `missing_bind`, `no_cost_function`, `float_in_hotpath`

### `deepseek-review-bundle`
- **Task**: Collect docs → enforce adversarial convergence prompt → save artifact
- **Sources**: `review_docs`, `adversarial_prompt_template`
- **Receipts Required**: `adversarialTrial`, `humanReview`
- **Failure Modes**: `missing_convergence_prompt`, `artifact_too_large`, `no_receipt_emitted`

### `warden-triage`
- **Task**: Classify outputs as `HOLD` / `CANDIDATE` / `BLOCK` / `REVIEWED`
- **Sources**: `output_artifact`, `receipt_ledger`
- **Receipts Required**: `wardenEmission`
- **Failure Modes**: `missing_status`, `no_receipt_boundary`, `self_promotion_detected`

---

## Scheduled Audit Jobs (Phase 2)

### Daily
- Check Lean build (`lake build`)
- Check sorry count (trend vs. baseline)
- Check uncommitted docs in `docs/gcl/`
- Check CFF malformed entries
- Check provenance gaps

### Weekly
- Run DeepSeek bundle lint
- Summarize new GCL docs
- Report Warden `HOLD`/`BLOCK` items
- Check MMR divergence / attestation staleness

---

## Promotion Phases

### Phase 0 — Read-Only Bridge (Current)
- No writes, no autonomous mutation
- Hermes can: search docs, summarize Warden state, run read-only git status, list Lean sorries, assemble review bundles
- **Output**: this document + `HermesAgentIntegration.lean`

### Phase 1 — Receipt-Producing Skills
- Allow artifact creation, no promotion
- Every skill emits: `SkillRunReceipt` + `SourceReceipt` + `WardenStatus`

### Phase 2 — Scheduled Warden Jobs
- Cron-driven recurring audits
- All outputs default to `HOLD`

### Phase 3 — Controlled Write Authority
- Hermes may open PRs or commits
- Each commit must include: source boundary, Warden state, rollback path, no self-promotion

---

## Prior Art

- **Nous Research Hermes Agent**: Self-improving agent with 4-layer memory, session lineage, FTS5 search, skill creation/patching, schema-versioned SQLite storage
- **Awareness Date**: 2026-04-05
- **Clean Room Status**: Independence confirmed for Research Stack's dual-storage SQLite + JSON, procedural/episodic separation, skill patch pattern, and prompt memory cap
- **Adaptations from Hermes**: Session lineage (`parent_session_id` + recursive CTE), FTS5 virtual table, pre-reset memory saving on `EMERGENCY` regret threshold, schema versioning, WAL mode with retry jitter
- **Record**: `scratch/exploit_recovery/audit/sessions/prior-art-hermes-agent-nous-research-20260405.json`

---

## Lean Formalization

The integration boundary is formalized in `HermesAgentIntegration.lean`:

- `HermesCommand` — inductive command surface (8 constructors)
- `HermesSkill` — skill specification with phase, receipts, failure modes
- `HermesStatus` — promotion state: `HOLD` / `CANDIDATE` / `REVIEWED` / `BLOCKED`
- `SkillRunReceipt` — execution receipt convertible to `ReceiptCore.Receipt`
- `canPromote` — gate function requiring receipt validation
- `readOnlyCannotPromote` — **theorem (proven)** — Phase 0 skills never promote
- `defaultStatusIsHold` — **theorem (proven)** — default status is `HOLD`

---

## The One Rule

> Hermes is autopoietic at the workflow layer, not authoritative at the truth layer.
