---
title: "<% tp.file.title %>"
type: "receipt"
schema: ""
version: "1.0.0"
generated: "<% tp.date.now('YYYY-MM-DDTHH:mm:ssZ') %>"
status: "<% tp.system.suggester(['valid', 'pending', 'failed', 'expired'], ['Valid', 'Pending', 'Failed', 'Expired']) %>"
layer: "<% tp.system.suggester(['L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6'], ['L0 - Primordial', 'L1 - Geometric', 'L2 - Biological', 'L3 - Thermodynamic', 'L4 - Security', 'L5 - Semantic', 'L6 - Meta']) %>"
theorem: ""
experiment: ""
hash: ""
---

# Receipt: <% tp.file.title %>

## Receipt Metadata
```json
{
  "schema": "<% tp.system.suggester(['stack_solidification_receipt_v1', 'formal_proof_receipt_v1', 'hardware_extraction_receipt_v1', 'experiment_receipt_v1'], ['Stack Solidification Receipt v1', 'Formal Proof Receipt v1', 'Hardware Extraction Receipt v1', 'Experiment Receipt v1']) %>",
  "version": "1.0.0",
  "generated_at_utc": "<% tp.date.now('YYYY-MM-DDTHH:mm:ssZ') %>",
  "parent_hash": "",
  "claim_boundary": "",
  "receipt_hash": ""
}
```

## Claim Boundary
<!-- What this receipt actually proves -->
> **Scope:** <!-- Explicit boundary of what is being claimed -->
> **Limitations:** <!-- What is NOT being claimed -->

## Observation Layer
<!-- What was measured/observed -->

### System State
- **Configuration:** <!-- System configuration -->
- **Input Parameters:** <!-- Test inputs -->
- **Environment:** <!-- Test environment -->

### Measurements
| Parameter | Value | Unit | Method |
|-----------|-------|------|--------|
| <!-- Param 1 --> | <!-- Value 1 --> | <!-- Unit 1 --> | <!-- Method 1 --> |
| <!-- Param 2 --> | <!-- Value 2 --> | <!-- Unit 2 --> | <!-- Method 2 --> |

## Decision Layer
<!-- What was decided based on observations -->

### Decision Logic
```lean
-- Decision criteria in Lean
def decisionCriteria (state : SystemState) : Bool :=
  condition1 state ∧ condition2 state
```

### Outcome
- **Decision:** <!-- What was decided -->
- **Rationale:** <!-- Why this decision was made -->
- **Confidence:** <!-- Confidence level -->

## Action Layer
<!-- What actions were taken -->

### Actions Performed
- **Action 1:** <!-- Description -->
  - **Status:** <% tp.system.suggester(['success', 'partial', 'failed'], ['Success', 'Partial', 'Failed']) %>
  - **Artifacts:** <!-- Generated artifacts -->

- **Action 2:** <!-- Description -->
  - **Status:** <% tp.system.suggester(['success', 'partial', 'failed'], ['Success', 'Partial', 'Failed']) %>
  - **Artifacts:** <!-- Generated artifacts -->

## Result Layer
<!-- What was the result of actions -->

### Success Metrics
- **Metric 1:** <!-- Value --> / <!-- Target -->
- **Metric 2:** <!-- Value --> / <!-- Target -->
- **Metric 3:** <!-- Value --> / <!-- Target -->

### Validation Status
- **Formal Verification:** <% tp.system.suggester(['passed', 'failed', 'pending'], ['Passed', 'Failed', 'Pending']) %>
- **Empirical Validation:** <% tp.system.suggester(['passed', 'failed', 'pending'], ['Passed', 'Failed', 'Pending']) %>
- **Peer Review:** <% tp.system.suggester(['passed', 'failed', 'pending'], ['Passed', 'Failed', 'Pending']) %>

## Receipt Dimensions
<!-- Core dimensions of this receipt -->

### Computational Dimensions
- **C (Crossing Matrix):** <!-- Description -->
- **σ (Sidon Slack):** <!-- Description -->
- **k (Step Count):** <!-- Description -->

### Information Dimensions
- **ε_seq (Residual Series):** <!-- Description -->
- **t (Timing):** <!-- Description -->
- **∅_scars (Scar Absence):** <!-- Description -->

## Chain of Custody
<!-- Traceability of this receipt -->

### Parent Receipts
- [[Parent Receipt 1]]
- [[Parent Receipt 2]]

### Child Receipts
- [[Child Receipt 1]]
- [[Child Receipt 2]]

### Hash Verification
```
SHA256: <% tp.system.suggester(['computed', 'pending'], ['Computed', 'Pending']) %>
Method: <!-- Hash computation method -->
```

## Reproducibility
<!-- How to reproduce this receipt -->

### Environment
- **OS:** <!-- Operating system -->
- **Lean Version:** <!-- Lean compiler version -->
- **Dependencies:** <!-- Key dependencies -->

### Procedure
1. <!-- Step 1 -->
2. <!-- Step 2 -->
3. <!-- Step 3 -->

### Command Line
```bash
# Commands to reproduce
lean build
python3 receipt_generator.py
```

## Anomalies & Exceptions
<!-- Anything unusual that occurred -->

### Observed Anomalies
- **Anomaly 1:** <!-- Description and impact -->
- **Anomaly 2:** <!-- Description and impact -->

### Exception Handling
- **Exception 1:** <!-- How handled -->
- **Exception 2:** <!-- How handled -->

## Quality Assurance
<!-- QA checks performed -->

### Automated Checks
- [ ] **Syntax Validation:** <!-- Pass/Fail -->
- [ ] **Type Checking:** <!-- Pass/Fail -->
- [ ] **Hash Verification:** <!-- Pass/Fail -->

### Manual Review
- [ ] **Logic Review:** <!-- Reviewer name -->
- [ ] **Domain Review:** <!-- Reviewer name -->
- [ ] **Final Approval:** <!-- Approver name -->

## Related Artifacts
- [[Related Formal Proof]]
- [[Related Experiment]]
- [[Related Hardware Test]]

## Notes
<!-- Additional context, observations, or concerns -->

## Tags
#receipt #layer-<% tp.system.suggester(['L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6'], ['L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6']) %> #status-<% tp.system.suggester(['valid', 'pending', 'failed', 'expired'], ['valid', 'pending', 'failed', 'expired']) %>