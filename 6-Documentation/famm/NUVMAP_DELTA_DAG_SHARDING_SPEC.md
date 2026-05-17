# NUVMAP Delta-DAG Sharding Spec

## Goal

Make search traces shardable, replayable, and independently verifiable.

## Shard ID format

```text
famm-ddag://<problem_hash>/<shard_type>/<hash>
```

## Required hashes

```json
{
  "problem_hash": "sha256(base instance)",
  "rule_hash": "sha256(route rule + weights)",
  "projection_hash": "sha256(NUVMAP projection config)",
  "node_hash": "sha256(projected node payload)",
  "edge_hash": "sha256(parent_hash + delta + child_hash)",
  "receipt_hash": "sha256(final verifier payload)"
}
```

## Edge verification

Every delta-edge shard must verify:

```text
apply_delta(parent_state, delta, route_rule)
→ child_state

hash(project(child_state))
= child_node_hash
```

## DAG merge condition

Two states may share a node if their NUVMAP projections match:

```math
h_{\mathrm{NUV}}(s_a)=h_{\mathrm{NUV}}(s_b)
```

The merge is safe only for the selected projection level. Exact receipt still replays an explicit solution path.

## Projection levels

| Level | Meaning | Use |
|---|---|---|
| `exact` | raw canonical state | safest; fewer merges |
| `frontier` | frontier + domains + scars + residual | normal FAMM use |
| `symmetry` | frontier plus symmetry/canonical color relabeling | aggressive merge |
| `semantic` | semantic-mass basin only | routing prior, not proof |

## Receipt rule

The DAG may guide and compress search, but the final solution must be verified by a domain exact gate.

For graph coloring:

```math
R(c)=|\{(u,v)\in E:c_u=c_v\}|=0
```

For exact cover:

```math
R(x)=\|Ax-\mathbf 1\|_1=0
```
