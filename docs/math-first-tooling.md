# Math-First Tooling

This document codifies the "math first" contract for the Research Stack: every
mathematical claim that ships from this repository must carry machine-checkable
evidence — a Lean proof, a DeepSeek review receipt with SHA-256 integrity, or
both — and the development environment must make it harder to bypass that
contract than to honour it.

It is the human-readable companion to:

| Artifact | Path |
|----------|------|
| Receipt schema | [`shared-data/schemas/deepseek-review-receipt.schema.json`](../shared-data/schemas/deepseek-review-receipt.schema.json) |
| Claim registry schema | [`shared-data/schemas/claims-registry.schema.json`](../shared-data/schemas/claims-registry.schema.json) |
| Claim registry | [`claims.yaml`](../claims.yaml) |
| Receipt validator | [`scripts/math-first/validate_deepseek_receipts.py`](../scripts/math-first/validate_deepseek_receipts.py) |
| Registry validator | [`scripts/math-first/validate_claims_registry.py`](../scripts/math-first/validate_claims_registry.py) |
| Evidence gate | [`scripts/math-first/require_math_evidence.py`](../scripts/math-first/require_math_evidence.py) |
| Pre-commit config | [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) |
| CI workflow | [`.github/workflows/math-check.yml`](../.github/workflows/math-check.yml) |
| MCP server registry | [`.mcp.json`](../.mcp.json) |

Read [`AGENTS.md`](../AGENTS.md) and
[`6-Documentation/wiki/DeepSeek-Review-Process.md`](../6-Documentation/wiki/DeepSeek-Review-Process.md)
first — this document layers tooling on top of those contracts and does not
restate them.

## Philosophy

1. **Lean is the source of truth.** Anything that can be stated as a Lean
   `theorem` or kernel obligation should live under
   `0-Core-Formalism/lean/Semantics/`. Other evidence (DeepSeek reviews,
   SymPy/Wolfram cross-checks, hardware receipts) is a witness, not a proof.
2. **Every claim has a status.** The states are
   `conjecture → verified-by-ai → formally-proven → published`. Movement only
   ever travels in that direction, and every transition is accompanied by a
   change to `claims.yaml`.
3. **Receipts pin model output to disk.** DeepSeek answers and their
   `*.receipt.json` siblings carry `prompt_sha256` and `answer_sha256` so a
   review can be re-validated without re-running the model.
4. **CI enforces the contract.** Anything humans are expected to remember is
   re-checked by a workflow that fails the PR if the contract is broken.
5. **AI assistants get tool access, not trust.** The `.mcp.json` registry
   gives Claude / Devin / Codex the Wolfram, SymPy, and Lean bridges they need
   to discharge proof obligations — and nothing else. DeepSeek review remains
   available through the canonical CLI emitter until a real MCP wrapper exists.

## Repository Layout (math-first surfaces)

```
0-Core-Formalism/lean/Semantics/      # Lean source of truth (lakefile.toml)
shared-data/schemas/                   # JSON Schemas for every receipt format
shared-data/artifacts/deepseek_review/ # Promoted DeepSeek review receipts
shared-data/data/stack_solidification/ # Stack receipts (math-track)
6-Documentation/docs/distilled/        # Distilled math specs (math-track)
scripts/math-first/                    # Validators + evidence gate
claims.yaml                            # Single source of truth for claims
.pre-commit-config.yaml                # Local guardrail
.github/workflows/math-check.yml       # CI guardrail
.mcp.json                              # AI-assistant tool registry
```

## Receipt Schema (`ollama_deepseek_review_receipt_v1`)

The schema at
[`shared-data/schemas/deepseek-review-receipt.schema.json`](../shared-data/schemas/deepseek-review-receipt.schema.json)
formalises the contract that the canonical emitter
[`5-Applications/tools-scripts/llm/ollama_deepseek_review_emitter.py`](../5-Applications/tools-scripts/llm/ollama_deepseek_review_emitter.py)
already writes. It validates two receipt flavours:

* **Primary review** (`ollama_deepseek_review_receipt_v1`) — requires
  `schema`, `created_at`, `model`, `endpoint`, `prompt_sha256`,
  `answer_sha256`, `usage.{prompt_tokens,completion_tokens,total_tokens}`,
  `context_files` (non-empty), and `answer_path`.
* **Continuation review** (`ollama_deepseek_review_continuation_receipt_v1`)
  — replaces `context_files` with `previous_answer_path` and optionally
  reports the `message_keys` returned by the continuation endpoint.

Both flavours pin SHA-256 hashes as the literal string `sha256:<64 hex>`,
require token counts to be non-negative integers, and require paths to be
repo-relative POSIX strings ending in `.md` for answer paths. Additional
fields are rejected so receipts stay shaped exactly as the emitter writes
them.

### Re-validate locally

```bash
uv run --python 3.11 \
  --with "jsonschema>=4.21" --with "rfc3339-validator" \
  python3 scripts/math-first/validate_deepseek_receipts.py
```

To validate a single receipt:

```bash
python3 scripts/math-first/validate_deepseek_receipts.py \
  shared-data/artifacts/deepseek_review/<topic>_<model>_<ts>.receipt.json
```

The validator has its own self-tests:

```bash
python3 scripts/math-first/test_validate_deepseek_receipts.py
```

## Mathematical Claim Registry

[`claims.yaml`](../claims.yaml) is the single source of truth for the rigor
level of every tracked mathematical claim. The schema accepts these fields:

| Field | Required | Notes |
|-------|----------|-------|
| `id` | yes | Stable kebab-case slug. |
| `title` | yes | One-line natural-language statement of the claim. |
| `status` | yes | `conjecture` \| `verified-by-ai` \| `formally-proven` \| `published`. |
| `lean` | conditional | Required when `status == formally-proven`. Repo-relative Lean source path. |
| `review_receipts` | conditional | Required when `status == verified-by-ai`. Repo-relative `*.receipt.json` paths. |
| `sources` | no | Supporting docs, scripts, or external citations. |
| `notes` | no | Free-form context. |

```bash
uv run --python 3.11 \
  --with "jsonschema>=4.21" --with "PyYAML" \
  python3 scripts/math-first/validate_claims_registry.py
```

The validator enforces the JSON Schema, asserts every `id` is unique, and
asserts every repo-relative path referenced from `lean`, `review_receipts`,
or `sources` exists on disk.

## Pre-Commit Hooks

`.pre-commit-config.yaml` wires four guardrails:

* `pre-commit-hooks` — `check-json`, `check-yaml`, EOF / trailing whitespace
  scoped to math-first files only (see [`AGENTS.md`](../AGENTS.md) "Do Not
  Sweep"), and `detect-private-key`.
* `deepseek-receipt-schema` — runs the receipt validator on every staged
  `*.receipt.json` under `shared-data/artifacts/deepseek_review/`.
* `claims-registry-schema` — runs the registry validator whenever
  `claims.yaml` is staged.
* `receipt-required-for-math-content` — invokes
  `scripts/math-first/require_math_evidence.py`. If a commit touches a
  math-track surface (`0-Core-Formalism/lean/Semantics/`,
  `6-Documentation/docs/distilled/`,
  `shared-data/data/stack_solidification/`), the same commit must also touch
  a math-evidence surface (a DeepSeek receipt, a Lean kernel, or
  `claims.yaml`).

### Install

```bash
uv tool install pre-commit          # one-time, per machine
pre-commit install                  # one-time, per clone
pre-commit run --all-files          # smoke-test
```

## CI Workflow

[`.github/workflows/math-check.yml`](../.github/workflows/math-check.yml)
runs on every PR and on pushes to `main` or `distilled` that touch a
math-first surface. It has three jobs:

1. **`validate-schemas`** — compiles every schema under
   `shared-data/schemas/`, validates every tracked DeepSeek receipt, runs the
   validator's own self-tests, validates `claims.yaml`, and finally re-runs
   the canonical emitter in `--verify-only` mode against every receipt to
   re-check `answer_sha256` against the answer file bytes on disk. This is
   the AGENTS.md contract for promoted Ollama/DeepSeek review receipts.
2. **`require-evidence`** — runs only on PRs and invokes
   `scripts/math-first/require_math_evidence.py --from-git-diff
   origin/<base>` to enforce the same evidence rule at PR scope that the
   pre-commit hook enforces at commit scope.
3. **`pre-commit`** — runs every pre-commit hook against the PR's range of
   changed files (`pre-commit run --from-ref <base> --to-ref HEAD`), so the
   guardrails are honoured even when a contributor has not installed the
   hooks locally.

The pre-existing `wolfram-verification.yml` workflow continues to police
mathematical formulas inside Lean source for missing Wolfram Alpha
verification comments; nothing here replaces it.

## MCP Servers for AI-Assisted Math

[`.mcp.json`](../.mcp.json) declares the math-first tool surface that
Claude Desktop, Devin, and other MCP-aware clients should advertise when
working in this repo. Each server is intentionally **gated on a runtime
environment variable**, so the config itself never carries secrets and
contributors who have not provisioned a backend simply skip it.

| Server | Purpose | Runtime requirement |
|--------|---------|---------------------|
| `filesystem` | Read/write proof artifacts, Lean kernels, receipts. | `npx`, scope pinned to repo root. |
| `sympy` | Local SymPy bridge for symbolic verification of arithmetic claims. | `uv tool run sympy-mcp` (`sympy-mcp` upstream). |
| `wolfram-alpha` | Wolfram Alpha verification for the formulas policed by `wolfram-verification.yml`. | `WOLFRAM_ALPHA_APPID`. |
| `lean` | Lean 4 / Mathlib typecheck bridge against `0-Core-Formalism/lean/Semantics/lakefile.toml`. | `elan` on PATH with `leanprover/lean4:v4.30.0-rc2`. |
| DeepSeek review | Use `5-Applications/tools-scripts/llm/ollama_deepseek_review_emitter.py` directly; no MCP server is currently advertised for it. | `OLLAMA_API_KEY` for non-local endpoints. |

To use these from Claude Desktop, point its `claude_desktop_config.json` at
the repo root or copy the relevant entries verbatim. Secrets live in the
shell/env, never in the config.

## Workflow: adding a new claim

1. Land the natural-language claim in `claims.yaml` with `status: conjecture`.
2. Produce a DeepSeek review via the canonical emitter. Commit both the
   answer markdown and `*.receipt.json`; promote `status` to
   `verified-by-ai` in the same commit. The pre-commit `require-evidence`
   gate now finds a receipt alongside any math-track edit, and the schema
   validator confirms the receipt parses.
3. When a Lean proof lands under `0-Core-Formalism/lean/Semantics/`, promote
   `status` to `formally-proven` and set `lean:` to the proof's source path.
4. On external publication, promote `status` to `published` and add the
   citation to `sources:`.

## Workflow: editing a math-track file

The math-first surfaces are:

* `0-Core-Formalism/lean/Semantics/...`
* `6-Documentation/docs/distilled/...`
* `shared-data/data/stack_solidification/...`

Any commit touching one of these surfaces must, in the same commit, touch
one of:

* `shared-data/artifacts/deepseek_review/...` (new receipt + answer file)
* `0-Core-Formalism/lean/Semantics/...` (Lean change in the same commit
  counts as evidence — Lean is the source of truth)
* `claims.yaml` (registry update)

The pre-commit hook and CI both enforce this. To bypass intentionally — for
example, a typo fix in a distilled doc with no semantic change — commit with
`git commit --no-verify` and explain the bypass in the PR description; CI
will still flag the PR and the maintainer can apply the
`math-first-exempt` label (one-off override).

## Verifying everything in one shot

```bash
# Schemas + receipts + claims + emitter --verify-only
uv run --python 3.11 \
  --with "jsonschema>=4.21" --with "rfc3339-validator" --with "PyYAML" \
  bash -c '
    python3 scripts/math-first/validate_deepseek_receipts.py \
      && python3 scripts/math-first/test_validate_deepseek_receipts.py \
      && python3 scripts/math-first/validate_claims_registry.py \
      && for r in shared-data/artifacts/deepseek_review/*.receipt.json; do \
           python3 5-Applications/tools-scripts/llm/ollama_deepseek_review_emitter.py --verify-only "$r"; \
         done
  '
```

If any of the above fails, the corresponding PR will not merge.
