# Semantic Engine Binding Derivation Workbench

Status: design method for ENE revamp

## Purpose

When inspecting MIT-licensed semantic engines, the goal is not to copy their
implementation. The goal is to inspect their conceptual bindings, identify the
minimum laws that make them work, then rederive those laws from the Research
Stack theory base.

This keeps the path clean:

```text
external engine -> conceptual binding observation -> Research Stack primitive
-> ENE plugin or substrate law -> local implementation
```

## What Counts As A Conceptual Binding

A conceptual binding is a relation that makes a semantic engine useful. It is
not a class name or library API. Examples:

- document to chunk
- chunk to embedding
- embedding to vector index
- query to retriever
- retriever result to citation
- entity mention to graph node
- graph edge to traversal
- node state to temporal fact
- source file to provenance receipt
- plugin connector to normalized record

These are the bindings to inspect.

## Research Stack Re-Derivation Frame

Every external binding should be rebuilt through local primitives:

| External binding | Research Stack re-derivation |
|---|---|
| document -> chunk | `bind(document, surface, informational metric)` |
| chunk -> embedding | `ConceptVector14` projection, not authority |
| embedding -> nearest neighbor | `Address-First Search Protocol` plus optional vector route |
| keyword -> result | `Substrate FTS Query Surface` |
| node -> graph edge | typed edge with receipt and settlement state |
| result -> citation | `InvariantReceipt` / source hash / path |
| memory update -> fact | `ENE Memory Atom` with concept anchor |
| plugin connector -> record | hotswap plugin `scan -> plan -> commit -> verify` |
| score -> rank | `SemanticMass` and Mass Number gate |
| uncertain import -> accepted record | `Meta-Autotype Contingent Field` plus HOLD/quarantine |

## Inspection Template

For each MIT semantic engine, create one workbench note with:

1. **License surface**
   - repository
   - license file
   - files or modules inspected
   - whether any non-MIT data/model dependency changes reuse constraints

2. **Binding inventory**
   - list the engine's core transformations
   - name the input and output of each transformation
   - identify whether the binding is lexical, vector, graph, temporal,
     provenance, agentic, or connector-based

3. **Hidden assumptions**
   - chunk size assumptions
   - embedding model assumptions
   - source trust assumptions
   - update/delete semantics
   - ranking semantics
   - citation/provenance behavior

4. **Research Stack derivation**
   - map each binding to `bind`, substrate, invariant, metric, and receipt
   - decide whether it becomes an ENE plugin, an ENE package law, a wiki
     tiddler pattern, or only an external reference

5. **Admissibility**
   - what is the Mass Number of adopting the idea?
   - what evidence reduces risk?
   - what residual remains?
   - should the result be `SEED`, `FORMING`, `STABLE`, or `HELD`?

## Binding Classes

### 1. Lexical Binding

```text
tokens / terms / exact symbols -> candidate records
```

Local derivation:

```text
Literal index + Substrate FTS Query Surface
```

Use for file paths, theorem names, acronyms, weird aliases, issue IDs, and
functions. Do not replace with pure vector search.

### 2. Vector Binding

```text
text surface -> coordinate vector -> approximate neighborhood
```

Local derivation:

```text
ConceptVector14 + Semantic Eigenvector Bundle + optional external embedding
```

The vector is a route hint, not proof. It must never promote a claim by itself.

### 3. Graph Binding

```text
entity/concept -> typed edge -> traversal path
```

Local derivation:

```text
ENE Memory Atom + typed edge + Fractal Hash Triplet + receipt
```

Every edge should explain itself as `defines`, `aliases`, `imports`, `cites`,
`derives`, `gates`, `blocks`, `promotes`, `demotes`, `benchmarks`,
`round-trips`, `fails`, `quarantines`, or `related-to`.

### 4. Temporal Binding

```text
old fact + new fact -> changed memory state
```

Local derivation:

```text
Concept Anchor Settlement State + wiki/plugin revision receipt
```

Use this for chat logs, TiddlyWiki edits, Notion/Linear mirrors, and evolving
paper interpretations.

### 5. Connector Binding

```text
external workspace -> normalized local record
```

Local derivation:

```text
hotswap plugin lifecycle: discover -> load -> admit -> scan -> plan -> commit -> verify -> unload
```

The TiddlyWiki bridge is the reference plugin. Future MIT-engine-derived
connectors should follow the same shape.

### 6. Claim Binding

```text
retrieved evidence -> promoted claim
```

Local derivation:

```text
Mass Number Sidecar Rule + InvariantReceipt + SettlementState
```

Semantic engines often blur retrieval with truth. ENE must not. Retrieval only
finds candidates. Promotion requires receipts.

## First Engines To Inspect

| Engine family | Binding to inspect | Expected local derivation |
|---|---|---|
| LangChain-style chains | component-to-component runnable binding | hotswap plugin lifecycle |
| LlamaIndex-style nodes | document/node/index/query binding | ENE Memory Atom + address-first search |
| Meilisearch-style hybrid search | lexical/vector/ranking fusion | FTS + ConceptVector14 + Mass Number result gate |
| local knowledge workspaces | file/connector/provenance binding | TiddlyWiki bridge + chat dump manifest |
| graph memory engines | temporal fact and edge binding | settlement state + typed graph receipts |

## Output Rule

Each inspected engine should produce:

- one `External Binding Inspection` note
- one `Research Stack Derivation` note
- optional tiddler cards only after the derivation has a local primitive
- no copied code unless license, dependency, and provenance notices are clean

## ENE Revamp Implication

The revamp should treat external semantic engines as prior-art binding
catalogs. ENE's originality is not "it has vectors" or "it has graph search."
The distinctive shape is:

```text
address-first retrieval
+ ConceptVector14 route hints
+ typed graph edges
+ Mass Number promotion gates
+ plugin receipts
+ settlement state
+ quarantine for uncertain imports
```

That is the first-principles rederivation target.

