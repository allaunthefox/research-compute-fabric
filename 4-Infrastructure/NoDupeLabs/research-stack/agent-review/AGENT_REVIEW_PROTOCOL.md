# Research Stack Agent Review Protocol

## Purpose

Create a repeatable agent-style review of the Research Stack that does not rely on vibes, single-pass summaries, or visual intuition alone.

The review answers:

```text
Does the stack preserve authority boundaries?
Do declared artifacts exist?
Do executable components run?
Do simulations emit invariant traces?
Do validators exist and pass?
Can numeric/visual/projection artifacts accidentally become truth?
What remains HOLD / PASS / SCAR / QUARANTINE?
```

## Prime rule

```text
A subsystem is not trusted because it is interesting.
A subsystem is routed only after source, schema, trace, and validator gates are visible.
```

## Review statuses

| Status | Meaning |
|---|---|
| `PASS` | Required files exist, executable gate passes, and no hard boundary violation is detected. |
| `HOLD` | Useful subsystem, but missing execution, validation, or downstream wiring. |
| `SCAR` | Known failure or invariant violation. Preserve as route memory. |
| `QUARANTINE` | Intentionally blocked from validation or observation-partner use. |
| `MISSING` | Declared artifact or required file is absent. |

## Maturity levels

| Level | Meaning |
|---|---|
| `SPEC_EXISTS` | Design/spec file exists. |
| `CODE_EXISTS` | Executable/script/source file exists. |
| `RUNS_LOCALLY` | Command runs without nonzero exit. |
| `EMITS_ARTIFACTS` | Expected output files are produced. |
| `VALIDATOR_EXISTS` | A validator/checker exists. |
| `VALIDATOR_PASSES` | Validator runs and passes. |
| `DOWNSTREAM_CONNECTED` | Outputs are consumed by another subsystem. |

## Subsystems under review

```text
measurement_registry
measurement_source_adapters
semantic_number_pattern_search
abstract_cot_integration
chandelier_genus3_model
pulsar_genus3_model
pulsar_marble_jar_multiscale
doppler_gradient_instrumentation
graph_lean_canonical_layer
famm_memory_layer
solar_system_quarantine
```

## Mandatory boundaries

### Measurement boundary

```text
exact ≠ measured ≠ conventional ≠ environmental ≠ model
```

Every routed number must carry:

```text
source
unit
exactness/status
uncertainty or explicit uncertainty gap
conditions
authority
allowed/blocked uses
```

### Paper boundary

```text
paper → light source / equation candidate
paper ≠ proof
paper ≠ basin
```

### Wolfram/computation boundary

```text
Wolfram/API computation → computational witness
computation ≠ proof
```

### Visualization boundary

```text
image/video/Mermaid/Ace/GraphML → projection or cue
projection ≠ canonical graph
```

### Solar-system boundary

```text
solar-system observations remain quarantined until separately verified
```

## Required outputs

The review harness emits:

```text
research-stack/agent-review/research_stack_agent_review.json
research-stack/agent-review/research_stack_agent_review.md
```

The JSON report is machine-readable. The Markdown report is the human-facing review.

## Manual run

```bash
python3 scripts/research_stack_agent_review.py
```

Static review only:

```bash
python3 scripts/research_stack_agent_review.py --no-execute
```

Full execution review:

```bash
python3 scripts/research_stack_agent_review.py --execute
```

## Interpretation

A passing agent review does not prove the Research Stack. It proves only that:

```text
files exist
commands run
validators pass
known authority boundaries are visible
known quarantine rules are preserved
```

Scientific, mathematical, or formal truth still requires source audit, empirical validation, or proof.
