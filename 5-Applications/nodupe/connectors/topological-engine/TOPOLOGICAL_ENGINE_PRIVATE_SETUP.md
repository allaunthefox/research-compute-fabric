# PRIVATE Topological Engine Connector

Obsidian + Neo4j connector for Research Stack.

## Authority boundary

- Obsidian = local human-readable vault/workbench mirror
- Neo4j = private graph traversal/query engine
- Graph.lean = canonical graph authority
- ENE = provenance/archive authority

Neo4j can discover candidate topology. It cannot certify proof, empirical validity, or basin promotion.

## Security rule

This connector must never be public.

Allowed exposure:

- localhost
- VPN
- tailnet
- SSH tunnel
- private reverse proxy

Forbidden exposure:

- public internet
- public Neo4j Browser/Bolt/HTTP
- unauthenticated HTTP
- public OpenAPI action
- public webhook

## Environment

```bash
export TOPOLOGICAL_ENGINE_TOKEN="long-random-private-token-at-least-32-chars"
export OBSIDIAN_VAULT_PATH="/absolute/path/to/private/obsidian-vault"
export NEO4J_URI="bolt://127.0.0.1:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="use-a-local-secret-manager"
```

Never store secrets in GitHub, Notion, Google Drive, or Obsidian notes.

## Mount

In `server.js`:

```js
import topologicalEngineRouter from "./connectors/topological-engine/neo4j_obsidian_connector_router.js";
app.use("/topology", topologicalEngineRouter);
```

## Endpoints

Mounted under `/topology`:

```text
GET  /topology/health
POST /topology/obsidian/write-note
GET  /topology/obsidian/read-note?path=...
POST /topology/obsidian/search
POST /topology/neo4j/cypher
POST /topology/neo4j/upsert-road
POST /topology/neo4j/import-obsidian-links
```

## Smoke tests

```bash
curl -H "Authorization: Bearer $TOPOLOGICAL_ENGINE_TOKEN" \
  http://127.0.0.1:3000/topology/health
```

```bash
curl -X POST http://127.0.0.1:3000/topology/obsidian/write-note \
  -H "Authorization: Bearer $TOPOLOGICAL_ENGINE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Topological Engine Smoke Test","folder":"Research Stack/Plumbing","body":"Private Obsidian mirror online.","artifact_class":"TextNote","outcome":"hold"}'
```

```bash
curl -X POST http://127.0.0.1:3000/topology/neo4j/upsert-road \
  -H "Authorization: Bearer $TOPOLOGICAL_ENGINE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sourceId":"artifact","sourceLabel":"Artifact","targetId":"fingerprint","targetLabel":"Fingerprint","relation":"NORMALIZES_TO","authority_scope":"candidate","outcome":"hold","torsion":1,"coherence":0.8}'
```

## Required private dependency

```bash
npm install neo4j-driver
```

The router also expects Express to already exist in the server app.

## Research Stack path

```text
Raw artifact
→ ENE receipt
→ Artifact Normalization
→ Obsidian markdown mirror
→ Neo4j private traversal engine
→ candidate roads
→ Graph.lean audit
→ Graph Diff + Torsion
→ FAMM memory
→ Notion registry summary
```

## Graph.lean audit rule

```text
Neo4j path hit → candidate road → Graph.lean audit → graph diff/torsion → FAMM outcome
```

No Neo4j query can promote a basin by itself.
