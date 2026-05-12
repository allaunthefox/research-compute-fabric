# AGENTS.md - Research Stack Operating Contract

This file is the first stop for coding agents working in this repository.

## Ground Rules

- Use `/home/allaun/Documents/Research Stack` as the active checkout unless a task explicitly points elsewhere.
- Read the nearest nested `AGENTS.md` before editing a subtree.
- Preserve user work. The working tree is often intentionally dirty; do not revert, delete, or stage unrelated files.
- Prefer repo-native tools and receipt generators over ad hoc summaries.
- Treat Lean as the source of truth for formal or hardware-adjacent claims.
- Keep claims bounded: a receipt proves only the gate it actually checks.
- Secrets are runtime-only. Use environment variables such as `OLLAMA_API_KEY`
  or `DEEPSEEK_API_KEY`; never paste, print, or commit literal provider keys.
- For repo-stabilization tasks, finish with a clean `git status --branch --short
  --untracked-files=all` and an empty `git clean -nd` dry run before claiming
  the tree is stable.

## Core Surfaces

- Lean/Semantics: `0-Core-Formalism/lean/Semantics/`
- Infrastructure shims and probes: `4-Infrastructure/shim/`
- Hardware bring-up: `4-Infrastructure/hardware/`
- Documentation and wiki surfaces: `6-Documentation/`
- Stack receipts: `shared-data/data/stack_solidification/`
- Promoted review receipts: `shared-data/artifacts/deepseek_review/`
- Canonical Ollama/DeepSeek review emitter:
  `5-Applications/tools-scripts/llm/ollama_deepseek_review_emitter.py`
- CAD harness: `5-Applications/text-to-cad/`
- Historical scoped staging maps:
  `6-Documentation/docs/stack_solidification_staging_manifest_2026-05-09.md`
  and `6-Documentation/docs/stack_solidification_staging_manifest_2026-05-10.md`

## Verification Expectations

- For Lean changes, run the narrow target first, then the broader `lake build` when feasible.
- For Python shims, run `python3 -m py_compile` on touched files.
- For JSON receipts, run `python3 -m json.tool` or a repo-native receipt parser.
- For promoted Ollama/DeepSeek review receipts, run
  `python3 5-Applications/tools-scripts/llm/ollama_deepseek_review_emitter.py --verify-only`
  so `answer_sha256` is checked against the answer file after write.
- For hardware claims, distinguish software witness, bitstream presence, SRAM load, flash persistence, UART beacon, and live hardware receipt.
- Before committing, run `git diff --cached --check` and a staged secret scan
  for touched source/receipt files. The repository credential hook is a final
  gate, not a substitute for local review.
- For root CAD setup changes, JSON-parse `package.json`, `.vscode/settings.json`,
  and `.vscode/tasks.json`, then use the pinned Python/CAD commands documented
  in `5-Applications/text-to-cad/AGENTS.md`.

## Do Not Sweep

Avoid broad cleanup or staging commands such as:

```bash
git add .
git add 0-Core-Formalism 4-Infrastructure 6-Documentation shared-data
git checkout -- .
git clean -fdx
```

Use explicit file lists from the relevant staging manifest.

`shared-data/` is ignored by default because most of it is generated or
offloaded. Promote only specific, durable receipts with `git add -f -- <path>`,
and keep empty/failed model outputs out of Git unless they are themselves the
evidence under review.

## Git Remote Hygiene

- The active branch may not have an upstream. Inspect with
  `git rev-parse --abbrev-ref --symbolic-full-name @{u}` before assuming push
  state.
- For GitHub sync, prefer the `github` remote and verify the remote head after
  push:

```bash
git fetch github <branch>
git rev-list --left-right --count FETCH_HEAD...HEAD
git push -u github <branch>
git ls-remote --heads github <branch>
```

- Dependabot banners printed by GitHub after push may be stale relative to the
  live alert API. Treat the push result and remote-head hash separately from
  dependency-alert remediation.

## Legacy Recovery Trigger

The phrase **`RECOVER LEGACY INFORMATION`** is the explicit retrieval trigger
for archived or quarantined concepts. Treat this as a user-controlled cold
archive request, not permission to revive an old branch wholesale.

Accepted trigger forms:

```text
RECOVER LEGACY INFORMATION: <path, commit, concept, or artifact>
Recover Legacy Information: <path, commit, concept, or artifact>
recover from cornfield: <path, commit, concept, or artifact>
```

When this trigger appears:

- Inspect the requested legacy source first with read-only commands such as
  `git show`, `git log`, or targeted file reads.
- Recover only the named file, concept, commit slice, or receipt requested.
- Modernize the recovered material onto the current clean branch before
  committing it.
- Never merge, reset to, or base new work on a legacy/cornfield branch unless
  the user explicitly asks for that exact branch operation.
- Preserve the legacy branch as retrievable archive state.

Current cornfield ref:

```text
backup/distilled-with-vcd-history-2026-05-11
```

## Nested Contracts

- Strict Lean/docs contract: `6-Documentation/docs/AGENTS.md`
- Lean module-local contract: `0-Core-Formalism/lean/Semantics/AGENTS.md`
- Infrastructure contract: `4-Infrastructure/AGENTS.md`
- CAD harness contract: `5-Applications/text-to-cad/AGENTS.md`
