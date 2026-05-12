# DeepSeek Review Process

> **Source:** [[Home|Wiki Home]] · `5-Applications/tools-scripts/llm/deepseek_review_adapter.py` · `shared-data/artifacts/deepseek_review/`

The Research Stack incorporates DeepSeek AI models for formal mathematical
review and validation of canonical specifications, Lean kernels, and
statistical-interpretation receipts. This page documents the wiki-level view
of the review pipeline, the receipt schema, and the canonical example
(prime-gap entropy collapse) shipped under
`shared-data/artifacts/deepseek_review/`.

---

## AI-Assisted Mathematical Review

DeepSeek review receipts provide reproducibility and integrity tracking for
AI-assisted mathematical validation. Each review run emits a paired
`.md` answer file and a `.receipt.json` sidecar that records the exact model,
endpoint, token usage, and SHA-256 hashes needed to re-validate the review
without re-running the model.

### Review Artifacts

| Path | Purpose |
|---|---|
| `shared-data/artifacts/deepseek_review/` | Root for all review answers and receipt sidecars |
| `*_deepseek-v3.2_*.md` | Primary review answer (markdown, model-authored) |
| `*_deepseek-v3.2_*.receipt.json` | Receipt for the primary review (schema `ollama_deepseek_review_receipt_v1`) |
| `*_deepseek-v4-flash_continuation_*.md` | Continuation answer when the primary review was truncated |
| `*_deepseek-v4-flash_continuation_*.receipt.json` | Receipt for the continuation (schema `ollama_deepseek_review_continuation_receipt_v1`) |

Receipt filenames are aligned with their answer files by sharing the same
`<topic>_<model>_<ISO-timestamp>` stem.

### Receipt Schema

Both receipt schemas are versioned JSON records that track every field needed
to re-derive the review independently of the model server.

| Field | Type | Notes |
|---|---|---|
| `schema` | string | `ollama_deepseek_review_receipt_v1` (primary) or `ollama_deepseek_review_continuation_receipt_v1` (continuation) |
| `created_at` | ISO-8601 timestamp | UTC time at which the review was produced |
| `model` | string | Model identifier (e.g. `deepseek-v3.2`, `deepseek-v4-flash`) |
| `endpoint` | URL | API endpoint that served the review (e.g. `https://ollama.com/v1/chat/completions`) |
| `prompt_sha256` | `sha256:<hex>` | SHA-256 of the exact serialized prompt body sent to the endpoint |
| `answer_sha256` | `sha256:<hex>` | SHA-256 of the answer payload written to `answer_path` |
| `usage.prompt_tokens` | int | Tokens consumed by the prompt as reported by the endpoint |
| `usage.completion_tokens` | int | Tokens produced by the model |
| `usage.total_tokens` | int | Sum of the two above (recorded for cross-checks) |
| `context_files` | string[] | Repo-relative paths to every file that participated in the review prompt context (primary receipt only; continuation consumers reconstruct this through `previous_answer_path` and the primary receipt) |
| `answer_path` | string | Repo-relative path to the answer markdown |
| `previous_answer_path` | string | Repo-relative path to the answer being continued (continuation receipt only) |
| `message_keys` | string[] | Field names returned alongside `content` by the continuation endpoint (e.g. `role`, `content`, `reasoning`) (continuation receipt only) |

Receipts are committed alongside the answers so that any future agent can:

1. Verify integrity by recomputing the SHA-256 of `answer_path` and comparing
   to `answer_sha256`.
2. Reconstruct the prompt by joining the listed `context_files` against the
   commit at which the receipt was authored.
3. Audit token usage and cost without re-querying the endpoint.

### Reconstructing context for continuations

Continuation receipts intentionally omit `context_files` — a continuation
inherits the prompt context of the primary review it extends. Consumers should
not treat the missing field as lost context; they reconstruct it through the
previous answer and primary receipt. To reconstruct the full context for a
continuation answer:

1. Read `previous_answer_path` from the continuation receipt.
2. Locate the sibling primary receipt by replacing the `.md` suffix on
   `previous_answer_path` with `.receipt.json` (the primary receipt and its
   answer share a stem).
3. Read `context_files` from that primary receipt and treat it as the
   continuation's effective context bundle.
4. The continuation prompt body itself is the primary answer at
   `previous_answer_path` plus any continuation directive recorded in the
   continuation answer's preamble; `prompt_sha256` on the continuation
   receipt covers that combined body.

### Review Process

Reviews are executed as a two-stage pipeline:

1. **Primary analysis** with `deepseek-v3.2` against a curated prompt that
   bundles the canonical spec, statistical receipts, and Lean kernels for the
   topic under review.
2. **Continuation** with `deepseek-v4-flash` when the primary review is
   truncated by the per-completion token cap. The continuation receipt
   references the primary answer via `previous_answer_path` and inherits the
   review topic via filename stem.

Every review answer is structured to include:

- A **YES/NO verdict table** answering the specific review questions posed
  in the prompt.
- An **arithmetic recheck** that recomputes every numeric claim in the
  reviewed material against the canonical specification.
- A **statistical interpretation** section that classifies thresholds as
  `CANONICAL`, `HEURISTIC`, or `DETERMINISTIC WINDOW FEATURE`, and flags
  null-model mismatches.
- A **failure mode analysis** that enumerates the conditions under which the
  reviewed method would emit false positives or false negatives.
- A **canonical spec patches** block of explicit warnings to copy verbatim
  into the reviewed specification.

### Example Review: Prime Gap Entropy Collapse

The canonical example shipped with the initial DeepSeek review tracking is
the prime-gap entropy-collapse analysis:

| Artifact | Path |
|---|---|
| Primary answer | `shared-data/artifacts/deepseek_review/prime_gap_entropy_collapse_deepseek_deepseek-v3.2_20260512T033551Z.md` |
| Primary receipt | `shared-data/artifacts/deepseek_review/prime_gap_entropy_collapse_deepseek_deepseek-v3.2_20260512T033551Z.receipt.json` |
| Continuation answer | `shared-data/artifacts/deepseek_review/prime_gap_entropy_collapse_deepseek_deepseek-v4-flash_continuation_20260512T033849Z.md` |
| Continuation receipt | `shared-data/artifacts/deepseek_review/prime_gap_entropy_collapse_deepseek_deepseek-v4-flash_continuation_20260512T033849Z.receipt.json` |

Context files cited by the primary receipt:

- `6-Documentation/docs/distilled/ArithmeticSpec_Corrected_2026-05-11.md`
- `shared-data/data/stack_solidification/prime_gap_k21_rerun_receipt_2026-05-11.md`
- `0-Core-Formalism/lean/Semantics/Semantics/HCMMR/Kernels/EntropyCollapseDetector.lean`

The review covers:

- **Arithmetic verification** of the canonical spec (crossing counts, `D₂`,
  `σ_q`, Kendall SD, and exact tail probabilities at `W=8`).
- **Statistical interpretation** of threshold selection — confirming `K=7`
  as non-selective (94.57% FPR under random-permutation null) and `K=21` as a
  heuristic ~5% FPR calibration (strict `>21`: 3.05%, inclusive `>=21`: 5.43%).
- **Failure mode analysis** for the random-permutation null model when
  applied to prime gaps (ties, non-uniform marginal distribution, local
  dependence make the FPR estimates unreliable).
- **Canonical spec patches** that add HEURISTIC warnings, clarify that
  window-level `σ_q` and `D₂` are deterministic features rather than
  estimators, document the null-model mismatch for prime gaps, and address
  multiple-testing and edge-effect considerations.
- **Continuation** (deepseek-v4-flash) extending the canonical spec patches
  with predictive-versus-contemporaneous fusion semantics, ground-truth
  caveats, parameter-sensitivity reporting requirements, edge-effect handling,
  reproducibility requirements, and an interpretation caveat for the final
  verdict surface.

---

## Adding a New Review

When emitting new review artifacts:

1. Write the answer to
   `shared-data/artifacts/deepseek_review/<topic>_deepseek_<model>_<ISO-Z>.md`.
   The literal `_deepseek_` segment is the **provider tag** and is held
   constant across all DeepSeek-family reviews; `<model>` is the specific
   model identifier (e.g. `deepseek-v3.2`, `deepseek-v4-flash`). The two
   segments are kept separate so future provider-level tooling (rate caps,
   budget accounting, fleet-wide audits) can filter on the provider tag
   without parsing the `<model>` slug. This is why the canonical example
   filenames contain `_deepseek_deepseek-v3.2_` — the doubled `deepseek` is
   intentional and reflects `<provider>_<model>`.
2. Write the matching receipt alongside it with the same stem and
   `.receipt.json` suffix, using `ollama_deepseek_review_receipt_v1` for the
   primary review and `ollama_deepseek_review_continuation_receipt_v1` for any
   continuation.
3. Populate `context_files` with repo-relative paths to every file consumed
   by the prompt so future agents can reproduce the prompt body. Continuation
   receipts omit `context_files` and `message_keys` records the alternate
   shape of the continuation response; consumers reconstruct continuation
   context via the primary receipt indexed by `previous_answer_path` (see
   [[#Reconstructing context for continuations]] above).
4. Record `prompt_sha256` and `answer_sha256` for integrity verification.
5. Commit the answer and receipt together — the receipt is meaningless
   without the answer it indexes, and the answer is unverifiable without the
   receipt.

---

## Related

- [[Build-System]] — pinned Python interpreter that drives the review adapter
  and ensures prompt-hash reproducibility across runs.
- `5-Applications/tools-scripts/llm/deepseek_review_adapter.py` — adapter that
  emits the receipt + answer pair.
- `6-Documentation/docs/distilled/` — canonical specs that reviews validate
  against (e.g. `ArithmeticSpec_Corrected_2026-05-11.md`).
- `0-Core-Formalism/lean/Semantics/Semantics/HCMMR/Kernels/` — Lean kernels
  cross-referenced as review context.
