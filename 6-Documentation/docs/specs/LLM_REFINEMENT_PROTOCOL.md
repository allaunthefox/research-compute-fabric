# LLM Refinement Protocol

Date captured: 2026-05-07
Source prompt: How to Squeeze GENIUS out of LLMs: Notes from My QRI Retreat Skillshare, Andres Gomez-Emilsson, 2026-05-07.

Purpose: convert a rough research idea into a stable, auditable refinement loop.

## Core rule

Treat an LLM as a chart-transform instrument, not as an answer oracle.

The protocol forces the model to expose hidden dimensions, rotate lenses, lock vocabulary, compress the result into primitives, and audit residuals before accepting a claim.

## Refinement loop

1. Table expansion
   - Ask the model to infer the hidden dimensions of the concept.
   - Require columns for axis, observable proxy, uncertainty, failure mode, primitive mapping, and test hook.

2. Lens sweep
   - Run the same concept through multiple charts.
   - Default lenses: hostile domain scientist, patent examiner, systems engineer, formal-methods auditor, safety reviewer, and implementation engineer.
   - Preserve disagreements between lenses instead of smoothing them away.

3. Glossary lock
   - Extract every polysemic or overloaded term.
   - Give each term a local project definition.
   - Reuse the definitions block across future chats and repo notes.

4. Primitive compression
   - Collapse the concept into the four keeper primitives: field, shear, packet, spectral.
   - Reject concepts that cannot identify their governing primitive or residual.

5. Residual audit
   - Mark each subclaim as one of: metaphor, hypothesis, engineering delta, evidence-backed, or rejected.
   - Identify analogy leakage, missing evidence, hidden priors, and overclaim attractors.

6. Test hook
   - Produce the smallest falsifiable test.
   - The test must specify measurable input, output, control, failure threshold, and expected residual.

7. Warden pass
   - Ask what would make the claim false.
   - Ask what evidence would upgrade or downgrade the claim.
   - Ask whether the terminology is doing real work or hiding uncertainty.

## Standard prompt

```text
Analyze the following concept using the LLM Refinement Protocol.

Concept:
[PASTE CONCEPT]

Step 1: Expand the hidden dimensions as a table.
Step 2: Run a lens sweep using hostile domain scientist, patent examiner, systems engineer, formal-methods auditor, safety reviewer, and implementation engineer.
Step 3: Build a glossary for overloaded terms.
Step 4: Collapse the result into field / shear / packet / spectral primitives.
Step 5: Audit residuals and classify each subclaim as metaphor, hypothesis, engineering delta, evidence-backed, or rejected.
Step 6: Propose the smallest falsifiable test.
Step 7: Give the Warden pass: what would make this false, what would upgrade it, and what language is hiding uncertainty?
```

## Output schema

```yaml
concept: string
one_sentence_claim: string
hidden_dimensions:
  - axis: string
    observable_proxy: string
    uncertainty: string
    failure_mode: string
    primitive: field|shear|packet|spectral|mixed
    test_hook: string
lens_sweep:
  - lens: string
    strongest_objection: string
    strongest_revision: string
glossary:
  - term: string
    local_definition: string
    forbidden_drift: string
primitive_compression:
  field: string
  shear: string
  packet: string
  spectral: string
residual_audit:
  - subclaim: string
    status: metaphor|hypothesis|engineering_delta|evidence_backed|rejected
    evidence_needed: string
smallest_test:
  input: string
  output: string
  control: string
  failure_threshold: string
  expected_residual: string
warden_pass:
  falsifier: string
  upgrade_path: string
  uncertainty_language: string
```

## Repository use

Use this protocol before promoting any new concept into a spec, patent-materials note, paper draft, Lean scaffold, or implementation ticket.
