---
project: ResearchStack
domain: axis-07-attestation
secondary_domains:
  - axis-04-formalization
  - axis-06-safety
  - axis-12-governance
type: ProvenanceInvariant
settlement: PROMOTED
authority: registry
route_signature: provenance/axis-07-attestation/uuid-step-invariant/v0
status: UUID_REQUIRED_FOR_ALL_PROVENANCE_NODES
---

# UUID Provenance Step Invariant

## Purpose

Every provenance-producing action must create stable machine-readable identity before it claims success.

The UUID step prevents evidence from becoming an unaddressable blob of text.

```text
no UUID → no DAG node
no DAG node → no provenance claim
no provenance claim → no promotion
```

## Core invariant

```text
everyActionClaim → uuid + timestamp + dagNode
```

Expanded:

```text
buildClaim                 → buildUUID + buildLog + buildDAG
benchmarkClaim             → benchmarkUUID + benchmarkArtifact + benchmarkDAG
externalVerificationClaim  → verificationUUID + attachedEvidence + verificationDAG
citationClaim              → citationUUID + sourceCitation + accessRecord
commitClaim                → commitUUID + fullCommitHash + repositoryRef
workflowStepClaim          → stepUUID + parentWorkflowUUID + timestamp
```

## UUID placement

A provenance DAG must assign UUIDs at all of these levels:

| Level | Required ID | Reason |
|---|---|---|
| workflow run | `run_id` | Identifies the whole execution |
| action step | `step_id` | Identifies each atomic action |
| claim | `claim_id` | Identifies the statement being made |
| evidence | `evidence_id` | Identifies attached proof material |
| edge | `edge_id` | Identifies why one node depends on another |
| artifact | `artifact_id` | Identifies produced files/logs/results |

## Minimal DAG node schema

```json
{
  "node_id": "uuid-v4",
  "node_type": "buildStep | benchmarkStep | verificationStep | citationStep | commitStep | workflowStep",
  "timestamp": "ISO-8601",
  "actor": "assistant | tool | user | ci",
  "action": "string",
  "claim": "string",
  "evidence": [
    {
      "evidence_id": "uuid-v4",
      "kind": "log | benchmark | citation | commit | api_output | screenshot | file",
      "path_or_url": "string",
      "sha256": "string | null"
    }
  ],
  "status": "pending | passed | failed | quarantined",
  "parent_ids": ["uuid-v4"],
  "edge_ids": ["uuid-v4"]
}
```

## Minimal DAG edge schema

```json
{
  "edge_id": "uuid-v4",
  "from": "uuid-v4",
  "to": "uuid-v4",
  "relation": "depends_on | proves | cites | produced_by | verifies | supersedes | quarantines",
  "timestamp": "ISO-8601"
}
```

## Build logging rule

A build log is not sufficient unless it is linked into the DAG.

Required build record:

```json
{
  "run_id": "uuid-v4",
  "build_id": "uuid-v4",
  "timestamp": "ISO-8601",
  "repo": "repository name",
  "commit": "full 40-character git hash",
  "command": "lake build",
  "log_path": "out/build_logs/lake_build_<timestamp>_<build_id>.log",
  "dag_path": "out/build_dag/build_dag_<timestamp>_<run_id>.json",
  "status": "passed | failed"
}
```

## Path safety rule

All filesystem paths must be quoted or normalized before writing logs or DAG artifacts.

```text
path_with_spaces → must_be_quoted
```

Example:

```bash
REPO_ROOT="/home/allaun/Documents/Research Stack"
BUILD_LOG_DIR="$REPO_ROOT/out/build_logs"
BUILD_DAG_DIR="$REPO_ROOT/out/build_dag"
mkdir -p "$BUILD_LOG_DIR" "$BUILD_DAG_DIR"
```

## User bandwidth protection

The UUID step protects user attention by making every claim traceable.

```text
claim_without_uuid → untraceable_claim
untraceable_claim → user_bandwidth_loss
```

Therefore:

```text
proof burden belongs to the claiming process,
not to the user after the fact.
```

## Promotion rule

A result may be promoted only if:

```text
claim_id exists
node_id exists
evidence_id exists when evidence is required
timestamp exists
DAG edge explains the dependency
status is passed or explicitly edge-survivor
```

Otherwise the result remains:

```text
HOLD_UNADDRESSABLE
```

## Current status

```text
UUID_REQUIRED_FOR_ALL_PROVENANCE_NODES
```

This invariant should be referenced by `all-actions`, `dag-check`, and `chain-all`.
