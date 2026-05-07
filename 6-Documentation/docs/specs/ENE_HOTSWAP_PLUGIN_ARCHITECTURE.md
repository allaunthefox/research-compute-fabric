# ENE Hotswappable Plugin Architecture

Status: revamp target / frontline module plan

## Purpose

ENE needs a plugin architecture where new data surfaces can be attached,
detached, audited, and upgraded without rewriting the core substrate. The
TiddlyWiki bridge is the first frontline plugin because it turns the wiki into
a live knowledge-capture surface instead of a sidecar document store.

## Design Rule

Plugins are not trusted just because they are installed. A plugin must provide:

- a manifest
- a stable plugin id
- declared read/write surfaces
- an explicit settlement policy
- deterministic receipts for each write
- dry-run mode
- idempotent ingest behavior
- a quarantine path for unknown or oversized content

## Plugin Lifecycle

1. `discover`: read plugin manifests from known plugin directories.
2. `load`: import the plugin module and check its declared interface version.
3. `admit`: verify that requested surfaces match the manifest.
4. `scan`: collect source records and compute source receipts.
5. `plan`: produce intended ENE package writes without mutating state.
6. `commit`: write packages, receipts, links, and plugin state.
7. `verify`: re-read written records and compare receipts.
8. `unload`: close file handles and release watcher resources.

## Minimal Plugin Manifest

```json
{
  "plugin_id": "ene.tiddlywiki.bridge",
  "version": "0.1.0",
  "interface_version": "ene-plugin-v0",
  "entrypoint": "tiddlywiki_ene_bridge.py",
  "surfaces": {
    "reads": ["6-Documentation/tiddlywiki-local/wiki/tiddlers"],
    "writes": ["data/substrate_index.db"]
  },
  "capabilities": [
    "scan",
    "dry_run",
    "ingest",
    "receipt",
    "incremental_state"
  ]
}
```

## TiddlyWiki Bridge Role

The bridge watches or scans `.tid` files, parses field headers and body text,
then upserts one ENE package per tiddler. It does not embed the entire
TiddlyWiki runtime inside ENE. Instead, it embeds the TiddlyWiki data surface:

- title
- tags
- type
- modified/created timestamps
- body hash
- source path
- wiki links
- concept anchor
- ConceptVector14-style route vector
- plugin receipt

This lets TiddlyWiki remain a good human editing surface while ENE remains the
truth substrate for search, provenance, and settlement.

## Package Shape

Package id:

```text
ene/tiddlywiki/<slug>
```

Version:

```text
<modified timestamp or file mtime>-<content hash prefix>
```

Concept anchor:

```json
{
  "domain": "wiki",
  "concept": "<slug>",
  "resolution": "FORMING",
  "source_plugin": "ene.tiddlywiki.bridge"
}
```

Verification basis:

```text
tiddlywiki_bridge_receipt:<sha256>
```

## Quarantine Rules

The plugin must refuse or quarantine:

- active script content
- tiddlers over the configured byte limit
- missing titles
- malformed field blocks
- package writes that cannot be re-read

## Near-Term Path

The current implementation is a standalone Python module. During the planned
ENE revamp, it should become the reference plugin for:

- plugin discovery
- dry-run planning
- receipt shape
- incremental state
- hotswap load/unload
- TiddlyWiki-to-ENE ingestion

